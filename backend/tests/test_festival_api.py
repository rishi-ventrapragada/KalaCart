"""Tests for Festival Demand Predictor (Phase 19)."""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_get_upcoming_opportunity():
    res = client.get("/api/v1/festival/upcoming")
    assert res.status_code == 200
    data = res.json()
    assert "festival_name" in data
    assert "days_remaining" in data
    assert "demand_surge_pct" in data
    assert data["demand_surge_pct"] > 0
    assert len(data["recommended_products"]) > 0
    assert "promotional_poster" in data


def test_get_diwali_prediction():
    res = client.get("/api/v1/festival/prediction/diwali")
    assert res.status_code == 200
    data = res.json()
    assert "Diwali" in data["festival_name"]
    assert data["demand_surge_pct"] >= 200
    # Check recommended products have stock and price guidance
    for rec in data["recommended_products"]:
        assert rec["recommended_stock"] > rec["current_stock"]
        assert rec["suggested_price"] >= rec["current_price"]
        assert rec["price_adjustment_pct"] > 0


def test_list_festivals():
    res = client.get("/api/v1/festival/list")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 6
    fest_keys = [f["key"] for f in data]
    assert "diwali" in fest_keys
    assert "pongal" in fest_keys
    assert "sankranti" in fest_keys
    assert "dussehra" in fest_keys
    assert "christmas" in fest_keys
    assert "eid" in fest_keys


def test_generate_poster():
    req = {
        "festival_key": "diwali",
        "artisan_name": "Ramesh Prajapat",
        "product_category": "Blue Pottery & Diyas",
        "discount_pct": 20
    }
    res = client.post("/api/v1/festival/generate-poster", json=req)
    assert res.status_code == 200
    data = res.json()
    assert "Ramesh Prajapat" in data["headline"]
    assert "20%" in data["offer_text"]
    assert len(data["hashtags"]) > 0
    assert len(data["suggested_caption"]) > 20
