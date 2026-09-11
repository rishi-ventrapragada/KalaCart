from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
from app.models.ondc import (
    ONDCPublishProductRequest,
    ONDCProductResponse,
    ONDCInventorySyncRequest,
    ONDCInventorySyncResponse,
    ONDCIncomingOrderRequest,
    ONDCOrderResponse,
    ONDCOrderState,
    ONDCCancellationRequest,
    ONDCReturnRequest,
    ONDCSyncLogResponse,
    ONDCBecknCatalogPayload,
    BecknItem
)
from app.services.ondc.base_provider import IONDCProvider
from app.services.ondc.beckn_provider import BecknProductionProvider

_ONDC_PRODUCTS: Dict[str, Dict[str, Any]] = {}
_ONDC_ORDERS: Dict[str, Dict[str, Any]] = {}
_ONDC_SYNC_LOGS: List[Dict[str, Any]] = []

class ONDCService:
    def __init__(self, provider: Optional[IONDCProvider] = None):
        self.provider = provider or BecknProductionProvider()

    def publish_product(self, req: ONDCPublishProductRequest) -> ONDCProductResponse:
        beckn_item = self.provider.build_beckn_item(req)
        now = datetime.utcnow().isoformat()
        mapping_id = str(uuid.uuid4())

        record = {
            "id": mapping_id,
            "product_id": req.product_id,
            "network_item_id": beckn_item.id,
            "domain": "ONDC:RET12",
            "bpp_id": "bpp.kalacart.in",
            "bpp_uri": "https://api.kalacart.in/ondc/bpp",
            "descriptor_name": beckn_item.descriptor.name,
            "descriptor_code": beckn_item.descriptor.code,
            "category_id": req.category_id,
            "fulfillment_id": beckn_item.fulfillment_id,
            "location_id": beckn_item.location_id,
            "time_to_ship_days": req.time_to_ship_days,
            "is_published": True,
            "sync_status": "synced",
            "last_synced_at": now,
            "beckn_payload": beckn_item
        }
        _ONDC_PRODUCTS[req.product_id] = record

        # Log transaction
        _ONDC_SYNC_LOGS.append({
            "id": str(uuid.uuid4()),
            "sync_type": "catalog_publish",
            "entity_id": req.product_id,
            "status": "success",
            "request_payload": req.model_dump(),
            "response_payload": beckn_item.model_dump(),
            "error_message": None,
            "created_at": now
        })

        return ONDCProductResponse(**record)

    def list_products(self) -> List[ONDCProductResponse]:
        return [ONDCProductResponse(**p) for p in _ONDC_PRODUCTS.values()]

    def sync_inventory(self, req: ONDCInventorySyncRequest) -> ONDCInventorySyncResponse:
        record = _ONDC_PRODUCTS.get(req.product_id)
        if not record:
            raise ValueError(f"Product {req.product_id} is not registered on ONDC")

        now = datetime.utcnow().isoformat()
        # update tags available_quantity
        beckn_item: BecknItem = record["beckn_payload"]
        for tag in beckn_item.tags:
            if tag.get("code") == "inventory":
                for item in tag.get("list", []):
                    if item.get("code") == "available_quantity":
                        item["value"] = str(req.new_stock_quantity)

        record["last_synced_at"] = now
        available = req.new_stock_quantity > 0

        _ONDC_SYNC_LOGS.append({
            "id": str(uuid.uuid4()),
            "sync_type": "inventory_sync",
            "entity_id": req.product_id,
            "status": "success",
            "request_payload": req.model_dump(),
            "response_payload": {"stock": req.new_stock_quantity, "available": available},
            "error_message": None,
            "created_at": now
        })

        return ONDCInventorySyncResponse(
            product_id=req.product_id,
            network_item_id=record["network_item_id"],
            synced_stock_quantity=req.new_stock_quantity,
            is_available_on_network=available,
            sync_status="synced",
            updated_at=now
        )

    def process_incoming_order(self, req: ONDCIncomingOrderRequest) -> ONDCOrderResponse:
        confirm_data = self.provider.handle_order_init_and_confirm(req)
        order_uuid = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        total_val = round(req.unit_price_inr * req.quantity, 2)

        order_record = {
            "id": order_uuid,
            "network_order_id": req.network_order_id,
            "kalacart_order_id": f"kc-ord-{uuid.uuid4().hex[:6]}",
            "bap_id": req.bap_id,
            "bap_uri": req.bap_uri,
            "transaction_id": req.transaction_id,
            "message_id": req.message_id,
            "total_value_inr": total_val,
            "state": ONDCOrderState.ACCEPTED,
            "fulfillment_status": "Assigned to Logistics Hub",
            "cancellation_reason_code": None,
            "return_status": None,
            "created_at": now,
            "updated_at": now
        }
        _ONDC_ORDERS[req.network_order_id] = order_record

        _ONDC_SYNC_LOGS.append({
            "id": str(uuid.uuid4()),
            "sync_type": "order_ingestion",
            "entity_id": req.network_order_id,
            "status": "success",
            "request_payload": req.model_dump(),
            "response_payload": confirm_data,
            "error_message": None,
            "created_at": now
        })

        return ONDCOrderResponse(**order_record)

    def list_orders(self) -> List[ONDCOrderResponse]:
        return [ONDCOrderResponse(**o) for o in _ONDC_ORDERS.values()]

    def cancel_order(self, network_order_id: str, req: ONDCCancellationRequest) -> ONDCOrderResponse:
        order = _ONDC_ORDERS.get(network_order_id)
        if not order:
            raise ValueError(f"ONDC Order {network_order_id} not found")

        cancel_resp = self.provider.handle_cancellation(network_order_id, req)
        now = datetime.utcnow().isoformat()
        order["state"] = ONDCOrderState.CANCELLED
        order["cancellation_reason_code"] = req.cancellation_reason_code
        order["fulfillment_status"] = "Cancelled"
        order["updated_at"] = now

        _ONDC_SYNC_LOGS.append({
            "id": str(uuid.uuid4()),
            "sync_type": "cancellation",
            "entity_id": network_order_id,
            "status": "success",
            "request_payload": req.model_dump(),
            "response_payload": cancel_resp,
            "error_message": None,
            "created_at": now
        })

        return ONDCOrderResponse(**order)

    def return_order(self, network_order_id: str, req: ONDCReturnRequest) -> ONDCOrderResponse:
        order = _ONDC_ORDERS.get(network_order_id)
        if not order:
            raise ValueError(f"ONDC Order {network_order_id} not found")

        return_resp = self.provider.handle_return(network_order_id, req)
        now = datetime.utcnow().isoformat()
        order["return_status"] = f"Return Initiated (Code: {req.return_reason_code})"
        order["updated_at"] = now

        _ONDC_SYNC_LOGS.append({
            "id": str(uuid.uuid4()),
            "sync_type": "return",
            "entity_id": network_order_id,
            "status": "success",
            "request_payload": req.model_dump(),
            "response_payload": return_resp,
            "error_message": None,
            "created_at": now
        })

        return ONDCOrderResponse(**order)

    def list_sync_logs(self) -> List[ONDCSyncLogResponse]:
        return [ONDCSyncLogResponse(**l) for l in _ONDC_SYNC_LOGS]
