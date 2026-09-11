"""Pydantic schemas for User model — with email authentication support."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserBase(BaseModel):
    name: str = Field(
        ..., min_length=1, max_length=100, description="User display name", examples=["Ramesh Kumar"]
    )
    email: str = Field(
        ..., min_length=5, max_length=255, description="User email address", examples=["artisan@kalacart.in"]
    )
    photo_url: Optional[str] = Field(default=None, description="User profile photo URL")

    @field_validator("name")
    @classmethod
    def _strip_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("name must not be empty")
        return v

    @field_validator("email")
    @classmethod
    def _normalize_email(cls, v: str) -> str:
        v = v.strip().lower()
        if not v or "@" not in v:
            raise ValueError("invalid email format")
        return v


class UserCreate(UserBase):
    uid: str = Field(..., min_length=1, max_length=128, description="Firebase Auth UID")


class UserSyncRequest(BaseModel):
    uid: str = Field(..., min_length=1, max_length=128, description="Firebase Auth UID")
    name: str = Field(..., min_length=1, max_length=100, description="User display name")
    email: str = Field(..., min_length=5, max_length=255, description="User email address")
    photo_url: Optional[str] = Field(default=None, description="Profile photo URL")


class UserResponse(UserBase):
    id: Optional[str] = Field(default=None, description="Internal UUID")
    uid: str = Field(..., description="Firebase UID")
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True
