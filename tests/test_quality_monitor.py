"""Tests for quality monitoring and metrics."""

import tempfile
from pathlib import Path

import numpy as np
import pytest

from src.watermark_removal.metrics import FrameMetrics, QualityMonitor


class TestFrameMetrics:
    """Test FrameMetrics dataclass."""

    def test_frame_metrics_creation(self):
        """Test creating FrameMetrics instance."""
        metrics = FrameMetrics(
            frame_id=0,
            boundary_smoothness=0.5,
            color_consistency=0.3,
            temporal_consistency=0.8,
            inpaint_quality=0.9,
        )
        assert metrics.frame_id == 0
        assert metrics.boundary_smoothness == 0.5
        assert metrics.color_consistency == 0.3
        assert metrics.temporal_consistency == 0.8
        assert metrics.inpaint_quality == 0.9

    def test_frame_metrics_default_quality(self):
        """Test FrameMetrics with default inpaint_quality."""
        metrics = FrameMetrics(
            frame_id=1,
            boundary_smoothness=0.2,
            color_consistency=0.4,
        )
        assert metrics.inpaint_quality == 1.0

    def test_frame_metrics_none_temporal(self):
        """Test FrameMetrics with None temporal_consistency."""
        metrics = FrameMetrics(
            frame_id=0,
            boundary_smoothness=0.5,
            color_consistency=0.3,
            temporal_consistency=None,
        )
        assert metrics.temporal_consistency is None

    def test_frame_metrics_to_dict(self):
        """Test FrameMetrics conversion to dictionary."""
        metrics = FrameMetrics(
            frame_id=5,
            boundary_smoothness=0.6,
            color_consistency=0.4,
            temporal_consistency=0.7,
            inpaint_quality=0.85,
        )
        d = metrics.to_dict()
        assert d["frame_id"] == 5
        assert d["boundary_smoothness"] == 0.6
        assert d["color_consistency"] == 0.4
        assert d["temporal_consistency"] == 0.7
        assert d["inpaint_quality"] == 0.85


