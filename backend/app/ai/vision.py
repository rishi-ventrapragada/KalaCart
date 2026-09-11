"""
Product attribute extraction for pricing — reads the product photo and the seller's
description with an image-capable model on OpenRouter (VISION_MODEL).

Returns normalized attributes the pricing engine can use directly: category, materials,
size, quality, craftsmanship complexity, estimated labour hours and a short observation.
Never logs the API key.
"""

import base64
import json
import logging
import re
from typing import Any, Dict, List, Optional

import cv2
import httpx
import numpy as np
from fastapi import HTTPException, status

from app.core.config import get_settings
from app.services.pricing_engine import CATEGORIES, QUALITIES, SIZES

logger = logging.getLogger(__name__)

# Longest edge sent to the model — enough to judge material and finish, far fewer image tokens
MAX_IMAGE_EDGE = 768

SYSTEM_PROMPT = (
    "You are a handicraft appraiser for KalaCart, an Indian artisan marketplace. From the product photo "
    "(if provided) and the seller's description, extract the attributes that drive a fair price.\n"
    "Return JSON only, no markdown, with exactly these keys:\n"
    '{"category": one of ' + json.dumps(CATEGORIES) + ", "
    '"materials": [1-5 materials that are visible or stated — never invent], '
    '"size": "Small" | "Medium" | "Large", '
    '"quality": "Basic" | "Standard" | "Premium" (finish and workmanship), '
    '"complexity": integer 1-5 (1 = simple, 5 = intricate, highly detailed handwork), '
    '"estimated_labour_hours": number of hours a skilled artisan needs to make one piece, '
    '"observations": one short sentence on what justifies the price (technique, detail, finish)}'
)


def image_data_url(image_bytes: bytes) -> str:
    """Decode, downscale to MAX_IMAGE_EDGE and re-encode as a JPEG data URL. Raises ValueError if not an image."""
    img = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Invalid image file — unable to decode as JPEG/PNG/WebP")
    h, w = img.shape[:2]
    scale = min(1.0, MAX_IMAGE_EDGE / float(max(h, w)))
    if scale < 1.0:
        img = cv2.resize(img, (max(1, int(w * scale)), max(1, int(h * scale))), interpolation=cv2.INTER_AREA)
    ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 85])
    if not ok:
        raise ValueError("Could not encode image")
    return "data:image/jpeg;base64," + base64.b64encode(buf.tobytes()).decode("ascii")


def _parse_json(text: str) -> Dict[str, Any]:
    t = (text or "").strip()
    t = re.sub(r"^```(?:json)?\s*|\s*```$", "", t, flags=re.IGNORECASE).strip()
    start, end = t.find("{"), t.rfind("}")
    if start == -1 or end <= start:
        raise ValueError("no JSON object in model output")
    data = json.loads(t[start : end + 1])
    if not isinstance(data, dict):
        raise ValueError("model output is not a JSON object")
    return data


def normalize_attributes(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Coerce model output into valid engine inputs; unknown or missing values fall back to neutral defaults."""

    def pick(value: Any, allowed: List[str], default: str) -> str:
        match = next((a for a in allowed if isinstance(value, str) and value.strip().lower() == a.lower()), None)
        return match or default

    materials = []
    for m in raw.get("materials") or []:
        if isinstance(m, str) and m.strip() and m.strip().title() not in materials:
            materials.append(m.strip().title()[:40])
    try:
        complexity = int(round(float(raw.get("complexity"))))
    except (TypeError, ValueError):
        complexity = 3
    try:
        hours: Optional[float] = float(raw.get("estimated_labour_hours"))
        hours = round(min(200.0, max(0.5, hours)), 1)
    except (TypeError, ValueError):
        hours = None
    observations = raw.get("observations")

    return {
        "category": pick(raw.get("category"), CATEGORIES, "Other"),
        "materials": materials[:5],
        "size": pick(raw.get("size"), SIZES, "Medium"),
        "quality": pick(raw.get("quality"), QUALITIES, "Standard"),
        "complexity": min(5, max(1, complexity)),
        "estimated_labour_hours": hours,
        "observations": observations.strip()[:240] if isinstance(observations, str) else "",
    }


async def extract_product_attributes(description: str, image_bytes: Optional[bytes] = None) -> Dict[str, Any]:
    """
    Extract pricing attributes from the description and (optionally) the product photo.

    Raises HTTPException 400 for an undecodable image, 500 if not configured, 502/504 on
    upstream failure or unparseable output (after one retry).
    """
    settings = get_settings()
    api_key = settings.OPENROUTER_API_KEY
    if not api_key:
        logger.error("OPENROUTER_API_KEY not configured")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI service not configured (missing API key)",
        )

    content: List[Dict[str, Any]] = [{"type": "text", "text": f"Seller description: {description}"}]
    if image_bytes:
        try:
            content.append({"type": "image_url", "image_url": {"url": image_data_url(image_bytes)}})
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    body = {
        "model": settings.VISION_MODEL,
        "messages": [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": content}],
        "temperature": 0.2,
        "max_tokens": 400,
        "reasoning": {"enabled": False},
        # Without JSON mode the model reliably emitted a malformed key when given a photo
        "response_format": {"type": "json_object"},
    }
    url = f"{settings.OPENROUTER_BASE_URL.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://kalacart.in",
        "X-Title": "KalaCart",
        "Content-Type": "application/json",
    }

    last_error = ""
    async with httpx.AsyncClient(timeout=45) as client:
        for attempt in (1, 2):
            try:
                resp = await client.post(url, headers=headers, json=body)
            except httpx.TimeoutException as exc:
                logger.error("Vision model timed out (attempt %d)", attempt)
                raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail="AI service timed out") from exc
            except httpx.RequestError as exc:
                logger.error("Vision model request error: %s", type(exc).__name__)
                raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="AI service unavailable") from exc
            if resp.status_code != 200:
                logger.error("Vision model HTTP %s for model %s", resp.status_code, settings.VISION_MODEL)
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="AI service temporarily unavailable (upstream error)",
                )
            try:
                text = resp.json()["choices"][0]["message"]["content"]
                return normalize_attributes(_parse_json(text))
            except (KeyError, IndexError, TypeError, ValueError) as exc:
                last_error = str(exc)
                logger.warning("Vision model output unusable (attempt %d): %s", attempt, exc)

    raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"AI returned unusable product attributes ({last_error})")
