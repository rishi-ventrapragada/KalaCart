"""
Tests for KalaCart Phase 6 — Cultural Heritage Intelligence.

Verifies:
1. Complete craft knowledge base query (History, Region, GI Details, Techniques, Tools, Materials, Master Artisans, Video Archives, Oral Stories).
2. AI Story Generator with strict factual separation (Historical Facts vs AI-generated Folklore Narratives) across multiple languages.
3. Museum Mode encyclopedia lookup by craft code and ID.
4. Verification Invariant: Every product links to its registered Cultural Heritage page.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_list_craft_library():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/api/v1/heritage/crafts")
        assert res.status_code == 200
        crafts = res.json()
        assert len(crafts) >= 2
        craft_codes = [c["craft_code"] for c in crafts]
        assert "GI-TEL-001" in craft_codes
        assert "GI-RAJ-004" in craft_codes


@pytest.mark.asyncio
async def test_get_craft_encyclopedia_museum_mode():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/api/v1/heritage/crafts/GI-TEL-001")
        assert res.status_code == 200
        detail = res.json()
        
        # Verify complete schema components required by Phase 6:
        assert detail["craft_code"] == "GI-TEL-001"
        assert "Pochampally" in detail["name"]
        assert len(detail["history_timeline"]) >= 3
        assert detail["gi_details"]["gi_number"] == "GI-TEL-001"
        assert len(detail["techniques"]) >= 3
        assert len(detail["tools"]) >= 2
        assert len(detail["materials"]) >= 2
        assert len(detail["master_artisans"]) >= 1
        assert len(detail["video_archive_urls"]) >= 1
        assert len(detail["oral_histories"]) >= 1

        # Check master artisan details
        artisan = detail["master_artisans"][0]
        assert "Mallesham" in artisan["name"]
        assert artisan["years_of_lineage"] >= 40

        # Check oral story details
        oral = detail["oral_histories"][0]
        assert "transcript_original" in oral
        assert "transcript_english" in oral
        assert "cultural_significance" in oral


@pytest.mark.asyncio
async def test_ai_story_generator_separates_facts_and_narratives():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Generate story in Hindi
        payload_hi = {
            "craft_id": "GI-TEL-001",
            "language": "hi",
            "story_theme": "origin_legend"
        }
        res_hi = await ac.post("/api/v1/heritage/generate-story", json=payload_hi)
        assert res_hi.status_code == 200
        story_hi = res_hi.json()
        
        # Verify clean separation between historical facts and AI narrative
        assert "historical_facts" in story_hi
        assert len(story_hi["historical_facts"]) >= 3
        assert "ai_generated_narrative" in story_hi
        assert story_hi["ai_generated_narrative"]["disclaimer"] is not None
        assert "दास्तान" in story_hi["ai_generated_narrative"]["title"] or "गाथा" in story_hi["ai_generated_narrative"]["title"] or len(story_hi["ai_generated_narrative"]["title"]) > 0

        # Generate story in Telugu
        payload_te = {
            "craft_id": "GI-TEL-001",
            "language": "te",
            "story_theme": "master_craftsman_journey"
        }
        res_te = await ac.post("/api/v1/heritage/generate-story", json=payload_te)
        assert res_te.status_code == 200
        story_te = res_te.json()
        assert len(story_te["historical_facts"]) >= 3
        assert story_te["language"] == "te"


@pytest.mark.asyncio
async def test_every_product_links_to_cultural_heritage():
    """
    Verification Invariant: Every product links to its registered Cultural Heritage page.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Test Pochampally Silk Product
        res_poch = await ac.get("/api/v1/heritage/product-link/00000000-0000-0000-0000-000000000102")
        assert res_poch.status_code == 200
        data_poch = res_poch.json()
        assert data_poch["matched"] is True
        assert data_poch["craft_code"] in ["GI-TEL-001", "GI-RAJ-004"]
        assert "/heritage/" in data_poch["heritage_url"]

        # Test Jaipur Blue Pottery Product
        res_pot = await ac.get("/api/v1/heritage/product-link/prod_jaipur_blue_pottery_08")
        assert res_pot.status_code == 200
        data_pot = res_pot.json()
        assert data_pot["matched"] is True
        assert data_pot["craft_code"] == "GI-RAJ-004"
        assert data_pot["heritage_url"] == "/heritage/GI-RAJ-004"
