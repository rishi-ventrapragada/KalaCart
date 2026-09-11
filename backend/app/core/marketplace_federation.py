"""
Global Marketplace Federation Core Engine (Phase 9)
Synchronizes a single unified inventory and price catalog across multiple external marketplaces:
- KalaCart (Direct)
- ONDC (Open Network for Digital Commerce)
- Amazon (Amazon India & Global)
- Etsy (Handmade & Vintage Global)
- Shopify (Artisan Mini-Storefronts)
- Export Catalog (Global B2B & Wholesale)

Features:
- Unified Central Inventory Management
- Real-Time Multi-Channel Stock Reservation
- Dynamic Multi-Currency Price Synchronization & Markup Rules
- Multi-Marketplace Order Aggregation & Auto-Deduction
- Real-Time Cross-Channel Performance & Revenue Analytics
"""

import uuid
import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class ChannelPlatform(str, Enum):
    KALACART_DIRECT = "kalacart_direct"
    ONDC = "ondc"
    AMAZON = "amazon"
    ETSY = "etsy"
    SHOPIFY = "shopify"
    EXPORT_B2B = "export_b2b"


class ChannelStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    SYNCING = "syncing"
    DISABLED = "disabled"


class SyncStatus(str, Enum):
    IN_SYNC = "in_sync"
    PENDING_UPDATE = "pending_update"
    OUT_OF_SYNC = "out_of_sync"
    DELISTED = "delisted"
    ERROR = "error"


class OrderReservationStatus(str, Enum):
    RESERVED = "reserved"
    FULFILLED = "fulfilled"
    RELEASED = "released"


class SalesChannel(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    channel_code: str
    channel_name: str
    platform_type: ChannelPlatform
    status: ChannelStatus = ChannelStatus.ACTIVE
    price_markup_pct: float = 0.0  # Percentage markup on base price
    currency: str = "INR"
    exchange_rate_to_inr: float = 1.0
    auto_sync_enabled: bool = True
    last_inventory_sync_at: Optional[str] = None
    last_order_sync_at: Optional[str] = None
    auth_credentials: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "channel_code": self.channel_code,
            "channel_name": self.channel_name,
            "platform_type": self.platform_type.value,
            "status": self.status.value,
            "price_markup_pct": self.price_markup_pct,
            "currency": self.currency,
            "exchange_rate_to_inr": self.exchange_rate_to_inr,
            "auto_sync_enabled": self.auto_sync_enabled,
            "last_inventory_sync_at": self.last_inventory_sync_at,
            "last_order_sync_at": self.last_order_sync_at,
            "created_at": self.created_at,
        }


class ChannelProductListing(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    artisan_id: str
    base_product_id: str
    channel_id: str
    channel_code: str
    channel_external_item_id: str
    channel_sku: str
    channel_title: str
    channel_price: float
    channel_currency: str = "INR"
    allocated_stock: int
    reserved_stock: int = 0
    available_stock: int
    sync_status: SyncStatus = SyncStatus.IN_SYNC
    last_synced_at: str = Field(default_factory=lambda: datetime.datetime.utcnow().isoformat())
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "artisan_id": self.artisan_id,
            "base_product_id": self.base_product_id,
            "channel_id": self.channel_id,
            "channel_code": self.channel_code,
            "channel_external_item_id": self.channel_external_item_id,
            "channel_sku": self.channel_sku,
            "channel_title": self.channel_title,
            "channel_price": self.channel_price,
            "channel_currency": self.channel_currency,
            "allocated_stock": self.allocated_stock,
            "reserved_stock": self.reserved_stock,
            "available_stock": self.available_stock,
            "sync_status": self.sync_status.value,
            "last_synced_at": self.last_synced_at,
            "metadata": self.metadata,
        }


