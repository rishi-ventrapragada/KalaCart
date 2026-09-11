"""
Test Suite for Robotics & Smart Manufacturing (KalaCart V10)
Verifies:
- Registration of digital workshop equipment (CNC, Laser Engraver, Ceramic Kiln, Smart Scale)
- Real-time IoT machine telemetry ingestion and anomaly detection
- Predictive maintenance scheduling and maintenance logs
- ML batch quality prediction linked with Workshop ERP
- Workshop health & energy consumption dashboard
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_workshop_dashboard_summary():
    response = client.get("/api/v1/robotics/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert "total_machines" in data
    assert "online_machines" in data
    assert "total_power_consumption_kw" in data
    assert "machines" in data
    assert data["total_machines"] >= 4


def test_register_new_workshop_machine():
    payload = {
        "workshop_id": "ws_moradabad_brass_04",
        "machine_code": "SCAN-3D-01",
        "machine_name": "Moradabad High-Res 3D Photogrammetry Scanner",
        "machine_type": "3d_scanner",
        "ip_address": "192.168.20.15",
    }
    response = client.post("/api/v1/robotics/machines/register", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["machine"]["machine_code"] == "SCAN-3D-01"
    assert data["machine"]["machine_type"] == "3d_scanner"
    assert data["machine"]["status"] == "online"


def test_ingest_telemetry_and_anomaly_detection():
    # 1. Fetch existing CNC machine
    dash_res = client.get("/api/v1/robotics/dashboard")
    cnc_machine = next(m for m in dash_res.json()["machines"] if m["machine_code"] == "CNC-WOOD-01")
    machine_id = cnc_machine["id"]

    # 2. Ingest normal telemetry
    norm_res = client.post(
        "/api/v1/robotics/telemetry/ingest",
        json={
            "machine_id": machine_id,
            "temperature_c": 35.0,
            "vibration_level_mm_s": 0.5,
            "power_consumption_w": 500.0,
            "additional_metrics": {"spindle_rpm": 4500},
        },
    )
    assert norm_res.status_code == 200
    assert norm_res.json()["machine_status"] in ("online", "busy")

    # 3. Ingest severe vibration anomaly (> 1.8 mm/s) -> triggers MAINTENANCE_REQUIRED
    anomaly_res = client.post(
        "/api/v1/robotics/telemetry/ingest",
        json={
            "machine_id": machine_id,
            "temperature_c": 82.0,
            "vibration_level_mm_s": 2.4,  # Anomaly!
            "power_consumption_w": 950.0,
            "additional_metrics": {},
        },
    )
    assert anomaly_res.status_code == 200
    assert anomaly_res.json()["machine_status"] == "maintenance_required"


def test_schedule_machine_maintenance():
    dash_res = client.get("/api/v1/robotics/dashboard")
    laser_machine = next(m for m in dash_res.json()["machines"] if m["machine_code"] == "LASER-ENGRAVE-02")
    machine_id = laser_machine["id"]

    payload = {
        "machine_id": machine_id,
        "maintenance_type": "filter_replacement",
        "scheduled_date": "2026-09-20",
        "technician_name": "Kavita Rao (Senior Optoelectronics Tech)",
        "notes": "Replace HEPA exhaust filter and realign focal collimator.",
    }
    response = client.post("/api/v1/robotics/maintenance/schedule", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    log = data["maintenance_log"]
    assert log["maintenance_type"] == "filter_replacement"
    assert log["status"] == "scheduled"
    assert log["technician_name"] == "Kavita Rao (Senior Optoelectronics Tech)"

    # Verify maintenance history in machine details
    details_res = client.get(f"/api/v1/robotics/machines/{machine_id}")
    assert details_res.status_code == 200
    assert len(details_res.json()["maintenance_history"]) >= 1


def test_predict_batch_quality_and_link_erp():
    dash_res = client.get("/api/v1/robotics/dashboard")
    kiln_machine = next(m for m in dash_res.json()["machines"] if m["machine_code"] == "KILN-CERAMIC-03")
    machine_id = kiln_machine["id"]

    payload = {
        "machine_id": machine_id,
        "batch_id": "BATCH-KHURJA-2026-09-A",
        "product_id": "PROD-CERAMIC-VASE-01",
    }
    response = client.post("/api/v1/robotics/quality/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    pred = data["quality_prediction"]
    assert pred["batch_id"] == "BATCH-KHURJA-2026-09-A"
    assert pred["predicted_quality_score"] > 80.0
    assert pred["passed_threshold"] is True
