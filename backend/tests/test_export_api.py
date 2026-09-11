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

def test_currencies_and_conversion():
    client = TestClient(app)

    # 1. Fetch supported currencies
    res = client.get("/api/v1/export/currencies")
    assert res.status_code == 200
    currencies = res.json()
    codes = [c["code"] for c in currencies]
    assert "USD" in codes
    assert "EUR" in codes
    assert "GBP" in codes
    assert "AED" in codes

    # 2. Convert ₹2500 INR to USD
    res_conv = client.post("/api/v1/export/convert", json={
        "amount_inr": 2500.0,
        "target_currency": "USD"
    })
    assert res_conv.status_code == 200
    data = res_conv.json()
    assert data["target_currency"] == "USD"
    assert data["symbol"] == "$"
    assert round(2500.0 / 83.50, 2) == data["converted_amount"]

def test_hsn_codes_lookup():
    client = TestClient(app)

    # Search for terracotta
    res = client.get("/api/v1/export/hsn-codes?query=pottery")
    assert res.status_code == 200
    items = res.json()
    assert len(items) >= 1
    assert items[0]["hsn_code"] == "691200"
    assert "lead-free" in items[0]["compliance_notes"].lower()

def test_product_export_configuration_and_pricing():
    client = TestClient(app)

    prod_id = "prod-pattachitra-999"
    config_payload = {
        "product_id": prod_id,
        "hsn_code": "520811",
        "export_ready": True,
        "customs_declaration_desc": "Hand-painted traditional palm leaf Pattachitra scroll artwork",
        "weight_grams": 450,
        "length_cm": 30.0,
        "width_cm": 20.0,
        "height_cm": 5.0,
        "lead_time_days": 5,
        "origin_state": "Odisha",
        "country_restrictions": []
    }

    res_post = client.post(f"/api/v1/export/products/{prod_id}", json=config_payload)
    assert res_post.status_code == 201, res_post.text
    prod = res_post.json()
    assert prod["hsn_code"] == "520811"
    assert len(prod["multi_currency_prices"]) >= 4

    # Verify retrieval
    res_get = client.get(f"/api/v1/export/products/{prod_id}")
    assert res_get.status_code == 200
    assert res_get.json()["product_id"] == prod_id

def test_international_shipping_estimation():
    client = TestClient(app)

    shipping_req = {
        "destination_country": "USA",
        "destination_postal_code": "10001",
        "weight_grams": 1500,
        "length_cm": 35.0,
        "width_cm": 25.0,
        "height_cm": 15.0,
        "product_value_inr": 8500.0
    }

    res = client.post("/api/v1/export/shipping-estimate", json=shipping_req)
    assert res.status_code == 200
    data = res.json()
    assert data["destination_country"] == "USA"
    assert len(data["courier_options"]) == 3
    carriers = [c["carrier_name"] for c in data["courier_options"]]
    assert any("DHL" in c for c in carriers)
    assert any("FedEx" in c for c in carriers)
    assert any("India Post" in c for c in carriers)
    assert data["estimated_import_duty_usd"] > 0

def test_generate_export_compliance_documents():
    client = TestClient(app)

    order_id = "order-export-555"
    res = client.post(f"/api/v1/export/documents/{order_id}/generate?destination_country=Germany")
    assert res.status_code == 200
    docs = res.json()
    assert docs["order_id"] == order_id
    assert docs["destination_country"] == "Germany"
    assert "KC-EXP-" in docs["export_invoice_number"]
    assert docs["commercial_invoice"]["incoterms"] == "DAP (Delivered at Place)"
    assert docs["packing_list"]["total_packages"] == 1
    assert "Certificate of Origin" in docs["certificate_of_origin"]["goods_description"] or "EPCH" in docs["certificate_of_origin"]["issuing_authority"]
