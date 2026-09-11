"""
Firebase Authentication — token verification & FastAPI dependency.

- initialize_firebase() reads FIREBASE_CREDENTIALS_PATH or FIREBASE_CREDENTIALS_JSON from Settings/env,
  calls firebase_admin.initialize_app(...) once, handles missing file gracefully.
- verify_firebase_token(id_token) -> dict  calls auth.verify_id_token() or, in DEBUG/mock mode,
  decodes without verification (logs warning). Returns dict {uid, phone_number, email... } or raises 401.
- get_current_user(Authorization header) -> dict  FastAPI dependency that extracts Bearer token,
  verifies it, fetches artisan via supabase_service.get_artisan_by_uid(uid).
"""

import base64
import json
import logging
import os
from typing import Any, Dict, Optional

from fastapi import Depends, Header, HTTPException, Request, status

logger = logging.getLogger(__name__)

# firebase_admin is optional for local dev without credentials
try:
    import firebase_admin  # type: ignore
    from firebase_admin import auth, credentials  # type: ignore
except ImportError:  # pragma: no cover
    firebase_admin = None  # type: ignore
    auth = None  # type: ignore
    credentials = None  # type: ignore

# Module flag for init once
_firebase_initialized: bool = False


def initialize_firebase() -> bool:
    """
    Initialize Firebase Admin SDK once from Settings/env.

    Reads:
      - FIREBASE_CREDENTIALS_JSON (inline JSON string) preferred
      - FIREBASE_CREDENTIALS_PATH (path to service-account json)

    Returns True if initialized (or already initialized), False if skipped (dev mock mode).
    Never raises — logs warning and allows dev mock instead.
    """
    global _firebase_initialized

    # If already initialized, short-circuit
    if _firebase_initialized:
        return True
    if firebase_admin is not None:
        try:
            if firebase_admin._apps:  # type: ignore[attr-defined]
                _firebase_initialized = True
                logger.info("Firebase Admin already initialized")
                return True
        except Exception:
            pass

    if firebase_admin is None or credentials is None:
        logger.warning(
            "firebase-admin not installed — running in mock auth mode. "
            "Install with: pip install firebase-admin"
        )
        return False

    # Resolve settings / env
    creds_json: Optional[str] = None
    creds_path: Optional[str] = None
    debug_mode: bool = False

    try:
        from app.core.config import get_settings

        settings = get_settings()
        creds_json = settings.FIREBASE_CREDENTIALS_JSON
        creds_path = settings.FIREBASE_CREDENTIALS_PATH
        debug_mode = bool(settings.DEBUG)
    except Exception as exc:
        logger.debug("Failed to read Settings for Firebase init: %s", exc)
        creds_json = os.getenv("FIREBASE_CREDENTIALS_JSON")
        creds_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
        debug_mode = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes", "on")

    # 1) Try inline JSON
    if creds_json:
        creds_json = creds_json.strip()
        if creds_json:
            try:
                # creds_json may be a JSON string or already dict-like
                if creds_json.startswith("{"):
                    cred_dict = json.loads(creds_json)
                else:
                    # Might be base64-encoded
                    try:
                        decoded = base64.b64decode(creds_json).decode("utf-8")
                        cred_dict = json.loads(decoded)
                    except Exception:
                        cred_dict = json.loads(creds_json)
                cred = credentials.Certificate(cred_dict)  # type: ignore
                firebase_admin.initialize_app(cred)  # type: ignore
                _firebase_initialized = True
                logger.info("Firebase Admin initialized via FIREBASE_CREDENTIALS_JSON")
                return True
            except Exception as exc:
                logger.warning("Failed to initialize Firebase via FIREBASE_CREDENTIALS_JSON: %s", exc)
                if not debug_mode:
                    # In production, surface but don't crash hard — allow mock fallback with warning
                    logger.error("Firebase init failed with JSON creds (non-debug mode still continuing in mock): %s", exc)

    # 2) Try file path
    if creds_path:
        creds_path = creds_path.strip()
        if creds_path and os.path.isfile(creds_path):
            try:
                cred = credentials.Certificate(creds_path)  # type: ignore
                firebase_admin.initialize_app(cred)  # type: ignore
                _firebase_initialized = True
                logger.info("Firebase Admin initialized via FIREBASE_CREDENTIALS_PATH=%s", creds_path)
                return True
            except Exception as exc:
                logger.warning("Failed to initialize Firebase via FIREBASE_CREDENTIALS_PATH=%s: %s", creds_path, exc)
        else:
            logger.warning(
                "FIREBASE_CREDENTIALS_PATH=%s not found or not a file — skipping Firebase init (dev mock mode)",
                creds_path,
            )
            if not debug_mode:
                logger.warning("Firebase credentials missing in non-debug mode — auth will fail for real tokens")

    # 3) No creds — dev mock mode
    if debug_mode:
        logger.warning(
            "Firebase credentials not configured — running in DEBUG mock auth mode. "
            "Tokens will be decoded WITHOUT verification. DO NOT use in production."
        )
    else:
        logger.warning(
            "Firebase credentials not configured — Firebase Admin not initialized. "
            "Set FIREBASE_CREDENTIALS_PATH or FIREBASE_CREDENTIALS_JSON."
        )
    return False


