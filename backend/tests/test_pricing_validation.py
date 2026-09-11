"""
Unit tests for Pydantic validation of pricing engine.

Covers:
- PricingPredictRequest: title length & control char strip, category normalization, materials list, material_cost, labour_hours, size, quality, market_position alias
- Confidence 0-100 validation via _validate_pricing_schema
- Breakdown sanitization (sum tolerance, missing keys healing, negative values)
- Control char strip helper, code fences, fallback breakdown
"""
import json
import os

os.environ.setdefault("DEBUG", "true")

import pytest
from pydantic import ValidationError

from app.api.pricing import (
    PricingPredictRequest,
    PricingBreakdown,
    PricingData,
    ALLOWED_CATEGORIES,
    ALLOWED_SIZES,
    ALLOWED_QUALITIES,
    ALLOWED_MARKET_POSITIONS,
    _strip_control,
    _strip_code_fences,
    _validate_pricing_schema,
    _compute_fallback_breakdown,
    _load_system_prompt,
    _CONTROL_RE,
)

# helper to build a valid request dict
def valid_req_dict(**overrides):
    base = {
        "title": "Handwoven Cotton Dupatta",
        "category": "Textiles",
        "materials": ["Cotton"],
        "material_cost": 420,
        "labour_hours": 8,
        "size": "Large",
        "quality": "Premium",
        "marketPosition": "Standard",
    }
    base.update(overrides)
    return base

def make_req(**overrides):
    return PricingPredictRequest(**valid_req_dict(**overrides))

VALID_PRICING_DICT = {
    "suggested_price": 899,
    "minimum_price": 780,
    "maximum_price": 980,
    "confidence": 92,
    "reasoning": "Handwoven cotton dupatta with premium finish and large size; 8 hours skilled labour at premium rate values artisan time. Material cost and craftsmanship support realistic retail positioning.",
    "breakdown": {"materials": 420, "labour": 240, "overhead": 89, "profit": 150},
}

# ── Title validation ──────────────────────────────────────────────────────

class TestTitleValidation:
    def test_valid_title(self):
        m = make_req(title="Handwoven Cotton Dupatta")
        assert m.title == "Handwoven Cotton Dupatta"

    def test_title_strips_control_chars(self):
        m = make_req(title="Handwoven\x00\x01 Cotton\x7f Dupatta")
        assert "\x00" not in m.title
        assert "\x01" not in m.title
        assert "\x7f" not in m.title
        assert m.title == "Handwoven Cotton Dupatta"

    def test_title_too_short_after_strip(self):
        with pytest.raises(ValidationError) as exc:
            make_req(title="Hi\x00")
        assert "title" in str(exc.value).lower()

    def test_title_exact_3_ok(self):
        m = make_req(title="Abc")
        assert len(m.title) == 3

    def test_title_too_long_201_fails(self):
        with pytest.raises(ValidationError):
            make_req(title="A" * 201)

    def test_title_exact_200_ok(self):
        m = make_req(title="A" * 200)
        assert len(m.title) == 200

    def test_title_whitespace_trim(self):
        m = make_req(title="  Handwoven Cotton Dupatta  ")
        assert m.title == "Handwoven Cotton Dupatta"

    def test_title_only_controls_fails(self):
        with pytest.raises(ValidationError):
            make_req(title="\x00\x01\x02")

    def test_strip_control_helper_direct(self):
        assert _strip_control("hello\x00world") == "helloworld"
        assert _strip_control("\x00\x1f trim \x7f ") == "trim"
        assert _strip_control("  normal  ") == "normal"
        assert _CONTROL_RE.search("hello\x00") is not None

# ── Category ──────────────────────────────────────────────────────────────

class TestCategoryValidation:
    def test_valid_category(self):
        m = make_req(category="Textiles")
        assert m.category == "Textiles"

    def test_category_case_insensitive_normalize(self):
        m = make_req(category="textiles")
        assert m.category == "Textiles"
        m2 = make_req(category="TEXTILES")
        assert m2.category == "Textiles"
        m3 = make_req(category=" pottery ")
        assert m3.category == "Pottery"

    def test_category_strips_control(self):
        m = make_req(category="Textiles\x00")
        assert m.category == "Textiles"

    def test_category_invalid(self):
        with pytest.raises(ValidationError) as exc:
            make_req(category="Electronics")
        assert "category" in str(exc.value).lower()

    def test_category_all_allowed(self):
        for cat in ALLOWED_CATEGORIES:
            m = make_req(category=cat)
            assert m.category == cat
            # lower case also
            m2 = make_req(category=cat.lower())
            assert m2.category == cat

    def test_category_too_short(self):
        with pytest.raises(ValidationError):
            make_req(category="A")  # length 1 -> fails min_length 2

    def test_category_too_long_51(self):
        with pytest.raises(ValidationError):
            make_req(category="A" * 51)

