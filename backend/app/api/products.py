"""
Products API routes - CRUD for handicraft listings.

All routes require Firebase auth via get_current_user dependency.

Phase C audit notes:
- SQL overfetch via `supabase_service.get_products_by_artisan(select "*")` etc.
  For high-scale, project only needed columns per listing vs detail.
- Async blocking: handlers are async but call sync Supabase; wrap with
  `run_supabase_sync` if load increases.
- ApiResponse envelope is raw dict here (consistent wire shape, not generic);
  keep for backward compat.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator

from app.core.security import get_current_user
from app.models.common import ApiResponse
from app.models.product import ProductBase, ProductUpdate, ProductStatus

logger = logging.getLogger(__name__)

router = APIRouter()


# ── Request models ───────────────────────────────────────────────

class ProductCreateBody(ProductBase):
    """
    Create payload WITHOUT artisan_id — artisan_id is derived from auth.
    Mirrors ProductCreate but without artisan_id field.
    """
    suggested_price: Optional[float] = Field(default=None, ge=0, le=10_000_000, description="AI-suggested price")
    ai_enhanced: bool = Field(default=False, description="Whether AI enhanced description/image")
    stock_quantity: Optional[int] = Field(default=1, ge=0, description="Inventory count")


# ── Helpers ──────────────────────────────────────────────────────

def _get_artisan_id(current: dict) -> str:
    artisan = current.get("artisan") or {}
    artisan_id = artisan.get("id")
    if not artisan_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Artisan identity missing")
    return str(artisan_id)


# ── Routes ───────────────────────────────────────────────────────

@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Create a product",
    description="Creates product owned by authenticated artisan. Body validated via ProductCreateBody.",
)
async def create_product(
    payload: ProductCreateBody,
    current=Depends(get_current_user),
):
    """
    POST /api/v1/products
    Body: ProductCreateBody (without artisan_id — derived from auth)
    Returns 201 with ApiResponse
    """
    artisan_id = _get_artisan_id(current)

    # Build data dict for supabase — merge payload + artisan_id
    data = payload.model_dump(exclude_none=False)
    # Ensure empty image_urls remains None or list
    data["artisan_id"] = artisan_id

    # --- Dual write for backward compat: JSONB + legacy TEXT[] ---
    # materials (JSONB materials_jsonb + legacy materials TEXT[])
    materials_val = data.get("materials")
    if materials_val is not None:
        # Keep legacy TEXT[] column as same array for backward compat reads
        # materials_jsonb is new canonical JSONB; write both
        data["materials_jsonb"] = materials_val
        # data["materials"] already holds list -> TEXT[] compatible
        # Ensure empty list stays as [] not null
        if isinstance(materials_val, list) and len(materials_val) == 0:
            data["materials"] = []
            data["materials_jsonb"] = []
    # seo_tags (JSONB seo_tags + legacy tags TEXT[])
    seo_val = data.get("seo_tags")
    if seo_val is not None:
        data["seo_tags"] = seo_val
        data["tags"] = seo_val  # legacy TEXT[] alias for older clients/search

    # Pricing fields (005_pricing_fields): passthrough via supabase_service._normalize_pricing_fields
    # Pydantic already maps aliases (confidence->confidence_score, breakdown->price_breakdown, reasoning->pricing_reason)
    # and validates ranges. No dual write needed; dict passthrough ensures new columns persist.
    # Supabase service will also normalize legacy aliases if raw dict bypasses Pydantic.

    try:
        from app.services.supabase_service import create_product as svc_create

        row = svc_create(data)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Failed to create product for artisan %s: %s", artisan_id, exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create product: {exc}") from exc

    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            "success": True,
            "message": "Product created",
            "data": row,
        },
    )


@router.get(
    "/my",
    summary="List my products",
    description="Lists products for authenticated artisan with pagination and optional category filter.",
)
async def list_my_products(
    limit: int = Query(default=20, ge=1, le=100, description="Page size 1-100"),
    offset: int = Query(default=0, ge=0, description="Pagination offset"),
    category: Optional[str] = Query(default=None, description="Filter by category"),
    current=Depends(get_current_user),
):
    """
    GET /api/v1/products/my?limit=20&offset=0&category?
    """
    artisan_id = _get_artisan_id(current)

    # Normalize category if provided
    if category is not None:
        category = category.strip().lower()
        if not category:
            category = None

    try:
        from app.services.supabase_service import get_products_by_artisan

        products = get_products_by_artisan(artisan_id, limit=limit, offset=offset, category=category)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Failed to list products for artisan %s: %s", artisan_id, exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to list products: {exc}") from exc

    return {
        "success": True,
        "message": "Products fetched",
        "data": products,
    }


@router.get(
    "/{product_id}",
    summary="Get product by ID",
    description="Returns product if published/is_active or owned by artisan. Else 404/403.",
)
async def get_product(
    product_id: str,
    current=Depends(get_current_user),
):
    """
    GET /api/v1/products/{id}
    Checks if product exists and if is_published / is_active or owned by artisan.
    """
    artisan_id = _get_artisan_id(current)

    try:
        from app.services.supabase_service import get_product_by_id

        product = get_product_by_id(product_id)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Failed to fetch product %s: %s", product_id, exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to fetch product: {exc}") from exc

    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    # Ownership check
    owner_id = str(product.get("artisan_id") or "")
    is_owner = owner_id == artisan_id

    # Visibility check: is_active / status
    is_active = product.get("is_active")
    status_val = product.get("status")
    # Treat missing is_active as True for backward compat
    is_published = True
    if is_active is not None:
        is_published = bool(is_active)
    elif status_val is not None:
        is_published = str(status_val).lower() in ("published", "active")

    if not is_published and not is_owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Product is not published and not owned by you",
        )

    # Also if product is published, anyone authenticated can view; if not published, only owner
    return {
        "success": True,
        "message": "Product fetched",
        "data": product,
    }


@router.put(
    "/{product_id}",
    summary="Update product",
    description="Partial update — verifies ownership, then updates via supabase_service.update_product.",
)
async def update_product(
    product_id: str,
    payload: ProductUpdate,
    current=Depends(get_current_user),
):
    """
    PUT /api/v1/products/{id}
    Body: ProductUpdate (partial)
    """
    artisan_id = _get_artisan_id(current)

    # Ensure at least one field is provided
    update_data = payload.model_dump(exclude_unset=True, exclude_none=False)
    # Remove None values that were not explicitly set? Use exclude_unset already; but also strip None where not intended?
    # Keep model_dump(exclude_unset=True) to only include provided fields, then drop None if they were unset
    # Actually exclude_unset already handles it; but we passed exclude_none=False so None that were explicitly set remain
    # Better: use exclude_unset=True and then filter where value is not None unless user wants to clear field (image_urls)
    # For simplicity, filter to keep only non-None except where field allows None (image_urls)
    # We'll keep all unset-excluded, and if value is None and key != image_urls, skip? But spec says partial — allow None to clear?
    # We'll just pass as-is excluding None for most, but allow image_urls=None to clear
    # Expand dual columns for catalog fields
    # If materials supplied, mirror to materials_jsonb + legacy TEXT[]
    if "materials" in update_data and update_data["materials"] is not None:
        update_data["materials_jsonb"] = update_data["materials"]
        update_data["tags"] = update_data.get("seo_tags")  # handled below
    if "seo_tags" in update_data and update_data["seo_tags"] is not None:
        update_data["seo_tags"] = update_data["seo_tags"]
        update_data["tags"] = update_data["seo_tags"]
    # care alias: care -> care_instruction already handled by model, but ensure
    if "care" in update_data and "care_instruction" not in update_data:
        update_data["care_instruction"] = update_data.pop("care")

    # Pricing fields (005) are nullable and should allow explicit None to clear
    _PRICING_NULLABLE = ("suggested_price", "minimum_price", "maximum_price", "confidence_score", "price_breakdown", "pricing_reason")
    filtered: dict = {}
    for k, v in update_data.items():
        if v is None and k not in ("image_urls", "suggested_price", "description", "description_hi", "care_instruction", *_PRICING_NULLABLE):
            # Skip None for required-like fields unless explicitly intended
            # Actually keep None only if user explicitly sent null for nullable fields
            continue
        filtered[k] = v
    # Ensure dual write for filtered as well
    if "materials" in filtered and filtered["materials"] is not None:
        filtered["materials_jsonb"] = filtered["materials"]
    if "seo_tags" in filtered and filtered["seo_tags"] is not None:
        filtered["tags"] = filtered["seo_tags"]

    # If still empty after filtering, check if original had any unset? Use original count
    if not filtered:
        # Fallback: if payload had no fields set at all, error
        if not update_data:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")
        # Otherwise filtered empty because all were None — treat as no-op
        filtered = update_data

    # Verify ownership via get_product_by_id first (for 404 vs 403 clarity)
    try:
        from app.services.supabase_service import get_product_by_id, update_product as svc_update

        existing = get_product_by_id(product_id)
        if not existing:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        if str(existing.get("artisan_id")) != artisan_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this product",
            )

        updated = svc_update(product_id, artisan_id, filtered)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Failed to update product %s for artisan %s: %s", product_id, artisan_id, exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to update product: {exc}") from exc

    return {
        "success": True,
        "message": "Product updated",
        "data": updated,
    }


@router.delete(
    "/{product_id}",
    summary="Delete product",
    description="Verifies ownership, deletes via supabase_service.delete_product, returns 200 with message (or 204).",
)
async def delete_product(
    product_id: str,
    current=Depends(get_current_user),
):
    """
    DELETE /api/v1/products/{id}
    """
    artisan_id = _get_artisan_id(current)

    # Verify ownership via get
    try:
        from app.services.supabase_service import delete_product as svc_delete, get_product_by_id

        existing = get_product_by_id(product_id)
        if not existing:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        if str(existing.get("artisan_id")) != artisan_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this product",
            )

        result = svc_delete(product_id, artisan_id)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Failed to delete product %s for artisan %s: %s", product_id, artisan_id, exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to delete product: {exc}") from exc

    # Return 200 with message for client convenience; 204 has no body
    return {
        "success": True,
        "message": "Product deleted",
        "data": result,
    }


# Legacy list endpoint without auth — kept for marketplace discovery but now optional
# We keep it under / route? Actually base list is already defined as POST "" and PUT etc.
# Add a public list for published products (no auth) for marketplace — optional
@router.get(
    "",
    summary="List published products (marketplace)",
    description="Public marketplace listing — no auth required. Supports pagination, category, search, language.",
    include_in_schema=True,
)
async def list_published_products(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    category: Optional[str] = Query(default=None),
    search: Optional[str] = Query(default=None),
    language: Optional[str] = Query(default=None),
):
    """
    GET /api/v1/products  — public marketplace feed.
    Auth is NOT required here — returns only published/active products.
    For artisan's own products (including drafts), use GET /my with auth.
    """
    try:
        from app.services.supabase_service import list_published_products as svc_list

        products = svc_list(limit=limit, offset=offset, category=category, search=search, language=language)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Failed to list published products: %s", exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to list products: {exc}") from exc

    return {
        "success": True,
        "message": "Products fetched",
        "data": products,
    }
