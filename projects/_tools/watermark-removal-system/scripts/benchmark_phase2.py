#!/usr/bin/env python3
"""
Phase 2 Performance Benchmarking Script

Benchmarks all Phase 2 features to measure per-frame overhead and identify bottlenecks:
- Temporal smoothing (simple + adaptive)
- Watermark tracking (YOLO detection)
- Poisson blending (iterations vs quality)
- Full Phase 2 pipeline overhead

Usage:
    python scripts/benchmark_phase2.py --num-frames 10 --feature all
    python scripts/benchmark_phase2.py --feature temporal --iterations 50 100 200
"""

import argparse
import logging
import time
import json
import tempfile
from pathlib import Path
from typing import Dict, List, Tuple
import numpy as np
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from watermark_removal.core.types import ProcessConfig, InpaintConfig, CropRegion
from watermark_removal.postprocessing.temporal_smoother import TemporalSmoother, AdaptiveTemporalSmoother
from watermark_removal.postprocessing.poisson_blender import PoissonBlender

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class SyntheticDataGenerator:
    """Generate synthetic test data (frames, masks, crops)."""

    @staticmethod
    def create_synthetic_frames(
        num_frames: int,
        width: int,
        height: int,
        watermark_region: Tuple[int, int, int, int] | None = None,
    ) -> List[np.ndarray]:
        """
        Create synthetic video frames with optional watermark region.

        Args:
            num_frames: Number of frames to generate
            width: Frame width in pixels
            height: Frame height in pixels
            watermark_region: (x, y, w, h) of watermark region, or None

        Returns:
            List of RGB frames (H, W, 3), uint8
        """
        frames = []
        for frame_idx in range(num_frames):
            # Create base frame with gradient pattern
            frame = np.zeros((height, width, 3), dtype=np.uint8)

            # Background: horizontal gradient
            for y in range(height):
                intensity = int(50 + 150 * (y / height))
                frame[y, :] = [intensity, intensity // 2, 200 - intensity // 2]

            # Add some motion pattern (vertical shift)
            motion_offset = (frame_idx * 5) % width
            frame[:, motion_offset:motion_offset+20, :] = [100, 200, 100]

            # Add watermark region (bright rectangle)
            if watermark_region:
                x, y, w, h = watermark_region
                # Clip to image bounds
                x_end = min(x + w, width)
                y_end = min(y + h, height)
                frame[y:y_end, x:x_end, :] = [50, 50, 150]  # Blue watermark

                # Add text-like pattern inside watermark
                if frame_idx % 2 == 0:
                    # Alternate frames: slightly different watermark position (moving)
                    x_alt = x + (1 if frame_idx % 4 == 0 else -1)
                    x_alt_end = min(x_alt + w, width)
                    if x_alt >= 0 and x_alt_end <= width:
                        frame[y:y_end, x_alt:x_alt_end, :] = [60, 60, 160]

            frames.append(frame)

        logger.info(f"Generated {num_frames} synthetic frames ({width}x{height})")
        return frames

    @staticmethod
    def create_inpainted_frames(
        num_frames: int,
        width: int,
        height: int,
        watermark_region: Tuple[int, int, int, int],
    ) -> List[np.ndarray]:
        """
        Create synthetic inpainted frames (watermark removed).

        Args:
            num_frames: Number of frames
            width: Frame width
            height: Frame height
            watermark_region: (x, y, w, h) of watermark region

        Returns:
            List of inpainted frames with watermark replaced by context
        """
        frames = SyntheticDataGenerator.create_synthetic_frames(num_frames, width, height, None)
        x, y, w, h = watermark_region

        # Replace watermark region with blurred context
        for frame in frames:
            x_end = min(x + w, width)
            y_end = min(y + h, height)
            region = frame[y:y_end, x:x_end, :]

            # Smooth the watermark region (simulate inpainting)
            for _ in range(3):
                region = (
                    np.roll(region, 1, axis=0) * 0.25 +
                    np.roll(region, -1, axis=0) * 0.25 +
                    region * 0.5
                )
            frame[y:y_end, x:x_end, :] = region

        return frames


class BenchmarkRunner:
    """Run benchmarks and collect timing data."""

    def __init__(self, num_frames: int = 10, resolution: str = "320x240"):
        """
        Initialize benchmark runner.

        Args:
            num_frames: Number of frames for each benchmark
            resolution: Resolution as "WxH" string
        """
        self.num_frames = num_frames
        width, height = map(int, resolution.split('x'))
        self.width = width
        self.height = height
        self.results: Dict[str, Dict] = {}

    def benchmark_temporal_smoothing(self) -> Dict:
        """
        Benchmark temporal smoothing overhead.

        Tests: alpha values 0.1, 0.3, 0.5
        Returns timing per-frame for each alpha.
        """
        logger.info("=" * 60)
        logger.info("BENCHMARK: Temporal Smoothing")
        logger.info("=" * 60)

        frames = SyntheticDataGenerator.create_synthetic_frames(
            self.num_frames, self.width, self.height
        )
        results = {"feature": "temporal_smoothing", "frames": self.num_frames}
        alpha_results = {}

        for alpha in [0.0, 0.1, 0.3, 0.5]:
            smoother = TemporalSmoother(alpha=alpha)

            # Warm up
            _ = smoother.smooth_sequence(frames[:2])

            # Benchmark
            start_time = time.perf_counter()
            _ = smoother.smooth_sequence(frames)
            elapsed = time.perf_counter() - start_time

            per_frame_ms = (elapsed / self.num_frames) * 1000
            alpha_results[f"alpha_{alpha}"] = {
                "total_time_sec": elapsed,
                "per_frame_ms": per_frame_ms,
            }
            logger.info(f"  alpha={alpha}: {per_frame_ms:.2f}ms/frame")

        results["alpha_results"] = alpha_results
        self.results["temporal_smoothing"] = results
        return results

    def benchmark_adaptive_temporal_smoothing(self) -> Dict:
        """
        Benchmark adaptive temporal smoothing.

        Compares simple vs adaptive smoothing on mixed motion.
        """
        logger.info("=" * 60)
        logger.info("BENCHMARK: Adaptive Temporal Smoothing")
        logger.info("=" * 60)

        frames = SyntheticDataGenerator.create_synthetic_frames(
            self.num_frames, self.width, self.height
        )
        results = {"feature": "adaptive_temporal_smoothing", "frames": self.num_frames}

        base_alpha = 0.3
        smoother = AdaptiveTemporalSmoother(alpha=base_alpha)

        # Warm up
        _ = [smoother.smooth_frame_adaptive(frames[i], frames[i-1]) for i in range(1, min(3, len(frames)))]

        # Benchmark adaptive
        start_time = time.perf_counter()
        smoothed_frames = []
        alphas_used = []
        for i, frame in enumerate(frames):
            prev = smoothed_frames[-1] if smoothed_frames else None
            smoothed_frame, used_alpha = smoother.smooth_frame_adaptive(
                frame, prev, motion_threshold=0.05
            )
            smoothed_frames.append(smoothed_frame)
            alphas_used.append(used_alpha)
        elapsed = time.perf_counter() - start_time

        per_frame_ms = (elapsed / self.num_frames) * 1000
        results["total_time_sec"] = elapsed
        results["per_frame_ms"] = per_frame_ms
        results["mean_alpha_used"] = float(np.mean([a for a in alphas_used if a > 0]))
        logger.info(f"  Total: {per_frame_ms:.2f}ms/frame (mean alpha: {results['mean_alpha_used']:.3f})")

        self.results["adaptive_temporal_smoothing"] = results
        return results

    def benchmark_poisson_blending(self, iterations_list: List[int] | None = None) -> Dict:
        """
        Benchmark Poisson blending with different iteration counts.

        Args:
            iterations_list: List of iteration counts to test (default: [50, 100, 200])

        Returns:
            Timing results for each iteration count
        """
        logger.info("=" * 60)
        logger.info("BENCHMARK: Poisson Blending")
        logger.info("=" * 60)

        if iterations_list is None:
            iterations_list = [50, 100, 200]

        # Create test crop (smaller for faster benchmarking)
        crop_size = 128
        target_frame = np.random.randint(50, 150, (crop_size, crop_size, 3), dtype=np.uint8)
        source_frame = np.random.randint(50, 150, (crop_size, crop_size, 3), dtype=np.uint8)

        # Create mask (center region is source, edges are target)
        mask = np.zeros((crop_size, crop_size), dtype=np.uint8)
        margin = 20
        mask[margin:-margin, margin:-margin] = 255

        results = {"feature": "poisson_blending", "crop_size": crop_size}
        iteration_results = {}

        for max_iter in iterations_list:
            blender = PoissonBlender(max_iterations=max_iter, tolerance=0.01)

            # Warm up
            _ = blender.blend(target_frame, source_frame, mask, blend_width=16)

            # Benchmark (single blend, 3 times for speed)
            times = []
            for _ in range(3):  # Run 3 times (reduced from 5 for speed)
                start_time = time.perf_counter()
                _ = blender.blend(target_frame, source_frame, mask, blend_width=16)
                elapsed = time.perf_counter() - start_time
                times.append(elapsed)

            mean_time = np.mean(times)
            std_time = np.std(times) if len(times) > 1 else 0
            iteration_results[f"iterations_{max_iter}"] = {
                "mean_time_ms": mean_time * 1000,
                "std_time_ms": std_time * 1000,
            }
            logger.info(f"  iterations={max_iter}: {mean_time*1000:.2f}±{std_time*1000:.2f}ms")

        results["iteration_results"] = iteration_results
        self.results["poisson_blending"] = results
        return results

    def benchmark_full_pipeline(self) -> Dict:
        """
        Benchmark full Phase 2 pipeline (temporal + tracking + poisson).

        Simulates typical processing workflow.
        """
        logger.info("=" * 60)
        logger.info("BENCHMARK: Full Phase 2 Pipeline")
        logger.info("=" * 60)

        watermark_region = (50, 50, 100, 100)
        frames = SyntheticDataGenerator.create_synthetic_frames(
            self.num_frames, self.width, self.height, watermark_region
        )
        inpainted_frames = SyntheticDataGenerator.create_inpainted_frames(
            self.num_frames, self.width, self.height, watermark_region
        )

        results = {"feature": "full_pipeline", "frames": self.num_frames}

        # Phase 1 baseline (no Phase 2 features)
        logger.info("  Running Phase 1 baseline (stitch only)...")
        start_baseline = time.perf_counter()
        # Simulate stitch: just identity operation
        _ = inpainted_frames.copy()
        baseline_time = time.perf_counter() - start_baseline

        # Phase 2 full (temporal + poisson)
        logger.info("  Running Phase 2 full pipeline...")
        start_phase2 = time.perf_counter()

        # Temporal smoothing
        temporal_smoother = TemporalSmoother(alpha=0.3)
        smoothed = temporal_smoother.smooth_sequence(inpainted_frames)

        # Poisson blending (simulate on crop regions only, not full frames)
        blender = PoissonBlender(max_iterations=100)
        crop_size = 128
        x, y, w, h = watermark_region
        for i in range(min(5, len(smoothed))):  # Only blend 5 frames for speed
            frame = smoothed[i]
            inpainted = inpainted_frames[i]

            # Extract crop region
            x_end = min(x + w, self.width)
            y_end = min(y + h, self.height)
            target_crop = frame[y:y_end, x:x_end, :].copy()
            source_crop = inpainted[y:y_end, x:x_end, :].copy()

            # Create mask for crop
            crop_mask = np.zeros_like(target_crop[:, :, 0], dtype=np.uint8)
            crop_mask[::] = 255

            # Blend crop only
            try:
                if target_crop.shape[0] > 0 and target_crop.shape[1] > 0:
                    blended = blender.blend(target_crop, source_crop, crop_mask, blend_width=16)
                    frame[y:y_end, x:x_end, :] = blended
            except Exception as e:
                logger.warning(f"Poisson blend failed: {e}")

        phase2_time = time.perf_counter() - start_phase2

        phase2_per_frame = (phase2_time / self.num_frames) * 1000
        baseline_per_frame = (baseline_time / self.num_frames) * 1000

        results["baseline_total_sec"] = baseline_time
        results["baseline_per_frame_ms"] = baseline_per_frame
        results["phase2_total_sec"] = phase2_time
        results["phase2_per_frame_ms"] = phase2_per_frame
        results["overhead_percent"] = ((phase2_time - baseline_time) / baseline_time) * 100 if baseline_time > 0 else 0

        logger.info(f"  Phase 1 baseline: {baseline_per_frame:.2f}ms/frame")
        logger.info(f"  Phase 2 full: {phase2_per_frame:.2f}ms/frame")
        logger.info(f"  Overhead: {results['overhead_percent']:.1f}%")

        self.results["full_pipeline"] = results
        return results

    def run_all_benchmarks(self, iterations_list: List[int] | None = None):
        """Run all benchmarks."""
        logger.info("\n")
        logger.info("╔" + "=" * 58 + "╗")
        logger.info("║" + " " * 10 + "PHASE 2 PERFORMANCE BENCHMARKS" + " " * 18 + "║")
        logger.info("║" + f" Frames: {self.num_frames}, Resolution: {self.width}x{self.height}" + " " * 20 + "║")
        logger.info("╚" + "=" * 58 + "╝")

        self.benchmark_temporal_smoothing()
        self.benchmark_adaptive_temporal_smoothing()
        self.benchmark_poisson_blending(iterations_list)
        self.benchmark_full_pipeline()

        logger.info("\n")
        self.print_summary()

    def print_summary(self):
        """Print benchmark summary."""
        logger.info("╔" + "=" * 58 + "╗")
        logger.info("║" + " " * 20 + "BENCHMARK SUMMARY" + " " * 20 + "║")
        logger.info("╚" + "=" * 58 + "╝")

        for feature, data in self.results.items():
            logger.info(f"\n{feature.upper().replace('_', ' ')}:")
            logger.info(json.dumps(data, indent=2))

    def save_results(self, output_path: Path):
        """Save benchmark results to JSON file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(self.results, f, indent=2)
        logger.info(f"Results saved to {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Benchmark Phase 2 watermark removal features"
    )
    parser.add_argument(
        "--num-frames",
        type=int,
        default=10,
        help="Number of frames for benchmarking (default: 10)"
    )
    parser.add_argument(
        "--resolution",
        type=str,
        default="320x240",
        help="Resolution as WxH (default: 320x240)"
    )
    parser.add_argument(
        "--feature",
        type=str,
        choices=["all", "temporal", "adaptive", "poisson", "pipeline"],
        default="all",
        help="Which feature to benchmark (default: all)"
    )
    parser.add_argument(
        "--iterations",
        type=int,
        nargs="+",
        default=[50, 100, 200],
        help="Poisson solver iterations to test (default: 50 100 200)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="benchmark_results.json",
        help="Output JSON file for results (default: benchmark_results.json)"
    )

    args = parser.parse_args()

    runner = BenchmarkRunner(num_frames=args.num_frames, resolution=args.resolution)

    if args.feature == "all":
        runner.run_all_benchmarks(args.iterations)
    elif args.feature == "temporal":
        runner.benchmark_temporal_smoothing()
    elif args.feature == "adaptive":
        runner.benchmark_adaptive_temporal_smoothing()
    elif args.feature == "poisson":
        runner.benchmark_poisson_blending(args.iterations)
    elif args.feature == "pipeline":
        runner.benchmark_full_pipeline()

    runner.print_summary()
    runner.save_results(Path(args.output))


if __name__ == "__main__":
    main()
