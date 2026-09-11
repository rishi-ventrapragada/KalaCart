"""
AI Marketing Studio Engine (Phase 4).
Generates multi-format posters, QR code assets, and multilingual copywriting with hashtags.
"""

import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from app.models.marketing_studio import (
    CampaignScheduleType,
    CopywritingRequest,
    CopywritingResponse,
    GeneratePosterRequest,
    GeneratePosterResponse,
    MarketingCampaignCreate,
    MarketingCampaignResponse,
    PosterFormat,
    PosterTheme,
)

logger = logging.getLogger(__name__)


def generate_multilingual_copywriting(req: CopywritingRequest) -> CopywritingResponse:
    """
    Generates high-converting captions, hashtags, and CTAs tailored for Indian crafts and festivals.
    """
    fest_prefix = f"Celebrate {req.festival} with " if req.festival else "Experience "
    lang = req.language.lower()

    if lang in ["hi", "hindi"]:
        headline = f"✨ {req.product_title} — शुद्ध हस्तकला की अनूठी पहचान"
        caption = (
            f"पारंपरिक भारतीय शिल्पकला का अद्वितीय नमूना! {req.store_name} द्वारा तैयार "
            f"यह {req.product_title} आपके घर को प्रामाणिक शिल्प सौंदर्य से भर देगा। "
            f"100% जीआई प्रमाणित कारीगरों द्वारा हस्तनिर्मित और सुरक्षित एस्क्रो सुरक्षा के साथ।"
        )
        cta = "👉 अभी ऑर्डर करें | सीमित हस्तनिर्मित संग्रह"
        hashtags = ["#हस्तशिल्प", "#भारतीयकारीगर", "#KalaCart", "#HandmadeInIndia", "#GICertified", "#VocalForLocal"]
    elif lang in ["te", "telugu"]:
        headline = f"✨ {req.product_title} — సంప్రదాయ చేతివృత్తుల అందం"
        caption = (
            f"{req.store_name} వారి ప్రామాణిక చేనేత మరియు హస్తకళల కళారూపం {req.product_title}. "
            f"ప్రత్యక్ష కళాకారుల నుండి 100% ఎస్క్రో భద్రతతో పొందండి."
        )
        cta = "👉 ఇప్పుడే ఆర్డర్ చేయండి"
        hashtags = ["#హస్తకళలు", "#చేనేత", "#KalaCart", "#IndianArtisans", "#VocalForLocal"]
    else:
        # Default English
        if req.theme == PosterTheme.LUXURY:
            headline = f"Heritage Luxury: {req.product_title}"
            caption = (
                f"{fest_prefix}the timeless artistry of {req.product_title}, masterfully handcrafted by {req.artisan_name} at {req.store_name}. "
                f"Every piece is authenticated with Geographical Indication (GI) certification, preserving 500 years of artisanal tradition. "
                f"Protected by KalaCart's 100% Escrow Vault."
            )
            cta = "Shop Authentic GI Heritage ➔"
            hashtags = ["#HeritageCrafts", "#LuxuryHandmade", "#JaipurPottery", "#GICertified", "#KalaCart", "#ArtisanMade"]
        elif req.theme == PosterTheme.MINIMAL:
            headline = f"Pure Form. Authentic Craft: {req.product_title}"
            caption = (
                f"Direct from the workshop of {req.artisan_name}. "
                f"Pure, sustainable, and handmade with natural minerals and age-old techniques. "
                f"Fair trade certified on KalaCart."
            )
            cta = "Discover Collection ➔"
            hashtags = ["#MinimalLiving", "#SustainableCraft", "#Handmade", "#ArtisanDirect", "#KalaCart"]
        else:
            headline = f"✨ {fest_prefix}Authentic Handcrafted {req.product_title}"
            caption = (
                f"Transform your space with authentic {req.craft_category} crafted by master artisan {req.artisan_name} ({req.store_name}). "
                f"100% GI-Tagged, insured fragile logistics, and direct artisan pricing."
            )
            cta = "Order Direct from Artisan ➔"
            hashtags = ["#HandcraftedIndia", "#VocalForLocal", "#KalaCart", "#SupportArtisans", "#IncredibleIndiaCrafts"]

    return CopywritingResponse(
        headline=headline,
        caption=caption,
        hashtags=hashtags,
        call_to_action=cta,
        language=req.language,
        tone=req.theme.value.lower(),
    )


def synthesize_marketing_poster(req: GeneratePosterRequest) -> GeneratePosterResponse:
    """
    Generates layout metadata, dimensions, QR code asset links, and copywriting for posters.
    """
    poster_id = f"post_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc)
    store_slug = req.store_slug or "rajesh-pottery"
    store_deep_link = f"https://kalacart.shop/store/{store_slug}"

    # Formatted high-res QR code link
    qr_code_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={store_deep_link}"

    # Dimensions by format
    dim_map = {
        PosterFormat.INSTAGRAM_POST: ("1:1", "1080x1080 px"),
        PosterFormat.WHATSAPP_BANNER: ("16:9", "1280x720 px"),
        PosterFormat.FESTIVAL_POSTER: ("4:5", "1080x1350 px"),
        PosterFormat.PRODUCT_FLYER: ("3:4", "1200x1600 px"),
        PosterFormat.STORY_IMAGE: ("9:16", "1080x1920 px"),
        PosterFormat.QR_POSTER: ("1:1.414", "1200x1700 px (A4 Printable)"),
    }
    aspect, dims = dim_map.get(req.format_type, ("1:1", "1080x1080 px"))

    copy_req = CopywritingRequest(
        product_title=req.product_title,
        craft_category="Handicrafts",
        artisan_name="Master Artisan",
        store_name=req.store_name,
        format_type=req.format_type,
        theme=req.theme,
        festival=req.festival,
        language=req.language,
    )
    copy_res = generate_multilingual_copywriting(copy_req)
    if req.custom_headline:
        copy_res.headline = req.custom_headline
    if req.custom_cta:
        copy_res.call_to_action = req.custom_cta

    # High quality rendered template backdrop
    poster_image_url = req.product_image_url or "https://images.unsplash.com/photo-1578749556568-bc2c40e68b61?w=1080"

    return GeneratePosterResponse(
        poster_id=poster_id,
        poster_image_url=poster_image_url,
        qr_code_url=qr_code_url,
        store_deep_link=store_deep_link,
        format_type=req.format_type,
        theme=req.theme,
        aspect_ratio=aspect,
        dimensions_px=dims,
        copywriting=copy_res,
        created_at=now,
    )
