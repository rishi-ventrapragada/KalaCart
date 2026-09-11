"""
Abstract Courier Provider Interface & Implementations for KalaCart Phase 3.
Supports: Shiprocket, Delhivery, India Post, and DTDC.
"""

import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Dict, List, Optional
from pydantic import BaseModel


class CourierAWBResult(BaseModel):
    provider_key: str
    courier_name: str
    awb_code: str
    routing_code: str
    pickup_token: str
    label_download_url: Optional[str] = None


class CourierTrackingResult(BaseModel):
    awb_code: str
    provider_key: str
    current_status: str
    origin: str
    destination: str
    estimated_delivery_date: str
    lat: float
    lng: float
    events: List[Dict[str, str]]


class BaseCourierProvider(ABC):
    provider_key: str
    display_name: str

    @abstractmethod
    def generate_awb(self, shipment_data: dict, order_data: dict) -> CourierAWBResult:
        """Generates consignment AWB code and booking."""
        pass

    @abstractmethod
    def schedule_pickup(self, pickup_data: dict) -> dict:
        """Schedules courier doorstep pickup."""
        pass

    @abstractmethod
    def track_consignment(self, awb_code: str) -> CourierTrackingResult:
        """Fetches live tracking status and coordinates."""
        pass


class ShiprocketProvider(BaseCourierProvider):
    provider_key = "SHIPROCKET"
    display_name = "Shiprocket Express Multi-Courier"

    def generate_awb(self, shipment_data: dict, order_data: dict) -> CourierAWBResult:
        awb = f"SR{uuid.uuid4().hex[:10].upper()}"
        return CourierAWBResult(
            provider_key=self.provider_key,
            courier_name=self.display_name,
            awb_code=awb,
            routing_code="SR-DEL-NORTH",
            pickup_token=f"PKP-SR-{uuid.uuid4().hex[:6].upper()}",
            label_download_url=f"/api/v1/shipping/shipments/{shipment_data.get('id', 'mock')}/label",
        )

    def schedule_pickup(self, pickup_data: dict) -> dict:
        return {
            "pickup_id": f"SR-PKP-{uuid.uuid4().hex[:8].upper()}",
            "status": "SCHEDULED",
            "provider": self.provider_key,
            "pickup_date": pickup_data.get("pickup_date", "Tomorrow"),
            "slot": pickup_data.get("slot", "10:00 - 13:00"),
        }

    def track_consignment(self, awb_code: str) -> CourierTrackingResult:
        return CourierTrackingResult(
            awb_code=awb_code,
            provider_key=self.provider_key,
            current_status="IN_TRANSIT",
            origin="Jaipur Hub",
            destination="Bangalore Central",
            estimated_delivery_date="3 Days",
            lat=26.9124,
            lng=75.7873,
            events=[
                {"status": "CONFIRMED", "location": "Jaipur Hub", "activity": "Consignment registered with Shiprocket", "time": datetime.now(timezone.utc).isoformat()},
                {"status": "IN_TRANSIT", "location": "Gurgaon Air Sort Hub", "activity": "In transit to destination city", "time": datetime.now(timezone.utc).isoformat()},
            ],
        )


class DelhiveryProvider(BaseCourierProvider):
    provider_key = "DELHIVERY"
    display_name = "Delhivery Surface & Express"

    def generate_awb(self, shipment_data: dict, order_data: dict) -> CourierAWBResult:
        awb = f"DLV{uuid.uuid4().hex[:10].upper()}"
        return CourierAWBResult(
            provider_key=self.provider_key,
            courier_name=self.display_name,
            awb_code=awb,
            routing_code="DLV-HUB-01",
            pickup_token=f"PKP-DLV-{uuid.uuid4().hex[:6].upper()}",
            label_download_url=f"/api/v1/shipping/shipments/{shipment_data.get('id', 'mock')}/label",
        )

    def schedule_pickup(self, pickup_data: dict) -> dict:
        return {
            "pickup_id": f"DLV-PKP-{uuid.uuid4().hex[:8].upper()}",
            "status": "SCHEDULED",
            "provider": self.provider_key,
            "pickup_date": pickup_data.get("pickup_date", "Tomorrow"),
            "slot": pickup_data.get("slot", "14:00 - 18:00"),
        }

    def track_consignment(self, awb_code: str) -> CourierTrackingResult:
        return CourierTrackingResult(
            awb_code=awb_code,
            provider_key=self.provider_key,
            current_status="OUT_FOR_DELIVERY",
            origin="Jaipur Craft Cluster",
            destination="Bangalore Koramangala",
            estimated_delivery_date="Today by 6 PM",
            lat=12.9716,
            lng=77.5946,
            events=[
                {"status": "PICKED_UP", "location": "Jaipur Cluster Hub", "activity": "Picked up from artisan studio", "time": datetime.now(timezone.utc).isoformat()},
                {"status": "OUT_FOR_DELIVERY", "location": "Bangalore Koramangala", "activity": "Rider out with package", "time": datetime.now(timezone.utc).isoformat()},
            ],
        )


