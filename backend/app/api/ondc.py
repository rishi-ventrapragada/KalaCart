from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional, Any
from app.core.security import get_current_user
from app.models.ondc import (
    ONDCPublishProductRequest,
    ONDCProductResponse,
    ONDCInventorySyncRequest,
    ONDCInventorySyncResponse,
    ONDCIncomingOrderRequest,
    ONDCOrderResponse,
    ONDCCancellationRequest,
    ONDCReturnRequest,
    ONDCSyncLogResponse
)
from app.services.ondc.ondc_service import ONDCService

router = APIRouter(prefix="/api/v1/ondc", tags=["ONDC Integration Layer"])
_ondc_service = ONDCService()

@router.post("/products/{product_id}/publish", response_model=ONDCProductResponse, status_code=status.HTTP_201_CREATED)
def publish_product_to_ondc(
    product_id: str,
    payload: ONDCPublishProductRequest,
    current_user: Any = Depends(get_current_user)
):
    """
    Publish a KalaCart product to the ONDC Open Network with Beckn v1.2 RET12 specifications.
    Zero duplication: maps directly to existing KalaCart product.
    """
    payload.product_id = product_id
    return _ondc_service.publish_product(payload)

@router.get("/products", response_model=List[ONDCProductResponse])
def list_ondc_published_products():
    """
    List all KalaCart products active on the ONDC Network.
    """
    return _ondc_service.list_products()

@router.post("/inventory/sync", response_model=ONDCInventorySyncResponse)
def sync_inventory_with_ondc(
    payload: ONDCInventorySyncRequest,
    current_user: Any = Depends(get_current_user)
):
    """
    Synchronize stock levels between KalaCart and ONDC Network.
    """
    try:
        return _ondc_service.sync_inventory(payload)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/orders/incoming", response_model=ONDCOrderResponse, status_code=status.HTTP_201_CREATED)
def handle_incoming_network_order(payload: ONDCIncomingOrderRequest):
    """
    Ingest Beckn Network order from buyer apps (Paytm, Mystore, Magicpin).
    """
    return _ondc_service.process_incoming_order(payload)

@router.get("/orders", response_model=List[ONDCOrderResponse])
def list_ondc_orders(current_user: Any = Depends(get_current_user)):
    """
    List all ONDC network orders.
    """
    return _ondc_service.list_orders()

@router.post("/orders/{order_id}/cancel", response_model=ONDCOrderResponse)
def cancel_ondc_order(
    order_id: str,
    payload: ONDCCancellationRequest,
    current_user: Any = Depends(get_current_user)
):
    """
    Execute Beckn cancellation flow with standardized reason codes.
    """
    try:
        return _ondc_service.cancel_order(network_order_id=order_id, req=payload)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/orders/{order_id}/return", response_model=ONDCOrderResponse)
def return_ondc_order(
    order_id: str,
    payload: ONDCReturnRequest,
    current_user: Any = Depends(get_current_user)
):
    """
    Execute Beckn return authorization flow.
    """
    try:
        return _ondc_service.return_order(network_order_id=order_id, req=payload)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/sync-logs", response_model=List[ONDCSyncLogResponse])
def list_ondc_sync_logs(current_user: Any = Depends(get_current_user)):
    """
    Audit trail of all Beckn transactions and sync logs.
    """
    return _ondc_service.list_sync_logs()
