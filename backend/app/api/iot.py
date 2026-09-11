"""IoT Smart Workshop API Router (Phase 7).

Endpoints:
  GET  /api/v1/iot/devices           - List all connected devices
  POST /api/v1/iot/devices           - Register a new IoT device
  POST /api/v1/iot/devices/{id}/ping - Ping device / heartbeat
  POST /api/v1/iot/readings          - Ingest single sensor reading
  POST /api/v1/iot/readings/batch    - Sync batch offline sensor readings
  POST /api/v1/iot/scan              - Process Barcode/QR or NFC scan event (auto stock update)
  POST /api/v1/iot/verify-weight     - Verify weight on smart scale
  POST /api/v1/iot/measure-package   - Package volumetric & dimensional calculations
  POST /api/v1/iot/print             - Dispatch thermal label print job
  GET  /api/v1/iot/workshop-climate  - Live temperature & humidity telemetry
  GET  /api/v1/iot/alerts            - List smart workshop alerts
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status

from app.models.iot import (
    IoTDeviceCreate,
    IoTDeviceUpdate,
    IoTDeviceResponse,
    SensorReadingCreate,
    SensorReadingResponse,
    BatchSensorSyncRequest,
    DeviceScanActionRequest,
    DeviceScanActionResponse,
    WeightVerificationRequest,
    WeightVerificationResponse,
    PackageMeasurementRequest,
    PackageMeasurementResponse,
    SmartPrintJobRequest,
    SmartPrintJobResponse,
    WorkshopClimateStatusResponse,
    IoTAlertResponse,
)
from app.services.iot_service import iot_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/iot", tags=["IoT Smart Workshop"])


@router.get("/devices", response_model=List[IoTDeviceResponse], status_code=status.HTTP_200_OK)
async def get_devices(artisan_id: Optional[str] = Query("00000000-0000-0000-0000-000000000002")):
    """List all connected workshop devices (scales, scanners, NFC, sensors, printers)."""
    return iot_service.list_devices(artisan_id=artisan_id)


@router.post("/devices", response_model=IoTDeviceResponse, status_code=status.HTTP_201_CREATED)
async def register_device(payload: IoTDeviceCreate):
    """Pair and register a new smart hardware device in the workshop."""
    artisan_id = payload.artisan_id or "00000000-0000-0000-0000-000000000002"
    return iot_service.register_device(artisan_id=artisan_id, payload=payload)


@router.post("/devices/{device_id}/ping", response_model=IoTDeviceResponse, status_code=status.HTTP_200_OK)
async def ping_device(device_id: str, battery_pct: Optional[int] = Query(None, ge=0, le=100)):
    """Device heartbeat ping to keep status online and update battery percentage."""
    return iot_service.ping_device(device_id=device_id, battery_pct=battery_pct)


@router.post("/readings", response_model=SensorReadingResponse, status_code=status.HTTP_201_CREATED)
async def record_sensor_reading(
    payload: SensorReadingCreate,
    artisan_id: Optional[str] = Query("00000000-0000-0000-0000-000000000002")
):
    """Ingest live sensor telemetry from smart scale, thermometer, or hygrometer."""
    return iot_service.record_reading(artisan_id=artisan_id, payload=payload)


@router.post("/readings/batch", status_code=status.HTTP_200_OK)
async def sync_offline_readings(payload: BatchSensorSyncRequest):
    """Batch synchronize readings collected offline during network outage."""
    artisan_id = payload.artisan_id or "00000000-0000-0000-0000-000000000002"
    count = iot_service.sync_batch_readings(artisan_id=artisan_id, readings=payload.readings)
    return {"status": "success", "synced_count": count, "message": f"Successfully ingested {count} offline readings."}


@router.post("/scan", response_model=DeviceScanActionResponse, status_code=status.HTTP_200_OK)
async def process_scan_event(
    payload: DeviceScanActionRequest,
    artisan_id: Optional[str] = Query("00000000-0000-0000-0000-000000000002")
):
    """
    Process Barcode, 2D QR, or NFC scan to automatically update inventory without manual entry.
    """
    return iot_service.process_scan_event(artisan_id=artisan_id, payload=payload)


@router.post("/verify-weight", response_model=WeightVerificationResponse, status_code=status.HTTP_200_OK)
async def verify_product_weight(payload: WeightVerificationRequest):
    """Verify weight on smart scale against catalog baseline and shipping limits."""
    return iot_service.verify_weight(payload=payload)


@router.post("/measure-package", response_model=PackageMeasurementResponse, status_code=status.HTTP_200_OK)
async def calculate_package_measurements(payload: PackageMeasurementRequest):
    """Calculate volumetric weight, chargeable weight, and parcel shipping tiers."""
    return iot_service.measure_package(payload=payload)


@router.post("/print", response_model=SmartPrintJobResponse, status_code=status.HTTP_200_OK)
async def trigger_smart_print_job(payload: SmartPrintJobRequest):
    """Format and send label print job (ZPL / ESC-POS) to wireless thermal printer."""
    return iot_service.dispatch_print_job(payload=payload)


@router.get("/workshop-climate", response_model=WorkshopClimateStatusResponse, status_code=status.HTTP_200_OK)
async def get_workshop_climate_telemetry(artisan_id: Optional[str] = Query("00000000-0000-0000-0000-000000000002")):
    """Get live ambient workshop temperature, humidity, and kiln status."""
    return iot_service.get_workshop_climate(artisan_id=artisan_id)


@router.get("/alerts", response_model=List[IoTAlertResponse], status_code=status.HTTP_200_OK)
async def get_iot_alerts(artisan_id: Optional[str] = Query("00000000-0000-0000-0000-000000000002")):
    """List active climate anomalies, device battery alerts, and threshold warnings."""
    return iot_service.get_alerts(artisan_id=artisan_id)

