"""Pydantic models for IoT Smart Workshop Domain (Phase 7)."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DeviceType(str, Enum):
    weighing_scale = "weighing_scale"
    barcode_scanner = "barcode_scanner"
    nfc_reader = "nfc_reader"
    temp_sensor = "temp_sensor"
    humidity_sensor = "humidity_sensor"
    smart_printer = "smart_printer"


class DeviceProtocol(str, Enum):
    bluetooth = "bluetooth"
    wifi = "wifi"
    usb = "usb"
    zigbee = "zigbee"


class DeviceStatus(str, Enum):
    online = "online"
    offline = "offline"
    pairing = "pairing"
    error = "error"


class ReadingType(str, Enum):
    weight_kg = "weight_kg"
    temperature_c = "temperature_c"
    humidity_rh = "humidity_rh"
    dimensions_cm = "dimensions_cm"


class QualityStatus(str, Enum):
    normal = "normal"
    warning = "warning"
    critical = "critical"


class DeviceEventType(str, Enum):
    barcode_scan = "barcode_scan"
    nfc_tap = "nfc_tap"
    print_job = "print_job"
    weight_verified = "weight_verified"
    threshold_alert = "threshold_alert"


class IoTDeviceBase(BaseModel):
    device_name: str = Field(..., min_length=2, max_length=150)
    device_type: DeviceType
    protocol: DeviceProtocol = Field(default=DeviceProtocol.bluetooth)
    mac_address: Optional[str] = None
    ip_address: Optional[str] = None
    location_in_workshop: Optional[str] = "Main Crafting Station"
    firmware_version: Optional[str] = "v1.4.2"
    config_params: Dict[str, Any] = Field(default_factory=dict)


class IoTDeviceCreate(IoTDeviceBase):
    artisan_id: Optional[str] = None


class IoTDeviceUpdate(BaseModel):
    device_name: Optional[str] = None
    protocol: Optional[DeviceProtocol] = None
    mac_address: Optional[str] = None
    ip_address: Optional[str] = None
    battery_pct: Optional[int] = Field(default=None, ge=0, le=100)
    status: Optional[DeviceStatus] = None
    location_in_workshop: Optional[str] = None
    config_params: Optional[Dict[str, Any]] = None


class IoTDeviceResponse(IoTDeviceBase):
    id: str
    artisan_id: str
    battery_pct: int = 100
    status: DeviceStatus = DeviceStatus.online
    last_ping_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class SensorReadingCreate(BaseModel):
    device_id: str
    reading_type: ReadingType
    value_numeric: float
    unit: str
    batch_id: Optional[str] = None
    raw_payload: Dict[str, Any] = Field(default_factory=dict)
    synced_offline: bool = False
    recorded_at: Optional[datetime] = None


class SensorReadingResponse(BaseModel):
    id: str
    device_id: str
    artisan_id: str
    reading_type: ReadingType
    value_numeric: float
    unit: str
    quality_status: QualityStatus = QualityStatus.normal
    batch_id: Optional[str] = None
    raw_payload: Dict[str, Any] = Field(default_factory=dict)
    synced_offline: bool = False
    recorded_at: datetime
    created_at: datetime


class BatchSensorSyncRequest(BaseModel):
    artisan_id: Optional[str] = None
    readings: List[SensorReadingCreate]


class DeviceScanActionRequest(BaseModel):
    device_id: Optional[str] = None
    scan_type: DeviceEventType = Field(default=DeviceEventType.barcode_scan)
    raw_code: str = Field(..., description="Scanned Barcode, QR string, or NFC UID")
    action: str = Field(default="stock_in", description="stock_in, stock_out, order_pick, verify_gi")
    quantity: int = Field(default=1, ge=1)
    notes: Optional[str] = None


class DeviceScanActionResponse(BaseModel):
    event_id: str
    status: str
    action_performed: str
    target_entity_type: str
    target_entity_id: str
    product_title: Optional[str] = None
    previous_stock: Optional[int] = None
    new_stock: Optional[int] = None
    message: str
    timestamp: datetime


class WeightVerificationRequest(BaseModel):
    device_id: Optional[str] = None
    product_id: Optional[str] = None
    order_id: Optional[str] = None
    measured_weight_kg: float = Field(..., gt=0.0)
    declared_weight_kg: Optional[float] = None
    tolerance_pct: float = Field(default=10.0, ge=1.0, le=50.0)


class WeightVerificationResponse(BaseModel):
    is_valid: bool
    measured_weight_kg: float
    expected_weight_kg: float
    variance_pct: float
    compliance_status: str  # verified_pass, overweight, underweight
    recommendation: str
    timestamp: datetime


class PackageMeasurementRequest(BaseModel):
    device_id: Optional[str] = None
    order_id: Optional[str] = None
    length_cm: float = Field(..., gt=0)
    width_cm: float = Field(..., gt=0)
    height_cm: float = Field(..., gt=0)
    weight_kg: float = Field(..., gt=0)


class PackageMeasurementResponse(BaseModel):
    volumetric_weight_kg: float
    chargeable_weight_kg: float
    package_tier: str  # small, medium, large, heavy
    shipping_ready: bool
    label_format_recommended: str


class SmartPrintJobRequest(BaseModel):
    device_id: Optional[str] = None
    job_type: str = Field(default="shipping_label", description="shipping_label, sku_barcode, gi_tag, qr_passport")
    order_id: Optional[str] = None
    product_id: Optional[str] = None
    copies: int = Field(default=1, ge=1, le=50)
    custom_text: Optional[str] = None


class SmartPrintJobResponse(BaseModel):
    job_id: str
    printer_name: str
    status: str  # queued, printing, completed, failed
    zpl_escpos_payload: str
    copies: int
    estimated_seconds: int
    message: str


class WorkshopClimateStatusResponse(BaseModel):
    artisan_id: str
    ambient_temperature_c: float
    ambient_humidity_rh: float
    kiln_temperature_c: Optional[float] = None
    climate_status: QualityStatus
    drying_condition: str  # optimal, humid_slow_drying, dry_fast_crack_risk
    active_alerts: List[str] = Field(default_factory=list)
    last_synced_at: datetime


class IoTAlertResponse(BaseModel):
    id: str
    device_name: str
    device_type: DeviceType
    alert_type: str
    severity: QualityStatus
    message: str
    created_at: datetime
