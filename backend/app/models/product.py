"""Pydantic models for Product domain — with category enum, validators, and storage URLs.
Extended 2026-09-01 with AI catalog fields: description_hi, materials/ seo_tags (JSONB), care_instruction.
Extended 2026-09-01 pricing: suggested_price, minimum_price, maximum_price, confidence_score,
price_breakdown JSONB, pricing_reason with aliases and range validators.
Handles both legacy TEXT[] (materials, tags) and new JSONB via dual-field + coalesce logic.
"""

import re
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class ProductCategory(str, Enum):
    """Allowed craft categories — extend as needed; validator allows custom fallback."""

    pottery = "pottery"
    textile = "textile"
    woodwork = "woodwork"
    jewelry = "jewelry"
    painting = "painting"
    metalwork = "metalwork"
    basketry = "basketry"
    leather = "leather"
    other = "other"


class ProductStatus(str, Enum):
    draft = "draft"
    published = "published"
    archived = "archived"


ALLOWED_CATEGORIES = {c.value for c in ProductCategory}

_CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")
_ALLOWED_BREAKDOWN_KEYS = {"materials", "labour", "overhead", "profit"}


def _strip_control(s: str) -> str:
    if not isinstance(s, str):
        s = str(s)
    return _CONTROL_RE.sub("", s).strip()


def _coerce_list_str(v: Any, max_items: int, max_len_each: int, min_items: int = 0, allow_empty: bool = True) -> Optional[List[str]]:
    """Coerce JSONB/TEXT[]/string input to List[str] with validation."""
    if v is None:
        return None if not allow_empty else []
    if isinstance(v, str):
        # Single comma-separated string -> list
        if not v.strip():
            return [] if allow_empty else None
        parts = [p.strip() for p in v.split(",") if p.strip()]
        v = parts
    if not isinstance(v, list):
        v = [str(v)]
    res = []
    for item in v:
        s = str(item).strip()
        if not s:
            continue
        if len(s) > max_len_each:
            raise ValueError(f"each item must be <= {max_len_each} chars (got {len(s)}: {s[:30]})")
        res.append(s)
    if len(res) < min_items:
        if not allow_empty and min_items > 0:
            raise ValueError(f"must have at least {min_items} items")
        # allow empty if min_items==0
    if len(res) > max_items:
        raise ValueError(f"cannot exceed {max_items} items (got {len(res)})")
    # uniqueness for seo_tags checked elsewhere if needed
    return res


def _validate_price_breakdown_dict(v: Any) -> Optional[Dict[str, float]]:
    """Validate price_breakdown dict: keys materials/labour/overhead/profit each >=0, allow partial."""
    if v is None:
        return None
    if isinstance(v, str):
        # Attempt JSON parse if stringified
        import json
        v_stripped = v.strip()
        if not v_stripped:
            return None
        if v_stripped == "{}":
            return {}
        try:
            parsed = json.loads(v_stripped)
            v = parsed
        except Exception:
            raise ValueError("price_breakdown must be a dict {materials,labour,overhead,profit}")
    if not isinstance(v, dict):
        raise ValueError("price_breakdown must be a dict {materials,labour,overhead,profit}")
    if len(v) == 0:
        return {}
    # Normalize keys lower
    normalized: Dict[str, float] = {}
    for k, val in v.items():
        key = str(k).strip().lower()
        if key not in _ALLOWED_BREAKDOWN_KEYS:
            raise ValueError(f"price_breakdown key must be one of {_ALLOWED_BREAKDOWN_KEYS}, got '{k}'")
        try:
            fval = float(val)
        except Exception:
            raise ValueError(f"price_breakdown.{key} must be a number >=0")
        if fval < 0:
            raise ValueError(f"price_breakdown.{key} must be >=0")
        # Round to 2 decimals
        normalized[key] = round(fval, 2)
    return normalized


