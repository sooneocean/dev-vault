"""
Pipeline parallelism for multi-stage processing.

Enables concurrent execution of dependent stages with task scheduling.
"""

import logging
import asyncio
import inspect
from typing import Optional, Dict, Any, List, Callable, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timezone
import time

logger = logging.getLogger(__name__)


class StageStatus(str, Enum):
    """Status of pipeline stage."""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    STALLED = "stalled"


@dataclass
class StageMetrics:
    """Metrics for a pipeline stage."""
    name: str
    items_processed: int = 0
    total_time_ms: float = 0.0
    avg_time_ms: float = 0.0
    min_time_ms: float = float("inf")
    max_time_ms: float = 0.0
    errors: int = 0
    status: StageStatus = StageStatus.IDLE


@dataclass
class PipelineTask:
    """Task in the pipeline."""
    task_id: str
    input_data: Any
    output_data: Optional[Any] = None
    created_at: datetime = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)


class PipelineStage:
    """Single stage in a pipeline."""

    def __init__(
        self,
        name: str,
        process_func: Callable,
        max_queue_size: int = 100,
    ):
        self.name = name
        self.process_func = process_func
        self.max_queue_size = max_queue_size
        self.input_queue: asyncio.Queue = asyncio.Queue(maxsize=max_queue_size)
        self.output_queue: asyncio.Queue = None
        self.metrics = StageMetrics(name=name)
        self.is_running = False

    async def process_item(self, item: PipelineTask) -> PipelineTask:
        """Process a single item."""
        start_time = time.time()

        try:
            # Call process function (handle both sync and async)
            if inspect.iscoroutinefunction(self.process_func):
                result = await self.process_func(item.input_data)
            else:
                result = self.process_func(item.input_data)

            item.output_data = result
            elapsed_ms = (time.time() - start_time) * 1000

            # Update metrics
            self.metrics.items_processed += 1
            self.metrics.total_time_ms += elapsed_ms
            self.metrics.avg_time_ms = self.metrics.total_time_ms / self.metrics.items_processed
            self.metrics.min_time_ms = min(self.metrics.min_time_ms, elapsed_ms)
            self.metrics.max_time_ms = max(self.metrics.max_time_ms, elapsed_ms)

            item.completed_at = datetime.now(timezone.utc)
            return item

        except Exception as e:
            self.metrics.errors += 1
            item.error = str(e)
            logger.error(f"Error in stage {self.name}: {e}")
            return item

    async def run(self):
        """Run the stage processing loop."""
        self.is_running = True
        self.metrics.status = StageStatus.RUNNING

        try:
            while self.is_running:
                try:
                    # Get item from input queue with timeout
                    item = await asyncio.wait_for(self.input_queue.get(), timeout=0.1)

                    if item is None:  # Sentinel value for shutdown
                        break

                    # Process item
                    processed = await self.process_item(item)

                    # Send to output queue if exists
                    if self.output_queue:
                        await self.output_queue.put(processed)

                except asyncio.TimeoutError:
                    # No items available, continue waiting
                    continue
                except Exception as e:
                    logger.error(f"Stage {self.name} error: {e}")
                    self.metrics.status = StageStatus.FAILED
                    break

        finally:
            self.is_running = False
            self.metrics.status = StageStatus.COMPLETED

    async def shutdown(self):
        """Shutdown the stage."""
        self.is_running = False
        # Drain remaining items
        while not self.input_queue.empty():
            try:
                self.input_queue.get_nowait()
            except asyncio.QueueEmpty:
                break


