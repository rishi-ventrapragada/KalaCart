"""Pydantic models for Sustainability Score & Carbon Intelligence domain (Phase 7)."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SustainabilityTier(str, Enum):
    bronze = "Bronze"
    silver = "Silver"
    gold = "Gold"
    green_leaf = "Green Leaf"


class LocalSourcingType(str, Enum):
    cluster = "cluster"      # Sourced within village/artisan cluster (< 50 km) - 20 pts
    regional = "regional"    # Sourced within state (< 300 km) - 15 pts
    national = "national"    # Sourced within India - 10 pts
    imported = "imported"    # Imported raw materials - 5 pts


class PlasticUsageType(str, Enum):
    zero_plastic = "zero_plastic"      # 100% plastic-free - 15 pts
    minimal = "minimal"                # < 5% plastic/resin - 10 pts
    moderate = "moderate"              # 5-20% plastic - 5 pts
    high = "high"                      # > 20% plastic - 0 pts


class PackagingType(str, Enum):
    zero_waste = "zero_waste"          # Compostable/jute/cloth/leaf wrap - 10 pts
    recycled_kraft = "recycled_kraft"  # Recycled corrugated/kraft paper - 8 pts
    standard_carton = "standard_carton"# Standard cardboard with paper fill - 6 pts
    plastic_wrap = "plastic_wrap"      # Plastic bubble wrap/thermocol - 0 pts


class MaterialOriginResponse(BaseModel):
    id: Optional[str] = None
    material_name: str
    category: str
    origin_cluster: str
    origin_state: str
    origin_lat: Optional[float] = None
    origin_lng: Optional[float] = None
    sustainability_score: int
    is_organic_natural: bool
    recycled_content_pct: float
    carbon_per_kg_kgco2e: float
    water_usage_liters_per_kg: float
    harvesting_method: Optional[str] = None
    biodegradable_days: Optional[int] = None


class RecyclingStep(BaseModel):
    component: str
    material: str
    recyclability_rating: str  # 100% Biodegradable, Curbside Recyclable, Upcyclable, Hazardous
    instruction: str
    disposal_bin_type: str


class ScoreFactorBreakdown(BaseModel):
    factor_name: str
    points_awarded: int
    max_points: int
    rating: str
    explanation: str


class SustainabilityCalculationRequest(BaseModel):
    product_id: Optional[str] = None
    materials: Optional[List[str]] = Field(default_factory=list, description="List of materials e.g. clay, terracotta, cotton")
    category: Optional[str] = "handicraft"
    weight_kg: Optional[float] = 1.0
    handmade_percentage: float = Field(default=100.0, ge=0.0, le=100.0, description="Handmade craftsmanship percentage (0-100)")
    local_sourcing: LocalSourcingType = Field(default=LocalSourcingType.cluster)
    plastic_usage: PlasticUsageType = Field(default=PlasticUsageType.zero_plastic)
    packaging: PackagingType = Field(default=PackagingType.zero_waste)


class SustainabilityScoreResponse(BaseModel):
    product_id: Optional[str] = None
    eco_score: int = Field(..., ge=0, le=100, description="Calculated Eco-Impact Score (0-100)")
    tier: SustainabilityTier
    badge_label: str
    badge_color_hex: str
    summary_headline: str
    overall_explanation: str
    
    # Phase 7 Core Metrics
    carbon_estimate_kgco2e: float = Field(..., description="Estimated product carbon footprint (kg CO2e)")
    carbon_saved_vs_industrial_kgco2e: float = Field(..., description="Carbon emissions saved compared to factory alternative")
    water_usage_liters: float = Field(..., description="Estimated water consumed in traditional crafting (liters)")
    water_saved_liters: float = Field(..., description="Water conserved vs synthetic industrial process")
    sustainable_material_score: int = Field(..., description="Raw Material score (0-30)")
    local_sourcing_score: int = Field(..., description="Local cluster sourcing score (0-20)")
    local_sourcing_radius_km: int = Field(default=35, description="Distance radius for raw material procurement (km)")
    eco_packaging_indicator: str = Field(..., description="Packaging type summary and rating")
    
    breakdowns: List[ScoreFactorBreakdown]
    key_positive_highlights: List[str]
    actionable_improvement_tips: List[str]
    material_origins: List[MaterialOriginResponse] = Field(default_factory=list)
    recycling_guidance: List[RecyclingStep] = Field(default_factory=list)


class OrderSustainabilityImpact(BaseModel):
    order_id: str
    order_number: Optional[str] = None
    total_carbon_kgco2e: float
    carbon_saved_kgco2e: float
    water_saved_liters: float
    eco_packaging_used: str
    trees_equivalent: float
    eco_certified_items_count: int
    message: str


class MonthlySustainabilityReportResponse(BaseModel):
    artisan_id: str
    report_month: str  # YYYY-MM
    total_orders_count: int
    eco_products_count: int
    eco_products_percentage: float
    total_carbon_saved_kgco2e: float
    total_water_saved_liters: float
    avg_eco_score: float
    trees_equivalent: float
    highlights: List[str] = Field(default_factory=list)
    metrics_summary: Dict[str, Any] = Field(default_factory=dict)
