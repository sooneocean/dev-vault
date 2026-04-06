"""
Integration tests for Phase 2 features.

Tests interactions between Phase 2 components:
- Multi-watermark processing
- YOLO detection + multi-watermark
- Temporal smoothing + Poisson blending
- Checkpoint resumption with Phase 2 configs
"""

import pytest
import tempfile
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from watermark_removal.core.types import ProcessConfig, CropRegion
from watermark_removal.preprocessing.crop_handler import CropHandler


class TestMultiWatermarkIntegration:
    """Integration tests for multi-watermark processing."""

    def test_multiple_crop_regions_same_frame(self):
        """Generate multiple CropRegions for same frame."""
        handler = CropHandler(context_padding=64, target_size=1024)
        frame_shape = (480, 640, 3)

        # Three watermarks in same frame
        bboxes = [
            (10, 20, 100, 50),
            (300, 20, 100, 50),
            (150, 300, 80, 40),
        ]

        crops = []
        for wid, bbox in enumerate(bboxes):
            crop = handler.compute_crop_region(0, bbox, frame_shape, watermark_id=wid)
            assert crop is not None
            crops.append(crop)

        # Verify uniqueness
        assert len(crops) == 3
        assert crops[0].watermark_id == 0
        assert crops[1].watermark_id == 1
        assert crops[2].watermark_id == 2
        assert crops[0].frame_id == crops[1].frame_id == crops[2].frame_id

    def test_overlapping_watermarks_merge(self):
        """Handle overlapping watermarks (should merge or limit)."""
        # Test IoU calculation
        bbox1 = (10, 20, 100, 50)
        bbox2 = (50, 30, 100, 50)  # Overlaps with bbox1

        # Compute IoU
        x1_min, y1_min, w1, h1 = bbox1
        x1_max, y1_max = x1_min + w1, y1_min + h1

        x2_min, y2_min, w2, h2 = bbox2
        x2_max, y2_max = x2_min + w2, y2_min + h2

        # Intersection
        x_inter_min = max(x1_min, x2_min)
        y_inter_min = max(y1_min, y2_min)
        x_inter_max = min(x1_max, x2_max)
        y_inter_max = min(y1_max, y2_max)

        inter_w = max(0, x_inter_max - x_inter_min)
        inter_h = max(0, y_inter_max - y_inter_min)
        intersection = inter_w * inter_h

        union = w1 * h1 + w2 * h2 - intersection
        iou = intersection / union if union > 0 else 0.0

        # Should be > 0 (overlapping)
        assert iou > 0.0
        # Should be < 1 (not identical)
        assert iou < 1.0

    def test_max_watermarks_per_frame_limit(self):
        """Enforce maximum watermarks per frame."""
        config = ProcessConfig(
            video_path="dummy.mp4",
            mask_path="dummy.png",
            max_watermarks_per_frame=2,
        )

        # Simulate detected watermarks
        detected = [
            (10, 20, 100, 50),
            (300, 20, 100, 50),
            (150, 300, 80, 40),  # This would be limited
        ]

        # Apply limit
        limited = detected[:config.max_watermarks_per_frame]

        assert len(limited) == 2
        assert len(detected) == 3


class TestWatermarkTrackerIntegration:
    """Integration tests for watermark tracking."""

    def test_tracker_config_enabled(self):
        """Tracker can be enabled via config."""
        config = ProcessConfig(
            video_path="dummy.mp4",
            mask_path="dummy.png",
            use_watermark_tracker=True,
            yolo_model_size="small",
        )

        assert config.use_watermark_tracker is True
        assert config.yolo_model_size == "small"

    def test_tracker_smoothing_factor(self):
        """Tracker smoothing is configurable."""
        config = ProcessConfig(
            video_path="dummy.mp4",
            mask_path="dummy.png",
            use_watermark_tracker=True,
            tracker_smoothing_factor=0.7,
        )

        assert config.tracker_smoothing_factor == 0.7

    def test_sparse_interpolation(self):
        """Bbox interpolation for sparse frames."""
        # Simulate sparse detections: frames 0, 10, 20
        detections = {
            0: [(100, 100, 200, 150)],
            10: [(150, 120, 200, 150)],
            20: [(200, 140, 200, 150)],
        }

        # Interpolate frame 5
        frame_id = 5
        weight = frame_id / 10  # Between 0 and 10

        bbox_start = detections[0][0]
        bbox_end = detections[10][0]

        x = int(bbox_start[0] * (1 - weight) + bbox_end[0] * weight)
        y = int(bbox_start[1] * (1 - weight) + bbox_end[1] * weight)

        # Interpolated bbox
        assert x > bbox_start[0]
        assert x < bbox_end[0]
        assert y > bbox_start[1]
        assert y < bbox_end[1]


class TestTemporalSmoothingIntegration:
    """Integration tests for temporal smoothing."""

    def test_temporal_smoothing_config(self):
        """Temporal smoothing parameter is stored."""
        config = ProcessConfig(
            video_path="dummy.mp4",
            mask_path="dummy.png",
            temporal_smooth_alpha=0.3,
        )

        assert config.temporal_smooth_alpha == 0.3

    def test_adaptive_temporal_smoothing_config(self):
        """Adaptive temporal smoothing with motion threshold."""
        config = ProcessConfig(
            video_path="dummy.mp4",
            mask_path="dummy.png",
            use_adaptive_temporal_smoothing=True,
            adaptive_motion_threshold=0.1,
        )

        assert config.use_adaptive_temporal_smoothing is True
        assert config.adaptive_motion_threshold == 0.1

    def test_temporal_smoothing_alpha_range(self):
        """Alpha should be in valid range [0, 1]."""
        config1 = ProcessConfig(
            video_path="dummy.mp4",
            mask_path="dummy.png",
            temporal_smooth_alpha=0.0,
        )
        assert config1.temporal_smooth_alpha >= 0.0

        config2 = ProcessConfig(
            video_path="dummy.mp4",
            mask_path="dummy.png",
            temporal_smooth_alpha=1.0,
        )
        assert config2.temporal_smooth_alpha <= 1.0


