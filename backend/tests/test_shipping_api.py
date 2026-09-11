import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import get_current_user

client = TestClient(app)

MOCK_USER = {
    'firebase_uid': 'test_user_uid_123',
    'phone': '+919876543210',
    'claims': {'uid': 'test_user_uid_123'}
}

@pytest.fixture(autouse=True)
def override_user():
    app.dependency_overrides[get_current_user] = lambda: MOCK_USER
    yield
    app.dependency_overrides.pop(get_current_user, None)


def test_shipping_estimate_and_smart_courier_ranking():
    req_payload = {
        'weight_kg': 1.5,
        'length_cm': 25.0,
        'width_cm': 20.0,
        'height_cm': 15.0,
        'origin_pincode': '302001',
        'destination_pincode': '560001',
        'is_fragile': True,
        'is_insured': True,
        'declared_value': 2500.0,
        'courier_preference': 'india_post'
    }
    res = client.post('/api/v1/shipping/estimate', json=req_payload)
    assert res.status_code == 200
    data = res.json()
    assert data['estimated_cost'] > 0
    assert data['estimated_delivery_days'] >= 1
    assert 'chargeable_weight_kg' in data
    assert 'volumetric_weight_kg' in data
    assert 'ranked_couriers' in data
    assert len(data['ranked_couriers']) >= 3
    assert any(c['is_recommended'] for c in data['ranked_couriers'])

    # Packaging Assistant
    assert 'packaging_assistant' in data
    pkg = data['packaging_assistant']
    assert pkg['is_fragile'] is True
    assert 'FRAGILE' in pkg['fragile_label']
    assert 'bubble wrap' in pkg['suggested_packing_material'].lower()


def test_shipment_creation_and_8_stage_tracking():
    # 1. Create Shipment
    ship_payload = {
        'order_id': '33333333-3333-3333-3333-333333333333',
        'origin_pincode': '302001',
        'destination_pincode': '560001',
        'weight_kg': 2.0,
        'length_cm': 30.0,
        'width_cm': 20.0,
        'height_cm': 15.0,
        'pickup_type': 'pickup_available',
        'courier_partner': 'India Post Speed Post',
        'is_fragile': True,
        'is_insured': True,
        'declared_value': 3500.0
    }
    res = client.post('/api/v1/shipping/shipments', json=ship_payload)
    assert res.status_code == 200
    shipment = res.json()
    tracking_number = shipment['tracking_number']
    assert tracking_number.startswith('INP-KC-')
    assert shipment['shipping_cost'] > 0

    # 2. Track Shipment
    res_track = client.get(f'/api/v1/shipping/track/{tracking_number}')
    assert res_track.status_code == 200
    track_data = res_track.json()
    assert track_data['tracking_number'] == tracking_number
    assert len(track_data['timeline']) >= 5
    statuses = [e['status'] for e in track_data['timeline']]
    assert 'CONFIRMED' in statuses or 'PACKED' in statuses
    assert 'DELIVERED' in statuses
    assert 'map_coordinates' in track_data
