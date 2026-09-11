import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_storefront_theme_list():
    res = client.get('/api/v1/storefront/themes')
    assert res.status_code == 200
    themes = res.json()
    assert len(themes) >= 3
    theme_keys = [t['theme_key'] for t in themes]
    assert 'heritage' in theme_keys
    assert 'modern' in theme_keys
    assert 'classic' in theme_keys


def test_public_mini_website_generation():
    res = client.get('/store/raj-pottery')
    assert res.status_code == 200
    data = res.json()

    # 1. Storefront & Branding
    assert 'storefront' in data
    assert data['storefront']['slug'] == 'raj-pottery'
    assert 'Raj Blue Pottery' in data['storefront']['store_name']
    assert 'kalacart.shop/store/raj-pottery' in data['storefront']['store_url']

    # 2. Hero, Products & Reviews
    assert 'products' in data
    assert len(data['products']) >= 2
    assert 'featured_products' in data
    assert 'ratings' in data
    assert data['ratings']['average_rating'] >= 4.0

    # 3. SEO & Structured Data
    assert 'seo' in data
    seo = data['seo']
    assert 'Raj Blue Pottery' in seo['meta_title']
    assert 'structured_schema' in seo
    assert seo['structured_schema']['@type'] == 'Store'

    # 4. Themes & Colors
    assert 'theme' in data
    assert data['theme']['theme_key'] == 'heritage'

    # 5. Contact, Map & Social Share Links
    assert 'contact' in data
    assert 'map_location' in data
    assert 'share_links' in data
    assert 'whatsapp' in data['share_links']
    assert 'facebook' in data['share_links']
    assert 'copy_link' in data['share_links']


def test_storefront_qr_endpoint():
    res = client.get('/store/raj-pottery/qr')
    assert res.status_code == 200
    assert res.headers['content-type'] in ['image/png', 'image/svg+xml']
