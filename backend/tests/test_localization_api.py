import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_list_all_11_supported_languages():
    response = client.get("/api/v1/localization/languages")
    assert response.status_code == 200
    languages = response.json()
    assert len(languages) == 11

    codes = [l["code"] for l in languages]
    expected_codes = ["en", "hi", "te", "ta", "kn", "fr", "de", "es", "ja", "ar", "zh"]
    for code in expected_codes:
        assert code in codes

    # Verify Arabic is RTL
    arabic = next(l for l in languages if l["code"] == "ar")
    assert arabic["direction"] == "rtl"

    # Verify Japanese and French are LTR
    japanese = next(l for l in languages if l["code"] == "ja")
    assert japanese["direction"] == "ltr"


def test_text_translation_and_caching():
    # 1. Translate to French
    req_fr = {
        "text": "Pochampally Ikat Pure Mulberry Silk Saree",
        "target_lang": "fr",
        "domain": "product"
    }
    res1 = client.post("/api/v1/localization/translate", json=req_fr)
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["target_lang"] == "fr"
    assert "soie" in data1["translated_text"].lower() or "sari" in data1["translated_text"].lower()
    assert data1["cached"] is False

    # 2. Translate again (Cache Hit)
    res2 = client.post("/api/v1/localization/translate", json=req_fr)
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["cached"] is True
    assert data2["translated_text"] == data1["translated_text"]

    # 3. Translate to Japanese
    req_ja = {
        "text": "Jaipur Blue Pottery Hand-Painted Floral Vase",
        "target_lang": "ja",
        "domain": "product"
    }
    res_ja = client.post("/api/v1/localization/translate", json=req_ja)
    assert res_ja.status_code == 200
    assert "ジャイプール" in res_ja.json()["translated_text"] or "陶器" in res_ja.json()["translated_text"]

    # 4. Translate to Telugu
    req_te = {
        "text": "Pochampally Ikat Pure Mulberry Silk Saree",
        "target_lang": "te",
        "domain": "product"
    }
    res_te = client.post("/api/v1/localization/translate", json=req_te)
    assert res_te.status_code == 200
    assert "పోచంపల్లి" in res_te.json()["translated_text"] or "పట్టు" in res_te.json()["translated_text"]


def test_product_multi_field_translation():
    payload = {
        "product_id": "prod_101",
        "title": "Pochampally Ikat Pure Mulberry Silk Saree",
        "description": "Authentic handloom saree crafted with vegetable dyes and silk mark certification.",
        "materials": ["Mulberry Silk", "Natural Dyes"],
        "techniques": ["Handcrafted"],
        "care_instructions": "Dry Clean Only",
        "target_lang": "ja"
    }
    response = client.post("/api/v1/localization/translate/product", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["target_lang"] == "ja"
    assert len(data["translated_materials"]) == 2
    assert len(data["translated_techniques"]) == 1
    assert data["translated_care_instructions"] is not None


def test_storefront_translation():
    payload = {
        "store_name": "Bastar Tribal Heritage Crafts",
        "tagline": "Handcrafted tribal brass sculptures from the heart of Chhattisgarh",
        "bio": "Generational master artisans preserving lost-wax brass bell metal casting.",
        "announcement": "Free international shipping for orders above $100",
        "target_lang": "fr"
    }
    response = client.post("/api/v1/localization/translate/storefront", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["target_lang"] == "fr"
    assert data["translated_store_name"] is not None
    assert data["translated_tagline"] is not None


def test_multilingual_chat_translation_seamless():
    # 1. French Buyer asks question in French
    buyer_msg = {
        "conversation_id": "conv_paris_hyd_001",
        "sender_id": "buyer_pierre_paris",
        "sender_role": "buyer",
        "message_text": "Bonjour, est-ce un tissage à la main authentique ?",
        "sender_lang": "fr",
        "recipient_lang": "te"
    }
    res1 = client.post("/api/v1/localization/translate/chat", json=buyer_msg)
    assert res1.status_code == 200
    chat1 = res1.json()
    assert chat1["detected_source_lang"] == "fr"
    assert chat1["recipient_lang"] == "te"
    # Telugu artisan receives question in Telugu
    assert "నమస్కారం" in chat1["translated_text"] or "చేనేత" in chat1["translated_text"]

    # 2. Telugu Artisan replies in Telugu
    seller_msg = {
        "conversation_id": "conv_paris_hyd_001",
        "sender_id": "artisan_ramesh_telangana",
        "sender_role": "seller",
        "message_text": "అవును, ఇది సిల్క్ మార్క్‌తో 100% సర్టిఫైడ్ చేనేత.",
        "sender_lang": "te",
        "recipient_lang": "fr"
    }
    res2 = client.post("/api/v1/localization/translate/chat", json=seller_msg)
    assert res2.status_code == 200
    chat2 = res2.json()
    assert chat2["detected_source_lang"] == "te"
    assert chat2["recipient_lang"] == "fr"
    # French buyer receives response in French
    assert "oui" in chat2["translated_text"].lower() or "certifi" in chat2["translated_text"].lower() or "soie" in chat2["translated_text"].lower()


def test_export_invoice_translation_with_currency():
    invoice_payload = {
        "invoice_number": "KC-EXP-2026-FR-092",
        "items": [
            {
                "name": "Pochampally Ikat Pure Mulberry Silk Saree",
                "quantity": 2,
                "price_inr": 8500.0,
                "hsn_code": "50072010"
            }
        ],
        "terms_and_conditions": "100% Escrow secured. Return accepted within 14 days of international delivery.",
        "target_lang": "fr",
        "target_currency": "EUR"
    }
    response = client.post("/api/v1/localization/translate/invoice", json=invoice_payload)
    assert response.status_code == 200
    inv = response.json()
    assert inv["target_lang"] == "fr"
    assert inv["target_currency"] == "EUR"
    assert len(inv["translated_items"]) == 1
    assert inv["translated_items"][0]["unit_price_converted"] > 0
    assert "€" in inv["translated_items"][0]["currency_symbol"]
    assert "TVA" in inv["localized_tax_disclaimer"] or "exportation" in inv["localized_tax_disclaimer"]


def test_currency_and_measurement_conversion():
    # 1. Currency Conversion INR -> USD
    cur_res = client.post("/api/v1/localization/currency/convert", json={
        "amount": 10000.0,
        "from_currency": "INR",
        "to_currency": "USD"
    })
    assert cur_res.status_code == 200
    cur_data = cur_res.json()
    assert cur_data["converted_amount"] == 119.0
    assert "$" in cur_data["formatted_string"]

    # 2. Measurement Conversion cm -> inches
    meas_res = client.post("/api/v1/localization/measurements/convert", json={
        "value": 50.8,
        "from_unit": "cm",
        "to_unit": "inches"
    })
    assert meas_res.status_code == 200
    assert meas_res.json()["converted_value"] == 20.0
    assert "inches" in meas_res.json()["formatted_string"]
