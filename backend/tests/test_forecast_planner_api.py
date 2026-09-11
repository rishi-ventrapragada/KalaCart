"""
Tests for Demand Forecast & Production Planner (Phase 4).
Tests 7/30/90-Day Forecasts, Batch Production Scheduling, Procurement Recommendations, and Workload Calendar.
"""

import os
os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("APP_ENV", "development")
os.environ.setdefault("SUPABASE_URL", "https://placeholder.supabase.co")

from datetime import date, timedelta
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


def test_get_multi_horizon_demand_forecasts():
    res = client.get("/api/v1/forecast-planner/forecasts")
    assert res.status_code == 200, res.text
    forecasts = res.json()
    assert len(forecasts) == 3

    horizons = [f["horizon"] for f in forecasts]
    assert "7_DAYS" in horizons
    assert "30_DAYS" in horizons
    assert "90_DAYS" in horizons

    for fc in forecasts:
        assert fc["predicted_units"] > 0
        assert fc["estimated_revenue"] > 0
        assert 0 <= fc["confidence_score"] <= 100
        assert len(fc["key_drivers"]) >= 2


def test_get_and_create_production_plans():
    # 1. Get default AI recommended plans
    list_res = client.get("/api/v1/forecast-planner/plans")
    assert list_res.status_code == 200, list_res.text
    plans = list_res.json()
    assert len(plans) >= 2

    # Verify recommendations like "Produce 25 baskets" or "Stock 40 pottery"
    titles = [p["batch_title"] for p in plans]
    assert any("40" in t for t in titles)
    assert any("25" in t for t in titles)

    for p in plans:
        assert len(p["required_materials"]) >= 1
        assert p["confidence_pct"] >= 80
        assert p["procurement_recommendation"] is not None

    # 2. Create custom production batch
    today = date.today()
    create_payload = {
        "batch_title": "Produce 30 Saharanpur Carved Wooden Trays",
        "recommended_quantity": 30,
        "current_inventory": 4,
        "buffer_stock": 5,
        "required_materials": [
            {
                "material_name": "Seasoned Sheesham Wood Planks",
                "required_amount": "25 sq ft",
                "estimated_cost": 4500.0,
                "is_in_stock": True,
            }
        ],
        "procurement_recommendation": "Wood stock sufficient. Order brass inlay trim.",
        "start_date": today.isoformat(),
        "target_completion_date": (today + timedelta(days=7)).isoformat(),
        "delivery_deadline": (today + timedelta(days=10)).isoformat(),
        "workload_status": "PLANNED",
        "estimated_production_cost": 5500.0,
        "projected_revenue": 27000.0,
    }
    create_res = client.post("/api/v1/forecast-planner/plans", json=create_payload)
    assert create_res.status_code == 201, create_res.text
    created = create_res.json()
    assert created["batch_title"] == "Produce 30 Saharanpur Carved Wooden Trays"
    assert created["recommended_quantity"] == 30


def test_get_production_workload_calendar():
    res = client.get("/api/v1/forecast-planner/calendar")
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["current_workload_hours"] > 0
    assert 0 <= data["capacity_utilization_pct"] <= 100
    assert len(data["events"]) >= 3

    event_types = [e["event_type"] for e in data["events"]]
    assert "BATCH_START" in event_types
    assert "DELIVERY_DEADLINE" in event_types
