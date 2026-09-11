from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.security import get_current_user
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
    DigitalContractSignRequest
)
from app.services.gov_procurement_service import gov_procurement_service

router = APIRouter(prefix="/api/v1/gov", tags=["Government & Institutional Procurement Hub"])


@router.post("/buyers/register", response_model=GovernmentBuyerProfile, status_code=status.HTTP_201_CREATED)
def register_buyer(
    payload: GovernmentBuyerRegister,
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user.get("uid") or current_user.get("user_id") or "gov_buyer_demo"
    return gov_procurement_service.register_or_update_buyer(user_id, payload)


@router.get("/buyers/me", response_model=GovernmentBuyerProfile)
def get_current_buyer_profile(
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user.get("uid") or current_user.get("user_id") or "gov_buyer_demo"
    profile = gov_procurement_service.get_buyer_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Buyer profile not found")
    return profile


@router.get("/tenders", response_model=List[TenderDocumentResponse])
def list_tenders(
    buyer_type: Optional[str] = Query(None, description="government, ngo, csr, school, museum, tourism, hotel"),
    craft_category: Optional[str] = Query(None, description="Textile, Pottery, Metal Art, etc."),
    lifecycle_stage: Optional[str] = Query(None, description="published, awarded, etc.")
):
    return gov_procurement_service.list_tenders(buyer_type, craft_category, lifecycle_stage)


@router.post("/tenders", response_model=TenderDocumentResponse, status_code=status.HTTP_201_CREATED)
def create_tender(
    payload: TenderDocumentCreate,
    current_user: dict = Depends(get_current_user)
):
    buyer_id = current_user.get("uid") or current_user.get("user_id") or "gov_buyer_demo"
    return gov_procurement_service.create_tender(buyer_id, payload)


@router.get("/tenders/{tender_id}", response_model=TenderDocumentResponse)
def get_tender_detail(tender_id: str):
    tender = gov_procurement_service.get_tender(tender_id)
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")
    return tender


@router.post("/tenders/{tender_id}/bids", response_model=TenderBidResponse, status_code=status.HTTP_201_CREATED)
def submit_bid(
    tender_id: str,
    payload: TenderBidCreate,
    current_user: dict = Depends(get_current_user)
):
    artisan_id = current_user.get("uid") or current_user.get("user_id") or "artisan_demo"
    try:
        return gov_procurement_service.submit_bid(tender_id, artisan_id, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/tenders/{tender_id}/bids", response_model=List[TenderBidResponse])
def list_bids(tender_id: str):
    return gov_procurement_service.list_tender_bids(tender_id)


@router.post("/tenders/{tender_id}/evaluate-and-award", response_model=ContractAwardResponse)
def evaluate_and_award_tender(
    tender_id: str,
    payload: TenderEvaluationRequest,
    current_user: dict = Depends(get_current_user)
):
    buyer_id = current_user.get("uid") or current_user.get("user_id") or "gov_buyer_demo"
    try:
        return gov_procurement_service.evaluate_and_award_tender(tender_id, buyer_id, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/contracts", response_model=List[ContractAwardResponse])
def list_contracts(
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user.get("uid") or current_user.get("user_id") or "gov_buyer_demo"
    return gov_procurement_service.list_contracts(user_id)


@router.get("/contracts/{contract_id}", response_model=ContractAwardResponse)
def get_contract_detail(contract_id: str):
    contract = gov_procurement_service.get_contract(contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    return contract


@router.get("/contracts/{contract_id}/milestones", response_model=List[MilestoneResponse])
def list_milestones(contract_id: str):
    return gov_procurement_service.list_milestones(contract_id)


@router.post("/contracts/{contract_id}/milestones/{milestone_id}/action", response_model=MilestoneResponse)
def action_milestone(
    contract_id: str,
    milestone_id: str,
    payload: MilestoneActionRequest,
    current_user: dict = Depends(get_current_user)
):
    try:
        return gov_procurement_service.action_milestone(contract_id, milestone_id, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
