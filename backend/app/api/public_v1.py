"""
KalaCart Public REST API v1 for Partners & Developers.
Exposes secure endpoints for Products, Stores, Orders, RFQs, Analytics, Payments, Notifications, and Reviews.
"""

import logging
import secrets
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.api_key_auth import RequirePublicApiAccess, create_partner_jwt
from app.models.common import ApiResponse
from app.models.public_api import (
    OAuthTokenRequest,
    OAuthTokenResponse,
    PublicProductItem,
    PublicProductCreate,
    PublicStoreProfile,
    PublicOrderCreate,
    PublicOrderResponse,
    PublicRFQCreate,
    PublicRFQResponse,
    PublicReviewCreate,
    PublicReviewResponse,
)
from app.services.webhook_service import trigger_webhook_event

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/public", tags=["Public API Platform"])

# Seed mock database catalogs for public sandbox
_PUBLIC_PRODUCTS: List[Dict[str, Any]] = [
    {
        "id": "prod-public-001",
        "title": "Jaipur Royal Cobalt Blue Floral Vase (12-inch)",
        "description": "Authentic quartz and copper oxide glazed terracotta vase hand-thrown by GI certified master potters.",
        "category": "Pottery & Ceramics",
        "price": 2899.0,
        "currency": "INR",
        "stock_quantity": 18,
        "artisan_id": "00000000-0000-0000-0000-000000000002",
        "artisan_name": "Master Artisan Ramesh Kumar",
        "craft_cluster": "Jaipur Blue Pottery Cluster",
        "gi_certified": True,
        "eco_score": 96,
        "image_url": "https://images.unsplash.com/photo-1578749556568-bc2c40e68b61?auto=format&fit=crop&q=80&w=600"
    },
    {
        "id": "prod-public-002",
        "title": "Pochampally Handwoven Double Ikat Silk Saree",
        "description": "Pure mulberry silk with geometric diamond weave dyed using organic madder root extracts.",
        "category": "Textiles & Handloom",
        "price": 8499.0,
        "currency": "INR",
        "stock_quantity": 8,
        "artisan_id": "00000000-0000-0000-0000-000000000003",
        "artisan_name": "Saraswathi Weavers Collective",
        "craft_cluster": "Telangana Ikat Cluster",
        "gi_certified": True,
        "eco_score": 98,
        "image_url": "https://images.unsplash.com/photo-1610030469983-98e550d6193c?auto=format&fit=crop&q=80&w=600"
    },
    {
        "id": "prod-public-003",
        "title": "Bastar Lost-Wax Cast Dhokra Tribal Bull Figurine",
        "description": "Ancient non-ferrous lost-wax metal casting crafted by indigenous artisans using recycled bell metal.",
        "category": "Metal Craft",
        "price": 3450.0,
        "currency": "INR",
        "stock_quantity": 12,
        "artisan_id": "00000000-0000-0000-0000-000000000004",
        "artisan_name": "Bastar Tribal Heritage Guild",
        "craft_cluster": "Chhattisgarh Dhokra Cluster",
        "gi_certified": True,
        "eco_score": 92,
        "image_url": "https://images.unsplash.com/photo-1590736969955-71cc94801759?auto=format&fit=crop&q=80&w=600"
    }
]

_PUBLIC_STORES: List[Dict[str, Any]] = [
    {
        "store_id": "store-001",
        "store_name": "Rajesh Heritage Blue Pottery",
        "slug": "rajesh-heritage-pottery",
        "artisan_name": "Ramesh Kumar & Sons",
        "craft_specialty": "Jaipur Glazed Ceramics",
        "location": "Jaipur, Rajasthan",
        "rating": 4.9,
        "total_reviews": 128,
        "verified_gi_artisan": True,
        "catalog_count": 24
    },
    {
        "store_id": "store-002",
        "store_name": "Pochampally Handloom Guild",
        "slug": "pochampally-weavers",
        "artisan_name": "Saraswathi Collective",
        "craft_specialty": "Double Ikat Silk & Cotton",
        "location": "Bhoodan Pochampally, Telangana",
        "rating": 4.95,
        "total_reviews": 312,
        "verified_gi_artisan": True,
        "catalog_count": 45
    }
]

