"""
Legal & Compliance API Endpoints for KalaCart.
Serves statutory policies, DPDP Act 2023 compliance verification, and GST standards.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, List, Any
from app.core.legal_compliance import (
    LEGAL_POLICIES,
    DPDP_COMPLIANCE_CHECKLIST,
    GST_COMPLIANCE_STANDARDS,
)

router = APIRouter(prefix="/legal", tags=["Legal & Regulatory Compliance"])

@router.get("/policies", summary="Get index of all statutory policies")
def get_all_policies():
    return {
        "status": "success",
        "policies": [
            {"key": k, "title": v["title"], "version": v["version"], "last_updated": v["last_updated"], "summary": v["summary"]}
            for k, v in LEGAL_POLICIES.items()
        ]
    }

@router.get("/policies/{policy_key}", summary="Get specific policy content")
def get_policy(policy_key: str):
    if policy_key not in LEGAL_POLICIES:
        raise HTTPException(status_code=404, detail="Policy not found")
    return {"status": "success", "policy": LEGAL_POLICIES[policy_key]}

@router.get("/dpdp-checklist", summary="Get Indian DPDP Act 2023 Compliance Checklist")
def get_dpdp_checklist():
    return {"status": "success", "dpdp_compliance": DPDP_COMPLIANCE_CHECKLIST}

@router.get("/gst-compliance", summary="Get GST Invoice & Tax Compliance Standards")
def get_gst_compliance():
    return {"status": "success", "gst_standards": GST_COMPLIANCE_STANDARDS}

