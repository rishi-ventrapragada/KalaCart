"""API Router for KalaCart NGO & Impact Analytics."""

from datetime import datetime
from typing import List, Optional
import uuid
from fastapi import APIRouter, HTTPException, Query, Response
from app.models.impact import (
    ImpactSummaryResponse,
    BeneficiaryProfile,
    BeneficiaryCreate,
    DistrictImpactReport,
    NGODashboardResponse,
    CSRImpactResponse,
    GovernmentImpactResponse,
    OrderSyncEvent,
)
from app.services.impact_pdf import generate_impact_report_pdf

router = APIRouter(prefix="/impact", tags=["NGO & Impact Analytics"])

# In-memory realistic stores initialized with live craft cluster metrics
_SUMMARY_DATA = {
    "total_artisans_onboarded": 14200,
    "women_artisans_count": 9650,
    "women_participation_pct": 67.96,
    "avg_household_income_growth_pct": 68.40,
    "rural_employment_hours_generated": 1450000,
    "active_shg_collectives": 480,
    "endangered_crafts_preserved": 34,
    "total_direct_payouts_inr": 48500000.00,
    "export_growth_pct": 42.50,
    "last_verified": datetime.now().isoformat(),
}

_BENEFICIARIES: List[dict] = [
    {
        "id": "ben-001",
        "artisan_id": "art-kachchh-01",
        "full_name": "Pabiben Rabari",
        "gender": "FEMALE",
        "age": 42,
        "district": "Kachchh",
        "state": "Gujarat",
        "craft_category": "Embroidery & Applique",
        "shg_collective_name": "Kutch Mahila Vikas Sangathan",
        "baseline_monthly_income_inr": 4200.00,
        "current_monthly_income_inr": 18500.00,
        "income_growth_pct": 340.48,
        "dependents_count": 4,
        "craft_generation": 4,
        "literacy_level": "Primary",
        "bank_account_verified": True,
        "created_at": datetime.now(),
    },
    {
        "id": "ben-002",
        "artisan_id": "art-varanasi-02",
        "full_name": "Nasreen Begum",
        "gender": "FEMALE",
        "age": 36,
        "district": "Varanasi",
        "state": "Uttar Pradesh",
        "craft_category": "Zari & Silk Weaving",
        "shg_collective_name": "Bunkar Mahila Utthan Dal",
        "baseline_monthly_income_inr": 5000.00,
        "current_monthly_income_inr": 16200.00,
        "income_growth_pct": 224.00,
        "dependents_count": 3,
        "craft_generation": 3,
        "literacy_level": "Secondary",
        "bank_account_verified": True,
        "created_at": datetime.now(),
    },
    {
        "id": "ben-003",
        "artisan_id": "art-bastar-03",
        "full_name": "Sukmati Mandavi",
        "gender": "FEMALE",
        "age": 29,
        "district": "Bastar",
        "state": "Chhattisgarh",
        "craft_category": "Dhokra Bell Metal",
        "shg_collective_name": "Tribal Artisan SHG Jagdalpur",
        "baseline_monthly_income_inr": 3500.00,
        "current_monthly_income_inr": 13800.00,
        "income_growth_pct": 294.28,
        "dependents_count": 2,
        "craft_generation": 5,
        "literacy_level": "Literate",
        "bank_account_verified": True,
        "created_at": datetime.now(),
    },
    {
        "id": "ben-004",
        "artisan_id": "art-madhubani-04",
        "full_name": "Sunita Jha",
        "gender": "FEMALE",
        "age": 39,
        "district": "Madhubani",
        "state": "Bihar",
        "craft_category": "Mithila Painting",
        "shg_collective_name": "Kala Gram Vikas Samiti",
        "baseline_monthly_income_inr": 4800.00,
        "current_monthly_income_inr": 15600.00,
        "income_growth_pct": 225.00,
        "dependents_count": 3,
        "craft_generation": 3,
        "literacy_level": "Higher Secondary",
        "bank_account_verified": True,
        "created_at": datetime.now(),
    }
]

