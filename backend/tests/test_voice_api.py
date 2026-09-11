import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_voice_intent_search_english():
    response = client.post(
        "/api/v1/voice/intent",
        json={"transcript": "Show blue pottery under 1000", "language": "en", "source_type": "SEARCH"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["intent_name"] == "SEARCH_PRODUCT"
    assert data["slots"]["category"] == "Pottery"
    assert data["slots"]["max_price"] == 1000.0


def test_voice_intent_search_nearby():
    response = client.post(
        "/api/v1/voice/intent",
        json={"transcript": "I need bamboo furniture nearby", "language": "en", "source_type": "SEARCH"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["intent_name"] == "SEARCH_PRODUCT"
    assert data["slots"]["nearby_only"] is True


def test_voice_intent_seller_create_product():
    response = client.post(
        "/api/v1/voice/intent",
        json={
            "transcript": "Add a bamboo basket, material is natural bamboo, price 850 rupees, quantity 20",
            "language": "en",
            "source_type": "CATALOG"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["intent_name"] == "CREATE_PRODUCT"
    assert data["slots"]["category"] == "Basketry"
    assert data["slots"]["price"] == 850.0
    assert data["slots"]["quantity"] == 20


def test_voice_intent_buyer_rfq():
    response = client.post(
        "/api/v1/voice/intent",
        json={"transcript": "Need quote for 50 pieces terracotta pots under 5000", "language": "en", "source_type": "RFQ"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["intent_name"] == "CREATE_RFQ"
    assert data["slots"]["quantity"] == 50
    assert data["slots"]["target_budget"] == 5000.0


def test_voice_intent_navigation():
    response = client.post(
        "/api/v1/voice/intent",
        json={"transcript": "Go to my orders", "language": "en", "source_type": "NAV"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["intent_name"] == "NAVIGATE"
    assert data["slots"]["destination"] == "orders"


def test_voice_intent_multilingual_telugu():
    response = client.post(
        "/api/v1/voice/intent",
        json={"transcript": "నాకు అందమైన కుండలు కావాలి 500 రూపాయలు", "language": "te", "source_type": "SEARCH"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["detected_language"] == "te"
    assert data["slots"]["category"] == "Pottery"
    assert data["slots"]["max_price"] == 500.0
