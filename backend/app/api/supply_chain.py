from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional, Any
from app.core.security import get_current_user
from app.models.supply_chain import (
    MaterialResponse,
    MaterialCategory,
    SupplierResponse,
    AIRecommendSuppliersRequest,
    AIRecommendSuppliersResponse,
    PurchaseRequestCreate,
    PurchaseRequestResponse,
    SupplierQuoteCreate,
    SupplierQuoteResponse,
    GroupPurchasePoolResponse
)
from app.services.supply_chain_service import SupplyChainService
from app.ai.supply_chain_recommender import SupplyChainAIRecommender

router = APIRouter(prefix="/api/v1/supply-chain", tags=["AI Supply Chain Network"])

def _get_uid(current_user: Any) -> str:
    if isinstance(current_user, dict):
        return current_user.get("uid") or current_user.get("id", "artisan-user")
    return getattr(current_user, "id", getattr(current_user, "uid", "artisan-user"))

@router.get("/materials", response_model=List[MaterialResponse])
def list_raw_materials(category: Optional[MaterialCategory] = Query(None)):
    """
    Browse certified raw materials (Bamboo, Clay, Brass, Fabric, Leather, Dyes).
    """
    return SupplyChainService.list_materials(category=category)

@router.post("/recommend-suppliers", response_model=AIRecommendSuppliersResponse)
def recommend_raw_material_suppliers(payload: AIRecommendSuppliersRequest):
    """
    AI Multi-criteria ranking (Price, Proximity, Quality Purity, Delivery SLA, Reviews).
    """
    return SupplyChainAIRecommender.recommend(req=payload)

@router.post("/purchase-requests", response_model=PurchaseRequestResponse, status_code=status.HTTP_201_CREATED)
def create_material_purchase_request(
    payload: PurchaseRequestCreate,
    current_user: Any = Depends(get_current_user)
):
    """
    Artisans create bulk or individual raw material procurement requests.
    """
    return SupplyChainService.create_purchase_request(
        artisan_id=_get_uid(current_user),
        payload=payload
    )

@router.get("/purchase-requests", response_model=List[PurchaseRequestResponse])
def list_purchase_requests(current_user: Any = Depends(get_current_user)):
    """
    List raw material purchase requests for current artisan.
    """
    return SupplyChainService.list_purchase_requests(artisan_id=_get_uid(current_user))

@router.post("/quotes", response_model=SupplierQuoteResponse, status_code=status.HTTP_201_CREATED)
def submit_supplier_quote(
    payload: SupplierQuoteCreate,
    current_user: Any = Depends(get_current_user)
):
    """
    Certified material suppliers submit itemized quotes.
    """
    try:
        return SupplyChainService.submit_quote(
            supplier_id=_get_uid(current_user),
            supplier_name="Verified Direct Mill Supplier",
            payload=payload
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/quotes/{quote_id}/accept", response_model=SupplierQuoteResponse)
def accept_supplier_quote(
    quote_id: str,
    current_user: Any = Depends(get_current_user)
):
    """
    Artisan accepts quote and confirms material order inside KalaCart.
    """
    try:
        return SupplyChainService.accept_quote(quote_id=quote_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/group-pools", response_model=List[GroupPurchasePoolResponse])
def list_group_purchase_pools():
    """
    List active cluster group-buying pools unlocking bulk volume discounts (20-35%).
    """
    return SupplyChainService.list_group_pools()
