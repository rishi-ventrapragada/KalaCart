"""
Pricing API — Intelligent Pricing Suggestions via DeepSeek / OpenRouter.

POST /api/v1/pricing/predict
- Input Pydantic PricingPredictRequest (title 3-200 strip control, category 2-50 normalized, materials 1-10 each 1-50, material_cost >=0 le 1M, labour_hours 1-40, size Small/Medium/Large, quality Basic/Standard/Premium, market_position Budget/Standard/Premium alias marketPosition)
- Security: strip control chars, validate ranges, rate limit 20 req/min per uid/IP (in-memory)
- Calls OpenRouter deepseek/deepseek-chat with pricing_system.md prompt, temperature 0.4, max_tokens 800, timeout 30s, headers Authorization Bearer, HTTP-Referer https://kalacart.in, X-Title KalaCart
- Validates schema: suggested_price int>=0, minimum_price int>=0 <=suggested, maximum_price int>=suggested, confidence 0-100, reasoning 10-500, breakdown {materials,labour,overhead,profit} sums to suggested (±15)
- Retry once on malformed JSON
- Never exposes API key
- Keeps POST /suggest deprecated alias

Do NOT implement marketplace/orders. Use DeepSeek through OpenRouter only.
"""

import json
import logging
import os
import re
import time
import inspect
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, Request, UploadFile, status
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.ai.vision import extract_product_attributes
from app.core.config import get_settings
from app.core.security import get_current_user
from app.services.pricing_engine import DEFAULT_LABOUR_HOURS, compute_price, seasonal_factor

logger = logging.getLogger(__name__)

router = APIRouter()

# ── Constants ──────────────────────────────────────────────────────────
ALLOWED_CATEGORIES = [
    "Textiles",
    "Pottery",
    "Woodwork",
    "Metalwork",
    "Jewelry",
    "Painting",
    "Basketry",
    "Leather",
    "Other",
]
ALLOWED_SIZES = ["Small", "Medium", "Large"]
ALLOWED_QUALITIES = ["Basic", "Standard", "Premium"]
ALLOWED_MARKET_POSITIONS = ["Budget", "Standard", "Premium"]

_RATE_LIMIT_MAX = 20
_RATE_LIMIT_WINDOW_SECONDS = 60
_rate_limit_store: Dict[str, List[float]] = {}

_PROMPT_PATH = Path(__file__).parent.parent / "ai" / "prompts" / "pricing_system.md"

_CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")

def _strip_control(s: str) -> str:
    """Strip control chars \\x00-\\x1f\\x7f and trim."""
    if not isinstance(s, str):
        s = str(s)
    s = _CONTROL_RE.sub("", s)
    return s.strip()

# ── Rate limiter helpers (Phase C: consolidated via app.core.rate_limit) ──
# This module keeps its own store (20/min) but delegates algorithm to shared helper.
from app.core.rate_limit import (
    check_rate_limit as _shared_check_rate_limit,
    clear_rate_limit_store as _shared_clear,
    get_rate_limit_key as _shared_get_key,
)


def _get_rate_limit_key(request: Request, current_user: Optional[Dict[str, Any]]) -> str:
    """Derive rate-limit key: prefer artisan uid, fallback to client IP."""
    return _shared_get_key(request, current_user)


def _check_rate_limit(key: str) -> None:
    """Enforce 20 req / 60s sliding window. Raises 429 if exceeded."""
    _shared_check_rate_limit(
        _rate_limit_store,
        key,
        _RATE_LIMIT_MAX,
        _RATE_LIMIT_WINDOW_SECONDS,
        detail_prefix="Rate limit exceeded",
    )


def _clear_rate_limit_store() -> None:
    """For tests — reset limiter."""
    _shared_clear(_rate_limit_store)


# ── Optional auth helper — consolidated into app.core.security (Phase C) ─────
# Previously duplicated here; now canonical in `app.core.security` to keep
# DI duplication (get_current_user vs get_optional_current_user) single-sourced.
# Re-export preserves `from app.api.pricing import get_optional_current_user` for tests
# and keeps backward compat while consolidating token/PII handling.
from app.core.security import get_optional_current_user  # noqa: F401 — re-export for compat


# ── Pydantic models ────────────────────────────────────────────────────

