from fastapi.testclient import TestClient
import pytest
from app.main import app
from app.core.security import get_current_user

@pytest.fixture(autouse=True)
def override_auth():
    app.dependency_overrides[get_current_user] = lambda: {
        "uid": "leader-sumati-001",
        "email": "sumati.devi@raghurajpurshg.in",
        "name": "Sumati Devi (SHG President)",
        "role": "seller"
    }
    yield
    app.dependency_overrides.clear()

def test_cooperative_shg_workspace_lifecycle():
    client = TestClient(app)

    # 1. Register a new Artisan SHG
    create_org_payload = {
        "name": "Maa Tarini Terracotta & Pattachitra Women's SHG",
        "registration_number": "SHG-OD-PURI-2024-889",
        "org_type": "shg",
        "state": "Odisha",
        "district": "Puri",
        "pincode": "752012",
        "bank_account_info": {
            "account_number": "998877665544",
            "ifsc": "SBIN0001234",
            "bank_name": "State Bank of India Puri Main Branch"
        },
        "revenue_split_rules": {
            "coop_reserve_fund_percent": 10.0,
            "labor_share_percent": 60.0,
            "material_reimbursement_percent": 30.0
        }
    }

    res_org = client.post("/api/v1/cooperative/organizations", json=create_org_payload)
    assert res_org.status_code == 201, res_org.text
    org = res_org.json()
    org_id = org["id"]
    assert org["name"] == "Maa Tarini Terracotta & Pattachitra Women's SHG"
    assert org["member_count"] == 1
    assert org["members"][0]["role"] == "leader"

    # 2. Add multiple specialized members (Manager, Accountant, Weaver Member)
    member_payloads = [
        {
            "user_id": "member-anita-002",
            "full_name": "Anita Das",
            "role": "manager",
            "craft_specialization": "Quality Inspector & Kiln Manager",
            "share_percentage": 25.0
        },
        {
            "user_id": "member-geeta-003",
            "full_name": "Geeta Maharana",
            "role": "accountant",
            "craft_specialization": "Ledger Bookkeeping & Bank Payouts",
            "share_percentage": 25.0
        },
        {
            "user_id": "member-priya-004",
            "full_name": "Priya Mohapatra",
            "role": "member",
            "craft_specialization": "Master Pattachitra Painter",
            "share_percentage": 25.0
        }
    ]

    for m in member_payloads:
        res_m = client.post(f"/api/v1/cooperative/organizations/{org_id}/members", json=m)
        assert res_m.status_code == 201, res_m.text

    # Verify updated member count
    res_dash = client.get(f"/api/v1/cooperative/organizations/{org_id}")
    assert res_dash.status_code == 200
    assert res_dash.json()["member_count"] == 4

    # 3. Pool products into Shared Inventory
    inv_payload = {
        "product_id": "prod-pattachitra-scroll-01",
        "product_name": "Handpainted Palm Leaf Radha Krishna Scroll",
        "quantity_pooled": 15,
        "unit_cost_inr": 850.0
    }
    res_inv = client.post(f"/api/v1/cooperative/organizations/{org_id}/shared-inventory", json=inv_payload)
    assert res_inv.status_code == 201, res_inv.text
    inv = res_inv.json()
    assert inv["quantity_pooled"] == 15
    assert inv["status"] == "available"

    # 4. Assign Production Task
    task_payload = {
        "assigned_to_member_id": "member-priya-004",
        "assigned_to_name": "Priya Mohapatra",
        "title": "Paint 10 Palm Leaf Bookmarks for Taj Hotels B2B Order",
        "description": "Natural mineral pigments with fine ink outline.",
        "target_units": 10,
        "deadline": "2026-09-15T18:00:00Z"
    }
    res_task = client.post(f"/api/v1/cooperative/organizations/{org_id}/tasks", json=task_payload)
    assert res_task.status_code == 201, res_task.text
    task = res_task.json()
    assert task["target_units"] == 10
    assert task["status"] == "in_progress"

    # 5. Log Attendance
    att_payload = {
        "member_id": "member-priya-004",
        "member_name": "Priya Mohapatra",
        "work_date": "2026-09-06",
        "status": "present",
        "hours_logged": 8.0
    }
    res_att = client.post(f"/api/v1/cooperative/organizations/{org_id}/attendance", json=att_payload)
    assert res_att.status_code == 201, res_att.text
    att = res_att.json()
    assert att["status"] == "present"
    assert att["hours_logged"] == 8.0

    # 6. Calculate Automated Revenue Sharing Split on an ₹8,500 Order
    payout_req = {
        "order_id": "ord-b2b-shg-001",
        "total_order_amount_inr": 8500.0,
        "participating_member_ids": ["member-priya-004", "member-anita-002"]
    }
    res_payout = client.post(f"/api/v1/cooperative/organizations/{org_id}/payouts/calculate", json=payout_req)
    assert res_payout.status_code == 200, res_payout.text
    payout = res_payout.json()
    assert payout["cooperative_fund_deduction_inr"] == 850.0  # 10% reserve fund
    assert len(payout["splits"]) == 2
    per_member = (8500.0 - 850.0) / 2.0  # 3825.0
    assert payout["splits"][0]["payout_amount_inr"] == per_member
