"""
Orders / Escrow / Lifecycle API — B2B Production Order Management (Phase 11).

Endpoints:
  POST  /api/v1/orders              - Create order (from RFQ, quote, or direct product)
  GET   /api/v1/orders              - List user orders (as buyer or seller)
  GET   /api/v1/orders/{id}         - Get order details with items, timeline & invoice
  PATCH /api/v1/orders/{id}/status  - Update order status along lifecycle flow
  POST  /api/v1/orders/{id}/cancel  - Cancel order
  POST  /api/v1/orders/{id}/dispute - Raise dispute on order
  GET   /api/v1/orders/{id}/invoice - Get invoice metadata
  GET   /api/v1/orders/{id}/invoice/pdf - Download GST tax invoice PDF
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import Response

from app.core.security import get_current_user
from app.database.connection import get_supabase_client
from app.models.order import (
    OrderStatus,
    OrderCreate,
    OrderStatusUpdate,
    OrderCancelRequest,
    OrderDisputeRequest,
    OrderResponse,
    OrderItemResponse,
    OrderStatusHistoryResponse,
    InvoiceResponse,
)
from app.services.invoice_pdf import generate_invoice_pdf
from app.services import inventory_service

logger = logging.getLogger(__name__)

router = APIRouter()

# Lifecycle transition rules
ALLOWED_TRANSITIONS = {
    OrderStatus.rfq_accepted: [OrderStatus.pending_advance, OrderStatus.cancelled],
    OrderStatus.pending_advance: [OrderStatus.seller_accepted, OrderStatus.cancelled],
    OrderStatus.seller_accepted: [OrderStatus.in_production, OrderStatus.cancelled],
    OrderStatus.in_production: [OrderStatus.quality_check, OrderStatus.disputed],
    OrderStatus.quality_check: [OrderStatus.ready_to_dispatch, OrderStatus.disputed],
    OrderStatus.ready_to_dispatch: [OrderStatus.shipped, OrderStatus.disputed],
    OrderStatus.shipped: [OrderStatus.delivered, OrderStatus.disputed],
    OrderStatus.delivered: [OrderStatus.completed, OrderStatus.disputed],
    OrderStatus.completed: [],
    OrderStatus.cancelled: [],
    OrderStatus.disputed: [OrderStatus.in_production, OrderStatus.completed, OrderStatus.cancelled],
}

# In-memory store fallback for development / mock mode when Supabase table isn't connected
_mock_orders: Dict[str, dict] = {}
_mock_order_items: Dict[str, List[dict]] = {}
_mock_status_history: Dict[str, List[dict]] = {}
_mock_invoices: Dict[str, dict] = {}


def _get_user_id(current_user: dict) -> str:
    artisan = current_user.get("artisan") or {}
    art_id = artisan.get("id")
    if art_id:
        return str(art_id)
    uid = current_user.get("firebase_uid")
    if uid:
        return str(uid)
    return "00000000-0000-0000-0000-000000000001"


def _build_order_response(order: dict, items: List[dict], history: List[dict], invoice: Optional[dict]) -> dict:
    resp = dict(order)
    resp["items"] = items
    resp["status_history"] = sorted(history, key=lambda x: str(x.get("created_at", "")))
    resp["invoice"] = invoice
    return resp


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_in: OrderCreate,
    current_user: dict = Depends(get_current_user),
):
    """
    Create a new production order from an RFQ quote or direct product.
    Generates Order ID, calculates GST, shipping, advance escrow, and issues initial Invoice.
    """
    buyer_id = _get_user_id(current_user)
    artisan_id = str(order_in.artisan_id)

    order_id = str(uuid.uuid4())
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    order_number = f"ORD-{date_str}-{order_id[:6].upper()}"

    # Price breakdown calculation
    qty = max(1, order_in.quantity)
    unit_p = max(0.0, float(order_in.unit_price))
    subtotal = round(qty * unit_p, 2)

    # Coupon & Growth Promotion calculation
    discount_amount = 0.0
    shipping_charges = round(float(order_in.shipping_charges), 2)
    applied_coupon = order_in.coupon_code.strip().upper() if order_in.coupon_code else None

    if applied_coupon == "WELCOME50":
        discount_amount += 50.0
    elif applied_coupon == "FESTIVAL15":
        discount_amount += round((subtotal * 15.0) / 100.0, 2)
    elif applied_coupon == "FREESHIP":
        shipping_charges = 0.0
    elif applied_coupon:
        # Default flat 10% coupon fallback for valid promotional tests
        discount_amount += round((subtotal * 10.0) / 100.0, 2)

    # Reward Points redemption (1 point = ₹0.50)
    reward_pts_used = max(0, int(order_in.reward_points_used or 0))
    if reward_pts_used > 0:
        reward_discount = round(reward_pts_used * 0.50, 2)
        discount_amount += reward_discount

    discount_amount = min(subtotal, round(discount_amount, 2))
    discounted_subtotal = max(0.0, subtotal - discount_amount)

    gst_rate = 18.0
    gst_amount = round((discounted_subtotal * gst_rate) / 100.0, 2)
    total_amount = round(discounted_subtotal + gst_amount + shipping_charges, 2)

    advance_pct = max(10.0, min(100.0, float(order_in.advance_percentage)))
    advance_amount = round((total_amount * advance_pct) / 100.0, 2)
    remaining_balance = round(total_amount - advance_amount, 2)

    now_iso = datetime.now(timezone.utc).isoformat()

    order_dict = {
        "id": order_id,
        "order_number": order_number,
        "buyer_id": buyer_id,
        "artisan_id": artisan_id,
        "rfq_id": order_in.rfq_id,
        "quote_id": order_in.quote_id,
        "status": OrderStatus.rfq_accepted.value,
        "currency": order_in.currency,
        "subtotal": subtotal,
        "discount_amount": discount_amount,
        "coupon_code": applied_coupon,
        "reward_points_used": reward_pts_used,
        "gst_rate": gst_rate,
        "gst_amount": gst_amount,
        "shipping_charges": shipping_charges,
        "total_amount": total_amount,
        "advance_amount": advance_amount,
        "remaining_balance": remaining_balance,
        "advance_paid": False,
        "final_paid": False,
        "delivery_address": order_in.delivery_address,
        "shipping_address": order_in.shipping_address,
        "buyer_name": order_in.buyer_name,
        "buyer_phone": order_in.buyer_phone,
        "buyer_email": order_in.buyer_email,
        "seller_name": order_in.seller_name,
        "seller_phone": order_in.seller_phone,
        "notes": order_in.notes,
        "cancel_reason": None,
        "dispute_reason": None,
        "created_at": now_iso,
        "updated_at": now_iso,
    }

    # Item record
    item_id = str(uuid.uuid4())
    item_dict = {
        "id": item_id,
        "order_id": order_id,
        "product_id": order_in.product_id,
        "product_title": order_in.product_title or "Artisan Handicraft Item",
        "product_image_url": order_in.product_image_url,
        "unit_price": unit_p,
        "quantity": qty,
        "subtotal": subtotal,
        "specifications": order_in.specifications or {},
        "created_at": now_iso,
    }

    # Initial status history
    history_id = str(uuid.uuid4())
    history_dict = {
        "id": history_id,
        "order_id": order_id,
        "from_status": None,
        "to_status": OrderStatus.rfq_accepted.value,
        "changed_by_id": buyer_id,
        "changed_by_role": "buyer",
        "notes": "Order placed and RFQ accepted by buyer",
        "created_at": now_iso,
    }

    # Initial Invoice
    inv_id = str(uuid.uuid4())
    inv_number = f"INV-{date_str}-{inv_id[:6].upper()}"
    invoice_dict = {
        "id": inv_id,
        "invoice_number": inv_number,
        "order_id": order_id,
        "buyer_id": buyer_id,
        "artisan_id": artisan_id,
        "invoice_date": now_iso,
        "due_date": None,
        "subtotal": subtotal,
        "tax_amount": gst_amount,
        "shipping_amount": shipping_charges,
        "total_amount": total_amount,
        "paid_amount": 0.0,
        "balance_due": total_amount,
        "status": "issued",
        "pdf_url": f"/api/v1/orders/{order_id}/invoice/pdf",
        "created_at": now_iso,
    }

    # Persist in Supabase or fallback mock store
    supabase_synced = False
    try:
        client = get_supabase_client()
        client.table("orders").insert(order_dict).execute()
        client.table("order_items").insert(item_dict).execute()
        client.table("order_status_history").insert(history_dict).execute()
        client.table("invoices").insert(invoice_dict).execute()
        supabase_synced = True
    except Exception as exc:
        logger.warning("Supabase orders table write failed (fallback to mock memory): %s", exc)

    _mock_orders[order_id] = order_dict
    _mock_order_items[order_id] = [item_dict]
    _mock_status_history[order_id] = [history_dict]
    _mock_invoices[order_id] = invoice_dict

    # Smart Inventory: Reserve stock for order item
    try:
        inventory_service.reserve_stock(
            product_id=order_in.product_id,
            artisan_id=artisan_id,
            quantity=qty,
            order_id=order_id,
        )
    except Exception as inv_err:
        logger.warning("Auto stock reservation skipped/failed: %s", inv_err)

    return _build_order_response(order_dict, [item_dict], [history_dict], invoice_dict)


@router.get("", response_model=List[OrderResponse])
async def list_orders(
    role: Optional[str] = Query(None, description="Filter by role: 'buyer' or 'seller'"),
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: dict = Depends(get_current_user),
):
    """List orders belonging to current user as buyer or seller."""
    user_id = _get_user_id(current_user)

    results: List[dict] = []
    try:
        client = get_supabase_client()
        q = client.table("orders").select("*")
        if role == "buyer":
            q = q.eq("buyer_id", user_id)
        elif role == "seller":
            q = q.eq("artisan_id", user_id)
        else:
            # Either buyer or artisan
            q = q.or_(f"buyer_id.eq.{user_id},artisan_id.eq.{user_id}")

        if status_filter:
            q = q.eq("status", status_filter)

        res = q.order("created_at", desc=True).execute()
        orders_db = res.data or []
        for o in orders_db:
            oid = o["id"]
            items_res = client.table("order_items").select("*").eq("order_id", oid).execute()
            hist_res = client.table("order_status_history").select("*").eq("order_id", oid).execute()
            inv_res = client.table("invoices").select("*").eq("order_id", oid).limit(1).execute()
            inv = inv_res.data[0] if inv_res.data else None
            results.append(_build_order_response(o, items_res.data or [], hist_res.data or [], inv))
        return results
    except Exception as exc:
        logger.debug("Supabase list orders failed, checking mock store: %s", exc)

    # Mock store fallback
    matched = []
    for oid, o in _mock_orders.items():
        if role == "buyer" and o.get("buyer_id") != user_id:
            continue
        elif role == "seller" and o.get("artisan_id") != user_id:
            continue
        elif not role and o.get("buyer_id") != user_id and o.get("artisan_id") != user_id:
            continue

        if status_filter and o.get("status") != status_filter:
            continue

        matched.append(_build_order_response(
            o,
            _mock_order_items.get(oid, []),
            _mock_status_history.get(oid, []),
            _mock_invoices.get(oid)
        ))
    return matched


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order_details(
    order_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Retrieve full order details including timeline history and invoice."""
    user_id = _get_user_id(current_user)

    try:
        client = get_supabase_client()
        res = client.table("orders").select("*").eq("id", order_id).limit(1).execute()
        if res.data:
            o = res.data[0]
            items_res = client.table("order_items").select("*").eq("order_id", order_id).execute()
            hist_res = client.table("order_status_history").select("*").eq("order_id", order_id).execute()
            inv_res = client.table("invoices").select("*").eq("order_id", order_id).limit(1).execute()
            inv = inv_res.data[0] if inv_res.data else None
            return _build_order_response(o, items_res.data or [], hist_res.data or [], inv)
    except Exception as exc:
        logger.debug("Supabase get order failed: %s", exc)

    if order_id in _mock_orders:
        return _build_order_response(
            _mock_orders[order_id],
            _mock_order_items.get(order_id, []),
            _mock_status_history.get(order_id, []),
            _mock_invoices.get(order_id)
        )

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")


