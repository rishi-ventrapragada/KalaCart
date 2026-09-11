"""
Tests for the unified artisan agent.

Network calls are mocked — these verify orchestration, validation, clamping and
graceful degradation, not OpenRouter itself. Live model behaviour is exercised
separately by scripts/agent_smoke_test.py.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List
from unittest.mock import AsyncMock, patch

import pytest

from app.agent import tools
from app.agent.models import AllModelsFailedError, ModelCall, list_free_models
from app.agent.orchestrator import (
    STAGE_CATALOG,
    STAGE_IMAGE,
    STAGE_PRICING,
    ArtisanAgent,
)

# ── Fixtures ───────────────────────────────────────────────────────────

VALID_CATALOG = {
    "title": "Handwoven Cotton Saree - Warangal",
    "description_en": (
        "This handwoven cotton saree comes from the looms of Warangal, Telangana, "
        "where weaving families have practised their craft across generations. "
        "Each piece takes several days on a traditional pit loom, using pure cotton "
        "yarn coloured with natural dyes. The weave is light and breathable, well "
        "suited to warm weather, and the border carries a temple motif drawn from "
        "regional architecture. Because every saree is made by hand, small "
        "variations in the weave are natural and mark it as genuinely handmade "
        "rather than machine produced. Suitable for both daily wear and festive occasions."
    ),
    "description_hi": (
        "यह हाथ से बुनी हुई सूती साड़ी तेलंगाना के वारंगल की है, जहाँ बुनकर परिवार "
        "पीढ़ियों से यह कला करते आ रहे हैं। शुद्ध सूती धागे और प्राकृतिक रंगों से बनी "
        "यह साड़ी हल्की और आरामदायक है। इसकी किनारी पर पारंपरिक मंदिर डिज़ाइन है।"
    ),
    "category": "Textiles",
    "materials": ["Cotton", "Natural Dyes"],
    "seo_tags": ["Handwoven Saree", "Cotton Saree", "Warangal Craft"],
    "care": "Hand wash in cold water, dry in shade, iron on medium heat.",
}

VALID_PRICING = {
    "suggested_price": 2400,
    "price_range": {"min": 2000, "max": 2900},
    "breakdown": {
        "material_cost": 600,
        "labour_cost": 1200,
        "skill_premium": 300,
        "platform_fee": 240,
        "packaging": 60,
    },
    "market_position": "Standard",
    "confidence": 0.8,
    "justification": "Priced to cover materials and fair labour for four days of weaving.",
    "factors": ["Material cost", "Labour hours", "Regional market rates"],
}

VALID_VISION_PLAN = {
    "subject": "Handwoven cotton saree on a wooden table",
    "category": "Textiles",
    "materials": ["Cotton"],
    "background_clutter": 0.7,
    "needs_background_removal": True,
    "brightness_adjust": 0.3,
    "contrast_adjust": 0.1,
    "warmth_adjust": 0.0,
    "sharpness_adjust": 0.4,
    "recommended_ratio": "1:1",
    "quality_score": 45,
    "issues": ["Cluttered background", "Underexposed"],
    "colors": ["Maroon", "Gold"],
}


def _mock_complete(payload: Dict[str, Any], model: str = "test/model:free"):
    """Build an AsyncMock standing in for models.complete()."""
    return AsyncMock(return_value=(json.dumps(payload), ModelCall(model=model)))


# ── extract_json ───────────────────────────────────────────────────────


class TestExtractJson:
    def test_plain_json(self):
        assert tools.extract_json('{"a": 1}') == {"a": 1}

    def test_fenced_json(self):
        assert tools.extract_json('```json\n{"a": 1}\n```') == {"a": 1}

    def test_bare_fence(self):
        assert tools.extract_json('```\n{"a": 1}\n```') == {"a": 1}

    def test_preamble_text(self):
        raw = 'Sure, here is the listing:\n{"a": 1}\nHope that helps!'
        assert tools.extract_json(raw) == {"a": 1}

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            tools.extract_json("")

    def test_no_json_raises(self):
        with pytest.raises(ValueError):
            tools.extract_json("I cannot help with that.")


# ── Catalog generation ─────────────────────────────────────────────────


class TestCatalog:
    @pytest.mark.asyncio
    async def test_generates_valid_listing(self):
        with patch.object(tools.model_router, "complete", _mock_complete(VALID_CATALOG)):
            result = await tools.generate_catalog("यह एक हाथ से बुनी साड़ी है", "hi")

        assert result["title"] == VALID_CATALOG["title"]
        assert result["category"] == "Textiles"
        # Hindi description must actually be Devanagari, not transliteration.
        assert any("ऀ" <= ch <= "ॿ" for ch in result["description_hi"])
        assert result["_model"] == "test/model:free"

    @pytest.mark.asyncio
    async def test_rejects_short_transcript(self):
        with pytest.raises(ValueError, match="5-2000"):
            await tools.generate_catalog("hi", "hi")

    @pytest.mark.asyncio
    async def test_rejects_overlong_transcript(self):
        with pytest.raises(ValueError, match="5-2000"):
            await tools.generate_catalog("x" * 2001, "hi")

    @pytest.mark.asyncio
    async def test_retries_then_succeeds(self):
        """First reply is junk; the strict retry must recover."""
        responses = [
            ("not json at all", ModelCall(model="bad/model:free")),
            (json.dumps(VALID_CATALOG), ModelCall(model="good/model:free")),
        ]
        mock = AsyncMock(side_effect=responses)
        with patch.object(tools.model_router, "complete", mock):
            result = await tools.generate_catalog("यह एक साड़ी है जो हाथ से बनी है", "hi")

        assert mock.await_count == 2
        assert result["_model"] == "good/model:free"

    @pytest.mark.asyncio
    async def test_devanagari_title_rejected(self):
        """Titles anchor search and must stay English even for a Hindi voice note."""
        bad = dict(VALID_CATALOG, title="हाथ से बनी वारंगल सूती साड़ी")
        mock = AsyncMock(return_value=(json.dumps(bad), ModelCall(model="m:free")))
        with patch.object(tools.model_router, "complete", mock):
            with pytest.raises(ValueError, match="failed validation"):
                await tools.generate_catalog("यह एक साड़ी है जो हाथ से बनी है", "hi")

    @pytest.mark.asyncio
    async def test_swapped_descriptions_rejected(self):
        """English and Hindi descriptions must not be transposed."""
        bad = dict(
            VALID_CATALOG,
            description_en=VALID_CATALOG["description_hi"],
            description_hi=VALID_CATALOG["description_en"],
        )
        mock = AsyncMock(return_value=(json.dumps(bad), ModelCall(model="m:free")))
        with patch.object(tools.model_router, "complete", mock):
            with pytest.raises(ValueError, match="failed validation"):
                await tools.generate_catalog("यह एक साड़ी है जो हाथ से बनी है", "hi")

    @pytest.mark.asyncio
    async def test_unparseable_retry_reports_as_validation_failure(self):
        """Both attempts unparseable -> a clean message, not a raw parser error."""
        mock = AsyncMock(return_value=("no json here", ModelCall(model="m:free")))
        with patch.object(tools.model_router, "complete", mock):
            with pytest.raises(ValueError, match="failed validation"):
                await tools.generate_catalog("यह एक साड़ी है जो हाथ से बनी है", "hi")

    @pytest.mark.asyncio
    async def test_raises_when_schema_invalid_twice(self):
        bad = dict(VALID_CATALOG, category="NotARealCategory")
        mock = AsyncMock(return_value=(json.dumps(bad), ModelCall(model="m:free")))
        with patch.object(tools.model_router, "complete", mock):
            with pytest.raises(ValueError, match="validation"):
                await tools.generate_catalog("यह एक साड़ी है जो हाथ से बनी है", "hi")

    @pytest.mark.asyncio
    async def test_image_context_is_passed_to_model(self):
        mock = _mock_complete(VALID_CATALOG)
        with patch.object(tools.model_router, "complete", mock):
            await tools.generate_catalog(
                "यह एक साड़ी है जो हाथ से बनी है", "hi", image_context=VALID_VISION_PLAN
            )

        sent = mock.await_args.args[0]
        user_msg = sent[-1]["content"]
        assert "product photo shows" in user_msg


# ── Pricing ────────────────────────────────────────────────────────────


class TestPricing:
    @pytest.mark.asyncio
    async def test_returns_clamped_price(self):
        with patch.object(tools.model_router, "complete", _mock_complete(VALID_PRICING)):
            result = await tools.suggest_price("Saree", "Textiles")

        assert result["suggested_price"] == 2400
        assert result["price_range"]["min"] <= 2400 <= result["price_range"]["max"]
        assert result["market_position"] == "Standard"

    @pytest.mark.asyncio
    async def test_suggested_price_forced_inside_range(self):
        """A model claiming a price outside its own range must be corrected."""
        broken = dict(VALID_PRICING, suggested_price=5000)
        with patch.object(tools.model_router, "complete", _mock_complete(broken)):
            result = await tools.suggest_price("Saree", "Textiles")

        assert result["price_range"]["min"] <= result["suggested_price"]
        assert result["suggested_price"] <= result["price_range"]["max"]

    @pytest.mark.asyncio
    async def test_swapped_range_is_reordered(self):
        broken = dict(VALID_PRICING, price_range={"min": 2900, "max": 2000})
        with patch.object(tools.model_router, "complete", _mock_complete(broken)):
            result = await tools.suggest_price("Saree", "Textiles")

        assert result["price_range"]["min"] <= result["price_range"]["max"]

    @pytest.mark.asyncio
    async def test_zero_price_rejected(self):
        broken = dict(VALID_PRICING, suggested_price=0)
        with patch.object(tools.model_router, "complete", _mock_complete(broken)):
            with pytest.raises(ValueError, match="usable suggested_price"):
                await tools.suggest_price("Saree", "Textiles")

    @pytest.mark.asyncio
    async def test_boolean_price_rejected(self):
        """float(True) == 1.0 would otherwise sneak through as a Rs 1 price."""
        broken = dict(VALID_PRICING, suggested_price=True)
        with patch.object(tools.model_router, "complete", _mock_complete(broken)):
            with pytest.raises(ValueError, match="usable suggested_price"):
                await tools.suggest_price("Saree", "Textiles")

    @pytest.mark.asyncio
    async def test_negative_price_rejected(self):
        broken = dict(VALID_PRICING, suggested_price=-500)
        with patch.object(tools.model_router, "complete", _mock_complete(broken)):
            with pytest.raises(ValueError, match="usable suggested_price"):
                await tools.suggest_price("Saree", "Textiles")

    @pytest.mark.asyncio
    async def test_confidence_clamped(self):
        broken = dict(VALID_PRICING, confidence=9.9)
        with patch.object(tools.model_router, "complete", _mock_complete(broken)):
            result = await tools.suggest_price("Saree", "Textiles")

        assert 0.0 <= result["confidence"] <= 1.0

    @pytest.mark.asyncio
    async def test_unknown_category_falls_back_to_other(self):
        mock = _mock_complete(VALID_PRICING)
        with patch.object(tools.model_router, "complete", mock):
            await tools.suggest_price("Saree", "Nonsense")

        assert "Category: Other" in mock.await_args.args[0][-1]["content"]


# ── Vision plan normalisation ──────────────────────────────────────────


class TestVisionPlan:
    @pytest.mark.asyncio
    async def test_clamps_out_of_range_values(self):
        wild = dict(
            VALID_VISION_PLAN,
            brightness_adjust=99,
            quality_score=5000,
            recommended_ratio="16:9",
            category="Nonsense",
        )
        with patch.object(tools.model_router, "complete", _mock_complete(wild)):
            plan, _ = await tools.analyze_image(b"fake-bytes")

        assert plan["brightness_adjust"] == 1.0
        assert plan["quality_score"] == 100
        assert plan["recommended_ratio"] == "1:1"
        assert plan["category"] == "Other"


# ── Orchestrator ───────────────────────────────────────────────────────


class TestOrchestrator:
    @pytest.mark.asyncio
    async def test_catalog_and_pricing_chain(self):
        """Pricing must consume the title the cataloguer produced."""
        catalog_mock = AsyncMock(return_value=dict(VALID_CATALOG, _model="c:free", _fallbacks=[]))
        pricing_mock = AsyncMock(return_value=dict(VALID_PRICING, _model="p:free", _fallbacks=[]))

        with patch.object(tools, "generate_catalog", catalog_mock), patch.object(
            tools, "suggest_price", pricing_mock
        ):
            result = await ArtisanAgent().run(
                transcript="यह एक हाथ से बुनी साड़ी है", language="hi"
            )

        statuses = {s.name: s.status for s in result.stages}
        assert statuses[STAGE_CATALOG] == "success"
        assert statuses[STAGE_PRICING] == "success"
        assert pricing_mock.await_args.kwargs["title"] == VALID_CATALOG["title"]

    @pytest.mark.asyncio
    async def test_catalog_failure_does_not_abort_run(self):
        """A failed stage is reported, not raised."""
        with patch.object(
            tools, "generate_catalog", AsyncMock(side_effect=ValueError("model broke"))
        ):
            result = await ArtisanAgent().run(transcript="यह एक साड़ी है", language="hi")

        statuses = {s.name: s.status for s in result.stages}
        assert statuses[STAGE_CATALOG] == "failed"
        # Nothing to price against, so pricing is skipped rather than failed.
        assert statuses[STAGE_PRICING] == "skipped"
        assert result.succeeded_any is False

    @pytest.mark.asyncio
    async def test_prices_from_photo_when_no_transcript(self):
        """A photo-only run should still reach a price via the vision plan."""
        enhanced = {
            "plan": VALID_VISION_PLAN,
            "plan_error": None,
            "model": "v:free",
            "fallbacks": [],
            "enhanced_bytes": b"png",
            "webp_bytes": b"webp",
            "thumbnail_bytes": b"thumb",
            "width": 1080,
            "height": 1080,
            "ratio": "1:1",
        }
        pricing_mock = AsyncMock(return_value=dict(VALID_PRICING, _model="p:free", _fallbacks=[]))

        with patch.object(
            tools, "enhance_product_image", AsyncMock(return_value=enhanced)
        ), patch.object(tools, "suggest_price", pricing_mock):
            result = await ArtisanAgent().run(image_bytes=b"fake")

        statuses = {s.name: s.status for s in result.stages}
        assert statuses[STAGE_IMAGE] == "success"
        assert statuses[STAGE_PRICING] == "success"
        assert pricing_mock.await_args.kwargs["title"] == VALID_VISION_PLAN["subject"]

    @pytest.mark.asyncio
    async def test_stage_subset_is_respected(self):
        catalog_mock = AsyncMock(return_value=dict(VALID_CATALOG, _model="c:free", _fallbacks=[]))
        with patch.object(tools, "generate_catalog", catalog_mock):
            result = await ArtisanAgent().run(
                transcript="यह एक साड़ी है जो हाथ से बनी है",
                stages=[STAGE_CATALOG],
            )

        assert {s.name for s in result.stages} == {STAGE_CATALOG}

    @pytest.mark.asyncio
    async def test_all_models_failed_is_reported_cleanly(self):
        """The artisan sees a readable message, never a raw provider error."""
        with patch.object(
            tools,
            "generate_catalog",
            AsyncMock(side_effect=AllModelsFailedError("catalog", ["a: 429", "b: 429"])),
        ):
            result = await ArtisanAgent().run(transcript="यह एक साड़ी है जो हाथ से बनी है")

        stage = next(s for s in result.stages if s.name == STAGE_CATALOG)
        assert stage.status == "failed"
        assert "rate-limited" in stage.error

    @pytest.mark.asyncio
    async def test_to_dict_excludes_raw_bytes(self):
        """The JSON body must never carry image bytes."""
        enhanced = {
            "plan": VALID_VISION_PLAN,
            "plan_error": None,
            "model": "v:free",
            "fallbacks": [],
            "enhanced_bytes": b"png",
            "webp_bytes": b"webp",
            "thumbnail_bytes": b"thumb",
            "width": 1080,
            "height": 1080,
            "ratio": "1:1",
        }
        with patch.object(
            tools, "enhance_product_image", AsyncMock(return_value=enhanced)
        ), patch.object(tools, "suggest_price", AsyncMock(side_effect=ValueError("skip"))):
            result = await ArtisanAgent().run(image_bytes=b"fake")

        payload = result.to_dict()
        assert "enhanced_bytes" not in json.dumps(payload)
        assert result.image_bytes["enhanced_bytes"] == b"png"


# ── Model router catalogue ─────────────────────────────────────────────


class TestLanguageDetection:
    def test_detects_devanagari(self):
        assert tools._is_devanagari("हाथ से बनी साड़ी") is True

    def test_plain_english_is_not_devanagari(self):
        assert tools._is_devanagari("Handwoven Cotton Saree") is False

    def test_english_with_one_hindi_term_tolerated(self):
        """A borrowed craft term must not disqualify an English title."""
        assert tools._is_devanagari("Handwoven Cotton Saree with साड़ी border") is False

    def test_empty_and_numeric_are_not_devanagari(self):
        assert tools._is_devanagari("") is False
        assert tools._is_devanagari("12345 -- 678") is False


class TestJsonExtraction:
    def test_ignores_braces_in_reasoning_prose(self):
        """Reasoning models narrate before answering; stray braces must not merge."""
        raw = (
            'We need a JSON object. Maybe {"draft": 1} is wrong, let me reconsider.\n'
            'Final answer:\n{"title": "Real Answer", "ok": true}'
        )
        assert tools.extract_json(raw)["title"] == "Real Answer"

    def test_prefers_last_fenced_block(self):
        raw = '```json\n{"a": 1}\n```\nOn reflection:\n```json\n{"a": 2}\n```'
        assert tools.extract_json(raw)["a"] == 2

    def test_handles_braces_inside_strings(self):
        raw = '{"note": "a } brace in a string", "ok": 1}'
        assert tools.extract_json(raw)["ok"] == 1


class TestRateLimiter:
    def setup_method(self):
        from app.api.agent import _clear_rate_limit_store

        _clear_rate_limit_store()

    def test_allows_up_to_limit_then_blocks(self):
        from fastapi import HTTPException

        from app.api.agent import _RATE_LIMIT_MAX, _check_rate_limit

        for _ in range(_RATE_LIMIT_MAX):
            _check_rate_limit("artisan:abc")

        with pytest.raises(HTTPException) as exc_info:
            _check_rate_limit("artisan:abc")
        assert exc_info.value.status_code == 429
        assert "Retry-After" in exc_info.value.headers

    def test_expired_keys_are_pruned(self):
        """Without pruning, every distinct IP would leak a list entry forever."""
        import time as _time

        from app.api.agent import (
            _RATE_LIMIT_WINDOW_SECONDS,
            _check_rate_limit,
            _rate_limit_store,
        )

        # Simulate a caller whose window has fully expired.
        _rate_limit_store["ip:1.2.3.4"] = [
            _time.time() - _RATE_LIMIT_WINDOW_SECONDS - 10
        ]
        _check_rate_limit("artisan:someone-else")

        assert "ip:1.2.3.4" not in _rate_limit_store

    def test_active_keys_survive_pruning(self):
        from app.api.agent import _check_rate_limit, _rate_limit_store

        _check_rate_limit("artisan:active")
        _check_rate_limit("artisan:other")
        assert "artisan:active" in _rate_limit_store


class TestModelCatalogue:
    def test_every_model_is_free_tier(self):
        """A paid slug slipping in would start charging the platform."""
        for model in list_free_models():
            assert model["slug"].endswith(":free"), model["slug"]

    def test_vision_chain_is_all_vision_capable(self):
        from app.agent.models import VISION_MODELS

        assert all(m.vision for m in VISION_MODELS)
        assert len(VISION_MODELS) >= 3
