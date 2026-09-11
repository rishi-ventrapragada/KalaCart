"""
Test Suite for Global Marketplace Federation (Phase 9)
Verifies:
- Cross-channel registration (KalaCart, ONDC, Amazon, Etsy, Shopify, Export)
- Multi-currency and markup pricing rules
- Unified central inventory synchronization
- Cross-marketplace order ingestion & atomic inventory deduction
- Real-time channel analytics
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_get_sales_channels():
    response = client.get("/api/v1/federation/channels")
    assert response.status_code == 200
    data = response.json()
    assert "count" in data
    assert "channels" in data
    assert data["count"] >= 5
    channel_codes = [c["channel_code"] for c in data["channels"]]
    assert "kalacart_direct" in channel_codes
    assert "ondc_network" in channel_codes
    assert "amazon_marketplace" in channel_codes
    assert "etsy_global" in channel_codes


def test_cross_channel_listings():
    response = client.get("/api/v1/federation/listings/PROD-FED-001")
    assert response.status_code == 200
    data = response.json()
    assert data["base_product_id"] == "PROD-FED-001"
    assert data["channel_count"] >= 5

    # Check that Etsy listing is in USD with markup
    etsy_listing = next((l for l in data["listings"] if l["channel_code"] == "etsy_global"), None)
    assert etsy_listing is not None
    assert etsy_listing["channel_currency"] == "USD"
    assert etsy_listing["channel_price"] > 0


def test_central_inventory_update_and_synchronization():
    # Update total stock of PROD-FED-001 to 80 units
    response = client.post(
        "/api/v1/federation/inventory/update",
        json={
            "base_product_id": "PROD-FED-001",
            "new_total_stock": 80,
            "new_base_price_inr": 9000.0,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["inventory"]["total_physical_stock"] == 80
    assert data["inventory"]["base_price_inr"] == 9000.0

    # Verify that all synchronized channel listings reflect the 80 units available stock
    for listing in data["synchronized_listings"]:
        assert listing["available_stock"] == 80


def test_cross_marketplace_order_ingestion_and_inventory_lock():
    # Ingest an order from Amazon for 5 units of PROD-FED-001
    order_payload = {
        "channel_code": "amazon_marketplace",
        "external_order_id": "AMZ-IN-9921-382910",
        "buyer_name": "Vikram Sethi",
        "buyer_location": "Bangalore, KA",
        "country_code": "IN",
        "items": [
            {
                "base_product_id": "PROD-FED-001",
                "quantity": 5,
                "unit_price": 10350.0,  # 9000 + 15% markup
            }
        ],
    }
    response = client.post("/api/v1/federation/orders/ingest", json=order_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    order_data = data["order"]
    assert order_data["external_order_id"] == "AMZ-IN-9921-382910"
    assert order_data["stock_reservation_status"] == "reserved"
    assert order_data["commission_deducted"] > 0

    # Verify that the central inventory for PROD-FED-001 is now deducted: 80 - 5 = 75
    listings_res = client.get("/api/v1/federation/listings/PROD-FED-001")
    assert listings_res.status_code == 200
    listings_data = listings_res.json()["listings"]
    for l in listings_data:
        assert l["available_stock"] == 75


def test_channel_analytics():
    response = client.get("/api/v1/federation/analytics")
    assert response.status_code == 200
    data = response.json()
    assert "total_channels" in data
    assert "total_products_tracked" in data
    assert "channels_breakdown" in data
    assert data["total_aggregated_orders"] >= 1
