"""
KalaCart Artisan Agent — the single agent behind all three AI features.

One agent, three tools, one call. The artisan photographs a product and speaks a
description; the agent runs the full listing pipeline and returns a ready-to-publish
product.

Why one agent rather than three endpoints: the stages feed each other. What the
vision model sees in the photo grounds the catalog text, and both the photo
assessment and the finished listing inform the price. Running them separately
throws that context away.

Execution model — stages are sequential only where a real dependency exists:

    [ photo ] ──> analyze_image ──┐
                                  ├──> generate_catalog ──> suggest_price
    [ voice transcript ] ─────────┘

Every stage degrades independently. A failed photo analysis still yields a
listing; a failed listing still yields an enhanced image. The artisan is never
left with nothing, and `stages` reports exactly what succeeded.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.agent import tools
from app.agent.models import AllModelsFailedError

logger = logging.getLogger(__name__)

# Stage identifiers, in pipeline order.
STAGE_IMAGE = "image_enhancement"
STAGE_CATALOG = "catalog_generation"
STAGE_PRICING = "price_suggestion"

ALL_STAGES = [STAGE_IMAGE, STAGE_CATALOG, STAGE_PRICING]


@dataclass
class StageResult:
    """Outcome of a single agent stage."""

    name: str
    status: str  # "success" | "failed" | "skipped"
    duration_ms: int = 0
    model: Optional[str] = None
    fallbacks: List[str] = field(default_factory=list)
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage": self.name,
            "status": self.status,
            "duration_ms": self.duration_ms,
            "model": self.model,
            "fallbacks": self.fallbacks,
            "error": self.error,
        }


@dataclass
class AgentResult:
    """Everything the agent produced for one product."""

    stages: List[StageResult] = field(default_factory=list)
    image: Optional[Dict[str, Any]] = None
    listing: Optional[Dict[str, Any]] = None
    pricing: Optional[Dict[str, Any]] = None
    # Binary outputs kept out of the JSON body; the API layer uploads them.
    image_bytes: Dict[str, Any] = field(default_factory=dict)
    total_ms: int = 0

    @property
    def succeeded_any(self) -> bool:
        return any(s.status == "success" for s in self.stages)

    def to_dict(self) -> Dict[str, Any]:
        """JSON-safe payload — excludes raw image bytes."""
        return {
            "success": self.succeeded_any,
            "stages": [s.to_dict() for s in self.stages],
            "image": self.image,
            "listing": self.listing,
            "pricing": self.pricing,
            "total_ms": self.total_ms,
        }


def _describe_error(exc: Exception) -> str:
    """Human-readable, secret-free error text for the client."""
    if isinstance(exc, AllModelsFailedError):
        return (
            "All free models were unavailable or rate-limited. "
            "Please try again in a moment."
        )
    if isinstance(exc, ValueError):
        return str(exc)
    return f"{type(exc).__name__}: {exc}"


class ArtisanAgent:
    """
    The single KalaCart agent.

    Usage:
        agent = ArtisanAgent()
        result = await agent.run(
            image_bytes=photo,
            transcript="यह हाथ से बुनी हुई कॉटन साड़ी है...",
            language="hi",
        )
    """

    def __init__(self, stage_timeout: float = 240.0) -> None:
        """
        Args:
            stage_timeout: Per-stage ceiling in seconds. The model router already
                has its own per-request timeout; this bounds the whole stage
                including fallbacks, so one dead stage cannot hang the request.
        """
        self.stage_timeout = stage_timeout

    async def run(
        self,
        image_bytes: Optional[bytes] = None,
        mime_type: str = "image/jpeg",
        transcript: Optional[str] = None,
        language: str = "hi",
        output_format: Optional[str] = None,
        material_cost: Optional[float] = None,
        labour_hours: Optional[float] = None,
        stages: Optional[List[str]] = None,
    ) -> AgentResult:
        """
        Run the agent end to end.

        Args:
            image_bytes: Product photo. Omit to skip image enhancement.
            mime_type: MIME type of the photo.
            transcript: Voice transcript. Omit to skip cataloguing.
            language: Language of the transcript.
            output_format: "1:1" or "4:5"; the vision model decides when omitted.
            material_cost: Artisan's material cost in INR, if known.
            labour_hours: Hours spent, if known.
            stages: Subset of ALL_STAGES to run. Defaults to everything possible.

        Returns:
            AgentResult with per-stage status. Never raises for stage failure —
            inspect `stages` to see what worked.
        """
        requested = set(stages or ALL_STAGES)
        started = time.monotonic()
        result = AgentResult()

        # ── Stage 1: image enhancement ─────────────────────────────────
        image_plan: Optional[Dict[str, Any]] = None

        if STAGE_IMAGE in requested and image_bytes:
            stage_started = time.monotonic()
            try:
                enhanced = await asyncio.wait_for(
                    tools.enhance_product_image(image_bytes, mime_type, output_format),
                    timeout=self.stage_timeout,
                )
                image_plan = enhanced.get("plan")
                result.image_bytes = {
                    "enhanced_bytes": enhanced.get("enhanced_bytes"),
                    "webp_bytes": enhanced.get("webp_bytes"),
                    "thumbnail_bytes": enhanced.get("thumbnail_bytes"),
                }
                result.image = {
                    # Default to 0 rather than null: the Android client reads
                    # these into primitive ints, where null would silently
                    # become 0 anyway — better to be explicit.
                    "width": enhanced.get("width") or 0,
                    "height": enhanced.get("height") or 0,
                    "ratio": enhanced.get("ratio"),
                    "quality_score": (image_plan or {}).get("quality_score"),
                    "issues": (image_plan or {}).get("issues", []),
                    "subject": (image_plan or {}).get("subject"),
                    "detected_category": (image_plan or {}).get("category"),
                    "detected_materials": (image_plan or {}).get("materials", []),
                    "colors": (image_plan or {}).get("colors", []),
                    "background_removed": (image_plan or {}).get(
                        "needs_background_removal", True
                    ),
                }
                result.stages.append(
                    StageResult(
                        name=STAGE_IMAGE,
                        status="success",
                        duration_ms=int((time.monotonic() - stage_started) * 1000),
                        model=enhanced.get("model"),
                        fallbacks=enhanced.get("fallbacks", []),
                        # Surface partial degradation: pixels enhanced, AI plan missing.
                        error=enhanced.get("plan_error"),
                    )
                )
            except Exception as exc:
                logger.exception("Image enhancement stage failed")
                result.stages.append(
                    StageResult(
                        name=STAGE_IMAGE,
                        status="failed",
                        duration_ms=int((time.monotonic() - stage_started) * 1000),
                        error=_describe_error(exc),
                    )
                )
        elif STAGE_IMAGE in requested:
            result.stages.append(
                StageResult(STAGE_IMAGE, "skipped", error="No image supplied")
            )

        # ── Stage 2: catalog generation ────────────────────────────────
        if STAGE_CATALOG in requested and transcript:
            stage_started = time.monotonic()
            try:
                listing = await asyncio.wait_for(
                    tools.generate_catalog(
                        transcript=transcript,
                        language=language,
                        image_context=image_plan,
                    ),
                    timeout=self.stage_timeout,
                )
                model = listing.pop("_model", None)
                fallbacks = listing.pop("_fallbacks", [])
                result.listing = listing
                result.stages.append(
                    StageResult(
                        name=STAGE_CATALOG,
                        status="success",
                        duration_ms=int((time.monotonic() - stage_started) * 1000),
                        model=model,
                        fallbacks=fallbacks,
                    )
                )
            except Exception as exc:
                logger.exception("Catalog generation stage failed")
                result.stages.append(
                    StageResult(
                        name=STAGE_CATALOG,
                        status="failed",
                        duration_ms=int((time.monotonic() - stage_started) * 1000),
                        error=_describe_error(exc),
                    )
                )
        elif STAGE_CATALOG in requested:
            result.stages.append(
                StageResult(STAGE_CATALOG, "skipped", error="No transcript supplied")
            )

        # ── Stage 3: price suggestion ──────────────────────────────────
        # Prefer the generated listing; fall back to what the photo revealed so
        # a photo-only request still gets a price.
        if STAGE_PRICING in requested:
            title = None
            category = "Other"
            description = ""
            materials: List[str] = []

            if result.listing:
                title = result.listing.get("title")
                category = result.listing.get("category", "Other")
                description = result.listing.get("description_en", "")
                materials = result.listing.get("materials", [])
            elif image_plan:
                title = image_plan.get("subject")
                category = image_plan.get("category", "Other")
                description = image_plan.get("subject", "")
                materials = image_plan.get("materials", [])

            if title:
                stage_started = time.monotonic()
                try:
                    pricing = await asyncio.wait_for(
                        tools.suggest_price(
                            title=title,
                            category=category,
                            description=description,
                            materials=materials,
                            material_cost=material_cost,
                            labour_hours=labour_hours,
                            image_context=image_plan,
                        ),
                        timeout=self.stage_timeout,
                    )
                    model = pricing.pop("_model", None)
                    fallbacks = pricing.pop("_fallbacks", [])
                    result.pricing = pricing
                    result.stages.append(
                        StageResult(
                            name=STAGE_PRICING,
                            status="success",
                            duration_ms=int((time.monotonic() - stage_started) * 1000),
                            model=model,
                            fallbacks=fallbacks,
                        )
                    )
                except Exception as exc:
                    logger.exception("Price suggestion stage failed")
                    result.stages.append(
                        StageResult(
                            name=STAGE_PRICING,
                            status="failed",
                            duration_ms=int((time.monotonic() - stage_started) * 1000),
                            error=_describe_error(exc),
                        )
                    )
            else:
                result.stages.append(
                    StageResult(
                        STAGE_PRICING,
                        "skipped",
                        error="Needs a listing or a photo to price against",
                    )
                )

        result.total_ms = int((time.monotonic() - started) * 1000)
        logger.info(
            "Agent run complete in %dms — %s",
            result.total_ms,
            ", ".join(f"{s.name}={s.status}" for s in result.stages),
        )
        return result


# Module-level default instance for convenience.
default_agent = ArtisanAgent()


__all__ = [
    "ArtisanAgent",
    "AgentResult",
    "StageResult",
    "default_agent",
    "ALL_STAGES",
    "STAGE_IMAGE",
    "STAGE_CATALOG",
    "STAGE_PRICING",
]
