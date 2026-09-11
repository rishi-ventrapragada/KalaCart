"""
Tests for Secure Payments & Escrow Engine (Phase 3).
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
    "firebase_uid": "test-buyer-uid-123",
    "email": "testbuyer@kalacart.in",
    "name": "Aditya Buyer",
    "artisan": {"id": "00000000-0000-0000-0000-000000000001"},
    "claims": {"uid": "test-buyer-uid-123"}
}

@pytest.fixture(autouse=True)
def setup_auth_override():
    app.dependency_overrides[get_current_user] = lambda: MOCK_USER
    yield
    app.dependency_overrides.pop(get_current_user, None)

client = TestClient(app)


def test_create_payment_order():
    payload = {
        "order_id": "00000000-0000-0000-0000-000000000099",
        "amount": 2500.0,
        "currency": "INR",
        "payment_method": "UPI",
        "gateway": "RAZORPAY",
        "buyer_email": "testbuyer@kalacart.in",
        "buyer_phone": "+919876543210",
        "buyer_name": "Aditya Buyer",
    }
    res = client.post("/api/v1/payments/create-order", json=payload)
    assert res.status_code == 201, res.text
    data = res.json()
    assert "gateway_order_id" in data
    assert data["amount"] == 2500.0
    assert data["gateway"] == "RAZORPAY"
    assert data["key_id"] == "rzp_test_1DP5mmOlF5G5ag"


def test_verify_payment_and_lock_escrow():
    order_id = "00000000-0000-0000-0000-000000000099"
    # 1. Create order
    create_res = client.post(
        "/api/v1/payments/create-order",
        json={"order_id": order_id, "amount": 2000.0, "payment_method": "UPI"},
    )
    assert create_res.status_code == 201
    gw_order_id = create_res.json()["gateway_order_id"]

    # 2. Verify payment with valid signature
    verify_payload = {
        "order_id": order_id,
        "gateway_order_id": gw_order_id,
        "gateway_payment_id": "pay_test_99887766",
        "gateway_signature": "sig_test_valid_signature",
        "payment_method": "UPI",
    }
    verify_res = client.post("/api/v1/payments/verify", json=verify_payload)
    assert verify_res.status_code == 200, verify_res.text
    pay_data = verify_res.json()
    assert pay_data["status"] == "CAPTURED"
    assert pay_data["gateway_payment_id"] == "pay_test_99887766"

    # 3. Check Escrow account status
    escrow_res = client.get(f"/api/v1/payments/status/{order_id}")
    assert escrow_res.status_code == 200
    escrow_data = escrow_res.json()
    assert escrow_data["escrow_status"] in ["FUNDS_LOCKED", "HELD_IN_ESCROW"]
    assert escrow_data["total_held_amount"] == 2000.0
    assert escrow_data["platform_fee"] == 100.0  # 5% of 2000
    assert escrow_data["artisan_payout_amount"] == 1900.0  # 95% of 2000


def test_release_escrow_to_seller_on_delivery():
    order_id = "00000000-0000-0000-0000-000000000099"
    release_payload = {
        "order_id": order_id,
        "reason": "Buyer verified handloom silk saree delivered in perfect condition",
    }
    release_res = client.post(f"/api/v1/payments/escrow/{order_id}/release", json=release_payload)
    assert release_res.status_code == 200, release_res.text
    payout_data = release_res.json()
    assert payout_data["status"] == "SUCCESS"
    assert payout_data["amount"] == 1900.0
    assert payout_data["order_id"] == order_id
    assert payout_data["payout_number"].startswith("PAYOUT-")


def test_refund_processing():
    refund_order_id = "00000000-0000-0000-0000-000000000088"
    # Lock funds first
    create_res = client.post(
        "/api/v1/payments/create-order",
        json={"order_id": refund_order_id, "amount": 1500.0, "payment_method": "CARD"},
    )
    assert create_res.status_code == 201
    gw_id = create_res.json()["gateway_order_id"]
    client.post(
        "/api/v1/payments/verify",
        json={
            "order_id": refund_order_id,
            "gateway_order_id": gw_id,
            "gateway_payment_id": "pay_test_refund_123",
            "gateway_signature": "sig_test_refund",
        },
    )

    # Process Partial Refund (INR 500)
    refund_payload = {
        "order_id": refund_order_id,
        "refund_amount": 500.0,
        "refund_reason": "PARTIAL_SETTLEMENT",
        "detailed_reason": "Minor cosmetic packaging damage",
    }
    refund_res = client.post("/api/v1/payments/refund", json=refund_payload)
    assert refund_res.status_code == 200, refund_res.text
    ref_data = refund_res.json()
    assert ref_data["status"] == "PROCESSED"
    assert ref_data["refund_amount"] == 500.0
    assert ref_data["refund_type"] == "PARTIAL"
    assert ref_data["refund_number"].startswith("REF-")


def test_retry_failed_payment():
    retry_order_id = "00000000-0000-0000-0000-000000000077"
    retry_res = client.post(f"/api/v1/payments/retry/{retry_order_id}?payment_method=NETBANKING")
    assert retry_res.status_code == 201, retry_res.text
    retry_data = retry_res.json()
    assert retry_data["order_id"] == retry_order_id
    assert "gateway_order_id" in retry_data
