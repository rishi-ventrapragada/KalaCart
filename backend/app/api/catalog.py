"""
Catalog API — Smart Catalog Generation via Qwen 3 / OpenRouter.

POST /api/v1/catalog/generate
- Auth required (Bearer Firebase token via get_current_user)
- Rate limit: 10 req / 60s per IP-or-artisan (in-memory window)
- Input: transcript (5-1000 chars, control chars stripped), language te|hi|en|ta|kn
- Calls OpenRouter qwen/qwen3-32b with catalog_system.md prompt, temperature 0.7, max_tokens 800, timeout 30s
- Validates JSON schema, retry once on malformed, 502 on persistent failure
- Never exposes OPENROUTER_API_KEY in response/logs

Do NOT modify Camera Studio. Do NOT implement pricing/marketplace.
"""

import json
import logging
import os
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field, field_validator

from app.core.config import get_settings
from app.core.security import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()

# ── Constants ──────────────────────────────────────────────────────────
ALLOWED_CATEGORIES = [
    "Textiles",
    "Pottery",
    "Woodwork",
    "Metalwork",
    "Jewelry",
    "Painting",
    "Basketry",
    "Leather",
    "Other",
]
ALLOWED_LANGUAGES = ["te", "hi", "en", "ta", "kn"]

_RATE_LIMIT_MAX = 10
_RATE_LIMIT_WINDOW_SECONDS = 60
# In-memory limiter: key -> list[timestamps]
_rate_limit_store: Dict[str, List[float]] = {}

_PROMPT_PATH = Path(__file__).parent.parent / "ai" / "prompts" / "catalog_system.md"

# ── Rate limiter helpers (Phase C: consolidated via app.core.rate_limit) ──
# This module keeps its own store (10/min) but delegates algorithm to shared
# helper so pruning, headers, and logging stay consistent across services.
from app.core.rate_limit import (
    check_rate_limit as _shared_check_rate_limit,
    clear_rate_limit_store as _shared_clear,
    get_rate_limit_key as _shared_get_key,
)


def _get_rate_limit_key(request: Request, current_user: Optional[Dict[str, Any]]) -> str:
    """Derive rate-limit key: prefer artisan uid, fallback to client IP."""
    # Delegated to shared helper — preserves prior behavior (without X-Forwarded-For)
    # Keep simple wrapper for backwards compat with tests that patch this function
    return _shared_get_key(request, current_user)


def _check_rate_limit(key: str) -> None:
    """Enforce 10 req / 60s sliding window. Raises 429 if exceeded."""
    # Shared helper handles pruning, Retry-After, and bounded store growth
    _shared_check_rate_limit(
        _rate_limit_store,
        key,
        _RATE_LIMIT_MAX,
        _RATE_LIMIT_WINDOW_SECONDS,
        detail_prefix="Rate limit exceeded",
    )


def _clear_rate_limit_store() -> None:
    """For tests — reset limiter."""
    _shared_clear(_rate_limit_store)


# ── Pydantic models ────────────────────────────────────────────────────

class GenerateCatalogRequest(BaseModel):
    """
    Input for POST /api/v1/catalog/generate

    - transcript: 5-1000 chars, control chars \\x00-\\x1f stripped, trimmed
    - language: te|hi|en|ta|kn (default te)
    """

    transcript: str = Field(
        ...,
        min_length=5,
        max_length=1000,
        description="Artisan voice transcript (5-1000 chars, control chars stripped)",
        examples=["Nenu cotton tho handloom saree chesanu, natural dyes vadenu, Warangal nunchi"],
    )
    language: str = Field(
        default="te",
        pattern=r"^(te|hi|en|ta|kn)$",
        description="Language hint: te|hi|en|ta|kn",
        examples=["te"],
    )

    @field_validator("transcript", mode="before")
    @classmethod
    def strip_control_and_trim(cls, v: Any) -> str:
        if not isinstance(v, str):
            v = str(v) if v is not None else ""
        # Strip control characters \x00-\x1f and \x7f, then trim
        v = re.sub(r"[\x00-\x1f\x7f]", "", v)
        v = v.strip()
        return v

    @field_validator("transcript")
    @classmethod
    def validate_transcript_length(cls, v: str) -> str:
        # After stripping, enforce 5-1000
        if len(v) < 5:
            raise ValueError("transcript must be at least 5 characters after stripping control chars and whitespace")
        if len(v) > 1000:
            raise ValueError("transcript must be at most 1000 characters")
        return v

    @field_validator("language", mode="before")
    @classmethod
    def normalize_language(cls, v: Any) -> str:
        if v is None:
            return "te"
        if not isinstance(v, str):
            v = str(v)
        v = v.strip().lower()
        return v


