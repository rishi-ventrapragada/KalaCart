import uuid
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

from app.models.executive_brain import (
    ExecutiveInsightResponse,
    CashflowForecastResponse,
    RiskPredictionResponse,
    AIDecisionCreate,
    AIDecisionActionRequest,
    AIDecisionResponse,
    ExecutiveReportResponse
)
from app.ai.executive_brain_engine import executive_brain_engine

# In-memory runtime persistence
_INSIGHTS: Dict[str, Dict[str, Any]] = {}
_CASHFLOWS: Dict[str, Dict[str, Any]] = {}
_RISKS: Dict[str, Dict[str, Any]] = {}
_DECISIONS: Dict[str, Dict[str, Any]] = {}

# Pre-populate sample seed insights & decisions
_D1_ID = "dec-501"
_DECISIONS[_D1_ID] = {
    "id": _D1_ID,
    "artisan_id": "artisan_demo",
    "decision_type": "discount",
    "title": "Apply 15% Pre-Diwali Flash Discount on Blue Pottery Vases",
    "rationale": "Demand elasticities indicate a 15% promotional tag will drive a 40% surge in order conversions over the next 10 days.",
    "proposed_payload": {"product_id": "prod_blue_pottery_vase", "discount_percentage": 15.0, "duration_days": 7},
    "projected_revenue_lift": 18500.0,
    "projected_cost_savings": 0.0,
    "confidence_score": 92.5,
    "status": "suggested",
    "approved_at": None,
    "rejected_reason": None,
    "executed_at": None,
    "execution_result": None,
    "created_at": "2026-09-06T08:00:00Z"
}

_D2_ID = "dec-502"
_DECISIONS[_D2_ID] = {
    "id": _D2_ID,
    "artisan_id": "artisan_demo",
    "decision_type": "production",
    "title": "Queue 100-Unit Production Batch of Terracotta Pooja Sets",
    "rationale": "Historical stockout occurred 14 days before Diwali last year. Current stock is 12 units against forecasted demand of 85 units.",
    "proposed_payload": {"product_id": "prod_terracotta_tea_set", "target_quantity": 100, "priority": "high"},
    "projected_revenue_lift": 32000.0,
    "projected_cost_savings": 4200.0,
    "confidence_score": 95.0,
    "status": "suggested",
    "approved_at": None,
    "rejected_reason": None,
    "executed_at": None,
    "execution_result": None,
    "created_at": "2026-09-06T08:00:00Z"
}

_D3_ID = "dec-503"
_DECISIONS[_D3_ID] = {
    "id": _D3_ID,
    "artisan_id": "artisan_demo",
    "decision_type": "export",
    "title": "Launch Dhokra Craft Collection on Dubai (UAE) Export Storefront",
    "rationale": "UAE searches for handcrafted brass figurines spiked by 210% this quarter with zero tariff barriers under CEPA.",
    "proposed_payload": {"target_currency": "AED", "target_country": "AE", "product_category": "dhokra_metal"},
    "projected_revenue_lift": 58000.0,
    "projected_cost_savings": 0.0,
    "confidence_score": 88.0,
    "status": "suggested",
    "approved_at": None,
    "rejected_reason": None,
    "executed_at": None,
    "execution_result": None,
    "created_at": "2026-09-06T08:00:00Z"
}


