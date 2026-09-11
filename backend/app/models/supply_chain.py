from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum

class MaterialCategory(str, Enum):
    BAMBOO = "bamboo"
    CLAY = "clay"
    BRASS = "brass"
    FABRIC = "fabric"
    LEATHER = "leather"
    NATURAL_DYES = "natural_dyes"

class SupplierResponse(BaseModel):
    id: str
    business_name: str
    contact_name: str
    phone: str
    email: str
    state: str
    city: str
    pincode: str
    rating: float
    total_orders_fulfilled: int
    quality_certified: bool
    is_verified: bool

class MaterialResponse(BaseModel):
    id: str
    supplier_id: str
    supplier_name: Optional[str] = None
    material_category: MaterialCategory
    title: str
    description: str
    purity_grade: str
    unit_type: str
    price_per_unit_inr: float
    minimum_order_qty: int
    available_stock: int
    in_stock: bool

class AIRecommendSuppliersRequest(BaseModel):
    material_category: MaterialCategory
    quantity: int = Field(..., gt=0)
    artisan_state: str = "Odisha"
    artisan_city: str = "Puri"
    prioritize: str = "balanced"  # "price", "distance", "quality", "speed", "balanced"

class RecommendedSupplierScore(BaseModel):
    supplier: SupplierResponse
    material: MaterialResponse
    composite_score: float  # 0 to 100
    price_score: float
    distance_score: float
    quality_score: float
    delivery_days: int
    estimated_logistics_cost_inr: float
    recommendation_reason: str

class AIRecommendSuppliersResponse(BaseModel):
    material_category: MaterialCategory
    recommended_suppliers: List[RecommendedSupplierScore]

class PurchaseRequestCreate(BaseModel):
    material_id: str
    quantity_requested: int = Field(..., gt=0)
    max_budget_inr: float = Field(..., gt=0)
    is_group_purchase: bool = False
    group_pool_id: Optional[str] = None
    delivery_location: str

class PurchaseRequestResponse(BaseModel):
    id: str
    artisan_id: str
    material_id: str
    quantity_requested: int
    max_budget_inr: float
    is_group_purchase: bool
    group_pool_id: Optional[str] = None
    delivery_location: str
    status: str
    created_at: str

class SupplierQuoteCreate(BaseModel):
    purchase_request_id: str
    quote_unit_price: float = Field(..., gt=0)
    estimated_delivery_days: int = Field(default=3, gt=0)
    quality_notes: Optional[str] = None

class SupplierQuoteResponse(BaseModel):
    id: str
    purchase_request_id: str
    supplier_id: str
    supplier_name: str
    quote_unit_price: float
    total_amount_inr: float
    estimated_delivery_days: int
    quality_notes: Optional[str] = None
    status: str
    created_at: str

class GroupPurchasePoolResponse(BaseModel):
    pool_id: str
    material_category: MaterialCategory
    cluster_name: str
    target_quantity: int
    current_pooled_quantity: int
    pool_completion_percent: float
    unlocked_discount_percent: float
    deadline_date: str
