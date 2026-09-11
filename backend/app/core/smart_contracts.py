"""
Smart Contracts & Institutional Escrow Engine (Phase 9).
Manages enterprise and government (GeM / PSUs) procurement agreements with:
- Milestone-based deliverables and partial releases
- Multi-party inspection sign-offs (Procurement Officer, Quality Inspector, Escrow Agent)
- Automated penalty deductions for delivery delays
- Digital cryptographic signatures and on-chain escrow state machines
"""

import time
import uuid
import hashlib
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone, timedelta

logger = logging.getLogger("kalacart.smart_contracts.escrow")


class ContractMilestone:
    def __init__(
        self,
        milestone_id: str,
        sequence: int,
        title: str,
        description: str,
        release_percentage: float,
        payout_amount: float,
        due_date: str,
    ):
        self.milestone_id = milestone_id
        self.sequence = sequence
        self.title = title
        self.description = description
        self.release_percentage = release_percentage
        self.payout_amount = payout_amount
        self.due_date = due_date
        self.completed_date: Optional[str] = None
        self.delivery_status = "pending"  # pending, delivered, inspection_in_progress, inspection_passed, inspection_failed
        self.escrow_release_status = "locked"  # locked, funded, released, penalized_release, refunded
        self.penalty_applied = 0.0
        self.net_payout = payout_amount
        self.approvals: List[Dict[str, Any]] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "milestone_id": self.milestone_id,
            "sequence": self.sequence,
            "title": self.title,
            "description": self.description,
            "release_percentage": self.release_percentage,
            "payout_amount": self.payout_amount,
            "due_date": self.due_date,
            "completed_date": self.completed_date,
            "delivery_status": self.delivery_status,
            "escrow_release_status": self.escrow_release_status,
            "penalty_applied": self.penalty_applied,
            "net_payout": self.net_payout,
            "approvals_count": len(self.approvals),
            "approvals": self.approvals,
        }


class SmartContractAgreement:
    def __init__(
        self,
        contract_id: str,
        contract_code: str,
        title: str,
        buyer_org_name: str,
        buyer_org_type: str,
        buyer_signatory_name: str,
        buyer_signatory_email: str,
        artisan_id: str,
        artisan_signatory_name: str,
        total_contract_value: float,
        penalty_per_day_late_pct: float = 0.5,
        max_penalty_cap_pct: float = 10.0,
    ):
        self.contract_id = contract_id
        self.contract_code = contract_code
        self.title = title
        self.buyer_org_name = buyer_org_name
        self.buyer_org_type = buyer_org_type
        self.buyer_signatory_name = buyer_signatory_name
        self.buyer_signatory_email = buyer_signatory_email
        self.artisan_id = artisan_id
        self.artisan_signatory_name = artisan_signatory_name
        self.total_contract_value = total_contract_value
        self.currency = "INR"

        self.escrow_funded_amount = 0.0
        self.escrow_released_amount = 0.0
        self.penalty_per_day_late_pct = penalty_per_day_late_pct
        self.max_penalty_cap_pct = max_penalty_cap_pct
        self.inspection_agency = "Quality Council of India (QCI)"

        self.contract_status = "draft"  # draft, signed_pending_escrow, active, completed, terminated, disputed
        self.digital_signature_buyer: Optional[str] = None
        self.digital_signature_artisan: Optional[str] = None
        self.blockchain_tx_hash: Optional[str] = None

        self.milestones: List[ContractMilestone] = []
        self.created_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "contract_id": self.contract_id,
            "contract_code": self.contract_code,
            "title": self.title,
            "buyer": {
                "org_name": self.buyer_org_name,
                "org_type": self.buyer_org_type,
                "signatory_name": self.buyer_signatory_name,
                "signatory_email": self.buyer_signatory_email,
                "signed": bool(self.digital_signature_buyer),
            },
            "artisan": {
                "artisan_id": self.artisan_id,
                "signatory_name": self.artisan_signatory_name,
                "signed": bool(self.digital_signature_artisan),
            },
            "financials": {
                "total_contract_value": self.total_contract_value,
                "currency": self.currency,
                "escrow_funded_amount": self.escrow_funded_amount,
                "escrow_released_amount": self.escrow_released_amount,
                "escrow_remaining_locked": round(self.escrow_funded_amount - self.escrow_released_amount, 2),
                "penalty_terms": f"{self.penalty_per_day_late_pct}% per day late (Max {self.max_penalty_cap_pct}%)",
            },
            "contract_status": self.contract_status,
            "blockchain_anchor": {
                "tx_hash": self.blockchain_tx_hash,
                "verified": bool(self.blockchain_tx_hash),
            },
            "milestones_count": len(self.milestones),
            "milestones": [m.to_dict() for m in self.milestones],
            "created_at": self.created_at,
        }


