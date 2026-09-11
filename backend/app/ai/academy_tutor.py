from typing import Dict, Any, List
from app.models.academy import AITutorQuery, AITutorResponse

# Craft Academy Knowledge Base
_KNOWLEDGE_BASE = {
    "photography": {
        "en": "For natural craft photography, use soft morning sunlight (7 AM - 9 AM) near a window. Place your terracotta or textile product on a neutral background like beige cotton fabric or rustic wood. Avoid using direct camera flash as it washes out intricate textures and glaze reflections.",
        "hi": "हस्तशिल्प की प्राकृतिक फोटोग्राफी के लिए सुबह की हल्की धूप (7-9 AM) में खिड़की के पास फोटो लें। मिट्टी के बर्तनों या कपड़ों को सादे सूती कपड़े या लकड़ी के तख्ते पर रखें। कैमरे की सीधी फ्लैश से बचें ताकि कलाकृति की बारीक बनावट और चमक खराब न हो।",
        "ta": "இயற்கையான கைவினைப் பொருட்களின் புகைப்படத்திற்கு காலை 7-9 மணிக்குள் மென்மையான சூரிய ஒளியைப் பயன்படுத்தவும். எளிய பின்னணியைப் பயன்படுத்தவும். நேரடி ஃப்ளாஷைத் தவிர்க்கவும்.",
        "te": "సహజమైన ఫోటోగ్రఫీ కోసం ఉదయం 7-9 గంటల మధ్య కిటికీ దగ్గర మృదువైన సూర్యకాంతిని ఉపయోగించండి. సాదా కాటన్ క్లాత్‌ను బ్యాక్‌గ్రౌండ్‌గా వాడండి.",
        "bn": "হস্তশিল্পের সুন্দর ছবির জন্য সকালের নরম আলো ব্যবহার করুন। একটি সাধারণ সুতির কাপড়ের ওপর পণ্য রেখে ছবি তুলুন। ফ্ল্যাশ ব্যবহার করবেন না।"
    },
    "pricing": {
        "en": "To calculate a profitable selling price for handmade products: Cost = (Raw Materials + Packaging) + (Crafting Hours × Hourly Wage) + Electricity/Overheads. Selling Price = Cost + Desired Margin (usually 30-40% for retail, 20-25% for wholesale). Never sell below your minimum cost floor.",
        "hi": "हस्तशिल्प की सही कीमत तय करने का फॉर्मूला: कुल लागत = (कच्चा माल + पैकेजिंग) + (कारीगरी के घंटे × प्रति घंटा मजदूरी) + बिजली/अन्य खर्चे। बिक्री मूल्य = कुल लागत + 30-40% मुनाफा मार्जिन। कभी भी लागत से कम पर न बेचें।",
        "ta": "விலை நிர்ணயம்: மொத்த செலவு = (மூலப்பொருள் + பேக்கிங்) + (வேலை நேரம் × கூலி) + இதர செலவுகள். விற்பனை விலை = செலவு + 30-40% லாபம்.",
        "te": "ధర నిర్ణయం: ఖర్చు = (ముడి సరుకు + ప్యాకింగ్) + (శ్రమ సమయం × రోజువారీ వేతనం). అమ్మకపు ధర = ఖర్చు + 30-40% లాభం.",
        "bn": "সঠিক মূল্য নির্ধারণ: মোট খরচ = (কাঁচামাল + প্যাকেজিং) + (কাজের সময় × পারিশ্রমিক)। বিক্রয় মূল্য = খরচ + ৩০-৪০% লাভ।"
    },
    "packaging": {
        "en": "For fragile terracotta pottery and brass handicrafts, use 3-ply corrugated boxes with eco-friendly honeycomb paper or shredded craft paper. Ensure at least 2 inches of cushioning around all sides. Seal with water-activated reinforced paper tape.",
        "hi": "मिट्टी के बर्तनों और पीतल की शिल्पकला के लिए 3-प्लाई वाले मजबूत गत्ते के डिब्बे और पर्यावरण-अनुकूल हनीकॉम्ब पेपर का उपयोग करें। चारों तरफ कम से कम 2 इंच की कुशनिंग रखें और सुरक्षित टेप लगाएं।",
        "ta": "உடையக்கூடிய மண்பாண்டங்களுக்கு 3-அடுக்கு அட்டைப்பெட்டிகள் மற்றும் சுற்றுச்சூழலுக்கு உகந்த பேப்பரை பயன்படுத்தவும்.",
        "te": "మట్టి పాత్రలు మరియు ఇత్తడి వస్తువుల కోసం దృఢమైన 3-ప్లై పెట్టెలు మరియు కుషనింగ్ పేపర్‌ను వాడండి.",
        "bn": "মাটির জিনিস ও পিতলের জন্য শক্ত ৩-প্লাই কার্টন এবং ইকো-ফ্রেন্ডলি কুশনিং পেপার ব্যবহার করুন।"
    },
    "gst": {
        "en": "Handicrafts under composition or standard GST scheme require clear HSN code tagging. For interstate B2B or B2C e-commerce sales through KalaCart, GST registration provides input tax credit (ITC) on your raw materials (clay, brass ingots, silk yarn), reducing total production tax burden.",
        "hi": "हस्तशिल्प वस्तुओं पर जीएसटी इनपुट टैक्स क्रेडिट (ITC) का लाभ मिलता है। जब आप कच्चा माल (मिट्टी, पीतल, रेशम) पक्के बिल पर खरीदते हैं, तो उस पर चुकाया गया टैक्स आपके अंतिम टैक्स में से घट जाता है।",
        "ta": "ஜிஎஸ்டி மூலப்பொருள் வாங்கும் போது செலுத்தப்பட்ட வரியை உங்கள் இறுதி வரியில் கழித்துக் கொள்ளலாம் (ITC).",
        "te": "జిఎస్‌టి ద్వారా మీరు కొనుగోలు చేసే ముడి సరుకులపై ఇన్‌పుట్ టాక్స్ క్రెడిట్ (ITC) ప్రయోజనం పొందవచ్చు.",
        "bn": "জিএসটি ইনপুট ট্যাক্স ক্রেডিট (ITC) এর মাধ্যমে কাঁচামাল কেনার কর আপনার মোট কর থেকে সমন্বয় হয়।"
    },
    "export": {
        "en": "To export handicrafts globally: 1. Obtain an Import Export Code (IEC) from DGFT. 2. Register with Export Promotion Council for Handicrafts (EPCH). 3. Ensure authentic GI Tag certification and lead-free compliance testing for dining pottery.",
        "hi": "विदेशों में हस्तशिल्प निर्यात करने के लिए: 1. डीजीएफटी से आईईसी (IEC) कोड प्राप्त करें। 2. ईपीसीएच (EPCH) में पंजीकरण कराएं। 3. जीआई टैग (GI Tag) और अंतरराष्ट्रीय गुणवत्ता प्रमाण पत्र अवश्य रखें।",
        "ta": "ஏற்றுமதி செய்ய: 1. IEC கோட் பெறவும். 2. EPCH பதிவு செய்யவும். 3. GI Tag தரச் சான்றிதழ் வைக்கவும்.",
        "te": "ఎగుమతి చేయడానికి: 1. IEC కోడ్ పొందండి. 2. EPCH రిజిస్ట్రేషన్ చేయండి. 3. GI ట్యాగ్ సర్టిఫికేట్ కలిగి ఉండండి.",
        "bn": "রপ্তানি করার জন্য: ১. IEC কোড নিন। ২. EPCH এ নথিভুক্ত করুন। ৩. জিআই ট্যাগ নিশ্চিত করুন।"
    }
}

