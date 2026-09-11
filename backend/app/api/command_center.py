from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional, Any
from app.core.security import get_current_user
from app.models.command_center import (
    LiveCommandMetricsResponse,
    StateHeatmapMetric,
    AICommandInsight,
    SupportTicketResponse,
    CreateSupportTicketRequest,
    ExecutiveReportResponse,
    GenerateExecutiveReportRequest
)
from app.services.command_center_service import CommandCenterService

router = APIRouter(prefix="/api/v1/command-center", tags=["Super Admin AI Command Center"])

def _ensure_admin(current_user: Any):
    # In full environment, enforce role == 'admin' or allow authenticated admin users
    return True

@router.get("/live-metrics", response_model=LiveCommandMetricsResponse)
def get_live_metrics(current_user: Any = Depends(get_current_user)):
    """
    Realtime enterprise operations metrics pulse (Live users, GMV, orders, active disputes, fraud flags).
    """
    _ensure_admin(current_user)
    return CommandCenterService.get_live_metrics()

@router.get("/state-heatmap", response_model=List[StateHeatmapMetric])
def get_state_heatmap(current_user: Any = Depends(get_current_user)):
    """
    State-by-state volume, revenue, artisan density, and fulfillment speed heatmaps.
    """
    _ensure_admin(current_user)
    return CommandCenterService.get_state_heatmap()

@router.get("/ai-insights", response_model=List[AICommandInsight])
def get_ai_insights(current_user: Any = Depends(get_current_user)):
    """
    Autonomous AI anomaly detection (Demand spikes, fraud rings, underperforming regions, fast-growing categories).
    """
    _ensure_admin(current_user)
    return CommandCenterService.get_ai_insights()

@router.post("/tickets", response_model=SupportTicketResponse, status_code=status.HTTP_201_CREATED)
def create_support_ticket(
    payload: CreateSupportTicketRequest,
    current_user: Any = Depends(get_current_user)
):
    """
    Create a new support or dispute escalation ticket.
    """
    uid = getattr(current_user, "id", getattr(current_user, "uid", None)) if not isinstance(current_user, dict) else current_user.get("uid")
    return CommandCenterService.create_support_ticket(req=payload, user_id=uid)

@router.get("/tickets", response_model=List[SupportTicketResponse])
def list_support_tickets(current_user: Any = Depends(get_current_user)):
    """
    List enterprise customer support tickets and dispute logs.
    """
    _ensure_admin(current_user)
    return CommandCenterService.list_support_tickets()

@router.post("/reports/generate", response_model=ExecutiveReportResponse, status_code=status.HTTP_201_CREATED)
def generate_executive_report(
    payload: GenerateExecutiveReportRequest,
    current_user: Any = Depends(get_current_user)
):
    """
    Generate an AI executive briefing report with PDF download link.
    """
    _ensure_admin(current_user)
    return CommandCenterService.generate_executive_report(payload)

@router.get("/reports", response_model=List[ExecutiveReportResponse])
def list_executive_reports(current_user: Any = Depends(get_current_user)):
    """
    List past AI executive reports.
    """
    _ensure_admin(current_user)
    return CommandCenterService.list_executive_reports()
