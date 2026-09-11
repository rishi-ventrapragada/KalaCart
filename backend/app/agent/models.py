"""
Free-tier model router for the KalaCart unified agent.

Every agent call goes through OpenRouter using ONLY `:free` model slugs, so the
platform incurs no token cost. Free models are rate-limited and occasionally
unavailable, so `complete()` walks a priority chain and falls back to the next
candidate on 429 / 5xx / timeout / empty response.

Chains are capability-scoped: vision tasks must use a model that accepts image
input, so text-only models are never offered an image payload.

No secrets are hardcoded — OPENROUTER_API_KEY comes from Settings / environment.
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence

import httpx

logger = logging.getLogger(__name__)

# ── Free model catalogue ───────────────────────────────────────────────
# Verified live against GET https://openrouter.ai/api/v1/models (":free" suffix).
# Ordered by usefulness per task; the router walks each list top-down.


@dataclass(frozen=True)
class FreeModel:
    """A single OpenRouter free-tier model and the inputs it accepts."""

    slug: str
    context: int
    vision: bool = False
    audio: bool = False
    notes: str = ""
    # Reasoning models think aloud before answering. They need a bigger token
    # budget or they exhaust it mid-thought and never emit the JSON, and their
    # prose must be stripped from the reply. Measured live, not assumed.
    reasoning: bool = False
    # A few free models reject response_format=json_object outright (HTTP 400).
    supports_json_mode: bool = True


# Vision-capable free models — required for image quality analysis.
# Ordered by measured reliability: the Gemmas answer in one shot, then the
# fastest reasoning VLMs. Models needing a paid/BYOK plan sit last so the chain
# only reaches them once everything usable has been tried.
VISION_MODELS: List[FreeModel] = [
    FreeModel("google/gemma-4-31b-it:free", 262_144, vision=True, notes="Strong general VLM"),
    FreeModel("google/gemma-4-26b-a4b-it:free", 262_144, vision=True, notes="Faster MoE VLM"),
    FreeModel(
        "nex-agi/nex-n2.5-mini:free", 262_144, vision=True, reasoning=True, notes="Fastest VLM"
    ),
    FreeModel("inclusionai/ling-3.0-flash-vl:free", 262_144, vision=True, supports_json_mode=False),
    FreeModel("dots-studio/dots-3-note-preview:free", 512_000, vision=True, reasoning=True),
    FreeModel("nex-agi/nex-n2.5-pro:free", 262_144, vision=True, reasoning=True),
    FreeModel(
        "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
        256_000,
        vision=True,
        audio=True,
        reasoning=True,
    ),
    # Returned HTTP 403 on this key — likely needs a privileged plan.
    FreeModel("thinkingmachines/inkling:free", 1_048_576, vision=True, audio=True, reasoning=True),
    FreeModel(
        "thinkingmachines/inkling-small:free",
        1_048_576,
        vision=True,
        audio=True,
        reasoning=True,
    ),
]

# Text models — cataloguing, translation, pricing reasoning.
# Non-reasoning models lead every JSON chain: they answer in one shot, while
# reasoning models must first be given room to think.
TEXT_MODELS: List[FreeModel] = [
    FreeModel("google/gemma-4-31b-it:free", 262_144, vision=True, notes="Excellent multilingual"),
    FreeModel("google/gemma-4-26b-a4b-it:free", 262_144, vision=True, notes="Clean one-shot JSON"),
    # Measured ~12s on a real catalog prompt — by far the fastest that reliably
    # produces valid JSON, so it sits ahead of the slower reasoning models.
    FreeModel("nex-agi/nex-n2.5-mini:free", 262_144, vision=True, reasoning=True, notes="Fast (~12s)"),
    FreeModel("dots-studio/dots-3-note-preview:free", 512_000, vision=True, reasoning=True, notes="~28s"),
    FreeModel("nex-agi/nex-n2.5-pro:free", 262_144, vision=True, reasoning=True, notes="~58s"),
    FreeModel(
        "nvidia/nemotron-3-ultra-550b-a55b:free",
        1_000_000,
        reasoning=True,
        notes="Strong but slow (~68s)",
    ),
    FreeModel(
        "nvidia/nemotron-3-super-120b-a12b:free",
        262_144,
        reasoning=True,
        notes="Strong but slow (~88s)",
    ),
    # Rejects response_format=json_object with HTTP 400 — never send it one.
    FreeModel(
        "inclusionai/ling-3.0-flash-fin:free",
        262_144,
        reasoning=True,
        supports_json_mode=False,
        notes="Finance-tuned; no JSON mode",
    ),
    FreeModel("poolside/laguna-s-2.1:free", 262_144),
    # Overruns even a 4000-token budget on catalog prompts — last resort only.
    FreeModel(
        "nvidia/nemotron-3.5-lightning:free",
        1_000_000,
        reasoning=True,
        notes="Verbose; often truncates",
    ),
    FreeModel("liquid/lfm-2.5-2.6b:free", 65_536, notes="Last-resort tiny model", reasoning=True),
]


def _by_slug(slug: str, pool: List[FreeModel]) -> FreeModel:
    """Look a model up by slug so chains stay readable and index-drift-proof."""
    for model in pool:
        if model.slug == slug:
            return model
    raise KeyError(slug)


# Task -> ordered chain. Pricing leads with the finance-tuned model; cataloguing
# leads with the strongest multilingual model (Hindi + regional languages).
TASK_CHAINS: Dict[str, List[FreeModel]] = {
    "vision": VISION_MODELS,
    # Both JSON chains lead with the Gemma models (best multilingual, clean
    # one-shot JSON), then the fastest models that reliably return valid JSON.
    # Gemma is frequently rate-limited on the free tier, so the models behind it
    # are ordered by measured latency — an artisan on a phone should not wait
    # 90s when a 12s model produces an equally valid listing.
    "catalog": [
        _by_slug("google/gemma-4-31b-it:free", TEXT_MODELS),
        _by_slug("google/gemma-4-26b-a4b-it:free", TEXT_MODELS),
        _by_slug("nex-agi/nex-n2.5-mini:free", TEXT_MODELS),
        _by_slug("dots-studio/dots-3-note-preview:free", TEXT_MODELS),
        _by_slug("nex-agi/nex-n2.5-pro:free", TEXT_MODELS),
        _by_slug("nvidia/nemotron-3-ultra-550b-a55b:free", TEXT_MODELS),
        _by_slug("nvidia/nemotron-3-super-120b-a12b:free", TEXT_MODELS),
    ],
    "pricing": [
        _by_slug("google/gemma-4-26b-a4b-it:free", TEXT_MODELS),
        _by_slug("google/gemma-4-31b-it:free", TEXT_MODELS),
        _by_slug("nex-agi/nex-n2.5-mini:free", TEXT_MODELS),
        _by_slug("dots-studio/dots-3-note-preview:free", TEXT_MODELS),
        _by_slug("nvidia/nemotron-3-ultra-550b-a55b:free", TEXT_MODELS),
        _by_slug("nvidia/nemotron-3-super-120b-a12b:free", TEXT_MODELS),
    ],
    "general": TEXT_MODELS,
}

# Errors that justify trying the next model in the chain.
_RETRYABLE_STATUS = {402, 408, 409, 429, 500, 502, 503, 504}

# Models this key is not entitled to (HTTP 403) or that no longer exist (404).
# That verdict will not change within the process, so remember it and stop
# spending a chain slot on them.
_UNAVAILABLE_MODELS: set[str] = set()

# Measured live: reasoning models take 60-90s on a real catalog prompt, so a
# 45s per-request timeout killed calls that would have succeeded.
DEFAULT_TIMEOUT = 100.0


class AllModelsFailedError(RuntimeError):
    """Raised when every model in a chain failed. Carries per-model reasons."""

    def __init__(self, task: str, attempts: Sequence[str]) -> None:
        self.task = task
        self.attempts = list(attempts)
        super().__init__(
            f"All free models failed for task '{task}': " + "; ".join(attempts)
        )


@dataclass
class ModelCall:
    """Telemetry for one completed call — surfaced so clients can show provenance."""

    model: str
    attempts: List[str] = field(default_factory=list)
    latency_ms: int = 0


def _resolve_credentials() -> tuple[str, str]:
    """Read API key + base URL from Settings, falling back to environment."""
    api_key: Optional[str] = None
    base_url = "https://openrouter.ai/api/v1"
    try:
        from app.core.config import get_settings

        settings = get_settings()
        api_key = settings.OPENROUTER_API_KEY
        base_url = settings.OPENROUTER_BASE_URL or base_url
    except Exception:  # pragma: no cover - settings optional in tests
        api_key = os.getenv("OPENROUTER_API_KEY")
        base_url = os.getenv("OPENROUTER_BASE_URL", base_url)

    if not api_key:
        api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENROUTER_API_KEY not set — add it to backend/.env to enable the AI agent"
        )
    return api_key, base_url.rstrip("/")


def _chain_for(task: str, require_vision: bool) -> List[FreeModel]:
    """Return the candidate chain, filtered to vision models when an image is attached."""
    chain = TASK_CHAINS.get(task, TASK_CHAINS["general"])
    if require_vision:
        chain = [m for m in chain if m.vision] or VISION_MODELS
    # Drop models already proven unavailable for this key, but never return an
    # empty chain — if all are marked, try anyway rather than failing outright.
    usable = [m for m in chain if m.slug not in _UNAVAILABLE_MODELS]
    return usable or chain


async def complete(
    messages: List[Dict[str, Any]],
    task: str = "general",
    temperature: float = 0.6,
    max_tokens: int = 1200,
    require_vision: bool = False,
    json_only: bool = False,
    timeout: float = DEFAULT_TIMEOUT,
    max_models: int = 5,
) -> tuple[str, ModelCall]:
    """
    Run a chat completion against the free-tier chain for `task`.

    Walks the chain until one model returns usable content. Rate limits (429) and
    server errors move to the next model; a 401 aborts immediately, since
    retrying a bad key only wastes the artisan's time.

    Args:
        messages: OpenAI-format messages. For vision, content may be a parts list.
        task: One of "vision" | "catalog" | "pricing" | "general".
        require_vision: Restrict the chain to image-capable models.
        json_only: Request a JSON object response where the provider supports it.
        max_models: Cap on how many models to try before giving up.

    Returns:
        (content, ModelCall) — the assistant text plus which model answered and
        what was tried before it.

    Raises:
        AllModelsFailedError: every candidate failed.
        ValueError: no API key configured, or the key was rejected.
    """
    api_key, base_url = _resolve_credentials()
    chain = _chain_for(task, require_vision)[:max_models]

    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://kalacart.in",
        "X-Title": "KalaCart Artisan Agent",
        "Content-Type": "application/json",
    }

    attempts: List[str] = []
    url = f"{base_url}/chat/completions"

    async with httpx.AsyncClient(timeout=timeout) as client:
        for model in chain:
            # Reasoning models spend most of their budget thinking. Measured
            # live: a catalog prompt needs ~4000 tokens before the JSON appears,
            # where 1400 truncated mid-thought every time.
            budget = max(max_tokens, 4000) if model.reasoning else max_tokens

            payload: Dict[str, Any] = {
                "model": model.slug,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": budget,
            }
            # Sending json_object to a model that rejects it is an instant 400.
            if json_only and model.supports_json_mode:
                payload["response_format"] = {"type": "json_object"}

            started = time.monotonic()
            try:
                response = await client.post(url, headers=headers, json=payload)
            except (httpx.TimeoutException, httpx.TransportError) as exc:
                attempts.append(f"{model.slug}: transport {type(exc).__name__}")
                logger.warning("Agent model %s transport error: %s", model.slug, exc)
                continue

            if response.status_code == 401:
                # Bad credentials — no point walking the rest of the chain.
                raise ValueError(
                    "OpenRouter rejected the API key (401) — check OPENROUTER_API_KEY"
                )

            if response.status_code in _RETRYABLE_STATUS:
                attempts.append(f"{model.slug}: HTTP {response.status_code}")
                logger.info(
                    "Agent model %s unavailable (HTTP %s) — falling back",
                    model.slug,
                    response.status_code,
                )
                continue

            if response.status_code in (403, 404):
                # Not entitled, or gone. Permanent for this key — stop retrying it.
                _UNAVAILABLE_MODELS.add(model.slug)
                attempts.append(f"{model.slug}: HTTP {response.status_code} (unavailable)")
                logger.warning(
                    "Agent model %s returned HTTP %s — skipping for this process",
                    model.slug,
                    response.status_code,
                )
                continue

            if response.status_code >= 400:
                attempts.append(f"{model.slug}: HTTP {response.status_code}")
                logger.warning("Agent model %s HTTP %s", model.slug, response.status_code)
                continue

            try:
                data = response.json()
                message = data["choices"][0]["message"]
                content = message.get("content")
                # Some reasoning models return an empty `content` and put the
                # answer in a separate reasoning field. Observed live on
                # ling-3.0-flash-fin and lfm-2.5 — without this they look like
                # failures and the chain falls through needlessly.
                if not content or not str(content).strip():
                    content = message.get("reasoning") or message.get("reasoning_content")
            except (ValueError, KeyError, IndexError, TypeError) as exc:
                attempts.append(f"{model.slug}: malformed response ({type(exc).__name__})")
                logger.warning("Agent model %s malformed response: %s", model.slug, exc)
                continue

            if not content or not str(content).strip():
                attempts.append(f"{model.slug}: empty content")
                continue

            finish_reason = (data["choices"][0] or {}).get("finish_reason")
            if finish_reason == "length" and json_only:
                # Truncated mid-output: any JSON in it is incomplete, so trying
                # the next model beats handing the parser a broken object.
                attempts.append(f"{model.slug}: truncated (hit token limit)")
                logger.info("Agent model %s truncated — falling back", model.slug)
                continue

            latency = int((time.monotonic() - started) * 1000)
            logger.info(
                "Agent task=%s served by %s in %dms (%d fallback(s))",
                task,
                model.slug,
                latency,
                len(attempts),
            )
            return str(content), ModelCall(
                model=model.slug, attempts=attempts, latency_ms=latency
            )

    raise AllModelsFailedError(task, attempts)


def list_free_models() -> List[Dict[str, Any]]:
    """Expose the catalogue for the GET /agent/models endpoint."""
    seen: Dict[str, FreeModel] = {}
    for model in VISION_MODELS + TEXT_MODELS:
        seen.setdefault(model.slug, model)
    return [
        {
            "slug": m.slug,
            "context": m.context,
            "vision": m.vision,
            "audio": m.audio,
            "notes": m.notes,
        }
        for m in seen.values()
    ]


__all__ = [
    "complete",
    "list_free_models",
    "AllModelsFailedError",
    "ModelCall",
    "FreeModel",
    "TASK_CHAINS",
    "VISION_MODELS",
    "TEXT_MODELS",
]
