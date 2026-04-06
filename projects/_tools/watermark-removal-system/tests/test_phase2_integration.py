"""
Integration tests for Phase 2 features (temporal smoothing, Poisson blending, checkpointing, tracking).

Tests the integration of Phase 2 components into the main Pipeline.
"""

import pytest
import tempfile
import numpy as np
from pathlib import Path

from src.watermark_removal.core.pipeline import Pipeline
from src.watermark_removal.core.types import ProcessConfig, CropRegion
from src.watermark_removal.postprocessing.temporal_smoother import TemporalSmoother
from src.watermark_removal.postprocessing.adaptive_temporal_smoother import AdaptiveTemporalSmoother
from src.watermark_removal.postprocessing.poisson_blender import PoissonBlender
from src.watermark_removal.preprocessing.watermark_tracker import BboxTracker
from src.watermark_removal.core.checkpoint import CheckpointManager


class TestTemporalSmoothing:
    """Test temporal smoothing functionality."""

    def test_temporal_smoother_init(self):
        """Initialize temporal smoother with default and custom alpha."""
        smoother = TemporalSmoother()
        assert smoother.alpha == 0.3

        smoother_custom = TemporalSmoother(alpha=0.5)
        assert smoother_custom.alpha == 0.5

    def test_adaptive_temporal_smoother_init(self):
        """Initialize adaptive temporal smoother."""
        smoother = AdaptiveTemporalSmoother()
        assert smoother.base_alpha == 0.3
        assert smoother.motion_threshold == 0.05
        assert smoother.min_alpha == 0.0
        assert smoother.max_alpha == 0.8

    def test_adaptive_smoother_motion_estimation(self):
        """Estimate motion between two frames."""
        smoother = AdaptiveTemporalSmoother()

        # Static frames: no motion
        frame1 = np.ones((100, 100, 3), dtype=np.uint8) * 128
        frame2 = np.ones((100, 100, 3), dtype=np.uint8) * 128

        motion = smoother.estimate_motion(frame1, frame2)
        assert motion == pytest.approx(0.0, abs=0.01)

        # High-motion frames
        frame1 = np.zeros((100, 100, 3), dtype=np.uint8)
        frame2 = np.ones((100, 100, 3), dtype=np.uint8) * 255

        motion = smoother.estimate_motion(frame1, frame2)
        assert motion > 0.9  # Should be very high

    def test_adaptive_smoother_alpha_adaptation(self):
        """Adapt alpha based on motion magnitude."""
        smoother = AdaptiveTemporalSmoother(
            base_alpha=0.3,
            motion_threshold=0.05,
            min_alpha=0.1,
            max_alpha=0.5,
        )

        # Low motion: should increase alpha
        alpha_low = smoother.adapt_alpha(motion=0.0)
        assert alpha_low > smoother.base_alpha

        # High motion: should decrease alpha
        alpha_high = smoother.adapt_alpha(motion=1.0)
        assert alpha_high < smoother.base_alpha

        # At threshold: should be base_alpha
        alpha_threshold = smoother.adapt_alpha(motion=0.05)
        assert alpha_threshold == pytest.approx(smoother.base_alpha, abs=0.01)

    def test_adaptive_smoother_smooth_frame(self):
        """Smooth frame with adaptive alpha."""
        smoother = AdaptiveTemporalSmoother()

        current = np.ones((50, 50, 3), dtype=np.uint8) * 100
        previous = np.ones((50, 50, 3), dtype=np.uint8) * 200

        # Provide motion estimate
        result = smoother.smooth_frame(current, previous, motion=0.0)

        # Should be closer to current than static temporal smoother
        assert result.dtype == np.uint8
        assert result.shape == (50, 50, 3)

    def test_adaptive_smoother_smooth_sequence(self):
        """Smooth frame sequence with adaptive alpha."""
        smoother = AdaptiveTemporalSmoother()

        frames = [
            np.ones((50, 50, 3), dtype=np.uint8) * i * 50
            for i in range(5)
        ]

        smoothed, motions = smoother.smooth_sequence(frames)

        assert len(smoothed) == 5
        assert len(motions) == 5
        # First motion should be 0.0
        assert motions[0] == 0.0
        # Other motions should be estimated
        assert all(0.0 <= m <= 1.0 for m in motions[1:])

    def test_temporal_smoother_invalid_alpha(self):
        """Temporal smoother rejects invalid alpha values."""
        with pytest.raises(ValueError):
            TemporalSmoother(alpha=-0.1)

        with pytest.raises(ValueError):
            TemporalSmoother(alpha=1.5)

    def test_smooth_frame_no_previous(self):
        """Smooth frame returns current frame when no previous frame."""
        smoother = TemporalSmoother(alpha=0.3)
        current = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)

        result = smoother.smooth_frame(current, None)
        np.testing.assert_array_equal(result, current)

    def test_smooth_frame_with_previous(self):
        """Smooth frame blends with previous frame."""
        smoother = TemporalSmoother(alpha=0.3)
        current = np.ones((100, 100, 3), dtype=np.uint8) * 100
        previous = np.ones((100, 100, 3), dtype=np.uint8) * 200

        result = smoother.smooth_frame(current, previous)

        # Expected: (1 - 0.3) * 100 + 0.3 * 200 = 70 + 60 = 130
        expected = np.ones((100, 100, 3), dtype=np.uint8) * 130
        np.testing.assert_array_almost_equal(result, expected, decimal=0)

    def test_smooth_sequence(self):
        """Smooth entire frame sequence with consecutive blending."""
        smoother = TemporalSmoother(alpha=0.3)

        # Create sequence of 3 frames
        frame1 = np.ones((50, 50, 3), dtype=np.uint8) * 100
        frame2 = np.ones((50, 50, 3), dtype=np.uint8) * 150
        frame3 = np.ones((50, 50, 3), dtype=np.uint8) * 200

        frames = [frame1, frame2, frame3]
        result = smoother.smooth_sequence(frames)

        assert len(result) == 3
        # First frame should be unchanged
        np.testing.assert_array_equal(result[0], frame1)
        # Second frame should be blended (between 100 and 150)
        assert np.all(result[1] < frame2)  # Lower than 150
        assert np.all(result[1] > frame1)  # Higher than 100


