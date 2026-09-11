import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_list_museum_collections():
    """Verify exhibition collections listing."""
    response = client.get("/api/v1/museum/collections")
    assert response.status_code == 200
    cols = response.json()
    assert len(cols) >= 2
    assert any("Sacred Bronzes" in c["title"] for c in cols)
    assert any("Royal Looms" in c["title"] for c in cols)


def test_get_single_museum_collection():
    """Verify single collection retrieval with gallery halls."""
    response = client.get("/api/v1/museum/collections/coll-sacred-metals")
    assert response.status_code == 200
    col = response.json()
    assert col["collection_code"] == "COL-METALS"
    assert len(col["gallery_rooms"]) >= 1


def test_list_gallery_rooms():
    """Verify 360° virtual gallery halls listing."""
    response = client.get("/api/v1/museum/galleries")
    assert response.status_code == 200
    rooms = response.json()
    assert len(rooms) >= 4
    assert any(r["room_code"] == "ROOM-BASTAR" for r in rooms)
    assert any(r["room_code"] == "ROOM-KASHMIR" for r in rooms)


def test_get_gallery_room():
    """Verify virtual room detail with 360 panorama and ambient audio."""
    response = client.get("/api/v1/museum/galleries/room-bastar-tribal")
    assert response.status_code == 200
    room = response.json()
    assert room["room_name"] == "Bastar Sacred Bronze & Forest Foundry"
    assert "panorama_360_url" in room
    assert len(room["artifacts"]) >= 1


def test_list_and_filter_artifacts():
    """Verify 3D artifacts filtering by region and craft category."""
    # List all
    response = client.get("/api/v1/museum/artifacts")
    assert response.status_code == 200
    artifacts = response.json()
    assert len(artifacts) >= 4

    # Filter by state
    gujarat_res = client.get("/api/v1/museum/artifacts?state=Gujarat")
    assert gujarat_res.status_code == 200
    guj_artifacts = gujarat_res.json()
    assert len(guj_artifacts) == 1
    assert guj_artifacts[0]["origin_district"] == "Kachchh"


def test_get_museum_artifact_detail():
    """Verify full deep view of 3D artifact with master lineage and materials."""
    response = client.get("/api/v1/museum/artifacts/art-dhokra-001")
    assert response.status_code == 200
    art = response.json()
    assert art["artifact_code"] == "KC-MUS-DHK-001"
    assert art["model_3d_glb_url"].endswith(".glb")
    assert art["xr_ar_supported"] is True
    assert art["artisan_details"]["name"] == "Sukmati Mandavi"
    assert art["artisan_details"]["generation"] == 5


def test_get_multilingual_audio_guides():
    """Verify multilingual narration audio tracks."""
    response = client.get("/api/v1/museum/audio-guides/art-dhokra-001")
    assert response.status_code == 200
    guides = response.json()
    assert len(guides) >= 3
    languages = [g["language_code"] for g in guides]
    assert "en" in languages
    assert "hi" in languages
    assert "bn" in languages

    # Filter single language
    hi_res = client.get("/api/v1/museum/audio-guides/art-dhokra-001?language_code=hi")
    assert hi_res.status_code == 200
    hi_guides = hi_res.json()
    assert len(hi_guides) == 1
    assert hi_guides[0]["language_code"] == "hi"


def test_get_craft_historical_timeline():
    """Verify craft timeline milestones from ancient to modern eras."""
    response = client.get("/api/v1/museum/timelines/DHOKRA")
    assert response.status_code == 200
    timeline = response.json()
    assert len(timeline) >= 3
    assert timeline[0]["era"] == "Harappan Bronze Age"
    assert "Mohenjo-daro" in timeline[0]["description"]


def test_get_xr_session():
    """Verify WebXR / AR QuickLook inspection parameters."""
    response = client.get("/api/v1/museum/xr-session/art-pashmina-002")
    assert response.status_code == 200
    session = response.json()
    assert session["artifact_id"] == "art-pashmina-002"
    assert session["ar_placement_mode"] == "surface_horizontal"
    assert "model_3d_glb_url" in session


def test_bidirectional_marketplace_cross_linking():
    """Verify seamless bidirectional cross-linking between products and museum artifacts."""
    # 1. From Museum Artifact -> Marketplace Products
    art_res = client.get("/api/v1/museum/cross-link/artifact/art-ajrakh-003")
    assert art_res.status_code == 200
    art_cross = art_res.json()
    assert len(art_cross["linked_marketplace_products"]) >= 2
    assert "Ajrakh" in art_cross["artifact_title"]

    # 2. From Marketplace Product -> Museum Heritage Archive
    prod_res = client.get("/api/v1/museum/cross-link/product/prod-kashmiri-pashmina-shawl-09")
    assert prod_res.status_code == 200
    prod_cross = prod_res.json()
    assert prod_cross["museum_heritage_verified"] is True
    assert prod_cross["matched_museum_artifact"]["artifact_code"] == "KC-MUS-PSH-002"
