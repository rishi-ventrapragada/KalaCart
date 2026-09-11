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
        'name': 'Master Artisan Ramesh',
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


def test_craft_passport_and_gi_verification_flow():
    # 1. List GI Crafts
    res = client.get('/api/v1/passports/gi-crafts')
    assert res.status_code == 200
    gi_crafts = res.json()
    assert len(gi_crafts) >= 4
    pochampally = next((c for c in gi_crafts if 'Pochampally' in c['craft_name']), None)
    assert pochampally is not None
    assert pochampally['gi_tag_number'] == 'GI-AP-0004'

    # 2. Filter GI Crafts by state
    res = client.get('/api/v1/passports/gi-crafts?state=Karnataka')
    assert res.status_code == 200
    ka_crafts = res.json()
    assert any('Channapatna' in c['craft_name'] for c in ka_crafts)

    # 3. Create Craft Passport
    passport_payload = {
        'product_id': 'prod-kondapalli-toy-01',
        'gi_tag_number': 'GI-AP-0008',
        'product_title': 'Handcrafted Kondapalli Dasavatara Wooden Toy Set',
        'craft_category': 'Wooden Craft',
        'craft_tradition': 'Kondapalli Softwood Carving with Natural Dyes',
        'village': 'Kondapalli',
        'district': 'NTR District',
        'state': 'Andhra Pradesh',
        'materials': ['Tella Poniki Softwood', 'Tamarind Seed Glue', 'Natural Pigments'],
        'care_instructions': 'Dust with dry microfiber cloth. Keep away from direct water moisture.'
    }
    res = client.post('/api/v1/passports/', json=passport_payload)
    assert res.status_code == 201
    passport = res.json()
    craft_id = passport['craft_id']
    assert craft_id.startswith('KALA-GI-AND-')
    assert passport['certificate_number'].startswith('CERT-GI-')
    assert passport['is_verified'] is True
    assert 'https://kalacart.app/passport/' in passport['verification_url']

    # 4. Get Passport Details
    res = client.get(f'/api/v1/passports/{craft_id}')
    assert res.status_code == 200
    fetched = res.json()
    assert fetched['craft_id'] == craft_id
    assert fetched['product_title'] == passport_payload['product_title']

    # 5. Public Authenticity Verification (from QR scan)
    res = client.get(f'/api/v1/passports/verify/{craft_id}')
    assert res.status_code == 200
    verification = res.json()
    assert verification['is_authentic'] is True
    assert 'GOVERNMENT GI VERIFIED' in verification['status_message']
    assert verification['passport']['craft_id'] == craft_id
    assert verification['gi_craft'] is not None
    assert verification['gi_craft']['gi_tag_number'] == 'GI-AP-0008'
    assert verification['certificate'] is not None
    assert verification['certificate']['certificate_status'] == 'valid'
    assert verification['certificate']['digital_signature_hash'].startswith('SHA256:')

    # 6. Download Official PDF Authenticity Certificate
    res = client.get(f'/api/v1/passports/{craft_id}/certificate/pdf')
    assert res.status_code == 200
    assert res.headers['content-type'] == 'application/pdf'
    assert res.content.startswith(b'%PDF')


def test_artisan_craft_passport_and_trust_score():
    artisan_id = '22222222-2222-2222-2222-222222222222'

    # 1. Create or Update Artisan Digital Passport
    artisan_payload = {
        'photo_url': 'https://images.unsplash.com/photo-1544005313-94ddf0286df2',
        'craft_title': 'Pochampally Handloom Ikat',
        'state': 'Telangana',
        'district': 'Yadadri Bhuvanagiri',
        'years_experience': 15,
        'gi_status': 'Verified',
        'awards': ['National Master Weaver Award 2025', 'State Shilpa Guru'],
        'languages': ['Telugu', 'Hindi', 'English']
    }
    res = client.post('/api/v1/passports/artisan', json=artisan_payload)
    assert res.status_code == 201
    artisan_passport = res.json()
    assert artisan_passport['artisan_id'] == artisan_id
    assert artisan_passport['verified_badge'] is True
    assert artisan_passport['trust_score'] >= 80

    # 2. Fetch Artisan Digital Passport
    res = client.get(f'/api/v1/passports/artisan/{artisan_id}')
    assert res.status_code == 200
    fetched = res.json()
    assert fetched['craft_title'] == 'Pochampally Handloom Ikat'
    assert fetched['years_experience'] == 15
    assert len(fetched['awards']) == 2

    # 3. Dynamic Trust Score Calculation Breakdown
    res = client.get(f'/api/v1/passports/trust-score/{artisan_id}')
    assert res.status_code == 200
    trust_breakdown = res.json()
    assert trust_breakdown['trust_score'] >= 0 and trust_breakdown['trust_score'] <= 100
    assert 'orders_score' in trust_breakdown
    assert 'reviews_score' in trust_breakdown
    assert 'fulfillment_rate' in trust_breakdown
    assert trust_breakdown['is_verified'] is True

    # 4. Submit GI Certificate
    cert_payload = {
        'craft_name': 'Pochampally Ikat',
        'gi_tag_number': 'GI-AP-0004',
        'certificate_url': 'https://storage.kalacart.app/certificates/pochampally_gi.pdf',
        'issuing_authority': 'Geographical Indications Registry of India'
    }
    res = client.post('/api/v1/passports/gi-certificate', json=cert_payload)
    assert res.status_code == 201
    cert_data = res.json()
    assert cert_data['gi_tag_number'] == 'GI-AP-0004'
    assert cert_data['is_valid'] is True
