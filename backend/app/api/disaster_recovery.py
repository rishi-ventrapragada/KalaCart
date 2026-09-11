"""
Disaster Recovery & Backup API for KalaCart.
Provides endpoints for automated DB & storage backup snapshots, PITR simulation,
migration rollback, and offline conflict resolution wizard.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

from app.core.disaster_recovery import disaster_recovery_engine
from app.core.security import get_current_user

router = APIRouter(prefix="/disaster-recovery", tags=["Disaster Recovery & Backups"])

class BackupCreateRequest(BaseModel):
    backup_type: str = "manual_full"
    note: str = ""

class RestoreSimulationRequest(BaseModel):
    backup_id: str
    target_point_in_time: Optional[str] = None

class MigrationRollbackRequest(BaseModel):
    migration_version: str

class OfflineConflictResolutionRequest(BaseModel):
    local_entity: Dict[str, Any]
    remote_entity: Dict[str, Any]

@router.get("/backups", summary="List all versioned backups")
def list_backups():
    return {"status": "success", "backups": disaster_recovery_engine.list_backups()}

@router.post("/backups/create", summary="Trigger automated or manual backup snapshot")
def create_backup(payload: BackupCreateRequest):
    record = disaster_recovery_engine.create_backup(payload.backup_type, payload.note)
    return {"status": "success", "backup": record}

@router.post("/restore/simulate", summary="Simulate Point-in-Time Recovery (PITR) & restore wizard")
def simulate_restore(payload: RestoreSimulationRequest):
    result = disaster_recovery_engine.simulate_restore(payload.backup_id, payload.target_point_in_time)
    return {"status": "success", "restore_result": result}

@router.post("/migrations/rollback", summary="Roll back database schema migration")
def rollback_migration(payload: MigrationRollbackRequest):
    result = disaster_recovery_engine.rollback_migration(payload.migration_version)
    return {"status": "success", "rollback_result": result}

@router.post("/conflicts/resolve", summary="Resolve offline-first data sync conflicts")
def resolve_offline_conflict(payload: OfflineConflictResolutionRequest):
    resolved = disaster_recovery_engine.resolve_offline_conflict(payload.local_entity, payload.remote_entity)
    return {"status": "success", "resolved_entity": resolved}

