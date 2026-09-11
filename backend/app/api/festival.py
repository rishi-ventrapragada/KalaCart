"""Festival Demand Predictor API (Phase 19).

Endpoints:
  GET /api/v1/festival/upcoming - Get upcoming festival opportunity
  GET /api/v1/festival/prediction/{festival_key} - Get prediction for a specific festival
  GET /api/v1/festival/list - List all supported festivals
  POST /api/v1/festival/generate-poster - Generate customized promotional poster text
"""

from typing import List, Optional
from fastapi import APIRouter, Query, status

from app.models.festival import (
    FestivalPredictionResponse,
    PosterGenerateRequest,
    FestivalPoster,
)
from app.services.festival_service import (
    get_upcoming_festival,
    FESTIVAL_CALENDAR,
)

router = APIRouter(prefix="/api/v1/festival", tags=["Festival Demand Predictor"])


@router.get("/upcoming", response_model=FestivalPredictionResponse, status_code=status.HTTP_200_OK)
async def get_upcoming_opportunity(target_key: Optional[str] = Query(None)):
    """Fetch seasonal prediction and opportunity details for the nearest or selected festival."""
    return get_upcoming_festival(target_key)


@router.get("/prediction/{festival_key}", response_model=FestivalPredictionResponse, status_code=status.HTTP_200_OK)
async def get_festival_prediction(festival_key: str):
    """Fetch seasonal prediction and inventory recommendations for a specific festival."""
    return get_upcoming_festival(festival_key)


@router.get("/list", response_model=List[dict], status_code=status.HTTP_200_OK)
async def list_festivals():
    """List all supported festivals in the calendar."""
    return [
        {
            "key": f["key"],
            "name": f["name"],
            "date": f"{f['year']}-{f['month']:02d}-{f['day']:02d}",
            "surge_pct": f["surge_pct"],
            "color_hex": f["color_hex"]
        }
        for f in FESTIVAL_CALENDAR
    ]


@router.post("/generate-poster", response_model=FestivalPoster, status_code=status.HTTP_200_OK)
async def generate_promotional_poster(request: PosterGenerateRequest):
    """Generate marketing poster headlines, discount badges, and social captions."""
    prediction = get_upcoming_festival(request.festival_key)
    poster = prediction.promotional_poster

    # Customize with artisan details if provided
    name = request.artisan_name or "Master Artisan"
    cat = request.product_category or "Handicrafts"
    disc = request.discount_pct or 15

    custom_headline = f"{prediction.festival_name} Special: Handcrafted {cat} by {name}"
    custom_offer = f"Exclusive Festive Discount: Flat {disc}% Off"
    custom_caption = (
        f"{custom_headline} ✨\n\n"
        f"Celebrate with authentic handmade heritage directly from {name}. "
        f"{custom_offer} for a limited time!\n\n"
        f"Support local craft traditions: {' '.join(poster.hashtags)}"
    )

    return FestivalPoster(
        headline=custom_headline,
        tagline=poster.tagline,
        offer_text=custom_offer,
        theme_color_hex=poster.theme_color_hex,
        hashtags=poster.hashtags,
        suggested_caption=custom_caption
    )
