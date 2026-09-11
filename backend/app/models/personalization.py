from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class UserBehaviorTrack(BaseModel):
    user_id: str = Field(..., description="Unique buyer or seller ID")
    user_role: str = Field(default="buyer", description="buyer, seller, or both")
    action_type: str = Field(
        ...,
        description="search, click, rfq, chat, order, view, like, filter_region, filter_material, festival_browse"
    )
    search_query: Optional[str] = Field(default=None, description="Search query string if applicable")
    category: Optional[str] = Field(default=None, description="Craft category, e.g. Pottery, Textile, Metal")
    material: Optional[str] = Field(default=None, description="Craft material, e.g. Bamboo, Brass, Silk, Terracotta, Wood")
    region: Optional[str] = Field(default=None, description="State or Cluster region, e.g. Telangana, Rajasthan, Assam")
    festival: Optional[str] = Field(default=None, description="Festival context, e.g. Diwali, Wedding, Pongal, Navratri")
    language: Optional[str] = Field(default="en", description="Preferred interface language, e.g. en, hi, te, ta, bn")
    target_id: Optional[str] = Field(default=None, description="Product ID, Artisan ID, or RFQ ID")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context or telemetry metadata")


class RecommendationWeightsResponse(BaseModel):
    user_id: str
    user_role: str = "buyer"
    category_weights: Dict[str, float] = {}
    material_weights: Dict[str, float] = {}
    region_weights: Dict[str, float] = {}
    festival_weights: Dict[str, float] = {}
    language_preference: str = "en"
    price_affinity_range: Dict[str, float] = {"min": 500.0, "max": 10000.0, "target_avg": 2500.0}
    rfq_intent_score: float = 0.0
    export_intent_score: float = 0.0
    top_preferred_region: Optional[str] = None
    top_preferred_material: Optional[str] = None
    top_preferred_category: Optional[str] = None
    top_preferred_festival: Optional[str] = None
    last_learned_at: str


class DynamicSection(BaseModel):
    id: str
    title: str
    subtitle: str
    widget_type: str = Field(
        ...,
        description="hero_spotlight, carousel, multi_grid, card_banner, rfq_spotlight, seller_showcase"
    )
    badge: Optional[str] = None
    reason: str = Field(..., description="AI explanation of why this section was personalized for user")
    items: List[Dict[str, Any]] = []
    view_all_link: Optional[str] = None
    display_order: int = 1


class PersonalizedLayoutResponse(BaseModel):
    user_id: str
    user_role: str = "buyer"
    persona_summary: str
    layout_version: str = "v2_dynamic"
    sections: List[DynamicSection]
    generated_at: str


class PersonaSimulationRequest(BaseModel):
    persona_type: str = Field(
        ...,
        description="telangana_bamboo_enthusiast, mumbai_wedding_shopper, global_b2b_buyer, varanasi_silk_collector, rajasthan_folk_lover, custom"
    )
    custom_region: Optional[str] = None
    custom_material: Optional[str] = None
    custom_festival: Optional[str] = None
    custom_language: Optional[str] = None