_PUBLIC_ORDERS: List[Dict[str, Any]] = [
    {
        "order_id": "ord-2026-8812",
        "order_number": "KC-B2B-9812",
        "status": "in_production",
        "total_amount": 5798.0,
        "currency": "INR",
        "tracking_number": "BLUEDART-IND-9021",
        "created_at": "2026-09-06T14:20:00Z"
    }
]

_PUBLIC_RFQS: List[Dict[str, Any]] = [
    {
        "rfq_id": "rfq-2026-0044",
        "reference_code": "RFQ-BLR-2026-44",
        "status": "open_bidding",
        "craft_category": "Pottery & Ceramics",
        "quantity": 100,
        "created_at": "2026-09-06T10:00:00Z"
    }
]

_PUBLIC_REVIEWS: List[Dict[str, Any]] = [
    {
        "id": "rev-001",
        "product_id": "prod-public-001",
        "rating": 5,
        "review_title": "Exceptional Mastercraft Pottery",
        "review_text": "Flawless glaze finish, true to GI heritage standards. Secure export packaging.",
        "reviewer_name": "Vikram Sethi",
        "verified_purchase": True,
        "created_at": "2026-09-05T12:00:00Z"
    }
]


# ── OAuth2 Token Endpoint ──────────────────────────────────────────────────────────

@router.post("/oauth/token", response_model=OAuthTokenResponse)
async def generate_oauth_token(req: OAuthTokenRequest):
    """
    OAuth2 Client Credentials Grant.
    Exchanges partner client_id and client_secret for a signed JWT access token.
    """
    return create_partner_jwt(req.client_id, req.client_secret, req.scope)


# ── 1. Products API ────────────────────────────────────────────────────────────────

@router.get("/products", response_model=ApiResponse[List[PublicProductItem]])
async def list_public_products(
    category: Optional[str] = Query(None),
    gi_only: bool = Query(False),
    partner: Dict[str, Any] = Depends(RequirePublicApiAccess(["products:read"]))
):
    """List public handicraft catalog with GI certification and eco metrics."""
    res = _PUBLIC_PRODUCTS
    if category:
        res = [p for p in res if category.lower() in p["category"].lower()]
    if gi_only:
        res = [p for p in res if p.get("gi_certified")]
    return ApiResponse(success=True, message="Products retrieved", data=res)


@router.get("/products/{product_id}", response_model=ApiResponse[PublicProductItem])
async def get_public_product(
    product_id: str,
    partner: Dict[str, Any] = Depends(RequirePublicApiAccess(["products:read"]))
):
    """Get single product details."""
    for p in _PUBLIC_PRODUCTS:
        if p["id"] == product_id:
            return ApiResponse(success=True, message="Product details found", data=p)
    raise HTTPException(status_code=404, detail="Product not found")


@router.post("/products", response_model=ApiResponse[PublicProductItem], status_code=status.HTTP_201_CREATED)
async def create_public_product(
    body: PublicProductCreate,
    partner: Dict[str, Any] = Depends(RequirePublicApiAccess(["products:write"], require_signature=False))
):
    """Create a new product listing (requires products:write scope)."""
    new_id = f"prod-public-{secrets.token_hex(4)}"
    new_item = {
        "id": new_id,
        "title": body.title,
        "description": body.description,
        "category": body.category,
        "price": body.price,
        "currency": body.currency,
        "stock_quantity": body.stock_quantity,
        "artisan_id": partner.get("id", "00000000-0000-0000-0000-000000000002"),
        "artisan_name": partner.get("partner_name", "Partner Guild"),
        "craft_cluster": body.craft_cluster,
        "gi_certified": body.gi_certified,
        "eco_score": 94,
        "image_url": "https://images.unsplash.com/photo-1578749556568-bc2c40e68b61?auto=format&fit=crop&q=80&w=600"
    }
    _PUBLIC_PRODUCTS.insert(0, new_item)
    return ApiResponse(success=True, message="Product created successfully", data=new_item)


