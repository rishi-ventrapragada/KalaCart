"""
Public API Authentication, Scope Verification, Request Signing (HMAC-SHA256) & Sliding-Window Rate Limiting.
"""

import hashlib
import hmac
import json
import logging
import secrets
import time
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Callable
import jwt

from fastapi import Depends, Header, HTTPException, Request, status
from app.core.config import get_settings
from app.core.rate_limit import check_rate_limit

logger = logging.getLogger(__name__)
settings = get_settings()

# Secret key for Partner JWT signature
JWT_SECRET = settings.SECRET_KEY or "kalacart_partner_platform_super_secret_jwt_key_2026"
JWT_ALGORITHM = "HS256"

# In-memory stores for API keys & usage logs
_API_KEYS_STORE: Dict[str, Dict[str, Any]] = {
    # Seed default sandbox enterprise partner key
    "kc_live_testpartner9999": {
        "id": "key-00000000-0000-0000-0000-000000000001",
        "partner_name": "CraftBazaar Global Integrations",
        "api_key_prefix": "kc_live_test",
        "raw_api_key": "kc_live_testpartner9999",
        "api_key_hash": hashlib.sha256("kc_live_testpartner9999".encode()).hexdigest(),
        "client_secret": "sec_sandbox_998877665544332211",
        "client_secret_hash": hashlib.sha256("sec_sandbox_998877665544332211".encode()).hexdigest(),
        "tier": "enterprise",
        "scopes": [
            "products:read", "products:write",
            "stores:read",
            "orders:read", "orders:write",
            "rfqs:read", "rfqs:write",
            "analytics:read",
            "payments:write",
            "notifications:write",
            "reviews:read", "reviews:write"
        ],
        "rate_limit_per_min": 600,
        "is_active": True,
        "created_at": "2026-09-01T00:00:00Z",
        "last_used_at": None,
    }
}

_PUBLIC_RATE_LIMIT_STORE: Dict[str, List[float]] = {}
_API_USAGE_LOGS: List[Dict[str, Any]] = []


def generate_partner_api_key(partner_name: str, scopes: List[str], tier: str = "standard") -> Dict[str, Any]:
    """Generates a secure API key, prefix, and client secret pair."""
    key_id = f"key-{secrets.token_hex(8)}"
    random_suffix = secrets.token_urlsafe(24)
    raw_api_key = f"kc_live_{random_suffix}"
    client_secret = f"sec_{secrets.token_hex(20)}"
    
    rate_limit = 600 if tier.lower() == "enterprise" else 60
    
    record = {
        "id": key_id,
        "partner_name": partner_name,
        "api_key_prefix": raw_api_key[:12],
        "raw_api_key": raw_api_key,
        "api_key_hash": hashlib.sha256(raw_api_key.encode()).hexdigest(),
        "client_secret": client_secret,
        "client_secret_hash": hashlib.sha256(client_secret.encode()).hexdigest(),
        "tier": tier,
        "scopes": scopes,
        "rate_limit_per_min": rate_limit,
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_used_at": None
    }
    
    _API_KEYS_STORE[raw_api_key] = record
    return record


def create_partner_jwt(client_id: str, client_secret: str, requested_scope: Optional[str] = None) -> Dict[str, Any]:
    """Issues OAuth2 JWT for Client Credentials flow."""
    # Find matching API key record
    matched_key = None
    for k, rec in _API_KEYS_STORE.items():
        if (k == client_id or rec.get("id") == client_id or rec.get("raw_api_key") == client_id):
            if rec.get("client_secret") == client_secret or rec.get("client_secret_hash") == hashlib.sha256(client_secret.encode()).hexdigest():
                matched_key = rec
                break
            
    if not matched_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid client_id or client_secret for OAuth2 token generation",
            headers={"WWW-Authenticate": "Bearer"}
        )

        
    if not matched_key.get("is_active", True):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="API Key has been revoked or deactivated")

    granted_scopes = matched_key.get("scopes", [])
    if requested_scope:
        req_list = requested_scope.split()
        granted_scopes = [s for s in req_list if s in granted_scopes]

    now = datetime.now(timezone.utc)
    expires = now + timedelta(days=1)
    
    payload = {
        "sub": matched_key["id"],
        "partner_name": matched_key["partner_name"],
        "tier": matched_key["tier"],
        "scopes": granted_scopes,
        "iat": int(now.timestamp()),
        "exp": int(expires.timestamp()),
        "iss": "kalacart-public-api"
    }
    
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return {
        "access_token": token,
        "token_type": "Bearer",
        "expires_in": 86400,
        "scope": " ".join(granted_scopes)
    }


