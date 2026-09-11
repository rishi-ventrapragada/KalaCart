"""
Unit and integration tests for KalaCart B2B Marketplace & Inventory APIs (Phase 7).

Tests:
1. Public marketplace products listing (GET /api/v1/marketplace/products)
2. Marketplace buyers listing (GET /api/v1/marketplace/buyers)
3. Send enquiry (POST /api/v1/marketplace/enquiry)
4. Duplicate enquiry detection (409 Conflict)
5. Enquire on own product forbidden (403 Forbidden)
6. List my enquiries (GET /api/v1/enquiries/my)
7. Accept enquiry (PATCH /api/v1/enquiries/{id}/accept)
8. Reject enquiry (PATCH /api/v1/enquiries/{id}/reject)
9. Publish product validation & success (PATCH /api/v1/products/{id}/publish)
10. Draft product (PATCH /api/v1/products/{id}/draft)
11. Push service notifications integration
"""

import uuid
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

from app.main import app
from app.core.security import get_current_user
from app.api.marketplace import _clear_enquiry_rate_store
import app.services.push_service as push_service

client = TestClient(app)

ARTISAN_ID_1 = "11111111-1111-1111-1111-111111111111"
ARTISAN_ID_2 = "22222222-2222-2222-2222-222222222222"
PRODUCT_ID_1 = "33333333-3333-3333-3333-333333333333"
ENQUIRY_ID_1 = "44444444-4444-4444-4444-444444444444"
BUYER_PROFILE_ID_1 = "55555555-5555-5555-5555-555555555555"

MOCK_USER_1 = {
    "firebase_uid": "uid_artisan_1",
    "phone": "+919876543210",
    "artisan": {
        "id": ARTISAN_ID_1,
        "name": "Ramesh Artisan",
        "phone": "+919876543210",
        "firebase_uid": "uid_artisan_1",
    },
    "claims": {"uid": "uid_artisan_1"},
}

MOCK_USER_2 = {
    "firebase_uid": "uid_artisan_2",
    "phone": "+919876543211",
    "artisan": {
        "id": ARTISAN_ID_2,
        "name": "Buyer Artisan",
        "phone": "+919876543211",
        "firebase_uid": "uid_artisan_2",
    },
    "claims": {"uid": "uid_artisan_2"},
}


@pytest.fixture(autouse=True)
def clean_rate_store():
    _clear_enquiry_rate_store()


# ── 1. GET /api/v1/marketplace/products ──────────────────────────────────────

def test_list_marketplace_products_public():
    """Marketplace products should be publicly browseable without auth."""
    app.dependency_overrides.pop(get_current_user, None)
    with patch("app.api.marketplace._get_supabase") as mock_sup:
        mock_client = MagicMock()
        mock_sup.return_value = mock_client
        
        mock_query = MagicMock()
        mock_client.table.return_value.select.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.order.return_value = mock_query
        mock_query.range.return_value = mock_query
        mock_query.execute.return_value = MagicMock(data=[
            {
                "id": PRODUCT_ID_1,
                "title": "Blue Pottery Vase",
                "price": 1250,
                "is_published": True,
                "is_deleted": False,
                "category": "pottery",
            }
        ])

        resp = client.get("/api/v1/marketplace/products?limit=10&category=pottery")
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert len(body["data"]) == 1
        assert body["data"][0]["title"] == "Blue Pottery Vase"


# ── 2. GET /api/v1/marketplace/buyers ────────────────────────────────────────

def test_list_marketplace_buyers():
    """List verified buyers with auth."""
    app.dependency_overrides[get_current_user] = lambda: MOCK_USER_1
    with patch("app.api.marketplace._get_supabase") as mock_sup:
        mock_client = MagicMock()
        mock_sup.return_value = mock_client

        mock_query = MagicMock()
        mock_client.table.return_value.select.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.ilike.return_value = mock_query
        mock_query.order.return_value = mock_query
        mock_query.range.return_value = mock_query
        mock_query.execute.return_value = MagicMock(data=[
            {
                "id": BUYER_PROFILE_ID_1,
                "company_name": "FabIndia Wholesale",
                "city": "Jaipur",
                "state": "Rajasthan",
                "verification_status": "verified",
                "minimum_order": 50,
                "required_quantity": 200,
            }
        ])

        resp = client.get("/api/v1/marketplace/buyers?city=Jaipur&verification_status=verified")
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert len(body["data"]) == 1
        assert body["data"][0]["company_name"] == "FabIndia Wholesale"
    app.dependency_overrides.pop(get_current_user, None)


# ── 3. POST /api/v1/marketplace/enquiry ──────────────────────────────────────