# ── 2. Stores API ──────────────────────────────────────────────────────────────────

@router.get("/stores", response_model=ApiResponse[List[PublicStoreProfile]])
async def list_public_stores(
    partner: Dict[str, Any] = Depends(RequirePublicApiAccess(["stores:read"]))
):
    """List verified artisan storefronts and guilds."""
    return ApiResponse(success=True, message="Stores retrieved", data=_PUBLIC_STORES)


@router.get("/stores/{slug}", response_model=ApiResponse[PublicStoreProfile])
async def get_public_store_by_slug(
    slug: str,
    partner: Dict[str, Any] = Depends(RequirePublicApiAccess(["stores:read"]))
):
    """Fetch artisan store profile by slug."""
    for s in _PUBLIC_STORES:
        if s["slug"] == slug:
            return ApiResponse(success=True, message="Store found", data=s)
    raise HTTPException(status_code=404, detail="Store not found")


# ── 3. Orders API ──────────────────────────────────────────────────────────────────

@router.get("/orders", response_model=ApiResponse[List[PublicOrderResponse]])
async def list_public_orders(
    partner: Dict[str, Any] = Depends(RequirePublicApiAccess(["orders:read"]))
):
    """List partner orders and escrow statuses."""
    return ApiResponse(success=True, message="Orders retrieved", data=_PUBLIC_ORDERS)


