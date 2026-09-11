"""
Global Marketplace Federation API Router (Phase 9)
Exposes multi-channel inventory synchronization, price sync, cross-marketplace order aggregation,
and channel performance analytics.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

from app.core.marketplace_federation import (
    marketplace_federation_engine,
    ChannelPlatform,
    ChannelStatus,
)

router = APIRouter(prefix="/api/v1/federation", tags=["Global Marketplace Federation"])


class RegisterChannelRequest(BaseModel):
    channel_code: str
    channel_name: str
    platform_type: str = "custom"
    price_markup_pct: float = 0.0
    currency: str = "INR"
    exchange_rate_to_inr: float = 1.0
    auth_credentials: Dict[str, Any] = {}


class UpdateInventoryRequest(BaseModel):
    base_product_id: str
    new_total_stock: Optional[int] = None
    new_base_price_inr: Optional[float] = None


class ChannelOrderItemRequest(BaseModel):
    base_product_id: str
    quantity: int = 1
    unit_price: float


class IngestChannelOrderRequest(BaseModel):
    channel_code: str
    external_order_id: str
    buyer_name: str
    buyer_location: str
    country_code: str = "IN"
    items: List[ChannelOrderItemRequest]


@router.get("/channels")
async def get_sales_channels():
    """Retrieve all active and connected marketplace sales channels (KalaCart, ONDC, Amazon, Etsy, Shopify, Export)."""
    channels = [c.to_dict() for c in marketplace_federation_engine.channels.values()]
    return {"count": len(channels), "channels": channels}


@router.post("/channels/register")
async def register_sales_channel(req: RegisterChannelRequest):
    """Register a new external marketplace sales channel."""
    try:
        platform = ChannelPlatform(req.platform_type)
    except ValueError:
        platform = ChannelPlatform.KALACART_DIRECT

    channel = marketplace_federation_engine.register_sales_channel(
        channel_code=req.channel_code,
        channel_name=req.channel_name,
        platform_type=platform,
        price_markup_pct=req.price_markup_pct,
        currency=req.currency,
        exchange_rate_to_inr=req.exchange_rate_to_inr,
        auth_credentials=req.auth_credentials,
    )
    return {
        "status": "success",
        "message": f"Sales channel {channel.channel_name} registered.",
        "channel": channel.to_dict(),
    }


@router.get("/listings/{base_product_id}")
async def get_cross_channel_listings(base_product_id: str):
    """Get all synchronized marketplace listings and localized prices for a base product."""
    listings = marketplace_federation_engine.channel_listings.get(base_product_id, [])
    if not listings:
        # attempt sync if product exists in central inventory
        listings = marketplace_federation_engine.sync_product_across_all_channels(base_product_id)
    return {
        "base_product_id": base_product_id,
        "channel_count": len(listings),
        "listings": [l.to_dict() for l in listings],
    }


@router.post("/inventory/update")
async def update_central_inventory(req: UpdateInventoryRequest):
    """Update central inventory stock or price, auto-synchronizing all external sales channels."""
    updated_item = marketplace_federation_engine.update_base_inventory(
        base_product_id=req.base_product_id,
        new_total_stock=req.new_total_stock,
        new_base_price_inr=req.new_base_price_inr,
    )
    if not updated_item:
        raise HTTPException(status_code=404, detail=f"Product {req.base_product_id} not found in central catalog.")

    listings = marketplace_federation_engine.channel_listings.get(req.base_product_id, [])
    return {
        "status": "success",
        "message": f"Central inventory updated and synchronized to {len(listings)} sales channels.",
        "inventory": updated_item.model_dump(),
        "synchronized_listings": [l.to_dict() for l in listings],
    }


@router.post("/orders/ingest")
async def ingest_marketplace_order(req: IngestChannelOrderRequest):
    """Ingest an order from an external marketplace (Amazon, Etsy, ONDC, etc.), locking and deducting unified inventory."""
    items_data = [i.model_dump() for i in req.items]
    result = marketplace_federation_engine.reserve_and_process_channel_order(
        channel_code=req.channel_code,
        external_order_id=req.external_order_id,
        buyer_name=req.buyer_name,
        buyer_location=req.buyer_location,
        country_code=req.country_code,
        items=items_data,
    )
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("message"))
    return result


@router.get("/analytics")
async def get_marketplace_analytics():
    """Retrieve cross-channel analytics, gross sales, artisan payouts, and marketplace commission stats."""
    return marketplace_federation_engine.get_channel_analytics()
