"""
Shared sliding-window rate limiting helper — Phase C refactor.

Centralizes the duplicated in-memory limiter previously copy-pasted across
`app.api.catalog`, `app.api.pricing`, `app.api.marketplace`, `app.api.notifications`.

Design for minimal refactor without breaking APIs:
- Each caller keeps its own store dict (isolated per domain / per window).
  This preserves independent limits (catalog 10/min vs pricing 20/min vs enquiry 10/hr).
- This module provides the pure algorithm so bug fixes / pruning / header logic
  evolve in one place.
- Each caller still exposes its own `_check_rate_limit` / `_get_rate_limit_key`
  / `_clear_rate_limit_store` wrappers for backwards-compat with tests that import
  those symbols directly (e.g. `catalog_module._clear_rate_limit_store`).

Scaling note:
  In-memory stores work for single-process dev / tests. For horizontal scaling
  replace with Redis INCR+EXPIRE or a distributed token-bucket and keep this
  module's interface.
"""

import time
import logging
from typing import Dict, List, Optional, Any

from fastapi import HTTPException, Request, status

logger = logging.getLogger(__name__)

# Generic sliding-window check
def check_rate_limit(
    store: Dict[str, List[float]],
    key: str,
    max_requests: int,
    window_seconds: int,
    *,
    detail_prefix: str = "Rate limit exceeded",
) -> None:
    """
    Enforce `max_requests` per `window_seconds` sliding window for `key`.

    Mutates `store` in-place: appends `now` on success, prunes expired.
    Raises HTTPException 429 with Retry-After header on exceeded.

    Args:
        store: dict key -> list[timestamps float] (caller-owned).
        key: rate-limit bucket key, e.g. "uid:abc" or "ip:1.2.3.4".
        max_requests: allowed requests per window.
        window_seconds: window length in seconds.
        detail_prefix: human prefix for error detail.
    """
    now = time.time()
    window_start = now - window_seconds
    timestamps = store.get(key, [])
    # Prune expired entries
    timestamps = [t for t in timestamps if t > window_start]
    if len(timestamps) >= max_requests:
        retry_after = int(timestamps[0] + window_seconds - now) + 1
        retry_after = max(1, retry_after)
        logger.warning(
            "Rate limit exceeded for key=%s (%d/%d in %ds)",
            # Avoid logging PII keys verbatim when uid-based — truncate
            key[:64] if len(key) > 64 else key,
            len(timestamps),
            max_requests,
            window_seconds,
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"{detail_prefix}. Max {max_requests} requests per {window_seconds // 60 or 1} minute(s). Try again in {retry_after}s."
            if window_seconds < 3600
            else f"{detail_prefix}. Max {max_requests} requests per hour. Try again in {retry_after}s.",
            headers={"Retry-After": str(retry_after)},
        )
    timestamps.append(now)
    store[key] = timestamps
    # Lazy cleanup when store grows unbounded
    if len(store) > 10000:
        for k in list(store.keys()):
            vals = store[k]
            filtered = [t for t in vals if t > window_start]
            if not filtered:
                store.pop(k, None)
            else:
                store[k] = filtered


def clear_rate_limit_store(store: Dict[str, List[float]]) -> None:
    """Test helper — clear in-memory store."""
    store.clear()


def get_rate_limit_key(
    request: Request,
    current_user: Optional[Dict[str, Any]],
    *,
    fallback_prefix: str = "ip",
) -> str:
    """
    Derive rate-limit key: prefer artisan/firebase uid, then artisan.id,
    then client IP, then X-Forwarded-For, then anonymous.

    Shared logic extracted from catalog/pricing. Does NOT log token/PII beyond
    truncated key in check_rate_limit path.
    """
    try:
        if current_user:
            # Prefer explicit Firebase UID
            uid = current_user.get("firebase_uid") or current_user.get("uid")
            if uid:
                return f"uid:{uid}"
            artisan = current_user.get("artisan") or {}
            if isinstance(artisan, dict) and artisan.get("id"):
                return f"artisan:{artisan.get('id')}"
            claims = current_user.get("claims") or {}
            if isinstance(claims, dict) and claims.get("uid"):
                return f"uid:{claims.get('uid')}"
    except Exception:
        pass
    # Fallback to IP
    try:
        client_host = request.client.host if getattr(request, "client", None) else None
        if client_host:
            return f"{fallback_prefix}:{client_host}"
    except Exception:
        pass
    # X-Forwarded-For fallback (when behind proxy)
    try:
        fwd = request.headers.get("x-forwarded-for")
        if fwd:
            return f"{fallback_prefix}:{fwd.split(',')[0].strip()}"
    except Exception:
        pass
    return f"{fallback_prefix}:anonymous"
