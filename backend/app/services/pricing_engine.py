"""
Dynamic pricing engine — turns product attributes into a fair, explainable INR price.

The price is computed, not generated. A vision model only extracts attributes (category,
materials, size, quality, craftsmanship complexity, labour estimate); from those:

  cost-based price = (materials + labour) x (1 + overhead) x (1 + margin)
  market band      = prices of comparable active KalaCart listings in the category
                     (when there are at least MIN_COMPARABLES), otherwise reference retail
                     ranges for Indian handicrafts, scaled by size
  seasonal factor  = festival / wedding-season demand windows by month and category
  suggested price  = cost-based price blended with the market target for the seller's
                     positioning, times the seasonal factor — never below the cost floor

Every factor is returned so the seller can see why a price was suggested.
"""

from __future__ import annotations

import statistics
from datetime import date
from typing import Any, Dict, List, Optional, Tuple

CATEGORIES = ["Textiles", "Pottery", "Woodwork", "Metalwork", "Jewelry", "Painting", "Basketry", "Leather", "Other"]
SIZES = ["Small", "Medium", "Large"]
QUALITIES = ["Basic", "Standard", "Premium"]
MARKET_POSITIONS = ["Budget", "Standard", "Premium"]

SIZE_FACTORS = {"Small": 0.6, "Medium": 1.0, "Large": 1.8}

# Reference retail ranges (INR) for a medium-sized handmade piece — used only while the
# marketplace has too few comparable listings of its own
REFERENCE_BANDS: Dict[str, Tuple[int, int]] = {
    "Textiles": (600, 1800),
    "Pottery": (450, 1500),
    "Woodwork": (800, 2500),
    "Metalwork": (750, 2200),
    "Jewelry": (900, 3200),
    "Painting": (1200, 4500),
    "Basketry": (350, 1100),
    "Leather": (700, 2400),
    "Other": (500, 1500),
}

# Artisan labour rate (INR/hour) by finish quality, adjusted by craftsmanship complexity 1-5
LABOUR_RATES = {"Basic": 55.0, "Standard": 82.0, "Premium": 115.0}
COMPLEXITY_RATE_FACTOR = {1: 0.85, 2: 0.95, 3: 1.0, 4: 1.12, 5: 1.25}
DEFAULT_LABOUR_HOURS = {"Small": 3.0, "Medium": 8.0, "Large": 20.0}

OVERHEAD = {"Budget": 0.15, "Standard": 0.20, "Premium": 0.25}
MARGIN = {"Budget": 0.20, "Standard": 0.25, "Premium": 0.30}
# Where in the market band each positioning aims: 0 = low end, 1 = high end
BAND_TARGET = {"Budget": 0.25, "Standard": 0.5, "Premium": 0.8}

# Materials are typically ~30% of a handicraft's retail price — used only when the seller gives no cost
TYPICAL_MATERIAL_SHARE = 0.30
# The artisan's cost plus at least this markup is the hard price floor
COST_FLOOR_MARKUP = 0.10
MIN_COMPARABLES = 5

# (months, categories, demand factor, label) — approximate Indian festival and wedding windows
SEASONS = [
    ({10, 11}, {"Pottery", "Textiles", "Metalwork", "Painting", "Jewelry"}, 1.15, "Diwali & Dussehra festive demand"),
    ({11, 12, 1, 2}, {"Textiles", "Jewelry", "Metalwork"}, 1.10, "Wedding season demand"),
    ({8}, {"Jewelry", "Textiles"}, 1.05, "Raksha Bandhan & Onam gifting demand"),
    ({3}, {"Textiles"}, 1.05, "Holi season demand"),
]


def round_price(value: float) -> int:
    """Round to the nearest ₹10."""
    return int(round(value / 10.0)) * 10


def seasonal_factor(category: str, today: date) -> Tuple[float, str]:
    """Strongest demand window active for the category this month, or (1.0, reason) if none."""
    factor, label = 1.0, "No festival demand window for this category this month"
    for months, categories, season_factor, season_label in SEASONS:
        if today.month in months and category in categories and season_factor > factor:
            factor, label = season_factor, season_label
    return factor, label


def market_band(category: str, size: str, comparable_prices: List[float]) -> Dict[str, Any]:
    """Price band from comparable listings, or reference ranges when there aren't enough."""
    prices = sorted(float(p) for p in comparable_prices if isinstance(p, (int, float)) and p > 0)
    if len(prices) >= MIN_COMPARABLES:
        quartiles = statistics.quantiles(prices, n=4)
        return {
            "source": "marketplace_listings",
            "comparables": len(prices),
            "low": round_price(quartiles[0]),
            "median": round_price(statistics.median(prices)),
            "high": round_price(quartiles[2]),
        }
    low, high = REFERENCE_BANDS.get(category, REFERENCE_BANDS["Other"])
    scale = SIZE_FACTORS.get(size, 1.0)
    return {
        "source": "reference_ranges",
        "comparables": len(prices),
        "low": round_price(low * scale),
        "median": round_price((low + high) / 2 * scale),
        "high": round_price(high * scale),
    }


