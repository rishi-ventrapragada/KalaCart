import uuid
import logging
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.security import get_current_user
from app.database.connection import get_supabase_client
from app.models.inventory import (
    ProductInventoryResponse,
    ProductInventoryCreate,
    ProductInventoryUpdate,
    StockAdjustmentRequest,
    StockMovementResponse,
    StockMovementType,
    RawMaterialCreate,
    RawMaterialUpdate,
    RawMaterialResponse,
    InventoryDashboardMetrics,
    InventoryAnalyticsResponse,
)
from app.services import inventory_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/inventory", tags=["inventory"])


def _get_user_id(current_user: dict) -> str:
    if current_user.get("uid"):
        return str(current_user["uid"])
    if current_user.get("artisan") and current_user["artisan"].get("id"):
        return str(current_user["artisan"]["id"])
    return "00000000-0000-0000-0000-000000000001"


@router.get("/dashboard", response_model=InventoryDashboardMetrics)
async def get_inventory_dashboard(current_user: dict = Depends(get_current_user)):
    user_id = _get_user_id(current_user)
    return inventory_service.get_dashboard_metrics(user_id)


@router.get("/analytics", response_model=InventoryAnalyticsResponse)
async def get_inventory_analytics(current_user: dict = Depends(get_current_user)):
    user_id = _get_user_id(current_user)
    return inventory_service.get_inventory_analytics(user_id)


@router.get("/products", response_model=List[ProductInventoryResponse])
async def list_product_inventory(
    status_filter: Optional[str] = Query(None, description="in_stock, low_stock, out_of_stock"),
    current_user: dict = Depends(get_current_user),
):
    user_id = _get_user_id(current_user)
    client = get_supabase_client()

    products_map = {}
    try:
        p_res = client.table("products").select("id, title, price, category, image_urls").eq("artisan_id", user_id).execute()
        if p_res.data:
            for p in p_res.data:
                products_map[p["id"]] = p
    except Exception:
        pass

    inv_list = []
    try:
        res = client.table("product_inventory").select("*").eq("artisan_id", user_id).execute()
        if res.data:
            inv_list = res.data
    except Exception:
        pass

    if not inv_list:
        inv_list = [v for v in inventory_service._mock_inventory.values() if v.get("artisan_id") == user_id]

    # If user has products but no inventory yet, auto initialize
    for pid, pdata in products_map.items():
        if not any(item["product_id"] == pid for item in inv_list):
            new_inv = inventory_service.get_or_create_inventory(pid, user_id, initial_stock=10)
            inv_list.append(new_inv)

    response_items = []
    for inv in inv_list:
        pid = inv["product_id"]
        avail = inv.get("available_stock", 0)
        min_st = inv.get("minimum_stock", 5)

        if avail == 0:
            badge = "out_of_stock"
        elif avail <= min_st:
            badge = "low_stock"
        else:
            badge = "in_stock"

        if status_filter and status_filter != badge:
            continue

        p_info = products_map.get(pid, {})
        img_urls = p_info.get("image_urls")
        first_img = img_urls[0] if (isinstance(img_urls, list) and img_urls) else None

        response_items.append(
            ProductInventoryResponse(
                id=inv["id"],
                product_id=pid,
                artisan_id=inv["artisan_id"],
                sku=inv.get("sku"),
                barcode=inv.get("barcode"),
                available_stock=avail,
                reserved_stock=inv.get("reserved_stock", 0),
                sold_stock=inv.get("sold_stock", 0),
                minimum_stock=min_st,
                product_title=p_info.get("title", f"Artisan Product {inv.get('sku', '')}"),
                product_price=p_info.get("price", 1500.0),
                product_image_url=first_img,
                category=p_info.get("category", "Craft"),
                status_badge=badge,
                created_at=inv.get("created_at") or datetime.now(timezone.utc),
                updated_at=inv.get("updated_at") or datetime.now(timezone.utc),
            )
        )

    return response_items