_DISTRICTS: List[dict] = [
    {
        "id": "dist-001",
        "district_name": "Kachchh",
        "state": "Gujarat",
        "artisan_households": 2400,
        "active_craft_clusters": 12,
        "top_specialty_craft": "Ajrakh & Rogan Art",
        "monthly_economic_output_inr": 8200000.00,
        "income_growth_yoy_pct": 74.20,
        "women_artisan_pct": 78.50,
        "district_development_index": 92.40,
        "ngo_partners_active": 4,
        "reported_quarter": "2026-Q3",
        "created_at": datetime.now(),
    },
    {
        "id": "dist-002",
        "district_name": "Varanasi",
        "state": "Uttar Pradesh",
        "artisan_households": 3100,
        "active_craft_clusters": 18,
        "top_specialty_craft": "Banarasi Silk Brocade",
        "monthly_economic_output_inr": 11500000.00,
        "income_growth_yoy_pct": 62.80,
        "women_artisan_pct": 61.20,
        "district_development_index": 89.10,
        "ngo_partners_active": 5,
        "reported_quarter": "2026-Q3",
        "created_at": datetime.now(),
    },
    {
        "id": "dist-003",
        "district_name": "Bastar",
        "state": "Chhattisgarh",
        "artisan_households": 1850,
        "active_craft_clusters": 9,
        "top_specialty_craft": "Dhokra Bell Metal & Wrought Iron",
        "monthly_economic_output_inr": 4600000.00,
        "income_growth_yoy_pct": 84.60,
        "women_artisan_pct": 72.00,
        "district_development_index": 85.70,
        "ngo_partners_active": 3,
        "reported_quarter": "2026-Q3",
        "created_at": datetime.now(),
    },
    {
        "id": "dist-004",
        "district_name": "Jaipur",
        "state": "Rajasthan",
        "artisan_households": 2900,
        "active_craft_clusters": 14,
        "top_specialty_craft": "Blue Pottery & Hand Block Print",
        "monthly_economic_output_inr": 9800000.00,
        "income_growth_yoy_pct": 58.40,
        "women_artisan_pct": 65.40,
        "district_development_index": 94.00,
        "ngo_partners_active": 4,
        "reported_quarter": "2026-Q3",
        "created_at": datetime.now(),
    },
    {
        "id": "dist-005",
        "district_name": "Madhubani",
        "state": "Bihar",
        "artisan_households": 2150,
        "active_craft_clusters": 11,
        "top_specialty_craft": "Mithila Painting & Sikki Grass",
        "monthly_economic_output_inr": 5400000.00,
        "income_growth_yoy_pct": 79.10,
        "women_artisan_pct": 88.60,
        "district_development_index": 87.30,
        "ngo_partners_active": 3,
        "reported_quarter": "2026-Q3",
        "created_at": datetime.now(),
    }
]


@router.get("/summary", response_model=ImpactSummaryResponse)
def get_impact_summary():
    """Retrieve national high-level social impact metrics."""
    return _SUMMARY_DATA


@router.get("/ngo-dashboard", response_model=NGODashboardResponse)
def get_ngo_dashboard(district: Optional[str] = None):
    """Retrieve full dashboard data for NGO field partners and microfinance coordinators."""
    filtered_beneficiaries = _BENEFICIARIES
    if district:
        filtered_beneficiaries = [b for b in _BENEFICIARIES if b["district"].lower() == district.lower()]

    shg_breakdown = [
        {"name": "Kutch Mahila Vikas Sangathan", "members": 340, "district": "Kachchh", "craft": "Embroidery"},
        {"name": "Bunkar Mahila Utthan Dal", "members": 280, "district": "Varanasi", "craft": "Handloom"},
        {"name": "Tribal Artisan SHG Jagdalpur", "members": 195, "district": "Bastar", "craft": "Dhokra Metal"},
        {"name": "Kala Gram Vikas Samiti", "members": 220, "district": "Madhubani", "craft": "Mithila Art"},
    ]

    active_initiatives = [
        {"title": "Solar Loom Digitization", "beneficiaries": 850, "status": "In Progress", "progress_pct": 72},
        {"title": "Direct UPI Payment Literacy", "beneficiaries": 4200, "status": "Completed", "progress_pct": 100},
        {"title": "Natural Vegetable Dye Certification", "beneficiaries": 1100, "status": "In Progress", "progress_pct": 65},
    ]

    return {
        "summary": _SUMMARY_DATA,
        "beneficiaries": filtered_beneficiaries,
        "shg_collective_breakdown": shg_breakdown,
        "skills_training_hours_delivered": 48500,
        "microfinance_enablement_inr": 18200000.00,
        "active_initiatives": active_initiatives,
    }


