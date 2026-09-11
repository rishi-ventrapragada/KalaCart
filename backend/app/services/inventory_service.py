import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from app.database.connection import get_supabase_client
from app.models.inventory import (
    StockMovementType,
    InventoryDashboardMetrics,
    InventoryAnalyticsResponse,
    MonthlyStockMovement,
    ProductMovementStat,
)

# In-memory mock store fallback for standalone/local tests
_mock_inventory: Dict[str, dict] = {}       # keyed by product_id
_mock_movements: List[dict] = []
_mock_raw_materials: Dict[str, dict] = {}   # keyed by material_id


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_or_create_inventory(product_id: str, artisan_id: str, initial_stock: int = 10, sku: Optional[str] = None) -> dict:
    client = get_supabase_client()
    try:
        res = client.table("product_inventory").select("*").eq("product_id", product_id).limit(1).execute()
        if res.data:
            return res.data[0]
    except Exception:
        pass

    if product_id in _mock_inventory:
        return _mock_inventory[product_id]

    # Create new inventory record
    inv_id = str(uuid.uuid4())
    generated_sku = sku or f"SKU-{product_id[:8].upper()}"
    inv_record = {
        "id": inv_id,
        "product_id": product_id,
        "artisan_id": artisan_id,
        "sku": generated_sku,
        "barcode": f"890{inv_id.replace('-', '')[:10]}",
        "available_stock": initial_stock,
        "reserved_stock": 0,
        "sold_stock": 0,
        "minimum_stock": 5,
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
    }

    try:
        res = client.table("product_inventory").insert(inv_record).execute()
        if res.data:
            inv_record = res.data[0]
    except Exception:
        pass

    _mock_inventory[product_id] = inv_record
    return inv_record


def adjust_stock(
    product_id: str,
    artisan_id: str,
    quantity: int,
    movement_type: StockMovementType,
    reference_id: Optional[str] = None,
    notes: Optional[str] = None,
) -> dict:
    inv = get_or_create_inventory(product_id, artisan_id)
    prev_stock = inv["available_stock"]
    new_stock = max(0, prev_stock + quantity)
    inv["available_stock"] = new_stock
    inv["updated_at"] = _now_iso()

    movement = {
        "id": str(uuid.uuid4()),
        "inventory_id": inv["id"],
        "product_id": product_id,
        "artisan_id": artisan_id,
        "movement_type": movement_type.value,
        "quantity": quantity,
        "previous_stock": prev_stock,
        "new_stock": new_stock,
        "reference_id": reference_id,
        "notes": notes or f"Stock {movement_type.value} adjustment",
        "created_at": _now_iso(),
    }

    client = get_supabase_client()
    try:
        client.table("product_inventory").update(inv).eq("id", inv["id"]).execute()
        client.table("stock_movements").insert(movement).execute()
    except Exception:
        pass

    _mock_inventory[product_id] = inv
    _mock_movements.append(movement)
    return inv


def reserve_stock(product_id: str, artisan_id: str, quantity: int, order_id: str) -> bool:
    inv = get_or_create_inventory(product_id, artisan_id)
    if inv["available_stock"] < quantity:
        # Allow partial/soft reservation or auto-adjust for artisan demo
        pass
    actual_reserve = min(inv["available_stock"], quantity)
    prev_avail = inv["available_stock"]
    inv["available_stock"] = max(0, prev_avail - actual_reserve)
    inv["reserved_stock"] = inv.get("reserved_stock", 0) + actual_reserve
    inv["updated_at"] = _now_iso()

    movement = {
        "id": str(uuid.uuid4()),
        "inventory_id": inv["id"],
        "product_id": product_id,
        "artisan_id": artisan_id,
        "movement_type": StockMovementType.reservation.value,
        "quantity": -actual_reserve,
        "previous_stock": prev_avail,
        "new_stock": inv["available_stock"],
        "reference_id": order_id,
        "notes": f"Stock reserved for Order {order_id}",
        "created_at": _now_iso(),
    }

    client = get_supabase_client()
    try:
        client.table("product_inventory").update(inv).eq("id", inv["id"]).execute()
        client.table("stock_movements").insert(movement).execute()
    except Exception:
        pass

    _mock_inventory[product_id] = inv
    _mock_movements.append(movement)
    return True


def release_reserved_stock(product_id: str, artisan_id: str, quantity: int, order_id: str) -> bool:
    inv = get_or_create_inventory(product_id, artisan_id)
    actual_release = min(inv.get("reserved_stock", 0), quantity)
    prev_avail = inv["available_stock"]
    inv["available_stock"] = prev_avail + actual_release
    inv["reserved_stock"] = max(0, inv.get("reserved_stock", 0) - actual_release)
    inv["updated_at"] = _now_iso()

    movement = {
        "id": str(uuid.uuid4()),
        "inventory_id": inv["id"],
        "product_id": product_id,
        "artisan_id": artisan_id,
        "movement_type": StockMovementType.release.value,
        "quantity": actual_release,
        "previous_stock": prev_avail,
        "new_stock": inv["available_stock"],
        "reference_id": order_id,
        "notes": f"Stock released from Cancelled Order {order_id}",
        "created_at": _now_iso(),
    }

    client = get_supabase_client()
    try:
        client.table("product_inventory").update(inv).eq("id", inv["id"]).execute()
        client.table("stock_movements").insert(movement).execute()
    except Exception:
        pass

    _mock_inventory[product_id] = inv
    _mock_movements.append(movement)
    return True


