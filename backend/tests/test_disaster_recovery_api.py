"""
Test suite for Disaster Recovery & Backup APIs.
Tests backup creation, listing, PITR simulation, migration rollback, and offline conflict resolution.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_list_and_create_backups():
    res = client.get("/api/v1/disaster-recovery/backups")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert len(data["backups"]) >= 1

    create_res = client.post(
        "/api/v1/disaster-recovery/backups/create",
        json={"backup_type": "manual_full", "note": "Pre-release snapshot 2026"}
    )
    assert create_res.status_code == 200
    created = create_res.json()
    assert created["status"] == "success"
    assert "backup_id" in created["backup"]

def test_simulate_point_in_time_recovery():
    res = client.post(
        "/api/v1/disaster-recovery/restore/simulate",
        json={"backup_id": "BKP-20260907-AUTO-01", "target_point_in_time": "2026-09-07T06:00:00Z"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    restore = data["restore_result"]
    assert restore["status"] == "completed_success"
    assert restore["checksum_verified"] is True
    assert restore["dry_run_passed"] is True

def test_migration_rollback():
    res = client.post(
        "/api/v1/disaster-recovery/migrations/rollback",
        json={"migration_version": "20260901_add_device_events"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["rollback_result"]["status"] == "success"

def test_offline_conflict_resolution():
    local_data = {"id": "prod-101", "stock": 42, "updated_at": "2026-09-07T06:10:00Z"}
    remote_data = {"id": "prod-101", "stock": 40, "price": 1250.0, "updated_at": "2026-09-07T06:05:00Z"}

    res = client.post(
        "/api/v1/disaster-recovery/conflicts/resolve",
        json={"local_entity": local_data, "remote_entity": remote_data}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    resolved = data["resolved_entity"]
    assert resolved["stock"] == 42
    assert resolved["price"] == 1250.0
    assert "conflict_resolved_at" in resolved

