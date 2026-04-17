"""
Distributed task queue for asynchronous frame processing.

Supports Celery and RQ with automatic fallback to in-memory queue.
"""

import logging
import uuid
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

# Try to import Celery
try:
    from celery import Celery, Task
    from celery.result import AsyncResult
    HAS_CELERY = True
except ImportError:
    HAS_CELERY = False
    logger.warning("Celery not available, using in-memory queue")

# Try to import RQ
try:
    import redis
    from rq import Queue, Worker
    from rq.job import Job
    HAS_RQ = True
except ImportError:
    HAS_RQ = False
    logger.warning("RQ not available, using in-memory queue")


class TaskStatus(str, Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRIED = "retried"


@dataclass
class TaskResult:
    """Result of task execution."""
    task_id: str
    status: TaskStatus
    result: Optional[Any] = None
    error: Optional[str] = None
    progress: float = 0.0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class TaskQueue(ABC):
    """Abstract base class for task queues."""

    @abstractmethod
    def enqueue(self, task_name: str, *args, **kwargs) -> str:
        """Enqueue task for execution."""
        pass

    @abstractmethod
    def get_result(self, task_id: str) -> Optional[TaskResult]:
        """Get result of completed task."""
        pass

    @abstractmethod
    def cancel_task(self, task_id: str) -> bool:
        """Cancel pending task."""
        pass

    @abstractmethod
    def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        pass


class InMemoryQueue(TaskQueue):
    """In-memory task queue for development/testing."""

    def __init__(self):
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self.results: Dict[str, TaskResult] = {}
        self.pending: list[str] = []

    def enqueue(self, task_name: str, *args, **kwargs) -> str:
        """Enqueue task."""
        task_id = str(uuid.uuid4())
        self.tasks[task_id] = {
            "name": task_name,
            "args": args,
            "kwargs": kwargs,
            "created_at": datetime.now(timezone.utc),
        }
        self.pending.append(task_id)
        self.results[task_id] = TaskResult(
            task_id=task_id,
            status=TaskStatus.PENDING,
        )
        logger.debug(f"Enqueued task {task_id}: {task_name}")
        return task_id

    def get_result(self, task_id: str) -> Optional[TaskResult]:
        """Get task result."""
        return self.results.get(task_id)

    def cancel_task(self, task_id: str) -> bool:
        """Cancel task if pending."""
        if task_id in self.pending:
            self.pending.remove(task_id)
            result = self.results.get(task_id)
            if result:
                result.status = TaskStatus.FAILED
                result.error = "Cancelled"
            return True
        return False

    def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        completed = sum(1 for r in self.results.values() if r.status == TaskStatus.COMPLETED)
        failed = sum(1 for r in self.results.values() if r.status == TaskStatus.FAILED)
        return {
            "pending": len(self.pending),
            "completed": completed,
            "failed": failed,
            "total_tasks": len(self.tasks),
        }

    def simulate_task_execution(self, task_id: str, result: Any = None, error: Optional[str] = None):
        """Simulate task execution (for testing)."""
        if task_id in self.results:
            task_result = self.results[task_id]
            if error:
                task_result.status = TaskStatus.FAILED
                task_result.error = error
            else:
                task_result.status = TaskStatus.COMPLETED
                task_result.result = result
            task_result.progress = 1.0
            task_result.completed_at = datetime.now(timezone.utc)

            if task_id in self.pending:
                self.pending.remove(task_id)


class CeleryQueue(TaskQueue):
    """Celery-based distributed task queue."""

    def __init__(
        self,
        broker_url: str = "redis://localhost:6379",
        backend_url: str = "redis://localhost:6379",
    ):
        self.broker_url = broker_url
        self.backend_url = backend_url
        self.enabled = HAS_CELERY

        if not self.enabled:
            logger.warning("Celery not available")
            return

        try:
            self.app = Celery(
                "watermark_removal",
                broker=broker_url,
                backend=backend_url,
            )
            self.app.conf.update(
                task_track_started=True,
                task_time_limit=600,  # 10 minutes
                worker_prefetch_multiplier=1,
            )
            logger.info(f"Celery initialized: {broker_url}")
        except Exception as e:
            logger.error(f"Failed to initialize Celery: {e}")
            self.enabled = False

    def enqueue(self, task_name: str, *args, **kwargs) -> str:
        """Enqueue task to Celery."""
        if not self.enabled:
            return ""

        try:
            # Task must be registered
            task = self.app.send_task(task_name, args=args, kwargs=kwargs)
            logger.debug(f"Enqueued Celery task {task.id}: {task_name}")
            return task.id
        except Exception as e:
            logger.error(f"Failed to enqueue task: {e}")
            return ""

    def get_result(self, task_id: str) -> Optional[TaskResult]:
        """Get result from Celery."""
        if not self.enabled:
            return None

        try:
            async_result = AsyncResult(task_id, app=self.app)
            status_map = {
                "PENDING": TaskStatus.PENDING,
                "STARTED": TaskStatus.RUNNING,
                "SUCCESS": TaskStatus.COMPLETED,
                "FAILURE": TaskStatus.FAILED,
                "RETRY": TaskStatus.RETRIED,
            }

            status = status_map.get(async_result.status, TaskStatus.PENDING)
            result = None
            error = None

            if async_result.successful():
                result = async_result.result
            elif async_result.failed():
                error = str(async_result.info)

            return TaskResult(
                task_id=task_id,
                status=status,
                result=result,
                error=error,
                progress=getattr(async_result, "progress", 0.0),
            )
        except Exception as e:
            logger.error(f"Failed to get result: {e}")
            return None

    def cancel_task(self, task_id: str) -> bool:
        """Cancel Celery task."""
        if not self.enabled:
            return False

        try:
            async_result = AsyncResult(task_id, app=self.app)
            async_result.revoke(terminate=True)
            logger.debug(f"Revoked Celery task {task_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to revoke task: {e}")
            return False

    def get_queue_stats(self) -> Dict[str, Any]:
        """Get Celery queue statistics."""
        if not self.enabled:
            return {}

        try:
            # Get inspector
            inspector = self.app.control.inspect()
            active = inspector.active()
            scheduled = inspector.scheduled()
            reserved = inspector.reserved()

            active_count = sum(len(v) for v in (active or {}).values())
            scheduled_count = sum(len(v) for v in (scheduled or {}).values())
            reserved_count = sum(len(v) for v in (reserved or {}).values())

            return {
                "active": active_count,
                "scheduled": scheduled_count,
                "reserved": reserved_count,
                "workers": len(active or {}),
            }
        except Exception as e:
            logger.warning(f"Failed to get Celery stats: {e}")
            return {}


class RQQueue(TaskQueue):
    """RQ (Redis Queue) based task queue."""

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        queue_name: str = "watermark_removal",
    ):
        self.redis_url = redis_url
        self.queue_name = queue_name
        self.enabled = HAS_RQ

        if not self.enabled:
            logger.warning("RQ not available")
            return

        try:
            redis_conn = redis.from_url(redis_url)
            self.queue = Queue(queue_name, connection=redis_conn)
            logger.info(f"RQ initialized: {redis_url}/{queue_name}")
        except Exception as e:
            logger.error(f"Failed to initialize RQ: {e}")
            self.enabled = False

    def enqueue(self, task_name: str, *args, **kwargs) -> str:
        """Enqueue task to RQ."""
        if not self.enabled:
            return ""

        try:
            # Task must be callable or importable
            job = self.queue.enqueue(task_name, *args, **kwargs)
            logger.debug(f"Enqueued RQ task {job.id}: {task_name}")
            return job.id
        except Exception as e:
            logger.error(f"Failed to enqueue task: {e}")
            return ""

    def get_result(self, task_id: str) -> Optional[TaskResult]:
        """Get result from RQ."""
        if not self.enabled:
            return None

        try:
            job = Job.fetch(task_id, connection=self.queue.connection)
            status_map = {
                "queued": TaskStatus.PENDING,
                "started": TaskStatus.RUNNING,
                "finished": TaskStatus.COMPLETED,
                "failed": TaskStatus.FAILED,
                "deferred": TaskStatus.PENDING,
            }

            status = status_map.get(job.get_status(), TaskStatus.PENDING)
            result = None
            error = None

            if job.is_finished:
                result = job.result
            elif job.is_failed:
                error = str(job.exc_info)

            return TaskResult(
                task_id=task_id,
                status=status,
                result=result,
                error=error,
                progress=getattr(job, "progress", 0.0),
            )
        except Exception as e:
            logger.error(f"Failed to get result: {e}")
            return None

    def cancel_task(self, task_id: str) -> bool:
        """Cancel RQ task."""
        if not self.enabled:
            return False

        try:
            job = Job.fetch(task_id, connection=self.queue.connection)
            job.cancel()
            logger.debug(f"Cancelled RQ task {task_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to cancel task: {e}")
            return False

    def get_queue_stats(self) -> Dict[str, Any]:
        """Get RQ queue statistics."""
        if not self.enabled:
            return {}

        try:
            return {
                "count": len(self.queue),
                "started": len(self.queue.started_job_registry),
                "finished": len(self.queue.finished_job_registry),
                "failed": len(self.queue.failed_job_registry),
            }
        except Exception as e:
            logger.warning(f"Failed to get RQ stats: {e}")
            return {}


