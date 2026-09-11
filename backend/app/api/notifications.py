"""
Notifications API — FCM token registration.

POST /api/v1/notifications/token
  Requires Authorization: Bearer <Firebase ID Token>
  Body: {fcm_token: str}
  Upserts token to artisans.fcm_token and notification_tokens table.

GET /api/v1/notifications/token
  Returns current token for authenticated user.

DELETE /api/v1/notifications/token
  Removes token.

All operations are idempotent, handle missing column/table gracefully (log, return success without hard failure).
Rate limiting: 30 requests per minute per user (in-memory).
"""

import logging
import re
import time
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.core.security import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()

# Simple in-memory rate limit per user
_rate_store: Dict[str, List[float]] = {}
_RATE_MAX = 30
_RATE_WINDOW = 60

_FCM_TOKEN_RE = re.compile(r"^[A-Za-z0-9\-\_\:\.]+$")
# FCM tokens are typically 140-200+ chars, but allow 20-4096
_FCM_MIN_LEN = 20
_FCM_MAX_LEN = 4096


# Phase C: delegate to shared helper — keeps store per-module for isolation
from app.core.rate_limit import check_rate_limit as _shared_check_rate_limit  # local alias


def _check_rate_limit(key: str) -> None:
    _shared_check_rate_limit(
        _rate_store,
        key,
        _RATE_MAX,
        _RATE_WINDOW,
        detail_prefix="Rate limit exceeded",
    )


class FcmTokenRequest(BaseModel):
    fcm_token: str = Field(..., description="FCM registration token", min_length=_FCM_MIN_LEN, max_length=_FCM_MAX_LEN)
    device_id: Optional[str] = Field(default=None, description="Optional device identifier for multi-device support")


class FcmTokenResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None


def _validate_token(token: str) -> str:
    token = token.strip()
    if len(token) < _FCM_MIN_LEN or len(token) > _FCM_MAX_LEN:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"fcm_token length must be { _FCM_MIN_LEN}-{ _FCM_MAX_LEN} chars")
    # Allow common FCM charset; be permissive — only reject obvious bad like control chars
    if re.search(r"[\x00-\x1F\x7F]", token):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="fcm_token contains invalid control characters")
    # Optional: warn if not matching typical pattern but still accept
    if not _FCM_TOKEN_RE.match(token):
        logger.debug("fcm_token does not match strict regex but accepting: %s", token[:12])
    return token


def _get_supabase():
    from app.database.connection import get_supabase_client

    return get_supabase_client()