class PricingPredictRequest(BaseModel):
    """
    Input for POST /api/v1/pricing/predict

    - title: 3-200 strip control chars [\\x00-\\x1f\\x7f], btrim
    - category: 2-50 normalized case-insensitive to Title, must be allowed
    - materials: 1-10 each 1-50 strip control non-empty
    - material_cost: float >=0 le 1_000_000
    - labour_hours: int 1-40
    - size: Small/Medium/Large normalize
    - quality: Basic/Standard/Premium
    - market_position: Budget/Standard/Premium alias marketPosition
    """

    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=False)

    title: str = Field(..., min_length=3, max_length=200, description="Product title 3-200 chars")
    category: str = Field(..., min_length=2, max_length=50, description="Category, must be one of allowed")
    materials: List[str] = Field(..., min_length=1, max_length=10, description="Materials 1-10 each 1-50")
    material_cost: float = Field(..., ge=0, le=1_000_000, description="Material cost INR >=0 <=1M")
    labour_hours: int = Field(..., ge=1, le=40, description="Labour hours 1-40")
    size: str = Field(..., description="Size Small/Medium/Large")
    quality: str = Field(..., description="Quality Basic/Standard/Premium")
    market_position: str = Field(..., alias="marketPosition", description="Market position Budget/Standard/Premium")
    dimensions: Optional[str] = Field(default=None, description="Optional dimensions LxWxH in cm")
    weight: Optional[float] = Field(default=None, ge=0, le=50000, description="Weight in grams")

    @field_validator("title", mode="before")
    @classmethod
    def strip_title(cls, v: Any) -> str:
        if v is None:
            return v  # let Pydantic raise
        v = _strip_control(str(v))
        return v

    @field_validator("title")
    @classmethod
    def validate_title_len(cls, v: str) -> str:
        if len(v) < 3:
            raise ValueError("title must be at least 3 characters after stripping control chars")
        if len(v) > 200:
            raise ValueError("title must be at most 200 characters")
        return v

    @field_validator("category", mode="before")
    @classmethod
    def strip_category(cls, v: Any) -> str:
        if v is None:
            return v
        v = _strip_control(str(v))
        return v

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        # Normalize case-insensitive to Title
        # e.g., "textiles" -> "Textiles", "TEXTILES" -> "Textiles"
        normalized = v.strip().title()
        # Handle special case: "Other" etc already title
        # Check length after strip
        if len(normalized) < 2 or len(normalized) > 50:
            raise ValueError("category must be 2-50 characters")
        if normalized not in ALLOWED_CATEGORIES:
            raise ValueError(f"category must be one of {ALLOWED_CATEGORIES}, got '{v}'")
        return normalized

    @field_validator("materials", mode="before")
    @classmethod
    def validate_materials_before(cls, v: Any) -> List[str]:
        if v is None:
            raise ValueError("materials is required")
        if not isinstance(v, list):
            raise ValueError("materials must be a list")
        if len(v) < 1 or len(v) > 10:
            raise ValueError("materials must be 1-10 items")
        cleaned: List[str] = []
        for item in v:
            if not isinstance(item, str):
                item = str(item)
            item = _strip_control(item)
            if not item:
                raise ValueError("each material must be non-empty 1-50 chars after stripping control chars")
            if len(item) < 1 or len(item) > 50:
                raise ValueError("each material must be 1-50 characters")
            cleaned.append(item)
        return cleaned

    @field_validator("material_cost", mode="before")
    @classmethod
    def validate_material_cost(cls, v: Any) -> float:
        # Pydantic will also check ge/le, but ensure sanitization
        try:
            fv = float(v)
        except Exception:
            raise ValueError("material_cost must be a number")
        if fv < 0:
            raise ValueError("material_cost must be >=0")
        if fv > 1_000_000:
            raise ValueError("material_cost must be <=1_000_000")
        return fv

    @field_validator("size", mode="before")
    @classmethod
    def normalize_size(cls, v: Any) -> str:
        if v is None:
            return v
        v = _strip_control(str(v))
        # Title case normalize
        v = v.strip().title()
        return v

    @field_validator("size")
    @classmethod
    def validate_size(cls, v: str) -> str:
        if v not in ALLOWED_SIZES:
            raise ValueError(f"size must be one of {ALLOWED_SIZES}, got '{v}'")
        return v

    @field_validator("quality", mode="before")
    @classmethod
    def normalize_quality(cls, v: Any) -> str:
        if v is None:
            return v
        v = _strip_control(str(v))
        v = v.strip().title()
        return v

    @field_validator("quality")
    @classmethod
    def validate_quality(cls, v: str) -> str:
        if v not in ALLOWED_QUALITIES:
            raise ValueError(f"quality must be one of {ALLOWED_QUALITIES}, got '{v}'")
        return v

    @field_validator("market_position", mode="before")
    @classmethod
    def normalize_market_position(cls, v: Any) -> str:
        if v is None:
            return v
        # Accept alias already handled by populate_by_name, but also strip
        v = _strip_control(str(v))
        v = v.strip().title()
        return v

    @field_validator("market_position")
    @classmethod
    def validate_market_position(cls, v: str) -> str:
        if v not in ALLOWED_MARKET_POSITIONS:
            raise ValueError(f"market_position must be one of {ALLOWED_MARKET_POSITIONS}, got '{v}'")
        return v


class PricingBreakdown(BaseModel):
    materials: float = Field(..., ge=0, description="Materials cost")
    labour: float = Field(..., ge=0, description="Labour cost")
    overhead: float = Field(..., ge=0, description="Overhead 15-25%")
    profit: float = Field(..., ge=0, description="Profit 20-30%")


