from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ExecutiveInsightResponse(BaseModel):
    id: str
    artisan_id: str
    insight_type: str
    title: str
    summary: str
    confidence_score: float
    impact_level: str
    metrics: Dict[str, Any] = {}
    recommendations: List[str] = []
    is_read: bool = False
    created_at: str


class CashflowForecastResponse(BaseModel):
    id: str
    artisan_id: str
    forecast_horizon_days: int
    projected_inflows: float
    projected_material_outflows: float
    projected_labour_outflows: float
    projected_logistics_outflows: float
    projected_net_cashflow: float
    estimated_runway_days: int
    working_capital_health: str  # critical, tight, healthy, surplus
    cashflow_breakdown: List[Dict[str, Any]] = []
    generated_at: str


class RiskPredictionResponse(BaseModel):
    id: str
    artisan_id: str
    risk_category: str  # stockout_risk, customer_churn, cash_deficit, supplier_delay, demand_slump
    target_entity_id: Optional[str] = None
    risk_level: str  # low, medium, high, critical
    risk_score: int
    predicted_date: Optional[str] = None
    description: str
    mitigation_action: str
    mitigation_status: str  # pending, in_progress, mitigated, dismissed
    created_at: str


class AIDecisionCreate(BaseModel):
    decision_type: str  # discount, production, hiring, export
    title: str
    rationale: str
    proposed_payload: Dict[str, Any]
    projected_revenue_lift: float = 0.0
    projected_cost_savings: float = 0.0
    confidence_score: float = 90.0


class AIDecisionActionRequest(BaseModel):
    action: str  # approve, reject, execute
    rejected_reason: Optional[str] = None


class AIDecisionResponse(BaseModel):
    id: str
    artisan_id: str
    decision_type: str
    title: str
    rationale: str
    proposed_payload: Dict[str, Any]
    projected_revenue_lift: float
    projected_cost_savings: float
    confidence_score: float
    status: str  # suggested, approved, rejected, executed
    approved_at: Optional[str] = None
    rejected_reason: Optional[str] = None
    executed_at: Optional[str] = None
    execution_result: Optional[Dict[str, Any]] = None
    created_at: str


class ExecutiveReportResponse(BaseModel):
    artisan_id: str
    report_type: str  # weekly, monthly
    generated_at: str
    revenue_forecast: Dict[str, Any]
    cashflow_summary: Dict[str, Any]
    top_growth_opportunities: List[str]
    critical_risks: List[str]
    pending_ai_decisions_count: int
    download_pdf_url: str
