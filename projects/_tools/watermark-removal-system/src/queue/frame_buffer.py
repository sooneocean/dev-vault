"""
Ring buffer implementation for zero-copy frame streaming.

Manages efficient frame passing between input and processing stages.
"""

import asyncio
import logging
from typing import Optional, Callable
from dataclasses import dataclass
from collections import deque
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class Frame:
    """Frame data with metadata."""
    frame_id: int
    image: np.ndarray  # BGR, (H, W, 3), uint8
    timestamp_ms: float
    sequence: int  # Order in stream


class FrameBuffer:
    """
    Ring buffer for streaming frame processing.

    Supports:
    - Configurable size
    - Backpressure handling (drop or queue)
    - Async producer/consumer
    - Statistics tracking
    """

    def __init__(
        self,
        max_size: int = 30,
        overflow_policy: str = "drop",  # "drop" or "block"
    ):
        """
        Initialize frame buffer.

        Args:
            max_size: Maximum frames to buffer
            overflow_policy: How to handle full buffer
                - "drop": Drop oldest frame
                - "block": Wait until space available
        """
        self.max_size = max_size
        self.overflow_policy = overflow_policy
        self.buffer = deque(maxlen=max_size)
        self.lock = asyncio.Lock()
        self.not_empty = asyncio.Condition(self.lock)

        # Statistics
        self.frames_processed = 0
        self.frames_dropped = 0
        self.frames_added = 0

        logger.info(f"FrameBuffer: size={max_size}, policy={overflow_policy}")

    async def put(self, frame: Frame) -> bool:
        """
        Add frame to buffer.

        Args:
            frame: Frame to add

        Returns:
            True if added, False if dropped
        """
        async with self.lock:
            if len(self.buffer) >= self.max_size:
                if self.overflow_policy == "drop":
                    # Drop oldest (implicitly via maxlen)
                    self.frames_dropped += 1
                    logger.debug(f"Frame {frame.frame_id} dropped (buffer full)")
                    return False
                elif self.overflow_policy == "block":
                    # Wait for space
                    while len(self.buffer) >= self.max_size:
                        await self.not_empty.wait()

            self.buffer.append(frame)
            self.frames_added += 1
            self.not_empty.notify_all()
            return True

    async def get(self) -> Optional[Frame]:
        """
        Get next frame from buffer.

        Waits if buffer empty.

        Returns:
            Frame or None if buffer closed
        """
        async with self.lock:
            while len(self.buffer) == 0:
                await self.not_empty.wait()

            if len(self.buffer) == 0:
                return None

            frame = self.buffer.popleft()
            self.frames_processed += 1
            self.not_empty.notify_all()
            return frame

    async def get_nowait(self) -> Optional[Frame]:
        """
        Get frame without waiting.

        Returns:
            Frame or None if empty
        """
        async with self.lock:
            if len(self.buffer) == 0:
                return None

            frame = self.buffer.popleft()
            self.frames_processed += 1
            self.not_empty.notify_all()
            return frame

    def size(self) -> int:
        """Current buffer size."""
        return len(self.buffer)

    def is_full(self) -> bool:
        """Check if buffer is full."""
        return len(self.buffer) >= self.max_size

    def is_empty(self) -> bool:
        """Check if buffer is empty."""
        return len(self.buffer) == 0

    def stats(self) -> dict:
        """Get buffer statistics."""
        return {
            "current_size": len(self.buffer),
            "max_size": self.max_size,
            "frames_added": self.frames_added,
            "frames_processed": self.frames_processed,
            "frames_dropped": self.frames_dropped,
            "queue_depth": len(self.buffer),
        }

    async def clear(self):
        """Clear all frames from buffer."""
        async with self.lock:
            self.buffer.clear()
            self.not_empty.notify_all()


class FrameQueue:
    """
    Async-friendly frame queue with callback support.

    Supports processing frames with custom functions.
    """

    def __init__(
        self,
        buffer_size: int = 30,
        overflow_policy: str = "drop",
    ):
        """Initialize frame queue."""
        self.buffer = FrameBuffer(buffer_size, overflow_policy)
        self.processing = False
        self.processor_fn: Optional[Callable] = None

    async def add_frame(self, frame: Frame) -> bool:
        """Add frame to queue."""
        return await self.buffer.put(frame)

    async def process_all(
        self,
        processor: Callable[[Frame], any],
    ) -> int:
        """
        Process all frames in queue.

        Args:
            processor: Async function to process each frame

        Returns:
            Number of frames processed
        """
        count = 0
        while not self.buffer.is_empty():
            frame = await self.buffer.get_nowait()
            if frame is not None:
                try:
                    await processor(frame)
                    count += 1
                except Exception as e:
                    logger.error(f"Error processing frame {frame.frame_id}: {e}")

        return count

    def get_stats(self) -> dict:
        """Get queue statistics."""
        return self.buffer.stats()


class BackpressureHandler:
    """
    Handles backpressure when buffer is full.

    Strategies:
    - Drop frames
    - Queue and wait
    - Adjust quality
    """

    def __init__(
        self,
        buffer: FrameBuffer,
        strategy: str = "drop",
    ):
        """
        Initialize backpressure handler.

        Args:
            buffer: Frame buffer to monitor
            strategy: How to handle pressure
                - "drop": Drop frames
                - "queue": Wait for space
                - "throttle": Reduce input rate
        """
        self.buffer = buffer
        self.strategy = strategy
        self.dropped_count = 0
        self.throttle_rate = 1.0  # Input rate multiplier

    async def handle(self, frame: Frame) -> bool:
        """
        Handle frame with backpressure strategy.

        Returns:
            True if frame accepted, False if dropped
        """
        if self.strategy == "drop":
            return await self.buffer.put(frame)

        elif self.strategy == "queue":
            # Wait indefinitely
            self.buffer.overflow_policy = "block"
            return await self.buffer.put(frame)

        elif self.strategy == "throttle":
            # Adjust input rate
            if self.buffer.is_full():
                self.throttle_rate *= 0.9  # Reduce rate
                logger.debug(f"Throttling: rate={self.throttle_rate:.2%}")
            elif not self.buffer.is_full():
                self.throttle_rate = min(1.0, self.throttle_rate * 1.05)  # Increase rate

            return await self.buffer.put(frame)

        return False

    def get_throttle_rate(self) -> float:
        """Get current input throttle rate."""
        return self.throttle_rate
