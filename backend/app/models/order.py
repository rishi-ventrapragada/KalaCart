"""Pydantic models for Order, OrderItem, OrderStatusHistory, and Invoice domain."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class OrderStatus(str, Enum):
    rfq_accepted = "rfq_accepted"
    pending_advance = "pending_advance"
    seller_accepted = "seller_accepted"
    in_production = "in_production"
    quality_check = "quality_check"
    ready_to_dispatch = "ready_to_dispatch"
    shipped = "shipped"
    delivered = "delivered"
    completed = "completed"
    cancelled = "cancelled"
    disputed = "disputed"


class OrderItemBase(BaseModel):
    product_id: Optional[str] = None
    product_title: str = Field(..., min_length=1, max_length=255)
    product_image_url: Optional[str] = None
    unit_price: float = Field(..., ge=0)
    quantity: int = Field(default=1, ge=1, le=10000)
    subtotal: float = Field(..., ge=0)
    specifications: Optional[Dict[str, Any]] = None


class OrderItemCreate(OrderItemBase):
    pass


class OrderItemResponse(OrderItemBase):
    id: str
    order_id: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class OrderStatusHistoryResponse(BaseModel):
    id: str
    order_id: str
    from_status: Optional[OrderStatus] = None
    to_status: OrderStatus
    changed_by_id: str
    changed_by_role: str
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class InvoiceResponse(BaseModel):
    id: str
    invoice_number: str
    order_id: str
    buyer_id: str
    artisan_id: str
    invoice_date: datetime
    due_date: Optional[datetime] = None
    subtotal: float
    tax_amount: float
    shipping_amount: float
    total_amount: float
    paid_amount: float
    balance_due: float
    status: str
    pdf_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class OrderBase(BaseModel):
    buyer_name: str = Field(..., min_length=1, max_length=150)
    buyer_phone: str = Field(..., description="Buyer phone number")
    buyer_email: Optional[str] = None
    seller_name: str = Field(..., min_length=1, max_length=150)
    seller_phone: str = Field(..., description="Seller phone number")
    delivery_address: str = Field(..., min_length=5, max_length=1000)
    shipping_address: str = Field(..., min_length=5, max_length=1000)
    notes: Optional[str] = Field(default=None, max_length=1000)
    currency: str = Field(default="INR", max_length=10)


class OrderCreate(OrderBase):
    artisan_id: str = Field(..., description="Artisan ID receiving the order")
    rfq_id: Optional[str] = None
    quote_id: Optional[str] = None
    product_id: Optional[str] = None
    quantity: int = Field(default=1, ge=1, le=10000)
    unit_price: float = Field(..., ge=0)
    product_title: Optional[str] = "Artisan Product"
    product_image_url: Optional[str] = None
    advance_percentage: float = Field(default=30.0, ge=10.0, le=100.0)
    shipping_charges: float = Field(default=0.0, ge=0.0)
    coupon_code: Optional[str] = None
    reward_points_used: int = Field(default=0, ge=0)
    specifications: Optional[Dict[str, Any]] = None


class OrderStatusUpdate(BaseModel):
    status: OrderStatus
    notes: Optional[str] = Field(default=None, max_length=1000)


class OrderUpdate(OrderStatusUpdate):
    """Backwards-compatible alias for partial order updates."""
    quantity: Optional[int] = None
    total_price: Optional[float] = None
    buyer_address: Optional[str] = None


class OrderCancelRequest(BaseModel):
    reason: str = Field(..., min_length=3, max_length=1000)


class OrderDisputeRequest(BaseModel):
    reason: str = Field(..., min_length=5, max_length=1000)
    dispute_type: Optional[str] = "quality_issue"


class OrderResponse(OrderBase):
    id: str
    order_number: str
    buyer_id: str
    artisan_id: str
    rfq_id: Optional[str] = None
    quote_id: Optional[str] = None
    status: OrderStatus
    subtotal: float
    discount_amount: float = 0.0
    coupon_code: Optional[str] = None
    reward_points_used: int = 0
    gst_rate: float
    gst_amount: float
    shipping_charges: float
    total_amount: float
    advance_amount: float
    remaining_balance: float
    advance_paid: bool
    final_paid: bool
    cancel_reason: Optional[str] = None
    dispute_reason: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    items: List[OrderItemResponse] = []
    status_history: List[OrderStatusHistoryResponse] = []
    invoice: Optional[InvoiceResponse] = None

    class Config:
        from_attributes = True
