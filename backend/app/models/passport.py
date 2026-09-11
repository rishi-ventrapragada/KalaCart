from datetime import datetime, date
from typing import List, Optional
from pydantic import BaseModel, Field


class GICraftBase(BaseModel):
    gi_tag_number: str
    craft_name: str
    craft_category: str
    state: str
    district: str
    geographical_origin: str
    gi_registration_year: int
    certifying_authority: str = "Geographical Indications Registry of India"
    specification_summary: str
    authorized_materials: List[str] = []
    is_active: bool = True


class GICraftResponse(GICraftBase):
    id: str
    created_at: datetime
    updated_at: datetime


class CraftPassportBase(BaseModel):
    craft_id: str
    product_id: Optional[str] = None
    gi_craft_id: Optional[str] = None
    artisan_id: str
    artisan_name: str
    product_title: str
    craft_category: str
    craft_tradition: str
    village: str
    district: str
    state: str
    materials: List[str] = []
    creation_date: date = Field(default_factory=date.today)
    certificate_number: str
    care_instructions: Optional[str] = None
    is_verified: bool = True


class CraftPassportCreate(BaseModel):
    product_id: Optional[str] = None
    gi_tag_number: Optional[str] = None
    product_title: str
    craft_category: str
    craft_tradition: str
    village: str
    district: str
    state: str
    materials: List[str] = []
    care_instructions: Optional[str] = None


class CraftPassportResponse(CraftPassportBase):
    id: str
    qr_code_url: Optional[str] = None
    certificate_pdf_url: Optional[str] = None
    verification_url: str
    view_count: int = 0
    created_at: datetime
    updated_at: datetime


class CertificateResponse(BaseModel):
    id: str
    certificate_number: str
    passport_id: str
    craft_id: str
    issued_to_artisan: str
    craft_name: str
    gi_tag_number: Optional[str] = None
    issuing_authority: str = "KalaCart Heritage Provenance & GI Board"
    issue_date: date
    certificate_status: str = "valid"
    digital_signature_hash: str
    pdf_url: Optional[str] = None
    created_at: datetime


class VerificationResult(BaseModel):
    is_authentic: bool
    status_message: str
    passport: CraftPassportResponse
    gi_craft: Optional[GICraftResponse] = None
    certificate: Optional[CertificateResponse] = None
    verified_at: datetime


# --- Phase 2: Artisan Digital Craft Passport & Trust System Models ---

class ArtisanPassportCreate(BaseModel):
    photo_url: Optional[str] = None
    craft_title: str
    state: str
    district: str
    years_experience: int = 1
    gi_status: str = "Pending"  # 'Pending', 'Verified', 'Not_Applicable'
    awards: List[str] = []
    languages: List[str] = ["English", "Hindi"]


class ArtisanPassportResponse(BaseModel):
    id: str
    artisan_id: str
    artisan_name: Optional[str] = "Master Artisan"
    photo_url: Optional[str] = None
    craft_title: str
    state: str
    district: str
    years_experience: int
    gi_status: str
    awards: List[str] = []
    languages: List[str] = []
    verified_badge: bool = False
    trust_score: int = 50
    qr_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class GICertificateCreate(BaseModel):
    craft_name: str
    gi_tag_number: str
    certificate_url: str
    issuing_authority: Optional[str] = "Geographical Indications Registry of India"


class GICertificateResponse(BaseModel):
    id: str
    artisan_id: str
    craft_name: str
    gi_tag_number: str
    certificate_url: str
    issuing_authority: str
    is_valid: bool
    verified_at: datetime
    created_at: datetime


class TrustScoreBreakdown(BaseModel):
    artisan_id: str
    trust_score: int
    orders_score: float
    reviews_score: float
    response_score: float
    fulfillment_score: float
    follower_score: float
    profile_score: float
    completed_orders: int
    avg_rating: float
    response_time_mins: int
    fulfillment_rate: float
    follower_count: int
    profile_completion_pct: int
    is_verified: bool
    calculated_at: datetime
