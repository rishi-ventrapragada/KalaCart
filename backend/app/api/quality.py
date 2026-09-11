"""Quality Verification Workflow API (Phase 20).

Milestones:
  In Production -> Sample Uploaded -> Buyer Approved -> Dispatch Allowed
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import get_current_user
from app.database.connection import get_supabase_client
from app.models.quality import (
    QualitySubmissionCreate,
    QualityReviewRequest,
    QualityReviewAction,
    QualityStatus,
    QualityVerificationResponse,
)
from app.models.order import OrderStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/quality", tags=["Quality Verification Workflow"])

# In-memory store fallback when Supabase table isn't created
_quality_records: Dict[str, dict] = {}


def _get_user_id(current_user: dict) -> str:
    artisan = current_user.get("artisan") or {}
    art_id = artisan.get("id")
    if art_id:
        return str(art_id)
    uid = current_user.get("firebase_uid")
    if uid:
        return str(uid)
    return "00000000-0000-0000-0000-000000000001"


def _format_quality_response(record: dict) -> QualityVerificationResponse:
    status_str = record.get("status", QualityStatus.sample_uploaded.value)
    status_enum = QualityStatus(status_str)

    labels = {
        QualityStatus.pending_submission: "Pending Submission",
        QualityStatus.sample_uploaded: "Sample Uploaded (Awaiting Buyer Review)",
        QualityStatus.changes_requested: "Changes Requested by Buyer",
        QualityStatus.buyer_approved: "Buyer Approved (Dispatch Allowed)",
        QualityStatus.quality_rejected: "Quality Rejected",
    }

    l = float(record.get("length_cm", 0.0))
    w = float(record.get("width_cm", 0.0))
    h = float(record.get("height_cm", 0.0))
    wt = float(record.get("weight_kg", 0.0))

    dims = f"{l:.1f} × {w:.1f} × {h:.1f} cm" if (l > 0 or w > 0 or h > 0) else "Not specified"
    weight_str = f"{wt:.2f} kg" if wt > 0 else "Not specified"

    dispatch_ok = status_enum == QualityStatus.buyer_approved

    return QualityVerificationResponse(
        id=record.get("id", str(uuid.uuid4())),
        order_id=record.get("order_id"),
        status=status_enum,
        status_label=labels.get(status_enum, "In Review"),
        product_photos=record.get("product_photos", []),
        packaging_photos=record.get("packaging_photos", []),
        length_cm=l,
        width_cm=w,
        height_cm=h,
        weight_kg=wt,
        dimensions_display=dims,
        weight_display=weight_str,
        seller_notes=record.get("seller_notes"),
        buyer_notes=record.get("buyer_notes"),
        submitted_at=record.get("submitted_at"),
        reviewed_at=record.get("reviewed_at"),
        dispatch_allowed=dispatch_ok,
    )


@router.post("/orders/{order_id}/submit", response_model=QualityVerificationResponse, status_code=status.HTTP_201_CREATED)
async def submit_quality_dossier(
    order_id: str,
    submission: QualitySubmissionCreate,
    current_user: dict = Depends(get_current_user),
):
    """Seller uploads finished craft photos, packaging proof, dimensions, and weight."""
    user_id = _get_user_id(current_user)
    now_iso = datetime.now(timezone.utc).isoformat()

    record_id = str(uuid.uuid4())
    record = {
        "id": record_id,
        "order_id": order_id,
        "submitted_by": user_id,
        "status": QualityStatus.sample_uploaded.value,
        "product_photos": submission.product_photos,
        "packaging_photos": submission.packaging_photos,
        "length_cm": submission.length_cm,
        "width_cm": submission.width_cm,
        "height_cm": submission.height_cm,
        "weight_kg": submission.weight_kg,
        "seller_notes": submission.seller_notes,
        "buyer_notes": None,
        "submitted_at": now_iso,
        "reviewed_at": None,
    }

    try:
        client = get_supabase_client()
        client.table("quality_verifications").upsert(record, on_conflict="order_id").execute()
        # Also advance order to quality_check if currently in_production
        client.table("orders").update({"status": OrderStatus.quality_check.value, "updated_at": now_iso}).eq("id", order_id).execute()
    except Exception as exc:
        logger.info("Supabase quality check write fallback to mock: %s", exc)

    _quality_records[order_id] = record
    return _format_quality_response(record)


@router.get("/orders/{order_id}", response_model=QualityVerificationResponse, status_code=status.HTTP_200_OK)
async def get_quality_dossier(order_id: str):
    """Retrieve the quality verification record for an order."""
    try:
        client = get_supabase_client()
        res = client.table("quality_verifications").select("*").eq("order_id", order_id).limit(1).execute()
        if res.data and len(res.data) > 0:
            return _format_quality_response(res.data[0])
    except Exception as exc:
        logger.debug("Supabase quality check lookup fallback: %s", exc)

    if order_id in _quality_records:
        return _format_quality_response(_quality_records[order_id])

    # Return empty template if not yet submitted
    default_rec = {
        "id": str(uuid.uuid4()),
        "order_id": order_id,
        "status": QualityStatus.pending_submission.value,
        "product_photos": [],
        "packaging_photos": [],
        "length_cm": 0.0,
        "width_cm": 0.0,
        "height_cm": 0.0,
        "weight_kg": 0.0,
        "seller_notes": None,
        "buyer_notes": None,
        "submitted_at": None,
        "reviewed_at": None,
    }
    return _format_quality_response(default_rec)


@router.post("/orders/{order_id}/review", response_model=QualityVerificationResponse, status_code=status.HTTP_200_OK)
async def review_quality_dossier(
    order_id: str,
    review: QualityReviewRequest,
    current_user: dict = Depends(get_current_user),
):
    """Buyer reviews sample: approve_sample, request_changes, reject_quality, or approve_production."""
    record = _quality_records.get(order_id)
    try:
        client = get_supabase_client()
        res = client.table("quality_verifications").select("*").eq("order_id", order_id).limit(1).execute()
        if res.data:
            record = res.data[0]
    except Exception:
        pass

    if not record:
        record = {
            "id": str(uuid.uuid4()),
            "order_id": order_id,
            "product_photos": [],
            "packaging_photos": [],
            "length_cm": 0.0,
            "width_cm": 0.0,
            "height_cm": 0.0,
            "weight_kg": 0.0,
            "seller_notes": None,
        }

    now_iso = datetime.now(timezone.utc).isoformat()
    record["buyer_notes"] = review.review_notes
    record["reviewed_at"] = now_iso

    order_status_update = None

    if review.action in (QualityReviewAction.approve_sample, QualityReviewAction.approve_production):
        record["status"] = QualityStatus.buyer_approved.value
        order_status_update = OrderStatus.ready_to_dispatch.value
    elif review.action == QualityReviewAction.request_changes:
        record["status"] = QualityStatus.changes_requested.value
        order_status_update = OrderStatus.quality_check.value
    elif review.action == QualityReviewAction.reject_quality:
        record["status"] = QualityStatus.quality_rejected.value
        order_status_update = OrderStatus.disputed.value

    try:
        client = get_supabase_client()
        client.table("quality_verifications").upsert(record, on_conflict="order_id").execute()
        if order_status_update:
            client.table("orders").update({"status": order_status_update, "updated_at": now_iso}).eq("id", order_id).execute()
    except Exception as exc:
        logger.info("Supabase review update fallback to mock: %s", exc)

    _quality_records[order_id] = record
    return _format_quality_response(record)
