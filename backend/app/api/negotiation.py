"""
AI Sales Negotiation Agent API Router (Phase 4).
Endpoints for Real-time Suggested Replies, Tone Variations, Margin-Protected Quotes, and Telemetry.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.ai.negotiation import (
    generate_itemized_quote,
    generate_suggested_replies,
)
from app.core.security import get_current_user
from app.models.negotiation import (
    GenerateQuoteRequest,
    GenerateQuoteResponse,
    NegotiationStatus,
    SuggestRepliesRequest,
    SuggestRepliesResponse,
    TrackReplyUsageRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/negotiation", tags=["AI Sales Negotiation Agent"])

_mock_negotiations: Dict[str, dict] = {}
_mock_usage_logs: List[dict] = []


def _get_artisan_id(current_user: dict) -> str:
    artisan = current_user.get("artisan") or {}
    art_id = artisan.get("id")
    if art_id:
        return str(art_id)
    uid = current_user.get("firebase_uid")
    if uid:
        return str(uid)
    return "00000000-0000-0000-0000-000000000002"


@router.post("/suggest-replies", response_model=SuggestRepliesResponse)
async def get_suggested_replies(
    req: SuggestRepliesRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Real-time AI endpoint returning 4 tone options (Friendly, Professional, Premium, Urgent)
    with margin-guaranteed counter-offer calculations.
    """
    return generate_suggested_replies(req)


@router.post("/generate-quote", response_model=GenerateQuoteResponse)
async def generate_quote(
    req: GenerateQuoteRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Calculates itemized discount, margin %, delivery, and net profit before sending formal quotes.
    """
    return generate_itemized_quote(req)


@router.post("/track-usage")
async def track_reply_usage(
    req: TrackReplyUsageRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Logs which tone and suggested text was chosen by the artisan to continuously refine AI advice.
    """
    artisan_id = _get_artisan_id(current_user)
    log_id = str(uuid.uuid4())
    log_dict = {
        "id": log_id,
        "artisan_id": artisan_id,
        "negotiation_id": req.negotiation_id,
        "suggested_text": req.suggested_text,
        "actual_sent_text": req.actual_sent_text,
        "tone": req.tone.value,
        "was_edited": req.was_edited,
        "result_status": req.result_status,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    _mock_usage_logs.append(log_dict)
    return {"success": True, "log_id": log_id, "status": "LOGGED"}
