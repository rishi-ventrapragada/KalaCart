"""
Personalized Recommendation Engine API (Taobao & Meesho Grade).

Endpoints:
- GET  /api/v1/recommendations/feed
- GET  /api/v1/recommendations/similar/{product_id}
- POST /api/v1/recommendations/track
- GET  /api/v1/recommendations/explore
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field

from app.database.connection import get_supabase_client

logger = logging.getLogger(__name__)

router = APIRouter()

DEFAULT_FALLBACK_PRODUCTS = [
    {
        "id": "prod_jaipur_vase_01",
        "title": "Jaipur Blue Pottery Floral Vase",
        "category": "Pottery",
        "price": 1350.0,
        "artisan_name": "Ramesh Kumawat",
        "artisan_id": "seller_ramesh",
        "seller_id": "seller_ramesh",
        "image_urls": ["https://images.unsplash.com/photo-1565193566173-7a0ee3dbe261?w=500"],
        "state": "Rajasthan",
        "city": "Jaipur",
        "rating": 4.9,
        "handmade_verified": True,
        "is_gi_certified": True,
        "seo_tags": ["pottery", "blue pottery", "vase", "ceramic", "jaipur"],
        "created_at": "2026-09-01T10:00:00Z"
    },
    {
        "id": "prod_banarasi_saree_02",
        "title": "Handwoven Banarasi Katan Silk Saree",
        "category": "Textile",
        "price": 8500.0,
        "artisan_name": "Ansari Handlooms",
        "artisan_id": "seller_ansari",
        "seller_id": "seller_ansari",
        "image_urls": ["https://images.unsplash.com/photo-1610030469983-98e550d6193c?w=500"],
        "state": "Uttar Pradesh",
        "city": "Varanasi",
        "rating": 4.8,
        "handmade_verified": True,
        "is_gi_certified": True,
        "seo_tags": ["textile", "saree", "silk", "banarasi", "handloom"],
        "created_at": "2026-09-02T11:00:00Z"
    },
    {
        "id": "prod_dhokra_horse_03",
        "title": "Bastar Dhokra Brass Cast Horse",
        "category": "Metal Art",
        "price": 2200.0,
        "artisan_name": "Sukhram Baghel",
        "artisan_id": "seller_sukhram",
        "seller_id": "seller_sukhram",
        "image_urls": ["https://images.unsplash.com/photo-1606293926075-69a00dbfde81?w=500"],
        "state": "Chhattisgarh",
        "city": "Bastar",
        "rating": 4.7,
        "handmade_verified": True,
        "is_gi_certified": True,
        "seo_tags": ["metal", "brass", "dhokra", "bastar", "figurine"],
        "created_at": "2026-09-03T12:00:00Z"
    },
    {
        "id": "prod_madhubani_art_04",
        "title": "Tree of Life Madhubani Canvas Painting",
        "category": "Painting",
        "price": 3400.0,
        "artisan_name": "Sunita Devi",
        "artisan_id": "seller_sunita",
        "seller_id": "seller_sunita",
        "image_urls": ["https://images.unsplash.com/photo-1579783900882-c0d3dad7b119?w=500"],
        "state": "Bihar",
        "city": "Madhubani",
        "rating": 4.95,
        "handmade_verified": True,
        "is_gi_certified": True,
        "seo_tags": ["painting", "madhubani", "canvas", "bihar", "folk art"],
        "created_at": "2026-09-04T13:00:00Z"
    },
    {
        "id": "prod_bamboo_basket_05",
        "title": "Assam Natural Bamboo Planter Basket",
        "category": "Bamboo Craft",
        "price": 750.0,
        "artisan_name": "Biren Bora",
        "artisan_id": "seller_biren",
        "seller_id": "seller_biren",
        "image_urls": ["https://images.unsplash.com/photo-1590402494682-cd3fb53b1f70?w=500"],
        "state": "Assam",
        "city": "Guwahati",
        "rating": 4.6,
        "handmade_verified": True,
        "is_gi_certified": False,
        "seo_tags": ["bamboo", "basket", "cane", "planter", "assam"],
        "created_at": "2026-09-05T14:00:00Z"
    }
]


class InteractionTrackRequest(BaseModel):
    user_id: str = Field(..., description="Unique user ID")
    interaction_type: str = Field(..., description="SEARCH, CLICK, PURCHASE, RFQ, FOLLOW, CHAT")
    target_id: Optional[str] = Field(None, description="Product ID, Seller ID, or RFQ ID")
    category: Optional[str] = Field(None, description="Craft category")
    tags: Optional[List[str]] = Field(default_factory=list, description="Associated craft tags")
    city: Optional[str] = None
    state: Optional[str] = None


class RecommendationFeedResponse(BaseModel):
    user_id: str
    recommended_for_you: List[Dict[str, Any]]
    because_you_viewed: List[Dict[str, Any]]
    nearby_trending: List[Dict[str, Any]]
    from_followed_stores: List[Dict[str, Any]]
    recently_popular: List[Dict[str, Any]]
    new_arrivals: List[Dict[str, Any]]
    generated_at: str


class CursorExploreResponse(BaseModel):
    items: List[Dict[str, Any]]
    next_cursor: Optional[str]
    has_more: bool


def calculate_jaccard_similarity(tags1: List[str], tags2: List[str]) -> float:
    if not tags1 or not tags2:
        return 0.0
    s1, s2 = set(t.lower() for t in tags1), set(t.lower() for t in tags2)
    intersection = len(s1 & s2)
    union = len(s1 | s2)
    return float(intersection) / float(union) if union > 0 else 0.0


@router.get("/feed", response_model=RecommendationFeedResponse)
async def get_personalized_feed(
    user_id: str = Query("guest_user", description="Buyer ID"),
    city: Optional[str] = Query(None, description="Buyer City"),
    state: Optional[str] = Query(None, description="Buyer State"),
    language: Optional[str] = Query("en", description="Buyer language"),
    supabase=Depends(get_supabase_client),
):
    """
    Generate dynamic 6-section personalized home feed from Supabase.
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    all_products: List[Dict[str, Any]] = []

    try:
        products_res = supabase.table("products").select("*").eq("published", True).eq("is_deleted", False).order("created_at", desc=True).limit(100).execute()
        all_products = products_res.data if products_res.data else []
    except Exception as e:
        logger.warning(f"Could not connect to Supabase products table: {e}")
        all_products = DEFAULT_FALLBACK_PRODUCTS.copy()

    if not all_products:
        all_products = DEFAULT_FALLBACK_PRODUCTS.copy()

    # User Interests
    preferred_categories: Dict[str, float] = {}
    try:
        user_interests_res = supabase.table("user_interests").select("*").eq("user_id", user_id).order("affinity_score", desc=True).execute()
        user_interests = user_interests_res.data if user_interests_res.data else []
        preferred_categories = {row["category"].lower(): float(row.get("affinity_score", 1.0)) for row in user_interests}
    except Exception:
        pass

    # Followed stores
    followed_seller_ids = set()
    try:
        followed_res = supabase.table("store_followers").select("seller_id").eq("buyer_id", user_id).execute()
        followed_seller_ids = set(r["seller_id"] for r in (followed_res.data or []))
    except Exception:
        pass

    # Recent views
    viewed_pids = []
    try:
        views_res = supabase.table("product_views").select("product_id, created_at").eq("user_id", user_id).order("created_at", desc=True).limit(10).execute()
        viewed_pids = [v["product_id"] for v in (views_res.data or [])]
    except Exception:
        pass

    # Section 1: Recommended For You
    def calc_rec_score(p: Dict[str, Any]) -> float:
        cat = str(p.get("category", "")).lower()
        score = preferred_categories.get(cat, 0.5) * 2.0
        if p.get("is_gi_certified"):
            score += 0.5
        if p.get("handmade_verified"):
            score += 0.3
        score += float(p.get("rating", 4.5)) * 0.2
        return score

    sorted_for_you = sorted(all_products, key=calc_rec_score, reverse=True)
    recommended_for_you = sorted_for_you[:12]

    # Section 2: Because You Viewed
    viewed_cats = set()
    for p in all_products:
        if p.get("id") in viewed_pids:
            viewed_cats.add(str(p.get("category", "")).lower())

    because_you_viewed = [
        p for p in all_products 
        if str(p.get("category", "")).lower() in viewed_cats and p.get("id") not in viewed_pids
    ][:10]
    if not because_you_viewed:
        because_you_viewed = sorted_for_you[1:10] if len(sorted_for_you) > 1 else all_products

    # Section 3: Nearby Trending
    nearby_trending = [
        p for p in all_products
        if (state and str(p.get("state", "")).lower() == state.lower())
        or (city and str(p.get("city", "")).lower() == city.lower())
    ][:10]
    if not nearby_trending:
        nearby_trending = sorted(all_products, key=lambda x: float(x.get("rating", 4.5)), reverse=True)[:10]

    # Section 4: From Followed Stores
    from_followed_stores = [
        p for p in all_products
        if p.get("artisan_id") in followed_seller_ids or p.get("seller_id") in followed_seller_ids
    ][:10]
    if not from_followed_stores:
        from_followed_stores = [p for p in all_products if p.get("handmade_verified")][:8]

    # Section 5: Recently Popular
    recently_popular = sorted(all_products, key=lambda x: (float(x.get("rating", 4.5)), float(x.get("price", 0))), reverse=True)[:12]

    # Section 6: New Arrivals
    new_arrivals = all_products[:12]

    return RecommendationFeedResponse(
        user_id=user_id,
        recommended_for_you=recommended_for_you,
        because_you_viewed=because_you_viewed,
        nearby_trending=nearby_trending,
        from_followed_stores=from_followed_stores,
        recently_popular=recently_popular,
        new_arrivals=new_arrivals,
        generated_at=now_iso,
    )


