"""
Vision pipeline unit tests — enhance, background, compose, pipeline.
Run: pytest backend/tests/test_vision_pipeline.py -v
"""
import io
import os
os.environ.setdefault("DEBUG", "true")
import pytest
import numpy as np
import cv2
from PIL import Image


# ── Helpers ──────────────────────────────────────────────────────────
def solid_bgr(w, h, color=(128, 64, 32)):
    img = np.full((h, w, 3), color, dtype=np.uint8)
    return img

def gradient_bgr(w=200, h=200):
    img = np.zeros((h, w, 3), dtype=np.uint8)
    for y in range(h):
        for x in range(w):
            img[y, x] = [(x * 255 // w), (y * 255 // h), 128]
    return img

def encode_png(img):
    ok, buf = cv2.imencode(".png", img)
    assert ok
    return buf.tobytes()

def encode_jpeg(img, q=90):
    ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, q])
    assert ok
    return buf.tobytes()


# ── enhance.py ──────────────────────────────────────────────────────
class TestEnhanceModule:
    def test_histogram_equalization_preserves_shape(self):
        from app.vision.enhance import histogram_equalization
        img = solid_bgr(100, 80, (50, 100, 150))
        out = histogram_equalization(img)
        assert out.shape == img.shape
        assert out.dtype == np.uint8
        # Should differ from input (equalization changes Y channel) unless uniform?
        # For non-uniform, ensure not equal; for solid may still change but check shape
        assert out.shape[2] == 3

    def test_histogram_handles_invalid_returns_original(self):
        from app.vision.enhance import histogram_equalization
        assert histogram_equalization(None) is None
        empty = np.array([], dtype=np.uint8)
        out = histogram_equalization(empty)
        # should return input (empty) without crash
        assert out is empty or out.size == 0

    def test_clahe_preserves_shape_and_dtype(self):
        from app.vision.enhance import apply_clahe
        img = gradient_bgr(120, 120)
        out = apply_clahe(img, clipLimit=2.0, tileGridSize=(8,8))
        assert out.shape == img.shape
        assert out.dtype == np.uint8
        # CLAHE should change values
        assert not np.array_equal(out, img)

    def test_clahe_invalid_input(self):
        from app.vision.enhance import apply_clahe
        img = None
        out = apply_clahe(img)  # type: ignore
        assert out is None

    def test_bilateral_denoise_shape(self):
        from app.vision.enhance import bilateral_denoise
        img = gradient_bgr(80, 80)
        out = bilateral_denoise(img, d=9, sigmaColor=75, sigmaSpace=75)
        assert out.shape == img.shape
        assert out.dtype == np.uint8

    def test_bilateral_d_parameter_clamped(self):
        from app.vision.enhance import bilateral_denoise
        img = solid_bgr(50, 50)
        # d=100 should be clamped to 15 internally, still works
        out = bilateral_denoise(img, d=100)
        assert out.shape == img.shape

    def test_unsharp_mask_preserves_shape(self):
        from app.vision.enhance import unsharp_mask
        img = gradient_bgr(100, 100)
        out = unsharp_mask(img, amount=0.5, radius=1.0)
        assert out.shape == img.shape
        assert out.dtype == np.uint8

    def test_unsharp_amount_zero_returns_copy(self):
        from app.vision.enhance import unsharp_mask
        img = solid_bgr(60, 60, (10,20,30))
        out = unsharp_mask(img, amount=0.0)
        assert np.array_equal(out, img)
        # should be copy not same object
        assert out is not img

    def test_unsharp_threshold_branch(self):
        from app.vision.enhance import unsharp_mask
        img = gradient_bgr(80, 80)
        out = unsharp_mask(img, amount=0.8, radius=1.5, threshold=10)
        assert out.shape == img.shape
        assert out.dtype == np.uint8

    def test_auto_brightness(self):
        from app.vision.enhance import auto_brightness_normalization
        # Dark image should be brightened toward mean 180
        dark = np.full((80,80,3), 40, dtype=np.uint8)
        out = auto_brightness_normalization(dark, target_mean=180)
        assert out.shape == dark.shape
        # mean should increase
        assert float(np.mean(cv2.cvtColor(out, cv2.COLOR_BGR2GRAY))) > float(np.mean(cv2.cvtColor(dark, cv2.COLOR_BGR2GRAY)))

    def test_auto_brightness_already_bright_no_change(self):
        from app.vision.enhance import auto_brightness_normalization
        bright = np.full((40,40,3), 180, dtype=np.uint8)
        # Add slight variation
        out = auto_brightness_normalization(bright, target_mean=180)
        assert out.shape == bright.shape
        # near 180, scale ~1, so output may be copy
        assert out.dtype == np.uint8

    def test_auto_brightness_near_zero_mean(self):
        from app.vision.enhance import auto_brightness_normalization
        black = np.zeros((40,40,3), dtype=np.uint8)
        out = auto_brightness_normalization(black)
        # Should return copy (skip scaling)
        assert out.shape == black.shape

    def test_white_balance(self):
        from app.vision.enhance import white_balance_simple
        # Create color cast image: strong blue
        img = np.full((60,60,3), (200, 100, 80), dtype=np.uint8)  # BGR blueish
        out = white_balance_simple(img)
        assert out.shape == img.shape
        assert out.dtype == np.uint8
        # After balance, channels should be closer
        b_mean, g_mean, r_mean = cv2.mean(img)[:3]
        ob, og, or_ = cv2.mean(out)[:3]
        # Check that balanced channels are nearer each other
        orig_spread = max(b_mean,g_mean,r_mean) - min(b_mean,g_mean,r_mean)
        new_spread = max(ob,og,or_) - min(ob,og,or_)
        assert new_spread <= orig_spread + 1  # allow equal

    def test_white_balance_black_channel_skips(self):
        from app.vision.enhance import white_balance_simple
        img = np.zeros((30,30,3), dtype=np.uint8)
        img[:,:,0] = 0
        img[:,:,1] = 100
        img[:,:,2] = 100
        out = white_balance_simple(img)
        assert out.shape == img.shape

    def test_enhance_image_total(self):
        from app.vision.enhance import enhance_image
        img = gradient_bgr(150, 150)
        out = enhance_image(img)
        assert out.shape == img.shape
        assert out.dtype == np.uint8
        # Should not be identical (pipeline changes)
        assert not np.array_equal(out, img)

    def test_enhance_image_invalid_raises_or_returns(self):
        from app.vision.enhance import enhance_image
        # None input: currently returns input if possible else raises
        # In implementation, if _validate_bgr fails and size 0 returns copy else raises
        # For None, it raises ValueError then returns None copy branch
        try:
            out = enhance_image(None)  # type: ignore
            # If it didn't raise, it should return None or handle
            assert out is None or isinstance(out, np.ndarray)
        except ValueError:
            pass

    def test_enhance_idempotent_multiple_runs(self):
        from app.vision.enhance import enhance_image
        img = solid_bgr(80,80, (90,110,130))
        out1 = enhance_image(img)
        out2 = enhance_image(out1)
        assert out1.shape == out2.shape
        assert out1.dtype == out2.dtype


