from datetime import datetime, date
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class ClusterRole(str, Enum):
    admin = "admin"
    manager = "manager"
    artisan = "artisan"
    viewer = "viewer"


class MemberStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    suspended = "suspended"


class ClusterBase(BaseModel):
    name: str
    tagline: Optional[str] = None
    craft_type: str
    state: str
    district: str
    village: str
    description: str
    managed_by_entity: Optional[str] = "Artisan Cooperative"
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    banner_url: Optional[str] = None
    logo_url: Optional[str] = None


class ClusterCreate(ClusterBase):
    pass


class ClusterResponse(ClusterBase):
    id: str
    total_artisans: int = 0
    total_products: int = 0
    monthly_turnover: float = 0.0
    is_verified: bool = True
    created_at: datetime
    updated_at: datetime


class ClusterMemberCreate(BaseModel):
    artisan_name: str
    craft_specialty: str
    phone: Optional[str] = None
    role: ClusterRole = ClusterRole.artisan


class ClusterMemberResponse(BaseModel):
    id: str
    cluster_id: str
    artisan_id: str
    role: ClusterRole
    status: MemberStatus
    artisan_name: str
    craft_specialty: str
    phone: Optional[str] = None
    joined_at: datetime


class ClusterProductItem(BaseModel):
    id: str
    cluster_id: str
    product_id: str
    artisan_id: str
    artisan_name: str
    product_title: str
    price: float
    category: str
    image_url: Optional[str] = None
    is_featured: bool = False
    curated_at: datetime


class ClusterAddProductRequest(BaseModel):
    product_id: str
    is_featured: bool = False


class ClusterRFQCreate(BaseModel):
    craft_requirement: str
    quantity: int
    budget_target: float
    deadline: Optional[date] = None


class ClusterRFQResponse(BaseModel):
    id: str
    cluster_id: str
    buyer_id: str
    buyer_name: str
    craft_requirement: str
    quantity: int
    budget_target: float
    deadline: Optional[date] = None
    status: str
    created_at: datetime


class ClusterAnalytics(BaseModel):
    cluster_id: str
    cluster_name: str
    active_artisans: int
    total_catalogue_items: int
    monthly_sales_inr: float
    top_artisan_contributors: List[dict] = []
    top_selling_crafts: List[dict] = []
