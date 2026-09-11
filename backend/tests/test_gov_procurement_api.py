import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import get_current_user

@pytest.fixture(autouse=True)
def override_auth():
    app.dependency_overrides[get_current_user] = lambda: {
        "uid": "gov_buyer_ministry_textiles",
        "email": "procurement@gov.in",
        "role": "buyer",
        "name": "Procurement Officer"
    }
    yield
    app.dependency_overrides.clear()

client = TestClient(app)


def test_gov_buyer_registration():
    payload = {
        "organization_name": "Indian Council of Cultural Relations (ICCR)",
        "buyer_type": "government",
        "department": "Cultural Diplomatic Exchange Division",
        "nodal_officer_name": "Smt. Arundhati Mukherjee",
        "nodal_officer_email": "arundhati.m@iccr.gov.in",
        "nodal_officer_phone": "+91 11 2337 9301",
        "pan_number": "AAAGI4422F",
        "gstin": "07AAAGI4422F1ZX",
        "gem_buyer_id": "GEM-BUY-ICCR-2026",
        "csr_registration_number": None,
        "allocated_annual_budget": 35000000.00
    }
    response = client.post("/api/v1/gov/buyers/register", json=payload)
    assert response.status_code in (200, 201)
    data = response.json()
    assert data["organization_name"] == payload["organization_name"]
    assert data["buyer_type"] == "government"
    assert data["verification_status"] == "verified"
    assert data["allocated_annual_budget"] == 35000000.00


def test_list_tenders_and_filters():
    # 1. List all tenders
    response = client.get("/api/v1/gov/tenders")
    assert response.status_code == 200
    tenders = response.json()
    assert isinstance(tenders, list)
    assert len(tenders) >= 2

    # 2. Filter by buyer_type=government
    gov_resp = client.get("/api/v1/gov/tenders?buyer_type=government")
    assert gov_resp.status_code == 200
    for t in gov_resp.json():
        assert t["buyer_type"] == "government"

    # 3. Filter by buyer_type=csr
    csr_resp = client.get("/api/v1/gov/tenders?buyer_type=csr")
    assert csr_resp.status_code == 200
    for t in csr_resp.json():
        assert t["buyer_type"] == "csr"


def test_create_tender_with_msme_and_gi_priority():
    tender_payload = {
        "title": "National Museum Exhibition: 500 Jaipur Blue Pottery Display Plates",
        "description": "Procurement of authentic GI-certified Jaipur Blue Pottery display plates for permanent gallery installation.",
        "craft_category": "Pottery",
        "target_quantity": 500,
        "estimated_budget": 850000.00,
        "delivery_deadline": "2026-12-15T18:00:00Z",
        "delivery_location": "National Museum, Janpath, New Delhi - 110011",
        "eligibility_criteria": {
            "msme_only": True,
            "gi_priority": True,
            "min_experience_years": 3,
            "cluster_state_preference": "Rajasthan",
            "shg_women_quota": False
        },
        "technical_specs": {
            "diameter_inches": 12,
            "glaze_type": "Lead-free traditional turquoise blue quartz glaze",
            "gi_tag_required": True
        },
        "document_urls": ["https://kalacart.in/tenders/museum_pottery_specs.pdf"]
    }
    response = client.post("/api/v1/gov/tenders", json=tender_payload)
    assert response.status_code in (200, 201)
    tender = response.json()
    assert tender["title"] == tender_payload["title"]
    assert tender["craft_category"] == "Pottery"
    assert tender["target_quantity"] == 500
    assert tender["eligibility_criteria"]["gi_priority"] is True
    assert tender["eligibility_criteria"]["msme_only"] is True
    assert tender["lifecycle_stage"] == "published"


def test_submit_bid_with_gi_and_msme_scoring():
    # Retrieve existing seeded tender
    tenders_res = client.get("/api/v1/gov/tenders?craft_category=Textile")
    assert tenders_res.status_code == 200
    tender_id = tenders_res.json()[0]["id"]

    bid_payload = {
        "artisan_business_name": "Telangana Master Weavers Producer Guild",
        "bid_unit_price": 1600.00,
        "proposed_delivery_days": 40,
        "technical_proposal": "GI Tagged authentic double ikat mulberry silk weave, verified by Ministry of Textiles Silk Mark.",
        "is_msme_registered": True,
        "msme_udyam_number": "UDYAM-TS-08-9918273",
        "is_gi_certified": True,
        "gi_certificate_number": "GI-TAG-TS-0091",
        "shg_member_count": 120
    }
    response = client.post(f"/api/v1/gov/tenders/{tender_id}/bids", json=bid_payload)
    assert response.status_code in (200, 201)
    bid = response.json()
    assert bid["artisan_business_name"] == bid_payload["artisan_business_name"]
    assert bid["is_gi_certified"] is True
    assert bid["is_msme_registered"] is True
    assert bid["technical_score"] >= 95.0  # Earned GI + MSME bonus
    assert bid["total_evaluation_score"] >= 90.0

    # List bids
    bids_res = client.get(f"/api/v1/gov/tenders/{tender_id}/bids")
    assert bids_res.status_code == 200
    assert len(bids_res.json()) >= 1


