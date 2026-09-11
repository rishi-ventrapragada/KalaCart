"""
KalaCart unified artisan agent — SUPERSEDED, not mounted.

Status (decision D-14, 2026-09-11): this package is kept for reference and is
NOT part of the live request path. `app/main.py` deliberately leaves its router
unmounted. The three artisan AI features are served by the dedicated endpoints:

    POST /api/v1/image/enhance     image enhancement  (app/vision/, OpenCV)
    POST /api/v1/catalog/voice     voice -> listing   (app/ai/speech.py, Sarvam)
    POST /api/v1/pricing/analyze   price suggestion   (app/services/pricing_engine.py)

Why superseded: the agent takes `transcript` as a string and has no
speech-to-text stage, so it cannot satisfy the voice-note requirement by
itself. Its image stage returns JSON advice rather than editing pixels.

Why kept rather than deleted: `app/agent/models.py` holds the OpenRouter
":free" model catalogue and the `complete()` fallback walker, which has no
equivalent anywhere else in the codebase and is the reason the text and vision
models cost nothing per token. `app/core/config.py` now points the live
endpoints at the same free slugs this walker ranks first.

Do not re-mount without revisiting D-14 — doing so restores a second,
competing implementation of the same three features.
"""

from app.agent.orchestrator import ArtisanAgent, AgentResult, default_agent

__all__ = ["ArtisanAgent", "AgentResult", "default_agent"]
