"""
Quantum-Ready Security Layer API Router (KalaCart V10)
Exposes algorithm agility, document signing/verification, authenticated encryption,
key rotation, and tamper alerts.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

from app.core.quantum_security import (
    quantum_security_manager,
    CryptoAlgorithmSuite,
    KeyType,
)

router = APIRouter(prefix="/api/v1/security-pqc", tags=["Quantum-Ready Security Layer (V10)"])


class SignDocumentRequest(BaseModel):
    key_alias: str
    document_payload: str
    caller_service: str = "artisan_smart_contracts"


class VerifyDocumentRequest(BaseModel):
    key_alias: str
    document_payload: str
    signature_token: str


class EncryptPayloadRequest(BaseModel):
    key_alias: str
    plaintext: str
    associated_context: str = ""


class DecryptPayloadRequest(BaseModel):
    key_alias: str
    ciphertext_envelope: str
    associated_context: str = ""


class RotateKeyRequest(BaseModel):
    key_alias: str


@router.get("/keys")
async def list_managed_keys():
    """Retrieve all managed cryptographic keys, current versions, and algorithm suites."""
    keys = [k.model_dump() for k in quantum_security_manager.managed_keys.values()]
    return {
        "active_provider": quantum_security_manager.provider.get_provider_name(),
        "keys_count": len(keys),
        "keys": keys,
    }


@router.get("/tamper-alerts")
async def get_tamper_alerts():
    """Retrieve cryptographic tamper detection logs and alerts."""
    return {
        "count": len(quantum_security_manager.tamper_alerts),
        "alerts": quantum_security_manager.tamper_alerts,
    }


@router.post("/sign")
async def sign_document(req: SignDocumentRequest):
    """Digitally sign a business document using post-quantum / hybrid signature suites."""
    res = quantum_security_manager.sign_business_document(
        key_alias=req.key_alias,
        document_payload=req.document_payload,
        caller_service=req.caller_service,
    )
    return res


@router.post("/verify")
async def verify_document(req: VerifyDocumentRequest):
    """Verify document signature against managed key alias without hardcoded algorithms."""
    is_valid = quantum_security_manager.verify_business_document(
        key_alias=req.key_alias,
        document_payload=req.document_payload,
        signature_token=req.signature_token,
    )
    return {
        "key_alias": req.key_alias,
        "valid": is_valid,
        "verification_status": "verified" if is_valid else "signature_mismatch",
    }


@router.post("/encrypt")
async def encrypt_payload(req: EncryptPayloadRequest):
    """Encrypt sensitive payload using authenticated envelope encryption (Kyber1024 / AES-GCM)."""
    res = quantum_security_manager.encrypt_sensitive_payload(
        key_alias=req.key_alias,
        plaintext=req.plaintext,
        associated_context=req.associated_context,
    )
    return res


@router.post("/decrypt")
async def decrypt_payload(req: DecryptPayloadRequest):
    """Decrypt payload with tamper detection verification."""
    try:
        pt = quantum_security_manager.decrypt_sensitive_payload(
            key_alias=req.key_alias,
            ciphertext_envelope=req.ciphertext_envelope,
            associated_context=req.associated_context,
        )
        return {
            "status": "success",
            "plaintext": pt,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/keys/rotate")
async def rotate_key(req: RotateKeyRequest):
    """Rotate key version in hardware keystore abstraction."""
    try:
        updated_key = quantum_security_manager.rotate_cryptographic_key(key_alias=req.key_alias)
        return {
            "status": "success",
            "message": f"Key '{req.key_alias}' rotated to version {updated_key.key_version}.",
            "key": updated_key.model_dump(),
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
