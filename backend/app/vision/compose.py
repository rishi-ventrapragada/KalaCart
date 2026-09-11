"""
Vision Compose Module — white studio background + ratio handling.

Functions:
- generate_white_background(width, height) -> white BGR image
- compose_on_white(foreground, mask, bg_color) -> composite with feathered edges
- crop_to_ratio(img, ratio "1:1" | "4:5") -> centered crop/pad to target ratio
- resize_to_target(img, target=1080) -> resize to 1080x1080 (1:1) or 864x1080 (4:5)

Handles edge cases: mismatched dimensions, invalid ratios, single-channel inputs.
"""

from __future__ import annotations

import logging
from typing import Tuple

import cv2
import numpy as np

logger = logging.getLogger(__name__)

# Allowed ratios — extendable if needed
ALLOWED_RATIOS = {"1:1", "4:5"}
# Map ratio string -> aspect (width/height)
RATIO_ASPECT: dict[str, float] = {"1:1": 1.0, "4:5": 4.0 / 5.0}  # 0.8
# Target sizes
TARGET_SIZE_1_1: Tuple[int, int] = (1080, 1080)  # (w, h)
TARGET_SIZE_4_5: Tuple[int, int] = (864, 1080)   # (w, h)


def generate_white_background(width: int, height: int) -> np.ndarray:
    """
    Create a white BGR image of given size.

    Args:
        width: Width in pixels (1..6000).
        height: Height in pixels (1..6000).

    Returns:
        BGR uint8 image filled with (255,255,255).

    Raises:
        ValueError if dimensions are out of range.
    """
    if not isinstance(width, int) or not isinstance(height, int):
        raise ValueError(f"Width/height must be int, got {type(width)}/{type(height)}")
    if width <= 0 or height <= 0:
        raise ValueError(f"Width/height must be >0, got {width}x{height}")
    # Clamp to pipeline max to avoid OOM
    if width > 6000 or height > 6000:
        raise ValueError(f"Dimensions too large: {width}x{height} (max 6000)")
    if width < 1 or height < 1:
        raise ValueError(f"Dimensions too small: {width}x{height}")

    return np.full((height, width, 3), 255, dtype=np.uint8)


