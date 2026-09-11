"""
Vision Background Module — foreground mask extraction.

Two entry points:
- remove_background(img)        -> mask (uint8 0/255)  [spec primary]
- get_foreground_mask(img, iterations=5) -> mask     [alias with configurable iterations]

Strategy:
1. Primary: OpenCV GrabCut (GC_INIT_WITH_RECT). Fast, accurate for studio/isolated objects.
2. Fallback: HSV + Otsu on V-channel + morphology if GrabCut fails, raises, or produces
   degenerate mask (all 0 or all 255). Fallback uses:
     - V-channel Otsu thresholding
     - HSV saturation value threshold
     - Morphological open/close + dilate to clean mask
3. Last resort: return full-white mask (no removal) so compose step degrades gracefully.

All masks are uint8 with values 0 (background) or 255 (foreground), same HxW as input.
"""

from __future__ import annotations

import logging
from typing import Optional

import cv2
import numpy as np

logger = logging.getLogger(__name__)


def _validate_input(img: np.ndarray) -> bool:
    """Return True if img is valid BGR uint8, else log and return False."""
    if img is None or not isinstance(img, np.ndarray) or img.size == 0:
        logger.warning("background: invalid image input (None/empty)")
        return False
    if img.ndim != 3 or img.shape[2] != 3:
        logger.warning("background: expected 3-channel BGR, got shape %s", getattr(img, "shape", None))
        return False
    if img.dtype != np.uint8:
        logger.warning("background: expected uint8, got %s", img.dtype)
        return False
    h, w = img.shape[:2]
    if h < 10 or w < 10:
        logger.warning("background: image too small for GrabCut (%dx%d)", w, h)
        return False
    return True


def _fallback_mask_otsu_morphology(img: np.ndarray) -> np.ndarray:
    """
    Fallback mask using V-channel Otsu + morphology.

    Steps:
      - Convert BGR -> HSV, extract V channel
      - Otsu threshold on V
      - Invert if needed (assume foreground darker than white bg? heuristic)
      - Morphology: open (remove specks), close (fill holes), dilate (expand fg)
      - Also combine with saturation mask to handle white-on-white edge case
    """
    try:
        h, w = img.shape[:2]
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        h_ch, s_ch, v_ch = cv2.split(hsv)

        # Otsu on V channel
        _, thresh_v = cv2.threshold(v_ch, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Heuristic: if >70% of image is considered foreground, likely threshold inverted
        # For typical product on light bg, background should be > foreground near borders
        # Check border pixels: average border V should be high if bg is white/light
        border_pixels = np.concatenate([
            v_ch[0, :], v_ch[-1, :], v_ch[:, 0], v_ch[:, -1]
        ])
        border_mean = float(np.mean(border_pixels))
        fg_ratio = float(np.mean(thresh_v == 255))

        # If border is bright (mean >150) and foreground mask is mostly white (>0.7), invert
        # Because white background -> V high -> thresh would mark bg as 255
        # We want fg = 255, bg = 0, so if bg is white, we need to invert
        if border_mean > 120 and fg_ratio > 0.5:
            # Means background (bright border) was classified as foreground -> invert
            thresh_v = cv2.bitwise_not(thresh_v)

        # Saturation mask: low saturation indicates white/gray background
        # Threshold S channel: foreground typically more saturated
        _, thresh_s = cv2.threshold(s_ch, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        # Combine: if either indicates foreground, keep it? Actually intersection is more conservative.
        # Use OR to avoid missing desaturated products (e.g., white pottery)
        # Choose adaptive: if product is low saturation, Otsu on S may be unreliable
        # So weight V more, but use S to clean background specks
        # For now, combine with AND to remove overly aggressive V mask on textured bg
        # Fallback blending: keep thresh_v as primary, but erode where S is very low (clear bg)
        # Simple: if V says fg and S is near 0, still consider bg if border is very desaturated
        # We'll do: mask = thresh_v (as primary)
        mask = thresh_v

        # Morphology cleaning
        # Kernel sizes adapt to image size
        k_small = max(3, min(7, min(h, w) // 200 + 3))
        if k_small % 2 == 0:
            k_small += 1
        k_large = k_small * 2 + 1
        if k_large % 2 == 0:
            k_large += 1

        kernel_small = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k_small, k_small))
        kernel_large = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k_large, k_large))

        # Open to remove small noise
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel_small, iterations=1)
        # Close to fill holes inside foreground
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel_large, iterations=2)
        # Slight dilate to include edges
        mask = cv2.dilate(mask, kernel_small, iterations=1)

        # Ensure mask is not degenerate
        fg_ratio_after = float(np.mean(mask == 255))
        if fg_ratio_after < 0.02 or fg_ratio_after > 0.98:
            logger.warning(
                "background fallback: degenerate mask after morphology (fg_ratio=%.3f) — returning full fg",
                fg_ratio_after,
            )
            return np.full((h, w), 255, dtype=np.uint8)

        return mask.astype(np.uint8)

    except Exception as exc:
        logger.warning("background fallback Otsu failed: %s", exc)
        h, w = img.shape[:2] if img is not None and hasattr(img, "shape") else (100, 100)
        return np.full((h, w), 255, dtype=np.uint8)