class CatalogData(BaseModel):
    title: str
    description_en: str
    description_hi: str
    category: str
    materials: List[str]
    seo_tags: List[str]
    care: str


class GenerateCatalogResponse(BaseModel):
    success: bool = True
    data: CatalogData


# ── Validation & parsing helpers (mirror app/ai/catalog.py) ────────────

def _strip_code_fences(text: str) -> str:
    if not text:
        return text
    t = text.strip()
    if t.startswith("```"):
        t = re.sub(r"^```(?:json)?\s*", "", t, flags=re.IGNORECASE)
        t = re.sub(r"\s*```\s*$", "", t)
        t = t.strip()
    start = t.find("{")
    end = t.rfind("}")
    if start != -1 and end != -1 and end > start:
        t = t[start : end + 1]
    return t.strip()


def _validate_catalog_schema(data: Dict[str, Any]) -> tuple[bool, str]:
    if not isinstance(data, dict):
        return False, "Root must be JSON object"
    required = ["title", "description_en", "description_hi", "category", "materials", "seo_tags", "care"]
    for key in required:
        if key not in data:
            return False, f"Missing required key: {key}"
    title = data.get("title")
    if not isinstance(title, str) or not (5 <= len(title.strip()) <= 80):
        return False, "title must be string 5-80 chars"
    de = data.get("description_en")
    if not isinstance(de, str) or not (20 <= len(de.strip()) <= 500):
        return False, "description_en must be string 20-500 chars"
    dh = data.get("description_hi")
    if not isinstance(dh, str) or not (20 <= len(dh.strip()) <= 500):
        return False, "description_hi must be string 20-500 chars"
    cat = data.get("category")
    if cat not in ALLOWED_CATEGORIES:
        return False, f"category must be one of {ALLOWED_CATEGORIES}"
    mats = data.get("materials")
    if not isinstance(mats, list) or not (1 <= len(mats) <= 5):
        return False, "materials must be list 1-5 items"
    for m in mats:
        if not isinstance(m, str) or not m.strip() or len(m.strip()) > 30:
            return False, "each material must be non-empty string <=30 chars"
    tags = data.get("seo_tags")
    if not isinstance(tags, list) or not (2 <= len(tags) <= 5):
        return False, "seo_tags must be list 2-5 items"
    for t in tags:
        if not isinstance(t, str) or not (2 <= len(t.strip()) <= 30):
            return False, "each seo_tag must be string 2-30 chars"
    lowered = [t.strip().lower() for t in tags]
    if len(lowered) != len(set(lowered)):
        return False, "seo_tags must be unique"
    care = data.get("care")
    if not isinstance(care, str) or not (5 <= len(care.strip()) <= 200):
        return False, "care must be string 5-200 chars"
    return True, ""


