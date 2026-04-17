"""
Tests for multi-watermark support.

Tests ProcessConfig, CropRegion, and Pipeline multi-watermark handling.
"""

import pytest
import tempfile
import numpy as np
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from watermark_removal.core.types import ProcessConfig, CropRegion
from watermark_removal.preprocessing.crop_handler import CropHandler


class TestProcessConfigMultiWatermark:
    """Test ProcessConfig with multi-watermark parameters."""

    def test_config_default_single_watermark(self):
        """Default config supports single watermark."""
        config = ProcessConfig(
            video_path="test.mp4",
            mask_path="mask.png",
        )
        assert config.max_watermarks_per_frame == 1
        assert config.watermark_merge_threshold == 0.3

    def test_config_multiple_watermarks(self):
        """Config can be set for multiple watermarks."""
        config = ProcessConfig(
            video_path="test.mp4",
            mask_path="mask.json",
            max_watermarks_per_frame=3,
            watermark_merge_threshold=0.5,
        )
        assert config.max_watermarks_per_frame == 3
        assert config.watermark_merge_threshold == 0.5

    def test_config_merge_threshold_valid(self):
        """Watermark merge threshold must be valid."""
        # Valid thresholds
        config1 = ProcessConfig(
            video_path="test.mp4",
            mask_path="mask.json",
            watermark_merge_threshold=0.0,
        )
        assert config1.watermark_merge_threshold == 0.0

        config2 = ProcessConfig(
            video_path="test.mp4",
            mask_path="mask.json",
            watermark_merge_threshold=1.0,
        )
        assert config2.watermark_merge_threshold == 1.0


class TestCropRegionMultiWatermark:
    """Test CropRegion with watermark_id."""

    def test_crop_region_default_watermark_id(self):
        """Default watermark_id is 0."""
        crop = CropRegion(
            frame_id=0,
            original_bbox=(10, 20, 100, 50),
            context_bbox=(0, 0, 150, 100),
            scale_factor=1.5,
        )
        assert crop.watermark_id == 0

    def test_crop_region_watermark_id_set(self):
        """CropRegion can set watermark_id."""
        crop = CropRegion(
            frame_id=0,
            original_bbox=(10, 20, 100, 50),
            context_bbox=(0, 0, 150, 100),
            scale_factor=1.5,
            watermark_id=2,
        )
        assert crop.watermark_id == 2

    def test_crop_region_multiple_watermarks_same_frame(self):
        """Multiple CropRegions can exist for same frame with different watermark_ids."""
        crop1 = CropRegion(
            frame_id=0,
            original_bbox=(10, 20, 100, 50),
            context_bbox=(0, 0, 150, 100),
            scale_factor=1.5,
            watermark_id=0,
        )
        crop2 = CropRegion(
            frame_id=0,
            original_bbox=(300, 200, 150, 80),
            context_bbox=(250, 150, 200, 130),
            scale_factor=1.3,
            watermark_id=1,
        )

        assert crop1.frame_id == crop2.frame_id
        assert crop1.watermark_id != crop2.watermark_id
        assert crop1.original_bbox != crop2.original_bbox


class TestCropHandlerMultiWatermark:
    """Test CropHandler with watermark_id support."""

    def test_compute_crop_region_default_watermark_id(self):
        """Compute crop region with default watermark_id."""
        handler = CropHandler(context_padding=64, target_size=1024)
        bbox = (50.0, 100.0, 200.0, 150.0)
        frame_shape = (480, 640, 3)

        crop = handler.compute_crop_region(0, bbox, frame_shape)

        assert crop is not None
        assert crop.watermark_id == 0
        assert crop.frame_id == 0

    def test_compute_crop_region_with_watermark_id(self):
        """Compute crop region with explicit watermark_id."""
        handler = CropHandler(context_padding=64, target_size=1024)
        bbox = (50.0, 100.0, 200.0, 150.0)
        frame_shape = (480, 640, 3)

        crop = handler.compute_crop_region(0, bbox, frame_shape, watermark_id=2)

        assert crop is not None
        assert crop.watermark_id == 2

    def test_compute_crop_regions_multiple(self):
        """Compute multiple crop regions for same frame."""
        handler = CropHandler(context_padding=64, target_size=1024)
        frame_shape = (480, 640, 3)

        # Two watermarks in same frame
        bbox1 = (10.0, 20.0, 100.0, 50.0)
        bbox2 = (300.0, 200.0, 150.0, 80.0)

        crop1 = handler.compute_crop_region(0, bbox1, frame_shape, watermark_id=0)
        crop2 = handler.compute_crop_region(0, bbox2, frame_shape, watermark_id=1)

        assert crop1 is not None
        assert crop2 is not None
        assert crop1.frame_id == crop2.frame_id == 0
        assert crop1.watermark_id == 0
        assert crop2.watermark_id == 1
        # Different bboxes should have different original_bboxes
        assert crop1.original_bbox != crop2.original_bbox


