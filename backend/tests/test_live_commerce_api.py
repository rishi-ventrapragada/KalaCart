from fastapi.testclient import TestClient
import pytest
from app.main import app
from app.core.security import get_current_user

@pytest.fixture(autouse=True)
def override_auth():
    app.dependency_overrides[get_current_user] = lambda: {
        "uid": "artisan-rajesh-001",
        "email": "rajesh.prajapati@jaipurpottery.in",
        "name": "Master Artisan Rajesh Prajapati",
        "role": "seller"
    }
    yield
    app.dependency_overrides.clear()

def test_live_session_lifecycle_and_pinning():
    client = TestClient(app)

    # 1. Artisan starts live selling session
    create_payload = {
        "title": "Live Masterclass: Throwing & Glazing Jaipur Blue Pottery on the Wheel",
        "description": "Watch live hand-carving and painting using natural cobalt blue quartz glaze with exclusive live flash discounts.",
        "cover_image_url": "https://storage.kalacart.in/live/covers/jaipur_pottery_live.jpg"
    }
    res_start = client.post("/api/v1/live/sessions", json=create_payload)
    assert res_start.status_code == 201, res_start.text
    session = res_start.json()
    session_id = session["id"]
    assert session["status"] == "live"
    assert "m3u8" in session["playback_hls_url"]
    assert len(session["products"]) == 2

    # 2. Pin featured craft product with 20% live flash coupon
    pin_payload = {
        "product_id": "prod-blue-pottery-tea-set",
        "live_discount_percent": 20.0,
        "coupon_code": "FLASHBLUE20"
    }
    res_pin = client.post(f"/api/v1/live/sessions/{session_id}/pin-product", json=pin_payload)
    assert res_pin.status_code == 200, res_pin.text
    pinned_sess = res_pin.json()
    assert pinned_sess["pinned_product"]["product_id"] == "prod-blue-pottery-tea-set"
    assert pinned_sess["pinned_coupon_code"] == "FLASHBLUE20"

def test_live_chat_and_floating_reactions():
    client = TestClient(app)

    # Fetch active session
    res_list = client.get("/api/v1/live/sessions")
    assert res_list.status_code == 200
    sessions = res_list.json()
    assert len(sessions) >= 1
    session_id = sessions[0]["id"]

    # 1. Buyer posts live question
    app.dependency_overrides[get_current_user] = lambda: {
        "uid": "buyer-ananya-002",
        "email": "ananya@example.com",
        "name": "Ananya Roy",
        "role": "buyer"
    }

    msg_payload = {
        "message_text": "Is this tea set microwave-safe and lead-free?",
        "is_question": True
    }
    res_msg = client.post(f"/api/v1/live/sessions/{session_id}/messages", json=msg_payload)
    assert res_msg.status_code == 201, res_msg.text
    msg = res_msg.json()
    assert msg["sender_name"] == "Ananya Roy"
    assert msg["is_pinned_question"] is True

    # 2. Buyer sends heart reaction burst
    res_react = client.post(f"/api/v1/live/sessions/{session_id}/react", json={"reaction_type": "heart", "count": 10})
    assert res_react.status_code == 200
    assert res_react.json()["total_likes"] > 1400

def test_instant_in_stream_purchase():
    client = TestClient(app)

    res_list = client.get("/api/v1/live/sessions")
    session_id = res_list.json()[0]["id"]

    # 1-Tap Purchase
    purchase_payload = {
        "product_id": "prod-blue-pottery-tea-set",
        "quantity": 1,
        "coupon_code": "FLASHBLUE20",
        "delivery_address": "Flat 304, Emerald Heights, Indiranagar, Bangalore 560038"
    }
    res_buy = client.post(f"/api/v1/live/sessions/{session_id}/purchase", json=purchase_payload)
    assert res_buy.status_code == 201, res_buy.text
    purchase = res_buy.json()
    assert purchase["stream_playback_maintained"] is True
    assert purchase["status"] == "confirmed_in_stream"
    assert "LIVE-ORD-" in purchase["order_id"]

def test_end_live_session():
    client = TestClient(app)

    res_list = client.get("/api/v1/live/sessions")
    session_id = res_list.json()[0]["id"]

    res_end = client.post(f"/api/v1/live/sessions/{session_id}/end")
    assert res_end.status_code == 200
    assert res_end.json()["status"] == "ended"
    assert res_end.json()["ended_at"] is not None
