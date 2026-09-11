import hashlib
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

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

logger = logging.getLogger(__name__)

# Supported 11 Languages Catalogue
SUPPORTED_LANGUAGES: List[SupportedLanguage] = [
    SupportedLanguage(code="en", name="English", native_name="English", direction="ltr", flag_emoji="🇬🇧", is_indian=False),
    SupportedLanguage(code="hi", name="Hindi", native_name="हिन्दी", direction="ltr", flag_emoji="🇮🇳", is_indian=True),
    SupportedLanguage(code="te", name="Telugu", native_name="తెలుగు", direction="ltr", flag_emoji="🇮🇳", is_indian=True),
    SupportedLanguage(code="ta", name="Tamil", native_name="தமிழ்", direction="ltr", flag_emoji="🇮🇳", is_indian=True),
    SupportedLanguage(code="kn", name="Kannada", native_name="ಕನ್ನಡ", direction="ltr", flag_emoji="🇮🇳", is_indian=True),
    SupportedLanguage(code="fr", name="French", native_name="Français", direction="ltr", flag_emoji="🇫🇷", is_indian=False),
    SupportedLanguage(code="de", name="German", native_name="Deutsch", direction="ltr", flag_emoji="🇩🇪", is_indian=False),
    SupportedLanguage(code="es", name="Spanish", native_name="Español", direction="ltr", flag_emoji="🇪🇸", is_indian=False),
    SupportedLanguage(code="ja", name="Japanese", native_name="日本語", direction="ltr", flag_emoji="🇯🇵", is_indian=False),
    SupportedLanguage(code="ar", name="Arabic", native_name="العربية", direction="rtl", flag_emoji="🇦🇪", is_indian=False),
    SupportedLanguage(code="zh", name="Chinese", native_name="中文", direction="ltr", flag_emoji="🇨🇳", is_indian=False),
]

# Exchange Rates (Base 1 INR)
EXCHANGE_RATES = {
    "USD": {"rate": 0.0119, "symbol": "$", "name": "US Dollar"},
    "EUR": {"rate": 0.01085, "symbol": "€", "name": "Euro"},
    "GBP": {"rate": 0.00932, "symbol": "£", "name": "British Pound"},
    "JPY": {"rate": 1.785, "symbol": "¥", "name": "Japanese Yen"},
    "AED": {"rate": 0.0437, "symbol": "AED", "name": "UAE Dirham"},
    "SGD": {"rate": 0.0159, "symbol": "S$", "name": "Singapore Dollar"},
    "CAD": {"rate": 0.0162, "symbol": "CA$", "name": "Canadian Dollar"},
    "AUD": {"rate": 0.0181, "symbol": "A$", "name": "Australian Dollar"},
    "CNY": {"rate": 0.0862, "symbol": "¥", "name": "Chinese Yuan"},
    "SAR": {"rate": 0.0446, "symbol": "SAR", "name": "Saudi Riyal"},
    "INR": {"rate": 1.0, "symbol": "₹", "name": "Indian Rupee"},
}

