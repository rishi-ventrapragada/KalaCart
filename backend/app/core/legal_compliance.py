"""
Legal & Regulatory Compliance Engine for KalaCart.
Contains verified statutory policies, Indian DPDP Act 2023 compliance checklist,
GDPR data subject rights handler, and GST invoice verification specs.
"""

from typing import Dict, List, Any

LEGAL_POLICIES: Dict[str, Dict[str, str]] = {
    "privacy_policy": {
        "title": "Privacy Policy",
        "version": "v1.0.0-2026",
        "last_updated": "2026-09-07",
        "summary": "Governs data collection, usage, processing under DPDP Act 2023 and GDPR.",
        "content": (
            "1. Introduction: KalaCart (\"we\", \"our\", \"us\") is committed to protecting the privacy of artisans, "
            "buyers, and partners under the Digital Personal Data Protection Act, 2023 (DPDP Act) and the General Data "
            "Protection Regulation (GDPR).\\n\\n"
            "2. Data Collected: Name, phone number, email, shipping address, GSTIN/PAN (for verified sellers), "
            "camera captures for AI Craft Studio, and voice samples for regional voice search.\\n\\n"
            "3. Lawful Basis: Explicit user consent, fulfillment of purchase contracts, and statutory compliance (GST/TDS).\\n\\n"
            "4. Data Principal Rights: Right to access, correct, withdraw consent, and request permanent erasure.\\n\\n"
            "5. Contact Grievance Officer: grievance@kalacart.in | Data Protection Officer, Bengaluru, India."
        )
    },
    "terms_of_service": {
        "title": "Terms of Service",
        "version": "v1.0.0-2026",
        "last_updated": "2026-09-07",
        "summary": "General terms governing platform usage, account creation, and user conduct.",
        "content": (
            "1. Acceptance of Terms: By accessing KalaCart web or mobile applications, you agree to these Terms.\\n\\n"
            "2. User Eligibility: Users must be at least 18 years of age or possess legal parental/guardian consent.\\n\\n"
            "3. Intellectual Property: Artisan motifs, GI heritage marks, and platform code are protected. Unauthorized "
            "scraping or counterfeit reproduction is strictly prohibited.\\n\\n"
            "4. Dispute Resolution: Subject to the exclusive jurisdiction of the courts in Bengaluru, Karnataka, India."
        )
    },
    "seller_agreement": {
        "title": "Artisan & Seller Agreement",
        "version": "v1.0.0-2026",
        "last_updated": "2026-09-07",
        "summary": "Mandatory terms for artisans, weavers, SHGs, and cooperatives selling on KalaCart.",
        "content": (
            "1. Authenticity Guarantee: Seller certifies all listed handicrafts meet authentic Geographical Indication (GI) "
            "or handmade criteria.\\n\\n"
            "2. Escrow Payouts: Payouts are held in RBI-compliant escrow and disbursed upon successful customer delivery and inspection.\\n\\n"
            "3. Commission & Fees: Transparent platform fee structure with zero listing fees for certified rural artisans.\\n\\n"
            "4. Quality Compliance: Strict penalties and delisting for counterfeit, factory-machine replicas."
        )
    },
    "buyer_agreement": {
        "title": "Buyer Agreement",
        "version": "v1.0.0-2026",
        "last_updated": "2026-09-07",
        "summary": "Purchase terms, B2B wholesale quotation rules, and payment guarantees.",
        "content": (
            "1. Fair-Trade Commitment: All purchases directly support authentic rural Indian artisans.\\n\\n"
            "2. Order Confirmation & Escrow Protection: Payments are secured until dispatch verification.\\n\\n"
            "3. B2B Quotes & Customization: Custom bulk orders require 50% escrow milestone deposit upon contract signing."
        )
    },
    "refund_policy": {
        "title": "Refund & Return Policy",
        "version": "v1.0.0-2026",
        "last_updated": "2026-09-07",
        "summary": "7-day return policy for transit damages and GI non-authenticity claims.",
        "content": (
            "1. Handmade Craftsmanship Tolerance: Slight color/texture variances are intrinsic to authentic handmade crafts.\\n\\n"
            "2. Eligible Returns: Physical transit damage, wrong item, or GI tag authenticity mismatch within 7 calendar days of delivery.\\n\\n"
            "3. Refund Processing: Refunds processed to original payment method within 5-7 business days upon craft return verification."
        )
    },
    "shipping_policy": {
        "title": "Shipping & Fulfillment Policy",
        "version": "v1.0.0-2026",
        "last_updated": "2026-09-07",
        "summary": "Pan-India and global export logistics specifications.",
        "content": (
            "1. Logistics Partners: India Post Speed Post, Blue Dart, Delhivery, and DHL Express (for international exports).\\n\\n"
            "2. Dispatch Timeline: Standard orders dispatch within 48-72 hours. Custom craft orders dispatch per agreed artisan schedule.\\n\\n"
            "3. Volumetric Weight Calculation: Standard logistics formula (L*W*H / 5000) applied transparently."
        )
    },
    "community_guidelines": {
        "title": "Community & Fair-Trade Guidelines",
        "version": "v1.0.0-2026",
        "last_updated": "2026-09-07",
        "summary": "Standards of conduct for respectful artisan-buyer interactions.",
        "content": (
            "1. Cultural Respect: Protect and celebrate indigenous heritage crafts.\\n\\n"
            "2. Anti-Harassment: Zero tolerance for discriminatory remarks or predatory pricing negotiations.\\n\\n"
            "3. Transparency: Transparent wage declarations and cluster origin disclosure."
        )
    },
    "data_retention_policy": {
        "title": "Data Retention & Erasure Policy",
        "version": "v1.0.0-2026",
        "last_updated": "2026-09-07",
        "summary": "Retention periods and automated anonymization rules.",
        "content": (
            "1. Transaction & Tax Records: Retained for 7 statutory financial years in compliance with the GST Act and Companies Act.\\n\\n"
            "2. Voice Search Telemetry: Retained for max 30 days then permanently purged.\\n\\n"
            "3. User Account Erasure: Inactive accounts purged or anonymized within 30 days of deletion request."
        )
    }
}

DPDP_COMPLIANCE_CHECKLIST: List[Dict[str, Any]] = [
    {"rule": "Clear Notice & Multilingual Consent", "status": "COMPLIANT", "details": "Consent notices in English + 10 regional Indian languages."},
    {"rule": "Data Fiduciary Accountability", "status": "COMPLIANT", "details": "Grievance officer & DPO appointed with 72h SLA."},
    {"rule": "Right to Erasure & Correction", "status": "COMPLIANT", "details": "Self-serve data download and account deletion via Settings."},
    {"rule": "Child Data Protection", "status": "COMPLIANT", "details": "No behavioral tracking or targeted ads for minors."},
    {"rule": "Breach Notification Protocol", "status": "COMPLIANT", "details": "CERT-In & Data Protection Board 6-hour breach notification SLA."}
]

GST_COMPLIANCE_STANDARDS: Dict[str, Any] = {
    "hsn_classification": "Standard 4/6-digit HSN codes assigned for handicrafts, textiles (Chapter 50-63), and pottery (Chapter 69).",
    "e_invoicing": "Automated IRN (Invoice Reference Number) & QR code generation for B2B transactions exceeding statutory threshold.",
    "reverse_charge_mechanism": "RCM tracking for unregistered rural artisan procurement.",
    "gstin_validation": "Real-time GST portal API verification."
}

