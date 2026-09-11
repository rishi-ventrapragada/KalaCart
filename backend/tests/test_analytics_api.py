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

def test_get_business_analytics_structure():
    res = client.get('/api/v1/analytics/business')
    assert res.status_code == 200
    data = res.json()
    assert data['success'] is True
    dash = data['data']
    
    assert 'metrics' in dash
    assert 'daily_sales' in dash
    assert 'monthly_revenue' in dash
    assert 'top_products' in dash
    assert 'category_performance' in dash
    assert 'insights' in dash
    assert 'has_sufficient_data' in dash

    metrics = dash['metrics']
    for req_field in ['revenue', 'orders', 'average_order_value', 'profit', 'expenses', 'conversion_rate', 'repeat_buyers_percentage']:
        assert req_field in metrics, f'Missing metric {req_field}'

    insights = dash['insights']
    for insight_field in ['best_selling_category', 'products_to_restock', 'slow_moving_inventory', 'highest_profit_product']:
        assert insight_field in insights, f'Missing insight {insight_field}'

    assert len(dash['daily_sales']) == 7
    assert len(dash['monthly_revenue']) == 6


def test_get_market_intelligence_dashboard():
    res = client.get('/api/v1/analytics/market-intelligence/dashboard')
    assert res.status_code == 200
    res_data = res.json()
    assert res_data['success'] is True
    dash = res_data['data']
    assert 'summary_reports' in dash
    assert 'trending_crafts' in dash
    assert 'city_demand_matrix' in dash
    assert 'export_opportunities' in dash
    assert 'ai_insights' in dash
    assert len(dash['trending_crafts']) > 0
    assert len(dash['city_demand_matrix']) > 0
    assert len(dash['ai_insights']) > 0


def test_get_craft_trends():
    res = client.get('/api/v1/analytics/market-intelligence/trends')
    assert res.status_code == 200
    res_data = res.json()
    assert res_data['success'] is True
    data = res_data['data']
    assert isinstance(data, list)
    assert any(item['craft_name'] == 'Jaipur Blue Pottery' for item in data)
    assert any('growth_rate_pct' in item for item in data)


def test_get_city_demand():
    res = client.get('/api/v1/analytics/market-intelligence/city-demand')
    assert res.status_code == 200
    res_data = res.json()
    assert res_data['success'] is True
    data = res_data['data']
    assert isinstance(data, list)
    assert any(item['city_name'] == 'Bengaluru' for item in data)
    assert any(item['demand_index'] > 80 for item in data)
    assert any(item['growth_yoy_pct'] > 0 for item in data)



def test_get_export_opportunities():
    res = client.get('/api/v1/analytics/market-intelligence/export-opportunities')
    assert res.status_code == 200
    res_data = res.json()
    assert res_data['success'] is True
    data = res_data['data']
    assert isinstance(data, list)
    assert len(data) > 0
    assert any('target_country' in item for item in data)


def test_get_export_readiness():
    res = client.get('/api/v1/analytics/market-intelligence/export-readiness/00000000-0000-0000-0000-000000000002')
    assert res.status_code == 200
    res_data = res.json()
    assert res_data['success'] is True
    data = res_data['data']
    assert data['overall_readiness_score'] >= 0
    assert 'readiness_tier' in data
    assert 'actionable_checkpoints' in data
    assert len(data['actionable_checkpoints']) > 0


def test_get_ai_insights():
    res = client.get('/api/v1/analytics/market-intelligence/ai-insights')
    assert res.status_code == 200
    res_data = res.json()
    assert res_data['success'] is True
    data = res_data['data']
    assert isinstance(data, list)
    assert any('Bamboo' in item['headline'] or 'Pottery' in item['craft'] for item in data)


