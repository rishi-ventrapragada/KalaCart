from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class BuyerOrganizationType(str, Enum):
    HOTEL = "hotel"
    RESTAURANT = "restaurant"
    EXPORTER = "exporter"
    GOVERNMENT = "government"
    CORPORATE = "corporate"
    RETAIL_CHAIN = "retail_chain"
    OTHER = "other"

class TenderStatus(str, Enum):
    DRAFT = "draft"
    OPEN = "open"
    UNDER_EVALUATION = "under_evaluation"
    AWARDED = "awarded"
    CANCELLED = "cancelled"
    FULFILLED = "fulfilled"

class BidStatus(str, Enum):
    SUBMITTED = "submitted"
    SHORTLISTED = "shortlisted"
    REJECTED = "rejected"
    AWARDED = "awarded"

class ContractStatus(str, Enum):
    ACTIVE = "active"
    IN_PRODUCTION = "in_production"
    DISPATCHED = "dispatched"
    COMPLETED = "completed"
    DISPUTED = "disputed"
    TERMINATED = "terminated"

# --- Tenders / Procurements ---

class ProcurementCreate(BaseModel):
    buyer_organization_name: str = Field(..., min_length=2)
    buyer_type: BuyerOrganizationType = Field(default=BuyerOrganizationType.CORPORATE)
    title: str = Field(..., min_length=5, max_length=255)
    description: str = Field(..., min_length=10)
    category_id: Optional[str] = None
    target_quantity: int = Field(..., gt=0)
    target_unit_price: Optional[float] = Field(None, ge=0)
    max_budget: float = Field(..., gt=0)
    delivery_deadline: datetime
    delivery_location: str = Field(..., min_length=3)
    technical_specs: Optional[Dict[str, Any]] = Field(default_factory=dict)
    attachment_urls: Optional[List[str]] = Field(default_factory=list)

class ProcurementResponse(BaseModel):
    id: str
    buyer_id: str
    buyer_organization_name: str
    buyer_type: BuyerOrganizationType
    title: str
    description: str
    category_id: Optional[str] = None
    target_quantity: int
    target_unit_price: Optional[float] = None
    max_budget: float
    delivery_deadline: str
    delivery_location: str
    technical_specs: Dict[str, Any] = Field(default_factory=dict)
    attachment_urls: List[str] = Field(default_factory=list)
    status: TenderStatus
    bids_count: int = 0
    created_at: str
    updated_at: str

# --- Bids ---

class ProcurementBidCreate(BaseModel):
    artisan_business_name: str = Field(..., min_length=2)
    bid_unit_price: float = Field(..., gt=0)
    proposed_delivery_days: int = Field(..., gt=0)
    technical_proposal: str = Field(..., min_length=10)
    certificate_urls: Optional[List[str]] = Field(default_factory=list)
    sample_image_urls: Optional[List[str]] = Field(default_factory=list)

class BidEvaluationRequest(BaseModel):
    evaluation_score: float = Field(..., ge=0, le=100)
    evaluation_notes: Optional[str] = None
    status: Optional[BidStatus] = Field(default=BidStatus.SHORTLISTED)

class ProcurementBidResponse(BaseModel):
    id: str
    procurement_id: str
    artisan_id: str
    artisan_business_name: str
    bid_unit_price: float
    total_bid_amount: float
    proposed_delivery_days: int
    technical_proposal: str
    certificate_urls: List[str] = Field(default_factory=list)
    sample_image_urls: List[str] = Field(default_factory=list)
    evaluation_score: Optional[float] = None
    evaluation_notes: Optional[str] = None
    status: BidStatus
    created_at: str

# --- Award & Contracts ---

class AwardTenderRequest(BaseModel):
    bid_id: str
    contract_terms: Optional[Dict[str, Any]] = Field(default_factory=dict)

class Milestone(BaseModel):
    milestone_name: str
    percentage: float
    amount: float
    due_date: str
    status: str = "pending"

class ProcurementContractResponse(BaseModel):
    id: str
    procurement_id: str
    bid_id: str
    buyer_id: str
    artisan_id: str
    contract_number: str
    total_contract_value: float
    quantity_awarded: int
    unit_price: float
    contract_terms: Dict[str, Any] = Field(default_factory=dict)
    milestones: List[Milestone] = Field(default_factory=list)
    status: ContractStatus
    signed_at: str
    created_at: str
