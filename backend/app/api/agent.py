"""
Unified Artisan Agent API.

A single endpoint that runs all three AI features in one call:
  1. AI Image Enhancer & Studio
  2. Multilingual Auto-Cataloger
  3. Dynamic Pricing Assistant

    POST /api/v1/agent/process    multipart — photo + transcript -> full listing
    POST /api/v1/agent/catalog    JSON — transcript only (no photo)
    GET  /api/v1/agent/models     free-model roster + configuration health

The Android client calls /process once and receives everything needed to publish
a product. The API key never leaves the server.

Security mirrors app/api/image.py: same size cap, MIME allowlist, executable
rejection, dimension bounds, and UUID storage paths (never the client filename).
"""

from __future__ import annotations

import logging
import time
import uuid
from typing import Any, Dict, List, Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from pydantic import BaseModel, Field, field_validator

from app.agent.models import list_free_models
from app.agent.orchestrator import ALL_STAGES, ArtisanAgent
from app.agent.tools import ALLOWED_CATEGORIES, ALLOWED_LANGUAGES, strip_control_chars
from app.core.security import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()

# ── Upload limits — kept in sync with app/api/image.py ─────────────────

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB

ALLOWED_MIMES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
    "image/pjpeg",
    "image/x-png",
}

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
BLOCKED_SUFFIXES = (".exe", ".sh", ".bat", ".php", ".js", ".jsp", ".py")

MIME_TO_EXT = {
    "image/jpeg": "jpg",
    "image/jpg": "jpg",
    "image/pjpeg": "jpg",
    "image/png": "png",
    "image/x-png": "png",
    "image/webp": "webp",
}

# Agent runs are expensive for the free tier — keep the limit tight.
_RATE_LIMIT_MAX = 10
_RATE_LIMIT_WINDOW_SECONDS = 60
_rate_limit_store: Dict[str, List[float]] = {}


def _rate_limit_key(request: Request, user: Optional[Dict[str, Any]]) -> str:
    """Prefer the authenticated artisan; fall back to client IP."""
    if user:
        uid = user.get("uid") or user.get("id") or user.get("firebase_uid")
        if uid:
            return f"artisan:{uid}"
    client = request.client.host if request and request.client else "unknown"
    return f"ip:{client}"


def _prune_rate_limit_store(window_start: float) -> None:
    """
    Drop keys whose window has fully expired.

    Without this the IP-keyed fallback leaks one list per distinct client
    forever. Cheap to run: the store only holds recently active callers.
    """
    stale = [
        key
        for key, stamps in _rate_limit_store.items()
        if not stamps or max(stamps) <= window_start
    ]
    for key in stale:
        del _rate_limit_store[key]


def _check_rate_limit(key: str) -> None:
    """Sliding-window limiter. Raises 429 when the window is full."""
    now = time.time()
    window_start = now - _RATE_LIMIT_WINDOW_SECONDS
    _prune_rate_limit_store(window_start)
    timestamps = [t for t in _rate_limit_store.get(key, []) if t > window_start]

    if len(timestamps) >= _RATE_LIMIT_MAX:
        retry_after = int(_RATE_LIMIT_WINDOW_SECONDS - (now - timestamps[0])) + 1
        _rate_limit_store[key] = timestamps
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                f"Rate limit exceeded — max {_RATE_LIMIT_MAX} agent runs per "
                f"{_RATE_LIMIT_WINDOW_SECONDS}s. Retry in {retry_after}s."
            ),
            headers={"Retry-After": str(retry_after)},
        )

    timestamps.append(now)
    _rate_limit_store[key] = timestamps


def _clear_rate_limit_store() -> None:
    """Test hook — reset the limiter between cases."""
    _rate_limit_store.clear()


