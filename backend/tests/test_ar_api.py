from fastapi.testclient import TestClient
import pytest
from app.main import app
from app.core.security import get_current_user

@pytest.fixture(autouse=True)
def override_auth():
    app.dependency_overrides[get_current_user] = lambda: {
        "uid": "artisan-raghurajpur-001",
        "email": "laxman.patachitra@odisha.in",
        "name": "Laxman Maharana",
        "role": "seller"
    }
    yield
    app.dependency_overrides.clear()

def test_get_product_3d_model():
    client = TestClient(app)

    prod_id = "prod-dhokra-brass-statue"
    res = client.get(f"/api/v1/ar/products/{prod_id}/model")
    assert res.status_code == 200, res.text
    model = res.json()
    assert model["product_id"] == prod_id
    assert model["model_format"] == "glb"
    assert model["is_ar_ready"] is True
    assert model["has_pbr_materials"] is True
    assert model["dimensions"]["height_cm"] == 35.0
    assert model["usdz_quicklook_url"] is not None

def test_generate_3d_preview_from_photos():
    client = TestClient(app)

    prod_id = "prod-blue-pottery-vase-01"
    gen_req = {
        "multi_angle_photo_urls": [
            "https://storage.kalacart.in/samples/vase_front.jpg",
            "https://storage.kalacart.in/samples/vase_right.jpg",
            "https://storage.kalacart.in/samples/vase_back.jpg",
            "https://storage.kalacart.in/samples/vase_left.jpg",
            "https://storage.kalacart.in/samples/vase_top.jpg"
        ],
        "length_cm": 20.0,
        "width_cm": 20.0,
        "height_cm": 30.0,
        "lighting_preset": "studio",
        "scale_reference": "coffee_table"
    }

    res = client.post(f"/api/v1/ar/products/{prod_id}/generate-3d", json=gen_req)
    assert res.status_code == 201, res.text
    data = res.json()
    assert data["product_id"] == prod_id
    assert data["synthesis_status"] == "completed"
    assert data["model_glb_url"].endswith(".glb")
    assert data["model_usdz_url"].endswith(".usdz")
    assert data["file_size_mb"] < 5.0
    assert len(data["turntable_frames_urls"]) == 16

def test_ar_capability_check_and_fallback():
    client = TestClient(app)

    # 1. Android Chrome Client -> Native ARCore
    res_android = client.get(
        "/api/v1/ar/capability-check?product_id=prod-pottery-01",
        headers={"user-agent": "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Mobile Safari/537.36"}
    )
    assert res_android.status_code == 200
    data_android = res_android.json()
    assert data_android["supports_native_arcore"] is True
    assert data_android["recommended_viewer_mode"] == "arcore_native"

    # 2. Desktop Windows Client -> Fallback to 360 Turntable Viewer
    res_desktop = client.get(
        "/api/v1/ar/capability-check?product_id=prod-pottery-01",
        headers={"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0"}
    )
    assert res_desktop.status_code == 200
    data_desktop = res_desktop.json()
    assert data_desktop["recommended_viewer_mode"] == "turntable_360"
    assert len(data_desktop["fallback_turntable_frames_urls"]) == 16
