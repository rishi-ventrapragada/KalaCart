"""
Upload API — image upload to Supabase Storage.

POST /api/v1/upload/image  file: UploadFile, auth required
Validates MIME jpeg/png/webp, size <10MB, delegates to storage_service.upload_image
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse

from app.core.security import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()

ALLOWED_MIME = {"image/jpeg", "image/jpg", "image/png", "image/webp"}
MAX_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


def _get_artisan_id(current: dict) -> str:
    artisan = current.get("artisan") or {}
    artisan_id = artisan.get("id")
    if not artisan_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Artisan identity missing")
    return str(artisan_id)


@router.post(
    "/image",
    status_code=status.HTTP_201_CREATED,
    summary="Upload product image",
    description="Validates MIME (jpeg/png/webp) and size <10MB, uploads via storage_service.",
)
async def upload_image(
    file: UploadFile = File(..., description="Image file (jpeg/png/webp, max 10MB)"),
    current=Depends(get_current_user),
):
    """
    POST /api/v1/upload/image
    Form-Data: file
    Auth: Bearer <Firebase token>
    Returns {url, filename} with 201
    """
    artisan_id = _get_artisan_id(current)

    if not file or not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File is required")

    content_type = (file.content_type or "").lower().strip()
    # Validate MIME
    if content_type not in ALLOWED_MIME:
        # Fallback: check extension
        ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
        if ext not in ("jpg", "jpeg", "png", "webp"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type '{content_type or ext}'. Allowed: jpeg, png, webp",
            )
        # Normalize content_type from ext
        if ext in ("jpg", "jpeg"):
            content_type = "image/jpeg"
        elif ext == "png":
            content_type = "image/png"
        elif ext == "webp":
            content_type = "image/webp"

    # Delegate to storage_service which also validates size and re-reads file
    # Note: storage_service.upload_image reads file bytes internally, so we pass file directly
    try:
        from app.services.storage_service import upload_image as svc_upload

        public_url = await svc_upload(file, artisan_id)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Failed to upload image for artisan %s: %s", artisan_id, exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to upload image: {exc}") from exc

    # svc_upload returns public_url string; derive filename from url path tail
    filename = public_url.rsplit("/", 1)[-1] if "/" in public_url else public_url
    # Also include storage path if needed: artisan_id/filename is embedded in URL
    # Return both url and filename
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            "success": True,
            "message": "Image uploaded",
            "data": {
                "url": public_url,
                "filename": filename,
                "public_url": public_url,
                "artisan_id": artisan_id,
            },
        },
    )
