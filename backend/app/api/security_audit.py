"""
Enterprise Security Audit API Endpoints (Phase 8).
Serves security scorecards, RLS compliance reports, and SQL injection audit verifications.
"""

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from app.core.security_audit import security_audit_engine

router = APIRouter(prefix="/api/v1/security", tags=["Enterprise Security Hardening"])


@router.get("/scorecard", response_class=PlainTextResponse)
async def get_security_scorecard_markdown():
    """
    Returns the comprehensive enterprise security scorecard in markdown format.
    """
    data = security_audit_engine.run_full_security_audit()
    return security_audit_engine.generate_scorecard_markdown(data)


@router.get("/scorecard/data")
async def get_security_scorecard_data():
    """
    Returns the security scorecard and audit results in structured JSON format.
    """
    return security_audit_engine.run_full_security_audit()


@router.post("/audit/run")
async def run_security_audit():
    """
    Executes a fresh enterprise security audit across all 12 dimensions.
    """
    results = security_audit_engine.run_full_security_audit()
    return {"status": "completed", "results": results}
