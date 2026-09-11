"""
Supabase access-token auth tests — app.core.supabase_auth, get_current_user, and the
image enhance endpoint for Supabase-authenticated users.

Tokens are signed with a throwaway ES256 key and the JWKS client is replaced with a stub
returning its public key, so no network access is needed.
"""
import os
import time
from types import SimpleNamespace

os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("APP_ENV", "development")
os.environ.setdefault("SUPABASE_URL", "https://placeholder.supabase.co")

import cv2
import jwt
import numpy as np
import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.main import app
from app.core import supabase_auth
from app.core.config import get_settings
from app.core.security import get_current_user

ISSUER = f"{get_settings().SUPABASE_URL.rstrip('/')}/auth/v1"
SIGNING_KEY = ec.generate_private_key(ec.SECP256R1())
USER_ID = "8d6c3f4e-1111-2222-3333-444455556666"
PROFILE = {"id": USER_ID, "auth_user_id": USER_ID, "full_name": "Test Artisan", "role": "seller"}

client = TestClient(app)


def make_token(key=SIGNING_KEY, **overrides) -> str:
    now = int(time.time())
    claims = {
        "iss": ISSUER,
        "sub": USER_ID,
        "aud": "authenticated",
        "role": "authenticated",
        "email": "artisan@kalacart.test",
        "iat": now,
        "exp": now + 3600,
        "user_metadata": {"full_name": "Test Artisan", "role": "seller"},
    }
    claims.update(overrides)
    return jwt.encode(claims, key, algorithm="ES256", headers={"kid": "test-kid"})


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
def stub_supabase(monkeypatch):
    stub_jwks = SimpleNamespace(get_signing_key_from_jwt=lambda token: SimpleNamespace(key=SIGNING_KEY.public_key()))
    monkeypatch.setattr(supabase_auth, "_jwks_client", stub_jwks)
    monkeypatch.setattr(supabase_auth, "_get_profile", lambda uid: dict(PROFILE))
    saved = app.dependency_overrides.pop(get_current_user, None)
    yield
    if saved is not None:
        app.dependency_overrides[get_current_user] = saved


class TestTokenVerification:
    def test_is_supabase_token_checks_issuer(self):
        assert supabase_auth.is_supabase_token(make_token()) is True
        assert supabase_auth.is_supabase_token(make_token(iss="https://securetoken.google.com/x")) is False
        assert supabase_auth.is_supabase_token("fake-jwt-for-test") is False

    def test_valid_token_returns_user_context(self):
        resp = client.get("/api/v1/auth/me", headers=auth(make_token()))
        assert resp.status_code == 200, resp.text
        data = resp.json()["data"]
        assert data["firebase_uid"] == USER_ID
        assert data["email"] == "artisan@kalacart.test"
        assert data["artisan"]["id"] == USER_ID
        assert data["artisan"]["role"] == "seller"

    def test_user_without_profile_still_authenticated(self, monkeypatch):
        monkeypatch.setattr(supabase_auth, "_get_profile", lambda uid: None)
        resp = client.get("/api/v1/auth/me", headers=auth(make_token()))
        assert resp.status_code == 200, resp.text
        assert resp.json()["data"]["artisan"]["id"] == USER_ID

    def test_expired_token_401(self):
        resp = client.get("/api/v1/auth/me", headers=auth(make_token(exp=int(time.time()) - 60)))
        assert resp.status_code == 401
        assert "expired" in resp.json()["message"].lower()

    def test_wrong_audience_401(self):
        resp = client.get("/api/v1/auth/me", headers=auth(make_token(aud="anon")))
        assert resp.status_code == 401

    def test_forged_signature_401(self):
        forged = make_token(key=ec.generate_private_key(ec.SECP256R1()))
        resp = client.get("/api/v1/auth/me", headers=auth(forged))
        assert resp.status_code == 401

    def test_signing_keys_unreachable_503(self, monkeypatch):
        def unreachable(token):
            raise jwt.PyJWKClientConnectionError("connection refused")

        monkeypatch.setattr(supabase_auth, "_jwks_client", SimpleNamespace(get_signing_key_from_jwt=unreachable))
        resp = client.get("/api/v1/auth/me", headers=auth(make_token()))
        assert resp.status_code == 503


def _product_png() -> bytes:
    img = np.full((400, 400, 3), (205, 208, 210), dtype=np.uint8)
    cv2.circle(img, (200, 200), 110, (40, 40, 200), -1)
    ok, buf = cv2.imencode(".png", img)
    assert ok
    return buf.tobytes()


class TestEnhanceAsSupabaseUser:
    def test_uploads_to_user_folder_with_user_token(self):
        token = make_token()
        with patch("app.api.image._upload_as_user") as upload:
            upload.side_effect = lambda bucket, access_token, files: [
                f"https://cdn.test/{bucket}/{path}" for path, _, _ in files
            ]
            resp = client.post(
                "/api/v1/image/enhance",
                files={"image": ("photo.png", _product_png(), "image/png")},
                data={"output_format": "1:1"},
                headers=auth(token),
            )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["storage_uploaded"] is True
        assert body["data"]["enhanced_url"].endswith("_enhanced.webp")
        bucket, access_token, files = upload.call_args.args
        assert access_token == token
        assert all(path.startswith(f"{USER_ID}/") for path, _, _ in files)

    def test_storage_rejection_returns_image_inline(self):
        with patch("app.api.image._upload_as_user", return_value=None):
            resp = client.post(
                "/api/v1/image/enhance",
                files={"image": ("photo.png", _product_png(), "image/png")},
                data={"output_format": "1:1"},
                headers=auth(make_token()),
            )
        assert resp.status_code == 200, resp.text
        data = resp.json()["data"]
        assert data["storage_uploaded"] is False
        assert data["enhanced_url"].startswith("data:image/webp;base64,")
        assert data["original_url"] is None

    def test_response_data_is_flat_for_mobile_client(self):
        with patch("app.api.image._upload_as_user", return_value=None):
            resp = client.post(
                "/api/v1/image/enhance",
                files={"image": ("photo.png", _product_png(), "image/png")},
                headers=auth(make_token()),
            )
        assert resp.status_code == 200, resp.text
        assert not any(isinstance(v, (dict, list)) for v in resp.json()["data"].values())
