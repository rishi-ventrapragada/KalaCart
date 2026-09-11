"""Pydantic models for Language domain."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class LanguageBase(BaseModel):
    code: str = Field(
        ...,
        min_length=2,
        max_length=10,
        description="ISO 639-1 language code",
        examples=["en", "hi", "bn", "ta"],
        pattern=r"^[a-z]{2,3}(-[A-Z]{2})?$",
    )
    name: str = Field(..., min_length=1, max_length=50, description="English name", examples=["Hindi"])
    native_name: str = Field(..., min_length=1, max_length=50, description="Native script name", examples=["हिन्दी"])

    @field_validator("code")
    @classmethod
    def _normalize_code(cls, v: str) -> str:
        return v.strip().lower()

    @field_validator("name", "native_name")
    @classmethod
    def _strip_names(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("name fields must not be empty")
        return v


class LanguageCreate(LanguageBase):
    """Payload for creating a language (admin)."""
    is_active: bool = Field(default=True, description="Whether language is offered to artisans")


class LanguageUpdate(BaseModel):
    """Partial update."""

    name: Optional[str] = Field(default=None, min_length=1, max_length=50)
    native_name: Optional[str] = Field(default=None, min_length=1, max_length=50)
    is_active: Optional[bool] = None


class LanguageResponse(LanguageBase):
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Default language seed for fallback when DB not seeded
DEFAULT_LANGUAGES = [
    {"code": "en", "name": "English", "native_name": "English"},
    {"code": "hi", "name": "Hindi", "native_name": "हिन्दी"},
    {"code": "bn", "name": "Bengali", "native_name": "বাংলা"},
    {"code": "ta", "name": "Tamil", "native_name": "தமிழ்"},
    {"code": "te", "name": "Telugu", "native_name": "తెలుగు"},
    {"code": "mr", "name": "Marathi", "native_name": "मराठी"},
    {"code": "gu", "name": "Gujarati", "native_name": "ગુજરાતી"},
    {"code": "kn", "name": "Kannada", "native_name": "ಕನ್ನಡ"},
    {"code": "ml", "name": "Malayalam", "native_name": "മലയാളം"},
    {"code": "pa", "name": "Punjabi", "native_name": "ਪੰਜਾਬੀ"},
]
