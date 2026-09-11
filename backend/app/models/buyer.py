"""Pydantic models for Buyer (inquiries/leads) domain."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class BuyerStatus(str, Enum):
    new = "new"
    contacted = "contacted"
    interested = "interested"
    converted = "converted"
    closed = "closed"


class BuyerBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Buyer name")
    phone: str = Field(..., pattern=r"^\+?[0-9]{10,15}$", description="Buyer phone (E.164)")
    location: Optional[str] = Field(default=None, max_length=200, description="Buyer location")
    product_interest: Optional[str] = Field(default=None, max_length=200, description="Product or category of interest")
    message: Optional[str] = Field(default=None, max_length=1000, description="Inquiry message")
    product_id: Optional[str] = Field(default=None, description="Related product UUID if inquiry is product-specific")
    status: BuyerStatus = Field(default=BuyerStatus.new, description="Lead status")

    @field_validator("name")
    @classmethod
    def _strip_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("name must not be empty")
        return v


class BuyerCreate(BuyerBase):
    """Payload for creating buyer inquiry."""
    pass


class BuyerUpdate(BaseModel):
    """Partial update for buyer."""

    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    phone: Optional[str] = Field(default=None, pattern=r"^\+?[0-9]{10,15}$")
    location: Optional[str] = Field(default=None, max_length=200)
    product_interest: Optional[str] = Field(default=None, max_length=200)
    message: Optional[str] = Field(default=None, max_length=1000)
    status: Optional[BuyerStatus] = None


class BuyerResponse(BuyerBase):
    id: str = Field(..., description="Buyer UUID")
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BuyerProfileBase(BaseModel):
    company_name: str = Field(..., min_length=1, max_length=200, description="Company name")
    business_type: Optional[str] = Field(default=None, max_length=100, description="Business type (e.g. Wholesaler, Exporter, Retailer)")
    business_category: Optional[str] = Field(default=None, max_length=100, description="Business category (e.g. Textiles, Pottery, Woodwork)")
    city: str = Field(..., min_length=1, max_length=100, description="City")
    state: str = Field(..., min_length=1, max_length=100, description="State")
    gst_number: Optional[str] = Field(default=None, max_length=15, description="GSTIN 15 characters")
    verification_status: str = Field(default="pending", description="Verification status (pending, verified, rejected)")
    minimum_order: Optional[int] = Field(default=None, ge=0, description="Minimum order quantity")
    required_quantity: Optional[int] = Field(default=None, ge=1, description="Required order quantity")
    logo_url: Optional[str] = Field(default=None, description="Logo URL")
    contact_phone: Optional[str] = Field(default=None, description="Contact phone")
    contact_email: Optional[str] = Field(default=None, description="Contact email")


class BuyerProfileResponse(BuyerProfileBase):
    id: str = Field(..., description="Buyer profile UUID")
    user_id: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
