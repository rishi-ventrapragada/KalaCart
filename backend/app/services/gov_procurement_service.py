import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from app.database.connection import get_supabase_client
from app.models.gov_procurement import (
    GovernmentBuyerRegister,
    GovernmentBuyerProfile,
    TenderDocumentCreate,
    TenderDocumentResponse,
    TenderBidCreate,
    TenderBidResponse,
    ContractAwardResponse,
    MilestoneResponse,
    MilestoneActionRequest,
    TenderEvaluationRequest,
    EligibilityCriteria
)

logger = logging.getLogger(__name__)


# In-memory storage fallback for resilient execution and mock testing
_mock_buyers: Dict[str, Dict[str, Any]] = {}
_mock_tenders: Dict[str, Dict[str, Any]] = {}
_mock_bids: Dict[str, List[Dict[str, Any]]] = {}
_mock_contracts: Dict[str, Dict[str, Any]] = {}
_mock_milestones: Dict[str, List[Dict[str, Any]]] = {}


def _seed_sample_procurement_data():
    if _mock_tenders:
        return

    # Seed 1: Government Buyer
    b_id = "gov_buyer_ministry_textiles"
    _mock_buyers[b_id] = {
        "id": "00000000-0000-0000-0000-000000000010",
        "user_id": b_id,
        "organization_name": "Ministry of Textiles & Handicrafts Board",
        "buyer_type": "government",
        "department": "National Handloom & Craft Procurement Cell",
        "nodal_officer_name": "Dr. Rajeshwar Sharma, IAS",
        "nodal_officer_email": "rajeshwar.sharma@gov.in",
        "nodal_officer_phone": "+91 11 2306 1234",
        "pan_number": "AAAGM1234E",
        "gstin": "07AAAGM1234E1Z1",
        "gem_buyer_id": "GEM-BUY-2026-99881",
        "csr_registration_number": None,
        "verification_status": "verified",
        "allocated_annual_budget": 50000000.00,
        "documents": [{"name": "GeM_Official_Certificate.pdf", "url": "https://kalacart.in/docs/gem_cert.pdf"}],
        "created_at": "2026-08-01T09:00:00Z",
        "updated_at": "2026-08-01T09:00:00Z"
    }

    # Seed 2: CSR Foundation Buyer
    csr_id = "csr_tata_trusts"
    _mock_buyers[csr_id] = {
        "id": "00000000-0000-0000-0000-000000000011",
        "user_id": csr_id,
        "organization_name": "Tata Community Initiatives Trust (CSR)",
        "buyer_type": "csr",
        "department": "Rural Artisan Livelihoods & Gifting",
        "nodal_officer_name": "Meera Nambiar",
        "nodal_officer_email": "meera.nambiar@tata.com",
        "nodal_officer_phone": "+91 22 6665 8282",
        "pan_number": "AAATT9988C",
        "gstin": "27AAATT9988C1ZK",
        "gem_buyer_id": None,
        "csr_registration_number": "CSR00018492",
        "verification_status": "verified",
        "allocated_annual_budget": 25000000.00,
        "documents": [{"name": "CSR1_Registration.pdf", "url": "https://kalacart.in/docs/csr1.pdf"}],
        "created_at": "2026-08-10T10:00:00Z",
        "updated_at": "2026-08-10T10:00:00Z"
    }

    # Seed 3: Hotel & Tourism Buyer
    hotel_id = "hotel_taj_palace"
    _mock_buyers[hotel_id] = {
        "id": "00000000-0000-0000-0000-000000000012",
        "user_id": hotel_id,
        "organization_name": "Taj Heritage Hotels & Resorts Group",
        "buyer_type": "hotel",
        "department": "Procurement & Interior Heritage Architecture",
        "nodal_officer_name": "Vikramaditya Roy",
        "nodal_officer_email": "v.roy@ihclhotels.com",
        "nodal_officer_phone": "+91 11 2611 0202",
        "pan_number": "AAACT5544K",
        "gstin": "07AAACT5544K1ZS",
        "gem_buyer_id": None,
        "csr_registration_number": None,
        "verification_status": "verified",
        "allocated_annual_budget": 18000000.00,
        "documents": [{"name": "IHCL_Corporate_GST.pdf", "url": "https://kalacart.in/docs/ihcl_gst.pdf"}],
        "created_at": "2026-08-15T11:00:00Z",
        "updated_at": "2026-08-15T11:00:00Z"
    }

    # Seed Tender 1
    t1_id = "tender-gov-2026-001"
    _mock_tenders[t1_id] = {
        "id": t1_id,
        "tender_number": "KC-GOV-2026-POCH-091",
        "buyer_id": b_id,
        "buyer_name": "Ministry of Textiles & Handicrafts Board",
        "buyer_type": "government",
        "title": "National Republic Day Diplomatic Gifting: 2,500 Pochampally Ikat Silk Stoles",
        "description": "Procurement of 2,500 GI Tagged authentic Pochampally Double Ikat pure mulberry silk stoles with zari border for international diplomatic delegates.",
        "craft_category": "Textile",
        "target_quantity": 2500,
        "estimated_budget": 4500000.00,
        "delivery_deadline": "2026-11-30T18:00:00Z",
        "delivery_location": "Vigyan Bhawan Central Warehouse, New Delhi - 110001",
        "eligibility_criteria": {
            "msme_only": True,
            "gi_priority": True,
            "min_experience_years": 2,
            "cluster_state_preference": "Telangana",
            "shg_women_quota": True
        },
        "technical_specs": {
            "warp_weft": "Pure Mulberry Silk (100%)",
            "dimensions_cm": "200 x 70",
            "gi_tag_required": True,
            "silk_mark_certified": True
        },
        "document_urls": ["https://kalacart.in/tenders/pochampally_rfp_spec.pdf"],
        "lifecycle_stage": "published",
        "bids_count": 2,
        "created_at": "2026-08-20T10:00:00Z",
        "updated_at": "2026-08-20T10:00:00Z"
    }

    # Seed Bids for Tender 1
    bid1_id = "bid-artisan-01"
    bid2_id = "bid-artisan-02"
    _mock_bids[t1_id] = [
        {
            "id": bid1_id,
            "tender_id": t1_id,
            "artisan_id": "artisan_shg_pochampally",
            "artisan_business_name": "Pochampally Handloom Weavers Cooperative SHG",
            "bid_unit_price": 1650.00,
            "total_bid_amount": 4125000.00,
            "proposed_delivery_days": 45,
            "technical_proposal": "Handcrafted by 85 certified master weavers with authentic GI QR-passports and Silk Mark labels.",
            "is_msme_registered": True,
            "msme_udyam_number": "UDYAM-TS-08-0029182",
            "is_gi_certified": True,
            "gi_certificate_number": "GI-AP-TS-0018-WEAVE",
            "shg_member_count": 85,
            "technical_score": 96.00,
            "financial_score": 95.00,
            "total_evaluation_score": 95.50,
            "evaluation_notes": "Meets 100% GI criteria, MSME preference valid, highly competitive unit price.",
            "status": "submitted",
            "created_at": "2026-08-22T12:00:00Z",
            "updated_at": "2026-08-22T12:00:00Z"
        },
        {
            "id": bid2_id,
            "tender_id": t1_id,
            "artisan_id": "artisan_sri_laxmi",
            "artisan_business_name": "Sri Laxmi Handlooms",
            "bid_unit_price": 1750.00,
            "total_bid_amount": 4375000.00,
            "proposed_delivery_days": 50,
            "technical_proposal": "Traditional natural dye double ikat silk stoles with commemorative gold foil gift packaging.",
            "is_msme_registered": True,
            "msme_udyam_number": "UDYAM-TS-08-0011234",
            "is_gi_certified": True,
            "gi_certificate_number": "GI-AP-TS-0022-SILK",
            "shg_member_count": 30,
            "technical_score": 91.00,
            "financial_score": 89.00,
            "total_evaluation_score": 90.00,
            "evaluation_notes": "Good sample quality, slightly higher price than L1.",
            "status": "submitted",
            "created_at": "2026-08-23T14:00:00Z",
            "updated_at": "2026-08-23T14:00:00Z"
        }
    ]

    # Seed Tender 2 (CSR Corporate Gifting)
    t2_id = "tender-csr-2026-002"
    _mock_tenders[t2_id] = {
        "id": t2_id,
        "tender_number": "KC-CSR-2026-BRASS-104",
        "buyer_id": csr_id,
        "buyer_name": "Tata Community Initiatives Trust (CSR)",
        "buyer_type": "csr",
        "title": "Corporate Diwali Green Hamper: 1,200 Bastar Dhokra Brass Planters",
        "description": "Eco-friendly handmade tribal brass cast planters directly from Bastar tribal artisans for executive gift kits.",
        "craft_category": "Metal Art",
        "target_quantity": 1200,
        "estimated_budget": 1800000.00,
        "delivery_deadline": "2026-10-15T18:00:00Z",
        "delivery_location": "Tata CSR Logistics Hub, Mumbai - 400001",
        "eligibility_criteria": {
            "msme_only": False,
            "gi_priority": True,
            "min_experience_years": 1,
            "cluster_state_preference": "Chhattisgarh",
            "shg_women_quota": True
        },
        "technical_specs": {
            "metal": "Lost Wax Bell Metal / Brass",
            "height_inches": 6.5,
            "gi_certified": True
        },
        "document_urls": ["https://kalacart.in/tenders/bastar_dhokra_csr.pdf"],
        "lifecycle_stage": "published",
        "bids_count": 1,
        "created_at": "2026-08-25T11:00:00Z",
        "updated_at": "2026-08-25T11:00:00Z"
    }

    # Seed Bid for Tender 2
    _mock_bids[t2_id] = [
        {
            "id": "bid-dhokra-01",
            "tender_id": t2_id,
            "artisan_id": "artisan_sukhram_bastar",
            "artisan_business_name": "Bastar Tribal Shilpkala Society",
            "bid_unit_price": 1400.00,
            "total_bid_amount": 1680000.00,
            "proposed_delivery_days": 35,
            "technical_proposal": "Authentic lost-wax casting by 45 tribal artisans from Kondagaon cluster.",
            "is_msme_registered": True,
            "msme_udyam_number": "UDYAM-CG-04-0003891",
            "is_gi_certified": True,
            "gi_certificate_number": "GI-CG-0012-DHOKRA",
            "shg_member_count": 45,
            "technical_score": 98.00,
            "financial_score": 97.00,
            "total_evaluation_score": 97.50,
            "evaluation_notes": "L1 qualifying bid, direct tribal craft producer.",
            "status": "submitted",
            "created_at": "2026-08-26T15:00:00Z",
            "updated_at": "2026-08-26T15:00:00Z"
        }
    ]


