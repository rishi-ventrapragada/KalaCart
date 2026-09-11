import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_get_impact_summary():
    """Verify national social impact metrics retrieval."""
    response = client.get("/api/v1/impact/summary")
    assert response.status_code == 200
    data = response.json()
    assert "total_artisans_onboarded" in data
    assert data["total_artisans_onboarded"] >= 14000
    assert data["women_participation_pct"] > 60.0
    assert data["rural_employment_hours_generated"] > 1000000
    assert data["endangered_crafts_preserved"] > 20


def test_get_ngo_dashboard():
    """Verify NGO dashboard returns beneficiaries and SHG collective data."""
    response = client.get("/api/v1/impact/ngo-dashboard")
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "beneficiaries" in data
    assert len(data["beneficiaries"]) > 0
    assert "shg_collective_breakdown" in data
    assert len(data["shg_collective_breakdown"]) > 0


def test_get_csr_dashboard():
    """Verify CSR corporate grant and ESG compliance metrics."""
    response = client.get("/api/v1/impact/csr-dashboard?partner_name=Tata+Trusts")
    assert response.status_code == 200
    data = response.json()
    assert data["corporate_partner_name"] == "Tata Trusts"
    assert data["grant_allocation_inr"] > 0
    assert data["women_empowerment_ratio_pct"] > 70.0
    assert len(data["sdg_alignment"]) >= 4


def test_get_gov_dashboard():
    """Verify Government ministry corridor analytics and district rankings."""
    response = client.get("/api/v1/impact/gov-dashboard")
    assert response.status_code == 200
    data = response.json()
    assert "jurisdiction" in data
    assert "state_level_growth" in data
    assert len(data["district_rankings"]) >= 5
    assert len(data["policy_action_items"]) >= 3


def test_list_district_reports():
    """Verify district report querying and filtering."""
    response = client.get("/api/v1/impact/districts")
    assert response.status_code == 200
    districts = response.json()
    assert len(districts) >= 5
    assert any(d["district_name"] == "Kachchh" for d in districts)

    # Test filtering by state
    gujarat_res = client.get("/api/v1/impact/districts?state=Gujarat")
    assert gujarat_res.status_code == 200
    guj_districts = gujarat_res.json()
    assert len(guj_districts) >= 1
    assert all(d["state"].lower() == "gujarat" for d in guj_districts)


def test_create_beneficiary():
    """Verify adding a new artisan beneficiary automatically increments national totals."""
    initial_summary = client.get("/api/v1/impact/summary").json()
    initial_total = initial_summary["total_artisans_onboarded"]

    payload = {
        "full_name": "Rukmani Devi",
        "gender": "FEMALE",
        "age": 34,
        "district": "Madhubani",
        "state": "Bihar",
        "craft_category": "Sikki Grass Weaving",
        "shg_collective_name": "Mithila Mahila Mandal",
        "baseline_monthly_income_inr": 4000.0,
        "current_monthly_income_inr": 16000.0,
        "dependents_count": 3,
        "craft_generation": 3,
        "literacy_level": "Secondary",
        "bank_account_verified": True
    }

    response = client.post("/api/v1/impact/beneficiaries", json=payload)
    assert response.status_code == 201
    ben = response.json()
    assert ben["full_name"] == "Rukmani Devi"
    assert ben["income_growth_pct"] == 300.0  # (16000-4000)/4000 * 100

    updated_summary = client.get("/api/v1/impact/summary").json()
    assert updated_summary["total_artisans_onboarded"] == initial_total + 1


def test_sync_order_impact_event():
    """Verify order completions automatically increment artisan payouts and employment hours."""
    initial_summary = client.get("/api/v1/impact/summary").json()
    initial_payout = initial_summary["total_direct_payouts_inr"]
    initial_hours = initial_summary["rural_employment_hours_generated"]

    sync_payload = {
        "order_id": "ORD-LIVE-TEST-992",
        "order_amount_inr": 10000.0,
        "craft_category": "Ajrakh Handblock",
        "district": "Kachchh",
        "state": "Gujarat",
        "is_women_led": True,
        "labor_hours": 36
    }

    response = client.post("/api/v1/impact/sync-order-event", json=sync_payload)
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["status"] == "synchronized"
    assert res_data["payout_credited_inr"] == 8500.0  # 85% direct payout
    assert res_data["employment_hours_added"] == 36

    updated_summary = client.get("/api/v1/impact/summary").json()
    assert updated_summary["total_direct_payouts_inr"] == initial_payout + 8500.0
    assert updated_summary["rural_employment_hours_generated"] == initial_hours + 36


def test_download_impact_pdf():
    """Verify PDF export for National, CSR, and Government impact audit reports."""
    for rtype in ["national", "csr", "government"]:
        response = client.get(f"/api/v1/impact/report/pdf?report_type={rtype}&partner_name=Reliance+Foundation")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert response.content.startswith(b"%PDF-")
        assert len(response.content) > 1000
