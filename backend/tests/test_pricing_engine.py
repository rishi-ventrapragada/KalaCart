"""
Pricing engine + vision attribute normalization tests (app.services.pricing_engine, app.ai.vision).
Pure functions — no network.
"""
import os

os.environ.setdefault("DEBUG", "true")

from datetime import date

import cv2
import numpy as np
import pytest

from app.ai.vision import image_data_url, normalize_attributes
from app.services import pricing_engine as engine

SEPTEMBER = date(2026, 9, 11)
OCTOBER = date(2026, 10, 20)


def price(**overrides):
    params = dict(
        category="Pottery",
        size="Medium",
        quality="Standard",
        complexity=3,
        market_position="Standard",
        labour_hours=6,
        material_cost=250.0,
        comparable_prices=[],
        today=SEPTEMBER,
    )
    params.update(overrides)
    return engine.compute_price(**params)


class TestSeasonalCalendar:
    def test_diwali_window_lifts_pottery(self):
        assert engine.seasonal_factor("Pottery", OCTOBER) == (1.15, "Diwali & Dussehra festive demand")

    def test_no_festival_in_september(self):
        factor, reason = engine.seasonal_factor("Pottery", SEPTEMBER)
        assert factor == 1.0
        assert "no festival" in reason.lower()

    def test_wedding_season_textiles(self):
        assert engine.seasonal_factor("Textiles", date(2026, 12, 5))[0] == 1.10

    def test_category_outside_window_unaffected(self):
        assert engine.seasonal_factor("Basketry", OCTOBER)[0] == 1.0


class TestMarketBand:
    def test_reference_ranges_scaled_by_size_when_few_listings(self):
        band = engine.market_band("Basketry", "Large", [500, 700])
        assert band["source"] == "reference_ranges"
        assert band["comparables"] == 2
        assert (band["low"], band["high"]) == (630, 1980)  # (350, 1100) x 1.8

    def test_marketplace_quartiles_with_enough_listings(self):
        band = engine.market_band("Textiles", "Medium", [800, 900, 1000, 1100, 1200, 1300, 1400, 0, None])
        assert band["source"] == "marketplace_listings"
        assert band["comparables"] == 7
        assert band["low"] < band["median"] < band["high"]
        assert band["median"] == 1100


class TestComputePrice:
    def test_prices_are_ordered_and_rounded(self):
        result = price()
        assert result["minimum_price"] <= result["suggested_price"] <= result["maximum_price"]
        for key in ("minimum_price", "suggested_price", "maximum_price"):
            assert result[key] % 10 == 0
        assert result["currency"] == "INR"

    def test_breakdown_sums_to_suggested_price(self):
        result = price()
        assert abs(sum(result["breakdown"].values()) - result["suggested_price"]) < 1

    def test_never_below_artisan_cost(self):
        result = price(category="Basketry", size="Small", material_cost=5000.0, labour_hours=10)
        labour = 10 * engine.LABOUR_RATES["Standard"]
        assert result["suggested_price"] >= (5000 + labour) * 1.1
        assert result["minimum_price"] >= (5000 + labour) * 1.1 - 10
        assert any("cover your costs" in f for f in result["factors"])

    def test_positioning_orders_prices(self):
        budget = price(market_position="Budget")["suggested_price"]
        standard = price(market_position="Standard")["suggested_price"]
        premium = price(market_position="Premium")["suggested_price"]
        assert budget < standard < premium

    def test_intricate_work_prices_higher(self):
        assert price(complexity=5, quality="Premium")["suggested_price"] > price(complexity=1, quality="Basic")["suggested_price"]

    def test_missing_material_cost_is_estimated_and_lowers_confidence(self):
        estimated = price(material_cost=None, labour_hours_estimated=True)
        provided = price()
        assert estimated["estimated_inputs"] == ["material_cost", "labour_hours"]
        assert estimated["confidence"] < provided["confidence"]
        assert "estimated" in estimated["factors"][0]

    def test_marketplace_listings_drive_band_and_confidence(self):
        listings = [1500, 1600, 1700, 1800, 1900, 2000]
        result = price(comparable_prices=listings)
        assert result["market"]["source"] == "marketplace_listings"
        assert result["confidence"] > price()["confidence"]
        assert 1300 <= result["suggested_price"] <= 2600

    def test_festival_month_lifts_price(self):
        september = price(today=SEPTEMBER)
        october = price(today=OCTOBER)
        assert october["suggested_price"] > september["suggested_price"]
        assert october["seasonal"]["factor"] == 1.15
        assert "seasonal lift" in october["reasoning"]

    def test_unknown_values_fall_back_to_defaults(self):
        result = price(category="Spaceships", size="Huge", quality="Legendary", market_position="Luxury", complexity=99)
        assert result["market"]["source"] == "reference_ranges"
        assert result["suggested_price"] > 0