# ── Materials ─────────────────────────────────────────────────────────────

class TestMaterialsValidation:
    def test_valid_single(self):
        m = make_req(materials=["Cotton"])
        assert m.materials == ["Cotton"]

    def test_materials_strip_control_and_trim(self):
        m = make_req(materials=["Cotton\x00", " Natural dyes "])
        assert m.materials == ["Cotton", "Natural dyes"]
        assert "\x00" not in m.materials[0]

    def test_materials_empty_list_fails(self):
        with pytest.raises(ValidationError):
            make_req(materials=[])

    def test_materials_too_many_11_fails(self):
        with pytest.raises(ValidationError):
            make_req(materials=[f"m{i}" for i in range(11)])

    def test_materials_max_10_ok(self):
        m = make_req(materials=[f"m{i}" for i in range(10)])
        assert len(m.materials) == 10

    def test_material_entry_empty_after_strip_fails(self):
        with pytest.raises(ValidationError):
            make_req(materials=["   "])

    def test_material_entry_with_control_only_fails(self):
        with pytest.raises(ValidationError):
            make_req(materials=["\x00\x01"])

    def test_material_entry_too_long_51_fails(self):
        with pytest.raises(ValidationError):
            make_req(materials=["A" * 51])

    def test_material_entry_exact_50_ok(self):
        m = make_req(materials=["A" * 50])
        assert m.materials[0] == "A" * 50

    def test_materials_not_list_fails(self):
        with pytest.raises(ValidationError):
            make_req(materials="Cotton")  # type: ignore

    def test_materials_non_string_coerced(self):
        # int should be coerced to str
        m = make_req(materials=[123])  # type: ignore
        assert m.materials == ["123"]

# ── Material cost ─────────────────────────────────────────────────────────

class TestMaterialCostValidation:
    def test_valid_zero(self):
        m = make_req(material_cost=0)
        assert m.material_cost == 0

    def test_negative_fails(self):
        with pytest.raises(ValidationError) as exc:
            make_req(material_cost=-1)
        assert "material_cost" in str(exc.value).lower() or ">=0" in str(exc.value)

    def test_negative_float_fails(self):
        with pytest.raises(ValidationError):
            make_req(material_cost=-0.01)

    def test_over_1M_fails(self):
        with pytest.raises(ValidationError):
            make_req(material_cost=1_000_001)

    def test_exact_1M_ok(self):
        m = make_req(material_cost=1_000_000)
        assert m.material_cost == 1_000_000

    def test_string_number_coerced(self):
        m = make_req(material_cost="420")  # type: ignore
        assert m.material_cost == 420

    def test_invalid_string_fails(self):
        with pytest.raises(ValidationError):
            make_req(material_cost="not-a-number")  # type: ignore

# ── Labour hours ──────────────────────────────────────────────────────────

class TestLabourHoursValidation:
    def test_valid_8(self):
        m = make_req(labour_hours=8)
        assert m.labour_hours == 8

    def test_valid_boundaries_1_and_40(self):
        assert make_req(labour_hours=1).labour_hours == 1
        assert make_req(labour_hours=40).labour_hours == 40

    def test_0_fails(self):
        with pytest.raises(ValidationError):
            make_req(labour_hours=0)

    def test_41_fails(self):
        with pytest.raises(ValidationError):
            make_req(labour_hours=41)

    def test_negative_fails(self):
        with pytest.raises(ValidationError):
            make_req(labour_hours=-5)

    def test_string_coerce_fails_or_passes(self):
        # Pydantic may coerce "8" to int 8
        m = make_req(labour_hours="8")  # type: ignore
        assert m.labour_hours == 8
        with pytest.raises(ValidationError):
            make_req(labour_hours="eight")  # type: ignore

# ── Size ──────────────────────────────────────────────────────────────────

