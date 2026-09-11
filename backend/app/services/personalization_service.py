"""
KalaCart Phase 6 — Personalization Service.

Manages user event telemetry ingestion, stores and syncs recommendation weights in Supabase,
and renders real-time dynamic layouts for buyers and sellers.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from app.models.personalization import (
    UserBehaviorTrack,
    RecommendationWeightsResponse,
    PersonalizedLayoutResponse,
    PersonaSimulationRequest
)
from app.ai.hyper_personalization_engine import HyperPersonalizationEngine, DEFAULT_CRAFT_CATALOG
from app.database.connection import get_supabase_client

logger = logging.getLogger(__name__)

# In-memory storage for high-speed simulation & offline / dev resilience
_MEMORY_BEHAVIOR_STORE: Dict[str, List[UserBehaviorTrack]] = {}
_MEMORY_WEIGHTS_STORE: Dict[str, RecommendationWeightsResponse] = {}

# Standard Predefined Personas for testing & verification
PREDEFINED_PERSONAS = {
    "telangana_bamboo_enthusiast": [
        UserBehaviorTrack(user_id="sim_telangana", action_type="search", search_query="bamboo craft telangana", region="Telangana", material="Bamboo"),
        UserBehaviorTrack(user_id="sim_telangana", action_type="click", category="Bamboo Craft", material="Bamboo", region="Telangana"),
        UserBehaviorTrack(user_id="sim_telangana", action_type="like", category="Bamboo Craft", material="Bamboo", region="Telangana"),
        UserBehaviorTrack(user_id="sim_telangana", action_type="order", category="Bamboo Craft", material="Bamboo", region="Telangana", metadata={"price": 890.0}),
    ],
    "mumbai_wedding_shopper": [
        UserBehaviorTrack(user_id="sim_wedding", action_type="search", search_query="bridal silk saree and kundan jewelry", festival="Wedding", material="Silk"),
        UserBehaviorTrack(user_id="sim_wedding", action_type="filter_material", material="Silk", festival="Wedding"),
        UserBehaviorTrack(user_id="sim_wedding", action_type="like", category="Handloom Silk", festival="Wedding", metadata={"price": 14500.0}),
        UserBehaviorTrack(user_id="sim_wedding", action_type="like", category="Jewelry", material="Silver / Kundan", festival="Wedding", metadata={"price": 6200.0}),
    ],
    "global_b2b_buyer": [
        UserBehaviorTrack(user_id="sim_b2b", action_type="rfq", category="Metal Art", region="Chhattisgarh", metadata={"quantity": 500, "is_export": True, "currency": "USD"}),
        UserBehaviorTrack(user_id="sim_b2b", action_type="chat", target_id="seller_sukhram", metadata={"is_export": True}),
        UserBehaviorTrack(user_id="sim_b2b", action_type="rfq", category="Pottery", region="Rajasthan", metadata={"quantity": 200, "is_export": True}),
    ],
    "varanasi_silk_collector": [
        UserBehaviorTrack(user_id="sim_varanasi", action_type="search", search_query="pure banarasi katan silk", region="Uttar Pradesh", material="Silk"),
        UserBehaviorTrack(user_id="sim_varanasi", action_type="click", category="Handloom Silk", region="Uttar Pradesh"),
        UserBehaviorTrack(user_id="sim_varanasi", action_type="order", category="Handloom Silk", region="Uttar Pradesh", metadata={"price": 12500.0}),
    ],
    "rajasthan_folk_lover": [
        UserBehaviorTrack(user_id="sim_rajasthan", action_type="search", search_query="jaipur blue pottery and kundan", region="Rajasthan", category="Pottery"),
        UserBehaviorTrack(user_id="sim_rajasthan", action_type="click", category="Pottery", material="Quartz Ceramic", region="Rajasthan"),
        UserBehaviorTrack(user_id="sim_rajasthan", action_type="like", category="Jewelry", region="Rajasthan"),
    ]
}


class PersonalizationService:
    """Service orchestrating continuous learning and dynamic layout feeds."""

    @classmethod
    async def record_behavior(cls, event: UserBehaviorTrack) -> Dict[str, Any]:
        """Ingests user behavior event and updates user's affinity profile."""
        if event.user_id not in _MEMORY_BEHAVIOR_STORE:
            _MEMORY_BEHAVIOR_STORE[event.user_id] = []
        _MEMORY_BEHAVIOR_STORE[event.user_id].append(event)

        # Re-learn weights
        weights = HyperPersonalizationEngine.calculate_weights(
            events=_MEMORY_BEHAVIOR_STORE[event.user_id],
            user_id=event.user_id,
            user_role=event.user_role
        )
        _MEMORY_WEIGHTS_STORE[event.user_id] = weights

        # Persist to Supabase if reachable
        try:
            supabase = get_supabase_client()
            supabase.table("user_behavior").insert({
                "user_id": event.user_id,
                "user_role": event.user_role,
                "action_type": event.action_type,
                "search_query": event.search_query,
                "category": event.category,
                "material": event.material,
                "region": event.region,
                "festival": event.festival,
                "language": event.language,
                "target_id": event.target_id,
                "metadata": event.metadata,
            }).execute()

            supabase.table("recommendation_weights").upsert({
                "user_id": weights.user_id,
                "user_role": weights.user_role,
                "category_weights": weights.category_weights,
                "material_weights": weights.material_weights,
                "region_weights": weights.region_weights,
                "festival_weights": weights.festival_weights,
                "language_preference": weights.language_preference,
                "price_affinity_range": weights.price_affinity_range,
                "rfq_intent_score": weights.rfq_intent_score,
                "export_intent_score": weights.export_intent_score,
                "top_preferred_region": weights.top_preferred_region,
                "top_preferred_material": weights.top_preferred_material,
                "top_preferred_category": weights.top_preferred_category,
                "top_preferred_festival": weights.top_preferred_festival,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }).execute()
        except Exception as e:
            logger.debug(f"Async Supabase sync fallback: {e}")

        return {"status": "success", "event_type": event.action_type, "top_category": weights.top_preferred_category}

    @classmethod
    async def get_user_weights(cls, user_id: str, role: str = "buyer") -> RecommendationWeightsResponse:
        """Fetches learned weights for a user, or generates default baseline."""
        if user_id in _MEMORY_WEIGHTS_STORE:
            return _MEMORY_WEIGHTS_STORE[user_id]

        events = _MEMORY_BEHAVIOR_STORE.get(user_id, [])
        weights = HyperPersonalizationEngine.calculate_weights(events=events, user_id=user_id, user_role=role)
        _MEMORY_WEIGHTS_STORE[user_id] = weights
        return weights

    @classmethod
    async def get_personalized_layout(cls, user_id: str, role: str = "buyer") -> PersonalizedLayoutResponse:
        """Generates dynamic non-fixed home layout tailored to user persona."""
        weights = await cls.get_user_weights(user_id, role)
        
        # Load products from catalog
        catalog = DEFAULT_CRAFT_CATALOG
        try:
            supabase = get_supabase_client()
            res = supabase.table("products").select("*").eq("published", True).limit(50).execute()
            if res.data:
                catalog = res.data
        except Exception:
            pass

        layout = HyperPersonalizationEngine.generate_dynamic_layout(
            user_id=user_id,
            weights=weights,
            catalog_products=catalog
        )

        # Cache layout in DB if available
        try:
            supabase = get_supabase_client()
            supabase.table("personalized_layouts").upsert({
                "user_id": user_id,
                "user_role": role,
                "persona_tag": layout.persona_summary,
                "section_order": [s.id for s in layout.sections],
                "widget_configs": [s.dict() for s in layout.sections],
                "generated_at": layout.generated_at,
            }).execute()
        except Exception:
            pass

        return layout

    @classmethod
    async def simulate_persona(cls, req: PersonaSimulationRequest, user_id: str = "simulated_user") -> PersonalizedLayoutResponse:
        """Simulates how a specific buyer persona experiences the home layout."""
        if req.persona_type in PREDEFINED_PERSONAS:
            events = PREDEFINED_PERSONAS[req.persona_type]
        else:
            # Custom persona events
            events = [
                UserBehaviorTrack(
                    user_id=user_id,
                    action_type="search",
                    search_query=f"{req.custom_material or 'craft'} {req.custom_region or 'India'}",
                    region=req.custom_region,
                    material=req.custom_material,
                    festival=req.custom_festival,
                    language=req.custom_language or "en"
                ),
                UserBehaviorTrack(
                    user_id=user_id,
                    action_type="like",
                    region=req.custom_region,
                    material=req.custom_material,
                    festival=req.custom_festival,
                ),
                UserBehaviorTrack(
                    user_id=user_id,
                    action_type="order",
                    region=req.custom_region,
                    material=req.custom_material,
                    festival=req.custom_festival,
                    metadata={"price": 3500.0}
                )
            ]

        weights = HyperPersonalizationEngine.calculate_weights(events=events, user_id=user_id)
        _MEMORY_WEIGHTS_STORE[user_id] = weights
        _MEMORY_BEHAVIOR_STORE[user_id] = events

        return HyperPersonalizationEngine.generate_dynamic_layout(
            user_id=user_id,
            weights=weights,
            catalog_products=DEFAULT_CRAFT_CATALOG
        )
