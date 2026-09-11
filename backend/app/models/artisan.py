"""Pydantic models for Artisan domain — with validators and enums."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class ArtisanBase(BaseModel):
    name: str = Field(
        ..., min_length=1, max_length=100, description="Artisan display name", examples=["Ramesh Kumar"]
    )
    phone: str = Field(
        ..., pattern=r"^\+?[0-9]{10,15}$", description="E.164 phone number", examples=["+919876543210"]
    )
    language_preference: str = Field(
        default="hi", min_length=2, max_length=10, description="Preferred language ISO code", examples=["hi", "en"]
    )
    location: Optional[str] = Field(default=None, max_length=200, description="Village / City, State")
    craft_type: Optional[str] = Field(
        default=None, max_length=100, description="Primary craft, e.g., pottery, textile", examples=["pottery"]
    )

    @field_validator("name")
    @classmethod
    def _strip_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("name must not be empty")
        return v

    @field_validator("language_preference")
    @classmethod
    def _normalize_lang(cls, v: str) -> str:
        return v.strip().lower()


class ArtisanCreate(ArtisanBase):
    firebase_uid: str = Field(..., min_length=1, max_length=128, description="Firebase Auth UID from Phone OTP")


class ArtisanUpdate(BaseModel):
    """Partial update — all fields optional."""

    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    phone: Optional[str] = Field(default=None, pattern=r"^\+?[0-9]{10,15}$")
    language_preference: Optional[str] = Field(default=None, min_length=2, max_length=10)
    location: Optional[str] = Field(default=None, max_length=200)
    craft_type: Optional[str] = Field(default=None, max_length=100)

    @field_validator("name")
    @classmethod
    def _strip_name_opt(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("name must not be empty")
        return v


class ArtisanResponse(ArtisanBase):
    id: str = Field(..., description="Supabase UUID primary key")
    firebase_uid: str = Field(..., description="Firebase UID")
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
