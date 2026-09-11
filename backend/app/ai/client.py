"""
OpenRouter client wrapper for Qwen 3 and DeepSeek models.
All AI calls go through OpenRouter for unified billing + fallback.
"""

import os
import httpx
from typing import List, Dict, Any

OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

QWEN_MODEL = os.getenv("QWEN_MODEL", "qwen/qwen3-32b")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek/deepseek-chat")


async def chat_completion(
    messages: List[Dict[str, str]],
    model: str = QWEN_MODEL,
    temperature: float = 0.7,
    max_tokens: int = 1024,
) -> str:
    """
    Calls OpenRouter chat completions endpoint.

    Args:
        messages: List of {"role": "system"|"user"|"assistant", "content": str}
        model: OpenRouter model slug
        temperature: Sampling temperature
        max_tokens: Max tokens to generate

    Returns:
        Assistant message content as string

    Raises:
        httpx.HTTPError on failure
    """
    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY not set")

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "https://kalacart.in",
        "X-Title": "KalaCart",
        "Content-Type": "application/json",
    }

    payload: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            f"{OPENROUTER_BASE_URL}/chat/completions",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