class Pipeline:
    """Multi-stage processing pipeline."""

    def __init__(self, name: str = "default"):
        self.name = name
        self.stages: List[PipelineStage] = []
        self.tasks: Dict[str, PipelineTask] = {}
        self.is_running = False

    def add_stage(
        self,
        name: str,
        process_func: Callable,
        max_queue_size: int = 100,
    ) -> PipelineStage:
        """Add a stage to the pipeline."""
        stage = PipelineStage(name, process_func, max_queue_size)

        # Connect to previous stage
        if self.stages:
            self.stages[-1].output_queue = stage.input_queue

        self.stages.append(stage)
        logger.info(f"Added stage '{name}' to pipeline '{self.name}'")
        return stage

    async def submit_task(self, task_id: str, input_data: Any) -> str:
        """Submit a task to the pipeline."""
        task = PipelineTask(task_id=task_id, input_data=input_data)
        self.tasks[task_id] = task

        if self.stages:
            await self.stages[0].input_queue.put(task)

        return task_id

    async def start(self):
        """Start the pipeline."""
        if self.is_running:
            return

        self.is_running = True

        # Start all stages
        self.stage_tasks = [asyncio.create_task(stage.run()) for stage in self.stages]
        logger.info(f"Pipeline '{self.name}' started with {len(self.stages)} stages")

    async def shutdown(self):
        """Shutdown the pipeline."""
        self.is_running = False

        # Send sentinel to first stage
        if self.stages:
            await self.stages[0].input_queue.put(None)

        # Wait for all stages to complete
        if hasattr(self, "stage_tasks"):
            await asyncio.gather(*self.stage_tasks, return_exceptions=True)

        # Shutdown stages
        for stage in self.stages:
            await stage.shutdown()

        logger.info(f"Pipeline '{self.name}' shutdown")

    def get_task_result(self, task_id: str) -> Optional[PipelineTask]:
        """Get result of a task."""
        return self.tasks.get(task_id)

    def get_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get metrics from all stages."""
        return {
            stage.name: {
                "items_processed": stage.metrics.items_processed,
                "avg_time_ms": stage.metrics.avg_time_ms,
                "min_time_ms": stage.metrics.min_time_ms,
                "max_time_ms": stage.metrics.max_time_ms,
                "errors": stage.metrics.errors,
                "status": stage.metrics.status.value,
            }
            for stage in self.stages
        }

    def get_throughput(self) -> Dict[str, float]:
        """Get throughput (items/sec) for each stage."""
        throughput = {}
        for stage in self.stages:
            if stage.metrics.total_time_ms > 0:
                throughput[stage.name] = (
                    stage.metrics.items_processed / (stage.metrics.total_time_ms / 1000)
                )
            else:
                throughput[stage.name] = 0.0

        return throughput

    def reset(self):
        """Reset pipeline."""
        self.stages.clear()
        self.tasks.clear()
        self.is_running = False


class PipelineOrchestrator:
    """Manages multiple pipelines."""

    def __init__(self):
        self.pipelines: Dict[str, Pipeline] = {}

    def create_pipeline(self, name: str) -> Pipeline:
        """Create a new pipeline."""
        pipeline = Pipeline(name)
        self.pipelines[name] = pipeline
        return pipeline

    def get_pipeline(self, name: str) -> Optional[Pipeline]:
        """Get pipeline by name."""
        return self.pipelines.get(name)

    async def start_all(self):
        """Start all pipelines."""
        for pipeline in self.pipelines.values():
            await pipeline.start()

    async def shutdown_all(self):
        """Shutdown all pipelines."""
        for pipeline in self.pipelines.values():
            await pipeline.shutdown()

    def get_all_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get metrics from all pipelines."""
        return {
            name: pipeline.get_metrics()
            for name, pipeline in self.pipelines.items()
        }

    def reset(self):
        """Reset all pipelines."""
        for pipeline in self.pipelines.values():
            pipeline.reset()
        self.pipelines.clear()


# Global orchestrator instance
orchestrator: Optional[PipelineOrchestrator] = None


def init_orchestrator():
    """Initialize global orchestrator."""
    global orchestrator
    orchestrator = PipelineOrchestrator()
    logger.info("Pipeline orchestrator initialized")


def get_orchestrator() -> PipelineOrchestrator:
    """Get global orchestrator instance."""
    global orchestrator
    if orchestrator is None:
        init_orchestrator()
    return orchestrator
