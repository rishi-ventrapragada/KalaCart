"""
Supabase / PostgreSQL connection helpers.

- get_supabase_client()          -> privileged client (service_role preferred)
- get_supabase_anon_client()     -> anon client for RLS-scoped operations
- get_db_pool()                  -> optional psycopg2 SimpleConnectionPool fallback
- check_supabase_health()        -> liveness check for monitoring

All secrets are sourced from app.core.config.Settings (which loads .env).
Falls back to os.getenv for early startup / testing without circular import.

Phase C audit — async correctness:
- Supabase-py client (`create_client`) is synchronous (uses httpx.Client sync).
  All `get_supabase_client()` callers in async handlers currently block the
  event loop during `.execute()` / storage uploads. This is acceptable for
  low-concurrency MVP but will become a bottleneck at scale. Recommend:
    await starlette.concurrency.run_in_threadpool(lambda: client.table(...).execute())
  or migrate to `supabase` async client (if available) / `asyncio.to_thread`.
- `psycopg2` pool (`get_db_pool`) is intentionally synchronous/thread-safe
  (SimpleConnectionPool). It is currently optional and unused in main paths;
  if adopted, use `psycopg[binary]` async pool (`AsyncConnectionPool`) or
  offload via threadpool. Marked sync-only by design.
- `check_supabase_health()` is declared `async` but internally performs sync
  I/O (`client.table(...).execute()`). Keep async signature for future
  non-blocking swap; callers `await` it without additional executor.
"""

import logging
import os
from functools import lru_cache
from typing import Any, Dict, Optional

from dotenv import load_dotenv

# Ensure .env is loaded before Settings reads it (pydantic-settings also loads, but this covers bare os.getenv fallback)
load_dotenv()

logger = logging.getLogger(__name__)

# Lazy supabase import — allows scaffold without dependency installed
try:
    from supabase import Client, create_client  # type: ignore
except ImportError:  # pragma: no cover
    Client = Any  # type: ignore
    create_client = None  # type: ignore  # noqa: N816

# Optional psycopg2 pool — import lazily
try:
    import psycopg2  # type: ignore
    from psycopg2 import pool as pg_pool  # type: ignore
except ImportError:  # pragma: no cover
    psycopg2 = None  # type: ignore
    pg_pool = None  # type: ignore

# Module-level pool singleton (not lru_cache because we need close semantics)
_db_pool: Optional[Any] = None


def _resolve_supabase_credentials() -> tuple[str, str]:
    """
    Resolve SUPABASE_URL and privileged key from Settings (preferred) or env.
    Raises ValueError if missing.
    """
    url: Optional[str] = None
    key: Optional[str] = None

    # Try Settings first — single source of truth
    try:
        from app.core.config import get_settings

        settings = get_settings()
        url = settings.SUPABASE_URL
        key = settings.supabase_service_key
    except Exception as exc:  # pragma: no cover — defensive fallback
        logger.debug("Failed to read Settings for Supabase credentials: %s", exc)

    # Fallback to raw env if Settings not populated (e.g., tests setting os.environ directly)
    if not url:
        url = os.getenv("SUPABASE_URL")
    if not key:
        # Prefer service_role, fall back to anon
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")

    if not url or not key:
        raise ValueError(
            "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY (or SUPABASE_KEY) must be set. "
            "Configure them in .env — see .env.example"
        )
    return url, key


@lru_cache(maxsize=1)
def get_supabase_client() -> "Client":
    """
    Returns a cached privileged Supabase client (service_role if available).
    Uses SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY (or SUPABASE_KEY fallback).

    Raises:
        RuntimeError  — supabase package not installed
        ValueError    — credentials missing
    """
    if create_client is None:
        raise RuntimeError("supabase package not installed. Run: pip install -r requirements.txt")

    url, key = _resolve_supabase_credentials()
    client: Client = create_client(url, key)
    logger.debug("Supabase privileged client created for %s", url)
    return client


