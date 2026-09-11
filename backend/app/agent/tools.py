"""
Tool layer for the KalaCart unified agent.

Each tool is one artisan-facing capability. They are plain async functions with
JSON-serialisable results so the orchestrator can call them directly (fast path)
or expose them as OpenAI-style tool definitions for model-driven routing.

Tools:
  enhance_product_image  — AI-guided studio enhancement (VLM plan + OpenCV execution)
  generate_catalog       — voice transcript -> SEO listing in English + Hindi
  suggest_price          — image + listing -> fair INR price with breakdown

Design note: the vision model only *chooses parameters*; all pixel work is done
by the existing deterministic OpenCV pipeline in app.vision. That keeps output
reproducible and means a hallucinating model can never corrupt an image.
"""

from __future__ import annotations

import base64
import json
import logging
import re
from typing import Any, Dict, List, Optional

from app.agent import models as model_router
from app.agent.models import ModelCall

logger = logging.getLogger(__name__)

# Shared vocabulary — mirrors app/api/catalog.py and app/api/pricing.py so the
# agent can never emit a category the rest of the platform rejects.
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

ALLOWED_LANGUAGES = ["te", "hi", "en", "ta", "kn", "bn", "mr", "gu", "ml", "pa", "or", "as"]

LANGUAGE_NAMES = {
    "te": "Telugu",
    "hi": "Hindi",
    "en": "English",
    "ta": "Tamil",
    "kn": "Kannada",
    "bn": "Bengali",
    "mr": "Marathi",
    "gu": "Gujarati",
    "ml": "Malayalam",
    "pa": "Punjabi",
    "or": "Odia",
    "as": "Assamese",
}


# ── JSON parsing helpers ───────────────────────────────────────────────


def strip_control_chars(text: str) -> str:
    """Remove C0/C1 control characters and trim."""
    if not isinstance(text, str):
        text = str(text)
    return re.sub(r"[\x00-\x1f\x7f]", "", text).strip()


def _balanced_json_objects(text: str) -> List[str]:
    """
    Yield every balanced {...} span in `text`, outermost first.

    Reasoning models narrate before answering, and that prose often contains
    stray braces. A naive first-{ to last-} scan would splice them together, so
    we track depth and respect string literals and escapes.
    """
    spans: List[str] = []
    depth = 0
    start = -1
    in_string = False
    escaped = False

    for index, char in enumerate(text):
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
        elif char == "{":
            if depth == 0:
                start = index
            depth += 1
        elif char == "}":
            if depth > 0:
                depth -= 1
                if depth == 0 and start != -1:
                    spans.append(text[start : index + 1])
                    start = -1

    return spans


def extract_json(raw: str) -> Dict[str, Any]:
    """
    Pull a JSON object out of a model response.

    Free models are inconsistent: some wrap output in markdown fences, and
    reasoning models emit paragraphs of thinking around the answer. We strip
    fences, then scan for balanced objects and return the largest one that
    parses — the answer, rather than a fragment quoted while thinking.

    Raises:
        ValueError: nothing parseable was found.
    """
    if not raw:
        raise ValueError("Empty model response")

    text = raw.strip()

    # Prefer a fenced block when present — models put the final answer there.
    fenced = re.findall(r"```(?:json)?\s*(.+?)```", text, flags=re.DOTALL | re.IGNORECASE)
    for block in reversed(fenced):  # last fence is usually the final answer
        try:
            parsed = json.loads(block.strip())
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            continue

    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    # Largest balanced object wins: the full answer outranks any smaller
    # fragment the model quoted mid-thought.
    candidates = sorted(_balanced_json_objects(text), key=len, reverse=True)
    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            continue

    if candidates:
        raise ValueError("Model returned unparseable JSON")
    raise ValueError("Model response contained no JSON object")


def _clamp(value: Any, low: float, high: float, default: float) -> float:
    """Coerce a model-supplied number into a safe range."""
    try:
        return max(low, min(high, float(value)))
    except (TypeError, ValueError):
        return default


# ── Tool 1: AI Image Enhancer & Studio ─────────────────────────────────

