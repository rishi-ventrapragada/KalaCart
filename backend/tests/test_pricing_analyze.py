"""
Pricing assistant endpoint tests — POST /api/v1/pricing/analyze.

The vision model and the comparable-listings lookup are mocked; the pricing engine runs for real.
"""
import os

os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("APP_ENV", "development")
os.environ.setdefault("SUPABASE_URL", "https://placeholder.supabase.co")

import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch

from app.main import app
from app.api import pricing as pricing_module
from app.core.security import get_current_user

MOCK_USER = {"uid": "seller-1", "firebase_uid": "seller-1", "artisan": {"id": "seller-1"}, "claims": {}}
ATTRIBUTES = {
    "category": "Basketry",
    "materials": ["Bamboo"],
    "size": "Small",
    "quality": "Standard",
    "complexity": 2,
    "estimated_labour_hours": 4.0,
    "observations": "Hand-woven bamboo with a painted rim.",
}

client = TestClient(app)


@pytest.fixture(autouse=True)
def seller_and_clean_limits():
    saved = app.dependency_overrides.get(get_current_user)
    app.dependency_overrides[get_current_user] = lambda: MOCK_USER
    pricing_module._clear_rate_limit_store()
    yield
    pricing_module._clear_rate_limit_store()
    if saved is None:
        app.dependency_overrides.pop(get_current_user, None)
    else:
        app.dependency_overrides[get_current_user] = saved


def _photo() -> bytes:
    img = np.full((300, 300, 3), 220, dtype=np.uint8)
    cv2.circle(img, (150, 150), 90, (60, 130, 190), -1)
    ok, buf = cv2.imencode(".jpg", img)
    assert ok
    return buf.tobytes()


def analyze(data=None, photo=True, content_type="image/jpeg", attributes=None, comparables=None):
    extract = AsyncMock(return_value=dict(attributes or ATTRIBUTES))
    form = {"description": "Handmade bamboo basket from Srikakulam with a red painted rim"}
    form.update(data or {})
    files = {"image": ("basket.jpg", _photo() if photo is True else photo, content_type)} if photo else None
    with patch("app.api.pricing.extract_product_attributes", extract), \
            patch("app.api.pricing._fetch_comparable_prices", return_value=comparables or []):
        resp = client.post("/api/v1/pricing/analyze", data=form, files=files)
    return resp, extract


