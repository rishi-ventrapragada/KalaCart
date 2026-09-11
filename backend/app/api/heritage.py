"""
KalaCart Phase 6 — Cultural Heritage Intelligence API.

Endpoints:
- GET  /api/v1/heritage/crafts
- GET  /api/v1/heritage/crafts/{craft_code}
- POST /api/v1/heritage/generate-story
- GET  /api/v1/heritage/product-link/{product_id}
"""

import logging
from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException, status

from app.models.heritage import (
    CraftHeritageDetail,
    CraftLibrarySummary,
    StoryGenerationRequest,
    StoryGenerationResponse
)
from app.services.heritage_service import CulturalHeritageService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/crafts", response_model=List[CraftLibrarySummary])
async def list_craft_library() -> List[CraftLibrarySummary]:
    """
    Returns summary list of all documented Indian craft traditions in the national repository.
    """
    return await CulturalHeritageService.list_crafts()


@router.get("/crafts/{craft_code}", response_model=CraftHeritageDetail)
async def get_craft_encyclopedia(craft_code: str) -> CraftHeritageDetail:
    """
    Museum Mode: Returns comprehensive craft encyclopedia:
    History, Region, GI Details, Techniques, Tools, Materials, Master Artisans,
    Video Archives, and Oral Histories.
    """
    detail = await CulturalHeritageService.get_craft_by_code(craft_code)
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Craft tradition '{craft_code}' not found in national repository."
        )
    return detail


@router.post("/generate-story", response_model=StoryGenerationResponse)
async def generate_heritage_story(req: StoryGenerationRequest) -> StoryGenerationResponse:
    """
    AI Story Generator:
    Generates multi-language cultural stories with strict factual separation
    (Historical Facts vs AI-generated Folklore Narratives).
    """
    return await CulturalHeritageService.generate_story(req)


@router.get("/product-link/{product_id}")
async def get_product_heritage_link(product_id: str) -> Dict[str, Any]:
    """
    Verification Invariant: Every product links to its registered Cultural Heritage page.
    """
    return await CulturalHeritageService.resolve_product_heritage(product_id)