def commit_reserved_sale(product_id: str, artisan_id: str, quantity: int, order_id: str) -> bool:
    inv = get_or_create_inventory(product_id, artisan_id)
    actual_sale = min(inv.get("reserved_stock", 0), quantity)
    if actual_sale == 0:
        actual_sale = quantity
    inv["reserved_stock"] = max(0, inv.get("reserved_stock", 0) - actual_sale)
    inv["sold_stock"] = inv.get("sold_stock", 0) + actual_sale
    inv["updated_at"] = _now_iso()

    movement = {
        "id": str(uuid.uuid4()),
        "inventory_id": inv["id"],
        "product_id": product_id,
        "artisan_id": artisan_id,
        "movement_type": StockMovementType.sale.value,
        "quantity": actual_sale,
        "previous_stock": inv["available_stock"],
        "new_stock": inv["available_stock"],
        "reference_id": order_id,
        "notes": f"Sale completed for Order {order_id}",
        "created_at": _now_iso(),
    }

    client = get_supabase_client()
    try:
        client.table("product_inventory").update(inv).eq("id", inv["id"]).execute()
        client.table("stock_movements").insert(movement).execute()
    except Exception:
        pass

    _mock_inventory[product_id] = inv
    _mock_movements.append(movement)
    return True


def get_dashboard_metrics(artisan_id: str) -> InventoryDashboardMetrics:
    client = get_supabase_client()
    inv_list: List[dict] = []
    try:
        res = client.table("product_inventory").select("*").eq("artisan_id", artisan_id).execute()
        if res.data:
            inv_list = res.data
    except Exception:
        pass

    if not inv_list:
        inv_list = [v for v in _mock_inventory.values() if v.get("artisan_id") == artisan_id]

    total_products = len(inv_list)
    items_in_stock = sum(item.get("available_stock", 0) for item in inv_list)
    low_stock_count = sum(
        1 for item in inv_list
        if 0 < item.get("available_stock", 0) <= item.get("minimum_stock", 5)
    )
    out_of_stock_count = sum(
        1 for item in inv_list
        if item.get("available_stock", 0) == 0
    )
    total_reserved = sum(item.get("reserved_stock", 0) for item in inv_list)
    total_sold = sum(item.get("sold_stock", 0) for item in inv_list)

    return InventoryDashboardMetrics(
        total_products=total_products,
        items_in_stock=items_in_stock,
        low_stock_count=low_stock_count,
        out_of_stock_count=out_of_stock_count,
        total_reserved_stock=total_reserved,
        total_sold_stock=total_sold,
    )


def get_inventory_analytics(artisan_id: str) -> InventoryAnalyticsResponse:
    client = get_supabase_client()
    inv_list: List[dict] = []
    movements: List[dict] = []
    try:
        inv_res = client.table("product_inventory").select("*").eq("artisan_id", artisan_id).execute()
        if inv_res.data:
            inv_list = inv_res.data
        mov_res = client.table("stock_movements").select("*").eq("artisan_id", artisan_id).execute()
        if mov_res.data:
            movements = mov_res.data
    except Exception:
        pass

    if not inv_list:
        inv_list = [v for v in _mock_inventory.values() if v.get("artisan_id") == artisan_id]
    if not movements:
        movements = [m for m in _mock_movements if m.get("artisan_id") == artisan_id]

    # Group movements by month
    month_names = ["May", "Jun", "Jul", "Aug", "Sep", "Oct"]
    monthly_map = {m: {"inflow": 0, "outflow": 0} for m in month_names}

    for mov in movements:
        created_str = mov.get("created_at")
        if created_str:
            try:
                dt = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
                m_label = dt.strftime("%b")
                if m_label in monthly_map:
                    qty = mov.get("quantity", 0)
                    if qty > 0:
                        monthly_map[m_label]["inflow"] += qty
                    else:
                        monthly_map[m_label]["outflow"] += abs(qty)
            except Exception:
                pass

    monthly_stats = [
        MonthlyStockMovement(
            month=m,
            inflow=monthly_map[m]["inflow"],
            outflow=monthly_map[m]["outflow"],
        )
        for m in month_names
    ]

    fast_moving = []
    dead_inventory = []

    for item in sorted(inv_list, key=lambda x: x.get("sold_stock", 0), reverse=True):
        stat = ProductMovementStat(
            product_id=item["product_id"],
            title=f"Artisan Craft {item.get('sku', '')}",
            total_sold=item.get("sold_stock", 0),
            available_stock=item.get("available_stock", 0),
        )
        if item.get("sold_stock", 0) > 0:
            fast_moving.append(stat)
        elif item.get("available_stock", 0) > 0:
            dead_inventory.append(stat)

    return InventoryAnalyticsResponse(
        monthly_stock_movements=monthly_stats,
        fast_moving_products=fast_moving[:5],
        dead_inventory=dead_inventory[:5],
    )