@router.get("/similar/{product_id}")
async def get_similar_products(
    product_id: str,
    limit: int = Query(8, ge=1, le=30),
    supabase=Depends(get_supabase_client),
):
    """
    Get visually & craft-similar items using category, materials, and tags.
    """
    candidates = []
    target = None
    try:
        target_res = supabase.table("products").select("*").eq("id", product_id).execute()
        if target_res.data:
            target = target_res.data[0]
        candidates_res = supabase.table("products").select("*").eq("published", True).neq("id", product_id).limit(60).execute()
        candidates = candidates_res.data or []
    except Exception as e:
        logger.warning(f"Supabase connection fallback: {e}")
        candidates = [p for p in DEFAULT_FALLBACK_PRODUCTS if p.get("id") != product_id]
        if not target and candidates:
            target = DEFAULT_FALLBACK_PRODUCTS[0]

    if not target:
        return {"product_id": product_id, "similar_products": candidates[:limit]}

    target_cat = str(target.get("category", "")).lower()
    target_tags = target.get("seo_tags") or []
    target_price = float(target.get("price") or 1000)

    def similarity_score(c: Dict[str, Any]) -> float:
        score = 0.0
        if str(c.get("category", "")).lower() == target_cat:
            score += 3.0
        c_tags = c.get("seo_tags") or []
        tag_sim = calculate_jaccard_similarity(target_tags, c_tags)
        score += tag_sim * 2.0
        c_price = float(c.get("price") or 1000)
        price_diff_ratio = abs(c_price - target_price) / max(target_price, 1.0)
        if price_diff_ratio < 0.3:
            score += 1.0
        return score

    ranked = sorted(candidates, key=similarity_score, reverse=True)
    return {
        "product_id": product_id,
        "target_category": target.get("category"),
        "similar_products": ranked[:limit],
    }