class GovernmentProcurementService:
    def __init__(self):
        _seed_sample_procurement_data()

    def register_or_update_buyer(self, user_id: str, data: GovernmentBuyerRegister) -> GovernmentBuyerProfile:
        now_iso = datetime.now(timezone.utc).isoformat()
        profile_data = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "organization_name": data.organization_name,
            "buyer_type": data.buyer_type,
            "department": data.department,
            "nodal_officer_name": data.nodal_officer_name,
            "nodal_officer_email": data.nodal_officer_email,
            "nodal_officer_phone": data.nodal_officer_phone,
            "pan_number": data.pan_number,
            "gstin": data.gstin,
            "gem_buyer_id": data.gem_buyer_id,
            "csr_registration_number": data.csr_registration_number,
            "verification_status": "verified",
            "allocated_annual_budget": data.allocated_annual_budget,
            "documents": [{"name": f"{data.organization_name}_Credentials.pdf", "url": "https://kalacart.in/docs/verified_credential.pdf"}],
            "created_at": now_iso,
            "updated_at": now_iso
        }
        _mock_buyers[user_id] = profile_data
        return GovernmentBuyerProfile(**profile_data)

    def get_buyer_profile(self, user_id: str) -> Optional[GovernmentBuyerProfile]:
        data = _mock_buyers.get(user_id)
        if not data:
            # Auto-provision a default demo profile if looking up demo buyer
            demo_profile = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "organization_name": "National Procurement & Heritage Directorate",
                "buyer_type": "government",
                "department": "Public Procurement Division",
                "nodal_officer_name": "Institutional Officer",
                "nodal_officer_email": f"{user_id}@kalacart-procure.gov.in",
                "nodal_officer_phone": "+91 11 2000 8888",
                "pan_number": "AAAGP1234N",
                "gstin": "07AAAGP1234N1Z2",
                "gem_buyer_id": f"GEM-BUY-{user_id[:8]}",
                "csr_registration_number": None,
                "verification_status": "verified",
                "allocated_annual_budget": 10000000.00,
                "documents": [],
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            _mock_buyers[user_id] = demo_profile
            return GovernmentBuyerProfile(**demo_profile)
        return GovernmentBuyerProfile(**data)

    def list_tenders(
        self,
        buyer_type: Optional[str] = None,
        craft_category: Optional[str] = None,
        lifecycle_stage: Optional[str] = None
    ) -> List[TenderDocumentResponse]:
        tenders = list(_mock_tenders.values())
        if buyer_type:
            tenders = [t for t in tenders if t.get("buyer_type") == buyer_type]
        if craft_category:
            tenders = [t for t in tenders if str(t.get("craft_category")).lower() == craft_category.lower()]
        if lifecycle_stage:
            tenders = [t for t in tenders if t.get("lifecycle_stage") == lifecycle_stage]
        
        # Sort newest first
        tenders = sorted(tenders, key=lambda x: x.get("created_at", ""), reverse=True)
        return [TenderDocumentResponse(**t) for t in tenders]

    def create_tender(self, buyer_id: str, payload: TenderDocumentCreate) -> TenderDocumentResponse:
        now_iso = datetime.now(timezone.utc).isoformat()
        buyer_profile = self.get_buyer_profile(buyer_id)
        tender_id = f"tender-{uuid.uuid4().hex[:8]}"
        tender_num = f"KC-{buyer_profile.buyer_type.upper()[:3]}-{datetime.now().year}-{uuid.uuid4().hex[:6].upper()}"

        tender_data = {
            "id": tender_id,
            "tender_number": tender_num,
            "buyer_id": buyer_id,
            "buyer_name": buyer_profile.organization_name,
            "buyer_type": buyer_profile.buyer_type,
            "title": payload.title,
            "description": payload.description,
            "craft_category": payload.craft_category,
            "target_quantity": payload.target_quantity,
            "estimated_budget": payload.estimated_budget,
            "delivery_deadline": payload.delivery_deadline,
            "delivery_location": payload.delivery_location,
            "eligibility_criteria": payload.eligibility_criteria.model_dump(),
            "technical_specs": payload.technical_specs or {},
            "document_urls": payload.document_urls or [],
            "lifecycle_stage": "published",
            "bids_count": 0,
            "created_at": now_iso,
            "updated_at": now_iso
        }
        _mock_tenders[tender_id] = tender_data
        _mock_bids[tender_id] = []
        return TenderDocumentResponse(**tender_data)

    def get_tender(self, tender_id: str) -> Optional[TenderDocumentResponse]:
        t = _mock_tenders.get(tender_id)
        if not t:
            return None
        return TenderDocumentResponse(**t)

    def submit_bid(self, tender_id: str, artisan_id: str, payload: TenderBidCreate) -> TenderBidResponse:
        tender = _mock_tenders.get(tender_id)
        if not tender:
            raise ValueError("Tender not found")

        now_iso = datetime.now(timezone.utc).isoformat()
        bid_id = f"bid-{uuid.uuid4().hex[:8]}"
        total_amount = round(payload.bid_unit_price * tender["target_quantity"], 2)

        # Automated scoring with MSME + GI preference
        tech_score = 85.0
        if payload.is_gi_certified:
            tech_score += 10.0  # +10 GI Tag priority
        if payload.is_msme_registered:
            tech_score += 5.0   # +5 MSME Udyam priority
        tech_score = min(tech_score, 100.0)

        # Financial score (L1 benchmark)
        estimated_unit_price = tender["estimated_budget"] / max(tender["target_quantity"], 1)
        price_ratio = payload.bid_unit_price / max(estimated_unit_price, 1.0)
        fin_score = max(50.0, min(100.0, 100.0 - (price_ratio - 0.8) * 50.0))
        total_score = round(0.5 * tech_score + 0.5 * fin_score, 2)

        bid_data = {
            "id": bid_id,
            "tender_id": tender_id,
            "artisan_id": artisan_id,
            "artisan_business_name": payload.artisan_business_name,
            "bid_unit_price": payload.bid_unit_price,
            "total_bid_amount": total_amount,
            "proposed_delivery_days": payload.proposed_delivery_days,
            "technical_proposal": payload.technical_proposal,
            "is_msme_registered": payload.is_msme_registered,
            "msme_udyam_number": payload.msme_udyam_number or "UDYAM-REG-VALID",
            "is_gi_certified": payload.is_gi_certified,
            "gi_certificate_number": payload.gi_certificate_number or "GI-CERT-VERIFIED",
            "shg_member_count": payload.shg_member_count,
            "technical_score": tech_score,
            "financial_score": fin_score,
            "total_evaluation_score": total_score,
            "evaluation_notes": f"Scored with MSME preference ({payload.is_msme_registered}) & GI Certified priority ({payload.is_gi_certified}).",
            "status": "submitted",
            "created_at": now_iso,
            "updated_at": now_iso
        }

        if tender_id not in _mock_bids:
            _mock_bids[tender_id] = []
        _mock_bids[tender_id].append(bid_data)
        tender["bids_count"] = len(_mock_bids[tender_id])
        return TenderBidResponse(**bid_data)

    def list_tender_bids(self, tender_id: str) -> List[TenderBidResponse]:
        bids = _mock_bids.get(tender_id, [])
        # Rank by total evaluation score descending
        sorted_bids = sorted(bids, key=lambda x: x.get("total_evaluation_score", 0), reverse=True)
        return [TenderBidResponse(**b) for b in sorted_bids]

    def evaluate_and_award_tender(
        self,
        tender_id: str,
        buyer_id: str,
        req: TenderEvaluationRequest
    ) -> ContractAwardResponse:
        tender = _mock_tenders.get(tender_id)
        if not tender:
            raise ValueError("Tender not found")

        bids = _mock_bids.get(tender_id, [])
        if not bids:
            raise ValueError("No bids submitted for this tender")

        winning_bid = None
        if req.winning_bid_id:
            winning_bid = next((b for b in bids if b["id"] == req.winning_bid_id), None)
        if not winning_bid:
            # Pick highest score
            winning_bid = sorted(bids, key=lambda x: x.get("total_evaluation_score", 0), reverse=True)[0]

        now_iso = datetime.now(timezone.utc).isoformat()
        contract_id = f"contract-{uuid.uuid4().hex[:8]}"
        contract_num = f"KC-CNTR-{datetime.now().year}-{uuid.uuid4().hex[:6].upper()}"

        contract_terms = {
            "tender_number": tender["tender_number"],
            "procurement_scope": tender["title"],
            "delivery_location": tender["delivery_location"],
            "quality_standard": "GI Tag & Handloom Board Certified Authentic Craft Quality",
            "liquidated_damages": "0.5% per week of delay up to a maximum of 5% contract value",
            "dispute_resolution": "Arbitration under the Indian Arbitration and Conciliation Act, 1996",
            "escrow_protection": "100% funds locked in KalaCart Institutional Escrow Account",
            "custom_terms": req.custom_terms or {}
        }

        award_data = {
            "id": contract_id,
            "contract_number": contract_num,
            "tender_id": tender_id,
            "buyer_id": buyer_id,
            "buyer_name": tender["buyer_name"],
            "artisan_id": winning_bid["artisan_id"],
            "artisan_business_name": winning_bid["artisan_business_name"],
            "artisan_is_msme": winning_bid["is_msme_registered"],
            "artisan_is_gi_certified": winning_bid["is_gi_certified"],
            "awarded_quantity": tender["target_quantity"],
            "awarded_unit_price": winning_bid["bid_unit_price"],
            "total_contract_value": winning_bid["total_bid_amount"],
            "evaluation_summary": {
                "technical_score": winning_bid["technical_score"],
                "financial_score": winning_bid["financial_score"],
                "total_evaluation_score": winning_bid["total_evaluation_score"],
                "gi_bonus_applied": winning_bid["is_gi_certified"],
                "msme_preference_applied": winning_bid["is_msme_registered"]
            },
            "digital_contract_terms": contract_terms,
            "contract_pdf_url": f"https://kalacart.in/contracts/{contract_num}.pdf",
            "buyer_signed": True,
            "buyer_signed_at": now_iso,
            "artisan_signed": True,
            "artisan_signed_at": now_iso,
            "status": "active",
            "created_at": now_iso,
            "updated_at": now_iso
        }

        # Update tender lifecycle
        tender["lifecycle_stage"] = "awarded"
        winning_bid["status"] = "awarded"
        _mock_contracts[contract_id] = award_data

        # Generate 4 Escrow Milestones
        total_val = winning_bid["total_bid_amount"]
        milestones = [
            {
                "id": f"ms-{contract_id}-1",
                "contract_award_id": contract_id,
                "milestone_index": 1,
                "title": "Milestone 1: Mobilization & Raw Material Advance (20%)",
                "percentage": 20.0,
                "amount": round(total_val * 0.20, 2),
                "deliverable_description": "Initial advance to procure authentic silk yarns, organic dyes, raw brass and clay.",
                "due_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
                "verification_doc_urls": ["https://kalacart.in/docs/material_purchase_invoice.pdf"],
                "status": "paid",
                "approved_by_buyer": True,
                "approved_at": now_iso,
                "escrow_transaction_id": f"ESCROW-TXN-ADV-{uuid.uuid4().hex[:6].upper()}",
                "paid_at": now_iso,
                "created_at": now_iso,
                "updated_at": now_iso
            },
            {
                "id": f"ms-{contract_id}-2",
                "contract_award_id": contract_id,
                "milestone_index": 2,
                "title": "Milestone 2: Batch Production & Mid-Term Quality Audit (40%)",
                "percentage": 40.0,
                "amount": round(total_val * 0.40, 2),
                "deliverable_description": "50% craft batch produced and GI craftsmanship inspection verified.",
                "due_date": (datetime.now() + timedelta(days=25)).strftime("%Y-%m-%d"),
                "verification_doc_urls": [],
                "status": "in_progress",
                "approved_by_buyer": False,
                "approved_at": None,
                "escrow_transaction_id": None,
                "paid_at": None,
                "created_at": now_iso,
                "updated_at": now_iso
            },
            {
                "id": f"ms-{contract_id}-3",
                "contract_award_id": contract_id,
                "milestone_index": 3,
                "title": "Milestone 3: Consignee Delivery & Acceptance Inspection (30%)",
                "percentage": 30.0,
                "amount": round(total_val * 0.30, 2),
                "deliverable_description": "Complete consignment delivered to warehouse and verified against RFP specs.",
                "due_date": (datetime.now() + timedelta(days=45)).strftime("%Y-%m-%d"),
                "verification_doc_urls": [],
                "status": "pending",
                "approved_by_buyer": False,
                "approved_at": None,
                "escrow_transaction_id": None,
                "paid_at": None,
                "created_at": now_iso,
                "updated_at": now_iso
            },
            {
                "id": f"ms-{contract_id}-4",
                "contract_award_id": contract_id,
                "milestone_index": 4,
                "title": "Milestone 4: Final Quality Warranty & Retention Release (10%)",
                "percentage": 10.0,
                "amount": round(total_val * 0.10, 2),
                "deliverable_description": "Retention warranty release 30 days post delivery completion.",
                "due_date": (datetime.now() + timedelta(days=75)).strftime("%Y-%m-%d"),
                "verification_doc_urls": [],
                "status": "pending",
                "approved_by_buyer": False,
                "approved_at": None,
                "escrow_transaction_id": None,
                "paid_at": None,
                "created_at": now_iso,
                "updated_at": now_iso
            }
        ]
        _mock_milestones[contract_id] = milestones
        return ContractAwardResponse(**award_data)

    def list_contracts(self, user_id: str) -> List[ContractAwardResponse]:
        contracts = list(_mock_contracts.values())
        user_contracts = [c for c in contracts if c["buyer_id"] == user_id or c["artisan_id"] == user_id]
        if not user_contracts:
            user_contracts = contracts  # fallback for overview
        return [ContractAwardResponse(**c) for c in user_contracts]

    def get_contract(self, contract_id: str) -> Optional[ContractAwardResponse]:
        c = _mock_contracts.get(contract_id)
        if not c:
            return None
        return ContractAwardResponse(**c)

    def list_milestones(self, contract_award_id: str) -> List[MilestoneResponse]:
        ms = _mock_milestones.get(contract_award_id, [])
        return [MilestoneResponse(**m) for m in ms]

    def action_milestone(
        self,
        contract_award_id: str,
        milestone_id: str,
        payload: MilestoneActionRequest
    ) -> MilestoneResponse:
        milestones = _mock_milestones.get(contract_award_id, [])
        target = next((m for m in milestones if m["id"] == milestone_id), None)
        if not target:
            raise ValueError("Milestone not found")

        now_iso = datetime.now(timezone.utc).isoformat()
        if payload.action == "submit_proof":
            target["status"] = "submitted_for_approval"
            if payload.verification_doc_urls:
                target["verification_doc_urls"] = payload.verification_doc_urls
        elif payload.action == "approve":
            target["status"] = "approved"
            target["approved_by_buyer"] = True
            target["approved_at"] = now_iso
        elif payload.action == "release_payment":
            target["status"] = "paid"
            target["approved_by_buyer"] = True
            target["approved_at"] = target.get("approved_at") or now_iso
            target["escrow_transaction_id"] = f"ESCROW-TXN-MS-{uuid.uuid4().hex[:6].upper()}"
            target["paid_at"] = now_iso
        elif payload.action == "dispute":
            target["status"] = "disputed"

        target["updated_at"] = now_iso
        return MilestoneResponse(**target)


gov_procurement_service = GovernmentProcurementService()
