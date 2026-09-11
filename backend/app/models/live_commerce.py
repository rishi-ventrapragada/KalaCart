from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum

class LiveSessionStatus(str, Enum):
    SCHEDULED = "scheduled"
    LIVE = "live"
    ENDED = "ended"

class LiveProductItem(BaseModel):
    id: str
    session_id: str
    product_id: str
    product_name: str
    live_special_price_inr: float
    original_price_inr: float
    limited_quantity: int
    is_pinned: bool = False
    display_order: int = 1
    sold_quantity: int = 0

class LiveSessionCreate(BaseModel):
    title: str = Field(..., min_length=5, max_length=255)
    description: str = Field(..., min_length=10)
    cover_image_url: Optional[str] = "https://storage.kalacart.in/live/covers/default_pottery_live.jpg"
    scheduled_start_time: Optional[str] = None
    featured_product_ids: Optional[List[str]] = Field(default_factory=list)

class LiveSessionResponse(BaseModel):
    id: str
    artisan_id: str
    artisan_name: str
    title: str
    description: str
    cover_image_url: str
    playback_hls_url: str
    webrtc_url: str
    status: LiveSessionStatus
    pinned_product: Optional[LiveProductItem] = None
    pinned_coupon_code: Optional[str] = None
    discount_percent: float = 0.0
    peak_viewers: int = 0
    total_views: int = 0
    likes_count: int = 0
    products: List[LiveProductItem] = Field(default_factory=list)
    started_at: str
    ended_at: Optional[str] = None

class PinProductRequest(BaseModel):
    product_id: str
    live_discount_percent: float = Field(default=15.0, ge=0, le=70)
    coupon_code: Optional[str] = "LIVEFLASH15"

class LiveMessageCreate(BaseModel):
    message_text: str = Field(..., min_length=1, max_length=500)
    is_question: bool = False

class LiveMessageResponse(BaseModel):
    id: str
    session_id: str
    user_id: str
    sender_name: str
    sender_role: str
    message_text: str
    is_pinned_question: bool = False
    created_at: str

class LiveReactionRequest(BaseModel):
    reaction_type: str = "heart"  # "heart", "fire", "clap", "diya", "sparkles"
    count: int = Field(default=1, ge=1, le=50)

class InStreamPurchaseRequest(BaseModel):
    product_id: str
    quantity: int = Field(default=1, ge=1)
    coupon_code: Optional[str] = None
    delivery_address: str = "Flat 101, Silk Enclave, Bangalore"

class InStreamPurchaseResponse(BaseModel):
    order_id: str
    session_id: str
    product_id: str
    product_name: str
    quantity: int
    unit_price_inr: float
    total_paid_inr: float
    status: str
    stream_playback_maintained: bool = True
    message: str
