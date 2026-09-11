"""
Spatial Commerce & GIS Intelligence Core Engine (KalaCart V10)
Provides geo-spatial intelligence across the platform:
- Craft cluster auto-association for every artisan seller.
- GeoJSON craft density heatmaps & state/district analytics.
- Experiential craft tourism trails & heritage circuits.
- Haversine-based "Nearby Workshops" locator for travelers and buyers.
- Geospatial supply chain route mapping & delivery zone SLA optimization.
"""

import uuid
import math
import datetime
from typing import Dict, List, Optional, Any, Tuple
from pydantic import BaseModel, Field


def calculate_haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Computes the great-circle distance between two geographic coordinates in kilometers."""
    r = 6371.0  # Earth's radius in km
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(r * c, 2)


class SpatialCluster(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    cluster_code: str
    cluster_name: str
    state: str
    district: str
    latitude: float
    longitude: float
    radius_km: float = 15.0
    primary_craft: str
    gi_tag_associated: Optional[str] = None
    registered_artisans_count: int = 0
    annual_craft_output_inr: float = 0.0
    tourism_route_name: Optional[str] = None
    boundary_geojson: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "cluster_code": self.cluster_code,
            "cluster_name": self.cluster_name,
            "state": self.state,
            "district": self.district,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "radius_km": self.radius_km,
            "primary_craft": self.primary_craft,
            "gi_tag_associated": self.gi_tag_associated,
            "registered_artisans_count": self.registered_artisans_count,
            "annual_craft_output_inr": self.annual_craft_output_inr,
            "tourism_route_name": self.tourism_route_name,
            "boundary_geojson": self.boundary_geojson,
            "created_at": self.created_at,
        }


class TourismTrailRoute(BaseModel):
    trail_id: str
    trail_name: str
    state: str
    description: str
    duration_days: int
    waypoints: List[Dict[str, Any]]  # List of clusters / workshops with lat/lon
    suggested_season: str = "OCT_TO_MAR"


class DeliveryZone(BaseModel):
    zone_code: str
    zone_name: str
    state: str
    tier: str = "Tier-1"
    sla_hours: int = 48
    standard_shipping_rate_inr: float = 75.0
    express_available: bool = True
    covered_pincodes: List[str] = Field(default_factory=list)


class SpatialCommerceEngine:
    """
    Geographic Information System (GIS) engine for cluster mapping,
    artisan workshop discovery, and supply chain route optimization.
    """

    def __init__(self):
        self.clusters: Dict[str, SpatialCluster] = {}
        self.tourism_trails: Dict[str, TourismTrailRoute] = {}
        self.delivery_zones: Dict[str, DeliveryZone] = {}
        self.seller_cluster_index: Dict[str, str] = {}  # artisan_id -> cluster_id
        self._seed_default_spatial_data()

    def _seed_default_spatial_data(self):
        # 1. Geographic Craft Clusters across India
        c1 = SpatialCluster(
            cluster_code="CLUSTER-CHANNAPATNA-01",
            cluster_name="Channapatna Lacquer Toy Craft Cluster",
            state="Karnataka",
            district="Ramanagara",
            latitude=12.6518,
            longitude=77.2089,
            radius_km=15.0,
            primary_craft="Channapatna Wooden Toys & Dolls",
            gi_tag_associated="Channapatna Toys and Dolls (GI-19)",
            registered_artisans_count=1850,
            annual_craft_output_inr=32000000.0,
            tourism_route_name="Southern Silk & Lacquerway Heritage Trail",
        )
        c2 = SpatialCluster(
            cluster_code="CLUSTER-VARANASI-02",
            cluster_name="Varanasi Handloom Silk & Brocade Cluster",
            state="Uttar Pradesh",
            district="Varanasi",
            latitude=25.3176,
            longitude=82.9739,
            radius_km=20.0,
            primary_craft="Banaras Pure Zari Silk Weaving",
            gi_tag_associated="Banaras Brocades and Sarees (GI-99)",
            registered_artisans_count=14200,
            annual_craft_output_inr=240000000.0,
            tourism_route_name="Ganga Eternal Heritage Craft Circuit",
        )
        c3 = SpatialCluster(
            cluster_code="CLUSTER-BASTAR-03",
            cluster_name="Bastar Dokra Metal & Bell Craft Hub",
            state="Chhattisgarh",
            district="Bastar",
            latitude=19.0740,
            longitude=82.0125,
            radius_km=35.0,
            primary_craft="Bastar Dokra Bell Metal Casting",
            gi_tag_associated="Bastar Dhokra (GI-83)",
            registered_artisans_count=3200,
            annual_craft_output_inr=48000000.0,
            tourism_route_name="Tribal Heartlands & Forest Craft Trail",
        )
        c4 = SpatialCluster(
            cluster_code="CLUSTER-BIDAR-04",
            cluster_name="Bidar Royal Bidriware Metal Cluster",
            state="Karnataka",
            district="Bidar",
            latitude=17.9104,
            longitude=77.5199,
            radius_km=12.0,
            primary_craft="Bidriware Silver Inlay Metal Craft",
            gi_tag_associated="Bidriware (GI-17)",
            registered_artisans_count=980,
            annual_craft_output_inr=28000000.0,
            tourism_route_name="Deccan Sultanate Royal Craft Trail",
        )

        for cl in [c1, c2, c3, c4]:
            self.clusters[cl.id] = cl

        # 2. Tourism Trails
        self.tourism_trails["trail_southern_silk"] = TourismTrailRoute(
            trail_id="trail_southern_silk",
            trail_name="Southern Silk & Lacquerway Heritage Trail",
            state="Karnataka",
            description="Experience live ivory wood lathe turning in Channapatna followed by pure mulberry silk weaving in Ramanagara.",
            duration_days=2,
            suggested_season="OCT_TO_FEB",
            waypoints=[
                {"cluster_code": c1.cluster_code, "name": c1.cluster_name, "lat": c1.latitude, "lon": c1.longitude},
                {"cluster_code": c4.cluster_code, "name": c4.cluster_name, "lat": c4.latitude, "lon": c4.longitude},
            ],
        )
        self.tourism_trails["trail_ganga_crafts"] = TourismTrailRoute(
            trail_id="trail_ganga_crafts",
            trail_name="Ganga Eternal Heritage Craft Circuit",
            state="Uttar Pradesh",
            description="Explore centuries-old pit loom silk brocade weaving in Varanasi and handmade woolen carpet knotting in Bhadohi.",
            duration_days=3,
            suggested_season="NOV_TO_MAR",
            waypoints=[
                {"cluster_code": c2.cluster_code, "name": c2.cluster_name, "lat": c2.latitude, "lon": c2.longitude},
            ],
        )

        # 3. Delivery Zones
        self.delivery_zones["ZONE-BLR-METRO"] = DeliveryZone(
            zone_code="ZONE-BLR-METRO",
            zone_name="Bangalore Urban & Craft Corridors",
            state="Karnataka",
            tier="Tier-1",
            sla_hours=24,
            standard_shipping_rate_inr=60.0,
            express_available=True,
            covered_pincodes=["560001", "560002", "562160"],
        )
        self.delivery_zones["ZONE-NCR"] = DeliveryZone(
            zone_code="ZONE-NCR",
            zone_name="Delhi NCR & Western UP",
            state="Delhi/UP",
            tier="Tier-1",
            sla_hours=24,
            standard_shipping_rate_inr=60.0,
            express_available=True,
            covered_pincodes=["110001", "201301", "122001"],
        )

    def find_nearest_craft_cluster(self, latitude: float, longitude: float) -> Tuple[SpatialCluster, float]:
        """Finds the closest geographic craft cluster and calculates distance in km."""
        closest_cluster = None
        min_distance = float("inf")

        for cl in self.clusters.values():
            dist = calculate_haversine_distance_km(latitude, longitude, cl.latitude, cl.longitude)
            if dist < min_distance:
                min_distance = dist
                closest_cluster = cl

        return closest_cluster, min_distance

    def assign_seller_to_cluster(self, artisan_id: str, latitude: float, longitude: float) -> SpatialCluster:
        """
        Geographic clustering guarantee:
        Assigns every seller/artisan automatically to their designated geographic craft cluster.
        """
        closest_cluster, distance_km = self.find_nearest_craft_cluster(latitude, longitude)
        self.seller_cluster_index[artisan_id] = closest_cluster.id
        closest_cluster.registered_artisans_count += 1
        return closest_cluster

    def find_nearby_workshops(self, user_lat: float, user_lon: float, max_radius_km: float = 100.0) -> List[Dict[str, Any]]:
        """
        Traveler & Experiential Tourism Discovery:
        Finds open craft clusters, master artisan workshops, and live demonstration points within radius.
        """
        nearby = []
        for cl in self.clusters.values():
            dist = calculate_haversine_distance_km(user_lat, user_lon, cl.latitude, cl.longitude)
            if dist <= max_radius_km:
                nearby.append({
                    "cluster": cl.to_dict(),
                    "distance_km": dist,
                    "directions_url": f"https://maps.google.com/?q={cl.latitude},{cl.longitude}",
                })
        return sorted(nearby, key=lambda x: x["distance_km"])

    def get_district_density_geojson(self, state_filter: Optional[str] = None) -> Dict[str, Any]:
        """
        Generates standard GeoJSON FeatureCollection for interactive GIS layers,
        rendering artisan density heatmaps and GI cluster centroids.
        """
        features = []
        for cl in self.clusters.values():
            if state_filter and cl.state.lower() != state_filter.lower():
                continue

            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [cl.longitude, cl.latitude],  # GeoJSON format: [lon, lat]
                },
                "properties": {
                    "cluster_code": cl.cluster_code,
                    "cluster_name": cl.cluster_name,
                    "state": cl.state,
                    "district": cl.district,
                    "primary_craft": cl.primary_craft,
                    "gi_tag": cl.gi_tag_associated,
                    "artisans_count": cl.registered_artisans_count,
                    "density_weight": min(1.0, cl.registered_artisans_count / 10000.0),
                    "annual_output_inr": cl.annual_craft_output_inr,
                },
            }
            features.append(feature)

        return {
            "type": "FeatureCollection",
            "features": features,
            "total_clusters": len(features),
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }

    def optimize_supply_chain_dispatch(self, origin_lat: float, origin_lon: float, destination_pincode: str) -> Dict[str, Any]:
        """
        Geographic routing: Matches shipment with designated regional delivery zone polygons
        and calculates transit SLA and freight rates.
        """
        # Match zone by pincode or fallback to Tier-1 default
        matched_zone = None
        for z in self.delivery_zones.values():
            if destination_pincode in z.covered_pincodes:
                matched_zone = z
                break

        if not matched_zone:
            matched_zone = self.delivery_zones["ZONE-BLR-METRO"]

        closest_cluster, dist_from_hub = self.find_nearest_craft_cluster(origin_lat, origin_lon)

        return {
            "origin_cluster": closest_cluster.cluster_name,
            "origin_coordinates": [origin_lat, origin_lon],
            "destination_pincode": destination_pincode,
            "delivery_zone": matched_zone.zone_name,
            "estimated_sla_hours": matched_zone.sla_hours,
            "freight_charge_inr": matched_zone.standard_shipping_rate_inr,
            "express_eligible": matched_zone.express_available,
            "optimized_corridor": f"{closest_cluster.district} Hub -> Regional Transit Hub -> Pincode {destination_pincode}",
        }


# Global Singleton Instance
spatial_commerce_engine = SpatialCommerceEngine()
