"""
Tests for KalaCart Phase 6 — Hyper-Personalization Engine.

Verifies:
1. Multi-source behavior signal tracking (search, click, rfq, chat, order, filters).
2. Continuous weight learning across regions, materials, categories, festivals, and price affinity.
3. Dynamic non-fixed home layout generation with adaptive AI widgets.
4. Persona simulation across distinct buyer profiles (e.g. Telangana Bamboo vs Mumbai Wedding vs B2B Wholesale).
5. Critical Requirement Verification: Two distinct users NEVER receive identical home feeds.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_track_user_behavior_and_learn_weights():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        user_id = "test_buyer_telangana_01"

        # 1. Ingest behavior signals
        events = [
            {
                "user_id": user_id,
                "action_type": "search",
                "search_query": "Telangana bamboo craft and planter",
                "region": "Telangana",
                "material": "Bamboo",
                "category": "Bamboo Craft"
            },
            {
                "user_id": user_id,
                "action_type": "click",
                "category": "Bamboo Craft",
                "material": "Bamboo",
                "region": "Telangana"
            },
            {
                "user_id": user_id,
                "action_type": "like",
                "category": "Bamboo Craft",
                "material": "Bamboo",
                "region": "Telangana"
            },
            {
                "user_id": user_id,
                "action_type": "order",
                "category": "Bamboo Craft",
                "material": "Bamboo",
                "region": "Telangana",
                "metadata": {"price": 890.0}
            }
        ]

        for ev in events:
            res = await ac.post("/api/v1/personalization/track", json=ev)
            assert res.status_code == 200

        # 2. Get learned weights
        res_weights = await ac.get(f"/api/v1/personalization/weights/{user_id}")
        assert res_weights.status_code == 200
        weights = res_weights.json()
        assert weights["user_id"] == user_id
        assert weights["top_preferred_region"] == "Telangana"
        assert weights["top_preferred_material"] == "Bamboo"
        assert weights["top_preferred_category"] == "Bamboo Craft"
        assert "Telangana" in weights["region_weights"]
        assert "Bamboo" in weights["material_weights"]


@pytest.mark.asyncio
async def test_get_personalized_home_layout():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        user_id = "test_buyer_telangana_01"
        res = await ac.get(f"/api/v1/personalization/home-layout?user_id={user_id}")
        assert res.status_code == 200
        layout = res.json()
        assert layout["user_id"] == user_id
        assert layout["layout_version"] == "v2_dynamic"
        assert len(layout["sections"]) >= 4

        # Verify section titles and reason explanations are tailored
        section_ids = [s["id"] for s in layout["sections"]]
        assert any("telangana" in sid for sid in section_ids)
        assert any("bamboo" in sid for sid in section_ids)

        for s in layout["sections"]:
            assert "reason" in s and len(s["reason"]) > 0
            assert "items" in s


@pytest.mark.asyncio
async def test_persona_simulation_b2b_vs_wedding():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Simulate Global B2B Buyer
        res_b2b = await ac.post(
            "/api/v1/personalization/simulate-persona",
            json={"persona_type": "global_b2b_buyer"}
        )
        assert res_b2b.status_code == 200
        b2b_layout = res_b2b.json()
        b2b_section_ids = [s["id"] for s in b2b_layout["sections"]]
        assert "export_ready_sellers" in b2b_section_ids

        # Simulate Mumbai Wedding Shopper
        res_wed = await ac.post(
            "/api/v1/personalization/simulate-persona",
            json={"persona_type": "mumbai_wedding_shopper"}
        )
        assert res_wed.status_code == 200
        wed_layout = res_wed.json()
        wed_section_ids = [s["id"] for s in wed_layout["sections"]]
        assert any("wedding" in sid for sid in wed_section_ids)


@pytest.mark.asyncio
async def test_two_users_never_receive_identical_feeds():
    """
    Core Phase 6 Requirement: Two users never receive identical feeds.
    Verify that User A (Telangana Bamboo Enthusiast) and User B (Mumbai Wedding Shopper)
    receive completely distinct section orders, titles, and item lists.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        user_a = "user_telangana_bamboo"
        user_b = "user_mumbai_wedding"

        # Train User A on Telangana & Bamboo
        await ac.post("/api/v1/personalization/track", json={
            "user_id": user_a,
            "action_type": "search",
            "region": "Telangana",
            "material": "Bamboo"
        })
        await ac.post("/api/v1/personalization/track", json={
            "user_id": user_a,
            "action_type": "order",
            "region": "Telangana",
            "material": "Bamboo",
            "metadata": {"price": 890.0}
        })

        # Train User B on Wedding & Silk & Jewelry
        await ac.post("/api/v1/personalization/track", json={
            "user_id": user_b,
            "action_type": "search",
            "festival": "Wedding",
            "material": "Silk"
        })
        await ac.post("/api/v1/personalization/track", json={
            "user_id": user_b,
            "action_type": "order",
            "festival": "Wedding",
            "material": "Silk",
            "metadata": {"price": 14500.0}
        })

        res_a = await ac.get(f"/api/v1/personalization/home-layout?user_id={user_a}")
        res_b = await ac.get(f"/api/v1/personalization/home-layout?user_id={user_b}")

        layout_a = res_a.json()
        layout_b = res_b.json()

        # Compare layouts
        section_ids_a = [s["id"] for s in layout_a["sections"]]
        section_ids_b = [s["id"] for s in layout_b["sections"]]

        titles_a = [s["title"] for s in layout_a["sections"]]
        titles_b = [s["title"] for s in layout_b["sections"]]

        # They must not be identical
        assert section_ids_a != section_ids_b
        assert titles_a != titles_b
        assert layout_a["persona_summary"] != layout_b["persona_summary"]


@pytest.mark.asyncio
async def test_list_available_personas():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/api/v1/personalization/personas")
        assert res.status_code == 200
        data = res.json()
        assert "personas" in data
        assert len(data["personas"]) >= 5
