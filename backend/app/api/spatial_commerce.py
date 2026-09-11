"""
Spatial Commerce & GIS API Router (KalaCart V10)
Exposes craft clusters, GeoJSON density heatmaps, craft tourism trails,
nearby workshop locators, and GIS delivery zone optimization.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

from app.core.spatial_commerce import (
    spatial_commerce_engine,
    SpatialCluster,
    TourismTrailRoute,
    DeliveryZone,
)

router = APIRouter(prefix="/api/v1/spatial", tags=["Spatial Commerce & GIS Intelligence (V10)"])


class AssignSellerClusterRequest(BaseModel):
    artisan_id: str
    latitude: float
    longitude: float


class OptimizeDispatchRequest(BaseModel):
    origin_latitude: float
    origin_longitude: float
    destination_pincode: str


@router.get("/clusters")
async def get_craft_clusters(
    state: Optional[str] = Query(None, description="Filter by state e.g. Karnataka, Uttar Pradesh"),
    craft: Optional[str] = Query(None, description="Filter by craft form e.g. Silk, Toys, Metal"),
):
    """Retrieve geographic craft clusters with artisan counts and GI details."""
    clusters = list(spatial_commerce_engine.clusters.values())
    if state:
        clusters = [c for c in clusters if c.state.lower() == state.lower()]
    if craft:
        clusters = [c for c in clusters if craft.lower() in c.primary_craft.lower()]

    return {
        "count": len(clusters),
        "clusters": [c.to_dict() for c in clusters],
    }


@router.get("/geojson/density")
async def get_craft_density_geojson(
    state: Optional[str] = Query(None, description="Filter by state")
):
    """Get standard GeoJSON FeatureCollection for interactive map rendering."""
    return spatial_commerce_engine.get_district_density_geojson(state_filter=state)


@router.get("/workshops/nearby")
async def find_nearby_workshops(
    latitude: float = Query(..., description="User GPS Latitude"),
    longitude: float = Query(..., description="User GPS Longitude"),
    radius_km: float = Query(100.0, description="Search radius in kilometers"),
):
    """Discover nearby artisan workshops and craft clusters within radius."""
    nearby = spatial_commerce_engine.find_nearby_workshops(
        user_lat=latitude,
        user_lon=longitude,
        max_radius_km=radius_km,
    )
    return {
        "user_coordinates": [latitude, longitude],
        "radius_km": radius_km,
        "count": len(nearby),
        "nearby_workshops": nearby,
    }


@router.get("/tourism-trails")
async def get_craft_tourism_trails():
    """Retrieve experiential craft tourism trails, routes, and waypoints."""
    trails = [t.model_dump() for t in spatial_commerce_engine.tourism_trails.values()]
    return {
        "count": len(trails),
        "tourism_trails": trails,
    }


@router.post("/sellers/assign-cluster")
async def assign_seller_to_cluster(req: AssignSellerClusterRequest):
    """Assign an artisan seller to their closest geographic craft cluster."""
    cluster = spatial_commerce_engine.assign_seller_to_cluster(
        artisan_id=req.artisan_id,
        latitude=req.latitude,
        longitude=req.longitude,
    )
    return {
        "status": "success",
        "artisan_id": req.artisan_id,
        "assigned_cluster": cluster.to_dict(),
    }


@router.post("/dispatch/optimize")
async def optimize_dispatch_route(req: OptimizeDispatchRequest):
    """Calculate geographic supply chain corridor, delivery zone SLA, and freight rate."""
    result = spatial_commerce_engine.optimize_supply_chain_dispatch(
        origin_lat=req.origin_latitude,
        origin_lon=req.origin_longitude,
        destination_pincode=req.destination_pincode,
    )
    return {
        "status": "success",
        "dispatch_plan": result,
    }
