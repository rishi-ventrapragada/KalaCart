"""
Unit tests for catalog validation helpers:
- _strip_control_chars / strip_control_and_trim
- transcript length 5-1000
- language regex
- _validate_catalog_schema
- _strip_code_fences
"""
import json
import os

os.environ.setdefault("DEBUG", "true")

import pytest
from pydantic import ValidationError

from app.api.catalog import GenerateCatalogRequest, _validate_catalog_schema, _strip_code_fences, ALLOWED_CATEGORIES
from app.ai.catalog import _strip_control_chars, _strip_code_fences as ai_strip_fences, _validate_catalog_schema as ai_validate


def valid_payload(**overrides):
    base = {
        "title": "Handloom Cotton Saree - Warangal",
        "description_en": "Handwoven in Warangal using pure cotton and natural dyes, this handloom saree celebrates Telangana heritage. Breathable weave drapes elegantly while subtle hues reflect eco-conscious craftsmanship. Woven on pit loom supporting sustainable livelihoods.",
        "description_hi": "वारंगल में शुद्ध कॉटन और प्राकृतिक रंगों से हाथ से बुनी गई यह साड़ी तेलंगाना की बुनकर परंपरा का प्रतीक है। इसकी हल्की बुनावट और प्राकृतिक रंग इसे रोज़मर्रा और त्योहार दोनों के लिए उपयुक्त बनाते हैं।",
        "category": "Textiles",
        "materials": ["Cotton"],
        "seo_tags": ["Handmade", "Cotton", "Sustainable"],
        "care": "Hand wash only",
    }
    base.update(overrides)
    return base


# ── Transcript stripping & length ──────────────────────────────────────────


class TestTranscriptValidation:
    def test_strip_control_chars_helper(self):
        assert _strip_control_chars("hello\x00\x01world") == "helloworld"
        assert _strip_control_chars("\x7f trim \x1f ") == "trim"
        assert _strip_control_chars("  normal  ") == "normal"

    def test_strip_control_chars_via_pydantic(self):
        m = GenerateCatalogRequest(transcript="Hello world cotton saree Warangal\x00\x01", language="en")
        assert "\x00" not in m.transcript
        assert m.transcript.startswith("Hello")

    def test_transcript_too_short_after_strip(self):
        with pytest.raises(ValidationError) as exc:
            GenerateCatalogRequest(transcript="hi\x00", language="en")
        assert "at least 5" in str(exc.value).lower()

    def test_transcript_empty_after_stripping_controls(self):
        with pytest.raises(ValidationError):
            GenerateCatalogRequest(transcript="\x00\x01\x02\x03", language="en")

    def test_transcript_too_long(self):
        with pytest.raises(ValidationError) as exc:
            GenerateCatalogRequest(transcript="a" * 1001, language="en")
        assert "at most 1000" in str(exc.value) or "1000" in str(exc.value)

    def test_transcript_exact_5_ok(self):
        m = GenerateCatalogRequest(transcript="Hello", language="en")
        assert len(m.transcript) == 5

    def test_transcript_exact_1000_ok(self):
        m = GenerateCatalogRequest(transcript="x" * 1000, language="en")
        assert len(m.transcript) == 1000

    def test_transcript_5_with_whitespace_trim(self):
        # "  Hello  " -> 5 after trim
        m = GenerateCatalogRequest(transcript="  Hello  ", language="en")
        assert m.transcript == "Hello"

    def test_transcript_controls_make_it_short(self):
        # "ab\x00\x01" -> "ab" -> too short -> 422
        with pytest.raises(ValidationError):
            GenerateCatalogRequest(transcript="ab\x00\x01", language="en")

    def test_language_valid_codes(self):
        for lang in ["te", "hi", "en", "ta", "kn"]:
            m = GenerateCatalogRequest(transcript="Valid transcript for language test", language=lang)
            assert m.language == lang

    def test_language_invalid(self):
        for bad in ["fr", "de", "es", "xx", "english"]:
            with pytest.raises(ValidationError):
                GenerateCatalogRequest(transcript="Valid transcript length sufficient", language=bad)

    def test_language_normalized_lowercase(self):
        m = GenerateCatalogRequest(transcript="Valid transcript length sufficient", language="TE")
        assert m.language == "te"

    def test_language_stripped(self):
        m = GenerateCatalogRequest(transcript="Valid transcript length sufficient", language="  en  ")
        assert m.language == "en"

    def test_default_language_te(self):
        m = GenerateCatalogRequest(transcript="Valid transcript length sufficient")
        # default should be te (per model)
        assert m.language == "te"


# ── Code fence stripping ───────────────────────────────────────────────────


class TestStripCodeFences:
    def test_plain_json_unchanged(self):
        j = json.dumps(valid_payload())
        assert json.loads(_strip_code_fences(j)) == valid_payload()
        assert json.loads(ai_strip_fences(j)) == valid_payload()

    def test_fenced_json(self):
        j = valid_payload()
        s = "```json\n" + json.dumps(j) + "\n```"
        assert json.loads(_strip_code_fences(s)) == j
        assert json.loads(ai_strip_fences(s)) == j

    def test_fenced_no_lang(self):
        j = valid_payload()
        s = "```\n" + json.dumps(j) + "\n```"
        assert json.loads(_strip_code_fences(s)) == j

    def test_preamble_before_json(self):
        j = valid_payload()
        s = "Here is your JSON:\n" + json.dumps(j) + " hope you like it"
        parsed = json.loads(_strip_code_fences(s))
        assert parsed["title"] == j["title"]

    def test_empty_string(self):
        assert _strip_code_fences("") == ""
        assert ai_strip_fences("") == ""

    def test_extract_outermost_braces(self):
        # LLM returns ```json { "a": 1 } ```
        s = 'Sure! ```json\n{"title":"Test Title Valid","description_en":"' + "a"*30 + '","description_hi":"'+"ब"*30+'","category":"Textiles","materials":["Cotton"],"seo_tags":["Handmade","Cotton"],"care":"Hand wash"}\n```'
        stripped = _strip_code_fences(s)
        assert stripped.startswith("{")
        assert stripped.endswith("}")


