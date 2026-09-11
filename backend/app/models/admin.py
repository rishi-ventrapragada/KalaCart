"""
Pydantic Models for KalaCart Phase 3: Admin Portal & Fraud Intelligence.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class AdminActionType(str, Enum):
    APPROVE_SELLER = "APPROVE_SELLER"
    SUSPEND_SELLER = "SUSPEND_SELLER"
    HIDE_PRODUCT = "HIDE_PRODUCT"
    UNHIDE_PRODUCT = "UNHIDE_PRODUCT"
    REMOVE_REVIEW = "REMOVE_REVIEW"
    RESOLVE_DISPUTE = "RESOLVE_DISPUTE"
    UPDATE_SETTINGS = "UPDATE_SETTINGS"


class FraudCategory(str, Enum):
    FAKE_REVIEW = "FAKE_REVIEW"
    SPAM_RFQ = "SPAM_RFQ"
    DUPLICATE_PRODUCT = "DUPLICATE_PRODUCT"
    ABNORMAL_PRICING = "ABNORMAL_PRICING"
    SUSPICIOUS_ACCOUNT = "SUSPICIOUS_ACCOUNT"
    UNUSUAL_TRANSACTION = "UNUSUAL_TRANSACTION"


class FraudSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ModerationRequest(BaseModel):
    action: AdminActionType
    target_entity: str
    target_id: str
    reason: str
    changes: Optional[Dict[str, Any]] = None


class AdminLogResponse(BaseModel):
    id: str
    admin_id: str
    admin_email: str
    action_type: str
    target_entity: str
    target_id: str
    reason: Optional[str] = None
    created_at: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class FraudReportResponse(BaseModel):
    id: str
    report_number: str
    entity_type: str
    entity_id: str
    fraud_category: FraudCategory
    risk_score: int
    severity: FraudSeverity
    ai_confidence: int
    flagged_reasons: List[str]
    status: str
    resolution_notes: Optional[str] = None
    created_at: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class AdminDashboardAnalytics(BaseModel):
    total_gmv: float
    total_revenue: float
    daily_active_users: int
    conversion_rate: float
    total_sellers: int
    total_products: int
    open_fraud_flags: int
    disputed_orders: int
    top_categories: List[Dict[str, Any]]
    state_wise_sales: List[Dict[str, Any]]
