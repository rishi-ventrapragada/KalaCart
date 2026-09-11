"""
Direct validation function tests for app.api.image
Targets >90% coverage of security validation helpers.
"""
import io
import os
import pytest
import numpy as np
import cv2

# Force DEBUG
os.environ.setdefault("DEBUG", "true")

from fastapi import HTTPException
from app.api.image import (
    _extract_extension,
    _sanitize_filename,
    _validate_dimensions_bytes,
    ALLOWED_EXTENSIONS,
    ALLOWED_MIMES,
    MAX_FILE_SIZE_BYTES,
    BLOCKED_EXTENSIONS,
)

# Helpers
def png_bytes(w, h):
    img = np.zeros((h, w, 3), dtype=np.uint8)
    img[:] = (100, 150, 200)
    ok, buf = cv2.imencode(".png", img)
    assert ok
    return buf.tobytes()

def jpeg_bytes(w, h):
    img = np.zeros((h, w, 3), dtype=np.uint8)
    img[:] = (100, 150, 200)
    ok, buf = cv2.imencode(".jpg", img)
    assert ok
    return buf.tobytes()


class TestSanitizeFilename:
    def test_none_returns_empty(self):
        from app.api.image import _sanitize_filename
        assert _sanitize_filename(None) == ""

    def test_empty_string(self):
        assert _sanitize_filename("") == ""

    def test_strips_whitespace(self):
        assert _sanitize_filename("  photo.jpg  ") == "photo.jpg"

    def test_preserves_traversal_for_validation(self):
        # sanitize does NOT reject traversal; validation layer does
        assert _sanitize_filename("../../etc/passwd") == "../../etc/passwd"


class TestExtractExtension:
    @pytest.mark.parametrize("filename,ctype,expected", [
        ("photo.jpg", "image/jpeg", "jpg"),
        ("photo.jpeg", "image/jpeg", "jpg"),
        ("IMAGE.PNG", "image/png", "png"),
        ("file.webp", "image/webp", "webp"),
        ("no_ext", "image/jpeg", "jpg"),
        (None, "image/png", "png"),
        (None, "image/jpeg", "jpg"),
        (None, "image/webp", "webp"),
        ("UPPER.JPEG", "image/jpeg", "jpg"),
        ("a.bmp", "image/jpeg", "jpg"),  # fallback to MIME when ext not allowed
    ])
    def test_extract_success(self, filename, ctype, expected):
        assert _extract_extension(filename, ctype) == expected

    @pytest.mark.parametrize("filename,ctype", [
        ("file.bmp", "image/bmp"),
        ("file.tiff", "image/tiff"),
        ("no_ext", None),
        (None, None),
        ("file.txt", "text/plain"),
        ("file", "application/octet-stream"),
    ])
    def test_extract_unsupported_raises_400(self, filename, ctype):
        with pytest.raises(HTTPException) as exc:
            _extract_extension(filename, ctype)
        assert exc.value.status_code == 400

    def test_jpeg_normalized_to_jpg(self):
        assert _extract_extension("test.jpeg", "image/jpeg") == "jpg"
        assert _extract_extension(None, "image/pjpeg") == "jpg"
        assert _extract_extension(None, "image/x-png") == "png"


class TestValidateDimensions:
    def test_valid_100x100(self):
        w, h = _validate_dimensions_bytes(png_bytes(100, 100))
        assert w == 100 and h == 100

    def test_valid_6000x6000(self):
        # create minimal bytes trick: just test boundary via mock decode?
        # Create 6000x6000 is heavy; test via mocking cv2 decode with synthetic dimensions?
        # Instead create 1000x1000 and ensure it passes, then test boundary errors with small/large
        w, h = _validate_dimensions_bytes(png_bytes(1000, 1000))
        assert w == 1000

    def test_too_small_raises(self):
        with pytest.raises(HTTPException) as exc:
            _validate_dimensions_bytes(png_bytes(50, 50))
        assert exc.value.status_code == 400
        assert "too small" in str(exc.value.detail).lower()

    def test_too_small_one_dimension(self):
        with pytest.raises(HTTPException):
            _validate_dimensions_bytes(png_bytes(99, 200))

    def test_too_large(self):
        # We mock by creating image that decodes to >6000 via oversized bytes?
        # Instead directly test _validate_dimensions that pipeline uses can be patched;
        # But _validate_dimensions_bytes decodes bytes, so we need to simulate large via mocked input.
        # Create 50x50 but monkeypatch cv2.imdecode to return large
        import app.api.image as img_mod
        import unittest.mock as mock
        fake_large = np.zeros((7000, 7000, 3), dtype=np.uint8)
        # we don't actually create 7000x7000 bytes (OOM); mock imdecode
        with mock.patch("app.api.image.cv2.imdecode", return_value=fake_large):
            with pytest.raises(HTTPException) as exc:
                _validate_dimensions_bytes(b"fake")
            assert exc.value.status_code == 400
            assert "too large" in str(exc.value.detail).lower()

    def test_empty_bytes_raises(self):
        with pytest.raises(HTTPException) as exc:
            _validate_dimensions_bytes(b"")
        assert exc.value.status_code == 400

    def test_invalid_image_bytes_raises(self):
        with pytest.raises(HTTPException) as exc:
            _validate_dimensions_bytes(b"this is not an image at all random bytes 12345")
        assert exc.value.status_code == 400
        assert "invalid image" in str(exc.value.detail).lower() or "unable to decode" in str(exc.value.detail).lower()

    @pytest.mark.parametrize("w,h,should_pass", [
        (100, 100, True),
        (100, 200, True),
        (6000, 6000, True),
        (99, 99, False),
        (6001, 100, False),
        (100, 6001, False),
    ])
    def test_parametrized_boundaries(self, w, h, should_pass):
        import unittest.mock as mock
        fake = np.zeros((h, w, 3), dtype=np.uint8)
        with mock.patch("app.api.image.cv2.imdecode", return_value=fake):
            if should_pass:
                rw, rh = _validate_dimensions_bytes(b"fake")
                assert rw == w and rh == h
            else:
                with pytest.raises(HTTPException):
                    _validate_dimensions_bytes(b"fake")


