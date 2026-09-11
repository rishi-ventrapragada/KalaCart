from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum

class BecknDomain(str, Enum):
    RET12 = "ONDC:RET12"  # Home & Decor / Handicrafts
    RET10 = "ONDC:RET10"  # Grocery
    RET14 = "ONDC:RET14"  # Electronics

class ONDCOrderState(str, Enum):
    CREATED = "Created"
    ACCEPTED = "Accepted"
    IN_PROGRESS = "In-progress"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"

class ONDCPublishProductRequest(BaseModel):
    product_id: str
    product_name: str
    product_description: str
    price_inr: float = Field(..., gt=0)
    stock_quantity: int = Field(..., ge=0)
    category_id: str = "Handicrafts & Handlooms"
    artisan_cluster_location: str = "Puri, Odisha"
    time_to_ship_days: int = Field(default=3, gt=0)
    image_urls: List[str] = Field(default_factory=list)

class BecknDescriptor(BaseModel):
    name: str
    code: str
    symbol: Optional[str] = None
    short_desc: str
    long_desc: str
    images: List[str] = Field(default_factory=list)

class BecknItem(BaseModel):
    id: str
    parent_item_id: Optional[str] = None
    descriptor: BecknDescriptor
    price: Dict[str, Any]
    category_id: str
    fulfillment_id: str = "F1"
    location_id: str = "L1"
    time_to_ship: str = "P3D"
    matched: bool = True
    tags: List[Dict[str, Any]] = Field(default_factory=list)

class ONDCBecknCatalogPayload(BaseModel):
    bpp_id: str
    bpp_uri: str
    domain: str = "ONDC:RET12"
    items: List[BecknItem]
    sync_timestamp: str

class ONDCProductResponse(BaseModel):
    id: str
    product_id: str
    network_item_id: str
    domain: str
    bpp_id: str
    bpp_uri: str
    descriptor_name: str
    descriptor_code: str
    category_id: str
    fulfillment_id: str
    location_id: str
    time_to_ship_days: int
    is_published: bool
    sync_status: str
    last_synced_at: str
    beckn_payload: Optional[BecknItem] = None

class ONDCInventorySyncRequest(BaseModel):
    product_id: str
    new_stock_quantity: int = Field(..., ge=0)

class ONDCInventorySyncResponse(BaseModel):
    product_id: str
    network_item_id: str
    synced_stock_quantity: int
    is_available_on_network: bool
    sync_status: str
    updated_at: str

class ONDCIncomingOrderRequest(BaseModel):
    network_order_id: str
    bap_id: str
    bap_uri: str
    transaction_id: str
    message_id: str
    network_item_id: str
    quantity: int = Field(..., gt=0)
    unit_price_inr: float = Field(..., gt=0)
    buyer_name: str
    buyer_phone: str
    delivery_address: str
    delivery_pincode: str

class ONDCOrderResponse(BaseModel):
    id: str
    network_order_id: str
    kalacart_order_id: Optional[str] = None
    bap_id: str
    bap_uri: str
    transaction_id: str
    message_id: str
    total_value_inr: float
    state: ONDCOrderState
    fulfillment_status: str
    cancellation_reason_code: Optional[str] = None
    return_status: Optional[str] = None
    created_at: str
    updated_at: str

class ONDCCancellationRequest(BaseModel):
    cancellation_reason_code: str = "001"  # "001": Buyer changed mind, "002": Delayed fulfillment
    cancellation_description: Optional[str] = None

class ONDCReturnRequest(BaseModel):
    return_reason_code: str = "003"  # "003": Damaged item in transit
    return_description: str

class ONDCSyncLogResponse(BaseModel):
    id: str
    sync_type: str
    entity_id: str
    status: str
    request_payload: Dict[str, Any]
    response_payload: Dict[str, Any]
    error_message: Optional[str] = None
    created_at: str
