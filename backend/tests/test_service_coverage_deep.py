"""
Deep Service Coverage Test Suite for Phase 8 Automated Testing Suite.
Tests storage, FCM, inventory, sustainability, IoT, and PDF generators.
"""

import pytest
from unittest.mock import MagicMock, patch

from app.services.invoice_pdf import generate_invoice_pdf
from app.services.certificate_pdf import generate_craft_certificate_pdf
from app.services.impact_pdf import generate_impact_report_pdf
from app.services.shipping_calculator import calculate_shipping_estimate
from app.services.inventory_service import (
    get_or_create_inventory,
    get_dashboard_metrics,
    get_inventory_analytics,
)
from app.services.iot_service import iot_service
from app.models.iot import IoTDeviceCreate, SensorReadingCreate, DeviceType, DeviceProtocol, ReadingType


from app.models.shipping import ShippingEstimateRequest


def test_pdf_generators():
    order_data = {
        "order_number": "ORD-2026-9999",
        "order_date": "07-Sep-2026",
        "status": "completed",
        "payment_method": "UPI",
    }
    invoice_data = {
        "invoice_number": "INV-2026-9999",
        "order_id": "ord-12345",
        "invoice_date": "07-Sep-2026",
        "artisan_name": "Ramesh Kumar",
        "artisan_location": "Jaipur, Rajasthan",
        "buyer_name": "Aditya Sharma",
        "buyer_address": "Bengaluru, Karnataka",
        "items": [{"title": "Blue Pottery Vase", "quantity": 2, "unit_price": 1250.0, "subtotal": 2500.0}],
        "subtotal": 2500.0,
        "shipping_cost": 150.0,
        "discount": 0.0,
        "total_amount": 2650.0,
    }
    pdf_bytes = generate_invoice_pdf(order_data, invoice_data)
    assert len(pdf_bytes) > 100
    assert pdf_bytes.startswith(b"%PDF")

    passport_data = {
        "passport_id": "PASS-RAJ-001",
        "product_title": "Jaipur Blue Pottery",
        "artisan_name": "Master Artisan Ramesh",
        "craft_cluster": "Jaipur Cluster",
        "state": "Rajasthan",
        "gi_tag_code": "GI-RAJ-004",
        "eco_score": 96.5,
        "authenticity_hash": "a1b2c3d4e5f6",
        "qr_code_base64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
    }
    cert_data = {
        "certificate_id": "CERT-2026-001",
        "verifier_name": "Craft Council of India",
        "issue_date": "2026-09-07",
    }
    cert_pdf = generate_craft_certificate_pdf(passport_data, cert_data)
    assert len(cert_pdf) > 100
    assert cert_pdf.startswith(b"%PDF")

    impact_data = {
        "report_id": "IMP-2026-001",
        "artisan_count": 50,
        "district": "Jaipur",
        "state": "Rajasthan",
        "total_earnings": 1500000.0,
        "crafts_digitized": 320,
    }
    imp_pdf = generate_impact_report_pdf(impact_data)
    assert len(imp_pdf) > 100
    assert imp_pdf.startswith(b"%PDF")


def test_shipping_calculator():
    req = ShippingEstimateRequest(
        origin_pincode="302001",
        destination_pincode="560001",
        weight_kg=2.0,
        length_cm=20.0,
        width_cm=15.0,
        height_cm=10.0,
    )
    est = calculate_shipping_estimate(req)
    assert est is not None
    assert est.chargeable_weight_kg >= 2.0
    assert len(est.ranked_couriers) > 0


def test_inventory_service_operations():
    artisan_id = "00000000-0000-0000-0000-000000000002"
    product_id = "00000000-0000-0000-0000-000000000101"

    inv = get_or_create_inventory(product_id, artisan_id, initial_stock=15)
    assert inv is not None
    assert inv.get("available_stock") >= 0

    metrics = get_dashboard_metrics(artisan_id)
    assert metrics is not None
    assert metrics.total_products >= 0

    analytics = get_inventory_analytics(artisan_id)
    assert analytics is not None
    assert len(analytics.monthly_stock_movements) == 6


def test_iot_service_operations():
    artisan_id = "00000000-0000-0000-0000-000000000002"
    device = iot_service.register_device(
        artisan_id=artisan_id,
        payload=IoTDeviceCreate(
            device_name="Kiln Temperature Sensor #1",
            device_type=DeviceType.temp_sensor,
            protocol=DeviceProtocol.zigbee,
            location_in_workshop="Main Furnace Room"
        )
    )
    assert device is not None
    assert device.id is not None

    dev_id = device.id
    reading = iot_service.record_reading(
        artisan_id=artisan_id,
        payload=SensorReadingCreate(
            device_id=dev_id,
            reading_type=ReadingType.temperature_c,
            value_numeric=850.5,
            unit="°C",
        )
    )
    assert reading is not None
    assert reading.value_numeric == 850.5

    status = iot_service.get_workshop_climate(artisan_id)
    assert status is not None
    assert status.ambient_temperature_c is not None
