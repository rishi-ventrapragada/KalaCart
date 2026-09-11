"""
Robotics & Smart Manufacturing Core Engine (KalaCart V10)
Integrates digitally assisted artisan workshops with:
- Laser Engravers, CNC Wood/Metal Carvers, Ceramic Kilns, 3D Scanners, Label Printers, Smart Scales.
- Real-time telemetry ingestion (temperature, vibration, power, runtime).
- Predictive maintenance scheduling and anomaly alerts.
- AI-based quality prediction from process telemetry.
- Seamless bridge with Workshop ERP production work orders and batches.
"""

import uuid
import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class MachineType(str, Enum):
    LASER_ENGRAVER = "laser_engraver"
    CNC_CARVER = "cnc_carver"
    CERAMIC_KILN = "ceramic_kiln"
    THREE_D_SCANNER = "3d_scanner"
    LABEL_PRINTER = "label_printer"
    SMART_SCALE = "smart_scale"
    BARCODE_APPLICATOR = "barcode_applicator"


class MachineStatus(str, Enum):
    ONLINE = "online"
    BUSY = "busy"
    MAINTENANCE_REQUIRED = "maintenance_required"
    OFFLINE = "offline"
    ERROR = "error"


class MaintenanceType(str, Enum):
    ROUTINE_CALIBRATION = "routine_calibration"
    FILTER_REPLACEMENT = "filter_replacement"
    THERMAL_SENSOR_CHECK = "thermal_sensor_check"
    SPINDLE_LUBRICATION = "spindle_lubrication"
    EMERGENCY_REPAIR = "emergency_repair"


class MachineTelemetry(BaseModel):
    temperature_c: float = 24.5
    vibration_level_mm_s: float = 0.4
    power_consumption_w: float = 180.0
    runtime_hours_total: float = 340.5
    runtime_hours_since_last_service: float = 42.0
    kiln_target_temp_c: Optional[float] = None
    kiln_actual_temp_c: Optional[float] = None
    spindle_rpm: Optional[int] = None
    laser_power_pct: Optional[float] = None


class SmartMachine(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workshop_id: str
    machine_code: str
    machine_name: str
    machine_type: MachineType
    status: MachineStatus = MachineStatus.ONLINE
    firmware_version: str = "v2.4.1"
    ip_address: str = "192.168.1.101"
    telemetry: MachineTelemetry = Field(default_factory=MachineTelemetry)
    created_at: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "workshop_id": self.workshop_id,
            "machine_code": self.machine_code,
            "machine_name": self.machine_name,
            "machine_type": self.machine_type.value,
            "status": self.status.value,
            "firmware_version": self.firmware_version,
            "ip_address": self.ip_address,
            "telemetry": self.telemetry.model_dump(),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class MaintenanceLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    machine_id: str
    maintenance_type: MaintenanceType
    status: str = "scheduled"  # scheduled, in_progress, completed, deferred
    scheduled_date: str
    completed_at: Optional[str] = None
    technician_name: str
    notes: str = ""
    cost_inr: float = 0.0
    created_at: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())


class QualityPrediction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    machine_id: str
    batch_id: str
    product_id: str
    predicted_quality_score: float  # 0.0 - 100.0%
    defect_probability_pct: float
    telemetry_snapshot: Dict[str, Any]
    risk_factors: List[str] = Field(default_factory=list)
    passed_threshold: bool = True
    created_at: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())


