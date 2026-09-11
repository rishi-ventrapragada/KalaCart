"""
Image Enhancement API — POST /api/v1/image/enhance

Security-first, pipeline-backed implementation.

Flow:
  1. Auth via Firebase JWT (Depends(get_current_user))
  2. SECURITY VALIDATION (must be done BEFORE pipeline):
     - Max 10 MB -> 413
     - Allowed MIME: image/jpeg, image/jpg, image/png, image/webp, image/pjpeg, image/x-png -> else 400
     - Reject executable MIME (contains "executable") or filename ends with .exe/.sh/.bat/.php/.js -> 400
     - Extension allowlist: jpg/jpeg/png/webp -> else 400
     - Path traversal guard: never use raw filename; generate UUID hex; reject "../" "/" "\" in filename
     - Decode with cv2.imdecode / PIL fallback; if fails -> 400
     - Dimensions 100-6000 -> else 400
  3. Pipeline: process_image_pipeline(image_bytes, output_format, enhance=True)
  4. Storage: base = "{artisan_id}/{uuid.hex}" ; upload original, enhanced PNG, WebP, thumb to bucket
     via Supabase Storage (or placeholder mock in DEBUG)
  5. Return {success, original_url, enhanced_url (prefer webp), thumbnail_url, width, height}

No AI marketplace / voice / catalog / translation / pricing logic here.
"""

import base64
import io
import logging
import os
import uuid
from typing import Dict, Any

import cv2
import numpy as np
from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse

from app.core.security import get_current_user
from app.vision.pipeline import process_image_pipeline

logger = logging.getLogger(__name__)

router = APIRouter()

# ── Constants ──────────────────────────────────────────────────────────

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB

ALLOWED_MIMES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
    "image/pjpeg",
    "image/x-png",
}

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}

BLOCKED_EXTENSIONS = {".exe", ".sh", ".bat", ".php", ".js"}
BLOCKED_SUFFIXES = ("exe", "sh", "bat", "php", "js")  # without dot for fallback

ALLOWED_OUTPUT_FORMATS = {"1:1", "4:5"}

MIN_DIM = 100
MAX_DIM = 6000

# MIME to extension helper for storage original
MIME_TO_EXT = {
    "image/jpeg": "jpg",
    "image/jpg": "jpg",
    "image/pjpeg": "jpg",
    "image/png": "png",
    "image/x-png": "png",
    "image/webp": "webp",
}

MIME_TO_CONTENT_TYPE = {
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "webp": "image/webp",
}


def _get_bucket_name() -> str:
    """Resolve bucket from Settings or env."""
    try:
        from app.core.config import get_settings

        return get_settings().SUPABASE_STORAGE_BUCKET or "product-images"
    except Exception:
        return os.getenv("SUPABASE_STORAGE_BUCKET", "product-images")


def _get_supabase_url() -> str:
    try:
        from app.core.config import get_settings

        return get_settings().SUPABASE_URL or os.getenv("SUPABASE_URL") or "https://placeholder.supabase.co"
    except Exception:
        return os.getenv("SUPABASE_URL") or "https://placeholder.supabase.co"


def _is_debug() -> bool:
    try:
        from app.core.config import get_settings

        s = get_settings()
        return bool(s.DEBUG)
    except Exception:
        return os.getenv("DEBUG", "false").lower() in ("true", "1", "yes", "on")


def _sanitize_filename(filename: str | None) -> str:
    """Return safe display filename or empty. Does NOT use for storage path."""
    if not filename:
        return ""
    return filename.strip()


