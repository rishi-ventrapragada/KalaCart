"""
Test Suite for Global Trade Intelligence (KalaCart V10)
Verifies:
- Live multi-currency foreign exchange rates against INR
- Foreign currency rate updates and 24h trend analytics
- AI-ranked export target country recommendations
- World trade heatmap generation and corridor analytics
- Historical country-level trade and buyer inquiry trends
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_get_live_exchange_rates():
    response = client.get("/api/v1/trade-intelligence/exchange-rates")
    assert response.status_code == 200
    data = response.json()
    assert data["base_currency"] == "INR"
    assert data["count"] >= 5
    currencies = [r["currency_code"] for r in data["rates"]]
    assert "USD" in currencies
    assert "EUR" in currencies
    assert "GBP" in currencies
    assert "AED" in currencies


def test_update_exchange_rate():
    update_payload = {
        "currency_code": "USD",
        "exchange_rate_to_inr": 84.15,
        "trend_24h_pct": 0.35,
    }
    response = client.post("/api/v1/trade-intelligence/exchange-rates/update", json=update_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["rate"]["currency_code"] == "USD"
    assert data["rate"]["exchange_rate_to_inr"] == 84.15
    assert data["rate"]["trend_24h_pct"] == 0.35


def test_get_country_export_recommendations():
    # 1. General recommendations
    response = client.get("/api/v1/trade-intelligence/recommendations")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] >= 4
    top_country = data["recommendations"][0]
    assert "market_attractiveness_score" in top_country
    assert top_country["market_attractiveness_score"] >= 90.0

    # 2. Filtered recommendations by craft category
    silk_res = client.get("/api/v1/trade-intelligence/recommendations?craft_category=Silk")
    assert silk_res.status_code == 200
    silk_data = silk_res.json()
    assert silk_data["count"] >= 1
    assert "Silk" in silk_data["recommendations"][0]["craft_category"]


def test_world_trade_heatmap():
    response = client.get("/api/v1/trade-intelligence/heatmap")
    assert response.status_code == 200
    data = response.json()
    assert data["total_countries_tracked"] >= 4
    assert "US" in data["heatmap_data"]
    assert "DE" in data["heatmap_data"]
    assert "AE" in data["heatmap_data"]
    assert data["heatmap_data"]["AE"]["free_trade_agreement"] is True


def test_get_country_trend_data():
    response = client.get("/api/v1/trade-intelligence/countries/US/trends")
    assert response.status_code == 200
    data = response.json()
    assert data["country_code"] == "US"
    assert len(data["monthly_trends"]) >= 1
    assert data["monthly_trends"][0]["buyer_inquiries_count"] > 0
