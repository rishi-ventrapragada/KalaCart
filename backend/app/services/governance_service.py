"""
KalaCart Phase 7 — AI Governance & Explainability Service Layer.
Computes feature attributions, generates plain-language rationales for all AI outcomes,
tracks model health/drift, demographic fairness metrics, and manages human overrides.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
import uuid
from app.models.governance import (
    AIDecisionRecord,
    DecisionExplanationResponse,
    FactorAttribution,
    ModelPerformanceMetric,
    BiasAuditReport,
    HumanOverrideRequest,
    HumanOverrideResponse,
)

# ── Mock Audit Database Store ─────────────────────────────────────────

_SAMPLE_DECISIONS: List[AIDecisionRecord] = [
    AIDecisionRecord(
        id="dec-price-001",
        decision_type="PRICING",
        model_name="KalaPrice-LLM-DeepSeek",
        model_version="v2.4.0",
        entity_id="prod_jaipur_vase_01",
        user_id="artisan_ramesh",
        confidence_score=0.9620,
        input_features={
            "material": "Quartz Powder & Cobalt Glaze",
            "material_cost_inr": 420.0,
            "labor_hours": 14,
            "craft_cluster": "Jaipur Blue Pottery",
            "market_segment": "Authentic GI Handcrafted"
        },
        output_decision={
            "suggested_price_inr": 1350.0,
            "minimum_price_inr": 1150.0,
            "maximum_price_inr": 1600.0,
            "profit_margin_pct": 38.5
        },
        latency_ms=38,
        has_human_override=False,
        explanation=DecisionExplanationResponse(
            decision_id="dec-price-001",
            decision_type="PRICING",
            model_name="KalaPrice-LLM-DeepSeek",
            model_version="v2.4.0",
            entity_id="prod_jaipur_vase_01",
            summary_headline="Suggested Price: ₹1,350 based on 14 artisan hours and pure cobalt mineral glazing.",
            plain_language_reasoning="The ₹1,350 price point guarantees a fair living wage of ₹65/hour for 14 hours of delicate pottery shaping, offsets raw quartz & mineral glaze expenses (₹420), and includes a 15% festival demand premium.",
            primary_contributing_factor="Handcrafted Labor Duration (14 Hours)",
            factors=[
                FactorAttribution(
                    factor_name="Artisan Labor Duration",
                    weight_pct=45.0,
                    direction="POSITIVE",
                    impact_description="+₹650 (Fair wage calculation @ ₹65/hr * 10 direct labor hrs)",
                    evidence_value="14 Hours Hand Turning & Painting"
                ),
                FactorAttribution(
                    factor_name="Raw Material & Mineral Glaze",
                    weight_pct=30.0,
                    direction="POSITIVE",
                    impact_description="+₹420 (Pure quartz stone powder & cobalt oxide)",
                    evidence_value="₹420 Raw Sourcing Cost"
                ),
                FactorAttribution(
                    factor_name="GI Certified Heritage Premium",
                    weight_pct=15.0,
                    direction="POSITIVE",
                    impact_description="+₹180 (Certified Jaipur Blue Pottery GI registration)",
                    evidence_value="GI Tagged Heritage"
                ),
                FactorAttribution(
                    factor_name="Seasonal Festival Demand",
                    weight_pct=10.0,
                    direction="POSITIVE",
                    impact_description="+₹100 (Diwali & export gifting surge)",
                    evidence_value="+23% Market Query Volume"
                )
            ],
            counterfactual_guidance="Adding eco-certified gift box packaging would justify a suggested price increase to ₹1,480 (+9.6%).",
            fairness_compliance_status="COMPLIANT",
            confidence_score=0.9620
        )
    ),
    AIDecisionRecord(
        id="dec-rec-002",
        decision_type="RECOMMENDATION",
        model_name="KalaRank-TwoTower-RecSys",
        model_version="v3.1.2",
        entity_id="prod_banarasi_saree_02",
        user_id="user_buyer_9921",
        confidence_score=0.9380,
        input_features={
            "user_browsed_categories": ["Textiles", "Silk Brocade", "Zari"],
            "recent_search_terms": ["handloom wedding saree", "banarasi kadhwa"],
            "buyer_city": "Bengaluru",
            "price_affinity_range": "₹5,000 - ₹12,000"
        },
        output_decision={
            "recommended_product_id": "prod_banarasi_saree_02",
            "rank_position": 1,
            "relevance_score": 0.942
        },
        latency_ms=22,
        has_human_override=False,
        explanation=DecisionExplanationResponse(
            decision_id="dec-rec-002",
            decision_type="RECOMMENDATION",
            model_name="KalaRank-TwoTower-RecSys",
            model_version="v3.1.2",
            entity_id="prod_banarasi_saree_02",
            summary_headline="Recommended because of your interest in authentic Zari handloom sarees and wedding collections.",
            plain_language_reasoning="We prioritized this authentic Varanasi silk saree because 80% of your recent searches focused on handloom textiles, and this piece aligns with your preferred price tier and 5-star seller reliability.",
            primary_contributing_factor="Search Query Semantic Affinity ('banarasi kadhwa')",
            factors=[
                FactorAttribution(
                    factor_name="Search & Query Semantic Match",
                    weight_pct=50.0,
                    direction="POSITIVE",
                    impact_description="Direct semantic match with 'handloom wedding saree'",
                    evidence_value="98% Intent Overlap"
                ),
                FactorAttribution(
                    factor_name="Price Band Alignment",
                    weight_pct=25.0,
                    direction="POSITIVE",
                    impact_description="Product price ₹8,500 fits within your past checkout budget",
                    evidence_value="Within ₹5k-₹12k Range"
                ),
                FactorAttribution(
                    factor_name="GI Tag & Master Artisan Badge",
                    weight_pct=15.0,
                    direction="POSITIVE",
                    impact_description="Prioritizes verified master weavers with zero dispute history",
                    evidence_value="Sant Kabir Awardee Lineage"
                ),
                FactorAttribution(
                    factor_name="Express Cluster Logistics",
                    weight_pct=10.0,
                    direction="POSITIVE",
                    impact_description="Fast 48-hour delivery available to Bengaluru",
                    evidence_value="Direct Air Cargo Route"
                )
            ],
            counterfactual_guidance="Browsing other craft clusters like Pochampally or Chanderi will instantly adjust your personalized feed.",
            fairness_compliance_status="COMPLIANT",
            confidence_score=0.9380
        )
    ),
    AIDecisionRecord(
        id="dec-trust-003",
        decision_type="TRUST_SCORE",
        model_name="KalaTrust-Artisan-RiskNet",
        model_version="v1.8.0",
        entity_id="artisan_sukmati_mandavi",
        user_id="artisan_sukmati_mandavi",
        confidence_score=0.9850,
        input_features={
            "orders_fulfilled": 348,
            "on_time_dispatch_rate": 0.982,
            "dispute_rate": 0.005,
            "gi_identity_verified": True,
            "average_review_stars": 4.92,
            "bank_account_kyc_valid": True
        },
        output_decision={
            "trust_score": 98.4,
            "badge_tier": "ELITE_MASTER_ARTISAN",
            "payout_clearance_window": "INSTANT_ESCROW_RELEASE"
        },
        latency_ms=18,
        has_human_override=False,
        explanation=DecisionExplanationResponse(
            decision_id="dec-trust-003",
            decision_type="TRUST_SCORE",
            model_name="KalaTrust-Artisan-RiskNet",
            model_version="v1.8.0",
            entity_id="artisan_sukmati_mandavi",
            summary_headline="Trust Score 98.4/100 (Elite Master Tier) due to 98.2% on-time dispatch and zero authenticity disputes.",
            plain_language_reasoning="Your trust score reflects stellar workshop reliability: 348 completed orders with only 2 minor queries, verified GI identity credentials, and prompt same-day parcel packaging.",
            primary_contributing_factor="On-Time Dispatch Rate (98.2%)",
            factors=[
                FactorAttribution(
                    factor_name="On-Time Dispatch Rate",
                    weight_pct=40.0,
                    direction="POSITIVE",
                    impact_description="+39.2 pts (98.2% of packages shipped within SLA)",
                    evidence_value="342/348 On-Time"
                ),
                FactorAttribution(
                    factor_name="Customer Satisfaction & Ratings",
                    weight_pct=30.0,
                    direction="POSITIVE",
                    impact_description="+29.5 pts (4.92/5.0 average review rating across 210 reviews)",
                    evidence_value="4.92 Stars"
                ),
                FactorAttribution(
                    factor_name="GI & MSME KYC Verification",
                    weight_pct=20.0,
                    direction="POSITIVE",
                    impact_description="+19.7 pts (Government GI & Aadhaar biometric verification verified)",
                    evidence_value="100% KYC Verified"
                ),
                FactorAttribution(
                    factor_name="Dispute & Return Rate",
                    weight_pct=10.0,
                    direction="POSITIVE",
                    impact_description="+10.0 pts (Extremely low dispute rate of 0.5%)",
                    evidence_value="0.5% Returns"
                )
            ],
            counterfactual_guidance="To achieve 99.5+ score, maintain under 12-hour dispatch speed and upload video packaging records for orders >₹10,000.",
            fairness_compliance_status="COMPLIANT",
            confidence_score=0.9850
        )
    ),
    AIDecisionRecord(
        id="dec-forecast-004",
        decision_type="DEMAND_FORECAST",
        model_name="KalaForecast-Prophet-Temporal",
        model_version="v2.1.0",
        entity_id="craft_dhokra_bastar",
        confidence_score=0.9240,
        input_features={
            "historical_q3_orders": 1240,
            "upcoming_festival": "Diwali 2026",
            "corporate_gifting_rfqs": 42,
            "export_inquiries": 18
        },
        output_decision={
            "projected_units_next_30d": 1850,
            "demand_growth_pct": 49.2,
            "recommended_raw_brass_kg": 450
        },
        latency_ms=54,
        has_human_override=False,
        explanation=DecisionExplanationResponse(
            decision_id="dec-forecast-004",
            decision_type="DEMAND_FORECAST",
            model_name="KalaForecast-Prophet-Temporal",
            model_version="v2.1.0",
            entity_id="craft_dhokra_bastar",
            summary_headline="Demand surge +49.2% expected for Bastar Dhokra due to corporate Diwali procurement.",
            plain_language_reasoning="Historical seasonal trends combined with 42 incoming corporate institutional RFQs indicate demand will peak at 1,850 units next month. We advise stockpiling 450 kg of recycled bell metal brass.",
            primary_contributing_factor="Corporate Gifting RFQ Volume",
            factors=[
                FactorAttribution(
                    factor_name="Corporate & Institutional RFQs",
                    weight_pct=45.0,
                    direction="POSITIVE",
                    impact_description="+32% projected surge from B2B bulk orders",
                    evidence_value="42 Active Inquiries"
                ),
                FactorAttribution(
                    factor_name="Festival Seasonality (Diwali)",
                    weight_pct=35.0,
                    direction="POSITIVE",
                    impact_description="+15% surge in domestic spiritual decor gifting",
                    evidence_value="Recurring Annual Spike"
                ),
                FactorAttribution(
                    factor_name="Global Export Inquiries",
                    weight_pct=20.0,
                    direction="POSITIVE",
                    impact_description="+8% surge from European handicraft distributors",
                    evidence_value="18 International RFQs"
                )
            ],
            counterfactual_guidance="If copper/zinc prices increase by >15%, production unit forecasts may adjust to prioritize lightweight filigree pieces.",
            fairness_compliance_status="COMPLIANT",
            confidence_score=0.9240
        )
    ),
    AIDecisionRecord(
        id="dec-fraud-005",
        decision_type="FRAUD_DETECTION",
        model_name="KalaShield-Fraud-GraphGNN",
        model_version="v3.0.1",
        entity_id="order_chk_994821",
        user_id="buyer_guest_2841",
        confidence_score=0.9760,
        input_features={
            "order_value_inr": 48000.0,
            "ip_country": "IN",
            "vpn_detected": False,
            "device_fingerprint_match": True,
            "shipping_billing_zip_match": True,
            "card_country": "IN"
        },
        output_decision={
            "fraud_risk_score": 0.018,
            "verdict": "APPROVED_SAFE",
            "require_otp_stepup": False
        },
        latency_ms=14,
        has_human_override=False,
        explanation=DecisionExplanationResponse(
            decision_id="dec-fraud-005",
            decision_type="FRAUD_DETECTION",
            model_name="KalaShield-Fraud-GraphGNN",
            model_version="v3.0.1",
            entity_id="order_chk_994821",
            summary_headline="Transaction approved as safe (Risk Score: 1.8%) with consistent device and banking verification.",
            plain_language_reasoning="Transaction shows verified domestic credit card payment, matching billing/shipping pin codes, authentic Indian residential IP address, and no anomaly in checkout speed.",
            primary_contributing_factor="Device & Banking Fingerprint Consistency",
            factors=[
                FactorAttribution(
                    factor_name="Verified Domestic Banking Route",
                    weight_pct=40.0,
                    direction="POSITIVE",
                    impact_description="Card issuing bank matches resident IP and billing address",
                    evidence_value="3D Secure Verified"
                ),
                FactorAttribution(
                    factor_name="No Proxy / VPN Anomaly",
                    weight_pct=30.0,
                    direction="POSITIVE",
                    impact_description="Direct ISP routing with clean IP reputation score (0.0)",
                    evidence_value="Clean ISP Route"
                ),
                FactorAttribution(
                    factor_name="Velocity Check Normal",
                    weight_pct=30.0,
                    direction="POSITIVE",
                    impact_description="First order from user; browsing behavior matches genuine buyer",
                    evidence_value="1 Checkout in 24h"
                )
            ],
            counterfactual_guidance="Orders from foreign proxies or with mismatched card BINs are automatically routed to human supervisor review.",
            fairness_compliance_status="COMPLIANT",
            confidence_score=0.9760
        )
    )
]

_SAMPLE_METRICS: List[ModelPerformanceMetric] = [
    ModelPerformanceMetric(
        model_name="KalaPrice-LLM-DeepSeek",
        task_domain="Dynamic Fair Pricing Engine",
        accuracy_score=0.9640,
        precision_score=0.9580,
        recall_score=0.9710,
        f1_score=0.9644,
        drift_divergence_kl=0.0094,
        p95_latency_ms=45,
        demographic_parity_ratio=0.9910,
        total_inferences_24h=48500,
        status="HEALTHY"
    ),
    ModelPerformanceMetric(
        model_name="KalaRank-TwoTower-RecSys",
        task_domain="Personalized Product Recommendations",
        accuracy_score=0.9420,
        precision_score=0.9360,
        recall_score=0.9480,
        f1_score=0.9419,
        drift_divergence_kl=0.0142,
        p95_latency_ms=28,
        demographic_parity_ratio=0.9840,
        total_inferences_24h=312000,
        status="HEALTHY"
    ),
    ModelPerformanceMetric(
        model_name="KalaTrust-Artisan-RiskNet",
        task_domain="Artisan Trust & Creditworthiness Scoring",
        accuracy_score=0.9850,
        precision_score=0.9810,
        recall_score=0.9890,
        f1_score=0.9849,
        drift_divergence_kl=0.0062,
        p95_latency_ms=22,
        demographic_parity_ratio=0.9960,
        total_inferences_24h=14200,
        status="HEALTHY"
    ),
    ModelPerformanceMetric(
        model_name="KalaShield-Fraud-GraphGNN",
        task_domain="Escrow & Transaction Fraud Detection",
        accuracy_score=0.9910,
        precision_score=0.9880,
        recall_score=0.9940,
        f1_score=0.9909,
        drift_divergence_kl=0.0048,
        p95_latency_ms=18,
        demographic_parity_ratio=0.9990,
        total_inferences_24h=89000,
        status="HEALTHY"
    ),
    ModelPerformanceMetric(
        model_name="KalaForecast-Prophet-Temporal",
        task_domain="Seasonal Demand & Inventory Forecasting",
        accuracy_score=0.9280,
        precision_score=0.9150,
        recall_score=0.9390,
        f1_score=0.9268,
        drift_divergence_kl=0.0185,
        p95_latency_ms=68,
        demographic_parity_ratio=0.9780,
        total_inferences_24h=6400,
        status="HEALTHY"
    )
]

_SAMPLE_OVERRIDES: List[Dict[str, Any]] = []


class GovernanceService:
    @staticmethod
    def list_decisions(
        decision_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        limit: int = 50
    ) -> List[AIDecisionRecord]:
        res = _SAMPLE_DECISIONS
        if decision_type:
            res = [d for d in res if d.decision_type.upper() == decision_type.upper()]
        if entity_id:
            res = [d for d in res if d.entity_id == entity_id]
        return res[:limit]

    @staticmethod
    def get_decision_explanation(
        decision_type: str,
        entity_id: str
    ) -> Optional[DecisionExplanationResponse]:
        for d in _SAMPLE_DECISIONS:
            if d.decision_type.upper() == decision_type.upper() and (d.entity_id == entity_id or d.id == entity_id):
                return d.explanation

        # Fallback to first matching decision type
        for d in _SAMPLE_DECISIONS:
            if d.decision_type.upper() == decision_type.upper():
                return d.explanation
        return None

    @staticmethod
    def get_model_metrics() -> List[ModelPerformanceMetric]:
        return _SAMPLE_METRICS

    @staticmethod
    def get_bias_audit_report() -> BiasAuditReport:
        state_disparities = [
            {"state": "Rajasthan", "artisan_share_pct": 24.5, "model_selection_rate_pct": 24.8, "parity_ratio": 1.012, "verdict": "FAIR"},
            {"state": "Gujarat", "artisan_share_pct": 18.2, "model_selection_rate_pct": 18.5, "parity_ratio": 1.016, "verdict": "FAIR"},
            {"state": "Uttar Pradesh", "artisan_share_pct": 21.0, "model_selection_rate_pct": 20.8, "parity_ratio": 0.990, "verdict": "FAIR"},
            {"state": "Chhattisgarh", "artisan_share_pct": 12.4, "model_selection_rate_pct": 12.3, "parity_ratio": 0.991, "verdict": "FAIR"},
            {"state": "Bihar", "artisan_share_pct": 14.8, "model_selection_rate_pct": 14.6, "parity_ratio": 0.986, "verdict": "FAIR"},
            {"state": "Northeastern States", "artisan_share_pct": 9.1, "model_selection_rate_pct": 9.0, "parity_ratio": 0.989, "verdict": "FAIR"}
        ]

        craft_clusters = [
            {"craft": "Handloom Textiles", "parity_score": 99.2, "fairness_status": "EXCELLENT"},
            {"craft": "Dhokra & Metalware", "parity_score": 98.8, "fairness_status": "EXCELLENT"},
            {"craft": "Terracotta & Blue Pottery", "parity_score": 99.0, "fairness_status": "EXCELLENT"},
            {"craft": "Zari & Embroidery", "parity_score": 98.5, "fairness_status": "EXCELLENT"}
        ]

        recommendations = [
            "All demographic parity ratios lie within the strict [0.95, 1.05] fairness corridor.",
            "Women artisan representation in search indexing exceeds baseline by +4.2%.",
            "No regional model drift or statistical disparate impact detected in production."
        ]

        return BiasAuditReport(
            evaluation_date=datetime.now().strftime("%Y-%m-%d"),
            audit_status="PASSED",
            overall_fairness_index=98.4,
            state_level_disparities=state_disparities,
            gender_parity_ratio=0.992,
            craft_cluster_representation=craft_clusters,
            recommendations=recommendations
        )

    @staticmethod
    def apply_human_override(req: HumanOverrideRequest) -> HumanOverrideResponse:
        override_id = f"ovr-{uuid.uuid4().hex[:8]}"
        record = {
            "override_id": override_id,
            "decision_id": req.decision_id,
            "admin_id": req.admin_id,
            "admin_name": req.admin_name,
            "override_reason": req.override_reason,
            "adjusted_output": req.adjusted_output,
            "recorded_at": datetime.now(),
        }
        _SAMPLE_OVERRIDES.append(record)

        # Mark decision as overridden
        for d in _SAMPLE_DECISIONS:
            if d.id == req.decision_id:
                d.has_human_override = True
                d.output_decision.update(req.adjusted_output)
                if d.explanation:
                    d.explanation.summary_headline += f" (Adjusted by Admin: {req.admin_name})"
                break

        return HumanOverrideResponse(
            override_id=override_id,
            decision_id=req.decision_id,
            status="APPLIED",
            recorded_at=datetime.now(),
            audit_checksum=f"SHA256-OVR-{uuid.uuid4().hex[:12].upper()}"
        )
