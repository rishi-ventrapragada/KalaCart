"""
Voice Commerce Engine API — Multilingual Intent Parsing & Audio Transcription Services.

POST /api/v1/voice/intent
- Parses voice transcripts in English, Hindi, Telugu, Tamil, Kannada
- Supports intent types:
  - SEARCH_PRODUCT (query, category, max_price, min_price, location, gi_certified)
  - CREATE_PRODUCT (title, category, materials, price, quantity, size)
  - CREATE_RFQ (title, category, quantity, budget, delivery_days)
  - NAVIGATE (destination: orders, messages, inventory, storefront, analytics, help)
  - READ_ALOUD (target_text, language)
"""

import logging
import re
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.core.security import get_optional_current_user
from app.database.connection import get_supabase_client

logger = logging.getLogger(__name__)

router = APIRouter()

ALLOWED_LANGUAGES = ["en", "hi", "te", "ta", "kn"]

CATEGORY_SYNONYMS = {
    "pottery": ["pottery", "pot", "vase", "ceramic", "mitti", "bartan", "clay", "matka", "కుండ", "மண்பாண்டங்கள்", "ಕುಂಬಾರಿಕೆ"],
    "textiles": ["textile", "fabric", "cotton", "silk", "saree", "dupatta", "shawl", "cloth", "weaving", "handloom", "khadi", "వస్త్రాలు", "ஜவுளி", "ವಸ್ತ್ರ"],
    "woodwork": ["wood", "wooden", "furniture", "teak", "carving", "woodwork", "lakdi", "చెక్క", "மரவேலை", "ಮರದ ಕೆಲಸ"],
    "metalwork": ["metal", "brass", "bronze", "copper", "iron", "dhokra", "peetal", "తామ్రం", "உலோக வேலை", "ಲೋಹದ ಕೆಲಸ"],
    "jewelry": ["jewelry", "jewellery", "earrings", "necklace", "bangles", "beads", "terracotta jewelry", "ఆభరణాలు", "நகைகள்", "ಆಭರಣ"],
    "painting": ["painting", "madhubani", "pattachitra", "kalamkari", "canvas", "art", "చిత్రం", "ஓவியம்", "ಚಿತ್ರಕಲೆ"],
    "basketry": ["basket", "bamboo", "cane", "jute", "wicker", "బుట్ట", "கூடை", "ಬುಟ್ಟಿ"],
    "leather": ["leather", "mojari", "jutti", "chappal", "wallet", "తోలు", "தோல்", "ಚರ್ಮ"],
}


class VoiceIntentRequest(BaseModel):
    transcript: str = Field(..., min_length=1, max_length=1500, description="Voice transcript string")
    language: Optional[str] = Field(default="en", description="Language code en|hi|te|ta|kn")
    source_type: Optional[str] = Field(default="SEARCH", description="SEARCH | CATALOG | RFQ | NAV | CHAT")


class VoiceIntentResponse(BaseModel):
    success: bool = True
    detected_language: str
    intent_name: str
    confidence: float
    slots: Dict[str, Any]
    summary_text: str


def _detect_language(transcript: str, hint_lang: Optional[str]) -> str:
    if hint_lang and hint_lang.lower() in ALLOWED_LANGUAGES and hint_lang.lower() != "en":
        return hint_lang.lower()

    # Unicode range checks
    has_devanagari = bool(re.search(r"[\u0900-\u097F]", transcript))
    has_telugu = bool(re.search(r"[\u0C00-\u0C7F]", transcript))
    has_tamil = bool(re.search(r"[\u0B80-\u0BFF]", transcript))
    has_kannada = bool(re.search(r"[\u0C80-\u0CFF]", transcript))

    if has_telugu:
        return "te"
    if has_tamil:
        return "ta"
    if has_kannada:
        return "kn"
    if has_devanagari:
        return "hi"
    return "en"


def _extract_category(text: str) -> Optional[str]:
    text_lower = text.lower()
    for cat_name, synonyms in CATEGORY_SYNONYMS.items():
        for syn in synonyms:
            if syn in text_lower:
                return cat_name.title()
    return None