def _validate_upload(upload: UploadFile, data: bytes) -> str:
    """
    Validate an uploaded image. Returns the normalised extension.

    Raises HTTPException 400/413 — never trusts the client filename.
    """
    if len(data) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Image exceeds {MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB limit",
        )
    if not data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Empty image file"
        )

    content_type = (upload.content_type or "").lower().strip()
    filename = (upload.filename or "").lower().strip()

    if "executable" in content_type or filename.endswith(BLOCKED_SUFFIXES):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Executable uploads are rejected"
        )

    # Path traversal guard — the filename is never used for storage, but a
    # traversal attempt is itself a signal worth rejecting.
    if any(token in filename for token in ("../", "..\\", "/", "\\")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid filename"
        )

    ext = ""
    if "." in filename:
        candidate = filename.rsplit(".", 1)[-1]
        if candidate in ALLOWED_EXTENSIONS:
            ext = "jpg" if candidate == "jpeg" else candidate

    if not ext:
        if content_type not in ALLOWED_MIMES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Unsupported image type '{content_type}'. "
                    "Allowed: jpg, jpeg, png, webp"
                ),
            )
        ext = MIME_TO_EXT.get(content_type, "jpg")

    if content_type and content_type not in ALLOWED_MIMES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported MIME type '{content_type}'",
        )

    return ext


def _store_outputs(
    artisan_id: str, ext: str, original: bytes, outputs: Dict[str, Any]
) -> Dict[str, Optional[str]]:
    """
    Upload the agent's image outputs, reusing the storage helper from the
    existing image endpoint so bucket handling stays in one place.

    Returns a dict of URLs; values are None when storage is unavailable, which
    keeps the agent useful in local development without Supabase.
    """
    urls: Dict[str, Optional[str]] = {
        "original_url": None,
        "enhanced_url": None,
        "thumbnail_url": None,
    }
    try:
        from app.api.image import _get_bucket_name, _upload_bytes_with_fallback

        bucket = _get_bucket_name()
        base = f"{artisan_id}/{uuid.uuid4().hex}"

        urls["original_url"] = _upload_bytes_with_fallback(
            bucket, f"{base}_original.{ext}", original, f"image/{'jpeg' if ext == 'jpg' else ext}"
        )
        if outputs.get("webp_bytes"):
            urls["enhanced_url"] = _upload_bytes_with_fallback(
                bucket, f"{base}_enhanced.webp", outputs["webp_bytes"], "image/webp"
            )
        elif outputs.get("enhanced_bytes"):
            urls["enhanced_url"] = _upload_bytes_with_fallback(
                bucket, f"{base}_enhanced.png", outputs["enhanced_bytes"], "image/png"
            )
        if outputs.get("thumbnail_bytes"):
            urls["thumbnail_url"] = _upload_bytes_with_fallback(
                bucket, f"{base}_thumb.webp", outputs["thumbnail_bytes"], "image/webp"
            )
    except Exception as exc:
        # Storage failure must not discard a successful AI run.
        # Log only the exception type: Supabase client errors can embed request
        # URLs carrying credentials, which must never reach the logs.
        logger.warning("Agent output storage failed: %s", type(exc).__name__)

    return urls


# ── Request / response models ──────────────────────────────────────────


class CatalogOnlyRequest(BaseModel):
    """Body for POST /agent/catalog — transcript without a photo."""

    transcript: str = Field(..., min_length=5, max_length=2000)
    language: str = Field(default="hi", max_length=8)
    material_cost: Optional[float] = Field(default=None, ge=0, le=1_000_000)
    labour_hours: Optional[float] = Field(default=None, ge=0, le=500)
    include_pricing: bool = Field(default=True)

    @field_validator("transcript", mode="before")
    @classmethod
    def clean_transcript(cls, v: Any) -> str:
        return strip_control_chars(str(v or ""))

    @field_validator("language")
    @classmethod
    def check_language(cls, v: str) -> str:
        v = (v or "hi").strip().lower()
        return v if v in ALLOWED_LANGUAGES else "hi"


# ── Endpoints ──────────────────────────────────────────────────────────


