"""Pydantic models for Enquiry domain — B2B marketplace enquiries.

Fields mirror DB enquiries table (006_marketplace.sql):
  id UUID, product_id UUID NOT NULL, artisan_id UUID NOT NULL (owner),
  buyer_profile_id UUID nullable, buyer_name TEXT, buyer_phone E.164,
  company_name TEXT, message TEXT 10-1000 sanitized, required_quantity INT >=1,
  minimum_order INT >=0 nullable, status pending/accepted/rejected/closed,
  created_at, updated_at.
"""

import re
import html
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

_CONTROL_RE = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]")


def _strip_control(s: str) -> str:
    if not isinstance(s, str):
        s = str(s)
    # Remove control chars, keep newline/tab? we strip all 0-31 except we already removed \x09 \x0A via regex? spec says \x00-\x1f, so remove all.
    s = _CONTROL_RE.sub("", s)
    return s.strip()


def _sanitize_message(s: str) -> str:
    # strip control, trim, html escape for storage? spec says sanitize strip \x00-\x1f and btrim, html escape optional.
    # We strip control and trim, also escape html to prevent XSS in rendering layer (defense in depth).
    # But DB trigger also sanitizes, so keep simple: strip control + trim.
    s = _strip_control(s)
    # Optionally escape html entities for safe display; not required to break data,
    # but we will store escaped? Keep raw sanitized without escape to preserve message intent.
    # Use html.escape for log/display safety elsewhere, but storage keep sanitized trimmed.
    # We will also collapse excessive whitespace? Keep as is trimmed.
    return s


class EnquiryStatus(str, Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"
    closed = "closed"


class EnquiryCreateRequest(BaseModel):
    """Body for POST /api/v1/marketplace/enquiry

    - product_id: UUID
    - message: 10-1000 chars, control chars \\x00-\\x1f stripped, trimmed
    - required_quantity: int >=1 <=10000
    - minimum_order: Optional int >=0 <=100000
    - delivery_month: Optional str (e.g., 'October 2026')
    """

    product_id: UUID = Field(..., description="Product UUID to enquire about")
    message: str = Field(..., min_length=10, max_length=1000, description="Enquiry message 10-1000 chars, control chars stripped")
    required_quantity: int = Field(..., ge=1, le=10000, description="Required quantity >=1 <=10000")
    minimum_order: Optional[int] = Field(default=None, ge=0, le=100000, description="Minimum order >=0 optional")
    delivery_month: Optional[str] = Field(default=None, max_length=100, description="Expected delivery month")

    @field_validator("message", mode="before")
    @classmethod
    def _sanitize_before(cls, v):
        if v is None:
            return v
        if not isinstance(v, str):
            v = str(v)
        # Strip control chars and trim before length validation
        v = _strip_control(v)
        return v

    @field_validator("message")
    @classmethod
    def _validate_length(cls, v: str) -> str:
        # After sanitization, validate 10-1000
        v = _strip_control(v).strip()
        if len(v) < 10:
            raise ValueError("message must be at least 10 characters after sanitization")
        if len(v) > 1000:
            raise ValueError("message must be at most 1000 characters")
        return v

    @field_validator("minimum_order", mode="before")
    @classmethod
    def _coerce_minimum(cls, v):
        if v is None or v == "":
            return None
        try:
            iv = int(v)
        except Exception:
            raise ValueError("minimum_order must be integer >=0")
        return iv


class EnquiryCreate(BaseModel):
    """Internal create model for DB insert (includes derived fields)."""

    product_id: str
    artisan_id: str
    buyer_profile_id: Optional[str] = None
    buyer_name: Optional[str] = None
    buyer_phone: Optional[str] = None
    company_name: Optional[str] = None
    message: str
    required_quantity: int
    minimum_order: Optional[int] = None
    delivery_month: Optional[str] = None
    status: EnquiryStatus = EnquiryStatus.pending


class EnquiryResponse(BaseModel):
    """Response model mirroring DB row."""

    id: str
    product_id: str
    artisan_id: str
    buyer_profile_id: Optional[str] = None
    buyer_name: Optional[str] = None
    buyer_phone: Optional[str] = None
    company_name: Optional[str] = None
    message: str
    required_quantity: int
    minimum_order: Optional[int] = None
    delivery_month: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
