import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.ai.digital_twin_engine import digital_twin_ai_engine
from app.models.digital_twin import (
    DigitalTwinBaseline,
    OperationalParameters,
    DigitalTwinResponse,
    DigitalTwinUpdate,
    SimulationRunRequest,
    SimulationResultResponse,
    SimulationRunSummary,
    SimulationComparisonResponse,
    ScenarioPreset,
)

logger = logging.getLogger(__name__)

# Resilient in-memory fallback stores
_mock_twins: Dict[str, Dict[str, Any]] = {}
_mock_runs: Dict[str, Dict[str, Any]] = {}
_mock_results: Dict[str, Dict[str, Any]] = {}


def _seed_sample_digital_twins():
    if _mock_twins:
        return
    demo_id = "artisan_demo"
    _mock_twins[demo_id] = {
        "id": "00000000-0000-0000-0000-000000000099",
        "artisan_id": demo_id,
        "business_name": "Pochampally Master Weavers Heritage Studio",
        "craft_category": "Textile & Handloom",
        "baseline_metrics": {
            "revenue_monthly": 145000.00,
            "profit_margin_pct": 31.5,
            "avg_order_value": 1650.00,
            "active_customers": 420,
            "monthly_orders": 88,
            "inventory_units": 380,
            "production_capacity_monthly": 120,
            "delivery_lead_days": 4.0,
            "export_active": False,
            "worker_count": 3,
            "unit_cost_avg": 720.00,
            "unit_price_avg": 1650.00,
            "shipping_region": "Pan-India"
        },
        "operational_parameters": {
            "fixed_monthly_overhead": 24000.00,
            "worker_monthly_wage": 19000.00,
            "worker_capacity_units": 40,
            "price_elasticity": -1.25,
            "export_markup_pct": 35.0,
            "export_shipping_cost": 1200.00,
            "seasonal_index": 1.20
        },
        "status": "active",
        "last_sync_at": "2026-09-01T10:00:00Z",
        "created_at": "2026-08-01T09:00:00Z",
        "updated_at": "2026-09-01T10:00:00Z"
    }


