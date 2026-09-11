import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import get_current_user
from app.models.inventory import StockMovementType

client = TestClient(app)

ARTISAN_USER = {
    'firebase_uid': 'mock_artisan_uid_123',
    'phone': '+919876543210',
    'artisan': {
        'id': '22222222-2222-2222-2222-222222222222',
        'name': 'Ramesh Kumar',
        'phone': '+919876543210',
        'firebase_uid': 'mock_artisan_uid_123',
    },
    'claims': {'uid': 'mock_artisan_uid_123'},
}

@pytest.fixture(autouse=True)
def override_user():
    app.dependency_overrides[get_current_user] = lambda: ARTISAN_USER
    yield
    app.dependency_overrides.pop(get_current_user, None)

def test_inventory_lifecycle_and_endpoints():
    headers = {'Authorization': 'Bearer mock_token'}
    product_id = 'test-prod-101'

    # 1. Product inventory fetch (auto initialized)
    res = client.get(f'/api/v1/inventory/products/{product_id}', headers=headers)
    assert res.status_code == 200
    inv = res.json()
    assert inv['product_id'] == product_id
    assert inv['available_stock'] == 10
    assert inv['status_badge'] == 'in_stock'

    # 2. Add Stock (Restock)
    restock_payload = {
        'quantity': 15,
        'movement_type': 'restock',
        'notes': 'Added festival batch stock'
    }
    res = client.post(f'/api/v1/inventory/products/{product_id}/stock', json=restock_payload, headers=headers)
    assert res.status_code == 200
    updated_inv = res.json()
    assert updated_inv['available_stock'] == 25

    # 3. Check movements audit trail
    res = client.get(f'/api/v1/inventory/products/{product_id}/movements', headers=headers)
    assert res.status_code == 200
    movements = res.json()
    assert len(movements) >= 1
    assert movements[0]['movement_type'] == 'restock'
    assert movements[0]['quantity'] == 15

    # 4. Check dashboard metrics
    res = client.get('/api/v1/inventory/dashboard', headers=headers)
    assert res.status_code == 200
    metrics = res.json()
    assert metrics['total_products'] >= 1
    assert metrics['items_in_stock'] >= 25

    # 5. Check analytics
    res = client.get('/api/v1/inventory/analytics', headers=headers)
    assert res.status_code == 200
    analytics = res.json()
    assert 'monthly_stock_movements' in analytics
    assert 'fast_moving_products' in analytics
    assert 'dead_inventory' in analytics

    # 6. Raw Materials: create & list
    raw_payload = {
        'name': 'Terracotta Natural Clay',
        'unit': 'kg',
        'current_stock': 50.0,
        'minimum_stock': 10.0,
        'cost_per_unit': 45.0,
        'supplier_info': 'Rajasthan Clay Suppliers'
    }
    res = client.post('/api/v1/inventory/raw-materials', json=raw_payload, headers=headers)
    assert res.status_code == 200
    created_mat = res.json()
    assert created_mat['name'] == 'Terracotta Natural Clay'
    assert created_mat['is_low_stock'] is False

    res = client.get('/api/v1/inventory/raw-materials', headers=headers)
    assert res.status_code == 200
    materials = res.json()
    assert len(materials) >= 1