def _extract_extension(filename: str | None, content_type: str | None) -> str:
    """
    Derive extension (jpg/png/webp) from filename or MIME.
    Returns normalized ext without dot, e.g., 'jpg'.
    Raises HTTPException 400 if not allowed.
    """
    ext = ""
    if filename and "." in filename:
        ext = filename.rsplit(".", 1)[-1].lower().strip()
        # Handle double extensions like .php.jpg — we already block executable suffixes
        if ext in ALLOWED_EXTENSIONS:
            if ext == "jpeg":
                return "jpg"
            return ext
        # If ext not in allowed but MIME is allowed, we may still accept via MIME fallback below
    # Fallback to MIME
    if content_type:
        ct = content_type.lower().strip()
        if ct in MIME_TO_EXT:
            return MIME_TO_EXT[ct]
    # If still not resolved, raise
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Unsupported file extension '.{ext}' or MIME '{content_type}'. Allowed: jpg, jpeg, png, webp",
    )


def _validate_dimensions_bytes(image_bytes: bytes) -> tuple[int, int]:
    """
    Decode image_bytes and validate dimensions 100-6000.
    Returns (width, height).
    Raises HTTPException 400 if invalid.
    """
    if not image_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty image file")
    # Try cv2
    try:
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is not None and img.size != 0:
            h, w = img.shape[:2]
            if w < MIN_DIM or h < MIN_DIM:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Image too small: {w}x{h} — minimum is {MIN_DIM}x{MIN_DIM}",
                )
            if w > MAX_DIM or h > MAX_DIM:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Image too large: {w}x{h} — maximum is {MAX_DIM}x{MAX_DIM}",
                )
            return w, h
        else:
            raise ValueError("cv2.imdecode returned None/empty")
    except HTTPException:
        raise
    except Exception as cv_exc:
        # Fallback to PIL for dimension check
        try:
            from PIL import Image

            pil = Image.open(io.BytesIO(image_bytes))
            # Handle truncated images
            pil.load()
            w, h = pil.size
            if w < MIN_DIM or h < MIN_DIM:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Image too small: {w}x{h} — minimum is {MIN_DIM}x{MIN_DIM}",
                )
            if w > MAX_DIM or h > MAX_DIM:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Image too large: {w}x{h} — maximum is {MAX_DIM}x{MAX_DIM}",
                )
            return w, h
        except HTTPException:
            raise
        except Exception as pil_exc:
            logger.warning("Dimension decode failed cv2=%s PIL=%s", cv_exc, pil_exc)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid image file — unable to decode as JPEG/PNG/WebP",
            ) from pil_exc


