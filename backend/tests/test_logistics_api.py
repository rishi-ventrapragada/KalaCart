"""
Tests for Multi-Courier Real Logistics Integration (Phase 3).
"""

import os
os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("APP_ENV", "development")
os.environ.setdefault("SUPABASE_URL", "https://placeholder.supabase.co")

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import get_current_user

MOCK_USER = {
    "firebase_uid": "test-seller-uid-123",
    "email": "artisan@kalacart.in",
    "name": "Jaipur Craft Artisan",
    "artisan": {"id": "00000000-0000-0000-0000-000000000002"},
    "claims": {"uid": "test-seller-uid-123"}
}

def _override_user():
    return MOCK_USER

@pytest.fixture(autouse=True)
def setup_auth_override():
    app.dependency_overrides[get_current_user] = _override_user
    yield
    app.dependency_overrides[get_current_user] = _override_user

client = TestClient(app)


def test_list_courier_providers():
    res = client.get("/api/v1/shipping/providers")
    assert res.status_code == 200
    providers = res.json()
    assert len(providers) >= 4
    keys = [p["provider_key"] for p in providers]
    assert "SHIPROCKET" in keys
    assert "DELHIVERY" in keys
    assert "INDIA_POST" in keys
    assert "DTDC" in keys


def test_create_shipment_with_provider_awb():
    payload = {
        "order_id": "00000000-0000-0000-0000-000000000099",
        "origin_pincode": "302001",
        "destination_pincode": "560001",
        "weight_kg": 2.5,
        "length_cm": 30.0,
        "width_cm": 20.0,
        "height_cm": 15.0,
        "pickup_type": "pickup_available",
        "courier_partner": "SHIPROCKET",
        "is_fragile": True,
        "is_insured": True,
        "is_cod": False,
        "declared_value": 3500.0,
    }
    res = client.post("/api/v1/shipping/shipments", json=payload)
    assert res.status_code == 200, res.text
    data = res.json()
    assert "tracking_number" in data
    assert data["tracking_number"].startswith("SR")
    assert "Shiprocket" in data["courier_partner"]
    assert data["status"] == "CONFIRMED"


def test_schedule_doorstep_pickup():
    pickup_payload = {
        "shipment_id": "00000000-0000-0000-0000-000000000099",
        "courier_partner": "DELHIVERY",
        "pickup_date": "2026-09-08",
        "pickup_time_slot": "14:00 - 18:00",
        "pickup_address": "12 Craft Village Studio, Sanganer, Jaipur",
        "pickup_pincode": "302001",
        "contact_person": "Master Artisan Ram",
        "contact_phone": "+919876543210",
    }
    res = client.post("/api/v1/shipping/pickup", json=pickup_payload)
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["status"] == "SCHEDULED"
    assert data["provider_key"] == "DELHIVERY"
    assert data["pickup_number"].startswith("PKP-")


def test_track_shipment_timeline():
    trk_res = client.get("/api/v1/shipping/track/SR9876543210")
    assert trk_res.status_code == 200, trk_res.text
    trk_data = trk_res.json()
    assert trk_data["tracking_number"] == "SR9876543210"
    assert "timeline" in trk_data
    assert len(trk_data["timeline"]) >= 1
    assert "lat" in trk_data["map_coordinates"]
