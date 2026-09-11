"""
Vision Enhance Module — modular OpenCV enhancements.

All functions accept BGR np.ndarray (as from cv2.imdecode) and return BGR np.ndarray.
Graceful edge-case handling: None / empty / wrong dtype returns input or raises ValueError
where appropriate, never crashes the pipeline.

Functions:
- histogram_equalization: YCrCb Y-channel equalization
- apply_clahe: LAB L-channel CLAHE
- bilateral_denoise: cv2.bilateralFilter
- unsharp_mask: Gaussian blur subtract sharpening
- auto_brightness_normalization: scale to target mean
- white_balance_simple: gray-world channel scaling
- enhance_image: orchestration

Dependencies: opencv-python (cv2), numpy, PIL (optional for fallback)
"""

from __future__ import annotations

import logging
from typing import Tuple

import cv2
import numpy as np

logger = logging.getLogger(__name__)


def _validate_bgr(img: np.ndarray) -> None:
    """Internal: validate that img is a 3-channel BGR uint8 array."""
    if img is None:
        raise ValueError("Image is None")
    if not isinstance(img, np.ndarray):
        raise ValueError(f"Expected np.ndarray, got {type(img)}")
    if img.size == 0:
        raise ValueError("Image array is empty")
    if img.ndim != 3 or img.shape[2] != 3:
        raise ValueError(f"Expected BGR image with 3 channels, got shape {img.shape}")
    if img.dtype != np.uint8:
        raise ValueError(f"Expected dtype uint8, got {img.dtype}")


# ── Individual operations ────────────────────────────────────────────

def histogram_equalization(img: np.ndarray) -> np.ndarray:
    """
    Apply histogram equalization on the Y channel of YCrCb.

    Args:
        img: BGR np.ndarray (uint8).

    Returns:
        BGR np.ndarray with equalized luminance.
    """
    try:
        _validate_bgr(img)
    except ValueError as e:
        logger.warning("histogram_equalization validation failed: %s — returning original", e)
        return img

    try:
        ycrcb = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
        y, cr, cb = cv2.split(ycrcb)
        y_eq = cv2.equalizeHist(y)
        merged = cv2.merge([y_eq, cr, cb])
        result = cv2.cvtColor(merged, cv2.COLOR_YCrCb2BGR)
        return result
    except Exception as exc:
        logger.warning("histogram_equalization failed: %s — returning original", exc)
        return img.copy()


def apply_clahe(
    img: np.ndarray,
    clipLimit: float = 2.0,
    tileGridSize: Tuple[int, int] = (8, 8),
) -> np.ndarray:
    """
    Apply CLAHE on L channel of LAB color space.

    Args:
        img: BGR np.ndarray (uint8).
        clipLimit: Threshold for contrast limiting (default 2.0).
        tileGridSize: Grid size for histogram equalization (default 8x8).

    Returns:
        BGR np.ndarray with local contrast enhancement.
    """
    try:
        _validate_bgr(img)
    except ValueError as e:
        logger.warning("apply_clahe validation failed: %s — returning original", e)
        return img

    try:
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=clipLimit, tileGridSize=tileGridSize)
        l_clahe = clahe.apply(l)
        merged = cv2.merge([l_clahe, a, b])
        result = cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)
        return result
    except Exception as exc:
        logger.warning("apply_clahe failed: %s — returning original", exc)
        return img.copy()


def bilateral_denoise(
    img: np.ndarray,
    d: int = 9,
    sigmaColor: float = 75,
    sigmaSpace: float = 75,
) -> np.ndarray:
    """
    Denoise while preserving edges using bilateral filter.

    Args:
        img: BGR np.ndarray (uint8).
        d: Diameter of pixel neighborhood (default 9).
        sigmaColor: Filter sigma in color space (default 75).
        sigmaSpace: Filter sigma in coordinate space (default 75).

    Returns:
        Denoised BGR np.ndarray.
    """
    try:
        _validate_bgr(img)
    except ValueError as e:
        logger.warning("bilateral_denoise validation failed: %s — returning original", e)
        return img

    try:
        # bilateralFilter expects appropriate sigma; clamp d to reasonable range
        d = int(max(1, min(15, d)))
        return cv2.bilateralFilter(img, d, sigmaColor, sigmaSpace)
    except Exception as exc:
        logger.warning("bilateral_denoise failed: %s — returning original", exc)
        return img.copy()


