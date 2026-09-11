import uuid
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

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

# In-memory stores for runtime
_WORKERS: Dict[str, Dict[str, Any]] = {}
_MACHINES: Dict[str, Dict[str, Any]] = {}
_BATCHES: Dict[str, Dict[str, Any]] = {}
_QUALITY_CHECKS: Dict[str, List[Dict[str, Any]]] = {}
_MATERIAL_USAGES: Dict[str, List[Dict[str, Any]]] = {}
_PRODUCTIVITY_LOGS: Dict[str, Dict[str, Any]] = {}
_PAYROLL_RECORDS: Dict[str, Dict[str, Any]] = {}

# Pre-populate sample seed data
_W1_ID = "w-101"
_WORKERS[_W1_ID] = {
    "id": _W1_ID,
    "artisan_id": "artisan_demo",
    "name": "Ramesh Kumar",
    "phone": "+91 98765 43210",
    "skills": ["pottery_throwing", "glazing"],
    "rate_type": "hourly",
    "base_rate": 150.0,
    "status": "active",
    "joined_date": "2025-01-10",
    "created_at": "2025-01-10T08:00:00Z"
}

_W2_ID = "w-102"
_WORKERS[_W2_ID] = {
    "id": _W2_ID,
    "artisan_id": "artisan_demo",
    "name": "Sunita Devi",
    "phone": "+91 98765 43211",
    "skills": ["hand_painting", "quality_inspection"],
    "rate_type": "piece_rate",
    "base_rate": 35.0,
    "status": "active",
    "joined_date": "2025-02-01",
    "created_at": "2025-02-01T08:00:00Z"
}

_M1_ID = "m-201"
_MACHINES[_M1_ID] = {
    "id": _M1_ID,
    "artisan_id": "artisan_demo",
    "name": "Electric Pottery Wheel 01",
    "machine_type": "pottery_wheel",
    "serial_number": "PW-2024-88A",
    "status": "operational",
    "last_serviced_date": "2026-08-01",
    "next_service_date": "2026-11-01",
    "notes": "Calibrated for high RPM clay molding",
    "created_at": "2025-01-01T08:00:00Z"
}

_B1_ID = "b-301"
_BATCHES[_B1_ID] = {
    "id": _B1_ID,
    "batch_code": "BATCH-2026-POT-001",
    "artisan_id": "artisan_demo",
    "product_id": "prod_blue_pottery_vase",
    "order_id": "ORD-2026-EXPORT-889",
    "target_quantity": 50,
    "completed_quantity": 48,
    "rejected_quantity": 2,
    "status": "in_production",
    "assigned_worker_ids": [_W1_ID, _W2_ID],
    "assigned_machine_id": _M1_ID,
    "scheduled_start_date": "2026-09-01",
    "scheduled_end_date": "2026-09-08",
    "actual_start_date": "2026-09-01",
    "actual_end_date": None,
    "estimated_labour_cost": 4500.0,
    "actual_labour_cost": 3800.0,
    "estimated_material_cost": 2500.0,
    "actual_material_cost": 2400.0,
    "notes": "Urgent batch for European export order",
    "created_at": "2026-09-01T09:00:00Z"
}