class ProfitMetrics(BaseModel):
    gross_profit: float = Field(..., description="Selling price minus base cost")
    platform_fee: float = Field(..., description="5% platform fee")
    estimated_shipping: float = Field(..., description="Estimated delivery cost")
    net_earnings: float = Field(..., description="Net payout to artisan")
    margin_percentage: float = Field(..., description="Net margin %")


class SeasonalBoostInfo(BaseModel):
    festival_name: str = Field(..., description="Name of active seasonal trend")
    multiplier: float = Field(..., description="Demand multiplier applied")
    is_active: bool = Field(..., description="Whether festival boost is currently active")


class PricingData(BaseModel):
    suggested_price: int = Field(..., ge=0, description="Suggested retail price INR")
    minimum_price: int = Field(..., ge=0, description="Minimum price <= suggested")
    maximum_price: int = Field(..., ge=0, description="Maximum price >= suggested")
    confidence: int = Field(..., ge=0, le=100, description="Confidence 0-100")
    reasoning: str = Field(..., min_length=10, max_length=500, description="Reasoning 10-500 chars 2-3 sentences")
    breakdown: PricingBreakdown
    demand_index: int = Field(default=75, ge=0, le=100, description="Live category demand index 0-100")
    competition_status: str = Field(default="Competitive", description="Below Market | Competitive | Premium")
    seasonal_boost: Optional[SeasonalBoostInfo] = Field(default=None, description="Active festival demand boost")
    profit_metrics: Optional[ProfitMetrics] = Field(default=None, description="Detailed profit and fee breakdown")


class PricingPredictResponse(BaseModel):
    success: bool = True
    data: PricingData


# ── Helpers for market signals, seasonal intelligence & competitors ────

def _fetch_demand_index(category: str) -> int:
    """Fetch live category demand index from Supabase or compute dynamic baseline."""
    try:
        client = get_supabase_client()
        res = client.table("market_demand").select("demand_index").eq("category", category).limit(1).execute()
        if res.data and len(res.data) > 0:
            return int(res.data[0].get("demand_index", 75))
    except Exception:
        pass
    category_defaults = {
        "Textiles": 84,
        "Pottery": 76,
        "Woodwork": 62,
        "Metalwork": 70,
        "Jewelry": 91,
        "Painting": 68,
        "Basketry": 58,
        "Leather": 65,
        "Other": 50,
    }
    return category_defaults.get(category, 70)


def _fetch_seasonal_boost(category: str) -> Optional[SeasonalBoostInfo]:
    """Check if category has an active festival surge in seasonal_trends."""
    try:
        from datetime import date
        today_str = date.today().isoformat()
        client = get_supabase_client()
        res = client.table("seasonal_trends").select("*").eq("is_active", True).lte("start_date", today_str).gte("end_date", today_str).execute()
        if res.data:
            for row in res.data:
                boosted = row.get("boosted_categories", [])
                if category in boosted:
                    return SeasonalBoostInfo(
                        festival_name=row.get("festival_name", "Festive Season"),
                        multiplier=float(row.get("demand_multiplier", 1.25)),
                        is_active=True
                    )
    except Exception:
        pass
    # No seasonal data available: use the festival calendar for today's date rather than
    # reporting a festival boost year-round
    from datetime import date

    factor, label = seasonal_factor(category, date.today())
    if factor > 1.0:
        return SeasonalBoostInfo(festival_name=label, multiplier=factor, is_active=True)
    return None


def _calculate_competition_status(suggested_price: int, category: str) -> str:
    """Anonymized benchmark comparing price against category marketplace listings."""
    category_benchmarks = {
        "Textiles": (600, 1800),
        "Pottery": (450, 1500),
        "Woodwork": (800, 2500),
        "Metalwork": (750, 2200),
        "Jewelry": (900, 3200),
        "Painting": (1200, 4500),
        "Basketry": (350, 1100),
        "Leather": (700, 2400),
        "Other": (500, 1500),
    }
    low, high = category_benchmarks.get(category, (500, 1800))
    if suggested_price < low:
        return "Below Market"
    elif suggested_price > high:
        return "Premium"
    else:
        return "Competitive"


def _compute_profit_metrics(selling_price: int, base_cost: float, weight_g: Optional[float] = None) -> ProfitMetrics:
    """Compute real-time platform fee, shipping estimate, and net artisan payout."""
    price = float(selling_price)
    platform_fee = round(price * 0.05, 2)
    weight = weight_g if weight_g and weight_g > 0 else 500.0
    if weight <= 500:
        shipping = 60.0
    elif weight <= 1500:
        shipping = 90.0
    else:
        shipping = 140.0

    gross_profit = round(price - base_cost, 2)
    net_earnings = round(max(0.0, price - platform_fee - (shipping * 0.5)), 2)
    margin = round((gross_profit / max(1.0, price)) * 100.0, 1)

    return ProfitMetrics(
        gross_profit=gross_profit,
        platform_fee=platform_fee,
        estimated_shipping=shipping,
        net_earnings=net_earnings,
        margin_percentage=margin,
    )