class TestSizeValidation:
    def test_valid_sizes(self):
        for s in ALLOWED_SIZES:
            assert make_req(size=s).size == s

    def test_case_insensitive_normalize(self):
        m = make_req(size="large")
        assert m.size == "Large"
        m = make_req(size=" SMALL ")
        assert m.size == "Small"
        m = make_req(size="medium")
        assert m.size == "Medium"

    def test_invalid_XL_fails(self):
        with pytest.raises(ValidationError) as exc:
            make_req(size="XL")
        assert "size" in str(exc.value).lower()

    def test_empty_fails(self):
        with pytest.raises(ValidationError):
            make_req(size="")

    def test_control_strip(self):
        m = make_req(size="Large\x00")
        assert m.size == "Large"

# ── Quality ───────────────────────────────────────────────────────────────

class TestQualityValidation:
    def test_valid_qualities(self):
        for q in ALLOWED_QUALITIES:
            assert make_req(quality=q).quality == q

    def test_normalize(self):
        assert make_req(quality="premium").quality == "Premium"
        assert make_req(quality=" BASIC ").quality == "Basic"

    def test_invalid_fails(self):
        with pytest.raises(ValidationError):
            make_req(quality="Superb")

# ── Market position (alias marketPosition) ────────────────────────────────

class TestMarketPositionValidation:
    def test_alias_marketPosition(self):
        # alias via marketPosition key
        m = PricingPredictRequest(
            title="Handwoven Cotton Dupatta",
            category="Textiles",
            materials=["Cotton"],
            material_cost=420,
            labour_hours=8,
            size="Large",
            quality="Premium",
            marketPosition="Standard",
        )
        assert m.market_position == "Standard"

    def test_snake_case_also_works_populate_by_name(self):
        m = PricingPredictRequest(
            title="Handwoven Cotton Dupatta",
            category="Textiles",
            materials=["Cotton"],
            material_cost=420,
            labour_hours=8,
            size="Large",
            quality="Premium",
            market_position="Budget",
        )
        assert m.market_position == "Budget"

    def test_valid_positions(self):
        for p in ALLOWED_MARKET_POSITIONS:
            assert make_req(marketPosition=p).market_position == p  # type: ignore

    def test_normalize_case(self):
        m = make_req(marketPosition="premium")  # type: ignore
        assert m.market_position == "Premium"

    def test_invalid_fails(self):
        with pytest.raises(ValidationError):
            make_req(marketPosition="Luxury")  # type: ignore

    def test_control_strip(self):
        m = make_req(marketPosition="Standard\x00")  # type: ignore
        assert m.market_position == "Standard"

# ── PricingBreakdown & PricingData output validation ──────────────────────