@router.get("/products/{product_id}", response_model=ProductInventoryResponse)
async def get_product_inventory(product_id: str, current_user: dict = Depends(get_current_user)):
    user_id = _get_user_id(current_user)
    inv = inventory_service.get_or_create_inventory(product_id, user_id)
    avail = inv.get("available_stock", 0)
    min_st = inv.get("minimum_stock", 5)
    badge = "out_of_stock" if avail == 0 else ("low_stock" if avail <= min_st else "in_stock")

    return ProductInventoryResponse(
        id=inv["id"],
        product_id=product_id,
        artisan_id=user_id,
        sku=inv.get("sku"),
        barcode=inv.get("barcode"),
        available_stock=avail,
        reserved_stock=inv.get("reserved_stock", 0),
        sold_stock=inv.get("sold_stock", 0),
        minimum_stock=min_st,
        product_title=f"Artisan Product {inv.get('sku', '')}",
        status_badge=badge,
        created_at=inv.get("created_at") or datetime.now(timezone.utc),
        updated_at=inv.get("updated_at") or datetime.now(timezone.utc),
    )


@router.post("/products/{product_id}/stock", response_model=ProductInventoryResponse)
async def add_or_adjust_stock(
    product_id: str,
    adjustment: StockAdjustmentRequest,
    current_user: dict = Depends(get_current_user),
):
    user_id = _get_user_id(current_user)
    updated_inv = inventory_service.adjust_stock(
        product_id=product_id,
        artisan_id=user_id,
        quantity=adjustment.quantity,
        movement_type=adjustment.movement_type,
        notes=adjustment.notes,
    )
    return await get_product_inventory(product_id, current_user)


@router.get("/products/{product_id}/movements", response_model=List[StockMovementResponse])
async def get_product_movements(product_id: str, current_user: dict = Depends(get_current_user)):
    user_id = _get_user_id(current_user)
    client = get_supabase_client()
    try:
        res = client.table("stock_movements").select("*").eq("product_id", product_id).order("created_at", desc=True).execute()
        if res.data:
            return res.data
    except Exception:
        pass

    movements = [m for m in inventory_service._mock_movements if m.get("product_id") == product_id]
    return sorted(movements, key=lambda x: x.get("created_at", ""), reverse=True)


# Raw Materials Endpoints
@router.get("/raw-materials", response_model=List[RawMaterialResponse])
async def list_raw_materials(current_user: dict = Depends(get_current_user)):
    user_id = _get_user_id(current_user)
    client = get_supabase_client()
    try:
        res = client.table("raw_materials").select("*").eq("artisan_id", user_id).execute()
        if res.data:
            return [
                RawMaterialResponse(
                    **r,
                    is_low_stock=r.get("current_stock", 0) <= r.get("minimum_stock", 5)
                )
                for r in res.data
            ]
    except Exception:
        pass

    mats = [v for v in inventory_service._mock_raw_materials.values() if v.get("artisan_id") == user_id]
    return [
        RawMaterialResponse(
            **m,
            is_low_stock=m.get("current_stock", 0) <= m.get("minimum_stock", 5)
        )
        for m in mats
    ]


@router.post("/raw-materials", response_model=RawMaterialResponse)
async def create_raw_material(material_in: RawMaterialCreate, current_user: dict = Depends(get_current_user)):
    user_id = _get_user_id(current_user)
    mat_id = str(uuid.uuid4())
    now_iso = datetime.now(timezone.utc).isoformat()
    mat_dict = {
        "id": mat_id,
        "artisan_id": user_id,
        "name": material_in.name,
        "unit": material_in.unit,
        "current_stock": material_in.current_stock,
        "minimum_stock": material_in.minimum_stock,
        "cost_per_unit": material_in.cost_per_unit,
        "supplier_info": material_in.supplier_info,
        "created_at": now_iso,
        "updated_at": now_iso,
    }

    client = get_supabase_client()
    try:
        res = client.table("raw_materials").insert(mat_dict).execute()
        if res.data:
            mat_dict = res.data[0]
    except Exception:
        pass

    inventory_service._mock_raw_materials[mat_id] = mat_dict
    return RawMaterialResponse(
        **mat_dict,
        is_low_stock=mat_dict["current_stock"] <= mat_dict["minimum_stock"]
    )