class ProductBase(BaseModel):
    """Shared fields for product creation/update. Includes AI catalog + pricing extensions."""

    title: str = Field(..., min_length=2, max_length=200, description="Product title")
    description: str = Field(..., min_length=10, max_length=5000, description="AI-generated or artisan-provided description (English)")
    # New fields (nullable for backward compat)
    description_hi: Optional[str] = Field(default=None, max_length=2000, description="Hindi description (Devanagari), 20-500 chars when present")
    category: str = Field(..., description="Craft category, e.g., pottery, textile, woodwork")
    price: float = Field(..., ge=0, le=10_000_000, description="Listed price in INR")
    language: str = Field(default="en", min_length=2, max_length=10, description="Content language code")
    image_urls: Optional[List[str]] = Field(default=None, description="Supabase Storage public URLs")
    status: ProductStatus = Field(default=ProductStatus.published, description="Publishing status")
    is_active: bool = Field(default=True, description="Soft publish flag for marketplace filtering")

    # Catalog JSONB fields — prefer JSONB (materials_jsonb/seo_tags) but accept legacy TEXT[] alias
    # materials: maps to materials_jsonb JSONB (and legacy materials TEXT[] fallback)
    materials: Optional[List[str]] = Field(default=None, description="Materials list 1-5 items, each <=30 chars (JSONB materials_jsonb, fallback to legacy materials TEXT[])")
    seo_tags: Optional[List[str]] = Field(default=None, description="SEO tags 2-5 items, each 2-30 chars, unique (JSONB seo_tags)")
    care_instruction: Optional[str] = Field(default=None, max_length=500, description="Care instructions 5-500 chars (DB) 5-200 per spec")

    # Pricing fields — AI intelligent pricing (005_pricing_fields)
    suggested_price: Optional[float] = Field(default=None, ge=0, le=1_000_000, description="AI-suggested price INR, >=0 <=1M, nullable")
    minimum_price: Optional[float] = Field(default=None, ge=0, le=1_000_000, description="AI minimum price floor INR, >=0, must be <= suggested_price when both present")
    maximum_price: Optional[float] = Field(default=None, ge=0, le=1_000_000, description="AI maximum price ceiling INR, >=0, must be >= suggested_price when both present")
    confidence_score: Optional[int] = Field(default=None, ge=0, le=100, description="Confidence 0-100 INT, nullable (alias: confidence)")
    price_breakdown: Optional[Dict[str, float]] = Field(default=None, description="Breakdown JSONB {materials,labour,overhead,profit} each >=0, alias: breakdown")
    pricing_reason: Optional[str] = Field(default=None, max_length=1000, description="Pricing reasoning 10-1000 chars, strip control chars, alias: reasoning")

    @field_validator("title")
    @classmethod
    def _strip_title(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("title must be at least 2 characters")
        return v

    @field_validator("description")
    @classmethod
    def _strip_description(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 10:
            raise ValueError("description must be at least 10 characters")
        return v

    @field_validator("description_hi")
    @classmethod
    def _validate_description_hi(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v = v.strip()
        if v == "":
            return None
        if not (20 <= len(v) <= 2000):
            raise ValueError("description_hi must be 20-2000 chars when present")
        return v

    @field_validator("category")
    @classmethod
    def _normalize_category(cls, v: str) -> str:
        v = v.strip().lower()
        if not v:
            raise ValueError("category must not be empty")
        return v

    @field_validator("language")
    @classmethod
    def _normalize_language(cls, v: str) -> str:
        return v.strip().lower()

    @field_validator("image_urls")
    @classmethod
    def _validate_image_urls(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is None:
            return v
        if len(v) > 10:
            raise ValueError("image_urls cannot exceed 10 items")
        for url in v:
            if not url.startswith(("http://", "https://")):
                raise ValueError(f"Invalid image URL: {url}")
        return v

    @field_validator("price")
    @classmethod
    def _round_price(cls, v: float) -> float:
        return round(float(v), 2)

    @field_validator("suggested_price", mode="before")
    @classmethod
    def _coerce_suggested(cls, v: Any) -> Optional[float]:
        if v is None or v == "":
            return None
        try:
            f = float(v)
        except Exception:
            raise ValueError("suggested_price must be a number")
        if f < 0:
            raise ValueError("suggested_price must be >=0")
        if f > 1_000_000:
            raise ValueError("suggested_price must be <= 1_000_000")
        return round(f, 2)

    @field_validator("minimum_price", mode="before")
    @classmethod
    def _coerce_minimum(cls, v: Any) -> Optional[float]:
        if v is None or v == "":
            return None
        try:
            f = float(v)
        except Exception:
            raise ValueError("minimum_price must be a number")
        if f < 0:
            raise ValueError("minimum_price must be >=0")
        if f > 1_000_000:
            raise ValueError("minimum_price must be <= 1_000_000")
        return round(f, 2)

    @field_validator("maximum_price", mode="before")
    @classmethod
    def _coerce_maximum(cls, v: Any) -> Optional[float]:
        if v is None or v == "":
            return None
        try:
            f = float(v)
        except Exception:
            raise ValueError("maximum_price must be a number")
        if f < 0:
            raise ValueError("maximum_price must be >=0")
        if f > 1_000_000:
            raise ValueError("maximum_price must be <= 1_000_000")
        return round(f, 2)

    @field_validator("confidence_score", mode="before")
    @classmethod
    def _coerce_confidence(cls, v: Any) -> Optional[int]:
        if v is None or v == "":
            return None
        try:
            iv = int(float(v)) if isinstance(v, str) and "." in v else int(v)
        except Exception:
            raise ValueError("confidence_score must be integer 0-100")
        if not (0 <= iv <= 100):
            raise ValueError("confidence_score must be between 0 and 100")
        return iv

    @field_validator("price_breakdown", mode="before")
    @classmethod
    def _coerce_price_breakdown(cls, v: Any) -> Optional[Dict[str, float]]:
        if v is None:
            return None
        # Allow empty dict/list string cases
        if isinstance(v, dict) and len(v) == 0:
            return {}
        return _validate_price_breakdown_dict(v)

    @field_validator("price_breakdown")
    @classmethod
    def _validate_breakdown_values(cls, v: Optional[Dict[str, float]]) -> Optional[Dict[str, float]]:
        if v is None:
            return None
        if len(v) == 0:
            return v
        for k, val in v.items():
            if val < 0:
                raise ValueError(f"price_breakdown.{k} must be >=0")
        return v

    @field_validator("pricing_reason", mode="before")
    @classmethod
    def _coerce_pricing_reason(cls, v: Any) -> Optional[str]:
        if v is None:
            return None
        if not isinstance(v, str):
            v = str(v)
        # Strip control chars
        v = _strip_control(v)
        if v == "":
            return None
        return v

    @field_validator("pricing_reason")
    @classmethod
    def _validate_pricing_reason(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v = _strip_control(v)
        if v == "":
            return None
        if not (10 <= len(v) <= 1000):
            raise ValueError("pricing_reason must be 10-1000 chars when present")
        return v

    @field_validator("materials", mode="before")
    @classmethod
    def _coerce_materials(cls, v: Any) -> Optional[List[str]]:
        # Accept TEXT[] legacy, JSONB list, or comma-separated string
        if v is None:
            return None
        return _coerce_list_str(v, max_items=5, max_len_each=30, min_items=0, allow_empty=True)

    @field_validator("materials")
    @classmethod
    def _validate_materials(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is None:
            return v
        if len(v) == 0:
            return v  # allow empty list for backward compat; require 1-5 when AI populates
        if not (1 <= len(v) <= 5):
            raise ValueError("materials must be 1-5 items when provided")
        for m in v:
            if not m.strip() or len(m) > 30:
                raise ValueError("each material must be non-empty <=30 chars")
        return [m.strip() for m in v]

    @field_validator("seo_tags", mode="before")
    @classmethod
    def _coerce_seo_tags(cls, v: Any) -> Optional[List[str]]:
        if v is None:
            return None
        return _coerce_list_str(v, max_items=5, max_len_each=30, min_items=0, allow_empty=True)

    @field_validator("seo_tags")
    @classmethod
    def _validate_seo_tags(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is None:
            return v
        if len(v) == 0:
            return v
        if not (2 <= len(v) <= 5):
            raise ValueError("seo_tags must be 2-5 items when provided")
        for t in v:
            if not (2 <= len(t.strip()) <= 30):
                raise ValueError("each seo_tag must be 2-30 chars")
        lowered = [t.strip().lower() for t in v]
        if len(lowered) != len(set(lowered)):
            raise ValueError("seo_tags must be unique (case-insensitive)")
        return [t.strip() for t in v]

    @field_validator("care_instruction")
    @classmethod
    def _validate_care(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v = v.strip()
        if v == "":
            return None
        if not (5 <= len(v) <= 500):
            raise ValueError("care_instruction must be 5-500 chars (spec 5-200)")
        # Strip control chars
        v = re.sub(r"[\x00-\x1f\x7f]", "", v).strip()
        if len(v) < 5:
            raise ValueError("care_instruction must be >=5 chars after stripping")
        return v

    @model_validator(mode="before")
    @classmethod
    def _handle_aliases(cls, data: Any) -> Any:
        """Handle alias fields for backward compatibility: materials TEXT[] vs materials_jsonb, tags vs seo_tags, pricing aliases."""
        if not isinstance(data, dict):
            return data
        # If payload contains legacy 'tags' but not 'seo_tags', migrate it
        if "seo_tags" not in data or data.get("seo_tags") is None:
            if "tags" in data and data["tags"] is not None:
                data["seo_tags"] = data.pop("tags")
            # also handle seoTags camelCase from Android
            elif "seoTags" in data:
                data["seo_tags"] = data.pop("seoTags")
        # materials aliases: materials_jsonb, materialsJsonb, legacy materials
        if "materials" not in data or data.get("materials") is None:
            for alias in ("materials_jsonb", "materialsJsonb", "materials_json"):
                if alias in data and data[alias] is not None:
                    data["materials"] = data.pop(alias)
                    break
        # care alias: care -> care_instruction
        if "care_instruction" not in data or data.get("care_instruction") is None:
            if "care" in data and data["care"] is not None:
                data["care_instruction"] = data.pop("care")
        # description_hi alias
        if "description_hi" not in data:
            for alias in ("descriptionHi", "description_hindi", "hindi_description"):
                if alias in data:
                    data["description_hi"] = data.pop(alias)
                    break
        # description_en alias -> description (English)
        if "description_en" in data and ("description" not in data or not data.get("description")):
            # Only if description is missing/empty, use description_en
            if data.get("description_en"):
                data["description"] = data.pop("description_en")
            else:
                data.pop("description_en", None)

        # Pricing aliases: confidence -> confidence_score, breakdown -> price_breakdown, reasoning -> pricing_reason
        # Also handle camelCase variants
        if "confidence_score" not in data or data.get("confidence_score") is None:
            for alias in ("confidence", "confidenceScore"):
                if alias in data and data[alias] is not None:
                    data["confidence_score"] = data.pop(alias)
                    break
        if "price_breakdown" not in data or data.get("price_breakdown") is None:
            for alias in ("breakdown", "priceBreakdown", "break_down", "pricing_breakdown"):
                if alias in data and data[alias] is not None:
                    data["price_breakdown"] = data.pop(alias)
                    break
        if "pricing_reason" not in data or data.get("pricing_reason") is None:
            for alias in ("reasoning", "pricingReason", "price_reason", "reason"):
                if alias in data and data[alias] is not None:
                    data["pricing_reason"] = data.pop(alias)
                    break
        # Also handle suggested/min/max camelCase if frontend uses it
        if "suggested_price" not in data or data.get("suggested_price") is None:
            for alias in ("suggestedPrice", "suggestedprice"):
                if alias in data and data[alias] is not None:
                    data["suggested_price"] = data.pop(alias)
                    break
        if "minimum_price" not in data or data.get("minimum_price") is None:
            for alias in ("minimumPrice", "min_price", "minPrice"):
                if alias in data and data[alias] is not None:
                    data["minimum_price"] = data.pop(alias)
                    break
        if "maximum_price" not in data or data.get("maximum_price") is None:
            for alias in ("maximumPrice", "max_price", "maxPrice"):
                if alias in data and data[alias] is not None:
                    data["maximum_price"] = data.pop(alias)
                    break
        return data

    @model_validator(mode="after")
    def _validate_pricing_ranges(self) -> "ProductBase":
        """Ensure minimum <= suggested <= maximum when both present, allow partial."""
        suggested = self.suggested_price
        minimum = self.minimum_price
        maximum = self.maximum_price
        if minimum is not None and suggested is not None:
            if minimum > suggested:
                raise ValueError(f"minimum_price ({minimum}) cannot exceed suggested_price ({suggested})")
        if maximum is not None and suggested is not None:
            if maximum < suggested:
                raise ValueError(f"maximum_price ({maximum}) cannot be less than suggested_price ({suggested})")
        if minimum is not None and maximum is not None:
            if minimum > maximum:
                raise ValueError(f"minimum_price ({minimum}) cannot exceed maximum_price ({maximum})")
        return self


class ProductCreate(ProductBase):
    """Payload for creating a product."""

    artisan_id: str = Field(..., description="Foreign key to artisans.id (UUID)")
    ai_enhanced: bool = Field(default=False, description="Whether AI enhanced description/image")
    stock_quantity: Optional[int] = Field(default=1, ge=0, description="Inventory count")

    # Override to keep compatibility: suggested_price etc inherited from ProductBase already validated
    # No duplication needed; ProductBase pricing validators apply.


class ProductUpdate(BaseModel):
    """Partial update model — all fields optional; ownership checked in service. Includes pricing fields."""

    title: Optional[str] = Field(default=None, min_length=2, max_length=200)
    description: Optional[str] = Field(default=None, min_length=10, max_length=5000)
    description_hi: Optional[str] = Field(default=None, max_length=2000)
    price: Optional[float] = Field(default=None, ge=0, le=10_000_000)
    category: Optional[str] = Field(default=None, max_length=50)
    language: Optional[str] = Field(default=None, min_length=2, max_length=10)
    image_urls: Optional[List[str]] = None
    suggested_price: Optional[float] = Field(default=None, ge=0, le=1_000_000, description="AI-suggested price")
    minimum_price: Optional[float] = Field(default=None, ge=0, le=1_000_000, description="Minimum price floor")
    maximum_price: Optional[float] = Field(default=None, ge=0, le=1_000_000, description="Maximum price ceiling")
    confidence_score: Optional[int] = Field(default=None, ge=0, le=100, description="Confidence 0-100")
    price_breakdown: Optional[Dict[str, float]] = Field(default=None, description="Breakdown {materials,labour,overhead,profit}")
    pricing_reason: Optional[str] = Field(default=None, max_length=1000, description="Pricing reasoning 10-1000 chars")
    ai_enhanced: Optional[bool] = None
    status: Optional[ProductStatus] = None
    is_active: Optional[bool] = None
    stock_quantity: Optional[int] = Field(default=None, ge=0)

    # Catalog fields
    materials: Optional[List[str]] = None
    seo_tags: Optional[List[str]] = None
    care_instruction: Optional[str] = Field(default=None, max_length=500)

    @field_validator("title")
    @classmethod
    def _strip_title_opt(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if len(v) < 2:
                raise ValueError("title must be at least 2 characters")
        return v

    @field_validator("description_hi")
    @classmethod
    def _validate_description_hi_opt(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v = v.strip()
        if v == "":
            return None
        if not (20 <= len(v) <= 2000):
            raise ValueError("description_hi must be 20-2000 chars when present")
        return v

    @field_validator("category")
    @classmethod
    def _normalize_category_opt(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip().lower()
            if not v:
                raise ValueError("category must not be empty")
        return v

    @field_validator("price")
    @classmethod
    def _round_price_opt(cls, v: Optional[float]) -> Optional[float]:
        if v is not None:
            return round(float(v), 2)
        return v

    @field_validator("suggested_price", mode="before")
    @classmethod
    def _coerce_suggested_opt(cls, v: Any) -> Optional[float]:
        if v is None or v == "":
            return None
        try:
            f = float(v)
        except Exception:
            raise ValueError("suggested_price must be a number")
        if f < 0:
            raise ValueError("suggested_price must be >=0")
        if f > 1_000_000:
            raise ValueError("suggested_price must be <=1_000_000")
        return round(f, 2)

    @field_validator("minimum_price", mode="before")
    @classmethod
    def _coerce_minimum_opt(cls, v: Any) -> Optional[float]:
        if v is None or v == "":
            return None
        try:
            f = float(v)
        except Exception:
            raise ValueError("minimum_price must be a number")
        if f < 0:
            raise ValueError("minimum_price must be >=0")
        if f > 1_000_000:
            raise ValueError("minimum_price must be <=1_000_000")
        return round(f, 2)

    @field_validator("maximum_price", mode="before")
    @classmethod
    def _coerce_maximum_opt(cls, v: Any) -> Optional[float]:
        if v is None or v == "":
            return None
        try:
            f = float(v)
        except Exception:
            raise ValueError("maximum_price must be a number")
        if f < 0:
            raise ValueError("maximum_price must be >=0")
        if f > 1_000_000:
            raise ValueError("maximum_price must be <=1_000_000")
        return round(f, 2)

    @field_validator("confidence_score", mode="before")
    @classmethod
    def _coerce_confidence_opt(cls, v: Any) -> Optional[int]:
        if v is None or v == "":
            return None
        try:
            iv = int(float(v)) if isinstance(v, str) and "." in str(v) else int(v)
        except Exception:
            raise ValueError("confidence_score must be integer 0-100")
        if not (0 <= iv <= 100):
            raise ValueError("confidence_score must be between 0 and 100")
        return iv

    @field_validator("price_breakdown", mode="before")
    @classmethod
    def _coerce_breakdown_opt(cls, v: Any) -> Optional[Dict[str, float]]:
        if v is None:
            return None
        if isinstance(v, dict) and len(v) == 0:
            return {}
        return _validate_price_breakdown_dict(v)

    @field_validator("pricing_reason", mode="before")
    @classmethod
    def _coerce_reason_opt(cls, v: Any) -> Optional[str]:
        if v is None:
            return None
        if not isinstance(v, str):
            v = str(v)
        v = _strip_control(v)
        if v == "":
            return None
        return v

    @field_validator("pricing_reason")
    @classmethod
    def _validate_reason_opt(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v = _strip_control(v)
        if v == "":
            return None
        if not (10 <= len(v) <= 1000):
            raise ValueError("pricing_reason must be 10-1000 chars when present")
        return v

    @field_validator("image_urls")
    @classmethod
    def _validate_image_urls_opt(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is None:
            return v
        if len(v) > 10:
            raise ValueError("image_urls cannot exceed 10 items")
        for url in v:
            if not url.startswith(("http://", "https://")):
                raise ValueError(f"Invalid image URL: {url}")
        return v

    @field_validator("materials", mode="before")
    @classmethod
    def _coerce_materials_opt(cls, v: Any) -> Optional[List[str]]:
        if v is None:
            return None
        return _coerce_list_str(v, max_items=5, max_len_each=30, min_items=0, allow_empty=True)

    @field_validator("seo_tags", mode="before")
    @classmethod
    def _coerce_seo_tags_opt(cls, v: Any) -> Optional[List[str]]:
        if v is None:
            return None
        return _coerce_list_str(v, max_items=5, max_len_each=30, min_items=0, allow_empty=True)

    @field_validator("care_instruction")
    @classmethod
    def _validate_care_opt(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v = v.strip()
        if v == "":
            return None
        if not (5 <= len(v) <= 500):
            raise ValueError("care_instruction must be 5-500 chars")
        v = re.sub(r"[\x00-\x1f\x7f]", "", v).strip()
        return v

    @model_validator(mode="before")
    @classmethod
    def _handle_aliases_opt(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        if "seo_tags" not in data or data.get("seo_tags") is None:
            if "tags" in data and data["tags"] is not None:
                data["seo_tags"] = data.pop("tags")
            elif "seoTags" in data:
                data["seo_tags"] = data.pop("seoTags")
        if "materials" not in data or data.get("materials") is None:
            for alias in ("materials_jsonb", "materialsJsonb"):
                if alias in data and data[alias] is not None:
                    data["materials"] = data.pop(alias)
                    break
        if "care_instruction" not in data or data.get("care_instruction") is None:
            if "care" in data and data["care"] is not None:
                data["care_instruction"] = data.pop("care")
        # Pricing aliases
        if "confidence_score" not in data or data.get("confidence_score") is None:
            for alias in ("confidence", "confidenceScore"):
                if alias in data and data[alias] is not None:
                    data["confidence_score"] = data.pop(alias)
                    break
        if "price_breakdown" not in data or data.get("price_breakdown") is None:
            for alias in ("breakdown", "priceBreakdown", "break_down", "pricing_breakdown"):
                if alias in data and data[alias] is not None:
                    data["price_breakdown"] = data.pop(alias)
                    break
        if "pricing_reason" not in data or data.get("pricing_reason") is None:
            for alias in ("reasoning", "pricingReason", "price_reason", "reason"):
                if alias in data and data[alias] is not None:
                    data["pricing_reason"] = data.pop(alias)
                    break
        # suggested/min/max aliases
        if "suggested_price" not in data or data.get("suggested_price") is None:
            for alias in ("suggestedPrice",):
                if alias in data and data[alias] is not None:
                    data["suggested_price"] = data.pop(alias)
                    break
        if "minimum_price" not in data or data.get("minimum_price") is None:
            for alias in ("minimumPrice", "min_price", "minPrice"):
                if alias in data and data[alias] is not None:
                    data["minimum_price"] = data.pop(alias)
                    break
        if "maximum_price" not in data or data.get("maximum_price") is None:
            for alias in ("maximumPrice", "max_price", "maxPrice"):
                if alias in data and data[alias] is not None:
                    data["maximum_price"] = data.pop(alias)
                    break
        # Also handle description_hi fallback
        if "description_hi" not in data:
            for alias in ("descriptionHi", "description_hindi", "hindi_description"):
                if alias in data:
                    data["description_hi"] = data.pop(alias)
                    break
        return data

    @model_validator(mode="after")
    def _validate_pricing_ranges_opt(self) -> "ProductUpdate":
        suggested = self.suggested_price
        minimum = self.minimum_price
        maximum = self.maximum_price
        if minimum is not None and suggested is not None:
            if minimum > suggested:
                raise ValueError(f"minimum_price ({minimum}) cannot exceed suggested_price ({suggested})")
        if maximum is not None and suggested is not None:
            if maximum < suggested:
                raise ValueError(f"maximum_price ({maximum}) cannot be less than suggested_price ({suggested})")
        if minimum is not None and maximum is not None:
            if minimum > maximum:
                raise ValueError(f"minimum_price ({minimum}) cannot exceed maximum_price ({maximum})")
        return self


class ProductResponse(ProductBase):
    """Response model with DB-generated fields."""

    id: str = Field(..., description="Product UUID")
    artisan_id: str = Field(..., description="Owner artisan UUID")
    ai_enhanced: bool = False
    stock_quantity: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
