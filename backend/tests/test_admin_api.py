"""
Tests for Admin Portal & Fraud Intelligence API (Phase 3).
"""

import os
os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("APP_ENV", "development")
os.environ.setdefault("SUPABASE_URL", "https://placeholder.supabase.co")

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import get_current_user

ADMIN_USER = {
    "firebase_uid": "admin-uid-999",
    "email": "superadmin@kalacart.in",
    "role": "admin",
    "is_admin": True,
    "claims": {"role": "admin", "uid": "admin-uid-999"}
}

@pytest.fixture(autouse=True)
def setup_auth_override():
    app.dependency_overrides[get_current_user] = lambda: ADMIN_USER
    yield
    app.dependency_overrides.pop(get_current_user, None)

client = TestClient(app)


def test_get_admin_dashboard_analytics():
    res = client.get("/api/v1/admin/dashboard")
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["total_gmv"] > 0
    assert data["total_revenue"] > 0
    assert data["daily_active_users"] > 0
    assert len(data["top_categories"]) >= 1
    assert len(data["state_wise_sales"]) >= 1


def test_list_fraud_reports():
    res = client.get("/api/v1/admin/fraud-reports")
    assert res.status_code == 200, res.text
    reports = res.json()
    assert len(reports) >= 3
    categories = [r["fraud_category"] for r in reports]
    assert "FAKE_REVIEW" in categories
    assert "DUPLICATE_PRODUCT" in categories
    assert "SPAM_RFQ" in categories


def test_perform_moderation_and_audit_trail():
    mod_payload = {
        "action": "SUSPEND_SELLER",
        "target_entity": "SELLER",
        "target_id": "seller_suspect_88",
        "reason": "Repeated non-authentic craft claims and bot review manipulation",
        "changes": {"status": "SUSPENDED", "is_verified": False}
    }
    res = client.post("/api/v1/admin/moderate", json=mod_payload)
    assert res.status_code == 200, res.text
    log_data = res.json()
    assert log_data["action_type"] == "SUSPEND_SELLER"
    assert log_data["target_entity"] == "SELLER"
    assert log_data["admin_email"] == "superadmin@kalacart.in"

    # Verify log appears in audit logs
    logs_res = client.get("/api/v1/admin/logs")
    assert logs_res.status_code == 200
    all_logs = logs_res.json()
    assert len(all_logs) >= 1
    assert all_logs[0]["action_type"] == "SUSPEND_SELLER"
