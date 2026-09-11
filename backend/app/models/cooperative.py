from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import date

class OrgType(str, Enum):
    SHG = "shg"
    COOPERATIVE = "cooperative"
    FPO = "fpo"
    CLUSTER_TRUST = "cluster_trust"

class MemberRole(str, Enum):
    LEADER = "leader"
    MANAGER = "manager"
    ACCOUNTANT = "accountant"
    MEMBER = "member"

class OrganizationCreate(BaseModel):
    name: str = Field(..., min_length=3)
    registration_number: str = Field(..., min_length=3)
    org_type: OrgType = Field(default=OrgType.SHG)
    state: str = "Odisha"
    district: str = "Puri"
    pincode: str = "752012"
    bank_account_info: Optional[Dict[str, Any]] = Field(default_factory=dict)
    revenue_split_rules: Optional[Dict[str, float]] = Field(default_factory=lambda: {
        "coop_reserve_fund_percent": 10.0,
        "labor_share_percent": 60.0,
        "material_reimbursement_percent": 30.0
    })

class MemberAddRequest(BaseModel):
    user_id: str
    full_name: str
    role: MemberRole = Field(default=MemberRole.MEMBER)
    craft_specialization: str
    share_percentage: float = Field(default=0.0, ge=0, le=100)

class MemberResponse(BaseModel):
    id: str
    org_id: str
    user_id: str
    full_name: str
    role: MemberRole
    craft_specialization: str
    share_percentage: float
    status: str
    joined_at: str

class OrganizationResponse(BaseModel):
    id: str
    name: str
    registration_number: str
    org_type: OrgType
    leader_id: str
    state: str
    district: str
    pincode: str
    member_count: int = 1
    total_pooled_items: int = 0
    bank_account_info: Dict[str, Any] = Field(default_factory=dict)
    revenue_split_rules: Dict[str, float] = Field(default_factory=dict)
    members: List[MemberResponse] = Field(default_factory=list)
    created_at: str

class SharedInventoryPoolRequest(BaseModel):
    product_id: str
    product_name: str
    quantity_pooled: int = Field(..., gt=0)
    unit_cost_inr: float = Field(..., gt=0)

class SharedInventoryResponse(BaseModel):
    id: str
    org_id: str
    product_id: str
    product_name: str
    contributing_member_id: str
    contributing_member_name: str
    quantity_pooled: int
    quantity_available: int
    unit_cost_inr: float
    status: str
    created_at: str

class TaskCreate(BaseModel):
    assigned_to_member_id: str
    assigned_to_name: str
    title: str
    description: str
    target_units: int = Field(..., gt=0)
    deadline: str

class TaskResponse(BaseModel):
    id: str
    org_id: str
    assigned_to_member_id: str
    assigned_to_name: str
    title: str
    description: str
    target_units: int
    completed_units: int
    deadline: str
    status: str
    created_at: str

class AttendanceLogRequest(BaseModel):
    member_id: str
    member_name: str
    work_date: Optional[str] = None
    status: str = "present"  # "present", "absent", "half_day"
    hours_logged: float = Field(default=8.0, ge=0, le=16)

class AttendanceResponse(BaseModel):
    id: str
    org_id: str
    member_id: str
    member_name: str
    work_date: str
    status: str
    hours_logged: float
    created_at: str

class MemberSplitItem(BaseModel):
    member_id: str
    member_name: str
    role: str
    payout_amount_inr: float
    labor_share_inr: float
    material_reimbursement_inr: float

class CalculatePayoutRequest(BaseModel):
    order_id: str
    total_order_amount_inr: float = Field(..., gt=0)
    participating_member_ids: List[str]

class PayoutSplitResponse(BaseModel):
    id: str
    org_id: str
    order_id: str
    total_order_amount_inr: float
    cooperative_fund_deduction_inr: float
    splits: List[MemberSplitItem]
    status: str
    created_at: str