# ── Schema validation ──────────────────────────────────────────────────────


class TestValidateCatalogSchema:
    def test_valid_passes(self):
        ok, msg = _validate_catalog_schema(valid_payload())
        assert ok is True, msg
        ok2, msg2 = ai_validate(valid_payload())
        assert ok2 is True, msg2

    def test_missing_title_fails(self):
        p = valid_payload()
        del p["title"]
        ok, msg = _validate_catalog_schema(p)
        assert ok is False
        assert "title" in msg.lower()

    def test_title_too_short_fails(self):
        ok, msg = _validate_catalog_schema(valid_payload(title="Hi"))
        assert not ok
        assert "title" in msg.lower()

    def test_title_too_long_fails(self):
        ok, _ = _validate_catalog_schema(valid_payload(title="A" * 81))
        assert not ok

    def test_description_en_too_short(self):
        ok, msg = _validate_catalog_schema(valid_payload(description_en="short"))
        assert not ok
        assert "description_en" in msg

    def test_description_hi_too_short(self):
        ok, _ = _validate_catalog_schema(valid_payload(description_hi="छोटा"))
        assert not ok

    def test_invalid_category_fails(self):
        ok, msg = _validate_catalog_schema(valid_payload(category="Silk"))
        assert not ok
        assert "category" in msg.lower()
        # ensure allowed list works
        for cat in ALLOWED_CATEGORIES:
            ok, _ = _validate_catalog_schema(valid_payload(category=cat))
            assert ok

    def test_empty_materials_fails(self):
        ok, _ = _validate_catalog_schema(valid_payload(materials=[]))
        assert not ok

    def test_materials_too_many_fails(self):
        ok, _ = _validate_catalog_schema(valid_payload(materials=["a", "b", "c", "d", "e", "f"]))
        assert not ok

    def test_materials_entry_empty_fails(self):
        ok, _ = _validate_catalog_schema(valid_payload(materials=["", "Cotton"]))
        assert not ok

    def test_materials_entry_too_long_fails(self):
        ok, _ = _validate_catalog_schema(valid_payload(materials=["A" * 31]))
        assert not ok

    def test_seo_tags_too_few_fails(self):
        ok, _ = _validate_catalog_schema(valid_payload(seo_tags=["OnlyOne"]))
        assert not ok

    def test_seo_tags_too_many_fails(self):
        ok, _ = _validate_catalog_schema(valid_payload(seo_tags=["a", "b", "c", "d", "e", "f"]))
        assert not ok

    def test_seo_tags_duplicate_case_insensitive_fails(self):
        ok, msg = _validate_catalog_schema(valid_payload(seo_tags=["Cotton", "cotton", "Handmade"]))
        assert not ok
        assert "unique" in msg.lower()

    def test_seo_tags_entry_too_short_fails(self):
        ok, _ = _validate_catalog_schema(valid_payload(seo_tags=["a", "Handmade"]))
        assert not ok

    def test_care_too_short_fails(self):
        ok, _ = _validate_catalog_schema(valid_payload(care="hi"))
        assert not ok

    def test_care_too_long_fails(self):
        ok, _ = _validate_catalog_schema(valid_payload(care="x" * 201))
        assert not ok

    def test_missing_required_keys(self):
        for key in ["title", "description_en", "description_hi", "category", "materials", "seo_tags", "care"]:
            p = valid_payload()
            del p[key]
            ok, msg = _validate_catalog_schema(p)
            assert not ok, f"should fail when missing {key}"
            assert key in msg

    def test_not_dict_fails(self):
        ok, msg = _validate_catalog_schema([])  # type: ignore
        assert not ok
        ok, _ = ai_validate("not a dict")  # type: ignore
        assert not ok

    def test_ai_validate_allows_control_char_check(self):
        # ai_validate additionally checks control chars in title
        p = valid_payload(title="Hello\x01World Valid Title Here")
        ok, msg = ai_validate(p)
        # app/ai/catalog adds control char check -> should fail
        assert not ok
        assert "control" in msg.lower()

    def test_seo_tags_unique_exact_duplicate_fails(self):
        ok, _ = _validate_catalog_schema(valid_payload(seo_tags=["Handmade", "Handmade", "Cotton"]))
        assert not ok

    def test_valid_all_categories(self):
        for cat in ALLOWED_CATEGORIES:
            ok, msg = _validate_catalog_schema(valid_payload(category=cat))
            assert ok, f"{cat} should be valid: {msg}"

    def test_valid_materials_boundaries(self):
        ok, _ = _validate_catalog_schema(valid_payload(materials=["Cotton"]))
        assert ok
        ok, _ = _validate_catalog_schema(valid_payload(materials=["a", "b", "c", "d", "e"]))
        assert ok

    def test_valid_seo_tags_boundaries(self):
        ok, _ = _validate_catalog_schema(valid_payload(seo_tags=["ab", "cd"]))
        assert ok
        ok, _ = _validate_catalog_schema(valid_payload(seo_tags=["ab", "cd", "ef", "gh", "ij"]))
        assert ok
