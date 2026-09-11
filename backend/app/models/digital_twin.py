from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class DigitalTwinBaseline(BaseModel):
    revenue_monthly: float = 125000.00
    profit_margin_pct: float = 28.5
    avg_order_value: float = 1450.00
    active_customers: int = 320
    monthly_orders: int = 86
    inventory_units: int = 450
    production_capacity_monthly: int = 120
    delivery_lead_days: float = 4.5
    export_active: bool = False
    worker_count: int = 3
    unit_cost_avg: float = 650.00
    unit_price_avg: float = 1450.00
    shipping_region: str = "Pan-India"


class OperationalParameters(BaseModel):
    fixed_monthly_overhead: float = 22000.00
    worker_monthly_wage: float = 18000.00
    worker_capacity_units: int = 40
    price_elasticity: float = -1.35
    export_markup_pct: float = 35.0
    export_shipping_cost: float = 1200.00
    seasonal_index: float = 1.15


class DigitalTwinResponse(BaseModel):
    id: str
    artisan_id: str
    business_name: str
    craft_category: str
    baseline_metrics: DigitalTwinBaseline
    operational_parameters: OperationalParameters
    status: str
    last_sync_at: str
    created_at: str
    updated_at: str


class DigitalTwinUpdate(BaseModel):
    business_name: Optional[str] = None
    craft_category: Optional[str] = None
    baseline_metrics: Optional[Dict[str, Any]] = None
    operational_parameters: Optional[Dict[str, Any]] = None


class SimulationLevers(BaseModel):
    price_adjustment_pct: float = Field(default=0.0, description="Price change in percentage, e.g. 10.0 for +10%")
    festival_discount_pct: float = Field(default=0.0, description="Festival promotional discount percentage, e.g. 15.0")
    extra_units_produced: int = Field(default=0, description="Extra production batch size in units, e.g. 100")
    hire_workers_count: int = Field(default=0, description="Additional workers hired, e.g. 1")
    enable_export: bool = Field(default=False, description="Open export channels to international buyers")
    shipping_region: Optional[str] = Field(default=None, description="Target shipping region: Pan-India, Tier-1 Metro, South India, Global (Export)")
    marketing_boost_pct: float = Field(default=0.0, description="Marketing spend increase percentage")
    simulation_horizon_months: int = Field(default=6, ge=1, le=24, description="Horizon for multi-month projections")


class ScenarioPreset(BaseModel):
    id: str
    name: str
    description: str
    icon: str
    scenario_type: str
    default_levers: SimulationLevers


class ProjectedMetrics(BaseModel):
    revenue_monthly: float
    profit_monthly: float
    profit_margin_pct: float
    demand_units_monthly: int
    units_sold_monthly: int
    inventory_end_units: int
    stockout_risk_pct: float
    delivery_workload_hours: float
    capacity_utilization_pct: float
    customer_growth_pct: float
    active_customers: int


class DeltaComparison(BaseModel):
    revenue_delta: float
    revenue_delta_pct: float
    profit_delta: float
    profit_delta_pct: float
    demand_delta_units: int
    demand_delta_pct: float
    inventory_delta_units: int
    workload_delta_hours: float
    customer_growth_delta: int


class MonthlyProjectionPoint(BaseModel):
    month: int
    month_name: str
    baseline_revenue: float
    simulated_revenue: float
    baseline_profit: float
    simulated_profit: float
    baseline_demand: int
    simulated_demand: int
    baseline_inventory: int
    simulated_inventory: int
    baseline_workload_hours: float
    simulated_workload_hours: float
    baseline_customers: int
    simulated_customers: int


class AIInsights(BaseModel):
    summary: str
    key_opportunities: List[str]
    risk_warnings: List[str]
    recommended_actions: List[str]
    confidence_score: float = 92.0


class SimulationRunRequest(BaseModel):
    scenario_name: str
    scenario_type: str = Field(
        default="custom_multi_lever",
        description="price_change, festival_discount, produce_extra, hire_worker, open_export, change_shipping_region, custom_multi_lever"
    )
    levers: SimulationLevers


class SimulationResultResponse(BaseModel):
    id: str
    simulation_run_id: str
    artisan_id: str
    scenario_name: str
    scenario_type: str
    levers: SimulationLevers
    baseline_snapshot: Dict[str, Any]
    projected_metrics: ProjectedMetrics
    delta_comparison: DeltaComparison
    monthly_projections: List[MonthlyProjectionPoint]
    ai_insights: AIInsights
    created_at: str


class SimulationRunSummary(BaseModel):
    id: str
    digital_twin_id: str
    artisan_id: str
    scenario_name: str
    scenario_type: str
    levers: Dict[str, Any]
    status: str
    created_at: str
    result_preview: Optional[Dict[str, Any]] = None


class SimulationComparisonResponse(BaseModel):
    runs: List[SimulationResultResponse]
    best_revenue_run_id: str
    best_profit_run_id: str
    lowest_risk_run_id: str
    comparative_summary: str
