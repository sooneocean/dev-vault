"""
Streaming input handlers for various video sources.

Supports file-based input, RTMP, HLS/DASH, and RTSP sources.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, AsyncGenerator, Tuple
import numpy as np

logger = logging.getLogger(__name__)


class InputHandler(ABC):
    """Base class for streaming input handlers."""

    def __init__(self, source_url: str):
        self.source_url = source_url
        self.is_connected = False
        self.fps = 30.0
        self.width = 1920
        self.height = 1080

    @abstractmethod
    async def connect(self) -> bool:
        """
        Connect to source.

        Returns:
            True if connection successful
        """
        pass

    @abstractmethod
    async def read_frame(self) -> Optional[np.ndarray]:
        """
        Read next frame from source.

        Returns:
            BGR frame (H, W, 3) uint8 array or None if end of stream
        """
        pass

    @abstractmethod
    async def disconnect(self):
        """Disconnect from source."""
        pass

    async def get_properties(self) -> dict:
        """Get stream properties."""
        return {
            "fps": self.fps,
            "width": self.width,
            "height": self.height,
            "connected": self.is_connected,
        }


class FileInputHandler(InputHandler):
    """Handler for file-based video input."""

    def __init__(self, source_url: str):
        super().__init__(source_url)
        self.reader = None
        self.frame_count = 0

        # Extract file path from URL
        if source_url.startswith("file://"):
            self.file_path = source_url[7:]
        else:
            self.file_path = source_url

    async def connect(self) -> bool:
        """Connect and open video file."""
        try:
            # Attempt to use OpenCV if available
            try:
                import cv2

                self.reader = cv2.VideoCapture(self.file_path)
                if not self.reader.isOpened():
                    logger.error(f"Failed to open video file: {self.file_path}")
                    return False

                # Extract properties
                self.fps = self.reader.get(cv2.CAP_PROP_FPS) or 30.0
                self.width = int(self.reader.get(cv2.CAP_PROP_FRAME_WIDTH))
                self.height = int(self.reader.get(cv2.CAP_PROP_FRAME_HEIGHT))

            except ImportError:
                logger.warning("OpenCV not available, simulating file input")
                # Simulate file input without OpenCV
                if not Path(self.file_path).exists():
                    logger.error(f"File not found: {self.file_path}")
                    return False

                self.reader = None  # Simulate without actual reading

            self.is_connected = True
            logger.info(f"Connected to file: {self.file_path}")
            return True

        except Exception as e:
            logger.error(f"Error connecting to file: {e}")
            return False

    async def read_frame(self) -> Optional[np.ndarray]:
        """Read next frame from file."""
        if not self.is_connected:
            return None

        try:
            if self.reader is None:
                # Simulated reader - return synthetic frames
                frame = np.random.randint(0, 256, (self.height, self.width, 3), dtype=np.uint8)
                self.frame_count += 1
                return frame

            ret, frame = self.reader.read()
            if not ret:
                logger.info(f"End of file reached: {self.file_path}")
                return None

            self.frame_count += 1
            return frame

        except Exception as e:
            logger.error(f"Error reading frame: {e}")
            return None

    async def disconnect(self):
        """Close file."""
        if self.reader is not None:
            try:
                import cv2

                self.reader.release()
            except Exception as e:
                logger.error(f"Error closing file: {e}")

        self.is_connected = False
        logger.info(f"Disconnected from file: {self.file_path}")


class RTMPInputHandler(InputHandler):
    """Handler for RTMP stream input."""

    def __init__(self, source_url: str):
        super().__init__(source_url)
        self.reader = None
        self.frame_count = 0

    async def connect(self) -> bool:
        """Connect to RTMP stream."""
        try:
            # Attempt to use OpenCV for RTMP
            try:
                import cv2

                self.reader = cv2.VideoCapture(self.source_url)
                if not self.reader.isOpened():
                    logger.error(f"Failed to connect to RTMP: {self.source_url}")
                    return False

                # Extract properties
                self.fps = self.reader.get(cv2.CAP_PROP_FPS) or 30.0
                self.width = int(self.reader.get(cv2.CAP_PROP_FRAME_WIDTH)) or 1920
                self.height = int(self.reader.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 1080

            except ImportError:
                logger.warning("OpenCV not available, simulating RTMP input")
                self.reader = None

            self.is_connected = True
            logger.info(f"Connected to RTMP: {self.source_url}")
            return True

        except Exception as e:
            logger.error(f"Error connecting to RTMP: {e}")
            return False

    async def read_frame(self) -> Optional[np.ndarray]:
        """Read frame from RTMP stream."""
        if not self.is_connected:
            return None

        try:
            if self.reader is None:
                # Simulated RTMP - return synthetic frames
                frame = np.random.randint(0, 256, (self.height, self.width, 3), dtype=np.uint8)
                self.frame_count += 1
                await asyncio.sleep(1.0 / self.fps)  # Simulate frame rate
                return frame

            ret, frame = self.reader.read()
            if not ret:
                logger.info(f"RTMP stream ended: {self.source_url}")
                return None

            self.frame_count += 1
            return frame

        except Exception as e:
            logger.error(f"Error reading RTMP frame: {e}")
            return None

    async def disconnect(self):
        """Disconnect from RTMP stream."""
        if self.reader is not None:
            try:
                import cv2

                self.reader.release()
            except Exception as e:
                logger.error(f"Error closing RTMP: {e}")

        self.is_connected = False
        logger.info(f"Disconnected from RTMP: {self.source_url}")


class RTSPInputHandler(InputHandler):
    """Handler for RTSP stream input (IP cameras)."""

    def __init__(self, source_url: str):
        super().__init__(source_url)
        self.reader = None
        self.frame_count = 0
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 3

    async def connect(self) -> bool:
        """Connect to RTSP stream."""
        try:
            # Attempt to use OpenCV for RTSP
            try:
                import cv2

                self.reader = cv2.VideoCapture(
                    self.source_url,
                    cv2.CAP_FFMPEG,
                )
                if not self.reader.isOpened():
                    logger.error(f"Failed to connect to RTSP: {self.source_url}")
                    return False

                # Extract properties
                self.fps = self.reader.get(cv2.CAP_PROP_FPS) or 30.0
                self.width = int(self.reader.get(cv2.CAP_PROP_FRAME_WIDTH)) or 1920
                self.height = int(self.reader.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 1080

            except ImportError:
                logger.warning("OpenCV not available, simulating RTSP input")
                self.reader = None

            self.is_connected = True
            self.reconnect_attempts = 0
            logger.info(f"Connected to RTSP: {self.source_url}")
            return True

        except Exception as e:
            logger.error(f"Error connecting to RTSP: {e}")
            return False

    async def read_frame(self) -> Optional[np.ndarray]:
        """Read frame from RTSP stream with reconnection."""
        if not self.is_connected:
            return None

        try:
            if self.reader is None:
                # Simulated RTSP - return synthetic frames
                frame = np.random.randint(0, 256, (self.height, self.width, 3), dtype=np.uint8)
                self.frame_count += 1
                await asyncio.sleep(1.0 / self.fps)
                return frame

            ret, frame = self.reader.read()

            if not ret:
                # Try to reconnect
                if self.reconnect_attempts < self.max_reconnect_attempts:
                    logger.warning(f"RTSP frame read failed, attempting reconnection")
                    self.reconnect_attempts += 1
                    await asyncio.sleep(1.0)
                    await self.disconnect()
                    return await self._reconnect_and_read()
                else:
                    logger.error(f"Max reconnection attempts reached for {self.source_url}")
                    return None

            self.frame_count += 1
            self.reconnect_attempts = 0  # Reset on successful read
            return frame

        except Exception as e:
            logger.error(f"Error reading RTSP frame: {e}")
            return None

    async def _reconnect_and_read(self) -> Optional[np.ndarray]:
        """Reconnect and attempt to read frame."""
        if await self.connect():
            return await self.read_frame()
        return None

    async def disconnect(self):
        """Disconnect from RTSP stream."""
        if self.reader is not None:
            try:
                import cv2

                self.reader.release()
            except Exception as e:
                logger.error(f"Error closing RTSP: {e}")

        self.is_connected = False
        logger.info(f"Disconnected from RTSP: {self.source_url}")


class HLSInputHandler(InputHandler):
    """Handler for HLS/DASH stream input."""

    def __init__(self, source_url: str):
        super().__init__(source_url)
        self.reader = None
        self.frame_count = 0

    async def connect(self) -> bool:
        """Connect to HLS stream."""
        try:
            # Use OpenCV to read HLS stream
            try:
                import cv2

                self.reader = cv2.VideoCapture(self.source_url)
                if not self.reader.isOpened():
                    logger.error(f"Failed to connect to HLS: {self.source_url}")
                    return False

                # Extract properties
                self.fps = self.reader.get(cv2.CAP_PROP_FPS) or 30.0
                self.width = int(self.reader.get(cv2.CAP_PROP_FRAME_WIDTH)) or 1920
                self.height = int(self.reader.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 1080

            except ImportError:
                logger.warning("OpenCV not available, simulating HLS input")
                self.reader = None

            self.is_connected = True
            logger.info(f"Connected to HLS: {self.source_url}")
            return True

        except Exception as e:
            logger.error(f"Error connecting to HLS: {e}")
            return False

    async def read_frame(self) -> Optional[np.ndarray]:
        """Read frame from HLS stream."""
        if not self.is_connected:
            return None

        try:
            if self.reader is None:
                # Simulated HLS - return synthetic frames
                frame = np.random.randint(0, 256, (self.height, self.width, 3), dtype=np.uint8)
                self.frame_count += 1
                await asyncio.sleep(1.0 / self.fps)
                return frame

            ret, frame = self.reader.read()
            if not ret:
                logger.info(f"HLS stream ended: {self.source_url}")
                return None

            self.frame_count += 1
            return frame

        except Exception as e:
            logger.error(f"Error reading HLS frame: {e}")
            return None

    async def disconnect(self):
        """Disconnect from HLS stream."""
        if self.reader is not None:
            try:
                import cv2

                self.reader.release()
            except Exception as e:
                logger.error(f"Error closing HLS: {e}")

        self.is_connected = False
        logger.info(f"Disconnected from HLS: {self.source_url}")


def create_input_handler(source_url: str) -> InputHandler:
    """
    Factory function to create appropriate input handler.

    Args:
        source_url: URL or path to source

    Returns:
        InputHandler instance

    Examples:
        file:///path/to/video.mp4 → FileInputHandler
        rtmp://example.com/live/stream → RTMPInputHandler
        rtsp://camera.example.com/stream → RTSPInputHandler
        https://example.com/stream.m3u8 → HLSInputHandler
    """
    if source_url.startswith("file://") or source_url.endswith(
        (".mp4", ".avi", ".mkv", ".mov", ".flv")
    ):
        return FileInputHandler(source_url)
    elif source_url.startswith("rtmp://"):
        return RTMPInputHandler(source_url)
    elif source_url.startswith("rtsp://"):
        return RTSPInputHandler(source_url)
    elif source_url.startswith("http") and ".m3u8" in source_url:
        return HLSInputHandler(source_url)
    else:
        # Default to file handler for unknown formats
        logger.warning(f"Unknown source format, defaulting to file handler: {source_url}")
        return FileInputHandler(source_url)
