from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class DeviceVerificationRequest(BaseModel):
    device_name: str
    device_fingerprint: str
    attestation_type: str = "play_integrity"  # play_integrity, safetynet, device_check, fido2_webauthn
    attestation_token: str
    biometric_enrolled: bool = False


class UserSessionResponse(BaseModel):
    session_id: str
    user_id: str
    device_name: str
    device_fingerprint: str
    attestation_verified: bool
    biometric_enrolled: bool
    ip_address: Optional[str] = None
    last_active_at: str
    expires_at: str
    is_revoked: bool
    revoked_reason: Optional[str] = None


class BiometricLoginRequest(BaseModel):
    device_fingerprint: str
    challenge: str
    signature: str
    public_key_credential_id: str


class AuditLogEntryCreate(BaseModel):
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    device_fingerprint: Optional[str] = None
    payload: Dict[str, Any] = {}


class AuditLogResponse(BaseModel):
    id: str
    actor_id: str
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    prev_record_hash: Optional[str] = None
    record_hash: str
    payload: Dict[str, Any] = {}
    created_at: str


class OfflineMutationItem(BaseModel):
    client_mutation_id: str
    entity_type: str
    entity_id: str
    mutation_type: str  # create, update, delete
    client_version: int
    payload: Dict[str, Any]


class OfflineSyncReplayRequest(BaseModel):
    mutations: List[OfflineMutationItem]


class OfflineSyncResultItem(BaseModel):
    client_mutation_id: str
    status: str  # synced, conflict_resolved, rejected
    resolved_version: int
    resolution_strategy: str
    applied_payload: Dict[str, Any]


class OfflineSyncResponse(BaseModel):
    total_replayed: int
    successful_count: int
    conflicts_resolved: int
    results: List[OfflineSyncResultItem]


class SystemHealthResponse(BaseModel):
    status: str  # healthy, degraded, critical
    uptime_percentage: float
    p99_latency_ms: float
    db_replication_lag_ms: float
    active_connections: int
    error_rate_percent: float
    last_backup_snapshot_at: str
    last_dr_drill_at: str
    disaster_recovery_rpo: str
    disaster_recovery_rto: str


class BlueGreenDeploymentRequest(BaseModel):
    target_slot: str  # blue, green
    release_version: str
    traffic_weight_percent: int = 100
    migration_checksum: str


class BlueGreenDeploymentResponse(BaseModel):
    release_version: str
    active_slot: str
    traffic_weight_percent: int
    migration_checksum: str
    status: str
    deployed_at: str


class EnterpriseReadinessReport(BaseModel):
    compliance_score_percent: float
    soc2_hipaa_iso27001_readiness: str
    encryption_standard: str
    biometric_fido2_enabled: bool
    audit_tamper_evident_status: str
    offline_queue_vector_clock_verified: bool
    blue_green_zero_downtime_verified: bool
    disaster_recovery_status: str
    generated_at: str
    executive_summary: str