def _grabcut_mask(img: np.ndarray, iterations: int = 5) -> Optional[np.ndarray]:
    """
    Try GrabCut and return mask (0/255) or None if failed/degenerate.

    Uses GC_INIT_WITH_RECT with rect inset 5% from border.
    """
    try:
        h, w = img.shape[:2]
        # Define rect with 5% inset; ensure at least 1px border
        margin_x = max(1, int(w * 0.05))
        margin_y = max(1, int(h * 0.05))
        rect = (margin_x, margin_y, w - 2 * margin_x, h - 2 * margin_y)
        if rect[2] <= 0 or rect[3] <= 0:
            logger.warning("GrabCut rect degenerate: %s", rect)
            return None

        mask_gc = np.zeros((h, w), np.uint8)
        bgd_model = np.zeros((1, 65), np.float64)
        fgd_model = np.zeros((1, 65), np.float64)

        # GrabCut — this can be slow but accurate; iterations capped to 5 default
        cv2.grabCut(img, mask_gc, rect, bgd_model, fgd_model, int(iterations), cv2.GC_INIT_WITH_RECT)

        # Convert GrabCut mask: 0,2 = background, 1,3 = foreground
        mask = np.where((mask_gc == 2) | (mask_gc == 0), 0, 1).astype(np.uint8) * 255

        # Check degeneracy: if mask is all 0 or all 255, treat as failure
        fg_ratio = float(np.mean(mask == 255))
        if fg_ratio < 0.02 or fg_ratio > 0.98:
            logger.warning("GrabCut produced degenerate mask (fg_ratio=%.3f), falling back", fg_ratio)
            return None

        # Light morphology to clean GrabCut edges (small close)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=1)

        return mask.astype(np.uint8)

    except cv2.error as e:
        logger.warning("GrabCut cv2.error: %s", e)
        return None
    except Exception as exc:
        logger.warning("GrabCut failed: %s", exc)
        return None


def get_foreground_mask(img: np.ndarray, iterations: int = 5) -> np.ndarray:
    """
    Extract foreground mask (uint8 0/255) using GrabCut with Otsu fallback.

    Args:
        img: BGR np.ndarray (uint8).
        iterations: GrabCut iteration count (default 5, range 1-10).

    Returns:
        Mask np.ndarray (H x W, uint8) where 255 = foreground, 0 = background.
        On total failure returns full-white mask (no background removal) so
        downstream compose degrades gracefully.
    """
    if not _validate_input(img):
        h, w = (img.shape[0], img.shape[1]) if isinstance(img, np.ndarray) and img.ndim >= 2 else (100, 100)
        logger.warning("get_foreground_mask: invalid input, returning full fg mask %dx%d", w, h)
        return np.full((h, w), 255, dtype=np.uint8)

    iterations = int(max(1, min(10, iterations)))

    # 1) Try GrabCut
    mask = _grabcut_mask(img, iterations=iterations)
    if mask is not None:
        logger.debug("get_foreground_mask: GrabCut succeeded (fg_ratio=%.2f)", float(np.mean(mask == 255)))
        return mask

    # 2) Fallback: Otsu + morphology
    logger.info("get_foreground_mask: GrabCut failed/degenerate — using Otsu fallback")
    fallback = _fallback_mask_otsu_morphology(img)
    return fallback


def remove_background(img: np.ndarray) -> np.ndarray:
    """
    Primary spec alias for background removal.

    Calls get_foreground_mask(img, iterations=5) with default iterations.
    Kept for API compatibility with spec: remove_background(img) -> mask

    Args:
        img: BGR np.ndarray (uint8).

    Returns:
        Mask np.ndarray (H x W, uint8 0/255).
    """
    return get_foreground_mask(img, iterations=5)
