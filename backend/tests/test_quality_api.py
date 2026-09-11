"""Tests for Quality Verification Workflow (Phase 20)."""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import get_current_user

client = TestClient(app)

ORDER_ID = "ord-quality-test-101"

MOCK_USER = {
    "firebase_uid": "uid_test_artisan_1",
    "phone": "+919876543210",
    "artisan": {
        "id": "11111111-1111-1111-1111-111111111111",
        "name": "Ramesh Artisan",
        "phone": "+919876543210",
        "firebase_uid": "uid_test_artisan_1",
    },
    "claims": {"uid": "uid_test_artisan_1"},
}

HEADERS = {"Authorization": "Bearer mock_token"}


@pytest.fixture(autouse=True)
def override_user():
    app.dependency_overrides[get_current_user] = lambda: MOCK_USER
    yield
    app.dependency_overrides.pop(get_current_user, None)


def test_submit_quality_dossier():
    payload = {
        "order_id": ORDER_ID,
        "product_photos": [
            "https://storage.kalacart.com/products/sample1.jpg",
            "https://storage.kalacart.com/products/sample2.jpg"
        ],
        "packaging_photos": [
            "https://storage.kalacart.com/packages/box1.jpg"
        ],
        "length_cm": 25.5,
        "width_cm": 15.0,
        "height_cm": 10.0,
        "weight_kg": 1.25,
        "seller_notes": "Finished handmade wooden carving with protective eco packaging."
    }
    res = client.post(f"/api/v1/quality/orders/{ORDER_ID}/submit", json=payload, headers=HEADERS)
    assert res.status_code == 201
    data = res.json()
    assert data["order_id"] == ORDER_ID
    assert data["status"] == "sample_uploaded"
    assert len(data["product_photos"]) == 2
    assert len(data["packaging_photos"]) == 1
    assert data["length_cm"] == 25.5
    assert data["weight_kg"] == 1.25
    assert data["dispatch_allowed"] is False


def test_get_quality_dossier():
    res = client.get(f"/api/v1/quality/orders/{ORDER_ID}", headers=HEADERS)
    assert res.status_code == 200
    data = res.json()
    assert data["order_id"] == ORDER_ID
    assert data["status"] == "sample_uploaded"
    assert data["seller_notes"] == "Finished handmade wooden carving with protective eco packaging."


def test_buyer_request_changes():
    review_payload = {
        "action": "request_changes",
        "review_notes": "Please add more bubble wrap / eco-cushioning around the delicate edges."
    }
    res = client.post(f"/api/v1/quality/orders/{ORDER_ID}/review", json=review_payload, headers=HEADERS)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "changes_requested"
    assert data["dispatch_allowed"] is False
    assert data["buyer_notes"] == "Please add more bubble wrap / eco-cushioning around the delicate edges."


def test_buyer_approve_sample():
    review_payload = {
        "action": "approve_sample",
        "review_notes": "Looks stunning! Approved for dispatch."
    }
    res = client.post(f"/api/v1/quality/orders/{ORDER_ID}/review", json=review_payload, headers=HEADERS)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "buyer_approved"
    assert data["dispatch_allowed"] is True
    assert "Approved for dispatch" in data["buyer_notes"]
