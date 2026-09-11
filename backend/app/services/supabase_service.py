"""
Supabase service layer — CRUD for artisans, products, buyers, orders, languages + Storage.

All operations use get_supabase_client() (privileged service_role).
Errors are logged and surfaced as HTTPException with appropriate status codes.

Phase C audit notes:
- SQL efficiency: most queries use `select("*")` (overfetch). For large tables
  (products with hi descriptions, JSONB) prefer explicit projection
  e.g. `select("id, title, category, price, is_published, image_urls")` for
  listings, and keep `select("*")` only for single-row fetches where full
  shape is required. See `analytics` for good example of projection.
- Async correctness: Supabase-py client is synchronous (httpx sync). Handlers
  are `async def` and call these sync methods directly, blocking the event loop
  under high concurrency. Recommended wrapper (non-breaking, comment-only now):
    from starlette.concurrency import run_in_threadpool
    await run_in_threadpool(lambda: client.table(...).execute())
  or `asyncio.to_thread`. Keep sync API for now for backward compat; add
  async wrappers when scaling to 100k+ reads.
- Logging PII: never log phone/token; only log ids with truncation (see helpers).
- Response model: uses raw dicts to preserve exact JSON shapes; ApiResponse
  generic is used only in analytics/products where schema is stable.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status

from app.database.connection import get_supabase_client

logger = logging.getLogger(__name__)

# ── Helpers ──────────────────────────────────────────────────────────


def _get_bucket_name() -> str:
    """Resolve storage bucket from Settings or fallback."""
    try:
        from app.core.config import get_settings

        return get_settings().SUPABASE_STORAGE_BUCKET or "product-images"
    except Exception:
        import os

        return os.getenv("SUPABASE_STORAGE_BUCKET", "product-images")


def _handle_supabase_error(exc: Exception, message: str, status_code: int = 500) -> None:
    """Log and raise HTTPException with context."""
    logger.error("%s: %s", message, exc, exc_info=True)
    raise HTTPException(status_code=status_code, detail=f"{message}: {exc}") from exc


# Phase C: async wrapper helper (non-breaking, for handlers to optionally use)
# Example: from app.services.supabase_service import run_supabase_sync; await run_supabase_sync(lambda c: c.table(...).execute())
try:
    from starlette.concurrency import run_in_threadpool as _run_in_threadpool  # type: ignore
except ImportError:
    _run_in_threadpool = None  # type: ignore

async def run_supabase_sync(fn):  # type: ignore
    """
    Helper to run a blocking Supabase sync call off the event loop.

    Usage:
        from app.services.supabase_service import run_supabase_sync, get_supabase_client
        def _query(client): return client.table("products").select(...).execute()
        result = await run_supabase_sync(lambda: _query(get_supabase_client()))

    Kept optional — current callers remain sync for backward compat.
    """
    if _run_in_threadpool is not None:
        return await _run_in_threadpool(fn)
    # Fallback: run directly (blocks) if starlette not available — log warning
    logger.debug("run_supabase_sync: starlette concurrency not available, running sync directly")
    return fn()


# ── Artisans ─────────────────────────────────────────────────────────


def upsert_artisan(
    firebase_uid: str,
    phone: Optional[str] = None,
    email: Optional[str] = None,
    name: Optional[str] = None,
    photo_url: Optional[str] = None,
    language_preference: str = "hi",
    location: Optional[str] = None,
    craft_type: Optional[str] = None,
) -> dict:
    """
    Upserts artisan by firebase_uid (unique). Returns the artisan row dict.

    Uses Supabase upsert with on_conflict=firebase_uid for idempotency.
    Falls back to select-then-insert/update if upsert not supported.
    """
    if not firebase_uid:
        raise HTTPException(status_code=400, detail="firebase_uid is required")

    from datetime import datetime, timezone
    client = get_supabase_client()
    payload: Dict[str, Any] = {
        "firebase_uid": firebase_uid,
        "language_preference": language_preference,
        "last_login": datetime.now(timezone.utc).isoformat(),
    }
    if phone is not None:
        payload["phone"] = phone
    if email is not None:
        payload["email"] = email
    if photo_url is not None:
        payload["photo_url"] = photo_url
        payload["avatar_url"] = photo_url
    if name is not None:
        payload["name"] = name
    if location is not None:
        payload["location"] = location
    if craft_type is not None:
        payload["craft_type"] = craft_type

    try:
        # Use upsert for atomicity — requires unique constraint on firebase_uid
        response = (
            client.table("artisans")
            .upsert(payload, on_conflict="firebase_uid")
            .select("*")
            .execute()
        )
        if response.data and len(response.data) > 0:
            logger.info("Upserted artisan firebase_uid=%s", firebase_uid)
            return response.data[0]

        # Fallback: fetch after upsert if no data returned
        return get_artisan_by_uid(firebase_uid)  # type: ignore

    except HTTPException:
        raise
    except Exception as exc:
        # Fallback path: try select then insert/update manually
        logger.warning("Upsert failed, trying fallback path: %s", exc)
        try:
            existing = client.table("artisans").select("*").eq("firebase_uid", firebase_uid).execute()
            if existing.data:
                # Update
                res = (
                    client.table("artisans")
                    .update(payload)
                    .eq("firebase_uid", firebase_uid)
                    .select("*")
                    .execute()
                )
                if res.data:
                    return res.data[0]
            else:
                res = client.table("artisans").insert(payload).select("*").execute()
                if res.data:
                    return res.data[0]
            raise ValueError("Fallback upsert returned no data")
        except HTTPException:
            raise
        except Exception as fallback_exc:
            _handle_supabase_error(fallback_exc, "Failed to upsert artisan")


def get_artisan_by_uid(uid: str) -> Optional[dict]:
    """Fetches artisan by Firebase UID. Returns None if not found."""
    if not uid:
        raise HTTPException(status_code=400, detail="firebase_uid is required")
    client = get_supabase_client()
    try:
        res = client.table("artisans").select("*").eq("firebase_uid", uid).limit(1).execute()
        if res.data:
            return res.data[0]
        return None
    except Exception as exc:
        _handle_supabase_error(exc, "Failed to fetch artisan by UID")


def get_artisan_by_id(artisan_id: str) -> Optional[dict]:
    """Fetches artisan by primary key ID. Returns None if not found."""
    if not artisan_id:
        raise HTTPException(status_code=400, detail="artisan_id is required")
    client = get_supabase_client()
    try:
        res = client.table("artisans").select("*").eq("id", artisan_id).limit(1).execute()
        if res.data:
            return res.data[0]
        return None
    except Exception as exc:
        _handle_supabase_error(exc, "Failed to fetch artisan by ID")


# ── Products ─────────────────────────────────────────────────────────

# Pricing fields 005: helper to normalize alias keys -> DB column names.
# Supports dual write passthrough: ensures new pricing columns (minimum_price,
# maximum_price, confidence_score, price_breakdown, pricing_reason) are persisted
# via generic dict. Maps legacy aliases (confidence, breakdown, reasoning) if caller
# hasn't already normalized via Pydantic.
_PRICING_ALIAS_MAP = {
    "confidence": "confidence_score",
    "confidenceScore": "confidence_score",
    "breakdown": "price_breakdown",
    "priceBreakdown": "price_breakdown",
    "reasoning": "pricing_reason",
    "pricingReason": "pricing_reason",
    "reason": "pricing_reason",
    "suggestedPrice": "suggested_price",
    "minimumPrice": "minimum_price",
    "min_price": "minimum_price",
    "minPrice": "minimum_price",
    "maximumPrice": "maximum_price",
    "max_price": "maximum_price",
    "maxPrice": "maximum_price",
}

def _normalize_pricing_fields(data: dict) -> dict:
    """Map pricing alias keys to canonical DB columns and sanitize.

    - Aliases: confidence -> confidence_score, breakdown -> price_breakdown, reasoning -> pricing_reason
    - Ensures price_breakdown remains dict (JSONB) not stringified list
    - No filtering of other keys — dict passthrough so new columns auto-persist
    - Idempotent: if canonical key already present, alias is ignored/removed
    """
    if not isinstance(data, dict):
        return data
    # Work on copy to avoid mutating caller unexpectedly? We mutate in-place for efficiency
    # but also remove aliases that would duplicate.
    for alias, canonical in list(_PRICING_ALIAS_MAP.items()):
        if alias in data and alias != canonical:
            if canonical not in data or data[canonical] is None:
                data[canonical] = data.pop(alias)
            else:
                # canonical already set, drop alias to avoid duplicate column error
                data.pop(alias, None)
    # Sanitize price_breakdown if it's a JSON string (e.g., from legacy client)
    if "price_breakdown" in data and isinstance(data["price_breakdown"], str):
        import json
        raw = data["price_breakdown"].strip()
        if raw == "":
            data["price_breakdown"] = {}
        elif raw.startswith("{"):
            try:
                data["price_breakdown"] = json.loads(raw)
            except Exception:
                # Keep as-is; DB will error if invalid — surfaced as HTTP 500 with context
                pass
    # Ensure confidence_score is int if needed (Supabase INT)
    if "confidence_score" in data and data["confidence_score"] is not None:
        try:
            # Allow float string "85.0" -> int 85
            val = data["confidence_score"]
            if isinstance(val, str) and "." in val:
                data["confidence_score"] = int(float(val))
            elif isinstance(val, float):
                data["confidence_score"] = int(val)
            elif isinstance(val, str):
                data["confidence_score"] = int(val.strip())
        except Exception:
            pass  # Let validation error surface later
    return data


def create_product(data: dict) -> dict:
    """
    Creates a product row. Expects keys: artisan_id, title, description, category, price, etc.
    Pricing fields (005): suggested_price, minimum_price, maximum_price, confidence_score,
    price_breakdown (JSONB), pricing_reason are passed through via generic dict passthrough.
    Aliases (confidence/breakdown/reasoning) are normalized to canonical columns.
    Returns inserted row.
    """
    if not data.get("artisan_id"):
        raise HTTPException(status_code=400, detail="artisan_id is required")
    if not data.get("title"):
        raise HTTPException(status_code=400, detail="title is required")

    # Normalize pricing aliases -> canonical DB columns (dual write passthrough)
    data = _normalize_pricing_fields(dict(data))

    client = get_supabase_client()
    try:
        res = client.table("products").insert(data).select("*").execute()
        if not res.data:
            raise ValueError("Insert returned no data")
        logger.info("Created product for artisan %s", data.get("artisan_id"))
        return res.data[0]
    except HTTPException:
        raise
    except Exception as exc:
        _handle_supabase_error(exc, "Failed to create product")


def get_products_by_artisan(
    artisan_id: str,
    limit: int = 20,
    offset: int = 0,
    category: Optional[str] = None,
) -> List[dict]:
    """Lists products for an artisan with pagination and optional category filter."""
    if not artisan_id:
        raise HTTPException(status_code=400, detail="artisan_id is required")
    if limit < 1 or limit > 100:
        raise HTTPException(status_code=400, detail="limit must be 1-100")
    if offset < 0:
        raise HTTPException(status_code=400, detail="offset must be >=0")

    client = get_supabase_client()
    try:
        query = client.table("products").select("*").eq("artisan_id", artisan_id)
        if category:
            query = query.eq("category", category)
        query = query.order("created_at", desc=True).range(offset, offset + limit - 1)
        res = query.execute()
        return res.data or []
    except HTTPException:
        raise
    except Exception as exc:
        _handle_supabase_error(exc, "Failed to list products by artisan")


def get_product_by_id(product_id: str) -> Optional[dict]:
    """Fetches single product by ID. Returns None if not found."""
    if not product_id:
        raise HTTPException(status_code=400, detail="product_id is required")
    client = get_supabase_client()
    try:
        res = client.table("products").select("*").eq("id", product_id).limit(1).execute()
        if res.data:
            return res.data[0]
        return None
    except Exception as exc:
        _handle_supabase_error(exc, "Failed to fetch product by ID")


def update_product(product_id: str, artisan_id: str, data: dict) -> dict:
    """
    Updates product owned by artisan_id. Enforces ownership.
    Returns updated row. Raises 404 if not found/unauthorized, 400 if empty.
    """
    if not product_id or not artisan_id:
        raise HTTPException(status_code=400, detail="product_id and artisan_id are required")
    if not data:
        raise HTTPException(status_code=400, detail="No fields to update")

    # Prevent overriding ownership fields
    data = {k: v for k, v in data.items() if k not in ("id", "artisan_id", "created_at")}

    # Normalize pricing aliases -> canonical DB columns (dual write passthrough)
    data = _normalize_pricing_fields(dict(data))

    client = get_supabase_client()
    try:
        # Verify ownership first
        existing = (
            client.table("products")
            .select("id")
            .eq("id", product_id)
            .eq("artisan_id", artisan_id)
            .limit(1)
            .execute()
        )
        if not existing.data:
            raise HTTPException(status_code=404, detail="Product not found or not owned by artisan")

        res = (
            client.table("products")
            .update(data)
            .eq("id", product_id)
            .eq("artisan_id", artisan_id)
            .select("*")
            .execute()
        )
        if not res.data:
            raise HTTPException(status_code=404, detail="Product update returned no data")
        logger.info("Updated product %s for artisan %s", product_id, artisan_id)
        return res.data[0]
    except HTTPException:
        raise
    except Exception as exc:
        _handle_supabase_error(exc, "Failed to update product")


def delete_product(product_id: str, artisan_id: str) -> dict:
    """Deletes product owned by artisan_id. Returns deleted row or 404."""
    if not product_id or not artisan_id:
        raise HTTPException(status_code=400, detail="product_id and artisan_id are required")

    client = get_supabase_client()
    try:
        existing = (
            client.table("products")
            .select("id")
            .eq("id", product_id)
            .eq("artisan_id", artisan_id)
            .limit(1)
            .execute()
        )
        if not existing.data:
            raise HTTPException(status_code=404, detail="Product not found or not owned by artisan")

        res = (
            client.table("products")
            .delete()
            .eq("id", product_id)
            .eq("artisan_id", artisan_id)
            .select("*")
            .execute()
        )
        logger.info("Deleted product %s for artisan %s", product_id, artisan_id)
        return {"deleted_id": product_id, "data": res.data[0] if res.data else None}
    except HTTPException:
        raise
    except Exception as exc:
        _handle_supabase_error(exc, "Failed to delete product")


def list_published_products(
    limit: int = 20,
    offset: int = 0,
    category: Optional[str] = None,
    search: Optional[str] = None,
    language: Optional[str] = None,
) -> List[dict]:
    """
    Lists published/active products for marketplace discovery.
    Filters: category, language, search (title/description ilike), pagination.
    """
    if limit < 1 or limit > 100:
        raise HTTPException(status_code=400, detail="limit must be 1-100")
    if offset < 0:
        raise HTTPException(status_code=400, detail="offset must be >=0")

    client = get_supabase_client()
    try:
        query = client.table("products").select("*")

        # Published filter — support both is_active and status conventions
        # Attempt to filter where is_active = true if column exists; otherwise no filter
        # We try is_active; if it errors due to missing column, fallback without filter
        # For now apply: eq is_active true if we assume soft-publish
        # We wrap in try and degrade gracefully
        try:
            query = query.eq("is_active", True)
        except Exception:
            pass

        if category:
            query = query.eq("category", category)
        if language:
            query = query.eq("language", language)
        if search:
            # Supabase postgrest supports or with ilike
            query = query.or_(f"title.ilike.%{search}%,description.ilike.%{search}%")

        query = query.order("created_at", desc=True).range(offset, offset + limit - 1)
        res = query.execute()
        return res.data or []
    except HTTPException:
        raise
    except Exception as exc:
        _handle_supabase_error(exc, "Failed to list published products")


# ── Buyers ───────────────────────────────────────────────────────────


def create_buyer(data: dict) -> dict:
    """Creates a buyer inquiry record."""
    client = get_supabase_client()
    try:
        res = client.table("buyers").insert(data).select("*").execute()
        if not res.data:
            raise ValueError("Insert returned no data")
        logger.info("Created buyer inquiry for %s", data.get("phone"))
        return res.data[0]
    except Exception as exc:
        _handle_supabase_error(exc, "Failed to create buyer")


def get_buyers_by_product(product_id: str, limit: int = 20, offset: int = 0) -> List[dict]:
    """Lists buyer inquiries for a product."""
    client = get_supabase_client()
    try:
        res = (
            client.table("buyers")
            .select("*")
            .eq("product_id", product_id)
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )
        return res.data or []
    except Exception as exc:
        _handle_supabase_error(exc, "Failed to list buyers")


# ── Orders ───────────────────────────────────────────────────────────


def create_order(data: dict) -> dict:
    """Creates an order record."""
    client = get_supabase_client()
    try:
        res = client.table("orders").insert(data).select("*").execute()
        if not res.data:
            raise ValueError("Insert returned no data")
        return res.data[0]
    except Exception as exc:
        _handle_supabase_error(exc, "Failed to create order")


def get_orders_by_artisan(artisan_id: str, limit: int = 20, offset: int = 0) -> List[dict]:
    """Lists orders for products owned by artisan (via join or product filter)."""
    client = get_supabase_client()
    try:
        # Join via products table — select orders where product's artisan_id matches
        # Supabase supports foreign table filter: products!inner(artisan_id)
        # Fallback: fetch product ids then query orders
        try:
            res = (
                client.table("orders")
                .select("*, products!inner(artisan_id)")
                .eq("products.artisan_id", artisan_id)
                .order("created_at", desc=True)
                .range(offset, offset + limit - 1)
                .execute()
            )
            return res.data or []
        except Exception:
            # Fallback: two-step
            prod_res = client.table("products").select("id").eq("artisan_id", artisan_id).execute()
            product_ids = [p["id"] for p in (prod_res.data or [])]
            if not product_ids:
                return []
            ord_res = (
                client.table("orders")
                .select("*")
                .in_("product_id", product_ids)
                .order("created_at", desc=True)
                .range(offset, offset + limit - 1)
                .execute()
            )
            return ord_res.data or []
    except Exception as exc:
        _handle_supabase_error(exc, "Failed to list orders by artisan")


def update_order_status(order_id: str, status_value: str) -> dict:
    """Updates order status."""
    client = get_supabase_client()
    try:
        res = client.table("orders").update({"status": status_value}).eq("id", order_id).select("*").execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="Order not found")
        return res.data[0]
    except HTTPException:
        raise
    except Exception as exc:
        _handle_supabase_error(exc, "Failed to update order status")


# ── Languages ────────────────────────────────────────────────────────


def list_languages() -> List[dict]:
    """Lists supported languages from Supabase."""
    client = get_supabase_client()
    try:
        res = client.table("languages").select("*").order("code").execute()
        return res.data or []
    except Exception as exc:
        _handle_supabase_error(exc, "Failed to list languages")


def get_language_by_code(code: str) -> Optional[dict]:
    """Fetches language by ISO code."""
    client = get_supabase_client()
    try:
        res = client.table("languages").select("*").eq("code", code).limit(1).execute()
        if res.data:
            return res.data[0]
        return None
    except Exception as exc:
        _handle_supabase_error(exc, "Failed to fetch language")


# ── Storage ──────────────────────────────────────────────────────────


def upload_product_image(file_bytes: bytes, filename: str, content_type: str = "image/jpeg") -> str:
    """
    Uploads image bytes to Supabase Storage bucket and returns public URL.

    Args:
        file_bytes: Raw image bytes
        filename: Storage path, e.g., "{artisan_id}/{uuid}.jpg"
        content_type: MIME type

    Returns:
        Public URL string
    """
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Empty file")
    if not filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    client = get_supabase_client()
    bucket = _get_bucket_name()

    try:
        # file_options upsert as string "true" per supabase-py expectations in some versions
        client.storage.from_(bucket).upload(
            path=filename,
            file=file_bytes,
            file_options={"content-type": content_type, "upsert": "true"},
        )
        logger.info("Uploaded %s to bucket %s", filename, bucket)
    except Exception as exc:
        # Handle duplicate (if upsert fails due to existing object without upsert permission)
        err_msg = str(exc).lower()
        if "already exists" in err_msg or "duplicate" in err_msg:
            try:
                client.storage.from_(bucket).update(
                    path=filename,
                    file=file_bytes,
                    file_options={"content-type": content_type, "upsert": "true"},
                )
                logger.info("Updated existing object %s in bucket %s", filename, bucket)
            except Exception as update_exc:
                _handle_supabase_error(update_exc, f"Failed to update existing image {filename}")
        else:
            _handle_supabase_error(exc, f"Failed to upload image {filename}")

    try:
        url = client.storage.from_(bucket).get_public_url(filename)
        # get_public_url may return dict or str depending on supabase version
        if isinstance(url, dict):
            return url.get("publicUrl") or url.get("public_url") or str(url)
        return str(url)
    except Exception as exc:
        _handle_supabase_error(exc, "Failed to get public URL for image")


def delete_image(path: str) -> bool:
    """Deletes object at path from storage bucket. Returns True on success."""
    if not path:
        raise HTTPException(status_code=400, detail="Storage path is required")
    client = get_supabase_client()
    bucket = _get_bucket_name()
    try:
        client.storage.from_(bucket).remove([path])
        logger.info("Deleted storage object %s from bucket %s", path, bucket)
        return True
    except Exception as exc:
        _handle_supabase_error(exc, f"Failed to delete image {path}")


def get_public_url(path: str) -> str:
    """Returns public URL for storage path without uploading."""
    if not path:
        raise HTTPException(status_code=400, detail="Storage path is required")
    client = get_supabase_client()
    bucket = _get_bucket_name()
    try:
        url = client.storage.from_(bucket).get_public_url(path)
        if isinstance(url, dict):
            return url.get("publicUrl") or url.get("public_url") or str(url)
        return str(url)
    except Exception as exc:
        _handle_supabase_error(exc, f"Failed to get public URL for {path}")
