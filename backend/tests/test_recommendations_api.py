"""
Test suite for Personalized Recommendation Engine APIs.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_recommendation_feed_uniqueness_and_sections():
    # User A (Jaipur Buyer)
    res_a = client.get("/api/v1/recommendations/feed?user_id=buyer_a&city=Jaipur&state=Rajasthan")
    assert res_a.status_code == 200
    data_a = res_a.json()
    assert "recommended_for_you" in data_a
    assert "because_you_viewed" in data_a
    assert "nearby_trending" in data_a
    assert "from_followed_stores" in data_a
    assert "recently_popular" in data_a
    assert "new_arrivals" in data_a

    # User B (Kanchipuram Buyer)
    res_b = client.get("/api/v1/recommendations/feed?user_id=buyer_b&city=Kanchipuram&state=Tamil Nadu")
    assert res_b.status_code == 200
    data_b = res_b.json()
    assert data_b["user_id"] == "buyer_b"


def test_track_interaction():
    payload = {
        "user_id": "buyer_test_123",
        "interaction_type": "CLICK",
        "target_id": "prod_blue_pottery_vase",
        "category": "Pottery",
        "tags": ["blue pottery", "ceramic", "jaipur"],
        "city": "Jaipur",
        "state": "Rajasthan",
    }
    res = client.post("/api/v1/recommendations/track", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["recorded_weight"] == 1.5


def test_similar_products():
    res = client.get("/api/v1/recommendations/similar/test_product_123?limit=5")
    assert res.status_code == 200
    data = res.json()
    assert "product_id" in data
    assert "similar_products" in data
    assert isinstance(data["similar_products"], list)


def test_explore_cursor_pagination():
    res = client.get("/api/v1/recommendations/explore?limit=4")
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert "has_more" in data

