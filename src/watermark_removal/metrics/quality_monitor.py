"""Quality monitoring and metrics for watermark removal pipeline."""

import csv
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional

import numpy as np
from skimage.metrics import structural_similarity as ssim


@dataclass
class FrameMetrics:
    """Quality metrics for a single frame."""

    frame_id: int
    """Frame index in video sequence."""

    boundary_smoothness: float
    """Gradient variance at inpaint boundaries (0-1, lower is smoother)."""

    color_consistency: float
    """Color histogram distance between original and stitched (0-1, lower is better)."""

    temporal_consistency: Optional[float] = None
    """Frame-to-frame SSIM with previous frame (0-1, higher is better). None for first frame."""

    inpaint_quality: float = 1.0
    """Inpaint quality heuristic based on region variance (0-1, higher is better)."""

    def to_dict(self) -> dict:
        """Convert to dictionary for CSV/JSON export."""
        return asdict(self)


class QualityMonitor:
    """Compute and log per-frame quality metrics."""

    def __init__(
        self,
        output_dir: Optional[str] = None,
        enable_logging: bool = True,
        csv_filename: str = "metrics.csv",
    ) -> None:
        """
        Initialize quality monitor.

        Args:
            output_dir: Directory to save metrics CSV and JSON. If None, no file logging.
            enable_logging: Enable console and file logging.
            csv_filename: Filename for metrics CSV output.
        """
        self.output_dir = Path(output_dir) if output_dir else None
        self.enable_logging = enable_logging
        self.csv_filename = csv_filename
        self.metrics: list[FrameMetrics] = []
        self._previous_frame: Optional[np.ndarray] = None

    def compute_boundary_smoothness(self, frame: np.ndarray, region_bbox: tuple) -> float:
        """
        Compute boundary smoothness metric (gradient variance at edges).

        Args:
            frame: Full frame (HxWx3, uint8).
            region_bbox: Bounding box (x, y, w, h) of inpainted region.

        Returns:
            Smoothness score (0-1, lower is smoother).
        """
        if frame.size == 0:
            return 1.0

        x, y, w, h = region_bbox

        # Define boundary pixels (feather width)
        feather_width = 5

        # Get boundary region (around inpaint area)
        x_start = max(0, x - feather_width)
        y_start = max(0, y - feather_width)
        x_end = min(frame.shape[1], x + w + feather_width)
        y_end = min(frame.shape[0], y + h + feather_width)

        boundary_region = frame[y_start:y_end, x_start:x_end]

        if boundary_region.size == 0:
            return 1.0

        # Convert to grayscale for gradient computation
        if len(boundary_region.shape) == 3:
            gray = np.mean(boundary_region.astype(np.float32), axis=2)
        else:
            gray = boundary_region.astype(np.float32)

        # Compute gradients (Sobel-like)
        gy, gx = np.gradient(gray)
        gradients = np.sqrt(gx**2 + gy**2)

        # Smoothness: normalized variance of gradients
        gradient_variance = np.var(gradients)
        # Normalize to [0, 1] with empirical scaling
        smoothness = min(1.0, gradient_variance / 100.0)

        return float(smoothness)

    def compute_color_consistency(
        self,
        original_frame: np.ndarray,
        stitched_frame: np.ndarray,
        region_bbox: tuple,
    ) -> float:
        """
        Compute color consistency (histogram distance between regions).

        Args:
            original_frame: Original frame before inpainting (HxWx3, uint8).
            stitched_frame: Frame after inpainting and blending (HxWx3, uint8).
            region_bbox: Bounding box (x, y, w, h) of stitched region.

        Returns:
            Color consistency score (0-1, lower is better match).
        """
        x, y, w, h = region_bbox

        # Clamp to frame bounds
        x_end = min(x + w, original_frame.shape[1])
        y_end = min(y + h, original_frame.shape[0])

        if x_end <= x or y_end <= y:
            return 1.0

        # Extract regions
        orig_region = original_frame[y:y_end, x:x_end]
        stitch_region = stitched_frame[y:y_end, x:x_end]

        if orig_region.size == 0:
            return 1.0

        # Compute histogram distance (chi-square like)
        color_distance = 0.0

        for c in range(min(3, orig_region.shape[2] if len(orig_region.shape) == 3 else 1)):
            orig_hist = np.histogram(orig_region[..., c], bins=32, range=(0, 256))[0]
            stitch_hist = np.histogram(stitch_region[..., c], bins=32, range=(0, 256))[0]

            # Normalize histograms
            orig_hist = orig_hist / (orig_hist.sum() + 1e-8)
            stitch_hist = stitch_hist / (stitch_hist.sum() + 1e-8)

            # L2 distance
            color_distance += np.sqrt(np.sum((orig_hist - stitch_hist) ** 2))

        # Average over channels and normalize to [0, 1]
        consistency = min(1.0, color_distance / 3.0)

        return float(consistency)

    def compute_temporal_consistency(self, current_frame: np.ndarray) -> Optional[float]:
        """
        Compute temporal consistency (frame-to-frame SSIM).

        Args:
            current_frame: Current frame (HxWx3, uint8).

        Returns:
            SSIM score (0-1, higher is more consistent), or None for first frame.
        """
        if self._previous_frame is None:
            return None

        if current_frame.size == 0 or self._previous_frame.size == 0:
            return None

        try:
            # Compute SSIM (convert to grayscale for speed)
            if len(current_frame.shape) == 3:
                curr_gray = np.mean(current_frame.astype(np.float32), axis=2)
            else:
                curr_gray = current_frame.astype(np.float32)

            if len(self._previous_frame.shape) == 3:
                prev_gray = np.mean(self._previous_frame.astype(np.float32), axis=2)
            else:
                prev_gray = self._previous_frame.astype(np.float32)

            # Normalize to [0, 1]
            curr_gray = curr_gray / 255.0
            prev_gray = prev_gray / 255.0

            # Compute SSIM
            temporal_ssim = ssim(prev_gray, curr_gray, data_range=1.0)

            # Normalize to [0, 1]
            temporal_ssim = max(0.0, min(1.0, (temporal_ssim + 1.0) / 2.0))

            return float(temporal_ssim)

        except Exception:
            return None

    def compute_inpaint_quality(self, inpainted_crop: np.ndarray) -> float:
        """
        Compute inpaint quality heuristic (based on region variance).

        Args:
            inpainted_crop: Inpainted crop (HxWh3, uint8).

        Returns:
            Quality score (0-1, higher is better).
        """
        if inpainted_crop.size == 0:
            return 0.0

        # Convert to grayscale
        if len(inpainted_crop.shape) == 3:
            gray = np.mean(inpainted_crop.astype(np.float32), axis=2)
        else:
            gray = inpainted_crop.astype(np.float32)

        # Compute variance (normalized)
        variance = np.var(gray) / 255.0

        # Quality heuristic: favor moderate variance (not too uniform, not too noisy)
        # Target variance around 0.3-0.5
        target_variance = 0.4
        quality = 1.0 - abs(variance - target_variance) / target_variance

        return float(max(0.0, min(1.0, quality)))

    def compute_frame_metrics(
        self,
        frame_id: int,
        current_frame: np.ndarray,
        inpainted_crop: Optional[np.ndarray] = None,
        region_bbox: Optional[tuple] = None,
        original_frame: Optional[np.ndarray] = None,
    ) -> FrameMetrics:
        """
        Compute all metrics for a frame.

        Args:
            frame_id: Frame index.
            current_frame: Current processed frame (HxWx3, uint8).
            inpainted_crop: Inpainted crop region (optional).
            region_bbox: Bounding box of inpainted region (x, y, w, h) (optional).
            original_frame: Original unprocessed frame for color consistency check (optional).

        Returns:
            FrameMetrics object with all computed metrics.
        """
        # Boundary smoothness
        boundary_smoothness = 1.0
        if region_bbox is not None:
            boundary_smoothness = self.compute_boundary_smoothness(current_frame, region_bbox)

        # Color consistency
        color_consistency = 1.0
        if original_frame is not None and region_bbox is not None:
            color_consistency = self.compute_color_consistency(
                original_frame, current_frame, region_bbox
            )

        # Temporal consistency
        temporal_consistency = self.compute_temporal_consistency(current_frame)

        # Inpaint quality
        inpaint_quality = 1.0
        if inpainted_crop is not None:
            inpaint_quality = self.compute_inpaint_quality(inpainted_crop)

        # Store for next frame's temporal consistency
        self._previous_frame = current_frame.copy()

        metrics = FrameMetrics(
            frame_id=frame_id,
            boundary_smoothness=boundary_smoothness,
            color_consistency=color_consistency,
            temporal_consistency=temporal_consistency,
            inpaint_quality=inpaint_quality,
        )

        self.metrics.append(metrics)
        return metrics

    def get_summary_statistics(self) -> dict:
        """
        Get summary statistics across all frames.

        Returns:
            Dictionary with min, max, mean for each metric.
        """
        if not self.metrics:
            return {}

        summary = {}

        # Boundary smoothness
        smoothness_scores = [m.boundary_smoothness for m in self.metrics]
        summary["boundary_smoothness"] = {
            "min": float(np.min(smoothness_scores)),
            "max": float(np.max(smoothness_scores)),
            "mean": float(np.mean(smoothness_scores)),
            "std": float(np.std(smoothness_scores)),
        }

        # Color consistency
        color_scores = [m.color_consistency for m in self.metrics]
        summary["color_consistency"] = {
            "min": float(np.min(color_scores)),
            "max": float(np.max(color_scores)),
            "mean": float(np.mean(color_scores)),
            "std": float(np.std(color_scores)),
        }

        # Temporal consistency (skip None values)
        temporal_scores = [m.temporal_consistency for m in self.metrics if m.temporal_consistency is not None]
        if temporal_scores:
            summary["temporal_consistency"] = {
                "min": float(np.min(temporal_scores)),
                "max": float(np.max(temporal_scores)),
                "mean": float(np.mean(temporal_scores)),
                "std": float(np.std(temporal_scores)),
            }

        # Inpaint quality
        quality_scores = [m.inpaint_quality for m in self.metrics]
        summary["inpaint_quality"] = {
            "min": float(np.min(quality_scores)),
            "max": float(np.max(quality_scores)),
            "mean": float(np.mean(quality_scores)),
            "std": float(np.std(quality_scores)),
        }

        summary["frame_count"] = len(self.metrics)

        return summary

    def save_metrics_csv(self) -> Optional[Path]:
        """
        Save metrics to CSV file.

        Returns:
            Path to CSV file if successful, None otherwise.
        """
        if not self.enable_logging or self.output_dir is None:
            return None

        if not self.metrics:
            return None

        try:
            csv_path = self.output_dir / self.csv_filename
            csv_path.parent.mkdir(parents=True, exist_ok=True)

            with open(csv_path, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=self.metrics[0].to_dict().keys())
                writer.writeheader()
                for metric in self.metrics:
                    writer.writerow(metric.to_dict())

            return csv_path

        except Exception as e:
            return None

    def save_metrics_json(self, filename: str = "metrics.json") -> Optional[Path]:
        """
        Save metrics and summary to JSON file.

        Args:
            filename: Output JSON filename.

        Returns:
            Path to JSON file if successful, None otherwise.
        """
        if not self.enable_logging or self.output_dir is None:
            return None

        try:
            json_path = self.output_dir / filename
            json_path.parent.mkdir(parents=True, exist_ok=True)

            data = {
                "metrics": [m.to_dict() for m in self.metrics],
                "summary": self.get_summary_statistics(),
            }

            with open(json_path, "w") as f:
                json.dump(data, f, indent=2)

            return json_path

        except Exception:
            return None

    def print_summary(self) -> None:
        """Print summary statistics to console."""
        summary = self.get_summary_statistics()

        if not summary:
            return

        print("\n=== Quality Metrics Summary ===")
        print(f"Frames processed: {summary.get('frame_count', 0)}")

        for metric_name, stats in summary.items():
            if metric_name == "frame_count":
                continue

            print(f"\n{metric_name}:")
            if isinstance(stats, dict):
                print(f"  Mean: {stats.get('mean', 0):.4f}")
                print(f"  Std:  {stats.get('std', 0):.4f}")
                print(f"  Min:  {stats.get('min', 0):.4f}")
                print(f"  Max:  {stats.get('max', 0):.4f}")
