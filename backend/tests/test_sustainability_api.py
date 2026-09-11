"""Tests for Sustainability / Eco-Impact Calculator (Phase 18)."""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_calculate_green_leaf_tier():
    payload = {
        "materials": ["terracotta", "clay", "natural dye"],
        "handmade_percentage": 100.0,
        "local_sourcing": "cluster",
        "plastic_usage": "zero_plastic",
        "packaging": "zero_waste",
    }
    res = client.post("/api/v1/sustainability/calculate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["eco_score"] == 100
    assert data["tier"] == "Green Leaf"
    assert data["badge_label"] == "Green Leaf Certified"
    assert len(data["breakdowns"]) == 5
    assert len(data["key_positive_highlights"]) > 0


def test_calculate_silver_tier():
    payload = {
        "materials": ["brass", "synthetic lacquer"],
        "handmade_percentage": 60.0,
        "local_sourcing": "national",
        "plastic_usage": "minimal",
        "packaging": "standard_carton",
    }
    res = client.post("/api/v1/sustainability/calculate", json=payload)
    assert res.status_code == 200
    data = res.json()
    # Material: 12, Handmade: 15, Sourcing: 10, Plastic: 10, Packaging: 6 = 53
    assert 50 <= data["eco_score"] <= 69
    assert data["tier"] == "Silver"
    assert len(data["actionable_improvement_tips"]) > 0


def test_calculate_bronze_tier():
    payload = {
        "materials": ["polyester", "pvc resin"],
        "handmade_percentage": 20.0,
        "local_sourcing": "imported",
        "plastic_usage": "high",
        "packaging": "plastic_wrap",
    }
    res = client.post("/api/v1/sustainability/calculate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["eco_score"] < 50
    assert data["tier"] == "Bronze"
    assert len(data["actionable_improvement_tips"]) >= 3


def test_get_product_sustainability():
    res = client.get("/api/v1/sustainability/product/fake-test-id")
    assert res.status_code == 200
    data = res.json()
    assert "eco_score" in data
    assert "tier" in data
    assert "carbon_estimate_kgco2e" in data
    assert "carbon_saved_vs_industrial_kgco2e" in data
    assert "water_saved_liters" in data
    assert "material_origins" in data
    assert "recycling_guidance" in data


def test_material_origins_catalog():
    res = client.get("/api/v1/sustainability/material-origins")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 4
    assert any("Jaipur" in m["origin_cluster"] or "Rajasthan" in m["origin_state"] for m in data)


def test_seller_sustainability_report():
    res = client.get("/api/v1/sustainability/seller/00000000-0000-0000-0000-000000000002/report")
    assert res.status_code == 200
    data = res.json()
    assert data["total_carbon_saved_kgco2e"] > 0
    assert data["eco_products_percentage"] == 100.0
    assert data["total_water_saved_liters"] > 0


def test_iot_devices_list():
    res = client.get("/api/v1/iot/devices")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 4
    assert any(d["device_type"] == "weighing_scale" for d in data)
    assert any(d["device_type"] == "barcode_scanner" for d in data)


def test_iot_device_ping():
    res = client.post("/api/v1/iot/devices/d0000001-0000-0000-0000-000000000001/ping?battery_pct=95")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "online"
    assert data["battery_pct"] == 95


def test_iot_barcode_scan_auto_stock_update():
    # 1. Auto Stock-In
    res = client.post("/api/v1/iot/scan", json={
        "raw_code": "8901234567890",
        "action": "stock_in",
        "quantity": 2,
        "scan_type": "barcode_scan"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["new_stock"] > data["previous_stock"]

    # 2. Auto Stock-Out
    res2 = client.post("/api/v1/iot/scan", json={
        "raw_code": "8901234567890",
        "action": "stock_out",
        "quantity": 1,
        "scan_type": "barcode_scan"
    })
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["status"] == "success"
    assert data2["new_stock"] < data2["previous_stock"]


def test_iot_weight_verification():
    res = client.post("/api/v1/iot/verify-weight", json={
        "measured_weight_kg": 1.26,
        "declared_weight_kg": 1.25,
        "tolerance_pct": 5.0
    })
    assert res.status_code == 200
    data = res.json()
    assert data["is_valid"] is True
    assert data["compliance_status"] == "verified_pass"


def test_iot_workshop_climate_telemetry():
    res = client.get("/api/v1/iot/workshop-climate")
    assert res.status_code == 200
    data = res.json()
    assert data["ambient_temperature_c"] > 0
    assert data["ambient_humidity_rh"] > 0
    assert data["climate_status"] in ["normal", "warning", "critical"]


def test_iot_smart_print_job():
    res = client.post("/api/v1/iot/print", json={
        "job_type": "shipping_label",
        "copies": 2
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "completed"
    assert data["copies"] == 2
    assert "ZPL" in data["zpl_escpos_payload"] or "^XA" in data["zpl_escpos_payload"]

