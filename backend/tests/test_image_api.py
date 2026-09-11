"""
API integration tests for POST /api/v1/image/enhance
Uses FastAPI TestClient with mocked auth and storage. Includes one real pipeline test.
"""
import io
import os
os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("APP_ENV", "development")
os.environ.setdefault("SUPABASE_URL", "https://placeholder.supabase.co")

import pytest
import numpy as np
import cv2
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.core.security import get_current_user

# ── Mock user ────────────────────────────────────────────────────────
MOCK_USER = {
    "firebase_uid": "test123",
    "artisan": {"id": "artisan123", "firebase_uid": "test123"},
    "claims": {}
}

def _override_get_current_user():
    return MOCK_USER

@pytest.fixture(autouse=True)
def setup_auth_override():
    app.dependency_overrides[get_current_user] = _override_get_current_user
    yield
    app.dependency_overrides[get_current_user] = _override_get_current_user

client = TestClient(app)

def make_png(w, h, color=(100,150,200)):
    img = np.full((h, w, 3), color, dtype=np.uint8)
    cv2.circle(img, (w//2, h//2), min(w,h)//4, (50, 180, 80), -1)
    ok, buf = cv2.imencode(".png", img)
    assert ok
    return buf.tobytes()

def make_jpeg(w, h):
    img = np.full((h, w, 3), (120,130,140), dtype=np.uint8)
    ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 85])
    assert ok
    return buf.tobytes()

# Fake pipeline result
def fake_pipeline_result(fmt="1:1"):
    # Minimal fake PNG/WebP bytes that are valid (use real encode for width/height)
    if fmt == "1:1":
        w, h = 1080, 1080
    else:
        w, h = 864, 1080
    fake_img = np.full((h, w, 3), (255,255,255), dtype=np.uint8)
    ok, png_buf = cv2.imencode(".png", fake_img)
    assert ok
    ok2, webp_buf = cv2.imencode(".webp", fake_img, [cv2.IMWRITE_WEBP_QUALITY, 85])
    if not ok2:
        # fallback via PIL
        from PIL import Image
        pil = Image.fromarray(cv2.cvtColor(fake_img, cv2.COLOR_BGR2RGB))
        out = io.BytesIO()
        pil.save(out, format="WEBP", quality=85)
        webp_bytes = out.getvalue()
    else:
        webp_bytes = webp_buf.tobytes()
    # thumbnail 256 long edge
    thumb = cv2.resize(fake_img, (256, 256), interpolation=cv2.INTER_AREA) if fmt=="1:1" else cv2.resize(fake_img, (205, 256), interpolation=cv2.INTER_AREA)
    ok3, thumb_buf = cv2.imencode(".webp", thumb, [cv2.IMWRITE_WEBP_QUALITY, 80])
    if not ok3:
        from PIL import Image
        pil2 = Image.fromarray(cv2.cvtColor(thumb, cv2.COLOR_BGR2RGB))
        out2 = io.BytesIO()
        pil2.save(out2, format="WEBP", quality=80)
        thumb_bytes = out2.getvalue()
    else:
        thumb_bytes = thumb_buf.tobytes()
    return {
        "original_bytes": b"orig",
        "enhanced_bytes": png_buf.tobytes(),
        "webp_bytes": webp_bytes,
        "thumbnail_bytes": thumb_bytes,
        "width": w,
        "height": h,
        "ratio": fmt,
    }

FAKE_URL = "https://placeholder.supabase.co/storage/v1/object/public/product-images/artisan123/fake.webp"

# Helper to get auth header (dependency override makes it optional but we send for completeness)
AUTH_HEADER = {"Authorization": "Bearer fake-jwt-for-test"}


