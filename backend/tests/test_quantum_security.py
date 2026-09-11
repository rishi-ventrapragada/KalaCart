"""
Test Suite for Quantum-Ready Security Layer (KalaCart V10)
Verifies:
- Key abstraction and algorithm agility across NIST PQC suites (Dilithium, Kyber) and Classical suites
- Digital document signing and verification with zero hardcoded algorithms
- Authenticated envelope encryption & decryption with cryptographic tamper detection
- Abstract hardware keystore key version rotation
- Hot-swappable CryptoProvider interface without touching business logic
"""

import pytest
import json
import base64
from fastapi.testclient import TestClient
from app.main import app
from app.core.quantum_security import (
    quantum_security_manager,
    CryptoProvider,
    CryptoAlgorithmSuite,
)

client = TestClient(app)


def test_list_managed_cryptographic_keys():
    response = client.get("/api/v1/security-pqc/keys")
    assert response.status_code == 200
    data = response.json()
    assert data["keys_count"] >= 2
    aliases = [k["key_alias"] for k in data["keys"]]
    assert "kalacart_master_identity_signer" in aliases
    assert "institutional_escrow_payload_cipher" in aliases


def test_sign_and_verify_document_post_quantum():
    # 1. Sign document
    payload = {
        "key_alias": "kalacart_master_identity_signer",
        "document_payload": json.dumps({"contract_code": "GEM-2026-CHANNAPATNA", "escrow_inr": 2500000.0}),
        "caller_service": "smart_contracts_service",
    }
    sign_res = client.post("/api/v1/security-pqc/sign", json=payload)
    assert sign_res.status_code == 200
    sign_data = sign_res.json()
    assert sign_data["quantum_safe"] is True
    assert "DILITHIUM" in sign_data["algorithm_used"]
    token = sign_data["signature_token"]

    # 2. Verify legitimate document
    verify_res = client.post(
        "/api/v1/security-pqc/verify",
        json={
            "key_alias": "kalacart_master_identity_signer",
            "document_payload": payload["document_payload"],
            "signature_token": token,
        },
    )
    assert verify_res.status_code == 200
    assert verify_res.json()["valid"] is True

    # 3. Verify tampered document fails
    tampered_verify = client.post(
        "/api/v1/security-pqc/verify",
        json={
            "key_alias": "kalacart_master_identity_signer",
            "document_payload": json.dumps({"contract_code": "GEM-2026-CHANNAPATNA", "escrow_inr": 5000000.0}),  # Tampered!
            "signature_token": token,
        },
    )
    assert tampered_verify.status_code == 200
    assert tampered_verify.json()["valid"] is False


def test_encrypt_decrypt_and_tamper_detection():
    secret_text = "Master Artisan Bank Account: SBIN0001234, IFSC: SBIN0001234, Routing: RTGS_SECURE"
    context = "tenant:odop_up"

    # 1. Encrypt
    enc_res = client.post(
        "/api/v1/security-pqc/encrypt",
        json={
            "key_alias": "institutional_escrow_payload_cipher",
            "plaintext": secret_text,
            "associated_context": context,
        },
    )
    assert enc_res.status_code == 200
    enc_data = enc_res.json()
    cipher_envelope = enc_data["ciphertext_envelope"]
    assert enc_data["quantum_safe"] is True

    # 2. Decrypt with matching context
    dec_res = client.post(
        "/api/v1/security-pqc/decrypt",
        json={
            "key_alias": "institutional_escrow_payload_cipher",
            "ciphertext_envelope": cipher_envelope,
            "associated_context": context,
        },
    )
    assert dec_res.status_code == 200
    assert dec_res.json()["plaintext"] == secret_text

    # 3. Decrypt with tampered context -> triggers tamper alert
    tamper_res = client.post(
        "/api/v1/security-pqc/decrypt",
        json={
            "key_alias": "institutional_escrow_payload_cipher",
            "ciphertext_envelope": cipher_envelope,
            "associated_context": "tenant:attacker_fake_tenant",  # Tampered!
        },
    )
    assert tamper_res.status_code == 400


def test_rotate_managed_key():
    rotate_res = client.post(
        "/api/v1/security-pqc/keys/rotate",
        json={"key_alias": "kalacart_master_identity_signer"},
    )
    assert rotate_res.status_code == 200
    key_info = rotate_res.json()["key"]
    assert key_info["key_version"] >= 2


def test_hot_swappable_crypto_provider():
    # Verify that business logic is completely decoupled from underlying provider implementation
    class MockCustomHSMProvider(CryptoProvider):
        def get_provider_name(self) -> str:
            return "Custom_Hardware_HSM_v4"
        def sign_payload(self, key_alias: str, payload_bytes: bytes, context_info=None):
            return "mock_hsm_sig_token", "CUSTOM_HSM_ECDSA_256"
        def verify_signature(self, key_alias: str, payload_bytes: bytes, signature_b64: str):
            return signature_b64 == "mock_hsm_sig_token"
        def encrypt_data(self, key_alias: str, plaintext_bytes: bytes, associated_data=None):
            return base64.b64encode(b"encrypted_by_mock_hsm:" + plaintext_bytes).decode(), "HSM_AES_256"
        def decrypt_data(self, key_alias: str, ciphertext_b64: str, associated_data=None):
            raw = base64.b64decode(ciphertext_b64.encode())
            return raw.replace(b"encrypted_by_mock_hsm:", b"")

    original_provider = quantum_security_manager.provider
    try:
        # Swap provider dynamically
        quantum_security_manager.set_provider(MockCustomHSMProvider())
        keys_res = client.get("/api/v1/security-pqc/keys")
        assert keys_res.status_code == 200
        assert keys_res.json()["active_provider"] == "Custom_Hardware_HSM_v4"

        # Sign with new provider
        sign_res = client.post(
            "/api/v1/security-pqc/sign",
            json={"key_alias": "test_key", "document_payload": "hello world"},
        )
        assert sign_res.status_code == 200
        assert sign_res.json()["signature_token"] == "mock_hsm_sig_token"
    finally:
        # Restore default NIST PQC provider
        quantum_security_manager.set_provider(original_provider)