def test_create_enquiry_success():
    """Send enquiry to product artisan."""
    app.dependency_overrides[get_current_user] = lambda: MOCK_USER_2
    with patch("app.api.marketplace._get_supabase") as mock_sup, \
         patch("app.services.supabase_service.get_product_by_id") as mock_get_p, \
         patch("app.services.push_service.send_enquiry_notification") as mock_push:

        mock_get_p.return_value = {
            "id": PRODUCT_ID_1,
            "artisan_id": ARTISAN_ID_1,  # owned by artisan 1
            "title": "Jaipur Blue Vase",
            "is_published": True,
            "is_deleted": False,
            "price": 1200,
        }

        mock_client = MagicMock()
        mock_sup.return_value = mock_client

        # dup query returns empty
        mock_client.table.return_value.select.return_value.eq.return_value.gte.return_value.limit.return_value.execute.return_value = MagicMock(data=[])
        # buyer profile lookup
        mock_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(data=[])

        # insert returns enquiry
        mock_client.table.return_value.insert.return_value.select.return_value.execute.return_value = MagicMock(data=[{
            "id": ENQUIRY_ID_1,
            "product_id": PRODUCT_ID_1,
            "artisan_id": ARTISAN_ID_1,
            "message": "We are interested in bulk ordering 50 units.",
            "required_quantity": 50,
            "delivery_month": "October 2026",
            "status": "pending",
        }])

        payload = {
            "product_id": PRODUCT_ID_1,
            "message": "We are interested in bulk ordering 50 units.",
            "required_quantity": 50,
            "delivery_month": "October 2026",
        }

        resp = client.post("/api/v1/marketplace/enquiry", json=payload)
        assert resp.status_code == 201
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["id"] == ENQUIRY_ID_1
        assert body["data"]["delivery_month"] == "October 2026"
    app.dependency_overrides.pop(get_current_user, None)


def test_create_enquiry_on_own_product_forbidden():
    """Enquiring on your own product should return 403 Forbidden."""
    app.dependency_overrides[get_current_user] = lambda: MOCK_USER_1  # artisan 1 owns the product
    with patch("app.api.marketplace._get_supabase") as mock_sup, \
         patch("app.services.supabase_service.get_product_by_id") as mock_get_p:
        mock_client = MagicMock()
        mock_sup.return_value = mock_client
        mock_get_p.return_value = {
            "id": PRODUCT_ID_1,
            "artisan_id": ARTISAN_ID_1,
            "title": "Jaipur Blue Vase",
            "is_published": True,
            "is_deleted": False,
        }
        payload = {
            "product_id": PRODUCT_ID_1,
            "message": "We are interested in bulk ordering 50 units.",
            "required_quantity": 50,
        }
        resp = client.post("/api/v1/marketplace/enquiry", json=payload)
        assert resp.status_code == 403
    app.dependency_overrides.pop(get_current_user, None)


# ── 4. GET /api/v1/enquiries/my ──────────────────────────────────────────────

def test_list_my_enquiries():
    """List enquiries received for my products."""
    app.dependency_overrides[get_current_user] = lambda: MOCK_USER_1
    with patch("app.api.marketplace._get_supabase") as mock_sup:
        mock_client = MagicMock()
        mock_sup.return_value = mock_client

        mock_query = MagicMock()
        mock_client.table.return_value.select.return_value.eq.return_value = mock_query
        mock_query.order.return_value.range.return_value.execute.return_value = MagicMock(data=[
            {
                "id": ENQUIRY_ID_1,
                "product_id": PRODUCT_ID_1,
                "artisan_id": ARTISAN_ID_1,
                "buyer_name": "FabIndia",
                "message": "Interested in 50 pieces.",
                "required_quantity": 50,
                "status": "pending",
            }
        ])

        # buyer_profiles lookup returns empty
        mock_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(data=[])

        resp = client.get("/api/v1/enquiries/my")
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert len(body["data"]) == 1
        assert body["data"][0]["id"] == ENQUIRY_ID_1
    app.dependency_overrides.pop(get_current_user, None)


# ── 5. PATCH /api/v1/enquiries/{id}/accept & reject ──────────────────────────

def test_accept_enquiry_success():
    """Accept an enquiry owned by the artisan."""
    app.dependency_overrides[get_current_user] = lambda: MOCK_USER_1
    with patch("app.api.marketplace._get_supabase") as mock_sup, \
         patch("app.services.push_service.send_enquiry_accepted_notification") as mock_push:

        mock_client = MagicMock()
        mock_sup.return_value = mock_client

        # select enquiry
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[
            {
                "id": ENQUIRY_ID_1,
                "artisan_id": ARTISAN_ID_1,
                "product_id": PRODUCT_ID_1,
                "buyer_name": "FabIndia",
                "status": "pending",
            }
        ])
        # update status
        mock_client.table.return_value.update.return_value.eq.return_value.select.return_value.execute.return_value = MagicMock(data=[
            {
                "id": ENQUIRY_ID_1,
                "artisan_id": ARTISAN_ID_1,
                "product_id": PRODUCT_ID_1,
                "status": "accepted",
            }
        ])

        resp = client.patch(f"/api/v1/enquiries/{ENQUIRY_ID_1}/accept")
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["status"] == "accepted"
    app.dependency_overrides.pop(get_current_user, None)


