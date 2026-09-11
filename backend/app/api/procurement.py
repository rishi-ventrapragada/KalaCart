from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional, Dict, Any
from app.core.security import get_current_user
from app.models.procurement import (
    ProcurementCreate,
    ProcurementResponse,
    ProcurementBidCreate,
    ProcurementBidResponse,
    BidEvaluationRequest,
    AwardTenderRequest,
    ProcurementContractResponse,
    TenderStatus,
    BuyerOrganizationType
)
from app.services.procurement_service import ProcurementService

router = APIRouter(prefix="/api/v1/procurement", tags=["National B2B Procurement Hub"])

def _get_uid(current_user: Any) -> str:
    if isinstance(current_user, dict):
        return current_user.get("uid") or current_user.get("id", "user-anon")
    return getattr(current_user, "id", getattr(current_user, "uid", "user-anon"))

@router.post("/tenders", response_model=ProcurementResponse, status_code=status.HTTP_201_CREATED)
def create_procurement_tender(
    payload: ProcurementCreate,
    current_user: Any = Depends(get_current_user)
):
    """
    Large Institutional Buyers (Hotels, Exporters, Government, Corporate) publish a bulk procurement tender.
    """
    return ProcurementService.create_procurement(
        buyer_id=_get_uid(current_user),
        payload=payload
    )

@router.get("/tenders", response_model=List[ProcurementResponse])
def list_procurement_tenders(
    status: Optional[TenderStatus] = Query(None),
    buyer_type: Optional[BuyerOrganizationType] = Query(None),
    category_id: Optional[str] = Query(None)
):
    """
    List published tenders open for bidding.
    """
    return ProcurementService.list_procurements(
        status=status,
        buyer_type=buyer_type,
        category_id=category_id
    )

@router.get("/tenders/{tender_id}", response_model=ProcurementResponse)
def get_procurement_tender(tender_id: str):
    """
    Get detailed specifications of a tender.
    """
    tender = ProcurementService.get_procurement(tender_id)
    if not tender:
        raise HTTPException(status_code=404, detail="Procurement tender not found")
    return tender

@router.post("/tenders/{tender_id}/bids", response_model=ProcurementBidResponse, status_code=status.HTTP_201_CREATED)
def submit_tender_bid(
    tender_id: str,
    payload: ProcurementBidCreate,
    current_user: Any = Depends(get_current_user)
):
    """
    Artisans / Craft Producer Companies submit a competitive tender bid with certifications & quotes.
    """
    try:
        return ProcurementService.submit_bid(
            procurement_id=tender_id,
            artisan_id=_get_uid(current_user),
            payload=payload
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/tenders/{tender_id}/bids", response_model=List[ProcurementBidResponse])
def list_tender_bids(
    tender_id: str,
    current_user: Any = Depends(get_current_user)
):
    """
    List all bids submitted for a specific tender.
    """
    tender = ProcurementService.get_procurement(tender_id)
    if not tender:
        raise HTTPException(status_code=404, detail="Procurement tender not found")
    return ProcurementService.list_bids_for_procurement(tender_id)

@router.post("/bids/{bid_id}/evaluate", response_model=ProcurementBidResponse)
def evaluate_bid(
    bid_id: str,
    payload: BidEvaluationRequest,
    current_user: Any = Depends(get_current_user)
):
    """
    Buyer evaluates, scores (0-100), and shortlists/rejects an artisan's bid.
    """
    try:
        return ProcurementService.evaluate_bid(
            bid_id=bid_id,
            eval_data=payload
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/tenders/{tender_id}/award", response_model=ProcurementContractResponse)
def award_tender(
    tender_id: str,
    payload: AwardTenderRequest,
    current_user: Any = Depends(get_current_user)
):
    """
    Buyer awards contract to the winning artisan bid, generating legal contract & milestone escrow schedules.
    """
    try:
        return ProcurementService.award_tender(
            procurement_id=tender_id,
            buyer_id=_get_uid(current_user),
            payload=payload
        )
    except PermissionError as pe:
        raise HTTPException(status_code=403, detail=str(pe))
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))

@router.get("/contracts", response_model=List[ProcurementContractResponse])
def list_procurement_contracts(
    current_user: Any = Depends(get_current_user)
):
    """
    View all active procurement contracts for the current buyer or artisan.
    """
    return ProcurementService.list_contracts(user_id=_get_uid(current_user))