@router.post(
    "/token",
    response_model=FcmTokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Register / upsert FCM token",
    description="Stores FCM token for authenticated artisan. Upserts artisans.fcm_token and notification_tokens table. Idempotent.",
)
async def register_fcm_token(
    payload: FcmTokenRequest,
    current=Depends(get_current_user),
):
    artisan = current.get("artisan") or {}
    artisan_id = str(artisan.get("id") or "")
    firebase_uid = current.get("firebase_uid") or artisan.get("firebase_uid") or ""
    if not artisan_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Artisan identity missing")

    _check_rate_limit(f"token:{artisan_id}")

    token = _validate_token(payload.fcm_token)
    client = _get_supabase()
    result_data: Dict[str, Any] = {"artisan_id": artisan_id, "fcm_token": token[:12] + "..."}

    # 1) Upsert artisans.fcm_token if column exists
    artisans_updated = False
    try:
        # Use supabase_service.update? Direct table update
        upd = client.table("artisans").update({"fcm_token": token}).eq("id", artisan_id).select("id,fcm_token").execute()
        if upd.data:
            artisans_updated = True
            logger.info("Updated artisans.fcm_token for artisan %s", artisan_id)
            result_data["artisans_fcm_token"] = "updated"
        else:
            # Try fallback: maybe RLS blocks? Use service_role should allow
            logger.debug("No data returned updating artisans.fcm_token for %s", artisan_id)
            result_data["artisans_fcm_token"] = "no_data"
    except Exception as exc:
        err = str(exc).lower()
        if "fcm_token" in err or "column" in err or "does not exist" in err:
            logger.warning("artisans.fcm_token column missing for artisan %s — migration 007 required: %s", artisan_id, exc)
            result_data["artisans_fcm_token"] = "column_missing"
            # Still continue to notification_tokens fallback
        else:
            logger.warning("Failed to update artisans.fcm_token for %s: %s", artisan_id, exc)
            # Don't fail request — continue to notification_tokens
            result_data["artisans_fcm_token_error"] = str(exc)[:200]

    # 2) Upsert notification_tokens table (preferred multi-device store)
    # Schema: id UUID PK default gen_random_uuid(), user_id TEXT, token TEXT UNIQUE, created_at, updated_at
    # We try upsert on token unique constraint
    notif_tokens_result = "skipped"
    try:
        # Check if table exists by attempting select limit 1
        # Then upsert token
        # Supabase upsert needs on_conflict; we use upsert with token as unique
        # Payload: user_id = firebase_uid or artisan_id, token = token, device_id optional?
        # Try to handle schema variants: user_id, token, device_id, created_at, updated_at
        insert_payload: Dict[str, Any] = {
            "user_id": firebase_uid or artisan_id,
            "token": token,
        }
        # Include artisan_id linkage if column exists? Try to add artisan_id if not failing
        # We will attempt upsert with on_conflict token
        try:
            res = client.table("notification_tokens").upsert(insert_payload, on_conflict="token").select("*").execute()
            if res.data:
                notif_tokens_result = "upserted"
                logger.info("Upserted notification_tokens for user %s token %s", firebase_uid or artisan_id, token[:12] + "...")
                result_data["notification_tokens"] = "upserted"
            else:
                notif_tokens_result = "no_data"
                result_data["notification_tokens"] = "no_data"
        except Exception as upsert_exc:
            err2 = str(upsert_exc).lower()
            # If upsert not supported, fallback to insert or update
            if "on_conflict" in err2 or "conflict" in err2 or "duplicate" in err2:
                try:
                    # Check existing
                    existing = client.table("notification_tokens").select("id").eq("token", token).limit(1).execute()
                    if existing.data:
                        # Update user_id to ensure linkage
                        upd2 = client.table("notification_tokens").update(insert_payload).eq("token", token).select("id").execute()
                        notif_tokens_result = "updated_existing"
                        result_data["notification_tokens"] = "updated_existing"
                    else:
                        ins = client.table("notification_tokens").insert(insert_payload).select("id").execute()
                        notif_tokens_result = "inserted"
                        result_data["notification_tokens"] = "inserted"
                except Exception as fallback_exc:
                    logger.warning("notification_tokens fallback failed: %s", fallback_exc)
                    result_data["notification_tokens_error"] = str(fallback_exc)[:200]
                    notif_tokens_result = "error"
            elif "does not exist" in err2 or "relation" in err2 or "table" in err2:
                logger.warning("notification_tokens table missing — migration 007 required: %s", upsert_exc)
                result_data["notification_tokens"] = "table_missing"
                notif_tokens_result = "table_missing"
            else:
                logger.warning("Failed to upsert notification_tokens: %s", upsert_exc)
                result_data["notification_tokens_error"] = str(upsert_exc)[:200]
                notif_tokens_result = "error"
    except Exception as exc:
        logger.warning("notification_tokens upsert outer failed: %s", exc)
        result_data["notification_tokens_error"] = str(exc)[:200]

    # Consider success if at least one store succeeded or column/table missing but we logged (MVP still returns success)
    # For strict, we return success True with details
    logger.info(
        "FCM token registration artisan=%s uid=%s artisans_updated=%s notif_tokens=%s",
        artisan_id, firebase_uid, artisans_updated, notif_tokens_result
    )

    return FcmTokenResponse(
        success=True,
        message="FCM token registered" if (artisans_updated or notif_tokens_result in ("upserted", "inserted", "updated_existing")) else "FCM token received (storage pending migration)",
        data=result_data,
    )


