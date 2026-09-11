"""
Supabase Auth access-token verification.

The Android app signs users in with Supabase Auth (email + password). Its access
tokens are JWTs signed with the project's asymmetric keys, which Supabase publishes
at {SUPABASE_URL}/auth/v1/.well-known/jwks.json — so the backend can verify them
without holding any secret.

- is_supabase_token(token)        -> bool   issuer check (signature verified separately)
- verify_supabase_token(token)    -> claims or raises 401 / 503
- supabase_user_context(claims)   -> current-user dict in the shape endpoints expect
"""

import logging
import os
from typing import Any, Dict, Optional

import jwt
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

# Cached JWKS client — keys are refetched hourly or when an unknown key id appears
_jwks_client: Optional[jwt.PyJWKClient] = None


def _issuer() -> Optional[str]:
    try:
        from app.core.config import get_settings

        url = get_settings().SUPABASE_URL
    except Exception:
        url = os.getenv("SUPABASE_URL")
    return f"{url.rstrip('/')}/auth/v1" if url else None


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def is_supabase_token(token: str) -> bool:
    """True if the token claims to be issued by this project's Supabase Auth (signature not yet checked)."""
    issuer = _issuer()
    if not issuer or not token:
        return False
    try:
        claims = jwt.decode(token, options={"verify_signature": False})
    except jwt.PyJWTError:
        return False
    return claims.get("iss") == issuer


def verify_supabase_token(token: str) -> Dict[str, Any]:
    """
    Verify signature, expiry, audience and issuer of a Supabase access token.

    Returns the decoded claims. Raises 401 for invalid/expired tokens and 503 when
    the signing keys cannot be fetched.
    """
    global _jwks_client

    issuer = _issuer()
    if not issuer:
        raise _unauthorized("Supabase auth is not configured (SUPABASE_URL missing)")
    try:
        if _jwks_client is None:
            _jwks_client = jwt.PyJWKClient(f"{issuer}/.well-known/jwks.json", lifespan=3600)
        signing_key = _jwks_client.get_signing_key_from_jwt(token)
        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=["ES256", "RS256"],
            audience="authenticated",
            issuer=issuer,
        )
    except jwt.PyJWKClientConnectionError as exc:
        logger.error("Supabase signing keys unreachable: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable — try again",
        ) from exc
    except jwt.ExpiredSignatureError as exc:
        raise _unauthorized("Session expired — please log in again") from exc
    except jwt.PyJWTError as exc:
        raise _unauthorized(f"Invalid access token: {exc}") from exc

    if not claims.get("sub"):
        raise _unauthorized("Invalid access token: missing subject")
    return claims


def _get_profile(auth_user_id: str) -> Optional[Dict[str, Any]]:
    """Fetch the user's profiles row (linked by auth_user_id). Returns None if absent or on error."""
    try:
        from app.database.connection import get_supabase_client

        res = (
            get_supabase_client()
            .table("profiles")
            .select("*")
            .eq("auth_user_id", auth_user_id)
            .limit(1)
            .execute()
        )
        return res.data[0] if res.data else None
    except Exception as exc:
        logger.warning("Profile lookup failed for uid=%s: %s", auth_user_id, exc)
        return None


def supabase_user_context(claims: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build the current-user dict endpoints expect from verified Supabase claims.

    Legacy endpoints read current_user["artisan"] / ["firebase_uid"]; for Supabase users the
    profile fills that role, keyed by the auth user id so storage paths and ownership checks
    match the profiles and products the app creates (profiles.id == auth user id).
    """
    uid = claims["sub"]
    profile = _get_profile(uid)
    metadata = claims.get("user_metadata") or {}
    artisan = {**(profile or {}), "id": uid, "profile_id": (profile or {}).get("id"), "auth_user_id": uid}

    return {
        "uid": uid,
        "user_id": uid,
        "firebase_uid": uid,
        "email": claims.get("email"),
        "phone": claims.get("phone") or None,
        "name": (profile or {}).get("full_name") or metadata.get("full_name"),
        "role": (profile or {}).get("role") or metadata.get("role"),
        "artisan": artisan,
        "profile": profile,
        "claims": claims,
        "auth_provider": "supabase",
    }
