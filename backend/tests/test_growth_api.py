"""
Tests for Growth & Marketing Engine (Phase 3).
Tests Coupons, Flash Sales, Reward Points, Referrals, Wishlists, and Checkout Impact.
"""

import os
os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("APP_ENV", "development")
os.environ.setdefault("SUPABASE_URL", "https://placeholder.supabase.co")

from datetime import datetime, timezone, timedelta
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import get_current_user

MOCK_BUYER = {
    "firebase_uid": "test-buyer-growth-123",
    "email": "buyer.growth@kalacart.in",
    "name": "Arjun Growth",
    "artisan": {"id": "00000000-0000-0000-0000-000000000001"},
    "claims": {"uid": "test-buyer-growth-123"}
}


@pytest.fixture(autouse=True)
def setup_auth_override():
    app.dependency_overrides[get_current_user] = lambda: MOCK_BUYER
    yield
    app.dependency_overrides.pop(get_current_user, None)


client = TestClient(app)


def test_create_and_validate_coupons():
    # 1. Create a custom 20% craft coupon
    valid_until = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    create_payload = {
        "code": "CRAFT20",
        "title": "20% Off on Heritage Crafts",
        "discount_type": "PERCENTAGE",
        "discount_value": 20.0,
        "min_order_amount": 1000.0,
        "max_discount_amount": 400.0,
        "valid_until": valid_until,
    }
    res = client.post("/api/v1/growth/coupons", json=create_payload)
    assert res.status_code == 201, res.text
    coupon_data = res.json()
    assert coupon_data["code"] == "CRAFT20"
    assert coupon_data["discount_value"] == 20.0

    # 2. List coupons
    list_res = client.get("/api/v1/growth/coupons")
    assert list_res.status_code == 200
    codes = [c["code"] for c in list_res.json()]
    assert "CRAFT20" in codes

    # 3. Validate coupon against below min order
    val_low = client.post(
        "/api/v1/growth/coupons/validate",
        json={"code": "CRAFT20", "cart_amount": 500.0},
    )
    assert val_low.status_code == 200
    assert val_low.json()["is_valid"] is False

    # 4. Validate coupon against eligible cart
    val_ok = client.post(
        "/api/v1/growth/coupons/validate",
        json={"code": "CRAFT20", "cart_amount": 1500.0},
    )
    assert val_ok.status_code == 200
    val_data = val_ok.json()
    assert val_data["is_valid"] is True
    assert val_data["discount_amount"] == 300.0  # 20% of 1500
    assert val_data["payable_amount"] == 1200.0


def test_campaigns_and_flash_sales():
    now = datetime.now(timezone.utc)
    camp_payload = {
        "title": "Terracotta Lamp Flash Sale",
        "campaign_type": "FLASH_SALE",
        "discount_pct": 25.0,
        "start_time": now.isoformat(),
        "end_time": (now + timedelta(hours=8)).isoformat(),
        "target_category": "Terracotta",
    }
    create_res = client.post("/api/v1/growth/campaigns", json=camp_payload)
    assert create_res.status_code == 201, create_res.text
    camp_data = create_res.json()
    assert camp_data["title"] == "Terracotta Lamp Flash Sale"
    assert camp_data["discount_pct"] == 25.0

    list_res = client.get("/api/v1/growth/campaigns")
    assert list_res.status_code == 200
    campaigns = list_res.json()
    assert len(campaigns) >= 1


def test_reward_points_balance_and_redemption():
    # 1. Balance
    bal_res = client.get("/api/v1/growth/rewards/balance")
    assert bal_res.status_code == 200
    bal_data = bal_res.json()
    assert bal_data["points_balance"] > 0
    assert bal_data["inr_value"] == bal_data["points_balance"] * 0.50

    # 2. Redeem points
    redeem_res = client.post(
        "/api/v1/growth/rewards/redeem",
        json={"points_to_redeem": 50, "cart_amount": 1000.0},
    )
    assert redeem_res.status_code == 200, redeem_res.text
    red_data = redeem_res.json()
    assert red_data["success"] is True
    assert red_data["points_redeemed"] == 50
    assert red_data["discount_inr"] == 25.0  # 50 * 0.50


def test_referrals_workflow():
    # 1. Get referral code
    code_res = client.get("/api/v1/growth/referrals/my-code")
    assert code_res.status_code == 200
    code_data = code_res.json()
    assert "referral_code" in code_data
    assert code_data["referrer_reward_points"] == 100

    # 2. Apply referral code
    apply_res = client.post(
        "/api/v1/growth/referrals/apply",
        json={"referral_code": code_data["referral_code"]},
    )
    assert apply_res.status_code == 200
    assert apply_res.json()["success"] is True

    # 3. Referral stats
    stats_res = client.get("/api/v1/growth/referrals/stats")
    assert stats_res.status_code == 200
    stats = stats_res.json()
    assert stats["total_invites"] > 0


def test_wishlist_and_price_drops():
    # 1. Add to wishlist
    prod_id = "00000000-0000-0000-0000-000000000999"
    add_res = client.post(
        "/api/v1/growth/wishlist",
        json={"product_id": prod_id, "current_price": 2400.0},
    )
    assert add_res.status_code == 201, add_res.text
    assert add_res.json()["product_id"] == prod_id

    # 2. Get wishlist
    get_res = client.get("/api/v1/growth/wishlist")
    assert get_res.status_code == 200
    wishlist = get_res.json()
    assert len(wishlist) >= 1

    # 3. Check price drops cron
    cron_res = client.post("/api/v1/growth/wishlist/check-price-drops")
    assert cron_res.status_code == 200
    assert cron_res.json()["checked_items"] >= 1

    # 4. Remove from wishlist
    del_res = client.delete(f"/api/v1/growth/wishlist/{prod_id}")
    assert del_res.status_code == 200


def test_checkout_with_coupon_and_reward_points():
    order_payload = {
        "artisan_id": "00000000-0000-0000-0000-000000000002",
        "buyer_name": "Arjun Growth",
        "buyer_phone": "9876543210",
        "buyer_email": "buyer.growth@kalacart.in",
        "seller_name": "Rajesh Pottery",
        "seller_phone": "9123456780",
        "delivery_address": "101 Crafts Street, Jaipur, Rajasthan",
        "shipping_address": "101 Crafts Street, Jaipur, Rajasthan",
        "quantity": 2,
        "unit_price": 1000.0,  # subtotal = 2000.0
        "shipping_charges": 150.0,
        "coupon_code": "FESTIVAL15",  # 15% off = ₹300
        "reward_points_used": 100,     # 100 pts = ₹50
    }
    res = client.post("/api/v1/orders", json=order_payload)
    assert res.status_code == 201, res.text
    data = res.json()
    assert data["subtotal"] == 2000.0
    assert data["discount_amount"] == 350.0  # ₹300 coupon + ₹50 rewards
    assert data["coupon_code"] == "FESTIVAL15"
    assert data["reward_points_used"] == 100
    # Discounted subtotal = 2000 - 350 = 1650
    # GST @ 18% = 297.0
    # Shipping = 150.0
    # Total = 1650 + 297 + 150 = 2097.0
    assert data["gst_amount"] == 297.0
    assert data["total_amount"] == 2097.0
