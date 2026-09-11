"""
Vision Background Module — foreground mask extraction.

Two entry points:
- remove_background(img)        -> mask (uint8 0/255)  [spec primary]
- get_foreground_mask(img, iterations=5) -> mask     [alias with configurable iterations]

Strategy:
1. Primary: OpenCV GrabCut, initialised with the product's estimated bounding box. The
   backdrop is modelled from the photo border as a few colour clusters (e.g. wall + table),
   with darker shades counted as backdrop so cast shadows aren't mistaken for the product.
   Backdrop-coloured fringe on the cut-out's edge (shadows, table) that connects to the real
   background is then stripped.
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

# GrabCut runs on a copy downscaled to this longest edge — full-resolution cuts are slow
GRABCUT_MAX_EDGE = 800
# Backdrop distance (see _backdrop_distance) below which a pixel reads as backdrop or its shadow
BACKDROP_MATCH = 14.0


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


def _backdrop_colors(lab: np.ndarray, k: int = 3) -> np.ndarray:
    """
    Model the backdrop from the photo border as up to k LAB colour clusters, so a two-tone
    setting (wall above, table below) is represented by both colours rather than one average.
    """
    h, w = lab.shape[:2]
    b = max(2, int(min(h, w) * 0.03))
    border = np.concatenate([
        lab[:b].reshape(-1, 3), lab[-b:].reshape(-1, 3),
        lab[:, :b].reshape(-1, 3), lab[:, -b:].reshape(-1, 3),
    ]).astype(np.float32)
    k = int(max(1, min(k, len(border) // 50)))
    if k == 1:
        return np.median(border, axis=0, keepdims=True)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
    _, _, centers = cv2.kmeans(border, k, None, criteria, 3, cv2.KMEANS_PP_CENTERS)
    return centers


def _backdrop_distance(lab: np.ndarray, colors: np.ndarray) -> np.ndarray:
    """
    Per-pixel distance to the nearest backdrop colour. Lightness differences count less than
    colour differences — and much less when the pixel is darker — so a cast shadow (same hue,
    lower lightness) still reads as backdrop.
    """
    best = np.full(lab.shape[:2], np.inf, dtype=np.float32)
    for c in colors:
        d_l = lab[:, :, 0] - c[0]
        l_weight = np.where(d_l < 0, 0.15, 0.6).astype(np.float32)
        dist = np.sqrt(l_weight * d_l ** 2 + (lab[:, :, 1] - c[1]) ** 2 + (lab[:, :, 2] - c[2]) ** 2)
        np.minimum(best, dist, out=best)
    return best


def _estimate_subject_rect(img: np.ndarray) -> Optional[tuple]:
    """
    Estimate the product's bounding box as the region that doesn't match the backdrop.

    Returns (x, y, w, h) kept at least 1px inside the frame so GrabCut still has
    background pixels outside it, or None when no distinct subject is found (e.g. a
    textile filling the whole photo).
    """
    h, w = img.shape[:2]
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB).astype(np.float32)
    dist = _backdrop_distance(lab, _backdrop_colors(lab))
    # Textured backdrops vary more — scale the threshold with the border's own spread
    b = max(2, int(min(h, w) * 0.03))
    border_dist = np.concatenate([dist[:b].ravel(), dist[-b:].ravel(), dist[:, :b].ravel(), dist[:, -b:].ravel()])
    threshold = max(BACKDROP_MATCH + 4.0, float(np.percentile(border_dist, 95)) * 1.5)
    diff = (dist > threshold).astype(np.uint8) * 255

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    diff = cv2.morphologyEx(diff, cv2.MORPH_OPEN, kernel)
    diff = cv2.morphologyEx(diff, cv2.MORPH_CLOSE, kernel, iterations=2)

    contours, _ = cv2.findContours(diff, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    min_area = 0.005 * h * w
    boxes = [cv2.boundingRect(c) for c in contours if cv2.contourArea(c) >= min_area]
    if not boxes:
        return None

    pad_x, pad_y = int(w * 0.04), int(h * 0.04)
    x0 = max(1, min(x for x, _, _, _ in boxes) - pad_x)
    y0 = max(1, min(y for _, y, _, _ in boxes) - pad_y)
    x1 = min(w - 1, max(x + bw for x, _, bw, _ in boxes) + pad_x)
    y1 = min(h - 1, max(y + bh for _, y, _, bh in boxes) + pad_y)
    if x1 - x0 < 2 or y1 - y0 < 2 or (x1 - x0) * (y1 - y0) > 0.96 * h * w:
        return None
    return (x0, y0, x1 - x0, y1 - y0)


def _keep_main_regions(mask: np.ndarray) -> np.ndarray:
    """Drop stray specks: keep connected regions at least 5% the size of the largest one."""
    n, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    if n <= 2:
        return mask
    areas = stats[1:, cv2.CC_STAT_AREA]
    keep = np.flatnonzero(areas >= 0.05 * areas.max()) + 1
    return np.where(np.isin(labels, keep), 255, 0).astype(np.uint8)


def _ellipse_kernel(radius: int) -> np.ndarray:
    size = 2 * max(1, radius) + 1
    return cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (size, size))


def _strip_backdrop_fringe(img: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """
    Remove shadows and backdrop that GrabCut left attached to the cut-out.

    Near the cut-out's edge, pixels that match the backdrop (a darker shade counts, so cast
    shadows match) are dropped when they connect to the real background. Colour alone can't
    do this — a basket's dark weave can be the same brown as a shadowed table — but backdrop-
    coloured patches enclosed by the product (weave cells, folds) aren't connected to the
    outside, so they stay. The product's core is never touched. Returns the input mask if
    the result looks wrong (too much removed).
    """
    fg = mask > 0
    fg_area = int(fg.sum())
    if fg_area < 400 or fg.all():
        return mask

    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB).astype(np.float32)
    backdrop_like = _backdrop_distance(lab, _backdrop_colors(lab)) <= BACKDROP_MATCH

    size = float(np.sqrt(fg_area))
    # Protected core = where the product's own (non-backdrop) colours are, with gaps between
    # them (dark weave cells) closed. Built from colour rather than by eroding the cut-out,
    # so a thick shadow attached to the cut-out can't end up inside the core.
    distinct = (fg & ~backdrop_like).astype(np.uint8) * 255
    distinct = cv2.morphologyEx(distinct, cv2.MORPH_CLOSE, _ellipse_kernel(max(2, int(size * 0.05))))
    core = cv2.erode(distinct, _ellipse_kernel(max(1, int(size * 0.02)))) > 0

    # 4-connectivity so weave/checker cells that touch only at corners stay separate
    candidate = ((backdrop_like & ~core) | ~fg).astype(np.uint8)
    _, labels = cv2.connectedComponents(candidate, connectivity=4)
    outside = np.unique(labels[~fg])
    reachable = np.isin(labels, outside[outside != 0])
    refined = (fg & ~reachable).astype(np.uint8) * 255

    removed = 1.0 - float(np.count_nonzero(refined)) / fg_area
    if removed > 0.35:
        logger.debug("fringe removal would drop %.0f%% of the cut-out — keeping GrabCut mask", removed * 100)
        return mask
    # Fill notches where weave cells on the product's own edge matched the backdrop
    refined = cv2.morphologyEx(refined, cv2.MORPH_CLOSE, _ellipse_kernel(max(2, int(size * 0.03))))
    refined = cv2.morphologyEx(refined, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
    return _keep_main_regions(refined)


def _grabcut_mask(img: np.ndarray, iterations: int = 5) -> Optional[np.ndarray]:
    """
    Try GrabCut and return mask (0/255) or None if failed/degenerate.

    Initialised with the estimated subject rectangle (falls back to a 5% inset), run on a
    copy downscaled to GRABCUT_MAX_EDGE, refined to strip shadow / backdrop fringe, then
    upscaled and cleaned of stray specks.
    """
    try:
        h, w = img.shape[:2]
        scale = min(1.0, GRABCUT_MAX_EDGE / float(max(h, w)))
        if scale < 1.0:
            small = cv2.resize(img, (max(10, int(w * scale)), max(10, int(h * scale))), interpolation=cv2.INTER_AREA)
        else:
            small = img
        sh, sw = small.shape[:2]

        rect = _estimate_subject_rect(small)
        if rect is None:
            # Define rect with 5% inset; ensure at least 1px border
            margin_x = max(1, int(sw * 0.05))
            margin_y = max(1, int(sh * 0.05))
            rect = (margin_x, margin_y, sw - 2 * margin_x, sh - 2 * margin_y)
        if rect[2] <= 0 or rect[3] <= 0:
            logger.warning("GrabCut rect degenerate: %s", rect)
            return None

        mask_gc = np.zeros((sh, sw), np.uint8)
        bgd_model = np.zeros((1, 65), np.float64)
        fgd_model = np.zeros((1, 65), np.float64)

        # GrabCut — this can be slow but accurate; iterations capped to 5 default
        cv2.grabCut(small, mask_gc, rect, bgd_model, fgd_model, int(iterations), cv2.GC_INIT_WITH_RECT)

        # Convert GrabCut mask: 0,2 = background, 1,3 = foreground
        mask = np.where((mask_gc == 2) | (mask_gc == 0), 0, 1).astype(np.uint8) * 255

        # Check degeneracy: if mask is all 0 or all 255, treat as failure
        fg_ratio = float(np.mean(mask == 255))
        if fg_ratio < 0.02 or fg_ratio > 0.98:
            logger.warning("GrabCut produced degenerate mask (fg_ratio=%.3f), falling back", fg_ratio)
            return None

        # Light morphology to clean GrabCut edges (small close), then remove isolated specks
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=1)
        mask = _keep_main_regions(mask)

        try:
            mask = _strip_backdrop_fringe(small, mask)
        except cv2.error as exc:
            logger.debug("fringe refinement skipped: %s", exc)

        if scale < 1.0:
            mask = cv2.resize(mask, (w, h), interpolation=cv2.INTER_LINEAR)
            mask = np.where(mask >= 128, 255, 0).astype(np.uint8)

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
