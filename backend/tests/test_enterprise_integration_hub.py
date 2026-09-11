"""
Unit & Integration Tests for Phase 9 Enterprise Integration Hub.
Covers:
- Connectors for Tally, ERPNext, Zoho Books, SAP, and QuickBooks
- Bi-Directional Order, Stock, GST, Invoice, and Customer Sync
- Outbound Webhook Dispatch with Retry Queues
- Integration Hub REST API Endpoints
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.enterprise_integration import enterprise_hub
from app.services.enterprise_connectors import (
    get_connector,
    TallyConnector,
    ERPNextConnector,
    ZohoBooksConnector,
    SAPConnector,
    QuickBooksConnector,
)

client = TestClient(app)


def test_erp_connector_factory_and_adapters():
    """Verify all 5 enterprise ERP connectors instantiate and format orders accurately."""
    sample_order = {
        "id": "ORD-5501",
        "buyer_name": "FabIndia Crafts Ltd",
        "buyer_gstin": "27AAACF1234F1Z0",
        "total_amount": 18500.0,
        "items": [{"product_id": "prod_silk_01", "quantity": 5, "unit_price": 3700.0}],
    }

    # 1. Tally XML Voucher
    tally = get_connector("tally", "http://localhost:9000")
    assert isinstance(tally, TallyConnector)
    tally_res = tally.sync_order(sample_order)
    assert tally_res["status"] == "synced"
    assert "TALLY-VCH-ORD-5501" in tally_res["external_voucher_no"]

    # 2. ERPNext JSON Doc
    erpnext = get_connector("erpnext", "https://erp.kalacart.in")
    assert isinstance(erpnext, ERPNextConnector)
    erp_res = erpnext.sync_order(sample_order)
    assert erp_res["status"] == "synced"
    assert erp_res["doc"]["doctype"] == "Sales Order"

    # 3. Zoho Books
    zoho = get_connector("zoho_books", "https://books.zoho.in")
    assert isinstance(zoho, ZohoBooksConnector)
    zoho_res = zoho.sync_order(sample_order)
    assert zoho_res["status"] == "synced"
    assert "ZH-SO-ORD-5501" in zoho_res["zoho_salesorder_id"]

    # 4. SAP S/4HANA
    sap = get_connector("sap", "https://sap.kalacart.in")
    assert isinstance(sap, SAPConnector)
    sap_res = sap.sync_order(sample_order)
    assert sap_res["status"] == "synced"
    assert "distribution_channel" in sap_res

    # 5. QuickBooks Online
    qb = get_connector("quickbooks", "https://quickbooks.api.intuit.com")
    assert isinstance(qb, QuickBooksConnector)
    qb_res = qb.sync_order(sample_order)
    assert qb_res["status"] == "synced"
    assert "QB-INV-ORD-5501" in qb_res["qb_estimate_or_invoice_id"]


def test_enterprise_hub_sync_job_lifecycle():
    """Verify triggering synchronization jobs across different entity types."""
    # 1. Inventory Sync on ERPNext
    inv_job = enterprise_hub.trigger_sync(
        account_id="acc-erpnext-01",
        sync_type="inventory",
        entity_payload={"items": [{"product_id": "prod_1", "stock": 100}]},
    )
    assert inv_job.status == "completed"
    assert inv_job.records_processed == 1

    # 2. GST / Invoice Sync on Zoho Books
    gst_job = enterprise_hub.trigger_sync(
        account_id="acc-zoho-01",
        sync_type="gst",
        entity_payload={"invoice_number": "INV-2026-99", "total_amount": 12000.0},
    )
    assert gst_job.status == "completed"
    assert gst_job.payload_summary["status"] == "synced"

    # 3. Customer Sync on SAP
    cust_job = enterprise_hub.trigger_sync(
        account_id="acc-sap-01",
        sync_type="customers",
        entity_payload={"name": "Kashmir Crafts Hub", "phone": "+919811122233"},
    )
    assert cust_job.status == "completed"


def test_webhook_dispatch_and_retry_queue():
    """Verify outbound webhook event recording and retry structure."""
    evt = enterprise_hub.dispatch_webhook(
        event_type="order.created",
        target_url="https://webhook.site/test-endpoint",
        payload={"order_id": "ORD-999", "amount": 4500.0},
        account_id="acc-tally-01",
    )
    assert evt.status == "delivered"
    assert evt.http_status_code == 200
    assert len(enterprise_hub.webhook_events) >= 1


def test_enterprise_integration_api_endpoints():
    """Test all Phase 9 Enterprise Integration Hub REST endpoints."""
    # 1. Summary
    r_sum = client.get("/api/v1/integrations/summary")
    assert r_sum.status_code == 200
    assert r_sum.json()["status"] == "success"
    assert len(r_sum.json()["data"]["supported_connectors"]) == 5

    # 2. Connect new account
    r_conn = client.post(
        "/api/v1/integrations/accounts/connect",
        json={
            "artisan_id": "artisan-custom-01",
            "provider": "tally",
            "account_name": "Artisan Custom Tally",
            "auth_type": "xml_rpc",
            "endpoint_url": "http://localhost:9000",
            "gstin": "29AAAAA0000A1Z5",
        },
    )
    assert r_conn.status_code == 200
    assert r_conn.json()["status"] == "success"

    # 3. Trigger sync via API
    r_sync = client.post(
        "/api/v1/integrations/sync/trigger",
        json={"account_id": "acc-tally-01", "sync_type": "orders"},
    )
    assert r_sync.status_code == 200
    assert r_sync.json()["sync_job"]["status"] == "completed"

    # 4. Dispatch webhook via API
    r_wh = client.post(
        "/api/v1/integrations/webhooks/dispatch",
        json={
            "event_type": "order.fulfilled",
            "target_url": "https://erp.client.com/webhook",
            "payload": {"order_id": "ORD-8888", "tracking_number": "TRACK-1234"},
        },
    )
    assert r_wh.status_code == 200
    assert r_wh.json()["status"] == "dispatched"
