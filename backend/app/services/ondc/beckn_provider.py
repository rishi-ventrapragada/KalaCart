from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid
from app.services.ondc.base_provider import IONDCProvider
from app.models.ondc import (
    ONDCPublishProductRequest,
    BecknItem,
    BecknDescriptor,
    ONDCIncomingOrderRequest,
    ONDCCancellationRequest,
    ONDCReturnRequest
)

class BecknProductionProvider(IONDCProvider):
    """
    Standard Beckn v1.2 Protocol Implementation for KalaCart BPP.
    Complies with ONDC:RET12 (Handicrafts, Artware & Handlooms) Domain specifications.
    """

    BPP_ID = "bpp.kalacart.in"
    BPP_URI = "https://api.kalacart.in/ondc/bpp"
    DOMAIN = "ONDC:RET12"

    def build_beckn_item(self, req: ONDCPublishProductRequest) -> BecknItem:
        network_item_id = f"KC-ONDC-{req.product_id[:8].upper()}" if "-" in req.product_id else f"KC-ONDC-{req.product_id}"

        descriptor = BecknDescriptor(
            name=req.product_name,
            code=f"HANDICRAFT-{req.category_id.replace(' ', '_').upper()}",
            symbol="GI-TAG-CERTIFIED",
            short_desc=req.product_description[:100],
            long_desc=req.product_description,
            images=req.image_urls or ["https://storage.kalacart.in/defaults/handicraft_preview.jpg"]
        )

        price = {
            "currency": "INR",
            "value": str(req.price_inr),
            "maximum_value": str(round(req.price_inr * 1.15, 2))  # MRP
        }

        tags = [
            {"code": "origin", "list": [{"code": "country", "value": "IND"}, {"code": "state", "value": req.artisan_cluster_location}]},
            {"code": "authenticity", "list": [{"code": "handcrafted", "value": "true"}, {"code": "gi_tagged", "value": "true"}]},
            {"code": "inventory", "list": [{"code": "available_quantity", "value": str(req.stock_quantity)}]}
        ]

        return BecknItem(
            id=network_item_id,
            descriptor=descriptor,
            price=price,
            category_id=req.category_id,
            fulfillment_id="F1-STANDARD-COURIER",
            location_id="L1-ARTISAN-HUB",
            time_to_ship=f"P{req.time_to_ship_days}D",
            matched=True,
            tags=tags
        )

    def handle_search(self, category_id: Optional[str] = None) -> List[BecknItem]:
        # Catalog responder
        return []

    def handle_order_init_and_confirm(self, req: ONDCIncomingOrderRequest) -> Dict[str, Any]:
        total_amount = round(req.unit_price_inr * req.quantity, 2)
        return {
            "beckn_order_id": req.network_order_id,
            "bpp_id": self.BPP_ID,
            "bpp_uri": self.BPP_URI,
            "bap_id": req.bap_id,
            "bap_uri": req.bap_uri,
            "state": "Accepted",
            "quote": {
                "price": {"currency": "INR", "value": str(total_amount)},
                "breakup": [
                    {"title": "Item Total", "price": {"currency": "INR", "value": str(total_amount)}},
                    {"title": "Handicraft Board Escrow Guarantee", "price": {"currency": "INR", "value": "0.00"}}
                ]
            },
            "fulfillment": {
                "id": "F1-STANDARD-COURIER",
                "type": "Delivery",
                "state": {"descriptor": {"code": "Order-picked-up"}},
                "tracking": True
            }
        }

    def handle_cancellation(self, order_id: str, req: ONDCCancellationRequest) -> Dict[str, Any]:
        return {
            "order_id": order_id,
            "state": "Cancelled",
            "cancellation_reason_code": req.cancellation_reason_code,
            "cancellation_timestamp": datetime.utcnow().isoformat(),
            "refund_status": "Escrow-Refund-Initiated"
        }

    def handle_return(self, order_id: str, req: ONDCReturnRequest) -> Dict[str, Any]:
        return {
            "order_id": order_id,
            "return_status": "Return-Approved",
            "return_reason_code": req.return_reason_code,
            "pickup_window": "Within 48 hours via India Post / Delhivery reverse logistics"
        }
