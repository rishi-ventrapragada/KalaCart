from typing import List
from fastapi import APIRouter, HTTPException, Query, status

from app.models.localization import (
    SupportedLanguage,
    TranslateTextRequest,
    TranslateTextResponse,
    ProductTranslateRequest,
    ProductTranslateResponse,
    StorefrontTranslateRequest,
    StorefrontTranslateResponse,
    InvoiceTranslateRequest,
    InvoiceTranslateResponse,
    ChatTranslateRequest,
    ChatTranslateResponse,
    VoiceTranslateRequest,
    VoiceTranslateResponse,
    CurrencyConvertRequest,
    CurrencyConvertResponse,
    MeasurementConvertRequest,
    MeasurementConvertResponse,
)
from app.services.translation_service import translation_service, SUPPORTED_LANGUAGES, EXCHANGE_RATES

router = APIRouter(prefix="/api/v1/localization", tags=["Global Translation & Localization"])


@router.get("/languages", response_model=List[SupportedLanguage])
def list_supported_languages():
    """List all 11 supported Indian and global languages."""
    return SUPPORTED_LANGUAGES


@router.post("/translate", response_model=TranslateTextResponse)
def translate_text(payload: TranslateTextRequest):
    """Translate arbitrary text into any of the 11 supported languages with caching."""
    return translation_service.translate_text(payload)


@router.post("/translate/product", response_model=ProductTranslateResponse)
def translate_product(payload: ProductTranslateRequest):
    """Translate all fields of a craft product listing preserving authentic GI terminology."""
    return translation_service.translate_product(payload)


@router.post("/translate/storefront", response_model=StorefrontTranslateResponse)
def translate_storefront(payload: StorefrontTranslateRequest):
    """Translate artisan digital storefront profile, bio, announcements, and story."""
    return translation_service.translate_storefront(payload)


@router.post("/translate/invoice", response_model=InvoiceTranslateResponse)
def translate_invoice(payload: InvoiceTranslateRequest):
    """Generate localized commercial export invoice with converted currency and tax notes."""
    return translation_service.translate_invoice(payload)


@router.post("/translate/chat", response_model=ChatTranslateResponse)
def translate_chat_message(payload: ChatTranslateRequest):
    """Real-time bidirectional buyer-seller conversation translation."""
    return translation_service.translate_chat(payload)


@router.post("/translate/voice", response_model=VoiceTranslateResponse)
def translate_voice(payload: VoiceTranslateRequest):
    """Speech transcript translation into multiple target languages."""
    return translation_service.translate_voice(payload)


@router.get("/currency/rates")
def get_exchange_rates():
    """Get live currency exchange rates against base INR."""
    return {"base_currency": "INR", "rates": EXCHANGE_RATES}


@router.post("/currency/convert", response_model=CurrencyConvertResponse)
def convert_currency(payload: CurrencyConvertRequest):
    """Convert amount between world currencies."""
    return translation_service.convert_currency(payload)


@router.post("/measurements/convert", response_model=MeasurementConvertResponse)
def convert_measurement(payload: MeasurementConvertRequest):
    """Convert dimensions, length, weight, and area between Metric & Imperial units."""
    return translation_service.convert_measurement(payload)
