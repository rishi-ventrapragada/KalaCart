"""
Vision Pipeline — main async orchestrator for KalaCart image enhancement.

Flow (as per spec):
  validate inputs -> decode cv2.imdecode -> EXIF rotation via PIL -> validate dims
  100x100..6000x6000 -> background mask -> enhance (if enabled, metered on the product)
  -> compose on white -> frame around the product (or centred crop_to_ratio)
  -> resize_to_target (1080) -> export PNG/WebP + thumbnail

Exports:
  async def process_image_pipeline(image_bytes: bytes, output_format: str="1:1",
                                   enhance: bool=True) -> dict

Return dict keys:
  original_bytes, enhanced_bytes (PNG), webp_bytes, thumbnail_bytes (WebP 256),
  width, height, ratio, background_removed

Fallback: if background removal fails, just enhance without removal.
All errors are caught and re-raised as ValueError with clear message for API layer.
The CPU-bound work runs in a worker thread so the event loop keeps serving requests.
No hardcoded secrets.
"""

from __future__ import annotations

import asyncio
import io
import logging
from typing import Dict

import cv2
import numpy as np

logger = logging.getLogger(__name__)

# Constants — match spec and storage_service limits
MIN_DIM = 100
MAX_DIM = 6000
MAX_FILE_BYTES = 10 * 1024 * 1024  # 10 MB soft check (pipeline also handles larger via resize)
ALLOWED_FORMATS = {"1:1", "4:5"}
WEBP_QUALITY = 85
THUMB_SIZE = 256  # longest edge for thumbnail (256 for square, ~205 for 4:5 will be computed)


def _fix_exif_rotation(image_bytes: bytes, decoded_bgr: np.ndarray) -> np.ndarray:
    """
    Handle EXIF orientation. Tries PIL ImageOps.exif_transpose; if orientation
    indicates rotation, re-decode via PIL and convert back to BGR.

    If no EXIF or PIL not handling, returns decoded_bgr unchanged.
    """
    try:
        from PIL import Image, ImageOps

        pil_img = Image.open(io.BytesIO(image_bytes))
        # exif_transpose handles all 8 orientations safely; no-op if no exif
        transposed = ImageOps.exif_transpose(pil_img)
        if transposed is None:
            return decoded_bgr

        # If transposed size differs from decoded_bgr or if transpose actually changed pixels,
        # we rebuild BGR from PIL. Check if transposed had exif applied by comparing mode/size.
        # PIL is RGB/RGBA; convert to BGR for OpenCV.
        # We always rebuild if PIL succeeded, to ensure rotation is applied correctly.
        # This is idempotent — if no rotation needed, result equals original.

        # Convert PIL -> numpy -> BGR
        if transposed.mode == "RGBA":
            # Composite alpha over white before BGR conversion
            bg = Image.new("RGB", transposed.size, (255, 255, 255))
            bg.paste(transposed, mask=transposed.split()[3])
            transposed = bg
        # Ensure RGB
        if transposed.mode != "RGB":
            transposed = transposed.convert("RGB")
        rgb_arr = np.array(transposed)  # H x W x 3 RGB
        bgr = cv2.cvtColor(rgb_arr, cv2.COLOR_RGB2BGR)
        # Heuristic: only use PIL result if dimensions differ or if decoded was likely misoriented
        # Simpler: if bgr shape != decoded_bgr shape, PIL rotation changed orientation -> use bgr
        # If shapes equal, check if we should still use PIL result (it may be same but correctly rotated)
        # We'll use PIL result whenever it was transposed and is valid, but keep decoded if PIL failed
        # Here we return bgr if it looks reasonable (non-empty, uint8)
        if bgr.size > 0 and bgr.dtype == np.uint8 and bgr.ndim == 3:
            # If decoded and bgr are same shape and content very similar, either is fine; prefer bgr
            return bgr
        return decoded_bgr

    except ImportError:
        logger.debug("Pillow not available for EXIF fix — skipping")
        return decoded_bgr
    except Exception as exc:
        logger.debug("EXIF fix failed (non-fatal): %s", exc)
        return decoded_bgr


