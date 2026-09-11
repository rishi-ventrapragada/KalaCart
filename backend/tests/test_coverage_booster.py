"""Coverage booster — hits defensive branches to push >85%+."""
import os, io, pytest, numpy as np, cv2
os.environ.setdefault("DEBUG","true")
from unittest.mock import patch, MagicMock

def solid(w,h):
    return np.full((h,w,3), (120,130,140), dtype=np.uint8)

class TestPipelineBooster:
    def test_fix_exif_import_error(self):
        from app.vision.pipeline import _fix_exif_rotation
        img = solid(20,20)
        decoded = cv2.imdecode(np.frombuffer(cv2.imencode(".png", img)[1].tobytes(), np.uint8), cv2.IMREAD_COLOR)
        # Simulate ImportError by patching PIL import to fail
        with patch.dict("sys.modules", {"PIL": None}):
            # Actually _fix_exif_rotation catches ImportError
            out = _fix_exif_rotation(b"fake", decoded)
            assert out.shape == decoded.shape

    def test_fix_exif_rgba_handling(self):
        from app.vision.pipeline import _fix_exif_rotation
        from PIL import Image
        # Create RGBA image bytes
        pil = Image.new("RGBA", (50,50), (255,0,0,128))
        buf = io.BytesIO()
        pil.save(buf, format="PNG")
        data = buf.getvalue()
        nparr = np.frombuffer(data, np.uint8)
        decoded = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        out = _fix_exif_rotation(data, decoded)
        assert out.shape[0]==50

    def test_decode_pil_fallback_after_cv2_fail(self):
        from app.vision.pipeline import _decode_image
        from PIL import Image
        # Create valid PNG bytes but force cv2.imdecode to return None
        img = solid(80,80)
        data = cv2.imencode(".png", img)[1].tobytes()
        with patch("app.vision.pipeline.cv2.imdecode", return_value=None):
            out = _decode_image(data)
            assert out.shape[0]==80

    def test_decode_both_fail_raises(self):
        from app.vision.pipeline import _decode_image
        with patch("app.vision.pipeline.cv2.imdecode", return_value=None):
            with patch("PIL.Image.open", side_effect=Exception("pil fail")):
                with pytest.raises(ValueError):
                    _decode_image(b"fakeimagebytes")

    def test_export_png_fallback(self):
        from app.vision.pipeline import _export_png
        img = solid(30,30)
        # Force cv2.imencode to fail
        with patch("app.vision.pipeline.cv2.imencode", return_value=(False, None)):
            data = _export_png(img)
            assert data[:8]==b"\x89PNG\r\n\x1a\n"

    def test_export_png_both_fail(self):
        from app.vision.pipeline import _export_png
        img = solid(20,20)
        with patch("app.vision.pipeline.cv2.imencode", side_effect=Exception("cv2 fail")):
            with patch("PIL.Image.fromarray", side_effect=Exception("pil fail")):
                with pytest.raises(RuntimeError):
                    _export_png(img)

    def test_export_webp_fallback(self):
        from app.vision.pipeline import _export_webp
        img = solid(30,30)
        with patch("app.vision.pipeline.cv2.imencode", return_value=(False, None)):
            data = _export_webp(img, quality=85)
            assert data[:4]==b"RIFF"

    def test_export_webp_both_fail(self):
        from app.vision.pipeline import _export_webp
        img = solid(20,20)
        with patch("app.vision.pipeline.cv2.imencode", side_effect=Exception("cv2 fail")):
            with patch("PIL.Image.fromarray", side_effect=Exception("pil fail")):
                with pytest.raises(RuntimeError):
                    _export_webp(img)

    def test_make_thumbnail_resize_fail(self):
        from app.vision.pipeline import _make_thumbnail
        img = solid(100,100)
        with patch("app.vision.pipeline.cv2.resize", side_effect=Exception("resize fail")):
            data = _make_thumbnail(img, thumb_long=256)
            assert data[:4]==b"RIFF"

    @pytest.mark.asyncio
    async def test_pipeline_background_fallback(self):
        from app.vision.pipeline import process_image_pipeline
        img = solid(120,120)
        data = cv2.imencode(".png", img)[1].tobytes()
        # Force background to return degenerate mask -> fallback to no removal
        with patch("app.vision.background.get_foreground_mask", return_value=np.zeros((120,120), dtype=np.uint8)):
            result = await process_image_pipeline(data, "1:1", enhance=False)
            assert result["width"]==1080

    @pytest.mark.asyncio
    async def test_pipeline_compose_fallback(self):
        from app.vision.pipeline import process_image_pipeline
        img = solid(120,120)
        data = cv2.imencode(".png", img)[1].tobytes()
        with patch("app.vision.compose.compose_on_white", side_effect=Exception("compose fail")):
            result = await process_image_pipeline(data, "1:1", enhance=False)
            assert result["width"]==1080

    @pytest.mark.asyncio
    async def test_pipeline_crop_resize_fallback(self):
        from app.vision.pipeline import process_image_pipeline
        img = solid(120,120)
        data = cv2.imencode(".png", img)[1].tobytes()
        with patch("app.vision.compose.crop_to_ratio", side_effect=Exception("crop fail")):
            with patch("app.vision.compose.resize_to_target", side_effect=Exception("resize fail")):
                result = await process_image_pipeline(data, "1:1", enhance=False)
                # Should still return something even if crop/resize fail (uses original composited size)
                assert "width" in result

    @pytest.mark.asyncio
    async def test_pipeline_thumbnail_fallback(self):
        from app.vision.pipeline import process_image_pipeline
        img = solid(120,120)
        data = cv2.imencode(".png", img)[1].tobytes()
        with patch("app.vision.pipeline._make_thumbnail", side_effect=Exception("thumb fail")):
            with patch("app.vision.pipeline.cv2.resize", return_value=np.zeros((256,256,3), dtype=np.uint8)):
                result = await process_image_pipeline(data, "1:1", enhance=False)
                assert len(result["thumbnail_bytes"])>0

