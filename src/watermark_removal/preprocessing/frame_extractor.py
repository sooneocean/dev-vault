"""Frame extraction from video files."""

import logging
from pathlib import Path

import cv2

from ..core.types import Frame

logger = logging.getLogger(__name__)


class FrameExtractor:
    """Extract frames from video file."""

    def __init__(self, video_path: str) -> None:
        """Initialize frame extractor.

        Args:
            video_path: Path to video file.

        Raises:
            FileNotFoundError: If video file does not exist.
            ValueError: If video file cannot be opened.
        """
        self.video_path = Path(video_path)
        if not self.video_path.exists():
            raise FileNotFoundError(f"Video file not found: {self.video_path}")

        # Open video to validate and extract metadata
        self.cap = cv2.VideoCapture(str(self.video_path))
        if not self.cap.isOpened():
            raise ValueError(f"Failed to open video: {self.video_path}")

        # Extract metadata
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        logger.info(
            f"Video loaded: {self.video_path} - "
            f"{self.total_frames} frames @ {self.fps:.2f} fps, "
            f"{self.width}x{self.height}"
        )

    def extract_all(self) -> list[Frame]:
        """Extract all frames from video.

        Returns:
            List of Frame objects in order.

        Raises:
            ValueError: If frame reading fails mid-extraction.
        """
        frames = []
        frame_id = 0

        while True:
            ret, frame = self.cap.read()
            if not ret:
                break

            # Calculate timestamp in milliseconds
            timestamp_ms = (frame_id / self.fps) * 1000.0

            # Create Frame object
            frame_obj = Frame(frame_id=frame_id, image=frame, timestamp_ms=timestamp_ms)
            frames.append(frame_obj)

            frame_id += 1

        self.cap.release()

        logger.info(f"Extracted {len(frames)} frames from video")

        return frames

    def __del__(self) -> None:
        """Cleanup: release video capture on deletion."""
        if hasattr(self, "cap") and self.cap is not None:
            self.cap.release()