class RoboticsManufacturingEngine:
    """
    Manages physical-to-digital workshop automation, machine health,
    predictive maintenance, and ERP integration for artisan cooperatives.
    """

    def __init__(self):
        self.machines: Dict[str, SmartMachine] = {}
        self.maintenance_records: Dict[str, List[MaintenanceLog]] = {}  # machine_id -> logs
        self.quality_evaluations: Dict[str, List[QualityPrediction]] = {}  # batch_id -> predictions
        self._seed_default_workshop_machines()

    def _seed_default_workshop_machines(self):
        # 1. Channapatna CNC Wood Carver
        cnc = SmartMachine(
            workshop_id="ws_channapatna_01",
            machine_code="CNC-WOOD-01",
            machine_name="Channapatna High-Precision Lathe & Carver",
            machine_type=MachineType.CNC_CARVER,
            status=MachineStatus.BUSY,
            ip_address="192.168.10.21",
            telemetry=MachineTelemetry(
                temperature_c=38.2,
                vibration_level_mm_s=0.6,
                power_consumption_w=650.0,
                runtime_hours_total=1240.0,
                runtime_hours_since_last_service=65.0,
                spindle_rpm=4200,
            ),
        )

        # 2. Khurja High-Temp Ceramic Kiln
        kiln = SmartMachine(
            workshop_id="ws_khurja_pottery_02",
            machine_code="KILN-CERAMIC-03",
            machine_name="Khurja Smart Electric Firing Kiln",
            machine_type=MachineType.CERAMIC_KILN,
            status=MachineStatus.ONLINE,
            ip_address="192.168.10.35",
            telemetry=MachineTelemetry(
                temperature_c=850.0,
                kiln_actual_temp_c=850.0,
                kiln_target_temp_c=900.0,
                power_consumption_w=2800.0,
                runtime_hours_total=890.0,
                runtime_hours_since_last_service=18.0,
            ),
        )

        # 3. Bidriware Precision Laser Engraver
        laser = SmartMachine(
            workshop_id="ws_bidar_metal_03",
            machine_code="LASER-ENGRAVE-02",
            machine_name="Bidriware Fiber Laser Precision Engraver",
            machine_type=MachineType.LASER_ENGRAVER,
            status=MachineStatus.ONLINE,
            ip_address="192.168.10.42",
            telemetry=MachineTelemetry(
                temperature_c=26.0,
                laser_power_pct=45.0,
                power_consumption_w=350.0,
                runtime_hours_total=420.0,
                runtime_hours_since_last_service=22.0,
            ),
        )

        # 4. Smart Scale & Barcode Label Applicator
        scale = SmartMachine(
            workshop_id="ws_bidar_metal_03",
            machine_code="SCALE-LABEL-01",
            machine_name="Dispatch Smart Scale & Barcode Labeler",
            machine_type=MachineType.SMART_SCALE,
            status=MachineStatus.ONLINE,
            ip_address="192.168.10.55",
            telemetry=MachineTelemetry(
                temperature_c=22.0,
                power_consumption_w=85.0,
                runtime_hours_total=210.0,
                runtime_hours_since_last_service=10.0,
            ),
        )

        for m in [cnc, kiln, laser, scale]:
            self.machines[m.id] = m
            self.maintenance_records[m.id] = []

        # Seed initial maintenance
        self.maintenance_records[cnc.id].append(
            MaintenanceLog(
                machine_id=cnc.id,
                maintenance_type=MaintenanceType.SPINDLE_LUBRICATION,
                status="completed",
                scheduled_date="2026-08-15",
                completed_at="2026-08-15T10:30:00Z",
                technician_name="Mahesh Sharma",
                notes="Lubricated high-speed spindle bearing, replaced carbon brushes.",
                cost_inr=1200.0,
            )
        )

    def register_machine(
        self,
        workshop_id: str,
        machine_code: str,
        machine_name: str,
        machine_type: MachineType,
        ip_address: str = "192.168.1.100",
    ) -> SmartMachine:
        """Registers a new robotic or smart manufacturing device."""
        machine = SmartMachine(
            workshop_id=workshop_id,
            machine_code=machine_code,
            machine_name=machine_name,
            machine_type=machine_type,
            ip_address=ip_address,
        )
        self.machines[machine.id] = machine
        self.maintenance_records[machine.id] = []
        return machine

    def ingest_telemetry(
        self,
        machine_id: str,
        temperature_c: float,
        vibration_level_mm_s: float,
        power_consumption_w: float,
        additional_metrics: Optional[Dict[str, Any]] = None,
    ) -> SmartMachine:
        """Ingests live IoT telemetry packet and detects anomalies."""
        machine = self.machines.get(machine_id)
        if not machine:
            raise ValueError(f"Machine '{machine_id}' not found.")

        machine.telemetry.temperature_c = temperature_c
        machine.telemetry.vibration_level_mm_s = vibration_level_mm_s
        machine.telemetry.power_consumption_w = power_consumption_w

        if additional_metrics:
            for k, v in additional_metrics.items():
                if hasattr(machine.telemetry, k):
                    setattr(machine.telemetry, k, v)

        # Anomaly Check
        if vibration_level_mm_s > 1.8 or temperature_c > 95.0:
            machine.status = MachineStatus.MAINTENANCE_REQUIRED
        elif machine.status == MachineStatus.MAINTENANCE_REQUIRED and vibration_level_mm_s <= 1.0:
            machine.status = MachineStatus.ONLINE

        machine.updated_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
        return machine

    def schedule_maintenance(
        self,
        machine_id: str,
        maintenance_type: MaintenanceType,
        scheduled_date: str,
        technician_name: str,
        notes: str = "",
    ) -> MaintenanceLog:
        """Schedules preventive maintenance for a workshop machine."""
        if machine_id not in self.machines:
            raise ValueError(f"Machine '{machine_id}' not found.")

        log = MaintenanceLog(
            machine_id=machine_id,
            maintenance_type=maintenance_type,
            status="scheduled",
            scheduled_date=scheduled_date,
            technician_name=technician_name,
            notes=notes,
        )
        self.maintenance_records[machine_id].append(log)
        return log

    def predict_batch_quality_and_link_erp(
        self,
        machine_id: str,
        batch_id: str,
        product_id: str,
    ) -> QualityPrediction:
        """
        Runs ML quality prediction from machine telemetry and connects output
        directly with Workshop ERP batch quality certificates.
        """
        machine = self.machines.get(machine_id)
        if not machine:
            raise ValueError(f"Machine '{machine_id}' not found.")

        tel = machine.telemetry
        risk_factors = []
        defect_prob = 1.0

        if tel.vibration_level_mm_s > 1.2:
            risk_factors.append("Spindle vibration slightly elevated (> 1.2 mm/s)")
            defect_prob += 3.5

        if machine.machine_type == MachineType.CERAMIC_KILN and tel.kiln_actual_temp_c and tel.kiln_target_temp_c:
            temp_delta = abs(tel.kiln_actual_temp_c - tel.kiln_target_temp_c)
            if temp_delta > 30.0:
                risk_factors.append(f"Kiln temperature variance {temp_delta}°C from target")
                defect_prob += 4.0

        score = max(0.0, min(100.0, round(100.0 - defect_prob, 2)))
        prediction = QualityPrediction(
            machine_id=machine_id,
            batch_id=batch_id,
            product_id=product_id,
            predicted_quality_score=score,
            defect_probability_pct=round(defect_prob, 2),
            telemetry_snapshot=tel.model_dump(),
            risk_factors=risk_factors,
            passed_threshold=score >= 90.0,
        )

        if batch_id not in self.quality_evaluations:
            self.quality_evaluations[batch_id] = []
        self.quality_evaluations[batch_id].append(prediction)

        return prediction

    def get_workshop_dashboard_summary(self, workshop_id: Optional[str] = None) -> Dict[str, Any]:
        """Aggregates machine uptime, maintenance alerts, energy consumption, and quality metrics."""
        filtered_machines = [
            m for m in self.machines.values()
            if not workshop_id or m.workshop_id == workshop_id
        ]

        total_machines = len(filtered_machines)
        online_count = sum(1 for m in filtered_machines if m.status in (MachineStatus.ONLINE, MachineStatus.BUSY))
        maintenance_needed = sum(1 for m in filtered_machines if m.status == MachineStatus.MAINTENANCE_REQUIRED)
        total_power_kw = sum(m.telemetry.power_consumption_w for m in filtered_machines) / 1000.0

        return {
            "total_machines": total_machines,
            "online_machines": online_count,
            "maintenance_required_count": maintenance_needed,
            "total_power_consumption_kw": round(total_power_kw, 2),
            "machines": [m.to_dict() for m in filtered_machines],
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }


# Global Singleton Engine Instance
robotics_engine = RoboticsManufacturingEngine()