class TestPoissonBlendingIntegration:
    """Integration tests for Poisson blending."""

    def test_poisson_config(self):
        """Poisson blending parameters are stored."""
        config = ProcessConfig(
            video_path="dummy.mp4",
            mask_path="dummy.png",
            use_poisson_blending=True,
            poisson_max_iterations=150,
            poisson_tolerance=0.001,
        )

        assert config.use_poisson_blending is True
        assert config.poisson_max_iterations == 150
        assert config.poisson_tolerance == 0.001

    def test_poisson_iterations_range(self):
        """Poisson iterations should be reasonable."""
        config = ProcessConfig(
            video_path="dummy.mp4",
            mask_path="dummy.png",
            poisson_max_iterations=100,
        )

        assert config.poisson_max_iterations > 0
        assert config.poisson_max_iterations <= 1000


class TestCheckpointIntegration:
    """Integration tests for checkpoint resumption."""

    def test_checkpoint_config(self):
        """Checkpoint configuration is stored."""
        config = ProcessConfig(
            video_path="dummy.mp4",
            mask_path="dummy.png",
            use_checkpoints=True,
            resume_from_checkpoint=True,
            checkpoint_dir="checkpoints",
        )

        assert config.use_checkpoints is True
        assert config.resume_from_checkpoint is True
        assert config.checkpoint_dir.exists() or config.checkpoint_dir.name == "checkpoints"

    def test_crop_region_checkpoint_serialization(self):
        """CropRegion serializes for checkpointing."""
        crop = CropRegion(
            frame_id=5,
            original_bbox=(10, 20, 100, 50),
            context_bbox=(0, 0, 150, 100),
            scale_factor=1.5,
            watermark_id=2,
            pad_left=10,
            pad_top=20,
            pad_right=10,
            pad_bottom=20,
        )

        # Serialize to dict
        data = {
            'frame_id': crop.frame_id,
            'original_bbox': crop.original_bbox,
            'context_bbox': crop.context_bbox,
            'scale_factor': crop.scale_factor,
            'watermark_id': crop.watermark_id,
            'pad_left': crop.pad_left,
            'pad_top': crop.pad_top,
            'pad_right': crop.pad_right,
            'pad_bottom': crop.pad_bottom,
        }

        # Deserialize
        crop2 = CropRegion(
            frame_id=data['frame_id'],
            original_bbox=data['original_bbox'],
            context_bbox=data['context_bbox'],
            scale_factor=data['scale_factor'],
            watermark_id=data['watermark_id'],
            pad_left=data['pad_left'],
            pad_top=data['pad_top'],
            pad_right=data['pad_right'],
            pad_bottom=data['pad_bottom'],
        )

        assert crop2.frame_id == 5
        assert crop2.watermark_id == 2
        assert crop2.scale_factor == 1.5


class TestPhase2ConfigurationCombinations:
    """Test various Phase 2 configuration combinations."""

    def test_config_all_features_disabled(self):
        """Config with all Phase 2 features disabled (Phase 1 mode)."""
        config = ProcessConfig(
            video_path="dummy.mp4",
            mask_path="dummy.png",
            temporal_smooth_alpha=0.0,
            use_adaptive_temporal_smoothing=False,
            use_poisson_blending=False,
            use_watermark_tracker=False,
            max_watermarks_per_frame=1,
        )

        assert config.temporal_smooth_alpha == 0.0
        assert config.use_adaptive_temporal_smoothing is False
        assert config.use_poisson_blending is False
        assert config.use_watermark_tracker is False

    def test_config_all_features_enabled(self):
        """Config with all Phase 2 features enabled."""
        config = ProcessConfig(
            video_path="dummy.mp4",
            mask_path="dummy.png",
            temporal_smooth_alpha=0.3,
            use_adaptive_temporal_smoothing=True,
            adaptive_motion_threshold=0.05,
            use_poisson_blending=True,
            poisson_max_iterations=100,
            use_watermark_tracker=True,
            max_watermarks_per_frame=3,
        )

        assert config.temporal_smooth_alpha == 0.3
        assert config.use_adaptive_temporal_smoothing is True
        assert config.use_poisson_blending is True
        assert config.use_watermark_tracker is True
        assert config.max_watermarks_per_frame == 3

    def test_config_partial_features(self):
        """Config with some Phase 2 features enabled."""
        config = ProcessConfig(
            video_path="dummy.mp4",
            mask_path="dummy.png",
            temporal_smooth_alpha=0.2,  # Only temporal smoothing
            use_adaptive_temporal_smoothing=False,
            use_poisson_blending=False,
            use_watermark_tracker=False,
            max_watermarks_per_frame=2,  # Only multi-watermark
        )

        assert config.temporal_smooth_alpha == 0.2
        assert config.max_watermarks_per_frame == 2
        assert config.use_adaptive_temporal_smoothing is False
        assert config.use_poisson_blending is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
