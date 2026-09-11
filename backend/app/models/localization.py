from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class SupportedLanguage(BaseModel):
    code: str
    name: str
    native_name: str
    direction: str = "ltr"  # ltr or rtl
    flag_emoji: str
    is_indian: bool = False


class TranslateTextRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Source text to translate")
    target_lang: str = Field(..., description="Target ISO 639-1 code (en, hi, te, ta, kn, fr, de, es, ja, ar, zh)")
    source_lang: str = Field(default="auto", description="Source ISO code or auto")
    domain: str = Field(default="general", description="general, product, chat, voice, storefront, invoice")


class TranslateTextResponse(BaseModel):
    original_text: str
    translated_text: str
    source_lang: str
    target_lang: str
    cached: bool = False
    confidence_score: float = 0.98


class ProductTranslateRequest(BaseModel):
    product_id: Optional[str] = None
    title: str
    description: str
    materials: List[str] = []
    techniques: List[str] = []
    care_instructions: Optional[str] = None
    target_lang: str


class ProductTranslateResponse(BaseModel):
    product_id: Optional[str] = None
    target_lang: str
    translated_title: str
    translated_description: str
    translated_materials: List[str] = []
    translated_techniques: List[str] = []
    translated_care_instructions: Optional[str] = None
    cached: bool = False


class StorefrontTranslateRequest(BaseModel):
    store_name: str
    tagline: str
    bio: str
    announcement: Optional[str] = None
    heritage_story: Optional[str] = None
    target_lang: str


class StorefrontTranslateResponse(BaseModel):
    target_lang: str
    translated_store_name: str
    translated_tagline: str
    translated_bio: str
    translated_announcement: Optional[str] = None
    translated_heritage_story: Optional[str] = None


class InvoiceTranslateRequest(BaseModel):
    invoice_number: str
    items: List[Dict[str, Any]]
    terms_and_conditions: str
    target_lang: str
    target_currency: Optional[str] = "USD"


class InvoiceTranslateResponse(BaseModel):
    invoice_number: str
    target_lang: str
    target_currency: str
    translated_items: List[Dict[str, Any]]
    translated_terms_and_conditions: str
    localized_tax_disclaimer: str


class ChatTranslateRequest(BaseModel):
    conversation_id: str
    sender_id: str
    sender_role: str = Field(default="buyer", description="buyer or seller")
    message_text: str
    sender_lang: str = Field(default="auto", description="auto, fr, ja, te, hi, etc.")
    recipient_lang: str = Field(..., description="target language of the recipient")


class ChatTranslateResponse(BaseModel):
    conversation_id: str
    sender_id: str
    sender_role: str
    original_text: str
    detected_source_lang: str
    recipient_lang: str
    translated_text: str
    all_translations: Dict[str, str] = {}
    timestamp: str


class VoiceTranslateRequest(BaseModel):
    audio_text_or_transcript: str
    source_lang: str = "auto"
    target_languages: List[str] = ["en", "hi", "fr", "ja", "ar", "te"]


class VoiceTranslateResponse(BaseModel):
    transcription: str
    detected_source_lang: str
    translations: Dict[str, str]


class CurrencyConvertRequest(BaseModel):
    amount: float
    from_currency: str = "INR"
    to_currency: str = "USD"


class CurrencyConvertResponse(BaseModel):
    original_amount: float
    from_currency: str
    to_currency: str
    exchange_rate: float
    converted_amount: float
    formatted_string: str


class MeasurementConvertRequest(BaseModel):
    value: float
    from_unit: str  # cm, inches, meters, yards, kg, lbs, g, oz
    to_unit: str


class MeasurementConvertResponse(BaseModel):
    original_value: float
    from_unit: str
    to_unit: str
    converted_value: float
    formatted_string: str