def test_evaluate_and_award_tender_contract():
    tenders_res = client.get("/api/v1/gov/tenders")
    assert tenders_res.status_code == 200
    # Find a tender that has bids
    tenders_with_bids = [t for t in tenders_res.json() if t.get("bids_count", 0) > 0]
    if tenders_with_bids:
        tender_id = tenders_with_bids[0]["id"]
    else:
        tender_id = tenders_res.json()[0]["id"]
        # Submit a bid first
        client.post(f"/api/v1/gov/tenders/{tender_id}/bids", json={
            "artisan_business_name": "Jaipur Master Clay Works",
            "bid_unit_price": 1600.0,
            "proposed_delivery_days": 30,
            "technical_proposal": "Handmade GI blue pottery",
            "is_msme_registered": True,
            "is_gi_certified": True,
            "shg_member_count": 20
        })

    eval_payload = {
        "custom_terms": {
            "packaging_rule": "Eco-friendly recyclable cardboard gift boxes with KalaCart QR seal"
        }
    }
    award_res = client.post(f"/api/v1/gov/tenders/{tender_id}/evaluate-and-award", json=eval_payload)
    assert award_res.status_code in (200, 201)
    award = award_res.json()
    assert award["status"] == "active"
    assert award["buyer_signed"] is True
    assert award["artisan_signed"] is True
    assert award["total_contract_value"] > 0
    assert "contract_number" in award

    # Verify Tender status transitioned to awarded
    tender_res = client.get(f"/api/v1/gov/tenders/{tender_id}")
    assert tender_res.json()["lifecycle_stage"] == "awarded"

    # Verify Milestones created
    contract_id = award["id"]
    ms_res = client.get(f"/api/v1/gov/contracts/{contract_id}/milestones")
    assert ms_res.status_code == 200
    milestones = ms_res.json()
    assert len(milestones) == 4
    assert milestones[0]["percentage"] == 20.0
    assert milestones[0]["status"] == "paid"  # Mobilization advance paid on signing
    assert milestones[1]["percentage"] == 40.0
    assert milestones[2]["percentage"] == 30.0
    assert milestones[3]["percentage"] == 10.0


def test_milestone_progression_and_escrow_release():
    contracts_res = client.get("/api/v1/gov/contracts")
    assert contracts_res.status_code == 200
    assert len(contracts_res.json()) >= 1
    contract_id = contracts_res.json()[0]["id"]

    ms_res = client.get(f"/api/v1/gov/contracts/{contract_id}/milestones")
    milestones = ms_res.json()
    ms2 = milestones[1]

    # 1. Artisan submits inspection proof
    proof_payload = {
        "action": "submit_proof",
        "verification_doc_urls": ["https://kalacart.in/reports/quality_inspection_batch1.pdf"],
        "remarks": "Batch 1 (50% production) completed and GI quality checked."
    }
    res1 = client.post(f"/api/v1/gov/contracts/{contract_id}/milestones/{ms2['id']}/action", json=proof_payload)
    assert res1.status_code == 200
    assert res1.json()["status"] == "submitted_for_approval"

    # 2. Buyer approves
    approve_payload = {
        "action": "approve",
        "remarks": "Inspection verified by Quality Assurance Officer."
    }
    res2 = client.post(f"/api/v1/gov/contracts/{contract_id}/milestones/{ms2['id']}/action", json=approve_payload)
    assert res2.status_code == 200
    assert res2.json()["status"] == "approved"
    assert res2.json()["approved_by_buyer"] is True

    # 3. Release escrow payout
    payout_payload = {
        "action": "release_payment",
        "remarks": "Escrow tranche 2 disbursed to artisan cooperative bank account."
    }
    res3 = client.post(f"/api/v1/gov/contracts/{contract_id}/milestones/{ms2['id']}/action", json=payout_payload)
    assert res3.status_code == 200
    assert res3.json()["status"] == "paid"
    assert "ESCROW-TXN" in res3.json()["escrow_transaction_id"]


def test_all_seven_buyer_types_supported():
    buyer_types = ["government", "ngo", "csr", "school", "museum", "tourism", "hotel"]
    for b_type in buyer_types:
        payload = {
            "organization_name": f"Test Organization for {b_type.upper()}",
            "buyer_type": b_type,
            "department": "Procurement",
            "nodal_officer_name": "Test Officer",
            "nodal_officer_email": f"procurement@{b_type}.org",
            "allocated_annual_budget": 5000000.00
        }
        res = client.post("/api/v1/gov/buyers/register", json=payload)
        assert res.status_code in (200, 201)
        assert res.json()["buyer_type"] == b_type