class TestPoissonBlending:
    """Test Poisson blending functionality."""

    def test_poisson_blender_init(self):
        """Initialize Poisson blender."""
        blender = PoissonBlender()
        assert blender.max_iterations == 100
        assert blender.tolerance == 0.01

    def test_poisson_blend_simple(self):
        """Blend two simple images."""
        blender = PoissonBlender(max_iterations=10)

        # Create target and source images
        target = np.ones((100, 100, 3), dtype=np.uint8) * 100
        source = np.ones((100, 100, 3), dtype=np.uint8) * 200

        # Create binary mask (255 = source region)
        mask = np.zeros((100, 100), dtype=np.uint8)
        mask[25:75, 25:75] = 255  # Center region from source

        result = blender.blend(target, source, mask, blend_width=32)

        # Result should be uint8 array
        assert result.dtype == np.uint8
        assert result.shape == (100, 100, 3)

    def test_poisson_blend_shape_mismatch(self):
        """Poisson blending handles shape mismatch gracefully."""
        blender = PoissonBlender()

        target = np.ones((100, 100, 3), dtype=np.uint8) * 100
        source = np.ones((80, 80, 3), dtype=np.uint8) * 200  # Wrong shape
        mask = np.zeros((100, 100), dtype=np.uint8)

        result = blender.blend(target, source, mask)

        # Should return target unchanged
        np.testing.assert_array_equal(result, target)


