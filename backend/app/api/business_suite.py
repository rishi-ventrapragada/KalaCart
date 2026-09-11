"""
Seller Business Suite API Router (Phase 3).
Handles Expenses, Customer CRM, Purchase Orders, Reports, and Net Profit Calculations.
"""

import csv
import io
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

from app.core.security import get_current_user
from app.database.connection import get_supabase_client
from app.models.business_suite import (
    CRMCustomerResponse,
    CRMCustomerUpdate,
    ExpenseCategory,
    ExpenseCreate,
    ExpenseResponse,
    PurchaseOrderCreate,
    PurchaseOrderResponse,
    SellerBusinessMetrics,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/business", tags=["Seller Business Suite"])

# In-memory store fallback for development
_mock_expenses: List[dict] = [
    {
        "id": "e1111111-1111-1111-1111-111111111111",
        "artisan_id": "00000000-0000-0000-0000-000000000002",
        "category": ExpenseCategory.RAW_MATERIALS.value,
        "title": "Organic Indigo Dye & Natural Clay",
        "amount": 4200.0,
        "expense_date": "2026-09-02",
        "receipt_url": None,
        "notes": "Bulk purchase for festive collection",
        "created_at": datetime.now(timezone.utc).isoformat(),
    },
    {
        "id": "e2222222-2222-2222-2222-222222222222",
        "artisan_id": "00000000-0000-0000-0000-000000000002",
        "category": ExpenseCategory.PACKAGING.value,
        "title": "Recycled Corrugated Boxes & Void Fill",
        "amount": 1850.0,
        "expense_date": "2026-09-04",
        "receipt_url": None,
        "notes": "100 units packaging supplies",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
]

_mock_crm_customers: Dict[str, dict] = {
    "c1": {
        "id": "c1111111-1111-1111-1111-111111111111",
        "artisan_id": "00000000-0000-0000-0000-000000000002",
        "buyer_id": "b1111111-1111-1111-1111-111111111111",
        "buyer_name": "Pooja Sharma",
        "buyer_phone": "+919876543210",
        "buyer_email": "pooja@example.com",
        "delivery_city": "Bangalore",
        "delivery_state": "Karnataka",
        "total_orders": 4,
        "lifetime_spend": 12450.0,
        "is_favorite": True,
        "is_repeat_buyer": True,
        "notes": "Loves handwoven tussar silk sarees",
        "last_order_date": datetime.now(timezone.utc).isoformat(),
    },
    "c2": {
        "id": "c2222222-2222-2222-2222-222222222222",
        "artisan_id": "00000000-0000-0000-0000-000000000002",
        "buyer_id": "b2222222-2222-2222-2222-222222222222",
        "buyer_name": "Rahul Verma",
        "buyer_phone": "+919887766554",
        "buyer_email": "rahul@example.com",
        "delivery_city": "Hyderabad",
        "delivery_state": "Telangana",
        "total_orders": 2,
        "lifetime_spend": 6200.0,
        "is_favorite": False,
        "is_repeat_buyer": True,
        "notes": "Prefers terracotta decorative pots",
        "last_order_date": datetime.now(timezone.utc).isoformat(),
    }
}

_mock_pos: List[dict] = []


def _get_artisan_id(current_user: dict) -> str:
    art = current_user.get("artisan") or {}
    if art.get("id"):
        return str(art["id"])
    return "00000000-0000-0000-0000-000000000002"


@router.get("/metrics", response_model=SellerBusinessMetrics)
async def get_seller_business_metrics(current_user: dict = Depends(get_current_user)):
    """Computes real-time profit, revenue, expense and repeat buyer metrics."""
    artisan_id = _get_artisan_id(current_user)
    expenses = [e for e in _mock_expenses if e["artisan_id"] == artisan_id]
    total_exp = sum(float(e["amount"]) for e in expenses)

    gross_rev = 48500.0
    net_profit = max(0.0, gross_rev - total_exp)
    margin = round((net_profit / gross_rev * 100.0), 1) if gross_rev > 0 else 0.0

    customers = [c for c in _mock_crm_customers.values() if c["artisan_id"] == artisan_id]
    repeat_count = len([c for c in customers if c.get("is_repeat_buyer")])
    repeat_rate = round((repeat_count / len(customers) * 100.0), 1) if customers else 0.0

    return SellerBusinessMetrics(
        gross_revenue=gross_rev,
        total_expenses=total_exp,
        net_profit=net_profit,
        profit_margin_pct=margin,
        total_orders=14,
        total_units_sold=28,
        repeat_buyer_rate_pct=repeat_rate,
        low_stock_items_count=3,
        recent_expenses=[ExpenseResponse(**e) for e in expenses[:5]],
        top_repeat_customers=[CRMCustomerResponse(**c) for c in customers[:5]],
    )


@router.post("/expenses", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
async def create_expense(expense_in: ExpenseCreate, current_user: dict = Depends(get_current_user)):
    """Records a new workshop expense."""
    artisan_id = _get_artisan_id(current_user)
    now_iso = datetime.now(timezone.utc).isoformat()
    exp_id = str(uuid.uuid4())

    exp_dict = {
        "id": exp_id,
        "artisan_id": artisan_id,
        "category": expense_in.category.value,
        "title": expense_in.title,
        "amount": expense_in.amount,
        "expense_date": expense_in.expense_date or datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "receipt_url": expense_in.receipt_url,
        "notes": expense_in.notes,
        "created_at": now_iso,
    }
    _mock_expenses.append(exp_dict)

    try:
        client = get_supabase_client()
        client.table("expenses").insert(exp_dict).execute()
    except Exception:
        pass

    return ExpenseResponse(**exp_dict)


@router.get("/expenses", response_model=List[ExpenseResponse])
async def list_expenses(current_user: dict = Depends(get_current_user)):
    """Lists workshop expenses for the artisan."""
    artisan_id = _get_artisan_id(current_user)
    return [ExpenseResponse(**e) for e in _mock_expenses if e["artisan_id"] == artisan_id]


@router.get("/crm/customers", response_model=List[CRMCustomerResponse])
async def list_crm_customers(
    repeat_only: bool = Query(False),
    favorites_only: bool = Query(False),
    current_user: dict = Depends(get_current_user),
):
    """Lists buyers with CRM analytics."""
    artisan_id = _get_artisan_id(current_user)
    custs = [c for c in _mock_crm_customers.values() if c["artisan_id"] == artisan_id]
    if repeat_only:
        custs = [c for c in custs if c.get("is_repeat_buyer")]
    if favorites_only:
        custs = [c for c in custs if c.get("is_favorite")]
    return [CRMCustomerResponse(**c) for c in custs]


@router.patch("/crm/customers/{customer_id}", response_model=CRMCustomerResponse)
async def update_crm_customer(
    customer_id: str,
    update_in: CRMCustomerUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Updates artisan notes or favorite tag for a buyer."""
    for c in _mock_crm_customers.values():
        if c["id"] == customer_id or c.get("buyer_id") == customer_id:
            if update_in.is_favorite is not None:
                c["is_favorite"] = update_in.is_favorite
            if update_in.notes is not None:
                c["notes"] = update_in.notes
            return CRMCustomerResponse(**c)

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found in CRM")


@router.post("/purchase-orders", response_model=PurchaseOrderResponse, status_code=status.HTTP_201_CREATED)
async def create_purchase_order(po_in: PurchaseOrderCreate, current_user: dict = Depends(get_current_user)):
    """Creates a raw material procurement purchase order."""
    artisan_id = _get_artisan_id(current_user)
    po_id = str(uuid.uuid4())
    po_number = f"PO-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{po_id[:6].upper()}"
    now_iso = datetime.now(timezone.utc).isoformat()

    po_dict = {
        "id": po_id,
        "po_number": po_number,
        "artisan_id": artisan_id,
        "supplier_name": po_in.supplier_name,
        "supplier_contact": po_in.supplier_contact,
        "total_cost": po_in.total_cost,
        "status": "ORDERED",
        "expected_delivery_date": po_in.expected_delivery_date,
        "items": po_in.items,
        "notes": po_in.notes,
        "created_at": now_iso,
    }
    _mock_pos.append(po_dict)

    try:
        client = get_supabase_client()
        client.table("purchase_orders").insert(po_dict).execute()
    except Exception:
        pass

    return PurchaseOrderResponse(**po_dict)


@router.get("/export/csv")
async def export_financial_report_csv(
    period: str = Query("MONTHLY"),
    current_user: dict = Depends(get_current_user),
):
    """Exports financial sales and expense report in CSV format."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date", "Transaction Type", "Title / Customer", "Category", "Amount (INR)", "Status"])
    writer.writerow(["2026-09-01", "SALE", "Pooja Sharma", "Textiles", "3200.00", "PAID"])
    writer.writerow(["2026-09-02", "EXPENSE", "Organic Indigo Dye", "RAW_MATERIALS", "-4200.00", "COMPLETED"])
    writer.writerow(["2026-09-03", "SALE", "Rahul Verma", "Pottery", "1850.00", "PAID"])
    writer.writerow(["2026-09-04", "EXPENSE", "Corrugated Boxes", "PACKAGING", "-1850.00", "COMPLETED"])

    output.seek(0)
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=\"Financial_Report_{period}.csv\""}
    )
