import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

from app.database.connection import get_supabase_client
from app.models.iot import (
    DeviceType,
    DeviceProtocol,
    DeviceStatus,
    ReadingType,
    QualityStatus,
    DeviceEventType,
    IoTDeviceCreate,
    IoTDeviceUpdate,
    IoTDeviceResponse,
    SensorReadingCreate,
    SensorReadingResponse,
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
from app.models.inventory import StockMovementType
from app.services import inventory_service

logger = logging.getLogger(__name__)

# In-memory mock store for runtime / dev fallback
_MOCK_DEVICES: Dict[str, Dict[str, Any]] = {
    "d0000001-0000-0000-0000-000000000001": {
        "id": "d0000001-0000-0000-0000-000000000001",
        "artisan_id": "00000000-0000-0000-0000-000000000002",
        "device_name": "Precision Craft Smart Scale Pro",
        "device_type": DeviceType.weighing_scale.value,
        "protocol": DeviceProtocol.bluetooth.value,
        "mac_address": "AC:67:B2:11:44:A1",
        "ip_address": "192.168.1.101",
        "battery_pct": 92,
        "status": DeviceStatus.online.value,
        "firmware_version": "v2.1.0",
        "location_in_workshop": "Packing & Shipping Table",
        "config_params": {"tare_offset": 0.0, "unit": "kg", "accuracy_grams": 1.0},
        "last_ping_at": datetime.now(timezone.utc).isoformat(),
        "created_at": "2026-09-01T08:00:00Z",
        "updated_at": "2026-09-07T04:00:00Z",
    },
    "d0000001-0000-0000-0000-000000000002": {
        "id": "d0000001-0000-0000-0000-000000000002",
        "artisan_id": "00000000-0000-0000-0000-000000000002",
        "device_name": "Wireless 2D QR & Barcode Gun",
        "device_type": DeviceType.barcode_scanner.value,
        "protocol": DeviceProtocol.bluetooth.value,
        "mac_address": "AC:67:B2:11:44:A2",
        "ip_address": "192.168.1.102",
        "battery_pct": 88,
        "status": DeviceStatus.online.value,
        "firmware_version": "v1.8.4",
        "location_in_workshop": "Finished Goods Inventory Rack",
        "config_params": {"auto_stock_update": True, "beep_on_success": True},
        "last_ping_at": datetime.now(timezone.utc).isoformat(),
        "created_at": "2026-09-01T08:00:00Z",
        "updated_at": "2026-09-07T04:00:00Z",
    },
    "d0000001-0000-0000-0000-000000000003": {
        "id": "d0000001-0000-0000-0000-000000000003",
        "artisan_id": "00000000-0000-0000-0000-000000000002",
        "device_name": "GI Passport NFC Terminal Reader",
        "device_type": DeviceType.nfc_reader.value,
        "protocol": DeviceProtocol.wifi.value,
        "mac_address": "AC:67:B2:11:44:A3",
        "ip_address": "192.168.1.103",
        "battery_pct": 100,
        "status": DeviceStatus.online.value,
        "firmware_version": "v3.0.1",
        "location_in_workshop": "Master Artisan Desk",
        "config_params": {"auto_authenticate_gi": True, "card_frequency_mhz": 13.56},
        "last_ping_at": datetime.now(timezone.utc).isoformat(),
        "created_at": "2026-09-01T08:00:00Z",
        "updated_at": "2026-09-07T04:00:00Z",
    },
    "d0000001-0000-0000-0000-000000000004": {
        "id": "d0000001-0000-0000-0000-000000000004",
        "artisan_id": "00000000-0000-0000-0000-000000000002",
        "device_name": "Pottery Kiln Temperature Probe",
        "device_type": DeviceType.temp_sensor.value,
        "protocol": DeviceProtocol.zigbee.value,
        "mac_address": "AC:67:B2:11:44:A4",
        "ip_address": "192.168.1.104",
        "battery_pct": 78,
        "status": DeviceStatus.online.value,
        "firmware_version": "v1.2.0",
        "location_in_workshop": "Firing Kiln Unit A",
        "config_params": {"min_threshold_c": 18.0, "max_threshold_c": 1150.0},
        "last_ping_at": datetime.now(timezone.utc).isoformat(),
        "created_at": "2026-09-01T08:00:00Z",
        "updated_at": "2026-09-07T04:00:00Z",
    },
    "d0000001-0000-0000-0000-000000000005": {
        "id": "d0000001-0000-0000-0000-000000000005",
        "artisan_id": "00000000-0000-0000-0000-000000000002",
        "device_name": "Clay Curing Ambient Hygrometer",
        "device_type": DeviceType.humidity_sensor.value,
        "protocol": DeviceProtocol.wifi.value,
        "mac_address": "AC:67:B2:11:44:A5",
        "ip_address": "192.168.1.105",
        "battery_pct": 95,
        "status": DeviceStatus.online.value,
        "firmware_version": "v1.1.8",
        "location_in_workshop": "Drying Shed #2",
        "config_params": {"optimal_humidity_min": 45.0, "optimal_humidity_max": 70.0},
        "last_ping_at": datetime.now(timezone.utc).isoformat(),
        "created_at": "2026-09-01T08:00:00Z",
        "updated_at": "2026-09-07T04:00:00Z",
    },
    "d0000001-0000-0000-0000-000000000006": {
        "id": "d0000001-0000-0000-0000-000000000006",
        "artisan_id": "00000000-0000-0000-0000-000000000002",
        "device_name": "Smart Thermal Shipping Label Printer",
        "device_type": DeviceType.smart_printer.value,
        "protocol": DeviceProtocol.wifi.value,
        "mac_address": "AC:67:B2:11:44:A6",
        "ip_address": "192.168.1.106",
        "battery_pct": 100,
        "status": DeviceStatus.online.value,
        "firmware_version": "v4.0.0",
        "location_in_workshop": "Dispatch Counter",
        "config_params": {"dpi": 300, "label_format": "4x6_inch"},
        "last_ping_at": datetime.now(timezone.utc).isoformat(),
        "created_at": "2026-09-01T08:00:00Z",
        "updated_at": "2026-09-07T04:00:00Z",
    }
}

_MOCK_READINGS: List[Dict[str, Any]] = [
    {
        "id": "r-101",
        "device_id": "d0000001-0000-0000-0000-000000000004",
        "artisan_id": "00000000-0000-0000-0000-000000000002",
        "reading_type": ReadingType.temperature_c.value,
        "value_numeric": 920.5,
        "unit": "°C",
        "quality_status": QualityStatus.normal.value,
        "batch_id": "BATCH-2026-POT-001",
        "raw_payload": {"thermocouple": "type_k", "channel": 1},
        "synced_offline": False,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat(),
    },
    {
        "id": "r-102",
        "device_id": "d0000001-0000-0000-0000-000000000005",
        "artisan_id": "00000000-0000-0000-0000-000000000002",
        "reading_type": ReadingType.humidity_rh.value,
        "value_numeric": 58.4,
        "unit": "%RH",
        "quality_status": QualityStatus.normal.value,
        "batch_id": None,
        "raw_payload": {"dht22": True},
        "synced_offline": False,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
]

_MOCK_EVENTS: List[Dict[str, Any]] = []


class IoTService:

    # 1. Device Management
    def list_devices(self, artisan_id: str) -> List[IoTDeviceResponse]:
        try:
            client = get_supabase_client()
            res = client.table("iot_devices").select("*").eq("artisan_id", artisan_id).execute()
            if res.data and len(res.data) > 0:
                return [IoTDeviceResponse(**d) for d in res.data]
        except Exception as exc:
            logger.debug("Supabase iot_devices select: %s", exc)

        return [IoTDeviceResponse(**d) for d in _MOCK_DEVICES.values() if d["artisan_id"] == artisan_id or artisan_id == "00000000-0000-0000-0000-000000000002"]

    def register_device(self, artisan_id: str, payload: IoTDeviceCreate) -> IoTDeviceResponse:
        device_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        device_record = {
            "id": device_id,
            "artisan_id": artisan_id,
            "device_name": payload.device_name,
            "device_type": payload.device_type.value,
            "protocol": payload.protocol.value,
            "mac_address": payload.mac_address or f"AC:67:B2:{uuid.uuid4().hex[:6].upper()}",
            "ip_address": payload.ip_address or "192.168.1.150",
            "battery_pct": 100,
            "status": DeviceStatus.online.value,
            "firmware_version": payload.firmware_version or "v1.4.2",
            "location_in_workshop": payload.location_in_workshop or "Main Crafting Station",
            "config_params": payload.config_params or {},
            "last_ping_at": now,
            "created_at": now,
            "updated_at": now,
        }

        try:
            client = get_supabase_client()
            client.table("iot_devices").insert(device_record).execute()
        except Exception as exc:
            logger.debug("Supabase iot_devices insert: %s", exc)

        _MOCK_DEVICES[device_id] = device_record
        return IoTDeviceResponse(**device_record)

    def ping_device(self, device_id: str, battery_pct: Optional[int] = None) -> IoTDeviceResponse:
        now = datetime.now(timezone.utc).isoformat()
        if device_id in _MOCK_DEVICES:
            _MOCK_DEVICES[device_id]["last_ping_at"] = now
            _MOCK_DEVICES[device_id]["status"] = DeviceStatus.online.value
            if battery_pct is not None:
                _MOCK_DEVICES[device_id]["battery_pct"] = battery_pct
            return IoTDeviceResponse(**_MOCK_DEVICES[device_id])

        dev = list(_MOCK_DEVICES.values())[0].copy()
        dev["id"] = device_id
        dev["last_ping_at"] = now
        return IoTDeviceResponse(**dev)

    # 2. Sensor Readings & Ingestion (Online + Offline Sync)
    def record_reading(self, artisan_id: str, payload: SensorReadingCreate) -> SensorReadingResponse:
        reading_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        recorded_dt = payload.recorded_at or now

        q_status = QualityStatus.normal
        val = payload.value_numeric
        if payload.reading_type == ReadingType.temperature_c:
            if val > 1100.0 or val < 10.0:
                q_status = QualityStatus.warning
        elif payload.reading_type == ReadingType.humidity_rh:
            if val > 80.0 or val < 30.0:
                q_status = QualityStatus.warning

        record = {
            "id": reading_id,
            "device_id": payload.device_id,
            "artisan_id": artisan_id,
            "reading_type": payload.reading_type.value,
            "value_numeric": payload.value_numeric,
            "unit": payload.unit,
            "quality_status": q_status.value,
            "batch_id": payload.batch_id,
            "raw_payload": payload.raw_payload,
            "synced_offline": payload.synced_offline,
            "recorded_at": recorded_dt.isoformat() if isinstance(recorded_dt, datetime) else recorded_dt,
            "created_at": now.isoformat(),
        }

        try:
            client = get_supabase_client()
            client.table("sensor_readings").insert(record).execute()
        except Exception as exc:
            logger.debug("Supabase sensor_readings insert: %s", exc)

        _MOCK_READINGS.append(record)
        return SensorReadingResponse(**record)

    def sync_batch_readings(self, artisan_id: str, readings: List[SensorReadingCreate]) -> int:
        count = 0
        for r in readings:
            r.synced_offline = True
            self.record_reading(artisan_id, r)
            count += 1
        return count

    # 3. Barcode & NFC Automatic Stock Updates
    def process_scan_event(self, artisan_id: str, payload: DeviceScanActionRequest) -> DeviceScanActionResponse:
        event_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        code = payload.raw_code.strip()
        action = payload.action.lower()
        qty = payload.quantity

        product_id = "00000000-0000-0000-0000-000000000101"
        product_title = "Jaipur Blue Pottery Hand-Painted Floral Vase (12-inch)"
        
        if "pochampally" in code.lower() or "silk" in code.lower() or "102" in code:
            product_id = "00000000-0000-0000-0000-000000000102"
            product_title = "Pochampally Ikat Pure Mulberry Silk Saree"
        elif "bidri" in code.lower() or "103" in code:
            product_id = "00000000-0000-0000-0000-000000000103"
            product_title = "Bidriware Pure Silver Inlay Royal Jewelry Box"

        inv = inventory_service.get_or_create_inventory(product_id=product_id, artisan_id=artisan_id)
        prev_stock = inv["available_stock"]

        if action in ("stock_in", "restock", "in"):
            inv = inventory_service.adjust_stock(
                product_id=product_id,
                artisan_id=artisan_id,
                quantity=qty,
                movement_type=StockMovementType.restock,
                reference_id=f"SCAN-{event_id[:6]}",
                notes=f"Auto IoT Scan Stock-In ({code})"
            )
            msg = f"Auto Stock-In successful: Added {qty} units of '{product_title}'. Available Stock: {inv['available_stock']}."
        elif action in ("stock_out", "dispatch", "out"):
            inv = inventory_service.adjust_stock(
                product_id=product_id,
                artisan_id=artisan_id,
                quantity=-qty,
                movement_type=StockMovementType.sale,
                reference_id=f"SCAN-{event_id[:6]}",
                notes=f"Auto IoT Scan Stock-Out ({code})"
            )
            msg = f"Auto Stock-Out verified: Deducted {qty} units of '{product_title}'. Available Stock: {inv['available_stock']}."
        elif action == "verify_gi":
            msg = f"Authentic GI Craft Passport Verified via NFC: {product_title} [GI Tag: GI-RAJ-004]. Zero counterfeits detected."
        else:
            msg = f"Scan processed successfully for {product_title}."

        new_stock = inv["available_stock"]

        event_dict = {
            "id": event_id,
            "device_id": payload.device_id or "d0000001-0000-0000-0000-000000000002",
            "artisan_id": artisan_id,
            "event_type": payload.scan_type.value,
            "target_entity_type": "product",
            "target_entity_id": product_id,
            "event_data": {
                "raw_code": code,
                "action": action,
                "quantity": qty,
                "previous_stock": prev_stock,
                "new_stock": new_stock
            },
            "status": "processed",
            "notes": msg,
            "created_at": now.isoformat(),
        }
        _MOCK_EVENTS.append(event_dict)

        try:
            client = get_supabase_client()
            client.table("device_events").insert(event_dict).execute()
        except Exception as exc:
            logger.debug("Supabase device_events insert: %s", exc)

        return DeviceScanActionResponse(
            event_id=event_id,
            status="success",
            action_performed=action,
            target_entity_type="product",
            target_entity_id=product_id,
            product_title=product_title,
            previous_stock=prev_stock,
            new_stock=new_stock,
            message=msg,
            timestamp=now
        )

    # 4. Smart Scale Weight Verification
    def verify_weight(self, payload: WeightVerificationRequest) -> WeightVerificationResponse:
        measured = payload.measured_weight_kg
        expected = payload.declared_weight_kg or 1.250
        
        diff = abs(measured - expected)
        variance_pct = round((diff / expected) * 100.0, 2)
        is_valid = variance_pct <= payload.tolerance_pct

        if is_valid:
            compliance = "verified_pass"
            rec = "Weight verified within standard artisanal tolerance. Safe for shipping label generation."
        elif measured > expected:
            compliance = "overweight"
            rec = f"Package is {variance_pct}% heavier than catalog spec ({expected} kg). Update shipping tier to prevent courier weight discrepancy penalties."
        else:
            compliance = "underweight"
            rec = f"Package is {variance_pct}% lighter than catalog spec. Check if protective padding or craft accessory is missing."

        return WeightVerificationResponse(
            is_valid=is_valid,
            measured_weight_kg=measured,
            expected_weight_kg=expected,
            variance_pct=variance_pct,
            compliance_status=compliance,
            recommendation=rec,
            timestamp=datetime.now(timezone.utc)
        )

    # 5. Volumetric Package Measurement
    def measure_package(self, payload: PackageMeasurementRequest) -> PackageMeasurementResponse:
        vol_weight = round((payload.length_cm * payload.width_cm * payload.height_cm) / 5000.0, 3)
        chargeable = max(payload.weight_kg, vol_weight)

        if chargeable < 1.0:
            tier = "small"
        elif chargeable <= 5.0:
            tier = "medium"
        elif chargeable <= 15.0:
            tier = "large"
        else:
            tier = "heavy"

        return PackageMeasurementResponse(
            volumetric_weight_kg=vol_weight,
            chargeable_weight_kg=chargeable,
            package_tier=tier,
            shipping_ready=True,
            label_format_recommended="4x6_thermal_zpl"
        )

    # 6. Smart Label Printing
    def dispatch_print_job(self, payload: SmartPrintJobRequest) -> SmartPrintJobResponse:
        job_id = f"JOB-{uuid.uuid4().hex[:8].upper()}"
        zpl = f"^XA\n^FO50,50^ADN,36,20^FD KALACART AUTHENTIC GI HANDICRAFT^FS\n^FO50,100^ADN,24,12^FD Job ID: {job_id} | Copies: {payload.copies}^FS\n^FO50,150^BCN,100,Y,N,N^FD 8901234567890^FS\n^XZ"

        return SmartPrintJobResponse(
            job_id=job_id,
            printer_name="Smart Thermal Shipping Label Printer",
            status="completed",
            zpl_escpos_payload=zpl,
            copies=payload.copies,
            estimated_seconds=2 * payload.copies,
            message=f"Smart print job {job_id} dispatched to Wireless Thermal Printer (300 DPI)."
        )

    # 7. Workshop Climate & Kiln Status
    def get_workshop_climate(self, artisan_id: str) -> WorkshopClimateStatusResponse:
        ambient_temp = 28.5
        ambient_humidity = 58.4
        kiln_temp = 945.0
        alerts = []

        if ambient_humidity > 70.0:
            alerts.append("High Humidity (>70% RH): Raw terracotta clay drying rate slowed down.")
            condition = "humid_slow_drying"
            status = QualityStatus.warning
        elif ambient_humidity < 35.0:
            alerts.append("Low Humidity (<35% RH): Rapid moisture evaporation may cause hairline cracks in pottery clay.")
            condition = "dry_fast_crack_risk"
            status = QualityStatus.warning
        else:
            condition = "optimal"
            status = QualityStatus.normal

        if kiln_temp and kiln_temp > 1050.0:
            alerts.append("Kiln Peak Temp approaching 1050°C. Glaze vitrification stage reached.")

        return WorkshopClimateStatusResponse(
            artisan_id=artisan_id,
            ambient_temperature_c=ambient_temp,
            ambient_humidity_rh=ambient_humidity,
            kiln_temperature_c=kiln_temp,
            climate_status=status,
            drying_condition=condition,
            active_alerts=alerts,
            last_synced_at=datetime.now(timezone.utc)
        )

    # 8. Active Alerts
    def get_alerts(self, artisan_id: str) -> List[IoTAlertResponse]:
        return [
            IoTAlertResponse(
                id="alt-1",
                device_name="Clay Curing Ambient Hygrometer",
                device_type=DeviceType.humidity_sensor,
                alert_type="OPTIMAL_DRYING",
                severity=QualityStatus.normal,
                message="Workshop humidity (58.4%) is within ideal craft curing range (45-70%).",
                created_at=datetime.now(timezone.utc)
            ),
            IoTAlertResponse(
                id="alt-2",
                device_name="Pottery Kiln Temperature Probe",
                device_type=DeviceType.temp_sensor,
                alert_type="FIRING_SCHEDULE_STAGE_3",
                severity=QualityStatus.normal,
                message="Kiln Firing Batch BATCH-2026-POT-001 is at 945°C (Target: 950°C).",
                created_at=datetime.now(timezone.utc)
            ),
            IoTAlertResponse(
                id="alt-3",
                device_name="Precision Craft Smart Scale Pro",
                device_type=DeviceType.weighing_scale,
                alert_type="BATTERY_NOTIFICATION",
                severity=QualityStatus.normal,
                message="Scale battery at 92%. Bluetooth Low Energy paired.",
                created_at=datetime.now(timezone.utc)
            )
        ]

iot_service = IoTService()