def _decode_image(image_bytes: bytes) -> np.ndarray:
    """Decode bytes via cv2.imdecode then EXIF fix."""
    if not image_bytes or len(image_bytes) == 0:
        raise ValueError("Empty image bytes")

    # Quick size guard (storage_service also enforces 10MB, but pipeline is lenient)
    if len(image_bytes) > MAX_FILE_BYTES * 2:  # allow up to 20MB before rejecting (high-res)
        logger.warning("Image bytes large (%d) — attempting decode anyway", len(image_bytes))

    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)  # BGR, strips alpha (we handle alpha via PIL if needed)
    if img is None:
        # Try PIL fallback for uncommon formats (e.g., palette PNG, CMYK jpeg)
        try:
            from PIL import Image
            pil = Image.open(io.BytesIO(image_bytes))
            if pil.mode == "RGBA":
                bg = Image.new("RGB", pil.size, (255, 255, 255))
                bg.paste(pil, mask=pil.split()[3])
                pil = bg
            if pil.mode != "RGB":
                pil = pil.convert("RGB")
            rgb = np.array(pil)
            img = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
            logger.info("Decoded via PIL fallback after cv2.imdecode failure")
        except Exception as exc:
            raise ValueError(f"Unable to decode image — not a valid JPEG/PNG/WebP: {exc}") from exc

    if img is None or img.size == 0:
        raise ValueError("Failed to decode image (cv2.imdecode returned None/empty)")

    # EXIF rotation fix — must pass original bytes for EXIF read
    img = _fix_exif_rotation(image_bytes, img)

    return img


def _validate_dimensions(img: np.ndarray) -> None:
    h, w = img.shape[:2]
    if w < MIN_DIM or h < MIN_DIM:
        raise ValueError(f"Image too small: {w}x{h} — minimum is {MIN_DIM}x{MIN_DIM}")
    if w > MAX_DIM or h > MAX_DIM:
        raise ValueError(f"Image too large: {w}x{h} — maximum is {MAX_DIM}x{MAX_DIM}")


def _export_png(img_bgr: np.ndarray) -> bytes:
    """Encode BGR image to PNG bytes via cv2.imencode."""
    try:
        ok, buf = cv2.imencode(".png", img_bgr)
        if not ok or buf is None:
            raise RuntimeError("cv2.imencode PNG returned not ok")
        return buf.tobytes()
    except Exception as exc:
        # Fallback via PIL
        try:
            from PIL import Image
            rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
            pil = Image.fromarray(rgb)
            out = io.BytesIO()
            pil.save(out, format="PNG", optimize=True)
            return out.getvalue()
        except Exception as e2:
            raise RuntimeError(f"PNG export failed: {exc} / fallback {e2}") from exc


def _export_webp(img_bgr: np.ndarray, quality: int = 85) -> bytes:
    """Encode BGR image to WebP bytes. Try cv2 then PIL fallback."""
    quality = int(max(1, min(100, quality)))
    # Try OpenCV first (fast, no extra dep beyond opencv-python which often includes webp)
    try:
        ok, buf = cv2.imencode(".webp", img_bgr, [cv2.IMWRITE_WEBP_QUALITY, quality])
        if ok and buf is not None and len(buf) > 0:
            return buf.tobytes()
        raise RuntimeError("cv2 webp encode returned not ok / empty")
    except Exception as cv_exc:
        logger.debug("cv2 WebP encode failed (%s) — trying PIL", cv_exc)
        try:
            from PIL import Image
            rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
            pil = Image.fromarray(rgb)
            out = io.BytesIO()
            pil.save(out, format="WEBP", quality=quality, method=4)
            data = out.getvalue()
            if not data:
                raise RuntimeError("PIL WebP produced empty bytes")
            return data
        except Exception as pil_exc:
            logger.warning("WebP export both cv2 and PIL failed: cv2=%s pil=%s", cv_exc, pil_exc)
            # Last resort: return PNG bytes but caller expects webp — raise
            raise RuntimeError(f"WebP export failed (cv2: {cv_exc}, PIL: {pil_exc})") from pil_exc