@router.patch("/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    order_id: str,
    update_in: OrderStatusUpdate,
    current_user: dict = Depends(get_current_user),
):
    """
    Transition order status along the 9-stage sequence:
    rfq_accepted -> pending_advance -> seller_accepted -> in_production -> quality_check ->
    ready_to_dispatch -> shipped -> delivered -> completed.
    """
    user_id = _get_user_id(current_user)

    # Fetch current order
    order = None
    try:
        client = get_supabase_client()
        res = client.table("orders").select("*").eq("id", order_id).limit(1).execute()
        if res.data:
            order = res.data[0]
    except Exception:
        pass

    if not order:
        order = _mock_orders.get(order_id)

    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    current_status = OrderStatus(order["status"])
    target_status = update_in.status

    # Validate transition
    allowed = ALLOWED_TRANSITIONS.get(current_status, [])
    if target_status not in allowed and target_status != current_status:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid transition from '{current_status.value}' to '{target_status.value}'. Allowed: {[s.value for s in allowed]}"
        )

    now_iso = datetime.now(timezone.utc).isoformat()
    order["status"] = target_status.value
    order["updated_at"] = now_iso

    # Escrow update
    if target_status == OrderStatus.seller_accepted:
        order["advance_paid"] = True
    elif target_status == OrderStatus.completed:
        order["final_paid"] = True

    # Determine actor role
    changed_by_role = "seller" if user_id == str(order.get("artisan_id")) else "buyer"

    hist_entry = {
        "id": str(uuid.uuid4()),
        "order_id": order_id,
        "from_status": current_status.value,
        "to_status": target_status.value,
        "changed_by_id": user_id,
        "changed_by_role": changed_by_role,
        "notes": update_in.notes or f"Status changed to {target_status.value.replace('_', ' ').title()}",
        "created_at": now_iso,
    }

    try:
        client = get_supabase_client()
        client.table("orders").update(order).eq("id", order_id).execute()
        client.table("order_status_history").insert(hist_entry).execute()
    except Exception as exc:
        logger.warning("Supabase update order status error: %s", exc)

    _mock_orders[order_id] = order
    if order_id not in _mock_status_history:
        _mock_status_history[order_id] = []
    _mock_status_history[order_id].append(hist_entry)

    # When order reaches completed stage, commit reserved stock to sold_stock and update sustainability carbon analytics
    if target_status == OrderStatus.completed:
        try:
            items = _mock_order_items.get(order_id, [])
            for it in items:
                inventory_service.commit_reserved_sale(
                    product_id=it["product_id"],
                    artisan_id=order["artisan_id"],
                    quantity=it.get("quantity", 1),
                    order_id=order_id,
                )
        except Exception as sale_err:
            logger.warning("Commit sale stock failed: %s", sale_err)

        # Automatic Sustainability & Carbon Impact Update (Phase 7)
        try:
            from app.services import sustainability_service
            items = _mock_order_items.get(order_id, [])
            sustainability_service.record_order_sustainability_impact(
                order_id=order_id,
                artisan_id=order["artisan_id"],
                items=items if items else [{"quantity": 1, "product_title": "GI Craft Product"}]
            )
        except Exception as sust_err:
            logger.warning("Sustainability impact update failed: %s", sust_err)

    return await get_order_details(order_id, current_user)


