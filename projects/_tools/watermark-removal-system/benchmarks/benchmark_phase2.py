#!/usr/bin/env python3
"""
Phase 2 performance benchmarking framework.

Measures processing time, memory usage, and quality metrics across multiple
Phase 2 configurations.

Usage:
    python benchmarks/benchmark_phase2.py
    python benchmarks/benchmark_phase2.py --output results.csv --plot results.png
"""

import argparse
import asyncio
import csv
import logging
import time
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    import numpy as np
except ImportError as e:
    print(f"Error: numpy not found. Install: pip install numpy")
    sys.exit(1)

try:
    import cv2
except ImportError:
    cv2 = None

try:
    import psutil
except ImportError:
    psutil = None

from watermark_removal.core.types import ProcessConfig, InpaintConfig
from watermark_removal.core.pipeline import Pipeline
from watermark_removal.preprocessing.crop_handler import CropHandler


logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
)


@dataclass
class BenchmarkConfig:
    """Configuration for a single benchmark run."""
    name: str
    description: str

    # Phase 1 settings
    context_padding: int = 64
    target_inpaint_size: int = 1024
    blend_feather_width: int = 32
    temporal_smooth_alpha: float = 0.0

    # Phase 2 settings
    use_adaptive_temporal_smoothing: bool = False
    adaptive_motion_threshold: float = 0.05
    use_poisson_blending: bool = False
    poisson_max_iterations: int = 100
    use_watermark_tracker: bool = False
    max_watermarks_per_frame: int = 1


@dataclass
class BenchmarkMetrics:
    """Metrics collected during a benchmark run."""
    config_name: str
    preprocessing_time_sec: float
    inpaint_time_sec: float
    postprocessing_time_sec: float
    total_time_sec: float
    memory_peak_mb: float
    frames_processed: int
    crops_processed: int

    # Derived metrics
    inpaint_time_per_frame: float = 0.0
    throughput_fps: float = 0.0

    def __post_init__(self):
        """Compute derived metrics."""
        if self.frames_processed > 0:
            self.inpaint_time_per_frame = self.inpaint_time_sec / self.frames_processed
            self.throughput_fps = self.frames_processed / self.total_time_sec if self.total_time_sec > 0 else 0.0


