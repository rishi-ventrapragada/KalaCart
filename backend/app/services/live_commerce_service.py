from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
from app.models.live_commerce import (
    LiveSessionCreate,
    LiveSessionResponse,
    LiveProductItem,
    PinProductRequest,
    LiveMessageCreate,
    LiveMessageResponse,
    LiveReactionRequest,
    InStreamPurchaseRequest,
    InStreamPurchaseResponse,
    LiveSessionStatus
)

_LIVE_SESSIONS: Dict[str, Dict[str, Any]] = {}
_LIVE_PRODUCTS: Dict[str, List[Dict[str, Any]]] = {}
_LIVE_MESSAGES: Dict[str, List[Dict[str, Any]]] = {}

class LiveCommerceService:
    @staticmethod
    def start_session(artisan_id: str, artisan_name: str, payload: LiveSessionCreate) -> LiveSessionResponse:
        session_id = str(uuid.uuid4())
        stream_key = f"live_{uuid.uuid4().hex[:10]}"
        now = datetime.utcnow().isoformat()

        # Generate live streaming endpoints
        hls_url = f"https://live.kalacart.in/hls/{stream_key}/index.m3u8"
        webrtc_url = f"wss://live.kalacart.in/webrtc/{stream_key}"

        # Populate sample products for the livestream
        prods = [
            {
                "id": str(uuid.uuid4()),
                "session_id": session_id,
                "product_id": "prod-dhokra-lamp-live-01",
                "product_name": "Authentic Bastar Lost-Wax Brass Lamp (Live Masterpiece)",
                "live_special_price_inr": 2850.0,
                "original_price_inr": 3400.0,
                "limited_quantity": 10,
                "is_pinned": True,
                "display_order": 1,
                "sold_quantity": 0
            },
            {
                "id": str(uuid.uuid4()),
                "session_id": session_id,
                "product_id": "prod-blue-pottery-tea-set",
                "product_name": "Jaipur Blue Pottery Hand-Glazed 6-Cup Tea Set",
                "live_special_price_inr": 1650.0,
                "original_price_inr": 2100.0,
                "limited_quantity": 15,
                "is_pinned": False,
                "display_order": 2,
                "sold_quantity": 0
            }
        ]
        _LIVE_PRODUCTS[session_id] = prods

        session_record = {
            "id": session_id,
            "artisan_id": artisan_id,
            "artisan_name": artisan_name,
            "title": payload.title,
            "description": payload.description,
            "cover_image_url": payload.cover_image_url or "https://storage.kalacart.in/live/covers/default_pottery_live.jpg",
            "playback_hls_url": hls_url,
            "webrtc_url": webrtc_url,
            "status": LiveSessionStatus.LIVE,
            "pinned_product_id": prods[0]["product_id"],
            "pinned_coupon_code": "LIVEFLASH15",
            "discount_percent": 15.0,
            "peak_viewers": 128,
            "total_views": 450,
            "likes_count": 1420,
            "started_at": now,
            "ended_at": None
        }
        _LIVE_SESSIONS[session_id] = session_record
        _LIVE_MESSAGES[session_id] = []

        return LiveCommerceService.get_session(session_id)

    @staticmethod
    def get_session(session_id: str) -> Optional[LiveSessionResponse]:
        session = _LIVE_SESSIONS.get(session_id)
        if not session:
            return None

        prod_list = [LiveProductItem(**p) for p in _LIVE_PRODUCTS.get(session_id, [])]
        pinned_item = next((p for p in prod_list if p.is_pinned), None)

        return LiveSessionResponse(
            id=session["id"],
            artisan_id=session["artisan_id"],
            artisan_name=session["artisan_name"],
            title=session["title"],
            description=session["description"],
            cover_image_url=session["cover_image_url"],
            playback_hls_url=session["playback_hls_url"],
            webrtc_url=session["webrtc_url"],
            status=session["status"],
            pinned_product=pinned_item,
            pinned_coupon_code=session["pinned_coupon_code"],
            discount_percent=session["discount_percent"],
            peak_viewers=session["peak_viewers"],
            total_views=session["total_views"],
            likes_count=session["likes_count"],
            products=prod_list,
            started_at=session["started_at"],
            ended_at=session.get("ended_at")
        )

    @staticmethod
    def list_active_sessions() -> List[LiveSessionResponse]:
        results = []
        for s_id in _LIVE_SESSIONS:
            sess = LiveCommerceService.get_session(s_id)
            if sess and sess.status == LiveSessionStatus.LIVE:
                results.append(sess)
        return results

    @staticmethod
    def pin_product(session_id: str, payload: PinProductRequest) -> LiveSessionResponse:
        session = _LIVE_SESSIONS.get(session_id)
        if not session:
            raise ValueError("Live session not found")

        prods = _LIVE_PRODUCTS.get(session_id, [])
        for p in prods:
            p["is_pinned"] = (p["product_id"] == payload.product_id)

        session["pinned_product_id"] = payload.product_id
        session["pinned_coupon_code"] = payload.coupon_code
        session["discount_percent"] = payload.live_discount_percent

        return LiveCommerceService.get_session(session_id)

    @staticmethod
    def send_message(session_id: str, user_id: str, sender_name: str, payload: LiveMessageCreate) -> LiveMessageResponse:
        if session_id not in _LIVE_SESSIONS:
            raise ValueError("Live session not found")

        msg_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        record = {
            "id": msg_id,
            "session_id": session_id,
            "user_id": user_id,
            "sender_name": sender_name,
            "sender_role": "buyer",
            "message_text": payload.message_text,
            "is_pinned_question": payload.is_question,
            "created_at": now
        }
        _LIVE_MESSAGES.setdefault(session_id, []).append(record)
        return LiveMessageResponse(**record)

    @staticmethod
    def list_messages(session_id: str) -> List[LiveMessageResponse]:
        return [LiveMessageResponse(**m) for m in _LIVE_MESSAGES.get(session_id, [])]

    @staticmethod
    def add_reaction(session_id: str, payload: LiveReactionRequest) -> int:
        session = _LIVE_SESSIONS.get(session_id)
        if not session:
            raise ValueError("Live session not found")
        session["likes_count"] += payload.count
        return session["likes_count"]

    @staticmethod
    def instant_in_stream_purchase(
        session_id: str,
        user_id: str,
        payload: InStreamPurchaseRequest
    ) -> InStreamPurchaseResponse:
        session = _LIVE_SESSIONS.get(session_id)
        if not session:
            raise ValueError("Live session not found")

        prods = _LIVE_PRODUCTS.get(session_id, [])
        prod = next((p for p in prods if p["product_id"] == payload.product_id), None)
        if not prod:
            # Fallback product item
            prod = {
                "product_id": payload.product_id,
                "product_name": "Handcrafted Live Showcase Craft Piece",
                "live_special_price_inr": 2850.0,
                "limited_quantity": 5,
                "sold_quantity": 0
            }

        unit_price = prod["live_special_price_inr"]
        if payload.coupon_code:
            unit_price = round(unit_price * 0.90, 2)  # Additional 10% flash coupon

        total = round(unit_price * payload.quantity, 2)
        prod["sold_quantity"] = prod.get("sold_quantity", 0) + payload.quantity

        order_id = f"LIVE-ORD-{datetime.utcnow().strftime('%Y%m')}-{uuid.uuid4().hex[:6].upper()}"

        return InStreamPurchaseResponse(
            order_id=order_id,
            session_id=session_id,
            product_id=payload.product_id,
            product_name=prod["product_name"],
            quantity=payload.quantity,
            unit_price_inr=unit_price,
            total_paid_inr=total,
            status="confirmed_in_stream",
            stream_playback_maintained=True,
            message="1-Tap purchase successful! Your live video feed continues uninterrupted."
        )

    @staticmethod
    def end_session(session_id: str) -> LiveSessionResponse:
        session = _LIVE_SESSIONS.get(session_id)
        if not session:
            raise ValueError("Live session not found")
        session["status"] = LiveSessionStatus.ENDED
        session["ended_at"] = datetime.utcnow().isoformat()
        return LiveCommerceService.get_session(session_id)
