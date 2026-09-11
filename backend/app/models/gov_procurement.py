from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class GovernmentBuyerRegister(BaseModel):
    organization_name: str = Field(..., description="Legal name of the entity, e.g. Ministry of Textiles, Tata CSR, Taj Group")
    buyer_type: str = Field(
        ...,
        description="government, ngo, csr, school, museum, tourism, hotel"
    )
    department: Optional[str] = Field(default=None, description="Department or division name")
    nodal_officer_name: str = Field(..., description="Procurement / nodal officer name")
    nodal_officer_email: str = Field(..., description="Official contact email")
    nodal_officer_phone: Optional[str] = Field(default=None, description="Contact phone number")
    pan_number: Optional[str] = Field(default=None, description="Organization PAN")
    gstin: Optional[str] = Field(default=None, description="GST Identification Number")
    gem_buyer_id: Optional[str] = Field(default=None, description="Government e-Marketplace (GeM) ID if applicable")
    csr_registration_number: Optional[str] = Field(default=None, description="CSR-1 or 80G/12A Registration number if CSR/NGO")
    allocated_annual_budget: float = Field(default=5000000.0, description="Annual craft procurement allocation in INR")


class GovernmentBuyerProfile(BaseModel):
    id: str
    user_id: str
    organization_name: str
    buyer_type: str
    department: Optional[str] = None
    nodal_officer_name: str
    nodal_officer_email: str
    nodal_officer_phone: Optional[str] = None
    pan_number: Optional[str] = None
    gstin: Optional[str] = None
    gem_buyer_id: Optional[str] = None
    csr_registration_number: Optional[str] = None
    verification_status: str
    allocated_annual_budget: float
    documents: List[Dict[str, Any]] = []
    created_at: str
    updated_at: str


class EligibilityCriteria(BaseModel):
    msme_only: bool = Field(default=False, description="Restrict to registered MSMEs")
    gi_priority: bool = Field(default=True, description="Priority points for Geographical Indication registered artisans")
    min_experience_years: int = Field(default=1, ge=0)
    cluster_state_preference: Optional[str] = Field(default=None, description="Preferred artisan state, e.g. Telangana, Rajasthan")
    shg_women_quota: bool = Field(default=False, description="Mandatory SHG / Women artisan quota")


class TenderDocumentCreate(BaseModel):
    title: str = Field(..., description="Tender RFP Title, e.g. Supply of 5,000 Pochampally Handloom Stoles")
    description: str = Field(..., description="Detailed scope of work and craft specifications")
    craft_category: str = Field(..., description="Textile, Pottery, Metal Art, Woodcraft, Painting, Bamboo Craft")
    target_quantity: int = Field(..., gt=0, description="Total units required")
    estimated_budget: float = Field(..., gt=0, description="Total estimated procurement value in INR")
    delivery_deadline: str = Field(..., description="ISO 8601 delivery deadline date")
    delivery_location: str = Field(..., description="Consignee delivery address & pin code")
    eligibility_criteria: EligibilityCriteria = Field(default_factory=EligibilityCriteria)
    technical_specs: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Dimensions, materials, GI compliance rules")
    document_urls: Optional[List[str]] = Field(default_factory=list, description="RFP and specs PDF URLs")


class TenderDocumentResponse(BaseModel):
    id: str
    tender_number: str
    buyer_id: str
    buyer_name: str
    buyer_type: str
    title: str
    description: str
    craft_category: str
    target_quantity: int
    estimated_budget: float
    delivery_deadline: str
    delivery_location: str
    eligibility_criteria: EligibilityCriteria
    technical_specs: Dict[str, Any] = {}
    document_urls: List[str] = []
    lifecycle_stage: str
    bids_count: int = 0
    created_at: str
    updated_at: str


class TenderBidCreate(BaseModel):
    artisan_business_name: str
    bid_unit_price: float = Field(..., gt=0)
    proposed_delivery_days: int = Field(..., gt=0)
    technical_proposal: str
    is_msme_registered: bool = True
    msme_udyam_number: Optional[str] = None
    is_gi_certified: bool = True
    gi_certificate_number: Optional[str] = None
    shg_member_count: int = 0


class TenderBidResponse(BaseModel):
    id: str
    tender_id: str
    artisan_id: str
    artisan_business_name: str
    bid_unit_price: float
    total_bid_amount: float
    proposed_delivery_days: int
    technical_proposal: str
    is_msme_registered: bool
    msme_udyam_number: Optional[str] = None
    is_gi_certified: bool
    gi_certificate_number: Optional[str] = None
    shg_member_count: int
    technical_score: float
    financial_score: float
    total_evaluation_score: float
    evaluation_notes: Optional[str] = None
    status: str
    created_at: str
    updated_at: str


class ContractAwardResponse(BaseModel):
    id: str
    contract_number: str
    tender_id: str
    buyer_id: str
    buyer_name: str
    artisan_id: str
    artisan_business_name: str
    artisan_is_msme: bool
    artisan_is_gi_certified: bool
    awarded_quantity: int
    awarded_unit_price: float
    total_contract_value: float
    evaluation_summary: Dict[str, Any]
    digital_contract_terms: Dict[str, Any]
    contract_pdf_url: Optional[str] = None
    buyer_signed: bool
    buyer_signed_at: Optional[str] = None
    artisan_signed: bool
    artisan_signed_at: Optional[str] = None
    status: str
    created_at: str
    updated_at: str


class MilestoneResponse(BaseModel):
    id: str
    contract_award_id: str
    milestone_index: int
    title: str
    percentage: float
    amount: float
    deliverable_description: str
    due_date: Optional[str] = None
    verification_doc_urls: List[str] = []
    status: str
    approved_by_buyer: bool
    approved_at: Optional[str] = None
    escrow_transaction_id: Optional[str] = None
    paid_at: Optional[str] = None
    created_at: str
    updated_at: str


class MilestoneActionRequest(BaseModel):
    action: str = Field(..., description="submit_proof, approve, release_payment, dispute")
    verification_doc_urls: Optional[List[str]] = Field(default=None, description="Uploaded proof documents")
    remarks: Optional[str] = Field(default=None, description="Approval notes or rejection reason")


class TenderEvaluationRequest(BaseModel):
    winning_bid_id: Optional[str] = None
    custom_terms: Optional[Dict[str, Any]] = None


class DigitalContractSignRequest(BaseModel):
    signer_role: str = Field(..., description="buyer or artisan")
    digital_signature_hash: Optional[str] = Field(default=None, description="Cryptographic signature token or Aadhaar eSign hash")
