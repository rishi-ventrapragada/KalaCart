"""
Pydantic Schemas for Demand Forecast & Production Planner (Phase 4).
"""

from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ForecastHorizon(str, Enum):
    DAYS_7 = "7_DAYS"
    DAYS_30 = "30_DAYS"
    DAYS_90 = "90_DAYS"


class WorkloadStatus(str, Enum):
    PLANNED = "PLANNED"
    IN_PROGRESS = "IN_PROGRESS"
    FIRING_WEAVING = "FIRING_WEAVING"
    QUALITY_CHECK = "QUALITY_CHECK"
    COMPLETED = "COMPLETED"


class MaterialRequirement(BaseModel):
    material_name: str
    required_amount: str
    estimated_cost: float
    is_in_stock: bool = False
    procurement_source: Optional[str] = None


class DemandForecastResponse(BaseModel):
    id: str
    artisan_id: str
    product_title: Optional[str] = None
    craft_category: str
    horizon: ForecastHorizon
    predicted_units: int
    estimated_revenue: float
    confidence_score: int
    seasonal_multiplier: float
    search_trend_factor: float
    rfq_demand_units: int
    historical_velocity: float
    key_drivers: List[str] = []
    forecast_generated_at: datetime
    valid_until: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductionPlanCreate(BaseModel):
    product_id: Optional[str] = None
    batch_title: str
    recommended_quantity: int = Field(..., ge=1)
    current_inventory: int = Field(default=0, ge=0)
    buffer_stock: int = Field(default=5, ge=0)
    required_materials: List[MaterialRequirement] = []
    procurement_recommendation: Optional[str] = None
    start_date: date
    target_completion_date: date
    delivery_deadline: Optional[date] = None
    workload_status: WorkloadStatus = WorkloadStatus.PLANNED
    estimated_production_cost: float = Field(default=0.0, ge=0)
    projected_revenue: float = Field(default=0.0, ge=0)


class ProductionPlanResponse(BaseModel):
    id: str
    artisan_id: str
    product_id: Optional[str] = None
    batch_title: str
    recommended_quantity: int
    current_inventory: int
    buffer_stock: int
    required_materials: List[MaterialRequirement] = []
    procurement_recommendation: Optional[str] = None
    confidence_pct: int = 88
    start_date: date
    target_completion_date: date
    delivery_deadline: Optional[date] = None
    workload_status: WorkloadStatus
    estimated_production_cost: float
    projected_revenue: float
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CalendarEvent(BaseModel):
    event_id: str
    title: str
    event_type: str  # BATCH_START, KILN_FIRING, LOOM_WEAVING, QUALITY_AUDIT, DELIVERY_DEADLINE
    event_date: date
    product_title: str
    quantity: int
    status: str
    priority: str  # HIGH, MEDIUM, NORMAL


class ProductionCalendarResponse(BaseModel):
    artisan_id: str
    current_workload_hours: float
    capacity_utilization_pct: float
    active_batches_count: int
    upcoming_deadlines_count: int
    events: List[CalendarEvent] = []
    planner_summary: str
