"""
Conftest: shared fixtures for KalaCart image module tests.
Provides synthetic image generators via cv2/numpy/PIL without external files.
"""
import os

# Ensure DEBUG mode for mock Supabase fallback paths
os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("APP_ENV", "development")
os.environ.setdefault("SUPABASE_URL", "https://placeholder.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "dummy_anon_key_for_testing")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "dummy_service_role_key_for_testing")
os.environ.setdefault("SUPABASE_STORAGE_BUCKET", "product-images")

import io
import numpy as np
import cv2
import pytest
from PIL import Image


@pytest.fixture
def tiny_png_100():
    """Return 100x100 PNG bytes (minimum valid dims)."""
    img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    ok, buf = cv2.imencode(".png", img)
    assert ok
    return buf.tobytes()


@pytest.fixture
def tiny_png_120x120():
    img = np.zeros((120, 120, 3), dtype=np.uint8)
    img[:] = (180, 120, 60)
    cv2.circle(img, (60, 60), 30, (50, 200, 50), -1)
    ok, buf = cv2.imencode(".png", img)
    assert ok
    return buf.tobytes()


@pytest.fixture
def tiny_jpeg_100():
    img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 90])
    assert ok
    return buf.tobytes()


@pytest.fixture
def small_50_png():
    """50x50 invalid (too small) per spec."""
    img = np.zeros((50, 50, 3), dtype=np.uint8)
    img[:] = (100, 100, 100)
    ok, buf = cv2.imencode(".png", img)
    assert ok
    return buf.tobytes()


@pytest.fixture
def medium_png_800x600():
    img = np.random.randint(0, 255, (600, 800, 3), dtype=np.uint8)
    ok, buf = cv2.imencode(".png", img)
    assert ok
    return buf.tobytes()


@pytest.fixture
def synthetic_product_image():
    """Create a realistic synthetic product-like image (300x400) for pipeline integration."""
    h, w = 400, 300
    img = np.full((h, w, 3), 245, dtype=np.uint8)  # near-white background
    # Draw product rectangle centered
    cv2.rectangle(img, (80, 100), (220, 320), (90, 60, 180), -1)
    cv2.circle(img, (150, 200), 40, (40, 180, 120), -1)
    # Add noise texture
    noise = np.random.randint(-10, 10, (h, w, 3), dtype=np.int16)
    img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    ok, buf = cv2.imencode(".png", img)
    assert ok
    return buf.tobytes()


def make_png_bytes(w: int, h: int, color=(128, 128, 128)) -> bytes:
    """Helper not a fixture: generate w x h PNG bytes with solid color."""
    img = np.full((h, w, 3), color, dtype=np.uint8)
    ok, buf = cv2.imencode(".png", img)
    assert ok
    return buf.tobytes()


def make_jpeg_bytes(w: int, h: int, color=(128, 128, 128), quality=85) -> bytes:
    img = np.full((h, w, 3), color, dtype=np.uint8)
    ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, quality])
    assert ok
    return buf.tobytes()


@pytest.fixture
def mock_artisan_user():
    return {
        "firebase_uid": "test123",
        "artisan": {"id": "artisan123", "firebase_uid": "test123"},
        "claims": {}
    }
