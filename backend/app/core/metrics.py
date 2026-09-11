"""
Production Metrics & Observability Collector (Phase 8).
Tracks API latency, request logs, error rates, percentiles (P50/P95/P99),
observable error events, active user sessions, and WebSocket health.
"""

import time
import math
import logging
from collections import deque, defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger("kalacart.monitoring")


class ObservableErrorEvent:
    def __init__(
        self,
        event_id: str,
        timestamp: str,
        level: str,
        message: str,
        route: str,
        method: str,
        status_code: int,
        request_id: str,
        stack_trace: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.event_id = event_id
        self.timestamp = timestamp
        self.level = level
        self.message = message
        self.route = route
        self.method = method
        self.status_code = status_code
        self.request_id = request_id
        self.stack_trace = stack_trace
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "level": self.level,
            "message": self.message,
            "route": self.route,
            "method": self.method,
            "status_code": self.status_code,
            "request_id": self.request_id,
            "stack_trace": self.stack_trace,
            "metadata": self.metadata,
        }


class MetricsCollector:
    """
    In-memory production metrics collector with rolling window percentile calculations,
    error rate tracking, active user tracking, and observable event ring buffer.
    """

    def __init__(self, max_recent_latencies: int = 1000, max_events: int = 200):
        self.start_time = time.time()
        self.total_requests = 0
        self.status_counts = defaultdict(int)
        self.route_counts = defaultdict(int)
        self.route_errors = defaultdict(int)
        self.route_latencies = defaultdict(lambda: deque(maxlen=200))
        self.recent_latencies = deque(maxlen=max_recent_latencies)
        self.observable_events = deque(maxlen=max_events)
        self.active_sessions: Dict[str, float] = {}  # user_id / session_id -> last_seen_epoch
        self.active_websockets: Dict[str, Dict[str, Any]] = {}
        self.total_websocket_connections = 0

    def record_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        request_id: str = "",
        user_id: Optional[str] = None,
    ) -> None:
        self.total_requests += 1
        self.status_counts[status_code] += 1

        # Normalize path for grouping (strip uuid/id params if needed)
        norm_route = self._normalize_route(path)
        self.route_counts[norm_route] += 1
        self.route_latencies[norm_route].append(duration_ms)
        self.recent_latencies.append(duration_ms)

        if status_code >= 400:
            self.route_errors[norm_route] += 1

        if user_id:
            self.active_sessions[user_id] = time.time()

    def record_error_event(
        self,
        message: str,
        route: str = "internal",
        method: str = "SYSTEM",
        status_code: int = 500,
        request_id: str = "",
        level: str = "CRITICAL",
        stack_trace: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ObservableErrorEvent:
        """
        Record a critical error or anomaly into the observable event stream.
        Ensures EVERY critical error generates an observable event.
        """
        import uuid

        event = ObservableErrorEvent(
            event_id=f"EVT-{uuid.uuid4().hex[:8].upper()}",
            timestamp=datetime.now(timezone.utc).isoformat(),
            level=level,
            message=message,
            route=route,
            method=method,
            status_code=status_code,
            request_id=request_id,
            stack_trace=stack_trace,
            metadata=metadata,
        )
        self.observable_events.appendleft(event)
        logger.error(
            "Observable Event Generated [%s] | level=%s route=%s status=%d req_id=%s msg=%s",
            event.event_id,
            level,
            route,
            status_code,
            request_id,
            message,
        )
        return event

    def register_websocket(self, client_id: str, channel: str = "general") -> None:
        self.total_websocket_connections += 1
        self.active_websockets[client_id] = {
            "channel": channel,
            "connected_at": datetime.now(timezone.utc).isoformat(),
            "last_ping": time.time(),
        }

    def unregister_websocket(self, client_id: str) -> None:
        self.active_websockets.pop(client_id, None)

    def ping_websocket(self, client_id: str) -> None:
        if client_id in self.active_websockets:
            self.active_websockets[client_id]["last_ping"] = time.time()

    def get_active_users_count(self, inactivity_timeout_sec: int = 300) -> int:
        now = time.time()
        # Clean up stale sessions
        stale = [uid for uid, last_seen in self.active_sessions.items() if now - last_seen > inactivity_timeout_sec]
        for uid in stale:
            self.active_sessions.pop(uid, None)
        return len(self.active_sessions)

    def compute_percentiles(self, values: List[float]) -> Dict[str, float]:
        if not values:
            return {"p50": 0.0, "p95": 0.0, "p99": 0.0, "avg": 0.0, "min": 0.0, "max": 0.0}

        sorted_v = sorted(values)
        n = len(sorted_v)

        def percentile(p: float) -> float:
            k = (n - 1) * p
            f = math.floor(k)
            c = math.ceil(k)
            if f == c:
                return sorted_v[int(k)]
            d0 = sorted_v[int(f)] * (c - k)
            d1 = sorted_v[int(c)] * (k - f)
            return d0 + d1

        return {
            "p50": round(percentile(0.50), 2),
            "p95": round(percentile(0.95), 2),
            "p99": round(percentile(0.99), 2),
            "avg": round(sum(sorted_v) / n, 2),
            "min": round(sorted_v[0], 2),
            "max": round(sorted_v[-1], 2),
        }

    def get_summary(self) -> Dict[str, Any]:
        uptime_sec = time.time() - self.start_time
        all_lats = list(self.recent_latencies)
        percentiles = self.compute_percentiles(all_lats)

        status_2xx = sum(count for code, count in self.status_counts.items() if 200 <= code < 300)
        status_3xx = sum(count for code, count in self.status_counts.items() if 300 <= code < 400)
        status_4xx = sum(count for code, count in self.status_counts.items() if 400 <= code < 500)
        status_5xx = sum(count for code, count in self.status_counts.items() if code >= 500)
        total_errors = status_4xx + status_5xx
        error_rate = (total_errors / self.total_requests * 100) if self.total_requests > 0 else 0.0

        return {
            "uptime_seconds": round(uptime_sec, 2),
            "total_requests": self.total_requests,
            "status_distribution": {
                "2xx": status_2xx,
                "3xx": status_3xx,
                "4xx": status_4xx,
                "5xx": status_5xx,
            },
            "error_rate_percentage": round(error_rate, 2),
            "latency_ms": percentiles,
            "active_users": self.get_active_users_count(),
            "active_websocket_connections": len(self.active_websockets),
            "total_events_recorded": len(self.observable_events),
        }

    def get_route_metrics(self) -> List[Dict[str, Any]]:
        results = []
        for route, count in sorted(self.route_counts.items(), key=lambda x: x[1], reverse=True)[:25]:
            lats = list(self.route_latencies[route])
            p = self.compute_percentiles(lats)
            errors = self.route_errors[route]
            err_rate = (errors / count * 100) if count > 0 else 0.0
            results.append({
                "route": route,
                "requests": count,
                "errors": errors,
                "error_rate_pct": round(err_rate, 2),
                "latency_p50_ms": p["p50"],
                "latency_p95_ms": p["p95"],
                "latency_avg_ms": p["avg"],
            })
        return results

    def get_recent_events(self, limit: int = 50, level: Optional[str] = None) -> List[Dict[str, Any]]:
        events = list(self.observable_events)
        if level:
            events = [e for e in events if e.level.upper() == level.upper()]
        return [e.to_dict() for e in events[:limit]]

    def reset(self) -> None:
        self.start_time = time.time()
        self.total_requests = 0
        self.status_counts.clear()
        self.route_counts.clear()
        self.route_errors.clear()
        self.route_latencies.clear()
        self.recent_latencies.clear()
        self.observable_events.clear()
        self.active_sessions.clear()
        self.active_websockets.clear()

    def _normalize_route(self, path: str) -> str:
        parts = path.strip("/").split("/")
        norm_parts = []
        for p in parts:
            # Check if UUID or hex or integer ID
            if len(p) > 10 and ("-" in p or any(c.isdigit() for c in p)):
                norm_parts.append("{id}")
            elif p.isdigit():
                norm_parts.append("{id}")
            else:
                norm_parts.append(p)
        return "/" + "/".join(norm_parts)


# Global singleton instance
metrics_collector = MetricsCollector()
