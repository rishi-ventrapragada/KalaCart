from fastapi import APIRouter, Depends, HTTPException, Query, Header, status
from typing import List, Optional, Any
from app.core.security import get_current_user
from app.models.ar import (
    Product3DModelResponse,
    Generate3DPreviewRequest,
    Generate3DPreviewResponse,
    ARSessionCapabilityCheckResponse
)
from app.services.ar_service import ARService

router = APIRouter(prefix="/api/v1/ar", tags=["AR Product Experience"])

@router.get("/products/{product_id}/model", response_model=Product3DModelResponse)
def get_product_3d_model(product_id: str):
    """
    Fetch 3D/AR model metadata, glTF/GLB/USDZ file links, dimensions, and PBR textures.
    """
    model = ARService.get_product_3d_model(product_id)
    if not model:
        raise HTTPException(status_code=404, detail="3D model not found for product")
    return model

@router.post("/products/{product_id}/generate-3d", response_model=Generate3DPreviewResponse, status_code=status.HTTP_201_CREATED)
def generate_3d_preview_from_photos(
    product_id: str,
    payload: Generate3DPreviewRequest,
    current_user: Any = Depends(get_current_user)
):
    """
    Sellers upload 4-8 multi-angle craft photos; AI photogrammetry synthesizes a lightweight (<4MB) 3D GLB & USDZ preview.
    """
    return ARService.generate_3d_preview(product_id=product_id, payload=payload)

@router.get("/capability-check", response_model=ARSessionCapabilityCheckResponse)
def check_ar_device_capability(
    user_agent: Optional[str] = Header(None),
    product_id: Optional[str] = Query(None)
):
    """
    Detects device WebXR / ARCore / QuickLook capability with graceful fallback to 360-degree turntable.
    """
    ua = user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"
    return ARService.check_capability(user_agent=ua, product_id=product_id)
