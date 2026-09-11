import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_get_pricing_explainability():
    """Verify 'Why was this price suggested?' plain reasoning and factor breakdown."""
    response = client.get("/api/v1/governance/explain/PRICING/prod_jaipur_vase_01")
    assert response.status_code == 200
    data = response.json()
    assert data["decision_type"] == "PRICING"
    assert "suggested price" in data["summary_headline"].lower()
    assert len(data["factors"]) >= 3
    assert any(f["factor_name"] == "Artisan Labor Duration" for f in data["factors"])
    assert data["fairness_compliance_status"] == "COMPLIANT"


def test_get_recommendation_explainability():
    """Verify 'Why am I seeing this product?' reasoning."""
    response = client.get("/api/v1/governance/explain/RECOMMENDATION/prod_banarasi_saree_02")
    assert response.status_code == 200
    data = response.json()
    assert data["decision_type"] == "RECOMMENDATION"
    assert "interest" in data["summary_headline"].lower()
    assert len(data["factors"]) >= 3
    assert data["confidence_score"] > 0.9


def test_get_trust_score_explainability():
    """Verify 'How is my trust score calculated?' breakdown."""
    response = client.get("/api/v1/governance/explain/TRUST_SCORE/artisan_sukmati_mandavi")
    assert response.status_code == 200
    data = response.json()
    assert data["decision_type"] == "TRUST_SCORE"
    assert "trust score" in data["summary_headline"].lower()
    assert any("dispatch" in f["factor_name"].lower() for f in data["factors"])


def test_list_ai_decisions_audit_log():
    """Verify admin view listing of immutable AI decisions."""
    response = client.get("/api/v1/governance/decisions")
    assert response.status_code == 200
    decisions = response.json()
    assert len(decisions) >= 5
    assert all("model_name" in d for d in decisions)
    assert all("input_features" in d for d in decisions)
    assert all("output_decision" in d for d in decisions)


def test_get_model_health_and_drift_metrics():
    """Verify production ML telemetry: accuracy, drift KL divergence, p95 latency."""
    response = client.get("/api/v1/governance/models/metrics")
    assert response.status_code == 200
    metrics = response.json()
    assert len(metrics) >= 4
    for m in metrics:
        assert m["accuracy_score"] > 0.9
        assert m["drift_divergence_kl"] < 0.05  # Within healthy drift threshold
        assert m["status"] == "HEALTHY"


def test_get_bias_and_fairness_report():
    """Verify demographic and state-level parity audit."""
    response = client.get("/api/v1/governance/bias-audit")
    assert response.status_code == 200
    report = response.json()
    assert report["audit_status"] == "PASSED"
    assert report["overall_fairness_index"] >= 95.0
    assert len(report["state_level_disparities"]) >= 5
    # All disparities must be within [0.90, 1.10]
    for st in report["state_level_disparities"]:
        assert 0.90 <= st["parity_ratio"] <= 1.10


def test_apply_human_override():
    """Verify human supervisor override adjusts decision output and preserves audit trail."""
    override_payload = {
        "decision_id": "dec-price-001",
        "admin_id": "admin_heritage_officer_07",
        "admin_name": "Dr. Ananya Varma",
        "override_reason": "Verified that this batch uses 24-carat liquid gold lustre highlighting, justifying premium baseline increase.",
        "adjusted_output": {
            "suggested_price_inr": 1850.0,
            "minimum_price_inr": 1600.0,
            "maximum_price_inr": 2200.0,
            "override_applied": True
        }
    }

    response = client.post("/api/v1/governance/override", json=override_payload)
    assert response.status_code == 201
    res = response.json()
    assert res["status"] == "APPLIED"
    assert "audit_checksum" in res
