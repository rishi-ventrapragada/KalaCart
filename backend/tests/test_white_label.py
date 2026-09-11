"""
Test Suite for White-Label Multi-Tenant Platform (Phase 9)
Verifies:
- Complete isolation between multiple government/NGO tenants (e.g., UP ODOP vs. TRIFED)
- Custom branding resolution by domain host and slug
- Policy, payment gateway, category, and district customizations
- Dynamic tenant provisioning & custom domain mapping
- Isolated tenant analytics and revenue separation
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_list_tenants():
    response = client.get("/api/v1/tenants/list")
    assert response.status_code == 200
    data = response.json()
    assert "count" in data
    assert "tenants" in data
    assert data["count"] >= 2
    slugs = [t["tenant_slug"] for t in data["tenants"]]
    assert "up-odop" in slugs
    assert "trifed-tribal" in slugs


def test_resolve_tenant_by_domain():
    # 1. Resolve UP ODOP via custom domain
    res_up = client.get("/api/v1/tenants/resolve?domain=odop.up.gov.in")
    assert res_up.status_code == 200
    data_up = res_up.json()["tenant"]
    assert data_up["tenant_slug"] == "up-odop"
    assert data_up["branding"]["brand_name"] == "UP ODOP Bazaar"
    assert data_up["branding"]["primary_color"] == "#1E3A8A"
    assert data_up["payment_settings"]["primary_gateway"] == "billdesk"
    assert "Varanasi" in data_up["supported_districts"]
    assert data_up["policies"]["gi_mandatory"] is True

    # 2. Resolve TRIFED via header
    res_tr = client.get("/api/v1/tenants/resolve", headers={"X-Tenant-Domain": "tribesindia.com"})
    assert res_tr.status_code == 200
    data_tr = res_tr.json()["tenant"]
    assert data_tr["tenant_slug"] == "trifed-tribal"
    assert data_tr["branding"]["brand_name"] == "Tribes India"
    assert data_tr["branding"]["primary_color"] == "#065F46"
    assert data_tr["payment_settings"]["primary_gateway"] == "razorpay"
    assert "Bastar" in data_tr["supported_districts"]
    assert data_tr["policies"]["commission_fee_pct"] == 0.0


def test_isolated_tenant_analytics():
    # Verify UP ODOP analytics are separate from TRIFED analytics
    res_up = client.get("/api/v1/tenants/resolve?domain=up-odop")
    up_id = res_up.json()["tenant"]["id"]

    res_tr = client.get("/api/v1/tenants/resolve?domain=trifed-tribal")
    tr_id = res_tr.json()["tenant"]["id"]

    analytics_up = client.get(f"/api/v1/tenants/{up_id}/analytics").json()
    analytics_tr = client.get(f"/api/v1/tenants/{tr_id}/analytics").json()

    assert analytics_up["tenant_slug"] == "up-odop"
    assert analytics_up["total_orders"] == 2
    assert analytics_up["gross_gmv_inr"] == 20900.0
    assert "Varanasi" in analytics_up["district_breakdown"]

    assert analytics_tr["tenant_slug"] == "trifed-tribal"
    assert analytics_tr["total_orders"] == 3
    assert analytics_tr["gross_gmv_inr"] == 9500.0
    assert "Bastar" in analytics_tr["district_breakdown"]


def test_provision_new_tenant_and_add_domain():
    provision_payload = {
        "tenant_slug": "kerala-craft-heritage",
        "organization_name": "Kerala State Handicrafts Development Corporation",
        "primary_contact_email": "md@keralacrafts.org",
        "organization_type": "government",
        "primary_domain": "keralacrafts.gov.in",
        "branding": {
            "brand_name": "Kairali Kerala Crafts",
            "logo_url": "https://keralacrafts.gov.in/logo.png",
            "primary_color": "#047857",
            "secondary_color": "#064E3B",
        },
        "supported_languages": ["ml", "en"],
        "supported_districts": ["Aranmula", "Thrissur", "Alappuzha"],
        "allowed_categories": ["Aranmula Kannadi", "Bell Metal", "Coir Craft", "Rosewood Carving"],
        "payment_gateway": "razorpay",
    }
    create_res = client.post("/api/v1/tenants/provision", json=provision_payload)
    assert create_res.status_code == 200
    tenant_data = create_res.json()["tenant"]
    tenant_id = tenant_data["id"]
    assert tenant_data["tenant_slug"] == "kerala-craft-heritage"
    assert "ml" in tenant_data["supported_languages"]

    # Resolve by new domain
    resolve_res = client.get("/api/v1/tenants/resolve?domain=keralacrafts.gov.in")
    assert resolve_res.status_code == 200
    assert resolve_res.json()["tenant"]["organization_name"] == "Kerala State Handicrafts Development Corporation"

    # Add a secondary domain
    add_dom_res = client.post(
        "/api/v1/tenants/domains/add",
        json={
            "tenant_id": tenant_id,
            "domain_name": "kairalicrafts.com",
            "is_primary": False,
        },
    )
    assert add_dom_res.status_code == 200
    assert add_dom_res.json()["domain"]["domain_name"] == "kairalicrafts.com"

    # Resolve by secondary domain
    resolve_sec = client.get("/api/v1/tenants/resolve?domain=kairalicrafts.com")
    assert resolve_sec.status_code == 200
    assert resolve_sec.json()["tenant"]["id"] == tenant_id


def test_update_tenant_settings():
    res_up = client.get("/api/v1/tenants/resolve?domain=up-odop")
    up_id = res_up.json()["tenant"]["id"]

    update_payload = {
        "tenant_id": up_id,
        "branding": {
            "primary_color": "#1E40AF",
        },
        "policies": {
            "return_policy_days": 15,
            "commission_fee_pct": 0.5,
        },
    }
    upd_res = client.put("/api/v1/tenants/settings", json=update_payload)
    assert upd_res.status_code == 200
    data = upd_res.json()["tenant"]
    assert data["branding"]["primary_color"] == "#1E40AF"
    assert data["policies"]["return_policy_days"] == 15
    assert data["policies"]["commission_fee_pct"] == 0.5
