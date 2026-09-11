from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.core.security import get_current_user
from app.models.enterprise_security import (
    DeviceVerificationRequest,
    UserSessionResponse,
    BiometricLoginRequest,
    AuditLogEntryCreate,
    AuditLogResponse,
    OfflineSyncReplayRequest,
    OfflineSyncResponse,
    SystemHealthResponse,
    BlueGreenDeploymentRequest,
    BlueGreenDeploymentResponse,
    EnterpriseReadinessReport
)
from app.services.enterprise_security_service import enterprise_security_service

router = APIRouter(prefix="/api/v1/enterprise", tags=["Enterprise Security & Reliability"])


# 1. Device Verification & Sessions
@router.post("/devices/verify", response_model=UserSessionResponse, status_code=status.HTTP_201_CREATED)
def verify_device(payload: DeviceVerificationRequest, request: Request, current_user: dict = Depends(get_current_user)):
    user_id = current_user.get("uid") or current_user.get("user_id") or "user_demo"
    client_ip = request.client.host if request.client else "127.0.0.1"
    return enterprise_security_service.verify_and_register_device(user_id, payload, ip_address=client_ip)


@router.get("/sessions", response_model=List[UserSessionResponse])
def get_user_sessions(current_user: dict = Depends(get_current_user)):
    user_id = current_user.get("uid") or current_user.get("user_id") or "user_demo"
    return enterprise_security_service.list_user_sessions(user_id)


@router.post("/sessions/{session_id}/revoke", response_model=UserSessionResponse)
def revoke_session(session_id: str, reason: Optional[str] = Query("Remote logout"), current_user: dict = Depends(get_current_user)):
    user_id = current_user.get("uid") or current_user.get("user_id") or "user_demo"
    res = enterprise_security_service.revoke_session(user_id, session_id, reason=reason)
    if not res:
        raise HTTPException(status_code=404, detail="Active user session not found")
    return res


# 2. Biometric FIDO2 Login
@router.post("/auth/biometric", response_model=dict)
def biometric_auth(payload: BiometricLoginRequest, current_user: dict = Depends(get_current_user)):
    user_id = current_user.get("uid") or current_user.get("user_id") or "user_demo"
    return enterprise_security_service.verify_biometric_login(user_id, payload)


# 3. Tamper-Evident Audit Logging
@router.get("/audit-logs", response_model=List[AuditLogResponse])
def get_audit_logs(limit: int = Query(50, ge=1, le=200), current_user: dict = Depends(get_current_user)):
    return enterprise_security_service.list_audit_logs(limit=limit)


# 4. Offline Queue Sync Replay
@router.post("/sync/offline-replay", response_model=OfflineSyncResponse)
def replay_offline_mutations(payload: OfflineSyncReplayRequest, current_user: dict = Depends(get_current_user)):
    user_id = current_user.get("uid") or current_user.get("user_id") or "user_demo"
    return enterprise_security_service.replay_offline_mutations(user_id, payload)


# 5. Observability & System Health Telemetry
@router.get("/health/telemetry", response_model=SystemHealthResponse)
def get_health_telemetry():
    return enterprise_security_service.get_system_health()


# 6. Blue-Green Deployment Orchestration
@router.post("/devops/blue-green", response_model=BlueGreenDeploymentResponse)
def switch_deployment(payload: BlueGreenDeploymentRequest, current_user: dict = Depends(get_current_user)):
    return enterprise_security_service.switch_blue_green_deployment(payload)


# 7. Enterprise Readiness Audit Report
@router.get("/reports/readiness", response_model=EnterpriseReadinessReport)
def get_enterprise_readiness():
    return enterprise_security_service.generate_readiness_report()
