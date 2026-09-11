"""
Tests for AI Sales Negotiation Agent (Phase 4).
Tests Real-time Suggested Replies, Tone Variations, Margin Protection, and Quote Calculations.
"""

import os
os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("APP_ENV", "development")
os.environ.setdefault("SUPABASE_URL", "https://placeholder.supabase.co")

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import get_current_user

MOCK_ARTISAN = {
    "firebase_uid": "test-artisan-uid-888",
    "email": "artisan@kalacart.in",
    "artisan": {"id": "00000000-0000-0000-0000-000000000002"},
    "claims": {"uid": "test-artisan-uid-888"}
}


@pytest.fixture(autouse=True)
def setup_auth_override():
    app.dependency_overrides[get_current_user] = lambda: MOCK_ARTISAN
    yield
    app.dependency_overrides.pop(get_current_user, None)


client = TestClient(app)


def test_suggested_replies_for_discount_inquiry():
    payload = {
        "product_title": "Jaipur Blue Pottery Hand-Painted Floral Vase",
        "listed_price": 1000.0,
        "buyer_message": "Can you do 900 for this vase?",
        "buyer_offered_price": 900.0,
        "material_cost": 350.0,
        "labor_cost": 200.0,
        "packaging_cost": 50.0,
    }
    res = client.post("/api/v1/negotiation/suggest-replies", json=payload)
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["buyer_target_price"] == 900.0
    assert data["is_loss_making_request"] is False
    assert len(data["suggestions"]) == 4

    tones = [s["tone"] for s in data["suggestions"]]
    assert "FRIENDLY" in tones
    assert "PROFESSIONAL" in tones
    assert "PREMIUM" in tones
    assert "URGENT" in tones

    # Verify all suggested prices yield positive net profit
    for s in data["suggestions"]:
        assert s["is_safe_margin"] is True
        assert s["projected_net_profit"] > 0
        assert s["profit_margin_pct"] > 0


def test_loss_making_offer_protection():
    # Listed ₹1,000 with total cost ~₹650, buyer asks for ₹300 (severe loss)
    payload = {
        "product_title": "Pochampally Silk Stole",
        "listed_price": 1000.0,
        "buyer_message": "Will take it for 300 only.",
        "buyer_offered_price": 300.0,
        "material_cost": 400.0,
        "labor_cost": 200.0,
        "packaging_cost": 50.0,
    }
    res = client.post("/api/v1/negotiation/suggest-replies", json=payload)
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["is_loss_making_request"] is True
    # Verify counter offers never drop below floor price
    for s in data["suggestions"]:
        assert s["proposed_price"] >= data["minimum_floor_price"]
        assert s["projected_net_profit"] > 0


def test_generate_itemized_quote():
    payload = {
        "product_title": "Bidriware Silver Inlay Box",
        "listed_price": 2500.0,
        "target_price": 2300.0,
        "quantity": 2,
        "material_cost": 750.0,
        "labor_cost": 450.0,
        "packaging_cost": 60.0,
    }
    res = client.post("/api/v1/negotiation/generate-quote", json=payload)
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["unit_price"] == 2300.0
    assert data["subtotal"] == 4600.0
    assert data["discount_amount"] == 400.0
    assert data["net_profit"] > 0
    assert data["is_profitable"] is True


def test_track_reply_usage():
    payload = {
        "suggested_text": "Namaste! For such a lovely craft order, I can do ₹940 including premium packaging.",
        "actual_sent_text": "Namaste! I can do ₹940 with packaging.",
        "tone": "FRIENDLY",
        "was_edited": True,
        "result_status": "SENT",
    }
    res = client.post("/api/v1/negotiation/track-usage", json=payload)
    assert res.status_code == 200, res.text
    assert res.json()["success"] is True
    assert res.json()["status"] == "LOGGED"
