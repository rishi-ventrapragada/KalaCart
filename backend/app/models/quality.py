"""Pydantic models for Pre-Dispatch Quality Verification Workflow (Phase 20).

Milestones:
  In Production -> Sample Uploaded -> Buyer Approved -> Dispatch Allowed
"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class QualityStatus(str, Enum):
    pending_submission = "pending_submission"
    sample_uploaded = "sample_uploaded"
    changes_requested = "changes_requested"
    buyer_approved = "buyer_approved"
    quality_rejected = "quality_rejected"


class QualityReviewAction(str, Enum):
    approve_sample = "approve_sample"
    request_changes = "request_changes"
    reject_quality = "reject_quality"
    approve_production = "approve_production"


class QualitySubmissionCreate(BaseModel):
    order_id: str
    product_photos: List[str] = Field(default_factory=list, description="Finished product photo URLs")
    packaging_photos: List[str] = Field(default_factory=list, description="Packaging & break-proof photo URLs")
    length_cm: float = Field(default=0.0, ge=0.0, description="Measured length in cm")
    width_cm: float = Field(default=0.0, ge=0.0, description="Measured width in cm")
    height_cm: float = Field(default=0.0, ge=0.0, description="Measured height in cm")
    weight_kg: float = Field(default=0.0, ge=0.0, description="Measured package weight in kg")
    seller_notes: Optional[str] = Field(default=None, max_length=1000)


class QualityReviewRequest(BaseModel):
    action: QualityReviewAction
    review_notes: Optional[str] = Field(default=None, max_length=1000)


class QualityVerificationResponse(BaseModel):
    id: str
    order_id: str
    status: QualityStatus
    status_label: str
    product_photos: List[str]
    packaging_photos: List[str]
    length_cm: float
    width_cm: float
    height_cm: float
    weight_kg: float
    dimensions_display: str
    weight_display: str
    seller_notes: Optional[str] = None
    buyer_notes: Optional[str] = None
    submitted_at: Optional[str] = None
    reviewed_at: Optional[str] = None
    dispatch_allowed: bool = False
