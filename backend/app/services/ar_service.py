from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid
from app.models.ar import (
    Product3DModelResponse,
    DimensionsCM,
    ModelFormat,
    Generate3DPreviewRequest,
    Generate3DPreviewResponse,
    ARSessionCapabilityCheckResponse
)
from app.ai.photogrammetry_3d import Photogrammetry3DPipeline

_PRODUCT_MODELS: Dict[str, Dict[str, Any]] = {}
_AR_ASSETS: Dict[str, Dict[str, Any]] = {}

class ARService:
    @staticmethod
    def get_product_3d_model(product_id: str) -> Optional[Product3DModelResponse]:
        record = _PRODUCT_MODELS.get(product_id)
        if not record:
            # Generate default certified craft 3D model
            now = datetime.utcnow().isoformat()
            record = {
                "id": str(uuid.uuid4()),
                "product_id": product_id,
                "model_format": ModelFormat.GLB,
                "model_file_url": f"https://storage.kalacart.in/models/3d_{product_id}.glb",
                "file_size_bytes": 3840000,
                "polygon_count": 18450,
                "dimensions": {
                    "length_cm": 25.0,
                    "width_cm": 20.0,
                    "height_cm": 35.0
                },
                "texture_resolution": "2k",
                "has_pbr_materials": True,
                "is_ar_ready": True,
                "usdz_quicklook_url": f"https://storage.kalacart.in/models/3d_{product_id}.usdz",
                "created_at": now
            }
            _PRODUCT_MODELS[product_id] = record

        return Product3DModelResponse(
            id=record["id"],
            product_id=record["product_id"],
            model_format=record["model_format"],
            model_file_url=record["model_file_url"],
            file_size_bytes=record["file_size_bytes"],
            polygon_count=record["polygon_count"],
            dimensions=DimensionsCM(**record["dimensions"]),
            texture_resolution=record["texture_resolution"],
            has_pbr_materials=record["has_pbr_materials"],
            is_ar_ready=record["is_ar_ready"],
            usdz_quicklook_url=record.get("usdz_quicklook_url"),
            created_at=record["created_at"]
        )

    @staticmethod
    def generate_3d_preview(product_id: str, payload: Generate3DPreviewRequest) -> Generate3DPreviewResponse:
        res = Photogrammetry3DPipeline.synthesize_3d_asset(product_id=product_id, req=payload)
        now = datetime.utcnow().isoformat()

        # Update product model store
        model_rec = {
            "id": str(uuid.uuid4()),
            "product_id": product_id,
            "model_format": ModelFormat.GLB,
            "model_file_url": res.model_glb_url,
            "file_size_bytes": int(res.file_size_mb * 1024 * 1024),
            "polygon_count": res.polygon_count,
            "dimensions": {
                "length_cm": payload.length_cm,
                "width_cm": payload.width_cm,
                "height_cm": payload.height_cm
            },
            "texture_resolution": "2k",
            "has_pbr_materials": True,
            "is_ar_ready": True,
            "usdz_quicklook_url": res.model_usdz_url,
            "created_at": now
        }
        _PRODUCT_MODELS[product_id] = model_rec

        _AR_ASSETS[product_id] = {
            "product_id": product_id,
            "multi_angle_photo_urls": payload.multi_angle_photo_urls,
            "turntable_frames_urls": res.turntable_frames_urls,
            "synthesis_status": "completed",
            "lighting_preset": payload.lighting_preset.value,
            "scale_reference_object": payload.scale_reference.value
        }

        return res

    @staticmethod
    def check_capability(user_agent: str, product_id: Optional[str] = None) -> ARSessionCapabilityCheckResponse:
        ua = user_agent.lower()
        supports_arcore = "android" in ua and "chrome" in ua
        supports_quicklook = "iphone" in ua or "ipad" in ua
        supports_webxr = "oculus" in ua or "chrome" in ua

        if supports_quicklook:
            mode = "quicklook_native"
        elif supports_arcore:
            mode = "arcore_native"
        elif supports_webxr:
            mode = "webxr"
        else:
            mode = "turntable_360"

        prod_id = product_id or "default-craft"
        fallback_frames = [
            f"https://storage.kalacart.in/turntable/{prod_id}/frame_{i:02d}.webp"
            for i in range(1, 17)
        ]

        return ARSessionCapabilityCheckResponse(
            client_platform="iOS" if supports_quicklook else ("Android" if "android" in ua else "Desktop/Other"),
            supports_native_arcore=supports_arcore,
            supports_webxr=supports_webxr,
            supports_quicklook=supports_quicklook,
            recommended_viewer_mode=mode,
            fallback_turntable_frames_urls=fallback_frames
        )