def _load_system_prompt() -> str:
    """Load catalog_system.md — fallback to embedded minimal prompt."""
    fallback = (
        "You are KalaCart's Smart Catalog Assistant (Qwen 3). "
        "Preserve artisan meaning, never invent materials, generate concise professional English (80-150 words), "
        "natural Hindi (Devanagari, preserve cultural terms), return valid JSON only with schema "
        "{title, description_en, description_hi, category, materials[], seo_tags[], care}. "
        "Categories allowed: [Textiles, Pottery, Woodwork, Metalwork, Jewelry, Painting, Basketry, Leather, Other]. "
        "Return JSON only, no markdown. "
        'Example: {"title":"Handloom Cotton Saree","description_en":"Handwoven...","description_hi":"वारंगल में...","category":"Textiles","materials":["Cotton"],"seo_tags":["Handmade","Cotton","Sustainable"],"care":"Hand wash cold"}'
    )
    try:
        if _PROMPT_PATH.exists():
            content = _PROMPT_PATH.read_text(encoding="utf-8")
            if content and content.strip():
                return content
    except Exception as exc:
        logger.warning("Failed to read catalog_system.md: %s", exc)
    logger.warning("Using fallback catalog system prompt (file not found: %s)", _PROMPT_PATH)
    return fallback


async def _call_openrouter(
    system_prompt: str,
    transcript: str,
    language: str,
    is_retry: bool = False,
) -> str:
    """Call OpenRouter chat/completions. Never logs API key."""
    settings = get_settings()
    api_key = settings.OPENROUTER_API_KEY or os.getenv("OPENROUTER_API_KEY")
    base_url = settings.OPENROUTER_BASE_URL or os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    model = settings.QWEN_MODEL or os.getenv("QWEN_MODEL", "qwen/qwen3-32b")

    if not api_key:
        logger.error("OPENROUTER_API_KEY not configured")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI service not configured (missing API key)",
        )

    # Build messages — on retry add strict instruction
    sys_content = system_prompt
    if is_retry:
        sys_content += (
            "\n\n[STRICT RETRY] Your previous output was invalid JSON. "
            "Return valid JSON only following schema "
            "{title, description_en, description_hi, category, materials[], seo_tags[], care} "
            "with no markdown, no code fences, no commentary. "
            "Categories allowed: [Textiles, Pottery, Woodwork, Metalwork, Jewelry, Painting, Basketry, Leather, Other]. "
            "Title 5-80 chars, description_en 20-500 (80-150 words), description_hi 20-500, "
            "materials 1-5 strings, seo_tags 2-5 strings, care 5-200."
        )

    user_content = (
        f"Language hint: {language}\n"
        f"Transcript: \"{transcript}\"\n\n"
        "Generate catalog JSON now. Return JSON only, no markdown."
    )

    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://kalacart.in",
        "X-Title": "KalaCart",
        "Content-Type": "application/json",
    }
    payload: Dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": sys_content},
            {"role": "user", "content": user_content},
        ],
        "temperature": 0.7,
        "max_tokens": 800,
    }

    url = f"{base_url.rstrip('/')}/chat/completions"
    logger.debug("OpenRouter call model=%s (key redacted) retry=%s", model, is_retry)

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, headers=headers, json=payload)
            # Raise for 4xx/5xx
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                # Do NOT include key in logs
                logger.error("OpenRouter HTTP %s for model %s", exc.response.status_code, model)
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="AI service temporarily unavailable (upstream error)",
                ) from exc
            data = response.json()
            try:
                content = data["choices"][0]["message"]["content"]
            except (KeyError, IndexError, TypeError) as exc:
                logger.error("OpenRouter malformed response structure: %s", exc)
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="LLM returned malformed JSON",
                ) from exc
            if not isinstance(content, str) or not content.strip():
                logger.error("OpenRouter empty content")
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="LLM returned malformed JSON",
                )
            return content
    except HTTPException:
        raise
    except httpx.TimeoutException as exc:
        logger.error("OpenRouter timeout: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="AI service timed out",
        ) from exc
    except httpx.RequestError as exc:
        logger.error("OpenRouter request error (key redacted): %s", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI service unavailable",
        ) from exc


# ── Route ──────────────────────────────────────────────────────────────

