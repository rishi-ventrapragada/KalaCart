from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class AudioGuide(BaseModel):
    id: str
    artifact_id: str
    language_code: str = "en"
    language_name: str = "English"
    narrator_name: str
    narration_title: str
    transcript: str
    audio_stream_url: str
    duration_seconds: int = 95
    is_master_artisan_voice: bool = False


class CraftTimelineEvent(BaseModel):
    era: str
    approximate_year: str
    title: str
    description: str
    dynasty_or_patron: Optional[str] = None
    innovation: Optional[str] = None


class MasterArtisanBio(BaseModel):
    name: str
    generation: int
    birthplace: str
    active_years: str
    awards: List[str]
    quote: str
    photograph_url: Optional[str] = None
    heritage_lineage: str


class MuseumArtifact(BaseModel):
    id: str
    collection_id: Optional[str] = None
    gallery_room_id: Optional[str] = None
    artifact_code: str
    title: str
    craft_category: str
    origin_district: str
    origin_state: str
    historical_period: str
    estimated_creation_year: Optional[str] = None
    medium_and_materials: str
    dimension_specs: Optional[str] = None
    description: str
    historical_significance: str
    master_artisan_name: Optional[str] = None
    master_artisan_bio: Optional[str] = None
    master_artisan_awards: List[str] = []
    model_3d_glb_url: str
    model_3d_usdz_url: Optional[str] = None
    thumbnail_image_url: str
    multi_angle_images: List[str] = []
    xr_ar_supported: bool = True
    gi_tag_registered: bool = True
    preservation_status: str = "Pristine Heritage"
    linked_product_ids: List[str] = []
    audio_guides: List[AudioGuide] = []
    timeline: List[CraftTimelineEvent] = []
    artisan_details: Optional[MasterArtisanBio] = None


class GalleryRoom(BaseModel):
    id: str
    collection_id: str
    room_code: str
    room_name: str
    architectural_theme: str
    panorama_360_url: str
    ambient_audio_url: Optional[str] = None
    lighting_preset: str = "GoldenHourWarmth"
    virtual_hall_capacity: int = 500
    artifacts_count: int = 0
    artifacts: List[MuseumArtifact] = []


class MuseumCollection(BaseModel):
    id: str
    collection_code: str
    title: str
    subtitle: Optional[str] = None
    description: str
    curator_name: str = "KalaCart Heritage Trust"
    cover_image_url: str
    banner_image_url: Optional[str] = None
    historical_era: str = "Ancient to Modern"
    display_order: int = 1
    is_featured: bool = True
    artifact_count: int = 0
    gallery_rooms: List[GalleryRoom] = []


class MuseumCrossLinkResponse(BaseModel):
    artifact_id: str
    artifact_title: str
    craft_category: str
    origin_district: str
    origin_state: str
    linked_marketplace_products: List[Dict[str, Any]]
    educational_note: str


class XRArtifactSessionResponse(BaseModel):
    artifact_id: str
    title: str
    model_3d_glb_url: str
    model_3d_usdz_url: Optional[str]
    scale_factor: float = 1.0
    initial_rotation: List[float] = [0.0, 45.0, 0.0]
    ar_placement_mode: str = "surface_horizontal"
    audio_narration_url: Optional[str]
    recommended_lighting: str = "museum_spotlight"
