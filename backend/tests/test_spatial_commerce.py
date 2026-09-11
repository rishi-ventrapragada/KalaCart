"""
Test Suite for Spatial Commerce & GIS Intelligence (KalaCart V10)
Verifies:
- Retrieval of geographic craft clusters (Channapatna, Varanasi, Bastar, Bidar)
- Automatic assignment of every seller to a craft cluster
- GeoJSON craft density heatmap feature collections
- Nearby workshop discovery using Haversine distance
- Experiential craft tourism trails & delivery route optimization
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_get_craft_clusters():
    response = client.get("/api/v1/spatial/clusters")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] >= 4
    cluster_names = [c["cluster_name"] for c in data["clusters"]]
    assert any("Channapatna" in name for name in cluster_names)
    assert any("Varanasi" in name for name in cluster_names)
    assert any("Bastar" in name for name in cluster_names)


def test_get_craft_density_geojson():
    response = client.get("/api/v1/spatial/geojson/density")
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "FeatureCollection"
    assert data["total_clusters"] >= 4
    for feature in data["features"]:
        assert feature["geometry"]["type"] == "Point"
        assert len(feature["geometry"]["coordinates"]) == 2  # [lon, lat]
        assert "artisans_count" in feature["properties"]


def test_find_nearby_workshops():
    # User coordinates near Bangalore/Channapatna (12.9716° N, 77.5946° E)
    response = client.get("/api/v1/spatial/workshops/nearby?latitude=12.9716&longitude=77.5946&radius_km=100")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] >= 1
    closest = data["nearby_workshops"][0]
    assert "Channapatna" in closest["cluster"]["cluster_name"]
    assert closest["distance_km"] < 65.0  # Approx 50km from Bangalore


def test_assign_seller_to_geographic_cluster():
    # Seller located in rural Varanasi (25.32° N, 82.98° E)
    payload = {
        "artisan_id": "art-banaras-weaver-99",
        "latitude": 25.3200,
        "longitude": 82.9800,
    }
    response = client.post("/api/v1/spatial/sellers/assign-cluster", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "Varanasi" in data["assigned_cluster"]["cluster_name"]


def test_optimize_dispatch_route():
    payload = {
        "origin_latitude": 12.6518,  # Channapatna
        "origin_longitude": 77.2089,
        "destination_pincode": "560001",  # Bangalore central
    }
    response = client.post("/api/v1/spatial/dispatch/optimize", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    plan = data["dispatch_plan"]
    assert "Channapatna" in plan["origin_cluster"]
    assert plan["estimated_sla_hours"] <= 48
