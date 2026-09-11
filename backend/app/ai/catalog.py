"""
AI service: Smart Catalog generation using Qwen 3 via OpenRouter.

Transforms artisan voice transcript + language hint into structured product listing.
Used by POST /api/v1/catalog/generate. Also importable as helper.

Do NOT modify Camera Studio. Do NOT implement pricing/marketplace. Qwen 3 only.
"""

import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List

import httpx

logger = logging.getLogger(__name__)

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

# Prompt file — modular as required
_PROMPT_PATH = Path(__file__).parent / "prompts" / "catalog_system.md"

# Fallback system prompt if file not found (must preserve same rules)
_FALLBACK_SYSTEM_PROMPT = """You are KalaCart's Smart Catalog Assistant (Qwen 3).
Preserve artisan meaning, never invent materials, generate concise professional English (80-150 words),
natural Hindi (Devanagari, preserve cultural terms like Warli/Ikat/Phulkari), and return valid JSON only
with schema {title, description_en, description_hi, category, materials[], seo_tags[], care}.
Categories allowed: [Textiles, Pottery, Woodwork, Metalwork, Jewelry, Painting, Basketry, Leather, Other]
Return JSON only, no markdown, no code fences.
Example: {"title":"Handloom Cotton Saree - Warangal","description_en":"Handwoven in Warangal... (80-150 words)","description_hi":"वारंगल में शुद्ध कॉटन से...","category":"Textiles","materials":["Cotton","Natural Dyes"],"seo_tags":["Handmade","Cotton","Sustainable"],"care":"Hand wash cold, dry in shade"}
Return JSON only, no markdown."""

# ── Helpers ────────────────────────────────────────────────────────────

def _load_system_prompt() -> str:
    """Load catalog_system.md as system prompt. Fallback to embedded if missing."""
    try:
        if _PROMPT_PATH.exists():
            content = _PROMPT_PATH.read_text(encoding="utf-8")
            # Guard: file must be non-empty
            if content and content.strip():
                return content
            logger.warning("catalog_system.md empty — using fallback prompt")
        else:
            logger.warning("catalog_system.md not found at %s — using fallback", _PROMPT_PATH)
    except Exception as exc:
        logger.warning("Failed to read catalog_system.md: %s — using fallback", exc)
    return _FALLBACK_SYSTEM_PROMPT


def _strip_control_chars(text: str) -> str:
    """Strip \\x00-\\x1f control characters and trim."""
    if not isinstance(text, str):
        text = str(text)
    # Remove control chars 0x00-0x1F and 0x7F
    text = re.sub(r"[\x00-\x1f\x7f]", "", text)
    return text.strip()


def _strip_code_fences(text: str) -> str:
    """Strip markdown code fences ```json ... ``` if present and extract JSON substring."""
    if not text:
        return text
    t = text.strip()
    # Remove ```json ... ``` or ``` ... ```
    if t.startswith("```"):
        # Find first { and last } to extract JSON
        # Also handle ```json\n{...}\n```
        # Remove leading fence line
        t = re.sub(r"^```(?:json)?\s*", "", t, flags=re.IGNORECASE)
        t = re.sub(r"\s*```\s*$", "", t)
        t = t.strip()
    # If still contains fences inside, try to extract JSON object via regex
    # Also handle case where LLM added preamble text before JSON
    # Extract outermost {...}
    start = t.find("{")
    end = t.rfind("}")
    if start != -1 and end != -1 and end > start:
        t = t[start : end + 1]
    return t.strip()


