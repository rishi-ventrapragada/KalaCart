import pytest
import time
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

API_KEY = "kc_live_testpartner9999"
CLIENT_ID = "kc_live_testpartner9999"
CLIENT_SECRET = "sec_sandbox_998877665544332211"


def test_oauth2_token_client_credentials():
    payload = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope": "products:read stores:read orders:read"
    }
    res = client.post("/api/v1/public/oauth/token", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "Bearer"
    assert "products:read" in data["scope"]


def test_api_key_scopes_list():
    res = client.get("/api/v1/developer/scopes")
    assert res.status_code == 200
    data = res.json()["data"]
    assert len(data) >= 10
    assert any(s["scope"] == "products:read" for s in data)
    assert any(s["scope"] == "orders:write" for s in data)


def test_provision_and_revoke_api_key():
    # 1. Provision
    payload = {
        "partner_name": "FabIndia Automated Integration",
        "scopes": ["products:read", "orders:write", "rfqs:read"],
        "tier": "enterprise"
    }
    res = client.post("/api/v1/developer/keys", json=payload)
    assert res.status_code == 201
    key_data = res.json()["data"]
    assert key_data["partner_name"] == "FabIndia Automated Integration"
    assert key_data["rate_limit_per_min"] == 600
    assert "raw_api_key" in key_data
    assert "client_secret" in key_data

    # 2. Test access using new key
    new_key = key_data["raw_api_key"]
    res_access = client.get("/api/v1/public/products", headers={"X-API-Key": new_key})
    assert res_access.status_code == 200

    # 3. Revoke
    res_del = client.delete(f"/api/v1/developer/keys/{key_data['id']}")
    assert res_del.status_code == 200
    assert res_del.json()["data"]["is_active"] is False

    # 4. Ensure revoked key cannot access
    res_revoked = client.get("/api/v1/public/products", headers={"X-API-Key": new_key})
    assert res_revoked.status_code == 403


def test_public_products_api():
    headers = {"X-API-Key": API_KEY}
    res = client.get("/api/v1/public/products", headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert len(data) > 0
    assert any("Jaipur" in p["title"] for p in data)

    # Test single product
    pid = data[0]["id"]
    res_single = client.get(f"/api/v1/public/products/{pid}", headers=headers)
    assert res_single.status_code == 200
    assert res_single.json()["data"]["id"] == pid


def test_public_stores_api():
    headers = {"X-API-Key": API_KEY}
    res = client.get("/api/v1/public/stores", headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert len(data) > 0

    # By slug
    res_slug = client.get("/api/v1/public/stores/rajesh-heritage-pottery", headers=headers)
    assert res_slug.status_code == 200
    assert res_slug.json()["data"]["slug"] == "rajesh-heritage-pottery"


def test_public_orders_and_rfqs_api():
    headers = {"X-API-Key": API_KEY}
    
    # 1. Create Order
    order_payload = {
        "product_id": "prod-public-001",
        "quantity": 2,
        "buyer_name": "FabIndia Purchasing",
        "buyer_email": "procurement@fabindia.com",
        "shipping_address": "123 Commercial St, Bengaluru",
        "delivery_city": "Bengaluru",
        "pincode": "560001"
    }
    res_order = client.post("/api/v1/public/orders", headers=headers, json=order_payload)
    assert res_order.status_code == 201
    assert "order_id" in res_order.json()["data"]

    # 2. Create RFQ
    rfq_payload = {
        "craft_category": "Pottery & Ceramics",
        "specifications": "GI Tagged Jaipur Blue Pottery Tea Sets",
        "quantity": 50,
        "target_budget_inr": 120000.0,
        "required_by_date": "2026-10-30",
        "company_name": "Heritage Crafts Living",
        "contact_email": "rfq@heritagecrafts.in"
    }
    res_rfq = client.post("/api/v1/public/rfqs", headers=headers, json=rfq_payload)
    assert res_rfq.status_code == 201
    assert "rfq_id" in res_rfq.json()["data"]


def test_public_analytics_payments_notifications_reviews():
    headers = {"X-API-Key": API_KEY}

    # Analytics
    res_ana = client.get("/api/v1/public/analytics", headers=headers)
    assert res_ana.status_code == 200
    assert res_ana.json()["data"]["national_active_clusters"] > 0

    # Payments Intent
    res_pay = client.post("/api/v1/public/payments/create-intent", headers=headers, json={"amount": 4500.0, "currency": "INR"})
    assert res_pay.status_code == 200
    assert "payment_intent_id" in res_pay.json()["data"]

    # Notifications Dispatch
    res_notif = client.post("/api/v1/public/notifications", headers=headers, json={"recipient": "+919876543210", "channel": "WHATSAPP"})
    assert res_notif.status_code == 200
    assert res_notif.json()["data"]["status"] == "QUEUED"

    # Reviews
    res_rev = client.get("/api/v1/public/reviews", headers=headers)
    assert res_rev.status_code == 200
    assert len(res_rev.json()["data"]) > 0


def test_webhook_lifecycle_and_test_ping():
    # 1. Register Webhook
    payload = {
        "target_url": "https://custom-erp.partner.in/webhook",
        "events": ["order.created", "order.status_changed"]
    }
    res = client.post("/api/v1/developer/webhooks", json=payload)
    assert res.status_code == 201
    wh = res.json()["data"]
    assert "secret_token" in wh
    wh_id = wh["id"]

    # 2. Ping Test
    res_test = client.post(f"/api/v1/developer/webhooks/{wh_id}/test", json={"event_type": "order.created"})
    assert res_test.status_code == 200
    deliveries = res_test.json()["data"]
    assert len(deliveries) > 0
    assert deliveries[0]["delivery_status"] == "success"
    assert deliveries[0]["signature"].startswith("sha256=")

    # 3. Inspect Deliveries
    res_del = client.get(f"/api/v1/developer/webhooks/{wh_id}/deliveries")
    assert res_del.status_code == 200
    assert len(res_del.json()["data"]) > 0

    # 4. Remove Webhook
    res_rm = client.delete(f"/api/v1/developer/webhooks/{wh_id}")
    assert res_rm.status_code == 200



