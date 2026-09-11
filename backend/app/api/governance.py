"""
API Router for KalaCart Phase 7 — AI Governance & Explainability.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from app.models.governance import (
    AIDecisionRecord,
    DecisionExplanationResponse,
    ModelPerformanceMetric,
    BiasAuditReport,
    HumanOverrideRequest,
    HumanOverrideResponse,
)
from app.services.governance_service import GovernanceService

router = APIRouter(prefix="/governance", tags=["AI Governance & Explainability"])


@router.get("/explain/{decision_type}/{entity_id}", response_model=DecisionExplanationResponse)
def get_user_explainability_record(decision_type: str, entity_id: str):
    """
    Retrieve plain-language and feature attribution explanation for any AI decision
    (Pricing, Recommendations, Trust Score, Demand Forecast, Search Ranking, Fraud Detection).
    """
    explanation = GovernanceService.get_decision_explanation(
        decision_type=decision_type,
        entity_id=entity_id
    )
    if not explanation:
        raise HTTPException(
            status_code=404,
            detail=f"Explainability record for {decision_type} on {entity_id} not found"
        )
    return explanation


@router.get("/decisions", response_model=List[AIDecisionRecord])
def list_ai_decisions(
    decision_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    limit: int = Query(50, le=200)
):
    """Admin & Compliance View: Query immutable audit logs of production AI decisions."""
    return GovernanceService.list_decisions(
        decision_type=decision_type,
        entity_id=entity_id,
        limit=limit
    )


@router.get("/models/metrics", response_model=List[ModelPerformanceMetric])
def get_model_health_metrics():
    """Retrieve production ML telemetry: accuracy, drift divergence KL, p95 latency, parity ratio."""
    return GovernanceService.get_model_metrics()


@router.get("/bias-audit", response_model=BiasAuditReport)
def get_bias_and_fairness_report():
    """Retrieve demographic and regional parity fairness audit across Indian craft states."""
    return GovernanceService.get_bias_audit_report()


@router.post("/override", response_model=HumanOverrideResponse, status_code=status.HTTP_201_CREATED)
def apply_human_override(payload: HumanOverrideRequest):
    """Execute human supervisor override over an automated AI decision with audit trail."""
    return GovernanceService.apply_human_override(payload)