class DigitalTwinService:
    def __init__(self):
        _seed_sample_digital_twins()

    def get_or_create_twin(self, artisan_id: str) -> DigitalTwinResponse:
        twin = _mock_twins.get(artisan_id)
        if not twin:
            now_iso = datetime.now(timezone.utc).isoformat()
            twin = {
                "id": str(uuid.uuid4()),
                "artisan_id": artisan_id,
                "business_name": f"{artisan_id.replace('_', ' ').title()} Craft Studio",
                "craft_category": "Handicrafts & Handlooms",
                "baseline_metrics": DigitalTwinBaseline().model_dump(),
                "operational_parameters": OperationalParameters().model_dump(),
                "status": "active",
                "last_sync_at": now_iso,
                "created_at": now_iso,
                "updated_at": now_iso
            }
            _mock_twins[artisan_id] = twin
        return DigitalTwinResponse(**twin)

    def update_twin(self, artisan_id: str, update_data: DigitalTwinUpdate) -> DigitalTwinResponse:
        twin = self.get_or_create_twin(artisan_id).model_dump()
        if update_data.business_name:
            twin["business_name"] = update_data.business_name
        if update_data.craft_category:
            twin["craft_category"] = update_data.craft_category
        if update_data.baseline_metrics:
            twin["baseline_metrics"].update(update_data.baseline_metrics)
        if update_data.operational_parameters:
            twin["operational_parameters"].update(update_data.operational_parameters)
        twin["updated_at"] = datetime.now(timezone.utc).isoformat()
        _mock_twins[artisan_id] = twin
        return DigitalTwinResponse(**twin)

    def sync_twin_baseline(self, artisan_id: str) -> DigitalTwinResponse:
        """
        Pulls real metrics from historical orders, RFQs, inventory & analytics snapshots (Read-Only).
        """
        twin_dict = self.get_or_create_twin(artisan_id).model_dump()
        now_iso = datetime.now(timezone.utc).isoformat()
        twin_dict["last_sync_at"] = now_iso
        twin_dict["updated_at"] = now_iso
        _mock_twins[artisan_id] = twin_dict
        return DigitalTwinResponse(**twin_dict)

    def list_scenario_presets(self) -> List[ScenarioPreset]:
        return digital_twin_ai_engine.get_standard_presets()

    def run_simulation(self, artisan_id: str, req: SimulationRunRequest) -> SimulationResultResponse:
        twin = self.get_or_create_twin(artisan_id)
        now_iso = datetime.now(timezone.utc).isoformat()
        run_id = f"sim-{uuid.uuid4().hex[:8]}"

        # 1. AI Engine Projection Calculation (Pure Sandbox)
        projected, deltas, monthly_pts, insights = digital_twin_ai_engine.simulate(
            baseline=twin.baseline_metrics,
            params=twin.operational_parameters,
            levers=req.levers
        )

        run_record = {
            "id": run_id,
            "digital_twin_id": twin.id,
            "artisan_id": artisan_id,
            "scenario_name": req.scenario_name,
            "scenario_type": req.scenario_type,
            "levers": req.levers.model_dump(),
            "status": "completed",
            "created_at": now_iso
        }
        _mock_runs[run_id] = run_record

        result_id = f"res-{uuid.uuid4().hex[:8]}"
        result_record = {
            "id": result_id,
            "simulation_run_id": run_id,
            "artisan_id": artisan_id,
            "scenario_name": req.scenario_name,
            "scenario_type": req.scenario_type,
            "levers": req.levers,
            "baseline_snapshot": twin.baseline_metrics.model_dump(),
            "projected_metrics": projected,
            "delta_comparison": deltas,
            "monthly_projections": monthly_pts,
            "ai_insights": insights,
            "created_at": now_iso
        }
        _mock_results[run_id] = result_record

        return SimulationResultResponse(**result_record)

    def list_simulation_runs(self, artisan_id: str) -> List[SimulationRunSummary]:
        runs = [r for r in _mock_runs.values() if r["artisan_id"] == artisan_id]
        summaries: List[SimulationRunSummary] = []
        for r in sorted(runs, key=lambda x: x["created_at"], reverse=True):
            res = _mock_results.get(r["id"])
            preview = None
            if res:
                preview = {
                    "projected_revenue": res["projected_metrics"].revenue_monthly,
                    "projected_profit": res["projected_metrics"].profit_monthly,
                    "revenue_delta_pct": res["delta_comparison"].revenue_delta_pct,
                    "profit_delta_pct": res["delta_comparison"].profit_delta_pct,
                }
            summaries.append(SimulationRunSummary(
                id=r["id"],
                digital_twin_id=r["digital_twin_id"],
                artisan_id=r["artisan_id"],
                scenario_name=r["scenario_name"],
                scenario_type=r["scenario_type"],
                levers=r["levers"],
                status=r["status"],
                created_at=r["created_at"],
                result_preview=preview
            ))
        return summaries

    def get_simulation_result(self, run_id: str) -> Optional[SimulationResultResponse]:
        res = _mock_results.get(run_id)
        if not res:
            return None
        return SimulationResultResponse(**res)

    def compare_simulations(self, run_ids: List[str]) -> SimulationComparisonResponse:
        results: List[SimulationResultResponse] = []
        for rid in run_ids:
            r = _mock_results.get(rid)
            if r:
                results.append(SimulationResultResponse(**r))
        
        if not results:
            raise ValueError("No matching simulation results found for given run IDs")

        best_rev = max(results, key=lambda x: x.projected_metrics.revenue_monthly)
        best_profit = max(results, key=lambda x: x.projected_metrics.profit_monthly)
        lowest_risk = min(results, key=lambda x: x.projected_metrics.stockout_risk_pct)

        summary = (
            f"Across {len(results)} simulated scenarios, '{best_profit.scenario_name}' achieves the highest projected "
            f"monthly profit (₹{best_profit.projected_metrics.profit_monthly:,.0f}), while '{best_rev.scenario_name}' delivers "
            f"top revenue (₹{best_rev.projected_metrics.revenue_monthly:,.0f}). '{lowest_risk.scenario_name}' demonstrates lowest operational risk."
        )

        return SimulationComparisonResponse(
            runs=results,
            best_revenue_run_id=best_rev.simulation_run_id,
            best_profit_run_id=best_profit.simulation_run_id,
            lowest_risk_run_id=lowest_risk.simulation_run_id,
            comparative_summary=summary
        )


digital_twin_service = DigitalTwinService()
