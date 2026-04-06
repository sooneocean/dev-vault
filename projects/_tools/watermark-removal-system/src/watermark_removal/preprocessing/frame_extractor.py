"""
Video frame extraction and metadata handling.

Extracts all frames from a video file, saves as PNG sequence, and returns Frame metadata.
"""

import logging
import cv2
from pathlib import Path
from typing import Generator

from ..core.types import Frame
from ..utils.image_io import get_video_metadata


logger = logging.getLogger(__name__)


class FrameExtractor:
    """
    Extracts frames from video files.

    Handles frame reading, PNG sequence generation, and metadata tracking.
    """

    def __init__(self, video_path: str | Path, output_dir: str | Path):
        """
        Initialize FrameExtractor.

        Args:
            video_path: Path to input video file
            output_dir: Directory to save PNG frames

        Raises:
            FileNotFoundError: If video file does not exist
        """
        self.video_path = Path(video_path)
        self.output_dir = Path(output_dir)

        if not self.video_path.exists():
            raise FileNotFoundError(f"Video file not found: {self.video_path}")

        # Verify video can be opened
        cap = cv2.VideoCapture(str(self.video_path))
        if not cap.isOpened():
            raise ValueError(f"Failed to open video: {self.video_path}")
        cap.release()

        self.output_dir.mkdir(parents=True, exist_ok=True)

    def extract_all(self) -> list[Frame]:
        """
        Extract all frames from video.

        Returns:
            List of Frame objects

        Raises:
            RuntimeError: If frame extraction fails
        """
        logger.info(f"Extracting frames from {self.video_path}")

        cap = cv2.VideoCapture(str(self.video_path))
        if not cap.isOpened():
            raise RuntimeError(f"Failed to open video: {self.video_path}")

        try:
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            logger.info(
                f"Video metadata: {width}x{height}, {fps:.2f}fps, {total_frames} frames"
            )

            frames = []
            frame_id = 0

            while True:
                ret, frame_bgr = cap.read()
                if not ret:
                    break

                # Calculate timestamp in milliseconds
                timestamp_ms = frame_id / fps * 1000.0 if fps > 0 else 0.0

                # Create Frame object
                frame = Frame(
                    frame_id=frame_id,
                    image=frame_bgr,
                    timestamp_ms=timestamp_ms,
                )

                # Save PNG
                frame_path = self.output_dir / f"frame_{frame_id:06d}.png"
                cv2.imwrite(str(frame_path), frame_bgr)

                frames.append(frame)
                frame_id += 1

            logger.info(f"Extracted {len(frames)} frames")
            return frames

        finally:
            cap.release()

    def extract_range(self, start_frame: int, end_frame: int) -> list[Frame]:
        """
        Extract a range of frames from video.

        Args:
            start_frame: 0-indexed start frame (inclusive)
            end_frame: 0-indexed end frame (exclusive)

        Returns:
            List of Frame objects for the specified range
        """
        cap = cv2.VideoCapture(str(self.video_path))
        if not cap.isOpened():
            raise RuntimeError(f"Failed to open video: {self.video_path}")

        try:
            fps = cap.get(cv2.CAP_PROP_FPS)
            frames = []

            # Seek to start frame
            cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

            for frame_id in range(start_frame, end_frame):
                ret, frame_bgr = cap.read()
                if not ret:
                    break

                timestamp_ms = frame_id / fps * 1000.0 if fps > 0 else 0.0
                frame = Frame(
                    frame_id=frame_id,
                    image=frame_bgr,
                    timestamp_ms=timestamp_ms,
                )
                frames.append(frame)

            return frames

        finally:
            cap.release()

    def extract_generator(self) -> Generator[Frame, None, None]:
        """
        Extract frames as generator (memory-efficient for large videos).

        Yields:
            Frame objects one at a time
        """
        cap = cv2.VideoCapture(str(self.video_path))
        if not cap.isOpened():
            raise RuntimeError(f"Failed to open video: {self.video_path}")

        try:
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_id = 0

            while True:
                ret, frame_bgr = cap.read()
                if not ret:
                    break

                timestamp_ms = frame_id / fps * 1000.0 if fps > 0 else 0.0
                frame = Frame(
                    frame_id=frame_id,
                    image=frame_bgr,
                    timestamp_ms=timestamp_ms,
                )

                # Save PNG
                frame_path = self.output_dir / f"frame_{frame_id:06d}.png"
                cv2.imwrite(str(frame_path), frame_bgr)

                yield frame
                frame_id += 1

        finally:
            cap.release()
