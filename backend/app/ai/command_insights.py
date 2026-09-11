from typing import List
from datetime import datetime
import uuid
from app.models.command_center import (
    AICommandInsight,
    InsightType,
    InsightSeverity
)

class CommandInsightsEngine:
    @staticmethod
    def detect_anomalies_and_insights() -> List[AICommandInsight]:
        now = datetime.utcnow().isoformat()
        
        insights = [
            AICommandInsight(
                id=f"ins-{uuid.uuid4().hex[:6]}",
                insight_type=InsightType.DEMAND_SPIKE,
                title="Surge in Festive Brass Dhokra Demand (+340%)",
                description="B2B buyers and hotel chains in Delhi NCR and Mumbai are placing large procurement orders for Diwali festival decor.",
                severity=InsightSeverity.HIGH,
                impact_metric="+₹42.5L GMV Pipeline",
                recommended_action="Notify Bastar and Moradabad artisan clusters to accelerate lost-wax casting production batches.",
                detected_at=now
            ),
            AICommandInsight(
                id=f"ins-{uuid.uuid4().hex[:6]}",
                insight_type=InsightType.FRAUD_RING,
                title="Coordinated Sybil Review Ring Detected",
                description="AI graph analysis detected 14 newly registered buyer accounts across 2 IP blocks posting identical 5-star reviews within 4 minutes.",
                severity=InsightSeverity.CRITICAL,
                impact_metric="14 Fake Reviews & 2 Accounts Flagged",
                recommended_action="Auto-quarantine flagged reviews, freeze buyer accounts, and submit for admin moderation review.",
                detected_at=now
            ),
            AICommandInsight(
                id=f"ins-{uuid.uuid4().hex[:6]}",
                insight_type=InsightType.FAST_GROWING_CATEGORY,
                title="Terracotta Dining Tableware Outperforming (+88% MoM)",
                description="Lead-free certified terracotta dinnerware is experiencing viral organic growth on the progressive web app.",
                severity=InsightSeverity.MEDIUM,
                impact_metric="+88% Monthly Velocity",
                recommended_action="Feature terracotta artisans in the upcoming marketing campaign and hero banners.",
                detected_at=now
            ),
            AICommandInsight(
                id=f"ins-{uuid.uuid4().hex[:6]}",
                insight_type=InsightType.UNDERPERFORMING_REGION,
                title="Courier Fulfillment Bottleneck in Northeast Region",
                description="Average shipment delivery time in Assam & Meghalaya increased to 9.2 days due to regional transit depot delays.",
                severity=InsightSeverity.MEDIUM,
                impact_metric="+3.1 Days Transit Delay",
                recommended_action="Route Northeast regional parcels via India Post Speed Post priority air network rather than surface road couriers.",
                detected_at=now
            )
        ]
        return insights
