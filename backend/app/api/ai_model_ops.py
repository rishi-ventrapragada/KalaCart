"""
AI Model Operations API (Phase 9).
Provides endpoints for:
- Listing and inspecting AI model registry & versions
- Registering new version artifacts
- Production version promotion & instant zero-downtime rollback
- A/B testing & canary experiment configuration
- Statistical drift detection & accuracy monitoring
- Human feedback labeling & RLHF dataset export
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.core.ai_model_ops import ai_model_ops

router = APIRouter(prefix="/api/v1/ai/ops", tags=["AI Model Operations & MLOps"])


class RegisterVersionRequest(BaseModel):
    model_name: str = Field(..., description="catalog_ai | pricing_ai | recommendation_ai | translation_ai | forecast_ai | negotiation_ai")
    version: str = Field(..., description="Semantic version string, e.g. v2.5.0")
    provider: str = Field(default="openrouter", description="openrouter | gemini | huggingface | custom_ml")
    foundation_model: str = Field(..., description="e.g. qwen/qwen3-32b, deepseek/deepseek-chat")
    system_prompt_version: str = Field(default="v1.0")
    hyperparameters: Dict[str, Any] = Field(default_factory=dict)
    evaluation_metrics: Dict[str, float] = Field(default_factory=dict)


class PromoteVersionRequest(BaseModel):
    model_name: str
    version: str


class RollbackRequest(BaseModel):
    model_name: str
    target_version: Optional[str] = None


class ABExperimentRequest(BaseModel):
    model_name: str
    version_a: str
    version_b: str
    traffic_split_b_pct: float = Field(default=20.0, ge=1.0, le=99.0)


class HumanFeedbackRequest(BaseModel):
    model_name: str
    model_version: str
    inference_id: str
    input_payload: Dict[str, Any]
    predicted_output: Dict[str, Any]
    human_rating: int = Field(..., ge=1, le=5)
    human_corrected_output: Optional[Dict[str, Any]] = None
    feedback_tag: str = Field(default="accurate", description="accurate | hallucination | price_too_high | craft_mismatch")
    notes: str = ""


@router.get("/registry", summary="Get all registered AI models, versions, and experiments")
def get_model_registry():
    return {"status": "success", "data": ai_model_ops.get_full_registry_summary()}


@router.post("/versions/register", summary="Register new AI model version artifact")
def register_version(payload: RegisterVersionRequest):
    try:
        v_obj = ai_model_ops.register_model_version(
            model_name=payload.model_name,
            version=payload.version,
            provider=payload.provider,
            foundation_model=payload.foundation_model,
            system_prompt_version=payload.system_prompt_version,
            hyperparameters=payload.hyperparameters,
            evaluation_metrics=payload.evaluation_metrics,
        )
        return {"status": "success", "registered_version": v_obj.to_dict()}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/promote", summary="Promote model version to active production master")
def promote_version(payload: PromoteVersionRequest):
    try:
        result = ai_model_ops.promote_version(payload.model_name, payload.version)
        return {"status": "success", "promotion": result}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/rollback", summary="Execute emergency zero-downtime rollback to previous stable model")
def rollback_model(payload: RollbackRequest):
    try:
        result = ai_model_ops.rollback_version(payload.model_name, payload.target_version)
        return {"status": "success", "rollback": result}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/ab-experiment", summary="Launch A/B or canary traffic split experiment")
def launch_ab_experiment(payload: ABExperimentRequest):
    try:
        exp = ai_model_ops.start_ab_experiment(
            model_name=payload.model_name,
            version_a=payload.version_a,
            version_b=payload.version_b,
            traffic_split_b_pct=payload.traffic_split_b_pct,
        )
        return {"status": "success", "experiment": exp}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/drift/{model_name}", summary="Detect concept & data drift for a model")
def detect_model_drift(model_name: str):
    try:
        drift = ai_model_ops.detect_drift(model_name)
        return {"status": "success", "drift_analysis": drift}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/feedback", summary="Submit artisan/human feedback & correction for RLHF")
def submit_human_feedback(payload: HumanFeedbackRequest):
    fb = ai_model_ops.record_feedback(
        model_name=payload.model_name,
        model_version=payload.model_version,
        inference_id=payload.inference_id,
        input_payload=payload.input_payload,
        predicted_output=payload.predicted_output,
        human_rating=payload.human_rating,
        human_corrected_output=payload.human_corrected_output,
        feedback_tag=payload.feedback_tag,
        notes=payload.notes,
    )
    return {"status": "recorded", "feedback": fb.to_dict()}


@router.get("/feedback/dataset", summary="Export RLHF dataset for fine-tuning")
def get_rlhf_dataset(
    model_name: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
):
    dataset = ai_model_ops.get_feedback_dataset(model_name=model_name, limit=limit)
    return {
        "status": "success",
        "total_samples": len(dataset),
        "samples": dataset,
    }
