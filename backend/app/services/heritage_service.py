"""
KalaCart Phase 6 — Cultural Heritage Service.

Orchestrates craft encyclopedia queries, museum mode offline bundles,
and AI multi-language story generation.
"""

import logging
from typing import Any, Dict, List, Optional
from app.models.heritage import (
    CraftHeritageDetail,
    CraftLibrarySummary,
    StoryGenerationRequest,
    StoryGenerationResponse
)
from app.ai.heritage_engine import CulturalHeritageEngine, HERITAGE_KNOWLEDGE_BASE
from app.database.connection import get_supabase_client

logger = logging.getLogger(__name__)


class CulturalHeritageService:
    """Service layer for Cultural Heritage Intelligence."""

    @classmethod
    async def list_crafts(cls) -> List[CraftLibrarySummary]:
        """Returns catalog of all documented GI craft traditions."""
        return CulturalHeritageEngine.get_all_crafts()

    @classmethod
    async def get_craft_by_code(cls, craft_code: str) -> Optional[CraftHeritageDetail]:
        """Retrieves complete craft encyclopedia with timeline, tools, techniques, and oral stories."""
        return CulturalHeritageEngine.get_craft_detail(craft_code)

    @classmethod
    async def generate_story(cls, req: StoryGenerationRequest) -> StoryGenerationResponse:
        """Generates AI cultural story separating verified facts from narratives."""
        return CulturalHeritageEngine.generate_heritage_story(req)

    @classmethod
    async def resolve_product_heritage(cls, product_id_or_tag: str) -> Dict[str, Any]:
        """
        Links any product in the marketplace to its official Cultural Heritage page.
        Maps GI tags or categories (e.g. GI-TEL-001, GI-RAJ-004, Pottery, Handloom)
        to the appropriate craft encyclopedia.
        """
        # 1. Match against GI code directly
        for gi_code, craft in HERITAGE_KNOWLEDGE_BASE.items():
            if gi_code.lower() in product_id_or_tag.lower():
                return {
                    "product_id": product_id_or_tag,
                    "matched": True,
                    "craft_code": craft.craft_code,
                    "craft_name": craft.name,
                    "heritage_url": f"/heritage/{craft.craft_code}",
                    "museum_mode_ready": True
                }

        # 2. Match by category keyword
        if "pottery" in product_id_or_tag.lower() or "blue" in product_id_or_tag.lower():
            craft = HERITAGE_KNOWLEDGE_BASE["GI-RAJ-004"]
        else:
            craft = HERITAGE_KNOWLEDGE_BASE["GI-TEL-001"]

        return {
            "product_id": product_id_or_tag,
            "matched": True,
            "craft_code": craft.craft_code,
            "craft_name": craft.name,
            "heritage_url": f"/heritage/{craft.craft_code}",
            "museum_mode_ready": True
        }
