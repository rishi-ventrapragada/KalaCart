from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class BeneficiaryProfile(BaseModel):
    id: str
    artisan_id: Optional[str] = None
    full_name: str
    gender: str = "FEMALE"
    age: Optional[int] = None
    district: str
    state: str
    craft_category: str
    shg_collective_name: Optional[str] = None
    baseline_monthly_income_inr: float = 4500.00
    current_monthly_income_inr: float = 14200.00
    income_growth_pct: float = 215.56
    dependents_count: int = 3
    craft_generation: int = 3
    literacy_level: str = "Secondary"
    bank_account_verified: bool = True
    created_at: Optional[datetime] = None


class BeneficiaryCreate(BaseModel):
    full_name: str
    gender: str = "FEMALE"
    age: Optional[int] = None
    district: str
    state: str
    craft_category: str
    shg_collective_name: Optional[str] = None
    baseline_monthly_income_inr: float = 4500.00
    current_monthly_income_inr: float = 14200.00
    dependents_count: int = 3
    craft_generation: int = 3
    literacy_level: str = "Secondary"
    bank_account_verified: bool = True


class DistrictImpactReport(BaseModel):
    id: str
    district_name: str
    state: str
    artisan_households: int
    active_craft_clusters: int
    top_specialty_craft: str
    monthly_economic_output_inr: float
    income_growth_yoy_pct: float
    women_artisan_pct: float
    district_development_index: float  # 0 to 100
    ngo_partners_active: int = 2
    reported_quarter: str = "2026-Q3"
    created_at: Optional[datetime] = None


class ImpactSummaryResponse(BaseModel):
    total_artisans_onboarded: int = 14200
    women_artisans_count: int = 9650
    women_participation_pct: float = 67.96
    avg_household_income_growth_pct: float = 68.40
    rural_employment_hours_generated: int = 1450000
    active_shg_collectives: int = 480
    endangered_crafts_preserved: int = 34
    total_direct_payouts_inr: float = 48500000.00
    export_growth_pct: float = 42.50
    last_verified: str


class NGODashboardResponse(BaseModel):
    summary: ImpactSummaryResponse
    beneficiaries: List[BeneficiaryProfile]
    shg_collective_breakdown: List[dict]
    skills_training_hours_delivered: int = 48500
    microfinance_enablement_inr: float = 18200000.00
    active_initiatives: List[dict]


class CSRImpactResponse(BaseModel):
    corporate_partner_name: str = "Enterprise Impact Partner"
    grant_allocation_inr: float = 12500000.00
    direct_artisans_supported: int = 3200
    women_empowerment_ratio_pct: float = 72.4
    co2_offset_tonnes: float = 38.6
    rural_employment_hours: int = 420000
    sdg_alignment: List[dict]
    quarterly_progress: List[dict]


class GovernmentImpactResponse(BaseModel):
    jurisdiction: str = "National Craft Development Corridor"
    total_districts_covered: int = 48
    artisan_population_uplifted: int = 68400
    state_level_growth: List[dict]
    district_rankings: List[DistrictImpactReport]
    craft_preservation_index: float = 88.5
    policy_action_items: List[str]


class OrderSyncEvent(BaseModel):
    order_id: str
    order_amount_inr: float
    craft_category: Optional[str] = "Handloom"
    district: Optional[str] = "Kachchh"
    state: Optional[str] = "Gujarat"
    is_women_led: bool = True
    labor_hours: Optional[int] = 24