@router.post("/{order_id}/cancel", response_model=OrderResponse)
async def cancel_order(
    order_id: str,
    cancel_in: OrderCancelRequest,
    current_user: dict = Depends(get_current_user),
):
    """Cancel an order before production begins."""
    user_id = _get_user_id(current_user)

    order = _mock_orders.get(order_id)
    try:
        client = get_supabase_client()
        res = client.table("orders").select("*").eq("id", order_id).limit(1).execute()
        if res.data:
            order = res.data[0]
    except Exception:
        pass

    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    curr_st = order.get("status")
    if curr_st in [OrderStatus.shipped.value, OrderStatus.delivered.value, OrderStatus.completed.value]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel order in '{curr_st}' stage. Please raise a dispute instead."
        )

    now_iso = datetime.now(timezone.utc).isoformat()
    order["status"] = OrderStatus.cancelled.value
    order["cancel_reason"] = cancel_in.reason
    order["updated_at"] = now_iso

    changed_by_role = "seller" if user_id == str(order.get("artisan_id")) else "buyer"
    hist_entry = {
        "id": str(uuid.uuid4()),
        "order_id": order_id,
        "from_status": curr_st,
        "to_status": OrderStatus.cancelled.value,
        "changed_by_id": user_id,
        "changed_by_role": changed_by_role,
        "notes": f"Order Cancelled: {cancel_in.reason}",
        "created_at": now_iso,
    }

    try:
        client = get_supabase_client()
        client.table("orders").update(order).eq("id", order_id).execute()
        client.table("order_status_history").insert(hist_entry).execute()
    except Exception:
        pass

    _mock_orders[order_id] = order
    _mock_status_history.setdefault(order_id, []).append(hist_entry)

    # Release reserved stock upon cancellation
    try:
        items = _mock_order_items.get(order_id, [])
        for it in items:
            inventory_service.release_reserved_stock(
                product_id=it["product_id"],
                artisan_id=order["artisan_id"],
                quantity=it.get("quantity", 1),
                order_id=order_id,
            )
    except Exception as rel_err:
        logger.warning("Release stock failed: %s", rel_err)

    return await get_order_details(order_id, current_user)


