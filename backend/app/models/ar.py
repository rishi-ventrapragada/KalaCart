from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum

class ModelFormat(str, Enum):
    GLB = "glb"
    GLTF = "gltf"
    USDZ = "usdz"

class LightingPreset(str, Enum):
    STUDIO = "studio"
    DAYLIGHT = "daylight"
    WARM_INDOOR = "warm_indoor"

class ScaleReference(str, Enum):
    COFFEE_TABLE = "coffee_table"
    DINING_TABLE = "dining_table"
    HUMAN_HAND = "human_hand"
    SHELF = "shelf"

class DimensionsCM(BaseModel):
    length_cm: float
    width_cm: float
    height_cm: float

class Product3DModelResponse(BaseModel):
    id: str
    product_id: str
    model_format: ModelFormat
    model_file_url: str
    file_size_bytes: int
    polygon_count: int
    dimensions: DimensionsCM
    texture_resolution: str = "2k"
    has_pbr_materials: bool = True
    is_ar_ready: bool = True
    usdz_quicklook_url: Optional[str] = None
    created_at: str

class Generate3DPreviewRequest(BaseModel):
    multi_angle_photo_urls: List[str] = Field(..., min_length=4)
    length_cm: float = Field(..., gt=0)
    width_cm: float = Field(..., gt=0)
    height_cm: float = Field(..., gt=0)
    lighting_preset: LightingPreset = Field(default=LightingPreset.STUDIO)
    scale_reference: ScaleReference = Field(default=ScaleReference.COFFEE_TABLE)

class Generate3DPreviewResponse(BaseModel):
    product_id: str
    synthesis_status: str
    model_glb_url: str
    model_usdz_url: str
    polygon_count: int
    file_size_mb: float
    turntable_frames_urls: List[str] = Field(default_factory=list)
    scale_reference_object: str
    is_ar_ready: bool = True
    message: str

class ARSessionCapabilityCheckResponse(BaseModel):
    client_platform: str
    supports_native_arcore: bool
    supports_webxr: bool
    supports_quicklook: bool
    recommended_viewer_mode: str  # "ar_native", "webxr", "turntable_360"
    fallback_turntable_frames_urls: List[str] = Field(default_factory=list)
