"""
Pydantic Schemas for Kala AI Autonomous Business Manager (Phase 4).
"""

from datetime import datetime, date
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class SuggestionType(str, Enum):
    PRICE_INCREASE = "PRICE_INCREASE"
    TRENDING_DEMAND = "TRENDING_DEMAND"
    URGENT_REPLY = "URGENT_REPLY"
    RESTOCK_ALERT = "RESTOCK_ALERT"
    BUNDLE_RECOMMENDATION = "BUNDLE_RECOMMENDATION"


class ActionType(str, Enum):
    UPDATE_PRICE = "UPDATE_PRICE"
    RESTOCK_ITEM = "RESTOCK_ITEM"
    REPLY_RFQ = "REPLY_RFQ"
    CREATE_COUPON = "CREATE_COUPON"
    VIEW_DETAILS = "VIEW_DETAILS"


class HighProbRFQ(BaseModel):
    rfq_id: str
    buyer_name: str
    product_category: str
    target_budget: float
    conversion_probability_pct: float
    urgency_notes: str


class FollowupCustomer(BaseModel):
    customer_id: str
    buyer_name: str
    city: str
    last_order_days_ago: int
    total_spend: float
    suggested_message: str


class MorningBriefingResponse(BaseModel):
    artisan_id: str
    briefing_date: date
    greeting: str
    today_sales: float
    yesterday_revenue: float
    pending_orders_count: int
    low_stock_count: int
    high_prob_rfqs: List[HighProbRFQ] = []
    followup_customers: List[FollowupCustomer] = []
    weekly_goal_target: float
    weekly_goal_current: float
    weekly_goal_pct: float
    key_takeaway: str

    model_config = ConfigDict(from_attributes=True)


class AISuggestionResponse(BaseModel):
    id: str
    artisan_id: str
    suggestion_type: SuggestionType
    title: str
    description: str
    potential_impact: Optional[str] = None
    confidence_pct: float = 85.0
    action_type: Optional[ActionType] = None
    action_payload: Optional[Dict[str, Any]] = None
    is_dismissed: bool = False
    is_applied: bool = False
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class HealthScoreBreakdown(BaseModel):
    factor_name: str
    score: int
    weight_pct: int
    status: str
    diagnostic_tip: str


class BusinessHealthScoreResponse(BaseModel):
    artisan_id: str
    overall_score: int
    grade: str
    summary: str
    response_time_score: int
    delivery_rate_score: int
    reviews_score: int
    inventory_health_score: int
    revenue_trend_score: int
    profile_completion_score: int
    breakdown: List[HealthScoreBreakdown] = []
    top_recommendation: str
    calculated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AIQueryRequest(BaseModel):
    query_text: str = Field(..., min_length=2, max_length=500)
    language: Optional[str] = "en"


class AIQueryResponse(BaseModel):
    query_text: str
    intent: str
    response_text: str
    supporting_data: Optional[Dict[str, Any]] = None
    suggested_followups: List[str] = []
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
