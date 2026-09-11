import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import get_current_user

client = TestClient(app)

BUYER_USER = {
    'firebase_uid': 'uid_buyer_1',
    'phone': '+919876543210',
    'artisan': {
        'id': '11111111-1111-1111-1111-111111111111',
        'name': 'Meera Buyer',
        'phone': '+919876543210',
        'firebase_uid': 'uid_buyer_1',
    },
    'claims': {'uid': 'uid_buyer_1'},
}

@pytest.fixture(autouse=True)
def override_user():
    app.dependency_overrides[get_current_user] = lambda: BUYER_USER
    yield
    app.dependency_overrides.pop(get_current_user, None)

def test_order_lifecycle():
    headers = {'Authorization': 'Bearer mock_token'}
    payload = {
        'buyer_name': 'Meera Sharma',
        'buyer_phone': '+919876543210',
        'buyer_email': 'meera@example.com',
        'seller_name': 'Ramesh Kumar',
        'seller_phone': '+919811223344',
        'delivery_address': '42 MG Road, Bangalore, KA 560001',
        'shipping_address': '12 Clay Studio, Jaipur, RJ 302001',
        'artisan_id': '22222222-2222-2222-2222-222222222222',
        'quantity': 10,
        'unit_price': 500.0,
        'product_title': 'Handmade Blue Pottery Vase',
        'advance_percentage': 30.0,
        'shipping_charges': 250.0
    }
    
    # 1. Create order
    res = client.post('/api/v1/orders', json=payload, headers=headers)
    assert res.status_code == 201, res.text
    order = res.json()
    order_id = order['id']
    assert order['status'] == 'rfq_accepted'
    assert order['subtotal'] == 5000.0
    assert order['gst_amount'] == 900.0
    assert order['total_amount'] == 6150.0
    assert order['advance_amount'] == 1845.0
    assert order['remaining_balance'] == 4305.0
    assert len(order['items']) == 1
    assert len(order['status_history']) == 1
    assert order['invoice'] is not None

    # 2. Get list of orders
    list_res = client.get('/api/v1/orders', headers=headers)
    assert list_res.status_code == 200
    assert any(o['id'] == order_id for o in list_res.json())

    # 3. Transition: rfq_accepted -> pending_advance
    t1 = client.patch(f'/api/v1/orders/{order_id}/status', json={'status': 'pending_advance'}, headers=headers)
    assert t1.status_code == 200
    assert t1.json()['status'] == 'pending_advance'

    # 4. Transition: pending_advance -> seller_accepted
    t2 = client.patch(f'/api/v1/orders/{order_id}/status', json={'status': 'seller_accepted'}, headers=headers)
    assert t2.status_code == 200
    assert t2.json()['status'] == 'seller_accepted'
    assert t2.json()['advance_paid'] is True

    # 5. Transition: seller_accepted -> in_production
    t3 = client.patch(f'/api/v1/orders/{order_id}/status', json={'status': 'in_production'}, headers=headers)
    assert t3.status_code == 200
    assert t3.json()['status'] == 'in_production'

    # 6. Fetch invoice metadata and PDF
    inv_res = client.get(f'/api/v1/orders/{order_id}/invoice', headers=headers)
    assert inv_res.status_code == 200
    assert inv_res.json()['order_id'] == order_id

    pdf_res = client.get(f'/api/v1/orders/{order_id}/invoice/pdf', headers=headers)
    assert pdf_res.status_code == 200
    assert pdf_res.headers['content-type'] == 'application/pdf'
    assert len(pdf_res.content) > 500
