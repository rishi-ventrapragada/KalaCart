from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional, Any
from app.core.security import get_current_user
from app.models.live_commerce import (
    LiveSessionCreate,
    LiveSessionResponse,
    PinProductRequest,
    LiveMessageCreate,
    LiveMessageResponse,
    LiveReactionRequest,
    InStreamPurchaseRequest,
    InStreamPurchaseResponse
)
from app.services.live_commerce_service import LiveCommerceService

router = APIRouter(prefix="/api/v1/live", tags=["Live Commerce Platform"])

def _get_user_info(current_user: Any) -> tuple[str, str]:
    if isinstance(current_user, dict):
        uid = current_user.get("uid") or current_user.get("id", "live-user")
        name = current_user.get("name") or current_user.get("full_name", "Craft Enthusiast")
        return uid, name
    uid = getattr(current_user, "id", getattr(current_user, "uid", "live-user"))
    name = getattr(current_user, "full_name", getattr(current_user, "name", "Craft Enthusiast"))
    return uid, name

@router.post("/sessions", response_model=LiveSessionResponse, status_code=status.HTTP_201_CREATED)
def start_live_session(
    payload: LiveSessionCreate,
    current_user: Any = Depends(get_current_user)
):
    """
    Artisan starts or schedules a live selling session with camera/mic stream endpoints.
    """
    uid, name = _get_user_info(current_user)
    return LiveCommerceService.start_session(artisan_id=uid, artisan_name=name, payload=payload)

@router.get("/sessions", response_model=List[LiveSessionResponse])
def list_active_live_sessions():
    """
    List all currently live craft selling streams.
    """
    return LiveCommerceService.list_active_sessions()

@router.get("/sessions/{session_id}", response_model=LiveSessionResponse)
def get_live_session(session_id: str):
    """
    Join live session, fetch playback HLS/WebRTC URLs, and view pinned products.
    """
    sess = LiveCommerceService.get_session(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Live session not found")
    return sess

@router.post("/sessions/{session_id}/pin-product", response_model=LiveSessionResponse)
def pin_product_to_stream(
    session_id: str,
    payload: PinProductRequest,
    current_user: Any = Depends(get_current_user)
):
    """
    Artisan spotlights and pins a craft product with live flash discount to all viewers.
    """
    try:
        return LiveCommerceService.pin_product(session_id=session_id, payload=payload)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/sessions/{session_id}/messages", response_model=LiveMessageResponse, status_code=status.HTTP_201_CREATED)
def send_live_chat_message(
    session_id: str,
    payload: LiveMessageCreate,
    current_user: Any = Depends(get_current_user)
):
    """
    Buyer or artisan posts real-time comments and questions.
    """
    uid, name = _get_user_info(current_user)
    try:
        return LiveCommerceService.send_message(
            session_id=session_id,
            user_id=uid,
            sender_name=name,
            payload=payload
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/sessions/{session_id}/messages", response_model=List[LiveMessageResponse])
def get_live_messages(session_id: str):
    """
    Fetch live chat message feed for the session.
    """
    return LiveCommerceService.list_messages(session_id=session_id)

@router.post("/sessions/{session_id}/react")
def send_live_reaction(session_id: str, payload: LiveReactionRequest):
    """
    Send floating emoji reactions (hearts, claps, diyas).
    """
    try:
        new_likes = LiveCommerceService.add_reaction(session_id=session_id, payload=payload)
        return {"session_id": session_id, "total_likes": new_likes}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/sessions/{session_id}/purchase", response_model=InStreamPurchaseResponse, status_code=status.HTTP_201_CREATED)
def in_stream_purchase(
    session_id: str,
    payload: InStreamPurchaseRequest,
    current_user: Any = Depends(get_current_user)
):
    """
    1-Tap in-stream purchase directly from the livestream without video feed interruption.
    """
    uid, _ = _get_user_info(current_user)
    try:
        return LiveCommerceService.instant_in_stream_purchase(
            session_id=session_id,
            user_id=uid,
            payload=payload
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/sessions/{session_id}/end", response_model=LiveSessionResponse)
def end_live_session(
    session_id: str,
    current_user: Any = Depends(get_current_user)
):
    """
    Conclude the live selling broadcast.
    """
    try:
        return LiveCommerceService.end_session(session_id=session_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
