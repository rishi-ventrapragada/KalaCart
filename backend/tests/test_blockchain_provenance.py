"""
Unit & Integration Tests for Phase 9 Blockchain Provenance & Digital Craft Passports.
Covers:
- Cryptographic Merkle Hash Minting & Anchor
- QR Code Verification & Tamper Detection
- On-Chain Ownership Transfer & Immutable History
- Blockchain Provenance REST API Endpoints
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.blockchain_provenance import blockchain_provenance_engine

client = TestClient(app)


def test_seed_heritage_craft_passports():
    """Verify seeded GI craft provenance certificates exist with confirmed blockchain anchors."""
    cert_no = "KC-PROV-2026-CHANNA-001"
    res = blockchain_provenance_engine.verify_provenance(cert_no)

    assert res["is_genuine"] is True
    assert res["tamper_status"] == "VERIFIED_GENUINE"
    assert res["craft_title"] == "Channapatna Lacquerware Toy Set"
    assert "Wrightia Tinctoria (Ivory Wood)" in res["materials"]
    assert res["gi_certification"]["gi_number"] == "GI-IN-0023-CHANNAPATNA"
    assert res["blockchain_proof"]["network"] == "polygon_pos"
    assert res["blockchain_proof"]["transaction_hash"].startswith("0x")


def test_mint_new_craft_provenance_certificate():
    """Test minting an immutable blockchain passport for a newly finished craft product."""
    new_rec = blockchain_provenance_engine.mint_provenance_certificate(
        product_id="prod_kullu_shawl_99",
        artisan_id="art_hemraj_01",
        artisan_name="Hemraj Sharma",
        craft_title="Kullu Handwoven Pashmina Shawl",
        craft_category="Textiles & Handloom",
        material_composition=["100% Himalayan Pashmina Wool", "Natural Walnut Bark Dye"],
        origin_region="Kullu Valley, Himachal Pradesh, India",
        gi_certificate_number="GI-IN-0019-KULLU-SHAWL",
        production_date="2026-09-01",
    )

    assert new_rec.certificate_number.startswith("KC-PROV-")
    assert new_rec.merkle_root_hash != ""
    assert new_rec.transaction_hash.startswith("0x")

    # Verify minted passport
    verify_res = blockchain_provenance_engine.verify_provenance(new_rec.certificate_number)
    assert verify_res["is_genuine"] is True
    assert verify_res["artisan"]["artisan_name"] == "Hemraj Sharma"


def test_tamper_detection_and_counterfeit_rejection():
    """Test counterfeit rejection when scanning an unanchored certificate."""
    fake_cert = "KC-PROV-FAKE-UNREGISTERED-999"
    res = blockchain_provenance_engine.verify_provenance(fake_cert)

    assert res["is_genuine"] is False
    assert res["tamper_status"] == "COUNTERFEIT_OR_UNREGISTERED"


def test_on_chain_ownership_transfer_ledger():
    """Test buyer purchasing a craft piece and claiming verified on-chain ownership."""
    cert_no = "KC-PROV-2026-BIDRI-003"

    transfer_res = blockchain_provenance_engine.transfer_ownership(
        certificate_number=cert_no,
        to_owner_id="buyer_rajesh_delhi",
        to_owner_name="Rajesh Singhania",
        to_owner_type="collector",
        transfer_reason="marketplace_purchase",
        sale_price=8500.0,
    )

    assert transfer_res["status"] == "TRANSFERRED"
    assert transfer_res["transfer_record"]["to_owner_name"] == "Rajesh Singhania"
    assert transfer_res["transfer_record"]["signature_proof"].startswith("0x")

    # Verify current owner has updated on the blockchain passport
    verify_res = blockchain_provenance_engine.verify_provenance(cert_no)
    assert verify_res["current_owner"]["owner_id"] == "buyer_rajesh_delhi"
    assert verify_res["ownership_transfer_count"] >= 1


def test_blockchain_provenance_api_endpoints():
    """Test all Phase 9 Blockchain Provenance REST endpoints."""
    # 1. List records
    r_list = client.get("/api/v1/provenance/records")
    assert r_list.status_code == 200
    assert r_list.json()["total_records"] >= 3

    # 2. Verify via QR endpoint
    r_ver = client.get("/api/v1/provenance/verify/KC-PROV-2026-POCHAM-002")
    assert r_ver.status_code == 200
    assert r_ver.json()["provenance"]["is_genuine"] is True

    # 3. Mint via API
    r_mint = client.post(
        "/api/v1/provenance/mint",
        json={
            "product_id": "prod_madhubani_01",
            "artisan_id": "art_sita_01",
            "artisan_name": "Sita Devi",
            "craft_title": "Madhubani Tree of Life Painting",
            "craft_category": "Paintings",
            "material_composition": ["Handmade Cowdung Paper", "Mineral Pigments"],
            "origin_region": "Madhubani, Bihar, India",
            "gi_certificate_number": "GI-IN-0031-MADHUBANI",
        },
    )
    assert r_mint.status_code == 200
    cert = r_mint.json()["provenance_record"]["certificate_number"]

    # 4. Transfer via API
    r_transfer = client.post(
        "/api/v1/provenance/transfer",
        json={
            "certificate_number": cert,
            "to_owner_id": "buyer_global_curator",
            "to_owner_name": "Victoria Heritage Gallery",
            "to_owner_type": "gallery",
            "sale_price": 15000.0,
        },
    )
    assert r_transfer.status_code == 200
    assert r_transfer.json()["transfer"]["status"] == "TRANSFERRED"