def _make_thumbnail(img_bgr: np.ndarray, thumb_long: int = THUMB_SIZE) -> bytes:
    """
    Create thumbnail WebP (long edge = thumb_long). Maintains aspect.
    For 1:1 1080x1080 -> thumb 256x256 ; for 4:5 864x1080 -> thumb ~205x256.
    """
    h, w = img_bgr.shape[:2]
    # Compute thumb size preserving aspect, long edge = thumb_long
    if h >= w:
        # Portrait / square: height = thumb_long
        th = thumb_long
        tw = max(1, int(round(w * (thumb_long / float(h)))))
    else:
        tw = thumb_long
        th = max(1, int(round(h * (thumb_long / float(w)))))
    try:
        # Use INTER_AREA for thumbnail downscale
        thumb = cv2.resize(img_bgr, (tw, th), interpolation=cv2.INTER_AREA)
    except Exception as exc:
        logger.warning("Thumbnail resize failed: %s — using original scaled", exc)
        thumb = img_bgr
    return _export_webp(thumb, quality=80)  # slightly lower quality for thumb


def _run_pipeline(image_bytes: bytes, output_format: str, enhance: bool) -> Dict:
    """Synchronous pipeline body (CPU-bound). Called by process_image_pipeline in a worker thread."""
    # Preserve original bytes as-is for return (caller may store original separately)
    original_bytes = image_bytes

    # ── Decode + EXIF + validate dims ────────────────────────────
    img = _decode_image(image_bytes)
    _validate_dimensions(img)

    h0, w0 = img.shape[:2]
    logger.info("Pipeline start: %dx%d format=%s enhance=%s bytes=%d", w0, h0, output_format, enhance, len(image_bytes))

    # ── Background mask (with fallback) ──────────────────────────
    mask = None
    mask_success = False
    try:
        from app.vision.background import get_foreground_mask

        mask = get_foreground_mask(img, iterations=5)
        # Validate mask
        if mask is None or mask.size == 0:
            raise RuntimeError("Mask is None/empty")
        if mask.shape[0] != img.shape[0] or mask.shape[1] != img.shape[1]:
            # Resize mask to img shape if needed (should not happen)
            mask = cv2.resize(mask, (img.shape[1], img.shape[0]), interpolation=cv2.INTER_NEAREST)
        # Degeneracy check already in background.py, but double-check
        fg_ratio = float(np.mean(mask == 255)) if mask.dtype == np.uint8 else 0.5
        if 0.02 < fg_ratio < 0.98:
            mask_success = True
        else:
            logger.warning("Pipeline: mask degenerate (fg_ratio=%.3f) — will skip removal", fg_ratio)
            mask = None
            mask_success = False
    except Exception as exc:
        logger.warning("Pipeline: background removal failed (%s) — continuing without removal", exc)
        mask = None
        mask_success = False

    # ── Enhance (if enabled) ─────────────────────────────────────
    # With a mask, exposure is metered on the product and white balance is read from the background
    enhanced_fg = img
    if enhance:
        try:
            from app.vision.enhance import enhance_image as _enhance

            enhanced_fg = _enhance(img, mask=mask if mask_success else None)
            logger.debug("Enhancement succeeded")
        except Exception as exc:
            logger.warning("Enhancement step failed (%s) — using original", exc)
            enhanced_fg = img.copy()
    else:
        logger.debug("Enhancement skipped (enhance=False)")

    # ── Compose on white (if mask succeeded) ─────────────────────
    composited = enhanced_fg
    if mask_success and mask is not None:
        try:
            from app.vision.compose import compose_on_white as _compose

            composited = _compose(enhanced_fg, mask, bg_color=(255, 255, 255))
            logger.debug("Compose on white succeeded")
        except Exception as exc:
            logger.warning("Compose failed (%s) — using enhanced image without removal", exc)
            composited = enhanced_fg.copy()
            mask_success = False

    # ── Frame: around the product when isolated, otherwise centred crop ─
    try:
        if mask_success and mask is not None:
            from app.vision.compose import crop_to_subject as _frame

            composited = _frame(composited, mask, ratio=output_format)
        else:
            from app.vision.compose import crop_to_ratio as _crop

            composited = _crop(composited, ratio=output_format)
    except Exception as exc:
        logger.warning("Framing failed (%s) — skipping crop", exc)

    # ── Resize to target 1080 ────────────────────────────────────
    try:
        from app.vision.compose import resize_to_target as _resize

        composited = _resize(composited, target=1080)
    except Exception as exc:
        logger.warning("resize_to_target failed (%s) — using cropped image", exc)

    width, height = composited.shape[1], composited.shape[0]
    logger.info("Pipeline result: %dx%d (format %s, background_removed=%s)", width, height, output_format, mask_success)

    # ── Export: PNG, WebP, thumbnail ─────────────────────────────
    try:
        enhanced_bytes = _export_png(composited)
    except Exception as exc:
        logger.error("PNG export failed: %s", exc)
        raise ValueError(f"Failed to export PNG: {exc}") from exc

    try:
        webp_bytes = _export_webp(composited, quality=WEBP_QUALITY)
    except Exception as exc:
        logger.error("WebP export failed: %s", exc)
        # Fallback: generate PNG as webp_bytes? Better raise — caller can decide
        raise ValueError(f"Failed to export WebP: {exc}") from exc

    try:
        thumbnail_bytes = _make_thumbnail(composited, thumb_long=THUMB_SIZE)
    except Exception as exc:
        logger.error("Thumbnail export failed: %s", exc)
        # Thumbnail failure should not fail whole pipeline — generate small webp via resize fallback
        try:
            thumb_fallback = cv2.resize(composited, (256, 256), interpolation=cv2.INTER_AREA)
            thumbnail_bytes = _export_webp(thumb_fallback, quality=80)
        except Exception as e2:
            raise ValueError(f"Thumbnail export failed: {exc} / fallback {e2}") from exc

    return {
        "original_bytes": original_bytes,
        "enhanced_bytes": enhanced_bytes,      # PNG
        "webp_bytes": webp_bytes,              # WebP quality 85
        "thumbnail_bytes": thumbnail_bytes,    # WebP 256 long edge
        "width": width,
        "height": height,
        "ratio": output_format,
        "background_removed": mask_success,
    }