def _is_debug_mock_allowed() -> bool:
    """Return True if DEBUG/mock decode is allowed (development)."""
    try:
        from app.core.config import get_settings

        settings = get_settings()
        return bool(settings.DEBUG) or settings.APP_ENV.lower() != "production"
    except Exception:
        return os.getenv("DEBUG", "false").lower() in ("true", "1", "yes", "on") or os.getenv(
            "APP_ENV", "development"
        ).lower() != "production"


def _decode_jwt_without_verify(token: str) -> Dict[str, Any]:
    """
    Decode JWT payload without verifying signature — DEBUG only.
    Returns payload dict or raises.
    """
    try:
        # JWT = header.payload.signature  (base64url)
        parts = token.split(".")
        if len(parts) < 2:
            raise ValueError("Invalid JWT structure")
        payload_b64 = parts[1]
        # Pad base64
        payload_b64 += "=" * (-len(payload_b64) % 4)
        payload_bytes = base64.urlsafe_b64decode(payload_b64)
        payload = json.loads(payload_bytes.decode("utf-8"))
        return payload
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Mock token decode failed: {exc}",
        ) from exc


def verify_firebase_token(id_token: str) -> Dict[str, Any]:
    """
    Verify Firebase ID token and return claims dict.

    Returns dict with at least: uid, phone_number, email (if present), name, firebase claims.
    Raises HTTPException 401 on failure.

    In DEBUG/mock mode (no Firebase init or DEBUG=true), will decode without verification
    as placeholder but logs a warning. In production with no creds, still raises 401 unless
    mock allowed.
    """
    if not id_token or not id_token.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Firebase ID token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    id_token = id_token.strip()

    # If Firebase is initialized, do real verification
    is_initialized = False
    if firebase_admin is not None:
        try:
            is_initialized = bool(firebase_admin._apps)  # type: ignore[attr-defined]
        except Exception:
            is_initialized = _firebase_initialized

    if is_initialized and auth is not None:
        try:
            decoded = auth.verify_id_token(id_token)  # type: ignore
            # Normalize to our return shape
            uid = decoded.get("uid") or decoded.get("sub") or decoded.get("user_id")
            if not uid:
                raise ValueError("Decoded token missing uid/sub")
            return {
                "uid": uid,
                "phone_number": decoded.get("phone_number"),
                "email": decoded.get("email"),
                "name": decoded.get("name"),
                "email_verified": decoded.get("email_verified"),
                "firebase": decoded,  # full claims for downstream use
            }
        except HTTPException:
            raise
        except Exception as exc:
            logger.warning("Firebase token verification failed: %s", exc)
            # In debug, allow fallback to mock decode; otherwise 401
            if _is_debug_mock_allowed():
                logger.warning("DEBUG mode — falling back to mock decode for token (INSECURE)")
                try:
                    payload = _decode_jwt_without_verify(id_token)
                except HTTPException:
                    # Opaque token in debug — fabricate payload
                    payload = {"phone_number": None, "uid": f"mock-{id_token[-8:]}" if len(id_token) >= 8 else "mock-uid"}
                    logger.warning("Opaque mock token — fabricated uid=%s (DEBUG ONLY)", payload["uid"])
                uid = payload.get("uid") or payload.get("sub") or payload.get("user_id") or payload.get("phone_number") or "mock-uid"
                # For mock, fabricate deterministic uid if needed
                if uid == "mock-uid" and payload.get("phone_number"):
                    uid = f"mock-{payload.get('phone_number')}"
                if uid == "mock-uid":
                    suffix = id_token[-8:] if len(id_token) >= 8 else id_token
                    uid = f"mock-{suffix}"
                logger.warning("Mock decoded token uid=%s (DEBUG ONLY)", uid)
                return {
                    "uid": uid,
                    "phone_number": payload.get("phone_number"),
                    "email": payload.get("email"),
                    "name": payload.get("name"),
                    "email_verified": payload.get("email_verified"),
                    "firebase": payload,
                    "_mock": True,
                }
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid Firebase ID token: {exc}",
                headers={"WWW-Authenticate": "Bearer"},
            ) from exc

    # Firebase not initialized — try mock if allowed
    if _is_debug_mock_allowed():
        logger.warning("Firebase not initialized — decoding token WITHOUT verification (DEBUG mock mode)")
        try:
            payload = _decode_jwt_without_verify(id_token)
        except HTTPException:
            # Opaque token (not JWT) — fabricate payload for dev testing
            payload = {"phone_number": None, "uid": None, "email": None, "name": None}
            logger.warning("Opaque token received — fabricating mock payload (DEBUG ONLY)")
        uid = (
            payload.get("uid")
            or payload.get("sub")
            or payload.get("user_id")
            or payload.get("phone_number")
            or "mock-uid"
        )
        if uid == "mock-uid" and payload.get("phone_number"):
            uid = f"mock-{payload.get('phone_number')}"
        # If token is opaque (not JWT), fabricate from raw token suffix for dev
        if uid == "mock-uid":
            # Use last 8 chars of token as pseudo-uid for testing
            suffix = id_token[-8:] if len(id_token) >= 8 else id_token
            uid = f"mock-{suffix}"
            payload.setdefault("phone_number", None)
        logger.warning("Mock decoded token uid=%s phone=%s (DEBUG ONLY)", uid, payload.get("phone_number"))
        return {
            "uid": uid,
            "phone_number": payload.get("phone_number"),
            "email": payload.get("email"),
            "name": payload.get("name"),
            "email_verified": payload.get("email_verified"),
            "firebase": payload,
            "_mock": True,
        }

    # Production without Firebase — hard fail
    logger.error("Firebase not initialized and mock not allowed — rejecting token")
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication service not configured",
        headers={"WWW-Authenticate": "Bearer"},
    )