class TestQualityMonitorInitialization:
    """Test QualityMonitor initialization."""

    def test_initialization_default(self):
        """Test QualityMonitor initializes with defaults."""
        monitor = QualityMonitor()
        assert monitor.output_dir is None
        assert monitor.enable_logging is True
        assert monitor.csv_filename == "metrics.csv"
        assert monitor.metrics == []
        assert monitor._previous_frame is None

    def test_initialization_with_output_dir(self):
        """Test initialization with output directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            monitor = QualityMonitor(output_dir=tmpdir)
            assert monitor.output_dir == Path(tmpdir)

    def test_initialization_disable_logging(self):
        """Test initialization with logging disabled."""
        monitor = QualityMonitor(enable_logging=False)
        assert monitor.enable_logging is False

    def test_initialization_custom_csv_filename(self):
        """Test initialization with custom CSV filename."""
        monitor = QualityMonitor(csv_filename="custom_metrics.csv")
        assert monitor.csv_filename == "custom_metrics.csv"


class TestBoundarySmoothnessMetric:
    """Test boundary smoothness computation."""

    def test_boundary_smoothness_empty_frame(self):
        """Test boundary smoothness with empty frame."""
        monitor = QualityMonitor()
        frame = np.array([], dtype=np.uint8)
        smoothness = monitor.compute_boundary_smoothness(frame, (0, 0, 100, 100))
        assert smoothness == 1.0

    def test_boundary_smoothness_uniform_frame(self):
        """Test boundary smoothness with uniform frame (smooth)."""
        monitor = QualityMonitor()
        frame = np.ones((480, 640, 3), dtype=np.uint8) * 128
        smoothness = monitor.compute_boundary_smoothness(frame, (100, 100, 200, 200))
        # Uniform frame should have very low gradient variance -> smoothness ~0
        assert 0 <= smoothness <= 1.0

    def test_boundary_smoothness_noisy_frame(self):
        """Test boundary smoothness with noisy frame (less smooth)."""
        monitor = QualityMonitor()
        frame = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)
        smoothness = monitor.compute_boundary_smoothness(frame, (100, 100, 200, 200))
        # Noisy frame should have high gradient variance -> smoothness > 0
        assert 0 <= smoothness <= 1.0

    def test_boundary_smoothness_at_edge(self):
        """Test boundary smoothness with region at frame edge."""
        monitor = QualityMonitor()
        frame = np.ones((100, 100, 3), dtype=np.uint8) * 128
        # Region at corner
        smoothness = monitor.compute_boundary_smoothness(frame, (0, 0, 50, 50))
        assert 0 <= smoothness <= 1.0


class TestColorConsistencyMetric:
    """Test color consistency computation."""

    def test_color_consistency_identical_frames(self):
        """Test color consistency with identical frames."""
        monitor = QualityMonitor()
        frame = np.ones((480, 640, 3), dtype=np.uint8) * 128
        consistency = monitor.compute_color_consistency(frame, frame, (100, 100, 200, 200))
        # Identical regions should have near-zero distance
        assert 0 <= consistency <= 0.1

    def test_color_consistency_different_frames(self):
        """Test color consistency with different frames."""
        monitor = QualityMonitor()
        frame1 = np.ones((480, 640, 3), dtype=np.uint8) * 50
        frame2 = np.ones((480, 640, 3), dtype=np.uint8) * 200
        consistency = monitor.compute_color_consistency(frame1, frame2, (100, 100, 200, 200))
        # Very different frames should have high distance
        assert consistency > 0.5

    def test_color_consistency_invalid_bbox(self):
        """Test color consistency with invalid bbox."""
        monitor = QualityMonitor()
        frame = np.ones((100, 100, 3), dtype=np.uint8)
        # Invalid bbox (beyond frame bounds)
        consistency = monitor.compute_color_consistency(frame, frame, (200, 200, 100, 100))
        assert consistency == 1.0

    def test_color_consistency_return_type(self):
        """Test color consistency returns float in [0, 1]."""
        monitor = QualityMonitor()
        frame1 = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)
        frame2 = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)
        consistency = monitor.compute_color_consistency(frame1, frame2, (100, 100, 200, 200))
        assert isinstance(consistency, float)
        assert 0 <= consistency <= 1.0


class TestTemporalConsistencyMetric:
    """Test temporal consistency computation."""

    def test_temporal_consistency_first_frame(self):
        """Test temporal consistency for first frame (no previous)."""
        monitor = QualityMonitor()
        frame = np.ones((480, 640, 3), dtype=np.uint8) * 128
        temporal = monitor.compute_temporal_consistency(frame)
        assert temporal is None

    def test_temporal_consistency_identical_frames(self):
        """Test temporal consistency with identical consecutive frames."""
        monitor = QualityMonitor()
        frame = np.ones((480, 640, 3), dtype=np.uint8) * 128

        # Use compute_frame_metrics to properly update _previous_frame
        metrics1 = monitor.compute_frame_metrics(0, frame)
        assert metrics1.temporal_consistency is None

        # Second identical frame
        metrics2 = monitor.compute_frame_metrics(1, frame)
        # Identical frames should have high SSIM -> consistency ~1.0
        assert metrics2.temporal_consistency is not None
        assert metrics2.temporal_consistency > 0.9

    def test_temporal_consistency_different_frames(self):
        """Test temporal consistency with different consecutive frames."""
        monitor = QualityMonitor()
        frame1 = np.ones((480, 640, 3), dtype=np.uint8) * 50
        # Create frame2 with random noise (very different)
        frame2 = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)

        # Use compute_frame_metrics
        metrics1 = monitor.compute_frame_metrics(0, frame1)
        assert metrics1.temporal_consistency is None

        # Very different frame
        metrics2 = monitor.compute_frame_metrics(1, frame2)
        assert metrics2.temporal_consistency is not None
        # Different frames should have lower consistency than identical frames
        assert 0 <= metrics2.temporal_consistency <= 0.9

    def test_temporal_consistency_sequence(self):
        """Test temporal consistency across frame sequence."""
        monitor = QualityMonitor()

        # Create frame sequence with gradual changes
        for i in range(5):
            frame = np.ones((100, 100, 3), dtype=np.uint8) * (100 + i * 10)
            metrics = monitor.compute_frame_metrics(i, frame)
            if i == 0:
                assert metrics.temporal_consistency is None
            else:
                assert metrics.temporal_consistency is not None
                assert 0 <= metrics.temporal_consistency <= 1.0


class TestInpaintQualityMetric:
    """Test inpaint quality computation."""

    def test_inpaint_quality_empty_crop(self):
        """Test inpaint quality with empty crop."""
        monitor = QualityMonitor()
        crop = np.array([], dtype=np.uint8)
        quality = monitor.compute_inpaint_quality(crop)
        assert quality == 0.0

    def test_inpaint_quality_uniform_crop(self):
        """Test inpaint quality with uniform crop."""
        monitor = QualityMonitor()
        crop = np.ones((100, 100, 3), dtype=np.uint8) * 128
        quality = monitor.compute_inpaint_quality(crop)
        # Uniform regions have low variance -> lower quality score
        assert 0 <= quality <= 1.0

    def test_inpaint_quality_noisy_crop(self):
        """Test inpaint quality with realistic noisy crop."""
        monitor = QualityMonitor()
        crop = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)
        quality = monitor.compute_inpaint_quality(crop)
        assert isinstance(quality, float)
        assert 0 <= quality <= 1.0

    def test_inpaint_quality_moderate_variance(self):
        """Test inpaint quality with moderate variance (ideal)."""
        monitor = QualityMonitor()
        # Create crop with moderate variance by mixing values
        crop = np.full((100, 100, 3), 128, dtype=np.uint8)
        crop[25:75, 25:75] = 150  # Add variation
        crop[50:100, 50:100] = 100  # More variation
        quality = monitor.compute_inpaint_quality(crop)
        # Should return a valid quality score
        assert 0 <= quality <= 1.0


class TestComputeFrameMetrics:
    """Test compute_frame_metrics method."""

    def test_compute_frame_metrics_minimal(self):
        """Test compute_frame_metrics with minimal inputs."""
        monitor = QualityMonitor()
        frame = np.ones((480, 640, 3), dtype=np.uint8) * 128
        metrics = monitor.compute_frame_metrics(0, frame)

        assert metrics.frame_id == 0
        assert 0 <= metrics.boundary_smoothness <= 1.0
        assert 0 <= metrics.color_consistency <= 1.0
        assert metrics.temporal_consistency is None  # First frame
        assert 0 <= metrics.inpaint_quality <= 1.0

    def test_compute_frame_metrics_full(self):
        """Test compute_frame_metrics with all parameters."""
        monitor = QualityMonitor()
        original = np.ones((480, 640, 3), dtype=np.uint8) * 100
        current = np.ones((480, 640, 3), dtype=np.uint8) * 120
        crop = np.ones((100, 100, 3), dtype=np.uint8) * 110
        region_bbox = (100, 100, 200, 200)

        metrics = monitor.compute_frame_metrics(
            frame_id=0,
            current_frame=current,
            inpainted_crop=crop,
            region_bbox=region_bbox,
            original_frame=original,
        )

        assert metrics.frame_id == 0
        assert isinstance(metrics.boundary_smoothness, float)
        assert isinstance(metrics.color_consistency, float)
        assert isinstance(metrics.inpaint_quality, float)

    def test_compute_frame_metrics_multiple_frames(self):
        """Test computing metrics for multiple frames."""
        monitor = QualityMonitor()

        for i in range(5):
            frame = np.ones((480, 640, 3), dtype=np.uint8) * (100 + i * 10)
            metrics = monitor.compute_frame_metrics(i, frame)
            assert metrics.frame_id == i

            if i == 0:
                assert metrics.temporal_consistency is None
            else:
                assert metrics.temporal_consistency is not None

        assert len(monitor.metrics) == 5


class TestSummaryStatistics:
    """Test summary statistics computation."""

    def test_summary_statistics_empty(self):
        """Test summary statistics with no metrics."""
        monitor = QualityMonitor()
        summary = monitor.get_summary_statistics()
        assert summary == {}

    def test_summary_statistics_single_frame(self):
        """Test summary statistics with single frame."""
        monitor = QualityMonitor()
        frame = np.ones((480, 640, 3), dtype=np.uint8) * 128
        monitor.compute_frame_metrics(0, frame)

        summary = monitor.get_summary_statistics()
        assert "frame_count" in summary
        assert summary["frame_count"] == 1
        assert "boundary_smoothness" in summary
        assert "color_consistency" in summary

    def test_summary_statistics_multiple_frames(self):
        """Test summary statistics with multiple frames."""
        monitor = QualityMonitor()

        for i in range(10):
            frame = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)
            monitor.compute_frame_metrics(i, frame)

        summary = monitor.get_summary_statistics()
        assert summary["frame_count"] == 10

        # Check that stats have correct structure
        for metric_name in ["boundary_smoothness", "color_consistency", "inpaint_quality"]:
            assert metric_name in summary
            stats = summary[metric_name]
            assert "min" in stats
            assert "max" in stats
            assert "mean" in stats
            assert "std" in stats

    def test_summary_statistics_values(self):
        """Test summary statistics values are in valid ranges."""
        monitor = QualityMonitor()

        for i in range(5):
            frame = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)
            monitor.compute_frame_metrics(i, frame)

        summary = monitor.get_summary_statistics()

        for metric_name, stats in summary.items():
            if metric_name == "frame_count":
                continue

            assert 0 <= stats["min"] <= 1.0
            assert 0 <= stats["max"] <= 1.0
            assert 0 <= stats["mean"] <= 1.0
            assert stats["std"] >= 0


class TestMetricsFileOutput:
    """Test metrics file output (CSV and JSON)."""

    def test_save_metrics_csv_no_logging(self):
        """Test that CSV is not saved when logging disabled."""
        with tempfile.TemporaryDirectory() as tmpdir:
            monitor = QualityMonitor(output_dir=tmpdir, enable_logging=False)
            frame = np.ones((100, 100, 3), dtype=np.uint8)
            monitor.compute_frame_metrics(0, frame)

            result = monitor.save_metrics_csv()
            assert result is None

    def test_save_metrics_csv_success(self):
        """Test successful CSV save."""
        with tempfile.TemporaryDirectory() as tmpdir:
            monitor = QualityMonitor(output_dir=tmpdir)

            for i in range(3):
                frame = np.ones((100, 100, 3), dtype=np.uint8) * (100 + i * 20)
                monitor.compute_frame_metrics(i, frame)

            csv_path = monitor.save_metrics_csv()
            assert csv_path is not None
            assert csv_path.exists()
            assert csv_path.name == "metrics.csv"

            # Verify CSV content
            with open(csv_path) as f:
                lines = f.readlines()
            assert len(lines) >= 4  # Header + 3 frames

    def test_save_metrics_csv_empty_metrics(self):
        """Test CSV save with no metrics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            monitor = QualityMonitor(output_dir=tmpdir)
            result = monitor.save_metrics_csv()
            assert result is None

    def test_save_metrics_json_success(self):
        """Test successful JSON save."""
        with tempfile.TemporaryDirectory() as tmpdir:
            monitor = QualityMonitor(output_dir=tmpdir)

            for i in range(3):
                frame = np.ones((100, 100, 3), dtype=np.uint8) * (100 + i * 20)
                monitor.compute_frame_metrics(i, frame)

            json_path = monitor.save_metrics_json()
            assert json_path is not None
            assert json_path.exists()
            assert json_path.name == "metrics.json"

    def test_save_metrics_json_custom_filename(self):
        """Test JSON save with custom filename."""
        with tempfile.TemporaryDirectory() as tmpdir:
            monitor = QualityMonitor(output_dir=tmpdir)
            frame = np.ones((100, 100, 3), dtype=np.uint8)
            monitor.compute_frame_metrics(0, frame)

            json_path = monitor.save_metrics_json(filename="custom.json")
            assert json_path is not None
            assert json_path.name == "custom.json"


