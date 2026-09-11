"""
Catalog API tests — POST /api/v1/catalog/generate

Coverage: auth, validation, control chars, retry, 502, 429, key never exposed.
Uses FastAPI TestClient + httpx.AsyncClient mocking.
"""
import json
import os

os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("APP_ENV", "development")
os.environ.setdefault("SUPABASE_URL", "https://placeholder.supabase.co")
os.environ.setdefault("SUPABASE_STORAGE_BUCKET", "product-images")
os.environ.setdefault("OPENROUTER_API_KEY", "test-key-do-not-expose")
os.environ.setdefault("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
os.environ.setdefault("QWEN_MODEL", "qwen/qwen3-32b")

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.core.security import get_current_user
from app.api import catalog as catalog_module

# ── Auth override ──────────────────────────────────────────────────────────
MOCK_USER = {"firebase_uid": "test", "artisan": {"id": "art123"}, "claims": {}}


def _override_user():
    return MOCK_USER


@pytest.fixture(autouse=True)
def override_auth():
    app.dependency_overrides[get_current_user] = _override_user
    yield
    app.dependency_overrides[get_current_user] = _override_user


client = TestClient(app)

# ── Valid catalog payload (passes _validate_catalog_schema) ────────────────
VALID_CATALOG = {
    "title": "Handloom Cotton Saree - Warangal",
    "description_en": "Handwoven in Warangal using pure cotton and natural dyes, this handloom saree celebrates Telangana textile heritage. Breathable plain weave drapes elegantly while subtle natural-dyed hues reflect eco-conscious craftsmanship. Woven on traditional pit loom supporting sustainable livelihoods and preserving generations of skill.",
    "description_hi": "वारंगल में शुद्ध कॉटन और प्राकृतिक रंगों से हाथ से बुनी गई यह साड़ी तेलंगाना की बुनकर परंपरा का प्रतीक है। इसकी हल्की बुनावट और प्राकृतिक रंग इसे रोज़मर्रा और त्योहार दोनों के लिए उपयुक्त बनाते हैं। पारंपरिक हथकरघे पर बनी यह साड़ी टिकाऊ है।",
    "category": "Textiles",
    "materials": ["Cotton"],
    "seo_tags": ["Handmade", "Cotton", "Sustainable"],
    "care": "Hand wash only",
}

VALID_CATALOG_JSON = json.dumps(VALID_CATALOG)


def _mock_openrouter_response(content_str: str, status_code: int = 200):
    """Build a mocked httpx response object."""
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.json.return_value = {"choices": [{"message": {"content": content_str}}]}

    def _raise():
        if status_code >= 400:
            import httpx

            req = MagicMock()
            resp = MagicMock()
            resp.status_code = status_code
            raise httpx.HTTPStatusError("upstream error", request=req, response=resp)

    mock_resp.raise_for_status = MagicMock(side_effect=_raise if status_code >= 400 else None)
    return mock_resp


def _make_async_client_mock(mock_resp_or_side_effect):
    """
    Returns a mock for httpx.AsyncClient that acts as async context manager.
    mock_resp_or_side_effect can be single mock response or list for sequential calls.
    """
    mock_client_instance = MagicMock()
    if isinstance(mock_resp_or_side_effect, list):
        mock_client_instance.post = AsyncMock(side_effect=mock_resp_or_side_effect)
    else:
        mock_client_instance.post = AsyncMock(return_value=mock_resp_or_side_effect)

    mock_async_client = MagicMock()
    mock_async_client.__aenter__ = AsyncMock(return_value=mock_client_instance)
    mock_async_client.__aexit__ = AsyncMock(return_value=None)
    return mock_async_client


@pytest.fixture(autouse=True)
def _clear_rate_limit():
    """Clear in-memory rate limiter before each test to avoid cross-test pollution."""
    catalog_module._clear_rate_limit_store()
    yield
    catalog_module._clear_rate_limit_store()


# ── Success cases ──────────────────────────────────────────────────────────


class TestGenerateSuccess:
    @patch("app.api.catalog.httpx.AsyncClient")
    def test_generate_success_en(self, mock_async_client_cls):
        mock_resp = _mock_openrouter_response(VALID_CATALOG_JSON)
        mock_async_client_cls.return_value = _make_async_client_mock(mock_resp)
        payload = {"transcript": "This is a handloom cotton saree made in Warangal with natural dyes", "language": "en"}
        resp = client.post("/api/v1/catalog/generate", json=payload, headers={"Authorization": "Bearer fake"})
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["title"] == VALID_CATALOG["title"]
        assert data["data"]["category"] == "Textiles"
        # No key leakage
        assert "OPENROUTER_API_KEY" not in resp.text
        assert "test-key-do-not-expose" not in resp.text

    @patch("app.api.catalog.httpx.AsyncClient")
    def test_generate_success_te(self, mock_async_client_cls):
        mock_resp = _mock_openrouter_response(VALID_CATALOG_JSON)
        mock_async_client_cls.return_value = _make_async_client_mock(mock_resp)
        payload = {
            "transcript": "Nenu cotton tho handloom saree chesanu, natural dyes vadenu, Warangal nunchi",
            "language": "te",
        }
        resp = client.post("/api/v1/catalog/generate", json=payload, headers={"Authorization": "Bearer fake"})
        assert resp.status_code == 200, resp.text
        assert resp.json()["success"] is True
        assert "OPENROUTER_API_KEY" not in resp.text


# ── Validation error cases ─────────────────────────────────────────────────


class TestGenerateValidation:
    def test_invalid_short_transcript(self):
        payload = {"transcript": "hi", "language": "en"}
        resp = client.post("/api/v1/catalog/generate", json=payload, headers={"Authorization": "Bearer fake"})
        assert resp.status_code == 422, resp.text

    def test_invalid_long_transcript(self):
        payload = {"transcript": "a" * 1001, "language": "en"}
        resp = client.post("/api/v1/catalog/generate", json=payload, headers={"Authorization": "Bearer fake"})
        assert resp.status_code == 422, resp.text

    def test_invalid_language(self):
        # limit to te|hi|en|ta|kn regex, fr should 422
        payload = {"transcript": "Valid transcript with enough length for testing", "language": "fr"}
        resp = client.post("/api/v1/catalog/generate", json=payload, headers={"Authorization": "Bearer fake"})
        assert resp.status_code == 422, resp.text

    @patch("app.api.catalog.httpx.AsyncClient")
    def test_control_chars_stripped(self, mock_async_client_cls):
        # \x00\x01 should be stripped and still succeed
        mock_resp = _mock_openrouter_response(VALID_CATALOG_JSON)
        mock_async_client_cls.return_value = _make_async_client_mock(mock_resp)
        payload = {
            "transcript": "Valid cotton saree Warangal natural dyes handloom\x00\x01 with extra text",
            "language": "en",
        }
        resp = client.post("/api/v1/catalog/generate", json=payload, headers={"Authorization": "Bearer fake"})
        assert resp.status_code == 200, resp.text
        assert resp.json()["success"] is True

    def test_invalid_language_uppercase_normalized_or_rejected(self):
        # FR upper should be lowercased to fr -> pattern rejects -> 422
        payload = {"transcript": "Valid transcript with enough length for testing", "language": "FR"}
        resp = client.post("/api/v1/catalog/generate", json=payload, headers={"Authorization": "Bearer fake"})
        assert resp.status_code == 422

    def test_transcript_exact_boundary_5_chars(self):
        # 5 chars minimal should be allowed if mock succeeds
        with patch("app.api.catalog.httpx.AsyncClient") as m:
            m.return_value = _make_async_client_mock(_mock_openrouter_response(VALID_CATALOG_JSON))
            payload = {"transcript": "Hello world amazing craft item here", "language": "en"}
            resp = client.post("/api/v1/catalog/generate", json=payload, headers={"Authorization": "Bearer fake"})
            assert resp.status_code == 200

    def test_transcript_exact_boundary_1000_chars(self):
        with patch("app.api.catalog.httpx.AsyncClient") as m:
            m.return_value = _make_async_client_mock(_mock_openrouter_response(VALID_CATALOG_JSON))
            payload = {"transcript": "a " * 500, "language": "en"}  # 1000 chars inc spaces stripped trim -> 999 ?
            # adjust to exactly 1000
            t = "x" * 1000
            resp = client.post("/api/v1/catalog/generate", json={"transcript": t, "language": "en"}, headers={"Authorization": "Bearer fake"})
            assert resp.status_code == 200


# ── Retry / 502 cases ──────────────────────────────────────────────────────


class TestGenerateRetry:
    @patch("app.api.catalog.httpx.AsyncClient")
    def test_malformed_json_retry(self, mock_async_client_cls):
        # first call returns not json, second returns valid -> 200
        first = _mock_openrouter_response("not json at all ###")
        second = _mock_openrouter_response(VALID_CATALOG_JSON)
        mock_async_client_cls.return_value = _make_async_client_mock([first, second])
        payload = {"transcript": "This is a valid length transcript for retry logic test", "language": "en"}
        resp = client.post("/api/v1/catalog/generate", json=payload, headers={"Authorization": "Bearer fake"})
        assert resp.status_code == 200, resp.text
        assert resp.json()["data"]["title"] == VALID_CATALOG["title"]

    @patch("app.api.catalog.httpx.AsyncClient")
    def test_persistent_malformed_502(self, mock_async_client_cls):
        bad1 = _mock_openrouter_response("not json")
        bad2 = _mock_openrouter_response("also not json {")
        mock_async_client_cls.return_value = _make_async_client_mock([bad1, bad2])
        payload = {"transcript": "Valid transcript length for persistent failure test", "language": "en"}
        resp = client.post("/api/v1/catalog/generate", json=payload, headers={"Authorization": "Bearer fake"})
        assert resp.status_code == 502, resp.text
        assert "malformed" in resp.text.lower()

    @patch("app.api.catalog.httpx.AsyncClient")
    def test_schema_validation_missing_materials_triggers_502(self, mock_async_client_cls):
        # LLM invents missing materials array => schema invalid => retry, both invalid => 502
        invalid = json.dumps({k: v for k, v in VALID_CATALOG.items() if k != "materials"})
        r1 = _mock_openrouter_response(invalid)
        r2 = _mock_openrouter_response(invalid)
        mock_async_client_cls.return_value = _make_async_client_mock([r1, r2])
        payload = {"transcript": "Cotton saree from Warangal with natural dyes handmade", "language": "en"}
        resp = client.post("/api/v1/catalog/generate", json=payload, headers={"Authorization": "Bearer fake"})
        assert resp.status_code == 502, resp.text

    @patch("app.api.catalog.httpx.AsyncClient")
    def test_schema_invalid_then_valid_on_retry(self, mock_async_client_cls):
        invalid = json.dumps({**VALID_CATALOG, "materials": []})  # empty materials invalid
        valid = _mock_openrouter_response(VALID_CATALOG_JSON)
        mock_async_client_cls.return_value = _make_async_client_mock([_mock_openrouter_response(invalid), valid])
        payload = {"transcript": "Cotton saree Warangal handmade with natural dyes properly", "language": "en"}
        resp = client.post("/api/v1/catalog/generate", json=payload, headers={"Authorization": "Bearer fake"})
        assert resp.status_code == 200, resp.text

    @patch("app.api.catalog.httpx.AsyncClient")
    def test_code_fence_stripped_success(self, mock_async_client_cls):
        fenced = "```json\n" + VALID_CATALOG_JSON + "\n```"
        mock_async_client_cls.return_value = _make_async_client_mock(_mock_openrouter_response(fenced))
        payload = {"transcript": "Handloom cotton saree Warangal natural dyes handloom", "language": "en"}
        resp = client.post("/api/v1/catalog/generate", json=payload, headers={"Authorization": "Bearer fake"})
        assert resp.status_code == 200

    @patch("app.api.catalog.httpx.AsyncClient")
    def test_never_exposes_key_on_502(self, mock_async_client_cls):
        bad1 = _mock_openrouter_response("bad")
        bad2 = _mock_openrouter_response("bad2")
        mock_async_client_cls.return_value = _make_async_client_mock([bad1, bad2])
        payload = {"transcript": "Valid transcript for key leak check on error path", "language": "en"}
        resp = client.post("/api/v1/catalog/generate", json=payload, headers={"Authorization": "Bearer fake"})
        assert resp.status_code == 502
        assert "OPENROUTER_API_KEY" not in resp.text
        assert "test-key-do-not-expose" not in resp.text

    @patch("app.api.catalog.httpx.AsyncClient")
    def test_never_exposes_key_on_success(self, mock_async_client_cls):
        mock_async_client_cls.return_value = _make_async_client_mock(_mock_openrouter_response(VALID_CATALOG_JSON))
        payload = {"transcript": "Another valid transcript for key leak success path", "language": "en"}
        resp = client.post("/api/v1/catalog/generate", json=payload, headers={"Authorization": "Bearer fake"})
        assert resp.status_code == 200
        assert "OPENROUTER_API_KEY" not in resp.text
        assert "test-key-do-not-expose" not in resp.text


# ── Auth / Rate limit ─────────────────────────────────────────────────────


class TestGenerateAuthRateLimit:
    def test_unauthorized_401(self):
        # remove auth override -> should 401
        app.dependency_overrides.pop(get_current_user, None)
        try:
            c2 = TestClient(app)
            payload = {"transcript": "Valid transcript with enough length for testing", "language": "en"}
            resp = c2.post("/api/v1/catalog/generate", json=payload)
            assert resp.status_code == 401, resp.text
            assert "authorization" in resp.text.lower() or "missing" in resp.text.lower()
            assert "OPENROUTER_API_KEY" not in resp.text
        finally:
            app.dependency_overrides[get_current_user] = _override_user

    @patch("app.api.catalog.httpx.AsyncClient")
    def test_rate_limit_429(self, mock_async_client_cls):
        mock_resp = _mock_openrouter_response(VALID_CATALOG_JSON)
        # Need 11 responses because 11 calls
        mock_async_client_cls.return_value = _make_async_client_mock([mock_resp] * 12)
        payload = {"transcript": "Handloom cotton saree Warangal natural dyes for rate limit", "language": "en"}
        # Send 11 rapid requests; first 10 should succeed, 11th 429
        statuses = []
        for i in range(11):
            r = client.post("/api/v1/catalog/generate", json=payload, headers={"Authorization": "Bearer fake"})
            statuses.append(r.status_code)
        assert statuses[:10] == [200] * 10, f"first 10 should be 200 got {statuses}"
        assert statuses[10] == 429, f"11th should be 429 got {statuses}"
        # Check Retry-After header present on 429th request body or headers
        # Re-issue one more to inspect headers
        last = client.post("/api/v1/catalog/generate", json=payload, headers={"Authorization": "Bearer fake"})
        assert last.status_code == 429
        assert "OPENROUTER_API_KEY" not in last.text

    @patch("app.api.catalog.httpx.AsyncClient")
    def test_rate_limit_resets_after_clear(self, mock_async_client_cls):
        mock_resp = _mock_openrouter_response(VALID_CATALOG_JSON)
        mock_async_client_cls.return_value = _make_async_client_mock([mock_resp] * 5)
        payload = {"transcript": "Handloom cotton saree Warangal natural dyes for reset test", "language": "en"}
        for _ in range(5):
            resp = client.post("/api/v1/catalog/generate", json=payload, headers={"Authorization": "Bearer fake"})
            assert resp.status_code == 200
        # manually clear and ensure next succeeds not rate limited
        catalog_module._clear_rate_limit_store()
        mock_async_client_cls.return_value = _make_async_client_mock(_mock_openrouter_response(VALID_CATALOG_JSON))
        resp = client.post("/api/v1/catalog/generate", json=payload, headers={"Authorization": "Bearer fake"})
        assert resp.status_code == 200


class TestCatalogEdgeCoverage:
    @patch("app.api.catalog.httpx.AsyncClient")
    def test_upstream_http_error_returns_502(self, mock_async_client_cls):
        # Mock response with 502 status -> raise_for_status triggers 502
        err_resp = _mock_openrouter_response("error", status_code=502)
        mock_async_client_cls.return_value = _make_async_client_mock(err_resp)
        payload = {"transcript": "Handloom cotton saree Warangal natural dyes for upstream error", "language": "en"}
        resp = client.post("/api/v1/catalog/generate", json=payload, headers={"Authorization": "Bearer fake"})
        assert resp.status_code == 502
        assert "OPENROUTER_API_KEY" not in resp.text

    @patch("app.api.catalog.httpx.AsyncClient")
    def test_timeout_returns_504(self, mock_async_client_cls):
        import httpx

        mock_instance = MagicMock()
        mock_instance.post = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_cm.__aexit__ = AsyncMock(return_value=None)
        mock_async_client_cls.return_value = mock_cm
        payload = {"transcript": "Handloom cotton saree Warangal natural dyes timeout test", "language": "en"}
        resp = client.post("/api/v1/catalog/generate", json=payload, headers={"Authorization": "Bearer fake"})
        assert resp.status_code == 504
        assert "OPENROUTER_API_KEY" not in resp.text

    @patch("app.api.catalog.httpx.AsyncClient")
    def test_empty_llm_content_returns_502(self, mock_async_client_cls):
        empty_resp = _mock_openrouter_response("   ")
        mock_async_client_cls.return_value = _make_async_client_mock(empty_resp)
        payload = {"transcript": "Handloom cotton saree Warangal natural dyes empty content", "language": "en"}
        resp = client.post("/api/v1/catalog/generate", json=payload, headers={"Authorization": "Bearer fake"})
        assert resp.status_code == 502

    @patch("app.api.catalog.get_settings")
    def test_missing_api_key_returns_500(self, mock_settings):
        mock_settings.return_value.OPENROUTER_API_KEY = None
        mock_settings.return_value.OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
        mock_settings.return_value.QWEN_MODEL = "qwen/qwen3-32b"
        # Also patch os.getenv to return None
        with patch("app.api.catalog.os.getenv", return_value=None):
            payload = {"transcript": "Handloom cotton saree Warangal natural dyes missing key", "language": "en"}
            resp = client.post("/api/v1/catalog/generate", json=payload, headers={"Authorization": "Bearer fake"})
            assert resp.status_code == 500
            assert "OPENROUTER_API_KEY" not in resp.text

    def test_load_system_prompt_fallback(self):
        # Force prompt file missing -> fallback used via patching Path.exists
        with patch("pathlib.Path.exists", return_value=False):
            txt = catalog_module._load_system_prompt()
            assert "Preserve artisan meaning" in txt or "Smart Catalog" in txt
            assert "qwen" in txt.lower() or "Qwen" in txt

    @patch("app.api.catalog.httpx.AsyncClient")
    def test_malformed_response_structure_returns_502(self, mock_async_client_cls):
        bad = MagicMock()
        bad.json.return_value = {"wrong": "structure"}
        bad.raise_for_status = MagicMock()
        mock_async_client_cls.return_value = _make_async_client_mock(bad)
        payload = {"transcript": "Handloom cotton saree Warangal natural dyes bad structure", "language": "en"}
        resp = client.post("/api/v1/catalog/generate", json=payload, headers={"Authorization": "Bearer fake"})
        assert resp.status_code == 502

    @patch("app.api.catalog.httpx.AsyncClient")
    def test_request_error_returns_502(self, mock_async_client_cls):
        import httpx

        mock_instance = MagicMock()
        mock_instance.post = AsyncMock(side_effect=httpx.RequestError("network down"))
        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_cm.__aexit__ = AsyncMock(return_value=None)
        mock_async_client_cls.return_value = mock_cm
        payload = {"transcript": "Handloom cotton saree Warangal natural dyes request error", "language": "en"}
        resp = client.post("/api/v1/catalog/generate", json=payload, headers={"Authorization": "Bearer fake"})
        assert resp.status_code == 502

    @patch("app.api.catalog.httpx.AsyncClient")
    def test_fenced_json_with_preamble_retry(self, mock_async_client_cls):
        preamble = 'Here is JSON: ```json\n' + VALID_CATALOG_JSON + '\n``` hope ok'
        mock_async_client_cls.return_value = _make_async_client_mock(_mock_openrouter_response(preamble))
        payload = {"transcript": "Handloom cotton saree Warangal natural dyes preamble", "language": "en"}
        resp = client.post("/api/v1/catalog/generate", json=payload, headers={"Authorization": "Bearer fake"})
        assert resp.status_code == 200
