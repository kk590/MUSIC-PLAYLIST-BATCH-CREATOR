"""Batch Priority Queue Module

This module provides priority-based task queue management for batch operations.
Uses Redis priority queues (multiple lists) or RabbitMQ for task prioritization.
"""

from celery import Celery
import redis
from typing import Optional

# Priority levels: 0=highest, 9=lowest
PRIORITY_LEVELS = {
    "critical": 0,
    "high": 3,
    "normal": 5,
    "low": 7,
    "background": 9
}

class BatchPriorityQueue:
    """Manages priority-based batch job queuing."""

    def __init__(self, celery_app: Celery, redis_client: Optional[redis.Redis] = None):
        self.celery_app = celery_app
        self.redis = redis_client
        self._queue_names = [f"batch_queue_p{p}" for p in range(10)]

    def enqueue_task(
        self,
        task_name: str,
        args: tuple = (),
        kwargs: dict = None,
        priority: int = 5
    ):
        """Enqueue a task with specified priority.

        Args:
            task_name: Name of the Celery task
            args: Positional arguments for the task
            kwargs: Keyword arguments for the task
            priority: Priority level (0=highest, 9=lowest)
        """
        priority = max(0, min(9, priority))
        task = self.celery_app.tasks.get(task_name)

        if task:
            return task.apply_async(
                args=args,
                kwargs=kwargs or {},
                priority=priority
            )
        raise ValueError(f"Task '{task_name}' not found")

    async def enqueue_playlist_generation(
        self,
        user_id: str,
        template_ids: list,
        priority: str = "normal"
    ) -> str:
        """Enqueue a batch playlist generation job with priority.

        Args:
            user_id: User identifier
            template_ids: List of template IDs
            priority: Priority string (critical/high/normal/low/background)

        Returns:
            Job ID string
        """
        priority_level = PRIORITY_LEVELS.get(priority, 5)

        from tasks import generate_playlist_from_template

        job_id = f"job_{user_id}_{template_ids[0]}"

        # Store job metadata in Redis
        if self.redis:
            self.redis.hset(f"job:{job_id}", mapping={
                "user_id": user_id,
                "template_ids": ",".join(template_ids),
                "priority": str(priority_level),
                "state": "queued"
            })

        # Enqueue with priority
        for template_id in template_ids:
            generate_playlist_from_template.apply_async(
                args=[job_id, template_id],
                priority=priority_level
            )

        return job_id

    async def get_queue_stats(self) -> dict:
        """Get statistics for all priority queues."""
        stats = {}
        if self.redis:
            for i, queue_name in enumerate(self._queue_names):
                length = self.redis.llen(queue_name)
                if length > 0:
                    stats[f"priority_{i}"] = length
        return stats

    async def reprioritize_job(self, job_id: str, new_priority: int):
        """Change the priority of a queued job.

        Note: Only works for jobs not yet picked up by workers.
        """
        if self.redis:
            self.redis.hset(f"job:{job_id}", "priority", str(new_priority))


# Module-level helper for quick usage
def set_job_priority(
    celery_app: Celery,
    task_name: str,
    args: tuple,
    priority: int = 5
):
    """Quick helper to enqueue a task with priority.

    Usage:
        set_job_priority(celery_app, "generate_playlist", ([job_id, template_id],), priority=3)
    """
    task = celery_app.tasks.get(task_name)
    if task:
        return task.apply_async(args=args, priority=priority)
    raise ValueError(f"Task '{task_name}' not found")
