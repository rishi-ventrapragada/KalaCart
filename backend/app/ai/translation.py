"""
AI service: Multilingual translation using Qwen 3.
Translates product listings while preserving cultural terms.
"""

from app.ai.client import chat_completion, QWEN_MODEL

TRANSLATION_SYSTEM_PROMPT = """
You are KalaCart's translator. Translate handicraft listings between Indian languages
(hi, bn, te, mr, ta, gu, kn, ml, pa, en) preserving craft-specific terms (e.g., Warli, Phulkari)
in transliteration. Output JSON: {translated_text: string, detected_language: string}.
See ai-prompts/translation_prompt.md.
"""


async def translate_text(
    text: str,
    target_language: str,
    source_language: str = "auto",
) -> dict:
    """
    Translates text to target language via Qwen.

    Returns:
        Dict with translated_text and detected_language
    """
    user_prompt = f"Source language: {source_language}\nTarget language: {target_language}\nText: \"{text}\""

    content = await chat_completion(
        messages=[
            {"role": "system", "content": TRANSLATION_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        model=QWEN_MODEL,
        temperature=0.3,
    )

    return {"raw": content}
