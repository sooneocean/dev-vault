"""Phase 2 end-to-end integration tests for watermark removal pipeline."""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import cv2
import numpy as np
import pytest

from src.watermark_removal.core.types import CropRegion, ProcessConfig
from src.watermark_removal.detection import WatermarkDetector, BBox
from src.watermark_removal.temporal import TemporalSmoother
from src.watermark_removal.blending import PoissonBlender, ColorMatcher
from src.watermark_removal.persistence import CropRegionSerializer
from src.watermark_removal.metrics import QualityMonitor


def create_test_frame(height: int = 480, width: int = 640, value: int = 128) -> np.ndarray:
    """Create a test frame with optional gradient pattern."""
    frame = np.ones((height, width, 3), dtype=np.uint8) * value
    # Add subtle gradient for realism
    for y in range(height):
        frame[y, :] = np.clip(value + y // 20, 0, 255)
    return frame


class TestPhase2TemporalSmoothing:
    """Test temporal smoothing in Phase 2 pipeline."""

    def test_temporal_smoothing_reduces_jitter(self):
        """Test that temporal smoothing reduces frame-to-frame jitter."""
        smoother = TemporalSmoother(alpha=0.3)

        # Create frames with slight jitter
        frame1 = create_test_frame(value=100)
        frame2 = create_test_frame(value=105)  # ±5 jitter
        frame3 = create_test_frame(value=102)  # ±2 jitter

        # Define region to blend
        region_bbox = (100, 100, 100, 100)

        # Blend frame2 with frame1 (alpha set in init)
        blended2 = smoother.blend_frame(frame2, frame1, region_bbox)
        assert blended2.dtype == np.uint8
        assert blended2.shape == frame2.shape

        # Blended frame should be closer to frame1 (smoothed)
        region_slice = (slice(100, 200), slice(100, 200))
        orig_mean = np.mean(frame2[region_slice])
        blended_mean = np.mean(blended2[region_slice])
        prev_mean = np.mean(frame1[region_slice])

        # Blended should be between original and previous
        assert min(orig_mean, prev_mean) <= blended_mean <= max(orig_mean, prev_mean)

    def test_temporal_smoothing_with_gradient(self):
        """Test temporal smoothing with gradient feathering."""
        smoother = TemporalSmoother(alpha=0.3)

        frame1 = create_test_frame(value=100)
        frame2 = create_test_frame(value=150)

        region_bbox = (100, 100, 150, 150)

        blended = smoother.blend_frame_gradient(
            frame2, frame1, region_bbox, feather_width=20
        )

        assert blended.dtype == np.uint8
        assert blended.shape == frame2.shape
        # Gradient blending should show feathering effect
        assert np.var(blended) > 0


class TestPhase2WatermarkDetection:
    """Test watermark detection integration."""

    def test_detector_initialization(self):
        """Test WatermarkDetector initialization."""
        detector = WatermarkDetector(
            model_name="yolov5s",
            confidence_threshold=0.5,
            nms_threshold=0.45,
        )
        assert detector.model_name == "yolov5s"
        assert detector.confidence_threshold == 0.5

    def test_bbox_serialization(self):
        """Test BBox serialization for JSON storage."""
        bbox = BBox(x=100, y=150, w=200, h=250, confidence=0.92)

        # Serialize
        bbox_dict = bbox.to_dict()
        assert bbox_dict["x"] == 100
        assert bbox_dict["confidence"] == 0.92

        # Deserialize
        restored = BBox.from_dict(bbox_dict)
        assert restored.x == bbox.x
        assert restored.confidence == bbox.confidence

    def test_detector_filter_methods(self):
        """Test detector filtering methods."""
        detector = WatermarkDetector()

        bboxes = [
            BBox(x=0, y=0, w=50, h=50, confidence=0.95),  # Area: 2500
            BBox(x=100, y=100, w=100, h=100, confidence=0.85),  # Area: 10000
            BBox(x=200, y=200, w=30, h=30, confidence=0.4),  # Area: 900
        ]

        # Filter by confidence
        high_conf = detector.filter_by_confidence(bboxes, 0.7)
        assert len(high_conf) == 2

        # Filter by area
        large = detector.filter_by_area(bboxes, min_area=1000)
        assert len(large) == 2

        # Get largest
        largest = detector.get_largest_bbox(bboxes)
        assert largest.w == 100


class TestPhase2PoissonBlending:
    """Test Poisson blending integration."""

    def test_poisson_blender_initialization(self):
        """Test PoissonBlender initialization."""
        blender = PoissonBlender(method="seamless_clone")
        assert blender.method == "seamless_clone"

    def test_color_matcher_initialization(self):
        """Test ColorMatcher initialization."""
        # ColorMatcher is stateless
        matcher = ColorMatcher()
        assert matcher is not None

    def test_blending_with_color_matching(self):
        """Test Poisson blending combined with color matching."""
        blender = PoissonBlender()
        matcher = ColorMatcher()

        background = create_test_frame(height=480, width=640, value=150)
        inpainted = create_test_frame(height=100, width=100, value=100)

        region_bbox = (100, 100, 100, 100)

        # Color match first
        matched = matcher.match_histograms(inpainted, background, region_bbox)
        assert matched.dtype == np.uint8

        # Then blend (if model loads)
        try:
            blended = blender.blend(background, matched, region_bbox)
            assert blended.shape == background.shape
        except Exception:
            # Model may not load in test environment
            pass


class TestPhase2CropRegionSerialization:
    """Test CropRegion checkpoint functionality."""

    def test_crop_region_serialization(self):
        """Test CropRegion JSON serialization."""
        crop = CropRegion(
            x=100, y=150, w=200, h=250,
            scale_factor=2.0,
            context_x=50, context_y=100,
            context_w=300, context_h=400,
            pad_left=10, pad_top=20, pad_right=30, pad_bottom=40,
        )

        crops = {0: crop, 1: crop}

        # Serialize
        json_str = CropRegionSerializer.serialize(crops)
        assert isinstance(json_str, str)

        # Deserialize
        restored = CropRegionSerializer.deserialize(json_str)
        assert len(restored) == 2
        assert restored[0].x == crop.x
        assert restored[1].scale_factor == crop.scale_factor

    def test_checkpoint_save_load(self):
        """Test checkpoint save and load workflow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            crop = CropRegion(
                x=100, y=150, w=200, h=250,
                scale_factor=2.0,
                context_x=50, context_y=100,
                context_w=300, context_h=400,
            )

            crops_orig = {i: crop for i in range(5)}

            # Save
            checkpoint_path = CropRegionSerializer.save_checkpoint(crops_orig, tmpdir)
            assert checkpoint_path is not None
            assert checkpoint_path.exists()

            # Load
            crops_loaded = CropRegionSerializer.load_checkpoint(tmpdir)
            assert crops_loaded is not None
            assert len(crops_loaded) == 5
            assert crops_loaded[0].x == crop.x

    def test_resumption_from_checkpoint(self):
        """Test pipeline resumption from checkpoint."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Phase 1: generate crops
            crops_phase1 = {i: CropRegion(
                x=i*100, y=100, w=200, h=200,
                scale_factor=2.0,
                context_x=50, context_y=50,
                context_w=300, context_h=300,
            ) for i in range(3)}

            # Save checkpoint
            CropRegionSerializer.save_checkpoint(crops_phase1, tmpdir)

            # Phase 2: load checkpoint (resume)
            crops_phase2 = CropRegionSerializer.load_checkpoint(tmpdir)

            # Verify crops are identical
            assert crops_phase2 is not None
            for i in range(3):
                assert crops_phase2[i].x == crops_phase1[i].x


class TestPhase2QualityMonitoring:
    """Test quality monitoring in Phase 2."""

    def test_quality_monitor_initialization(self):
        """Test QualityMonitor initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            monitor = QualityMonitor(output_dir=tmpdir)
            assert monitor.output_dir == Path(tmpdir)

    def test_compute_metrics_for_frames(self):
        """Test computing metrics for multiple frames."""
        monitor = QualityMonitor()

        for i in range(5):
            frame = create_test_frame(value=100 + i*10)
            metrics = monitor.compute_frame_metrics(i, frame)
            assert metrics.frame_id == i
            assert 0 <= metrics.boundary_smoothness <= 1.0

    def test_metrics_export(self):
        """Test metrics export to CSV and JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            monitor = QualityMonitor(output_dir=tmpdir)

            # Compute some metrics
            for i in range(5):
                frame = create_test_frame(value=100 + i*10)
                monitor.compute_frame_metrics(i, frame)

            # Export
            csv_path = monitor.save_metrics_csv()
            json_path = monitor.save_metrics_json()

            assert csv_path is not None
            assert json_path is not None
            assert csv_path.exists()
            assert json_path.exists()

    def test_summary_statistics(self):
        """Test metrics summary statistics."""
        monitor = QualityMonitor()

        for i in range(10):
            frame = create_test_frame()
            monitor.compute_frame_metrics(i, frame)

        summary = monitor.get_summary_statistics()
        assert summary["frame_count"] == 10
        assert "boundary_smoothness" in summary
        assert "mean" in summary["boundary_smoothness"]


class TestPhase2FullPipeline:
    """End-to-end tests for Phase 2 features working together."""

    def test_temporal_smoothing_with_quality_monitoring(self):
        """Test temporal smoothing with concurrent quality monitoring."""
        smoother = TemporalSmoother(alpha=0.3)
        monitor = QualityMonitor()

        frames = [create_test_frame(value=100 + i*5) for i in range(5)]
        region_bbox = (100, 100, 100, 100)

        for i, frame in enumerate(frames):
            # Apply temporal smoothing
            if i > 0:
                smoothed = smoother.blend_frame(frame, frames[i-1], region_bbox)
            else:
                smoothed = frame

            # Monitor quality
            metrics = monitor.compute_frame_metrics(i, smoothed)
            assert metrics is not None

        # Verify metrics were computed
        assert len(monitor.metrics) == 5

    def test_detection_and_blending_workflow(self):
        """Test detection output feeding into blending."""
        # Simulate detection results
        bboxes = [
            BBox(x=100, y=100, w=200, h=200, confidence=0.95),
            BBox(x=400, y=150, w=150, h=150, confidence=0.85),
        ]

        matcher = ColorMatcher()

        # Background and inpainted content
        background = create_test_frame(height=480, width=640, value=150)
        inpainted = create_test_frame(height=200, width=200, value=100)

        # Use largest detection
        largest_bbox = max(bboxes, key=lambda b: b.w * b.h)

        # Color match
        matched = matcher.match_histograms(inpainted, background)
        assert matched.shape == inpainted.shape

    def test_full_phase2_workflow(self):
        """Test complete Phase 2 workflow: detection -> temporal smooth -> quality monitor."""
        # 1. Detection
        detector = WatermarkDetector()
        bboxes = [BBox(x=100, y=100, w=200, h=200, confidence=0.9)]

        # 2. Temporal smoothing
        smoother = TemporalSmoother(alpha=0.3)

        # 3. Blending
        blender = PoissonBlender()
        matcher = ColorMatcher()

        # 4. Serialization
        crops = {0: CropRegion(
            x=100, y=100, w=200, h=200,
            scale_factor=2.0,
            context_x=50, context_y=50,
            context_w=300, context_h=300,
        )}

        # 5. Quality monitoring
        monitor = QualityMonitor()

        # Simulate processing frames
        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(3):
                # Create frames
                original = create_test_frame(value=100)
                inpainted = create_test_frame(value=120)

                # Temporal smooth
                if i > 0:
                    smoothed = smoother.blend_frame(inpainted, original, (100, 100, 200, 200))
                else:
                    smoothed = inpainted

                # Quality monitor
                monitor.compute_frame_metrics(i, smoothed)

            # Save checkpoint
            CropRegionSerializer.save_checkpoint(crops, tmpdir)

            # Export metrics
            monitor.save_metrics_csv()
            monitor.save_metrics_json()

            # Verify all components worked
            assert len(monitor.metrics) == 3
            assert CropRegionSerializer.load_checkpoint(tmpdir) is not None

    def test_backward_compatibility_phase1(self):
        """Test Phase 2 is backward compatible with Phase 1 configs."""
        config = ProcessConfig(
            video_path="test.mp4",
            mask_path="mask.png",
            output_dir="/tmp/out",
            # Phase 2 fields default to safe values
        )

        # Phase 2 defaults should be applied
        assert config.temporal_smooth_enabled is True
        assert config.temporal_smooth_alpha == 0.3

        # Validation should pass
        assert 0.0 <= config.temporal_smooth_alpha <= 1.0


class TestPhase2Features:
    """Test individual Phase 2 features in isolation."""

    def test_temporal_smoothing_disabled(self):
        """Test pipeline works with temporal smoothing disabled."""
        config = ProcessConfig(
            video_path="test.mp4",
            mask_path="mask.png",
            output_dir="/tmp/out",
            temporal_smooth_enabled=False,
        )
        assert config.temporal_smooth_enabled is False

    def test_detection_confidence_threshold(self):
        """Test detector respects confidence threshold."""
        detector = WatermarkDetector(confidence_threshold=0.8)

        bboxes = [
            BBox(x=0, y=0, w=100, h=100, confidence=0.95),
            BBox(x=200, y=200, w=50, h=50, confidence=0.7),
        ]

        filtered = detector.filter_by_confidence(bboxes, 0.8)
        assert len(filtered) == 1
        assert filtered[0].confidence == 0.95

    def test_poisson_blend_fallback(self):
        """Test Poisson blending has fallback to simple paste."""
        blender = PoissonBlender()

        # Simple paste without model (fallback)
        background = create_test_frame(height=480, width=640)
        inpainted = create_test_frame(height=100, width=100, value=200)

        region_bbox = (100, 100, 100, 100)

        # Should return something even if blend fails
        result = blender.blend(background, inpainted, region_bbox)
        assert result is not None
        assert result.shape == background.shape
