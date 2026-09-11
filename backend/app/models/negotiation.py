"""
Pydantic Schemas for AI Sales Negotiation Agent (Phase 4).
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class NegotiationTone(str, Enum):
    FRIENDLY = "FRIENDLY"
    PROFESSIONAL = "PROFESSIONAL"
    PREMIUM = "PREMIUM"
    URGENT = "URGENT"


class NegotiationStatus(str, Enum):
    PROPOSED = "PROPOSED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    CONVERTED_TO_ORDER = "CONVERTED_TO_ORDER"


class SuggestReplyOption(BaseModel):
    tone: NegotiationTone
    reply_text: str
    proposed_price: float
    discount_pct: float
    projected_net_profit: float
    profit_margin_pct: float
    value_add_offered: Optional[str] = None
    is_safe_margin: bool = True


class SuggestRepliesRequest(BaseModel):
    product_id: Optional[str] = None
    product_title: str
    listed_price: float = Field(..., ge=0)
    buyer_message: str = Field(..., min_length=1)
    buyer_offered_price: Optional[float] = None
    material_cost: Optional[float] = None
    labor_cost: Optional[float] = None
    packaging_cost: Optional[float] = 50.0
    language: Optional[str] = "en"


class SuggestRepliesResponse(BaseModel):
    buyer_intent: str
    buyer_target_price: Optional[float] = None
    minimum_floor_price: float
    listed_price: float
    is_loss_making_request: bool
    suggestions: List[SuggestReplyOption] = []
    negotiation_tip: str
    created_at: datetime


class GenerateQuoteRequest(BaseModel):
    product_title: str
    listed_price: float = Field(..., ge=0)
    target_price: float = Field(..., ge=0)
    quantity: int = Field(default=1, ge=1)
    material_cost: Optional[float] = None
    labor_cost: Optional[float] = None
    packaging_cost: Optional[float] = 50.0
    shipping_cost: Optional[float] = 100.0


class GenerateQuoteResponse(BaseModel):
    unit_price: float
    quantity: int
    subtotal: float
    discount_amount: float
    discount_pct: float
    material_cost_total: float
    labor_cost_total: float
    packaging_cost_total: float
    shipping_cost: float
    estimated_platform_fee: float
    net_profit: float
    profit_margin_pct: float
    is_profitable: bool
    status_message: str


class TrackReplyUsageRequest(BaseModel):
    negotiation_id: Optional[str] = None
    suggested_text: str
    actual_sent_text: str
    tone: NegotiationTone
    was_edited: bool = False
    result_status: str = "SENT"