def _validate_catalog_schema(data: Dict[str, Any]) -> tuple[bool, str]:
    """Validate catalog JSON schema. Returns (is_valid, error_msg)."""
    if not isinstance(data, dict):
        return False, "Root must be JSON object"

    # Required keys
    required = ["title", "description_en", "description_hi", "category", "materials", "seo_tags", "care"]
    for key in required:
        if key not in data:
            return False, f"Missing required key: {key}"

    # title: 5-80 chars
    title = data.get("title")
    if not isinstance(title, str) or not (5 <= len(title.strip()) <= 80):
        return False, "title must be string 5-80 chars"
    if re.search(r"[\x00-\x1f\x7f]", title):
        return False, "title contains control characters"

    # description_en: 20-500
    de = data.get("description_en")
    if not isinstance(de, str) or not (20 <= len(de.strip()) <= 500):
        return False, "description_en must be string 20-500 chars"

    # description_hi: 20-500
    dh = data.get("description_hi")
    if not isinstance(dh, str) or not (20 <= len(dh.strip()) <= 500):
        return False, "description_hi must be string 20-500 chars"

    # category
    cat = data.get("category")
    if cat not in ALLOWED_CATEGORIES:
        return False, f"category must be one of {ALLOWED_CATEGORIES}"

    # materials: list 1-5 non-empty strings
    mats = data.get("materials")
    if not isinstance(mats, list) or not (1 <= len(mats) <= 5):
        return False, "materials must be list 1-5 items"
    for m in mats:
        if not isinstance(m, str) or not m.strip() or len(m.strip()) > 30:
            return False, "each material must be non-empty string <=30 chars"

    # seo_tags: list 2-5 strings 2-30 chars
    tags = data.get("seo_tags")
    if not isinstance(tags, list) or not (2 <= len(tags) <= 5):
        return False, "seo_tags must be list 2-5 items"
    for t in tags:
        if not isinstance(t, str) or not (2 <= len(t.strip()) <= 30):
            return False, "each seo_tag must be string 2-30 chars"
    # uniqueness case-insensitive
    lowered = [t.strip().lower() for t in tags]
    if len(lowered) != len(set(lowered)):
        return False, "seo_tags must be unique"

    # care: 5-200
    care = data.get("care")
    if not isinstance(care, str) or not (5 <= len(care.strip()) <= 200):
        return False, "care must be string 5-200 chars"

    # No extra validation for word count (80-150) — keep len check only to avoid false negatives
    return True, ""


async def _call_openrouter(
    system_prompt: str,
    transcript: str,
    language: str,
    is_retry: bool = False,
) -> str:
    """
    Call OpenRouter chat/completions with Qwen 3.
    Never logs API key.
    """
    # Resolve settings — prefer Pydantic Settings, fallback to os.getenv
    api_key: str | None = None
    base_url: str = "https://openrouter.ai/api/v1"
    model: str = "qwen/qwen3-32b"

    try:
        from app.core.config import get_settings

        settings = get_settings()
        api_key = settings.OPENROUTER_API_KEY
        base_url = settings.OPENROUTER_BASE_URL or base_url
        model = settings.QWEN_MODEL or model
    except Exception:
        api_key = os.getenv("OPENROUTER_API_KEY")
        base_url = os.getenv("OPENROUTER_BASE_URL", base_url)
        model = os.getenv("QWEN_MODEL", model)

    if not api_key:
        raise ValueError("OPENROUTER_API_KEY not set — configure in .env / Settings")

    # Redact key in logs — never log raw key
    logger.debug("Calling OpenRouter model=%s base=%s (key redacted)", model, base_url)

    # Build messages
    # On retry, add strict instruction
    sys_content = system_prompt
    if is_retry:
        sys_content += (
            "\n\n[STRICT RETRY] Your previous output was invalid JSON. "
            "Return valid JSON only following schema "
            "{title, description_en, description_hi, category, materials[], seo_tags[], care} "
            "with no markdown, no code fences, no commentary. "
            "Categories allowed: [Textiles, Pottery, Woodwork, Metalwork, Jewelry, Painting, Basketry, Leather, Other]. "
            "Ensure title 5-80, description_en 20-500 (80-150 words), description_hi 20-500, "
            "materials 1-5, seo_tags 2-5, care 5-200."
        )

    user_content = f"Language hint: {language}\nTranscript: \"{transcript}\"\n\nGenerate catalog JSON now. Return JSON only, no markdown."

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

    # Log payload without key
    safe_payload = {k: v for k, v in payload.items() if k != "api_key"}
    logger.debug("OpenRouter payload model=%s messages=%s", model, len(payload["messages"]))

    url = f"{base_url.rstrip('/')}/chat/completions"

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(url, headers=headers, json=payload)
        # Raise for 4xx/5xx — let caller handle retry mapping
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            # Never include key in error
            logger.error("OpenRouter HTTP error %s for model %s", exc.response.status_code, model)
            raise
        data = response.json()
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            logger.error("OpenRouter malformed response: %s", exc)
            raise ValueError("OpenRouter returned malformed response structure") from exc
        return content