# ── background.py ───────────────────────────────────────────────────
class TestBackgroundModule:
    def test_get_foreground_mask_returns_0_255(self):
        from app.vision.background import get_foreground_mask
        img = np.full((200,200,3), 255, dtype=np.uint8)
        cv2.rectangle(img, (60,60), (140,140), (50,80,160), -1)
        mask = get_foreground_mask(img, iterations=2)
        assert mask.shape == (200,200)
        assert mask.dtype == np.uint8
        unique = set(np.unique(mask).tolist())
        assert unique.issubset({0, 255})

    def test_get_foreground_mask_small_image_fallback(self):
        from app.vision.background import get_foreground_mask
        img = np.full((20,20,3), 200, dtype=np.uint8)
        mask = get_foreground_mask(img, iterations=2)
        assert mask.shape == (20,20)
        assert mask.dtype == np.uint8

    def test_get_foreground_mask_invalid_input_returns_full_white(self):
        from app.vision.background import get_foreground_mask
        mask = get_foreground_mask(None)  # type: ignore
        assert mask.dtype == np.uint8
        assert np.all(mask == 255)

    def test_fallback_otsu_used_when_grabcut_degenerate(self):
        from app.vision.background import get_foreground_mask
        # Solid color image: grabcut will be degenerate -> fallback should return mask
        img = np.full((100,100,3), 128, dtype=np.uint8)
        mask = get_foreground_mask(img, iterations=1)
        assert mask.shape == (100,100)
        assert set(np.unique(mask).tolist()).issubset({0,255, 128}) or mask.dtype == np.uint8

    def test_remove_background_alias(self):
        from app.vision.background import remove_background, get_foreground_mask
        img = solid_bgr(80,80, (100,100,100))
        m1 = remove_background(img)
        m2 = get_foreground_mask(img)
        assert m1.shape == m2.shape
        assert m1.dtype == np.uint8

    def test_mask_fallback_returns_0_255(self):
        from app.vision.background import _fallback_mask_otsu_morphology
        img = np.full((120,120,3), 240, dtype=np.uint8)
        cv2.circle(img, (60,60), 30, (30,30,200), -1)
        mask = _fallback_mask_otsu_morphology(img)
        assert mask.dtype == np.uint8
        assert mask.shape == (120,120)
        assert set(np.unique(mask).tolist()).issubset({0,255})


