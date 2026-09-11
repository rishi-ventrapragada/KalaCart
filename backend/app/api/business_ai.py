"""
Kala AI Autonomous Business Manager API Router (Phase 4).
Endpoints for Morning Briefings, Contextual Suggestions, Health Scores, and Natural Language Assistant.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.ai.business_manager import (
    answer_business_nl_query,
    calculate_business_health_score,
    generate_live_suggestions,
    generate_morning_briefing,
)
from app.core.security import get_current_user
from app.models.business_ai import (
    AIQueryRequest,
    AIQueryResponse,
    AISuggestionResponse,
    BusinessHealthScoreResponse,
    MorningBriefingResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ai-manager", tags=["Kala AI Business Manager"])


def _get_artisan_id(current_user: dict) -> str:
    artisan = current_user.get("artisan") or {}
    art_id = artisan.get("id")
    if art_id:
        return str(art_id)
    uid = current_user.get("firebase_uid")
    if uid:
        return str(uid)
    return "00000000-0000-0000-0000-000000000002"


@router.get("/briefing", response_model=MorningBriefingResponse)
async def get_daily_morning_briefing(
    current_user: dict = Depends(get_current_user),
):
    """
    Generates or fetches today's morning briefing for the artisan's shop.
    """
    artisan_id = _get_artisan_id(current_user)
    return generate_morning_briefing(artisan_id)


@router.get("/health-score", response_model=BusinessHealthScoreResponse)
async def get_business_health_score(
    current_user: dict = Depends(get_current_user),
):
    """
    Calculates 0-100 Business Health Score and diagnostic factor breakdowns.
    """
    artisan_id = _get_artisan_id(current_user)
    return calculate_business_health_score(artisan_id)


@router.get("/suggestions", response_model=List[AISuggestionResponse])
async def get_ai_suggestions(
    current_user: dict = Depends(get_current_user),
):
    """
    Fetches real-time actionable suggestion cards for the artisan.
    """
    artisan_id = _get_artisan_id(current_user)
    return generate_live_suggestions(artisan_id)


@router.post("/suggestions/{suggestion_id}/dismiss")
async def dismiss_suggestion(
    suggestion_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Dismisses an action suggestion card.
    """
    return {"success": True, "suggestion_id": suggestion_id, "status": "DISMISSED"}


@router.post("/query", response_model=AIQueryResponse)
async def ask_kala_ai(
    req: AIQueryRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Natural language Q&A endpoint allowing artisans to ask business questions about earnings, best sellers, and customers.
    """
    artisan_id = _get_artisan_id(current_user)
    res_dict = answer_business_nl_query(artisan_id, req.query_text)
    return AIQueryResponse(**res_dict)