# ── Public API ─────────────────────────────────────────────────────────

async def generate_catalog_entry(
    transcript: str | None = None,
    language: str = "te",
    *args: Any,
    **kwargs: Any,
) -> dict:
    """
    Generate catalog entry from artisan transcript.

    Args:
        transcript: Voice transcript text (5-1000 chars, will be stripped of control chars).
                    Also accepts `voice_transcript` as alias for backwards compatibility.
        language: Language hint — one of te|hi|en|ta|kn (default te). Also accepts `language_hint`.

    Returns:
        Dict with keys: title, description_en, description_hi, category, materials, seo_tags, care

    Raises:
        ValueError: on invalid input length or LLM malformed JSON after retry
        httpx.HTTPError: on transport failure

    Retry: once if JSON invalid / schema validation fails.
    """
    # ── Backwards compatibility: accept voice_transcript / language_hint / image_context ──
    if transcript is None:
        # Try aliases
        transcript = kwargs.pop("voice_transcript", None) or kwargs.pop("transcript", None)
        if transcript is None and args:
            transcript = args[0] if isinstance(args[0], str) else None

    if not transcript:
        # No transcript at all
        raise ValueError("transcript is required (5-1000 chars)")

    # Language aliases
    if "language_hint" in kwargs and kwargs["language_hint"]:
        language = kwargs["language_hint"]
    if "language_hint" in kwargs:
        kwargs.pop("language_hint", None)
    # Ignore image_context — not used per spec (catalog is transcript-only)
    kwargs.pop("image_context", None)
    kwargs.pop("voice_transcript", None)

    # Sanitize
    transcript = _strip_control_chars(transcript)
    language = str(language).strip().lower() if language else "te"
    if language not in ALLOWED_LANGUAGES:
        # Keep as-is but log — validation will be done at API layer; helper coerces to te
        logger.warning("Unknown language hint '%s' — coercing to 'te'", language)
        # Do not fail hard here; treat as te for prompt but keep original hint for user message?
        # We'll pass original but model prompt handles hint textually
        pass
    if language not in ALLOWED_LANGUAGES:
        language = "te"

    # Validate length after stripping
    if not (5 <= len(transcript) <= 1000):
        raise ValueError(f"transcript must be 5-1000 chars after stripping (got {len(transcript)})")

    system_prompt = _load_system_prompt()

    # ── First attempt ──────────────────────────────────────────────────
    raw = await _call_openrouter(system_prompt, transcript, language, is_retry=False)
    stripped = _strip_code_fences(raw)

    data: Dict[str, Any] | None = None
    try:
        data = json.loads(stripped)
    except json.JSONDecodeError as exc:
        logger.warning("First LLM output invalid JSON: %s — raw preview: %s", exc, stripped[:300])
        data = None

    if data is not None:
        valid, err = _validate_catalog_schema(data)
        if valid:
            logger.info("Catalog generation succeeded on first attempt (category=%s)", data.get("category"))
            return data
        else:
            logger.warning("First LLM output schema invalid: %s — data: %s", err, str(data)[:400])
            data = None

    # ── Retry once with strict instruction ─────────────────────────────
    logger.info("Retrying catalog generation once with strict JSON instruction")
    raw_retry = await _call_openrouter(system_prompt, transcript, language, is_retry=True)
    stripped_retry = _strip_code_fences(raw_retry)

    try:
        data_retry = json.loads(stripped_retry)
    except json.JSONDecodeError as exc:
        logger.error("Retry LLM output still invalid JSON: %s — raw: %s", exc, stripped_retry[:500])
        raise ValueError("LLM returned malformed JSON") from exc

    valid, err = _validate_catalog_schema(data_retry)
    if not valid:
        logger.error("Retry LLM output schema invalid: %s — data: %s", err, str(data_retry)[:500])
        raise ValueError("LLM returned malformed JSON")

    logger.info("Catalog generation succeeded on retry (category=%s)", data_retry.get("category"))
    return data_retry


# Also expose helpers for api layer to reuse validation without import loop
__all__ = [
    "generate_catalog_entry",
    "ALLOWED_CATEGORIES",
    "ALLOWED_LANGUAGES",
    "_validate_catalog_schema",
    "_strip_code_fences",
    "_strip_control_chars",
    "_load_system_prompt",
]