@router.post("/track", status_code=status.HTTP_200_OK)
async def track_interaction(
    payload: InteractionTrackRequest,
    supabase=Depends(get_supabase_client),
):
    """
    Record user interactions (SEARCH, CLICK, PURCHASE, RFQ, FOLLOW, CHAT)
    and update affinity scores in user_interests in real-time.
    """
    weights = {
        "SEARCH": 1.0,
        "CLICK": 1.5,
        "CHAT": 2.5,
        "RFQ": 3.5,
        "FOLLOW": 4.0,
        "PURCHASE": 5.0,
    }
    weight = weights.get(payload.interaction_type.upper(), 1.0)

    event_data = {
        "buyer_id": payload.user_id,
        "event_type": f"INTERACTION_{payload.interaction_type.upper()}",
        "target_id": payload.target_id,
        "city": payload.city,
        "state": payload.state,
        "metadata": {
            "category": payload.category,
            "tags": payload.tags,
            "weight": weight,
        },
    }
    try:
        supabase.table("analytics_events").insert(event_data).execute()
    except Exception as e:
        logger.warning(f"Analytics event insert skipped: {e}")

    if payload.category:
        try:
            existing = supabase.table("user_interests").select("*").eq("user_id", payload.user_id).eq("category", payload.category).execute()
            if existing.data:
                row = existing.data[0]
                new_affinity = float(row.get("affinity_score", 1.0)) + weight
                update_fields: Dict[str, Any] = {
                    "affinity_score": new_affinity,
                    "last_interaction_at": datetime.now(timezone.utc).isoformat(),
                }
                supabase.table("user_interests").update(update_fields).eq("id", row["id"]).execute()
            else:
                supabase.table("user_interests").insert({
                    "user_id": payload.user_id,
                    "category": payload.category,
                    "tags": payload.tags or [],
                    "affinity_score": weight,
                }).execute()
        except Exception as e:
            logger.warning(f"User interest upsert skipped: {e}")

    return {"status": "success", "recorded_weight": weight}


@router.get("/explore", response_model=CursorExploreResponse)
async def explore_cursor_pagination(
    cursor: Optional[str] = Query(None, description="Created at timestamp cursor"),
    limit: int = Query(15, ge=1, le=50),
    category: Optional[str] = None,
    state: Optional[str] = None,
    supabase=Depends(get_supabase_client),
):
    """
    Infinite scrolling Explore feed with cursor-based pagination.
    """
    items = []
    try:
        query = supabase.table("products").select("*").eq("published", True).eq("is_deleted", False)
        if category and category != "All Categories":
            query = query.ilike("category", f"%{category}%")
        if state and state != "All India" and state != "Nearby":
            query = query.eq("state", state)
        if cursor:
            query = query.lt("created_at", cursor)

        query = query.order("created_at", desc=True).limit(limit + 1)
        res = query.execute()
        items = res.data or []
    except Exception as e:
        logger.warning(f"Supabase explore error: {e}")
        items = DEFAULT_FALLBACK_PRODUCTS.copy()

    has_more = len(items) > limit
    page_items = items[:limit]

    next_cursor = None
    if has_more and page_items:
        next_cursor = page_items[-1].get("created_at")

    return CursorExploreResponse(
        items=page_items,
        next_cursor=next_cursor,
        has_more=has_more,
    )

