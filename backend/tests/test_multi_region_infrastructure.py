"""
Unit & Integration Tests for Phase 9 Multi-Region Cloud Infrastructure.
Tests:
- Multi-Region Database Routing & Failover simulation
- Scaled WebSocket & Redis Pub/Sub Broadcast
- Worker Cluster Queue Prioritization & Task Execution
- Multi-Region Storage CDN URL Generation & Cache Headers
- Infrastructure Observability API Endpoints
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database.multi_region import multi_region_db
from app.core.realtime import scaled_realtime_manager
from app.core.worker_cluster import worker_cluster_manager
from app.services.multi_region_storage import multi_region_storage_service

client = TestClient(app)


def test_multi_region_db_routing():
    """Verify primary write routing and replica read selection."""
    write_reg = multi_region_db.get_write_region()
    assert write_reg.region_id == "ap-south-1"
    assert write_reg.is_primary is True

    # Read routing
    read_reg = multi_region_db.get_read_region("us-east-1")
    assert read_reg.region_id == "us-east-1"
    assert read_reg.healthy is True

    # Test degraded replica fallback to primary
    multi_region_db.record_heartbeat("us-east-1", healthy=False, lag_ms=999.0)
    fallback_reg = multi_region_db.get_read_region("us-east-1")
    assert fallback_reg.region_id == "ap-south-1"

    # Restore health
    multi_region_db.record_heartbeat("us-east-1", healthy=True, lag_ms=18.0)


def test_failover_and_restore_simulation():
    """Verify disaster recovery active-passive promotion and failback."""
    # Simulate failover to Europe (eu-central-1)
    event = multi_region_db.trigger_failover_simulation("eu-central-1", "Regional Outage Drill")
    assert event["status"] == "FAILOVER_COMPLETE"
    assert event["promoted_primary"] == "eu-central-1"
    assert multi_region_db.primary_region_id == "eu-central-1"
    assert multi_region_db.failover_active is True

    # Failback restore to Mumbai
    restore_event = multi_region_db.restore_primary_region()
    assert restore_event["status"] == "FAILBACK_COMPLETE"
    assert multi_region_db.primary_region_id == "ap-south-1"
    assert multi_region_db.failover_active is False


@pytest.mark.asyncio
async def test_scaled_realtime_manager():
    """Verify WebSocket client registration and cross-pod broadcast."""
    client_id = "test-ws-client-99"
    channel = "live:commerce:stream-404"

    scaled_realtime_manager.register_client(client_id, channel)
    assert client_id in scaled_realtime_manager.channel_subscribers[channel]

    result = await scaled_realtime_manager.broadcast(
        channel=channel,
        message={"type": "FLASH_DISCOUNT", "discount_pct": 25},
        origin_region="ap-south-1",
    )
    assert result["status"] == "broadcast_dispatched"
    assert result["local_subscribers"] >= 1

    scaled_realtime_manager.unregister_client(client_id)
    assert client_id not in scaled_realtime_manager.channel_subscribers[channel]


def test_worker_cluster_execution():
    """Verify worker queue depths, prioritization, and task completion."""
    task = worker_cluster_manager.enqueue(
        name="ai_catalog_tagging",
        queue_name="ai_generation",
        payload={"product_id": "prod_101"},
        priority=2,
    )
    assert task.status == "queued"
    assert worker_cluster_manager.queue_lengths["ai_generation"] >= 1

    processed_task = worker_cluster_manager.process_task(
        task_id=task.task_id,
        worker_id="worker-pod-02",
        simulate_duration_ms=65.0,
        success=True,
    )
    assert processed_task.status == "completed"
    assert processed_task.assigned_worker_id == "worker-pod-02"


def test_cdn_url_resolution_and_cache_headers():
    """Verify Cloudflare CDN edge URL transformation and immutable headers."""
    raw_storage_url = "https://supabase.kalacart.in/storage/v1/object/public/products/artisan-1/pottery.jpg"
    cdn_url = multi_region_storage_service.resolve_cdn_url(
        raw_storage_url=raw_storage_url,
        width=800,
        quality=80,
        format_webp=True,
    )
    assert "https://cdn.kalacart.in/products/artisan-1/pottery.jpg" in cdn_url
    assert "w=800" in cdn_url
    assert "fmt=webp" in cdn_url

    headers = multi_region_storage_service.get_edge_cache_headers(is_immutable=True)
    assert "immutable" in headers["Cache-Control"]
    assert "31536000" in headers["Cache-Control"]


def test_infrastructure_api_endpoints():
    """Test all Phase 9 multi-region API routes."""
    # 1. Topology
    r_topo = client.get("/api/v1/infrastructure/topology")
    assert r_topo.status_code == 200
    data = r_topo.json()
    assert data["status"] == "operational"
    assert data["database_topology"]["primary_region"] == "ap-south-1"

    # 2. Worker enqueue & status
    r_enqueue = client.post(
        "/api/v1/infrastructure/workers/enqueue",
        json={"name": "test_job", "queue_name": "high_priority", "priority": 1},
    )
    assert r_enqueue.status_code == 200
    assert r_enqueue.json()["status"] == "enqueued"

    r_workers = client.get("/api/v1/infrastructure/workers/status")
    assert r_workers.status_code == 200
    assert r_workers.json()["cluster_nodes_count"] > 0

    # 3. Realtime Stats
    r_rt = client.get("/api/v1/infrastructure/realtime/stats")
    assert r_rt.status_code == 200

    # 4. CDN Resolve API
    r_cdn = client.get(
        "/api/v1/infrastructure/cdn/resolve",
        params={"storage_url": "https://supabase.kalacart.in/storage/v1/object/public/products/demo.png"},
    )
    assert r_cdn.status_code == 200
    assert "cdn.kalacart.in" in r_cdn.json()["cdn_edge_url"]
