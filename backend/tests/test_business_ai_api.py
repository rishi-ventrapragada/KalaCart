"""
Tests for Kala AI Autonomous Business Manager (Phase 4).
Tests Morning Briefings, Health Score (0-100), Action Suggestions, and Natural Language Q&A.
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


def test_get_daily_morning_briefing():
    res = client.get("/api/v1/ai-manager/briefing")
    assert res.status_code == 200, res.text
    data = res.json()
    assert "greeting" in data
    assert data["today_sales"] >= 0
    assert data["yesterday_revenue"] >= 0
    assert data["pending_orders_count"] >= 0
    assert data["weekly_goal_pct"] > 0
    assert len(data["high_prob_rfqs"]) >= 1
    assert len(data["followup_customers"]) >= 1


def test_get_business_health_score():
    res = client.get("/api/v1/ai-manager/health-score")
    assert res.status_code == 200, res.text
    data = res.json()
    assert 0 <= data["overall_score"] <= 100
    assert data["grade"] in ["A+", "A", "B", "C"]
    assert len(data["breakdown"]) == 6
    assert "top_recommendation" in data


def test_get_and_dismiss_suggestions():
    res = client.get("/api/v1/ai-manager/suggestions")
    assert res.status_code == 200, res.text
    suggestions = res.json()
    assert len(suggestions) >= 3
    types = [s["suggestion_type"] for s in suggestions]
    assert "PRICE_INCREASE" in types
    assert "TRENDING_DEMAND" in types
    assert "URGENT_REPLY" in types

    sugg_id = suggestions[0]["id"]
    dis_res = client.post(f"/api/v1/ai-manager/suggestions/{sugg_id}/dismiss")
    assert dis_res.status_code == 200
    assert dis_res.json()["status"] == "DISMISSED"


def test_natural_language_queries():
    # 1. Earnings
    earn_res = client.post("/api/v1/ai-manager/query", json={"query_text": "How much did I earn this month?"})
    assert earn_res.status_code == 200, earn_res.text
    earn_data = earn_res.json()
    assert earn_data["intent"] == "EARNINGS"
    assert "84,200" in earn_data["response_text"]
    assert earn_data["supporting_data"]["net_profit"] == 52800.0

    # 2. Best Selling Product
    best_res = client.post("/api/v1/ai-manager/query", json={"query_text": "Which product sells best?"})
    assert best_res.status_code == 200, best_res.text
    best_data = best_res.json()
    assert best_data["intent"] == "BEST_SELLER"
    assert "Jaipur Blue Pottery" in best_data["response_text"]

    # 3. Customer Geography
    cust_res = client.post("/api/v1/ai-manager/query", json={"query_text": "Show customers from Hyderabad"})
    assert cust_res.status_code == 200, cust_res.text
    cust_data = cust_res.json()
    assert cust_data["intent"] == "CUSTOMER_LOOKUP"
    assert "Hyderabad" in cust_data["response_text"]