class WorkshopERPService:

    # 1. Worker Management
    def create_worker(self, artisan_id: str, payload: WorkerCreate) -> WorkerResponse:
        worker_id = f"w-{uuid.uuid4().hex[:6]}"
        now = datetime.now(timezone.utc).isoformat()
        worker = {
            "id": worker_id,
            "artisan_id": artisan_id,
            "name": payload.name,
            "phone": payload.phone,
            "skills": payload.skills,
            "rate_type": payload.rate_type,
            "base_rate": payload.base_rate,
            "status": payload.status,
            "joined_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "created_at": now
        }
        _WORKERS[worker_id] = worker
        return WorkerResponse(**worker)

    def list_workers(self, artisan_id: str) -> List[WorkerResponse]:
        return [WorkerResponse(**w) for w in _WORKERS.values() if w["artisan_id"] == artisan_id]

    # 2. Machine Management
    def create_machine(self, artisan_id: str, payload: MachineCreate) -> MachineResponse:
        machine_id = f"m-{uuid.uuid4().hex[:6]}"
        now = datetime.now(timezone.utc).isoformat()
        machine = {
            "id": machine_id,
            "artisan_id": artisan_id,
            "name": payload.name,
            "machine_type": payload.machine_type,
            "serial_number": payload.serial_number,
            "status": payload.status,
            "last_serviced_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "next_service_date": None,
            "notes": payload.notes,
            "created_at": now
        }
        _MACHINES[machine_id] = machine
        return MachineResponse(**machine)

    def list_machines(self, artisan_id: str) -> List[MachineResponse]:
        return [MachineResponse(**m) for m in _MACHINES.values() if m["artisan_id"] == artisan_id]

    # 3. Production Batch Management (Direct link to Orders)
    def create_production_batch(self, artisan_id: str, payload: ProductionBatchCreate) -> ProductionBatchResponse:
        batch_id = f"b-{uuid.uuid4().hex[:6]}"
        batch_code = f"BATCH-{datetime.now(timezone.utc).strftime('%Y%m')}-{uuid.uuid4().hex[:4].upper()}"
        now = datetime.now(timezone.utc).isoformat()
        
        batch = {
            "id": batch_id,
            "batch_code": batch_code,
            "artisan_id": artisan_id,
            "product_id": payload.product_id,
            "order_id": payload.order_id,
            "target_quantity": payload.target_quantity,
            "completed_quantity": 0,
            "rejected_quantity": 0,
            "status": "queued",
            "assigned_worker_ids": payload.assigned_worker_ids,
            "assigned_machine_id": payload.assigned_machine_id,
            "scheduled_start_date": payload.scheduled_start_date or datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "scheduled_end_date": payload.scheduled_end_date,
            "actual_start_date": None,
            "actual_end_date": None,
            "estimated_labour_cost": payload.estimated_labour_cost,
            "actual_labour_cost": 0.0,
            "estimated_material_cost": payload.estimated_material_cost,
            "actual_material_cost": 0.0,
            "notes": payload.notes,
            "created_at": now
        }
        _BATCHES[batch_id] = batch
        return ProductionBatchResponse(**batch)

    def list_production_batches(self, artisan_id: str, order_id: Optional[str] = None) -> List[ProductionBatchResponse]:
        batches = [b for b in _BATCHES.values() if b["artisan_id"] == artisan_id]
        if order_id:
            batches = [b for b in batches if b.get("order_id") == order_id]
        return [ProductionBatchResponse(**b) for b in batches]

    def get_production_batch(self, batch_id: str) -> Optional[ProductionBatchResponse]:
        batch = _BATCHES.get(batch_id)
        if not batch:
            return None
        return ProductionBatchResponse(**batch)

    def update_batch_status(self, batch_id: str, status: str, completed_qty: Optional[int] = None) -> Optional[ProductionBatchResponse]:
        batch = _BATCHES.get(batch_id)
        if not batch:
            return None
        batch["status"] = status
        if status == "in_production" and not batch["actual_start_date"]:
            batch["actual_start_date"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        elif status == "completed":
            batch["actual_end_date"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if completed_qty is not None:
            batch["completed_quantity"] = completed_qty
        return ProductionBatchResponse(**batch)

    # 4. Quality Checks
    def log_quality_check(self, batch_id: str, inspector_id: str, payload: QualityCheckCreate) -> QualityCheckResponse:
        qc_id = f"qc-{uuid.uuid4().hex[:6]}"
        now = datetime.now(timezone.utc).isoformat()
        pass_rate = round((payload.passed_count / max(1, payload.total_inspected)) * 100, 2)
        
        qc = {
            "id": qc_id,
            "batch_id": batch_id,
            "inspector_id": inspector_id,
            "total_inspected": payload.total_inspected,
            "passed_count": payload.passed_count,
            "rejected_count": payload.rejected_count,
            "pass_rate_percentage": pass_rate,
            "defect_types": payload.defect_types,
            "result": payload.result,
            "inspection_notes": payload.inspection_notes,
            "inspected_at": now
        }
        if batch_id not in _QUALITY_CHECKS:
            _QUALITY_CHECKS[batch_id] = []
        _QUALITY_CHECKS[batch_id].append(qc)

        if batch_id in _BATCHES:
            _BATCHES[batch_id]["completed_quantity"] += payload.passed_count
            _BATCHES[batch_id]["rejected_quantity"] += payload.rejected_count
            if payload.result == "passed" and _BATCHES[batch_id]["completed_quantity"] >= _BATCHES[batch_id]["target_quantity"]:
                _BATCHES[batch_id]["status"] = "completed"
                _BATCHES[batch_id]["actual_end_date"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        return QualityCheckResponse(**qc)

    def list_quality_checks(self, batch_id: str) -> List[QualityCheckResponse]:
        items = _QUALITY_CHECKS.get(batch_id, [])
        return [QualityCheckResponse(**i) for i in items]

    # 5. Raw Material Usage
    def log_material_usage(self, batch_id: str, payload: MaterialUsageCreate) -> MaterialUsageResponse:
        usage_id = f"mat-{uuid.uuid4().hex[:6]}"
        now = datetime.now(timezone.utc).isoformat()
        total_cost = round(payload.quantity_used * payload.unit_cost, 2)

        usage = {
            "id": usage_id,
            "batch_id": batch_id,
            "material_id": payload.material_id,
            "material_name": payload.material_name,
            "quantity_used": payload.quantity_used,
            "unit_of_measure": payload.unit_of_measure,
            "unit_cost": payload.unit_cost,
            "total_cost": total_cost,
            "logged_at": now
        }
        if batch_id not in _MATERIAL_USAGES:
            _MATERIAL_USAGES[batch_id] = []
        _MATERIAL_USAGES[batch_id].append(usage)

        if batch_id in _BATCHES:
            _BATCHES[batch_id]["actual_material_cost"] += total_cost

        return MaterialUsageResponse(**usage)

    def list_material_usages(self, batch_id: str) -> List[MaterialUsageResponse]:
        items = _MATERIAL_USAGES.get(batch_id, [])
        return [MaterialUsageResponse(**i) for i in items]

    # 6. Daily Worker Productivity & Labour Cost
    def log_productivity(self, payload: DailyProductivityCreate) -> DailyProductivityResponse:
        log_id = f"prod-{uuid.uuid4().hex[:6]}"
        now = datetime.now(timezone.utc).isoformat()
        worker = _WORKERS.get(payload.worker_id)
        worker_name = worker["name"] if worker else "Unknown Worker"

        labour_cost = 0.0
        if worker:
            if worker["rate_type"] == "hourly":
                labour_cost = round(payload.hours_worked * worker["base_rate"], 2)
            elif worker["rate_type"] == "piece_rate":
                labour_cost = round(payload.units_produced * worker["base_rate"], 2)
            else:
                labour_cost = round(worker["base_rate"] / 26.0, 2)

        log = {
            "id": log_id,
            "worker_id": payload.worker_id,
            "worker_name": worker_name,
            "batch_id": payload.batch_id,
            "work_date": payload.work_date or datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "hours_worked": payload.hours_worked,
            "units_produced": payload.units_produced,
            "calculated_labour_cost": labour_cost,
            "notes": payload.notes,
            "created_at": now
        }
        _PRODUCTIVITY_LOGS[log_id] = log

        if payload.batch_id and payload.batch_id in _BATCHES:
            _BATCHES[payload.batch_id]["actual_labour_cost"] += labour_cost

        return DailyProductivityResponse(**log)

    def list_productivity_logs(self, worker_id: Optional[str] = None, batch_id: Optional[str] = None) -> List[DailyProductivityResponse]:
        logs = list(_PRODUCTIVITY_LOGS.values())
        if worker_id:
            logs = [l for l in logs if l["worker_id"] == worker_id]
        if batch_id:
            logs = [l for l in logs if l.get("batch_id") == batch_id]
        return [DailyProductivityResponse(**l) for l in logs]

    # 7. Automated Payroll Calculation
    def generate_payroll(self, artisan_id: str, payload: PayrollGenerateRequest) -> List[PayrollRecordResponse]:
        records = []
        target_workers = [w for w in _WORKERS.values() if w["artisan_id"] == artisan_id and w["status"] == "active"]
        if payload.worker_id:
            target_workers = [w for w in target_workers if w["id"] == payload.worker_id]

        for w in target_workers:
            w_logs = [l for l in _PRODUCTIVITY_LOGS.values() if l["worker_id"] == w["id"] and payload.period_start <= l["work_date"] <= payload.period_end]
            total_hours = sum(l["hours_worked"] for l in w_logs)
            total_units = sum(l["units_produced"] for l in w_logs)
            regular_hours = min(48.0, total_hours)
            overtime_hours = max(0.0, total_hours - 48.0)

            if w["rate_type"] == "hourly":
                base_earn = regular_hours * w["base_rate"]
                ot_earn = overtime_hours * (w["base_rate"] * 1.5)
            elif w["rate_type"] == "piece_rate":
                base_earn = total_units * w["base_rate"]
                ot_earn = 0.0
            else:
                base_earn = w["base_rate"]
                ot_earn = 0.0

            bonus = 500.0 if total_units >= 50 else 0.0
            deductions = 200.0
            gross = round(base_earn + ot_earn + bonus, 2)
            net = round(max(0.0, gross - deductions), 2)

            rec_id = f"pay-{uuid.uuid4().hex[:6]}"
            rec_code = f"PAY-{datetime.now(timezone.utc).strftime('%Y%m')}-{uuid.uuid4().hex[:4].upper()}"

            record = {
                "id": rec_id,
                "payroll_code": rec_code,
                "artisan_id": artisan_id,
                "worker_id": w["id"],
                "worker_name": w["name"],
                "period_start": payload.period_start,
                "period_end": payload.period_end,
                "regular_hours": regular_hours,
                "overtime_hours": overtime_hours,
                "total_pieces_produced": total_units,
                "base_earnings": round(base_earn, 2),
                "overtime_earnings": round(ot_earn, 2),
                "bonus_amount": bonus,
                "deductions": deductions,
                "gross_pay": gross,
                "net_pay": net,
                "payment_status": "processed",
                "payment_method": "upi",
                "payment_reference": f"UPI-REF-{uuid.uuid4().hex[:8].upper()}",
                "paid_at": datetime.now(timezone.utc).isoformat()
            }
            _PAYROLL_RECORDS[rec_id] = record
            records.append(PayrollRecordResponse(**record))

        return records

    # 8. Workshop Production & KPI Reporting
    def generate_production_report(self, artisan_id: str) -> ProductionReportResponse:
        now = datetime.now(timezone.utc).isoformat()
        workers = [w for w in _WORKERS.values() if w["artisan_id"] == artisan_id]
        machines = [m for m in _MACHINES.values() if m["artisan_id"] == artisan_id and m["status"] == "operational"]
        batches = [b for b in _BATCHES.values() if b["artisan_id"] == artisan_id]

        active_batches = [b for b in batches if b["status"] in ("in_production", "qc_review")]
        completed_batches = [b for b in batches if b["status"] == "completed"]

        total_units = sum(b["completed_quantity"] for b in batches)
        total_labour = sum(b["actual_labour_cost"] for b in batches)
        total_material = sum(b["actual_material_cost"] for b in batches)

        all_qc = []
        for b in batches:
            all_qc.extend(_QUALITY_CHECKS.get(b["id"], []))
        total_inspected = sum(q["total_inspected"] for q in all_qc)
        total_passed = sum(q["passed_count"] for q in all_qc)
        overall_pass_rate = round((total_passed / max(1, total_inspected)) * 100, 2) if total_inspected > 0 else 96.5

        all_prod_hours = sum(l["hours_worked"] for l in _PRODUCTIVITY_LOGS.values())
        all_prod_units = sum(l["units_produced"] for l in _PRODUCTIVITY_LOGS.values())
        avg_productivity = round(all_prod_units / max(1.0, all_prod_hours), 2)

        batch_summaries = [
            {
                "batch_id": b["id"],
                "batch_code": b["batch_code"],
                "product_id": b["product_id"],
                "order_id": b.get("order_id"),
                "status": b["status"],
                "target_quantity": b["target_quantity"],
                "completed_quantity": b["completed_quantity"],
                "total_cost": round(b["actual_labour_cost"] + b["actual_material_cost"], 2)
            }
            for b in batches
        ]

        return ProductionReportResponse(
            artisan_id=artisan_id,
            report_generated_at=now,
            total_workers=len(workers),
            active_machines=len(machines),
            active_batches=len(active_batches),
            completed_batches_period=len(completed_batches),
            total_units_produced=total_units,
            overall_quality_pass_rate=overall_pass_rate,
            total_labour_cost=round(total_labour, 2),
            total_material_cost=round(total_material, 2),
            average_worker_productivity_units_per_hour=avg_productivity,
            batch_summary=batch_summaries
        )


workshop_erp_service = WorkshopERPService()