@router.post("/{order_id}/dispute", response_model=OrderResponse)
async def raise_dispute(
    order_id: str,
    dispute_in: OrderDisputeRequest,
    current_user: dict = Depends(get_current_user),
):
    """Raise dispute on order (quality issue, dispatch delay, wrong spec)."""
    user_id = _get_user_id(current_user)

    order = _mock_orders.get(order_id)
    try:
        client = get_supabase_client()
        res = client.table("orders").select("*").eq("id", order_id).limit(1).execute()
        if res.data:
            order = res.data[0]
    except Exception:
        pass

    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    now_iso = datetime.now(timezone.utc).isoformat()
    curr_st = order.get("status")
    order["status"] = OrderStatus.disputed.value
    order["dispute_reason"] = dispute_in.reason
    order["updated_at"] = now_iso

    changed_by_role = "seller" if user_id == str(order.get("artisan_id")) else "buyer"
    hist_entry = {
        "id": str(uuid.uuid4()),
        "order_id": order_id,
        "from_status": curr_st,
        "to_status": OrderStatus.disputed.value,
        "changed_by_id": user_id,
        "changed_by_role": changed_by_role,
        "notes": f"Dispute Raised ({dispute_in.dispute_type}): {dispute_in.reason}",
        "created_at": now_iso,
    }

    try:
        client = get_supabase_client()
        client.table("orders").update(order).eq("id", order_id).execute()
        client.table("order_status_history").insert(hist_entry).execute()
    except Exception:
        pass

    _mock_orders[order_id] = order
    _mock_status_history.setdefault(order_id, []).append(hist_entry)

    return await get_order_details(order_id, current_user)