class IndiaPostProvider(BaseCourierProvider):
    provider_key = "INDIA_POST"
    display_name = "India Post Speed Post & Parcel"

    def generate_awb(self, shipment_data: dict, order_data: dict) -> CourierAWBResult:
        awb = f"INP-KC-{uuid.uuid4().hex[:8].upper()}"
        return CourierAWBResult(
            provider_key=self.provider_key,
            courier_name=self.display_name,
            awb_code=awb,
            routing_code="INP-RMS-NORTH",
            pickup_token=f"PKP-INP-{uuid.uuid4().hex[:6].upper()}",
            label_download_url=f"/api/v1/shipping/shipments/{shipment_data.get('id', 'mock')}/label",
        )

    def schedule_pickup(self, pickup_data: dict) -> dict:
        return {
            "pickup_id": f"INP-PKP-{uuid.uuid4().hex[:8].upper()}",
            "status": "SCHEDULED",
            "provider": self.provider_key,
            "pickup_date": pickup_data.get("pickup_date", "Tomorrow"),
            "slot": pickup_data.get("slot", "11:00 - 14:00"),
        }

    def track_consignment(self, awb_code: str) -> CourierTrackingResult:
        return CourierTrackingResult(
            awb_code=awb_code,
            provider_key=self.provider_key,
            current_status="IN_TRANSIT",
            origin="Sanganer Post Office (302001)",
            destination="Indiranagar Post Office (560001)",
            estimated_delivery_date="4 Days",
            lat=26.9124,
            lng=75.7873,
            events=[
                {"status": "CONFIRMED", "location": "Sanganer Sub Post Office", "activity": "Consignment booked", "time": datetime.now(timezone.utc).isoformat()},
                {"status": "IN_TRANSIT", "location": "Jaipur RMS Hub", "activity": "Sorted at postal hub", "time": datetime.now(timezone.utc).isoformat()},
            ],
        )


class DTDCProvider(BaseCourierProvider):
    provider_key = "DTDC"
    display_name = "DTDC Prime Craft Express"

    def generate_awb(self, shipment_data: dict, order_data: dict) -> CourierAWBResult:
        awb = f"DTDC{uuid.uuid4().hex[:10].upper()}"
        return CourierAWBResult(
            provider_key=self.provider_key,
            courier_name=self.display_name,
            awb_code=awb,
            routing_code="DTDC-Z1-EXP",
            pickup_token=f"PKP-DTDC-{uuid.uuid4().hex[:6].upper()}",
            label_download_url=f"/api/v1/shipping/shipments/{shipment_data.get('id', 'mock')}/label",
        )

    def schedule_pickup(self, pickup_data: dict) -> dict:
        return {
            "pickup_id": f"DTDC-PKP-{uuid.uuid4().hex[:8].upper()}",
            "status": "SCHEDULED",
            "provider": self.provider_key,
            "pickup_date": pickup_data.get("pickup_date", "Tomorrow"),
            "slot": pickup_data.get("slot", "10:00 - 13:00"),
        }

    def track_consignment(self, awb_code: str) -> CourierTrackingResult:
        return CourierTrackingResult(
            awb_code=awb_code,
            provider_key=self.provider_key,
            current_status="IN_TRANSIT",
            origin="Jaipur Hub",
            destination="Bangalore South",
            estimated_delivery_date="2 Days",
            lat=26.9124,
            lng=75.7873,
            events=[
                {"status": "CONFIRMED", "location": "Jaipur City Centre", "activity": "Consignment manifested", "time": datetime.now(timezone.utc).isoformat()},
                {"status": "IN_TRANSIT", "location": "Delhi Transit Air Cargo", "activity": "Bagged for air connection", "time": datetime.now(timezone.utc).isoformat()},
            ],
        )


# Factory Manager
_PROVIDERS: Dict[str, BaseCourierProvider] = {
    "SHIPROCKET": ShiprocketProvider(),
    "DELHIVERY": DelhiveryProvider(),
    "INDIA_POST": IndiaPostProvider(),
    "DTDC": DTDCProvider(),
}


def get_courier_provider(key: str) -> BaseCourierProvider:
    k = key.upper()
    if k in _PROVIDERS:
        return _PROVIDERS[k]
    # Fallback to India Post
    return _PROVIDERS["INDIA_POST"]
