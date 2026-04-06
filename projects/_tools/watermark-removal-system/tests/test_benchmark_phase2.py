"""
Unit tests for Phase 2 performance benchmarking framework.

Tests benchmark configuration, metrics collection, and result export.
"""

import pytest
import tempfile
import csv
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import from benchmarks
sys.path.insert(0, str(Path(__file__).parent.parent / "benchmarks"))

from benchmark_phase2 import (
    BenchmarkConfig,
    BenchmarkMetrics,
    BenchmarkRunner,
    build_configs,
    generate_test_video,
    create_test_mask,
)


class TestBenchmarkConfig:
    """Test BenchmarkConfig structure."""

    def test_config_creation(self):
        """Create a benchmark configuration."""
        config = BenchmarkConfig(
            name="test-config",
            description="Test configuration",
            temporal_smooth_alpha=0.3,
            use_poisson_blending=True,
            poisson_max_iterations=100,
        )

        assert config.name == "test-config"
        assert config.temporal_smooth_alpha == 0.3
        assert config.use_poisson_blending is True
        assert config.poisson_max_iterations == 100

    def test_config_defaults(self):
        """Config has sensible defaults."""
        config = BenchmarkConfig(
            name="default",
            description="Default config",
        )

        assert config.context_padding == 64
        assert config.target_inpaint_size == 1024
        assert config.blend_feather_width == 32
        assert config.temporal_smooth_alpha == 0.0
        assert config.use_adaptive_temporal_smoothing is False
        assert config.use_poisson_blending is False
        assert config.max_watermarks_per_frame == 1


class TestBenchmarkMetrics:
    """Test BenchmarkMetrics and derived metrics."""

    def test_metrics_creation(self):
        """Create metrics object."""
        metrics = BenchmarkMetrics(
            config_name="test",
            preprocessing_time_sec=1.0,
            inpaint_time_sec=10.0,
            postprocessing_time_sec=2.0,
            total_time_sec=13.0,
            memory_peak_mb=1024.0,
            frames_processed=30,
            crops_processed=30,
        )

        assert metrics.config_name == "test"
        assert metrics.total_time_sec == 13.0

    def test_metrics_derived_fields(self):
        """Computed metrics are correct."""
        metrics = BenchmarkMetrics(
            config_name="test",
            preprocessing_time_sec=1.0,
            inpaint_time_sec=10.0,
            postprocessing_time_sec=2.0,
            total_time_sec=13.0,
            memory_peak_mb=1024.0,
            frames_processed=30,
            crops_processed=30,
        )

        # __post_init__ computes derived fields
        assert metrics.inpaint_time_per_frame == pytest.approx(10.0 / 30)
        assert metrics.throughput_fps == pytest.approx(30 / 13.0, rel=0.01)

    def test_metrics_zero_frames(self):
        """Handle zero frames processed."""
        metrics = BenchmarkMetrics(
            config_name="test",
            preprocessing_time_sec=0.0,
            inpaint_time_sec=0.0,
            postprocessing_time_sec=0.0,
            total_time_sec=0.1,
            memory_peak_mb=100.0,
            frames_processed=0,
            crops_processed=0,
        )

        assert metrics.inpaint_time_per_frame == 0.0
        assert metrics.throughput_fps == 0.0


class TestBuildConfigs:
    """Test configuration matrix generation."""

    def test_configs_list_not_empty(self):
        """Build configs returns a list."""
        configs = build_configs()

        assert isinstance(configs, list)
        assert len(configs) > 0

    def test_configs_have_unique_names(self):
        """All configs have unique names."""
        configs = build_configs()
        names = [c.name for c in configs]

        assert len(names) == len(set(names))

    def test_configs_cover_features(self):
        """Config matrix covers Phase 2 features."""
        configs = build_configs()

        # Check for temporal smoothing configs
        temporal_configs = [c for c in configs if c.temporal_smooth_alpha > 0]
        assert len(temporal_configs) >= 3  # 0.1, 0.3, 0.5

        # Check for adaptive temporal smoothing
        adaptive_configs = [c for c in configs if c.use_adaptive_temporal_smoothing]
        assert len(adaptive_configs) >= 1

        # Check for Poisson blending
        poisson_configs = [c for c in configs if c.use_poisson_blending]
        assert len(poisson_configs) >= 3  # 50, 100, 200 iterations

        # Check for multi-watermark
        multi_configs = [c for c in configs if c.max_watermarks_per_frame > 1]
        assert len(multi_configs) >= 1


