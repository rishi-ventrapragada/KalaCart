"""
Global Trade Intelligence API Router (KalaCart V10)
Exposes international demand analytics, live foreign exchange rates,
world trade heatmaps, and country export recommendations.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

from app.core.global_trade import (
    global_trade_engine,
    ExchangeRate,
    CountryTradeOpportunity,
)

router = APIRouter(prefix="/api/v1/trade-intelligence", tags=["Global Trade Intelligence (V10)"])


class UpdateExchangeRateRequest(BaseModel):
    currency_code: str
    exchange_rate_to_inr: float
    trend_24h_pct: float = 0.0


@router.get("/exchange-rates")
async def get_live_exchange_rates():
    """Retrieve live multi-currency foreign exchange rates against INR."""
    return global_trade_engine.get_exchange_rates()


@router.post("/exchange-rates/update")
async def update_exchange_rate(req: UpdateExchangeRateRequest):
    """Update a foreign currency conversion rate."""
    updated = global_trade_engine.update_exchange_rate(
        currency_code=req.currency_code,
        new_rate_to_inr=req.exchange_rate_to_inr,
        trend_24h=req.trend_24h_pct,
    )
    if not updated:
        raise HTTPException(status_code=404, detail=f"Currency code '{req.currency_code}' not found.")
    return {
        "status": "success",
        "rate": updated.model_dump(),
    }


@router.get("/recommendations")
async def get_export_recommendations(
    craft_category: Optional[str] = Query(None, description="Filter by craft category e.g. Silk, Brass, Pashmina")
):
    """Get AI-ranked export target country recommendations and market attractiveness scores."""
    recs = global_trade_engine.get_country_trade_recommendations(craft_category=craft_category)
    return {
        "count": len(recs),
        "recommendations": recs,
    }


@router.get("/heatmap")
async def get_trade_heatmap():
    """Retrieve geo-spatial trade volume and opportunity intensity data for interactive world map."""
    return global_trade_engine.get_world_trade_heatmap()


@router.get("/countries/{country_code}/trends")
async def get_country_trend_data(country_code: str):
    """Retrieve historical buyer inquiry volume and export GMV trends for a target country."""
    c_code = country_code.upper()
    trends = global_trade_engine.trends.get(c_code, [])
    return {
        "country_code": c_code,
        "monthly_trends": [t.model_dump() for t in trends],
    }
