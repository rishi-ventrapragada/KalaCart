from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.security import get_current_user
from app.models.digital_twin import (
    DigitalTwinResponse,
    DigitalTwinUpdate,
    SimulationRunRequest,
    SimulationResultResponse,
    SimulationRunSummary,
    SimulationComparisonResponse,
    ScenarioPreset,
)
from app.services.digital_twin_service import digital_twin_service

router = APIRouter(prefix="/api/v1/twin", tags=["Digital Twin Marketplace & AI Sandbox"])


@router.get("", response_model=DigitalTwinResponse)
def get_digital_twin(current_user: dict = Depends(get_current_user)):
    """Fetch or auto-initialize digital twin for current artisan business."""
    artisan_id = current_user.get("uid") or current_user.get("user_id") or "artisan_demo"
    return digital_twin_service.get_or_create_twin(artisan_id)


@router.put("", response_model=DigitalTwinResponse)
def update_digital_twin(
    payload: DigitalTwinUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update artisan digital twin operational parameters and baselines."""
    artisan_id = current_user.get("uid") or current_user.get("user_id") or "artisan_demo"
    return digital_twin_service.update_twin(artisan_id, payload)


@router.post("/sync", response_model=DigitalTwinResponse)
def sync_digital_twin(current_user: dict = Depends(get_current_user)):
    """Resynchronize digital twin baseline from historical orders, RFQs, inventory & analytics."""
    artisan_id = current_user.get("uid") or current_user.get("user_id") or "artisan_demo"
    return digital_twin_service.sync_twin_baseline(artisan_id)


@router.get("/presets", response_model=List[ScenarioPreset])
def list_scenario_presets():
    """List standard one-click simulation scenario presets."""
    return digital_twin_service.list_scenario_presets()


@router.post("/simulate", response_model=SimulationResultResponse, status_code=status.HTTP_201_CREATED)
def run_simulation(
    payload: SimulationRunRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Execute predictive AI simulation run in 100% read-only sandbox.
    Never modifies live product listings, inventory or orders.
    """
    artisan_id = current_user.get("uid") or current_user.get("user_id") or "artisan_demo"
    return digital_twin_service.run_simulation(artisan_id, payload)


@router.get("/simulations", response_model=List[SimulationRunSummary])
def list_simulation_runs(current_user: dict = Depends(get_current_user)):
    """List all simulation runs executed for current artisan's digital twin."""
    artisan_id = current_user.get("uid") or current_user.get("user_id") or "artisan_demo"
    return digital_twin_service.list_simulation_runs(artisan_id)


@router.get("/simulations/{run_id}", response_model=SimulationResultResponse)
def get_simulation_detail(run_id: str):
    """Get full results, time-series projections, and AI recommendations for a specific simulation run."""
    res = digital_twin_service.get_simulation_result(run_id)
    if not res:
        raise HTTPException(status_code=404, detail="Simulation run result not found")
    return res


@router.post("/simulations/compare", response_model=SimulationComparisonResponse)
def compare_simulations(run_ids: List[str]):
    """Compare multiple simulation runs side-by-side."""
    try:
        return digital_twin_service.compare_simulations(run_ids)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