class TestImageApiBooster:
    def test_extract_extension_double_ext_php(self):
        from app.api.image import _extract_extension
        # filename with .php should still extract via MIME fallback to jpg if allowed
        assert _extract_extension("image.php.jpg", "image/jpeg") == "jpg"

    def test_validate_dimensions_empty_and_large(self):
        from app.api.image import _validate_dimensions_bytes
        with pytest.raises(Exception):
            _validate_dimensions_bytes(b"")
        with patch("app.api.image.cv2.imdecode", return_value=np.zeros((7000,7000,3), dtype=np.uint8)):
            with pytest.raises(Exception):
                _validate_dimensions_bytes(b"fake")

    def test_upload_bytes_production_retry_fail(self):
        import app.api.image as m
        with patch("app.core.config.get_settings") as mock_s:
            mock_s.return_value.DEBUG=False
            mock_s.return_value.SUPABASE_URL="https://prod.supabase.co"
            mock_s.return_value.SUPABASE_STORAGE_BUCKET="product-images"
            mock_client = MagicMock()
            mock_storage = MagicMock()
            mock_client.storage.from_.return_value=mock_storage
            mock_storage.upload.side_effect=[Exception("already exists"), Exception("still fail")]
            with patch("app.database.connection.get_supabase_client", return_value=mock_client):
                with patch("app.services.storage_service.ensure_bucket_exists", return_value=True):
                    with pytest.raises(Exception) as exc:
                        m._upload_bytes_with_fallback("product-images","a/b.png",b"data","image/png")
                    # In production this raises 500
                    assert exc.value.status_code==500 or "Failed" in str(exc.value)

    def test_enhance_api_pipeline_incomplete_result(self):
        from fastapi.testclient import TestClient
        from app.main import app
        from app.core.security import get_current_user
        app.dependency_overrides[get_current_user]=lambda: {"firebase_uid":"test123","artisan":{"id":"artisan123"},"claims":{}}
        client=TestClient(app)
        img=np.full((100,100,3),(100,100,100),dtype=np.uint8)
        png=cv2.imencode(".png",img)[1].tobytes()
        async def incomplete_pipeline(*a,**k):
            return {"enhanced_bytes":None,"webp_bytes":None,"thumbnail_bytes":None,"width":0,"height":0,"ratio":"1:1"}
        with patch("app.api.image.process_image_pipeline", side_effect=incomplete_pipeline):
            resp=client.post("/api/v1/image/enhance", files={"image":("a.png",png,"image/png")}, data={"output_format":"1:1"}, headers={"Authorization":"Bearer test"})
            assert resp.status_code==500
        app.dependency_overrides.clear()
        app.dependency_overrides[get_current_user]=lambda: {"firebase_uid":"test123","artisan":{"id":"artisan123"},"claims":{}}