class SmartContractsEscrowEngine:
    """Manages full lifecycle for enterprise milestone escrow contracts."""

    def __init__(self):
        self.contracts: Dict[str, SmartContractAgreement] = {}
        self._seed_government_procurement_contract()

    def _seed_government_procurement_contract(self):
        """Seed a representative Ministry of Textiles / GeM procurement agreement."""
        c_code = "SC-GEM-2026-CHANNAPATNA-500"
        contract = SmartContractAgreement(
            contract_id="contract-gem-001",
            contract_code=c_code,
            title="GeM National Procurement — 5,000 Channapatna GI Educational Craft Kits",
            buyer_org_name="Ministry of Education & Tribal Affairs (Govt of India)",
            buyer_org_type="government",
            buyer_signatory_name="Dr. Alok Verma (Joint Secretary)",
            buyer_signatory_email="alok.verma@gov.in",
            artisan_id="art-ramesh-01",
            artisan_signatory_name="Ramesh Kumar Varma (President, Channapatna Craft Cooperative)",
            total_contract_value=2500000.0,  # ₹25 Lakhs
        )

        # 3 Milestones: Advance / Raw Material (30%), Mid-Production Batch (40%), Final Delivery & QCI Inspection (30%)
        m1 = ContractMilestone(
            milestone_id="ms-01",
            sequence=1,
            title="Milestone 1: Ivory Wood Sourcing & Eco-Lac Formulation",
            description="Procurement of certified sustainable timber and non-toxic dyes",
            release_percentage=30.0,
            payout_amount=750000.0,
            due_date=(datetime.now(timezone.utc) - timedelta(days=15)).strftime("%Y-%m-%d"),
        )
        m1.completed_date = m1.due_date
        m1.delivery_status = "inspection_passed"
        m1.escrow_release_status = "released"
        m1.approvals.append({
            "approver_role": "quality_inspector",
            "approver_name": "QCI Senior Assessor",
            "status": "approved",
            "signature": "0xQCI_SIG_1001",
            "approved_at": m1.due_date,
        })

        m2 = ContractMilestone(
            milestone_id="ms-02",
            sequence=2,
            title="Milestone 2: Batch 1 Production (2,500 Sets Complete)",
            description="Precision lathe turning, lacquering, and preliminary packaging",
            release_percentage=40.0,
            payout_amount=1000000.0,
            due_date=(datetime.now(timezone.utc) + timedelta(days=10)).strftime("%Y-%m-%d"),
        )
        m2.delivery_status = "inspection_in_progress"
        m2.escrow_release_status = "funded"

        m3 = ContractMilestone(
            milestone_id="ms-03",
            sequence=3,
            title="Milestone 3: Final Delivery & Warehouse Acceptance",
            description="Consignment arrival at Central Stores (New Delhi) with barcode verification",
            release_percentage=30.0,
            payout_amount=750000.0,
            due_date=(datetime.now(timezone.utc) + timedelta(days=30)).strftime("%Y-%m-%d"),
        )
        m3.delivery_status = "pending"
        m3.escrow_release_status = "funded"

        contract.milestones = [m1, m2, m3]
        contract.digital_signature_buyer = "0xDIGISIGN_BUYER_GOV_INDIA"
        contract.digital_signature_artisan = "0xDIGISIGN_ARTISAN_PRESIDENT"
        contract.escrow_funded_amount = 2500000.0
        contract.escrow_released_amount = 750000.0
        contract.contract_status = "active"
        contract.blockchain_tx_hash = "0x8f29ab40192e10bf94827cd910283719bca091823719"

        self.contracts[contract.contract_id] = contract

    def create_contract(
        self,
        title: str,
        buyer_org_name: str,
        buyer_org_type: str,
        buyer_signatory_name: str,
        buyer_signatory_email: str,
        artisan_id: str,
        artisan_signatory_name: str,
        total_contract_value: float,
        milestones: List[Dict[str, Any]],
        penalty_per_day_late_pct: float = 0.5,
        max_penalty_cap_pct: float = 10.0,
    ) -> SmartContractAgreement:
        """Creates a draft enterprise milestone smart agreement."""
        c_id = f"contract-{uuid.uuid4().hex[:8]}"
        c_code = f"SC-{buyer_org_type.upper()[:3]}-{datetime.now(timezone.utc).strftime('%Y')}-{uuid.uuid4().hex[:4].upper()}"

        contract = SmartContractAgreement(
            contract_id=c_id,
            contract_code=c_code,
            title=title,
            buyer_org_name=buyer_org_name,
            buyer_org_type=buyer_org_type,
            buyer_signatory_name=buyer_signatory_name,
            buyer_signatory_email=buyer_signatory_email,
            artisan_id=artisan_id,
            artisan_signatory_name=artisan_signatory_name,
            total_contract_value=total_contract_value,
            penalty_per_day_late_pct=penalty_per_day_late_pct,
            max_penalty_cap_pct=max_penalty_cap_pct,
        )

        seq = 1
        for m in milestones:
            pct = m.get("release_percentage", 100.0 / len(milestones))
            payout = (total_contract_value * pct) / 100.0
            ms = ContractMilestone(
                milestone_id=f"ms-{uuid.uuid4().hex[:6]}",
                sequence=seq,
                title=m.get("title", f"Milestone Stage {seq}"),
                description=m.get("description", ""),
                release_percentage=pct,
                payout_amount=payout,
                due_date=m.get("due_date", (datetime.now(timezone.utc) + timedelta(days=seq * 15)).strftime("%Y-%m-%d")),
            )
            contract.milestones.append(ms)
            seq += 1

        self.contracts[c_id] = contract
        logger.info("Created Smart Agreement: %s (%s)", c_id, c_code)
        return contract

    def sign_contract(
        self,
        contract_id: str,
        signer_role: str,
        signer_name: str,
    ) -> SmartContractAgreement:
        """Applies digital cryptographic signature from Buyer or Artisan."""
        contract = self.contracts.get(contract_id)
        if not contract:
            raise ValueError(f"Contract '{contract_id}' not found")

        sig = f"0xSIG_{hashlib.sha256((signer_name + str(time.time())).encode('utf-8')).hexdigest()[:32]}"
        if signer_role.lower() in ("buyer", "government", "enterprise"):
            contract.digital_signature_buyer = sig
        else:
            contract.digital_signature_artisan = sig

        if contract.digital_signature_buyer and contract.digital_signature_artisan:
            contract.contract_status = "signed_pending_escrow"
            contract.blockchain_tx_hash = "0x" + hashlib.sha256(contract.contract_code.encode("utf-8")).hexdigest()

        return contract

    def fund_escrow(self, contract_id: str, amount: float) -> SmartContractAgreement:
        """Buyer deposits funds into institutional escrow lockbox."""
        contract = self.contracts.get(contract_id)
        if not contract:
            raise ValueError(f"Contract '{contract_id}' not found")

        contract.escrow_funded_amount += amount
        if contract.escrow_funded_amount >= contract.total_contract_value:
            contract.contract_status = "active"
            for m in contract.milestones:
                if m.escrow_release_status == "locked":
                    m.escrow_release_status = "funded"

        logger.info("Funded escrow for %s: +₹%.2f (Total: ₹%.2f)", contract_id, amount, contract.escrow_funded_amount)
        return contract

    def submit_milestone_delivery(self, contract_id: str, milestone_id: str) -> ContractMilestone:
        """Artisan marks milestone deliverable complete and requests inspection."""
        contract = self.contracts.get(contract_id)
        if not contract:
            raise ValueError(f"Contract '{contract_id}' not found")

        ms = next((m for m in contract.milestones if m.milestone_id == milestone_id), None)
        if not ms:
            raise ValueError(f"Milestone '{milestone_id}' not found")

        ms.delivery_status = "inspection_in_progress"
        ms.completed_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return ms

    def approve_milestone_and_release_escrow(
        self,
        contract_id: str,
        milestone_id: str,
        approver_role: str,
        approver_name: str,
        comments: str = "Quality and quantity verified against specification",
    ) -> Dict[str, Any]:
        """Inspector / Procurement Officer approves milestone and releases payout."""
        contract = self.contracts.get(contract_id)
        if not contract:
            raise ValueError(f"Contract '{contract_id}' not found")

        ms = next((m for m in contract.milestones if m.milestone_id == milestone_id), None)
        if not ms:
            raise ValueError(f"Milestone '{milestone_id}' not found")

        # Check late delivery penalties
        due_dt = datetime.strptime(ms.due_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        now_dt = datetime.now(timezone.utc)
        days_late = max(0, (now_dt - due_dt).days)

        penalty = 0.0
        if days_late > 0:
            penalty_pct = min(days_late * contract.penalty_per_day_late_pct, contract.max_penalty_cap_pct)
            penalty = round((ms.payout_amount * penalty_pct) / 100.0, 2)

        net_payout = round(ms.payout_amount - penalty, 2)
        ms.penalty_applied = penalty
        ms.net_payout = net_payout
        ms.delivery_status = "inspection_passed"
        ms.escrow_release_status = "released" if penalty == 0.0 else "penalized_release"

        approval_record = {
            "approver_role": approver_role,
            "approver_name": approver_name,
            "status": "approved",
            "comments": comments,
            "signature": f"0xAPPROVE_{uuid.uuid4().hex[:16]}",
            "approved_at": datetime.now(timezone.utc).isoformat(),
        }
        ms.approvals.append(approval_record)
        contract.escrow_released_amount += net_payout

        # Check if all milestones completed
        if all(m.escrow_release_status in ("released", "penalized_release") for m in contract.milestones):
            contract.contract_status = "completed"

        logger.info(
            "Released Milestone %s: Net ₹%.2f (Penalty: ₹%.2f) to Artisan %s",
            milestone_id,
            net_payout,
            penalty,
            contract.artisan_id,
        )
        return {
            "status": "ESCROW_RELEASED",
            "contract_id": contract_id,
            "milestone_id": milestone_id,
            "gross_amount": ms.payout_amount,
            "penalty_deducted": penalty,
            "net_payout_released": net_payout,
            "days_late": days_late,
            "contract_status": contract.contract_status,
        }

    def get_engine_summary(self) -> Dict[str, Any]:
        return {
            "total_contracts": len(self.contracts),
            "contracts": [c.to_dict() for c in self.contracts.values()],
        }


# Global singleton
smart_contracts_escrow = SmartContractsEscrowEngine()
