from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class WorkerCreate(BaseModel):
    name: str
    phone: Optional[str] = None
    skills: List[str] = []
    rate_type: str = "hourly"  # hourly, piece_rate, monthly
    base_rate: float = 0.0
    status: str = "active"


class WorkerResponse(BaseModel):
    id: str
    artisan_id: str
    name: str
    phone: Optional[str] = None
    skills: List[str] = []
    rate_type: str
    base_rate: float
    status: str
    joined_date: str
    created_at: str


class MachineCreate(BaseModel):
    name: str
    machine_type: str
    serial_number: Optional[str] = None
    status: str = "operational"  # operational, in_use, maintenance_needed, broken
    notes: Optional[str] = None


class MachineResponse(BaseModel):
    id: str
    artisan_id: str
    name: str
    machine_type: str
    serial_number: Optional[str] = None
    status: str
    last_serviced_date: Optional[str] = None
    next_service_date: Optional[str] = None
    notes: Optional[str] = None
    created_at: str


class ProductionBatchCreate(BaseModel):
    product_id: str
    order_id: Optional[str] = None  # Direct linkage to KalaCart order
    target_quantity: int = 1
    assigned_worker_ids: List[str] = []
    assigned_machine_id: Optional[str] = None
    scheduled_start_date: Optional[str] = None
    scheduled_end_date: Optional[str] = None
    estimated_labour_cost: float = 0.0
    estimated_material_cost: float = 0.0
    notes: Optional[str] = None


class ProductionBatchResponse(BaseModel):
    id: str
    batch_code: str
    artisan_id: str
    product_id: str
    order_id: Optional[str] = None
    target_quantity: int
    completed_quantity: int
    rejected_quantity: int
    status: str  # queued, in_production, qc_review, completed, cancelled
    assigned_worker_ids: List[str] = []
    assigned_machine_id: Optional[str] = None
    scheduled_start_date: Optional[str] = None
    scheduled_end_date: Optional[str] = None
    actual_start_date: Optional[str] = None
    actual_end_date: Optional[str] = None
    estimated_labour_cost: float
    actual_labour_cost: float
    estimated_material_cost: float
    actual_material_cost: float
    notes: Optional[str] = None
    created_at: str


class QualityCheckCreate(BaseModel):
    total_inspected: int
    passed_count: int
    rejected_count: int
    defect_types: List[Dict[str, Any]] = []
    result: str = "passed"  # passed, failed, rework_needed
    inspection_notes: Optional[str] = None


class QualityCheckResponse(BaseModel):
    id: str
    batch_id: str
    inspector_id: str
    total_inspected: int
    passed_count: int
    rejected_count: int
    pass_rate_percentage: float
    defect_types: List[Dict[str, Any]] = []
    result: str
    inspection_notes: Optional[str] = None
    inspected_at: str


class MaterialUsageCreate(BaseModel):
    material_id: Optional[str] = None
    material_name: str
    quantity_used: float
    unit_of_measure: str = "units"
    unit_cost: float = 0.0


class MaterialUsageResponse(BaseModel):
    id: str
    batch_id: str
    material_id: Optional[str] = None
    material_name: str
    quantity_used: float
    unit_of_measure: str
    unit_cost: float
    total_cost: float
    logged_at: str


class DailyProductivityCreate(BaseModel):
    worker_id: str
    batch_id: Optional[str] = None
    work_date: Optional[str] = None
    hours_worked: float
    units_produced: int = 0
    notes: Optional[str] = None


class DailyProductivityResponse(BaseModel):
    id: str
    worker_id: str
    worker_name: str
    batch_id: Optional[str] = None
    work_date: str
    hours_worked: float
    units_produced: int
    calculated_labour_cost: float
    notes: Optional[str] = None
    created_at: str


class PayrollGenerateRequest(BaseModel):
    period_start: str
    period_end: str
    worker_id: Optional[str] = None


class PayrollRecordResponse(BaseModel):
    id: str
    payroll_code: str
    artisan_id: str
    worker_id: str
    worker_name: str
    period_start: str
    period_end: str
    regular_hours: float
    overtime_hours: float
    total_pieces_produced: int
    base_earnings: float
    overtime_earnings: float
    bonus_amount: float
    deductions: float
    gross_pay: float
    net_pay: float
    payment_status: str
    payment_method: Optional[str] = None
    payment_reference: Optional[str] = None
    paid_at: Optional[str] = None


class ProductionReportResponse(BaseModel):
    artisan_id: str
    report_generated_at: str
    total_workers: int
    active_machines: int
    active_batches: int
    completed_batches_period: int
    total_units_produced: int
    overall_quality_pass_rate: float
    total_labour_cost: float
    total_material_cost: float
    average_worker_productivity_units_per_hour: float
    batch_summary: List[Dict[str, Any]]
