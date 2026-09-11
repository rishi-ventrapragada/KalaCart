from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid
from app.models.supply_chain import (
    MaterialResponse,
    MaterialCategory,
    SupplierResponse,
    PurchaseRequestCreate,
    PurchaseRequestResponse,
    SupplierQuoteCreate,
    SupplierQuoteResponse,
    GroupPurchasePoolResponse
)
from app.ai.supply_chain_recommender import _SEED_SUPPLIERS

_PURCHASE_REQUESTS: Dict[str, Dict[str, Any]] = {}
_SUPPLIER_QUOTES: Dict[str, Dict[str, Any]] = {}
_GROUP_POOLS: List[GroupPurchasePoolResponse] = [
    GroupPurchasePoolResponse(
        pool_id="pool-raghurajpur-clay",
        material_category=MaterialCategory.CLAY,
        cluster_name="Raghurajpur Heritage Artisan Village",
        target_quantity=50,
        current_pooled_quantity=38,
        pool_completion_percent=76.0,
        unlocked_discount_percent=25.0,
        deadline_date=(datetime.utcnow() + timedelta(days=4)).strftime("%Y-%m-%d")
    ),
    GroupPurchasePoolResponse(
        pool_id="pool-bastar-brass",
        material_category=MaterialCategory.BRASS,
        cluster_name="Bastar Bell Metal Craftsmen Guild",
        target_quantity=500,
        current_pooled_quantity=420,
        pool_completion_percent=84.0,
        unlocked_discount_percent=30.0,
        deadline_date=(datetime.utcnow() + timedelta(days=6)).strftime("%Y-%m-%d")
    )
]

class SupplyChainService:
    @staticmethod
    def list_materials(category: Optional[MaterialCategory] = None) -> List[MaterialResponse]:
        results = []
        for s in _SEED_SUPPLIERS:
            mat_dict = dict(s["material"])
            mat_dict["supplier_name"] = s["business_name"]
            if category and mat_dict["material_category"] != category.value:
                continue
            results.append(MaterialResponse(**mat_dict))
        return results

    @staticmethod
    def create_purchase_request(artisan_id: str, payload: PurchaseRequestCreate) -> PurchaseRequestResponse:
        req_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        record = {
            "id": req_id,
            "artisan_id": artisan_id,
            "material_id": payload.material_id,
            "quantity_requested": payload.quantity_requested,
            "max_budget_inr": payload.max_budget_inr,
            "is_group_purchase": payload.is_group_purchase,
            "group_pool_id": payload.group_pool_id,
            "delivery_location": payload.delivery_location,
            "status": "open",
            "created_at": now
        }
        _PURCHASE_REQUESTS[req_id] = record
        return PurchaseRequestResponse(**record)

    @staticmethod
    def list_purchase_requests(artisan_id: Optional[str] = None) -> List[PurchaseRequestResponse]:
        if not artisan_id:
            return [PurchaseRequestResponse(**p) for p in _PURCHASE_REQUESTS.values()]
        return [
            PurchaseRequestResponse(**p)
            for p in _PURCHASE_REQUESTS.values()
            if p["artisan_id"] == artisan_id
        ]

    @staticmethod
    def submit_quote(supplier_id: str, supplier_name: str, payload: SupplierQuoteCreate) -> SupplierQuoteResponse:
        req = _PURCHASE_REQUESTS.get(payload.purchase_request_id)
        if not req:
            raise ValueError(f"Purchase request {payload.purchase_request_id} not found")

        quote_id = str(uuid.uuid4())
        total = round(payload.quote_unit_price * req["quantity_requested"], 2)
        now = datetime.utcnow().isoformat()

        record = {
            "id": quote_id,
            "purchase_request_id": payload.purchase_request_id,
            "supplier_id": supplier_id,
            "supplier_name": supplier_name,
            "quote_unit_price": payload.quote_unit_price,
            "total_amount_inr": total,
            "estimated_delivery_days": payload.estimated_delivery_days,
            "quality_notes": payload.quality_notes or "100% Certified Direct Mill Supply",
            "status": "submitted",
            "created_at": now
        }
        _SUPPLIER_QUOTES[quote_id] = record
        req["status"] = "quotes_received"
        return SupplierQuoteResponse(**record)

    @staticmethod
    def accept_quote(quote_id: str) -> SupplierQuoteResponse:
        quote = _SUPPLIER_QUOTES.get(quote_id)
        if not quote:
            raise ValueError(f"Quote {quote_id} not found")

        quote["status"] = "accepted"
        req = _PURCHASE_REQUESTS.get(quote["purchase_request_id"])
        if req:
            req["status"] = "ordered"

        return SupplierQuoteResponse(**quote)

    @staticmethod
    def list_group_pools() -> List[GroupPurchasePoolResponse]:
        return _GROUP_POOLS
