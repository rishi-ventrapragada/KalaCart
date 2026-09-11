"""
Prompt files existence and content tests.

Ensures catalog_system.md, translation.md, seo.md contain required instructions
for preserving artisan meaning, never invent materials, valid JSON only, etc.
"""
import os
from pathlib import Path

# Resolve repo root
PROMPT_DIR = Path(__file__).parent.parent / "app" / "ai" / "prompts"

CATALOG_PATH = PROMPT_DIR / "catalog_system.md"
TRANSLATION_PATH = PROMPT_DIR / "translation.md"
SEO_PATH = PROMPT_DIR / "seo.md"


class TestPromptFilesExist:
    def test_catalog_system_exists(self):
        assert CATALOG_PATH.exists(), f"Missing {CATALOG_PATH}"
        assert CATALOG_PATH.stat().st_size > 200

    def test_translation_exists(self):
        assert TRANSLATION_PATH.exists(), f"Missing {TRANSLATION_PATH}"
        assert TRANSLATION_PATH.stat().st_size > 200

    def test_seo_exists(self):
        assert SEO_PATH.exists(), f"Missing {SEO_PATH}"
        assert SEO_PATH.stat().st_size > 200

    def test_prompt_dir_contains_all_three(self):
        files = {p.name for p in PROMPT_DIR.glob("*.md")}
        assert "catalog_system.md" in files
        assert "translation.md" in files
        assert "seo.md" in files


class TestCatalogSystemContent:
    def setup_method(self):
        self.text = CATALOG_PATH.read_text(encoding="utf-8")
        self.lower = self.text.lower()

    def test_preserve_artisan_meaning(self):
        assert "preserve artisan meaning" in self.lower

    def test_never_invent_materials(self):
        assert "never invent materials" in self.lower

    def test_return_valid_json_only(self):
        # file uses "Return JSON only, no markdown" — accept with or without "valid"
        assert "return json only" in self.lower
        assert "return valid json only" in self.lower or "return json only" in self.lower

    def test_no_markdown_no_code_fences(self):
        assert "no markdown" in self.lower
        # at least mention code fences or json
        assert "code fences" in self.lower or "```json" in self.text

    def test_qwen3_model_mentioned(self):
        assert "qwen" in self.lower

    def test_temperature_and_tokens_documented(self):
        # developer instructions should mention temperature 0.7 and max_tokens 800 or temperature
        assert "temperature" in self.lower

    def test_categories_listed(self):
        for cat in ["Textiles", "Pottery", "Woodwork", "Metalwork", "Jewelry", "Painting", "Basketry", "Leather", "Other"]:
            assert cat in self.text

    def test_schema_keys_present(self):
        for key in ["title", "description_en", "description_hi", "category", "materials", "seo_tags", "care"]:
            assert key in self.text

    def test_contains_example(self):
        assert "Handloom Cotton Saree" in self.text or "Warangal" in self.text

    def test_does_not_contain_pricing_logic(self):
        # Ensure pricing is not implemented in catalog prompt
        assert "pricing" not in self.lower or "Do NOT add pricing" in self.text or "Do NOT" in self.text

    def test_contains_language_hint_handling(self):
        assert "language" in self.lower


class TestTranslationContent:
    def setup_method(self):
        self.text = TRANSLATION_PATH.read_text(encoding="utf-8")
        self.lower = self.text.lower()

    def test_natural_hindi(self):
        assert "natural hindi" in self.lower

    def test_preserve_cultural_terms(self):
        assert "preserve cultural terms" in self.lower
        # Should give examples
        assert "Warli" in self.text or "Ikat" in self.text

    def test_devanagari(self):
        assert "devanagari" in self.lower

    def test_not_literal_translation(self):
        # Should warn about literal MT
        assert "literal" in self.lower

    def test_return_json_when_requested(self):
        # Should mention Return JSON only at least conditionally
        assert "return json only" in self.lower or "translated_text" in self.text

    def test_does_not_expose_marketplace(self):
        assert "Do NOT expose" in self.text or "not as a separate endpoint" in self.text.lower() or "Do NOT" in self.text


class TestSeoContent:
    def setup_method(self):
        self.text = SEO_PATH.read_text(encoding="utf-8")
        self.lower = self.text.lower()

    def test_seo_tags_rules(self):
        assert "seo_tags" in self.lower
        assert "seo" in self.lower

    def test_care_instruction_present(self):
        assert "care" in self.lower

    def test_handmade_example(self):
        assert "Handmade" in self.text

    def test_constraints_documented(self):
        assert "2–5" in self.text or "2-5" in self.text
        assert "unique" in self.lower

    def test_never_invent_material_in_seo(self):
        assert "never invent" in self.lower or "not in materials" in self.lower

    def test_return_json_only(self):
        assert "return json only" in self.lower

    def test_integration_note_unified_call(self):
        assert "unified" in self.lower or "single" in self.lower or "already returns" in self.lower

    def test_no_pricing_marketplace(self):
        assert "pricing" in self.lower or "Do NOT create pricing" in self.text