@router.get("/{order_id}/invoice", response_model=InvoiceResponse)
async def get_order_invoice(
    order_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Fetch invoice metadata for order."""
    try:
        client = get_supabase_client()
        res = client.table("invoices").select("*").eq("order_id", order_id).limit(1).execute()
        if res.data:
            return res.data[0]
    except Exception:
        pass

    inv = _mock_invoices.get(order_id)
    if inv:
        return inv

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")


@router.get("/{order_id}/invoice/pdf")
async def download_invoice_pdf(
    order_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Download authentic GST Tax Invoice PDF for an order."""
    order_resp = await get_order_details(order_id, current_user)
    if isinstance(order_resp, dict):
        order_data = order_resp
        inv_data = order_resp.get("invoice") or {
            "invoice_number": f"INV-{order_resp.get('order_number', '0000')}",
            "invoice_date": datetime.now(timezone.utc).isoformat()
        }
        order_number = order_resp.get("order_number", "0000")
    else:
        order_data = order_resp.model_dump()
        inv = order_resp.invoice
        inv_data = inv.model_dump() if inv else {
            "invoice_number": f"INV-{order_resp.order_number}",
            "invoice_date": datetime.now(timezone.utc).isoformat()
        }
        order_number = order_resp.order_number

    pdf_bytes = generate_invoice_pdf(order_data, inv_data)
    filename = f"Invoice_{order_number}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=\"{filename}\""}
    )
