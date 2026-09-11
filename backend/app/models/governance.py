from datetime import datetime, date
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class FactorAttribution(BaseModel):
    factor_name: str
    weight_pct: float
    direction: str = "POSITIVE"  # POSITIVE, NEGATIVE, NEUTRAL
    impact_description: str
    evidence_value: Optional[str] = None


class DecisionExplanationResponse(BaseModel):
    decision_id: str
    decision_type: str  # PRICING, RECOMMENDATION, TRUST_SCORE, DEMAND_FORECAST, SEARCH_RANKING, FRAUD_DETECTION
    model_name: str
    model_version: str = "v2.4.0"
    entity_id: str
    summary_headline: str
    plain_language_reasoning: str
    primary_contributing_factor: str
    factors: List[FactorAttribution]
    counterfactual_guidance: Optional[str] = None
    fairness_compliance_status: str = "COMPLIANT"
    confidence_score: float = 0.95
    timestamp: datetime = Field(default_factory=datetime.now)


class AIDecisionRecord(BaseModel):
    id: str
    decision_type: str
    model_name: str
    model_version: str = "v2.4.0"
    entity_id: str
    user_id: Optional[str] = None
    confidence_score: float
    input_features: Dict[str, Any]
    output_decision: Dict[str, Any]
    latency_ms: int = 42
    has_human_override: bool = False
    created_at: datetime = Field(default_factory=datetime.now)
    explanation: Optional[DecisionExplanationResponse] = None


class ModelPerformanceMetric(BaseModel):
    model_name: str
    task_domain: str
    accuracy_score: float
    precision_score: float
    recall_score: float
    f1_score: float
    drift_divergence_kl: float
    p95_latency_ms: int
    demographic_parity_ratio: float
    total_inferences_24h: int
    status: str = "HEALTHY"


class BiasAuditReport(BaseModel):
    evaluation_date: str
    audit_status: str = "PASSED"
    overall_fairness_index: float = 98.4
    state_level_disparities: List[Dict[str, Any]]
    gender_parity_ratio: float = 0.992
    craft_cluster_representation: List[Dict[str, Any]]
    recommendations: List[str]


class HumanOverrideRequest(BaseModel):
    decision_id: str
    admin_id: str
    admin_name: str
    override_reason: str
    adjusted_output: Dict[str, Any]


class HumanOverrideResponse(BaseModel):
    override_id: str
    decision_id: str
    status: str = "APPLIED"
    recorded_at: datetime = Field(default_factory=datetime.now)
    audit_checksum: str
