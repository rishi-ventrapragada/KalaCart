from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum

class InsightSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class InsightType(str, Enum):
    DEMAND_SPIKE = "demand_spike"
    FRAUD_RING = "fraud_ring"
    UNDERPERFORMING_REGION = "underperforming_region"
    FAST_GROWING_CATEGORY = "fast_growing_category"

class StateHeatmapMetric(BaseModel):
    state_code: str
    state_name: str
    orders_count: int
    gmv_inr: float
    active_artisans: int
    fulfillment_rate_percent: float
    heat_score: float  # 0.0 to 100.0

class LiveCommandMetricsResponse(BaseModel):
    timestamp: str
    live_active_users: int
    orders_today: int
    platform_gmv_inr: float
    net_revenue_inr: float
    active_disputes: int
    fraud_alerts: int
    active_sellers: int
    state_metrics: List[StateHeatmapMetric] = Field(default_factory=list)

class AICommandInsight(BaseModel):
    id: str
    insight_type: InsightType
    title: str
    description: str
    severity: InsightSeverity
    impact_metric: str
    recommended_action: str
    detected_at: str

class SupportTicketResponse(BaseModel):
    id: str
    ticket_number: str
    user_id: Optional[str] = None
    user_email: str
    user_type: str
    category: str
    subject: str
    description: str
    priority: str
    status: str
    ai_sentiment_score: float
    created_at: str

class CreateSupportTicketRequest(BaseModel):
    user_email: str
    user_type: str = "buyer"
    category: str
    subject: str
    description: str
    priority: str = "medium"

class GenerateExecutiveReportRequest(BaseModel):
    report_title: str
    report_period: str = "daily"  # "daily", "weekly", "monthly", "quarterly"

class ExecutiveReportResponse(BaseModel):
    id: str
    report_title: str
    report_period: str
    summary_markdown: str
    ai_insights: List[AICommandInsight] = Field(default_factory=list)
    kpi_snapshot: Dict[str, Any] = Field(default_factory=dict)
    pdf_export_url: str
    generated_by_ai: bool = True
    created_at: str
