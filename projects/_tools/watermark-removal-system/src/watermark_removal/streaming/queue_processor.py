"""
Async background task processing for streaming frames.

Consumes frames from queue, processes via optical flow + detection + inpaint,
and caches results in StreamingSession.
"""

import asyncio
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional
import numpy as np

from .session_manager import StreamingSession, FrameResult

logger = logging.getLogger(__name__)


class BackgroundTaskRunner:
    """Process frames asynchronously from a queue."""

    def __init__(
        self,
        session: StreamingSession,
        max_queue_size: int = 100,
        timeout_per_frame_sec: float = 300.0,
    ):
        """
        Initialize background task runner.

        Args:
            session: StreamingSession instance to store results
            max_queue_size: Max frames in queue before dropping (backpressure)
            timeout_per_frame_sec: Timeout per frame processing (seconds)
        """
        self.session = session
        self.queue: asyncio.Queue = asyncio.Queue(maxsize=max_queue_size)
        self.timeout_per_frame_sec = timeout_per_frame_sec
        self._running = False
        self._worker_task: Optional[asyncio.Task] = None
        logger.info(
            f"BackgroundTaskRunner: queue_size={max_queue_size}, timeout={timeout_per_frame_sec}s"
        )

    async def start(self):
        """Start the background processing loop."""
        self._running = True
        self._worker_task = asyncio.create_task(self._process_queue())
        logger.info(f"Started background task runner for session {self.session.session_id}")

    async def stop(self):
        """Stop the background processing loop."""
        self._running = False
        if self._worker_task:
            try:
                await asyncio.wait_for(self._worker_task, timeout=5.0)
            except asyncio.TimeoutError:
                self._worker_task.cancel()
            logger.info(f"Stopped background task runner for session {self.session.session_id}")

    async def submit_frame(
        self,
        frame_id: int,
        frame_data: bytes,
    ) -> bool:
        """
        Submit a frame for asynchronous processing.

        Args:
            frame_id: Unique frame identifier
            frame_data: Serialized frame (PNG/JPEG bytes)

        Returns:
            True if queued, False if queue full (backpressure overflow)
        """
        if self.queue.full():
            logger.warning(f"Queue full for session {self.session.session_id}, dropping frame {frame_id}")
            return False

        await self.queue.put((frame_id, frame_data))
        logger.debug(f"Queued frame {frame_id} for session {self.session.session_id}")
        return True

    async def _process_queue(self):
        """
        Background worker loop: process frames from queue.

        For each frame:
        1. Create FrameResult with "processing" status
        2. Execute optical flow alignment (Unit 21)
        3. Execute ensemble detection (Unit 22)
        4. Execute inpainting if watermark detected
        5. Cache result and update metrics
        """
        while self._running:
            try:
                # Timeout to allow graceful shutdown
                frame_id, frame_data = await asyncio.wait_for(
                    self.queue.get(),
                    timeout=1.0,
                )

                # Create result entry with "processing" status
                result = FrameResult(
                    frame_id=frame_id,
                    status="processing",
                    timestamp=datetime.now(),
                )
                self.session.add_frame_result(frame_id, result)
                logger.debug(f"Processing frame {frame_id}")

                # Process frame with timeout
                try:
                    await asyncio.wait_for(
                        self._process_single_frame(result, frame_data),
                        timeout=self.timeout_per_frame_sec,
                    )
                    result.status = "completed"
                    logger.info(f"Completed frame {frame_id}")

                except asyncio.TimeoutError:
                    result.status = "error"
                    result.error_message = f"Processing timeout after {self.timeout_per_frame_sec}s"
                    self.session.error_count += 1
                    logger.error(f"Frame {frame_id} processing timeout")

                except Exception as e:
                    result.status = "error"
                    result.error_message = str(e)
                    self.session.error_count += 1
                    logger.error(f"Frame {frame_id} processing failed: {e}")

                finally:
                    self.queue.task_done()
                    self.session.update_activity()

            except asyncio.TimeoutError:
                # Queue empty, continue waiting
                continue

    async def _process_single_frame(
        self,
        result: FrameResult,
        frame_data: bytes,
    ) -> None:
        """
        Process a single frame through streaming pipeline.

        Phases (placeholder for Unit 21, 22, inpaint integration):
        1. Decode frame data to numpy array
        2. Optical flow alignment (Unit 21 OpticalFlowProcessor)
        3. Ensemble detection (Unit 22 EnsembleDetector)
        4. If watermark detected: inpaint via InpaintExecutor
        5. Post-processing (smoothing, blending)
        6. Encode output and save

        Args:
            result: FrameResult to populate with metrics/output
            frame_data: Raw frame bytes (PNG/JPEG)
        """
        # Lazy imports to avoid hard dependencies at module load
        try:
            import cv2
        except ImportError:
            raise ImportError("OpenCV required for frame decoding")

        start_time = datetime.now()

        # Phase 1: Decode frame
        frame_array = cv2.imdecode(
            np.frombuffer(frame_data, np.uint8),
            cv2.IMREAD_COLOR,
        )
        if frame_array is None:
            raise ValueError("Failed to decode frame data")

        decode_time_ms = (datetime.now() - start_time).total_seconds() * 1000

        # Phase 2: Optical flow alignment (Unit 21)
        # TODO: Integrate OpticalFlowProcessor from Unit 21
        # optical_flow = await flow_processor.align_frame(frame_array)
        flow_time_ms = 0  # Placeholder

        # Phase 3: Ensemble detection (Unit 22)
        # TODO: Integrate EnsembleDetector from Unit 22
        # bboxes, confidences = await ensemble_detector.detect(frame_array)
        watermark_detected = False
        detection_time_ms = 0  # Placeholder
        bboxes = []

        # Phase 4: Inpaint if watermark detected
        inpaint_time_ms = 0
        output_path = None
        if watermark_detected and bboxes:
            # TODO: Integrate InpaintExecutor for detected regions
            # For now, just store frame as output
            output_path = Path(f"/tmp/frame_{result.frame_id}_inpainted.png")
            inpaint_time_ms = 0

        # Phase 5: Post-processing (smoothing, blending)
        # TODO: Apply temporal smoothing if previous frame available
        # TODO: Apply Poisson blending for seamless inpainting
        postprocess_time_ms = 0

        # Phase 6: Encode output
        total_time_ms = (datetime.now() - start_time).total_seconds() * 1000

        # Populate result
        result.output_path = output_path
        result.metrics = {
            "frame_id": result.frame_id,
            "total_time_ms": total_time_ms,
            "decode_time_ms": decode_time_ms,
            "flow_time_ms": flow_time_ms,
            "detection_time_ms": detection_time_ms,
            "inpaint_time_ms": inpaint_time_ms,
            "postprocess_time_ms": postprocess_time_ms,
            "watermark_detected": watermark_detected,
            "bbox_count": len(bboxes) if bboxes else 0,
        }

        # Accumulate metrics in session
        self.session.metrics_accumulator["frames_processed"] = (
            self.session.metrics_accumulator.get("frames_processed", 0) + 1
        )
        self.session.metrics_accumulator["total_time_ms"] = (
            self.session.metrics_accumulator.get("total_time_ms", 0) + total_time_ms
        )
        if watermark_detected:
            self.session.metrics_accumulator["watermarks_detected"] = (
                self.session.metrics_accumulator.get("watermarks_detected", 0) + 1
            )

        logger.debug(
            f"Frame {result.frame_id}: {total_time_ms:.1f}ms "
            f"(decode={decode_time_ms:.1f}, flow={flow_time_ms:.1f}, "
            f"detect={detection_time_ms:.1f}, inpaint={inpaint_time_ms:.1f})"
        )

    async def get_queue_size(self) -> int:
        """Get current queue size (frames pending processing)."""
        return self.queue.qsize()

    async def wait_all_done(self, timeout_sec: float = 3600.0) -> bool:
        """
        Wait for all queued frames to complete processing.

        Args:
            timeout_sec: Max wait time (seconds)

        Returns:
            True if all frames processed, False if timeout
        """
        try:
            await asyncio.wait_for(self.queue.join(), timeout=timeout_sec)
            return True
        except asyncio.TimeoutError:
            logger.warning(
                f"Timeout waiting for queue completion in session {self.session.session_id}"
            )
            return False