def compose_on_white(
    foreground: np.ndarray,
    mask: np.ndarray,
    bg_color: Tuple[int, int, int] = (255, 255, 255),
) -> np.ndarray:
    """
    Composite foreground onto solid background using feathered mask.

    Feathering: Gaussian blur on mask (kernel ~21) to soften hard GrabCut edges,
    then alpha blend: result = fg * alpha + bg * (1 - alpha).

    Args:
        foreground: BGR uint8 image (H x W x 3).
        mask: Single-channel uint8 mask (H x W) 0=bg, 255=fg. If None or shape mismatch,
              feathered copy is created or foreground is returned unchanged.
        bg_color: BGR background color tuple (default white).

    Returns:
        BGR uint8 composited image same size as foreground.
    """
    if foreground is None or not isinstance(foreground, np.ndarray) or foreground.size == 0:
        raise ValueError("compose_on_white: foreground is None/empty")
    if foreground.ndim != 3 or foreground.shape[2] != 3:
        raise ValueError(f"compose_on_white: foreground expected 3-channel BGR, got {foreground.shape}")
    h, w = foreground.shape[:2]

    # Validate mask
    use_mask = None
    if mask is None:
        logger.warning("compose_on_white: mask is None — returning foreground unchanged")
        return foreground.copy()
    if not isinstance(mask, np.ndarray):
        logger.warning("compose_on_white: mask not ndarray (%s) — returning foreground", type(mask))
        return foreground.copy()
    if mask.size == 0:
        logger.warning("compose_on_white: empty mask — returning foreground")
        return foreground.copy()

    # Handle mask dimensionality: if 3-channel, convert to single channel
    if mask.ndim == 3:
        if mask.shape[2] == 3:
            mask = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)
        elif mask.shape[2] == 1:
            mask = mask[:, :, 0]
        else:
            logger.warning("compose_on_white: unexpected mask channels %s", mask.shape)
            return foreground.copy()

    # Resize mask if mismatch
    if mask.shape[0] != h or mask.shape[1] != w:
        logger.warning(
            "compose_on_white: mask shape %s != foreground %s — resizing mask",
            mask.shape, (h, w)
        )
        try:
            mask = cv2.resize(mask, (w, h), interpolation=cv2.INTER_NEAREST)
        except Exception as exc:
            logger.warning("compose_on_white: mask resize failed: %s — returning foreground", exc)
            return foreground.copy()

    # Normalize mask to uint8 0-255 if needed
    if mask.dtype != np.uint8:
        # If mask is 0-1 float, scale
        if mask.dtype in (np.float32, np.float64):
            mask = np.clip(mask * 255, 0, 255).astype(np.uint8)
        else:
            mask = mask.astype(np.uint8)
    # Binarize-ish: ensure 0-255 but keep feathered range
    # If mask is already 0/1, convert to 0/255
    if mask.max() <= 1 and mask.dtype == np.uint8:
        mask = (mask * 255).astype(np.uint8)

    try:
        # Feather mask edges via Gaussian blur — kernel size adaptive but fixed 21 for soft edges
        # Small masks (<100px) use smaller kernel to avoid over-blur
        ksize = 21
        if min(h, w) < 100:
            ksize = 5
        elif min(h, w) < 300:
            ksize = 11
        # Ensure odd
        if ksize % 2 == 0:
            ksize += 1

        # Use BORDER_REPLICATE to avoid dark border artifacts
        feathered = cv2.GaussianBlur(mask, (ksize, ksize), sigmaX=0, borderType=cv2.BORDER_REPLICATE)

        # Normalize to 0.0-1.0 float
        alpha = feathered.astype(np.float32) / 255.0
        # Expand to 3 channels
        alpha_3 = np.stack([alpha, alpha, alpha], axis=-1)  # H x W x 3

        # Background image
        bg = np.full_like(foreground, bg_color, dtype=np.uint8)
        bg_f = bg.astype(np.float32)
        fg_f = foreground.astype(np.float32)

        # Alpha blend
        composited_f = fg_f * alpha_3 + bg_f * (1.0 - alpha_3)
        composited = np.clip(composited_f, 0, 255).astype(np.uint8)
        return composited

    except Exception as exc:
        logger.warning("compose_on_white: blending failed: %s — returning foreground", exc)
        return foreground.copy()