class ExecutiveBrainService:

    def generate_executive_insights(self, artisan_id: str) -> List[ExecutiveInsightResponse]:
        now = datetime.now(timezone.utc).isoformat()
        rev_pred = executive_brain_engine.predict_revenue_and_demand([54000.0, 62000.0, 71000.0])
        fest_pred = executive_brain_engine.detect_festival_opportunities()

        # Insight 1: Revenue & Growth Forecast
        ins1_id = f"ins-{uuid.uuid4().hex[:6]}"
        ins1 = {
            "id": ins1_id,
            "artisan_id": artisan_id,
            "insight_type": "revenue_forecast",
            "title": f"Forecast: ₹{rev_pred['forecast_next_30d']:,} Expected Next 30 Days (+12% MoM)",
            "summary": "AI revenue models project steady acceleration driven by organic repeat buyer cohorts and early festival gifting.",
            "confidence_score": 91.5,
            "impact_level": "high",
            "metrics": rev_pred,
            "recommendations": ["Scale raw clay procurement by 20%", "Review B2B quotation response times"],
            "is_read": False,
            "created_at": now
        }
        _INSIGHTS[ins1_id] = ins1

        # Insight 2: Festival Opportunity
        ins2_id = f"ins-{uuid.uuid4().hex[:6]}"
        ins2 = {
            "id": ins2_id,
            "artisan_id": artisan_id,
            "insight_type": "festival_opportunity",
            "title": f"Diwali Surge Window Opening ({fest_pred['days_until']} Days Remaining)",
            "summary": "Festive demand surge of +65% projected for brassware, diyas, and festive gift boxes.",
            "confidence_score": 94.0,
            "impact_level": "critical",
            "metrics": fest_pred,
            "recommendations": ["Publish festive bundles by Sep 15", "Run WhatsApp marketing campaign"],
            "is_read": False,
            "created_at": now
        }
        _INSIGHTS[ins2_id] = ins2

        return [ExecutiveInsightResponse(**i) for i in _INSIGHTS.values() if i["artisan_id"] == artisan_id]

    def get_cashflow_forecast(self, artisan_id: str) -> CashflowForecastResponse:
        forecast_data = executive_brain_engine.predict_cashflow_runway(
            projected_inflows=85000.0,
            material_burn=22000.0,
            labour_burn=18000.0,
            logistics_burn=6500.0,
            cash_balance=145000.0
        )
        rec_id = f"cash-{uuid.uuid4().hex[:6]}"
        now = datetime.now(timezone.utc).isoformat()
        rec = {
            "id": rec_id,
            "artisan_id": artisan_id,
            **forecast_data,
            "generated_at": now
        }
        _CASHFLOWS[rec_id] = rec
        return CashflowForecastResponse(**rec)

    def get_risk_predictions(self, artisan_id: str) -> List[RiskPredictionResponse]:
        items = [
            {"product_id": "prod_terracotta_tea_set", "name": "Terracotta Tea Set", "stock": 6, "daily_velocity": 2.0},
            {"product_id": "prod_blue_pottery_vase", "name": "Blue Pottery Floral Vase", "stock": 25, "daily_velocity": 1.2}
        ]
        risks = executive_brain_engine.evaluate_risk_predictions(items, active_orders=14)
        out = []
        for r in risks:
            r_id = f"risk-{uuid.uuid4().hex[:6]}"
            r_record = {
                "id": r_id,
                "artisan_id": artisan_id,
                **r,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            _RISKS[r_id] = r_record
            out.append(RiskPredictionResponse(**r_record))
        return out

    def list_ai_decisions(self, artisan_id: str) -> List[AIDecisionResponse]:
        return [AIDecisionResponse(**d) for d in _DECISIONS.values() if d["artisan_id"] == artisan_id]

    def create_ai_decision(self, artisan_id: str, payload: AIDecisionCreate) -> AIDecisionResponse:
        dec_id = f"dec-{uuid.uuid4().hex[:6]}"
        now = datetime.now(timezone.utc).isoformat()
        decision = {
            "id": dec_id,
            "artisan_id": artisan_id,
            "decision_type": payload.decision_type,
            "title": payload.title,
            "rationale": payload.rationale,
            "proposed_payload": payload.proposed_payload,
            "projected_revenue_lift": payload.projected_revenue_lift,
            "projected_cost_savings": payload.projected_cost_savings,
            "confidence_score": payload.confidence_score,
            "status": "suggested",
            "approved_at": None,
            "rejected_reason": None,
            "executed_at": None,
            "execution_result": None,
            "created_at": now
        }
        _DECISIONS[dec_id] = decision
        return AIDecisionResponse(**decision)

    def act_on_decision(self, decision_id: str, payload: AIDecisionActionRequest) -> Optional[AIDecisionResponse]:
        decision = _DECISIONS.get(decision_id)
        if not decision:
            return None

        now = datetime.now(timezone.utc).isoformat()
        if payload.action == "approve":
            decision["status"] = "approved"
            decision["approved_at"] = now
        elif payload.action == "reject":
            decision["status"] = "rejected"
            decision["rejected_reason"] = payload.rejected_reason or "Artisan declined proposal."
        elif payload.action == "execute":
            if decision["status"] != "approved":
                decision["status"] = "approved"
                decision["approved_at"] = now
            decision["status"] = "executed"
            decision["executed_at"] = now
            decision["execution_result"] = {
                "success": True,
                "action_type": decision["decision_type"],
                "executed_payload": decision["proposed_payload"],
                "system_message": "AI Autonomous action executed successfully with artisan approval authorization."
            }

        return AIDecisionResponse(**decision)

    def generate_executive_report(self, artisan_id: str, report_type: str = "weekly") -> ExecutiveReportResponse:
        now = datetime.now(timezone.utc).isoformat()
        pending_decisions = len([d for d in _DECISIONS.values() if d["artisan_id"] == artisan_id and d["status"] == "suggested"])

        return ExecutiveReportResponse(
            artisan_id=artisan_id,
            report_type=report_type,
            generated_at=now,
            revenue_forecast={
                "projected_monthly": 79500.0,
                "confidence": 91.5,
                "trend": "+14.8% vs last month"
            },
            cashflow_summary={
                "net_working_capital": 38500.0,
                "runway_days": 115,
                "status": "healthy_surplus"
            },
            top_growth_opportunities=[
                "Diwali gift hamper packaging & pre-orders",
                "Expand Dhokra collection to UAE cross-border marketplace",
                "Restock terracotta glaze to avoid 4-day stockout"
            ],
            critical_risks=[
                "Stockout risk on Terracotta Tea Sets (3 days of stock remaining)",
                "B2B repeat order cadence dropped for 3 corporate clients"
            ],
            pending_ai_decisions_count=pending_decisions,
            download_pdf_url=f"https://storage.kalacart.in/reports/executive_{report_type}_{artisan_id}_{datetime.now(timezone.utc).strftime('%Y%m%d')}.pdf"
        )


executive_brain_service = ExecutiveBrainService()
