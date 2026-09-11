"""
Distributed Background Job & Worker Cluster Manager (Phase 9).
Manages multi-region asynchronous job execution, prioritized job queues
(high_priority, ai_generation, media_processing, analytics_batch), dead-letter handling,
and concurrency auto-scaling.
"""

import time
import uuid
import logging
from typing import Any, Dict, List, Optional
from collections import deque
from datetime import datetime, timezone

from app.core.config import get_settings

logger = logging.getLogger("kalacart.workers.cluster")


class WorkerTask:
    def __init__(
        self,
        task_id: str,
        name: str,
        queue_name: str,
        payload: Dict[str, Any],
        priority: int = 1,
        retries_remaining: int = 3,
    ):
        self.task_id = task_id
        self.name = name
        self.queue_name = queue_name
        self.payload = payload
        self.priority = priority
        self.retries_remaining = retries_remaining
        self.status = "queued"
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.started_at: Optional[str] = None
        self.completed_at: Optional[str] = None
        self.duration_ms: float = 0.0
        self.error: Optional[str] = None
        self.assigned_worker_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "name": self.name,
            "queue_name": self.queue_name,
            "priority": self.priority,
            "retries_remaining": self.retries_remaining,
            "status": self.status,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "duration_ms": round(self.duration_ms, 2),
            "error": self.error,
            "assigned_worker_id": self.assigned_worker_id,
        }


class WorkerClusterManager:
    """
    Coordinates distributed workers across multiple pods and priority queues.
    """

    QUEUES = ["high_priority", "ai_generation", "media_processing", "analytics_batch", "dead_letter"]

    def __init__(self):
        settings = get_settings()
        self.concurrency_per_node = getattr(settings, "WORKER_CONCURRENCY", 8)
        self.total_nodes = 4
        self.active_tasks: Dict[str, WorkerTask] = {}
        self.completed_tasks = deque(maxlen=200)
        self.dead_letter_tasks = deque(maxlen=100)

        self.queue_lengths = {q: 0 for q in self.QUEUES}
        self.total_processed = 0
        self.total_failed = 0

    def enqueue(
        self,
        name: str,
        queue_name: str = "high_priority",
        payload: Optional[Dict[str, Any]] = None,
        priority: int = 1,
    ) -> WorkerTask:
        """Enqueue a background task to the appropriate worker cluster queue."""
        if queue_name not in self.QUEUES:
            queue_name = "high_priority"

        task_id = f"JOB-{uuid.uuid4().hex[:10].upper()}"
        task = WorkerTask(
            task_id=task_id,
            name=name,
            queue_name=queue_name,
            payload=payload or {},
            priority=priority,
        )
        self.active_tasks[task_id] = task
        self.queue_lengths[queue_name] += 1
        logger.info("Enqueued task %s (%s) into [%s]", task_id, name, queue_name)
        return task

    def process_task(
        self,
        task_id: str,
        worker_id: str = "worker-node-01",
        simulate_duration_ms: float = 45.0,
        success: bool = True,
        error_msg: Optional[str] = None,
    ) -> Optional[WorkerTask]:
        """Execute or record completion of a background job."""
        task = self.active_tasks.get(task_id)
        if not task:
            return None

        task.started_at = datetime.now(timezone.utc).isoformat()
        task.assigned_worker_id = worker_id
        task.completed_at = datetime.now(timezone.utc).isoformat()
        task.duration_ms = simulate_duration_ms

        if success:
            task.status = "completed"
            self.total_processed += 1
            if self.queue_lengths[task.queue_name] > 0:
                self.queue_lengths[task.queue_name] -= 1
            self.completed_tasks.appendleft(task)
            del self.active_tasks[task_id]
        else:
            task.retries_remaining -= 1
            task.error = error_msg or "Execution error"
            if task.retries_remaining <= 0:
                task.status = "dead_letter"
                self.total_failed += 1
                if self.queue_lengths[task.queue_name] > 0:
                    self.queue_lengths[task.queue_name] -= 1
                self.queue_lengths["dead_letter"] += 1
                self.dead_letter_tasks.appendleft(task)
                del self.active_tasks[task_id]
                logger.error("Task %s moved to dead-letter queue: %s", task_id, error_msg)
            else:
                task.status = "retrying"

        return task

    def get_cluster_status(self) -> Dict[str, Any]:
        """Returns worker nodes, queue depths, throughput, and error rates."""
        total_capacity = self.concurrency_per_node * self.total_nodes
        busy_workers = len(self.active_tasks)
        return {
            "cluster_nodes_count": self.total_nodes,
            "concurrency_per_node": self.concurrency_per_node,
            "total_cluster_capacity": total_capacity,
            "active_running_tasks": busy_workers,
            "utilization_percentage": round((busy_workers / total_capacity * 100) if total_capacity > 0 else 0, 2),
            "queue_depths": self.queue_lengths,
            "total_processed_lifetime": self.total_processed,
            "total_failed_lifetime": self.total_failed,
            "dead_letter_count": len(self.dead_letter_tasks),
        }


# Global worker cluster singleton
worker_cluster_manager = WorkerClusterManager()