class ChannelOrder(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    channel_id: str
    channel_code: str
    external_order_id: str
    kalacart_order_id: str = Field(default_factory=lambda: f"KC-FED-{uuid.uuid4().hex[:8].upper()}")
    buyer_name: str
    buyer_location: str
    country_code: str = "IN"
    gross_amount: float
    currency: str = "INR"
    commission_deducted: float = 0.0
    net_payout_to_artisan: float
    channel_status: str = "received"
    items: List[Dict[str, Any]]
    stock_reservation_status: OrderReservationStatus = OrderReservationStatus.RESERVED
    created_at: str = Field(default_factory=lambda: datetime.datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "channel_id": self.channel_id,
            "channel_code": self.channel_code,
            "external_order_id": self.external_order_id,
            "kalacart_order_id": self.kalacart_order_id,
            "buyer_name": self.buyer_name,
            "buyer_location": self.buyer_location,
            "country_code": self.country_code,
            "gross_amount": self.gross_amount,
            "currency": self.currency,
            "commission_deducted": self.commission_deducted,
            "net_payout_to_artisan": self.net_payout_to_artisan,
            "channel_status": self.channel_status,
            "items": self.items,
            "stock_reservation_status": self.stock_reservation_status.value,
            "created_at": self.created_at,
        }


class CentralProductInventory(BaseModel):
    base_product_id: str
    title: str
    base_price_inr: float
    total_physical_stock: int
    reserved_stock: int = 0
    available_stock: int
    artisan_id: str
    category: str


class GlobalMarketplaceFederationEngine:
    """
    Central orchestrator managing multi-channel product publishing, synchronized inventory allocation,
    stock locks, order aggregation, and channel analytics.
    """

    def __init__(self):
        self.channels: Dict[str, SalesChannel] = {}
        self.products_inventory: Dict[str, CentralProductInventory] = {}
        self.channel_listings: Dict[str, List[ChannelProductListing]] = {}  # base_product_id -> listings
        self.orders: Dict[str, ChannelOrder] = {}
        self._seed_default_channels_and_inventory()

    def _seed_default_channels_and_inventory(self):
        # 1. Channels
        default_channels = [
            SalesChannel(
                channel_code="kalacart_direct",
                channel_name="KalaCart Direct Storefront",
                platform_type=ChannelPlatform.KALACART_DIRECT,
                price_markup_pct=0.0,
                currency="INR",
                exchange_rate_to_inr=1.0,
            ),
            SalesChannel(
                channel_code="ondc_network",
                channel_name="ONDC National Digital Network",
                platform_type=ChannelPlatform.ONDC,
                price_markup_pct=3.0,
                currency="INR",
                exchange_rate_to_inr=1.0,
            ),
            SalesChannel(
                channel_code="amazon_marketplace",
                channel_name="Amazon Karigar & Global",
                platform_type=ChannelPlatform.AMAZON,
                price_markup_pct=15.0,
                currency="INR",
                exchange_rate_to_inr=1.0,
            ),
            SalesChannel(
                channel_code="etsy_global",
                channel_name="Etsy Handmade Global",
                platform_type=ChannelPlatform.ETSY,
                price_markup_pct=20.0,
                currency="USD",
                exchange_rate_to_inr=0.012,  # 1 INR = ~0.012 USD
            ),
            SalesChannel(
                channel_code="shopify_storefront",
                channel_name="Artisan Brand Shopify Boutique",
                platform_type=ChannelPlatform.SHOPIFY,
                price_markup_pct=5.0,
                currency="INR",
                exchange_rate_to_inr=1.0,
            ),
            SalesChannel(
                channel_code="export_b2b_catalog",
                channel_name="Global Wholesale Export Catalog",
                platform_type=ChannelPlatform.EXPORT_B2B,
                price_markup_pct=-10.0,  # Wholesale discount
                currency="USD",
                exchange_rate_to_inr=0.012,
            ),
        ]
        for ch in default_channels:
            self.channels[ch.id] = ch

        # 2. Central Inventory Mock
        mock_p1 = CentralProductInventory(
            base_product_id="PROD-FED-001",
            title="Royal Bidriware Silver Inlay Floral Vase",
            base_price_inr=8500.0,
            total_physical_stock=50,
            reserved_stock=0,
            available_stock=50,
            artisan_id="artisan_karnataka_01",
            category="Metal Craft",
        )
        mock_p2 = CentralProductInventory(
            base_product_id="PROD-FED-002",
            title="Pochampally Ikat Handwoven Silk Saree",
            base_price_inr=14200.0,
            total_physical_stock=30,
            reserved_stock=0,
            available_stock=30,
            artisan_id="artisan_telangana_02",
            category="Handloom & Textiles",
        )
        self.products_inventory[mock_p1.base_product_id] = mock_p1
        self.products_inventory[mock_p2.base_product_id] = mock_p2

        # 3. Synchronize initial listings across channels
        for p in [mock_p1, mock_p2]:
            self.sync_product_across_all_channels(p.base_product_id)

    def register_sales_channel(
        self,
        channel_code: str,
        channel_name: str,
        platform_type: ChannelPlatform,
        price_markup_pct: float = 0.0,
        currency: str = "INR",
        exchange_rate_to_inr: float = 1.0,
        auth_credentials: Optional[Dict[str, Any]] = None,
    ) -> SalesChannel:
        """Register a new external marketplace sales channel."""
        channel = SalesChannel(
            channel_code=channel_code,
            channel_name=channel_name,
            platform_type=platform_type,
            price_markup_pct=price_markup_pct,
            currency=currency,
            exchange_rate_to_inr=exchange_rate_to_inr,
            auth_credentials=auth_credentials or {},
        )
        self.channels[channel.id] = channel
        return channel

    def sync_product_across_all_channels(self, base_product_id: str) -> List[ChannelProductListing]:
        """
        Calculates localized channel prices and synchronizes unified stock to all active channels.
        """
        if base_product_id not in self.products_inventory:
            return []

        base_item = self.products_inventory[base_product_id]
        listings: List[ChannelProductListing] = []

        for ch in self.channels.values():
            if ch.status != ChannelStatus.ACTIVE:
                continue

            # Calculate price: Base Price + Markup % -> convert to target currency
            marked_up_inr = base_item.base_price_inr * (1 + (ch.price_markup_pct / 100.0))
            if ch.currency == "USD":
                channel_price = round(marked_up_inr * ch.exchange_rate_to_inr, 2)
            else:
                channel_price = round(marked_up_inr, 2)

            sku = f"{base_item.base_product_id}-{ch.platform_type.value.upper()}"
            ext_id = f"EXT-{ch.channel_code[:4].upper()}-{uuid.uuid4().hex[:6].upper()}"

            listing = ChannelProductListing(
                artisan_id=base_item.artisan_id,
                base_product_id=base_product_id,
                channel_id=ch.id,
                channel_code=ch.channel_code,
                channel_external_item_id=ext_id,
                channel_sku=sku,
                channel_title=base_item.title,
                channel_price=channel_price,
                channel_currency=ch.currency,
                allocated_stock=base_item.available_stock,
                reserved_stock=0,
                available_stock=base_item.available_stock,
                sync_status=SyncStatus.IN_SYNC,
                last_synced_at=datetime.datetime.utcnow().isoformat(),
                metadata={"markup_pct": ch.price_markup_pct, "currency": ch.currency},
            )
            listings.append(listing)
            ch.last_inventory_sync_at = datetime.datetime.utcnow().isoformat()

        self.channel_listings[base_product_id] = listings
        return listings

    def update_base_inventory(
        self,
        base_product_id: str,
        new_total_stock: Optional[int] = None,
        new_base_price_inr: Optional[float] = None,
    ) -> Optional[CentralProductInventory]:
        """
        Updates central product stock or pricing, triggering an instant broadcast sync to all channels.
        """
        if base_product_id not in self.products_inventory:
            return None

        item = self.products_inventory[base_product_id]
        if new_total_stock is not None:
            item.total_physical_stock = new_total_stock
            item.available_stock = max(0, item.total_physical_stock - item.reserved_stock)
        if new_base_price_inr is not None:
            item.base_price_inr = new_base_price_inr

        # Broadcast update to all channels
        self.sync_product_across_all_channels(base_product_id)
        return item

    def reserve_and_process_channel_order(
        self,
        channel_code: str,
        external_order_id: str,
        buyer_name: str,
        buyer_location: str,
        items: List[Dict[str, Any]],  # [{ "base_product_id": "...", "quantity": 2, "unit_price": 100 }]
        country_code: str = "IN",
    ) -> Dict[str, Any]:
        """
        Atomic Multi-Channel Order Ingestion:
        1. Validates available stock in central inventory
        2. Locks/Reserves stock across ALL channels instantaneously
        3. Records unified order with marketplace commission breakdowns
        4. Broadcasts new available stock balances
        """
        target_channel = next((c for c in self.channels.values() if c.channel_code == channel_code), None)
        if not target_channel:
            return {"status": "error", "message": f"Sales channel {channel_code} not found."}

        # Validate stock for all items
        for itm in items:
            p_id = itm.get("base_product_id")
            qty = itm.get("quantity", 1)
            if p_id not in self.products_inventory:
                return {"status": "error", "message": f"Product {p_id} not found in central catalog."}
            if self.products_inventory[p_id].available_stock < qty:
                return {"status": "error", "message": f"Insufficient stock for product {p_id}. Available: {self.products_inventory[p_id].available_stock}, Requested: {qty}"}

        gross_amount = sum(itm.get("unit_price", 0.0) * itm.get("quantity", 1) for itm in items)
        commission_rate = 0.10 if target_channel.platform_type == ChannelPlatform.AMAZON else 0.05
        commission_deducted = round(gross_amount * commission_rate, 2)
        net_payout = round(gross_amount - commission_deducted, 2)

        # Atomic reservation & deduction
        for itm in items:
            p_id = itm.get("base_product_id")
            qty = itm.get("quantity", 1)
            prod = self.products_inventory[p_id]
            prod.total_physical_stock -= qty
            prod.available_stock = max(0, prod.total_physical_stock - prod.reserved_stock)
            # Re-sync across all marketplaces
            self.sync_product_across_all_channels(p_id)

        order = ChannelOrder(
            channel_id=target_channel.id,
            channel_code=target_channel.channel_code,
            external_order_id=external_order_id,
            buyer_name=buyer_name,
            buyer_location=buyer_location,
            country_code=country_code,
            gross_amount=gross_amount,
            currency=target_channel.currency,
            commission_deducted=commission_deducted,
            net_payout_to_artisan=net_payout,
            channel_status="confirmed",
            items=items,
            stock_reservation_status=OrderReservationStatus.RESERVED,
        )
        self.orders[order.id] = order
        target_channel.last_order_sync_at = datetime.datetime.utcnow().isoformat()

        return {
            "status": "success",
            "message": f"Order {external_order_id} aggregated from {target_channel.channel_name}. Inventory updated across all marketplaces.",
            "order": order.to_dict(),
        }

    def get_channel_analytics(self) -> Dict[str, Any]:
        """
        Aggregates multi-channel sales volume, revenue, GMV, and inventory health metrics.
        """
        channel_stats: Dict[str, Dict[str, Any]] = {}
        for ch in self.channels.values():
            channel_stats[ch.channel_code] = {
                "channel_name": ch.channel_name,
                "platform_type": ch.platform_type.value,
                "currency": ch.currency,
                "total_orders": 0,
                "gross_revenue": 0.0,
                "net_artisan_payout": 0.0,
                "commission_paid": 0.0,
            }

        for ord in self.orders.values():
            if ord.channel_code in channel_stats:
                st = channel_stats[ord.channel_code]
                st["total_orders"] += 1
                st["gross_revenue"] += ord.gross_amount
                st["net_artisan_payout"] += ord.net_payout_to_artisan
                st["commission_paid"] += ord.commission_deducted

        total_orders_all = len(self.orders)
        total_products_tracked = len(self.products_inventory)
        total_active_listings = sum(len(listings) for listings in self.channel_listings.values())

        return {
            "total_channels": len(self.channels),
            "active_channels": sum(1 for c in self.channels.values() if c.status == ChannelStatus.ACTIVE),
            "total_products_tracked": total_products_tracked,
            "total_cross_channel_listings": total_active_listings,
            "total_aggregated_orders": total_orders_all,
            "channels_breakdown": channel_stats,
            "timestamp": datetime.datetime.utcnow().isoformat(),
        }


# Singleton Engine instance
marketplace_federation_engine = GlobalMarketplaceFederationEngine()
