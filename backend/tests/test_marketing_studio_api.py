"""
Tests for AI Marketing Studio (Phase 4).
Tests Poster Generation, Multilingual Copywriting, and Campaign Scheduling.
"""

import os
os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("APP_ENV", "development")
os.environ.setdefault("SUPABASE_URL", "https://placeholder.supabase.co")

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import get_current_user

MOCK_ARTISAN = {
    "firebase_uid": "test-artisan-uid-888",
    "email": "artisan@kalacart.in",
    "artisan": {"id": "00000000-0000-0000-0000-000000000002"},
    "claims": {"uid": "test-artisan-uid-888"}
}


@pytest.fixture(autouse=True)
def setup_auth_override():
    app.dependency_overrides[get_current_user] = lambda: MOCK_ARTISAN
    yield
    app.dependency_overrides.pop(get_current_user, None)


client = TestClient(app)


def test_generate_marketing_poster():
    payload = {
        "product_title": "Jaipur Blue Pottery Hand-Painted Floral Vase",
        "product_price": 2499.0,
        "product_image_url": "https://images.unsplash.com/photo-1578749556568-bc2c40e68b61?w=1080",
        "store_name": "Rajesh Heritage Pottery",
        "store_slug": "rajesh-pottery",
        "format_type": "INSTAGRAM_POST",
        "theme": "LUXURY",
        "festival": "Diwali",
        "language": "en",
    }
    res = client.post("/api/v1/marketing-studio/generate-poster", json=payload)
    assert res.status_code == 200, res.text
    data = res.json()
    assert "poster_id" in data
    assert "qr_code_url" in data
    assert "https://kalacart.shop/store/rajesh-pottery" in data["store_deep_link"]
    assert data["format_type"] == "INSTAGRAM_POST"
    assert data["aspect_ratio"] == "1:1"
    assert len(data["copywriting"]["hashtags"]) >= 3


def test_multilingual_copywriting():
    # Hindi Copy
    hi_res = client.post(
        "/api/v1/marketing-studio/copywriting",
        json={
            "product_title": "हस्तनिर्मित ब्लू पॉटरी फूलदान",
            "craft_category": "Pottery",
            "artisan_name": "राजेश प्रजापति",
            "store_name": "राजेश हेरिटेज पॉटरी",
            "language": "hi",
        },
    )
    assert hi_res.status_code == 200, hi_res.text
    hi_data = hi_res.json()
    assert "हस्तशिल्प" in hi_data["caption"] or "शिल्पकला" in hi_data["caption"]
    assert "#KalaCart" in hi_data["hashtags"]


def test_schedule_and_list_marketing_campaigns():
    camp_payload = {
        "product_title": "Pochampally Ikat Pure Silk Saree",
        "product_price": 7850.0,
        "campaign_title": "Weekend Handloom Heritage Campaign",
        "format_type": "WHATSAPP_BANNER",
        "theme": "TRADITIONAL",
        "schedule_type": "WEEKEND",
        "language": "en",
    }
    create_res = client.post("/api/v1/marketing-studio/campaigns", json=camp_payload)
    assert create_res.status_code == 201, create_res.text
    camp_data = create_res.json()
    assert camp_data["campaign_title"] == "Weekend Handloom Heritage Campaign"
    assert "qr_code_url" in camp_data
    assert camp_data["status"] == "SCHEDULED"

    list_res = client.get("/api/v1/marketing-studio/campaigns")
    assert list_res.status_code == 200
    campaigns = list_res.json()
    assert len(campaigns) >= 1