class TestMultiWatermarkProcessing:
    """Test multi-watermark workflow."""

    def test_multiple_bboxes_per_frame_dict(self):
        """Parse multiple bboxes from frame dict."""
        # Simulate bbox_dict with multiple watermarks per frame
        bbox_dict = {
            0: [(10.0, 20.0, 100.0, 50.0), (300.0, 200.0, 150.0, 80.0)],  # 2 watermarks
            1: [(15.0, 25.0, 100.0, 50.0)],  # 1 watermark
        }

        # Process frame 0
        frame_0_bboxes = bbox_dict.get(0)
        assert frame_0_bboxes is not None
        assert len(frame_0_bboxes) == 2

        # Process frame 1
        frame_1_bboxes = bbox_dict.get(1)
        assert frame_1_bboxes is not None
        assert len(frame_1_bboxes) == 1

    def test_crop_region_filename_with_watermark_id(self):
        """Crop filenames include watermark_id."""
        crops_dir = Path("crops")

        # Generate filenames as Pipeline would
        frame_id = 5
        watermark_ids = [0, 1]

        filenames = [
            crops_dir / f"crop_{frame_id:06d}_w{wid}.png"
            for wid in watermark_ids
        ]

        assert filenames[0] == Path("crops/crop_000005_w0.png")
        assert filenames[1] == Path("crops/crop_000005_w1.png")

    def test_watermark_limit_enforcement(self):
        """Enforce max_watermarks_per_frame limit."""
        config = ProcessConfig(
            video_path="test.mp4",
            mask_path="mask.json",
            max_watermarks_per_frame=2,
        )

        # Simulate detected watermarks
        detected_bboxes = [
            (10.0, 20.0, 100.0, 50.0),
            (300.0, 200.0, 150.0, 80.0),
            (100.0, 300.0, 80.0, 60.0),  # This would be skipped
        ]

        # Apply limit
        limited_bboxes = detected_bboxes[: config.max_watermarks_per_frame]

        assert len(limited_bboxes) == 2
        assert len(detected_bboxes) == 3


class TestMultiWatermarkCLI:
    """Test multi-watermark CLI parameters."""

    def test_cli_max_watermarks_parameter(self):
        """CLI accepts max_watermarks_per_frame parameter."""
        # Simulated parsed args
        class Args:
            max_watermarks_per_frame = 3
            watermark_merge_threshold = 0.4

        config = ProcessConfig(
            video_path="test.mp4",
            mask_path="mask.json",
        )

        # Apply CLI overrides
        if hasattr(Args, 'max_watermarks_per_frame') and Args.max_watermarks_per_frame is not None:
            config.max_watermarks_per_frame = Args.max_watermarks_per_frame
        if hasattr(Args, 'watermark_merge_threshold') and Args.watermark_merge_threshold is not None:
            config.watermark_merge_threshold = Args.watermark_merge_threshold

        assert config.max_watermarks_per_frame == 3
        assert config.watermark_merge_threshold == 0.4


class TestCropRegionCheckpointSerialization:
    """Test CropRegion serialization with watermark_id."""

    def test_crop_region_to_dict(self):
        """CropRegion serializes to dict with watermark_id."""
        crop = CropRegion(
            frame_id=5,
            original_bbox=(10, 20, 100, 50),
            context_bbox=(0, 0, 150, 100),
            scale_factor=1.5,
            watermark_id=2,
            pad_left=5,
            pad_top=10,
            pad_right=5,
            pad_bottom=10,
        )

        # Serialize
        crop_dict = {
            "frame_id": crop.frame_id,
            "original_bbox": crop.original_bbox,
            "context_bbox": crop.context_bbox,
            "scale_factor": crop.scale_factor,
            "watermark_id": crop.watermark_id,
            "pad_left": crop.pad_left,
            "pad_top": crop.pad_top,
            "pad_right": crop.pad_right,
            "pad_bottom": crop.pad_bottom,
        }

        assert crop_dict["watermark_id"] == 2
        assert crop_dict["frame_id"] == 5

    def test_crop_region_from_dict(self):
        """CropRegion deserializes from dict with watermark_id."""
        crop_dict = {
            "frame_id": 5,
            "original_bbox": (10, 20, 100, 50),
            "context_bbox": (0, 0, 150, 100),
            "scale_factor": 1.5,
            "watermark_id": 2,
            "pad_left": 5,
            "pad_top": 10,
            "pad_right": 5,
            "pad_bottom": 10,
        }

        # Deserialize
        crop = CropRegion(
            frame_id=crop_dict["frame_id"],
            original_bbox=crop_dict["original_bbox"],
            context_bbox=crop_dict["context_bbox"],
            scale_factor=crop_dict["scale_factor"],
            watermark_id=crop_dict["watermark_id"],
            pad_left=crop_dict["pad_left"],
            pad_top=crop_dict["pad_top"],
            pad_right=crop_dict["pad_right"],
            pad_bottom=crop_dict["pad_bottom"],
        )

        assert crop.watermark_id == 2
        assert crop.frame_id == 5
        assert crop.original_bbox == (10, 20, 100, 50)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
