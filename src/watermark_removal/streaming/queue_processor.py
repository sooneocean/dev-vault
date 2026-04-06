"""Async background task runner for processing queued frames."""

import asyncio
import logging
import time
from typing import Any, Callable, Optional

import numpy as np

from .session_manager import ProcessingResult, StreamingSession

logger = logging.getLogger(__name__)


class BackgroundTaskRunner:
    """Async loop consuming frames from queue and processing them."""

    def __init__(
        self,
        process_func: Callable[[np.ndarray, Any], tuple[np.ndarray, dict]],
        queue_size: int = 100,
    ) -> None:
        """Initialize background task runner.

        Args:
            process_func: Async function that processes a frame.
                         Signature: async func(frame: np.ndarray, session: StreamingSession) -> (output_frame, metrics_dict)
            queue_size: Maximum queue size before dropping frames.
        """
        self.process_func = process_func
        self.queue_size = queue_size
        self.task_queue: asyncio.Queue[tuple[StreamingSession, int, np.ndarray]] = (
            asyncio.Queue()
        )
        self.is_running = False
        self.background_task: Optional[asyncio.Task] = None
        self.processed_count = 0
        self.error_count = 0

    async def start(self) -> None:
        """Start the background processing loop."""
        if self.is_running:
            logger.warning("BackgroundTaskRunner already running")
            return
        self.is_running = True
        self.background_task = asyncio.create_task(self._process_loop())
        logger.info("BackgroundTaskRunner started")

    async def stop(self) -> None:
        """Stop the background processing loop."""
        if not self.is_running:
            logger.warning("BackgroundTaskRunner not running")
            return
        self.is_running = False
        if self.background_task:
            await self.background_task
        logger.info(
            f"BackgroundTaskRunner stopped. "
            f"Processed: {self.processed_count}, Errors: {self.error_count}"
        )

    async def enqueue_frame(
        self, session: StreamingSession, frame_id: int, frame: np.ndarray
    ) -> bool:
        """Enqueue a frame for processing.

        Args:
            session: StreamingSession instance.
            frame_id: Frame identifier.
            frame: Frame data (HxWx3, uint8).

        Returns:
            bool: True if enqueued successfully, False if queue full.
        """
        if self.task_queue.full():
            logger.warning(
                f"Queue full ({self.queue_size}), dropping oldest frame for session {session.session_id}"
            )
            return False
        await self.task_queue.put((session, frame_id, frame))
        session.update_activity()
        return True

    async def _process_loop(self) -> None:
        """Main processing loop consuming from queue."""
        while self.is_running:
            try:
                # Wait for next task with timeout to check is_running flag
                try:
                    session, frame_id, frame = await asyncio.wait_for(
                        self.task_queue.get(), timeout=0.5
                    )
                except asyncio.TimeoutError:
                    continue

                # Create pending result
                result = ProcessingResult(
                    frame_id=frame_id,
                    session_id=session.session_id,
                    status="processing",
                )
                session.cache_result(result)

                # Process frame with error handling
                try:
                    start_time = time.time()
                    output_frame, metrics = await self.process_func(frame, session)
                    elapsed_ms = (time.time() - start_time) * 1000

                    # Update result
                    result.output_frame = output_frame
                    result.metrics = metrics
                    result.status = "completed"
                    result.completed_at = time.time()

                    # Add metrics to session accumulator
                    for metric_name, value in metrics.items():
                        if isinstance(value, (int, float)):
                            session.add_metric(metric_name, float(value))

                    session.add_metric("processing_time_ms", elapsed_ms)
                    session.cache_result(result)
                    self.processed_count += 1

                    logger.debug(
                        f"Processed frame {frame_id} for session {session.session_id} "
                        f"in {elapsed_ms:.1f}ms"
                    )
                except Exception as e:
                    # Mark result as error
                    result.status = "error"
                    result.error_message = str(e)
                    result.completed_at = time.time()
                    session.cache_result(result)
                    session.processing_errors += 1
                    self.error_count += 1
                    logger.error(
                        f"Error processing frame {frame_id} for session {session.session_id}: {e}"
                    )

            except Exception as e:
                logger.error(f"Unexpected error in process loop: {e}")
                await asyncio.sleep(0.1)

    def get_queue_depth(self) -> int:
        """Get current queue size.

        Returns:
            int: Number of items in queue.
        """
        return self.task_queue.qsize()

    def get_stats(self) -> dict[str, int]:
        """Get processing statistics.

        Returns:
            dict: Statistics including processed count, error count, queue depth.
        """
        return {
            "processed_count": self.processed_count,
            "error_count": self.error_count,
            "queue_depth": self.get_queue_depth(),
            "is_running": self.is_running,
        }
