"""
Multi-Region Cloud Infrastructure & Topology API (Phase 9).
Provides observability and controls for:
- Multi-region database topologies & replication lag
- Primary / Replica failover orchestration & DR simulation
- Scaled WebSocket connection cluster stats & message broadcast
- Background worker cluster queue depth & throughput
- CDN edge caching & regional storage replication metrics
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.database.multi_region import multi_region_db
from app.core.realtime import scaled_realtime_manager
from app.core.worker_cluster import worker_cluster_manager
from app.services.multi_region_storage import multi_region_storage_service

router = APIRouter(prefix="/api/v1/infrastructure", tags=["Multi-Region Cloud Infrastructure"])


class FailoverSimulationRequest(BaseModel):
    target_region_id: str = Field(..., description="Region ID to promote to primary (e.g. us-east-1, eu-central-1)")
    reason: str = Field(default="Automated multi-region failover drill", description="Drill context or reason")


class RealtimeBroadcastRequest(BaseModel):
    channel: str = Field(default="live:commerce:stream-101", description="Target broadcast topic")
    data: Dict[str, Any] = Field(..., description="Event payload to broadcast across pods")


class EnqueueTaskRequest(BaseModel):
    name: str = Field(..., description="Task name e.g. generate_catalog_ai")
    queue_name: str = Field(default="high_priority", description="high_priority | ai_generation | media_processing | analytics_batch")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Task arguments")
    priority: int = Field(default=1, ge=1, le=5)


@router.get("/topology", summary="Get global multi-region cloud topology")
async def get_multi_region_topology():
    """
    Returns full deployment topology across API, Database, Storage, Realtime, and Worker layers.
    """
    return {
        "status": "operational",
        "architecture_tier": "Enterprise Multi-Region (Phase 9)",
        "database_topology": multi_region_db.get_topology_status(),
        "storage_and_cdn": multi_region_storage_service.get_replication_status(),
        "realtime_cluster": scaled_realtime_manager.get_cluster_stats(),
        "worker_cluster": worker_cluster_manager.get_cluster_status(),
    }


@router.post("/failover/simulate", summary="Trigger disaster recovery failover drill")
async def simulate_failover(payload: FailoverSimulationRequest):
    """
    Simulates promoting a secondary read-replica to primary master status during region failure.
    """
    try:
        event = multi_region_db.trigger_failover_simulation(
            target_region_id=payload.target_region_id,
            reason=payload.reason,
        )
        return {"status": "success", "failover_event": event}
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/failover/restore", summary="Failback to India Mumbai Primary Master")
async def restore_primary_master():
    """
    Restores ap-south-1 Mumbai as the default primary write master after failover recovery.
    """
    event = multi_region_db.restore_primary_region()
    return {"status": "success", "restore_event": event}


@router.post("/realtime/broadcast", summary="Broadcast realtime event across all cluster pods")
async def broadcast_realtime_event(payload: RealtimeBroadcastRequest):
    """
    Broadcasts message to all connected clients across all API pods via Redis Pub/Sub.
    """
    result = await scaled_realtime_manager.broadcast(
        channel=payload.channel,
        message=payload.data,
        origin_region=multi_region_db.current_region_id,
    )
    return {"status": "dispatched", "broadcast_result": result}


@router.get("/realtime/stats", summary="Get realtime WebSocket cluster status")
async def get_realtime_stats():
    """
    Returns active subscribers, channel distribution, and Redis Pub/Sub bridge health.
    """
    return scaled_realtime_manager.get_cluster_stats()


@router.post("/workers/enqueue", summary="Enqueue job into distributed worker cluster")
async def enqueue_worker_job(payload: EnqueueTaskRequest):
    """
    Dispatches task to dedicated worker queue with priority and retry tracking.
    """
    task = worker_cluster_manager.enqueue(
        name=payload.name,
        queue_name=payload.queue_name,
        payload=payload.payload,
        priority=payload.priority,
    )
    return {"status": "enqueued", "task": task.to_dict()}


@router.get("/workers/status", summary="Get background worker cluster queue depths & metrics")
async def get_worker_status():
    """
    Returns worker node concurrency, queue lengths, dead-letter count, and throughput.
    """
    return worker_cluster_manager.get_cluster_status()


@router.get("/cdn/resolve", summary="Resolve optimized CDN URL for media asset")
async def resolve_cdn_asset(
    storage_url: str = Query(..., description="Raw Supabase storage URL"),
    width: Optional[int] = Query(None, description="Optional target image width in pixels"),
    quality: int = Query(85, ge=10, le=100, description="WebP compression quality"),
):
    """
    Generates Cloudflare edge-cached CDN URL with WebP transform parameters.
    """
    cdn_url = multi_region_storage_service.resolve_cdn_url(
        raw_storage_url=storage_url,
        width=width,
        quality=quality,
        format_webp=True,
    )
    headers = multi_region_storage_service.get_edge_cache_headers(is_immutable=True)
    return {
        "raw_storage_url": storage_url,
        "cdn_edge_url": cdn_url,
        "edge_cache_headers": headers,
    }
