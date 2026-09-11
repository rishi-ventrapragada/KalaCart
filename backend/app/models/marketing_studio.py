"""
Pydantic Schemas for AI Marketing Studio (Phase 4).
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class PosterFormat(str, Enum):
    INSTAGRAM_POST = "INSTAGRAM_POST"
    WHATSAPP_BANNER = "WHATSAPP_BANNER"
    FESTIVAL_POSTER = "FESTIVAL_POSTER"
    PRODUCT_FLYER = "PRODUCT_FLYER"
    STORY_IMAGE = "STORY_IMAGE"
    QR_POSTER = "QR_POSTER"


class PosterTheme(str, Enum):
    MINIMAL = "MINIMAL"
    LUXURY = "LUXURY"
    TRADITIONAL = "TRADITIONAL"
    MODERN = "MODERN"


class CampaignScheduleType(str, Enum):
    TOMORROW = "TOMORROW"
    WEEKEND = "WEEKEND"
    FESTIVAL = "FESTIVAL"
    CUSTOM = "CUSTOM"


class CopywritingRequest(BaseModel):
    product_title: str
    craft_category: str
    artisan_name: str
    store_name: str
    format_type: PosterFormat = PosterFormat.INSTAGRAM_POST
    theme: PosterTheme = PosterTheme.TRADITIONAL
    festival: Optional[str] = None
    language: str = "en"


class CopywritingResponse(BaseModel):
    headline: str
    caption: str
    hashtags: List[str]
    call_to_action: str
    language: str
    tone: str


class GeneratePosterRequest(BaseModel):
    product_id: Optional[str] = None
    product_title: str
    product_price: float = Field(..., ge=0)
    product_image_url: Optional[str] = None
    store_name: str
    store_slug: str
    format_type: PosterFormat = PosterFormat.INSTAGRAM_POST
    theme: PosterTheme = PosterTheme.TRADITIONAL
    festival: Optional[str] = None
    language: str = "en"
    custom_headline: Optional[str] = None
    custom_cta: Optional[str] = None


class GeneratePosterResponse(BaseModel):
    poster_id: str
    poster_image_url: str
    qr_code_url: str
    store_deep_link: str
    format_type: PosterFormat
    theme: PosterTheme
    aspect_ratio: str
    dimensions_px: str
    copywriting: CopywritingResponse
    created_at: datetime


class MarketingCampaignCreate(BaseModel):
    product_id: Optional[str] = None
    product_title: str
    product_price: float
    product_image_url: Optional[str] = None
    campaign_title: str
    format_type: PosterFormat = PosterFormat.INSTAGRAM_POST
    theme: PosterTheme = PosterTheme.TRADITIONAL
    festival: Optional[str] = None
    language: str = "en"
    schedule_type: CampaignScheduleType = CampaignScheduleType.TOMORROW
    scheduled_for: Optional[datetime] = None


class MarketingCampaignResponse(BaseModel):
    id: str
    artisan_id: str
    campaign_title: str
    format_type: PosterFormat
    theme: PosterTheme
    festival: Optional[str] = None
    language: str
    schedule_type: CampaignScheduleType
    scheduled_for: datetime
    status: str
    poster_image_url: str
    qr_code_url: str
    headline: str
    caption: str
    hashtags: List[str]
    call_to_action: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
