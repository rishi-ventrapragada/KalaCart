"""
Auth API routes - Firebase Email/Password & Phone OTP verification + Supabase provisioning.
Supports syncing users via UID, email, display name, and photo URL.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator

from app.core.security import get_current_user, verify_firebase_token
from app.models.common import ApiResponse
from app.models.user import UserSyncRequest

logger = logging.getLogger(__name__)

router = APIRouter()


class SyncUserRequest(BaseModel):
    """Body for POST /sync-user — syncs Firebase user (email or phone) to Supabase."""

    uid: Optional[str] = Field(default=None, description="Firebase UID")
    firebase_uid: Optional[str] = Field(default=None, description="Firebase UID alias")
    email: Optional[str] = Field(default=None, description="User email address")
    id_token: Optional[str] = Field(default=None, description="Firebase ID token")
    idToken: Optional[str] = Field(default=None, description="Firebase ID token alias")
    firebase_token: Optional[str] = Field(default=None, description="Firebase ID token alias")
    name: Optional[str] = Field(default=None, max_length=100, description="Artisan / User display name")
    photo_url: Optional[str] = Field(default=None, description="Profile photo URL")
    photo: Optional[str] = Field(default=None, description="Profile photo URL alias")
    phone: Optional[str] = Field(default=None, description="Optional phone number")
    language_preference: Optional[str] = Field(default="hi", max_length=10, description="Language preference")
    location: Optional[str] = Field(default=None, max_length=200, description="Location")
    craft_type: Optional[str] = Field(default=None, max_length=100, description="Primary craft")

    @field_validator("name")
    @classmethod
    def _strip_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not v:
                return None
            return v
        return v

    @field_validator("email")
    @classmethod
    def _normalize_email(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip().lower()
            return v if v else None
        return v


@router.post(
    "/sync-user",
    summary="Sync Firebase user to Supabase",
    description="Verifies Firebase user (via token or direct UID), extracts profile info, and upserts user / artisan.",
)
async def sync_user(payload: SyncUserRequest):
    """
    POST /api/v1/auth/sync-user
    Accepts: { uid, name, email, photo_url, idToken?, ... }
    """
    token = payload.id_token or payload.idToken or payload.firebase_token
    firebase_uid = payload.uid or payload.firebase_uid
    email = payload.email
    phone = payload.phone
    name = payload.name
    photo_url = payload.photo_url or payload.photo

    # If ID token provided, decode claims
    if token:
        try:
            claims = verify_firebase_token(token)
            if claims:
                firebase_uid = firebase_uid or claims.get("uid")
                email = email or claims.get("email")
                phone = phone or claims.get("phone_number")
                name = name or claims.get("name")
                photo_url = photo_url or claims.get("picture")
        except Exception as e:
            logger.warning("Token verification failed in sync_user: %s", e)

    if not firebase_uid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing user UID (must provide uid or valid id_token)")

    # Check if user is new
    is_new_user = False
    try:
        from app.services.supabase_service import get_artisan_by_uid
        existing = get_artisan_by_uid(firebase_uid)
        is_new_user = existing is None
    except Exception as exc:
        logger.warning("Failed to check existing artisan for uid=%s: %s", firebase_uid, exc)
        is_new_user = True

    # Upsert user in Supabase
    try:
        from app.services.supabase_service import upsert_artisan
        artisan = upsert_artisan(
            firebase_uid=firebase_uid,
            phone=phone,
            email=email,
            name=name,
            photo_url=photo_url,
            language_preference=payload.language_preference or "hi",
            location=payload.location,
            craft_type=payload.craft_type,
        )
    except Exception as exc:
        logger.error("Failed to upsert artisan uid=%s: %s", firebase_uid, exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to sync user: {exc}") from exc

    if not artisan:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to sync user: no data returned")

    artisan_id = artisan.get("id") or artisan.get("artisan_id")
    http_status = status.HTTP_201_CREATED if is_new_user else status.HTTP_200_OK

    return JSONResponse(
        status_code=http_status,
        content={
            "success": True,
            "message": "User created successfully" if is_new_user else "User synced successfully",
            "data": {
                "artisan_id": artisan_id,
                "id": artisan_id,
                "uid": firebase_uid,
                "firebase_uid": firebase_uid,
                "email": email,
                "name": name,
                "photo_url": photo_url,
                "phone": phone,
                "is_new_user": is_new_user,
                "artisan": artisan,
            },
        },
    )


@router.get(
    "/me",
    summary="Get current artisan/user profile",
    description="Requires Authorization: Bearer <Firebase ID Token>. Returns user profile.",
)
async def get_current_artisan(current=Depends(get_current_user)):
    """
    GET /api/v1/auth/me
    """
    artisan = current.get("artisan")
    firebase_uid = current.get("firebase_uid")
    phone = current.get("phone")
    email = current.get("email")

    return {
        "success": True,
        "message": "Current user fetched",
        "data": {
            "artisan": artisan,
            "firebase_uid": firebase_uid,
            "email": email,
            "phone": phone,
        },
    }