# ── Optional auth helper (centralized for Phase C) ─────────────────────
# NOTE: pricing previously duplicated this dependency. It is now canonical here
# to avoid DI duplication (get_current_user vs get_optional_current_user) and to
# keep token-handling / PII rules single-sourced. pricing still re-exports it
# for backwards compat (from app.api.pricing import get_optional_current_user).


async def get_optional_current_user(
    request: Any = None,  # type: ignore — FastAPI injects Request; Any keeps optional for direct calls
    authorization: Optional[str] = Header(default=None, description="Bearer <Firebase ID Token>"),
) -> Optional[Dict[str, Any]]:
    """
    Optional auth dependency — returns user dict if Authorization present,
    None if missing. If token present but invalid, raises 401.

    Centralized (Phase C): previously duplicated in `app.api.pricing`.
    Respects `app.dependency_overrides[get_current_user]` for tests so
    TestClient overrides continue to work when called as `Depends(get_optional_current_user)`.

    SECURITY: Never logs raw token. Logs only truncated uid / mock warnings.
    ASYNC NOTE: Underlying `verify_firebase_token` and `get_artisan_by_uid`
    are synchronous (Supabase postgrest / Firebase Admin). For strict async
    correctness run them in `starlette.concurrency.run_in_threadpool` or
    `asyncio.to_thread` to avoid blocking the event loop. Current sync calls are
    kept for backward compat and small-request workload; a threadpool wrapper
    is provided as comment for future scale.

    Request injection: FastAPI will inject `Request` when used as dependency
    `Depends(get_optional_current_user)`. We accept `Any` to stay compatible
    with direct calls where only `authorization` is supplied.
    """
    # Detect if first arg is actually Request (has .app) or is missing/authorization string
    actual_request = request
    if isinstance(request, str) or request is None:
        # No Request object — check if authorization holds the request object due to positional swap
        # (get_optional_current_user(request, authorization) vs (authorization))
        # If `authorization` looks like a Request, swap.
        if authorization is not None and hasattr(authorization, "app"):
            actual_request = authorization  # type: ignore
            authorization = None  # type: ignore
        else:
            # Check positional misuse where first string is actually token when caller did
            # get_optional_current_user(authorization_string) without Request
            if isinstance(request, str) and authorization is None:
                authorization = request  # type: ignore
            actual_request = None
    if actual_request is not None and hasattr(actual_request, "app"):
        try:
            overrides = getattr(actual_request.app, "dependency_overrides", {})
            if get_current_user in overrides:
                import inspect as _inspect

                overridden = overrides[get_current_user]
                try:
                    if _inspect.iscoroutinefunction(overridden):
                        try:
                            result = await overridden()  # type: ignore
                        except TypeError:
                            result = await overridden(authorization=authorization)  # type: ignore
                    else:
                        try:
                            result = overridden()  # type: ignore
                        except TypeError:
                            result = overridden(authorization=authorization)  # type: ignore
                        if _inspect.isawaitable(result):
                            result = await result  # type: ignore
                    if isinstance(result, dict):
                        return result
                    return result
                except HTTPException:
                    raise
                except Exception as exc:
                    logger.debug("Overridden get_current_user failed (optional path): %s", exc)
                    # Fall through to normal handling
                    pass
        except Exception:
            pass

    if not authorization:
        return None

    # Parse Bearer
    parts = authorization.strip().split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header. Expected 'Bearer <token>'",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = parts[1].strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Empty Bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # SECURITY: never log `token` itself
    claims = verify_firebase_token(token)
    uid = claims.get("uid")
    # Best-effort artisan fetch (optional for pricing personalization)
    artisan = None
    try:
        from app.services.supabase_service import get_artisan_by_uid

        if uid:
            # ASYNC CORRECTNESS NOTE: get_artisan_by_uid is sync (Supabase postgrest httpx).
            # Under high concurrency wrap with: await run_in_threadpool(lambda: get_artisan_by_uid(uid))
            artisan = get_artisan_by_uid(uid)
    except Exception:
        artisan = None
    return {
        "firebase_uid": uid,
        "phone": claims.get("phone_number"),
        "artisan": artisan,
        "claims": claims,
    }