class TestVisionAttributes:
    def test_normalizes_model_output(self):
        attrs = normalize_attributes({
            "category": "basketry",
            "materials": ["bamboo", "Bamboo", "paint", ""],
            "size": "small",
            "quality": "PREMIUM",
            "complexity": "4.4",
            "estimated_labour_hours": 900,
            "observations": "  Tight hand weave with painted rim.  ",
        })
        assert attrs == {
            "category": "Basketry",
            "materials": ["Bamboo", "Paint"],
            "size": "Small",
            "quality": "Premium",
            "complexity": 4,
            "estimated_labour_hours": 200.0,
            "observations": "Tight hand weave with painted rim.",
        }

    def test_garbage_output_gets_neutral_defaults(self):
        attrs = normalize_attributes({"category": "Spaceship", "complexity": "very", "estimated_labour_hours": None})
        assert attrs["category"] == "Other"
        assert attrs["size"] == "Medium"
        assert attrs["quality"] == "Standard"
        assert attrs["complexity"] == 3
        assert attrs["estimated_labour_hours"] is None

    def test_image_is_downscaled_for_the_model(self):
        import base64

        big = np.full((2000, 3000, 3), 180, dtype=np.uint8)
        ok, buf = cv2.imencode(".png", big)
        url = image_data_url(buf.tobytes())
        assert url.startswith("data:image/jpeg;base64,")
        decoded = cv2.imdecode(np.frombuffer(base64.b64decode(url.split(",", 1)[1]), np.uint8), cv2.IMREAD_COLOR)
        assert max(decoded.shape[:2]) == 768

    def test_invalid_image_rejected(self):
        with pytest.raises(ValueError):
            image_data_url(b"not an image")


def _vision_settings(key="or-test-key"):
    from types import SimpleNamespace

    return SimpleNamespace(OPENROUTER_API_KEY=key, OPENROUTER_BASE_URL="https://openrouter.ai/api/v1", VISION_MODEL="qwen/qwen3.7-flash")


def _vision_client(*contents):
    from unittest.mock import AsyncMock, MagicMock

    responses = []
    for content in contents:
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {"choices": [{"message": {"content": content}}]}
        responses.append(resp)
    instance = MagicMock()
    instance.post = AsyncMock(side_effect=responses)
    ctx = MagicMock()
    ctx.__aenter__ = AsyncMock(return_value=instance)
    ctx.__aexit__ = AsyncMock(return_value=None)
    return ctx, instance


class TestVisionExtraction:
    VALID = '{"category": "Basketry", "materials": ["Bamboo"], "size": "Small", "quality": "Standard", "complexity": 2, "estimated_labour_hours": 3, "observations": "Tight weave."}'

    @pytest.mark.asyncio
    async def test_sends_photo_in_json_mode(self):
        from unittest.mock import patch
        from app.ai.vision import extract_product_attributes

        ok, buf = cv2.imencode(".png", np.full((200, 200, 3), 128, dtype=np.uint8))
        ctx, client = _vision_client(self.VALID)
        with patch("app.ai.vision.get_settings", return_value=_vision_settings()), patch("app.ai.vision.httpx.AsyncClient", return_value=ctx):
            attrs = await extract_product_attributes("Bamboo basket", buf.tobytes())

        assert attrs["category"] == "Basketry"
        body = client.post.call_args.kwargs["json"]
        assert body["model"] == "qwen/qwen3.7-flash"
        assert body["response_format"] == {"type": "json_object"}
        assert body["messages"][1]["content"][1]["image_url"]["url"].startswith("data:image/jpeg;base64,")

    @pytest.mark.asyncio
    async def test_retries_once_on_malformed_output(self):
        from unittest.mock import patch
        from app.ai.vision import extract_product_attributes

        malformed = '{\n"category": "Basketry",\nsize": "Small"\n}'
        ctx, client = _vision_client(malformed, self.VALID)
        with patch("app.ai.vision.get_settings", return_value=_vision_settings()), patch("app.ai.vision.httpx.AsyncClient", return_value=ctx):
            attrs = await extract_product_attributes("Bamboo basket")
        assert client.post.call_count == 2
        assert attrs["size"] == "Small"

    @pytest.mark.asyncio
    async def test_persistent_malformed_output_502(self):
        from unittest.mock import patch
        from fastapi import HTTPException
        from app.ai.vision import extract_product_attributes

        ctx, _ = _vision_client("not json", "still not json")
        with patch("app.ai.vision.get_settings", return_value=_vision_settings()), patch("app.ai.vision.httpx.AsyncClient", return_value=ctx):
            with pytest.raises(HTTPException) as exc:
                await extract_product_attributes("Bamboo basket")
        assert exc.value.status_code == 502

    @pytest.mark.asyncio
    async def test_missing_key_500(self):
        from unittest.mock import patch
        from fastapi import HTTPException
        from app.ai.vision import extract_product_attributes

        with patch("app.ai.vision.get_settings", return_value=_vision_settings(key=None)):
            with pytest.raises(HTTPException) as exc:
                await extract_product_attributes("Bamboo basket")
        assert exc.value.status_code == 500