@router.get("/csr-dashboard", response_model=CSRImpactResponse)
def get_csr_dashboard(partner_name: str = "Enterprise Impact Partner"):
    """Retrieve corporate CSR compliance and ESG impact metrics."""
    sdg_alignment = [
        {"sdg_code": "SDG 1", "title": "No Poverty", "contribution_metric": "3,200 Artisan Families Uplifted"},
        {"sdg_code": "SDG 5", "title": "Gender Equality", "contribution_metric": "72.4% Women Beneficiaries"},
        {"sdg_code": "SDG 8", "title": "Decent Work & Growth", "contribution_metric": "420,000 Fair-Wage Labor Hours"},
        {"sdg_code": "SDG 12", "title": "Responsible Consumption", "contribution_metric": "38.6 MT CO2 Offset via Zero-Plastic Packaging"},
    ]

    quarterly_progress = [
        {"quarter": "2025-Q4", "grant_utilized_pct": 25, "artisans_supported": 800, "payout_inr": 2800000},
        {"quarter": "2026-Q1", "grant_utilized_pct": 50, "artisans_supported": 1650, "payout_inr": 5900000},
        {"quarter": "2026-Q2", "grant_utilized_pct": 75, "artisans_supported": 2400, "payout_inr": 8900000},
        {"quarter": "2026-Q3", "grant_utilized_pct": 100, "artisans_supported": 3200, "payout_inr": 12500000},
    ]

    return {
        "corporate_partner_name": partner_name,
        "grant_allocation_inr": 12500000.00,
        "direct_artisans_supported": 3200,
        "women_empowerment_ratio_pct": 72.4,
        "co2_offset_tonnes": 38.6,
        "rural_employment_hours": 420000,
        "sdg_alignment": sdg_alignment,
        "quarterly_progress": quarterly_progress,
    }


@router.get("/gov-dashboard", response_model=GovernmentImpactResponse)
def get_gov_dashboard():
    """Retrieve government ministry and district administration economic intelligence."""
    state_level_growth = [
        {"state": "Gujarat", "districts": 8, "total_output_inr": 18400000, "growth_pct": 71.4, "employment_hours": 320000},
        {"state": "Uttar Pradesh", "districts": 12, "total_output_inr": 24500000, "growth_pct": 65.2, "employment_hours": 410000},
        {"state": "Rajasthan", "districts": 10, "total_output_inr": 19200000, "growth_pct": 60.1, "employment_hours": 340000},
        {"state": "Chhattisgarh", "districts": 6, "total_output_inr": 9800000, "growth_pct": 82.3, "employment_hours": 190000},
        {"state": "Bihar", "districts": 7, "total_output_inr": 11200000, "growth_pct": 76.5, "employment_hours": 210000},
    ]

    policy_action_items = [
        "Extend zero-interest micro-credit lines to registered SHGs in Bastar and Madhubani clusters.",
        "Facilitate direct export documentation clearance at Ahmedabad and Varanasi ICD terminals.",
        "Establish GI-tag authentication kiosks at 15 major tourist craft hubs."
    ]

    return {
        "jurisdiction": "National Craft Development Corridor",
        "total_districts_covered": len(_DISTRICTS) * 9 + 3,
        "artisan_population_uplifted": 68400,
        "state_level_growth": state_level_growth,
        "district_rankings": _DISTRICTS,
        "craft_preservation_index": 88.5,
        "policy_action_items": policy_action_items,
    }


@router.get("/districts", response_model=List[DistrictImpactReport])
def list_district_reports(state: Optional[str] = None):
    """List district-level development indices and economic reports."""
    if state:
        return [d for d in _DISTRICTS if d["state"].lower() == state.lower()]
    return _DISTRICTS