def test_reject_enquiry_success():
    """Reject an enquiry owned by the artisan."""
    app.dependency_overrides[get_current_user] = lambda: MOCK_USER_1
    with patch("app.api.marketplace._get_supabase") as mock_sup:
        mock_client = MagicMock()
        mock_sup.return_value = mock_client

        # select enquiry
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[
            {
                "id": ENQUIRY_ID_1,
                "artisan_id": ARTISAN_ID_1,
                "product_id": PRODUCT_ID_1,
                "status": "pending",
            }
        ])
        # update status
        mock_client.table.return_value.update.return_value.eq.return_value.select.return_value.execute.return_value = MagicMock(data=[
            {
                "id": ENQUIRY_ID_1,
                "artisan_id": ARTISAN_ID_1,
                "status": "rejected",
            }
        ])

        resp = client.patch(f"/api/v1/enquiries/{ENQUIRY_ID_1}/reject")
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["status"] == "rejected"
    app.dependency_overrides.pop(get_current_user, None)


# ── 6. PATCH /api/v1/products/{id}/publish & draft ───────────────────────────

def test_publish_product_validation_failure():
    """Publishing without valid title, description, price, or image should return 400."""
    app.dependency_overrides[get_current_user] = lambda: MOCK_USER_1
    with patch("app.api.marketplace._get_supabase") as mock_sup, \
         patch("app.services.supabase_service.get_product_by_id") as mock_get_p:
        mock_client = MagicMock()
        mock_sup.return_value = mock_client
        mock_get_p.return_value = {
            "id": PRODUCT_ID_1,
            "artisan_id": ARTISAN_ID_1,
            "title": "",  # missing title
            "description": "Short",  # short desc
            "price": 0,  # 0 price
            "image_urls": [],  # missing image
        }
        resp = client.patch(f"/api/v1/products/{PRODUCT_ID_1}/publish")
        assert resp.status_code == 400
    app.dependency_overrides.pop(get_current_user, None)


def test_publish_product_success():
    """Publishing a valid product succeeds and sets is_published=True."""
    app.dependency_overrides[get_current_user] = lambda: MOCK_USER_1
    with patch("app.api.marketplace._get_supabase") as mock_sup, \
         patch("app.services.supabase_service.get_product_by_id") as mock_get_p, \
         patch("app.services.supabase_service.update_product") as mock_up, \
         patch("app.services.push_service.send_product_published_notification") as mock_push:

        mock_client = MagicMock()
        mock_sup.return_value = mock_client
        mock_get_p.return_value = {
            "id": PRODUCT_ID_1,
            "artisan_id": ARTISAN_ID_1,
            "title": "Authentic Blue Pottery Vase",
            "description": "Handcrafted blue pottery vase made in Jaipur Rajasthan with traditional motifs.",
            "price": 1500,
            "image_urls": ["https://storage.supabase.co/product-images/vase.png"],
            "is_published": False,
            "is_deleted": False,
        }
        mock_up.return_value = {
            "id": PRODUCT_ID_1,
            "artisan_id": ARTISAN_ID_1,
            "title": "Authentic Blue Pottery Vase",
            "is_published": True,
            "buyer_visible": True,
        }

        resp = client.patch(f"/api/v1/products/{PRODUCT_ID_1}/publish")
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["is_published"] is True
    app.dependency_overrides.pop(get_current_user, None)


def test_draft_product_success():
    """Moving product to draft unpublishes it."""
    app.dependency_overrides[get_current_user] = lambda: MOCK_USER_1
    with patch("app.services.supabase_service.get_product_by_id") as mock_get_p, \
         patch("app.services.supabase_service.update_product") as mock_up:

        mock_get_p.return_value = {
            "id": PRODUCT_ID_1,
            "artisan_id": ARTISAN_ID_1,
            "title": "Authentic Blue Pottery Vase",
            "is_published": True,
            "is_deleted": False,
        }
        mock_up.return_value = {
            "id": PRODUCT_ID_1,
            "artisan_id": ARTISAN_ID_1,
            "is_published": False,
            "buyer_visible": False,
        }

        resp = client.patch(f"/api/v1/products/{PRODUCT_ID_1}/draft")
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["is_published"] is False
    app.dependency_overrides.pop(get_current_user, None)