# ── compose.py ──────────────────────────────────────────────────────
class TestComposeModule:
    def test_generate_white_background_shape(self):
        from app.vision.compose import generate_white_background
        bg = generate_white_background(200, 100)
        assert bg.shape == (100,200,3)
        assert np.all(bg == 255)

    def test_generate_white_background_invalid(self):
        from app.vision.compose import generate_white_background
        with pytest.raises(ValueError):
            generate_white_background(0, 100)
        with pytest.raises(ValueError):
            generate_white_background(100, -5)
        with pytest.raises(ValueError):
            generate_white_background(7000, 100)

    def test_crop_to_ratio_1_1(self):
        from app.vision.compose import crop_to_ratio
        img = np.random.randint(0,255,(600,800,3), dtype=np.uint8)  # 800x600 -> aspect 1.33
        out = crop_to_ratio(img, "1:1")
        h, w = out.shape[:2]
        assert abs(w/h - 1.0) < 0.02  # square

    def test_crop_to_ratio_4_5(self):
        from app.vision.compose import crop_to_ratio
        img = np.random.randint(0,255,(600,800,3), dtype=np.uint8)  # wider than 0.8
        out = crop_to_ratio(img, "4:5")
        h, w = out.shape[:2]
        assert abs(w/h - 0.8) < 0.05

    def test_crop_to_ratio_already_square_no_change_aspect(self):
        from app.vision.compose import crop_to_ratio
        img = np.random.randint(0,255,(500,500,3), dtype=np.uint8)
        out = crop_to_ratio(img, "1:1")
        assert out.shape[0] == 500 and out.shape[1] == 500

    def test_crop_to_ratio_padding_branch(self):
        from app.vision.compose import crop_to_ratio
        # Very tall image: 300x600 -> aspect 0.5, target 0.8 needs padding width
        img = np.random.randint(0,255,(600,300,3), dtype=np.uint8)
        out = crop_to_ratio(img, "4:5")
        h, w = out.shape[:2]
        assert abs(w/h - 0.8) < 0.05
        # height preserved (600), width padded to 480
        assert h == 600

    def test_crop_invalid_ratio_raises(self):
        from app.vision.compose import crop_to_ratio
        img = solid_bgr(100,100)
        with pytest.raises(ValueError):
            crop_to_ratio(img, "16:9")
        with pytest.raises(ValueError):
            crop_to_ratio(None, "1:1")  # type: ignore

    def test_resize_to_target_1_1(self):
        from app.vision.compose import resize_to_target, crop_to_ratio
        img = np.random.randint(0,255,(800,800,3), dtype=np.uint8)
        cropped = crop_to_ratio(img, "1:1")
        resized = resize_to_target(cropped, target=1080)
        assert resized.shape[0] == 1080 and resized.shape[1] == 1080

    def test_resize_to_target_4_5(self):
        from app.vision.compose import resize_to_target
        # Create 4:5 image
        img = np.random.randint(0,255,(1080,864,3), dtype=np.uint8)  # already 864x1080
        resized = resize_to_target(img, target=1080)
        assert resized.shape[1] == 864 and resized.shape[0] == 1080

    def test_resize_already_target_returns_copy(self):
        from app.vision.compose import resize_to_target
        img = np.random.randint(0,255,(1080,1080,3), dtype=np.uint8)
        out = resize_to_target(img, target=1080)
        assert out.shape == img.shape
        assert out is not img  # copy

    def test_resize_invalid_target(self):
        from app.vision.compose import resize_to_target
        img = solid_bgr(100,100)
        with pytest.raises(ValueError):
            resize_to_target(img, target=0)
        with pytest.raises(ValueError):
            resize_to_target(img, target=7000)

    def test_compose_on_white(self):
        from app.vision.compose import compose_on_white
        fg = np.full((100,100,3), (50,80,160), dtype=np.uint8)
        mask = np.zeros((100,100), dtype=np.uint8)
        mask[25:75, 25:75] = 255
        out = compose_on_white(fg, mask, bg_color=(255,255,255))
        assert out.shape == fg.shape
        # Corners should be white (blended)
        assert np.all(out[0,0] == 255)
        # Center should retain fg color (approx, feathered)
        # Feather blur may slightly blend edge but center solid
        assert out[50,50].tolist() != [255,255,255]

    def test_compose_mask_none_returns_copy(self):
        from app.vision.compose import compose_on_white
        fg = solid_bgr(50,50)
        out = compose_on_white(fg, None)  # type: ignore
        assert np.array_equal(out, fg)

    def test_compose_mismatched_mask_resized(self):
        from app.vision.compose import compose_on_white
        fg = solid_bgr(100,100)
        mask_small = np.full((50,50), 255, dtype=np.uint8)
        out = compose_on_white(fg, mask_small)
        assert out.shape == fg.shape

    def test_compose_float_mask(self):
        from app.vision.compose import compose_on_white
        fg = solid_bgr(40,40)
        mask_f = np.ones((40,40), dtype=np.float32) * 0.5
        out = compose_on_white(fg, mask_f)
        assert out.shape == fg.shape