async def process_image_pipeline(
    image_bytes: bytes,
    output_format: str = "1:1",
    enhance: bool = True,
) -> Dict:
    """
    Main pipeline — decode, validate, remove background, enhance, frame, resize, export.

    Args:
        image_bytes: Raw uploaded image bytes (jpeg/png/webp).
        output_format: "1:1" or "4:5" (output aspect).
        enhance: Whether to run enhancement chain (default True).

    Returns:
        dict with keys:
            original_bytes: bytes (the input image_bytes as-is, for storage caller to use)
            enhanced_bytes: bytes (PNG, full resolution 1080 target)
            webp_bytes: bytes (WebP quality 85, same resolution)
            thumbnail_bytes: bytes (WebP small ~256 long edge)
            width: int
            height: int
            ratio: str  (echo of output_format)
            background_removed: bool (False when no clean subject/background split was found)

    Raises:
        ValueError on validation / decode failure.
    """
    # ── Validate format ──────────────────────────────────────────
    if output_format not in ALLOWED_FORMATS:
        raise ValueError(f"Invalid output_format '{output_format}'. Allowed: {ALLOWED_FORMATS}")

    if not image_bytes or len(image_bytes) == 0:
        raise ValueError("Empty image bytes — upload a valid image")

    # OpenCV work is CPU-bound — run it off the event loop so other requests aren't blocked
    return await asyncio.to_thread(_run_pipeline, image_bytes, output_format, enhance)
