"""
Global Trade Intelligence Core Engine (KalaCart V10)
Provides real-time international trade intelligence, foreign currency exchange rates,
predictive cross-border demand analytics, HS code trade flows, seasonal export surge calendars,
competitor region benchmarking, and automated country recommendations for artisan cooperatives.
"""

import uuid
import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class ExchangeRate(BaseModel):
    currency_code: str
    currency_name: str
    symbol: str
    exchange_rate_to_inr: float  # 1 Foreign Unit = X INR
    trend_24h_pct: float = 0.0
    last_updated_at: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())


class CountryTradeOpportunity(BaseModel):
    destination_country_code: str
    country_name: str
    craft_category: str
    hs_code: str
    annual_import_volume_usd: float
    yoy_growth_pct: float
    average_tariff_pct: float
    peak_demand_season: str
    competitor_countries: List[str]
    market_attractiveness_score: float  # 0 - 100
    export_readiness_recommendation: str


class MonthlyTrend(BaseModel):
    country_code: str
    year: int
    month: int
    craft_category: str
    search_interest_index: float  # 0 - 100
    buyer_inquiries_count: int
    gmv_exported_inr: float


class GlobalTradeIntelligenceEngine:
    """
    Analyzes global trade corridors, currency arbitrage opportunities,
    and predicts optimal export destinations for Indian GI handicrafts.
    """

    def __init__(self):
        self.exchange_rates: Dict[str, ExchangeRate] = {}
        self.trade_opportunities: Dict[str, CountryTradeOpportunity] = {}  # key: country_code:hs_code
        self.trends: Dict[str, List[MonthlyTrend]] = {}  # country_code -> trends
        self._seed_default_trade_data()

    def _seed_default_trade_data(self):
        # 1. Foreign Exchange Rates
        rates = [
            ExchangeRate(currency_code="USD", currency_name="US Dollar", symbol="$", exchange_rate_to_inr=83.50, trend_24h_pct=0.12),
            ExchangeRate(currency_code="EUR", currency_name="Euro", symbol="€", exchange_rate_to_inr=90.20, trend_24h_pct=-0.05),
            ExchangeRate(currency_code="GBP", currency_name="British Pound", symbol="£", exchange_rate_to_inr=105.80, trend_24h_pct=0.25),
            ExchangeRate(currency_code="AED", currency_name="UAE Dirham", symbol="AED", exchange_rate_to_inr=22.75, trend_24h_pct=0.01),
            ExchangeRate(currency_code="JPY", currency_name="Japanese Yen", symbol="¥", exchange_rate_to_inr=0.55, trend_24h_pct=-0.30),
            ExchangeRate(currency_code="AUD", currency_name="Australian Dollar", symbol="A$", exchange_rate_to_inr=54.60, trend_24h_pct=0.18),
        ]
        for r in rates:
            self.exchange_rates[r.currency_code] = r

        # 2. Global Trade Corridors
        corridors = [
            CountryTradeOpportunity(
                destination_country_code="US",
                country_name="United States",
                craft_category="Handloom Silk & Textiles",
                hs_code="5007.20.00",
                annual_import_volume_usd=450000000.0,
                yoy_growth_pct=14.5,
                average_tariff_pct=3.2,
                peak_demand_season="Q4_HOLIDAY",
                competitor_countries=["Vietnam", "China", "Italy"],
                market_attractiveness_score=94.5,
                export_readiness_recommendation="High demand for authentic Varanasi & Pochampally pure silk sarees in corporate gifting and luxury bridal boutiques.",
            ),
            CountryTradeOpportunity(
                destination_country_code="DE",
                country_name="Germany",
                craft_category="Brass Metalware & Bell Metal",
                hs_code="7419.80.00",
                annual_import_volume_usd=185000000.0,
                yoy_growth_pct=8.2,
                average_tariff_pct=2.5,
                peak_demand_season="SPRING_HOME_DECOR",
                competitor_countries=["Morocco", "Turkey", "China"],
                market_attractiveness_score=88.0,
                export_readiness_recommendation="Strong eco-conscious demand for Moradabad brass planter vessels and Bidriware tableware with lead-free certification.",
            ),
            CountryTradeOpportunity(
                destination_country_code="AE",
                country_name="United Arab Emirates",
                craft_category="Pashmina & Royal Cashmere",
                hs_code="6214.20.00",
                annual_import_volume_usd=280000000.0,
                yoy_growth_pct=22.0,
                average_tariff_pct=0.0,  # CEPA Zero Duty
                peak_demand_season="DIWALI_EXPAT_AND_RAMADAN",
                competitor_countries=["Iran", "Turkey"],
                market_attractiveness_score=96.0,
                export_readiness_recommendation="Zero-duty CEPA corridor; exceptional demand for authentic GI Kashmir Pashmina with microchip authenticity tags.",
            ),
            CountryTradeOpportunity(
                destination_country_code="GB",
                country_name="United Kingdom",
                craft_category="Channapatna Eco Wooden Toys",
                hs_code="9503.00.10",
                annual_import_volume_usd=92000000.0,
                yoy_growth_pct=18.4,
                average_tariff_pct=2.0,
                peak_demand_season="Q4_HOLIDAY",
                competitor_countries=["Germany", "China"],
                market_attractiveness_score=91.0,
                export_readiness_recommendation="Enormous growth in Montessori schools and organic toy retailers seeking non-toxic vegetable lacquered Channapatna kits.",
            ),
        ]
        for c in corridors:
            key = f"{c.destination_country_code}:{c.hs_code}"
            self.trade_opportunities[key] = c

        # 3. Monthly Trends
        now = datetime.datetime.now(datetime.timezone.utc)
        self.trends["US"] = [
            MonthlyTrend(
                country_code="US",
                year=now.year,
                month=now.month,
                craft_category="Handloom Silk & Textiles",
                search_interest_index=88.5,
                buyer_inquiries_count=340,
                gmv_exported_inr=14500000.0,
            )
        ]
        self.trends["AE"] = [
            MonthlyTrend(
                country_code="AE",
                year=now.year,
                month=now.month,
                craft_category="Pashmina & Royal Cashmere",
                search_interest_index=94.0,
                buyer_inquiries_count=520,
                gmv_exported_inr=28400000.0,
            )
        ]

    def get_exchange_rates(self) -> Dict[str, Any]:
        """Returns live multi-currency foreign exchange rates against INR."""
        rates_list = [r.model_dump() for r in self.exchange_rates.values()]
        return {
            "base_currency": "INR",
            "count": len(rates_list),
            "rates": rates_list,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }

    def update_exchange_rate(self, currency_code: str, new_rate_to_inr: float, trend_24h: float = 0.0) -> Optional[ExchangeRate]:
        """Updates a foreign currency exchange rate."""
        rate = self.exchange_rates.get(currency_code.upper())
        if not rate:
            return None
        rate.exchange_rate_to_inr = new_rate_to_inr
        rate.trend_24h_pct = trend_24h
        rate.last_updated_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
        return rate

    def get_country_trade_recommendations(self, craft_category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Ranks top international export target countries based on import volume,
        YoY growth, tariff rates, and market attractiveness scores.
        """
        opps = list(self.trade_opportunities.values())
        if craft_category:
            opps = [o for o in opps if craft_category.lower() in o.craft_category.lower()]

        # Sort by market attractiveness score descending
        sorted_opps = sorted(opps, key=lambda x: x.market_attractiveness_score, reverse=True)
        return [o.model_dump() for o in sorted_opps]

    def get_world_trade_heatmap(self) -> Dict[str, Any]:
        """
        Generates geo-spatial trade volume and opportunity intensity data
        for the interactive global export map dashboard.
        """
        country_heat: Dict[str, Dict[str, Any]] = {}
        for opp in self.trade_opportunities.values():
            code = opp.destination_country_code
            if code not in country_heat:
                country_heat[code] = {
                    "country_code": code,
                    "country_name": opp.country_name,
                    "total_import_volume_usd": 0.0,
                    "average_score": 0.0,
                    "top_categories": [],
                    "peak_season": opp.peak_demand_season,
                    "free_trade_agreement": opp.average_tariff_pct == 0.0,
                }
            country_heat[code]["total_import_volume_usd"] += opp.annual_import_volume_usd
            country_heat[code]["average_score"] = opp.market_attractiveness_score
            country_heat[code]["top_categories"].append(opp.craft_category)

        return {
            "total_countries_tracked": len(country_heat),
            "heatmap_data": country_heat,
            "top_export_corridor": "India -> UAE (CEPA Zero Duty)",
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }


# Global Singleton Engine Instance
global_trade_engine = GlobalTradeIntelligenceEngine()
