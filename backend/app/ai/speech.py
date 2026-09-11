"""
Speech-to-text for artisan voice notes via Sarvam AI (Indian languages).

POST {SARVAM_BASE_URL}/speech-to-text — multipart `file` + `model` / `mode` / `language_code`,
authenticated with the `api-subscription-key` header. The synchronous REST API handles clips
up to ~30 seconds. Never logs the API key.
"""

import logging
from typing import Any, Dict

import httpx
from fastapi import HTTPException, status

from app.core.config import get_settings

logger = logging.getLogger(__name__)

# App language codes -> Sarvam BCP-47 codes; "auto" lets Sarvam detect the spoken language
SARVAM_LANGUAGE_CODES = {
    "hi": "hi-IN",
    "te": "te-IN",
    "ta": "ta-IN",
    "kn": "kn-IN",
    "en": "en-IN",
    "auto": "unknown",
}

SUPPORTED_AUDIO_TYPES = {
    "audio/wav", "audio/x-wav", "audio/wave", "audio/vnd.wave",
    "audio/mpeg", "audio/mp3",
    "audio/mp4", "audio/m4a", "audio/x-m4a", "audio/aac",
    "audio/ogg", "audio/opus", "audio/webm", "audio/flac", "audio/amr",
    "video/mp4", "video/webm",  # some recorders label audio-only files as video
}

# A 30-second voice note is far below this in any supported format
MAX_AUDIO_BYTES = 5 * 1024 * 1024


def _error_message(resp: httpx.Response) -> str:
    try:
        error = resp.json().get("error") or {}
        return str(error.get("message") or "")[:200] or f"HTTP {resp.status_code}"
    except ValueError:
        return f"HTTP {resp.status_code}"


async def transcribe_audio(
    audio: bytes,
    filename: str,
    content_type: str,
    language: str = "auto",
) -> Dict[str, Any]:
    """
    Transcribe a voice note in its spoken language.

    Args:
        audio: Raw audio bytes (wav, mp3, m4a/aac, ogg/opus, webm, flac, amr).
        filename: Original file name (sent to Sarvam for format detection).
        content_type: MIME type of the audio.
        language: App language code (hi|te|ta|kn|en) or "auto" to detect.

    Returns:
        {"transcript": str, "language_code": str | None}  e.g. language_code "te-IN"

    Raises:
        HTTPException 500 if not configured, 422 if Sarvam can't process the audio,
        502/504 on upstream failure.
    """
    settings = get_settings()
    api_key = settings.SARVAM_API_KEY
    if not api_key:
        logger.error("SARVAM_API_KEY not configured")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Speech-to-text service not configured (missing API key)",
        )

    url = f"{settings.SARVAM_BASE_URL.rstrip('/')}/speech-to-text"
    form = {
        "model": settings.SARVAM_STT_MODEL,
        "mode": "transcribe",
        "language_code": SARVAM_LANGUAGE_CODES.get(language, "unknown"),
    }

    try:
        async with httpx.AsyncClient(timeout=45) as client:
            resp = await client.post(
                url,
                headers={"api-subscription-key": api_key},
                files={"file": (filename, audio, content_type)},
                data=form,
            )
    except httpx.TimeoutException as exc:
        logger.error("Sarvam speech-to-text timed out")
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail="Speech-to-text service timed out") from exc
    except httpx.RequestError as exc:
        logger.error("Sarvam speech-to-text request error: %s", type(exc).__name__)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Speech-to-text service unavailable") from exc

    if resp.status_code != 200:
        message = _error_message(resp)
        logger.warning("Sarvam speech-to-text HTTP %s: %s", resp.status_code, message)
        if resp.status_code in (400, 422):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Could not process the voice note: {message}",
            )
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Speech-to-text service temporarily unavailable")

    body = resp.json()
    return {
        "transcript": (body.get("transcript") or "").strip(),
        "language_code": body.get("language_code"),
    }