class TestQualityMonitorIntegration:
    """Integration tests for QualityMonitor."""

    def test_full_workflow_with_logging(self):
        """Test full workflow: compute, save, and print metrics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            monitor = QualityMonitor(output_dir=tmpdir)

            # Simulate processing frames
            for i in range(10):
                original = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)
                current = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)
                crop = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)

                monitor.compute_frame_metrics(
                    frame_id=i,
                    current_frame=current,
                    inpainted_crop=crop,
                    region_bbox=(100, 100, 200, 200),
                    original_frame=original,
                )

            # Save and print
            csv_path = monitor.save_metrics_csv()
            json_path = monitor.save_metrics_json()
            monitor.print_summary()

            assert csv_path is not None
            assert json_path is not None
            assert len(monitor.metrics) == 10

    def test_temporal_consistency_across_frames(self):
        """Test temporal consistency is computed correctly across frames."""
        monitor = QualityMonitor()

        # Frame 1: smooth gradient
        frame1 = np.zeros((100, 100, 3), dtype=np.uint8)
        for i in range(100):
            frame1[i, :] = int(i * 255 / 100)

        # Frame 2: similar smooth gradient (slight shift)
        frame2 = np.zeros((100, 100, 3), dtype=np.uint8)
        for i in range(100):
            frame2[i, :] = int((i - 1) * 255 / 100) if i > 0 else 0

        metrics1 = monitor.compute_frame_metrics(0, frame1)
        assert metrics1.temporal_consistency is None

        metrics2 = monitor.compute_frame_metrics(1, frame2)
        assert metrics2.temporal_consistency is not None
        # Similar frames should have high temporal consistency
        assert metrics2.temporal_consistency > 0.7