_VISION_SYSTEM_PROMPT = """You are KalaCart's product photography director for Indian handicrafts.

You are shown ONE artisan product photo taken on a phone, often in poor light on a
cluttered household background. Assess it and return a correction plan.

Return JSON ONLY with this exact schema:
{
  "subject": "<short description of the product, max 80 chars>",
  "category": "<one of: Textiles, Pottery, Woodwork, Metalwork, Jewelry, Painting, Basketry, Leather, Other>",
  "materials": ["<visible material>", ...],
  "background_clutter": <0.0-1.0, how cluttered/distracting the background is>,
  "needs_background_removal": <true|false>,
  "brightness_adjust": <-1.0 to 1.0, negative = too bright, positive = too dark/needs lifting>,
  "contrast_adjust": <-1.0 to 1.0>,
  "warmth_adjust": <-1.0 to 1.0, positive = image too cool and needs warming>,
  "sharpness_adjust": <0.0-1.0, how much detail recovery the texture needs>,
  "recommended_ratio": "<1:1 or 4:5>",
  "quality_score": <0-100, current e-commerce readiness>,
  "issues": ["<short issue>", ...],
  "colors": ["<dominant colour name>", ...]
}

Judge honestly — an accurate low score is more useful than flattery.
Return JSON only. No markdown, no code fences, no commentary."""


async def analyze_image(
    image_bytes: bytes,
    mime_type: str = "image/jpeg",
) -> tuple[Dict[str, Any], ModelCall]:
    """
    Ask a free vision model to produce an enhancement plan for a product photo.

    Args:
        image_bytes: Raw image bytes (already validated by the API layer).
        mime_type: MIME type for the data URI.

    Returns:
        (plan dict with normalised/clamped fields, ModelCall telemetry)
    """
    b64 = base64.b64encode(image_bytes).decode("ascii")
    data_uri = f"data:{mime_type};base64,{b64}"

    messages = [
        {"role": "system", "content": _VISION_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Assess this artisan product photo and return the correction plan JSON.",
                },
                {"type": "image_url", "image_url": {"url": data_uri}},
            ],
        },
    ]

    raw, call = await model_router.complete(
        messages,
        task="vision",
        temperature=0.3,
        # Several free VLMs reason before answering; 700 tokens truncated them
        # mid-thought, so the whole vision stage fell back to pipeline defaults.
        max_tokens=1500,
        require_vision=True,
        json_only=True,
        max_models=6,
    )

    plan = extract_json(raw)

    # Clamp every numeric the pipeline will act on — never trust raw model output.
    normalised: Dict[str, Any] = {
        "subject": strip_control_chars(str(plan.get("subject", "Handcrafted product")))[:80],
        "category": plan.get("category")
        if plan.get("category") in ALLOWED_CATEGORIES
        else "Other",
        "materials": [
            strip_control_chars(str(m))[:30]
            for m in (plan.get("materials") or [])
            if str(m).strip()
        ][:5],
        "background_clutter": _clamp(plan.get("background_clutter"), 0.0, 1.0, 0.5),
        "needs_background_removal": bool(plan.get("needs_background_removal", True)),
        "brightness_adjust": _clamp(plan.get("brightness_adjust"), -1.0, 1.0, 0.0),
        "contrast_adjust": _clamp(plan.get("contrast_adjust"), -1.0, 1.0, 0.0),
        "warmth_adjust": _clamp(plan.get("warmth_adjust"), -1.0, 1.0, 0.0),
        "sharpness_adjust": _clamp(plan.get("sharpness_adjust"), 0.0, 1.0, 0.3),
        "recommended_ratio": plan.get("recommended_ratio")
        if plan.get("recommended_ratio") in {"1:1", "4:5"}
        else "1:1",
        "quality_score": int(_clamp(plan.get("quality_score"), 0, 100, 50)),
        "issues": [
            strip_control_chars(str(i))[:120] for i in (plan.get("issues") or [])
        ][:6],
        "colors": [
            strip_control_chars(str(c))[:24] for c in (plan.get("colors") or [])
        ][:5],
    }
    return normalised, call


