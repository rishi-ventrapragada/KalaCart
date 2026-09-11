"""
AI service: Intelligent Pricing using DeepSeek.
Suggests fair market price based on craft, materials, labor, and comparables.
"""

from app.ai.client import chat_completion, DEEPSEEK_MODEL

PRICING_SYSTEM_PROMPT = """
You are KalaCart's pricing analyst. Suggest a fair price in INR for a handicraft
using: craft category, materials, artisan hours, complexity, and regional market data.
Output JSON: {suggested_price: number, price_range: {min, max}, justification: string,
factors: [string]}. Be fair to artisan — do not underprice handmade labor.
See ai-prompts/pricing_prompt.md.
"""


async def suggest_price(
    category: str,
    description: str,
    materials: list[str] | None = None,
    artisan_hours: float | None = None,
) -> dict:
    """
    Calls DeepSeek via OpenRouter to generate price suggestion.

    Returns:
        Dict with suggested_price, price_range, justification, factors
    """
    user_prompt = (
        f"Category: {category}\n"
        f"Description: {description}\n"
        f"Materials: {', '.join(materials or [])}\n"
        f"Artisan hours: {artisan_hours or 'unknown'}\n\n"
        "Suggest price JSON now."
    )

    content = await chat_completion(
        messages=[
            {"role": "system", "content": PRICING_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        model=DEEPSEEK_MODEL,
        temperature=0.5,
    )

    return {"raw": content}
