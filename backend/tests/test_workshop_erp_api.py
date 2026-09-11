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

def test_worker_and_machine_management():
    client = TestClient(app)
    # 1. Add worker
    w_resp = client.post("/api/v1/erp/workers", json={
        "name": "Govind Sahu",
        "phone": "+91 99887 76655",
        "skills": ["brass_casting", "engraving"],
        "rate_type": "hourly",
        "base_rate": 180.0,
        "status": "active"
    })
    assert w_resp.status_code == 201, w_resp.text
    w_data = w_resp.json()
    assert w_data["name"] == "Govind Sahu"
    assert "brass_casting" in w_data["skills"]
    assert w_data["base_rate"] == 180.0

    # 2. List workers
    w_list_resp = client.get("/api/v1/erp/workers")
    assert w_list_resp.status_code == 200
    assert len(w_list_resp.json()) >= 1

    # 3. Add machine
    m_resp = client.post("/api/v1/erp/machines", json={
        "name": "Brass Polishing Lathe #2",
        "machine_type": "lathe",
        "serial_number": "BPL-2025-99B",
        "status": "operational",
        "notes": "High precision buffing head"
    })
    assert m_resp.status_code == 201, m_resp.text
    m_data = m_resp.json()
    assert m_data["machine_type"] == "lathe"

    # 4. List machines
    m_list_resp = client.get("/api/v1/erp/machines")
    assert m_list_resp.status_code == 200
    assert len(m_list_resp.json()) >= 1

def test_production_batch_linked_to_order():
    client = TestClient(app)
    # Create batch explicitly linked to a KalaCart order
    order_id = "ORD-2026-B2B-109"
    batch_resp = client.post("/api/v1/erp/batches", json={
        "product_id": "prod_dhokra_horse_figurine",
        "order_id": order_id,
        "target_quantity": 25,
        "assigned_worker_ids": ["w-101"],
        "assigned_machine_id": "m-201",
        "scheduled_start_date": "2026-09-10",
        "scheduled_end_date": "2026-09-18",
        "estimated_labour_cost": 3000.0,
        "estimated_material_cost": 2000.0,
        "notes": "Dhokra brass batch for corporate gifting"
    })
    assert batch_resp.status_code == 201, batch_resp.text
    batch_data = batch_resp.json()
    batch_id = batch_data["id"]
    assert batch_data["order_id"] == order_id
    assert batch_data["target_quantity"] == 25
    assert batch_data["status"] == "queued"

    # Verify filtering batches by order_id
    filter_resp = client.get(f"/api/v1/erp/batches?order_id={order_id}")
    assert filter_resp.status_code == 200
    batches = filter_resp.json()
    assert len(batches) == 1
    assert batches[0]["id"] == batch_id

    # Update batch status to in_production
    status_resp = client.patch(f"/api/v1/erp/batches/{batch_id}/status?status=in_production")
    assert status_resp.status_code == 200
    assert status_resp.json()["status"] == "in_production"
    assert status_resp.json()["actual_start_date"] is not None

def test_quality_checks_and_material_usage():
    client = TestClient(app)
    # 1. Create a batch
    batch_resp = client.post("/api/v1/erp/batches", json={
        "product_id": "prod_terracotta_tea_set",
        "order_id": "ORD-2026-RETAIL-554",
        "target_quantity": 30,
        "estimated_labour_cost": 1500.0,
        "estimated_material_cost": 800.0
    })
    batch_id = batch_resp.json()["id"]

    # 2. Log raw material usage
    mat_resp = client.post(f"/api/v1/erp/batches/{batch_id}/materials", json={
        "material_name": "Fine Red Terracotta Clay",
        "quantity_used": 15.5,
        "unit_of_measure": "kg",
        "unit_cost": 40.0
    })
    assert mat_resp.status_code == 201
    mat_data = mat_resp.json()
    assert mat_data["total_cost"] == 620.0

    # Verify material usage history
    mat_list = client.get(f"/api/v1/erp/batches/{batch_id}/materials")
    assert mat_list.status_code == 200
    assert len(mat_list.json()) == 1

    # 3. Log Quality Check
    qc_resp = client.post(f"/api/v1/erp/batches/{batch_id}/qc", json={
        "total_inspected": 30,
        "passed_count": 29,
        "rejected_count": 1,
        "defect_types": [{"defect": "minor hairline crack on saucer", "count": 1}],
        "result": "passed",
        "inspection_notes": "Passed GI craft standard criteria"
    })
    assert qc_resp.status_code == 201
    qc_data = qc_resp.json()
    assert qc_data["pass_rate_percentage"] == 96.67
    assert qc_data["result"] == "passed"

    # Verify QC history
    qc_list = client.get(f"/api/v1/erp/batches/{batch_id}/qc")
    assert qc_list.status_code == 200
    assert len(qc_list.json()) == 1

def test_daily_productivity_payroll_and_reporting():
    client = TestClient(app)
    # 1. Log productivity for worker
    prod_resp = client.post("/api/v1/erp/productivity", json={
        "worker_id": "w-101",
        "batch_id": "b-301",
        "work_date": "2026-09-05",
        "hours_worked": 8.0,
        "units_produced": 12,
        "notes": "Smooth clay wheel spinning"
    })
    assert prod_resp.status_code == 201
    prod_data = prod_resp.json()
    assert prod_data["hours_worked"] == 8.0
    assert prod_data["calculated_labour_cost"] == 1200.0

    # 2. Generate Payroll
    pay_resp = client.post("/api/v1/erp/payroll/generate", json={
        "period_start": "2026-09-01",
        "period_end": "2026-09-30"
    })
    assert pay_resp.status_code == 200
    payroll_records = pay_resp.json()
    assert len(payroll_records) >= 1
    assert payroll_records[0]["payment_status"] == "processed"
    assert payroll_records[0]["payment_reference"] is not None

    # 3. Generate Production Report & KPIs
    rep_resp = client.get("/api/v1/erp/reports/production")
    assert rep_resp.status_code == 200
    report = rep_resp.json()
    assert report["total_workers"] >= 1
    assert report["overall_quality_pass_rate"] > 0
    assert len(report["batch_summary"]) >= 1