@router.post("/process", status_code=status.HTTP_200_OK)
async def process_product(
    request: Request,
    image: Optional[UploadFile] = File(default=None, description="Product photo"),
    transcript: Optional[str] = Form(default=None, description="Voice transcript"),
    language: str = Form(default="hi", description="Transcript language code"),
    output_format: Optional[str] = Form(default=None, description="1:1 or 4:5"),
    material_cost: Optional[float] = Form(default=None),
    labour_hours: Optional[float] = Form(default=None),
    stages: Optional[str] = Form(
        default=None, description="Comma-separated stage subset"
    ),
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Run the unified agent: enhance the photo, write the listing, suggest a price.

    At least one of `image` or `transcript` is required. Whatever is supplied
    determines which stages run, and each stage degrades independently — a
    partial result is returned rather than a total failure.
    """
    _check_rate_limit(_rate_limit_key(request, current_user))

    if image is None and not (transcript and transcript.strip()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide at least an image or a transcript",
        )

    image_bytes: Optional[bytes] = None
    ext = "jpg"
    mime_type = "image/jpeg"

    if image is not None:
        image_bytes = await image.read()
        ext = _validate_upload(image, image_bytes)
        mime_type = image.content_type or f"image/{'jpeg' if ext == 'jpg' else ext}"

    if output_format and output_format not in {"1:1", "4:5"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="output_format must be '1:1' or '4:5'",
        )

    language = (language or "hi").strip().lower()
    if language not in ALLOWED_LANGUAGES:
        language = "hi"

    requested_stages: Optional[List[str]] = None
    if stages:
        requested_stages = [s.strip() for s in stages.split(",") if s.strip() in ALL_STAGES]
        if not requested_stages:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"stages must be a subset of {ALL_STAGES}",
            )

    agent = ArtisanAgent()
    try:
        result = await agent.run(
            image_bytes=image_bytes,
            mime_type=mime_type,
            transcript=strip_control_chars(transcript) if transcript else None,
            language=language,
            output_format=output_format,
            material_cost=material_cost,
            labour_hours=labour_hours,
            stages=requested_stages,
        )
    except ValueError as exc:
        # Configuration problems (missing/invalid API key) surface here.
        logger.error("Agent configuration error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc

    payload = result.to_dict()

    # Persist whenever a photo was uploaded — even if enhancement failed, the
    # artisan's original must not be lost when catalog/pricing succeeded.
    if image_bytes:
        artisan_id = str(
            current_user.get("uid")
            or current_user.get("id")
            or current_user.get("firebase_uid")
            or "anonymous"
        )
        urls = _store_outputs(artisan_id, ext, image_bytes, result.image_bytes)
        # to_dict() always emits an "image" key, set to None when the stage did
        # not run — so coalesce before merging the URLs in.
        if not payload.get("image"):
            payload["image"] = {}
        payload["image"].update(urls)

    if not result.succeeded_any:
        # Every stage failed — report it honestly rather than returning success.
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "message": "All agent stages failed",
                "stages": payload["stages"],
            },
        )

    return payload


@router.post("/catalog", status_code=status.HTTP_200_OK)
async def catalog_only(
    request: Request,
    body: CatalogOnlyRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Voice-only path: generate a listing (and optionally a price) with no photo.

    Useful when the artisan has already uploaded images separately, or is adding
    a description to an existing product.
    """
    _check_rate_limit(_rate_limit_key(request, current_user))

    stages = ["catalog_generation"]
    if body.include_pricing:
        stages.append("price_suggestion")

    agent = ArtisanAgent()
    try:
        result = await agent.run(
            transcript=body.transcript,
            language=body.language,
            material_cost=body.material_cost,
            labour_hours=body.labour_hours,
            stages=stages,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc

    if not result.succeeded_any:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "message": "Catalog generation failed",
                "stages": [s.to_dict() for s in result.stages],
            },
        )

    return result.to_dict()


@router.get("/models", status_code=status.HTTP_200_OK)
async def agent_models() -> Dict[str, Any]:
    """
    Report the free-model roster and whether the agent is configured.

    Never returns the API key — only whether one is present.
    """
    configured = False
    try:
        from app.core.config import get_settings

        configured = bool(get_settings().OPENROUTER_API_KEY)
    except Exception:
        import os

        configured = bool(os.getenv("OPENROUTER_API_KEY"))

    models = list_free_models()
    return {
        "configured": configured,
        "tier": "free",
        "model_count": len(models),
        "models": models,
        "stages": ALL_STAGES,
        "categories": ALLOWED_CATEGORIES,
        "languages": ALLOWED_LANGUAGES,
    }


__all__ = ["router"]
