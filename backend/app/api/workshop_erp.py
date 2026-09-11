from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.security import get_current_user
from app.models.workshop_erp import (
    WorkerCreate, WorkerResponse,
    MachineCreate, MachineResponse,
    ProductionBatchCreate, ProductionBatchResponse,
    QualityCheckCreate, QualityCheckResponse,
    MaterialUsageCreate, MaterialUsageResponse,
    DailyProductivityCreate, DailyProductivityResponse,
    PayrollGenerateRequest, PayrollRecordResponse,
    ProductionReportResponse
)
from app.services.workshop_erp_service import workshop_erp_service

router = APIRouter(prefix="/api/v1/erp", tags=["Workshop ERP"])


# 1. Workers
@router.post("/workers", response_model=WorkerResponse, status_code=status.HTTP_201_CREATED)
def add_worker(payload: WorkerCreate, current_user: dict = Depends(get_current_user)):
    artisan_id = current_user.get("uid") or current_user.get("user_id") or "artisan_demo"
    return workshop_erp_service.create_worker(artisan_id, payload)


@router.get("/workers", response_model=List[WorkerResponse])
def get_workers(current_user: dict = Depends(get_current_user)):
    artisan_id = current_user.get("uid") or current_user.get("user_id") or "artisan_demo"
    return workshop_erp_service.list_workers(artisan_id)


# 2. Machines & Equipment
@router.post("/machines", response_model=MachineResponse, status_code=status.HTTP_201_CREATED)
def add_machine(payload: MachineCreate, current_user: dict = Depends(get_current_user)):
    artisan_id = current_user.get("uid") or current_user.get("user_id") or "artisan_demo"
    return workshop_erp_service.create_machine(artisan_id, payload)


@router.get("/machines", response_model=List[MachineResponse])
def get_machines(current_user: dict = Depends(get_current_user)):
    artisan_id = current_user.get("uid") or current_user.get("user_id") or "artisan_demo"
    return workshop_erp_service.list_machines(artisan_id)


# 3. Production Batches
@router.post("/batches", response_model=ProductionBatchResponse, status_code=status.HTTP_201_CREATED)
def create_batch(payload: ProductionBatchCreate, current_user: dict = Depends(get_current_user)):
    artisan_id = current_user.get("uid") or current_user.get("user_id") or "artisan_demo"
    return workshop_erp_service.create_production_batch(artisan_id, payload)


@router.get("/batches", response_model=List[ProductionBatchResponse])
def list_batches(order_id: Optional[str] = Query(None), current_user: dict = Depends(get_current_user)):
    artisan_id = current_user.get("uid") or current_user.get("user_id") or "artisan_demo"
    return workshop_erp_service.list_production_batches(artisan_id, order_id=order_id)


@router.get("/batches/{batch_id}", response_model=ProductionBatchResponse)
def get_batch(batch_id: str, current_user: dict = Depends(get_current_user)):
    batch = workshop_erp_service.get_production_batch(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Production batch not found")
    return batch


@router.patch("/batches/{batch_id}/status", response_model=ProductionBatchResponse)
def update_batch_status(batch_id: str, status_val: str = Query(..., alias="status"), completed_qty: Optional[int] = Query(None), current_user: dict = Depends(get_current_user)):
    batch = workshop_erp_service.update_batch_status(batch_id, status_val, completed_qty)
    if not batch:
        raise HTTPException(status_code=404, detail="Production batch not found")
    return batch


# 4. Quality Checks
@router.post("/batches/{batch_id}/qc", response_model=QualityCheckResponse, status_code=status.HTTP_201_CREATED)
def record_quality_check(batch_id: str, payload: QualityCheckCreate, current_user: dict = Depends(get_current_user)):
    inspector_id = current_user.get("uid") or current_user.get("user_id") or "inspector_demo"
    return workshop_erp_service.log_quality_check(batch_id, inspector_id, payload)


@router.get("/batches/{batch_id}/qc", response_model=List[QualityCheckResponse])
def get_batch_qc_history(batch_id: str, current_user: dict = Depends(get_current_user)):
    return workshop_erp_service.list_quality_checks(batch_id)


# 5. Raw Material Usages
@router.post("/batches/{batch_id}/materials", response_model=MaterialUsageResponse, status_code=status.HTTP_201_CREATED)
def record_material_usage(batch_id: str, payload: MaterialUsageCreate, current_user: dict = Depends(get_current_user)):
    return workshop_erp_service.log_material_usage(batch_id, payload)


@router.get("/batches/{batch_id}/materials", response_model=List[MaterialUsageResponse])
def get_batch_materials(batch_id: str, current_user: dict = Depends(get_current_user)):
    return workshop_erp_service.list_material_usages(batch_id)


# 6. Daily Productivity
@router.post("/productivity", response_model=DailyProductivityResponse, status_code=status.HTTP_201_CREATED)
def log_daily_productivity(payload: DailyProductivityCreate, current_user: dict = Depends(get_current_user)):
    return workshop_erp_service.log_productivity(payload)


@router.get("/productivity", response_model=List[DailyProductivityResponse])
def get_productivity(worker_id: Optional[str] = Query(None), batch_id: Optional[str] = Query(None), current_user: dict = Depends(get_current_user)):
    return workshop_erp_service.list_productivity_logs(worker_id=worker_id, batch_id=batch_id)


# 7. Payroll
@router.post("/payroll/generate", response_model=List[PayrollRecordResponse])
def generate_payroll_records(payload: PayrollGenerateRequest, current_user: dict = Depends(get_current_user)):
    artisan_id = current_user.get("uid") or current_user.get("user_id") or "artisan_demo"
    return workshop_erp_service.generate_payroll(artisan_id, payload)


# 8. Workshop Production Report & KPIs
@router.get("/reports/production", response_model=ProductionReportResponse)
def get_workshop_report(current_user: dict = Depends(get_current_user)):
    artisan_id = current_user.get("uid") or current_user.get("user_id") or "artisan_demo"
    return workshop_erp_service.generate_production_report(artisan_id)