class TestBboxTracking:
    """Test bounding box tracking functionality."""

    def test_tracker_init(self):
        """Initialize bbox tracker."""
        tracker = BboxTracker(motion_smoothing_factor=0.3)
        assert tracker.motion_smoothing_factor == 0.3
        assert len(tracker.detections) == 0

    def test_tracker_invalid_factor(self):
        """Tracker rejects invalid smoothing factor."""
        with pytest.raises(ValueError):
            BboxTracker(motion_smoothing_factor=-0.1)

        with pytest.raises(ValueError):
            BboxTracker(motion_smoothing_factor=1.5)

    def test_add_detection(self):
        """Add bbox detection to tracker."""
        tracker = BboxTracker()

        tracker.add_detection(0, (10, 20, 100, 50), confidence=0.9)

        assert 0 in tracker.detections
        assert tracker.detections[0].bbox == (10, 20, 100, 50)
        assert tracker.detections[0].confidence == 0.9

    def test_add_invalid_confidence(self):
        """Tracker rejects invalid confidence."""
        tracker = BboxTracker()

        with pytest.raises(ValueError):
            tracker.add_detection(0, (10, 20, 100, 50), confidence=1.5)

    def test_interpolate_exact_match(self):
        """Interpolate returns exact bbox when detection exists."""
        tracker = BboxTracker()
        tracker.add_detection(0, (10, 20, 100, 50))

        result = tracker.interpolate(0)
        assert result == (10, 20, 100, 50)

    def test_interpolate_no_detections(self):
        """Interpolate returns None when no detections exist."""
        tracker = BboxTracker()
        result = tracker.interpolate(5)
        assert result is None

    def test_smooth_trajectory_complete(self):
        """Generate smooth trajectory for full frame range."""
        tracker = BboxTracker(motion_smoothing_factor=0.3)

        # Add sparse detections (frames 0, 10, 20)
        tracker.add_detection(0, (10, 10, 100, 100))
        tracker.add_detection(10, (50, 50, 100, 100))
        tracker.add_detection(20, (90, 90, 100, 100))

        # Generate trajectory for all frames
        frame_ids = list(range(21))
        trajectory = tracker.smooth_trajectory(frame_ids)

        assert len(trajectory.frame_ids) == 21
        assert len(trajectory.bboxes) == 21
        # First bbox should be exact (detected)
        assert trajectory.bboxes[0] == (10, 10, 100, 100)
        # Middle bbox should be interpolated
        assert trajectory.bboxes[5] != trajectory.bboxes[0]
        assert trajectory.bboxes[5] != trajectory.bboxes[10]

    def test_get_motion_vector(self):
        """Estimate motion vector between frames."""
        tracker = BboxTracker()

        tracker.add_detection(0, (10, 10, 100, 100))
        tracker.add_detection(5, (20, 20, 100, 100))

        motion = tracker.get_motion_vector(0, 5)

        assert motion is not None
        dx, dy = motion
        # Center should move from (60, 60) to (70, 70)
        assert dx > 0
        assert dy > 0

    def test_trajectory_confidence(self):
        """Estimate trajectory confidence based on detections."""
        tracker = BboxTracker()

        # No detections
        assert tracker.get_trajectory_confidence() == 0.0

        # Single detection
        tracker.add_detection(0, (10, 10, 100, 100), confidence=0.9)
        conf = tracker.get_trajectory_confidence()
        assert 0.4 < conf < 0.6  # Single detection confidence

        # Multiple detections
        tracker.add_detection(5, (20, 20, 100, 100), confidence=0.95)
        conf = tracker.get_trajectory_confidence()
        assert conf == pytest.approx((0.9 + 0.95) / 2, abs=0.01)  # Average confidence


class TestCheckpointing:
    """Test checkpoint save/load functionality."""

    def test_checkpoint_manager_init(self):
        """Initialize checkpoint manager."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CheckpointManager(Path(tmpdir))
            assert manager.checkpoint_dir.exists()

    def test_save_and_load_crop_regions(self):
        """Save and load crop regions from checkpoint."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CheckpointManager(Path(tmpdir))

            # Create sample crop regions
            crops = [
                CropRegion(
                    frame_id=0,
                    original_bbox=(10, 20, 100, 50),
                    context_bbox=(0, 0, 150, 100),
                    scale_factor=1.5,
                    pad_left=5,
                    pad_top=10,
                ),
                CropRegion(
                    frame_id=1,
                    original_bbox=(20, 30, 120, 60),
                    context_bbox=(10, 10, 160, 110),
                    scale_factor=1.5,
                    pad_left=5,
                    pad_top=10,
                ),
            ]

            # Save
            checkpoint_path = manager.save_crop_regions(
                "test_video",
                crops,
                {"test": "metadata"},
            )
            assert checkpoint_path.exists()

            # Load
            loaded_crops, state = manager.load_crop_regions("test_video")

            assert len(loaded_crops) == 2
            assert loaded_crops[0].frame_id == 0
            assert loaded_crops[1].frame_id == 1
            assert state["test"] == "metadata"

    def test_load_nonexistent_checkpoint(self):
        """Load nonexistent checkpoint returns empty results."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CheckpointManager(Path(tmpdir))

            crops, state = manager.load_crop_regions("nonexistent")

            assert crops == []
            assert state == {}

    def test_checkpoint_path_generation(self):
        """Checkpoint paths are generated correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CheckpointManager(Path(tmpdir))

            path = manager.get_checkpoint_path("my_video")

            assert path.name == "my_video_checkpoint.json"
            assert path.parent == manager.checkpoint_dir


