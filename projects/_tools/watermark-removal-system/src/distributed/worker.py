"""
Worker management for distributed frame processing.

Handles worker lifecycle, task execution, and failure recovery.
"""

import logging
import asyncio
import inspect
import uuid
from typing import Optional, Dict, Any, Callable, List
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class WorkerStatus(str, Enum):
    """Worker status."""
    IDLE = "idle"
    PROCESSING = "processing"
    PAUSED = "paused"
    ERROR = "error"
    SHUTDOWN = "shutdown"


@dataclass
class WorkerConfig:
    """Worker configuration."""
    worker_id: str
    max_concurrent_tasks: int = 1
    task_timeout_seconds: int = 300
    heartbeat_interval_seconds: int = 10
    max_retries: int = 3
    enable_auto_scaling: bool = True


class Worker:
    """Distributed worker for processing tasks."""

    def __init__(self, config: WorkerConfig):
        self.config = config
        self.status = WorkerStatus.IDLE
        self.current_tasks: Dict[str, Dict[str, Any]] = {}
        self.completed_count = 0
        self.failed_count = 0
        self.started_at = datetime.now(timezone.utc)
        self.last_heartbeat = datetime.now(timezone.utc)
        self.total_processing_time_ms = 0.0
        self.task_handlers: Dict[str, Callable] = {}

    def register_task_handler(self, task_type: str, handler: Callable):
        """Register handler for task type."""
        self.task_handlers[task_type] = handler
        logger.debug(f"Registered handler for {task_type}")

    async def process_task(
        self,
        task_id: str,
        task_type: str,
        task_data: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """
        Process single task.

        Args:
            task_id: Unique task identifier
            task_type: Type of task to process
            task_data: Task input data

        Returns:
            Task result or None on failure
        """
        if task_type not in self.task_handlers:
            logger.error(f"No handler for task type: {task_type}")
            return None

        if len(self.current_tasks) >= self.config.max_concurrent_tasks:
            logger.warning(f"Worker at capacity, rejecting task {task_id}")
            return None

        # Register task
        self.current_tasks[task_id] = {
            "task_type": task_type,
            "started_at": datetime.now(timezone.utc),
            "status": "running",
        }
        self.status = WorkerStatus.PROCESSING

        try:
            # Execute task with timeout
            handler = self.task_handlers[task_type]
            result = await asyncio.wait_for(
                self._execute_with_retry(handler, task_data),
                timeout=self.config.task_timeout_seconds,
            )

            # Update stats
            self.completed_count += 1
            self.current_tasks[task_id]["status"] = "completed"
            self._update_processing_time(task_id)

            logger.debug(f"Completed task {task_id}")
            return result

        except asyncio.TimeoutError:
            logger.error(f"Task {task_id} timed out")
            self.failed_count += 1
            self.current_tasks[task_id]["status"] = "failed"
            return None

        except Exception as e:
            logger.error(f"Task {task_id} failed: {e}")
            self.failed_count += 1
            self.current_tasks[task_id]["status"] = "failed"
            self.status = WorkerStatus.ERROR
            return None

        finally:
            # Clean up task
            if task_id in self.current_tasks:
                del self.current_tasks[task_id]

            # Reset status if no more tasks
            if not self.current_tasks:
                self.status = WorkerStatus.IDLE

    async def _execute_with_retry(self, handler: Callable, task_data: Dict[str, Any]) -> Optional[Any]:
        """Execute handler with automatic retry."""
        last_error = None

        for attempt in range(self.config.max_retries):
            try:
                if inspect.iscoroutinefunction(handler):
                    return await handler(task_data)
                else:
                    return handler(task_data)

            except Exception as e:
                last_error = e
                if attempt < self.config.max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.debug(f"Retry attempt {attempt + 1}, waiting {wait_time}s")
                    await asyncio.sleep(wait_time)

        raise last_error

    def update_heartbeat(self):
        """Update heartbeat timestamp."""
        self.last_heartbeat = datetime.now(timezone.utc)

    def get_stats(self) -> Dict[str, Any]:
        """Get worker statistics."""
        uptime = (datetime.now(timezone.utc) - self.started_at).total_seconds()
        total_tasks = self.completed_count + self.failed_count
        avg_processing_ms = (
            self.total_processing_time_ms / self.completed_count
            if self.completed_count > 0
            else 0.0
        )

        return {
            "worker_id": self.config.worker_id,
            "status": self.status.value,
            "uptime_seconds": uptime,
            "completed_tasks": self.completed_count,
            "failed_tasks": self.failed_count,
            "current_load": len(self.current_tasks),
            "max_capacity": self.config.max_concurrent_tasks,
            "avg_processing_ms": avg_processing_ms,
            "total_tasks": total_tasks,
        }

    def _update_processing_time(self, task_id: str):
        """Update total processing time."""
        if task_id in self.current_tasks:
            started = self.current_tasks[task_id].get("started_at")
            if started:
                elapsed = (datetime.now(timezone.utc) - started).total_seconds() * 1000
                self.total_processing_time_ms += elapsed


class WorkerPool:
    """Pool of workers for task distribution."""

    def __init__(self, size: int = 4, config_template: Optional[WorkerConfig] = None):
        self.size = size
        self.workers: Dict[str, Worker] = {}
        self.config_template = config_template

        # Create workers
        for i in range(size):
            worker_id = f"worker-{uuid.uuid4().hex[:8]}"
            config = WorkerConfig(
                worker_id=worker_id,
                **(vars(config_template) if config_template else {}),
            )
            if not config_template:
                config.worker_id = worker_id
            self.workers[worker_id] = Worker(config)

        logger.info(f"Created worker pool with {size} workers")

    async def process_task(
        self,
        task_id: str,
        task_type: str,
        task_data: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """Process task using available worker."""
        # Find worker with lowest load
        available = sorted(
            self.workers.values(),
            key=lambda w: len(w.current_tasks),
        )

        for worker in available:
            if len(worker.current_tasks) < worker.config.max_concurrent_tasks:
                return await worker.process_task(task_id, task_type, task_data)

        logger.warning("No available workers")
        return None

    def register_task_handler(self, task_type: str, handler: Callable):
        """Register handler for all workers."""
        for worker in self.workers.values():
            worker.register_task_handler(task_type, handler)

    def get_pool_stats(self) -> Dict[str, Any]:
        """Get pool statistics."""
        worker_stats = [w.get_stats() for w in self.workers.values()]
        total_completed = sum(s["completed_tasks"] for s in worker_stats)
        total_failed = sum(s["failed_tasks"] for s in worker_stats)
        total_load = sum(s["current_load"] for s in worker_stats)
        total_capacity = sum(s["max_capacity"] for s in worker_stats)

        return {
            "pool_size": self.size,
            "total_completed": total_completed,
            "total_failed": total_failed,
            "current_load": total_load,
            "total_capacity": total_capacity,
            "worker_utilization": total_load / total_capacity if total_capacity > 0 else 0.0,
            "workers": worker_stats,
        }

    async def shutdown(self):
        """Shutdown all workers."""
        for worker in self.workers.values():
            worker.status = WorkerStatus.SHUTDOWN

        logger.info("Worker pool shutdown")


class WorkerManager:
    """High-level worker management."""

    def __init__(self, pool_size: int = 4):
        self.pool = WorkerPool(pool_size)
        self.task_registry: Dict[str, Dict[str, Any]] = {}

    async def submit_task(
        self,
        task_type: str,
        task_data: Dict[str, Any],
    ) -> Optional[str]:
        """Submit task for processing."""
        task_id = str(uuid.uuid4())
        self.task_registry[task_id] = {
            "task_type": task_type,
            "submitted_at": datetime.now(timezone.utc),
            "status": "queued",
        }

        # Process task asynchronously
        result = await self.pool.process_task(task_id, task_type, task_data)

        if result is not None:
            self.task_registry[task_id]["status"] = "completed"
            self.task_registry[task_id]["result"] = result
        else:
            self.task_registry[task_id]["status"] = "failed"

        return task_id

    def register_task_type(self, task_type: str, handler: Callable):
        """Register handler for task type."""
        self.pool.register_task_handler(task_type, handler)

    def get_task_status(self, task_id: str) -> Optional[str]:
        """Get task status."""
        if task_id in self.task_registry:
            return self.task_registry[task_id].get("status")
        return None

    def get_task_result(self, task_id: str) -> Optional[Any]:
        """Get task result."""
        if task_id in self.task_registry:
            return self.task_registry[task_id].get("result")
        return None

    def get_manager_stats(self) -> Dict[str, Any]:
        """Get manager statistics."""
        return {
            "pool_stats": self.pool.get_pool_stats(),
            "total_submitted": len(self.task_registry),
            "completed": sum(1 for t in self.task_registry.values() if t.get("status") == "completed"),
            "failed": sum(1 for t in self.task_registry.values() if t.get("status") == "failed"),
            "queued": sum(1 for t in self.task_registry.values() if t.get("status") == "queued"),
        }


# Global worker manager instance
worker_manager: Optional[WorkerManager] = None


def init_worker_manager(pool_size: int = 4):
    """Initialize global worker manager."""
    global worker_manager
    worker_manager = WorkerManager(pool_size)
    logger.info(f"Worker manager initialized with pool size {pool_size}")


def get_worker_manager() -> WorkerManager:
    """Get global worker manager instance."""
    global worker_manager
    if worker_manager is None:
        init_worker_manager()
    return worker_manager
