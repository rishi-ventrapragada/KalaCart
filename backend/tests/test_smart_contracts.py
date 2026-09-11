"""
Test Suite for Smart Contracts & Institutional Escrow (Phase 9)
Verifies:
- Creation of draft procurement agreements with defined milestones
- Cryptographic digital signing (buyer, artisan, escrow agent)
- Multi-party inspection approvals & score recording
- Penalty calculations on late deliverable submissions
- Automated milestone release & escrow balance updates
"""

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_smart_contracts_summary():
    response = client.get("/api/v1/contracts/summary")
    assert response.status_code == 200
    data = response.json()
    assert "total_contracts" in data
    assert "contracts" in data
    assert data["total_contracts"] >= 1


def test_smart_contracts_list():
    response = client.get("/api/v1/contracts/list")
    assert response.status_code == 200
    data = response.json()
    assert "count" in data
    assert "contracts" in data
    assert data["count"] >= 1


def test_contract_details_not_found():
    response = client.get("/api/v1/contracts/NON_EXISTENT_ID")
    assert response.status_code == 404


def test_full_contract_escrow_milestone_lifecycle():
    # 4 days past due date to test penalty calculation
    past_due_date = (datetime.now(timezone.utc) - timedelta(days=4)).strftime("%Y-%m-%d")

    # 1. Create a new contract in draft status
    create_payload = {
        "title": "Ministry of Culture Handloom Procurement 2026",
        "buyer_org_name": "Ministry of Textiles & Handlooms",
        "buyer_org_type": "government",
        "buyer_signatory_name": "Dr. R. Sharma (Director of Procurement)",
        "buyer_signatory_email": "r.sharma@textiles.gov.in",
        "artisan_id": "artisan_banaras_test_01",
        "artisan_signatory_name": "Banaras Silk Heritage Guild",
        "total_contract_value": 500000.0,
        "penalty_per_day_late_pct": 0.5,
        "max_penalty_cap_pct": 10.0,
        "milestones": [
            {
                "title": "Milestone 1: 100 Pure Zari Silk Sarees Weaving",
                "description": "Completion of 100 authentic Varanasi handloom sarees with GI tags.",
                "release_percentage": 50.0,
                "due_date": past_due_date,
            },
            {
                "title": "Milestone 2: Final Batch 100 Sarees & Packaging",
                "description": "Completion of remaining 100 sarees and eco-packaging.",
                "release_percentage": 50.0,
                "due_date": (datetime.now(timezone.utc) + timedelta(days=30)).strftime("%Y-%m-%d"),
            },
        ],
    }
    create_res = client.post("/api/v1/contracts/create", json=create_payload)
    assert create_res.status_code == 200
    contract_data = create_res.json()["contract"]
    contract_id = contract_data["contract_id"]
    assert contract_data["contract_status"] == "draft"
    assert len(contract_data["milestones"]) == 2

    # 2. Digitally Sign Contract (Buyer + Artisan)
    sign_buyer = client.post(
        "/api/v1/contracts/sign",
        json={
            "contract_id": contract_id,
            "signer_role": "buyer",
            "signer_name": "Dr. R. Sharma",
        },
    )
    assert sign_buyer.status_code == 200

    sign_artisan = client.post(
        "/api/v1/contracts/sign",
        json={
            "contract_id": contract_id,
            "signer_role": "artisan",
            "signer_name": "Master Artisan Ramu",
        },
    )
    assert sign_artisan.status_code == 200
    assert sign_artisan.json()["contract_status"] == "signed_pending_escrow"

    # 3. Fund Escrow Account
    fund_res = client.post(
        "/api/v1/contracts/escrow/fund",
        json={
            "contract_id": contract_id,
            "amount": 500000.0,
        },
    )
    assert fund_res.status_code == 200
    assert fund_res.json()["contract_status"] == "active"
    assert fund_res.json()["escrow_funded_amount"] == 500000.0

    milestone_1_id = contract_data["milestones"][0]["milestone_id"]

    # 4. Submit Milestone Deliverables
    deliver_res = client.post(
        "/api/v1/contracts/milestones/deliver",
        json={
            "contract_id": contract_id,
            "milestone_id": milestone_1_id,
            "delivery_notes": "100 Handloom Zari sarees delivered to Central Quality Hub.",
        },
    )
    assert deliver_res.status_code == 200

    # 5. Quality Inspection & Multi-party Approval with Penalty Deduction (4 days late = 2.0% penalty)
    approve_res = client.post(
        "/api/v1/contracts/milestones/approve",
        json={
            "contract_id": contract_id,
            "milestone_id": milestone_1_id,
            "approver_role": "quality_inspector",
            "approver_name": "S. Verma (Chief Textile Inspector)",
            "comments": "Zari purity tested via spectrography (98.4% pure silver/gold zari). Approved.",
        },
    )
    assert approve_res.status_code == 200
    payout_info = approve_res.json()
    assert payout_info["gross_amount"] == 250000.0
    # Penalty: 4 days * 0.5% = 2.0% of 250,000 = 5,000 INR
    assert payout_info["penalty_deducted"] == 5000.0
    assert payout_info["net_payout_released"] == 245000.0

    # 6. Verify Contract Escrow Balances
    contract_check = client.get(f"/api/v1/contracts/{contract_id}")
    assert contract_check.status_code == 200
    c_final = contract_check.json()
    assert c_final["financials"]["escrow_funded_amount"] == 500000.0
    assert c_final["financials"]["escrow_released_amount"] == 245000.0