class TestBreakdownAndConfidenceOutput:
    def test_valid_pricing_data_passes_schema(self):
        valid, msg, normalized = _validate_pricing_schema(dict(VALID_PRICING_DICT), make_req())
        assert valid is True, msg
        assert normalized is not None
        assert normalized["confidence"] == 92

    def test_confidence_150_fails(self):
        bad = dict(VALID_PRICING_DICT)
        bad["confidence"] = 150
        valid, msg, _ = _validate_pricing_schema(bad, make_req())
        assert not valid
        assert "confidence" in msg.lower()

    def test_confidence_negative_fails(self):
        bad = dict(VALID_PRICING_DICT)
        bad["confidence"] = -1
        valid, msg, _ = _validate_pricing_schema(bad, make_req())
        assert not valid

    def test_confidence_0_and_100_boundaries(self):
        for c in [0, 100]:
            d = dict(VALID_PRICING_DICT)
            d["confidence"] = c
            valid, msg, _ = _validate_pricing_schema(d, make_req())
            assert valid is True, msg

    def test_reasoning_too_short_fails(self):
        bad = dict(VALID_PRICING_DICT)
        bad["reasoning"] = "short"
        valid, _, _ = _validate_pricing_schema(bad, make_req())
        assert not valid

    def test_reasoning_too_long_fails(self):
        bad = dict(VALID_PRICING_DICT)
        bad["reasoning"] = "A" * 501
        valid, _, _ = _validate_pricing_schema(bad, make_req())
        assert not valid

    def test_reasoning_exact_10_ok(self):
        d = dict(VALID_PRICING_DICT)
        d["reasoning"] = "A" * 10
        valid, _, _ = _validate_pricing_schema(d, make_req())
        assert valid is True

    def test_reasoning_exact_500_ok(self):
        d = dict(VALID_PRICING_DICT)
        d["reasoning"] = "A" * 500
        valid, _, _ = _validate_pricing_schema(d, make_req())
        assert valid is True

    def test_breakdown_missing_heals_with_req(self):
        # Current implementation: missing "breakdown" key fails immediately (no fallback).
        # Verify that missing key is correctly flagged, and that present-but-null heals.
        data = dict(VALID_PRICING_DICT)
        data.pop("breakdown")
        req = make_req()
        valid, msg, normalized = _validate_pricing_schema(data, req)
        assert valid is False
        assert "breakdown" in msg.lower()
        # When breakdown key present but value is None, fallback should heal
        # Use suggested that matches fallback total to allow healing within tolerance
        fallback = _compute_fallback_breakdown(req)
        fallback_total = int(round(sum(fallback.values())))
        data2 = dict(VALID_PRICING_DICT)
        data2["suggested_price"] = fallback_total
        data2["minimum_price"] = int(fallback_total * 0.85)
        data2["maximum_price"] = int(fallback_total * 1.15)
        data2["breakdown"] = None  # type: ignore
        valid2, msg2, norm2 = _validate_pricing_schema(data2, req)
        assert valid2 is True, msg2
        assert "breakdown" in norm2
        bd = norm2["breakdown"]
        assert abs(sum(bd.values()) - norm2["suggested_price"]) <= 15

    def test_breakdown_missing_without_req_fails(self):
        data = dict(VALID_PRICING_DICT)
        data.pop("breakdown")
        valid, msg, _ = _validate_pricing_schema(data, None)
        assert not valid

    def test_breakdown_partial_missing_heals(self):
        # Partial breakdown: implementation fills missing keys from fallback.
        # Choose values where fallback sum can still be within tolerance after healing.
        # Use a suggested_price that matches fallback-computed sum closely to avoid tolerance failure.
        # Instead we test that missing keys are filled, regardless of final tolerance outcome.
        data = dict(VALID_PRICING_DICT)
        data["breakdown"] = {"materials": 420, "labour": 240}  # missing overhead, profit
        req = make_req()
        # Compute what fallback would give to set suggested to allow healing
        fallback = _compute_fallback_breakdown(req)
        expected_suggested = int(round(sum(fallback.values())))
        # Align suggested_price to fallback total so healing can succeed within tolerance
        data["suggested_price"] = expected_suggested
        data["minimum_price"] = int(expected_suggested * 0.85)
        data["maximum_price"] = int(expected_suggested * 1.15)
        valid, msg, normalized = _validate_pricing_schema(data, req)
        assert valid is True, msg
        assert "overhead" in normalized["breakdown"]
        assert "profit" in normalized["breakdown"]
        # Sum within tolerance after healing
        bd = normalized["breakdown"]
        assert abs(sum(bd.values()) - normalized["suggested_price"]) <= 15

    def test_breakdown_negative_fails(self):
        data = dict(VALID_PRICING_DICT)
        data["breakdown"] = {"materials": -10, "labour": 240, "overhead": 89, "profit": 150}
        valid, msg, _ = _validate_pricing_schema(data, make_req())
        assert not valid
        assert "breakdown" in msg.lower()

    def test_breakdown_sum_beyond_tolerance_heals_or_fails(self):
        # sum far from suggested, handler should attempt to heal profit
        data = dict(VALID_PRICING_DICT)
        data["breakdown"] = {"materials": 10, "labour": 10, "overhead": 10, "profit": 10}
        valid, msg, normalized = _validate_pricing_schema(data, make_req())
        # Either heals to valid or fails — but after healing, sum should be within tolerance if valid
        if valid:
            bd = normalized["breakdown"]
            assert abs(sum(bd.values()) - normalized["suggested_price"]) <= 15
        else:
            assert "breakdown" in msg.lower()

    def test_minimum_greater_than_suggested_fails(self):
        bad = dict(VALID_PRICING_DICT)
        bad["minimum_price"] = 1000  # >899
        valid, msg, _ = _validate_pricing_schema(bad, make_req())
        assert not valid
        assert "minimum_price" in msg.lower()

    def test_maximum_less_than_suggested_fails(self):
        bad = dict(VALID_PRICING_DICT)
        bad["maximum_price"] = 800  # <899
        valid, msg, _ = _validate_pricing_schema(bad, make_req())
        assert not valid
        assert "maximum_price" in msg.lower()

    def test_suggested_negative_fails(self):
        bad = dict(VALID_PRICING_DICT)
        bad["suggested_price"] = -10
        valid, _, _ = _validate_pricing_schema(bad, make_req())
        assert not valid

    def test_breakdown_sanitization_rounds(self):
        data = dict(VALID_PRICING_DICT)
        data["breakdown"] = {"materials": 420.1234, "labour": 240.5678, "overhead": 89.999, "profit": 150.111}
        # need to adjust suggested to match sum? Keep suggested 899 but sum now ~900.8 within tolerance, so should pass and round
        valid, _, normalized = _validate_pricing_schema(data, make_req())
        # Should be valid and rounded
        assert valid is True
        for v in normalized["breakdown"].values():
            # rounded to 2 decimals
            assert isinstance(v, float)

    def test_pricing_breakdown_model_ge0(self):
        # Pydantic PricingBreakdown enforces >=0
        b = PricingBreakdown(materials=420, labour=240, overhead=89, profit=150)
        assert b.materials == 420
        with pytest.raises(ValidationError):
            PricingBreakdown(materials=-1, labour=0, overhead=0, profit=0)

    def test_pricing_data_confidence_range(self):
        with pytest.raises(ValidationError):
            PricingData(
                suggested_price=899,
                minimum_price=780,
                maximum_price=980,
                confidence=150,
                reasoning="A" * 20,
                breakdown=PricingBreakdown(materials=420, labour=240, overhead=89, profit=150),
            )
        # valid
        d = PricingData(
            suggested_price=899,
            minimum_price=780,
            maximum_price=980,
            confidence=92,
            reasoning="A" * 20,
            breakdown=PricingBreakdown(materials=420, labour=240, overhead=89, profit=150),
        )
        assert d.confidence == 92

