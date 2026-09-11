"""
Pydantic data models for KalaCart Public API Platform, Developer Portal, Webhooks, and Security.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ApiScope(BaseModel):
    scope: str
    description: str
    category: str


class ApiKeyCreate(BaseModel):
    partner_name: str = Field(..., min_length=2, max_length=150)
    scopes: List[str] = Field(default_factory=lambda: ["products:read", "stores:read", "orders:read", "rfqs:read", "analytics:read", "reviews:read"])
    tier: str = Field(default="standard")  # 'standard', 'enterprise'


class ApiKeyResponse(BaseModel):
    id: str
    partner_name: str
    api_key_prefix: str
    raw_api_key: Optional[str] = None
    client_secret: Optional[str] = None
    scopes: List[str]
    tier: str
    rate_limit_per_min: int
    is_active: bool
    created_at: str
    last_used_at: Optional[str] = None


class OAuthTokenRequest(BaseModel):
    grant_type: str = Field(default="client_credentials")
    client_id: str
    client_secret: str
    scope: Optional[str] = None


class OAuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int = 86400
    scope: str


class WebhookCreate(BaseModel):
    target_url: str = Field(..., min_length=8, max_length=500)
    events: List[str] = Field(default_factory=lambda: ["order.created", "order.status_changed", "rfq.received"])


class WebhookResponse(BaseModel):
    id: str
    target_url: str
    secret_token: str
    events: List[str]
    is_active: bool
    failure_count: int
    last_triggered_at: Optional[str] = None
    created_at: str


class WebhookTestTrigger(BaseModel):
    event_type: str = "order.created"
    custom_payload: Optional[Dict[str, Any]] = None


class WebhookDeliveryResponse(BaseModel):
    id: str
    webhook_id: str
    event_type: str
    payload: Dict[str, Any]
    response_status: Optional[int] = None
    delivery_status: str
    signature: str
    delivered_at: str


class ApiUsageMetric(BaseModel):
    endpoint: str
    total_calls: int
    success_rate_pct: float
    avg_latency_ms: float
    p95_latency_ms: float


class ApiUsageDashboardResponse(BaseModel):
    total_requests_24h: int
    error_rate_pct: float
    rate_limit_remaining: int
    rate_limit_total: int
    endpoints: List[ApiUsageMetric]
    recent_logs: List[Dict[str, Any]]


# Public Entity Schema Models
class PublicProductItem(BaseModel):
    id: str
    title: str
    description: str
    category: str
    price: float
    currency: str = "INR"
    stock_quantity: int
    artisan_id: str
    artisan_name: str
    craft_cluster: str
    gi_certified: bool
    eco_score: int
    image_url: Optional[str] = None


class PublicProductCreate(BaseModel):
    title: str
    description: str
    category: str
    price: float
    currency: str = "INR"
    stock_quantity: int = 1
    craft_cluster: str = "Jaipur Pottery Cluster"
    gi_certified: bool = True
    materials: List[str] = Field(default_factory=lambda: ["Clay", "Natural Glaze"])


class PublicStoreProfile(BaseModel):
    store_id: str
    store_name: str
    slug: str
    artisan_name: str
    craft_specialty: str
    location: str
    rating: float
    total_reviews: int
    verified_gi_artisan: bool
    catalog_count: int


class PublicOrderCreate(BaseModel):
    product_id: str
    quantity: int = Field(default=1, ge=1)
    buyer_name: str
    buyer_email: str
    shipping_address: str
    delivery_city: str
    pincode: str
    payment_method: str = "ESCROW"


class PublicOrderResponse(BaseModel):
    order_id: str
    order_number: str
    status: str
    total_amount: float
    currency: str = "INR"
    tracking_number: Optional[str] = None
    created_at: str


class PublicRFQCreate(BaseModel):
    craft_category: str
    specifications: str
    quantity: int = Field(default=50, ge=1)
    target_budget_inr: float
    required_by_date: str
    company_name: str
    contact_email: str


class PublicRFQResponse(BaseModel):
    rfq_id: str
    reference_code: str
    status: str
    craft_category: str
    quantity: int
    created_at: str


class PublicReviewCreate(BaseModel):
    product_id: str
    rating: int = Field(..., ge=1, le=5)
    review_title: str
    review_text: str
    reviewer_name: str


class PublicReviewResponse(BaseModel):
    id: str
    product_id: str
    rating: int
    review_title: str
    review_text: str
    reviewer_name: str
    verified_purchase: bool
    created_at: str
