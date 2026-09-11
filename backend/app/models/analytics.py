from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class DailySaleStat(BaseModel):
    date: str
    sales_amount: float = Field(default=0.0)
    orders_count: int = Field(default=0)


class MonthlyRevenueStat(BaseModel):
    month: str
    revenue: float = Field(default=0.0)
    order_count: int = Field(default=0)


class TopProductStat(BaseModel):
    product_id: str
    title: str
    revenue: float = Field(default=0.0)
    units_sold: int = Field(default=0)
    image_url: Optional[str] = None


class CategoryPerformanceStat(BaseModel):
    category: str
    revenue: float = Field(default=0.0)
    order_count: int = Field(default=0)
    percentage: float = Field(default=0.0)


class BusinessMetrics(BaseModel):
    revenue: float = Field(default=0.0)
    orders: int = Field(default=0)
    average_order_value: float = Field(default=0.0)
    profit: float = Field(default=0.0)
    expenses: float = Field(default=0.0)
    conversion_rate: float = Field(default=0.0)
    repeat_buyers_percentage: float = Field(default=0.0)
    repeat_buyers_count: int = Field(default=0)
    total_buyers_count: int = Field(default=0)
    # Sustainability & Carbon metrics
    carbon_saved_kgco2e: float = Field(default=0.0)
    eco_products_percentage: float = Field(default=100.0)
    trees_equivalent: float = Field(default=0.0)


class BusinessInsights(BaseModel):
    best_selling_category: Optional[str] = None
    products_to_restock: List[str] = Field(default_factory=list)
    slow_moving_inventory: List[str] = Field(default_factory=list)
    highest_profit_product: Optional[str] = None
    highest_profit_amount: Optional[float] = None


class BusinessAnalyticsResponse(BaseModel):
    has_sufficient_data: bool = Field(default=False)
    metrics: BusinessMetrics
    daily_sales: List[DailySaleStat] = Field(default_factory=list)
    monthly_revenue: List[MonthlyRevenueStat] = Field(default_factory=list)
    top_products: List[TopProductStat] = Field(default_factory=list)
    category_performance: List[CategoryPerformanceStat] = Field(default_factory=list)
    insights: BusinessInsights


# ── Phase 7: Research & Market Intelligence Models ─────────────────────────────

class MarketReportResponse(BaseModel):
    id: Optional[str] = None
    report_title: str
    craft_category: str
    cluster_region: Optional[str] = "Pan-India"
    period: str = "2026-Q3"
    executive_summary: str
    demand_growth_pct: float
    top_driver: Optional[str] = None
    price_movement_pct: float
    export_potential_score: int
    key_insights: List[str] = Field(default_factory=list)
    warehouse_source: str = "analytics_warehouse"
    created_at: Optional[str] = None


class TrendPredictionResponse(BaseModel):
    id: Optional[str] = None
    craft_name: str
    category: str
    growth_rate_pct: float
    prediction_timeframe: str  # 'Next 30 Days', 'Next Quarter', 'Festive Season'
    peak_month: str
    confidence_score: int
    demand_level: str  # 'SURGING', 'HIGH', 'MODERATE', 'STABLE'
    average_market_price: float
    projected_price_delta_pct: float
    top_target_cities: List[str] = Field(default_factory=list)
    seasonal_factors: List[str] = Field(default_factory=list)


class CityDemandResponse(BaseModel):
    id: Optional[str] = None
    city_name: str
    state: str
    demand_index: int  # 0-100
    growth_yoy_pct: float
    search_volume_index: int
    top_trending_crafts: List[str] = Field(default_factory=list)
    average_order_value: float
    buyer_segment: str


class ExportOpportunityResponse(BaseModel):
    id: Optional[str] = None
    target_country: str
    country_code: str
    demand_score: int  # 0-100
    top_demanded_crafts: List[str] = Field(default_factory=list)
    annual_market_size_usd: float
    import_duty_advantage: Optional[str] = None
    gi_protection_recognized: bool = True
    recommended_certifications: List[str] = Field(default_factory=list)


class ExportReadinessEvaluation(BaseModel):
    artisan_id: str
    overall_readiness_score: int  # 0-100
    readiness_tier: str  # 'Export Champion', 'Export Ready', 'Developing Capacity', 'Domestic Focus'
    gi_compliance_score: int
    digital_traceability_score: int
    eco_packaging_score: int
    pricing_competitiveness_score: int
    top_recommended_markets: List[str] = Field(default_factory=list)
    actionable_checkpoints: List[str] = Field(default_factory=list)


class AIInsightQuote(BaseModel):
    id: str
    headline: str
    craft: str
    region_or_city: str
    growth_stat: str
    sentiment: str  # 'BULLISH', 'OPPORTUNITY', 'EXPANDING'
    recommended_action: str


class MarketIntelligenceDashboardResponse(BaseModel):
    summary_reports: List[MarketReportResponse]
    trending_crafts: List[TrendPredictionResponse]
    city_demand_matrix: List[CityDemandResponse]
    export_opportunities: List[ExportOpportunityResponse]
    ai_insights: List[AIInsightQuote]
    top_growing_category: str
    national_demand_momentum_pct: float
    generated_at: str
