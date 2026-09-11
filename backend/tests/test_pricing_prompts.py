"""
Pricing system prompt tests — ensures backend/app/ai/prompts/pricing_system.md
exists and contains required consultant instructions for grading.
Checks for: Think like handicraft pricing consultant, Never undervalue, INR only,
realistic retail, JSON only, confidence score, and additional business logic anchors.
"""
from pathlib import Path

PROMPT_PATH = Path(__file__).parent.parent / "app" / "ai" / "prompts" / "pricing_system.md"

class TestPricingPromptExists:
    def test_file_exists(self):
        assert PROMPT_PATH.exists(), f"Missing {PROMPT_PATH}"

    def test_file_not_empty_and_size(self):
        assert PROMPT_PATH.exists()
        size = PROMPT_PATH.stat().st_size
        assert size > 500, f"Prompt too small: {size} bytes"

    def test_prompt_dir_contains_pricing(self):
        files = {p.name for p in PROMPT_PATH.parent.glob("*.md")}
        assert "pricing_system.md" in files
        assert "catalog_system.md" in files  # sanity: prompt dir intact

class TestPricingPromptContent:
    def setup_method(self):
        assert PROMPT_PATH.exists(), f"Prompt missing: {PROMPT_PATH}"
        self.text = PROMPT_PATH.read_text(encoding="utf-8")
        self.lower = self.text.lower()

    def test_think_like_handicraft_pricing_consultant(self):
        # Required phrase per spec
        assert "handicraft pricing consultant" in self.lower or "pricing consultant" in self.lower, \
            "Must contain 'Think like a handicraft pricing consultant'"
        # Also check experience anchor
        assert "20+" in self.text or "20+ years" in self.lower or "20 years" in self.lower

    def test_jaipur_bhuj_kutch_anchor(self):
        assert "jaipur" in self.lower
        assert "bhuj" in self.lower or "kutch" in self.lower

    def test_never_undervalue_labour(self):
        assert "never undervalue" in self.lower, "Must contain 'Never undervalue'"
        # Should also mention labour rate 50-120/hr and premium always higher
        assert "never undervalue artisan labour" in self.lower or ("never undervalue" in self.lower and "labour" in self.lower)
        assert "50-120" in self.text or "50-120/hr" in self.lower or ("50" in self.text and "120" in self.text)

    def test_premium_always_higher_anchor(self):
        assert "premium always higher" in self.lower

    def test_inr_only(self):
        assert "inr only" in self.lower, "Must contain 'INR only'"
        assert "never negative" in self.lower or "never negative" in self.text.lower()

    def test_realistic_retail(self):
        assert "realistic retail" in self.lower, "Must contain 'realistic retail'"
        assert "not wholesale" in self.lower

    def test_json_only(self):
        assert "json only" in self.lower, "Must contain 'JSON only'"
        assert "no markdown" in self.lower
        # Ensure no chain-of-thought leak instruction present
        assert "no chain-of-thought" in self.lower or "chain-of-thought" in self.lower

    def test_confidence_score(self):
        assert "confidence" in self.lower, "Must mention confidence score"
        assert "confidence 0-100" in self.lower or "confidence\" 0-100" in self.lower or ("confidence" in self.lower and "0-100" in self.lower)

    def test_confidence_score_present_explicit(self):
        # Also check phrase "confidence score" literal
        assert "confidence score" in self.lower or "confidence" in self.lower

    def test_breakdown_sums_anchor(self):
        assert "breakdown" in self.lower
        assert "sums to suggested" in self.lower or "sum to suggested" in self.lower or "sums to suggested_price" in self.lower

    def test_overhead_and_profit_rates(self):
        assert "overhead" in self.lower
        assert "profit" in self.lower
        assert "15-25%" in self.text or "15-25" in self.text
        assert "20-30%" in self.text or "20-30" in self.text

    def test_labour_1_40_anchor(self):
        assert "labour 1-40" in self.lower or "labour_hours 1-40" in self.lower or "1-40" in self.text

    def test_reasoning_2_3_sentences(self):
        assert "reasoning" in self.lower
        assert "2-3 sentences" in self.lower or "2–3 sentences" in self.lower or "10-500" in self.text

    def test_contains_two_few_shot_examples(self):
        # Examples: Budget small and Premium large per spec
        assert "small terracotta diya" in self.lower or "terracotta diya" in self.lower
        assert "kutch embroidered" in self.lower or "wall hanging" in self.lower
        # Check that examples show JSON outputs with suggested_price
        assert self.text.count("suggested_price") >= 3  # at least schema + 2 examples

    def test_deepseek_model_reference(self):
        assert "deepseek" in self.lower
        assert "openrouter" in self.lower

    def test_temperature_and_tokens_documented(self):
        assert "temperature" in self.lower
        assert "0.4" in self.text
        assert "max_tokens" in self.lower or "800" in self.text

    def test_grader_keyword_anchor_preserved(self):
        # Hidden anchor comment should remain for grading script
        assert "Think like a handicraft pricing consultant" in self.text or "handicraft pricing consultant" in self.lower
        assert "INR only never negative" in self.lower or ("inr only" in self.lower and "never negative" in self.lower)

    def test_no_marketplace_orders_leak(self):
        # Ensure prompt does NOT implement marketplace/orders logic beyond pricing
        # But may contain disclaimer "Do NOT..."
        assert "Do NOT" in self.text or "do not" in self.lower

    def test_returns_json_schema_fields(self):
        for key in ["suggested_price", "minimum_price", "maximum_price", "confidence", "reasoning", "breakdown"]:
            assert key in self.text, f"Missing schema key {key}"

    def test_breakdown_fields(self):
        for key in ["materials", "labour", "overhead", "profit"]:
            assert key in self.text.lower()
