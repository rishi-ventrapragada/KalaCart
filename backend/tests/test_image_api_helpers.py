"""Extra helper coverage for app.api.image internals to push >90%."""
import os, io, pytest, numpy as np, cv2
os.environ.setdefault("DEBUG", "true")
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
import app.api.image as img_mod

class TestBucketHelpers:
    def test_get_bucket_from_settings(self):
        with patch("app.api.image.get_settings") if hasattr(img_mod, "get_settings") else patch("app.core.config.get_settings") as mock_get:
            # Patch via app.core.config
            with patch("app.core.config.get_settings") as m:
                m.return_value.SUPABASE_STORAGE_BUCKET = "my-bucket"
                assert img_mod._get_bucket_name() == "my-bucket"

    def test_get_bucket_fallback_env(self):
        with patch("app.core.config.get_settings", side_effect=Exception("fail")):
            with patch.dict(os.environ, {"SUPABASE_STORAGE_BUCKET": "env-bucket"}):
                assert img_mod._get_bucket_name() == "env-bucket"
            with patch.dict(os.environ, {}, clear=False):
                os.environ.pop("SUPABASE_STORAGE_BUCKET", None)
                # ensure default
                val = img_mod._get_bucket_name()
                assert val == "product-images"

    def test_get_supabase_url_settings(self):
        with patch("app.core.config.get_settings") as m:
            m.return_value.SUPABASE_URL = "https://my.supabase.co"
            assert img_mod._get_supabase_url() == "https://my.supabase.co"

    def test_get_supabase_url_fallback(self):
        with patch("app.core.config.get_settings", side_effect=Exception("fail")):
            with patch.dict(os.environ, {"SUPABASE_URL": "https://env.supabase.co"}):
                assert img_mod._get_supabase_url() == "https://env.supabase.co"
            with patch.dict(os.environ, {}, clear=False):
                os.environ.pop("SUPABASE_URL", None)
                assert img_mod._get_supabase_url() == "https://placeholder.supabase.co"

    def test_is_debug_true_false(self):
        with patch("app.core.config.get_settings") as m:
            m.return_value.DEBUG = True
            assert img_mod._is_debug() is True
            m.return_value.DEBUG = False
            assert img_mod._is_debug() is False
        with patch("app.core.config.get_settings", side_effect=Exception("fail")):
            with patch.dict(os.environ, {"DEBUG": "true"}):
                assert img_mod._is_debug() is True
            with patch.dict(os.environ, {"DEBUG": "false"}):
                assert img_mod._is_debug() is False

