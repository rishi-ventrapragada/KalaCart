from fastapi.testclient import TestClient
import pytest
from app.main import app
from app.core.security import get_current_user

@pytest.fixture(autouse=True)
def override_auth():
    app.dependency_overrides[get_current_user] = lambda: {
        "uid": "enterprise-admin-001",
        "email": "security.admin@kalacart.in",
        "role": "admin",
        "name": "Enterprise Security Officer"
    }
    yield
    app.dependency_overrides.clear()

def test_device_verification_and_multi_device_sessions():
    client = TestClient(app)
    # 1. Verify and register device session
    verify_payload = {
        "device_name": "Google Pixel 8 Pro (Hardware TEE)",
        "device_fingerprint": "fp_pix8_98a72b14c5",
        "attestation_type": "play_integrity",
        "attestation_token": "token_hardware_backed_attestation_mock",
        "biometric_enrolled": True
    }
    res_dev = client.post("/api/v1/enterprise/devices/verify", json=verify_payload)
    assert res_dev.status_code == 201, res_dev.text
    session = res_dev.json()
    sess_id = session["session_id"]
    assert session["attestation_verified"] is True
    assert session["biometric_enrolled"] is True
    assert session["is_revoked"] is False

    # 2. List active user sessions
    res_list = client.get("/api/v1/enterprise/sessions")
    assert res_list.status_code == 200
    sessions = res_list.json()
    assert len(sessions) >= 1

    # 3. Remote Revoke Session
    res_revoke = client.post(f"/api/v1/enterprise/sessions/{sess_id}/revoke?reason=Lost%20Device")
    assert res_revoke.status_code == 200
    assert res_revoke.json()["is_revoked"] is True
    assert res_revoke.json()["revoked_reason"] == "Lost Device"

def test_biometric_fido2_login_and_tamper_evident_audit_log():
    client = TestClient(app)
    # 1. Biometric login
    bio_payload = {
        "device_fingerprint": "fp_pix8_98a72b14c5",
        "challenge": "chal_98a7b612e",
        "signature": "sig_ecc_secp256r1_valid",
        "public_key_credential_id": "cred_fido2_99a81"
    }
    res_bio = client.post("/api/v1/enterprise/auth/biometric", json=bio_payload)
    assert res_bio.status_code == 200
    assert res_bio.json()["authenticated"] is True
    assert "access_token" in res_bio.json()

    # 2. Audit log list & cryptographic hash verification
    res_audit = client.get("/api/v1/enterprise/audit-logs")
    assert res_audit.status_code == 200
    logs = res_audit.json()
    assert len(logs) >= 2
    for log in logs:
        assert len(log["record_hash"]) == 64  # SHA-256 length
        assert log["prev_record_hash"] is not None

def test_offline_queue_replay_and_deterministic_conflict_resolution():
    client = TestClient(app)
    # Send offline transaction queue
    replay_payload = {
        "mutations": [
            {
                "client_mutation_id": "mut_offline_001",
                "entity_type": "inventory",
                "entity_id": "prod_blue_pottery_vase",
                "mutation_type": "update",
                "client_version": 1,  # Behind server version 2 -> triggers 3-way merge
                "payload": {"stock": 18, "notes": "Offline local stock count update"}
            },
            {
                "client_mutation_id": "mut_offline_002",
                "entity_type": "order",
                "entity_id": "ord_offline_draft_88",
                "mutation_type": "create",
                "client_version": 3,  # Ahead/fresh -> client authoritative
                "payload": {"total_amount": 2400.0, "status": "draft"}
            }
        ]
    }
    res_replay = client.post("/api/v1/enterprise/sync/offline-replay", json=replay_payload)
    assert res_replay.status_code == 200, res_replay.text
    sync_resp = res_replay.json()
    assert sync_resp["total_replayed"] == 2
    assert sync_resp["successful_count"] == 2
    assert sync_resp["conflicts_resolved"] == 1
    statuses = [r["status"] for r in sync_resp["results"]]
    assert "conflict_resolved" in statuses
    assert "synced" in statuses

def test_system_health_blue_green_and_enterprise_readiness():
    client = TestClient(app)
    # 1. System Health Telemetry
    res_health = client.get("/api/v1/enterprise/health/telemetry")
    assert res_health.status_code == 200
    health = res_health.json()
    assert health["status"] == "healthy"
    assert health["uptime_percentage"] >= 99.9
    assert health["p99_latency_ms"] < 100.0

    # 2. Blue-Green Traffic Switch
    bg_payload = {
        "target_slot": "green",
        "release_version": "v5.3.0-enterprise",
        "traffic_weight_percent": 100,
        "migration_checksum": "sha256:4a8b792c0192e"
    }
    res_bg = client.post("/api/v1/enterprise/devops/blue-green", json=bg_payload)
    assert res_bg.status_code == 200
    assert res_bg.json()["active_slot"] == "green"
    assert res_bg.json()["release_version"] == "v5.3.0-enterprise"

    # 3. Enterprise Readiness Audit Report
    res_report = client.get("/api/v1/enterprise/reports/readiness")
    assert res_report.status_code == 200
    rep = res_report.json()
    assert rep["compliance_score_percent"] >= 95.0
    assert "READY" in rep["soc2_hipaa_iso27001_readiness"]
    assert rep["biometric_fido2_enabled"] is True
    assert rep["offline_queue_vector_clock_verified"] is True
    assert rep["blue_green_zero_downtime_verified"] is True
