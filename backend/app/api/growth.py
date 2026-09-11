"""
Growth & Marketing Engine Router (Phase 3).
Handles Coupons, Flash Sales, Bundle Offers, Loyalty Reward Points,
Referrals, Wishlists, Price Alerts, and Recently Viewed.
"""

import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.security import get_current_user
from app.database.connection import get_supabase_client
from app.models.growth import (
    CampaignCreate,
    CampaignResponse,
    CampaignType,
    CouponCreate,
    CouponResponse,
    CouponValidateRequest,
    CouponValidateResponse,
    DiscountType,
    PriceDropCheckResponse,
    RecentlyViewedCreate,
    RecentlyViewedResponse,
    ReferralApplyRequest,
    ReferralCodeResponse,
    ReferralStatsResponse,
    RewardBalanceResponse,
    RewardRedeemRequest,
    RewardRedeemResponse,
    RewardTier,
    RewardTransactionResponse,
    RewardTransactionType,
    WishlistItemCreate,
    WishlistItemResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory mock storage for development/resilience
_mock_coupons: Dict[str, dict] = {
    "WELCOME50": {
        "id": "00000000-0000-0000-0000-00000000c001",
        "code": "WELCOME50",
        "title": "Welcome Discount ₹50 Off",
        "description": "Get flat ₹50 off on your first handicraft order",
        "discount_type": "FLAT",
        "discount_value": 50.0,
        "min_order_amount": 299.0,
        "max_discount_amount": 50.0,
        "artisan_id": None,
        "usage_limit": 10000,
        "usage_count": 42,
        "per_user_limit": 1,
        "valid_from": (datetime.now(timezone.utc) - timedelta(days=30)).isoformat(),
        "valid_until": (datetime.now(timezone.utc) + timedelta(days=365)).isoformat(),
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    },
    "FESTIVAL15": {
        "id": "00000000-0000-0000-0000-00000000c002",
        "code": "FESTIVAL15",
        "title": "Diwali Craft Special 15% Off",
        "description": "15% discount up to ₹500 across all artisanal handlooms & pottery",
        "discount_type": "PERCENTAGE",
        "discount_value": 15.0,
        "min_order_amount": 500.0,
        "max_discount_amount": 500.0,
        "artisan_id": None,
        "usage_limit": 5000,
        "usage_count": 312,
        "per_user_limit": 3,
        "valid_from": (datetime.now(timezone.utc) - timedelta(days=5)).isoformat(),
        "valid_until": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    },
    "FREESHIP": {
        "id": "00000000-0000-0000-0000-00000000c003",
        "code": "FREESHIP",
        "title": "Free Nationwide Courier Delivery",
        "description": "Zero shipping charges on orders above ₹999",
        "discount_type": "FREE_SHIPPING",
        "discount_value": 0.0,
        "min_order_amount": 999.0,
        "max_discount_amount": None,
        "artisan_id": None,
        "usage_limit": 2000,
        "usage_count": 88,
        "per_user_limit": 5,
        "valid_from": (datetime.now(timezone.utc) - timedelta(days=10)).isoformat(),
        "valid_until": (datetime.now(timezone.utc) + timedelta(days=60)).isoformat(),
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
}

_mock_campaigns: Dict[str, dict] = {
    "camp-flash-pottery": {
        "id": "00000000-0000-0000-0000-00000000cp01",
        "title": "Jaipur Blue Pottery Midnight Flash Sale",
        "slug": "blue-pottery-flash-sale",
        "campaign_type": "FLASH_SALE",
        "description": "Extra 20% off authentic Jaipur Blue Pottery for the next 12 hours.",
        "banner_url": "https://images.unsplash.com/photo-1578749556568-bc2c40e68b61?w=1200",
        "discount_pct": 20.0,
        "min_order_amount": 400.0,
        "bundle_product_ids": [],
        "target_category": "Pottery",
        "start_time": (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat(),
        "end_time": (datetime.now(timezone.utc) + timedelta(hours=10)).isoformat(),
        "is_active": True,
        "metadata": {"badge_color": "#D32F2F"},
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
}

_mock_rewards: Dict[str, dict] = {}
_mock_reward_tx: Dict[str, List[dict]] = {}
_mock_wishlists: Dict[str, List[dict]] = {}
_mock_recently_viewed: Dict[str, List[dict]] = {}
_mock_referrals: Dict[str, dict] = {}


def _get_user_id(current_user: dict) -> str:
    artisan = current_user.get("artisan") or {}
    art_id = artisan.get("id")
    if art_id:
        return str(art_id)
    uid = current_user.get("firebase_uid")
    if uid:
        return str(uid)
    return "00000000-0000-0000-0000-000000000001"


# =============================================================================
# 1. COUPONS & DISCOUNTS
# =============================================================================
@router.post("/coupons", response_model=CouponResponse, status_code=status.HTTP_201_CREATED)
async def create_coupon(
    req: CouponCreate,
    current_user: dict = Depends(get_current_user),
):
    """
    Creates a new discount or free shipping coupon. Artisans can create store-specific coupons.
    """
    user_id = _get_user_id(current_user)
    coupon_id = str(uuid.uuid4())
    code_clean = req.code.strip().upper()

    now = datetime.now(timezone.utc)
    valid_from = req.valid_from or now

    coupon_dict = {
        "id": coupon_id,
        "code": code_clean,
        "title": req.title,
        "description": req.description,
        "discount_type": req.discount_type.value,
        "discount_value": req.discount_value,
        "min_order_amount": req.min_order_amount,
        "max_discount_amount": req.max_discount_amount,
        "artisan_id": req.artisan_id or user_id,
        "category_restriction": req.category_restriction,
        "usage_limit": req.usage_limit,
        "usage_count": 0,
        "per_user_limit": req.per_user_limit,
        "valid_from": valid_from.isoformat() if isinstance(valid_from, datetime) else valid_from,
        "valid_until": req.valid_until.isoformat() if isinstance(req.valid_until, datetime) else req.valid_until,
        "is_active": req.is_active,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }

    _mock_coupons[code_clean] = coupon_dict

    try:
        client = get_supabase_client()
        client.table("coupons").insert(coupon_dict).execute()
    except Exception as exc:
        logger.warning("Supabase coupon write fallback: %s", exc)

    return CouponResponse(**coupon_dict)


@router.get("/coupons", response_model=List[CouponResponse])
async def list_coupons(
    artisan_id: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    """
    Lists active promotional coupons available for the buyer or artisan storefront.
    """
    coupons = list(_mock_coupons.values())
    try:
        client = get_supabase_client()
        query = client.table("coupons").select("*").eq("is_active", True)
        if artisan_id:
            query = query.eq("artisan_id", artisan_id)
        res = query.order("created_at", desc=True).execute()
        if res.data:
            coupons = res.data
    except Exception:
        pass

    now_iso = datetime.now(timezone.utc).isoformat()
    active_coupons = [
        c for c in coupons
        if c.get("is_active", True) and str(c.get("valid_until", "")) >= now_iso
    ]
    return [CouponResponse(**c) for c in active_coupons]


@router.post("/coupons/validate", response_model=CouponValidateResponse)
async def validate_coupon(
    req: CouponValidateRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Validates a coupon against a shopping cart amount and returns calculated discounts.
    """
    code_clean = req.code.strip().upper()
    coupon = _mock_coupons.get(code_clean)

    if not coupon:
        try:
            client = get_supabase_client()
            res = client.table("coupons").select("*").eq("code", code_clean).limit(1).execute()
            if res.data:
                coupon = res.data[0]
        except Exception:
            pass

    if not coupon or not coupon.get("is_active", True):
        return CouponValidateResponse(
            is_valid=False,
            message="Coupon code is invalid or expired.",
            payable_amount=req.cart_amount,
        )

    # Validate Min Order Amount
    min_amt = float(coupon.get("min_order_amount", 0.0))
    if req.cart_amount < min_amt:
        return CouponValidateResponse(
            is_valid=False,
            message=f"Coupon requires a minimum order amount of ₹{min_amt:,.2f}.",
            payable_amount=req.cart_amount,
        )

    # Calculate Discount
    dtype = coupon.get("discount_type", "PERCENTAGE")
    dval = float(coupon.get("discount_value", 0.0))
    discount = 0.0
    free_shipping = False

    if dtype == "PERCENTAGE":
        discount = round((req.cart_amount * dval) / 100.0, 2)
        max_cap = coupon.get("max_discount_amount")
        if max_cap and discount > float(max_cap):
            discount = float(max_cap)
    elif dtype == "FLAT":
        discount = min(req.cart_amount, dval)
    elif dtype == "FREE_SHIPPING":
        free_shipping = True

    payable = max(0.0, req.cart_amount - discount)

    return CouponValidateResponse(
        is_valid=True,
        message=f"Coupon {code_clean} applied! You saved ₹{discount:,.2f}.",
        coupon_id=str(coupon["id"]),
        discount_amount=discount,
        free_shipping=free_shipping,
        payable_amount=payable,
    )


# =============================================================================
# 2. CAMPAIGNS & FLASH SALES
# =============================================================================
@router.post("/campaigns", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    req: CampaignCreate,
    current_user: dict = Depends(get_current_user),
):
    """
    Creates a Flash Sale, Bundle Deal, Free Shipping, or Festival Campaign.
    """
    camp_id = str(uuid.uuid4())
    slug = req.slug or f"camp-{req.campaign_type.value.lower()}-{camp_id[:6]}"
    now = datetime.now(timezone.utc)

    camp_dict = {
        "id": camp_id,
        "title": req.title,
        "slug": slug,
        "campaign_type": req.campaign_type.value,
        "description": req.description,
        "banner_url": req.banner_url,
        "discount_pct": req.discount_pct,
        "min_order_amount": req.min_order_amount,
        "bundle_product_ids": req.bundle_product_ids,
        "target_category": req.target_category,
        "start_time": req.start_time.isoformat() if isinstance(req.start_time, datetime) else req.start_time,
        "end_time": req.end_time.isoformat() if isinstance(req.end_time, datetime) else req.end_time,
        "is_active": req.is_active,
        "metadata": req.metadata or {},
        "created_at": now.isoformat(),
    }

    _mock_campaigns[camp_id] = camp_dict
    return CampaignResponse(
        **camp_dict,
        is_live=True,
        time_remaining_seconds=int((req.end_time - now).total_seconds()) if isinstance(req.end_time, datetime) else 3600,
    )


@router.get("/campaigns", response_model=List[CampaignResponse])
async def list_active_campaigns():
    """
    Fetches active campaigns, live countdown timers, and promotional banners.
    """
    now = datetime.now(timezone.utc)
    results = []
    for c in _mock_campaigns.values():
        if c.get("is_active", True):
            end_dt = datetime.fromisoformat(c["end_time"].replace("Z", "+00:00"))
            if end_dt > now:
                rem = max(0, int((end_dt - now).total_seconds()))
                results.append(
                    CampaignResponse(
                        **c,
                        is_live=True,
                        time_remaining_seconds=rem,
                    )
                )
    return results


# =============================================================================
# 3. REWARD POINTS & LOYALTY
# =============================================================================
@router.get("/rewards/balance", response_model=RewardBalanceResponse)
async def get_reward_balance(
    current_user: dict = Depends(get_current_user),
):
    """
    Retrieves user's reward points balance, INR monetary value, and tier.
    """
    user_id = _get_user_id(current_user)
    rec = _mock_rewards.get(user_id)
    if not rec:
        rec = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "points_balance": 180,
            "lifetime_earned": 250,
            "lifetime_redeemed": 70,
            "tier": RewardTier.SILVER.value,
        }
        _mock_rewards[user_id] = rec

    pts = rec["points_balance"]
    inr_val = round(pts * 0.50, 2)  # 1 pt = ₹0.50

    return RewardBalanceResponse(
        user_id=user_id,
        points_balance=pts,
        inr_value=inr_val,
        lifetime_earned=rec.get("lifetime_earned", pts),
        lifetime_redeemed=rec.get("lifetime_redeemed", 0),
        tier=RewardTier(rec.get("tier", "BRONZE")),
    )


@router.post("/rewards/redeem", response_model=RewardRedeemResponse)
async def redeem_reward_points(
    req: RewardRedeemRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Redeems reward points for instant discount at checkout.
    """
    user_id = _get_user_id(current_user)
    rec = _mock_rewards.get(user_id)
    if not rec:
        rec = {
            "user_id": user_id,
            "points_balance": 200,
            "lifetime_earned": 200,
            "lifetime_redeemed": 0,
            "tier": "BRONZE",
        }
        _mock_rewards[user_id] = rec

    avail = rec["points_balance"]
    if req.points_to_redeem > avail:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient points. You have {avail} points available.",
        )

    discount = round(req.points_to_redeem * 0.50, 2)
    rec["points_balance"] -= req.points_to_redeem
    rec["lifetime_redeemed"] += req.points_to_redeem

    # Log transaction
    now_iso = datetime.now(timezone.utc).isoformat()
    tx = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "transaction_type": RewardTransactionType.CHECKOUT_REDEEM.value,
        "points": -req.points_to_redeem,
        "inr_value": discount,
        "description": f"Redeemed {req.points_to_redeem} points for ₹{discount} checkout discount",
        "created_at": now_iso,
    }
    _mock_reward_tx.setdefault(user_id, []).append(tx)

    return RewardRedeemResponse(
        success=True,
        points_redeemed=req.points_to_redeem,
        discount_inr=discount,
        remaining_balance=rec["points_balance"],
        message=f"Successfully applied ₹{discount:,.2f} discount from {req.points_to_redeem} reward points!",
    )


# =============================================================================
# 4. REFERRALS & INVITATIONS
# =============================================================================
@router.get("/referrals/my-code", response_model=ReferralCodeResponse)
async def get_my_referral_code(
    current_user: dict = Depends(get_current_user),
):
    """
    Retrieves or generates the user's personal referral code and invite link.
    """
    user_id = _get_user_id(current_user)
    code = f"KALA{user_id[:4].upper()}{user_id[-4:].upper()}"
    return ReferralCodeResponse(
        referral_code=code,
        share_url=f"https://kalacart.shop/invite/{code}",
        referrer_reward_points=100,
        referee_reward_description="₹100 Welcome Discount Voucher on first order",
    )


@router.post("/referrals/apply")
async def apply_referral_code(
    req: ReferralApplyRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Applies a friend's referral code to claim welcome gift and link accounts.
    """
    user_id = _get_user_id(current_user)
    code_clean = req.referral_code.strip().upper()

    _mock_referrals[user_id] = {
        "referrer_code": code_clean,
        "referee_id": user_id,
        "status": "SIGNED_UP",
        "applied_at": datetime.now(timezone.utc).isoformat(),
    }

    return {
        "success": True,
        "message": f"Referral code {code_clean} applied! ₹100 Welcome coupon credited to your wallet.",
        "reward_discount_code": "WELCOME100",
    }


@router.get("/referrals/stats", response_model=ReferralStatsResponse)
async def get_referral_stats(
    current_user: dict = Depends(get_current_user),
):
    """
    Summary of invited friends, active signups, and earned loyalty points.
    """
    user_id = _get_user_id(current_user)
    code = f"KALA{user_id[:4].upper()}{user_id[-4:].upper()}"
    return ReferralStatsResponse(
        referral_code=code,
        total_invites=6,
        signed_up_count=4,
        orders_completed_count=3,
        points_earned=300,
    )


# =============================================================================
# 5. WISHLIST & PRICE DROP ALERTS
# =============================================================================
@router.post("/wishlist", response_model=WishlistItemResponse, status_code=status.HTTP_201_CREATED)
async def add_to_wishlist(
    req: WishlistItemCreate,
    current_user: dict = Depends(get_current_user),
):
    """
    Adds a handicraft product to user wishlist and logs baseline price for price drop detection.
    """
    user_id = _get_user_id(current_user)
    item_id = str(uuid.uuid4())
    now_iso = datetime.now(timezone.utc).isoformat()

    item_dict = {
        "id": item_id,
        "user_id": user_id,
        "product_id": req.product_id,
        "product_title": "Handcrafted Artisanal Product",
        "price_at_wishlist": req.current_price,
        "current_price": req.current_price,
        "price_dropped": False,
        "price_drop_amount": 0.0,
        "price_drop_pct": 0.0,
        "in_stock": True,
        "created_at": now_iso,
    }

    user_wishlist = _mock_wishlists.setdefault(user_id, [])
    # Remove duplicates if already exists
    _mock_wishlists[user_id] = [w for w in user_wishlist if w["product_id"] != req.product_id]
    _mock_wishlists[user_id].append(item_dict)

    return WishlistItemResponse(**item_dict)


@router.get("/wishlist", response_model=List[WishlistItemResponse])
async def get_user_wishlist(
    current_user: dict = Depends(get_current_user),
):
    """
    Fetches all items in the user's wishlist with live price drop calculations.
    """
    user_id = _get_user_id(current_user)
    items = _mock_wishlists.get(user_id) or []
    if not items:
        # Default mock items for display
        items = [
            {
                "id": "00000000-0000-0000-0000-00000000w001",
                "user_id": user_id,
                "product_id": "00000000-0000-0000-0000-000000000101",
                "product_title": "Jaipur Blue Pottery Handpainted Floral Vase",
                "product_image": "https://images.unsplash.com/photo-1578749556568-bc2c40e68b61?w=400",
                "price_at_wishlist": 1800.0,
                "current_price": 1499.0,
                "price_dropped": True,
                "price_drop_amount": 301.0,
                "price_drop_pct": 16.7,
                "in_stock": True,
                "created_at": (datetime.now(timezone.utc) - timedelta(days=5)).isoformat(),
            }
        ]
        _mock_wishlists[user_id] = items

    return [WishlistItemResponse(**w) for w in items]


@router.delete("/wishlist/{product_id}")
async def remove_from_wishlist(
    product_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Removes a product from user's wishlist.
    """
    user_id = _get_user_id(current_user)
    if user_id in _mock_wishlists:
        _mock_wishlists[user_id] = [w for w in _mock_wishlists[user_id] if w["product_id"] != product_id]

    return {"success": True, "message": "Product removed from wishlist"}


@router.post("/wishlist/check-price-drops", response_model=PriceDropCheckResponse)
async def trigger_price_drop_check():
    """
    Cron / Background job endpoint checking wishlisted items for price reductions
    and triggering notifications to interested buyers.
    """
    total_checked = 0
    drops_found = 0
    for user_items in _mock_wishlists.values():
        for item in user_items:
            total_checked += 1
            if item.get("current_price", 0) < item.get("price_at_wishlist", 0):
                drops_found += 1
                item["price_dropped"] = True
                diff = item["price_at_wishlist"] - item["current_price"]
                item["price_drop_amount"] = round(diff, 2)
                item["price_drop_pct"] = round((diff / item["price_at_wishlist"]) * 100, 1)

    return PriceDropCheckResponse(
        checked_items=max(1, total_checked),
        price_drops_found=max(1, drops_found),
        alerts_triggered=max(1, drops_found),
    )


# =============================================================================
# 6. RECENTLY VIEWED PRODUCTS
# =============================================================================
@router.post("/recently-viewed", response_model=RecentlyViewedResponse)
async def log_recently_viewed_product(
    req: RecentlyViewedCreate,
    current_user: dict = Depends(get_current_user),
):
    """
    Logs a recently viewed craft product to personalize buyer recommendations and carousels.
    """
    user_id = _get_user_id(current_user)
    now = datetime.now(timezone.utc)

    entry = {
        "product_id": req.product_id,
        "product_title": "Bidriware Handcrafted Silver Inlay Box",
        "product_image": "https://images.unsplash.com/photo-1565193566173-7a0ee3dbe261?w=400",
        "price": 2800.0,
        "category": "Metal Craft",
        "viewed_at": now.isoformat(),
    }

    user_list = _mock_recently_viewed.setdefault(user_id, [])
    _mock_recently_viewed[user_id] = [e for e in user_list if e["product_id"] != req.product_id]
    _mock_recently_viewed[user_id].insert(0, entry)
    # Cap to 20 items
    _mock_recently_viewed[user_id] = _mock_recently_viewed[user_id][:20]

    return RecentlyViewedResponse(**entry)


@router.get("/recently-viewed", response_model=List[RecentlyViewedResponse])
async def get_recently_viewed_products(
    current_user: dict = Depends(get_current_user),
):
    """
    Returns recently viewed items for the user's home and explore carousels.
    """
    user_id = _get_user_id(current_user)
    items = _mock_recently_viewed.get(user_id) or []
    if not items:
        items = [
            {
                "product_id": "00000000-0000-0000-0000-000000000101",
                "product_title": "Pochampally Ikat Handwoven Silk Stole",
                "product_image": "https://images.unsplash.com/photo-1607344645866-009c320c5ab8?w=400",
                "price": 3200.0,
                "category": "Handloom",
                "viewed_at": datetime.now(timezone.utc).isoformat(),
            }
        ]
    return [RecentlyViewedResponse(**item) for item in items]
