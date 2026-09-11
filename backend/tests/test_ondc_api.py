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

def test_ondc_publish_and_catalog_mapping():
    client = TestClient(app)

    prod_id = "prod-dhokra-lamp-88"
    publish_req = {
        "product_id": prod_id,
        "product_name": "Authentic Bastar Dhokra Brass Floor Lamp",
        "product_description": "Lost-wax cast bell metal floor lamp hand-poured by tribal master artisans in Bastar.",
        "price_inr": 3450.0,
        "stock_quantity": 25,
        "category_id": "Handicrafts & Handlooms",
        "artisan_cluster_location": "Bastar, Chhattisgarh",
        "time_to_ship_days": 3,
        "image_urls": ["https://storage.kalacart.in/crafts/dhokra_lamp.jpg"]
    }

    # 1. Publish to ONDC
    res_pub = client.post(f"/api/v1/ondc/products/{prod_id}/publish", json=publish_req)
    assert res_pub.status_code == 201, res_pub.text
    ondc_prod = res_pub.json()
    assert ondc_prod["domain"] == "ONDC:RET12"
    assert ondc_prod["bpp_id"] == "bpp.kalacart.in"
    assert "KC-ONDC-" in ondc_prod["network_item_id"]
    assert ondc_prod["beckn_payload"]["descriptor"]["name"] == "Authentic Bastar Dhokra Brass Floor Lamp"

    # 2. List published products
    res_list = client.get("/api/v1/ondc/products")
    assert res_list.status_code == 200
    prods = res_list.json()
    assert any(p["product_id"] == prod_id for p in prods)

def test_ondc_inventory_sync():
    client = TestClient(app)

    prod_id = "prod-dhokra-lamp-88"
    sync_req = {
        "product_id": prod_id,
        "new_stock_quantity": 18
    }
    res = client.post("/api/v1/ondc/inventory/sync", json=sync_req)
    assert res.status_code == 200
    inv = res.json()
    assert inv["synced_stock_quantity"] == 18
    assert inv["is_available_on_network"] is True

def test_ondc_incoming_order_and_cancellation():
    client = TestClient(app)

    net_order_id = "ONDC-ORD-998822"
    incoming_order = {
        "network_order_id": net_order_id,
        "bap_id": "paytm.ondc.buyer.in",
        "bap_uri": "https://ondc.paytm.com/bap",
        "transaction_id": "txn-55443322",
        "message_id": "msg-11223344",
        "network_item_id": "KC-ONDC-PROD-DHO",
        "quantity": 2,
        "unit_price_inr": 3450.0,
        "buyer_name": "Rohan Deshmukh",
        "buyer_phone": "+919876541234",
        "delivery_address": "Flat 402, Lotus Towers, Pune 411038",
        "delivery_pincode": "411038"
    }

    # 1. Ingest order
    res_order = client.post("/api/v1/ondc/orders/incoming", json=incoming_order)
    assert res_order.status_code == 201, res_order.text
    order = res_order.json()
    assert order["network_order_id"] == net_order_id
    assert order["total_value_inr"] == 6900.0
    assert order["state"] == "Accepted"

    # 2. List orders
    res_list = client.get("/api/v1/ondc/orders")
    assert res_list.status_code == 200
    orders = res_list.json()
    assert any(o["network_order_id"] == net_order_id for o in orders)

    # 3. Buyer Cancels Order via ONDC
    cancel_req = {
        "cancellation_reason_code": "001",
        "cancellation_description": "Buyer ordered alternate craft item"
    }
    res_cancel = client.post(f"/api/v1/ondc/orders/{net_order_id}/cancel", json=cancel_req)
    assert res_cancel.status_code == 200
    canceled_order = res_cancel.json()
    assert canceled_order["state"] == "Cancelled"
    assert canceled_order["cancellation_reason_code"] == "001"

def test_ondc_sync_logs_audit():
    client = TestClient(app)

    res = client.get("/api/v1/ondc/sync-logs")
    assert res.status_code == 200
    logs = res.json()
    assert len(logs) >= 3
    types = [l["sync_type"] for l in logs]
    assert "catalog_publish" in types
    assert "inventory_sync" in types
    assert "cancellation" in types
