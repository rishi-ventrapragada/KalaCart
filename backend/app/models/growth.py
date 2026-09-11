"""
Growth & Marketing Engine Models (Phase 3).
Defines schemas for Coupons, Discounts, Flash Sales, Bundle Offers,
Reward Points, Referrals, Wishlists, and Price Alerts.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class DiscountType(str, Enum):
    PERCENTAGE = "PERCENTAGE"
    FLAT = "FLAT"
    FREE_SHIPPING = "FREE_SHIPPING"


class CampaignType(str, Enum):
    FLASH_SALE = "FLASH_SALE"
    BUNDLE_OFFER = "BUNDLE_OFFER"
    FREE_SHIPPING = "FREE_SHIPPING"
    FESTIVAL_OFFER = "FESTIVAL_OFFER"


class RewardTier(str, Enum):
    BRONZE = "BRONZE"
    SILVER = "SILVER"
    GOLD = "GOLD"
    PLATINUM = "PLATINUM"


class RewardTransactionType(str, Enum):
    PURCHASE_EARN = "PURCHASE_EARN"
    WELCOME_BONUS = "WELCOME_BONUS"
    REFERRAL_BONUS = "REFERRAL_BONUS"
    CHECKOUT_REDEEM = "CHECKOUT_REDEEM"
    EXPIRED = "EXPIRED"


class ReferralStatus(str, Enum):
    PENDING = "PENDING"
    SIGNED_UP = "SIGNED_UP"
    COMPLETED = "COMPLETED"
    REWARDED = "REWARDED"


# -----------------------------------------------------------------------------
# Coupon Models
# -----------------------------------------------------------------------------
class CouponBase(BaseModel):
    code: str = Field(..., min_length=3, max_length=50)
    title: str = Field(..., min_length=3, max_length=200)
    description: Optional[str] = None
    discount_type: DiscountType = DiscountType.PERCENTAGE
    discount_value: float = Field(..., ge=0)
    min_order_amount: float = Field(default=0.0, ge=0)
    max_discount_amount: Optional[float] = Field(default=None, ge=0)
    artisan_id: Optional[str] = None
    category_restriction: Optional[str] = None
    usage_limit: Optional[int] = Field(default=None, ge=1)
    per_user_limit: int = Field(default=1, ge=1)
    valid_from: Optional[datetime] = None
    valid_until: datetime
    is_active: bool = True


class CouponCreate(CouponBase):
    pass


class CouponResponse(CouponBase):
    id: str
    usage_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CouponValidateRequest(BaseModel):
    code: str
    cart_amount: float = Field(..., ge=0)
    artisan_id: Optional[str] = None
    category: Optional[str] = None


class CouponValidateResponse(BaseModel):
    is_valid: bool
    message: str
    coupon_id: Optional[str] = None
    discount_amount: float = 0.0
    free_shipping: bool = False
    payable_amount: float = 0.0


# -----------------------------------------------------------------------------
# Campaign Models
# -----------------------------------------------------------------------------
class CampaignBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    slug: Optional[str] = None
    campaign_type: CampaignType = CampaignType.FLASH_SALE
    description: Optional[str] = None
    banner_url: Optional[str] = None
    discount_pct: float = Field(default=0.0, ge=0, le=100)
    min_order_amount: float = Field(default=0.0, ge=0)
    bundle_product_ids: List[str] = Field(default_factory=list)
    target_category: Optional[str] = None
    start_time: datetime
    end_time: datetime
    is_active: bool = True
    metadata: Optional[Dict[str, Any]] = None


class CampaignCreate(CampaignBase):
    pass


class CampaignResponse(CampaignBase):
    id: str
    time_remaining_seconds: Optional[int] = None
    is_live: bool = False
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# -----------------------------------------------------------------------------
# Reward Points Models
# -----------------------------------------------------------------------------
class RewardBalanceResponse(BaseModel):
    user_id: str
    points_balance: int
    inr_value: float
    lifetime_earned: int
    lifetime_redeemed: int
    tier: RewardTier
    earn_rate_description: str = "1 point per ₹10 spent (1 point = ₹0.50)"

    model_config = ConfigDict(from_attributes=True)


class RewardRedeemRequest(BaseModel):
    points_to_redeem: int = Field(..., ge=1)
    cart_amount: float = Field(..., ge=0)


class RewardRedeemResponse(BaseModel):
    success: bool
    points_redeemed: int
    discount_inr: float
    remaining_balance: int
    message: str


class RewardTransactionResponse(BaseModel):
    id: str
    user_id: str
    transaction_type: RewardTransactionType
    points: int
    inr_value: float
    order_id: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# -----------------------------------------------------------------------------
# Referral Models
# -----------------------------------------------------------------------------
class ReferralCodeResponse(BaseModel):
    referral_code: str
    share_url: str
    referrer_reward_points: int = 100
    referee_reward_description: str = "₹100 Welcome Discount Voucher"


class ReferralApplyRequest(BaseModel):
    referral_code: str


class ReferralStatsResponse(BaseModel):
    referral_code: str
    total_invites: int
    signed_up_count: int
    orders_completed_count: int
    points_earned: int


# -----------------------------------------------------------------------------
# Wishlist & Price Alerts Models
# -----------------------------------------------------------------------------
class WishlistItemCreate(BaseModel):
    product_id: str
    current_price: float = Field(..., ge=0)
    notify_price_drop: bool = True
    notify_back_in_stock: bool = True


class WishlistItemResponse(BaseModel):
    id: str
    user_id: str
    product_id: str
    product_title: Optional[str] = "Artisan Craft"
    product_image: Optional[str] = None
    price_at_wishlist: float
    current_price: float
    price_dropped: bool = False
    price_drop_amount: float = 0.0
    price_drop_pct: float = 0.0
    in_stock: bool = True
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PriceDropCheckResponse(BaseModel):
    checked_items: int
    price_drops_found: int
    alerts_triggered: int


# -----------------------------------------------------------------------------
# Recently Viewed Models
# -----------------------------------------------------------------------------
class RecentlyViewedCreate(BaseModel):
    product_id: str


class RecentlyViewedResponse(BaseModel):
    product_id: str
    product_title: str
    product_image: Optional[str] = None
    price: float
    category: Optional[str] = None
    viewed_at: datetime

    model_config = ConfigDict(from_attributes=True)
