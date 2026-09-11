"""
Database Performance & Slow Query Monitor (Phase 8).
Tracks execution duration of database operations and logs slow queries
exceeding the configurable threshold (default: 200ms).
"""

import time
import logging
from collections import deque
from datetime import datetime, timezone
from functools import wraps
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("kalacart.db_monitor")

DEFAULT_SLOW_QUERY_THRESHOLD_MS = 200.0


class SlowQueryRecord:
    def __init__(
        self,
        query_tag: str,
        duration_ms: float,
        timestamp: str,
        table_name: Optional[str] = None,
        operation: str = "SELECT",
        details: Optional[str] = None,
    ):
        self.query_tag = query_tag
        self.duration_ms = duration_ms
        self.timestamp = timestamp
        self.table_name = table_name or "unknown"
        self.operation = operation
        self.details = details or ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query_tag": self.query_tag,
            "duration_ms": self.duration_ms,
            "timestamp": self.timestamp,
            "table_name": self.table_name,
            "operation": self.operation,
            "details": self.details,
        }


class DatabaseMonitor:
    """
    Tracks database query execution stats, latency distribution, and slow queries.
    """

    def __init__(self, slow_threshold_ms: float = DEFAULT_SLOW_QUERY_THRESHOLD_MS, max_records: int = 100):
        self.slow_threshold_ms = slow_threshold_ms
        self.slow_queries = deque(maxlen=max_records)
        self.total_queries = 0
        self.slow_query_count = 0
        self.total_query_duration_ms = 0.0

    def record_query(
        self,
        query_tag: str,
        duration_ms: float,
        table_name: Optional[str] = None,
        operation: str = "SELECT",
        details: Optional[str] = None,
    ) -> Optional[SlowQueryRecord]:
        self.total_queries += 1
        self.total_query_duration_ms += duration_ms

        if duration_ms >= self.slow_threshold_ms:
            self.slow_query_count += 1
            record = SlowQueryRecord(
                query_tag=query_tag,
                duration_ms=round(duration_ms, 2),
                timestamp=datetime.now(timezone.utc).isoformat(),
                table_name=table_name,
                operation=operation,
                details=details,
            )
            self.slow_queries.appendleft(record)
            logger.warning(
                "🐌 Slow Database Query Detected | tag=%s table=%s op=%s duration=%.2f ms (threshold=%.1f ms)",
                query_tag,
                table_name,
                operation,
                duration_ms,
                self.slow_threshold_ms,
            )
            return record
        return None

    def get_slow_queries(self, limit: int = 50) -> List[Dict[str, Any]]:
        return [q.to_dict() for q in list(self.slow_queries)[:limit]]

    def get_stats(self) -> Dict[str, Any]:
        avg_lat = (self.total_query_duration_ms / self.total_queries) if self.total_queries > 0 else 0.0
        return {
            "total_queries": self.total_queries,
            "slow_query_count": self.slow_query_count,
            "slow_query_threshold_ms": self.slow_threshold_ms,
            "average_query_latency_ms": round(avg_lat, 2),
            "recent_slow_queries_recorded": len(self.slow_queries),
        }

    def reset(self) -> None:
        self.total_queries = 0
        self.slow_query_count = 0
        self.total_query_duration_ms = 0.0
        self.slow_queries.clear()


# Global singleton instance
db_monitor = DatabaseMonitor()


def track_db_query(query_tag: str, table_name: Optional[str] = None, operation: str = "QUERY"):
    """
    Decorator for synchronous or asynchronous DB operations to track latency and slow queries.
    """
    def decorator(func: Callable):
        if asyncio_iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                start = time.perf_counter()
                try:
                    result = await func(*args, **kwargs)
                    duration_ms = (time.perf_counter() - start) * 1000.0
                    db_monitor.record_query(query_tag, duration_ms, table_name, operation)
                    return result
                except Exception as exc:
                    duration_ms = (time.perf_counter() - start) * 1000.0
                    db_monitor.record_query(query_tag, duration_ms, table_name, operation, details=f"Error: {exc}")
                    raise
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                start = time.perf_counter()
                try:
                    result = func(*args, **kwargs)
                    duration_ms = (time.perf_counter() - start) * 1000.0
                    db_monitor.record_query(query_tag, duration_ms, table_name, operation)
                    return result
                except Exception as exc:
                    duration_ms = (time.perf_counter() - start) * 1000.0
                    db_monitor.record_query(query_tag, duration_ms, table_name, operation, details=f"Error: {exc}")
                    raise
            return sync_wrapper
    return decorator


def asyncio_iscoroutinefunction(func: Any) -> bool:
    import asyncio
    return asyncio.iscoroutinefunction(func)