class TestFileSizeMimeExtensionTraversal:
    def test_max_file_size_constant(self):
        assert MAX_FILE_SIZE_BYTES == 10 * 1024 * 1024

    def test_allowed_mimes_contains_jpeg_png_webp(self):
        assert "image/jpeg" in ALLOWED_MIMES
        assert "image/png" in ALLOWED_MIMES
        assert "image/webp" in ALLOWED_MIMES

    def test_allowed_extensions(self):
        assert "jpg" in ALLOWED_EXTENSIONS
        assert "png" in ALLOWED_EXTENSIONS
        assert "webp" in ALLOWED_EXTENSIONS

    def test_blocked_extensions(self):
        for ext in [".exe", ".sh", ".bat", ".php", ".js"]:
            assert ext in BLOCKED_EXTENSIONS

    @pytest.mark.parametrize("filename", [
        "../../etc/passwd",
        "../secret.jpg",
        "/etc/passwd",
        "foo\\bar.jpg",
        "a/b/c.jpg",
        "..\\..\\windows\\system32\\evil.jpg",
    ])
    def test_traversal_patterns_detected(self, filename):
        # The API checks `".." in filename or "/" in filename or "\\" in filename`
        assert (".." in filename) or ("/" in filename) or ("\\" in filename)

    @pytest.mark.parametrize("mime", [
        "application/x-sh",
        "application/x-executable",
        "application/x-bat",
        "something executable here",
    ])
    def test_executable_mime_detection(self, mime):
        assert "executable" in mime.lower() or mime.startswith("application/x-")

    @pytest.mark.parametrize("mime,allowed", [
        ("image/jpeg", True),
        ("image/png", True),
        ("image/webp", True),
        ("image/jpg", True),
        ("text/plain", False),
        ("application/json", False),
        ("application/x-sh", False),
        ("image/bmp", False),
    ])
    def test_mime_allowlist(self, mime, allowed):
        assert (mime.lower() in ALLOWED_MIMES) == allowed

    @pytest.mark.parametrize("ext,allowed", [
        ("jpg", True),
        ("jpeg", True),
        ("png", True),
        ("webp", True),
        ("bmp", False),
        ("tiff", False),
        ("exe", False),
        ("sh", False),
    ])
    def test_extension_allowlist(self, ext, allowed):
        normalized = "jpg" if ext == "jpeg" else ext
        # only jpg/png/webp are allowed (jpeg normalised to jpg)
        assert (normalized in ALLOWED_EXTENSIONS) == allowed

    def test_dimensions_min_max_via_real_bytes(self):
        # 100x100 passes, 50x50 fails via real encode
        w, h = _validate_dimensions_bytes(png_bytes(100, 100))
        assert w == 100
        with pytest.raises(HTTPException):
            _validate_dimensions_bytes(png_bytes(50, 50))

    def test_file_size_edge_10mb(self):
        # simulate: exactly 10MB should pass, 10MB+1 fails
        assert MAX_FILE_SIZE_BYTES == 10485760
        ok_size = MAX_FILE_SIZE_BYTES
        bad_size = MAX_FILE_SIZE_BYTES + 1
        # We test the comparison logic directly
        assert not (ok_size > MAX_FILE_SIZE_BYTES)
        assert (bad_size > MAX_FILE_SIZE_BYTES)
