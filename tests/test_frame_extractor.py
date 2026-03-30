"""Tests for frame extraction."""

import tempfile
from pathlib import Path

import cv2
import numpy as np
import pytest

from src.watermark_removal.core.types import Frame
from src.watermark_removal.preprocessing.frame_extractor import FrameExtractor


@pytest.fixture
def temp_video_dir():
    """Create temporary directory for test videos."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def create_test_video(
    video_path: Path,
    width: int = 640,
    height: int = 480,
    frame_count: int = 10,
    fps: float = 30.0,
) -> None:
    """Create a synthetic test video.

    Args:
        video_path: Path to save video.
        width: Video width.
        height: Video height.
        frame_count: Number of frames.
        fps: Frames per second.
    """
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(video_path), fourcc, fps, (width, height))

    if not writer.isOpened():
        raise ValueError(f"Failed to create video: {video_path}")

    for frame_id in range(frame_count):
        # Create frame with simple pattern (diagonal lines + frame_id)
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        # Add diagonal line
        cv2.line(frame, (0, 0), (width, height), (255, 0, 0), 2)
        # Add text with frame ID
        cv2.putText(
            frame,
            f"Frame {frame_id}",
            (50, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (0, 255, 0),
            2,
        )
        writer.write(frame)

    writer.release()


class TestFrameExtractor:
    """Tests for FrameExtractor class."""

    def test_frame_extractor_valid_video(self, temp_video_dir):
        """Test extraction from valid video file."""
        video_path = temp_video_dir / "test.mp4"
        create_test_video(video_path, frame_count=10)

        extractor = FrameExtractor(str(video_path))
        frames = extractor.extract_all()

        assert len(frames) == 10
        assert isinstance(frames[0], Frame)
        assert frames[0].frame_id == 0
        assert frames[9].frame_id == 9
        assert all(f.image.shape == (480, 640, 3) for f in frames)
        assert all(f.image.dtype == np.uint8 for f in frames)

    def test_frame_extractor_frame_timestamps(self, temp_video_dir):
        """Test that timestamps are calculated correctly."""
        video_path = temp_video_dir / "test.mp4"
        fps = 30.0
        create_test_video(video_path, frame_count=5, fps=fps)

        extractor = FrameExtractor(str(video_path))
        frames = extractor.extract_all()

        # Check timestamps: frame_i should be at (i / fps) * 1000 ms
        for i, frame in enumerate(frames):
            expected_ts = (i / fps) * 1000.0
            assert abs(frame.timestamp_ms - expected_ts) < 0.1

    def test_frame_extractor_non_standard_fps(self, temp_video_dir):
        """Test extraction from video with non-standard fps."""
        video_path = temp_video_dir / "test.mp4"
        fps = 23.976  # Non-standard fps
        create_test_video(video_path, frame_count=6, fps=fps)

        extractor = FrameExtractor(str(video_path))
        frames = extractor.extract_all()

        assert len(frames) == 6
        # Verify timestamps are calculated with correct fps
        for i, frame in enumerate(frames):
            expected_ts = (i / fps) * 1000.0
            assert abs(frame.timestamp_ms - expected_ts) < 0.1

    def test_frame_extractor_single_frame_video(self, temp_video_dir):
        """Test extraction from video with only 1 frame."""
        video_path = temp_video_dir / "single.mp4"
        create_test_video(video_path, frame_count=1)

        extractor = FrameExtractor(str(video_path))
        frames = extractor.extract_all()

        assert len(frames) == 1
        assert frames[0].frame_id == 0
        assert frames[0].timestamp_ms == 0.0

    def test_frame_extractor_metadata(self, temp_video_dir):
        """Test that video metadata is extracted correctly."""
        video_path = temp_video_dir / "test.mp4"
        width, height, frame_count, fps = 800, 600, 15, 24.0
        create_test_video(video_path, width=width, height=height, frame_count=frame_count, fps=fps)

        extractor = FrameExtractor(str(video_path))

        assert extractor.width == width
        assert extractor.height == height
        assert extractor.total_frames == frame_count
        assert abs(extractor.fps - fps) < 0.1

    def test_frame_extractor_bgr_format(self, temp_video_dir):
        """Test that frames are in BGR format (OpenCV default)."""
        video_path = temp_video_dir / "test.mp4"
        create_test_video(video_path, frame_count=3)

        extractor = FrameExtractor(str(video_path))
        frames = extractor.extract_all()

        # All frames should be BGR uint8
        for frame in frames:
            assert frame.image.dtype == np.uint8
            assert len(frame.image.shape) == 3
            assert frame.image.shape[2] == 3  # 3 channels

    def test_frame_extractor_missing_file(self):
        """Test that FileNotFoundError is raised for missing video."""
        with pytest.raises(FileNotFoundError):
            FrameExtractor("/nonexistent/path/video.mp4")

    def test_frame_extractor_init_validates_video(self, temp_video_dir):
        """Test that invalid video raises ValueError on initialization."""
        # Create a text file (not a video)
        fake_video = temp_video_dir / "fake.mp4"
        fake_video.write_text("not a video")

        with pytest.raises(ValueError, match="Failed to open video"):
            FrameExtractor(str(fake_video))

    def test_frame_extractor_frame_dimensions(self, temp_video_dir):
        """Test that frame dimensions match video metadata."""
        video_path = temp_video_dir / "test.mp4"
        width, height = 1024, 768
        create_test_video(video_path, width=width, height=height, frame_count=5)

        extractor = FrameExtractor(str(video_path))
        frames = extractor.extract_all()

        for frame in frames:
            assert frame.image.shape[0] == height
            assert frame.image.shape[1] == width
            assert frame.image.shape[2] == 3

    def test_frame_extractor_frame_id_sequence(self, temp_video_dir):
        """Test that frame IDs are sequential starting from 0."""
        video_path = temp_video_dir / "test.mp4"
        create_test_video(video_path, frame_count=20)

        extractor = FrameExtractor(str(video_path))
        frames = extractor.extract_all()

        frame_ids = [f.frame_id for f in frames]
        expected_ids = list(range(len(frames)))
        assert frame_ids == expected_ids
