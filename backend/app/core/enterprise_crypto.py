import hashlib
import json
import secrets
from typing import Dict, Any, Optional


class EnterpriseCrypto:
    """Cryptographic utilities for SHA-256 tamper-evident hash chaining and token hashing."""

    @staticmethod
    def compute_sha256_hash(data: str) -> str:
        return hashlib.sha256(data.encode("utf-8")).hexdigest()

    @staticmethod
    def compute_audit_hash(actor_id: str, action: str, resource_type: str, resource_id: Optional[str], payload: Dict[str, Any], prev_hash: Optional[str]) -> str:
        canonical_payload = json.dumps(payload, sort_keys=True)
        raw_str = f"{prev_hash or 'GENESIS'}:{actor_id}:{action}:{resource_type}:{resource_id or ''}:{canonical_payload}"
        return hashlib.sha256(raw_str.encode("utf-8")).hexdigest()

    @staticmethod
    def generate_secure_token() -> str:
        return secrets.token_urlsafe(32)

    @staticmethod
    def verify_biometric_signature(challenge: str, signature: str, public_key_id: str) -> bool:
        # FIDO2/WebAuthn signature verification simulation
        return bool(challenge and signature and public_key_id)


enterprise_crypto = EnterpriseCrypto()