@lru_cache(maxsize=1)
def get_supabase_anon_client() -> "Client":
    """
    Returns a cached anon Supabase client (RLS-enforced).
    Useful for operations that should respect Row Level Security as end-user.

    Falls back to privileged client if anon key not set.
    """
    if create_client is None:
        raise RuntimeError("supabase package not installed. Run: pip install -r requirements.txt")

    # Try Settings / env for anon-specific key
    anon_key: Optional[str] = None
    url: Optional[str] = None
    try:
        from app.core.config import get_settings

        settings = get_settings()
        url = settings.SUPABASE_URL
        anon_key = settings.SUPABASE_KEY
    except Exception:
        pass

    if not url:
        url = os.getenv("SUPABASE_URL")
    if not anon_key:
        anon_key = os.getenv("SUPABASE_KEY")

    # If no anon key, fall back to privileged client (with warning)
    if not anon_key:
        logger.warning("SUPABASE_KEY (anon) not set — anon client falling back to privileged client")
        return get_supabase_client()

    if not url:
        raise ValueError("SUPABASE_URL must be set in environment")

    client: Client = create_client(url, anon_key)
    logger.debug("Supabase anon client created for %s", url)
    return client


def get_db_url() -> str:
    """Returns PostgreSQL connection string from Settings or DATABASE_URL env."""
    db_url: Optional[str] = None
    try:
        from app.core.config import get_settings

        db_url = get_settings().DATABASE_URL
    except Exception:
        pass
    if not db_url:
        db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL not set — required for direct PostgreSQL access")
    return db_url


def get_db_pool(
    minconn: int = 1,
    maxconn: int = 10,
) -> Optional[Any]:
    """
    Returns a psycopg2 SimpleConnectionPool singleton (lazy, optional).
    Returns None if psycopg2 or DATABASE_URL not configured — caller must handle fallback.

    Args:
        minconn: minimum connections in pool
        maxconn: maximum connections in pool

    Thread-safe via psycopg2.pool.SimpleConnectionPool.
    """
    global _db_pool

    if _db_pool is not None:
        return _db_pool

    if pg_pool is None or psycopg2 is None:
        logger.info("psycopg2 not installed — skipping DB pool creation")
        return None

    try:
        dsn = get_db_url()
    except ValueError:
        logger.info("DATABASE_URL not set — DB pool not created (Supabase client-only mode)")
        return None

    try:
        _db_pool = pg_pool.SimpleConnectionPool(minconn, maxconn, dsn=dsn)
        logger.info("PostgreSQL connection pool created (min=%d, max=%d)", minconn, maxconn)
    except Exception as exc:
        logger.error("Failed to create PostgreSQL pool: %s", exc)
        _db_pool = None

    return _db_pool


def close_db_pool() -> None:
    """Closes all connections in the pool — call on app shutdown."""
    global _db_pool
    if _db_pool is not None:
        try:
            _db_pool.closeall()
            logger.info("PostgreSQL pool closed")
        except Exception as exc:
            logger.warning("Error closing DB pool: %s", exc)
        finally:
            _db_pool = None


async def check_supabase_health() -> Dict[str, Any]:
    """
    Health check for Supabase connectivity.

    Tests:
      1. Privileged client can be created
      2. A lightweight query executes (select 1 or artisans head)

    Returns:
        dict with status, latency, and optional error
    """
    import time

    start = time.monotonic()
    try:
        client = get_supabase_client()
        # Lightweight query — count artisans with limit 1 (does not require table to have data)
        # Use head via limit to avoid large payload
        client.table("artisans").select("id").limit(1).execute()
        elapsed_ms = (time.monotonic() - start) * 1000
        return {
            "status": "healthy",
            "supabase_reachable": True,
            "latency_ms": round(elapsed_ms, 2),
        }
    except ValueError as ve:
        # Missing credentials
        elapsed_ms = (time.monotonic() - start) * 1000
        logger.warning("Supabase health check failed — missing config: %s", ve)
        return {
            "status": "unhealthy",
            "supabase_reachable": False,
            "latency_ms": round(elapsed_ms, 2),
            "error": str(ve),
        }
    except Exception as exc:
        elapsed_ms = (time.monotonic() - start) * 1000
        logger.error("Supabase health check failed: %s", exc)
        return {
            "status": "unhealthy",
            "supabase_reachable": False,
            "latency_ms": round(elapsed_ms, 2),
            "error": str(exc),
        }
