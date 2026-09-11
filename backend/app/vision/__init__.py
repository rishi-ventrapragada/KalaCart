"""
KalaCart Vision Pipeline — AI Image Enhancement

Exports for backend/app/vision:
- enhance.py:  histogram_equalization, apply_clahe, bilateral_denoise, unsharp_mask,
               auto_brightness_normalization, white_balance_simple, enhance_image
- background.py: remove_background, get_foreground_mask
- compose.py:  generate_white_background, compose_on_white, crop_to_ratio, resize_to_target
- pipeline.py: process_image_pipeline (main async orchestrator)

Usage:
    from app.vision import process_image_pipeline, enhance_image
    from app.vision.background import get_foreground_mask
    from app.vision.compose import compose_on_white, crop_to_ratio

No secrets are hardcoded; all thresholds are configurable via function args.
"""

from app.vision.background import get_foreground_mask, remove_background
from app.vision.compose import (
    compose_on_white,
    crop_to_ratio,
    generate_white_background,
    resize_to_target,
)
from app.vision.enhance import (
    apply_clahe,
    auto_brightness_normalization,
    bilateral_denoise,
    enhance_image,
    histogram_equalization,
    unsharp_mask,
    white_balance_simple,
)
from app.vision.pipeline import process_image_pipeline

__all__ = [
    # enhance
    "histogram_equalization",
    "apply_clahe",
    "bilateral_denoise",
    "unsharp_mask",
    "auto_brightness_normalization",
    "white_balance_simple",
    "enhance_image",
    # background
    "remove_background",
    "get_foreground_mask",
    # compose
    "generate_white_background",
    "compose_on_white",
    "crop_to_ratio",
    "resize_to_target",
    # pipeline
    "process_image_pipeline",
]

__version__ = "1.0.0"
