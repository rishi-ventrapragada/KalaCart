"""
Centralized application configuration using Pydantic Settings.

All environment variables are validated here — no hardcoded secrets elsewhere.
Loads from .env via python-dotenv / pydantic-settings.
"""

from functools import lru_cache
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment / .env file.

    Every secret must be injected via environment — never hardcoded.
    Use get_settings() to obtain the cached singleton.
    """

    # ── App ──────────────────────────────────────────────────────────
    APP_NAME: str = Field(default="KalaCart API", description="Application name")
    APP_ENV: str = Field(default="development", description="development | staging | production")
    DEBUG: bool = Field(default=False, description="Enable debug mode")
    API_V1_PREFIX: str = Field(default="/api/v1", description="API version prefix")
    SECRET_KEY: str = Field(default="change-me-in-production", description="JWT / signing secret")
    # Held as a raw string, NOT List[str]. pydantic-settings JSON-decodes complex
    # types (list/dict) in the env source *before* field validators run, so a
    # documented comma-separated value like "https://a.com,https://b.com" raised
    # SettingsError at import and crashed startup. Parsing happens in the
    # CORS_ORIGINS property below, which accepts both comma-separated and JSON.
    CORS_ORIGINS_RAW: str = Field(
        default="http://localhost:3000,http://10.0.2.2:8000",
        alias="CORS_ORIGINS",
        description="Allowed CORS origins — comma-separated or JSON array",
    )

    # ── Supabase ─────────────────────────────────────────────────────
    SUPABASE_URL: Optional[str] = Field(default=None, description="Supabase project URL")
    SUPABASE_KEY: Optional[str] = Field(default=None, description="Supabase anon / publishable key")
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = Field(
        default=None, description="Supabase service_role key (server-side privileged)"
    )
    SUPABASE_STORAGE_BUCKET: str = Field(
        default="product-images", description="Default Supabase Storage bucket"
    )
    DATABASE_URL: Optional[str] = Field(
        default=None, description="Direct PostgreSQL connection string (Supabase pooler)"
    )

    # ── Firebase ─────────────────────────────────────────────────────
    FIREBASE_CREDENTIALS_PATH: Optional[str] = Field(
        default=None, description="Path to Firebase service account JSON"
    )
    FIREBASE_CREDENTIALS_JSON: Optional[str] = Field(
        default=None, description="Inline Firebase service account JSON string"
    )

    # ── AI / OpenRouter ──────────────────────────────────────────────
    OPENROUTER_API_KEY: Optional[str] = Field(default=None, description="OpenRouter API key")
    OPENROUTER_BASE_URL: str = Field(default="https://openrouter.ai/api/v1")
    # Text and vision models are held to OpenRouter ":free" slugs by decision D-13.
    # The AI-Features handover defaulted these to qwen/qwen3.6-flash and
    # qwen/qwen3.7-flash, which are paid; those defaults were not adopted.
    # Both slugs below are free and vision-capable, and are the same models the
    # agent's fallback walker ranks first (app/agent/models.py).
    QWEN_MODEL: str = Field(default="google/gemma-4-31b-it:free")
    # Was "deepseek/deepseek-chat" — a PAID slug, and reachable: app/api/pricing.py
    # (_call_openrouter) and app/ai/pricing.py both send requests with it, so a
    # deployed backend would have billed the OpenRouter account on every pricing
    # call. Repointed to the same free slug the other features use, per D-13.
    # The env var still overrides if a paid model is ever deliberately chosen.
    DEEPSEEK_MODEL: str = Field(default="google/gemma-4-31b-it:free")
    # Image-capable model that reads product photos for the pricing assistant
    VISION_MODEL: str = Field(default="google/gemma-4-31b-it:free")

    # ── Speech-to-text / Sarvam AI (voice notes in Indian languages) ─
    SARVAM_API_KEY: Optional[str] = Field(default=None, description="Sarvam AI API subscription key")
    SARVAM_BASE_URL: str = Field(default="https://api.sarvam.ai")
    SARVAM_STT_MODEL: str = Field(default="saaras:v3", description="Sarvam speech-to-text model")

    # ── Misc ─────────────────────────────────────────────────────────
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, description="API rate limit")

    # ── Multi-Region Cloud Infrastructure (Phase 9) ───────────────────
    PRIMARY_REGION: str = Field(default="ap-south-1", description="Primary write region (India / Mumbai)")
    CURRENT_REGION: str = Field(default="ap-south-1", description="Current deployed region")
    CDN_BASE_URL: str = Field(default="https://cdn.kalacart.in", description="Global Cloudflare CDN endpoint")
    EDGE_CACHE_ENABLED: bool = Field(default=True, description="Enable edge caching for static & read assets")
    REDIS_URL: str = Field(default="redis://localhost:6379/0", description="Redis connection URL for cache & pubsub")
    WORKER_CONCURRENCY: int = Field(default=8, description="Concurrency level for background task workers")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # ignore unrelated env vars
        case_sensitive=False,
    )

    # ── Validators ───────────────────────────────────────────────────
    @field_validator("DEBUG", mode="before")
    @classmethod
    def _parse_debug(cls, v):
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes", "on")
        return v

    # ── Helpers ──────────────────────────────────────────────────────
    @property
    def CORS_ORIGINS(self) -> List[str]:
        """
        Allowed CORS origins, parsed from CORS_ORIGINS_RAW.

        Accepts either a comma-separated string (the format documented in
        .env.example) or a JSON array. Callers read settings.CORS_ORIGINS and
        always get a list, so this is a drop-in for the former List[str] field.

        Note: CORS is a browser policy. The Flutter/Android app sends no Origin
        header and is unaffected by this list; it matters only for the web admin.
        """
        raw = (self.CORS_ORIGINS_RAW or "").strip()
        if not raw:
            return []
        if raw.startswith("["):
            import json

            try:
                parsed = json.loads(raw)
                if isinstance(parsed, list):
                    return [str(o).strip() for o in parsed if str(o).strip()]
            except Exception:
                pass
        return [origin.strip() for origin in raw.split(",") if origin.strip()]

    @property
    def supabase_service_key(self) -> Optional[str]:
        """Preferred privileged key — service_role falls back to anon key."""
        return self.SUPABASE_SERVICE_ROLE_KEY or self.SUPABASE_KEY

    @property
    def is_production(self) -> bool:
        return self.APP_ENV.lower() == "production"

    @field_validator("SECRET_KEY")
    @classmethod
    def _validate_secret_key(cls, v: str) -> str:
        # In production, require non-default, sufficiently long secret
        # Non-blocking here (validate lazily) — main.py startup will warn/error if insecure
        return v

    def validate_secret_key_or_warn(self) -> None:
        """Call on startup: ensure SECRET_KEY is not default in production."""
        import logging as _lg

        _lg.getLogger(__name__)
        if self.is_production and self.SECRET_KEY in ("change-me-in-production", "change-me-to-a-secure-random-string", ""):
            raise ValueError(
                "SECRET_KEY is insecure default in production — set a 32+ char random value via env SECRET_KEY"
            )
        if self.is_production and len(self.SECRET_KEY) < 32:
            import logging

            logging.getLogger(__name__).warning(
                "SECRET_KEY length %d < 32 in production — generate longer random key", len(self.SECRET_KEY)
            )

    def validate_supabase(self) -> None:
        """Raise ValueError if required Supabase vars are missing."""
        if not self.SUPABASE_URL:
            raise ValueError("SUPABASE_URL is required — set it in .env")
        if not self.supabase_service_key:
            raise ValueError(
                "SUPABASE_SERVICE_ROLE_KEY or SUPABASE_KEY is required — set it in .env"
            )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Cached singleton — reads .env once, reuses across the app.
    Call get_settings() anywhere instead of os.getenv().
    """
    return Settings()
