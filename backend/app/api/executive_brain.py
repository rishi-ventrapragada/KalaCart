from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.security import get_current_user
from app.models.executive_brain import (
    ExecutiveInsightResponse,
    CashflowForecastResponse,
    RiskPredictionResponse,
    AIDecisionCreate,
    AIDecisionActionRequest,
    AIDecisionResponse,
    ExecutiveReportResponse
)
from app.services.executive_brain_service import executive_brain_service

router = APIRouter(prefix="/api/v1/brain", tags=["Predictive AI Executive Brain"])


@router.get("/insights", response_model=List[ExecutiveInsightResponse])
def get_insights(current_user: dict = Depends(get_current_user)):
    artisan_id = current_user.get("uid") or current_user.get("user_id") or "artisan_demo"
    return executive_brain_service.generate_executive_insights(artisan_id)


@router.get("/cashflow", response_model=CashflowForecastResponse)
def get_cashflow_forecast(current_user: dict = Depends(get_current_user)):
    artisan_id = current_user.get("uid") or current_user.get("user_id") or "artisan_demo"
    return executive_brain_service.get_cashflow_forecast(artisan_id)


@router.get("/risks", response_model=List[RiskPredictionResponse])
def get_risk_predictions(current_user: dict = Depends(get_current_user)):
    artisan_id = current_user.get("uid") or current_user.get("user_id") or "artisan_demo"
    return executive_brain_service.get_risk_predictions(artisan_id)


@router.get("/decisions", response_model=List[AIDecisionResponse])
def list_decisions(current_user: dict = Depends(get_current_user)):
    artisan_id = current_user.get("uid") or current_user.get("user_id") or "artisan_demo"
    return executive_brain_service.list_ai_decisions(artisan_id)


@router.post("/decisions", response_model=AIDecisionResponse, status_code=status.HTTP_201_CREATED)
def create_decision(payload: AIDecisionCreate, current_user: dict = Depends(get_current_user)):
    artisan_id = current_user.get("uid") or current_user.get("user_id") or "artisan_demo"
    return executive_brain_service.create_ai_decision(artisan_id, payload)


@router.post("/decisions/{decision_id}/action", response_model=AIDecisionResponse)
def act_on_decision(decision_id: str, payload: AIDecisionActionRequest, current_user: dict = Depends(get_current_user)):
    res = executive_brain_service.act_on_decision(decision_id, payload)
    if not res:
        raise HTTPException(status_code=404, detail="AI Decision proposal not found")
    return res


@router.get("/reports/executive", response_model=ExecutiveReportResponse)
def get_executive_report(report_type: str = Query("weekly", regex="^(weekly|monthly)$"), current_user: dict = Depends(get_current_user)):
    artisan_id = current_user.get("uid") or current_user.get("user_id") or "artisan_demo"
    return executive_brain_service.generate_executive_report(artisan_id, report_type)
