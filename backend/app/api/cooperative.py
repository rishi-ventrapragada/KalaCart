from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional, Any
from app.core.security import get_current_user
from app.models.cooperative import (
    OrganizationCreate,
    OrganizationResponse,
    MemberAddRequest,
    MemberResponse,
    SharedInventoryPoolRequest,
    SharedInventoryResponse,
    TaskCreate,
    TaskResponse,
    AttendanceLogRequest,
    AttendanceResponse,
    CalculatePayoutRequest,
    PayoutSplitResponse
)
from app.services.cooperative_service import CooperativeService

router = APIRouter(prefix="/api/v1/cooperative", tags=["Cooperative & SHG Workspace"])

def _get_user_info(current_user: Any) -> tuple[str, str]:
    if isinstance(current_user, dict):
        uid = current_user.get("uid") or current_user.get("id", "artisan-anon")
        name = current_user.get("name") or current_user.get("full_name", "Artisan Leader")
        return uid, name
    uid = getattr(current_user, "id", getattr(current_user, "uid", "artisan-anon"))
    name = getattr(current_user, "full_name", getattr(current_user, "name", "Artisan Leader"))
    return uid, name

@router.post("/organizations", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
def create_organization(
    payload: OrganizationCreate,
    current_user: Any = Depends(get_current_user)
):
    """
    Register a Self Help Group (SHG), artisan producer cooperative, or craft trust.
    """
    uid, name = _get_user_info(current_user)
    return CooperativeService.create_organization(
        leader_id=uid,
        leader_name=name,
        payload=payload
    )

@router.get("/organizations/{org_id}", response_model=OrganizationResponse)
def get_organization_dashboard(org_id: str):
    """
    Retrieve cooperative workspace dashboard, member counts, pooled inventory, and rules.
    """
    org = CooperativeService.get_organization(org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org

@router.post("/organizations/{org_id}/members", response_model=MemberResponse, status_code=status.HTTP_201_CREATED)
def add_organization_member(
    org_id: str,
    payload: MemberAddRequest,
    current_user: Any = Depends(get_current_user)
):
    """
    Add members with specialized roles (Leader, Manager, Accountant, Member).
    """
    try:
        return CooperativeService.add_member(org_id=org_id, payload=payload)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/organizations/{org_id}/members", response_model=List[MemberResponse])
def list_organization_members(org_id: str):
    """
    List all active members and their assigned craft specializations.
    """
    return CooperativeService.list_members(org_id=org_id)

@router.post("/organizations/{org_id}/shared-inventory", response_model=SharedInventoryResponse, status_code=status.HTTP_201_CREATED)
def pool_shared_inventory(
    org_id: str,
    payload: SharedInventoryPoolRequest,
    current_user: Any = Depends(get_current_user)
):
    """
    Artisan member contributes stock into the cooperative shared inventory and storefront.
    """
    uid, name = _get_user_info(current_user)
    try:
        return CooperativeService.pool_inventory(
            org_id=org_id,
            member_id=uid,
            member_name=name,
            payload=payload
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/organizations/{org_id}/shared-inventory", response_model=List[SharedInventoryResponse])
def list_shared_inventory(org_id: str):
    """
    List pooled items in the shared cooperative inventory ledger.
    """
    return CooperativeService.list_shared_inventory(org_id=org_id)

@router.post("/organizations/{org_id}/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def assign_production_task(
    org_id: str,
    payload: TaskCreate,
    current_user: Any = Depends(get_current_user)
):
    """
    Assign production milestones and batch targets to cooperative members.
    """
    try:
        return CooperativeService.create_task(org_id=org_id, payload=payload)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/organizations/{org_id}/tasks", response_model=List[TaskResponse])
def list_production_tasks(org_id: str):
    """
    List all active tasks and production progress.
    """
    return CooperativeService.list_tasks(org_id=org_id)

@router.post("/organizations/{org_id}/attendance", response_model=AttendanceResponse, status_code=status.HTTP_201_CREATED)
def log_member_attendance(
    org_id: str,
    payload: AttendanceLogRequest,
    current_user: Any = Depends(get_current_user)
):
    """
    Log daily artisan workshop attendance and work hours.
    """
    try:
        return CooperativeService.log_attendance(org_id=org_id, payload=payload)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/organizations/{org_id}/payouts/calculate", response_model=PayoutSplitResponse)
def calculate_revenue_sharing_payout(
    org_id: str,
    payload: CalculatePayoutRequest,
    current_user: Any = Depends(get_current_user)
):
    """
    Transparently calculate automated revenue splits and member bank payouts.
    """
    try:
        return CooperativeService.calculate_payout(org_id=org_id, payload=payload)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