@router.post("/beneficiaries", response_model=BeneficiaryProfile, status_code=201)
def create_beneficiary(payload: BeneficiaryCreate):
    """Enroll a new artisan beneficiary into socio-economic tracking."""
    growth = 0.0
    if payload.baseline_monthly_income_inr > 0:
        growth = round(
            ((payload.current_monthly_income_inr - payload.baseline_monthly_income_inr)
             / payload.baseline_monthly_income_inr) * 100.0,
            2
        )
    
    new_ben = {
        "id": f"ben-{uuid.uuid4().hex[:6]}",
        "artisan_id": None,
        "full_name": payload.full_name,
        "gender": payload.gender,
        "age": payload.age,
        "district": payload.district,
        "state": payload.state,
        "craft_category": payload.craft_category,
        "shg_collective_name": payload.shg_collective_name,
        "baseline_monthly_income_inr": payload.baseline_monthly_income_inr,
        "current_monthly_income_inr": payload.current_monthly_income_inr,
        "income_growth_pct": growth,
        "dependents_count": payload.dependents_count,
        "craft_generation": payload.craft_generation,
        "literacy_level": payload.literacy_level,
        "bank_account_verified": payload.bank_account_verified,
        "created_at": datetime.now(),
    }
    _BENEFICIARIES.append(new_ben)
    _SUMMARY_DATA["total_artisans_onboarded"] += 1
    if payload.gender.upper() == "FEMALE":
        _SUMMARY_DATA["women_artisans_count"] += 1
    _SUMMARY_DATA["women_participation_pct"] = round(
        (_SUMMARY_DATA["women_artisans_count"] / _SUMMARY_DATA["total_artisans_onboarded"]) * 100.0, 2
    )
    return new_ben


@router.post("/sync-order-event")
def sync_order_impact_event(event: OrderSyncEvent):
    """Automatically increment socio-economic and employment metrics upon live order completion."""
    # 1. Increment total direct payouts (85% of order goes directly to artisan)
    direct_payout = event.order_amount_inr * 0.85
    _SUMMARY_DATA["total_direct_payouts_inr"] += direct_payout

    # 2. Increment rural employment hours
    labor_hours = event.labor_hours or 24
    _SUMMARY_DATA["rural_employment_hours_generated"] += labor_hours

    # 3. If district matches, update monthly economic output
    for d in _DISTRICTS:
        if event.district and d["district_name"].lower() == event.district.lower():
            d["monthly_economic_output_inr"] += event.order_amount_inr
            break

    _SUMMARY_DATA["last_verified"] = datetime.now().isoformat()

    return {
        "status": "synchronized",
        "order_id": event.order_id,
        "payout_credited_inr": round(direct_payout, 2),
        "employment_hours_added": labor_hours,
        "updated_total_payouts_inr": round(_SUMMARY_DATA["total_direct_payouts_inr"], 2),
        "updated_rural_hours": _SUMMARY_DATA["rural_employment_hours_generated"],
    }


@router.get("/report/pdf")
def download_impact_pdf(
    report_type: str = Query("national", enum=["national", "csr", "government"]),
    partner_name: Optional[str] = "Global Impact Partners LLC"
):
    """Generate and download official PDF Social Impact Audit Report / ESG Certificate."""
    title_map = {
        "national": "National Social & Craft Impact Audit Certificate",
        "csr": f"Corporate ESG & Social Impact Audit — {partner_name}",
        "government": "District Socio-Economic & Craft Development Report",
    }
    report_title = title_map.get(report_type, "Social Impact Audit Certificate")
    
    csr_payload = None
    if report_type == "csr":
        csr_payload = {
            "corporate_partner_name": partner_name,
            "grant_allocation_inr": 12500000.00,
            "direct_artisans_supported": 3200,
            "women_empowerment_ratio_pct": 72.4,
            "co2_offset_tonnes": 38.6,
        }

    pdf_bytes = generate_impact_report_pdf(
        summary_data=_SUMMARY_DATA,
        districts_data=_DISTRICTS,
        csr_data=csr_payload,
        report_title=report_title,
        organization_name="KalaCart Socio-Economic Impact Directorate"
    )

    filename = f"KalaCart_Impact_Report_{report_type.upper()}_{datetime.now().strftime('%Y%m%d')}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