class TestAnalyzePrice:
    def test_photo_and_description_give_explainable_price(self):
        resp, extract = analyze()
        assert resp.status_code == 200, resp.text
        data = resp.json()["data"]

        assert data["minimum_price"] <= data["suggested_price"] <= data["maximum_price"]
        assert data["currency"] == "INR"
        assert data["attributes"]["category"] == "Basketry"
        # Seller gave neither cost: material cost estimated, labour hours taken from the photo reading
        assert data["estimated_inputs"] == ["material_cost", "labour_hours"]
        assert data["labour_hours"] == 4.0
        assert data["market"]["source"] == "reference_ranges"
        assert len(data["factors"]) >= 4
        assert abs(sum(data["breakdown"].values()) - data["suggested_price"]) < 1

        text, image_bytes = extract.call_args.args
        assert "bamboo basket" in text
        assert image_bytes is not None

    def test_seller_facts_override_model_and_raise_confidence(self):
        guessed, _ = analyze()
        resp, extract = analyze(data={
            "category": "textiles",
            "materials": "cotton, natural dyes",
            "material_cost": "400",
            "labour_hours": "12",
            "market_position": "premium",
            "quality": "premium",
        })
        assert resp.status_code == 200, resp.text
        extract.assert_called_once()  # size and complexity still come from the photo
        data = resp.json()["data"]
        assert data["attributes"]["category"] == "Textiles"
        assert data["attributes"]["quality"] == "Premium"
        assert data["attributes"]["size"] == "Small"
        assert data["attributes"]["materials"] == ["Cotton", "Natural Dyes"]
        assert data["estimated_inputs"] == []
        assert data["labour_hours"] == 12.0
        assert data["market_position"] == "Premium"
        assert data["confidence"] > guessed.json()["data"]["confidence"]
        assert "Materials: Cotton, Natural Dyes" in extract.call_args.args[0]

    def test_known_attributes_skip_the_ai_call(self):
        resp, extract = analyze(data={
            "category": "Pottery",
            "size": "Large",
            "quality": "Premium",
            "complexity": "4",
            "material_cost": "900",
            "labour_hours": "15",
        })
        assert resp.status_code == 200, resp.text
        extract.assert_not_called()
        data = resp.json()["data"]
        assert data["attributes"]["size"] == "Large"
        assert data["attributes"]["complexity"] == 4
        assert data["estimated_inputs"] == []

    def test_description_only_still_prices_with_lower_confidence(self):
        with_photo, _ = analyze()
        resp, extract = analyze(photo=None)
        assert resp.status_code == 200, resp.text
        assert extract.call_args.args[1] is None
        assert resp.json()["data"]["confidence"] < with_photo.json()["data"]["confidence"]

    def test_marketplace_comparables_used_when_available(self):
        resp, _ = analyze(comparables=[400, 450, 500, 550, 600, 650])
        assert resp.status_code == 200, resp.text
        market = resp.json()["data"]["market"]
        assert market["source"] == "marketplace_listings"
        assert market["comparables"] == 6

    @pytest.mark.parametrize(
        "data, photo, content_type, code",
        [
            ({"market_position": "luxury"}, True, "image/jpeg", 422),
            ({"category": "spaceships"}, True, "image/jpeg", 422),
            ({"size": "huge"}, True, "image/jpeg", 422),
            ({"quality": "gold"}, True, "image/jpeg", 422),
            ({"complexity": "9"}, True, "image/jpeg", 422),
            ({}, b"GIF89a", "image/gif", 400),
            # pytest.param(id=...) keeps the 10 MB payload out of the test's node
            # ID. Without it the generated ID embedded all 10,485,761 bytes, which
            # made the ID multi-megabyte and errored at setup on Windows.
            pytest.param({}, b"0" * (10 * 1024 * 1024 + 1), "image/jpeg", 413, id="oversized-photo"),
            ({"description": "hi"}, True, "image/jpeg", 422),
            ({"material_cost": "-5"}, True, "image/jpeg", 422),
        ],
    )
    def test_invalid_input_rejected_before_ai_call(self, data, photo, content_type, code):
        resp, extract = analyze(data=data, photo=photo, content_type=content_type)
        assert resp.status_code == code, resp.text
        extract.assert_not_called()

    def test_requires_login(self):
        app.dependency_overrides.pop(get_current_user, None)
        resp = client.post("/api/v1/pricing/analyze", data={"description": "Handmade bamboo basket"})
        assert resp.status_code == 401


class TestMarketHelpers:
    def test_comparable_lookup_returns_empty_on_error(self):
        with patch("app.database.connection.get_supabase_client", side_effect=RuntimeError("db down")):
            assert pricing_module._fetch_comparable_prices("Pottery") == []

    def test_comparable_lookup_keeps_numeric_prices(self):
        query = MagicMock()
        query.select.return_value = query
        query.eq.return_value = query
        query.limit.return_value = query
        query.execute.return_value = MagicMock(data=[{"price": 500}, {"price": None}, {"price": 725.5}])
        supabase = MagicMock()
        supabase.table.return_value = query
        with patch("app.database.connection.get_supabase_client", return_value=supabase):
            assert pricing_module._fetch_comparable_prices("Pottery") == [500.0, 725.5]

    def test_predict_seasonal_boost_follows_calendar(self):
        with patch("app.api.pricing.seasonal_factor", return_value=(1.0, "No festival demand window")):
            assert pricing_module._fetch_seasonal_boost("Pottery") is None
        with patch("app.api.pricing.seasonal_factor", return_value=(1.15, "Diwali & Dussehra festive demand")):
            boost = pricing_module._fetch_seasonal_boost("Pottery")
        assert boost.festival_name == "Diwali & Dussehra festive demand"
        assert boost.multiplier == 1.15
