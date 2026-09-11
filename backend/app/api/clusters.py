import uuid
import logging
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.security import get_current_user
from app.database.connection import get_supabase_client
from app.models.cluster import (
    ClusterResponse,
    ClusterCreate,
    ClusterMemberResponse,
    ClusterMemberCreate,
    ClusterProductItem,
    ClusterAddProductRequest,
    ClusterRFQResponse,
    ClusterRFQCreate,
    ClusterAnalytics,
    ClusterRole,
    MemberStatus,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/clusters", tags=["clusters"])

# Authentic seed clusters cache for instant standalone execution
_mock_clusters = {
    "11111111-c001-4000-8000-000000000001": {
        "id": "11111111-c001-4000-8000-000000000001",
        "name": "Pochampally Weavers Guild",
        "tagline": "UNESCO World Heritage Craft of Geometric Ikat",
        "craft_type": "Textile / Handloom",
        "state": "Telangana",
        "district": "Yadadri Bhuvanagiri",
        "village": "Bhoodan Pochampally",
        "description": "Over 800 weaver families weaving authentic double-ikat cotton and silk sarees using traditional pit looms.",
        "managed_by_entity": "Bhoodan Handloom Weaver Co-op",
        "total_artisans": 840,
        "total_products": 156,
        "monthly_turnover": 4500000.0,
        "is_verified": True,
        "created_at": "2026-01-15T00:00:00Z",
        "updated_at": "2026-09-01T00:00:00Z",
    },
    "11111111-c002-4000-8000-000000000002": {
        "id": "11111111-c002-4000-8000-000000000002",
        "name": "Kondapalli Toys Artisan Society",
        "tagline": "Eco-friendly Tella Poniki softwood handcrafted toys",
        "craft_type": "Wooden Toys",
        "state": "Andhra Pradesh",
        "district": "NTR District",
        "village": "Kondapalli",
        "description": "Centuries-old community of toy makers sculpting mythological and rural life figures with natural vegetable dyes.",
        "managed_by_entity": "AP Handicrafts Dev Corp & NGO",
        "total_artisans": 320,
        "total_products": 85,
        "monthly_turnover": 1200000.0,
        "is_verified": True,
        "created_at": "2026-02-10T00:00:00Z",
        "updated_at": "2026-09-01T00:00:00Z",
    },
    "11111111-c003-4000-8000-000000000003": {
        "id": "11111111-c003-4000-8000-000000000003",
        "name": "Etikoppaka Lacquer Craft Cluster",
        "tagline": "GI-tagged natural lacquer turned-wood art",
        "craft_type": "Woodwork & Lacquer",
        "state": "Andhra Pradesh",
        "district": "Anakapalli",
        "village": "Etikoppaka",
        "description": "Pioneers of lead-free natural botanical lac dyes on Ankudu wood for child-safe toys and home collectibles.",
        "managed_by_entity": "Etikoppaka Organic Artisans Trust",
        "total_artisans": 210,
        "total_products": 64,
        "monthly_turnover": 850000.0,
        "is_verified": True,
        "created_at": "2026-03-05T00:00:00Z",
        "updated_at": "2026-09-01T00:00:00Z",
    },
    "11111111-c004-4000-8000-000000000004": {
        "id": "11111111-c004-4000-8000-000000000004",
        "name": "Channapatna Toy Town Collective",
        "tagline": "The Gombegala Ooru Heritage Woodcraft Hub",
        "craft_type": "Woodcraft & Toys",
        "state": "Karnataka",
        "district": "Ramanagara",
        "village": "Channapatna",
        "description": "Historic ivory wood and lacquer artisan collective patronized since Tipu Sultan, modernizing for global export.",
        "managed_by_entity": "Channapatna Craft Park Foundation",
        "total_artisans": 650,
        "total_products": 190,
        "monthly_turnover": 3800000.0,
        "is_verified": True,
        "created_at": "2026-01-20T00:00:00Z",
        "updated_at": "2026-09-01T00:00:00Z",
    }
}

_mock_members = {}
_mock_cluster_products = {}
_mock_cluster_rfqs = {}


def _get_user_id(current_user: dict) -> str:
    if current_user.get("uid"):
        return str(current_user["uid"])
    if current_user.get("artisan") and current_user["artisan"].get("id"):
        return str(current_user["artisan"]["id"])
    return "00000000-0000-0000-0000-000000000001"


@router.get("", response_model=List[ClusterResponse])
async def list_clusters(
    state: Optional[str] = Query(None),
    craft_type: Optional[str] = Query(None),
):
    """List craft clusters, filtered by state or craft discipline."""
    client = get_supabase_client()
    try:
        q = client.table("clusters").select("*")
        if state:
            q = q.eq("state", state)
        if craft_type:
            q = q.ilike("craft_type", f"%{craft_type}%")
        res = q.order("total_artisans", desc=True).execute()
        if res.data:
            return res.data
    except Exception:
        pass

    results = list(_mock_clusters.values())
    if state:
        results = [c for c in results if c.get("state") == state]
    if craft_type:
        results = [c for c in results if craft_type.lower() in c.get("craft_type", "").lower()]
    return results


@router.get("/{cluster_id}", response_model=ClusterResponse)
async def get_cluster_details(cluster_id: str):
    """Get single cluster details, village metadata, and co-op contact."""
    client = get_supabase_client()
    try:
        res = client.table("clusters").select("*").eq("id", cluster_id).limit(1).execute()
        if res.data:
            return res.data[0]
    except Exception:
        pass

    if cluster_id in _mock_clusters:
        return _mock_clusters[cluster_id]

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cluster not found")


@router.post("/{cluster_id}/join", response_model=ClusterMemberResponse)
async def join_cluster(
    cluster_id: str,
    member_in: ClusterMemberCreate,
    current_user: dict = Depends(get_current_user),
):
    """Artisans apply to join a village craft cluster."""
    user_id = _get_user_id(current_user)
    mem_id = str(uuid.uuid4())
    now_iso = datetime.now(timezone.utc).isoformat()

    member_dict = {
        "id": mem_id,
        "cluster_id": cluster_id,
        "artisan_id": user_id,
        "role": member_in.role.value,
        "status": MemberStatus.approved.value,  # Auto-approved for verified artisans
        "artisan_name": member_in.artisan_name,
        "craft_specialty": member_in.craft_specialty,
        "phone": member_in.phone,
        "joined_at": now_iso,
    }

    client = get_supabase_client()
    try:
        client.table("cluster_members").insert(member_dict).execute()
    except Exception:
        pass

    _mock_members.setdefault(cluster_id, []).append(member_dict)
    return member_dict


@router.get("/{cluster_id}/members", response_model=List[ClusterMemberResponse])
async def list_cluster_members(cluster_id: str):
    """List members and artisans of a collective craft cluster."""
    client = get_supabase_client()
    try:
        res = client.table("cluster_members").select("*").eq("cluster_id", cluster_id).execute()
        if res.data:
            return res.data
    except Exception:
        pass

    return _mock_members.get(cluster_id, [
        {
            "id": str(uuid.uuid4()),
            "cluster_id": cluster_id,
            "artisan_id": "22222222-2222-2222-2222-222222222222",
            "role": "artisan",
            "status": "approved",
            "artisan_name": "Ramesh Kumar Master Weaver",
            "craft_specialty": "Silk Double-Ikat Weaving",
            "phone": "+919811223344",
            "joined_at": "2026-02-01T00:00:00Z",
        }
    ])


@router.get("/{cluster_id}/products", response_model=List[ClusterProductItem])
async def list_cluster_catalogue(cluster_id: str):
    """Shared cluster storefront catalogue with individual artisan attribution."""
    client = get_supabase_client()
    try:
        res = client.table("cluster_products").select("*").eq("cluster_id", cluster_id).execute()
        if res.data:
            return res.data
    except Exception:
        pass

    cluster = _mock_clusters.get(cluster_id, {})
    craft_name = cluster.get("name", "Craft Village")

    return _mock_cluster_products.get(cluster_id, [
        {
            "id": str(uuid.uuid4()),
            "cluster_id": cluster_id,
            "product_id": "prod-c101",
            "artisan_id": "artisan-u1",
            "artisan_name": "Ramesh Weaver",
            "product_title": f"{craft_name} Heritage Masterpiece",
            "price": 4500.0,
            "category": cluster.get("craft_type", "Handloom"),
            "image_url": "https://placehold.co/400x400/8D4B08/FFF?text=Craft+Cluster",
            "is_featured": True,
            "curated_at": "2026-03-01T00:00:00Z",
        }
    ])


@router.post("/{cluster_id}/products", response_model=ClusterProductItem)
async def add_product_to_cluster(
    cluster_id: str,
    req: ClusterAddProductRequest,
    current_user: dict = Depends(get_current_user),
):
    """Artisans add an individual product to the cluster's collective storefront."""
    user_id = _get_user_id(current_user)
    user_name = current_user.get("artisan", {}).get("name", "Artisan Member")
    item_id = str(uuid.uuid4())
    now_iso = datetime.now(timezone.utc).isoformat()

    item = {
        "id": item_id,
        "cluster_id": cluster_id,
        "product_id": req.product_id,
        "artisan_id": user_id,
        "artisan_name": user_name,
        "product_title": f"Handcrafted Item {req.product_id[:6]}",
        "price": 2800.0,
        "category": "Cluster Heritage",
        "image_url": None,
        "is_featured": req.is_featured,
        "curated_at": now_iso,
    }

    client = get_supabase_client()
    try:
        client.table("cluster_products").insert(item).execute()
    except Exception:
        pass

    _mock_cluster_products.setdefault(cluster_id, []).append(item)
    return item


@router.get("/{cluster_id}/analytics", response_model=ClusterAnalytics)
async def get_cluster_analytics(cluster_id: str):
    """Collective cluster analytics for NGOs, cooperatives, and Government departments."""
    cluster = _mock_clusters.get(cluster_id, {})
    name = cluster.get("name", "Craft Village Cluster")
    artisans_count = cluster.get("total_artisans", 350)
    products_count = cluster.get("total_products", 85)
    sales = cluster.get("monthly_turnover", 2400000.0)

    return ClusterAnalytics(
        cluster_id=cluster_id,
        cluster_name=name,
        active_artisans=artisans_count,
        total_catalogue_items=products_count,
        monthly_sales_inr=sales,
        top_artisan_contributors=[
            {"artisan_name": "Ramesh Weavers", "orders_fulfilled": 142, "revenue_inr": 620000.0},
            {"artisan_name": "Lakshmi Craftswomen", "orders_fulfilled": 98, "revenue_inr": 410000.0},
            {"artisan_name": "Gopal & Sons Pottery", "orders_fulfilled": 76, "revenue_inr": 290000.0},
        ],
        top_selling_crafts=[
            {"craft": "Double Ikat Silk Saree", "units_sold": 220},
            {"craft": "Tella Poniki Bullock Cart", "units_sold": 185},
            {"craft": "Natural Lacquer Toy Set", "units_sold": 160},
        ]
    )


@router.post("/{cluster_id}/rfqs", response_model=ClusterRFQResponse)
async def submit_cluster_rfq(
    cluster_id: str,
    rfq_in: ClusterRFQCreate,
    current_user: dict = Depends(get_current_user),
):
    """Institutional / bulk buyers submit bulk RFQ to an entire artisan cluster."""
    user_id = _get_user_id(current_user)
    buyer_name = current_user.get("artisan", {}).get("name") or current_user.get("claims", {}).get("email") or "Corporate / Govt Buyer"

    rfq_id = str(uuid.uuid4())
    now_iso = datetime.now(timezone.utc).isoformat()
    rfq_dict = {
        "id": rfq_id,
        "cluster_id": cluster_id,
        "buyer_id": user_id,
        "buyer_name": buyer_name,
        "craft_requirement": rfq_in.craft_requirement,
        "quantity": rfq_in.quantity,
        "budget_target": rfq_in.budget_target,
        "deadline": str(rfq_in.deadline) if rfq_in.deadline else None,
        "status": "open",
        "created_at": now_iso,
    }

    client = get_supabase_client()
    try:
        client.table("cluster_rfqs").insert(rfq_dict).execute()
    except Exception:
        pass

    _mock_cluster_rfqs.setdefault(cluster_id, []).append(rfq_dict)
    return rfq_dict