@router.get(
    "/token",
    response_model=FcmTokenResponse,
    summary="Get current FCM token",
    description="Returns stored FCM token for authenticated artisan (from artisans.fcm_token or notification_tokens).",
)
async def get_fcm_token(current=Depends(get_current_user)):
    artisan = current.get("artisan") or {}
    artisan_id = str(artisan.get("id") or "")
    firebase_uid = current.get("firebase_uid") or artisan.get("firebase_uid") or ""
    if not artisan_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Artisan identity missing")

    client = _get_supabase()
    found_token: Optional[str] = None
    source = "none"

    # Try artisans.fcm_token
    try:
        res = client.table("artisans").select("fcm_token").eq("id", artisan_id).limit(1).execute()
        if res.data and res.data[0].get("fcm_token"):
            found_token = str(res.data[0].get("fcm_token"))
            source = "artisans.fcm_token"
    except Exception as exc:
        logger.debug("GET token artisans.fcm_token lookup failed: %s", exc)

    # Fallback notification_tokens
    if not found_token:
        try:
            # Try by firebase_uid first
            uid = firebase_uid or artisan_id
            nt = client.table("notification_tokens").select("token").eq("user_id", uid).order("created_at", desc=True).limit(1).execute()
            if nt.data and nt.data[0].get("token"):
                found_token = str(nt.data[0].get("token"))
                source = "notification_tokens"
            else:
                # Try artisan_id fallback
                if uid != artisan_id:
                    nt2 = client.table("notification_tokens").select("token").eq("user_id", artisan_id).order("created_at", desc=True).limit(1).execute()
                    if nt2.data and nt2.data[0].get("token"):
                        found_token = str(nt2.data[0].get("token"))
                        source = "notification_tokens(artisan_id)"
        except Exception as exc:
            logger.debug("GET token notification_tokens lookup failed: %s", exc)

    if not found_token:
        return FcmTokenResponse(success=True, message="No FCM token registered", data={"artisan_id": artisan_id, "source": source, "fcm_token": None})

    # Mask token for response
    masked = found_token[:12] + "..." + found_token[-6:] if len(found_token) > 20 else found_token[:6] + "..."
    return FcmTokenResponse(
        success=True,
        message="FCM token found",
        data={"artisan_id": artisan_id, "source": source, "fcm_token_masked": masked, "fcm_token": found_token},
    )


@router.delete(
    "/token",
    response_model=FcmTokenResponse,
    summary="Delete FCM token",
    description="Removes FCM token from artisans.fcm_token (sets null) and notification_tokens.",
)
async def delete_fcm_token(
    current=Depends(get_current_user),
    token: Optional[str] = None,
):
    artisan = current.get("artisan") or {}
    artisan_id = str(artisan.get("id") or "")
    firebase_uid = current.get("firebase_uid") or artisan.get("firebase_uid") or ""
    if not artisan_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Artisan identity missing")

    _check_rate_limit(f"token:del:{artisan_id}")

    client = _get_supabase()
    result_data: Dict[str, Any] = {"artisan_id": artisan_id}

    # Clear artisans.fcm_token if matches provided token or clear all if no token specified
    try:
        if token:
            # Only clear if matching
            res = client.table("artisans").select("fcm_token").eq("id", artisan_id).limit(1).execute()
            if res.data and res.data[0].get("fcm_token") == token:
                client.table("artisans").update({"fcm_token": None}).eq("id", artisan_id).execute()
                result_data["artisans_fcm_token"] = "cleared"
            else:
                result_data["artisans_fcm_token"] = "not_matching_no_clear"
        else:
            client.table("artisans").update({"fcm_token": None}).eq("id", artisan_id).execute()
            result_data["artisans_fcm_token"] = "cleared"
    except Exception as exc:
        err = str(exc).lower()
        if "fcm_token" in err or "column" in err:
            result_data["artisans_fcm_token"] = "column_missing"
        else:
            logger.warning("DELETE token artisans clear failed: %s", exc)
            result_data["artisans_fcm_token_error"] = str(exc)[:200]

    # Delete from notification_tokens
    try:
        if token:
            client.table("notification_tokens").delete().eq("token", token).execute()
            result_data["notification_tokens"] = "deleted_token"
        else:
            # Delete all tokens for user
            uid = firebase_uid or artisan_id
            # Delete by both uid possibilities
            client.table("notification_tokens").delete().eq("user_id", uid).execute()
            if uid != artisan_id:
                client.table("notification_tokens").delete().eq("user_id", artisan_id).execute()
            result_data["notification_tokens"] = "deleted_user_tokens"
    except Exception as exc:
        err = str(exc).lower()
        if "does not exist" in err or "relation" in err:
            result_data["notification_tokens"] = "table_missing"
        else:
            logger.warning("DELETE token notification_tokens failed: %s", exc)
            result_data["notification_tokens_error"] = str(exc)[:200]

    return FcmTokenResponse(success=True, message="FCM token deleted", data=result_data)