def unsharp_mask(
    img: np.ndarray,
    amount: float = 0.5,
    radius: float = 1.0,
    threshold: int = 0,
) -> np.ndarray:
    """
    Sharpen image via unsharp masking (original + amount * (original - blurred)).

    Args:
        img: BGR np.ndarray (uint8).
        amount: Sharpening strength (0.0-2.0, default 0.5).
        radius: Gaussian blur sigma (default 1.0). Kernel derived as (0,0) with sigma=radius.
        threshold: Minimum brightness difference to apply sharpening (0-255, 0=always).

    Returns:
        Sharpened BGR np.ndarray.
    """
    try:
        _validate_bgr(img)
    except ValueError as e:
        logger.warning("unsharp_mask validation failed: %s — returning original", e)
        return img

    try:
        amount = float(max(0.0, min(3.0, amount)))
        radius = float(max(0.1, min(10.0, radius)))
        threshold = int(max(0, min(255, threshold)))

        if amount == 0:
            return img.copy()

        # Gaussian blur — kernel (0,0) auto-computed from sigma=radius
        blurred = cv2.GaussianBlur(img, (0, 0), sigmaX=radius, sigmaY=radius)

        # Weighted addition: sharpened = (1+amount)*img - amount*blurred
        sharpened = cv2.addWeighted(img, 1.0 + amount, blurred, -amount, 0)

        # Threshold handling — only sharpen where difference exceeds threshold
        if threshold > 0:
            # Compute per-pixel difference magnitude
            diff = cv2.absdiff(img, blurred)
            # Convert to grayscale magnitude for thresholding
            diff_gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
            # Mask where difference is significant
            mask = diff_gray >= threshold
            # Expand mask to 3 channels
            mask_3 = np.stack([mask] * 3, axis=-1)
            # Where mask false, keep original; where true, use sharpened
            result = np.where(mask_3, sharpened, img)
            return result.astype(np.uint8)

        return sharpened
    except Exception as exc:
        logger.warning("unsharp_mask failed: %s — returning original", exc)
        return img.copy()


def auto_brightness_normalization(
    img: np.ndarray,
    target_mean: int = 180,
) -> np.ndarray:
    """
    Normalize image brightness to a target mean.

    Computes mean of grayscale, calculates scale factor to reach target_mean,
    applies scaling with clipping.

    Args:
        img: BGR np.ndarray (uint8).
        target_mean: Desired mean brightness (0-255, default 180 — studio bright).

    Returns:
        Brightness-normalized BGR np.ndarray.
    """
    try:
        _validate_bgr(img)
    except ValueError as e:
        logger.warning("auto_brightness_normalization validation failed: %s — returning original", e)
        return img

    try:
        target_mean = int(max(1, min(255, target_mean)))
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        current_mean = float(np.mean(gray))

        if current_mean < 1.0:
            logger.warning("auto_brightness_normalization: current_mean ~0 — skipping")
            return img.copy()

        # Avoid excessive scaling: clamp factor to [0.5, 2.5]
        scale = target_mean / current_mean
        scale = float(max(0.5, min(2.5, scale)))

        # If scale close to 1.0, skip to avoid unnecessary quantization
        if 0.95 <= scale <= 1.05:
            return img.copy()

        # Apply scale with clipping — use convertScaleAbs-style but preserve float then clip
        # alpha = scale, beta = 0
        result = cv2.convertScaleAbs(img, alpha=scale, beta=0)
        # Alternative high-quality: numpy multiply + clip
        # result = np.clip(img.astype(np.float32) * scale, 0, 255).astype(np.uint8)
        return result
    except Exception as exc:
        logger.warning("auto_brightness_normalization failed: %s — returning original", exc)
        return img.copy()


