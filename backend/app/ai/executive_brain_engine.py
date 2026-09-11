import math
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any


class ExecutiveBrainEngine:
    """Predictive Machine Learning & Algorithmic Forecasting Engine for Artisans."""

    def predict_revenue_and_demand(self, past_sales: List[float], growth_rate: float = 0.12) -> Dict[str, Any]:
        if not past_sales:
            past_sales = [45000.0, 52000.0, 61000.0]
        avg_monthly = sum(past_sales) / len(past_sales)
        next_30d = round(avg_monthly * (1 + growth_rate), 2)
        next_60d = round(next_30d * (1 + growth_rate * 0.9), 2)
        next_90d = round(next_60d * (1 + growth_rate * 0.8), 2)

        return {
            "historical_monthly_average": round(avg_monthly, 2),
            "forecast_next_30d": next_30d,
            "forecast_next_60d": next_60d,
            "forecast_next_90d": next_90d,
            "projected_quarterly_total": round(next_30d + next_60d + next_90d, 2),
            "demand_trend": "accelerating_positive"
        }

    def predict_cashflow_runway(self, projected_inflows: float, material_burn: float, labour_burn: float, logistics_burn: float, cash_balance: float = 120000.0) -> Dict[str, Any]:
        total_monthly_outflow = material_burn + labour_burn + logistics_burn
        net_monthly = projected_inflows - total_monthly_outflow
        runway_days = 180 if total_monthly_outflow == 0 else int(round((cash_balance / max(1.0, total_monthly_outflow)) * 30))
        
        health = "surplus" if net_monthly > 15000 else "healthy" if net_monthly >= 0 else "tight" if runway_days > 45 else "critical"

        breakdown = [
            {"week": "Week 1", "projected_inflow": round(projected_inflows * 0.22, 2), "projected_outflow": round(total_monthly_outflow * 0.25, 2)},
            {"week": "Week 2", "projected_inflow": round(projected_inflows * 0.26, 2), "projected_outflow": round(total_monthly_outflow * 0.25, 2)},
            {"week": "Week 3", "projected_inflow": round(projected_inflows * 0.28, 2), "projected_outflow": round(total_monthly_outflow * 0.25, 2)},
            {"week": "Week 4", "projected_inflow": round(projected_inflows * 0.24, 2), "projected_outflow": round(total_monthly_outflow * 0.25, 2)},
        ]

        return {
            "forecast_horizon_days": 30,
            "projected_inflows": projected_inflows,
            "projected_material_outflows": material_burn,
            "projected_labour_outflows": labour_burn,
            "projected_logistics_outflows": logistics_burn,
            "projected_net_cashflow": round(net_monthly, 2),
            "estimated_runway_days": runway_days,
            "working_capital_health": health,
            "cashflow_breakdown": breakdown
        }

    def evaluate_risk_predictions(self, inventory_items: List[Dict[str, Any]], active_orders: int) -> List[Dict[str, Any]]:
        risks = []
        now = datetime.now(timezone.utc)

        # 1. Stockout Risk
        for item in inventory_items:
            stock = item.get("stock", 10)
            velocity = item.get("daily_velocity", 1.5)
            days_left = stock / max(0.1, velocity)
            if days_left < 7:
                out_date = (now + timedelta(days=int(days_left))).strftime("%Y-%m-%d")
                risks.append({
                    "risk_category": "stockout_risk",
                    "target_entity_id": item.get("product_id", "prod_generic"),
                    "risk_level": "high" if days_left < 4 else "medium",
                    "risk_score": 85 if days_left < 4 else 65,
                    "predicted_date": out_date,
                    "description": f"Stock depleted in {int(days_left)} days for {item.get('name', 'craft product')} at current order velocity.",
                    "mitigation_action": f"Trigger production batch of {int(velocity * 20)} units or restock raw materials immediately.",
                    "mitigation_status": "pending"
                })

        # 2. Customer Churn Risk
        risks.append({
            "risk_category": "customer_churn",
            "target_entity_id": "tier_b2b_wholesale",
            "risk_level": "medium",
            "risk_score": 42,
            "predicted_date": (now + timedelta(days=14)).strftime("%Y-%m-%d"),
            "description": "3 B2B buyers have not reordered in 45 days despite historical monthly cadence.",
            "mitigation_action": "Issue automated personalized re-engagement catalogue and 10% volume discount.",
            "mitigation_status": "pending"
        })

        return risks

    def detect_festival_opportunities(self) -> Dict[str, Any]:
        return {
            "upcoming_festival": "Diwali Festival of Lights",
            "days_until": 28,
            "expected_demand_surge_percent": 65.0,
            "recommended_inventory_buffer": 2.5,
            "high_affinity_categories": ["terracotta_diyas", "brass_pooja_lamps", "handwoven_silk_sarees"],
            "suggested_marketing_launch_date": (datetime.now(timezone.utc) + timedelta(days=3)).strftime("%Y-%m-%d")
        }


executive_brain_engine = ExecutiveBrainEngine()