class TaskQueueFactory:
    """Factory for creating appropriate task queue."""

    @staticmethod
    def create(
        queue_type: str = "auto",
        **kwargs,
    ) -> TaskQueue:
        """
        Create task queue.

        Args:
            queue_type: "celery", "rq", "memory", or "auto"
            **kwargs: Arguments for queue initialization

        Returns:
            Configured TaskQueue instance
        """
        if queue_type == "auto":
            # Auto-select best available
            if HAS_CELERY:
                return CeleryQueue(**kwargs)
            elif HAS_RQ:
                return RQQueue(**kwargs)
            else:
                logger.info("Using in-memory queue (Celery/RQ not available)")
                return InMemoryQueue()

        elif queue_type == "celery":
            if not HAS_CELERY:
                logger.warning("Celery not available, falling back to in-memory")
                return InMemoryQueue()
            return CeleryQueue(**kwargs)

        elif queue_type == "rq":
            if not HAS_RQ:
                logger.warning("RQ not available, falling back to in-memory")
                return InMemoryQueue()
            return RQQueue(**kwargs)

        elif queue_type == "memory":
            return InMemoryQueue()

        else:
            raise ValueError(f"Unknown queue type: {queue_type}")


# Global task queue instance
task_queue: Optional[TaskQueue] = None


def init_task_queue(queue_type: str = "auto", **kwargs):
    """Initialize global task queue."""
    global task_queue
    task_queue = TaskQueueFactory.create(queue_type, **kwargs)
    logger.info(f"Task queue initialized: {queue_type}")


def get_task_queue() -> TaskQueue:
    """Get global task queue instance."""
    global task_queue
    if task_queue is None:
        init_task_queue()
    return task_queue
