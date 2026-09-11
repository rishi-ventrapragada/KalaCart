"""
Pydantic Models for KalaCart Phase 3: Seller Business Suite.
"""

from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ExpenseCategory(str, Enum):
    RAW_MATERIALS = "RAW_MATERIALS"
    WORKSHOP_RENT = "WORKSHOP_RENT"
    PACKAGING = "PACKAGING"
    TOOLS = "TOOLS"
    LABOUR = "LABOUR"
    UTILITIES = "UTILITIES"
    LOGISTICS = "LOGISTICS"
    OTHER = "OTHER"


class ExpenseCreate(BaseModel):
    category: ExpenseCategory
    title: str = Field(..., max_length=150)
    amount: float = Field(..., gt=0)
    expense_date: Optional[str] = None
    receipt_url: Optional[str] = None
    notes: Optional[str] = None


class ExpenseResponse(BaseModel):
    id: str
    artisan_id: str
    category: ExpenseCategory
    title: str
    amount: float
    expense_date: str
    receipt_url: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class CRMCustomerResponse(BaseModel):
    id: str
    artisan_id: str
    buyer_id: str
    buyer_name: str
    buyer_phone: Optional[str] = None
    buyer_email: Optional[str] = None
    delivery_city: Optional[str] = None
    delivery_state: Optional[str] = None
    total_orders: int
    lifetime_spend: float
    is_favorite: bool
    is_repeat_buyer: bool
    notes: Optional[str] = None
    last_order_date: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class CRMCustomerUpdate(BaseModel):
    is_favorite: Optional[bool] = None
    notes: Optional[str] = None


class PurchaseOrderCreate(BaseModel):
    supplier_name: str
    supplier_contact: Optional[str] = None
    total_cost: float
    expected_delivery_date: Optional[str] = None
    items: List[Dict[str, Any]] = []
    notes: Optional[str] = None


class PurchaseOrderResponse(BaseModel):
    id: str
    po_number: str
    artisan_id: str
    supplier_name: str
    supplier_contact: Optional[str] = None
    total_cost: float
    status: str
    expected_delivery_date: Optional[str] = None
    items: List[Dict[str, Any]] = []
    notes: Optional[str] = None
    created_at: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class SellerBusinessMetrics(BaseModel):
    gross_revenue: float
    total_expenses: float
    net_profit: float
    profit_margin_pct: float
    total_orders: int
    total_units_sold: int
    repeat_buyer_rate_pct: float
    low_stock_items_count: int
    recent_expenses: List[ExpenseResponse]
    top_repeat_customers: List[CRMCustomerResponse]
