from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
from app.models.command_center import (
    LiveCommandMetricsResponse,
    StateHeatmapMetric,
    AICommandInsight,
    SupportTicketResponse,
    CreateSupportTicketRequest,
    ExecutiveReportResponse,
    GenerateExecutiveReportRequest
)
from app.ai.command_insights import CommandInsightsEngine

_SUPPORT_TICKETS: Dict[str, Dict[str, Any]] = {}
_EXECUTIVE_REPORTS: Dict[str, Dict[str, Any]] = {}

class CommandCenterService:
    @staticmethod
    def get_live_metrics() -> LiveCommandMetricsResponse:
        now = datetime.utcnow().isoformat()
        
        states = [
            StateHeatmapMetric(
                state_code="OR",
                state_name="Odisha",
                orders_count=1840,
                gmv_inr=3680000.0,
                active_artisans=420,
                fulfillment_rate_percent=98.4,
                heat_score=94.5
            ),
            StateHeatmapMetric(
                state_code="RJ",
                state_name="Rajasthan",
                orders_count=2450,
                gmv_inr=6125000.0,
                active_artisans=580,
                fulfillment_rate_percent=97.8,
                heat_score=98.2
            ),
            StateHeatmapMetric(
                state_code="UP",
                state_name="Uttar Pradesh",
                orders_count=1920,
                gmv_inr=4800000.0,
                active_artisans=510,
                fulfillment_rate_percent=96.5,
                heat_score=91.0
            ),
            StateHeatmapMetric(
                state_code="CG",
                state_name="Chhattisgarh",
                orders_count=820,
                gmv_inr=2460000.0,
                active_artisans=240,
                fulfillment_rate_percent=99.1,
                heat_score=82.0
            ),
            StateHeatmapMetric(
                state_code="TN",
                state_name="Tamil Nadu",
                orders_count=1290,
                gmv_inr=3225000.0,
                active_artisans=310,
                fulfillment_rate_percent=97.2,
                heat_score=86.5
            ),
            StateHeatmapMetric(
                state_code="KA",
                state_name="Karnataka",
                orders_count=1680,
                gmv_inr=4200000.0,
                active_artisans=390,
                fulfillment_rate_percent=98.0,
                heat_score=89.4
            )
        ]

        total_orders = sum(s.orders_count for s in states)
        total_gmv = sum(s.gmv_inr for s in states)
        net_revenue = round(total_gmv * 0.08, 2)  # 8% platform fee
        active_sellers = sum(s.active_artisans for s in states)

        return LiveCommandMetricsResponse(
            timestamp=now,
            live_active_users=3842,
            orders_today=total_orders,
            platform_gmv_inr=total_gmv,
            net_revenue_inr=net_revenue,
            active_disputes=6,
            fraud_alerts=2,
            active_sellers=active_sellers,
            state_metrics=states
        )

    @staticmethod
    def get_state_heatmap() -> List[StateHeatmapMetric]:
        metrics = CommandCenterService.get_live_metrics()
        return metrics.state_metrics

    @staticmethod
    def get_ai_insights() -> List[AICommandInsight]:
        return CommandInsightsEngine.detect_anomalies_and_insights()

    @staticmethod
    def create_support_ticket(req: CreateSupportTicketRequest, user_id: Optional[str] = None) -> SupportTicketResponse:
        t_id = str(uuid.uuid4())
        t_num = f"TICK-{datetime.utcnow().strftime('%Y%m')}-{uuid.uuid4().hex[:5].upper()}"
        now = datetime.utcnow().isoformat()

        # Sentiment analyzer mock
        sentiment = 0.85 if req.priority in ["high", "critical"] else 0.40

        record = {
            "id": t_id,
            "ticket_number": t_num,
            "user_id": user_id,
            "user_email": req.user_email,
            "user_type": req.user_type,
            "category": req.category,
            "subject": req.subject,
            "description": req.description,
            "priority": req.priority,
            "status": "open",
            "ai_sentiment_score": sentiment,
            "created_at": now
        }
        _SUPPORT_TICKETS[t_id] = record
        return SupportTicketResponse(**record)

    @staticmethod
    def list_support_tickets() -> List[SupportTicketResponse]:
        return [SupportTicketResponse(**t) for t in _SUPPORT_TICKETS.values()]

    @staticmethod
    def generate_executive_report(req: GenerateExecutiveReportRequest) -> ExecutiveReportResponse:
        report_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        metrics = CommandCenterService.get_live_metrics()
        insights = CommandCenterService.get_ai_insights()

        summary_md = f"""# KalaCart Executive Intelligence Report
**Period**: {req.report_period.capitalize()} | **Generated**: {now}

## Platform Operational KPIs
- **Platform GMV**: ₹{metrics.platform_gmv_inr:,.2f}
- **Net Revenue**: ₹{metrics.net_revenue_inr:,.2f}
- **Total Orders**: {metrics.orders_today:,}
- **Active Artisans**: {metrics.active_sellers:,}
- **Live Active Users**: {metrics.live_active_users:,}

## Strategic AI Insights
- **Demand**: {insights[0].title}
- **Risk & Fraud**: {insights[1].title}
- **Emerging Growth**: {insights[2].title}
- **Logistics Diagnostic**: {insights[3].title}
"""

        record = {
            "id": report_id,
            "report_title": req.report_title,
            "report_period": req.report_period,
            "summary_markdown": summary_md,
            "ai_insights": [i.model_dump() for i in insights],
            "kpi_snapshot": {
                "gmv": metrics.platform_gmv_inr,
                "net_revenue": metrics.net_revenue_inr,
                "total_orders": metrics.orders_today,
                "active_sellers": metrics.active_sellers
            },
            "pdf_export_url": f"https://storage.kalacart.in/executive_reports/report_{report_id}.pdf",
            "generated_by_ai": True,
            "created_at": now
        }
        _EXECUTIVE_REPORTS[report_id] = record
        return ExecutiveReportResponse(
            id=record["id"],
            report_title=record["report_title"],
            report_period=record["report_period"],
            summary_markdown=record["summary_markdown"],
            ai_insights=insights,
            kpi_snapshot=record["kpi_snapshot"],
            pdf_export_url=record["pdf_export_url"],
            generated_by_ai=record["generated_by_ai"],
            created_at=record["created_at"]
        )

    @staticmethod
    def list_executive_reports() -> List[ExecutiveReportResponse]:
        results = []
        for r in _EXECUTIVE_REPORTS.values():
            insights = [AICommandInsight(**i) for i in r["ai_insights"]]
            results.append(ExecutiveReportResponse(
                id=r["id"],
                report_title=r["report_title"],
                report_period=r["report_period"],
                summary_markdown=r["summary_markdown"],
                ai_insights=insights,
                kpi_snapshot=r["kpi_snapshot"],
                pdf_export_url=r["pdf_export_url"],
                generated_by_ai=r["generated_by_ai"],
                created_at=r["created_at"]
            ))
        return results