async def enhance_product_image(
    image_bytes: bytes,
    mime_type: str = "image/jpeg",
    output_format: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Tool 1 — AI Image Enhancer & Studio.

    A vision model inspects the photo and produces a plan; the existing OpenCV
    pipeline then does the actual pixel work (background removal, CLAHE, white
    balance, unsharp mask, compose on white, crop, resize, export).

    If the vision model is unavailable the pipeline still runs with defaults, so
    the artisan always gets an enhanced image — the AI plan is an improvement,
    not a hard dependency.

    Returns:
        dict with the enhancement plan, output image bytes, and dimensions.
    """
    plan: Dict[str, Any] = {}
    call: Optional[ModelCall] = None
    plan_error: Optional[str] = None

    try:
        plan, call = await analyze_image(image_bytes, mime_type)
    except Exception as exc:
        # Degrade gracefully — the deterministic pipeline can run without a plan.
        plan_error = str(exc)
        logger.warning("Vision analysis failed (%s) — using pipeline defaults", exc)
        plan = {
            "subject": "Handcrafted product",
            "category": "Other",
            "materials": [],
            "needs_background_removal": True,
            "recommended_ratio": "1:1",
            "quality_score": 50,
            "issues": [],
            "colors": [],
        }

    ratio = output_format or plan.get("recommended_ratio") or "1:1"
    if ratio not in {"1:1", "4:5"}:
        ratio = "1:1"

    from app.vision.pipeline import process_image_pipeline

    result = await process_image_pipeline(
        image_bytes=image_bytes,
        output_format=ratio,
        enhance=True,
    )

    return {
        "plan": plan,
        "plan_error": plan_error,
        "model": call.model if call else None,
        "fallbacks": call.attempts if call else [],
        "enhanced_bytes": result.get("enhanced_bytes"),
        "webp_bytes": result.get("webp_bytes"),
        "thumbnail_bytes": result.get("thumbnail_bytes"),
        "width": result.get("width"),
        "height": result.get("height"),
        "ratio": ratio,
    }


# ── Tool 2: Multilingual Auto-Cataloger ────────────────────────────────

_CATALOG_SYSTEM_PROMPT = """You are KalaCart's Smart Catalog Assistant for Indian artisans.

An artisan has described their handmade product by voice in their own language.
You receive the transcript. Turn it into a professional e-commerce listing.

ABSOLUTE RULES:
- Preserve the artisan's meaning. NEVER invent materials, dimensions, or claims
  they did not make. If a detail is absent, leave it out.
- Keep cultural craft terms intact (Warli, Ikat, Phulkari, Pattachitra, Bidri,
  Kalamkari, Chikankari, Madhubani, Dhokra, Channapatna). Transliterate, never
  translate them away.

LANGUAGE OF EACH FIELD — follow exactly, whatever language the artisan spoke:
- title:        ENGLISH (Latin script). Never Devanagari or any other script.
- description_en: ENGLISH, professional and warm, SEO-friendly, 80-150 words.
- description_hi: HINDI in Devanagari — a real translation, not transliterated
                  English.
- category:     ENGLISH, exactly one of the allowed values below.
- materials:    ENGLISH (e.g. "Cotton", "Natural Dyes" — not "सूती धागा").
- seo_tags:     ENGLISH search terms a buyer would type.
- care:         ENGLISH care instructions.
Only description_hi is in Hindi. Every other field is English.

Return JSON ONLY with this exact schema:
{
  "title": "<5-80 chars, specific and searchable>",
  "description_en": "<80-150 words>",
  "description_hi": "<Devanagari Hindi>",
  "category": "<one of: Textiles, Pottery, Woodwork, Metalwork, Jewelry, Painting, Basketry, Leather, Other>",
  "materials": ["<material>", ...],
  "seo_tags": ["<tag>", ...],
  "care": "<care instructions, 5-200 chars>"
}

Return JSON only. No markdown, no code fences, no commentary."""


def _is_devanagari(text: str, threshold: float = 0.3) -> bool:
    """
    True when `text` is substantially Devanagari.

    Used to keep English-only fields English. The threshold tolerates an
    incidental Hindi craft term inside an otherwise English string.
    """
    if not text:
        return False
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return False
    devanagari = sum(1 for c in letters if "ऀ" <= c <= "ॿ")
    return (devanagari / len(letters)) > threshold


def _validate_catalog(data: Dict[str, Any]) -> tuple[bool, str]:
    """Validate the catalog schema against the same rules the existing API enforces."""
    if not isinstance(data, dict):
        return False, "Root must be a JSON object"

    for key in (
        "title",
        "description_en",
        "description_hi",
        "category",
        "materials",
        "seo_tags",
        "care",
    ):
        if key not in data:
            return False, f"Missing required key: {key}"

    title = data.get("title")
    if not isinstance(title, str) or not (5 <= len(title.strip()) <= 80):
        return False, "title must be a string of 5-80 chars"
    # The title anchors search and the marketplace UI, so it must be English
    # even when the artisan spoke Hindi. Free models drift here roughly one run
    # in three; the retry with this message reliably corrects it.
    if _is_devanagari(title):
        return False, "title must be in English, not Devanagari"

    for field_name, lo, hi in (("description_en", 20, 2000), ("description_hi", 20, 2000)):
        value = data.get(field_name)
        if not isinstance(value, str) or not (lo <= len(value.strip()) <= hi):
            return False, f"{field_name} must be a string of {lo}-{hi} chars"

    # Guard against the two descriptions being swapped or both emitted in one
    # language — the bilingual listing is the whole point of this feature.
    if _is_devanagari(data["description_en"]):
        return False, "description_en must be in English"
    if not _is_devanagari(data["description_hi"]):
        return False, "description_hi must be in Devanagari Hindi"

    if data.get("category") not in ALLOWED_CATEGORIES:
        return False, f"category must be one of {ALLOWED_CATEGORIES}"

    materials = data.get("materials")
    if not isinstance(materials, list) or not (1 <= len(materials) <= 8):
        return False, "materials must be a list of 1-8 items"

    tags = data.get("seo_tags")
    if not isinstance(tags, list) or not (2 <= len(tags) <= 10):
        return False, "seo_tags must be a list of 2-10 items"

    care = data.get("care")
    if not isinstance(care, str) or not (5 <= len(care.strip()) <= 300):
        return False, "care must be a string of 5-300 chars"

    return True, ""


async def generate_catalog(
    transcript: str,
    language: str = "hi",
    image_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Tool 2 — Multilingual Auto-Cataloger.

    Args:
        transcript: Voice transcript in the artisan's language (5-2000 chars).
        language: BCP-47-ish language hint for the transcript.
        image_context: Optional plan from `analyze_image` — lets the cataloguer
            ground itself in what the photo actually shows.

    Returns:
        Validated listing dict plus `_model` / `_fallbacks` provenance keys.

    Raises:
        ValueError: transcript invalid, or the model failed schema validation twice.
    """
    transcript = strip_control_chars(transcript)
    if not (5 <= len(transcript) <= 2000):
        raise ValueError(
            f"transcript must be 5-2000 chars after cleaning (got {len(transcript)})"
        )

    language = (language or "hi").strip().lower()
    language_label = LANGUAGE_NAMES.get(language, language)

    context_block = ""
    if image_context:
        visible = ", ".join(image_context.get("materials") or []) or "not clear"
        context_block = (
            "\n\nThe product photo shows: "
            f"{image_context.get('subject', 'unknown')}. "
            f"Visible materials: {visible}. "
            f"Photo suggests category: {image_context.get('category', 'Other')}.\n"
            "Use this only to confirm details the artisan mentioned — do not add "
            "claims from the photo alone."
        )

    user_content = (
        f"Artisan's spoken language: {language_label} ({language})\n"
        f'Voice transcript: "{transcript}"'
        f"{context_block}\n\n"
        "Generate the catalog listing JSON now."
    )

    messages: List[Dict[str, Any]] = [
        {"role": "system", "content": _CATALOG_SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]

    raw, call = await model_router.complete(
        messages, task="catalog", temperature=0.7, max_tokens=1400, json_only=True
    )

    data: Optional[Dict[str, Any]] = None
    try:
        candidate = extract_json(raw)
        valid, err = _validate_catalog(candidate)
        if valid:
            data = candidate
        else:
            logger.warning("Catalog schema invalid on first attempt: %s", err)
    except ValueError as exc:
        logger.warning("Catalog JSON parse failed on first attempt: %s", exc)

    if data is None:
        # One strict retry — a different model may also answer, since the router
        # re-walks the chain from the top.
        messages.append(
            {
                "role": "user",
                "content": (
                    "Your previous reply was not valid. Return ONLY a JSON object "
                    "with keys title, description_en, description_hi, category, "
                    "materials, seo_tags, care. No markdown, no commentary."
                ),
            }
        )
        raw_retry, call = await model_router.complete(
            messages, task="catalog", temperature=0.4, max_tokens=1400, json_only=True
        )
        # Symmetric with the first attempt: a retry that is still unparseable
        # should report as a validation failure, not leak a raw parser message.
        try:
            candidate = extract_json(raw_retry)
        except ValueError as exc:
            raise ValueError(f"Catalog generation failed validation: {exc}") from exc
        valid, err = _validate_catalog(candidate)
        if not valid:
            raise ValueError(f"Catalog generation failed validation: {err}")
        data = candidate

    data["_model"] = call.model
    data["_fallbacks"] = call.attempts
    return data


# ── Tool 3: Dynamic Pricing Assistant ──────────────────────────────────

_PRICING_SYSTEM_PROMPT = """You are KalaCart's pricing analyst for Indian handicrafts.

Suggest a fair selling price in INR. You are given the product listing, visible
materials, the artisan's material cost and labour hours, and the photo's assessed
quality.

PRINCIPLES:
- Never underprice handmade labour. Rural artisan labour is worth at least
  Rs 60/hour; skilled/heritage work Rs 120-250/hour.
- Account for material cost, labour, skill premium, platform commission (~10%),
  and packaging.
- Stay realistic for the Indian D2C handicraft market — an inflated price that
  never sells helps nobody.
- The justification must be plain language an artisan can read and trust.

Return JSON ONLY with this exact schema:
{
  "suggested_price": <integer INR>,
  "price_range": {"min": <integer INR>, "max": <integer INR>},
  "breakdown": {
    "material_cost": <number>,
    "labour_cost": <number>,
    "skill_premium": <number>,
    "platform_fee": <number>,
    "packaging": <number>
  },
  "market_position": "<Budget|Standard|Premium>",
  "confidence": <0.0-1.0>,
  "justification": "<2-3 plain sentences>",
  "factors": ["<factor considered>", ...]
}

Return JSON only. No markdown, no code fences, no commentary."""


async def suggest_price(
    title: str,
    category: str,
    description: str = "",
    materials: Optional[List[str]] = None,
    material_cost: Optional[float] = None,
    labour_hours: Optional[float] = None,
    image_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Tool 3 — Dynamic Pricing Assistant.

    Combines the photo assessment and the generated listing into a fair price
    with a transparent cost breakdown.

    Returns:
        Pricing dict with clamped numerics plus `_model` / `_fallbacks`.

    Raises:
        ValueError: the model produced nothing parseable.
    """
    materials = materials or []
    category = category if category in ALLOWED_CATEGORIES else "Other"

    quality_note = ""
    if image_context:
        quality_note = (
            f"\nPhoto assessment: quality score {image_context.get('quality_score', 'n/a')}/100, "
            f"visible materials: {', '.join(image_context.get('materials') or []) or 'unclear'}, "
            f"dominant colours: {', '.join(image_context.get('colors') or []) or 'unclear'}."
        )

    user_content = (
        f"Title: {strip_control_chars(title)}\n"
        f"Category: {category}\n"
        f"Description: {strip_control_chars(description)[:900]}\n"
        f"Materials: {', '.join(materials) or 'unspecified'}\n"
        f"Artisan material cost (INR): {material_cost if material_cost is not None else 'unknown'}\n"
        f"Labour hours: {labour_hours if labour_hours is not None else 'unknown'}"
        f"{quality_note}\n\n"
        "Suggest the price JSON now."
    )

    messages = [
        {"role": "system", "content": _PRICING_SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]

    raw, call = await model_router.complete(
        messages, task="pricing", temperature=0.3, max_tokens=900, json_only=True
    )

    data = extract_json(raw)

    # Validate before clamping: clamping first would silently turn a bogus 0 or
    # a negative price into Rs 1 rather than surfacing the bad response.
    raw_price = data.get("suggested_price")
    # bool is a subclass of int, and float(True) == 1.0 would pass as a Rs 1 price.
    if isinstance(raw_price, bool):
        raise ValueError("Model did not return a usable suggested_price")
    try:
        raw_price = float(raw_price)
    except (TypeError, ValueError):
        raise ValueError("Model did not return a usable suggested_price") from None
    if raw_price < 1:
        raise ValueError("Model did not return a usable suggested_price")
    suggested = int(min(raw_price, 10_000_000))

    price_range = data.get("price_range") or {}
    low = int(_clamp(price_range.get("min"), 1, 10_000_000, suggested * 0.85))
    high = int(_clamp(price_range.get("max"), 1, 10_000_000, suggested * 1.25))
    if low > high:
        low, high = high, low
    # Keep the suggested price inside its own advertised range.
    low = min(low, suggested)
    high = max(high, suggested)

    raw_breakdown = data.get("breakdown") or {}
    breakdown = {
        key: round(_clamp(raw_breakdown.get(key), 0, 10_000_000, 0.0), 2)
        for key in (
            "material_cost",
            "labour_cost",
            "skill_premium",
            "platform_fee",
            "packaging",
        )
    }

    position = data.get("market_position")
    if position not in {"Budget", "Standard", "Premium"}:
        position = "Standard"

    return {
        "suggested_price": suggested,
        "price_range": {"min": low, "max": high},
        "breakdown": breakdown,
        "market_position": position,
        "confidence": round(_clamp(data.get("confidence"), 0.0, 1.0, 0.6), 2),
        "justification": strip_control_chars(str(data.get("justification", "")))[:800],
        "factors": [
            strip_control_chars(str(f))[:120] for f in (data.get("factors") or [])
        ][:8],
        "_model": call.model,
        "_fallbacks": call.attempts,
    }


# ── Tool definitions for model-driven routing ──────────────────────────
# Exposed so the orchestrator can let a model choose tools in conversational
# mode. The fast path calls the functions above directly.

TOOL_DEFINITIONS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "enhance_product_image",
            "description": (
                "Analyze and enhance an artisan product photo to e-commerce "
                "standard: remove cluttered background, correct lighting, crop "
                "to marketplace ratio."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "output_format": {
                        "type": "string",
                        "enum": ["1:1", "4:5"],
                        "description": "Target aspect ratio.",
                    }
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_catalog",
            "description": (
                "Turn an artisan's voice transcript in a regional Indian language "
                "into an SEO-friendly product listing in English and Hindi."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "transcript": {"type": "string"},
                    "language": {"type": "string", "enum": ALLOWED_LANGUAGES},
                },
                "required": ["transcript"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "suggest_price",
            "description": (
                "Suggest a fair, competitive INR selling price with a transparent "
                "cost breakdown."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "category": {"type": "string", "enum": ALLOWED_CATEGORIES},
                    "description": {"type": "string"},
                    "materials": {"type": "array", "items": {"type": "string"}},
                    "material_cost": {"type": "number"},
                    "labour_hours": {"type": "number"},
                },
                "required": ["title", "category"],
            },
        },
    },
]


__all__ = [
    "analyze_image",
    "enhance_product_image",
    "generate_catalog",
    "suggest_price",
    "extract_json",
    "strip_control_chars",
    "TOOL_DEFINITIONS",
    "ALLOWED_CATEGORIES",
    "ALLOWED_LANGUAGES",
]
