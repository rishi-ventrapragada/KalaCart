from fastapi.testclient import TestClient
import pytest
from app.main import app
from app.core.security import get_current_user

@pytest.fixture(autouse=True)
def override_auth():
    app.dependency_overrides[get_current_user] = lambda: {
        "uid": "artisan_demo",
        "email": "master_artisan@kalacart.test",
        "role": "seller",
        "name": "Master Artisan"
    }
    yield
    app.dependency_overrides.clear()

def test_predictive_insights_and_festival_detection():
    client = TestClient(app)
    # 1. Fetch AI Executive Insights
    res = client.get("/api/v1/brain/insights")
    assert res.status_code == 200, res.text
    insights = res.json()
    assert len(insights) >= 2
    types = [i["insight_type"] for i in insights]
    assert "revenue_forecast" in types
    assert "festival_opportunity" in types

def test_cashflow_and_risk_predictions():
    client = TestClient(app)
    # 1. Fetch Cashflow Forecast
    res_cash = client.get("/api/v1/brain/cashflow")
    assert res_cash.status_code == 200, res_cash.text
    cash_data = res_cash.json()
    assert cash_data["forecast_horizon_days"] == 30
    assert cash_data["projected_inflows"] > 0
    assert cash_data["working_capital_health"] in ("healthy", "surplus")
    assert len(cash_data["cashflow_breakdown"]) == 4

    # 2. Fetch Risk Predictions
    res_risk = client.get("/api/v1/brain/risks")
    assert res_risk.status_code == 200, res_risk.text
    risks = res_risk.json()
    assert len(risks) >= 2
    cat_names = [r["risk_category"] for r in risks]
    assert "stockout_risk" in cat_names
    assert "customer_churn" in cat_names

def test_ai_decisions_proposals_and_human_approval_workflow():
    client = TestClient(app)
    # 1. List existing suggested decisions
    res_list = client.get("/api/v1/brain/decisions")
    assert res_list.status_code == 200
    decisions = res_list.json()
    assert len(decisions) >= 3

    # 2. Create new decision (suggest hiring a seasonal potter for Diwali)
    create_payload = {
        "decision_type": "hiring",
        "title": "Hire 2 Seasonal Master Potters for Diwali Rush (30 Days)",
        "rationale": "Production capacity at 100% utilization. Additional 2 potters will capture ₹65,000 in unfulfilled orders.",
        "proposed_payload": {"headcount": 2, "skill": "pottery_wheel", "duration_weeks": 4, "max_rate": 200.0},
        "projected_revenue_lift": 65000.0,
        "projected_cost_savings": 0.0,
        "confidence_score": 93.0
    }
    res_create = client.post("/api/v1/brain/decisions", json=create_payload)
    assert res_create.status_code == 201, res_create.text
    dec = res_create.json()
    dec_id = dec["id"]
    assert dec["status"] == "suggested"
    assert dec["approved_at"] is None

    # 3. Seller Approves decision
    res_appr = client.post(f"/api/v1/brain/decisions/{dec_id}/action", json={"action": "approve"})
    assert res_appr.status_code == 200
    assert res_appr.json()["status"] == "approved"
    assert res_appr.json()["approved_at"] is not None

    # 4. Execute approved decision
    res_exec = client.post(f"/api/v1/brain/decisions/{dec_id}/action", json={"action": "execute"})
    assert res_exec.status_code == 200
    assert res_exec.json()["status"] == "executed"
    assert res_exec.json()["execution_result"]["success"] is True

def test_executive_reports_pdf_generation():
    client = TestClient(app)
    # 1. Weekly report
    res_rep = client.get("/api/v1/brain/reports/executive?report_type=weekly")
    assert res_rep.status_code == 200, res_rep.text
    rep = res_rep.json()
    assert rep["report_type"] == "weekly"
    assert "pdf" in rep["download_pdf_url"]
    assert len(rep["top_growth_opportunities"]) >= 1
    assert len(rep["critical_risks"]) >= 1