def _extract_price(text: str) -> Optional[float]:
    # Match phrases like "under 1000", "below 850", "₹ 500", "price 850", "keemat 1200", "500 rupaye"
    patterns = [
        r"(?:under|below|less than|within|keemat|price|cost|rupees|rupaye|rs\.?|₹|\/)\s*(\d+(?:,\d+)*(?:\.\d+)?)",
        r"(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:rupees|rupaye|rs|inr|rupess)",
        r"(?:రూపాయలు|ரூபாய்|ರೂಪಾಯಿ)\s*(\d+)",
        r"(\d+)\s*(?:రూపాయలు|ரூபாய்|ರೂಪಾಯಿ)"
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            num_str = match.group(1).replace(",", "")
            try:
                return float(num_str)
            except ValueError:
                pass
    return None


def _extract_quantity(text: str) -> Optional[int]:
    # Match "quantity 20", "20 units", "50 pieces", "20 pieces", "20 count"
    patterns = [
        r"(?:quantity|qty|units|pieces|count|nos|pcs|nag)\s*(\d+)",
        r"(\d+)\s*(?:units|pieces|pcs|items|boxes|baskets|pots|sarees)"
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                pass
    return None


def _parse_voice_intent(transcript: str, language: str, source_type: str) -> tuple[str, float, Dict[str, Any], str]:
    t_lower = transcript.lower()
    slots: Dict[str, Any] = {}

    # 1. Navigation Intent
    nav_keywords = ["open", "go to", "show my", "navigate", "kholey", "theeyi", "thira"]
    if any(k in t_lower for k in nav_keywords) and not any(k in t_lower for k in ["product", "basket", "pot", "saree", "under"]):
        if "order" in t_lower or "ordar" in t_lower:
            return "NAVIGATE", 0.95, {"destination": "orders"}, "Navigating to Orders"
        if "message" in t_lower or "chat" in t_lower:
            return "NAVIGATE", 0.95, {"destination": "messages"}, "Navigating to Messages"
        if "inventory" in t_lower or "stock" in t_lower:
            return "NAVIGATE", 0.95, {"destination": "inventory"}, "Navigating to Inventory"
        if "analytics" in t_lower or "sales" in t_lower:
            return "NAVIGATE", 0.95, {"destination": "analytics"}, "Navigating to Business Analytics"

    # 2. Seller Product Creation Intent
    create_keywords = ["add", "create", "new product", "sell", "upload", "banana", "banao", "jodna", "cherchu"]
    is_create = any(k in t_lower for k in create_keywords) or source_type == "CATALOG"
    if is_create and not ("show" in t_lower or "find" in t_lower or "search" in t_lower):
        category = _extract_category(transcript) or "Other"
        price = _extract_price(transcript) or 0.0
        quantity = _extract_quantity(transcript) or 10

        # Extract material
        materials = []
        for m in ["bamboo", "cotton", "silk", "terracotta", "clay", "brass", "wood", "jute", "leather", "wool"]:
            if m in t_lower:
                materials.append(m.title())
        if not materials and "material" in t_lower:
            m_match = re.search(r"material(?: is|:)?\s*([a-zA-Z]+)", transcript, re.IGNORECASE)
            if m_match:
                materials.append(m_match.group(1).title())

        # Clean title
        title = transcript
        for p in ["add a", "add", "create a", "create", "sell a", "sell", "material is", "price", "quantity"]:
            title = re.sub(re.escape(p), "", title, flags=re.IGNORECASE)
        title = title.strip().title()
        if len(title) > 60:
            title = f"{materials[0] if materials else ''} {category}".strip()

        slots = {
            "title": title if len(title) >= 3 else f"Handcrafted {category}",
            "category": category,
            "materials": materials if materials else ["Natural Organic"],
            "price": price if price > 0 else 850.0,
            "quantity": quantity,
            "size": "Medium"
        }
        return "CREATE_PRODUCT", 0.92, slots, f"Product form populated for {slots['title']}"

    # 3. Buyer RFQ Intent
    rfq_keywords = ["need quote", "bulk order", "rfq", "requirement", "need quotation", "50 pieces", "100 units", "wholesale"]
    if any(k in t_lower for k in rfq_keywords) or source_type == "RFQ":
        category = _extract_category(transcript) or "Handicrafts"
        quantity = _extract_quantity(transcript) or 50
        budget = _extract_price(transcript) or 5000.0

        slots = {
            "title": f"Bulk Requirement for {category}",
            "category": category,
            "quantity": quantity,
            "target_budget": budget,
            "delivery_days": 14
        }
        return "CREATE_RFQ", 0.90, slots, f"RFQ Created: {quantity} units of {category} (Budget: ₹{budget:,.0f})"

    # 4. Buyer Product Search Intent (Default)
    category = _extract_category(transcript)
    max_price = _extract_price(transcript)
    is_nearby = "nearby" in t_lower or "near me" in t_lower or "paas" in t_lower or "daggara" in t_lower
    is_gi = "gi" in t_lower or "certified" in t_lower or "authentic" in t_lower or "traditional" in t_lower

    query = transcript
    for rem in ["show", "find", "search", "i need", "looking for", "dikhao", "chupinchu", "under", "below", "nearby"]:
        query = re.sub(re.escape(rem), "", query, flags=re.IGNORECASE)
    query = query.strip()

    slots = {
        "query": query if query else (category or "Handicrafts"),
        "category": category,
        "max_price": max_price,
        "nearby_only": is_nearby,
        "gi_certified_only": is_gi
    }
    summary = f"Searching for '{slots['query']}'"
    if max_price:
        summary += f" under ₹{max_price:,.0f}"
    if is_nearby:
        summary += " nearby"

    return "SEARCH_PRODUCT", 0.94, slots, summary


@router.post(
    "/intent",
    response_model=VoiceIntentResponse,
    status_code=status.HTTP_200_OK,
    summary="Parse multilingual voice commands into structured commerce actions",
)
async def parse_voice_intent(
    payload: VoiceIntentRequest,
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_current_user),
):
    """
    POST /api/v1/voice/intent
    Extracts structured marketplace intents from raw speech transcripts across 5 languages.
    Logs event into voice_transcripts table asynchronously.
    """
    detected_lang = _detect_language(payload.transcript, payload.language)
    intent_name, confidence, slots, summary = _parse_voice_intent(
        payload.transcript, detected_lang, payload.source_type or "SEARCH"
    )

    # Persist audit record in Supabase
    try:
        client = get_supabase_client()
        user_id = current_user.get("uid") if current_user else None
        client.table("voice_transcripts").insert({
            "user_id": user_id,
            "source_type": payload.source_type or "SEARCH",
            "raw_transcript": payload.transcript,
            "detected_language": detected_lang,
            "intent_name": intent_name,
            "extracted_slots": slots
        }).execute()
    except Exception as exc:
        logger.warning("Could not persist voice transcript to Supabase: %s", exc)

    return VoiceIntentResponse(
        success=True,
        detected_language=detected_lang,
        intent_name=intent_name,
        confidence=confidence,
        slots=slots,
        summary_text=summary
    )
