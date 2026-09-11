"""
Enterprise Integration Hub API (Phase 9).
Provides endpoints for:
- Managing ERP integration accounts (Tally, ERPNext, Zoho Books, SAP, QuickBooks)
- Triggering on-demand or automated synchronization jobs (Orders, Inventory, GST, Invoices, Customers)
- Webhook dispatch testing & retry queue inspection
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.core.enterprise_integration import enterprise_hub

router = APIRouter(prefix="/api/v1/integrations", tags=["Enterprise Integration Hub"])


class ConnectAccountRequest(BaseModel):
    artisan_id: str
    provider: str = Field(..., description="tally | erpnext | zoho_books | sap | quickbooks")
    account_name: str
    auth_type: str = Field(default="api_key", description="oauth2 | api_key | basic_auth | xml_rpc")
    endpoint_url: str
    credentials: Dict[str, Any] = Field(default_factory=dict)
    gstin: Optional[str] = None
    sync_config: Optional[Dict[str, bool]] = None


class TriggerSyncRequest(BaseModel):
    account_id: str
    sync_type: str = Field(default="orders", description="orders | inventory | gst | invoices | customers | full_sync")
    entity_payload: Optional[Dict[str, Any]] = None


class DispatchWebhookRequest(BaseModel):
    event_type: str = Field(default="order.created", description="order.created | order.fulfilled | inventory.updated | invoice.generated")
    target_url: str
    payload: Dict[str, Any]
    account_id: Optional[str] = None


@router.get("/summary", summary="Get integration hub summary & connected accounts")
def get_hub_summary():
    return {"status": "success", "data": enterprise_hub.get_hub_summary()}


@router.post("/accounts/connect", summary="Connect a new ERP/Accounting integration account")
def connect_account(payload: ConnectAccountRequest):
    try:
        acc = enterprise_hub.connect_account(
            artisan_id=payload.artisan_id,
            provider=payload.provider,
            account_name=payload.account_name,
            auth_type=payload.auth_type,
            endpoint_url=payload.endpoint_url,
            credentials=payload.credentials,
            gstin=payload.gstin,
            sync_config=payload.sync_config,
        )
        return {"status": "success", "account": acc.to_dict()}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/sync/trigger", summary="Trigger synchronization job (Orders, Stock, GST, Invoices)")
def trigger_sync_job(payload: TriggerSyncRequest):
    try:
        job = enterprise_hub.trigger_sync(
            account_id=payload.account_id,
            sync_type=payload.sync_type,
            entity_payload=payload.entity_payload,
        )
        return {"status": "success", "sync_job": job.to_dict()}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/webhooks/dispatch", summary="Dispatch real-time webhook event to external endpoint")
def dispatch_webhook(payload: DispatchWebhookRequest):
    evt = enterprise_hub.dispatch_webhook(
        event_type=payload.event_type,
        target_url=payload.target_url,
        payload=payload.payload,
        account_id=payload.account_id,
    )
    return {"status": "dispatched", "webhook_event": evt.to_dict()}