def _upload_bytes_with_fallback(bucket: str, path: str, data: bytes, content_type: str) -> str:
    """
    Upload raw bytes to Supabase Storage with DEBUG mock fallback.
    Returns public URL.
    """
    if not data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty data for upload")
    if ".." in path or path.startswith("/") or "\\" in path:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid storage path")

    is_debug = _is_debug()
    supabase_url = _get_supabase_url().rstrip("/") if _get_supabase_url() else "https://placeholder.supabase.co"
    target_bucket = bucket or _get_bucket_name()

    # Ensure bucket exists (best effort)
    if not is_debug or _get_supabase_url() != "https://placeholder.supabase.co":
        try:
            from app.services.storage_service import ensure_bucket_exists

            ensure_bucket_exists()
        except Exception as be:
            logger.debug("ensure_bucket_exists non-fatal: %s", be)

    try:
        from app.database.connection import get_supabase_client

        client = get_supabase_client()
        # Attempt upload
        client.storage.from_(target_bucket).upload(
            path=path,
            file=data,
            file_options={"content-type": content_type, "upsert": "false"},
        )
        logger.info("Uploaded %s/%s (%d bytes, %s)", target_bucket, path, len(data), content_type)
    except Exception as exc:
        err_lower = str(exc).lower()
        # Handle duplicate (extremely rare UUID collision)
        if "already exists" in err_lower or "duplicate" in err_lower:
            alt_path = f"{path.rsplit('.',1)[0]}_{uuid.uuid4().hex[:6]}.{path.rsplit('.',1)[-1]}" if "." in path else f"{path}_{uuid.uuid4().hex[:6]}"
            try:
                from app.database.connection import get_supabase_client

                client = get_supabase_client()
                client.storage.from_(target_bucket).upload(
                    path=alt_path,
                    file=data,
                    file_options={"content-type": content_type, "upsert": "false"},
                )
                path = alt_path
                logger.info("Retry upload succeeded for alternate path %s/%s", target_bucket, path)
            except Exception as retry_exc:
                if is_debug:
                    logger.warning("Supabase upload failed for %s (%s) — mock URL (DEBUG)", path, retry_exc)
                    return f"{supabase_url}/storage/v1/object/public/{target_bucket}/{path}"
                logger.error("Retry upload failed for %s/%s: %s", target_bucket, path, retry_exc)
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to upload to storage: {retry_exc}") from retry_exc
        else:
            if is_debug:
                logger.warning("Supabase upload failed for %s/%s (%s) — mock URL (DEBUG)", target_bucket, path, exc)
                return f"{supabase_url}/storage/v1/object/public/{target_bucket}/{path}"
            logger.error("Failed to upload %s/%s: %s", target_bucket, path, exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to upload to storage: {exc}") from exc

    # Get public URL
    try:
        from app.database.connection import get_supabase_client

        client = get_supabase_client()
        url = client.storage.from_(target_bucket).get_public_url(path)
        if isinstance(url, dict):
            public_url = url.get("publicUrl") or url.get("public_url") or str(url)
        else:
            public_url = str(url)
        if not public_url or public_url.strip().lower() in ("none", ""):
            raise ValueError("Empty public URL")
        return public_url
    except HTTPException:
        raise
    except Exception as exc:
        if is_debug:
            logger.warning("get_public_url failed for %s/%s (%s) — mock URL (DEBUG)", target_bucket, path, exc)
            return f"{supabase_url}/storage/v1/object/public/{target_bucket}/{path}"
        logger.error("Failed to get public URL for %s/%s: %s", target_bucket, path, exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Upload succeeded but failed to get public URL: {exc}") from exc


def _upload_as_user(bucket: str, access_token: str, files: list[tuple[str, bytes, str]]) -> list[str] | None:
    """
    Upload (path, data, content_type) files to Supabase Storage with the end user's access
    token, so storage RLS applies (users may write only under their own auth-uid folder).

    Returns public URLs in input order, or None if storage is unconfigured or rejects any upload.
    """
    import httpx

    from app.core.config import get_settings

    settings = get_settings()
    base_url = (settings.SUPABASE_URL or "").rstrip("/")
    api_key = settings.SUPABASE_KEY
    if not base_url or not api_key:
        return None

    urls: list[str] = []
    try:
        with httpx.Client(timeout=30) as client:
            for path, data, content_type in files:
                resp = client.post(
                    f"{base_url}/storage/v1/object/{bucket}/{path}",
                    headers={
                        "apikey": api_key,
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": content_type,
                        "x-upsert": "false",
                    },
                    content=data,
                )
                if resp.status_code >= 300:
                    logger.warning(
                        "Storage rejected upload %s/%s: HTTP %s %s", bucket, path, resp.status_code, resp.text[:200]
                    )
                    return None
                urls.append(f"{base_url}/storage/v1/object/public/{bucket}/{path}")
    except httpx.HTTPError as exc:
        logger.warning("Storage upload failed for bucket=%s: %s", bucket, exc)
        return None
    return urls


@router.post(
    "/enhance",
    summary="Enhance product image (background removal + CLAHE + compose on white)",
    description=(
        "Auth required. Form-data: image (file) + output_format ('1:1' or '4:5') + enhance (bool, default true). "
        "Validates file size, MIME, extension, path traversal, executable blocks, and dimensions "
        "BEFORE running pipeline. Uploads original + enhanced PNG/WebP + thumbnail to Supabase Storage. "
        "Returns public URLs (or the enhanced image inline as a data URL if storage rejects the upload)."
    ),
    status_code=200,
)
async def enhance_image(
    image: UploadFile = File(..., description="Image file (jpeg/png/webp, max 10MB)"),
    output_format: str = Form(default="1:1", description="Output aspect ratio: 1:1 or 4:5"),
    enhance: bool = Form(default=True, description="Run lighting/colour enhancement (background removal and framing always run)"),
    authorization: str | None = Header(default=None, include_in_schema=False),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    POST /api/v1/image/enhance

    Security validated first, then pipeline, then storage.

    Args:
        image: UploadFile (form-data)
        output_format: str Form field "1:1" | "4:5"
        current_user: dict from get_current_user (contains artisan, firebase_uid)

    Returns:
        JSON: { success, original_url, enhanced_url, thumbnail_url, width, height, ratio }
    """
    # ── Resolve artisan identity ───────────────────────────────────────
    artisan = current_user.get("artisan") or {}
    firebase_uid = current_user.get("firebase_uid") or artisan.get("firebase_uid") or "unknown"
    # artisan_id prefer DB id (uuid), fallback to firebase_uid
    artisan_id = artisan.get("id") or artisan.get("artisan_id") or firebase_uid
    if not artisan_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unable to resolve artisan identity")
    artisan_id_str = str(artisan_id).strip()
    # Guard: artisan_id should not contain path traversal
    if ".." in artisan_id_str or "/" in artisan_id_str or "\\" in artisan_id_str:
        logger.warning("Invalid artisan_id contains path traversal: %s", artisan_id_str)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid artisan identity")

    logger.info("Image enhance request artisan=%s output_format=%s file=%s ct=%s", artisan_id_str, output_format, image.filename, image.content_type)

    # ── SECURITY VALIDATION (must be done first, before pipeline) ───────

    # 1. Validate output_format early (cheap)
    if output_format not in ALLOWED_OUTPUT_FORMATS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid output_format '{output_format}'. Allowed: 1:1, 4:5",
        )

    # 2. Filename checks (before reading bytes)
    raw_filename = _sanitize_filename(image.filename)
    # Note: we never use raw_filename for storage; only for validation
    if not raw_filename:
        # Some clients send empty filename; still need to validate via MIME
        logger.debug("Uploaded file has empty filename — will validate via MIME only")
        raw_filename = "upload"

    # Path traversal guard on filename itself (reject "../" "/" "\")
    if ".." in raw_filename or "/" in raw_filename or "\\" in raw_filename:
        logger.warning("Path traversal detected in filename: %s", raw_filename)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid filename: path traversal detected")

    # Executable extension block (filename ends with .exe/.sh/.bat/.php/.js)
    lower_fname = raw_filename.lower().strip()
    for blocked in BLOCKED_EXTENSIONS:
        if lower_fname.endswith(blocked):
            logger.warning("Blocked executable extension in filename: %s", raw_filename)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Executable file type not allowed: {blocked}")

    # Also check double extension e.g., image.jpg.php
    # If any part after splitting by '.' contains blocked ext, reject
    parts = lower_fname.split(".")
    if len(parts) > 1:
        for p in parts[1:]:
            if p in BLOCKED_SUFFIXES:
                # But allow "jpg" etc — only block the blocked list
                logger.warning("Blocked executable suffix in filename parts: %s", raw_filename)
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Executable file type not allowed: .{p}")

    # 3. MIME validation
    content_type_raw = (image.content_type or "").strip()
    content_type = content_type_raw.lower()

    # Reject executable MIME
    if "executable" in content_type:
        logger.warning("Blocked executable MIME: %s", content_type_raw)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Executable MIME type not allowed")

    # Also if content_type contains blocked substrings like x-sh, etc. (paranoid)
    for blocked in BLOCKED_SUFFIXES:
        if f"application/x-{blocked}" in content_type or f"application/{blocked}" in content_type:
            logger.warning("Blocked application MIME with executable suffix: %s", content_type_raw)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Executable MIME not allowed: {content_type_raw}")

    # Allowed MIME allowlist
    if content_type not in ALLOWED_MIMES:
        logger.warning("Rejected MIME not in allowlist: '%s' filename=%s", content_type_raw, raw_filename)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{content_type_raw or 'unknown'}'. Allowed: jpeg, png, webp",
        )

    # 4. Extension allowlist (from filename or MIME)
    try:
        ext_original = _extract_extension(raw_filename if "." in raw_filename else None, content_type)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unable to determine file extension: {exc}") from exc

    # Additional extension guard: must be in allowed set (already checked, but double)
    if ext_original not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File extension '.{ext_original}' not allowed. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    # Also ensure filename extension if present is allowed (not just MIME)
    if "." in raw_filename:
        fname_ext = raw_filename.rsplit(".", 1)[-1].lower()
        if fname_ext == "jpeg":
            fname_ext = "jpg"
        # If filename has extension, it must be allowed; but we already allow via MIME fallback
        # If filename ext is present but not allowed (e.g., .bmp, .tiff), reject
        if fname_ext not in ALLOWED_EXTENSIONS and fname_ext not in ("jpeg", "jpg", "png", "webp"):
            # But if fname_ext is blocked executable already rejected; here reject other disallowed
            # Check: if filename has .bmp, that's not allowed even if MIME says jpeg (spoof)
            logger.warning("Filename extension '.%s' not allowed — rejecting (MIME=%s)", fname_ext, content_type)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File extension '.{fname_ext}' not allowed. Allowed: jpg, jpeg, png, webp",
            )

    # 5. Read bytes + file size check (10 MB -> 413)
    try:
        image_bytes = await image.read()
    except Exception as exc:
        logger.error("Failed to read uploaded file: %s", exc)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to read uploaded file: {exc}") from exc

    if not image_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty")

    if len(image_bytes) > MAX_FILE_SIZE_BYTES:
        logger.warning("Payload too large: %d bytes > %d", len(image_bytes), MAX_FILE_SIZE_BYTES)
        # Use 413 Content Too Large (new name) with fallback for older Starlette
        _413 = getattr(status, "HTTP_413_CONTENT_TOO_LARGE", 413)
        raise HTTPException(
            status_code=_413,
            detail=f"File too large ({len(image_bytes)} bytes). Maximum is 10 MB",
        )

    # 6. Decode validation + dimension check (100-6000, else 400)
    # This also ensures bytes are actually decodable as image
    try:
        w, h = _validate_dimensions_bytes(image_bytes)
        logger.debug("Validated dimensions %dx%d", w, h)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid image file: {exc}") from exc

    # All security checks passed — proceed to pipeline

    # ── PIPELINE ─────────────────────────────────────────────────────────
    try:
        logger.info("Running pipeline for artisan=%s format=%s bytes=%d", artisan_id_str, output_format, len(image_bytes))
        result: Dict[str, Any] = await process_image_pipeline(
            image_bytes=image_bytes,
            output_format=output_format,
            enhance=enhance,
        )
    except ValueError as ve:
        # Pipeline validation error (decode, dimensions, format) — map to 400
        logger.warning("Pipeline validation failed: %s", ve)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve)) from ve
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Pipeline unexpected failure: %s", exc, exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Image processing failed: {exc}") from exc

    # Extract results
    try:
        enhanced_bytes = result.get("enhanced_bytes")  # PNG
        webp_bytes = result.get("webp_bytes")  # WebP
        thumbnail_bytes = result.get("thumbnail_bytes")  # WebP thumb
        width = int(result.get("width") or 0)
        height = int(result.get("height") or 0)
        ratio = result.get("ratio") or output_format

        if not enhanced_bytes or not webp_bytes or not thumbnail_bytes:
            raise ValueError("Pipeline returned incomplete bytes (missing enhanced/webp/thumbnail)")

        if width == 0 or height == 0:
            # Fallback to decode enhanced_bytes to get dims if pipeline didn't return
            try:
                nparr = np.frombuffer(enhanced_bytes, np.uint8)
                img_check = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                if img_check is not None:
                    height, width = img_check.shape[:2]
            except Exception:
                width = width or 1080
                height = height or 1080

    except ValueError as ve:
        logger.error("Pipeline result incomplete: %s", ve)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(ve)) from ve
    except Exception as exc:
        logger.error("Failed to extract pipeline result: %s", exc, exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to process pipeline result: {exc}") from exc

    background_removed = bool(result.get("background_removed", False))

    # ── STORAGE: generate random UUID paths (never use filename) ────────
    bucket = _get_bucket_name()
    base = f"{artisan_id_str}/{uuid.uuid4().hex}"
    original_path = f"{base}_original.{ext_original}"
    enhanced_png_path = f"{base}_enhanced.png"
    enhanced_webp_path = f"{base}_enhanced.webp"
    thumb_path = f"{base}_thumb.webp"

    logger.info("Uploading to bucket=%s base=%s", bucket, base)

    # ── UPLOAD (original + enhanced PNG + WebP + thumbnail) ──────────────
    uploads = [
        ("original", original_path, image_bytes, MIME_TO_CONTENT_TYPE.get(ext_original, "image/jpeg")),
        ("enhanced PNG", enhanced_png_path, enhanced_bytes, "image/png"),
        ("enhanced WebP", enhanced_webp_path, webp_bytes, "image/webp"),
        ("thumbnail", thumb_path, thumbnail_bytes, "image/webp"),
    ]
    is_supabase_user = current_user.get("auth_provider") == "supabase"

    if is_supabase_user:
        # Upload as the user: storage RLS lets them write only under their own auth-uid folder,
        # which is artisan_id_str for Supabase users. No mock URLs — if storage rejects the
        # upload, the result is returned inline below instead.
        import asyncio

        urls = None
        scheme, _, access_token = (authorization or "").partition(" ")
        access_token = access_token.strip()
        if scheme.lower() == "bearer" and access_token:
            urls = await asyncio.to_thread(
                _upload_as_user, bucket, access_token, [(path, data, ct) for _, path, data, ct in uploads]
            )
        storage_uploaded = urls is not None
    else:
        urls = []
        for label, path, data, content_type in uploads:
            try:
                urls.append(_upload_bytes_with_fallback(bucket, path, data, content_type))
            except HTTPException:
                raise
            except Exception as exc:
                logger.error("%s upload failed: %s", label, exc, exc_info=True)
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to upload {label}: {exc}") from exc
        storage_uploaded = True

    original_url, enhanced_png_url, enhanced_webp_url, thumbnail_url = urls if urls else (None, None, None, None)
    # Prefer WebP for enhanced_url
    enhanced_url = enhanced_webp_url or enhanced_png_url
    if not storage_uploaded:
        enhanced_url = "data:image/webp;base64," + base64.b64encode(webp_bytes).decode("ascii")

    logger.info(
        "Enhance success artisan=%s %dx%d ratio=%s background_removed=%s stored=%s",
        artisan_id_str,
        width,
        height,
        ratio,
        background_removed,
        storage_uploaded,
    )

    # ── RESPONSE ─────────────────────────────────────────────────────────
    payload = {
        "original_url": original_url,
        "enhanced_url": enhanced_url,
        "enhanced_png_url": enhanced_png_url,
        "enhanced_webp_url": enhanced_webp_url,
        "thumbnail_url": thumbnail_url,
        "width": width,
        "height": height,
        "ratio": ratio,
        "bucket": bucket,
        "background_removed": background_removed,
        "storage_uploaded": storage_uploaded,
    }
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "message": "Image enhanced" if storage_uploaded else "Image enhanced (storage upload failed — image returned inline)",
            **payload,
            # Also include paths for debugging/audit (not required but helpful)
            "paths": {
                "original": original_path,
                "enhanced_png": enhanced_png_path,
                "enhanced_webp": enhanced_webp_path,
                "thumbnail": thumb_path,
            },
            # Same fields in the {success, message, data} envelope the mobile client parses.
            # Keep it flat: Android reads data as Map<String, String>.
            "data": payload,
        },
    )