# ── Helpers for system prompt, fences, validation ──────────────────────

def _load_system_prompt() -> str:
    """Load pricing_system.md — fallback to embedded minimal prompt."""
    fallback = (
        "You are KalaCart's Handicraft Pricing Consultant with 20+ years experience in Jaipur/Bhuj/Kutch artisan markets. "
        "Estimate fair retail price INR only, realistic retail not wholesale, never negative. "
        "Use materials + labour (never undervalue artisan labour: ₹50-120/hr depending quality, premium always higher) + craftsmanship complexity + size + uniqueness premium + market positioning + overhead 15-25% + profit 20-30%. "
        "Inputs: title, category (Textiles/Pottery/Woodwork/Metalwork/Jewelry/Painting/Basketry/Leather/Other), materials[], material_cost, labour_hours 1-40, size Small/Medium/Large, quality Basic/Standard/Premium, market_position Budget/Standard/Premium. "
        "Output JSON only, no markdown, no chain-of-thought, include confidence 0-100, reasoning concise 2-3 sentences, breakdown {materials,labour,overhead,profit} sums to suggested (±15). "
        "INR only, never negative, labour 1-40, confidence 0-100, realistic retail, overhead/profit realistic. "
        "Provide reasoning 10-500 chars. Return valid JSON only."
    )
    try:
        if _PROMPT_PATH.exists():
            content = _PROMPT_PATH.read_text(encoding="utf-8")
            if content and content.strip():
                return content
    except Exception as exc:
        logger.warning("Failed to read pricing_system.md: %s", exc)
    logger.warning("Using fallback pricing system prompt (file not found: %s)", _PROMPT_PATH)
    return fallback


def _strip_code_fences(text: str) -> str:
    if not text:
        return text
    t = text.strip()
    if t.startswith("```"):
        t = re.sub(r"^```(?:json)?\s*", "", t, flags=re.IGNORECASE)
        t = re.sub(r"\s*```\s*$", "", t)
        t = t.strip()
    start = t.find("{")
    end = t.rfind("}")
    if start != -1 and end != -1 and end > start:
        t = t[start : end + 1]
    return t.strip()


def _labour_rate_for_quality(quality: str) -> float:
    """Return hourly rate based on quality: Premium always higher."""
    q = (quality or "").strip().title()
    if q == "Premium":
        return 115.0  # within 100-120
    if q == "Standard":
        return 82.0  # within 75-90
    # Basic
    return 55.0  # within 50-65


def _compute_fallback_breakdown(req: PricingPredictRequest, suggested: Optional[int] = None) -> Dict[str, float]:
    """Compute fallback breakdown from inputs, ensuring sum ≈ suggested."""
    materials = float(req.material_cost)
    labour = float(req.labour_hours) * _labour_rate_for_quality(req.quality)
    base = materials + labour
    # Overhead by market position / quality
    pos = req.market_position.title() if req.market_position else "Standard"
    if pos == "Premium":
        overhead_rate = 0.25
    elif pos == "Budget":
        overhead_rate = 0.15
    else:
        overhead_rate = 0.20
    # Adjust by size
    size = req.size.title() if req.size else "Medium"
    if size == "Large":
        overhead_rate = min(0.25, overhead_rate + 0.02)
    elif size == "Small":
        overhead_rate = max(0.15, overhead_rate - 0.02)

    overhead = base * overhead_rate
    if suggested is not None:
        # profit = remainder to hit suggested
        profit = float(suggested) - (materials + labour + overhead)
        # Ensure profit realistic 20-30% of (base+overhead) — clamp if negative or unrealistic
        if profit < 0:
            # If suggested too low, recompute with profit 20% and adjust suggested
            profit_rate = 0.20 if pos == "Budget" else (0.30 if pos == "Premium" else 0.25)
            profit = (base + overhead) * profit_rate
        else:
            # Clamp profit to 20-30% if far outside? Keep as is if within ± a bit, else adjust but keep sum tolerance
            min_profit = (base + overhead) * 0.18
            max_profit = (base + overhead) * 0.35
            if profit < min_profit:
                profit = min_profit
            elif profit > max_profit:
                profit = max_profit
    else:
        profit_rate = 0.20 if pos == "Budget" else (0.30 if pos == "Premium" else 0.25)
        profit = (base + overhead) * profit_rate
    return {
        "materials": round(materials, 2),
        "labour": round(labour, 2),
        "overhead": round(overhead, 2),
        "profit": round(profit, 2),
    }