@router.post("/orders", response_model=ApiResponse[PublicOrderResponse], status_code=status.HTTP_201_CREATED)
async def create_public_order(
    body: PublicOrderCreate,
    partner: Dict[str, Any] = Depends(RequirePublicApiAccess(["orders:write"], require_signature=False))
):
    """Place a B2B order and trigger instant webhook notifications."""
    order_id = f"ord-{secrets.token_hex(4)}"
    order_num = f"KC-EXT-{secrets.token_hex(3).upper()}"
    new_order = {
        "order_id": order_id,
        "order_number": order_num,
        "status": "pending_escrow",
        "total_amount": 2899.0 * body.quantity,
        "currency": "INR",
        "tracking_number": f"IN-EXP-{secrets.token_hex(4).upper()}",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    _PUBLIC_ORDERS.insert(0, new_order)

    # Trigger webhook event
    await trigger_webhook_event("order.created", {
        "order_id": order_id,
        "order_number": order_num,
        "partner_name": partner.get("partner_name"),
        "total_amount": new_order["total_amount"],
        "buyer_email": body.buyer_email
    })

    return ApiResponse(success=True, message="Order created and webhook triggered", data=new_order)


# ── 4. RFQs API ───────────────────────────────────────────────────────────────────

@router.get("/rfqs", response_model=ApiResponse[List[PublicRFQResponse]])
async def list_public_rfqs(
    partner: Dict[str, Any] = Depends(RequirePublicApiAccess(["rfqs:read"]))
):
    """List open Request For Quotes (RFQs) across handicraft clusters."""
    return ApiResponse(success=True, message="RFQs retrieved", data=_PUBLIC_RFQS)


@router.post("/rfqs", response_model=ApiResponse[PublicRFQResponse], status_code=status.HTTP_201_CREATED)
async def create_public_rfq(
    body: PublicRFQCreate,
    partner: Dict[str, Any] = Depends(RequirePublicApiAccess(["rfqs:write"], require_signature=False))
):
    """Submit institutional RFQ to artisan cooperatives."""
    rfq_id = f"rfq-{secrets.token_hex(4)}"
    ref = f"RFQ-PUB-{secrets.token_hex(3).upper()}"
    new_rfq = {
        "rfq_id": rfq_id,
        "reference_code": ref,
        "status": "open_bidding",
        "craft_category": body.craft_category,
        "quantity": body.quantity,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    _PUBLIC_RFQS.insert(0, new_rfq)

    await trigger_webhook_event("rfq.received", {
        "rfq_id": rfq_id,
        "reference_code": ref,
        "craft_category": body.craft_category,
        "quantity": body.quantity,
        "company": body.company_name
    })

    return ApiResponse(success=True, message="RFQ published to verified artisan clusters", data=new_rfq)


# ── 5. Analytics API ───────────────────────────────────────────────────────────────

@router.get("/analytics", response_model=ApiResponse[Dict[str, Any]])
async def get_public_market_analytics(
    partner: Dict[str, Any] = Depends(RequirePublicApiAccess(["analytics:read"]))
):
    """Query high-level market demand, volume, and carbon intelligence statistics."""
    analytics_data = {
        "national_active_clusters": 48,
        "top_growing_crafts": [
            {"craft": "Jaipur Blue Pottery", "growth_rate_pct": 34.5},
            {"craft": "Bamboo Eco-Craft", "growth_rate_pct": 23.0},
            {"craft": "Pochampally Ikat", "growth_rate_pct": 27.8}
        ],
        "total_co2e_saved_kg": 42500.0,
        "verified_gi_artisans": 1420
    }
    return ApiResponse(success=True, message="Public analytics retrieved", data=analytics_data)


# ── 6. Payments API ────────────────────────────────────────────────────────────────

@router.post("/payments/create-intent", response_model=ApiResponse[Dict[str, Any]])
async def create_payment_intent(
    payload: Dict[str, Any],
    partner: Dict[str, Any] = Depends(RequirePublicApiAccess(["payments:write"], require_signature=False))
):
    """Initiate escrow payment intent for cross-border or domestic trade."""
    intent = {
        "payment_intent_id": f"pi_{secrets.token_hex(12)}",
        "client_secret": f"seti_{secrets.token_hex(16)}",
        "amount": payload.get("amount", 2899.0),
        "currency": payload.get("currency", "INR"),
        "escrow_guarantee": True,
        "status": "requires_payment_method"
    }
    return ApiResponse(success=True, message="Payment intent created", data=intent)


# ── 7. Notifications API ───────────────────────────────────────────────────────────

@router.post("/notifications", response_model=ApiResponse[Dict[str, Any]])
async def send_partner_notification(
    payload: Dict[str, Any],
    partner: Dict[str, Any] = Depends(RequirePublicApiAccess(["notifications:write"], require_signature=False))
):
    """Dispatch SMS / WhatsApp / Email notification to artisan cooperatives."""
    return ApiResponse(
        success=True,
        message="Notification queued for dispatch",
        data={
            "dispatch_id": f"disp-{secrets.token_hex(6)}",
            "channel": payload.get("channel", "WHATSAPP"),
            "status": "QUEUED",
            "recipient": payload.get("recipient", "+919876543210")
        }
    )


# ── 8. Reviews API ─────────────────────────────────────────────────────────────────

@router.get("/reviews", response_model=ApiResponse[List[PublicReviewResponse]])
async def get_public_reviews(
    product_id: Optional[str] = Query(None),
    partner: Dict[str, Any] = Depends(RequirePublicApiAccess(["reviews:read"]))
):
    """Fetch verified buyer reviews for GI crafts."""
    res = _PUBLIC_REVIEWS
    if product_id:
        res = [r for r in res if r["product_id"] == product_id]
    return ApiResponse(success=True, message="Reviews retrieved", data=res)


@router.post("/reviews", response_model=ApiResponse[PublicReviewResponse], status_code=status.HTTP_201_CREATED)
async def create_public_review(
    body: PublicReviewCreate,
    partner: Dict[str, Any] = Depends(RequirePublicApiAccess(["reviews:write"], require_signature=False))
):
    """Submit certified review for a purchased craft."""
    new_rev = {
        "id": f"rev-{secrets.token_hex(4)}",
        "product_id": body.product_id,
        "rating": body.rating,
        "review_title": body.review_title,
        "review_text": body.review_text,
        "reviewer_name": body.reviewer_name,
        "verified_purchase": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    _PUBLIC_REVIEWS.insert(0, new_rev)
    return ApiResponse(success=True, message="Review submitted successfully", data=new_rev)
