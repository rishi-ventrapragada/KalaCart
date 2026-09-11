from fastapi.testclient import TestClient
from datetime import datetime, timedelta
import pytest
from app.main import app
from app.core.security import get_current_user

@pytest.fixture(autouse=True)
def override_auth():
    app.dependency_overrides[get_current_user] = lambda: {
        "uid": "test-buyer-123",
        "email": "buyer@tajhotels.example.com",
        "name": "Taj Procurement Director",
        "role": "buyer"
    }
    yield
    app.dependency_overrides.clear()

def test_full_b2b_tender_procurement_lifecycle():
    client = TestClient(app)
    
    # 1. Buyer (Hotel chain) posts bulk procurement tender for 500 handcrafted brass lamps
    deadline = (datetime.utcnow() + timedelta(days=30)).isoformat()
    create_tender_payload = {
        "buyer_organization_name": "Taj Palace & Resorts",
        "buyer_type": "hotel",
        "title": "500 Handcrafted Brass Dhokra Floor Lamps for Lobby Renovation",
        "description": "Seeking certified authentic Dhokra brass floor lamps (2.5ft height) with antique patina finish.",
        "category_id": "brass_dhokra_craft",
        "target_quantity": 500,
        "target_unit_price": 3200.0,
        "max_budget": 1600000.0,
        "delivery_deadline": deadline,
        "delivery_location": "Taj Palace, Sardar Patel Marg, New Delhi 110021",
        "technical_specs": {
            "height_inches": 30,
            "weight_kg": 4.5,
            "metal": "Virgin Brass & Bronze Alloy",
            "certification": "National Handloom and Handicrafts Board / GI Tagged"
        },
        "attachment_urls": ["https://storage.kalacart.in/tenders/taj_lamp_blueprint.pdf"]
    }
    
    res = client.post("/api/v1/procurement/tenders", json=create_tender_payload)
    assert res.status_code == 201, res.text
    tender = res.json()
    tender_id = tender["id"]
    assert tender["status"] == "open"
    assert tender["buyer_organization_name"] == "Taj Palace & Resorts"
    assert tender["target_quantity"] == 500

    # 2. List open tenders
    res_list = client.get("/api/v1/procurement/tenders")
    assert res_list.status_code == 200
    tenders = res_list.json()
    assert any(t["id"] == tender_id for t in tenders)

    # 3. Artisan 1 submits a competitive tender bid
    app.dependency_overrides[get_current_user] = lambda: {
        "uid": "artisan-bastar-001",
        "email": "ramesh.dhokra@bastar.in",
        "name": "Ramesh Baghel",
        "role": "seller"
    }

    bid_payload_1 = {
        "artisan_business_name": "Bastar Dhokra Master Craftsmen Collective",
        "bid_unit_price": 3100.0,
        "proposed_delivery_days": 25,
        "technical_proposal": "Lost-wax bell metal casting using traditional clay core and beeswax molds with 100% genuine antique brass.",
        "certificate_urls": ["https://storage.kalacart.in/certs/gi_bastar_dhokra_cert.pdf"],
        "sample_image_urls": ["https://storage.kalacart.in/samples/dhokra_lamp_sample1.jpg"]
    }
    res_bid1 = client.post(f"/api/v1/procurement/tenders/{tender_id}/bids", json=bid_payload_1)
    assert res_bid1.status_code == 201, res_bid1.text
    bid_1 = res_bid1.json()
    assert bid_1["total_bid_amount"] == 3100.0 * 500  # 1,550,000
    assert bid_1["status"] == "submitted"

    # 4. Artisan 2 submits another competitive bid
    app.dependency_overrides[get_current_user] = lambda: {
        "uid": "artisan-moradabad-002",
        "email": "suresh.brass@moradabad.in",
        "name": "Suresh Brass Works",
        "role": "seller"
    }
    bid_payload_2 = {
        "artisan_business_name": "Moradabad Brass Guild",
        "bid_unit_price": 3300.0,
        "proposed_delivery_days": 20,
        "technical_proposal": "Die-cast brass with etched floral embossing and double clear lacquer coat.",
        "certificate_urls": ["https://storage.kalacart.in/certs/iso_9001_moradabad.pdf"],
        "sample_image_urls": ["https://storage.kalacart.in/samples/moradabad_lamp_sample.jpg"]
    }
    res_bid2 = client.post(f"/api/v1/procurement/tenders/{tender_id}/bids", json=bid_payload_2)
    assert res_bid2.status_code == 201
    bid_2 = res_bid2.json()

    # 5. Buyer reviews & evaluates submitted bids
    app.dependency_overrides[get_current_user] = lambda: {
        "uid": "test-buyer-123",
        "email": "buyer@tajhotels.example.com",
        "name": "Taj Procurement Director",
        "role": "buyer"
    }

    res_bids_list = client.get(f"/api/v1/procurement/tenders/{tender_id}/bids")
    assert res_bids_list.status_code == 200
    bids = res_bids_list.json()
    assert len(bids) == 2

    # Buyer scores Bastar collective with 96/100 (GI authenticity & great price)
    res_eval = client.post(f"/api/v1/procurement/bids/{bid_1['id']}/evaluate", json={
        "evaluation_score": 96.0,
        "evaluation_notes": "Exceptional GI craft authenticity, highly compliant technical sample and below budget.",
        "status": "shortlisted"
    })
    assert res_eval.status_code == 200
    assert res_eval.json()["evaluation_score"] == 96.0
    assert res_eval.json()["status"] == "shortlisted"

    # 6. Buyer awards contract to Bastar Master Craftsmen
    award_payload = {
        "bid_id": bid_1["id"],
        "contract_terms": {
            "jurisdiction": "Delhi High Court / National Crafts Council",
            "quality_standard": "GI Tagged Certified Lost-Wax Casting Grade A",
            "escrow_guarantee": "100% Escrow backed milestone release"
        }
    }
    res_award = client.post(f"/api/v1/procurement/tenders/{tender_id}/award", json=award_payload)
    assert res_award.status_code == 200, res_award.text
    contract = res_award.json()
    assert contract["procurement_id"] == tender_id
    assert contract["bid_id"] == bid_1["id"]
    assert contract["artisan_id"] == "artisan-bastar-001"
    assert contract["total_contract_value"] == 1550000.0
    assert contract["status"] == "active"
    assert len(contract["milestones"]) == 3
    assert contract["milestones"][0]["milestone_name"] == "Advance Material Sourcing (30%)"
    assert contract["milestones"][0]["amount"] == 465000.0

    # 7. Check Contracts List
    res_contracts = client.get("/api/v1/procurement/contracts")
    assert res_contracts.status_code == 200
    contracts = res_contracts.json()
    assert any(c["id"] == contract["id"] for c in contracts)
