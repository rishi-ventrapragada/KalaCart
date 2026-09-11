"""
Demand Forecast & Production Planner API Router (Phase 4).
Endpoints for Multi-Horizon Forecasts (7/30/90 days), Production Batch Plans,
Procurement Alerts, and Workshop Workload Calendar.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.ai.forecast_planner import (
    generate_demand_forecasts,
    generate_production_calendar,
    generate_production_plans,
)
from app.core.security import get_current_user
from app.models.forecast_planner import (
    DemandForecastResponse,
    ProductionCalendarResponse,
    ProductionPlanCreate,
    ProductionPlanResponse,
    WorkloadStatus,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/forecast-planner", tags=["Demand Forecast & Production Planner"])

_mock_plans: Dict[str, dict] = {}


def _get_artisan_id(current_user: dict) -> str:
    artisan = current_user.get("artisan") or {}
    art_id = artisan.get("id")
    if art_id:
        return str(art_id)
    uid = current_user.get("firebase_uid")
    if uid:
        return str(uid)
    return "00000000-0000-0000-0000-000000000002"


@router.get("/forecasts", response_model=List[DemandForecastResponse])
async def get_demand_forecasts(
    current_user: dict = Depends(get_current_user),
):
    """
    Returns multi-horizon demand projections (7 days, 30 days, 90 days)
    combining historical sales, search volume, B2B RFQs, and festival calendar.
    """
    artisan_id = _get_artisan_id(current_user)
    return generate_demand_forecasts(artisan_id)


@router.get("/plans", response_model=List[ProductionPlanResponse])
async def get_production_plans(
    current_user: dict = Depends(get_current_user),
):
    """
    Returns active workshop production schedules and raw material procurement recommendations.
    """
    artisan_id = _get_artisan_id(current_user)
    items = [p for p in _mock_plans.values() if str(p.get("artisan_id")) == artisan_id]
    if not items:
        return generate_production_plans(artisan_id)
    return [ProductionPlanResponse(**p) for p in items]


@router.post("/plans", response_model=ProductionPlanResponse, status_code=status.HTTP_201_CREATED)
async def create_production_plan(
    req: ProductionPlanCreate,
    current_user: dict = Depends(get_current_user),
):
    """
    Creates a new planned production batch for the workshop.
    """
    artisan_id = _get_artisan_id(current_user)
    plan_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    plan_dict = {
        "id": plan_id,
        "artisan_id": artisan_id,
        "product_id": req.product_id,
        "batch_title": req.batch_title,
        "recommended_quantity": req.recommended_quantity,
        "current_inventory": req.current_inventory,
        "buffer_stock": req.buffer_stock,
        "required_materials": [m.dict() for m in req.required_materials],
        "procurement_recommendation": req.procurement_recommendation,
        "confidence_pct": 90,
        "start_date": req.start_date,
        "target_completion_date": req.target_completion_date,
        "delivery_deadline": req.delivery_deadline,
        "workload_status": req.workload_status.value,
        "estimated_production_cost": req.estimated_production_cost,
        "projected_revenue": req.projected_revenue,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }

    _mock_plans[plan_id] = plan_dict
    return ProductionPlanResponse(**plan_dict)


@router.get("/calendar", response_model=ProductionCalendarResponse)
async def get_production_calendar(
    current_user: dict = Depends(get_current_user),
):
    """
    Returns the workshop workload calendar with scheduled firing/weaving milestones and delivery deadlines.
    """
    artisan_id = _get_artisan_id(current_user)
    return generate_production_calendar(artisan_id)
