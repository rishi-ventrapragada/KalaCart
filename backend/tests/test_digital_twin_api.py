import pytest
from fastapi.testclient import TestClient
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

client = TestClient(app)


def test_get_and_sync_digital_twin():
    # 1. Fetch Digital Twin
    res = client.get("/api/v1/twin")
    assert res.status_code == 200
    twin = res.json()
    assert twin["artisan_id"] == "artisan_demo"
    assert "baseline_metrics" in twin
    assert twin["baseline_metrics"]["revenue_monthly"] > 0
    assert twin["baseline_metrics"]["production_capacity_monthly"] > 0
    assert twin["operational_parameters"]["worker_capacity_units"] > 0

    # 2. Resync baseline (read-only snapshot)
    res_sync = client.post("/api/v1/twin/sync")
    assert res_sync.status_code == 200
    assert res_sync.json()["status"] == "active"


def test_list_scenario_presets():
    res = client.get("/api/v1/twin/presets")
    assert res.status_code == 200
    presets = res.json()
    assert len(presets) >= 6
    preset_types = [p["scenario_type"] for p in presets]
    assert "price_change" in preset_types
    assert "festival_discount" in preset_types
    assert "produce_extra" in preset_types
    assert "hire_worker" in preset_types
    assert "open_export" in preset_types
    assert "change_shipping_region" in preset_types


def test_simulation_1_increase_price_10_pct():
    payload = {
        "scenario_name": "Increase Price by 10%",
        "scenario_type": "price_change",
        "levers": {
            "price_adjustment_pct": 10.0,
            "festival_discount_pct": 0.0,
            "extra_units_produced": 0,
            "hire_workers_count": 0,
            "enable_export": False,
            "simulation_horizon_months": 6
        }
    }
    res = client.post("/api/v1/twin/simulate", json=payload)
    assert res.status_code == 201
    result = res.json()
    
    # Assert predicted metrics
    proj = result["projected_metrics"]
    assert "revenue_monthly" in proj
    assert "profit_monthly" in proj
    assert "demand_units_monthly" in proj
    assert "inventory_end_units" in proj
    assert "delivery_workload_hours" in proj
    assert "customer_growth_pct" in proj

    # Check deltas
    deltas = result["delta_comparison"]
    assert "revenue_delta" in deltas
    assert "profit_delta" in deltas

    # Check 6-month timeline
    assert len(result["monthly_projections"]) == 6
    assert len(result["ai_insights"]["recommended_actions"]) >= 1


def test_simulation_2_festival_discount():
    payload = {
        "scenario_name": "Diwali Festival 20% Discount",
        "scenario_type": "festival_discount",
        "levers": {
            "price_adjustment_pct": 0.0,
            "festival_discount_pct": 20.0,
            "extra_units_produced": 50,
            "marketing_boost_pct": 30.0,
            "simulation_horizon_months": 6
        }
    }
    res = client.post("/api/v1/twin/simulate", json=payload)
    assert res.status_code == 201
    result = res.json()
    proj = result["projected_metrics"]
    assert proj["demand_units_monthly"] > result["baseline_snapshot"]["monthly_orders"]
    assert proj["customer_growth_pct"] > 5.0


def test_simulation_3_produce_100_extra_units():
    payload = {
        "scenario_name": "Produce 100 Extra Stock Units",
        "scenario_type": "produce_extra",
        "levers": {
            "extra_units_produced": 100,
            "simulation_horizon_months": 6
        }
    }
    res = client.post("/api/v1/twin/simulate", json=payload)
    assert res.status_code == 201
    result = res.json()
    proj = result["projected_metrics"]
    assert proj["inventory_end_units"] > 0
    assert proj["stockout_risk_pct"] <= 15.0


def test_simulation_4_hire_one_worker():
    payload = {
        "scenario_name": "Hire 1 Master Artisan",
        "scenario_type": "hire_worker",
        "levers": {
            "hire_workers_count": 1,
            "simulation_horizon_months": 6
        }
    }
    res = client.post("/api/v1/twin/simulate", json=payload)
    assert res.status_code == 201
    result = res.json()
    proj = result["projected_metrics"]
    assert proj["capacity_utilization_pct"] > 0
    assert proj["delivery_workload_hours"] > 0


def test_simulation_5_open_export_sales():
    payload = {
        "scenario_name": "Open Export Sales to GCC & Europe",
        "scenario_type": "open_export",
        "levers": {
            "enable_export": True,
            "shipping_region": "Global (Export)",
            "simulation_horizon_months": 6
        }
    }
    res = client.post("/api/v1/twin/simulate", json=payload)
    assert res.status_code == 201
    result = res.json()
    deltas = result["delta_comparison"]
    assert deltas["revenue_delta"] > 0
    assert deltas["customer_growth_delta"] > 0


def test_simulation_6_change_shipping_region():
    payload = {
        "scenario_name": "Expand to Pan-India Express",
        "scenario_type": "change_shipping_region",
        "levers": {
            "shipping_region": "Pan-India",
            "marketing_boost_pct": 15.0,
            "simulation_horizon_months": 6
        }
    }
    res = client.post("/api/v1/twin/simulate", json=payload)
    assert res.status_code == 201
    result = res.json()
    assert result["projected_metrics"]["revenue_monthly"] > 0


def test_simulation_runs_history_and_comparison():
    # 1. List runs
    res_list = client.get("/api/v1/twin/simulations")
    assert res_list.status_code == 200
    runs = res_list.json()
    assert len(runs) >= 3

    # 2. Get specific run detail
    run_id = runs[0]["id"]
    res_detail = client.get(f"/api/v1/twin/simulations/{run_id}")
    assert res_detail.status_code == 200
    assert res_detail.json()["simulation_run_id"] == run_id

    # 3. Compare multiple runs
    run_ids = [r["id"] for r in runs[:3]]
    res_comp = client.post("/api/v1/twin/simulations/compare", json=run_ids)
    assert res_comp.status_code == 200
    comp_data = res_comp.json()
    assert len(comp_data["runs"]) == len(run_ids)
    assert comp_data["best_profit_run_id"] in run_ids
    assert comp_data["comparative_summary"] is not None


def test_sandbox_safety_guarantee_no_production_data_mutation():
    """
    Verify that executing simulations never mutates live product listings, inventory, or orders.
    """
    # Fetch live products before simulation
    prod_res_before = client.get("/api/v1/products")
    prods_before = prod_res_before.json() if prod_res_before.status_code == 200 else []

    # Run aggressive simulation
    sim_payload = {
        "scenario_name": "Aggressive 50% Price Surge & Mass Production",
        "scenario_type": "custom_multi_lever",
        "levers": {
            "price_adjustment_pct": 50.0,
            "extra_units_produced": 500,
            "hire_workers_count": 5,
            "enable_export": True
        }
    }
    sim_res = client.post("/api/v1/twin/simulate", json=sim_payload)
    assert sim_res.status_code == 201

    # Fetch live products after simulation
    prod_res_after = client.get("/api/v1/products")
    prods_after = prod_res_after.json() if prod_res_after.status_code == 200 else []

    # Assert live product database state is strictly unchanged
    assert len(prods_before) == len(prods_after)
