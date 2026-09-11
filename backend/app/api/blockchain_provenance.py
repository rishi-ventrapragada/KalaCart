"""
Blockchain Provenance & Digital Craft Certificate API (Phase 9).
Provides endpoints for:
- Querying and minting immutable craft digital certificates
- Real-time QR code verification and tamper detection
- On-chain ownership transfer to buyers & collectors
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.core.blockchain_provenance import blockchain_provenance_engine

router = APIRouter(prefix="/api/v1/provenance", tags=["Blockchain Provenance & Craft Passports"])


class MintProvenanceRequest(BaseModel):
    product_id: str
    artisan_id: str
    artisan_name: str
    craft_title: str
    craft_category: str
    material_composition: List[str]
    origin_region: str
    gi_certificate_number: Optional[str] = None
    production_date: Optional[str] = None


class TransferOwnershipRequest(BaseModel):
    certificate_number: str
    to_owner_id: str
    to_owner_name: str
    to_owner_type: str = Field(default="buyer", description="buyer | collector | gallery")
    transfer_reason: str = Field(default="marketplace_purchase")
    sale_price: Optional[float] = None


@router.get("/verify/{certificate_number}", summary="Verify craft provenance via QR / Certificate Number")
def verify_craft_provenance(certificate_number: str):
    """
    Scanned by buyers or auditors to verify GI authenticity, origin, and tamper status.
    """
    result = blockchain_provenance_engine.verify_provenance(certificate_number)
    return {"status": "success", "provenance": result}


@router.post("/mint", summary="Mint immutable blockchain authenticity certificate for craft")
def mint_certificate(payload: MintProvenanceRequest):
    rec = blockchain_provenance_engine.mint_provenance_certificate(
        product_id=payload.product_id,
        artisan_id=payload.artisan_id,
        artisan_name=payload.artisan_name,
        craft_title=payload.craft_title,
        craft_category=payload.craft_category,
        material_composition=payload.material_composition,
        origin_region=payload.origin_region,
        gi_certificate_number=payload.gi_certificate_number,
        production_date=payload.production_date,
    )
    return {"status": "minted", "provenance_record": rec.to_dict()}


@router.post("/transfer", summary="Execute blockchain ownership transfer to buyer")
def transfer_craft_ownership(payload: TransferOwnershipRequest):
    try:
        res = blockchain_provenance_engine.transfer_ownership(
            certificate_number=payload.certificate_number,
            to_owner_id=payload.to_owner_id,
            to_owner_name=payload.to_owner_name,
            to_owner_type=payload.to_owner_type,
            transfer_reason=payload.transfer_reason,
            sale_price=payload.sale_price,
        )
        return {"status": "success", "transfer": res}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/records", summary="List all minted craft provenance records")
def list_provenance_records():
    return {
        "status": "success",
        "total_records": len(blockchain_provenance_engine.records),
        "records": [r.to_dict() for r in blockchain_provenance_engine.records.values()],
    }