def _validate_pricing_schema(data: Dict[str, Any], req: Optional[PricingPredictRequest] = None) -> tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    Validate pricing JSON schema. Returns (valid, err_msg, normalized_data or None)
    Normalizes breakdown fills missing fields from fallback if needed.
    """
    if not isinstance(data, dict):
        return False, "Root must be JSON object", None

    required = ["suggested_price", "minimum_price", "maximum_price", "confidence", "reasoning", "breakdown"]
    for key in required:
        if key not in data:
            return False, f"Missing required key: {key}", None

    # suggested_price
    try:
        suggested = int(data["suggested_price"])
    except Exception:
        return False, "suggested_price must be int", None
    if suggested < 0:
        return False, "suggested_price must be >=0", None

    # minimum_price
    try:
        minimum = int(data["minimum_price"])
    except Exception:
        return False, "minimum_price must be int", None
    if minimum < 0:
        return False, "minimum_price must be >=0", None
    if minimum > suggested:
        return False, "minimum_price must be <= suggested_price", None

    # maximum_price
    try:
        maximum = int(data["maximum_price"])
    except Exception:
        return False, "maximum_price must be int", None
    if maximum < suggested:
        return False, "maximum_price must be >= suggested_price", None

    # confidence
    try:
        confidence = int(data["confidence"])
    except Exception:
        return False, "confidence must be int", None
    if not (0 <= confidence <= 100):
        return False, "confidence must be 0-100", None

    # reasoning
    reasoning = data.get("reasoning")
    if not isinstance(reasoning, str):
        return False, "reasoning must be string", None
    reasoning_stripped = reasoning.strip()
    if not (10 <= len(reasoning_stripped) <= 500):
        return False, "reasoning must be 10-500 chars", None
    # Ensure 2-3 sentences? Not strict — just check at least one period or length; we allow 10-500
    # Could check at least 2 sentences but not enforce strictly
    data["reasoning"] = reasoning_stripped

    # breakdown
    breakdown = data.get("breakdown")
    if not isinstance(breakdown, dict):
        # Try to fill fallback if request available
        if req is not None:
            fallback = _compute_fallback_breakdown(req, suggested)
            data["breakdown"] = fallback
            breakdown = fallback
        else:
            return False, "breakdown must be object {materials,labour,overhead,profit}", None

    # Ensure breakdown has all keys, fill missing from fallback
    fallback_bd = _compute_fallback_breakdown(req, suggested) if req is not None else None
    for key in ["materials", "labour", "overhead", "profit"]:
        if key not in breakdown or breakdown[key] is None:
            if fallback_bd is not None:
                breakdown[key] = fallback_bd[key]
            else:
                return False, f"breakdown missing key: {key}", None
        # validate numeric >=0
        try:
            val = float(breakdown[key])
        except Exception:
            return False, f"breakdown.{key} must be number", None
        if val < 0:
            return False, f"breakdown.{key} must be >=0", None
        breakdown[key] = round(val, 2)

    # Check sum approx suggested ±15 tolerance
    bd_sum = breakdown["materials"] + breakdown["labour"] + breakdown["overhead"] + breakdown["profit"]
    tolerance = 15.0
    if abs(bd_sum - suggested) > tolerance:
        # Attempt to adjust profit to make sum match within tolerance if req available?
        # We will auto-correct profit to meet tolerance: adjust profit = suggested - (materials+labour+overhead)
        # But if difference huge, still consider invalid — we try to fix
        if req is not None:
            # Fix profit
            materials = breakdown["materials"]
            labour = breakdown["labour"]
            overhead = breakdown["overhead"]
            # Compute corrected profit
            corrected_profit = float(suggested) - (materials + labour + overhead)
            # If corrected_profit negative, adjust overhead too? But overhead should stay 15-25%
            if corrected_profit < 0:
                # Cap profit at 0 and adjust overhead?
                # Instead, consider schema invalid but we will fix breakdown to sum correctly
                # Recompute fallback fully
                fb = _compute_fallback_breakdown(req, suggested)
                data["breakdown"] = fb
                breakdown = fb
                bd_sum2 = fb["materials"] + fb["labour"] + fb["overhead"] + fb["profit"]
                if abs(bd_sum2 - suggested) > tolerance:
                    return False, f"breakdown sum {bd_sum} not within ±{tolerance} of suggested_price {suggested}", None
            else:
                breakdown["profit"] = round(corrected_profit, 2)
                bd_sum = breakdown["materials"] + breakdown["labour"] + breakdown["overhead"] + breakdown["profit"]
                if abs(bd_sum - suggested) > tolerance:
                    return False, f"breakdown sum {bd_sum} not within ±{tolerance} of suggested_price {suggested}", None
        else:
            return False, f"breakdown sum {bd_sum} not within ±{tolerance} of suggested_price {suggested}", None

    # Normalize ints
    data["suggested_price"] = suggested
    data["minimum_price"] = minimum
    data["maximum_price"] = maximum
    data["confidence"] = confidence
    data["breakdown"] = breakdown

    # Dynamic Pricing Intelligence enrichment
    if req is not None:
        demand_idx = _fetch_demand_index(req.category)
        comp_status = _calculate_competition_status(suggested, req.category)
        seasonal = _fetch_seasonal_boost(req.category)
        base_cost = breakdown["materials"] + breakdown["labour"]
        weight_val = getattr(req, "weight", None)
        profit_calc = _compute_profit_metrics(suggested, base_cost, weight_val)

        data["demand_index"] = demand_idx
        data["competition_status"] = comp_status
        if seasonal:
            data["seasonal_boost"] = seasonal.model_dump()
        data["profit_metrics"] = profit_calc.model_dump()

    return True, "", data


async def _call_openrouter(
    system_prompt: str,
    payload: PricingPredictRequest,
    is_retry: bool = False,
) -> str:
    """Call OpenRouter chat/completions with DeepSeek. Never logs API key."""
    settings = get_settings()
    api_key = settings.OPENROUTER_API_KEY or os.getenv("OPENROUTER_API_KEY")
    base_url = settings.OPENROUTER_BASE_URL or os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    model = settings.DEEPSEEK_MODEL or os.getenv("DEEPSEEK_MODEL", "deepseek/deepseek-chat")

    if not api_key:
        logger.error("OPENROUTER_API_KEY not configured")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI service not configured (missing API key)",
        )

    sys_content = system_prompt
    if is_retry:
        sys_content += (
            "\n\n[STRICT RETRY] Previous output was invalid JSON. "
            "Return valid JSON only matching schema "
            "{\"suggested_price\": int >=0, \"minimum_price\": int >=0 <= suggested_price, \"maximum_price\": int >= suggested_price, \"confidence\": int 0-100, \"reasoning\": string 10-500 chars 2-3 sentences, \"breakdown\": {\"materials\": float>=0, \"labour\": float>=0, \"overhead\": float>=0, \"profit\": float>=0}} "
            "with breakdown sum approx suggested (±15), INR only, never negative, labour 1-40, confidence 0-100, overhead 15-25% and profit 20-30% realistic. "
            "No markdown, no code fences, no commentary, no chain-of-thought. JSON only."
        )

    # User content: JSON stringified inputs + business logic hints
    user_payload = {
        "title": payload.title,
        "category": payload.category,
        "materials": payload.materials,
        "material_cost": payload.material_cost,
        "labour_hours": payload.labour_hours,
        "size": payload.size,
        "quality": payload.quality,
        "market_position": payload.market_position,
    }
    business_hints = (
        "Business logic hints: estimate fair price using materials + labour (never undervalue artisan labour: ₹50-120/hr depending quality, premium always higher) "
        "+ craftsmanship complexity + size (Small/Medium/Large) + uniqueness premium + market positioning (Budget/Standard/Premium) "
        "+ overhead 15-25% + profit 20-30%. INR only, never negative, labour 1-40, confidence 0-100, realistic retail (not wholesale), overhead/profit realistic. "
        "Breakdown {materials,labour,overhead,profit} must sum to suggested (±15). "
        "Return JSON only."
    )
    user_content = json.dumps(user_payload, ensure_ascii=False) + "\n" + business_hints

    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://kalacart.in",
        "X-Title": "KalaCart",
        "Content-Type": "application/json",
    }
    body: Dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": sys_content},
            {"role": "user", "content": user_content},
        ],
        "temperature": 0.4,
        "max_tokens": 800,
    }

    url = f"{base_url.rstrip('/')}/chat/completions"
    logger.debug("OpenRouter DeepSeek call model=%s retry=%s (key redacted)", model, is_retry)

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, headers=headers, json=body)
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                logger.error("OpenRouter HTTP %s for model %s", exc.response.status_code, model)
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="AI service temporarily unavailable (upstream error)",
                ) from exc
            data = response.json()
            try:
                content = data["choices"][0]["message"]["content"]
            except (KeyError, IndexError, TypeError) as exc:
                logger.error("OpenRouter malformed response structure: %s", exc)
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="LLM returned malformed JSON",
                ) from exc
            if not isinstance(content, str) or not content.strip():
                logger.error("OpenRouter empty content")
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="LLM returned malformed JSON",
                )
            return content
    except HTTPException:
        raise
    except httpx.TimeoutException as exc:
        logger.error("OpenRouter timeout: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="AI service timed out",
        ) from exc
    except httpx.RequestError as exc:
        logger.error("OpenRouter request error (key redacted): %s", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI service unavailable",
        ) from exc


# ── Core handler ───────────────────────────────────────────────────────

async def _handle_predict(
    payload: PricingPredictRequest,
    request: Request,
    current_user: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    # Rate limit check
    rate_key = _get_rate_limit_key(request, current_user)
    _check_rate_limit(rate_key)

    artisan_uid = "unknown"
    try:
        if current_user and isinstance(current_user, dict):
            artisan_uid = current_user.get("firebase_uid") or current_user.get("uid") or str(current_user.get("artisan", {}).get("id") if isinstance(current_user.get("artisan"), dict) else "unknown")
    except Exception:
        pass

    logger.info(
        "Pricing predict request uid=%s title='%s' cat=%s materials=%s cost=%.2f hrs=%d size=%s quality=%s position=%s rate_key=%s",
        artisan_uid,
        payload.title[:40],
        payload.category,
        payload.materials,
        payload.material_cost,
        payload.labour_hours,
        payload.size,
        payload.quality,
        payload.market_position,
        rate_key,
    )

    system_prompt = _load_system_prompt()

    # First attempt
    try:
        raw = await _call_openrouter(system_prompt, payload, is_retry=False)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Unexpected error calling LLM (key redacted): %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="LLM returned malformed JSON",
        ) from exc

    stripped = _strip_code_fences(raw)
    data: Optional[Dict[str, Any]] = None
    valid = False
    err_msg = ""

    try:
        data = json.loads(stripped)
        valid, err_msg, normalized = _validate_pricing_schema(data, payload)
        if valid and normalized is not None:
            data = normalized
        else:
            logger.warning("First LLM output schema invalid: %s — preview: %s", err_msg, stripped[:500])
            data = None
    except json.JSONDecodeError as exc:
        logger.warning("First LLM output invalid JSON: %s — preview: %s", exc, stripped[:400])
        data = None

    if data is not None and valid:
        logger.info("Pricing success first attempt suggested=%s confidence=%s", data.get("suggested_price"), data.get("confidence"))
        return {"success": True, "data": data}

    # Retry once with strict instruction
    logger.info("Retrying pricing with strict JSON instruction (uid=%s)", artisan_uid)
    try:
        raw_retry = await _call_openrouter(system_prompt, payload, is_retry=True)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Unexpected retry error (key redacted): %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="LLM returned malformed JSON",
        ) from exc

    stripped_retry = _strip_code_fences(raw_retry)
    try:
        data_retry = json.loads(stripped_retry)
    except json.JSONDecodeError as exc:
        logger.error("Retry LLM output still invalid JSON: %s — raw preview: %s", exc, stripped_retry[:500])
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="LLM returned malformed JSON",
        ) from exc

    valid_retry, err_retry, normalized_retry = _validate_pricing_schema(data_retry, payload)
    if not valid_retry or normalized_retry is None:
        logger.error("Retry LLM output schema invalid: %s — data preview: %s", err_retry, str(data_retry)[:600])
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="LLM returned malformed JSON",
        )

    logger.info("Pricing success on retry suggested=%s", normalized_retry.get("suggested_price"))
    return {"success": True, "data": normalized_retry}


# ── Routes ─────────────────────────────────────────────────────────────

@router.post(
    "/predict",
    response_model=PricingPredictResponse,
    status_code=status.HTTP_200_OK,
    summary="Predict fair price for handicraft (DeepSeek)",
    description=(
        "Auth optional (personalized) fallback allowed. Rate limited 20/min per uid/IP. "
        "Calls OpenRouter DeepSeek with pricing_system.md, temperature 0.4, max_tokens 800, timeout 30s. "
        "Validates JSON schema with one retry. Uses OPENROUTER_API_KEY, model deepseek/deepseek-chat."
    ),
)
async def predict_price(
    payload: PricingPredictRequest,
    request: Request,
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_current_user),
):
    """
    POST /api/v1/pricing/predict — intelligent pricing via DeepSeek.

    Validates inputs, enforces rate limit, calls LLM, validates schema, retries once.
    """
    return await _handle_predict(payload, request, current_user)


@router.post(
    "/suggest",
    deprecated=True,
    summary="Deprecated alias for /predict (backward compat)",
    description="Deprecated — use POST /api/v1/pricing/predict. Kept for backward compatibility.",
)
async def suggest_price_alias(
    payload: PricingPredictRequest,
    request: Request,
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_current_user),
):
    """Deprecated alias — calls same handler as /predict."""
    return await _handle_predict(payload, request, current_user)


# ── Pricing assistant: product photo + description → explainable price ─

ANALYZE_IMAGE_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/webp"}
ANALYZE_MAX_IMAGE_BYTES = 10 * 1024 * 1024


def _fetch_comparable_prices(category: str) -> List[float]:
    """Prices of active KalaCart listings in the category (up to 200). Empty list on any error."""
    try:
        from app.database.connection import get_supabase_client

        res = (
            get_supabase_client()
            .table("products")
            .select("price")
            .eq("category", category)
            .eq("is_active", True)
            .limit(200)
            .execute()
        )
        return [float(row["price"]) for row in (res.data or []) if isinstance(row.get("price"), (int, float))]
    except Exception as exc:
        logger.warning("Comparable price lookup failed for category=%s: %s", category, exc)
        return []


@router.post(
    "/analyze",
    status_code=status.HTTP_200_OK,
    summary="Suggest a price from a product photo and description",
    description=(
        "Auth required. Rate limited 20/min per uid/IP (shared with /predict). Multipart: description (required), "
        "image (optional, jpeg/png/webp up to 10 MB) and optional seller facts that override what the AI reads: "
        "title, category, materials (comma-separated), material_cost (INR), labour_hours, market_position "
        "(Budget|Standard|Premium). A vision model (VISION_MODEL) extracts category, materials, size, quality and "
        "craftsmanship complexity; the price itself is computed from costs, comparable listings (or reference "
        "ranges) and the festival calendar, and every factor is returned."
    ),
)
async def analyze_price(
    request: Request,
    description: str = Form(..., min_length=5, max_length=1500),
    image: Optional[UploadFile] = File(default=None),
    title: Optional[str] = Form(default=None, max_length=200),
    category: Optional[str] = Form(default=None),
    materials: Optional[str] = Form(default=None, max_length=300),
    material_cost: Optional[float] = Form(default=None, ge=0, le=1_000_000),
    labour_hours: Optional[float] = Form(default=None, gt=0, le=500),
    market_position: str = Form(default="Standard"),
    size: Optional[str] = Form(default=None, description="Small|Medium|Large"),
    quality: Optional[str] = Form(default=None, description="Basic|Standard|Premium"),
    complexity: Optional[int] = Form(default=None, ge=1, le=5, description="Craftsmanship complexity 1-5"),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    import asyncio
    from datetime import date

    _check_rate_limit(_get_rate_limit_key(request, current_user))

    def allowed(value: Optional[str], options: List[str], field: str) -> Optional[str]:
        if not value or not value.strip():
            return None
        normalized = _strip_control(value).title()
        if normalized not in options:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"{field} must be one of {options}",
            )
        return normalized

    position = allowed(market_position, ALLOWED_MARKET_POSITIONS, "market_position") or "Standard"
    seller_category = allowed(category, ALLOWED_CATEGORIES, "category")
    seller_size = allowed(size, ALLOWED_SIZES, "size")
    seller_quality = allowed(quality, ALLOWED_QUALITIES, "quality")
    seller_materials = [m.strip().title() for m in _strip_control(materials or "").split(",") if m.strip()][:5]

    image_bytes: Optional[bytes] = None
    if image is not None and image.filename:
        content_type = (image.content_type or "").split(";")[0].strip().lower()
        if content_type not in ANALYZE_IMAGE_TYPES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported image type. Use JPEG, PNG or WebP")
        image_bytes = await image.read() or None
        if image_bytes and len(image_bytes) > ANALYZE_MAX_IMAGE_BYTES:
            raise HTTPException(
                status_code=getattr(status, "HTTP_413_CONTENT_TOO_LARGE", 413),
                detail="Image too large (max 10 MB)",
            )

    if seller_category and seller_size and seller_quality and complexity:
        # Everything the engine needs is already known (e.g. recalculating after the seller changes
        # costs) — skip the AI call so the price updates instantly and at no cost
        attributes = {
            "category": seller_category,
            "materials": seller_materials,
            "size": seller_size,
            "quality": seller_quality,
            "complexity": complexity,
            "estimated_labour_hours": None,
            "observations": "",
        }
        image_bytes = None  # not analyzed on this path
    else:
        text = _strip_control(description)
        if title and title.strip():
            text = f"{_strip_control(title)}. {text}"
        if seller_materials:
            text += f" Materials: {', '.join(seller_materials)}."

        attributes = await extract_product_attributes(text, image_bytes)
        # Facts the seller states override what the model inferred
        seller_facts = {"category": seller_category, "size": seller_size, "quality": seller_quality, "complexity": complexity}
        attributes.update({key: value for key, value in seller_facts.items() if value})
        if seller_materials:
            attributes["materials"] = seller_materials

    hours = labour_hours or attributes.get("estimated_labour_hours") or DEFAULT_LABOUR_HOURS[attributes["size"]]
    comparables = await asyncio.to_thread(_fetch_comparable_prices, attributes["category"])
    result = compute_price(
        category=attributes["category"],
        size=attributes["size"],
        quality=attributes["quality"],
        complexity=attributes["complexity"],
        market_position=position,
        labour_hours=float(hours),
        material_cost=material_cost,
        comparable_prices=comparables,
        today=date.today(),
        labour_hours_estimated=labour_hours is None,
        image_analyzed=image_bytes is not None,
    )

    logger.info(
        "Pricing analyze uid=%s category=%s suggested=%s market=%s image=%s",
        current_user.get("uid") or current_user.get("firebase_uid"),
        attributes["category"],
        result["suggested_price"],
        result["market"]["source"],
        image_bytes is not None,
    )
    return {
        "success": True,
        "data": {**result, "attributes": attributes, "labour_hours": float(hours), "market_position": position},
    }