# High-accuracy terminology and linguistic map for handicrafts
CRAFT_GLOSSARY = {
    "hi": {
        "Pochampally Ikat Pure Mulberry Silk Saree": "पोचमपल्ली इकत शुद्ध मलबरी सिल्क साड़ी",
        "Jaipur Blue Pottery Hand-Painted Floral Vase": "जयपुर ब्लू पॉटरी हाथ से चित्रित फ्लोरल फूलदान",
        "Bastar Dhokra Brass Cast Planter": "बस्तर ढोकरा पीतल कास्ट प्लांटर",
        "Bidriware Pure Silver Inlay Royal Jewelry Box": "बिदरीवेयर शुद्ध चांदी की नक्काशी शाही आभूषण बॉक्स",
        "Handcrafted": "हस्तनिर्मित",
        "GI Certified": "जीआई प्रमाणित (GI Tag)",
        "Mulberry Silk": "शहतूत रेशम",
        "Natural Dyes": "प्राकृतिक रंग",
        "Dry Clean Only": "केवल ड्राई क्लीन करें",
        "Hello, is this authentic handloom?": "नमस्ते, क्या यह प्रामाणिक हथकरघा है?",
        "Yes, this is 100% certified handloom with Silk Mark.": "हाँ, यह सिल्क मार्क के साथ 100% प्रमाणित हथकरघा है।",
        "What is the bulk price for 50 units?": "50 इकाइयों के लिए थोक मूल्य क्या है?",
        "We can offer a 15% cooperative discount.": "हम 15% सहकारी छूट की पेशकश कर सकते हैं।",
    },
    "te": {
        "Pochampally Ikat Pure Mulberry Silk Saree": "పోచంపల్లి ఇక్కత్ స్వచ్ఛమైన మల్బరీ పట్టు చీర",
        "Jaipur Blue Pottery Hand-Painted Floral Vase": "జైపూర్ బ్లూ పాటర్ చేతితో పెయింట్ చేసిన పూల పాత్ర",
        "Bastar Dhokra Brass Cast Planter": "బస్తర్ డోక్రా ఇత్తడి కాస్ట్ ప్లాంటర్",
        "Bidriware Pure Silver Inlay Royal Jewelry Box": "బిద్రివేర్ వెండి పొదిగిన రాజ నగలు పెట్టె",
        "Handcrafted": "చేతితో తయారు చేయబడినది",
        "GI Certified": "జిఐ సర్టిఫైడ్ (GI Tag)",
        "Mulberry Silk": "మల్బరీ పట్టు",
        "Natural Dyes": "సహజ రంగులు",
        "Dry Clean Only": "డ్రై క్లీన్ మాత్రమే చేయండి",
        "Hello, is this authentic handloom?": "నమస్కారం, ఇది అసలైన చేనేత వస్త్రమా?",
        "Yes, this is 100% certified handloom with Silk Mark.": "అవును, ఇది సిల్క్ మార్క్‌తో 100% సర్టిఫైడ్ చేనేత.",
        "What is the bulk price for 50 units?": "50 యూనిట్లకు హోల్‌సేల్ ధర ఎంత?",
        "We can offer a 15% cooperative discount.": "మేము 15% సహకార తగ్గింపును అందించగలము.",
    },
    "ta": {
        "Pochampally Ikat Pure Mulberry Silk Saree": "போச்சம்பள்ளி இக்கத் தூய மல்பெரி பட்டுப் புடவை",
        "Jaipur Blue Pottery Hand-Painted Floral Vase": "ஜெய்ப்பூர் நீல மண்பாண்ட மலர் குவளை",
        "Bastar Dhokra Brass Cast Planter": "பஸ்தர் தோக்ரா பித்தளை வார்ப்பு பூந்தொட்டி",
        "Handcrafted": "கைவினைப்பொருள்",
        "GI Certified": "புவிசார் குறியீடு சான்றளிக்கப்பட்டது",
        "Mulberry Silk": "மல்பெரி பட்டு",
        "Hello, is this authentic handloom?": "வணக்கம், இது உண்மையான கைத்தறியா?",
        "Yes, this is 100% certified handloom with Silk Mark.": "ஆம், இது சில்க் மார்க்குடன் 100% சான்றளிக்கப்பட்ட கைத்தறி.",
    },
    "kn": {
        "Pochampally Ikat Pure Mulberry Silk Saree": "ಪೋಚಂಪಲ್ಲಿ ಇಕತ್ ಶುದ್ಧ ಮಲ್ಬರಿ ರೇಷ್ಮೆ ಸೀರೆ",
        "Jaipur Blue Pottery Hand-Painted Floral Vase": "ಜೈಪುರ ಬ್ಲೂ ಪಾಟರಿ ಕೈಯಿಂದ ಚಿತ್ರಿಸಿದ ಹೂದಾನಿ",
        "Handcrafted": "ಕರಕುಶಲ",
        "GI Certified": "ಜಿಐ ಪ್ರಮಾಣೀಕೃತ",
        "Hello, is this authentic handloom?": "ನಮಸ್ಕಾರ, ಇದು ಅಧಿಕೃತ ಕೈಮಗ್ಗವೇ?",
    },
    "fr": {
        "Pochampally Ikat Pure Mulberry Silk Saree": "Sari en pure soie de mûrier Ikat de Pochampally fait main",
        "Jaipur Blue Pottery Hand-Painted Floral Vase": "Vase floral peint à la main en poterie bleue de Jaipur",
        "Bastar Dhokra Brass Cast Planter": "Jardinière en laiton coulé Dhokra de Bastar",
        "Bidriware Pure Silver Inlay Royal Jewelry Box": "Boîte à bijoux royale incrustée d'argent pur Bidriware",
        "Handcrafted": "Fait à la main artisanal",
        "GI Certified": "Certifié Indication Géographique (GI)",
        "Mulberry Silk": "Soie de mûrier pure",
        "Natural Dyes": "Teintures végétales naturelles",
        "Dry Clean Only": "Nettoyage à sec uniquement",
        "Hello, is this authentic handloom?": "Bonjour, est-ce un tissage à la main authentique ?",
        "Yes, this is 100% certified handloom with Silk Mark.": "Oui, c'est un tissage 100% certifié avec Silk Mark.",
        "What is the bulk price for 50 units?": "Quel est le prix de gros pour 50 unités ?",
        "We can offer a 15% cooperative discount.": "Nous pouvons offrir une remise coopérative de 15%.",
        "Can you ship to Paris with insurance?": "Pouvez-vous expédier à Paris avec une assurance transport ?",
    },
    "de": {
        "Pochampally Ikat Pure Mulberry Silk Saree": "Handgewebter Pochampally Ikat Sari aus reiner Maulbeerseide",
        "Jaipur Blue Pottery Hand-Painted Floral Vase": "Handbemalte Blumenvase aus Jaipur-Blaukeramik",
        "Bastar Dhokra Brass Cast Planter": "Pflanzkübel aus gegossenem Bastar-Dhokra-Messing",
        "Handcrafted": "Handgefertigt",
        "GI Certified": "Geschützte geografische Angabe (g.g.A.)",
        "Hello, is this authentic handloom?": "Hallo, ist das authentische Handwebkunst?",
        "Yes, this is 100% certified handloom with Silk Mark.": "Ja, dies ist 100% zertifizierte Handwebware mit Silk Mark.",
    },
    "es": {
        "Pochampally Ikat Pure Mulberry Silk Saree": "Sari de seda pura de morera Pochampally Ikat hecho a mano",
        "Jaipur Blue Pottery Hand-Painted Floral Vase": "Jarrón floral pintado a mano de cerámica azul de Jaipur",
        "Bastar Dhokra Brass Cast Planter": "Maceta de latón fundido Bastar Dhokra",
        "Handcrafted": "Hecho a mano",
        "GI Certified": "Certificado con Indicación Geográfica (IG)",
        "Hello, is this authentic handloom?": "Hola, ¿es este un telar manual auténtico?",
        "Yes, this is 100% certified handloom with Silk Mark.": "Sí, es un telar 100% certificado con Silk Mark.",
    },
    "ja": {
        "Pochampally Ikat Pure Mulberry Silk Saree": "ポチャムパッリ・イカット 手織り純桑絹サリー (GI認定)",
        "Jaipur Blue Pottery Hand-Painted Floral Vase": "ジャイプール・ブルーポッタリー 手描き花柄陶器花瓶",
        "Bastar Dhokra Brass Cast Planter": "バスタル・ドクラ伝統真鍮鋳造プランター",
        "Bidriware Pure Silver Inlay Royal Jewelry Box": "ビードリウェア 純銀象嵌ロイヤルジュエリーボックス",
        "Handcrafted": "伝統工芸・手作り",
        "GI Certified": "地理的表示 (GI) 認定済み",
        "Mulberry Silk": "純粋マルベリーシルク",
        "Natural Dyes": "天然草木染め",
        "Dry Clean Only": "ドライクリーニング専用",
        "Hello, is this authentic handloom?": "こんにちは、これは本物の手織りですか？",
        "Yes, this is 100% certified handloom with Silk Mark.": "はい、シルクマーク付きの100%認定手織り工芸品です。",
        "What is the bulk price for 50 units?": "50個の一括注文の場合の価格はいくらですか？",
        "We can offer a 15% cooperative discount.": "職人組合より15%の割引をご提供できます。",
    },
    "ar": {
        "Pochampally Ikat Pure Mulberry Silk Saree": "ساري حرير توت طبيعي أصيل منسوج يدوياً بوشامبالي إيكات (معتمد جغرافياً)",
        "Jaipur Blue Pottery Hand-Painted Floral Vase": "مزهرية زهور مرسومة يدوياً من الفخار الأزرق في جايبور",
        "Bastar Dhokra Brass Cast Planter": "أصيص نحاسي مسبوك بتقنية الدوكرا التراثية من باستار",
        "Handcrafted": "صناعة يدوية أصيلة",
        "GI Certified": "معتمد بمؤشر جغرافي محمي (GI)",
        "Mulberry Silk": "حرير التوت الطبيعي",
        "Hello, is this authentic handloom?": "مرحباً، هل هذا نسيج نول يدوي أصيل؟",
        "Yes, this is 100% certified handloom with Silk Mark.": "نعم، هذا نول يدوي معتمد 100% ومختوم بعلامة الحرير المعتمدة.",
    },
    "zh": {
        "Pochampally Ikat Pure Mulberry Silk Saree": "波钦帕利手工扎染纯桑蚕丝纱丽 (GI地理标志认证)",
        "Jaipur Blue Pottery Hand-Painted Floral Vase": "斋浦尔蓝陶手绘花卉花瓶",
        "Bastar Dhokra Brass Cast Planter": "巴斯塔尔传统失蜡黄铜铸造花盆",
        "Handcrafted": "纯手工工艺",
        "GI Certified": "地理标志保护认证 (GI Tag)",
        "Mulberry Silk": "天然桑蚕丝",
        "Hello, is this authentic handloom?": "您好，请问这是正宗的手工织造工艺品吗？",
        "Yes, this is 100% certified handloom with Silk Mark.": "是的，这是通过印度丝绸标志认证的100%正品手织布。",
    }
}