class TestEnhanceSuccess:
    @patch("app.api.image._upload_bytes_with_fallback", return_value=FAKE_URL)
    @patch("app.api.image.process_image_pipeline")
    def test_enhance_success_1_1(self, mock_pipeline, mock_upload):
        mock_pipeline.return_value = fake_pipeline_result("1:1")
        png = make_png(100, 100)
        resp = client.post(
            "/api/v1/image/enhance",
            files={"image": ("photo.png", png, "image/png")},
            data={"output_format": "1:1"},
            headers=AUTH_HEADER,
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["success"] is True
        assert "original_url" in data
        assert "thumbnail_url" in data
        assert "width" in data and "height" in data
        assert data["width"] == 1080
        assert data["height"] == 1080
        assert data["ratio"] == "1:1"
        # Check that pipeline called with correct format
        mock_pipeline.assert_called_once()
        assert mock_pipeline.call_args.kwargs.get("output_format") == "1:1" or mock_pipeline.call_args.args[1] == "1:1"

    @patch("app.api.image._upload_bytes_with_fallback", return_value=FAKE_URL)
    @patch("app.api.image.process_image_pipeline")
    def test_enhance_success_4_5(self, mock_pipeline, mock_upload):
        mock_pipeline.return_value = fake_pipeline_result("4:5")
        png = make_png(120, 120)
        resp = client.post(
            "/api/v1/image/enhance",
            files={"image": ("product.webp", png, "image/webp")},
            data={"output_format": "4:5"},
            headers=AUTH_HEADER,
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["success"] is True
        assert data["width"] == 864
        assert data["height"] == 1080
        assert data["ratio"] == "4:5"
        assert "thumbnail_url" in data
        assert "original_url" in data

    def test_enhance_integration_real_pipeline(self):
        """One integration test with real pipeline on synthetic image (no mocks except storage)."""
        with patch("app.api.image._upload_bytes_with_fallback", return_value=FAKE_URL):
            png = make_png(300, 300)
            resp = client.post(
                "/api/v1/image/enhance",
                files={"image": ("real.png", png, "image/png")},
                data={"output_format": "1:1"},
                headers=AUTH_HEADER,
            )
            assert resp.status_code == 200, resp.text
            data = resp.json()
            assert data["width"] == 1080
            assert data["height"] == 1080
            # Verify URLs are placeholder mock
            assert "placeholder.supabase.co" in data["original_url"]

    @patch("app.api.image._upload_bytes_with_fallback", return_value=FAKE_URL)
    @patch("app.api.image.process_image_pipeline")
    def test_enhance_jpeg_accepts(self, mock_pipeline, mock_upload):
        mock_pipeline.return_value = fake_pipeline_result("1:1")
        jpg = make_jpeg(200, 200)
        resp = client.post(
            "/api/v1/image/enhance",
            files={"image": ("photo.jpg", jpg, "image/jpeg")},
            data={"output_format": "1:1"},
            headers=AUTH_HEADER,
        )
        assert resp.status_code == 200


class TestEnhanceReject:
    def test_reject_large_file(self):
        # Create >10MB payload; content is valid mime but exceeds size before decode
        big = b"\xff\xd8\xff" + b"a" * (10 * 1024 * 1024 + 5)  # 10MB+5
        resp = client.post(
            "/api/v1/image/enhance",
            files={"image": ("big.jpg", big, "image/jpeg")},
            data={"output_format": "1:1"},
            headers=AUTH_HEADER,
        )
        assert resp.status_code == 413, resp.text
        assert "too large" in resp.text.lower() or "10 mb" in resp.text.lower()

    def test_reject_invalid_mime(self):
        png = make_png(100, 100)
        resp = client.post(
            "/api/v1/image/enhance",
            files={"image": ("doc.txt", b"hello world text", "text/plain")},
            data={"output_format": "1:1"},
            headers=AUTH_HEADER,
        )
        assert resp.status_code == 400
        assert "unsupported" in resp.text.lower() or "allowed" in resp.text.lower()

    def test_reject_executable_mime(self):
        # Use application/x-sh and filename with .sh to trigger both checks
        resp = client.post(
            "/api/v1/image/enhance",
            files={"image": ("evil.sh", b"#!/bin/bash\necho hi", "application/x-sh")},
            data={"output_format": "1:1"},
            headers=AUTH_HEADER,
        )
        assert resp.status_code == 400
        assert "executable" in resp.text.lower() or "not allowed" in resp.text.lower()

    def test_reject_executable_mime_with_executable_substring(self):
        # MIME containing "executable"
        png = make_png(100, 100)
        resp = client.post(
            "/api/v1/image/enhance",
            files={"image": ("photo.png", png, "application/x-executable")},
            data={"output_format": "1:1"},
            headers=AUTH_HEADER,
        )
        assert resp.status_code == 400

    def test_reject_path_traversal(self):
        png = make_png(100, 100)
        resp = client.post(
            "/api/v1/image/enhance",
            files={"image": ("../../etc/passwd", png, "image/png")},
            data={"output_format": "1:1"},
            headers=AUTH_HEADER,
        )
        assert resp.status_code == 400
        assert "traversal" in resp.text.lower() or "invalid filename" in resp.text.lower()

    def test_reject_path_traversal_slash(self):
        png = make_png(100, 100)
        resp = client.post(
            "/api/v1/image/enhance",
            files={"image": ("a/b/c.jpg", png, "image/jpeg")},
            data={"output_format": "1:1"},
            headers=AUTH_HEADER,
        )
        assert resp.status_code == 400

    def test_reject_invalid_dimensions_small(self):
        # 50x50 should be rejected (min 100)
        tiny = make_png(50, 50)
        resp = client.post(
            "/api/v1/image/enhance",
            files={"image": ("tiny.png", tiny, "image/png")},
            data={"output_format": "1:1"},
            headers=AUTH_HEADER,
        )
        assert resp.status_code == 400
        assert "too small" in resp.text.lower()

    def test_reject_invalid_dimensions_via_monkeypatch_pipeline(self, monkeypatch):
        # Monkeypatch pipeline to simulate returning 50x50 invalid? Actually API validates before pipeline,
        # so we monkeypatch _validate_dimensions_bytes to raise, but easier: patch pipeline to raise ValueError 50x50
        async def fake_bad_pipeline(image_bytes, output_format="1:1", enhance=True):
            raise ValueError("Image too small: 50x50 — minimum is 100x100")
        monkeypatch.setattr("app.api.image.process_image_pipeline", fake_bad_pipeline)
        png = make_png(100, 100)  # valid size passes validate, but pipeline raises
        resp = client.post(
            "/api/v1/image/enhance",
            files={"image": ("ok.png", png, "image/png")},
            data={"output_format": "1:1"},
            headers=AUTH_HEADER,
        )
        assert resp.status_code == 400
        assert "too small" in resp.text.lower() or "minimum" in resp.text.lower()

    def test_reject_blocked_extension_exe(self):
        png = make_png(100, 100)
        resp = client.post(
            "/api/v1/image/enhance",
            files={"image": ("malware.exe", png, "image/jpeg")},
            data={"output_format": "1:1"},
            headers=AUTH_HEADER,
        )
        assert resp.status_code == 400

    def test_reject_double_extension_php(self):
        png = make_png(100, 100)
        resp = client.post(
            "/api/v1/image/enhance",
            files={"image": ("image.jpg.php", png, "image/jpeg")},
            data={"output_format": "1:1"},
            headers=AUTH_HEADER,
        )
        assert resp.status_code == 400

    def test_reject_invalid_mime_bmp(self):
        png = make_png(100, 100)
        resp = client.post(
            "/api/v1/image/enhance",
            files={"image": ("photo.bmp", png, "image/bmp")},
            data={"output_format": "1:1"},
            headers=AUTH_HEADER,
        )
        assert resp.status_code == 400

    def test_reject_invalid_output_format(self):
        png = make_png(100, 100)
        resp = client.post(
            "/api/v1/image/enhance",
            files={"image": ("photo.png", png, "image/png")},
            data={"output_format": "16:9"},
            headers=AUTH_HEADER,
        )
        assert resp.status_code == 400
        assert "invalid output_format" in resp.text.lower() or "allowed" in resp.text.lower()

    def test_reject_empty_file(self):
        resp = client.post(
            "/api/v1/image/enhance",
            files={"image": ("empty.png", b"", "image/png")},
            data={"output_format": "1:1"},
            headers=AUTH_HEADER,
        )
        assert resp.status_code == 400

    def test_reject_undecodable_bytes(self):
        resp = client.post(
            "/api/v1/image/enhance",
            files={"image": ("fake.png", b"not an image at all", "image/png")},
            data={"output_format": "1:1"},
            headers=AUTH_HEADER,
        )
        assert resp.status_code == 400

    def test_unauthorized_no_header(self):
        # Temporarily remove override to test 401
        app.dependency_overrides.pop(get_current_user, None)
        try:
            png = make_png(100, 100)
            # No Authorization header -> should be 401 due to get_current_user
            # need client without override
            from fastapi.testclient import TestClient as TC
            c2 = TC(app)
            resp = c2.post(
                "/api/v1/image/enhance",
                files={"image": ("photo.png", png, "image/png")},
                data={"output_format": "1:1"},
            )
            assert resp.status_code == 401, resp.text
            assert "authorization" in resp.text.lower() or "missing" in resp.text.lower()
        finally:
            app.dependency_overrides[get_current_user] = _override_get_current_user

    def test_invalid_content_type_traversal_in_storage_path_blocked(self):
        # Ensure storage path validation works via _upload fallback mock not needed
        # Just verify API rejects when artisan_id contains traversal (mock user with bad id)
        bad_user = {"firebase_uid": "../evil", "artisan": {"id": "../evil"}, "claims": {}}
        app.dependency_overrides[get_current_user] = lambda: bad_user
        try:
            png = make_png(100, 100)
            resp = client.post(
                "/api/v1/image/enhance",
                files={"image": ("photo.png", png, "image/png")},
                data={"output_format": "1:1"},
                headers=AUTH_HEADER,
            )
            assert resp.status_code == 400
        finally:
            app.dependency_overrides[get_current_user] = _override_get_current_user


class TestStorageFallbackAndArtisanResolve:
    @patch("app.api.image._upload_bytes_with_fallback")
    @patch("app.api.image.process_image_pipeline")
    def test_storage_called_four_times(self, mock_pipeline, mock_upload):
        mock_pipeline.return_value = fake_pipeline_result("1:1")
        mock_upload.return_value = FAKE_URL
        png = make_png(100, 100)
        resp = client.post(
            "/api/v1/image/enhance",
            files={"image": ("photo.png", png, "image/png")},
            data={"output_format": "1:1"},
            headers=AUTH_HEADER,
        )
        assert resp.status_code == 200
        # original + enhanced png + webp + thumb = 4 uploads
        assert mock_upload.call_count == 4

    @patch("app.api.image._upload_bytes_with_fallback", return_value=FAKE_URL)
    @patch("app.api.image.process_image_pipeline")
    def test_firebase_uid_fallback_when_artisan_missing(self, mock_pipeline, mock_upload):
        mock_pipeline.return_value = fake_pipeline_result("1:1")
        user_no_artisan_id = {"firebase_uid": "uid999", "artisan": {}, "claims": {}}
        app.dependency_overrides[get_current_user] = lambda: user_no_artisan_id
        try:
            png = make_png(100, 100)
            resp = client.post(
                "/api/v1/image/enhance",
                files={"image": ("x.png", png, "image/png")},
                data={"output_format": "1:1"},
                headers=AUTH_HEADER,
            )
            assert resp.status_code == 200
        finally:
            app.dependency_overrides[get_current_user] = _override_get_current_user
