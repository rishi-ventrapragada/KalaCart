"""
API Router for KalaCart Phase 7 — Digital Craft Museum.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, status
from app.models.museum import (
    MuseumCollection,
    GalleryRoom,
    MuseumArtifact,
    AudioGuide,
    CraftTimelineEvent,
    MuseumCrossLinkResponse,
    XRArtifactSessionResponse,
)
from app.services.museum_service import MuseumService

router = APIRouter(prefix="/museum", tags=["Digital Craft Museum"])


@router.get("/collections", response_model=List[MuseumCollection])
def list_museum_collections():
    """Retrieve all curated digital craft museum exhibition collections."""
    return MuseumService.list_collections()


@router.get("/collections/{collection_id}", response_model=MuseumCollection)
def get_museum_collection(collection_id: str):
    """Retrieve a single museum exhibition collection with gallery halls."""
    col = MuseumService.get_collection_by_id(collection_id)
    if not col:
        raise HTTPException(status_code=404, detail="Museum collection not found")
    return col


@router.get("/galleries", response_model=List[GalleryRoom])
def list_gallery_rooms():
    """Retrieve all 360° virtual exhibition halls and ambient soundscapes."""
    return MuseumService.list_gallery_rooms()


@router.get("/galleries/{room_id}", response_model=GalleryRoom)
def get_gallery_room(room_id: str):
    """Retrieve details and 3D artifacts for a specific 360° virtual gallery room."""
    room = MuseumService.get_gallery_room_by_id(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Virtual gallery room not found")
    return room


@router.get("/artifacts", response_model=List[MuseumArtifact])
def list_museum_artifacts(
    craft_category: Optional[str] = None,
    state: Optional[str] = None,
    collection_id: Optional[str] = None,
):
    """Search & filter 3D museum artifacts across Indian craft regions and historical eras."""
    return MuseumService.list_artifacts(
        craft_category=craft_category,
        state=state,
        collection_id=collection_id
    )


@router.get("/artifacts/{artifact_id}", response_model=MuseumArtifact)
def get_museum_artifact(artifact_id: str):
    """Retrieve full deep view of a 3D museum artifact, master lineage, and audio guides."""
    art = MuseumService.get_artifact_by_id(artifact_id)
    if not art:
        raise HTTPException(status_code=404, detail="Museum artifact not found")
    return art


@router.get("/audio-guides/{artifact_id}", response_model=List[AudioGuide])
def get_artifact_audio_guides(artifact_id: str, language_code: Optional[str] = None):
    """Retrieve multilingual audio narration guides for a specific artifact."""
    return MuseumService.get_audio_guides(artifact_id=artifact_id, language_code=language_code)


@router.get("/timelines/{craft_code}", response_model=List[CraftTimelineEvent])
def get_craft_historical_timeline(craft_code: str):
    """Retrieve chronological historical timeline milestones and royal patronage history."""
    timeline = MuseumService.get_craft_timeline(craft_code)
    if not timeline:
        raise HTTPException(status_code=404, detail="Craft historical timeline not found")
    return timeline


@router.get("/xr-session/{artifact_id}", response_model=XRArtifactSessionResponse)
def get_xr_artifact_session(artifact_id: str):
    """Generate WebXR / AR QuickLook inspection parameters for 3D model."""
    session = MuseumService.get_xr_session(artifact_id)
    if not session:
        raise HTTPException(status_code=404, detail="XR session not available for this artifact")
    return session


@router.get("/cross-link/artifact/{artifact_id}", response_model=MuseumCrossLinkResponse)
def cross_link_artifact_to_marketplace(artifact_id: str):
    """Cross-link a museum artifact to authentic verified marketplace products from master artisans."""
    cross_link = MuseumService.cross_link_artifact_to_products(artifact_id)
    if not cross_link:
        raise HTTPException(status_code=404, detail="Artifact not found for cross-linking")
    return cross_link


@router.get("/cross-link/product/{product_id}")
def cross_link_product_to_museum(product_id: str):
    """Cross-reference a live marketplace product with its historical museum lineage and 3D archives."""
    return MuseumService.cross_link_product_to_museum(product_id)
