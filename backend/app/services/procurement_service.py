from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid
from app.models.procurement import (
    ProcurementCreate,
    ProcurementResponse,
    ProcurementBidCreate,
    ProcurementBidResponse,
    BidEvaluationRequest,
    AwardTenderRequest,
    ProcurementContractResponse,
    Milestone,
    TenderStatus,
    BidStatus,
    ContractStatus,
    BuyerOrganizationType
)

# In-Memory Fallback Stores for deterministic mock/test and decoupled isolation
_PROCUREMENTS: Dict[str, Dict[str, Any]] = {}
_BIDS: Dict[str, Dict[str, Any]] = {}
_CONTRACTS: Dict[str, Dict[str, Any]] = {}

class ProcurementService:
    @staticmethod
    def create_procurement(buyer_id: str, payload: ProcurementCreate) -> ProcurementResponse:
        procurement_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        record = {
            "id": procurement_id,
            "buyer_id": buyer_id,
            "buyer_organization_name": payload.buyer_organization_name,
            "buyer_type": payload.buyer_type,
            "title": payload.title,
            "description": payload.description,
            "category_id": payload.category_id,
            "target_quantity": payload.target_quantity,
            "target_unit_price": payload.target_unit_price,
            "max_budget": payload.max_budget,
            "delivery_deadline": payload.delivery_deadline.isoformat(),
            "delivery_location": payload.delivery_location,
            "technical_specs": payload.technical_specs or {},
            "attachment_urls": payload.attachment_urls or [],
            "status": TenderStatus.OPEN,
            "bids_count": 0,
            "created_at": now,
            "updated_at": now
        }
        _PROCUREMENTS[procurement_id] = record
        return ProcurementResponse(**record)

    @staticmethod
    def list_procurements(
        status: Optional[TenderStatus] = None,
        buyer_type: Optional[BuyerOrganizationType] = None,
        category_id: Optional[str] = None
    ) -> List[ProcurementResponse]:
        results = []
        for p in _PROCUREMENTS.values():
            if status and p["status"] != status:
                continue
            if buyer_type and p["buyer_type"] != buyer_type:
                continue
            if category_id and p["category_id"] != category_id:
                continue
            results.append(ProcurementResponse(**p))
        return results

    @staticmethod
    def get_procurement(procurement_id: str) -> Optional[ProcurementResponse]:
        record = _PROCUREMENTS.get(procurement_id)
        if not record:
            return None
        return ProcurementResponse(**record)

    @staticmethod
    def submit_bid(
        procurement_id: str,
        artisan_id: str,
        payload: ProcurementBidCreate
    ) -> ProcurementBidResponse:
        procurement = _PROCUREMENTS.get(procurement_id)
        if not procurement:
            raise ValueError(f"Procurement {procurement_id} not found")
        if procurement["status"] not in [TenderStatus.OPEN, TenderStatus.UNDER_EVALUATION]:
            raise ValueError("Tender is no longer accepting bids")

        bid_id = str(uuid.uuid4())
        total_bid_amount = round(payload.bid_unit_price * procurement["target_quantity"], 2)
        now = datetime.utcnow().isoformat()

        # Check existing bid by artisan
        for bid in _BIDS.values():
            if bid["procurement_id"] == procurement_id and bid["artisan_id"] == artisan_id:
                raise ValueError("Artisan has already submitted a bid for this tender")

        bid_record = {
            "id": bid_id,
            "procurement_id": procurement_id,
            "artisan_id": artisan_id,
            "artisan_business_name": payload.artisan_business_name,
            "bid_unit_price": payload.bid_unit_price,
            "total_bid_amount": total_bid_amount,
            "proposed_delivery_days": payload.proposed_delivery_days,
            "technical_proposal": payload.technical_proposal,
            "certificate_urls": payload.certificate_urls or [],
            "sample_image_urls": payload.sample_image_urls or [],
            "evaluation_score": None,
            "evaluation_notes": None,
            "status": BidStatus.SUBMITTED,
            "created_at": now
        }
        _BIDS[bid_id] = bid_record
        procurement["bids_count"] += 1
        return ProcurementBidResponse(**bid_record)

    @staticmethod
    def list_bids_for_procurement(procurement_id: str) -> List[ProcurementBidResponse]:
        return [
            ProcurementBidResponse(**b)
            for b in _BIDS.values()
            if b["procurement_id"] == procurement_id
        ]

    @staticmethod
    def evaluate_bid(
        bid_id: str,
        eval_data: BidEvaluationRequest
    ) -> ProcurementBidResponse:
        bid = _BIDS.get(bid_id)
        if not bid:
            raise ValueError(f"Bid {bid_id} not found")
        
        bid["evaluation_score"] = eval_data.evaluation_score
        bid["evaluation_notes"] = eval_data.evaluation_notes
        if eval_data.status:
            bid["status"] = eval_data.status
        
        # update tender status to under evaluation if open
        procurement = _PROCUREMENTS.get(bid["procurement_id"])
        if procurement and procurement["status"] == TenderStatus.OPEN:
            procurement["status"] = TenderStatus.UNDER_EVALUATION

        return ProcurementBidResponse(**bid)

    @staticmethod
    def award_tender(
        procurement_id: str,
        buyer_id: str,
        payload: AwardTenderRequest
    ) -> ProcurementContractResponse:
        procurement = _PROCUREMENTS.get(procurement_id)
        if not procurement:
            raise ValueError("Procurement tender not found")
        if procurement["buyer_id"] != buyer_id:
            raise PermissionError("Only the owning buyer can award the tender")
        
        bid = _BIDS.get(payload.bid_id)
        if not bid or bid["procurement_id"] != procurement_id:
            raise ValueError("Invalid winning bid specified")

        # Mark bid as awarded, reject other submitted bids
        for b in _BIDS.values():
            if b["procurement_id"] == procurement_id:
                if b["id"] == bid["id"]:
                    b["status"] = BidStatus.AWARDED
                elif b["status"] != BidStatus.REJECTED:
                    b["status"] = BidStatus.REJECTED

        procurement["status"] = TenderStatus.AWARDED
        now = datetime.utcnow()
        contract_id = str(uuid.uuid4())
        contract_number = f"KC-B2B-{now.strftime('%Y%m')}-{uuid.uuid4().hex[:6].upper()}"
        total_val = bid["total_bid_amount"]

        # Default standard 3-stage milestone escrow
        milestones = [
            Milestone(
                milestone_name="Advance Material Sourcing (30%)",
                percentage=30.0,
                amount=round(total_val * 0.30, 2),
                due_date=(now + timedelta(days=5)).strftime("%Y-%m-%d"),
                status="pending"
            ),
            Milestone(
                milestone_name="Batch Mid-Inspection (40%)",
                percentage=40.0,
                amount=round(total_val * 0.40, 2),
                due_date=(now + timedelta(days=15)).strftime("%Y-%m-%d"),
                status="pending"
            ),
            Milestone(
                milestone_name="Final Delivery & Quality Approval (30%)",
                percentage=30.0,
                amount=round(total_val * 0.30, 2),
                due_date=(now + timedelta(days=bid["proposed_delivery_days"])).strftime("%Y-%m-%d"),
                status="pending"
            )
        ]

        contract_record = {
            "id": contract_id,
            "procurement_id": procurement_id,
            "bid_id": bid["id"],
            "buyer_id": buyer_id,
            "artisan_id": bid["artisan_id"],
            "contract_number": contract_number,
            "total_contract_value": total_val,
            "quantity_awarded": procurement["target_quantity"],
            "unit_price": bid["bid_unit_price"],
            "contract_terms": payload.contract_terms or {
                "jurisdiction": "National Handicrafts Development Board / India",
                "inspection_standard": "GI Tag & Handloom Board Certified Grade A",
                "penalty_clause": "0.5% per day delay up to max 5%"
            },
            "milestones": [m.model_dump() for m in milestones],
            "status": ContractStatus.ACTIVE,
            "signed_at": now.isoformat(),
            "created_at": now.isoformat()
        }
        _CONTRACTS[contract_id] = contract_record
        return ProcurementContractResponse(
            **contract_record
        )

    @staticmethod
    def list_contracts(user_id: str) -> List[ProcurementContractResponse]:
        results = []
        for c in _CONTRACTS.values():
            if c["buyer_id"] == user_id or c["artisan_id"] == user_id:
                results.append(ProcurementContractResponse(**c))
        return results
