from typing import List, Optional, Dict, Any
from datetime import datetime, date
import uuid
from app.models.cooperative import (
    OrganizationCreate,
    OrganizationResponse,
    MemberAddRequest,
    MemberResponse,
    MemberRole,
    SharedInventoryPoolRequest,
    SharedInventoryResponse,
    TaskCreate,
    TaskResponse,
    AttendanceLogRequest,
    AttendanceResponse,
    CalculatePayoutRequest,
    PayoutSplitResponse,
    MemberSplitItem
)

_ORGANIZATIONS: Dict[str, Dict[str, Any]] = {}
_MEMBERS: List[Dict[str, Any]] = []
_SHARED_INVENTORY: List[Dict[str, Any]] = []
_TASKS: List[Dict[str, Any]] = []
_ATTENDANCE: List[Dict[str, Any]] = []
_PAYOUTS: List[Dict[str, Any]] = []

class CooperativeService:
    @staticmethod
    def create_organization(leader_id: str, leader_name: str, payload: OrganizationCreate) -> OrganizationResponse:
        org_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        org_record = {
            "id": org_id,
            "name": payload.name,
            "registration_number": payload.registration_number,
            "org_type": payload.org_type,
            "leader_id": leader_id,
            "state": payload.state,
            "district": payload.district,
            "pincode": payload.pincode,
            "bank_account_info": payload.bank_account_info or {},
            "revenue_split_rules": payload.revenue_split_rules or {
                "coop_reserve_fund_percent": 10.0,
                "labor_share_percent": 60.0,
                "material_reimbursement_percent": 30.0
            },
            "created_at": now
        }
        _ORGANIZATIONS[org_id] = org_record

        # Automatically add the leader as first member
        leader_member = {
            "id": str(uuid.uuid4()),
            "org_id": org_id,
            "user_id": leader_id,
            "full_name": leader_name,
            "role": MemberRole.LEADER,
            "craft_specialization": "Master Artisan & Administration",
            "share_percentage": 25.0,
            "status": "active",
            "joined_at": now
        }
        _MEMBERS.append(leader_member)

        return CooperativeService.get_organization(org_id)

    @staticmethod
    def get_organization(org_id: str) -> Optional[OrganizationResponse]:
        org = _ORGANIZATIONS.get(org_id)
        if not org:
            return None
        
        members = [MemberResponse(**m) for m in _MEMBERS if m["org_id"] == org_id]
        pooled_count = sum(i["quantity_available"] for i in _SHARED_INVENTORY if i["org_id"] == org_id)

        return OrganizationResponse(
            id=org["id"],
            name=org["name"],
            registration_number=org["registration_number"],
            org_type=org["org_type"],
            leader_id=org["leader_id"],
            state=org["state"],
            district=org["district"],
            pincode=org["pincode"],
            member_count=len(members),
            total_pooled_items=pooled_count,
            bank_account_info=org["bank_account_info"],
            revenue_split_rules=org["revenue_split_rules"],
            members=members,
            created_at=org["created_at"]
        )

    @staticmethod
    def add_member(org_id: str, payload: MemberAddRequest) -> MemberResponse:
        if org_id not in _ORGANIZATIONS:
            raise ValueError("Organization not found")
        
        member_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        record = {
            "id": member_id,
            "org_id": org_id,
            "user_id": payload.user_id,
            "full_name": payload.full_name,
            "role": payload.role,
            "craft_specialization": payload.craft_specialization,
            "share_percentage": payload.share_percentage,
            "status": "active",
            "joined_at": now
        }
        _MEMBERS.append(record)
        return MemberResponse(**record)

    @staticmethod
    def list_members(org_id: str) -> List[MemberResponse]:
        return [MemberResponse(**m) for m in _MEMBERS if m["org_id"] == org_id]

    @staticmethod
    def pool_inventory(
        org_id: str,
        member_id: str,
        member_name: str,
        payload: SharedInventoryPoolRequest
    ) -> SharedInventoryResponse:
        if org_id not in _ORGANIZATIONS:
            raise ValueError("Organization not found")

        inv_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        record = {
            "id": inv_id,
            "org_id": org_id,
            "product_id": payload.product_id,
            "product_name": payload.product_name,
            "contributing_member_id": member_id,
            "contributing_member_name": member_name,
            "quantity_pooled": payload.quantity_pooled,
            "quantity_available": payload.quantity_pooled,
            "unit_cost_inr": payload.unit_cost_inr,
            "status": "available",
            "created_at": now
        }
        _SHARED_INVENTORY.append(record)
        return SharedInventoryResponse(**record)

    @staticmethod
    def list_shared_inventory(org_id: str) -> List[SharedInventoryResponse]:
        return [SharedInventoryResponse(**i) for i in _SHARED_INVENTORY if i["org_id"] == org_id]

    @staticmethod
    def create_task(org_id: str, payload: TaskCreate) -> TaskResponse:
        if org_id not in _ORGANIZATIONS:
            raise ValueError("Organization not found")

        t_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        record = {
            "id": t_id,
            "org_id": org_id,
            "assigned_to_member_id": payload.assigned_to_member_id,
            "assigned_to_name": payload.assigned_to_name,
            "title": payload.title,
            "description": payload.description,
            "target_units": payload.target_units,
            "completed_units": 0,
            "deadline": payload.deadline,
            "status": "in_progress",
            "created_at": now
        }
        _TASKS.append(record)
        return TaskResponse(**record)

    @staticmethod
    def list_tasks(org_id: str) -> List[TaskResponse]:
        return [TaskResponse(**t) for t in _TASKS if t["org_id"] == org_id]

    @staticmethod
    def log_attendance(org_id: str, payload: AttendanceLogRequest) -> AttendanceResponse:
        if org_id not in _ORGANIZATIONS:
            raise ValueError("Organization not found")

        att_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        w_date = payload.work_date or date.today().isoformat()

        record = {
            "id": att_id,
            "org_id": org_id,
            "member_id": payload.member_id,
            "member_name": payload.member_name,
            "work_date": w_date,
            "status": payload.status,
            "hours_logged": payload.hours_logged,
            "created_at": now
        }
        _ATTENDANCE.append(record)
        return AttendanceResponse(**record)

    @staticmethod
    def calculate_payout(org_id: str, payload: CalculatePayoutRequest) -> PayoutSplitResponse:
        org = _ORGANIZATIONS.get(org_id)
        if not org:
            raise ValueError("Organization not found")

        rules = org.get("revenue_split_rules", {
            "coop_reserve_fund_percent": 10.0,
            "labor_share_percent": 60.0,
            "material_reimbursement_percent": 30.0
        })

        coop_percent = rules.get("coop_reserve_fund_percent", 10.0)
        coop_fund_cut = round(payload.total_order_amount_inr * (coop_percent / 100.0), 2)
        distributable = payload.total_order_amount_inr - coop_fund_cut

        participating_members = [
            m for m in _MEMBERS
            if m["org_id"] == org_id and m["user_id"] in payload.participating_member_ids
        ]

        if not participating_members:
            # Fallback to all members in organization
            participating_members = [m for m in _MEMBERS if m["org_id"] == org_id]

        splits: List[MemberSplitItem] = []
        if participating_members:
            per_member_share = round(distributable / len(participating_members), 2)
            labor_part = round(per_member_share * 0.65, 2)
            mat_part = round(per_member_share - labor_part, 2)

            for m in participating_members:
                splits.append(MemberSplitItem(
                    member_id=m["user_id"],
                    member_name=m["full_name"],
                    role=m["role"],
                    payout_amount_inr=per_member_share,
                    labor_share_inr=labor_part,
                    material_reimbursement_inr=mat_part
                ))

        payout_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        res_record = {
            "id": payout_id,
            "org_id": org_id,
            "order_id": payload.order_id,
            "total_order_amount_inr": payload.total_order_amount_inr,
            "cooperative_fund_deduction_inr": coop_fund_cut,
            "splits": splits,
            "status": "approved",
            "created_at": now
        }
        _PAYOUTS.append(res_record)
        return PayoutSplitResponse(**res_record)
