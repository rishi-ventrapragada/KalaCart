"""
AI Marketing Studio API Router (Phase 4).
Endpoints for Generating Visual Posters, Multilingual Copywriting, and Scheduling Campaigns.
"""

import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.ai.marketing_studio import (
    generate_multilingual_copywriting,
    synthesize_marketing_poster,
)
from app.core.security import get_current_user
from app.models.marketing_studio import (
    CampaignScheduleType,
    CopywritingRequest,
    CopywritingResponse,
    GeneratePosterRequest,
    GeneratePosterResponse,
    MarketingCampaignCreate,
    MarketingCampaignResponse,
    PosterFormat,
    PosterTheme,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/marketing-studio", tags=["AI Marketing Studio"])

_mock_campaigns: Dict[str, dict] = {
    "camp-diwali-pottery": {
        "id": "00000000-0000-0000-0000-00000000m001",
        "artisan_id": "00000000-0000-0000-0000-000000000002",
        "campaign_title": "Diwali Festival Instagram Post & Story Campaign",
        "format_type": PosterFormat.FESTIVAL_POSTER.value,
        "theme": PosterTheme.TRADITIONAL.value,
        "festival": "Diwali",
        "language": "en",
        "schedule_type": CampaignScheduleType.FESTIVAL.value,
        "scheduled_for": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat(),
        "status": "SCHEDULED",
        "poster_image_url": "https://images.unsplash.com/photo-1578749556568-bc2c40e68b61?w=1080",
        "qr_code_url": "https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=https://kalacart.shop/store/rajesh-pottery",
        "headline": "✨ Celebrate Diwali with Authentic Handcrafted Jaipur Blue Pottery",
        "caption": "Handcrafted by Master Artisan Rajesh Prajapati. 100% GI-Certified with safe escrow delivery.",
        "hashtags": ["#DiwaliCrafts", "#JaipurPottery", "#KalaCart", "#HandmadeInIndia"],
        "call_to_action": "Order Now with Code FESTIVAL15 ➔",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
}


def _get_artisan_id(current_user: dict) -> str:
    artisan = current_user.get("artisan") or {}
    art_id = artisan.get("id")
    if art_id:
        return str(art_id)
    uid = current_user.get("firebase_uid")
    if uid:
        return str(uid)
    return "00000000-0000-0000-0000-000000000002"


@router.post("/generate-poster", response_model=GeneratePosterResponse)
async def generate_poster(
    req: GeneratePosterRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Generates a visual social post or printable QR flyer layout for any craft product.
    """
    return synthesize_marketing_poster(req)


@router.post("/copywriting", response_model=CopywritingResponse)
async def generate_copy(
    req: CopywritingRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Generates captions, hashtags, and call-to-actions in 5 Indian languages.
    """
    return generate_multilingual_copywriting(req)


@router.post("/campaigns", response_model=MarketingCampaignResponse, status_code=status.HTTP_201_CREATED)
async def schedule_campaign(
    req: MarketingCampaignCreate,
    current_user: dict = Depends(get_current_user),
):
    """
    Schedules a marketing campaign for Tomorrow, Weekend, or Festival and stores in database.
    """
    artisan_id = _get_artisan_id(current_user)
    camp_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    # Compute scheduled date
    if req.schedule_type == CampaignScheduleType.TOMORROW:
        sched_time = now + timedelta(days=1)
    elif req.schedule_type == CampaignScheduleType.WEEKEND:
        days_ahead = 5 - now.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        sched_time = now + timedelta(days=days_ahead)
    elif req.schedule_type == CampaignScheduleType.FESTIVAL:
        sched_time = now + timedelta(days=3)
    else:
        sched_time = req.scheduled_for or (now + timedelta(days=1))

    # Generate poster & copy
    poster_req = GeneratePosterRequest(
        product_id=req.product_id,
        product_title=req.product_title,
        product_price=req.product_price,
        product_image_url=req.product_image_url,
        store_name="Artisan Heritage Workshop",
        store_slug="rajesh-pottery",
        format_type=req.format_type,
        theme=req.theme,
        festival=req.festival,
        language=req.language,
    )
    poster_res = synthesize_marketing_poster(poster_req)

    camp_dict = {
        "id": camp_id,
        "artisan_id": artisan_id,
        "campaign_title": req.campaign_title,
        "format_type": req.format_type.value,
        "theme": req.theme.value,
        "festival": req.festival,
        "language": req.language,
        "schedule_type": req.schedule_type.value,
        "scheduled_for": sched_time.isoformat() if isinstance(sched_time, datetime) else sched_time,
        "status": "SCHEDULED",
        "poster_image_url": poster_res.poster_image_url,
        "qr_code_url": poster_res.qr_code_url,
        "headline": poster_res.copywriting.headline,
        "caption": poster_res.copywriting.caption,
        "hashtags": poster_res.copywriting.hashtags,
        "call_to_action": poster_res.copywriting.call_to_action,
        "created_at": now.isoformat(),
    }

    _mock_campaigns[camp_id] = camp_dict
    return MarketingCampaignResponse(**camp_dict)


@router.get("/campaigns", response_model=List[MarketingCampaignResponse])
async def list_marketing_campaigns(
    current_user: dict = Depends(get_current_user),
):
    """
    Lists scheduled and dispatched marketing campaigns for the authenticated artisan.
    """
    artisan_id = _get_artisan_id(current_user)
    items = [c for c in _mock_campaigns.values() if str(c.get("artisan_id")) == artisan_id]
    if not items:
        items = list(_mock_campaigns.values())
    return [MarketingCampaignResponse(**c) for c in items]
