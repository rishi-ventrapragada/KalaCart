from fastapi.testclient import TestClient
import pytest
from app.main import app
from app.core.security import get_current_user

@pytest.fixture(autouse=True)
def override_auth():
    app.dependency_overrides[get_current_user] = lambda: {
        "uid": "admin-super-001",
        "email": "superadmin@kalacart.in",
        "name": "Super Admin Officer",
        "role": "admin"
    }
    yield
    app.dependency_overrides.clear()

def test_command_center_live_metrics_and_heatmap():
    client = TestClient(app)

    # 1. Fetch live operations metrics
    res = client.get("/api/v1/command-center/live-metrics")
    assert res.status_code == 200
    metrics = res.json()
    assert metrics["live_active_users"] > 0
    assert metrics["orders_today"] > 0
    assert metrics["platform_gmv_inr"] > 0
    assert metrics["net_revenue_inr"] > 0
    assert len(metrics["state_metrics"]) >= 5

    # 2. State heatmap
    res_heat = client.get("/api/v1/command-center/state-heatmap")
    assert res_heat.status_code == 200
    states = res_heat.json()
    assert any(s["state_code"] == "OR" for s in states)
    assert any(s["state_code"] == "RJ" for s in states)

def test_command_center_ai_insights():
    client = TestClient(app)

    res = client.get("/api/v1/command-center/ai-insights")
    assert res.status_code == 200
    insights = res.json()
    assert len(insights) >= 4
    
    types = [i["insight_type"] for i in insights]
    assert "demand_spike" in types
    assert "fraud_ring" in types
    assert "fast_growing_category" in types
    assert "underperforming_region" in types

def test_support_tickets_lifecycle():
    client = TestClient(app)

    ticket_req = {
        "user_email": "buyer@example.com",
        "user_type": "buyer",
        "category": "Dispute Resolution",
        "subject": "Fragile terracotta vase arrived with hairline crack",
        "description": "The packaging was slightly crushed in transit.",
        "priority": "high"
    }
    res_post = client.post("/api/v1/command-center/tickets", json=ticket_req)
    assert res_post.status_code == 201
    ticket = res_post.json()
    assert "TICK-" in ticket["ticket_number"]
    assert ticket["status"] == "open"
    assert ticket["ai_sentiment_score"] > 0.5

    # List tickets
    res_list = client.get("/api/v1/command-center/tickets")
    assert res_list.status_code == 200
    tickets = res_list.json()
    assert any(t["id"] == ticket["id"] for t in tickets)

def test_executive_report_generation():
    client = TestClient(app)

    gen_req = {
        "report_title": "Q3 Enterprise Artisan Marketplace Performance Briefing",
        "report_period": "quarterly"
    }
    res_gen = client.post("/api/v1/command-center/reports/generate", json=gen_req)
    assert res_gen.status_code == 201
    rep = res_gen.json()
    assert rep["report_title"] == "Q3 Enterprise Artisan Marketplace Performance Briefing"
    assert "Executive Intelligence Report" in rep["summary_markdown"]
    assert rep["pdf_export_url"].endswith(".pdf")
    assert len(rep["ai_insights"]) >= 4

    # List reports
    res_list = client.get("/api/v1/command-center/reports")
    assert res_list.status_code == 200
    reports = res_list.json()
    assert any(r["id"] == rep["id"] for r in reports)
