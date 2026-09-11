"""
Robotics & Smart Manufacturing API Router (KalaCart V10)
Exposes workshop machine telemetry, predictive maintenance, quality predictions,
and ERP integration endpoints.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

from app.core.robotics_manufacturing import (
    robotics_engine,
    MachineType,
    MachineStatus,
    MaintenanceType,
)

router = APIRouter(prefix="/api/v1/robotics", tags=["Robotics & Smart Manufacturing (V10)"])


class RegisterMachineRequest(BaseModel):
    workshop_id: str
    machine_code: str
    machine_name: str
    machine_type: str = "cnc_carver"
    ip_address: str = "192.168.1.100"


class IngestTelemetryRequest(BaseModel):
    machine_id: str
    temperature_c: float
    vibration_level_mm_s: float
    power_consumption_w: float
    additional_metrics: Dict[str, Any] = {}


class ScheduleMaintenanceRequest(BaseModel):
    machine_id: str
    maintenance_type: str = "spindle_lubrication"
    scheduled_date: str
    technician_name: str
    notes: str = ""


class PredictQualityRequest(BaseModel):
    machine_id: str
    batch_id: str
    product_id: str


@router.get("/dashboard")
async def get_workshop_dashboard(workshop_id: Optional[str] = Query(None)):
    """Retrieve full workshop machine health, uptime, energy consumption, and telemetry stats."""
    return robotics_engine.get_workshop_dashboard_summary(workshop_id=workshop_id)


@router.get("/machines/{machine_id}")
async def get_machine_details(machine_id: str):
    """Get detailed machine record, telemetry, and maintenance history."""
    machine = robotics_engine.machines.get(machine_id)
    if not machine:
        raise HTTPException(status_code=404, detail=f"Machine '{machine_id}' not found.")
    logs = robotics_engine.maintenance_records.get(machine_id, [])
    return {
        "machine": machine.to_dict(),
        "maintenance_history": [l.model_dump() for l in logs],
    }


@router.post("/machines/register")
async def register_machine(req: RegisterMachineRequest):
    """Register a new robotic / digitally assisted machine into the workshop network."""
    try:
        m_type = MachineType(req.machine_type)
    except ValueError:
        m_type = MachineType.CNC_CARVER

    machine = robotics_engine.register_machine(
        workshop_id=req.workshop_id,
        machine_code=req.machine_code,
        machine_name=req.machine_name,
        machine_type=m_type,
        ip_address=req.ip_address,
    )
    return {
        "status": "success",
        "message": f"Machine '{machine.machine_name}' registered successfully.",
        "machine": machine.to_dict(),
    }


@router.post("/telemetry/ingest")
async def ingest_machine_telemetry(req: IngestTelemetryRequest):
    """Ingest live sensor packet from laser engraver, CNC lathe, or kiln."""
    try:
        updated_machine = robotics_engine.ingest_telemetry(
            machine_id=req.machine_id,
            temperature_c=req.temperature_c,
            vibration_level_mm_s=req.vibration_level_mm_s,
            power_consumption_w=req.power_consumption_w,
            additional_metrics=req.additional_metrics,
        )
        return {
            "status": "success",
            "machine_status": updated_machine.status.value,
            "telemetry": updated_machine.telemetry.model_dump(),
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/maintenance/schedule")
async def schedule_maintenance(req: ScheduleMaintenanceRequest):
    """Schedule preventive maintenance for a manufacturing unit."""
    try:
        m_type = MaintenanceType(req.maintenance_type)
    except ValueError:
        m_type = MaintenanceType.ROUTINE_CALIBRATION

    try:
        log = robotics_engine.schedule_maintenance(
            machine_id=req.machine_id,
            maintenance_type=m_type,
            scheduled_date=req.scheduled_date,
            technician_name=req.technician_name,
            notes=req.notes,
        )
        return {
            "status": "success",
            "maintenance_log": log.model_dump(),
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/quality/predict")
async def predict_batch_quality(req: PredictQualityRequest):
    """Predict craft production batch quality from sensor telemetry and link with Workshop ERP."""
    try:
        prediction = robotics_engine.predict_batch_quality_and_link_erp(
            machine_id=req.machine_id,
            batch_id=req.batch_id,
            product_id=req.product_id,
        )
        return {
            "status": "success",
            "quality_prediction": prediction.model_dump(),
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
