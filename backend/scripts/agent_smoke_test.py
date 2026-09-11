"""
Live smoke test for the unified artisan agent.

Calls OpenRouter for real using free models. Requires OPENROUTER_API_KEY in the
environment or backend/.env.

    python scripts/agent_smoke_test.py                # catalog + pricing
    python scripts/agent_smoke_test.py photo.jpg      # all three stages

Costs nothing: every model in the chain is a `:free` slug.
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

# Windows consoles default to cp1252, which cannot print Devanagari. Force UTF-8
# so the Hindi description is readable rather than crashing the script.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except (ValueError, OSError):  # pragma: no cover - exotic consoles
            pass


def emit(text: str = "") -> None:
    """
    Print text that may contain Devanagari.

    A cp1252 Windows console raises UnicodeEncodeError mid-line, which silently
    truncated the descriptions in earlier runs. Fall back to an escaped form so
    the operator still sees the content rather than a blank line.
    """
    try:
        print(text)
    except UnicodeEncodeError:
        encoding = getattr(sys.stdout, "encoding", "ascii") or "ascii"
        print(text.encode(encoding, errors="backslashreplace").decode(encoding))

# Make `app` importable when run from the backend directory.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Load .env if python-dotenv is available.
try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass

from app.agent.orchestrator import ArtisanAgent  # noqa: E402

# A realistic Hindi voice transcript from an artisan.
SAMPLE_TRANSCRIPT = (
    "नमस्ते, मैं वारंगल से हूँ। यह साड़ी मैंने अपने हाथ से बुनी है, "
    "शुद्ध सूती धागे से। इसे बनाने में मुझे चार दिन लगे। "
    "रंग प्राकृतिक हैं, हल्दी और नील से बनाए गए हैं। "
    "किनारी पर मंदिर का डिज़ाइन है जो हमारे यहाँ पारंपरिक है।"
)

GREEN, RED, YELLOW, DIM, RESET = "\033[92m", "\033[91m", "\033[93m", "\033[2m", "\033[0m"


def _status_icon(status: str) -> str:
    return {"success": f"{GREEN}OK{RESET}", "failed": f"{RED}FAIL{RESET}"}.get(
        status, f"{YELLOW}SKIP{RESET}"
    )


async def main() -> int:
    if not os.getenv("OPENROUTER_API_KEY"):
        emit(f"{RED}OPENROUTER_API_KEY is not set.{RESET}")
        emit("Set it in backend/.env or export it, then re-run.")
        return 2

    image_bytes = None
    if len(sys.argv) > 1:
        path = Path(sys.argv[1])
        if not path.exists():
            emit(f"{RED}No such file: {path}{RESET}")
            return 2
        image_bytes = path.read_bytes()
        emit(f"Photo: {path.name} ({len(image_bytes) // 1024} KB)")

    emit(f"{DIM}Running the agent against OpenRouter free models...{RESET}\n")

    agent = ArtisanAgent()
    result = await agent.run(
        image_bytes=image_bytes,
        transcript=SAMPLE_TRANSCRIPT,
        language="hi",
        material_cost=600,
        labour_hours=32,
    )

    emit("=" * 68)
    emit("STAGES")
    emit("=" * 68)
    for stage in result.stages:
        emit(f"  [{_status_icon(stage.status)}] {stage.name:20} {stage.duration_ms:>6} ms")
        if stage.model:
            emit(f"        model: {stage.model}")
        if stage.fallbacks:
            emit(f"        {YELLOW}fell back past: {', '.join(stage.fallbacks)}{RESET}")
        if stage.error:
            emit(f"        {RED}{stage.error}{RESET}")

    if result.image:
        emit("\n" + "=" * 68)
        emit("1. IMAGE ENHANCEMENT")
        emit("=" * 68)
        img = result.image
        emit(f"  Subject        : {img.get('subject')}")
        emit(f"  Quality score  : {img.get('quality_score')}/100")
        emit(f"  Output         : {img.get('width')}x{img.get('height')} ({img.get('ratio')})")
        emit(f"  Detected       : {img.get('detected_category')} / {img.get('detected_materials')}")
        if img.get("issues"):
            emit(f"  Issues found   : {'; '.join(img['issues'])}")

    if result.listing:
        emit("\n" + "=" * 68)
        emit("2. MULTILINGUAL CATALOG")
        emit("=" * 68)
        listing = result.listing
        emit(f"  Title    : {listing.get('title')}")
        emit(f"  Category : {listing.get('category')}")
        emit(f"  Materials: {', '.join(listing.get('materials', []))}")
        emit(f"  SEO tags : {', '.join(listing.get('seo_tags', []))}")
        emit(f"\n  English:\n    {listing.get('description_en', '')}")
        emit(f"\n  Hindi:\n    {listing.get('description_hi', '')}")
        emit(f"\n  Care     : {listing.get('care')}")

    if result.pricing:
        emit("\n" + "=" * 68)
        emit("3. DYNAMIC PRICING")
        emit("=" * 68)
        pricing = result.pricing
        rng = pricing.get("price_range", {})
        emit(f"  Suggested : Rs {pricing.get('suggested_price'):,}")
        emit(f"  Range     : Rs {rng.get('min'):,} - Rs {rng.get('max'):,}")
        emit(f"  Position  : {pricing.get('market_position')}")
        emit(f"  Confidence: {pricing.get('confidence')}")
        emit("  Breakdown :")
        for key, value in (pricing.get("breakdown") or {}).items():
            emit(f"      {key:16} Rs {value:,.2f}")
        emit(f"\n  Why: {pricing.get('justification')}")

    emit("\n" + "=" * 68)
    ok = sum(1 for s in result.stages if s.status == "success")
    total = len([s for s in result.stages if s.status != "skipped"])
    emit(f"{ok}/{total} stages succeeded in {result.total_ms} ms")
    emit("=" * 68)

    return 0 if result.succeeded_any else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