class TestPhase2ConfigIntegration:
    """Test Phase 2 feature flags in ProcessConfig."""

    def test_config_temporal_smoothing_defaults(self):
        """ProcessConfig has temporal smoothing defaults."""
        config = ProcessConfig(
            video_path="input.mp4",
            mask_path="mask.png",
        )

        assert config.temporal_smooth_alpha == 0.0
        assert config.use_adaptive_temporal_smoothing is False
        assert config.adaptive_motion_threshold == 0.05

    def test_config_poisson_blending_defaults(self):
        """ProcessConfig has Poisson blending defaults."""
        config = ProcessConfig(
            video_path="input.mp4",
            mask_path="mask.png",
        )

        assert config.use_poisson_blending is False
        assert config.poisson_max_iterations == 100
        assert config.poisson_tolerance == 0.01

    def test_config_watermark_tracker_defaults(self):
        """ProcessConfig has watermark tracker defaults."""
        config = ProcessConfig(
            video_path="input.mp4",
            mask_path="mask.png",
        )

        assert config.use_watermark_tracker is False
        assert config.yolo_model_path is None
        assert config.yolo_confidence_threshold == 0.5
        assert config.tracker_smoothing_factor == 0.3

    def test_config_checkpoint_defaults(self):
        """ProcessConfig has checkpoint defaults."""
        config = ProcessConfig(
            video_path="input.mp4",
            mask_path="mask.png",
        )

        assert config.use_checkpoints is False
        assert config.resume_from_checkpoint is False

    def test_config_with_phase2_features_enabled(self):
        """Create config with Phase 2 features enabled."""
        config = ProcessConfig(
            video_path="input.mp4",
            mask_path="mask.png",
            temporal_smooth_alpha=0.3,
            use_poisson_blending=True,
            use_watermark_tracker=True,
            use_checkpoints=True,
        )

        assert config.temporal_smooth_alpha == 0.3
        assert config.use_poisson_blending is True
        assert config.use_watermark_tracker is True
        assert config.use_checkpoints is True


class TestPhase2PipelineIntegration:
    """Test Phase 2 feature integration with Pipeline class."""

    def test_pipeline_with_temporal_smoothing_config(self):
        """Pipeline accepts temporal smoothing configuration."""
        config = ProcessConfig(
            video_path="input.mp4",
            mask_path="mask.png",
            temporal_smooth_alpha=0.3,
        )
        pipeline = Pipeline(config)

        assert pipeline.config.temporal_smooth_alpha == 0.3

    def test_pipeline_with_poisson_blending_config(self):
        """Pipeline accepts Poisson blending configuration."""
        config = ProcessConfig(
            video_path="input.mp4",
            mask_path="mask.png",
            use_poisson_blending=True,
            poisson_max_iterations=50,
        )
        pipeline = Pipeline(config)

        assert pipeline.config.use_poisson_blending is True
        assert pipeline.config.poisson_max_iterations == 50

    def test_pipeline_with_checkpointing_config(self):
        """Pipeline accepts checkpointing configuration."""
        config = ProcessConfig(
            video_path="input.mp4",
            mask_path="mask.png",
            use_checkpoints=True,
            resume_from_checkpoint=True,
        )
        pipeline = Pipeline(config)

        assert pipeline.config.use_checkpoints is True
        assert pipeline.config.resume_from_checkpoint is True

    def test_pipeline_all_phase2_features_combined(self):
        """Pipeline can be configured with all Phase 2 features enabled."""
        config = ProcessConfig(
            video_path="input.mp4",
            mask_path="mask.png",
            temporal_smooth_alpha=0.3,
            use_poisson_blending=True,
            use_watermark_tracker=True,
            use_checkpoints=True,
        )
        pipeline = Pipeline(config)

        assert pipeline.config.temporal_smooth_alpha == 0.3
        assert pipeline.config.use_poisson_blending is True
        assert pipeline.config.use_watermark_tracker is True
        assert pipeline.config.use_checkpoints is True

    def test_pipeline_with_adaptive_temporal_smoothing(self):
        """Pipeline supports adaptive temporal smoothing."""
        config = ProcessConfig(
            video_path="input.mp4",
            mask_path="mask.png",
            use_adaptive_temporal_smoothing=True,
            adaptive_motion_threshold=0.05,
        )
        pipeline = Pipeline(config)

        assert pipeline.config.use_adaptive_temporal_smoothing is True
        assert pipeline.config.adaptive_motion_threshold == 0.05

    def test_pipeline_with_watermark_tracker_and_adaptive_smoothing(self):
        """Pipeline can combine watermark tracking with adaptive temporal smoothing."""
        config = ProcessConfig(
            video_path="input.mp4",
            mask_path="mask.json",
            use_watermark_tracker=True,
            use_adaptive_temporal_smoothing=True,
            tracker_smoothing_factor=0.3,
            adaptive_motion_threshold=0.05,
        )
        pipeline = Pipeline(config)

        assert pipeline.config.use_watermark_tracker is True
        assert pipeline.config.use_adaptive_temporal_smoothing is True
        assert pipeline.config.tracker_smoothing_factor == 0.3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
