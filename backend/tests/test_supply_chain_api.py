from fastapi.testclient import TestClient
import pytest
from app.main import app
from app.core.security import get_current_user

@pytest.fixture(autouse=True)
def override_auth():
    app.dependency_overrides[get_current_user] = lambda: {
        "uid": "artisan-raghurajpur-001",
        "email": "laxman.patachitra@odisha.in",
        "name": "Laxman Maharana",
        "role": "seller"
    }
    yield
    app.dependency_overrides.clear()

def test_browse_raw_materials_and_filter():
    client = TestClient(app)

    # 1. Fetch all raw materials
    res = client.get("/api/v1/supply-chain/materials")
    assert res.status_code == 200
    materials = res.json()
    assert len(materials) >= 4
    categories = [m["material_category"] for m in materials]
    assert "clay" in categories
    assert "brass" in categories
    assert "bamboo" in categories
    assert "fabric" in categories

    # 2. Filter by category
    res_clay = client.get("/api/v1/supply-chain/materials?category=clay")
    assert res_clay.status_code == 200
    clay_items = res_clay.json()
    assert len(clay_items) == 1
    assert clay_items[0]["material_category"] == "clay"
    assert "Terracotta" in clay_items[0]["title"]

def test_ai_recommend_suppliers():
    client = TestClient(app)

    req = {
        "material_category": "clay",
        "quantity": 5,
        "artisan_state": "Odisha",
        "artisan_city": "Puri",
        "prioritize": "distance"
    }

    res = client.post("/api/v1/supply-chain/recommend-suppliers", json=req)
    assert res.status_code == 200
    data = res.json()
    assert data["material_category"] == "clay"
    assert len(data["recommended_suppliers"]) >= 1

    top = data["recommended_suppliers"][0]
    assert top["composite_score"] > 80.0
    assert top["distance_score"] >= 90.0
    assert "Khurda" in top["recommendation_reason"] or "Odisha" in top["supplier"]["state"]

def test_purchase_request_and_supplier_quote_lifecycle():
    client = TestClient(app)

    # 1. Artisan creates purchase request for 2 tons of clay
    req_payload = {
        "material_id": "mat-clay-01",
        "quantity_requested": 2,
        "max_budget_inr": 9000.0,
        "is_group_purchase": False,
        "delivery_location": "Craft Studio, Raghurajpur Craft Village, Puri, Odisha 752012"
    }
    res_req = client.post("/api/v1/supply-chain/purchase-requests", json=req_payload)
    assert res_req.status_code == 201, res_req.text
    req_obj = res_req.json()
    req_id = req_obj["id"]
    assert req_obj["status"] == "open"
    assert req_obj["quantity_requested"] == 2

    # 2. Supplier submits quote
    quote_payload = {
        "purchase_request_id": req_id,
        "quote_unit_price": 4150.0,
        "estimated_delivery_days": 2,
        "quality_notes": "100-mesh screened clay delivered via dedicated mini-truck."
    }
    res_quote = client.post("/api/v1/supply-chain/quotes", json=quote_payload)
    assert res_quote.status_code == 201, res_quote.text
    quote_obj = res_quote.json()
    quote_id = quote_obj["id"]
    assert quote_obj["total_amount_inr"] == 8300.0
    assert quote_obj["status"] == "submitted"

    # 3. Artisan accepts quote and orders inside KalaCart
    res_accept = client.post(f"/api/v1/supply-chain/quotes/{quote_id}/accept")
    assert res_accept.status_code == 200
    accepted = res_accept.json()
    assert accepted["status"] == "accepted"

def test_group_purchase_pools():
    client = TestClient(app)

    res = client.get("/api/v1/supply-chain/group-pools")
    assert res.status_code == 200
    pools = res.json()
    assert len(pools) >= 2
    brass_pool = next(p for p in pools if p["material_category"] == "brass")
    assert brass_pool["unlocked_discount_percent"] == 30.0
    assert brass_pool["pool_completion_percent"] == 84.0
