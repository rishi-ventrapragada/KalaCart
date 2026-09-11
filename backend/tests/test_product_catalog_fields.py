"""
Product catalog fields tests — ensures new columns/fields exist.

Checks:
- DB schema.sql contains description_hi, care_instruction, seo_tags, materials_jsonb
- Pydantic Product models expose those fields
- Model validation for new fields (20-500 hi, 1-5 materials, 2-5 seo_tags, care 5-200)
"""
import os
from pathlib import Path

os.environ.setdefault("DEBUG", "true")

from pydantic import ValidationError
import pytest


def _schema_text():
    root = Path(__file__).parent.parent.parent
    schema_path = root / "database" / "schema.sql"
    if schema_path.exists():
        return schema_path.read_text(encoding="utf-8").lower()
    # fallback to backend relative
    alt = Path(__file__).parent.parent / "database" / "schema.sql"
    if alt.exists():
        return alt.read_text(encoding="utf-8").lower()
    return ""


class TestSchemaSQLColumns:
    def test_description_hi_in_schema(self):
        txt = _schema_text()
        assert "description_hi" in txt, "schema.sql must contain description_hi"

    def test_care_instruction_in_schema(self):
        txt = _schema_text()
        assert "care_instruction" in txt

    def test_seo_tags_in_schema(self):
        txt = _schema_text()
        assert "seo_tags" in txt

    def test_materials_jsonb_in_schema(self):
        txt = _schema_text()
        assert "materials_jsonb" in txt

    def test_schema_has_gin_indexes(self):
        txt = _schema_text()
        assert "gin" in txt
        assert "seo_tags" in txt


class TestPydanticProductFieldsExist:
    def test_product_base_has_new_fields(self):
        from app.models.product import ProductBase

        fields = set(ProductBase.model_fields.keys())
        assert "description_hi" in fields, f"missing description_hi in {fields}"
        assert "materials" in fields
        assert "seo_tags" in fields
        assert "care_instruction" in fields
        assert "title" in fields
        assert "category" in fields

    def test_product_create_allows_new_fields(self):
        from app.models.product import ProductCreate

        p = ProductCreate(
            title="Handloom Saree",
            description="A beautiful handloom saree made with natural dyes and cotton, long enough.",
            artisan_id="11111111-1111-1111-1111-111111111111",
            price=2500,
            category="Textiles",
            description_hi="वारंगल में शुद्ध कॉटन से हाथ से बुनी गई यह साड़ी तेलंगाना की परंपरा है और बहुत सुंदर है।",
            materials=["Cotton", "Natural Dyes"],
            seo_tags=["Handmade", "Cotton", "Sustainable"],
            care_instruction="Hand wash cold, dry in shade",
        )
        assert p.description_hi is not None
        assert p.materials == ["Cotton", "Natural Dyes"]
        assert p.seo_tags == ["Handmade", "Cotton", "Sustainable"]
        assert p.care_instruction == "Hand wash cold, dry in shade"

    def test_product_response_has_new_fields(self):
        from app.models.product import ProductResponse

        fields = set(ProductResponse.model_fields.keys())
        assert "description_hi" in fields
        assert "materials" in fields
        assert "seo_tags" in fields
        assert "care_instruction" in fields


class TestPydanticProductValidation:
    def test_description_hi_too_short_rejected(self):
        from app.models.product import ProductCreate

        with pytest.raises(ValidationError):
            ProductCreate(
                title="Saree",
                description="Valid description long enough for validation",
                artisan_id="11111111-1111-1111-1111-111111111111",
                price=100,
                category="Textiles",
                description_hi="छोटा",  # <20
            )

    def test_description_hi_none_allowed(self):
        from app.models.product import ProductCreate

        p = ProductCreate(
            title="Saree",
            description="Valid description long enough for validation",
            artisan_id="11111111-1111-1111-1111-111111111111",
            price=100,
            category="Textiles",
            description_hi=None,
        )
        assert p.description_hi is None

    def test_materials_coerced_and_validated(self):
        from app.models.product import ProductCreate

        p = ProductCreate(
            title="Saree",
            description="Valid description long enough for validation",
            artisan_id="11111111-1111-1111-1111-111111111111",
            price=100,
            category="Textiles",
            materials=["Cotton"],
        )
        assert p.materials == ["Cotton"]

    def test_seo_tags_duplicate_rejected(self):
        from app.models.product import ProductCreate

        with pytest.raises(ValidationError) as exc:
            ProductCreate(
                title="Saree",
                description="Valid description long enough for validation",
                artisan_id="11111111-1111-1111-1111-111111111111",
                price=100,
                category="Textiles",
                seo_tags=["Cotton", "cotton", "Handmade"],
            )
        assert "unique" in str(exc.value).lower()

    def test_care_instruction_strips_control_chars(self):
        from app.models.product import ProductCreate

        p = ProductCreate(
            title="Saree",
            description="Valid description long enough for validation",
            artisan_id="11111111-1111-1111-1111-111111111111",
            price=100,
            category="Textiles",
            care_instruction="Hand wash\x00 cold",
        )
        assert "\x00" not in p.care_instruction

    def test_materials_alias_materials_jsonb(self):
        from app.models.product import ProductBase

        p = ProductBase(
            title="Saree",
            description="Valid description long enough for validation",
            price=100,
            category="Textiles",
            materials_jsonb=["Cotton", "Silk"],
        )
        assert p.materials == ["Cotton", "Silk"]

    def test_seo_tags_alias_tags(self):
        from app.models.product import ProductBase

        p = ProductBase(
            title="Saree",
            description="Valid description long enough for validation",
            price=100,
            category="Textiles",
            tags=["Handmade", "Cotton"],
        )
        assert p.seo_tags == ["Handmade", "Cotton"]

    def test_care_alias_care(self):
        from app.models.product import ProductBase

        p = ProductBase(
            title="Saree",
            description="Valid description long enough for validation",
            price=100,
            category="Textiles",
            care="Hand wash cold",
        )
        assert p.care_instruction == "Hand wash cold"

    def test_description_en_alias(self):
        from app.models.product import ProductBase

        p = ProductBase(
            title="Saree",
            price=100,
            category="Textiles",
            description_en="Valid description long enough for validation via alias",
        )
        assert p.description is not None