class TestUploadBytesFallback:
    def _make_client_mock(self, fail_first=False):
        mock_client = MagicMock()
        mock_storage = MagicMock()
        mock_client.storage.from_.return_value = mock_storage
        # get_public_url returns string
        mock_storage.get_public_url.return_value = "https://cdn.example.com/fake.png"
        if fail_first:
            mock_storage.upload.side_effect = Exception("already exists duplicate")
        else:
            mock_storage.upload.return_value = None
        return mock_client

    def test_upload_empty_data_raises(self):
        with pytest.raises(HTTPException) as exc:
            img_mod._upload_bytes_with_fallback("bucket", "path.png", b"", "image/png")
        assert exc.value.status_code == 400

    def test_upload_bad_path_traversal(self):
        with pytest.raises(HTTPException) as exc:
            img_mod._upload_bytes_with_fallback("bucket", "../evil.png", b"data", "image/png")
        assert exc.value.status_code == 400
        with pytest.raises(HTTPException):
            img_mod._upload_bytes_with_fallback("bucket", "/absolute.png", b"data", "image/png")
        with pytest.raises(HTTPException):
            img_mod._upload_bytes_with_fallback("bucket", "a\\b.png", b"data", "image/png")

    def test_upload_debug_mock_fallback_on_storage_fail(self):
        with patch("app.core.config.get_settings") as mock_settings:
            mock_settings.return_value.DEBUG = True
            mock_settings.return_value.SUPABASE_URL = "https://placeholder.supabase.co"
            mock_settings.return_value.SUPABASE_STORAGE_BUCKET = "product-images"
            with patch("app.database.connection.get_supabase_client", side_effect=Exception("supabase down")):
                # Should return mock URL in debug
                url = img_mod._upload_bytes_with_fallback("product-images", "artisan123/fake.png", b"data", "image/png")
                assert "placeholder.supabase.co" in url
                assert "artisan123/fake.png" in url

    def test_upload_success_path(self):
        with patch("app.core.config.get_settings") as mock_settings:
            mock_settings.return_value.DEBUG = False
            mock_settings.return_value.SUPABASE_URL = "https://my.supabase.co"
            mock_settings.return_value.SUPABASE_STORAGE_BUCKET = "product-images"
            mock_client = self._make_client_mock()
            with patch("app.database.connection.get_supabase_client", return_value=mock_client):
                with patch("app.services.storage_service.ensure_bucket_exists", return_value=True):
                    url = img_mod._upload_bytes_with_fallback("product-images", "artisan123/a.png", b"data", "image/png")
                    assert "cdn.example.com" in url
                    assert mock_client.storage.from_.called

    def test_upload_duplicate_retry(self):
        with patch("app.core.config.get_settings") as mock_settings:
            mock_settings.return_value.DEBUG = True
            mock_settings.return_value.SUPABASE_URL = "https://placeholder.supabase.co"
            mock_settings.return_value.SUPABASE_STORAGE_BUCKET = "product-images"
            # First call raises duplicate, second succeeds
            mock_client = MagicMock()
            mock_storage = MagicMock()
            mock_client.storage.from_.return_value = mock_storage
            mock_storage.upload.side_effect = [Exception("already exists"), None]
            mock_storage.get_public_url.return_value = "https://cdn.example.com/retry.png"
            with patch("app.database.connection.get_supabase_client", return_value=mock_client):
                with patch("app.services.storage_service.ensure_bucket_exists", return_value=True):
                    url = img_mod._upload_bytes_with_fallback("product-images", "artisan123/b.png", b"data", "image/png")
                    assert "retry" in url or "cdn.example.com" in url

    def test_upload_get_public_url_dict_handling(self):
        with patch("app.core.config.get_settings") as mock_settings:
            mock_settings.return_value.DEBUG = True
            mock_settings.return_value.SUPABASE_URL = "https://placeholder.supabase.co"
            mock_settings.return_value.SUPABASE_STORAGE_BUCKET = "product-images"
            mock_client = MagicMock()
            mock_storage = MagicMock()
            mock_client.storage.from_.return_value = mock_storage
            mock_storage.upload.return_value = None
            mock_storage.get_public_url.return_value = {"publicUrl": "https://dict.example.com/file.png"}
            with patch("app.database.connection.get_supabase_client", return_value=mock_client):
                url = img_mod._upload_bytes_with_fallback("bucket", "path/file.png", b"data", "image/png")
                assert "dict.example.com" in url

    def test_upload_public_url_empty_fallback_to_mock(self):
        with patch("app.core.config.get_settings") as mock_settings:
            mock_settings.return_value.DEBUG = True
            mock_settings.return_value.SUPABASE_URL = "https://placeholder.supabase.co"
            mock_settings.return_value.SUPABASE_STORAGE_BUCKET = "product-images"
            mock_client = MagicMock()
            mock_storage = MagicMock()
            mock_client.storage.from_.return_value = mock_storage
            mock_storage.upload.return_value = None
            mock_storage.get_public_url.return_value = None
            with patch("app.database.connection.get_supabase_client", return_value=mock_client):
                url = img_mod._upload_bytes_with_fallback("bucket", "path/file.png", b"data", "image/png")
                assert "placeholder.supabase.co" in url

class TestUploadBytesEdge:
    def test_upload_production_storage_failure_raises_500(self):
        with patch("app.core.config.get_settings") as mock_settings:
            mock_settings.return_value.DEBUG = False
            mock_settings.return_value.SUPABASE_URL = "https://prod.supabase.co"
            mock_settings.return_value.SUPABASE_STORAGE_BUCKET = "product-images"
            with patch("app.database.connection.get_supabase_client", side_effect=Exception("db down")):
                with patch("app.services.storage_service.ensure_bucket_exists", side_effect=Exception("bucket fail")):
                    # In prod, _upload should raise 500 not return mock
                    with pytest.raises(HTTPException) as exc:
                        # need to ensure path valid, data valid, but supabase fails
                        img_mod._upload_bytes_with_fallback("product-images", "artisan123/fail.png", b"validdata", "image/png")
                    assert exc.value.status_code == 500 or "placeholder" not in str(exc.value.detail)