def crop_to_ratio(img: np.ndarray, ratio: str = "1:1") -> np.ndarray:
    """
    Crop (and pad if needed) image to target aspect ratio, centered.

    - ratio "1:1" -> square crop centered (1.0)
    - ratio "4:5" -> width:height = 0.8, if image is wider than 0.8 crop width,
      if taller, crop height; if image is too narrow to crop (e.g., very tall thin strip),
      pad with white to reach ratio instead of over-cropping.

    Padding with white is used when centered crop would require negative crop
    (i.e., image already has smaller aspect than target and cropping would enlarge).

    Args:
        img: BGR uint8 image (H x W x 3).
        ratio: "1:1" or "4:5".

    Returns:
        BGR image with aspect exactly target (within 1px).

    Raises:
        ValueError if ratio is unsupported or img invalid.
    """
    if img is None or not isinstance(img, np.ndarray) or img.size == 0:
        raise ValueError("crop_to_ratio: img is None/empty")
    if img.ndim != 3 or img.shape[2] != 3:
        raise ValueError(f"crop_to_ratio: expected BGR 3-channel, got shape {img.shape}")
    if ratio not in ALLOWED_RATIOS:
        raise ValueError(f"Unsupported ratio '{ratio}'. Allowed: {ALLOWED_RATIOS}")

    h, w = img.shape[:2]
    target_aspect = RATIO_ASPECT[ratio]  # w/h
    current_aspect = w / float(h) if h != 0 else 1.0

    # If already very close (within 0.01), return copy
    if abs(current_aspect - target_aspect) < 0.01:
        return img.copy()

    try:
        if current_aspect > target_aspect:
            # Image is wider than target -> crop width, keep full height
            # New width = h * target_aspect
            new_w = int(round(h * target_aspect))
            new_w = max(1, min(w, new_w))
            x0 = (w - new_w) // 2
            cropped = img[:, x0 : x0 + new_w]
            # If cropped width is still not exactly target due to rounding, pad 1px white if needed
            # Actually aspect will be new_w / h
            return cropped

        else:
            # Image is taller/narrower than target -> need wider image
            # Usually we would crop height: new_h = w / target_aspect
            # But if image is very narrow (current_aspect << target), cropping height would be small
            # and lose content. Alternative for 4:5 vs 1:1: pad width with white instead of cropping height.
            # Heuristic: if current_aspect < target_aspect and ratio == "4:5":
            #   Pad width rather than crop height when the difference is significant and height is large
            # For spec compliance: "pad with white if needed" — we pad when cropping would enlarge beyond original.
            # Here we choose to pad width with white to reach target aspect, preserving all content.
            # Compute desired width for current height: desired_w = h * target_aspect
            # If desired_w > w, pad; else crop height.
            desired_w = int(round(h * target_aspect))
            if desired_w > w:
                # Need to pad width with white
                pad_total = desired_w - w
                pad_left = pad_total // 2
                pad_right = pad_total - pad_left
                padded = cv2.copyMakeBorder(
                    img, 0, 0, pad_left, pad_right,
                    borderType=cv2.BORDER_CONSTANT, value=(255, 255, 255)
                )
                return padded
            else:
                # Crop height (centered)
                new_h = int(round(w / target_aspect))
                new_h = max(1, min(h, new_h))
                y0 = (h - new_h) // 2
                cropped = img[y0 : y0 + new_h, :]
                return cropped

    except Exception as exc:
        logger.warning("crop_to_ratio failed (%s): %s — returning original", ratio, exc)
        return img.copy()


def crop_to_subject(
    img: np.ndarray,
    mask: np.ndarray,
    ratio: str = "1:1",
    margin: float = 0.10,
) -> np.ndarray:
    """
    Frame the product: crop to the target ratio around the mask's bounding box, leaving
    `margin` of empty space on the tighter side, and pad with white where the frame
    extends past the photo. Intended for images already composed on white.

    Falls back to crop_to_ratio when the mask is missing, mismatched or empty.

    Args:
        img: BGR uint8 image (H x W x 3), background already white.
        mask: Single-channel uint8 mask (H x W), 255 = product.
        ratio: "1:1" or "4:5".
        margin: Fraction of the frame kept empty on each side of the product (0-0.4).

    Returns:
        BGR image with aspect exactly target (within 1px).
    """
    if img is None or not isinstance(img, np.ndarray) or img.size == 0:
        raise ValueError("crop_to_subject: img is None/empty")
    if img.ndim != 3 or img.shape[2] != 3:
        raise ValueError(f"crop_to_subject: expected BGR 3-channel, got shape {img.shape}")
    if ratio not in ALLOWED_RATIOS:
        raise ValueError(f"Unsupported ratio '{ratio}'. Allowed: {ALLOWED_RATIOS}")

    h, w = img.shape[:2]
    if mask is None or not isinstance(mask, np.ndarray) or mask.shape[:2] != (h, w):
        return crop_to_ratio(img, ratio)
    ys, xs = np.nonzero(mask > 127)
    if xs.size == 0:
        return crop_to_ratio(img, ratio)

    aspect = RATIO_ASPECT[ratio]
    fill = 1.0 - 2.0 * float(max(0.0, min(0.4, margin)))
    x0, x1 = int(xs.min()), int(xs.max()) + 1
    y0, y1 = int(ys.min()), int(ys.max()) + 1

    # Frame height that fits the product at `fill` in both dimensions — but never tiny,
    # so a small detected region isn't blown up into a blurry close-up
    frame_h = int(round(max((y1 - y0) / fill, (x1 - x0) / fill / aspect, 0.4 * min(h, w))))
    frame_w = max(1, int(round(frame_h * aspect)))

    left = int(round((x0 + x1) / 2.0 - frame_w / 2.0))
    top = int(round((y0 + y1) / 2.0 - frame_h / 2.0))

    canvas = np.full((frame_h, frame_w, 3), 255, dtype=np.uint8)
    sx0, sy0 = max(0, left), max(0, top)
    sx1, sy1 = min(w, left + frame_w), min(h, top + frame_h)
    if sx1 > sx0 and sy1 > sy0:
        canvas[sy0 - top : sy1 - top, sx0 - left : sx1 - left] = img[sy0:sy1, sx0:sx1]
    return canvas