def white_balance_simple(img: np.ndarray) -> np.ndarray:
    """
    Simple gray-world white balance: scale each channel to global mean.

    Computes mean per channel (B, G, R), global mean = average of channel means,
    then scales each channel by global_mean / channel_mean.

    Args:
        img: BGR np.ndarray (uint8).

    Returns:
        White-balanced BGR np.ndarray.
    """
    try:
        _validate_bgr(img)
    except ValueError as e:
        logger.warning("white_balance_simple validation failed: %s — returning original", e)
        return img

    try:
        # Compute per-channel mean — avoid division by zero
        b_mean, g_mean, r_mean = cv2.mean(img)[:3]  # cv2.mean returns (B,G,R,alpha)
        # Alternative: np.mean(img.reshape(-1,3), axis=0)

        # Guard against zero means (e.g., completely black channel)
        if min(b_mean, g_mean, r_mean) < 1.0:
            logger.debug("white_balance_simple: channel mean near zero, skipping balance")
            return img.copy()

        global_mean = (b_mean + g_mean + r_mean) / 3.0
        if global_mean < 1.0:
            return img.copy()

        # Compute scale factors
        b_scale = global_mean / b_mean
        g_scale = global_mean / g_mean
        r_scale = global_mean / r_mean

        # Clamp scales to avoid color explosion — typical range [0.7, 1.4]
        b_scale = float(max(0.6, min(1.6, b_scale)))
        g_scale = float(max(0.6, min(1.6, g_scale)))
        r_scale = float(max(0.6, min(1.6, r_scale)))

        # If all scales near 1.0, already balanced
        if all(0.95 <= s <= 1.05 for s in (b_scale, g_scale, r_scale)):
            return img.copy()

        # Split and scale
        b, g, r = cv2.split(img)
        b = np.clip(b.astype(np.float32) * b_scale, 0, 255).astype(np.uint8)
        g = np.clip(g.astype(np.float32) * g_scale, 0, 255).astype(np.uint8)
        r = np.clip(r.astype(np.float32) * r_scale, 0, 255).astype(np.uint8)

        result = cv2.merge([b, g, r])
        return result
    except Exception as exc:
        logger.warning("white_balance_simple failed: %s — returning original", exc)
        return img.copy()


def enhance_image(img: np.ndarray) -> np.ndarray:
    """
    Orchestrate full enhancement pipeline.

    Order (as per spec):
        1. auto_brightness_normalization (target_mean=180)
        2. CLAHE (LAB L-channel)
        3. bilateral_denoise
        4. unsharp_mask + white_balance_simple

    Each step is wrapped in try/except so a single failure does not abort the chain.
    Returns enhanced BGR image. If all steps fail, returns a copy of original.

    Args:
        img: BGR np.ndarray (uint8).

    Returns:
        Enhanced BGR np.ndarray.
    """
    try:
        _validate_bgr(img)
    except ValueError as e:
        logger.warning("enhance_image: invalid input %s", e)
        # Return as-is if possible, otherwise raise
        if isinstance(img, np.ndarray) and img.size > 0:
            return img.copy() if img.dtype == np.uint8 else img
        raise

    result = img.copy()

    # Step 1: Brightness normalization — bring mean toward studio bright 180
    try:
        result = auto_brightness_normalization(result, target_mean=180)
    except Exception as exc:
        logger.warning("enhance_image: brightness step failed: %s", exc)

    # Step 2: CLAHE for local contrast
    try:
        result = apply_clahe(result, clipLimit=2.0, tileGridSize=(8, 8))
    except Exception as exc:
        logger.warning("enhance_image: CLAHE step failed: %s", exc)

    # Step 3: Denoise before sharpening (avoid amplifying noise)
    try:
        result = bilateral_denoise(result, d=9, sigmaColor=75, sigmaSpace=75)
    except Exception as exc:
        logger.warning("enhance_image: bilateral step failed: %s", exc)

    # Step 4a: Unsharp mask sharpening
    try:
        result = unsharp_mask(result, amount=0.5, radius=1.0, threshold=0)
    except Exception as exc:
        logger.warning("enhance_image: unsharp step failed: %s", exc)

    # Step 4b: White balance — after sharpening so colors are balanced last
    try:
        result = white_balance_simple(result)
    except Exception as exc:
        logger.warning("enhance_image: white_balance step failed: %s", exc)

    return result
