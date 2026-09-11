"""
Test Suite for Verifiable Digital Identity (KalaCart V10)
Verifies:
- Retrieval of accredited credential issuers
- Issuance of W3C-compliant verifiable credentials with Ed25519 cryptographic signatures
- Completely offline cryptographic QR verification without server lookups
- Tamper detection on modified claims/signatures
- On-chain and local registry revocation handling
"""

import pytest
import json
import base64
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_get_credential_issuers():
    response = client.get("/api/v1/identity/issuers")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] >= 2
    dids = [i["issuer_did"] for i in data["issuers"]]
    assert "did:kalacart:gov:textiles-ministry" in dids
    assert "did:kalacart:org:qci-india" in dids


def test_issue_and_fetch_verifiable_credential():
    payload = {
        "subject_did": "did:kalacart:artisan:sitara-varanasi-02",
        "artisan_id": "art-sitara-02",
        "issuer_did": "did:kalacart:gov:textiles-ministry",
        "credential_type": "gi_certification",
        "claims": {
            "artisan_name": "Sitara Devi",
            "craft_form": "Banaras Pure Zari Silk Brocade",
            "gi_tag": "Banaras Brocades and Sarees",
            "gi_user_registration_no": "GI/AU/3910/2015",
            "district": "Varanasi, Uttar Pradesh",
        },
    }
    response = client.post("/api/v1/identity/issue", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    cred = data["credential"]
    cred_id = cred["credential_id"]
    assert cred["subject_did"] == "did:kalacart:artisan:sitara-varanasi-02"
    assert "proof_signature" in cred
    assert "qr_payload_encoded" in cred

    # Fetch by artisan DID
    art_res = client.get("/api/v1/identity/artisan/did:kalacart:artisan:sitara-varanasi-02")
    assert art_res.status_code == 200
    assert art_res.json()["count"] >= 1


def test_offline_qr_cryptographic_verification():
    # 1. Issue credential
    payload = {
        "subject_did": "did:kalacart:artisan:bastar-dokra-01",
        "issuer_did": "did:kalacart:org:qci-india",
        "credential_type": "master_craftsman_trust",
        "claims": {
            "artisan_name": "Mangal Ram",
            "craft": "Bastar Dokra Bell Metal Casting",
            "purity_certification": "99.4% Bell Metal Alloy",
        },
    }
    issue_res = client.post("/api/v1/identity/issue", json=payload)
    assert issue_res.status_code == 200
    qr_token = issue_res.json()["credential"]["qr_payload_encoded"]

    # 2. Verify offline directly from QR token (no server DB lookup required)
    verify_res = client.post("/api/v1/identity/verify-offline", json={"qr_token": qr_token})
    assert verify_res.status_code == 200
    v_data = verify_res.json()
    assert v_data["valid"] is True
    assert v_data["status"] == "valid"
    assert v_data["verification_mode"] == "offline_cryptographic_verified"
    assert v_data["claims"]["artisan_name"] == "Mangal Ram"


def test_offline_tamper_detection():
    # 1. Issue legitimate credential
    payload = {
        "subject_did": "did:kalacart:artisan:legit-01",
        "issuer_did": "did:kalacart:gov:textiles-ministry",
        "credential_type": "skill_certificate",
        "claims": {"skill_level": "Master", "score": 95},
    }
    issue_res = client.post("/api/v1/identity/issue", json=payload)
    qr_token = issue_res.json()["credential"]["qr_payload_encoded"]

    # 2. Tamper with the claims payload in the token (e.g. change score to 100)
    raw_json = json.loads(base64.urlsafe_b64decode(qr_token.encode("utf-8")).decode("utf-8"))
    raw_json["clm"]["score"] = 100  # Tampered!
    tampered_token = base64.urlsafe_b64encode(json.dumps(raw_json).encode("utf-8")).decode("utf-8")

    # 3. Attempt offline verification -> should return valid=False with signature mismatch
    verify_res = client.post("/api/v1/identity/verify-offline", json={"qr_token": tampered_token})
    assert verify_res.status_code == 200
    assert verify_res.json()["valid"] is False
    assert verify_res.json()["status"] == "invalid_signature"


def test_credential_revocation():
    # 1. Issue credential
    payload = {
        "subject_did": "did:kalacart:artisan:temp-01",
        "issuer_did": "did:kalacart:gov:textiles-ministry",
        "credential_type": "training_completion",
        "claims": {"course": "Advanced Natural Dye Chemistry"},
    }
    issue_res = client.post("/api/v1/identity/issue", json=payload)
    cred = issue_res.json()["credential"]
    cred_id = cred["credential_id"]
    qr_token = cred["qr_payload_encoded"]

    # 2. Revoke
    revoke_res = client.post(
        "/api/v1/identity/revoke",
        json={"credential_id": cred_id, "reason": "Certificate replaced by revised syllabus accreditation."},
    )
    assert revoke_res.status_code == 200
    assert revoke_res.json()["status"] == "success"

    # 3. Offline verify should now register as revoked
    verify_res = client.post("/api/v1/identity/verify-offline", json={"qr_token": qr_token})
    assert verify_res.status_code == 200
    assert verify_res.json()["valid"] is False
    assert verify_res.json()["status"] == "revoked"
