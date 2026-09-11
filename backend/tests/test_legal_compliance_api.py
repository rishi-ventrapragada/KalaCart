"""
Test suite for Legal, Compliance, DPDP, and GST endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_get_policies_index():
    res = client.get("/api/v1/legal/policies")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    keys = [p["key"] for p in data["policies"]]
    assert "privacy_policy" in keys
    assert "terms_of_service" in keys
    assert "seller_agreement" in keys
    assert "buyer_agreement" in keys
    assert "refund_policy" in keys
    assert "shipping_policy" in keys
    assert "community_guidelines" in keys
    assert "data_retention_policy" in keys

def test_get_individual_policy():
    res = client.get("/api/v1/legal/policies/privacy_policy")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "DPDP Act" in data["policy"]["content"]

def test_dpdp_checklist():
    res = client.get("/api/v1/legal/dpdp-checklist")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert len(data["dpdp_compliance"]) == 5

def test_gst_compliance_standards():
    res = client.get("/api/v1/legal/gst-compliance")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "hsn_classification" in data["gst_standards"]