async def get_current_user(
    authorization: Optional[str] = Header(default=None, description="Bearer <Firebase ID Token>"),
) -> Dict[str, Any]:
    """
    FastAPI dependency: validates Authorization: Bearer <token> header,
    verifies Firebase token, fetches artisan via Supabase.

    Returns dict: {firebase_uid, phone, artisan}
    Raises:
      401 — missing/invalid token
      404 — valid token but no artisan found (user not synced)

    SECURITY: Never logs raw Authorization header / id_token. Logs only uid suffix for mock.
    ASYNC CORRECTNESS: verify_firebase_token (Firebase Admin sync) and get_artisan_by_uid
    (Supabase sync) currently block the event loop. For 100k+ scale, offload to
    `starlette.concurrency.run_in_threadpool` — see comment inside.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Parse Bearer token
    parts = authorization.strip().split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header. Expected 'Bearer <token>'",
            headers={"WWW-Authenticate": "Bearer"},
        )
    id_token = parts[1].strip()
    if not id_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Empty Bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify token
    claims = verify_firebase_token(id_token)
    uid: str = claims.get("uid")  # type: ignore
    phone_number: Optional[str] = claims.get("phone_number")

    if not uid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing uid",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Fetch artisan via Supabase
    try:
        from app.services.supabase_service import get_artisan_by_uid

        artisan = get_artisan_by_uid(uid)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Failed to fetch artisan for uid=%s: %s", uid, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch user profile",
        ) from exc

    if artisan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artisan profile not found. Call POST /api/v1/auth/sync-user first.",
        )

    return {
        "firebase_uid": uid,
        "phone": phone_number or artisan.get("phone"),
        "artisan": artisan,
        "claims": claims,
    }


# ── Enterprise Brute-Force Protection & Rate Limiting (Phase 8) ──────────────

class BruteForceLimiter:
    """
    In-memory rate limiter and brute-force attempt tracker.
    Blocks IP / User after consecutive failed authentication attempts.
    """

    def __init__(self, max_attempts: int = 5, window_seconds: int = 300, lockout_seconds: int = 900):
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self.lockout_seconds = lockout_seconds
        self._failed_attempts: Dict[str, List[float]] = {}
        self._lockouts: Dict[str, float] = {}

    def is_locked_out(self, key: str) -> tuple[bool, int]:
        """Returns (is_locked, remaining_seconds_locked)."""
        import time
        now = time.time()
        if key in self._lockouts:
            locked_until = self._lockouts[key]
            if now < locked_until:
                return True, int(locked_until - now)
            else:
                del self._lockouts[key]
                self._failed_attempts.pop(key, None)
        return False, 0

    def record_failure(self, key: str) -> bool:
        """Records failed attempt. Returns True if key is now locked out."""
        import time
        now = time.time()
        attempts = self._failed_attempts.get(key, [])
        # Filter attempts within window
        attempts = [t for t in attempts if now - t <= self.window_seconds]
        attempts.append(now)
        self._failed_attempts[key] = attempts

        if len(attempts) >= self.max_attempts:
            self._lockouts[key] = now + self.lockout_seconds
            logger.warning("🚨 Brute-force lockout triggered for key=%s (locked for %ds)", key, self.lockout_seconds)
            return True
        return False

    def record_success(self, key: str) -> None:
        """Clears failed attempts on successful authentication."""
        self._failed_attempts.pop(key, None)
        self._lockouts.pop(key, None)

    def reset(self) -> None:
        self._failed_attempts.clear()
        self._lockouts.clear()


# Global singleton brute-force limiter
brute_force_limiter = BruteForceLimiter()


def check_brute_force(key: str) -> None:
    """Dependency / helper to abort if IP or username is locked out."""
    locked, remaining = brute_force_limiter.is_locked_out(key)
    if locked:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many failed attempts. Account temporarily locked. Try again in {remaining} seconds.",
            headers={"Retry-After": str(remaining)},
        )