@router.post(
    "/generate",
    response_model=GenerateCatalogResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate catalog entry from artisan transcript",
    description=(
        "Auth required. Rate limited 10/min per artisan/IP. "
        "Translates + SEO in single Qwen3 call. Validates JSON schema with one retry. "
        "Uses OPENROUTER_API_KEY, model qwen/qwen3-32b, base https://openrouter.ai/api/v1/chat/completions."
    ),
)
async def generate_catalog(
    payload: GenerateCatalogRequest,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Generates structured catalog JSON from artisan voice transcript.

    - Validates transcript (5-1000 chars, control chars stripped)
    - Enforces rate limit 10/min
    - Requires auth (get_current_user)
    - Calls OpenRouter Qwen3 with catalog_system.md prompt
    - Strips markdown fences, parses JSON, validates schema
    - Retry once with strict instruction on invalid JSON
    - Returns {success:true, data:{...}} or 502/429/422
    """
    # ── Rate limit check (before LLM call) ──────────────────────────
    rate_key = _get_rate_limit_key(request, current_user)
    _check_rate_limit(rate_key)

    transcript = payload.transcript  # already stripped by validator
    language = payload.language

    # Log without PII — only length and language
    artisan_uid = current_user.get("firebase_uid", "unknown") if isinstance(current_user, dict) else "unknown"
    logger.info(
        "Catalog generate request uid=%s lang=%s transcript_len=%d rate_key=%s",
        artisan_uid,
        language,
        len(transcript),
        rate_key,
    )

    system_prompt = _load_system_prompt()

    # ── First attempt ───────────────────────────────────────────────
    try:
        raw = await _call_openrouter(system_prompt, transcript, language, is_retry=False)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Unexpected error calling LLM (key redacted): %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="LLM returned malformed JSON",
        ) from exc

    stripped = _strip_code_fences(raw)
    data: Optional[Dict[str, Any]] = None
    valid = False
    err_msg = ""

    try:
        data = json.loads(stripped)
        valid, err_msg = _validate_catalog_schema(data)
        if not valid:
            logger.warning("First LLM output schema invalid: %s", err_msg)
            data = None
    except json.JSONDecodeError as exc:
        logger.warning("First LLM output invalid JSON: %s — preview: %s", exc, stripped[:400])
        data = None

    if data is not None and valid:
        # Normalize whitespace for response
        data["title"] = data["title"].strip()
        data["description_en"] = data["description_en"].strip()
        data["description_hi"] = data["description_hi"].strip()
        data["care"] = data["care"].strip()
        logger.info("Catalog generate success on first attempt category=%s", data.get("category"))
        return {"success": True, "data": data}

    # ── Retry once ──────────────────────────────────────────────────
    logger.info("Retrying catalog generation with strict JSON instruction (uid=%s)", artisan_uid)
    try:
        raw_retry = await _call_openrouter(system_prompt, transcript, language, is_retry=True)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Unexpected retry error (key redacted): %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="LLM returned malformed JSON",
        ) from exc

    stripped_retry = _strip_code_fences(raw_retry)
    try:
        data_retry = json.loads(stripped_retry)
    except json.JSONDecodeError as exc:
        logger.error("Retry LLM output still invalid JSON: %s — raw preview: %s", exc, stripped_retry[:500])
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="LLM returned malformed JSON",
        ) from exc

    valid_retry, err_retry = _validate_catalog_schema(data_retry)
    if not valid_retry:
        logger.error("Retry LLM output schema invalid: %s — data preview: %s", err_retry, str(data_retry)[:500])
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="LLM returned malformed JSON",
        )

    # Success on retry
    data_retry["title"] = data_retry["title"].strip()
    data_retry["description_en"] = data_retry["description_en"].strip()
    data_retry["description_hi"] = data_retry["description_hi"].strip()
    data_retry["care"] = data_retry["care"].strip()
    logger.info("Catalog generate success on retry category=%s", data_retry.get("category"))
    return {"success": True, "data": data_retry}

