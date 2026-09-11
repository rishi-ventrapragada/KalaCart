import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import get_current_user

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

def test_clusters_api_flow():
    # 1. List Clusters
    res = client.get('/api/v1/clusters')
    assert res.status_code == 200
    clusters = res.json()
    assert isinstance(clusters, list)
    assert len(clusters) >= 4
    pochampally = next((c for c in clusters if 'Pochampally' in c['name']), None)
    assert pochampally is not None
    cluster_id = pochampally['id']

    # 2. Get Cluster Details
    res = client.get(f'/api/v1/clusters/{cluster_id}')
    assert res.status_code == 200
    details = res.json()
    assert details['name'] == pochampally['name']
    assert details['state'] == 'Telangana'
    assert details['is_verified'] is True

    # 3. Join Cluster
    join_payload = {
        'artisan_name': 'Ramesh Kumar',
        'craft_specialty': 'Ikat Double Tie-Dye Weaving',
        'phone': '+919876543210'
    }
    res = client.post(f'/api/v1/clusters/{cluster_id}/join', json=join_payload)
    assert res.status_code in [200, 201]
    member = res.json()
    assert member['cluster_id'] == cluster_id
    assert member['role'] == 'artisan'

    # 4. List Members
    res = client.get(f'/api/v1/clusters/{cluster_id}/members')
    assert res.status_code == 200
    members = res.json()
    assert len(members) >= 1

    # 5. List Cluster Products (Attribution check)
    res = client.get(f'/api/v1/clusters/{cluster_id}/products')
    assert res.status_code == 200
    products = res.json()
    assert len(products) >= 1
    assert products[0]['artisan_name'] is not None

    # 6. Add Product to Cluster Catalogue
    prod_payload = {
        'product_id': '44444444-4444-4444-4444-444444444444',
        'is_featured': True
    }
    res = client.post(f'/api/v1/clusters/{cluster_id}/products', json=prod_payload)
    assert res.status_code in [200, 201]
    new_prod = res.json()
    assert new_prod['cluster_id'] == cluster_id

    # 7. Cluster Analytics
    res = client.get(f'/api/v1/clusters/{cluster_id}/analytics')
    assert res.status_code == 200
    analytics = res.json()
    assert analytics['cluster_id'] == cluster_id
    assert 'active_artisans' in analytics
    assert 'total_catalogue_items' in analytics
    assert 'monthly_sales_inr' in analytics

    # 8. Create Collective RFQ
    rfq_payload = {
        'craft_requirement': 'Bulk Order for Pochampally Ikat Silk Stoles (500 units)',
        'quantity': 500,
        'budget_target': 450000.0
    }
    res = client.post(f'/api/v1/clusters/{cluster_id}/rfqs', json=rfq_payload)
    assert res.status_code in [200, 201]
    rfq = res.json()
    assert rfq['cluster_id'] == cluster_id
    assert rfq['quantity'] == 500
    assert rfq['status'] == 'open'