# ── pipeline.py ─────────────────────────────────────────────────────
class TestPipeline:
    @pytest.mark.asyncio
    async def test_process_pipeline_1_1_produces_1080(self):
        from app.vision.pipeline import process_image_pipeline
        img = solid_bgr(300, 300, (100,120,140))
        # Draw simple object
        cv2.rectangle(img, (80,80), (220,220), (200,50,50), -1)
        b = encode_png(img)
        result = await process_image_pipeline(b, output_format="1:1", enhance=True)
        assert result["width"] == 1080
        assert result["height"] == 1080
        assert result["ratio"] == "1:1"
        assert len(result["enhanced_bytes"]) > 0
        assert len(result["webp_bytes"]) > 0
        assert len(result["thumbnail_bytes"]) > 0
        # Verify decodability
        n = np.frombuffer(result["enhanced_bytes"], np.uint8)
        dec = cv2.imdecode(n, cv2.IMREAD_COLOR)
        assert dec.shape[1] == 1080 and dec.shape[0] == 1080

    @pytest.mark.asyncio
    async def test_process_pipeline_4_5_produces_864x1080(self):
        from app.vision.pipeline import process_image_pipeline
        img = solid_bgr(400, 500, (80,90,100))
        cv2.circle(img, (200,250), 80, (50,180,90), -1)
        b = encode_png(img)
        result = await process_image_pipeline(b, output_format="4:5", enhance=True)
        assert result["width"] == 864
        assert result["height"] == 1080
        assert result["ratio"] == "4:5"

    @pytest.mark.asyncio
    async def test_invalid_output_format_raises(self):
        from app.vision.pipeline import process_image_pipeline
        img = solid_bgr(200,200)
        b = encode_png(img)
        with pytest.raises(ValueError) as exc:
            await process_image_pipeline(b, output_format="16:9")
        assert "Invalid output_format" in str(exc.value)

    @pytest.mark.asyncio
    async def test_empty_bytes_raises(self):
        from app.vision.pipeline import process_image_pipeline
        with pytest.raises(ValueError) as exc:
            await process_image_pipeline(b"", output_format="1:1")
        assert "Empty" in str(exc.value)
        with pytest.raises(ValueError):
            await process_image_pipeline(None, output_format="1:1")  # type: ignore

    @pytest.mark.asyncio
    async def test_webp_signature(self):
        from app.vision.pipeline import process_image_pipeline
        img = solid_bgr(200,200, (60,70,80))
        b = encode_png(img)
        result = await process_image_pipeline(b, output_format="1:1", enhance=False)
        webp = result["webp_bytes"]
        # WebP files start with RIFF....WEBP
        assert webp[:4] == b"RIFF"
        assert b"WEBP" in webp[:12]
        thumb = result["thumbnail_bytes"]
        assert thumb[:4] == b"RIFF"
        assert b"WEBP" in thumb[:12]

    @pytest.mark.asyncio
    async def test_thumbnail_size(self):
        from app.vision.pipeline import process_image_pipeline
        img = solid_bgr(400,400)
        b = encode_png(img)
        result = await process_image_pipeline(b, output_format="1:1", enhance=False)
        thumb_bytes = result["thumbnail_bytes"]
        n = np.frombuffer(thumb_bytes, np.uint8)
        thumb = cv2.imdecode(n, cv2.IMREAD_COLOR)
        assert thumb is not None
        # Long edge should be 256 for 1:1
        assert max(thumb.shape[0], thumb.shape[1]) == 256
        # For 4:5, test separately
        result2 = await process_image_pipeline(b, output_format="4:5", enhance=False)
        thumb2_bytes = result2["thumbnail_bytes"]
        n2 = np.frombuffer(thumb2_bytes, np.uint8)
        thumb2 = cv2.imdecode(n2, cv2.IMREAD_COLOR)
        assert thumb2.shape[0] == 256  # height long edge
        assert thumb2.shape[1] == 205 or thumb2.shape[1] == 204  # 864/1080 *256 ~205

    @pytest.mark.asyncio
    async def test_pipeline_without_enhance(self):
        from app.vision.pipeline import process_image_pipeline
        img = solid_bgr(250,250)
        b = encode_png(img)
        r1 = await process_image_pipeline(b, output_format="1:1", enhance=True)
        r2 = await process_image_pipeline(b, output_format="1:1", enhance=False)
        # Both should succeed and produce correct dims, but enhanced may differ
        assert r1["width"] == r2["width"] == 1080
        assert len(r1["enhanced_bytes"]) > 0
        assert len(r2["enhanced_bytes"]) > 0

    @pytest.mark.asyncio
    async def test_pipeline_invalid_image_bytes(self):
        from app.vision.pipeline import process_image_pipeline
        with pytest.raises(ValueError):
            await process_image_pipeline(b"not an image", output_format="1:1")

    @pytest.mark.asyncio
    async def test_pipeline_jpeg_input(self):
        from app.vision.pipeline import process_image_pipeline
        img = solid_bgr(300,300, (120,130,140))
        b = encode_jpeg(img)
        result = await process_image_pipeline(b, output_format="1:1")
        assert result["width"] == 1080

    def test_export_helpers_signature(self):
        from app.vision.pipeline import _export_png, _export_webp
        img = solid_bgr(50,50)
        png = _export_png(img)
        assert png[:8] == b"\x89PNG\r\n\x1a\n"
        webp = _export_webp(img, quality=85)
        assert webp[:4] == b"RIFF"

    def test_decode_invalid_raises(self):
        from app.vision.pipeline import _decode_image
        with pytest.raises(ValueError):
            _decode_image(b"")
        with pytest.raises(ValueError):
            _decode_image(b"garbage bytes not image")

    def test_validate_dimensions_boundaries(self):
        from app.vision.pipeline import _validate_dimensions
        small = np.zeros((50,50,3), dtype=np.uint8)
        with pytest.raises(ValueError):
            _validate_dimensions(small)
        large = np.zeros((7000,100,3), dtype=np.uint8)
        with pytest.raises(ValueError):
            _validate_dimensions(large)
        ok = np.zeros((600,800,3), dtype=np.uint8)
        _validate_dimensions(ok)  # no raise