class AITutorEngine:
    @staticmethod
    def answer_query(query: AITutorQuery) -> AITutorResponse:
        text = query.question.lower()
        lang = query.preferred_language.lower()
        if lang not in ["hi", "ta", "te", "bn", "en"]:
            lang = "en"

        matched_topic = "pricing"
        if any(w in text for w in ["photo", "camera", "picture", "light", "background", "तस्वीर", "फोटो", "படம்", "ఫోటో", "ছবি"]):
            matched_topic = "photography"
        elif any(w in text for w in ["package", "box", "bubble", "break", "courier", "पैकिंग", "डिब्बा", "பேக்கிங்", "ప్యాకింగ్"]):
            matched_topic = "packaging"
        elif any(w in text for w in ["gst", "tax", "invoice", "hsn", "टैक्स", "जीएसटी", "வரி", "పన్ను"]):
            matched_topic = "gst"
        elif any(w in text for w in ["export", "abroad", "foreign", "iec", "epch", "विदेश", "निर्यात", "ஏற்றுமதி", "ఎగుమతి", "রপ্তানি"]):
            matched_topic = "export"
        elif any(w in text for w in ["price", "cost", "margin", "profit", "discount", "कीमत", "दाम", "मुनाफा", "விலை", "ధర", "লাভ"]):
            matched_topic = "pricing"

        answer = _KNOWLEDGE_BASE.get(matched_topic, {}).get(lang) or _KNOWLEDGE_BASE.get(matched_topic, {}).get("en", "")

        followups = {
            "photography": [
                "How do I edit photos on my smartphone?",
                "What is the best angle for pottery vs sarees?",
                "How to take 360-degree product videos?"
            ],
            "pricing": [
                "How do I calculate wholesale bulk discounts?",
                "How to protect profit during buyer negotiations?",
                "Should I charge separately for shipping?"
            ],
            "packaging": [
                "Which box thickness is required for heavy brass items?",
                "How to avoid moisture damage for wooden artifacts?",
                "Where can I buy eco-friendly honeycomb paper in bulk?"
            ],
            "gst": [
                "Do I need GST if my annual sales are under 20 Lakhs?",
                "What is the HSN code for handloom sarees?",
                "How to claim input tax credit on craft tools?"
            ],
            "export": [
                "How to register with EPCH council?",
                "What documents are needed for US / Europe customs?",
                "How to accept international wire payments safely?"
            ]
        }

        return AITutorResponse(
            answer=answer,
            detected_language=lang,
            suggested_followups=followups.get(matched_topic, followups["pricing"]),
            reference_lesson_id=f"lesson-{matched_topic}-01"
        )
