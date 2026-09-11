from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class HistoryTimelineEvent(BaseModel):
    century_epoch: str
    dynasty_ruler: str
    milestone_description: str
    archaeological_evidence: Optional[str] = None


class GIDetails(BaseModel):
    gi_number: str
    registration_year: int
    legal_status: str
    gi_authority: str
    specification: str
    certificate_url: Optional[str] = None


class CraftTechnique(BaseModel):
    step_number: int
    title: str
    description: str
    duration_days: float
    mastery_level: str


class CraftTool(BaseModel):
    tool_name: str
    traditional_name: str
    material: str
    usage_description: str


class CraftMaterial(BaseModel):
    name: str
    sourcing_location: str
    natural_eco_status: str
    properties: str


class VideoArchiveItem(BaseModel):
    title: str
    duration_seconds: int
    thumbnail_url: str
    video_url: str
    curator_notes: str


class RegionInfo(BaseModel):
    state: str
    district: str
    cluster_name: str
    geo_lat: float
    geo_lng: float
    village_count: int


class MasterArtisanResponse(BaseModel):
    id: str
    craft_id: str
    name: str
    title_recognition: str
    state: str
    village: str
    years_of_lineage: int
    biography: str
    profile_image_url: Optional[str] = None
    audio_quote_url: Optional[str] = None
    active_mentees_trained: int = 20


class OralHistoryResponse(BaseModel):
    id: str
    craft_id: str
    artisan_narrator_name: str
    story_title: str
    vernacular_language: str
    audio_recording_url: Optional[str] = None
    transcript_original: str
    transcript_english: str
    cultural_significance: str
    recorded_date: str


class CraftHeritageDetail(BaseModel):
    id: str
    craft_code: str
    name: str
    vernacular_names: Dict[str, str] = {}
    category: str
    summary: str
    region: RegionInfo
    history_timeline: List[HistoryTimelineEvent] = []
    gi_details: GIDetails
    techniques: List[CraftTechnique] = []
    tools: List[CraftTool] = []
    materials: List[CraftMaterial] = []
    video_archive_urls: List[VideoArchiveItem] = []
    cover_image_url: Optional[str] = None
    gallery_images: List[str] = []
    master_artisans: List[MasterArtisanResponse] = []
    oral_histories: List[OralHistoryResponse] = []


class CraftLibrarySummary(BaseModel):
    id: str
    craft_code: str
    name: str
    category: str
    state: str
    cluster_name: str
    gi_number: str
    summary: str
    cover_image_url: Optional[str] = None


class StoryGenerationRequest(BaseModel):
    craft_id: str
    language: str = Field(default="en", description="en, hi, te, ta, bn, mr")
    story_theme: str = Field(
        default="origin_legend",
        description="origin_legend, master_craftsman_journey, divine_patronage, contemporary_renaissance"
    )


class HistoricalFactItem(BaseModel):
    epoch: str
    fact_statement: str
    source_citation: str


class AINarrativeStory(BaseModel):
    title: str
    narrative_body: str
    cultural_motifs: List[str] = []
    symbolism_explained: str
    disclaimer: str = "AI-generated cultural narrative based on oral folk traditions. Historical facts are certified separately."


class StoryGenerationResponse(BaseModel):
    craft_id: str
    craft_name: str
    language: str
    story_theme: str
    historical_facts: List[HistoricalFactItem]
    ai_generated_narrative: AINarrativeStory
    reading_time_minutes: int = 4
    generated_at: str
