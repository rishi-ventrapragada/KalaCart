"""
Background Task & Queue Monitor (Phase 8).
Tracks background jobs, queues, execution durations, and error rates.
"""

import time
import logging
from collections import deque
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger("kalacart.queue_monitor")


class QueueTaskRecord:
    def __init__(
        self,
        task_id: str,
        task_name: str,
        queue_name: str = "default",
        status: str = "queued",
        created_at: Optional[str] = None,
        started_at: Optional[str] = None,
        completed_at: Optional[str] = None,
        duration_ms: float = 0.0,
        error: Optional[str] = None,
    ):
        self.task_id = task_id
        self.task_name = task_name
        self.queue_name = queue_name
        self.status = status
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()
        self.started_at = started_at
        self.completed_at = completed_at
        self.duration_ms = duration_ms
        self.error = error

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "task_name": self.task_name,
            "queue_name": self.queue_name,
            "status": self.status,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "duration_ms": round(self.duration_ms, 2),
            "error": self.error,
        }


class QueueMonitor:
    """
    In-memory monitor for background queues and async jobs.
    """

    def __init__(self, max_history: int = 100):
        self.active_tasks: Dict[str, QueueTaskRecord] = {}
        self.completed_tasks = deque(maxlen=max_history)
        self.total_enqueued = 0
        self.total_completed = 0
        self.total_failed = 0

    def start_task(self, task_id: str, task_name: str, queue_name: str = "default") -> QueueTaskRecord:
        record = QueueTaskRecord(
            task_id=task_id,
            task_name=task_name,
            queue_name=queue_name,
            status="processing",
            started_at=datetime.now(timezone.utc).isoformat(),
        )
        self.active_tasks[task_id] = record
        self.total_enqueued += 1
        return record

    def finish_task(
        self,
        task_id: str,
        duration_ms: float,
        success: bool = True,
        error: Optional[str] = None,
    ) -> Optional[QueueTaskRecord]:
        record = self.active_tasks.pop(task_id, None)
        if record:
            record.completed_at = datetime.now(timezone.utc).isoformat()
            record.duration_ms = duration_ms
            record.status = "completed" if success else "failed"
            record.error = error

            if success:
                self.total_completed += 1
            else:
                self.total_failed += 1

            self.completed_tasks.appendleft(record)
            return record
        return None

    def get_summary(self) -> Dict[str, Any]:
        return {
            "active_tasks_count": len(self.active_tasks),
            "total_enqueued": self.total_enqueued,
            "total_completed": self.total_completed,
            "total_failed": self.total_failed,
            "success_rate_percentage": round(
                (self.total_completed / (self.total_completed + self.total_failed) * 100)
                if (self.total_completed + self.total_failed) > 0
                else 100.0,
                2,
            ),
            "active_tasks": [t.to_dict() for t in self.active_tasks.values()],
        }

    def get_recent_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        return [t.to_dict() for t in list(self.completed_tasks)[:limit]]

    def reset(self) -> None:
        self.active_tasks.clear()
        self.completed_tasks.clear()
        self.total_enqueued = 0
        self.total_completed = 0
        self.total_failed = 0


# Global singleton instance
queue_monitor = QueueMonitor()
