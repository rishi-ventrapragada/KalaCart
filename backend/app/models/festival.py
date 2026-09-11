"""Pydantic models for Festival Demand Predictor (Phase 19).

Festivals covered:
- Diwali
- Pongal
- Sankranti
- Dussehra
- Christmas
- Eid
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class FestivalType(str, Enum):
    diwali = "Diwali"
    pongal = "Pongal"
    sankranti = "Sankranti"
    dussehra = "Dussehra"
    christmas = "Christmas"
    eid = "Eid"


class ProductFestivalRecommendation(BaseModel):
    product_id: Optional[str] = None
    product_title: str
    category: str
    current_stock: int = Field(default=0, ge=0)
    recommended_stock: int = Field(default=0, ge=0, description="Suggested inventory quantity to stock")
    current_price: float = Field(default=0.0, ge=0.0)
    suggested_price: float = Field(default=0.0, ge=0.0, description="AI suggested price increase/decrease")
    price_adjustment_pct: float = Field(default=0.0, description="Percentage change e.g. +15.0 or -5.0")
    reasoning: str
    confidence_score: int = Field(default=85, ge=0, le=100)


class FestivalPoster(BaseModel):
    headline: str
    tagline: str
    offer_text: str
    theme_color_hex: str
    hashtags: List[str]
    suggested_caption: str


class FestivalPredictionResponse(BaseModel):
    festival_key: str
    festival_name: str
    festival_date: str
    days_remaining: int
    demand_surge_pct: int = Field(..., description="Estimated percentage demand growth e.g. 180%")
    target_audiences: List[str]
    trending_crafts: List[str]
    recommended_products: List[ProductFestivalRecommendation]
    promotional_poster: FestivalPoster
    actionable_preparation_steps: List[str]


class PosterGenerateRequest(BaseModel):
    festival_key: str
    artisan_name: Optional[str] = "Artisan"
    product_category: Optional[str] = "Handicrafts"
    discount_pct: Optional[int] = 15