def resize_to_target(img: np.ndarray, target: int = 1080) -> np.ndarray:
    """
    Resize image to studio target resolution while preserving aspect.

    - For 1:1 input (aspect ~1.0):  target x target (e.g., 1080x1080)
    - For 4:5 input (aspect ~0.8):  864 x 1080  (int(target*0.8) x target)
    - Fallback for other aspects: height = target, width = round(target * aspect) clipped,
      then aspect ratio preserved via cv2.resize.

    Uses INTER_AREA for downscale and INTER_CUBIC for upscale for quality.

    Args:
        img: BGR uint8 image (H x W x 3).
        target: Long-edge target (default 1080).

    Returns:
        Resized BGR uint8 image.

    Raises:
        ValueError if img invalid.
    """
    if img is None or not isinstance(img, np.ndarray) or img.size == 0:
        raise ValueError("resize_to_target: img is None/empty")
    if img.ndim != 3 or img.shape[2] != 3:
        raise ValueError(f"resize_to_target: expected BGR 3-channel, got {img.shape}")
    if not isinstance(target, int) or target <= 0 or target > 6000:
        raise ValueError(f"resize_to_target: invalid target {target} (1..6000)")

    h, w = img.shape[:2]
    aspect = w / float(h) if h != 0 else 1.0

    # Determine target size
    if abs(aspect - 1.0) < 0.05:
        # Squareish -> 1:1
        dst_w, dst_h = target, target
    elif abs(aspect - 0.8) < 0.06:
        # 4:5ish
        dst_w, dst_h = int(round(target * 0.8)), target
        # Ensure exact spec sizes for canonical ratios
        if aspect == 0.8 or abs(aspect - 0.8) < 0.02:
            dst_w, dst_h = 864, 1080 if target == 1080 else (int(round(target * 0.8)), target)
    else:
        # Generic: keep height = target, compute width to preserve aspect
        # But if image is landscape (aspect >1), keep width = target instead
        if aspect >= 1.0:
            # Landscape or square: width = target
            dst_w = target
            dst_h = int(round(target / aspect))
        else:
            # Portrait: height = target
            dst_h = target
            dst_w = int(round(target * aspect))
        dst_w = max(1, dst_w)
        dst_h = max(1, dst_h)

    # If already at target, return copy to avoid interpolation artifacts
    if h == dst_h and w == dst_w:
        return img.copy()

    try:
        # Choose interpolation
        if dst_w * dst_h < w * h:
            interp = cv2.INTER_AREA  # downscale
        else:
            interp = cv2.INTER_CUBIC  # upscale

        resized = cv2.resize(img, (dst_w, dst_h), interpolation=interp)
        return resized
    except Exception as exc:
        logger.warning("resize_to_target failed: %s — returning original", exc)
        return img.copy()