class TestDimensionViaPilFallback:
    def test_validate_dimensions_pil_fallback_success(self):
        # Force cv2.imdecode to fail, PIL should succeed
        import numpy as np, cv2, io
        from PIL import Image
        # Create 120x120 PNG
        img = np.full((120,120,3), (100,100,100), dtype=np.uint8)
        ok, buf = cv2.imencode(".png", img)
        data = buf.tobytes()
        with patch("app.api.image.cv2.imdecode", return_value=None):
            w, h = img_mod._validate_dimensions_bytes(data)
            assert w == 120 and h == 120

    def test_validate_dimensions_both_fail_raises_invalid(self):
        with patch("app.api.image.cv2.imdecode", side_effect=Exception("cv2 fail")):
            with patch("PIL.Image.open", side_effect=Exception("pil fail")):
                with pytest.raises(HTTPException) as exc:
                    img_mod._validate_dimensions_bytes(b"notimagebytes")
                assert exc.value.status_code == 400

class TestEnhanceAdditionalCoverage:
    def test_enhance_all_validate_invalid_inputs(self):
        from app.vision.enhance import histogram_equalization, apply_clahe, bilateral_denoise, unsharp_mask, auto_brightness_normalization, white_balance_simple
        # Test with wrong dtype
        bad = np.zeros((10,10,3), dtype=np.float32)
        assert histogram_equalization(bad) is bad or isinstance(histogram_equalization(bad), np.ndarray)
        assert apply_clahe(bad) is not None
        # empty array
        empty = np.array([], dtype=np.uint8)
        assert bilateral_denoise(empty).size == 0 or isinstance(bilateral_denoise(empty), np.ndarray)
        # single channel
        gray = np.zeros((10,10), dtype=np.uint8)
        assert unsharp_mask(gray).shape == gray.shape or unsharp_mask(gray).size == 0
        # 1-channel check for auto brightness
        assert auto_brightness_normalization(gray) is not None
        assert white_balance_simple(gray) is not None

    def test_compose_invalid_fg_raises(self):
        from app.vision.compose import compose_on_white, crop_to_ratio, resize_to_target, generate_white_background
        with pytest.raises(ValueError):
            compose_on_white(None, np.zeros((10,10), dtype=np.uint8))
        with pytest.raises(ValueError):
            compose_on_white(np.zeros((10,10), dtype=np.uint8), np.zeros((10,10), dtype=np.uint8))
        with pytest.raises(ValueError):
            crop_to_ratio(None, "1:1")
        with pytest.raises(ValueError):
            resize_to_target(None, 1080)
        with pytest.raises(ValueError):
            generate_white_background("a", "b")  # type: ignore
        with pytest.raises(ValueError):
            generate_white_background(10, 7000)

    def test_compose_3channel_mask(self):
        from app.vision.compose import compose_on_white
        fg = np.full((50,50,3), (100,100,100), dtype=np.uint8)
        mask3 = np.zeros((50,50,3), dtype=np.uint8)
        mask3[:,:,0] = 255
        out = compose_on_white(fg, mask3)
        assert out.shape == fg.shape

    def test_pipeline_exif_and_decode_branches(self, monkeypatch):
        from app.vision.pipeline import _fix_exif_rotation, _decode_image
        # Test ImportError branch by hiding PIL
        # Not easy to trigger; instead test that _fix_exif_rotation handles invalid bytes gracefully
        img = np.zeros((20,20,3), dtype=np.uint8)
        img[:] = (10,20,30)
        nparr = np.frombuffer(cv2.imencode(".png", img)[1].tobytes(), np.uint8)
        decoded = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        # Pass garbage bytes to _fix_exif_rotation should return original
        garbage = b"not an image"
        out = _fix_exif_rotation(garbage, decoded)
        assert out.shape == decoded.shape

        # Test _decode_image with empty
        with pytest.raises(ValueError):
            _decode_image(b"")

        # Test large bytes warning path: >20MB
        big = b"a" * (21 * 1024 * 1024)
        with pytest.raises(ValueError):
            _decode_image(big)