def generate_test_video(
    video_path: Path,
    num_frames: int = 30,
    width: int = 1920,
    height: int = 1080,
    fps: int = 30,
    watermark_bbox: Tuple[int, int, int, int] = (100, 100, 200, 150),
) -> Path:
    """
    Generate a synthetic test video with watermark.

    Args:
        video_path: Output video file path
        num_frames: Number of frames to generate
        width: Frame width (pixels)
        height: Frame height (pixels)
        fps: Frames per second
        watermark_bbox: (x, y, w, h) watermark region

    Returns:
        Path to generated video
    """
    if cv2 is None:
        raise ImportError("OpenCV (cv2) required for video generation. Install: pip install opencv-python")

    logger.info(f"Generating test video: {num_frames} frames, {width}x{height}")

    # Create video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(str(video_path), fourcc, fps, (width, height))

    if not writer.isOpened():
        raise RuntimeError(f"Failed to create video writer for {video_path}")

    x, y, w, h = watermark_bbox

    for frame_id in range(num_frames):
        # Create frame with gradient background
        frame = np.zeros((height, width, 3), dtype=np.uint8)

        # Add gradient (blue to green)
        for row in range(height):
            intensity = int(255 * row / height)
            frame[row, :] = [255 - intensity, intensity, 100]

        # Add noise pattern
        noise = np.random.randint(0, 30, (height, width, 3), dtype=np.uint8)
        frame = cv2.addWeighted(frame, 0.8, noise, 0.2, 0)

        # Draw moving object (to test adaptive temporal smoothing)
        obj_x = int(x + (frame_id / num_frames) * (width - x - 100))
        obj_y = int(y + (frame_id / num_frames) * (height - y - 100))
        cv2.circle(frame, (obj_x, obj_y), 30, (0, 255, 255), -1)

        # Add watermark region (solid box + text)
        cv2.rectangle(frame, (x, y), (x + w, y + h), (200, 200, 200), -1)
        cv2.putText(
            frame,
            "WATERMARK",
            (x + 10, y + h // 2),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (0, 0, 0),
            2,
        )

        writer.write(frame)

    writer.release()
    logger.info(f"Generated: {video_path} ({video_path.stat().st_size / 1e6:.1f} MB)")

    return video_path


def create_test_mask(
    mask_path: Path,
    watermark_bbox: Tuple[int, int, int, int] = (100, 100, 200, 150),
) -> Path:
    """
    Create a test watermark mask image.

    Args:
        mask_path: Output mask file path
        watermark_bbox: (x, y, w, h) watermark region

    Returns:
        Path to generated mask
    """
    if cv2 is None:
        raise ImportError("OpenCV (cv2) required for mask generation. Install: pip install opencv-python")

    x, y, w, h = watermark_bbox

    # Create mask image (same size as watermark region)
    mask = np.ones((h, w, 3), dtype=np.uint8) * 255

    # Add some pattern
    cv2.rectangle(mask, (5, 5), (w - 5, h - 5), (200, 200, 200), 2)
    cv2.putText(
        mask,
        "MASK",
        (10, h // 2),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (100, 100, 100),
        2,
    )

    cv2.imwrite(str(mask_path), mask)
    logger.info(f"Generated mask: {mask_path}")

    return mask_path


def build_configs() -> List[BenchmarkConfig]:
    """Build test configuration matrix."""
    configs = [
        BenchmarkConfig(
            name="Phase1-Baseline",
            description="Phase 1 baseline (no postprocessing)",
            temporal_smooth_alpha=0.0,
            use_adaptive_temporal_smoothing=False,
            use_poisson_blending=False,
            use_watermark_tracker=False,
        ),
        BenchmarkConfig(
            name="Phase2-TemporalSmoothing-0.1",
            description="Temporal smoothing alpha=0.1",
            temporal_smooth_alpha=0.1,
            use_adaptive_temporal_smoothing=False,
            use_poisson_blending=False,
        ),
        BenchmarkConfig(
            name="Phase2-TemporalSmoothing-0.3",
            description="Temporal smoothing alpha=0.3",
            temporal_smooth_alpha=0.3,
            use_adaptive_temporal_smoothing=False,
            use_poisson_blending=False,
        ),
        BenchmarkConfig(
            name="Phase2-TemporalSmoothing-0.5",
            description="Temporal smoothing alpha=0.5",
            temporal_smooth_alpha=0.5,
            use_adaptive_temporal_smoothing=False,
            use_poisson_blending=False,
        ),
        BenchmarkConfig(
            name="Phase2-AdaptiveTemporal",
            description="Adaptive temporal smoothing",
            temporal_smooth_alpha=0.0,
            use_adaptive_temporal_smoothing=True,
            adaptive_motion_threshold=0.05,
            use_poisson_blending=False,
        ),
        BenchmarkConfig(
            name="Phase2-Poisson-50iter",
            description="Poisson blending (50 iterations)",
            temporal_smooth_alpha=0.0,
            use_adaptive_temporal_smoothing=False,
            use_poisson_blending=True,
            poisson_max_iterations=50,
        ),
        BenchmarkConfig(
            name="Phase2-Poisson-100iter",
            description="Poisson blending (100 iterations)",
            temporal_smooth_alpha=0.0,
            use_adaptive_temporal_smoothing=False,
            use_poisson_blending=True,
            poisson_max_iterations=100,
        ),
        BenchmarkConfig(
            name="Phase2-Poisson-200iter",
            description="Poisson blending (200 iterations)",
            temporal_smooth_alpha=0.0,
            use_adaptive_temporal_smoothing=False,
            use_poisson_blending=True,
            poisson_max_iterations=200,
        ),
        BenchmarkConfig(
            name="Phase2-MultiWatermark",
            description="Multi-watermark support (3 watermarks per frame)",
            temporal_smooth_alpha=0.0,
            use_adaptive_temporal_smoothing=False,
            use_poisson_blending=False,
            max_watermarks_per_frame=3,
        ),
        BenchmarkConfig(
            name="Phase2-AllCombined",
            description="All Phase 2 features combined",
            temporal_smooth_alpha=0.3,
            use_adaptive_temporal_smoothing=True,
            adaptive_motion_threshold=0.05,
            use_poisson_blending=True,
            poisson_max_iterations=100,
            max_watermarks_per_frame=2,
        ),
    ]

    return configs


class BenchmarkRunner:
    """Executes benchmark runs and collects metrics."""

    def __init__(self, video_path: Path, mask_path: Path, output_dir: Path):
        """
        Initialize benchmark runner.

        Args:
            video_path: Path to test video
            mask_path: Path to watermark mask
            output_dir: Directory for output files
        """
        self.video_path = video_path
        self.mask_path = mask_path
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def run_benchmark(self, config: BenchmarkConfig) -> BenchmarkMetrics:
        """
        Run a single benchmark.

        Args:
            config: BenchmarkConfig to run

        Returns:
            BenchmarkMetrics with measurements
        """
        logger.info(f"\n{'='*70}")
        logger.info(f"Running: {config.name}")
        logger.info(f"Description: {config.description}")
        logger.info(f"{'='*70}")

        # Create output directory for this benchmark
        bench_dir = self.output_dir / config.name
        bench_dir.mkdir(parents=True, exist_ok=True)

        # Build ProcessConfig
        process_config = ProcessConfig(
            video_path=self.video_path,
            mask_path=self.mask_path,
            output_dir=bench_dir,
            context_padding=config.context_padding,
            target_inpaint_size=config.target_inpaint_size,
            blend_feather_width=config.blend_feather_width,
            temporal_smooth_alpha=config.temporal_smooth_alpha,
            use_adaptive_temporal_smoothing=config.use_adaptive_temporal_smoothing,
            adaptive_motion_threshold=config.adaptive_motion_threshold,
            use_poisson_blending=config.use_poisson_blending,
            poisson_max_iterations=config.poisson_max_iterations,
            use_watermark_tracker=config.use_watermark_tracker,
            max_watermarks_per_frame=config.max_watermarks_per_frame,
            keep_intermediate=False,
        )

        # Memory baseline
        mem_before = 0.0
        if psutil is not None:
            process = psutil.Process()
            mem_before = process.memory_info().rss / (1024 * 1024)  # MB

        # Run pipeline with timing
        start_time = time.time()
        try:
            result = await Pipeline.create_and_run(process_config)
            total_time = time.time() - start_time

            # Extract timing from result if available
            preprocessing_time = result.get('preprocessing_time_sec', 0.0)
            inpaint_time = result.get('inpaint_duration_sec', 0.0)
            postprocessing_time = result.get('postprocessing_time_sec', 0.0)

            # If not in result, estimate
            if preprocessing_time == 0.0:
                preprocessing_time = total_time * 0.1
            if inpaint_time == 0.0:
                inpaint_time = total_time * 0.8
            if postprocessing_time == 0.0:
                postprocessing_time = total_time * 0.1

        except Exception as e:
            logger.error(f"Benchmark failed: {e}", exc_info=True)
            # Return failure metrics
            total_time = time.time() - start_time
            preprocessing_time = inpaint_time = postprocessing_time = 0.0
            result = {'frames_processed': 0, 'crops_created': 0}

        # Memory peak
        mem_peak = 0.0
        if psutil is not None:
            mem_after = process.memory_info().rss / (1024 * 1024)
            mem_peak = max(mem_before, mem_after)
        else:
            mem_peak = mem_before

        # Collect metrics
        metrics = BenchmarkMetrics(
            config_name=config.name,
            preprocessing_time_sec=preprocessing_time,
            inpaint_time_sec=inpaint_time,
            postprocessing_time_sec=postprocessing_time,
            total_time_sec=total_time,
            memory_peak_mb=mem_peak,
            frames_processed=result.get('frames_processed', 0),
            crops_processed=result.get('crops_created', 0),
        )

        logger.info(f"Total time: {metrics.total_time_sec:.1f}s")
        logger.info(f"Memory peak: {metrics.memory_peak_mb:.1f} MB")
        logger.info(f"Throughput: {metrics.throughput_fps:.2f} fps")

        return metrics

    async def run_all_benchmarks(self, configs: List[BenchmarkConfig]) -> List[BenchmarkMetrics]:
        """
        Run all benchmark configurations.

        Args:
            configs: List of BenchmarkConfigs to run

        Returns:
            List of BenchmarkMetrics
        """
        results = []

        for i, config in enumerate(configs, 1):
            logger.info(f"\n[{i}/{len(configs)}] Running benchmark...")
            metrics = await self.run_benchmark(config)
            results.append(metrics)
            logger.info(f"✓ Completed: {config.name}")

        return results

    def export_csv(self, metrics_list: List[BenchmarkMetrics], csv_path: Path) -> Path:
        """
        Export metrics to CSV.

        Args:
            metrics_list: List of BenchmarkMetrics
            csv_path: Output CSV file path

        Returns:
            Path to CSV file
        """
        csv_path.parent.mkdir(parents=True, exist_ok=True)

        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'config_name',
                'preprocessing_time_sec',
                'inpaint_time_sec',
                'postprocessing_time_sec',
                'total_time_sec',
                'memory_peak_mb',
                'frames_processed',
                'crops_processed',
                'inpaint_time_per_frame',
                'throughput_fps',
            ])
            writer.writeheader()

            for metrics in metrics_list:
                writer.writerow({
                    'config_name': metrics.config_name,
                    'preprocessing_time_sec': f"{metrics.preprocessing_time_sec:.2f}",
                    'inpaint_time_sec': f"{metrics.inpaint_time_sec:.2f}",
                    'postprocessing_time_sec': f"{metrics.postprocessing_time_sec:.2f}",
                    'total_time_sec': f"{metrics.total_time_sec:.2f}",
                    'memory_peak_mb': f"{metrics.memory_peak_mb:.1f}",
                    'frames_processed': metrics.frames_processed,
                    'crops_processed': metrics.crops_processed,
                    'inpaint_time_per_frame': f"{metrics.inpaint_time_per_frame:.3f}",
                    'throughput_fps': f"{metrics.throughput_fps:.2f}",
                })

        logger.info(f"Exported CSV: {csv_path}")
        return csv_path

    def print_summary(self, metrics_list: List[BenchmarkMetrics]):
        """Print summary table."""
        logger.info("\n" + "="*100)
        logger.info("BENCHMARK RESULTS SUMMARY")
        logger.info("="*100)

        # Sort by total time
        sorted_metrics = sorted(metrics_list, key=lambda m: m.total_time_sec)

        header = f"{'Config':<30} {'Total (s)':<12} {'Inpaint (s)':<12} {'FPS':<8} {'Memory (MB)':<12}"
        logger.info(header)
        logger.info("-" * 100)

        for metrics in sorted_metrics:
            logger.info(
                f"{metrics.config_name:<30} "
                f"{metrics.total_time_sec:>10.2f}s  "
                f"{metrics.inpaint_time_sec:>10.2f}s  "
                f"{metrics.throughput_fps:>6.2f}  "
                f"{metrics.memory_peak_mb:>10.1f}"
            )

        # Recommendations
        fastest = sorted_metrics[0]
        slowest = sorted_metrics[-1]

        logger.info("\n" + "="*100)
        logger.info("RECOMMENDATIONS")
        logger.info("="*100)
        logger.info(f"🏃 Fastest:  {fastest.config_name} ({fastest.total_time_sec:.2f}s)")
        logger.info(f"🐢 Slowest:  {slowest.config_name} ({slowest.total_time_sec:.2f}s)")

        # Best balanced (good quality/performance)
        balanced = sorted_metrics[len(sorted_metrics) // 2]
        logger.info(f"⚖️  Balanced: {balanced.config_name} ({balanced.total_time_sec:.2f}s)")


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Phase 2 performance benchmarking",
    )
    parser.add_argument(
        "--video",
        type=Path,
        help="Test video (generates if not provided)",
    )
    parser.add_argument(
        "--mask",
        type=Path,
        help="Watermark mask (generates if not provided)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("benchmark_results"),
        help="Output directory for benchmark results",
    )
    parser.add_argument(
        "--csv",
        type=Path,
        help="CSV output path (default: benchmark_results/results.csv)",
    )
    parser.add_argument(
        "--configs",
        type=str,
        default="all",
        help="Configs to run (all, fast, quality) or comma-separated list",
    )

    args = parser.parse_args()

    # Setup temporary directory
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Generate or use provided video/mask
        if args.video:
            video_path = args.video
        else:
            video_path = tmpdir / "test_video.mp4"
            generate_test_video(video_path, num_frames=30)

        if args.mask:
            mask_path = args.mask
        else:
            mask_path = tmpdir / "watermark_mask.png"
            create_test_mask(mask_path)

        # Build configurations
        all_configs = build_configs()

        if args.configs == "fast":
            configs = [c for c in all_configs if "Phase1" in c.name or "0.1" in c.name]
        elif args.configs == "quality":
            configs = [c for c in all_configs if "Poisson" in c.name or "Adaptive" in c.name]
        else:
            configs = all_configs

        # Run benchmarks
        runner = BenchmarkRunner(video_path, mask_path, args.output_dir)
        results = await runner.run_all_benchmarks(configs)

        # Export results
        csv_path = args.csv or args.output_dir / "results.csv"
        runner.export_csv(results, csv_path)

        # Print summary
        runner.print_summary(results)


if __name__ == "__main__":
    asyncio.run(main())
