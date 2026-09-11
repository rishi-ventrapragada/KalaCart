"""
Pydantic models for KalaCart Automatic Mini Storefront Website & Theme Generator.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class StorefrontBase(BaseModel):
    store_name: str = Field(..., min_length=2, max_length=255, description="Artisan store / business name")
    tagline: Optional[str] = Field(None, max_length=255, description="Short brand tagline")
    description: Optional[str] = Field(None, description="Detailed craft story and artisan heritage description")
    banner_url: Optional[str] = Field(None, description="Hero storefront banner image URL")
    logo_url: Optional[str] = Field(None, description="Artisan or shop logo image URL")
    theme_color: str = Field(default="#8D2741", description="Primary brand accent hex color")
    theme_template: str = Field(default="heritage", description="Storefront design template (heritage, modern, classic)")
    whatsapp_number: Optional[str] = Field(None, description="WhatsApp contact phone with country code")
    instagram_handle: Optional[str] = Field(None, description="Instagram username without @")
    facebook_url: Optional[str] = Field(None, description="Facebook page URL")
    youtube_url: Optional[str] = Field(None, description="YouTube channel URL")
    website_url: Optional[str] = Field(None, description="External portfolio / website URL")
    is_published: bool = Field(default=True, description="Whether storefront is publicly accessible")


class StorefrontCreate(StorefrontBase):
    seller_id: str = Field(..., description="Firebase UID or seller profile ID")
    slug: Optional[str] = Field(None, description="Custom or auto-generated URL slug")


class StorefrontUpdate(BaseModel):
    store_name: Optional[str] = None
    tagline: Optional[str] = None
    description: Optional[str] = None
    banner_url: Optional[str] = None
    logo_url: Optional[str] = None
    theme_color: Optional[str] = None
    theme_template: Optional[str] = None
    whatsapp_number: Optional[str] = None
    instagram_handle: Optional[str] = None
    facebook_url: Optional[str] = None
    youtube_url: Optional[str] = None
    website_url: Optional[str] = None
    is_published: Optional[bool] = None


class StoreTheme(BaseModel):
    theme_key: str
    name: str
    description: str
    primary_color: str
    secondary_color: str
    font_family: str
    layout_style: str
    is_active: bool = True


class StoreSeoMetadata(BaseModel):
    meta_title: str
    meta_description: str
    og_image_url: str
    canonical_url: str
    structured_schema: Dict[str, Any]


class StorefrontResponse(StorefrontBase):
    id: str
    seller_id: str
    slug: str
    qr_code_url: Optional[str] = None
    store_url: str
    seo: Optional[StoreSeoMetadata] = None
    view_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class PublicStorefrontView(BaseModel):
    storefront: StorefrontResponse
    seller: Dict[str, Any]
    products: List[Dict[str, Any]]
    featured_products: List[Dict[str, Any]]
    ratings: Dict[str, Any]
    followers: Dict[str, Any]
    seo: StoreSeoMetadata
    theme: Dict[str, Any]