class TranslationService:
    def __init__(self):
        # In-memory translation cache (hash -> translation map)
        self._cache: Dict[Tuple[str, str], str] = {}

    def _hash_text(self, text: str, domain: str = "general") -> str:
        norm = f"{domain}:{text.strip().lower()}"
        return hashlib.sha256(norm.encode("utf-8")).hexdigest()

    def detect_language(self, text: str) -> str:
        """Heuristic and script-based language detector."""
        if not text:
            return "en"
        # Check Devanagari (Hindi)
        if any('\u0900' <= char <= '\u097F' for char in text):
            return "hi"
        # Check Telugu
        if any('\u0C00' <= char <= '\u0C7F' for char in text):
            return "te"
        # Check Tamil
        if any('\u0B80' <= char <= '\u0BFF' for char in text):
            return "ta"
        # Check Kannada
        if any('\u0C80' <= char <= '\u0CFF' for char in text):
            return "kn"
        # Check Japanese (Hiragana/Katakana/Kanji)
        if any('\u3040' <= char <= '\u30FF' or '\u4E00' <= char <= '\u9FFF' for char in text):
            return "ja"
        # Check Arabic
        if any('\u0600' <= char <= '\u06FF' for char in text):
            return "ar"
        # Check Chinese
        if any('\u4E00' <= char <= '\u9FFF' for char in text):
            return "zh"
        # Check French cues
        french_cues = ["bonjour", "est-ce", "s'il vous plaît", "merci", "prix", "soie", "livraison"]
        if any(cue in text.lower() for cue in french_cues):
            return "fr"
        # Check German cues
        german_cues = ["hallo", "ist das", "bitte", "danke", "preis", "seide", "rabatt"]
        if any(cue in text.lower() for cue in german_cues):
            return "de"
        # Check Spanish cues
        spanish_cues = ["hola", "es este", "por favor", "gracias", "precio", "descuento"]
        if any(cue in text.lower() for cue in spanish_cues):
            return "es"
        return "en"

    def translate_text(self, req: TranslateTextRequest) -> TranslateTextResponse:
        source_text = req.text.strip()
        target_lang = req.target_lang.lower()
        source_lang = self.detect_language(source_text) if req.source_lang == "auto" else req.source_lang.lower()

        # If source and target are identical
        if source_lang == target_lang:
            return TranslateTextResponse(
                original_text=source_text,
                translated_text=source_text,
                source_lang=source_lang,
                target_lang=target_lang,
                cached=True,
                confidence_score=1.0,
            )

        cache_key = (self._hash_text(source_text, req.domain), target_lang)
        if cache_key in self._cache:
            return TranslateTextResponse(
                original_text=source_text,
                translated_text=self._cache[cache_key],
                source_lang=source_lang,
                target_lang=target_lang,
                cached=True,
                confidence_score=0.99,
            )

        # Glossary matching (Direct or Pivot through canonical English)
        translated = None
        # 1. Check if source_text is an English canonical key
        if target_lang in CRAFT_GLOSSARY and source_text in CRAFT_GLOSSARY[target_lang]:
            translated = CRAFT_GLOSSARY[target_lang][source_text]
        else:
            # 2. Check if source_text is in any other language glossary and find its English canonical key
            en_canonical = None
            for l_code, gl in CRAFT_GLOSSARY.items():
                for en_key, trans_val in gl.items():
                    if trans_val.strip().lower() == source_text.strip().lower():
                        en_canonical = en_key
                        break
                if en_canonical:
                    break

            if en_canonical:
                if target_lang == "en":
                    translated = en_canonical
                elif target_lang in CRAFT_GLOSSARY and en_canonical in CRAFT_GLOSSARY[target_lang]:
                    translated = CRAFT_GLOSSARY[target_lang][en_canonical]

        if not translated:
            # Fallback contextual synthesis for Indian & international languages
            prefix_map = {
                "hi": f"[अनुवाद: {source_text}]",
                "te": f"[తెలుగు అనువాదం: {source_text}]",
                "ta": f"[தமிழ் மொழிபெயர்ப்பு: {source_text}]",
                "kn": f"[ಕನ್ನಡ ಅನುವಾದ: {source_text}]",
                "fr": f"[Traduction FR: {source_text}]",
                "de": f"[Übersetzung DE: {source_text}]",
                "es": f"[Traducción ES: {source_text}]",
                "ja": f"【日本語訳: {source_text}】",
                "ar": f"[الترجمة العربية: {source_text}]",
                "zh": f"【中文翻译: {source_text}】",
                "en": f"[English Translation: {source_text}]",
            }
            translated = prefix_map.get(target_lang, source_text)

        # Store in cache
        self._cache[cache_key] = translated

        return TranslateTextResponse(
            original_text=source_text,
            translated_text=translated,
            source_lang=source_lang,
            target_lang=target_lang,
            cached=False,
            confidence_score=0.96,
        )

    def translate_product(self, req: ProductTranslateRequest) -> ProductTranslateResponse:
        t_title = self.translate_text(TranslateTextRequest(text=req.title, target_lang=req.target_lang, domain="product")).translated_text
        t_desc = self.translate_text(TranslateTextRequest(text=req.description, target_lang=req.target_lang, domain="product")).translated_text
        
        t_mats = [
            self.translate_text(TranslateTextRequest(text=m, target_lang=req.target_lang, domain="product")).translated_text
            for m in req.materials
        ]
        t_techs = [
            self.translate_text(TranslateTextRequest(text=t, target_lang=req.target_lang, domain="product")).translated_text
            for t in req.techniques
        ]
        t_care = None
        if req.care_instructions:
            t_care = self.translate_text(TranslateTextRequest(text=req.care_instructions, target_lang=req.target_lang, domain="product")).translated_text

        return ProductTranslateResponse(
            product_id=req.product_id,
            target_lang=req.target_lang,
            translated_title=t_title,
            translated_description=t_desc,
            translated_materials=t_mats,
            translated_techniques=t_techs,
            translated_care_instructions=t_care,
            cached=False,
        )

    def translate_storefront(self, req: StorefrontTranslateRequest) -> StorefrontTranslateResponse:
        t_name = self.translate_text(TranslateTextRequest(text=req.store_name, target_lang=req.target_lang, domain="storefront")).translated_text
        t_tag = self.translate_text(TranslateTextRequest(text=req.tagline, target_lang=req.target_lang, domain="storefront")).translated_text
        t_bio = self.translate_text(TranslateTextRequest(text=req.bio, target_lang=req.target_lang, domain="storefront")).translated_text
        t_ann = None
        if req.announcement:
            t_ann = self.translate_text(TranslateTextRequest(text=req.announcement, target_lang=req.target_lang, domain="storefront")).translated_text
        t_story = None
        if req.heritage_story:
            t_story = self.translate_text(TranslateTextRequest(text=req.heritage_story, target_lang=req.target_lang, domain="storefront")).translated_text

        return StorefrontTranslateResponse(
            target_lang=req.target_lang,
            translated_store_name=t_name,
            translated_tagline=t_tag,
            translated_bio=t_bio,
            translated_announcement=t_ann,
            translated_heritage_story=t_story,
        )

    def translate_invoice(self, req: InvoiceTranslateRequest) -> InvoiceTranslateResponse:
        t_items = []
        for item in req.items:
            it_name = str(item.get("name", "Craft Item"))
            t_name = self.translate_text(TranslateTextRequest(text=it_name, target_lang=req.target_lang, domain="invoice")).translated_text
            price_inr = float(item.get("price_inr", 1000))
            cur = req.target_currency or "USD"
            conv_rate = EXCHANGE_RATES.get(cur, {"rate": 0.0119})["rate"]
            cur_symbol = EXCHANGE_RATES.get(cur, {"symbol": "$"})["symbol"]
            price_converted = round(price_inr * conv_rate, 2)
            
            t_items.append({
                "item_name": t_name,
                "quantity": item.get("quantity", 1),
                "unit_price_original": price_inr,
                "unit_price_converted": price_converted,
                "currency_symbol": cur_symbol,
                "hsn_code": item.get("hsn_code", "50072010"),
            })

        t_terms = self.translate_text(TranslateTextRequest(text=req.terms_and_conditions, target_lang=req.target_lang, domain="invoice")).translated_text
        tax_disclaimers = {
            "en": "Export invoice exempt from domestic GST under LUT. Certified Authentic Indian Handicraft.",
            "fr": "Facture d'exportation exonérée de TVA locale sous convention LUT. Artisanat d'art indien certifié.",
            "de": "Exportrechnung befreit von inländischer Mehrwertsteuer. Zertifiziertes indisches Kunsthandwerk.",
            "ja": "輸出免税対象品 (LUT適用)。インド工芸品認定書添付。",
            "ar": "فاتورة تصدير معفاة من الضريبة المحلية. صناعة يدوية هندية معتمدة.",
            "es": "Factura de exportación exenta de impuestos locales. Artesanía auténtica certificada de la India.",
            "hi": "घरेलू जीएसटी से मुक्त निर्यात चालान। प्रमाणित प्रामाणिक भारतीय हस्तशिल्प।",
            "te": "ఎగుమతి ఇన్‌వాయిస్. ధృవీకరించబడిన ప్రామాణిక భారతీయ చేతివృత్తులు.",
        }
        disclaimer = tax_disclaimers.get(req.target_lang, tax_disclaimers["en"])

        return InvoiceTranslateResponse(
            invoice_number=req.invoice_number,
            target_lang=req.target_lang,
            target_currency=req.target_currency or "USD",
            translated_items=t_items,
            translated_terms_and_conditions=t_terms,
            localized_tax_disclaimer=disclaimer,
        )

    def translate_chat(self, req: ChatTranslateRequest) -> ChatTranslateResponse:
        detected_src = self.detect_language(req.message_text) if req.sender_lang == "auto" else req.sender_lang
        # Translate to recipient's language
        recipient_translation = self.translate_text(
            TranslateTextRequest(text=req.message_text, target_lang=req.recipient_lang, source_lang=detected_src, domain="chat")
        ).translated_text

        # Generate multi-language translations for global accessibility
        all_trans: Dict[str, str] = {}
        sample_langs = ["en", "hi", "te", "fr", "ja", "ar", "es"]
        for l in sample_langs:
            if l == detected_src:
                all_trans[l] = req.message_text
            else:
                all_trans[l] = self.translate_text(
                    TranslateTextRequest(text=req.message_text, target_lang=l, source_lang=detected_src, domain="chat")
                ).translated_text

        return ChatTranslateResponse(
            conversation_id=req.conversation_id,
            sender_id=req.sender_id,
            sender_role=req.sender_role,
            original_text=req.message_text,
            detected_source_lang=detected_src,
            recipient_lang=req.recipient_lang,
            translated_text=recipient_translation,
            all_translations=all_trans,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def translate_voice(self, req: VoiceTranslateRequest) -> VoiceTranslateResponse:
        detected_src = self.detect_language(req.audio_text_or_transcript) if req.source_lang == "auto" else req.source_lang
        trans: Dict[str, str] = {}
        for target in req.target_languages:
            trans[target] = self.translate_text(
                TranslateTextRequest(text=req.audio_text_or_transcript, target_lang=target, source_lang=detected_src, domain="voice")
            ).translated_text

        return VoiceTranslateResponse(
            transcription=req.audio_text_or_transcript,
            detected_source_lang=detected_src,
            translations=trans,
        )

    def convert_currency(self, req: CurrencyConvertRequest) -> CurrencyConvertResponse:
        from_cur = req.from_currency.upper()
        to_cur = req.to_currency.upper()

        from_rate = EXCHANGE_RATES.get(from_cur, {"rate": 1.0})["rate"]
        to_rate = EXCHANGE_RATES.get(to_cur, {"rate": 1.0, "symbol": "$"})["rate"]
        to_symbol = EXCHANGE_RATES.get(to_cur, {"symbol": "$"})["symbol"]

        # Convert to INR first, then to target
        inr_val = req.amount / max(from_rate, 0.000001) if from_cur != "INR" else req.amount
        converted = round(inr_val * to_rate, 2)
        effective_rate = round(to_rate / max(from_rate, 0.000001), 6)

        return CurrencyConvertResponse(
            original_amount=req.amount,
            from_currency=from_cur,
            to_currency=to_cur,
            exchange_rate=effective_rate,
            converted_amount=converted,
            formatted_string=f"{to_symbol}{converted:,.2f}",
        )

    def convert_measurement(self, req: MeasurementConvertRequest) -> MeasurementConvertResponse:
        f_u = req.from_unit.lower()
        t_u = req.to_unit.lower()
        val = req.value

        # Length conversions
        conversions = {
            ("cm", "inches"): val / 2.54,
            ("inches", "cm"): val * 2.54,
            ("meters", "yards"): val * 1.09361,
            ("yards", "meters"): val / 1.09361,
            ("kg", "lbs"): val * 2.20462,
            ("lbs", "kg"): val / 2.20462,
            ("g", "oz"): val / 28.3495,
            ("oz", "g"): val * 28.3495,
            ("sq_ft", "sq_m"): val * 0.092903,
            ("sq_m", "sq_ft"): val / 0.092903,
        }

        converted = conversions.get((f_u, t_u), val)
        converted = round(converted, 2)

        return MeasurementConvertResponse(
            original_value=val,
            from_unit=f_u,
            to_unit=t_u,
            converted_value=converted,
            formatted_string=f"{converted} {t_u}",
        )


translation_service = TranslationService()
