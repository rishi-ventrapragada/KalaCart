"""
Voice catalog tests — POST /api/v1/catalog/voice and the Sarvam client (app.ai.speech).

Sarvam and OpenRouter are mocked; no network access or real keys are used.
"""
import json
import os
from types import SimpleNamespace

os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("APP_ENV", "development")
os.environ.setdefault("SUPABASE_URL", "https://placeholder.supabase.co")

import httpx
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch

from app.main import app
from app.ai import speech
from app.api import catalog as catalog_module
from app.core.security import get_current_user

MOCK_USER = {"firebase_uid": "seller-1", "uid": "seller-1", "artisan": {"id": "seller-1"}, "claims": {}}

CATALOG = {
    "title": "Handmade Bamboo Basket - Srikakulam",
    "description_en": (
        "Hand-woven from natural bamboo by artisans in Srikakulam, this sturdy basket brings rustic warmth to any "
        "home. Each strip is split and plaited by hand using techniques passed down through generations, giving the "
        "basket a tight, durable weave. Use it for fruit, bread, storage or as a planter cover. Lightweight, "
        "biodegradable and plastic-free, it supports rural livelihoods while adding a sustainable, handcrafted touch "
        "to your kitchen or living room."
    ),
    "description_hi": "श्रीकाकुलम के कारीगरों द्वारा प्राकृतिक बांस से हाथ से बुनी यह मज़बूत टोकरी हर घर में देसी गर्माहट लाती है।",
    "category": "Basketry",
    "materials": ["Bamboo"],
    "seo_tags": ["Handmade", "Bamboo Basket", "Eco-Friendly"],
    "care": "Keep dry, wipe with a soft cloth",
}
TELUGU_TRANSCRIPT = "ఇది చేతితో చేసిన వెదురు బుట్ట నేను సహజమైన వెదురు వాడాను మా ఊరు శ్రీకాకుళం దీన్ని పొడిగా ఉంచాలి."

client = TestClient(app)


@pytest.fixture(autouse=True)
def seller_and_clean_limits():
    saved = app.dependency_overrides.get(get_current_user)
    app.dependency_overrides[get_current_user] = lambda: MOCK_USER
    catalog_module._clear_rate_limit_store()
    yield
    catalog_module._clear_rate_limit_store()
    if saved is None:
        app.dependency_overrides.pop(get_current_user, None)
    else:
        app.dependency_overrides[get_current_user] = saved


def _llm_client(content: str):
    """httpx.AsyncClient mock returning one OpenRouter chat completion."""
    resp = MagicMock()
    resp.status_code = 200
    resp.raise_for_status = MagicMock()
    resp.json.return_value = {"choices": [{"message": {"content": content}}]}
    instance = MagicMock()
    instance.post = AsyncMock(return_value=resp)
    ctx = MagicMock()
    ctx.__aenter__ = AsyncMock(return_value=instance)
    ctx.__aexit__ = AsyncMock(return_value=None)
    return ctx, instance


def post_voice(audio=b"RIFF....WAVEfmt fake-audio", content_type="audio/wav", language=None):
    data = {} if language is None else {"language": language}
    return client.post("/api/v1/catalog/voice", files={"audio": ("note.wav", audio, content_type)}, data=data)


class TestVoiceEndpoint:
    def test_voice_note_becomes_bilingual_listing(self):
        ctx, llm = _llm_client(json.dumps(CATALOG, ensure_ascii=False))
        stt = AsyncMock(return_value={"transcript": TELUGU_TRANSCRIPT, "language_code": "te-IN"})
        with patch("app.api.catalog.transcribe_audio", stt), patch("app.api.catalog.httpx.AsyncClient", return_value=ctx):
            resp = post_voice(content_type="audio/mp4")

        assert resp.status_code == 200, resp.text
        data = resp.json()["data"]
        assert data["title"] == CATALOG["title"]
        assert data["description_hi"] == CATALOG["description_hi"]
        assert data["transcript"] == TELUGU_TRANSCRIPT
        assert data["detected_language"] == "te-IN"

        assert stt.call_args.args[3] == "auto"  # language defaults to auto-detect
        payload = llm.post.call_args.kwargs["json"]
        assert "Language hint: te" in payload["messages"][1]["content"]
        assert payload["reasoning"] == {"enabled": False}

    def test_explicit_language_passed_to_speech_to_text(self):
        ctx, _ = _llm_client(json.dumps(CATALOG, ensure_ascii=False))
        stt = AsyncMock(return_value={"transcript": "यह हाथ से बनी बांस की टोकरी है", "language_code": "hi-IN"})
        with patch("app.api.catalog.transcribe_audio", stt), patch("app.api.catalog.httpx.AsyncClient", return_value=ctx):
            resp = post_voice(language="HI")
        assert resp.status_code == 200, resp.text
        assert stt.call_args.args[3] == "hi"

    def test_unsupported_audio_type_rejected_before_transcription(self):
        stt = AsyncMock()
        with patch("app.api.catalog.transcribe_audio", stt):
            resp = post_voice(audio=b"hello", content_type="text/plain")
        assert resp.status_code == 400
        stt.assert_not_called()

    def test_empty_audio_rejected(self):
        with patch("app.api.catalog.transcribe_audio", AsyncMock()) as stt:
            resp = post_voice(audio=b"")
        assert resp.status_code == 400
        stt.assert_not_called()

    def test_oversized_audio_413(self):
        with patch("app.api.catalog.transcribe_audio", AsyncMock()) as stt:
            resp = post_voice(audio=b"0" * (speech.MAX_AUDIO_BYTES + 1))
        assert resp.status_code == 413
        stt.assert_not_called()

    def test_invalid_language_422(self):
        with patch("app.api.catalog.transcribe_audio", AsyncMock()) as stt:
            resp = post_voice(language="fr")
        assert resp.status_code == 422
        stt.assert_not_called()

    def test_silent_voice_note_422_without_llm_call(self):
        ctx, llm = _llm_client("{}")
        stt = AsyncMock(return_value={"transcript": "  ", "language_code": None})
        with patch("app.api.catalog.transcribe_audio", stt), patch("app.api.catalog.httpx.AsyncClient", return_value=ctx):
            resp = post_voice()
        assert resp.status_code == 422
        assert "couldn't hear" in resp.json()["message"].lower()
        llm.post.assert_not_called()

    def test_speech_service_failure_propagates(self):
        stt = AsyncMock(side_effect=HTTPException(status_code=502, detail="Speech-to-text service unavailable"))
        with patch("app.api.catalog.transcribe_audio", stt):
            resp = post_voice()
        assert resp.status_code == 502

    def test_voice_shares_rate_limit_with_generate(self):
        ctx, _ = _llm_client(json.dumps(CATALOG, ensure_ascii=False))
        stt = AsyncMock(return_value={"transcript": TELUGU_TRANSCRIPT, "language_code": "te-IN"})
        with patch("app.api.catalog.transcribe_audio", stt), patch("app.api.catalog.httpx.AsyncClient", return_value=ctx):
            codes = [post_voice().status_code for _ in range(catalog_module._RATE_LIMIT_MAX + 1)]
        assert codes[-1] == 429