def compute_price(
    *,
    category: str,
    size: str,
    quality: str,
    complexity: int,
    market_position: str,
    labour_hours: float,
    material_cost: Optional[float],
    comparable_prices: List[float],
    today: date,
    labour_hours_estimated: bool = False,
    image_analyzed: bool = False,
) -> Dict[str, Any]:
    """
    Compute suggested / minimum / maximum INR price with breakdown, market band, seasonal factor,
    confidence and human-readable factors.
    """
    category = category if category in CATEGORIES else "Other"
    size = size if size in SIZES else "Medium"
    quality = quality if quality in QUALITIES else "Standard"
    market_position = market_position if market_position in MARKET_POSITIONS else "Standard"
    complexity = int(min(5, max(1, complexity)))

    band = market_band(category, size, comparable_prices)
    estimated: List[str] = []
    if material_cost is None:
        material_cost = band["median"] * TYPICAL_MATERIAL_SHARE
        estimated.append("material_cost")
    if labour_hours_estimated:
        estimated.append("labour_hours")

    rate = LABOUR_RATES[quality] * COMPLEXITY_RATE_FACTOR[complexity]
    labour = labour_hours * rate
    base_cost = material_cost + labour
    overhead = base_cost * OVERHEAD[market_position]
    cost_based = (base_cost + overhead) * (1 + MARGIN[market_position])
    floor = base_cost * (1 + COST_FLOOR_MARKUP)

    # Blend what the piece costs to make with what the market pays for this positioning,
    # kept near the market band unless costs demand more
    target = band["low"] + (band["high"] - band["low"]) * BAND_TARGET[market_position]
    blended = min(max(0.5 * cost_based + 0.5 * target, band["low"] * 0.9), band["high"] * 1.25)
    season, season_label = seasonal_factor(category, today)
    raised_to_floor = blended * season < floor

    # Round to ₹10, but round the cost floor *up* so rounding never prices below cost
    floor_price = int(-(-floor // 10)) * 10
    suggested = max(round_price(blended * season), floor_price)
    minimum = min(max(floor_price, round_price(suggested * 0.85)), suggested)
    maximum = round_price(suggested * 1.2)

    # Breakdown sums to the suggested price; overhead gives way first when the market caps the margin
    remaining = suggested - material_cost - labour
    overhead_share = min(overhead, max(0.0, remaining))
    breakdown = {
        "materials": round(material_cost, 2),
        "labour": round(labour, 2),
        "overhead": round(overhead_share, 2),
        "profit": round(max(0.0, remaining - overhead_share), 2),
    }

    confidence = 45
    confidence += 20 if band["source"] == "marketplace_listings" else 5
    confidence += 0 if "material_cost" in estimated else 15
    confidence += 0 if "labour_hours" in estimated else 10
    confidence += 5 if image_analyzed else 0

    factors = [
        f"Materials ₹{round(material_cost)}"
        + (" (estimated — enter your actual material cost for a better price)" if "material_cost" in estimated else " (your cost)"),
        f"Labour {labour_hours:g} h × ₹{round(rate)}/h ({quality.lower()} finish, complexity {complexity}/5)"
        + (" — hours estimated from the photo and description" if "labour_hours" in estimated else ""),
        f"{market_position} positioning: {round(OVERHEAD[market_position] * 100)}% overhead + "
        f"{round(MARGIN[market_position] * 100)}% margin → cost-based ₹{round_price(cost_based)}",
    ]
    if band["source"] == "marketplace_listings":
        factors.append(
            f"{band['comparables']} comparable {category.lower()} listings on KalaCart sell for "
            f"₹{band['low']}–₹{band['high']} (median ₹{band['median']})"
        )
    else:
        factors.append(
            f"Typical retail range for a {size.lower()} {category.lower()} piece: ₹{band['low']}–₹{band['high']} "
            "(reference data — not enough KalaCart listings in this category yet)"
        )
    factors.append(season_label + (f" (+{round((season - 1) * 100)}%)" if season > 1 else ""))
    if raised_to_floor:
        factors.append("Raised to cover your costs — typical prices are below what this piece costs to make")

    reasoning = (
        f"Suggested ₹{suggested}: making it costs about ₹{round(base_cost)} in materials and labour, and similar "
        f"{category.lower()} pieces sell for ₹{band['low']}–₹{band['high']}."
    )
    if season > 1:
        reasoning += f" Includes a {round((season - 1) * 100)}% seasonal lift for {season_label.lower()}."

    return {
        "suggested_price": suggested,
        "minimum_price": minimum,
        "maximum_price": maximum,
        "currency": "INR",
        "confidence": min(95, confidence),
        "breakdown": breakdown,
        "market": band,
        "seasonal": {"factor": season, "reason": season_label},
        "estimated_inputs": estimated,
        "factors": factors,
        "reasoning": reasoning,
    }
