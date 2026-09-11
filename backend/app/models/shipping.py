from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ShipmentStatus(str, Enum):
    confirmed = "CONFIRMED"
    preparing = "PREPARING"
    packed = "PACKED"
    picked_up = "PICKED_UP"
    in_transit = "IN_TRANSIT"
    out_for_delivery = "OUT_FOR_DELIVERY"
    delivered = "DELIVERED"
    completed = "COMPLETED"
    cancelled = "CANCELLED"


class PickupType(str, Enum):
    pickup_available = "pickup_available"
    self_drop = "self_drop"


class PackageSize(str, Enum):
    small = "small"
    medium = "medium"
    large = "large"
    bulk = "bulk"


class CourierRankOption(BaseModel):
    courier_name: str
    courier_key: str
    estimated_cost: float
    estimated_days: int
    speed_rating: float  # 1.0 to 5.0
    reliability_score: float  # 0 to 100
    is_recommended: bool = False


class PackagingRecommendation(BaseModel):
    suggested_box_size: str
    is_fragile: bool
    fragile_label: str
    suggested_packing_material: str
    estimated_volumetric_weight: float
    instructions: str


class ShippingEstimateRequest(BaseModel):
    weight_kg: float = Field(..., gt=0, description="Gross physical weight in kg")
    length_cm: float = Field(..., gt=0, description="Length in cm")
    width_cm: float = Field(..., gt=0, description="Width in cm")
    height_cm: float = Field(..., gt=0, description="Height in cm")
    origin_pincode: str = Field(..., min_length=6, max_length=6)
    destination_pincode: str = Field(..., min_length=6, max_length=6)
    is_fragile: bool = False
    is_insured: bool = False
    is_cod: bool = False
    declared_value: float = Field(default=0.0, ge=0.0)
    courier_preference: Optional[str] = "india_post"


class ShippingEstimateResponse(BaseModel):
    estimated_cost: float
    estimated_delivery_days: int
    estimated_delivery_date: str
    package_size: PackageSize
    chargeable_weight_kg: float
    volumetric_weight_kg: float
    base_rate: float
    fragile_surcharge: float
    insurance_fee: float
    cod_fee: float
    courier_partner: str
    ranked_couriers: List[CourierRankOption] = []
    packaging_assistant: PackagingRecommendation
    pickup_available: bool
    self_drop_available: bool


class TrackingEventResponse(BaseModel):
    id: str
    shipment_id: str
    status: str
    location: str
    activity: str
    timestamp: datetime


class ShipmentCreateRequest(BaseModel):
    order_id: str
    origin_pincode: str
    destination_pincode: str
    weight_kg: float = 1.0
    length_cm: float = 20.0
    width_cm: float = 15.0
    height_cm: float = 10.0
    pickup_type: PickupType = PickupType.pickup_available
    courier_partner: Optional[str] = "India Post Speed Post"
    is_fragile: bool = False
    is_insured: bool = False
    is_cod: bool = False
    declared_value: float = 0.0


class ShipmentResponse(BaseModel):
    id: str
    order_id: str
    tracking_number: str
    courier_partner: str
    pickup_type: str
    status: str
    origin_pincode: str
    destination_pincode: str
    weight_kg: float
    package_size: str
    is_fragile: bool
    is_insured: bool
    is_cod: bool
    shipping_cost: float
    estimated_delivery_days: int
    label_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    tracking_events: List[TrackingEventResponse] = []


class TrackingResponse(BaseModel):
    tracking_number: str
    courier_partner: str
    current_status: str
    origin_pincode: str
    destination_pincode: str
    estimated_delivery_days: int
    map_coordinates: Dict[str, Any] = {"lat": 26.9124, "lng": 75.7873, "city": "Jaipur Hub"}
    timeline: List[TrackingEventResponse] = []
