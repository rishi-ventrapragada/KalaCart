"""
Pydantic Schemas for KalaCart Phase 3: Secure Payments & Escrow Architecture.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class PaymentGateway(str, Enum):
    RAZORPAY = "RAZORPAY"
    UPI = "UPI"
    STRIPE = "STRIPE"
    MOCK = "MOCK"


class PaymentMethod(str, Enum):
    UPI = "UPI"
    CARD = "CARD"
    NETBANKING = "NETBANKING"
    WALLET = "WALLET"


class PaymentStatus(str, Enum):
    PENDING = "PENDING"
    CAPTURED = "CAPTURED"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"
    PARTIALLY_REFUNDED = "PARTIALLY_REFUNDED"


class EscrowStatus(str, Enum):
    HELD_IN_ESCROW = "HELD_IN_ESCROW"
    FUNDS_LOCKED = "FUNDS_LOCKED"
    RELEASED_TO_SELLER = "RELEASED_TO_SELLER"
    REFUNDED_TO_BUYER = "REFUNDED_TO_BUYER"
    DISPUTED = "DISPUTED"
    PARTIALLY_REFUNDED = "PARTIALLY_REFUNDED"


class PayoutStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class RefundReason(str, Enum):
    ORDER_CANCELLED = "ORDER_CANCELLED"
    QUALITY_DEFECT = "QUALITY_DEFECT"
    DELIVERY_FAILED = "DELIVERY_FAILED"
    BUYER_REQUEST = "BUYER_REQUEST"
    PARTIAL_SETTLEMENT = "PARTIAL_SETTLEMENT"


class PaymentOrderCreate(BaseModel):
    order_id: str = Field(..., description="Internal Order UUID or Order Number")
    amount: float = Field(..., gt=0, description="Total amount in INR")
    currency: str = Field(default="INR", description="Currency ISO code")
    payment_method: PaymentMethod = Field(default=PaymentMethod.UPI)
    gateway: PaymentGateway = Field(default=PaymentGateway.RAZORPAY)
    buyer_email: Optional[str] = None
    buyer_phone: Optional[str] = None
    buyer_name: Optional[str] = None
    notes: Optional[Dict[str, Any]] = None


class PaymentOrderResponse(BaseModel):
    gateway_order_id: str
    order_id: str
    amount: float
    currency: str = "INR"
    key_id: str
    gateway: PaymentGateway
    prefill_name: Optional[str] = None
    prefill_email: Optional[str] = None
    prefill_contact: Optional[str] = None
    theme_color: str = "#8D4B08"


class PaymentVerifyRequest(BaseModel):
    order_id: str
    gateway_order_id: str
    gateway_payment_id: str
    gateway_signature: str
    payment_method: Optional[PaymentMethod] = PaymentMethod.UPI


class PaymentResponse(BaseModel):
    id: str
    order_id: str
    buyer_id: str
    seller_id: str
    gateway: PaymentGateway
    payment_method: PaymentMethod
    gateway_order_id: Optional[str] = None
    gateway_payment_id: Optional[str] = None
    amount: float
    currency: str = "INR"
    status: PaymentStatus
    payment_type: str = "FULL"
    created_at: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class EscrowStatusResponse(BaseModel):
    id: str
    order_id: str
    buyer_id: str
    artisan_id: str
    total_held_amount: float
    released_amount: float
    refunded_amount: float
    platform_fee: float
    artisan_payout_amount: float
    escrow_status: EscrowStatus
    locked_at: Optional[str] = None
    released_at: Optional[str] = None
    notes: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class ReleaseEscrowRequest(BaseModel):
    order_id: str
    reason: Optional[str] = "Buyer confirmed delivery and inspection"


class RefundRequest(BaseModel):
    order_id: str
    refund_amount: Optional[float] = Field(None, gt=0, description="Amount to refund, defaults to full order amount")
    refund_reason: RefundReason = Field(default=RefundReason.ORDER_CANCELLED)
    detailed_reason: Optional[str] = None


class RefundResponse(BaseModel):
    id: str
    refund_number: str
    order_id: str
    refund_amount: float
    refund_reason: str
    refund_type: str
    status: str
    gateway_refund_id: Optional[str] = None
    created_at: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class PayoutResponse(BaseModel):
    id: str
    payout_number: str
    artisan_id: str
    order_id: str
    amount: float
    currency: str = "INR"
    payout_method: str
    status: PayoutStatus
    gateway_transfer_id: Optional[str] = None
    processed_at: Optional[str] = None
    created_at: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)