class TestTestVideoGeneration:
    """Test synthetic test video generation."""

    def test_generate_test_video(self):
        """Generate test video."""
        try:
            import cv2
        except ImportError:
            pytest.skip("OpenCV not available")

        with tempfile.TemporaryDirectory() as tmpdir:
            video_path = Path(tmpdir) / "test.mp4"

            result = generate_test_video(
                video_path,
                num_frames=5,
                width=640,
                height=480,
            )

            assert result == video_path
            assert video_path.exists()
            assert video_path.stat().st_size > 0

    def test_generate_test_video_custom_params(self):
        """Generate video with custom parameters."""
        try:
            import cv2
        except ImportError:
            pytest.skip("OpenCV not available")

        with tempfile.TemporaryDirectory() as tmpdir:
            video_path = Path(tmpdir) / "test.mp4"

            generate_test_video(
                video_path,
                num_frames=10,
                width=1920,
                height=1080,
                fps=60,
                watermark_bbox=(200, 200, 300, 250),
            )

            assert video_path.exists()


class TestTestMaskGeneration:
    """Test watermark mask generation."""

    def test_create_test_mask(self):
        """Generate test watermark mask."""
        try:
            import cv2
        except ImportError:
            pytest.skip("OpenCV not available")

        with tempfile.TemporaryDirectory() as tmpdir:
            mask_path = Path(tmpdir) / "mask.png"

            result = create_test_mask(
                mask_path,
                watermark_bbox=(100, 100, 200, 150),
            )

            assert result == mask_path
            assert mask_path.exists()

    def test_mask_dimensions(self):
        """Mask has correct dimensions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mask_path = Path(tmpdir) / "mask.png"

            try:
                import cv2
            except ImportError:
                pytest.skip("OpenCV not available")

            w, h = 200, 150
            create_test_mask(mask_path, watermark_bbox=(100, 100, w, h))

            mask = cv2.imread(str(mask_path))
            assert mask is not None
            assert mask.shape[0] == h
            assert mask.shape[1] == w


class TestBenchmarkRunnerInit:
    """Test BenchmarkRunner initialization."""

    def test_runner_creation(self):
        """Create benchmark runner."""
        with tempfile.TemporaryDirectory() as tmpdir:
            video_path = Path(tmpdir) / "video.mp4"
            mask_path = Path(tmpdir) / "mask.png"
            output_dir = Path(tmpdir) / "results"

            runner = BenchmarkRunner(video_path, mask_path, output_dir)

            assert runner.video_path == video_path
            assert runner.mask_path == mask_path
            assert runner.output_dir == output_dir
            assert output_dir.exists()


class TestCSVExport:
    """Test CSV export functionality."""

    def test_export_csv(self):
        """Export metrics to CSV."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "results.csv"
            video_path = Path(tmpdir) / "video.mp4"
            mask_path = Path(tmpdir) / "mask.png"
            output_dir = Path(tmpdir) / "benchmarks"

            runner = BenchmarkRunner(video_path, mask_path, output_dir)

            # Create sample metrics
            metrics_list = [
                BenchmarkMetrics(
                    config_name="config1",
                    preprocessing_time_sec=1.0,
                    inpaint_time_sec=10.0,
                    postprocessing_time_sec=2.0,
                    total_time_sec=13.0,
                    memory_peak_mb=1024.0,
                    frames_processed=30,
                    crops_processed=30,
                ),
                BenchmarkMetrics(
                    config_name="config2",
                    preprocessing_time_sec=1.5,
                    inpaint_time_sec=15.0,
                    postprocessing_time_sec=2.5,
                    total_time_sec=19.0,
                    memory_peak_mb=1536.0,
                    frames_processed=30,
                    crops_processed=60,
                ),
            ]

            result = runner.export_csv(metrics_list, csv_path)

            assert result == csv_path
            assert csv_path.exists()

    def test_csv_contents(self):
        """CSV has correct structure and values."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "results.csv"
            video_path = Path(tmpdir) / "video.mp4"
            mask_path = Path(tmpdir) / "mask.png"
            output_dir = Path(tmpdir) / "benchmarks"

            runner = BenchmarkRunner(video_path, mask_path, output_dir)

            metrics_list = [
                BenchmarkMetrics(
                    config_name="test_config",
                    preprocessing_time_sec=1.0,
                    inpaint_time_sec=10.0,
                    postprocessing_time_sec=2.0,
                    total_time_sec=13.0,
                    memory_peak_mb=1024.0,
                    frames_processed=30,
                    crops_processed=30,
                ),
            ]

            runner.export_csv(metrics_list, csv_path)

            # Read and verify CSV
            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            assert len(rows) == 1
            assert rows[0]['config_name'] == 'test_config'
            assert float(rows[0]['total_time_sec']) == pytest.approx(13.0)
            assert int(rows[0]['frames_processed']) == 30
            assert int(rows[0]['crops_processed']) == 30


class TestMetricsCollection:
    """Test metrics collection during benchmarks."""

    def test_metrics_timing_order(self):
        """Metrics have consistent timing relationships."""
        metrics = BenchmarkMetrics(
            config_name="test",
            preprocessing_time_sec=1.0,
            inpaint_time_sec=10.0,
            postprocessing_time_sec=2.0,
            total_time_sec=13.0,
            memory_peak_mb=1024.0,
            frames_processed=30,
            crops_processed=30,
        )

        # Total should equal sum of phases (approximately)
        sum_phases = (
            metrics.preprocessing_time_sec
            + metrics.inpaint_time_sec
            + metrics.postprocessing_time_sec
        )
        assert metrics.total_time_sec == pytest.approx(sum_phases)

    def test_metrics_proportions(self):
        """Inpaint time is typically largest."""
        metrics = BenchmarkMetrics(
            config_name="test",
            preprocessing_time_sec=1.0,
            inpaint_time_sec=10.0,
            postprocessing_time_sec=2.0,
            total_time_sec=13.0,
            memory_peak_mb=1024.0,
            frames_processed=30,
            crops_processed=30,
        )

        # Inpaint should be the dominant phase
        assert metrics.inpaint_time_sec > metrics.preprocessing_time_sec
        assert metrics.inpaint_time_sec > metrics.postprocessing_time_sec


class TestBenchmarkSummary:
    """Test summary and recommendations."""

    def test_print_summary_does_not_crash(self):
        """Print summary method runs without error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            video_path = Path(tmpdir) / "video.mp4"
            mask_path = Path(tmpdir) / "mask.png"
            output_dir = Path(tmpdir) / "benchmarks"

            runner = BenchmarkRunner(video_path, mask_path, output_dir)

            metrics_list = [
                BenchmarkMetrics(
                    config_name=f"config{i}",
                    preprocessing_time_sec=i * 1.0,
                    inpaint_time_sec=i * 10.0,
                    postprocessing_time_sec=i * 2.0,
                    total_time_sec=i * 13.0,
                    memory_peak_mb=1024.0 * (i + 1),
                    frames_processed=30,
                    crops_processed=30,
                )
                for i in range(1, 4)
            ]

            # Should not raise
            runner.print_summary(metrics_list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
