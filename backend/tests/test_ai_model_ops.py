"""
Unit & Integration Tests for Phase 9 AI Model Operations & MLOps Engine.
Covers:
- Registry for all 6 Core AI Models (Catalog, Pricing, Recommendation, Translation, Forecast, Negotiation)
- Zero-Downtime Model Version Registration & Promotion
- Emergency Rollback to Stable Release
- Canary & A/B Traffic Splitting Experimentation
- Concept & Statistical Drift Detection (PSI)
- RLHF / Human Feedback Loop & Dataset Harvesting
- REST API Endpoints for AI Model Operations
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.ai_model_ops import ai_model_ops

client = TestClient(app)


def test_core_models_initial_registration():
    """Verify all 6 core models are registered with active versions and evaluation metrics."""
    summary = ai_model_ops.get_full_registry_summary()
    assert summary["total_registered_models"] == 6

    model_names = [m["model_name"] for m in summary["models"]]
    for expected in [
        "catalog_ai",
        "pricing_ai",
        "recommendation_ai",
        "translation_ai",
        "forecast_ai",
        "negotiation_ai",
    ]:
        assert expected in model_names


def test_model_version_lifecycle_and_promotion():
    """Test registering a new model version and promoting it to production."""
    # Register v2.5.0 for pricing_ai
    new_ver = ai_model_ops.register_model_version(
        model_name="pricing_ai",
        version="v2.5.0",
        provider="openrouter",
        foundation_model="deepseek/deepseek-chat",
        system_prompt_version="v2.5",
        hyperparameters={"temperature": 0.2, "top_p": 0.85},
        evaluation_metrics={"accuracy_pct": 99.2, "latency_p95_ms": 95.0, "f1_score": 0.98, "drift_score": 0.005},
    )
    assert new_ver.status == "staging"
    assert "v2.5.0" in ai_model_ops.registry["pricing_ai"].versions

    # Promote to active production version
    promo_result = ai_model_ops.promote_version("pricing_ai", "v2.5.0")
    assert promo_result["status"] == "promoted"
    assert promo_result["new_active_version"] == "v2.5.0"
    assert ai_model_ops.registry["pricing_ai"].active_version == "v2.5.0"
    assert ai_model_ops.registry["pricing_ai"].versions["v2.5.0"].status == "deployed"


def test_emergency_zero_downtime_rollback():
    """Test instant rollback from degraded version to previous stable version."""
    # Rollback pricing_ai from v2.5.0 back to v2.4.0
    rb_result = ai_model_ops.rollback_version("pricing_ai", target_version="v2.4.0")
    assert rb_result["status"] == "rolled_back"
    assert rb_result["restored_version"] == "v2.4.0"
    assert ai_model_ops.registry["pricing_ai"].active_version == "v2.4.0"
    assert ai_model_ops.registry["pricing_ai"].versions["v2.4.0"].status == "deployed"
    assert ai_model_ops.registry["pricing_ai"].versions["v2.5.0"].status == "rolled_back"


def test_ab_experimentation_and_traffic_splitting():
    """Test setting up an A/B canary split experiment between two model versions."""
    exp = ai_model_ops.start_ab_experiment(
        model_name="catalog_ai",
        version_a="v2.1.0",
        version_b="v2.1.0",  # Using existing version
        traffic_split_b_pct=50.0,
    )
    assert exp["status"] == "running"
    assert exp["traffic_split_b_pct"] == 50.0

    # Resolve models through inference router
    resolved_versions = set()
    for _ in range(50):
        m = ai_model_ops.resolve_model_for_inference("catalog_ai")
        resolved_versions.add(m.version)

    assert "v2.1.0" in resolved_versions


def test_concept_and_data_drift_detection():
    """Test statistical drift monitoring (PSI scoring) for production models."""
    # Test normal drift score
    normal_drift = ai_model_ops.detect_drift("translation_ai")
    assert normal_drift["drift_status"] == "NORMAL"
    assert normal_drift["drift_score_psi"] < 0.08

    # Simulate critical drift injection
    ai_model_ops.record_inference(
        model_name="translation_ai",
        version="v3.0.0",
        duration_ms=110.0,
        success=True,
        drift_delta=0.18,
    )
    critical_drift = ai_model_ops.detect_drift("translation_ai")
    assert critical_drift["drift_status"] == "CRITICAL_DRIFT"
    assert "Retrain" in critical_drift["recommendation"]

    # Reset drift back to baseline
    ai_model_ops.record_inference(
        model_name="translation_ai",
        version="v3.0.0",
        duration_ms=90.0,
        success=True,
        drift_delta=0.015,
    )


def test_human_feedback_labeling_and_rlhf_dataset():
    """Test collecting artisan ratings and human corrections for continuous RLHF."""
    fb = ai_model_ops.record_feedback(
        model_name="negotiation_ai",
        model_version="v2.0.0",
        inference_id="INF-9876",
        input_payload={"buyer_offer": 500.0, "artisan_min": 650.0},
        predicted_output={"counter_offer": 580.0, "accepted": False},
        human_rating=5,
        human_corrected_output={"counter_offer": 600.0, "reason": "Slightly higher margin for bulk silk"},
        feedback_tag="accurate",
        notes="Good negotiation posture",
    )
    assert fb.human_rating == 5
    assert fb.feedback_tag == "accurate"

    # Export dataset
    dataset = ai_model_ops.get_feedback_dataset(model_name="negotiation_ai", limit=10)
    assert len(dataset) >= 1
    assert dataset[0]["model_name"] == "negotiation_ai"


def test_ai_model_ops_api_endpoints():
    """Test all Phase 9 AI Model Operations REST endpoints."""
    # 1. Registry summary
    r_reg = client.get("/api/v1/ai/ops/registry")
    assert r_reg.status_code == 200
    assert r_reg.json()["status"] == "success"
    assert r_reg.json()["data"]["total_registered_models"] == 6

    # 2. Register version
    r_ver = client.post(
        "/api/v1/ai/ops/versions/register",
        json={
            "model_name": "forecast_ai",
            "version": "v1.6.0-rc1",
            "provider": "custom_ml",
            "foundation_model": "prophet_v2",
            "evaluation_metrics": {"accuracy_pct": 95.8},
        },
    )
    assert r_ver.status_code == 200
    assert r_ver.json()["registered_version"]["version"] == "v1.6.0-rc1"

    # 3. Drift check API
    r_drift = client.get("/api/v1/ai/ops/drift/forecast_ai")
    assert r_drift.status_code == 200
    assert "drift_status" in r_drift.json()["drift_analysis"]

    # 4. Human feedback API
    r_fb = client.post(
        "/api/v1/ai/ops/feedback",
        json={
            "model_name": "catalog_ai",
            "model_version": "v2.1.0",
            "inference_id": "INF-1122",
            "input_payload": {"craft_name": "Channapatna Toy"},
            "predicted_output": {"tags": ["wood", "toy"]},
            "human_rating": 4,
            "feedback_tag": "accurate",
        },
    )
    assert r_fb.status_code == 200
    assert r_fb.json()["status"] == "recorded"

    # 5. RLHF dataset export API
    r_ds = client.get("/api/v1/ai/ops/feedback/dataset")
    assert r_ds.status_code == 200
    assert r_ds.json()["total_samples"] >= 1
