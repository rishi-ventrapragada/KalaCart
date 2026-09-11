import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import brute_force_limiter

client = TestClient(app)


def test_brute_force_limiter():
    brute_force_limiter.reset()
    key = "test_ip_123.45.67.89"

    # 4 failed attempts shouldn't lock out (threshold is 5)
    for _ in range(4):
        locked = brute_force_limiter.record_failure(key)
        assert not locked

    is_locked, _ = brute_force_limiter.is_locked_out(key)
    assert not is_locked

    # 5th attempt locks out
    locked = brute_force_limiter.record_failure(key)
    assert locked
    is_locked, remaining = brute_force_limiter.is_locked_out(key)
    assert is_locked
    assert remaining > 0

    # Reset cleans up
    brute_force_limiter.record_success(key)
    is_locked, _ = brute_force_limiter.is_locked_out(key)
    assert not is_locked


def test_security_scorecard_data_endpoint():
    response = client.get("/api/v1/security/scorecard/data")
    assert response.status_code == 200
    data = response.json()
    assert "overall_security_score" in data
    assert data["overall_security_score"] >= 95.0
    assert data["security_grade"] in ["A+", "A"]
    assert "audits" in data
    assert "sql_injection_audit" in data["audits"]
    assert "row_level_security" in data["audits"]
    assert "storage_permissions" in data["audits"]
    assert "mobile_and_transport" in data["audits"]
    assert data["audits"]["sql_injection_audit"]["status"] == "PASSED"
    assert data["audits"]["row_level_security"]["status"] == "PASSED"


def test_security_scorecard_markdown_endpoint():
    response = client.get("/api/v1/security/scorecard")
    assert response.status_code == 200
    scorecard_md = response.text
    assert "# KalaCart Enterprise Security Scorecard" in scorecard_md
    assert "Certificate Pinning" in scorecard_md
    assert "Encrypted Database" in scorecard_md
    assert "Secure Key Storage" in scorecard_md
    assert "JWT Refresh Rotation" in scorecard_md
    assert "Root & Tamper Detection" in scorecard_md
    assert "Screenshot Protection" in scorecard_md
    assert "SQL Injection Audit" in scorecard_md
    assert "RLS Verification" in scorecard_md


def test_run_security_audit_post():
    response = client.post("/api/v1/security/audit/run")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert "results" in data
    assert data["results"]["compliance_verdict"] == "ENTERPRISE_READY_COMPLIANT"
