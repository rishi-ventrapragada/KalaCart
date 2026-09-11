"""
Verifiable Digital Identity API Router (KalaCart V10)
Exposes issuance of W3C Verifiable Credentials, offline QR verification,
issuers registry, and revocation management.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

from app.core.verifiable_identity import (
    verifiable_identity_engine,
    CredentialType,
    VerificationResultStatus,
)

router = APIRouter(prefix="/api/v1/identity", tags=["Verifiable Digital Identity (V10)"])


class IssueCredentialRequest(BaseModel):
    subject_did: str
    issuer_did: str
    credential_type: str = "artisan_identity"
    claims: Dict[str, Any]
    artisan_id: Optional[str] = None
    expiration_date: Optional[str] = None


class VerifyQROfflineRequest(BaseModel):
    qr_token: str


class RevokeCredentialRequest(BaseModel):
    credential_id: str
    reason: str


@router.get("/issuers")
async def get_credential_issuers():
    """List trusted government and craft council credential issuers."""
    return {
        "count": len(verifiable_identity_engine.issuers),
        "issuers": [i.model_dump() for i in verifiable_identity_engine.issuers.values()],
    }


@router.get("/credentials/{credential_id}")
async def get_credential_details(credential_id: str):
    """Retrieve full verifiable credential and cryptographic signature proof."""
    vc = verifiable_identity_engine.credentials.get(credential_id)
    if not vc:
        raise HTTPException(status_code=404, detail=f"Credential '{credential_id}' not found.")
    return vc.to_dict()


@router.get("/artisan/{subject_did}")
async def get_artisan_credentials(subject_did: str):
    """Retrieve all verifiable credentials issued to an artisan DID."""
    matched = [
        vc.to_dict()
        for vc in verifiable_identity_engine.credentials.values()
        if vc.subject_did == subject_did
    ]
    return {
        "subject_did": subject_did,
        "count": len(matched),
        "credentials": matched,
    }


@router.post("/issue")
async def issue_credential(req: IssueCredentialRequest):
    """Issue a new tamper-proof W3C verifiable credential with an offline-verifiable QR token."""
    try:
        c_type = CredentialType(req.credential_type)
    except ValueError:
        c_type = CredentialType.ARTISAN_IDENTITY

    try:
        vc = verifiable_identity_engine.issue_verifiable_credential(
            subject_did=req.subject_did,
            issuer_did=req.issuer_did,
            credential_type=c_type,
            claims=req.claims,
            artisan_id=req.artisan_id,
            expiration_date=req.expiration_date,
        )
        return {
            "status": "success",
            "message": "Verifiable credential successfully signed and issued.",
            "credential": vc.to_dict(),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/verify-offline")
async def verify_credential_offline(req: VerifyQROfflineRequest):
    """
    Offline Verification Endpoint:
    Cryptographically verifies the authenticity and signatures of the self-contained QR token
    without database lookups.
    """
    result = verifiable_identity_engine.verify_credential_offline(req.qr_token)
    return result


@router.post("/revoke")
async def revoke_credential(req: RevokeCredentialRequest):
    """Revoke a verifiable credential."""
    success = verifiable_identity_engine.revoke_credential(
        credential_id=req.credential_id,
        reason=req.reason,
    )
    if not success:
        raise HTTPException(status_code=404, detail=f"Credential '{req.credential_id}' not found.")
    return {
        "status": "success",
        "message": f"Credential '{req.credential_id}' has been revoked.",
    }
