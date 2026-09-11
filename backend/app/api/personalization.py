"""
KalaCart Phase 6 — Hyper-Personalization Engine API.

Endpoints:
- POST /api/v1/personalization/track
- GET  /api/v1/personalization/weights/{user_id}
- GET  /api/v1/personalization/home-layout
- POST /api/v1/personalization/simulate-persona
- GET  /api/v1/personalization/personas
"""

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query, status

from app.models.personalization import (
    UserBehaviorTrack,
    RecommendationWeightsResponse,
    PersonalizedLayoutResponse,
    PersonaSimulationRequest
)
from app.services.personalization_service import PersonalizationService, PREDEFINED_PERSONAS

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/track", status_code=status.HTTP_200_OK)
async def track_behavior(event: UserBehaviorTrack) -> Dict[str, Any]:
    """
    Ingests granular user interaction telemetry:
    (search, click, rfq, chat, order, view, like, filter_region, filter_material, festival_browse)
    and updates affinity weights continuously.
    """
    return await PersonalizationService.record_behavior(event)


@router.get("/weights/{user_id}", response_model=RecommendationWeightsResponse)
async def get_user_weights(
    user_id: str,
    role: str = Query("buyer", description="buyer, seller, or both")
) -> RecommendationWeightsResponse:
    """
    Returns learned multi-dimensional preference weights for a given user.
    """
    return await PersonalizationService.get_user_weights(user_id=user_id, role=role)


@router.get("/home-layout", response_model=PersonalizedLayoutResponse)
async def get_personalized_home_layout(
    user_id: str = Query("default_guest", description="Unique user or guest ID"),
    role: str = Query("buyer", description="buyer or seller")
) -> PersonalizedLayoutResponse:
    """
    Renders completely personalized dynamic home layout with custom AI widgets,
    re-arranged sections, and contextual categories (e.g. Telangana crafts, Bamboo recommendations, Wedding curation).
    """
    return await PersonalizationService.get_personalized_layout(user_id=user_id, role=role)


@router.post("/simulate-persona", response_model=PersonalizedLayoutResponse)
async def simulate_persona(
    req: PersonaSimulationRequest,
    user_id: str = Query("sim_user_active", description="User ID for simulation")
) -> PersonalizedLayoutResponse:
    """
    Simulates home feed layouts under distinct personas
    (e.g., telangana_bamboo_enthusiast vs mumbai_wedding_shopper vs global_b2b_buyer).
    """
    return await PersonalizationService.simulate_persona(req=req, user_id=user_id)


@router.get("/personas")
async def list_available_personas() -> Dict[str, Any]:
    """
    Lists predefined personas for sandbox demonstration and testing.
    """
    return {
        "personas": [
            {
                "id": "telangana_bamboo_enthusiast",
                "label": "Telangana Bamboo Enthusiast",
                "description": "Prefers Telangana GI crafts, eco-friendly bamboo planters, and local master weavers."
            },
            {
                "id": "mumbai_wedding_shopper",
                "label": "Mumbai Wedding & Bridal Shopper",
                "description": "Looking for bridal Banarasi silk lehengas, Kundan jewelry, and luxury wedding hampers."
            },
            {
                "id": "global_b2b_buyer",
                "label": "Global B2B Wholesale Importer",
                "description": "Submits high-volume RFQs for Bell Metal Dokra and Jaipur ceramics for international export."
            },
            {
                "id": "varanasi_silk_collector",
                "label": "Varanasi Silk Connoisseur",
                "description": "Heirloom collector focusing exclusively on Varanasi handloom silks and zari artistry."
            },
            {
                "id": "rajasthan_folk_lover",
                "label": "Rajasthan Folk & Pottery Collector",
                "description": "Passionate about Jaipur Blue Pottery, Sanganeri prints, and royal craft traditions."
            }
        ]
    }
