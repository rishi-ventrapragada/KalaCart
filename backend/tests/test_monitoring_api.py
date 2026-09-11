import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.metrics import metrics_collector
from app.core.db_monitor import db_monitor
from app.core.queue_monitor import queue_monitor

client = TestClient(app)


def test_monitoring_system_health():
    response = client.get("/api/v1/monitoring/system-health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "services" in data
    assert "metrics_snapshot" in data
    assert "api_server" in data["services"]
    assert "database" in data["services"]


def test_monitoring_metrics_and_percentiles():
    # Record some test requests
    metrics_collector.record_request("GET", "/api/v1/catalog/search", 200, 45.2)
    metrics_collector.record_request("GET", "/api/v1/catalog/search", 200, 85.0)
    metrics_collector.record_request("POST", "/api/v1/orders", 201, 120.5)

    response = client.get("/api/v1/monitoring/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "routes" in data
    assert data["summary"]["total_requests"] >= 3
    assert "latency_ms" in data["summary"]
    assert "p50" in data["summary"]["latency_ms"]
    assert "p95" in data["summary"]["latency_ms"]
    assert "p99" in data["summary"]["latency_ms"]


def test_monitoring_active_users_and_uptime():
    response = client.get("/api/v1/monitoring/active-users")
    assert response.status_code == 200
    data = response.json()
    assert "active_users_count" in data

    response_uptime = client.get("/api/v1/monitoring/uptime")
    assert response_uptime.status_code == 200
    uptime_data = response_uptime.json()
    assert "uptime_seconds" in uptime_data
    assert "availability_percentage" in uptime_data


def test_monitoring_storage_and_websocket_status():
    response = client.get("/api/v1/monitoring/storage-usage")
    assert response.status_code == 200
    data = response.json()
    assert "buckets" in data
    assert "total_used_mb" in data

    response_ws = client.get("/api/v1/monitoring/websocket-status")
    assert response_ws.status_code == 200
    ws_data = response_ws.json()
    assert ws_data["status"] == "connected"
    assert "channels" in ws_data


def test_database_slow_query_monitoring():
    db_monitor.reset()
    # Fast query (under 200ms)
    db_monitor.record_query("select_artisan_fast", 15.2, "artisans", "SELECT")
    assert db_monitor.slow_query_count == 0

    # Slow query (over 200ms)
    db_monitor.record_query("search_all_crafts_slow", 350.0, "products", "SELECT", "Full table scan")
    assert db_monitor.slow_query_count == 1

    response = client.get("/api/v1/monitoring/slow-queries")
    assert response.status_code == 200
    data = response.json()
    assert data["stats"]["slow_query_count"] >= 1
    assert len(data["slow_queries"]) >= 1
    assert data["slow_queries"][0]["query_tag"] == "search_all_crafts_slow"


def test_every_critical_error_generates_observable_event():
    initial_event_count = len(metrics_collector.observable_events)

    # Post an event
    payload = {
        "message": "Out of memory simulated in background worker",
        "route": "worker.sync",
        "method": "WORKER",
        "status_code": 500,
        "request_id": "REQ-CRIT-999",
        "level": "CRITICAL",
        "stack_trace": "MemoryError: unable to allocate 500MB",
    }
    post_resp = client.post("/api/v1/monitoring/events/record", json=payload)
    assert post_resp.status_code == 200
    assert post_resp.json()["status"] == "recorded"

    # Verify event appears in observable event stream
    get_resp = client.get("/api/v1/monitoring/events?level=CRITICAL")
    assert get_resp.status_code == 200
    events_data = get_resp.json()
    assert events_data["total_events"] == initial_event_count + 1
    found = any(e["request_id"] == "REQ-CRIT-999" for e in events_data["events"])
    assert found, "Critical error event must be present in observable event stream"
