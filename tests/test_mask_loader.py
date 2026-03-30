"""Tests for mask loading."""

import json
import tempfile
from pathlib import Path

import cv2
import numpy as np
import pytest

from src.watermark_removal.core.types import Frame, Mask, MaskType
from src.watermark_removal.preprocessing.mask_loader import MaskLoader


@pytest.fixture
def temp_mask_dir():
    """Create temporary directory for test masks."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def create_test_image_mask(mask_path: Path, width: int = 100, height: int = 100) -> None:
    """Create a test image mask (grayscale PNG).

    Args:
        mask_path: Path to save mask image.
        width: Image width.
        height: Image height.
    """
    # Create simple mask: white circle in center
    mask = np.zeros((height, width), dtype=np.uint8)
    center = (width // 2, height // 2)
    radius = 30
    cv2.circle(mask, center, radius, 255, -1)

    cv2.imwrite(str(mask_path), mask)


def create_test_bbox_mask(mask_path: Path, frames: dict) -> None:
    """Create a test bbox mask (JSON).

    Args:
        mask_path: Path to save bbox JSON.
        frames: Dict mapping frame_id (int) to bbox dict {"x": int, "y": int, "w": int, "h": int}.
    """
    # Convert int keys to strings for JSON
    json_data = {str(frame_id): bbox for frame_id, bbox in frames.items()}

    with open(mask_path, "w") as f:
        json.dump(json_data, f)


class TestMaskLoaderImage:
    """Tests for IMAGE mask loading."""

    def test_mask_loader_image_creation(self, temp_mask_dir):
        """Test creating mask loader with image mask."""
        mask_path = temp_mask_dir / "mask.png"
        create_test_image_mask(mask_path)

        loader = MaskLoader(str(mask_path))

        assert loader.mask_type == MaskType.IMAGE
        assert loader.mask_path == mask_path

    def test_mask_loader_image_loading(self, temp_mask_dir):
        """Test loading image mask for frame."""
        mask_path = temp_mask_dir / "mask.png"
        create_test_image_mask(mask_path, width=100, height=100)

        loader = MaskLoader(str(mask_path))
        frame = Frame(frame_id=0, image=np.zeros((480, 640, 3), dtype=np.uint8), timestamp_ms=0.0)
        mask = loader.load_for_frame(frame)

        assert mask is not None
        assert isinstance(mask, Mask)
        assert mask.type == MaskType.IMAGE
        assert isinstance(mask.data, np.ndarray)
        assert mask.data.shape == (100, 100)
        assert mask.valid_frame_range == (0, float("inf"))

    def test_mask_loader_image_caching(self, temp_mask_dir):
        """Test that image masks are cached (loaded once)."""
        mask_path = temp_mask_dir / "mask.png"
        create_test_image_mask(mask_path)

        loader = MaskLoader(str(mask_path))
        frame0 = Frame(frame_id=0, image=np.zeros((480, 640, 3), dtype=np.uint8), timestamp_ms=0.0)
        frame1 = Frame(frame_id=1, image=np.zeros((480, 640, 3), dtype=np.uint8), timestamp_ms=33.33)

        mask0 = loader.load_for_frame(frame0)
        mask1 = loader.load_for_frame(frame1)

        # Both masks should reference the same cached data
        assert mask0.data is mask1.data

    def test_mask_loader_image_all_frames(self, temp_mask_dir):
        """Test that image mask applies to all frames."""
        mask_path = temp_mask_dir / "mask.png"
        create_test_image_mask(mask_path)

        loader = MaskLoader(str(mask_path))

        for frame_id in [0, 10, 100, 1000]:
            frame = Frame(
                frame_id=frame_id,
                image=np.zeros((480, 640, 3), dtype=np.uint8),
                timestamp_ms=frame_id * 33.33,
            )
            mask = loader.load_for_frame(frame)

            assert mask is not None
            assert mask.type == MaskType.IMAGE
            assert mask.valid_frame_range == (0, float("inf"))


class TestMaskLoaderBBox:
    """Tests for BBOX mask loading."""

    def test_mask_loader_bbox_creation(self, temp_mask_dir):
        """Test creating mask loader with bbox JSON."""
        mask_path = temp_mask_dir / "bboxes.json"
        create_test_bbox_mask(mask_path, {0: {"x": 100, "y": 100, "w": 50, "h": 50}})

        loader = MaskLoader(str(mask_path))

        assert loader.mask_type == MaskType.BBOX
        assert loader.mask_path == mask_path

    def test_mask_loader_bbox_loading(self, temp_mask_dir):
        """Test loading bbox mask for frame."""
        mask_path = temp_mask_dir / "bboxes.json"
        create_test_bbox_mask(
            mask_path,
            {0: {"x": 100, "y": 200, "w": 50, "h": 50}},
        )

        loader = MaskLoader(str(mask_path))
        frame = Frame(frame_id=0, image=np.zeros((480, 640, 3), dtype=np.uint8), timestamp_ms=0.0)
        mask = loader.load_for_frame(frame)

        assert mask is not None
        assert isinstance(mask, Mask)
        assert mask.type == MaskType.BBOX
        assert mask.data == {"x": 100, "y": 200, "w": 50, "h": 50}
        assert mask.valid_frame_range == (0, 0)

    def test_mask_loader_bbox_missing_frame(self, temp_mask_dir):
        """Test that missing frames return None."""
        mask_path = temp_mask_dir / "bboxes.json"
        create_test_bbox_mask(
            mask_path,
            {0: {"x": 100, "y": 100, "w": 50, "h": 50}},
        )

        loader = MaskLoader(str(mask_path))
        frame = Frame(frame_id=5, image=np.zeros((480, 640, 3), dtype=np.uint8), timestamp_ms=166.67)
        mask = loader.load_for_frame(frame)

        assert mask is None

    def test_mask_loader_bbox_sparse_frames(self, temp_mask_dir):
        """Test that sparse frame IDs are handled correctly."""
        mask_path = temp_mask_dir / "bboxes.json"
        create_test_bbox_mask(
            mask_path,
            {
                0: {"x": 100, "y": 200, "w": 50, "h": 50},
                5: {"x": 105, "y": 205, "w": 50, "h": 50},
                10: {"x": 110, "y": 210, "w": 50, "h": 50},
            },
        )

        loader = MaskLoader(str(mask_path))

        # Frames with bboxes
        mask0 = loader.load_for_frame(Frame(0, np.zeros((480, 640, 3), dtype=np.uint8), 0.0))
        mask5 = loader.load_for_frame(Frame(5, np.zeros((480, 640, 3), dtype=np.uint8), 166.67))
        mask10 = loader.load_for_frame(Frame(10, np.zeros((480, 640, 3), dtype=np.uint8), 333.33))

        assert mask0 is not None
        assert mask0.data["x"] == 100
        assert mask5 is not None
        assert mask5.data["x"] == 105
        assert mask10 is not None
        assert mask10.data["x"] == 110

        # Frames without bboxes
        mask1 = loader.load_for_frame(Frame(1, np.zeros((480, 640, 3), dtype=np.uint8), 33.33))
        mask2 = loader.load_for_frame(Frame(2, np.zeros((480, 640, 3), dtype=np.uint8), 66.67))

        assert mask1 is None
        assert mask2 is None

    def test_mask_loader_bbox_caching(self, temp_mask_dir):
        """Test that bbox data is cached."""
        mask_path = temp_mask_dir / "bboxes.json"
        create_test_bbox_mask(
            mask_path,
            {0: {"x": 100, "y": 100, "w": 50, "h": 50}},
        )

        loader = MaskLoader(str(mask_path))
        frame0 = Frame(0, np.zeros((480, 640, 3), dtype=np.uint8), 0.0)
        frame1 = Frame(1, np.zeros((480, 640, 3), dtype=np.uint8), 33.33)

        loader.load_for_frame(frame0)
        loader.load_for_frame(frame1)

        # Both calls should use same cached JSON data
        assert loader._cached_bbox_data is not None


class TestMaskLoaderErrors:
    """Tests for error handling."""

    def test_mask_loader_file_not_found(self):
        """Test FileNotFoundError for missing mask file."""
        with pytest.raises(FileNotFoundError):
            MaskLoader("/nonexistent/mask.json")

    def test_mask_loader_unsupported_format(self, temp_mask_dir):
        """Test ValueError for unsupported mask format."""
        mask_path = temp_mask_dir / "mask.txt"
        mask_path.write_text("unsupported")

        with pytest.raises(ValueError, match="Unsupported mask file format"):
            MaskLoader(str(mask_path))

    def test_mask_loader_corrupted_image(self, temp_mask_dir):
        """Test error when image mask is corrupted."""
        mask_path = temp_mask_dir / "corrupt.png"
        mask_path.write_text("not an image")

        loader = MaskLoader(str(mask_path))
        frame = Frame(0, np.zeros((480, 640, 3), dtype=np.uint8), 0.0)

        with pytest.raises(ValueError, match="Failed to read image mask"):
            loader.load_for_frame(frame)

    def test_mask_loader_invalid_json(self, temp_mask_dir):
        """Test error when bbox JSON is invalid."""
        mask_path = temp_mask_dir / "invalid.json"
        mask_path.write_text("{ invalid json }")

        loader = MaskLoader(str(mask_path))
        frame = Frame(0, np.zeros((480, 640, 3), dtype=np.uint8), 0.0)

        with pytest.raises(json.JSONDecodeError):
            loader.load_for_frame(frame)


class TestMaskLoaderIntegration:
    """Integration tests."""

    def test_mask_loader_supports_jpg(self, temp_mask_dir):
        """Test that JPG format is supported."""
        mask_path = temp_mask_dir / "mask.jpg"
        create_test_image_mask(mask_path)

        loader = MaskLoader(str(mask_path))

        assert loader.mask_type == MaskType.IMAGE

    def test_mask_loader_supports_jpeg(self, temp_mask_dir):
        """Test that JPEG format is supported."""
        mask_path = temp_mask_dir / "mask.jpeg"
        create_test_image_mask(mask_path)

        loader = MaskLoader(str(mask_path))

        assert loader.mask_type == MaskType.IMAGE