def verify_request_signature(
    secret: str,
    timestamp: str,
    body: bytes,
    received_signature: str
) -> bool:
    """
    Validates HMAC-SHA256 request signature:
    Signature = HMAC-SHA256(secret, timestamp + '.' + body)
    """
    if not timestamp or not received_signature:
        return False
        
    # Guard against replay attacks (5 minute window)
    try:
        req_ts = float(timestamp)
        if abs(time.time() - req_ts) > 300:
            logger.warning("Request signature timestamp drift exceeded 300 seconds")
            return False
    except ValueError:
        return False

    message = f"{timestamp}.".encode("utf-8") + body
    expected = hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, received_signature)


class RequirePublicApiAccess:
    """
    FastAPI Security Dependency that authenticates Public API requests via:
    1. X-API-Key header
    2. Authorization: Bearer <Partner JWT>
    3. Enforces scope authorization
    4. Optional HMAC-SHA256 Request Signing
    5. Sliding-window rate limit enforcement
    """

    def __init__(self, required_scopes: Optional[List[str]] = None, require_signature: bool = False):
        self.required_scopes = required_scopes or []
        self.require_signature = require_signature

    async def __call__(
        self,
        request: Request,
        x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
        authorization: Optional[str] = Header(None),
        x_timestamp: Optional[str] = Header(None, alias="X-Timestamp"),
        x_signature: Optional[str] = Header(None, alias="X-Signature-SHA256"),
    ) -> Dict[str, Any]:
        start_time = time.time()
        partner_info = None

        # 1. Authenticate via X-API-Key
        if x_api_key:
            key_hash = hashlib.sha256(x_api_key.encode()).hexdigest()
            for raw_k, rec in _API_KEYS_STORE.items():
                if raw_k == x_api_key or rec.get("api_key_hash") == key_hash:
                    if not rec.get("is_active", True):
                        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="API Key is inactive")
                    partner_info = rec
                    break
            if not partner_info:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API Key provided in X-API-Key")

        # 2. Authenticate via Bearer JWT
        elif authorization and authorization.startswith("Bearer "):
            token = authorization[7:].strip()
            try:
                payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
                partner_info = {
                    "id": payload.get("sub"),
                    "partner_name": payload.get("partner_name"),
                    "tier": payload.get("tier", "standard"),
                    "scopes": payload.get("scopes", []),
                    "rate_limit_per_min": 600 if payload.get("tier") == "enterprise" else 60,
                }
            except jwt.ExpiredSignatureError:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Partner JWT token has expired")
            except Exception as e:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid Partner JWT token: {str(e)}")

        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required. Provide X-API-Key header or Authorization: Bearer <token>",
                headers={"WWW-Authenticate": "Bearer"}
            )

        # 3. Scope Verification
        granted_scopes = partner_info.get("scopes", [])
        for req_scope in self.required_scopes:
            if req_scope not in granted_scopes and "*:*" not in granted_scopes:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient API scope. Required: '{req_scope}'. Granted: {granted_scopes}"
                )

        # 4. Request Signing Verification (HMAC-SHA256)
        if self.require_signature:
            body = await request.body()
            secret = partner_info.get("client_secret") or "sec_sandbox_998877665544332211"
            if not verify_request_signature(secret, x_timestamp or "", body, x_signature or ""):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid HMAC-SHA256 request signature or timestamp drift exceeded"
                )

        # 5. Sliding-Window Rate Limiting
        rate_limit_max = partner_info.get("rate_limit_per_min", 60)
        rate_key = f"key:{partner_info['id']}"
        check_rate_limit(_PUBLIC_RATE_LIMIT_STORE, rate_key, rate_limit_max, 60, detail_prefix="Public API Rate Limit Exceeded")

        # 6. Record Telemetry / Usage
        latency = round((time.time() - start_time) * 1000, 2)
        _API_USAGE_LOGS.append({
            "id": f"log-{secrets.token_hex(6)}",
            "api_key_id": partner_info.get("id"),
            "endpoint": request.url.path,
            "method": request.method,
            "status_code": 200,
            "response_time_ms": latency,
            "ip_address": request.client.host if request.client else "127.0.0.1",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

        return partner_info