class TestGenerationLimits:
    def test_full_length_description_is_accepted(self):
        long_listing = dict(CATALOG, description_en=CATALOG["description_en"] * 2)  # ~900 chars, 150 words
        assert 500 < len(long_listing["description_en"]) <= catalog_module.DESCRIPTION_MAX_CHARS
        ok, err = catalog_module._validate_catalog_schema(long_listing)
        assert ok, err


def _sarvam_settings(key="sarvam-test-key"):
    return SimpleNamespace(SARVAM_API_KEY=key, SARVAM_BASE_URL="https://api.sarvam.ai", SARVAM_STT_MODEL="saaras:v3")


def _sarvam_client(status_code=200, body=None, raises=None):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = body or {}
    instance = MagicMock()
    instance.post = AsyncMock(side_effect=raises) if raises else AsyncMock(return_value=resp)
    ctx = MagicMock()
    ctx.__aenter__ = AsyncMock(return_value=instance)
    ctx.__aexit__ = AsyncMock(return_value=None)
    return ctx, instance


class TestSarvamClient:
    @pytest.mark.asyncio
    async def test_transcribe_sends_contract_fields(self):
        ctx, sarvam = _sarvam_client(body={"request_id": "r1", "transcript": " नमस्ते ", "language_code": "hi-IN"})
        with patch("app.ai.speech.get_settings", return_value=_sarvam_settings()), patch("app.ai.speech.httpx.AsyncClient", return_value=ctx):
            result = await speech.transcribe_audio(b"audio", "note.m4a", "audio/mp4", "te")

        assert result == {"transcript": "नमस्ते", "language_code": "hi-IN"}
        kwargs = sarvam.post.call_args.kwargs
        assert sarvam.post.call_args.args[0] == "https://api.sarvam.ai/speech-to-text"
        assert kwargs["headers"] == {"api-subscription-key": "sarvam-test-key"}
        assert kwargs["data"] == {"model": "saaras:v3", "mode": "transcribe", "language_code": "te-IN"}
        assert kwargs["files"]["file"] == ("note.m4a", b"audio", "audio/mp4")

    @pytest.mark.asyncio
    async def test_missing_key_500(self):
        with patch("app.ai.speech.get_settings", return_value=_sarvam_settings(key=None)):
            with pytest.raises(HTTPException) as exc:
                await speech.transcribe_audio(b"audio", "note.wav", "audio/wav")
        assert exc.value.status_code == 500

    @pytest.mark.asyncio
    async def test_rejected_audio_422_with_reason(self):
        body = {"error": {"message": "Audio duration exceeds 30 seconds", "code": "invalid_request_error"}}
        ctx, _ = _sarvam_client(status_code=400, body=body)
        with patch("app.ai.speech.get_settings", return_value=_sarvam_settings()), patch("app.ai.speech.httpx.AsyncClient", return_value=ctx):
            with pytest.raises(HTTPException) as exc:
                await speech.transcribe_audio(b"audio", "note.wav", "audio/wav")
        assert exc.value.status_code == 422
        assert "30 seconds" in exc.value.detail

    @pytest.mark.asyncio
    async def test_auth_failure_502_without_leaking_key(self):
        ctx, _ = _sarvam_client(status_code=403, body={"error": {"message": "Invalid API key"}})
        with patch("app.ai.speech.get_settings", return_value=_sarvam_settings()), patch("app.ai.speech.httpx.AsyncClient", return_value=ctx):
            with pytest.raises(HTTPException) as exc:
                await speech.transcribe_audio(b"audio", "note.wav", "audio/wav")
        assert exc.value.status_code == 502
        assert "sarvam-test-key" not in exc.value.detail

    @pytest.mark.asyncio
    async def test_timeout_504(self):
        ctx, _ = _sarvam_client(raises=httpx.ReadTimeout("slow"))
        with patch("app.ai.speech.get_settings", return_value=_sarvam_settings()), patch("app.ai.speech.httpx.AsyncClient", return_value=ctx):
            with pytest.raises(HTTPException) as exc:
                await speech.transcribe_audio(b"audio", "note.wav", "audio/wav")
        assert exc.value.status_code == 504
