"""
Image studio quality checks on synthetic product photos: the background actually turns
white, product colour survives enhancement, the product is framed rather than
centre-cropped, and frame-filling textiles are left intact.
"""
import os

os.environ.setdefault("DEBUG", "true")

import cv2
import numpy as np
import pytest


def product_photo(w=900, h=700, backdrop=(196, 200, 204), center=(640, 430), axes=(150, 190)):
    """Red woven product (striped ellipse) on a slightly noisy grey backdrop, off-centre."""
    rng = np.random.default_rng(7)
    img = np.full((h, w, 3), backdrop, dtype=np.int16)
    img += rng.integers(-6, 7, size=img.shape, dtype=np.int16)
    product = np.zeros((h, w), dtype=np.uint8)
    cv2.ellipse(product, center, axes, 0, 0, 360, 255, -1)
    stripes = ((np.arange(h)[:, None] // 12) % 2 == 0) & (product > 0)
    img[product > 0] = (40, 40, 190)
    img[stripes] = (30, 30, 150)
    return np.clip(img, 0, 255).astype(np.uint8), product


def decode(png_bytes):
    return cv2.imdecode(np.frombuffer(png_bytes, np.uint8), cv2.IMREAD_COLOR)


def encode_png(img):
    ok, buf = cv2.imencode(".png", img)
    assert ok
    return buf.tobytes()


class TestStudioOutput:
    @pytest.mark.asyncio
    async def test_background_becomes_white_and_product_keeps_colour(self):
        from app.vision.pipeline import process_image_pipeline

        img, _ = product_photo()
        result = await process_image_pipeline(encode_png(img), output_format="1:1", enhance=True)
        out = decode(result["enhanced_bytes"])

        assert result["background_removed"] is True
        corners = np.concatenate([out[:40, :40], out[:40, -40:], out[-40:, :40], out[-40:, -40:]])
        assert corners.mean() > 245

        # Product region stays clearly red — gray-world balancing used to pull it toward grey
        h, w = out.shape[:2]
        b, g, r = out[h // 2 - 30 : h // 2 + 30, w // 2 - 30 : w // 2 + 30].reshape(-1, 3).mean(axis=0)
        assert r > 120 and r - g > 60 and r - b > 60

    @pytest.mark.asyncio
    async def test_off_centre_product_is_framed_in_the_middle(self):
        from app.vision.pipeline import process_image_pipeline

        img, _ = product_photo(center=(680, 450))
        result = await process_image_pipeline(encode_png(img), output_format="4:5", enhance=False)
        out = decode(result["enhanced_bytes"])
        assert (result["width"], result["height"]) == (864, 1080)

        ys, xs = np.nonzero(cv2.cvtColor(out, cv2.COLOR_BGR2GRAY) < 200)
        assert abs(xs.mean() / out.shape[1] - 0.5) < 0.08
        assert abs(ys.mean() / out.shape[0] - 0.5) < 0.08
        # Product fills a good share of the frame instead of floating in the original's empty space
        assert (xs.max() - xs.min()) / out.shape[1] > 0.6

    @pytest.mark.asyncio
    async def test_frame_filling_textile_is_not_cut_out(self):
        from app.vision.pipeline import process_image_pipeline

        rng = np.random.default_rng(3)
        textile = np.zeros((600, 600, 3), dtype=np.uint8)
        textile[:] = (20, 120, 200)
        textile[(np.arange(600)[:, None] // 20 + np.arange(600)[None, :] // 20) % 2 == 0] = (30, 30, 160)
        textile = np.clip(textile.astype(np.int16) + rng.integers(-8, 9, textile.shape), 0, 255).astype(np.uint8)

        result = await process_image_pipeline(encode_png(textile), output_format="1:1", enhance=True)
        out = decode(result["enhanced_bytes"])
        assert result["background_removed"] is False
        # No white cut-out holes punched into the fabric
        assert (cv2.cvtColor(out, cv2.COLOR_BGR2GRAY) > 245).mean() < 0.02


class TestFramingAndCorrection:
    def test_crop_to_subject_pads_with_white_at_photo_edge(self):
        from app.vision.compose import crop_to_subject

        img = np.full((300, 400, 3), 255, dtype=np.uint8)
        mask = np.zeros((300, 400), dtype=np.uint8)
        img[100:300, 300:400] = (0, 0, 180)
        mask[100:300, 300:400] = 255  # touches right and bottom edges

        out = crop_to_subject(img, mask, ratio="1:1", margin=0.1)
        assert abs(out.shape[1] / out.shape[0] - 1.0) < 0.01
        assert np.all(out[:5, :5] == 255)
        assert np.all(out[-5:, -5:] == 255)  # padding beyond the photo is white, not black

    def test_crop_to_subject_empty_mask_falls_back_to_centre_crop(self):
        from app.vision.compose import crop_to_subject

        img = np.random.randint(0, 255, (300, 500, 3), dtype=np.uint8)
        out = crop_to_subject(img, np.zeros((300, 500), dtype=np.uint8), ratio="1:1")
        assert out.shape[:2] == (300, 300)

    def test_white_balance_from_neutral_background_removes_cast(self):
        from app.vision.enhance import white_balance_from_background

        img = np.full((200, 200, 3), (200, 190, 170), dtype=np.uint8)  # warm cast on a grey wall
        img[60:140, 60:140] = (40, 40, 190)
        mask = np.zeros((200, 200), dtype=np.uint8)
        mask[60:140, 60:140] = 255

        out = white_balance_from_background(img, mask)
        bg = out[:40, :40].reshape(-1, 3).mean(axis=0)
        assert bg.max() - bg.min() < 8

    def test_white_balance_skips_coloured_backdrop(self):
        from app.vision.enhance import white_balance_from_background

        img = np.full((200, 200, 3), (40, 160, 40), dtype=np.uint8)  # green cloth backdrop
        mask = np.zeros((200, 200), dtype=np.uint8)
        mask[60:140, 60:140] = 255
        assert np.array_equal(white_balance_from_background(img, mask), img)

    def test_auto_exposure_meters_on_product(self):
        from app.vision.enhance import auto_exposure

        img = np.full((200, 200, 3), 240, dtype=np.uint8)  # bright backdrop
        img[50:150, 50:150] = 50  # dark, underexposed product
        img[50:150, 50:150, 2] = 70
        mask = np.zeros((200, 200), dtype=np.uint8)
        mask[50:150, 50:150] = 255

        out = auto_exposure(img, mask=mask)
        before = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)[50:150, 50:150, 0].mean()
        after = cv2.cvtColor(out, cv2.COLOR_BGR2LAB)[50:150, 50:150, 0].mean()
        assert after > before + 30