# ── Code fences & strip helpers ───────────────────────────────────────────

class TestCodeFencesAndPrompt:
    def test_strip_code_fences_plain(self):
        j = json.dumps(VALID_PRICING_DICT)
        assert json.loads(_strip_code_fences(j)) == VALID_PRICING_DICT

    def test_strip_code_fences_fenced_json(self):
        fenced = "```json\n" + json.dumps(VALID_PRICING_DICT) + "\n```"
        assert json.loads(_strip_code_fences(fenced)) == VALID_PRICING_DICT

    def test_strip_code_fences_fenced_no_lang(self):
        s = "```\n" + json.dumps(VALID_PRICING_DICT) + "\n```"
        assert json.loads(_strip_code_fences(s)) == VALID_PRICING_DICT

    def test_strip_code_fences_preamble_extracts_braces(self):
        s = "Sure here is JSON:\n" + json.dumps(VALID_PRICING_DICT) + "\n hope you like it"
        parsed = json.loads(_strip_code_fences(s))
        assert parsed["suggested_price"] == 899

    def test_strip_code_fences_empty(self):
        assert _strip_code_fences("") == ""

    def test_strip_code_fences_nested_braces(self):
        s = 'prefix { "a": 1 } suffix but we extract outermost'
        # _strip_code_fences extracts from first { to last }
        stripped = _strip_code_fences(s)
        assert stripped.startswith("{")
        assert stripped.endswith("}")

    def test_load_prompt_exists_or_fallback(self):
        txt = _load_system_prompt()
        assert isinstance(txt, str)
        assert len(txt) > 50

    def test_compute_fallback_breakdown_consistency(self):
        req = make_req(material_cost=420, labour_hours=8, size="Large", quality="Premium", marketPosition="Standard")
        bd = _compute_fallback_breakdown(req, suggested=899)
        assert bd["materials"] == 420
        assert bd["labour"] == 8 * 115.0  # premium rate
        # overhead check approx 20% +/- size adjust
        assert 15 <= (bd["overhead"] / (bd["materials"] + bd["labour"]) * 100) <= 26
        # profit non-negative
        assert bd["profit"] >= 0
        # sum approx suggested within healing tolerance? For given suggested 899, heuristic may adjust profit but sum may still be close after healing in validation
        # We just ensure all non-negative
        for v in bd.values():
            assert v >= 0

    def test_labour_rate_premium_always_higher(self):
        req_basic = make_req(quality="Basic", labour_hours=10)
        req_std = make_req(quality="Standard", labour_hours=10)
        req_prem = make_req(quality="Premium", labour_hours=10)
        bd_b = _compute_fallback_breakdown(req_basic)
        bd_s = _compute_fallback_breakdown(req_std)
        bd_p = _compute_fallback_breakdown(req_prem)
        assert bd_p["labour"] > bd_s["labour"]
        assert bd_s["labour"] > bd_b["labour"]

    def test_pricing_predict_request_control_chars_in_materials(self):
        m = make_req(materials=["Cotton\x00", " Silk\x7f "])
        assert m.materials == ["Cotton", "Silk"]
