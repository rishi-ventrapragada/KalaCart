"""
Tests for Seller Business Suite API (Phase 3).
"""

import os
os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("APP_ENV", "development")
os.environ.setdefault("SUPABASE_URL", "https://placeholder.supabase.co")

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import get_current_user

MOCK_SELLER = {
    "firebase_uid": "test-artisan-uid-888",
    "email": "artisan@kalacart.in",
    "artisan": {"id": "00000000-0000-0000-0000-000000000002"},
    "claims": {"uid": "test-artisan-uid-888"}
}

@pytest.fixture(autouse=True)
def setup_auth_override():
    app.dependency_overrides[get_current_user] = lambda: MOCK_SELLER
    yield
    app.dependency_overrides.pop(get_current_user, None)

client = TestClient(app)


def test_get_business_metrics():
    res = client.get("/api/v1/business/metrics")
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["gross_revenue"] > 0
    assert data["net_profit"] > 0
    assert data["profit_margin_pct"] > 0
    assert "top_repeat_customers" in data
    assert len(data["top_repeat_customers"]) >= 1


def test_create_and_list_expenses():
    payload = {
        "category": "RAW_MATERIALS",
        "title": "Natural Clay & Glazing Powder",
        "amount": 2400.0,
        "notes": "Procured for ceramic bowl production"
    }
    create_res = client.post("/api/v1/business/expenses", json=payload)
    assert create_res.status_code == 201, create_res.text
    data = create_res.json()
    assert data["title"] == "Natural Clay & Glazing Powder"
    assert data["amount"] == 2400.0

    list_res = client.get("/api/v1/business/expenses")
    assert list_res.status_code == 200
    all_expenses = list_res.json()
    assert len(all_expenses) >= 1


def test_crm_customer_management():
    list_res = client.get("/api/v1/business/crm/customers?repeat_only=true")
    assert list_res.status_code == 200, list_res.text
    customers = list_res.json()
    assert len(customers) >= 1
    cust_id = customers[0]["id"]

    # Update customer notes
    update_res = client.patch(f"/api/v1/business/crm/customers/{cust_id}", json={"is_favorite": True, "notes": "VIP Loyal Customer"})
    assert update_res.status_code == 200, update_res.text
    assert update_res.json()["is_favorite"] is True
    assert update_res.json()["notes"] == "VIP Loyal Customer"


def test_export_financial_csv():
    res = client.get("/api/v1/business/export/csv?period=MONTHLY")
    assert res.status_code == 200
    assert "text/csv" in res.headers["content-type"]
    assert "Date,Transaction Type" in res.text
