"""
Smart Contracts & Institutional Escrow API Router (Phase 9)
Provides automated enterprise & government procurement lifecycle management,
milestone-based escrow locks, multi-party inspection approvals, and penalty calculations.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

from app.core.smart_contracts import (
    smart_contracts_escrow,
    SmartContractAgreement,
    ContractMilestone,
)

router = APIRouter(prefix="/api/v1/contracts", tags=["Smart Contracts & Institutional Escrow"])


class MilestoneCreateRequest(BaseModel):
    title: str
    description: str
    release_percentage: float = 50.0
    due_date: Optional[str] = None


class CreateContractRequest(BaseModel):
    title: str
    buyer_org_name: str
    buyer_org_type: str = "government"
    buyer_signatory_name: str
    buyer_signatory_email: str
    artisan_id: str
    artisan_signatory_name: str
    total_contract_value: float
    penalty_per_day_late_pct: float = 0.5
    max_penalty_cap_pct: float = 10.0
    milestones: List[MilestoneCreateRequest]


class SignContractRequest(BaseModel):
    contract_id: str
    signer_role: str = "buyer"  # buyer, artisan
    signer_name: str


class FundEscrowRequest(BaseModel):
    contract_id: str
    amount: float


class SubmitMilestoneDeliveryRequest(BaseModel):
    contract_id: str
    milestone_id: str
    delivery_notes: str = ""


class ApproveMilestoneRequest(BaseModel):
    contract_id: str
    milestone_id: str
    approver_role: str = "quality_inspector"
    approver_name: str
    comments: str = "Approved"


@router.get("/summary")
async def get_contracts_summary():
    """Retrieve an aggregate summary of institutional contracts, escrow locked funds, and release stats."""
    return smart_contracts_escrow.get_engine_summary()


@router.get("/list")
async def list_contracts():
    """List all active and completed smart contracts."""
    return {
        "count": len(smart_contracts_escrow.contracts),
        "contracts": [c.to_dict() for c in smart_contracts_escrow.contracts.values()],
    }


@router.get("/{contract_id}")
async def get_contract_details(contract_id: str):
    """Retrieve full details of a smart contract including milestones, signers, escrow locks, and approvals."""
    contract = smart_contracts_escrow.contracts.get(contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail=f"Contract {contract_id} not found.")
    return contract.to_dict()


@router.post("/create")
async def create_contract(req: CreateContractRequest):
    """Create a new smart procurement agreement in DRAFT status with defined milestones."""
    milestones_data = [m.model_dump() for m in req.milestones]
    contract = smart_contracts_escrow.create_contract(
        title=req.title,
        buyer_org_name=req.buyer_org_name,
        buyer_org_type=req.buyer_org_type,
        buyer_signatory_name=req.buyer_signatory_name,
        buyer_signatory_email=req.buyer_signatory_email,
        artisan_id=req.artisan_id,
        artisan_signatory_name=req.artisan_signatory_name,
        total_contract_value=req.total_contract_value,
        milestones=milestones_data,
        penalty_per_day_late_pct=req.penalty_per_day_late_pct,
        max_penalty_cap_pct=req.max_penalty_cap_pct,
    )
    return {
        "status": "success",
        "message": f"Contract {contract.contract_code} created.",
        "contract": contract.to_dict(),
    }


@router.post("/sign")
async def sign_contract(req: SignContractRequest):
    """Apply a verified cryptographic digital signature to a contract."""
    try:
        contract = smart_contracts_escrow.sign_contract(
            contract_id=req.contract_id,
            signer_role=req.signer_role,
            signer_name=req.signer_name,
        )
        return {
            "status": "success",
            "contract_status": contract.contract_status,
            "contract": contract.to_dict(),
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/escrow/fund")
async def fund_escrow(req: FundEscrowRequest):
    """Deposit institutional escrow funds into the contract's secure lock."""
    try:
        contract = smart_contracts_escrow.fund_escrow(
            contract_id=req.contract_id,
            amount=req.amount,
        )
        return {
            "status": "success",
            "contract_status": contract.contract_status,
            "escrow_funded_amount": contract.escrow_funded_amount,
            "contract": contract.to_dict(),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/milestones/deliver")
async def submit_milestone_delivery(req: SubmitMilestoneDeliveryRequest):
    """Submit craft deliverables against a contract milestone for quality inspection."""
    try:
        ms = smart_contracts_escrow.submit_milestone_delivery(
            contract_id=req.contract_id,
            milestone_id=req.milestone_id,
        )
        return {
            "status": "success",
            "milestone": ms.to_dict(),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/milestones/approve")
async def approve_and_release_milestone(req: ApproveMilestoneRequest):
    """Approve a milestone, record inspection scores, calculate penalties if late, and release partial escrow funds."""
    try:
        result = smart_contracts_escrow.approve_milestone_and_release_escrow(
            contract_id=req.contract_id,
            milestone_id=req.milestone_id,
            approver_role=req.approver_role,
            approver_name=req.approver_name,
            comments=req.comments,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
