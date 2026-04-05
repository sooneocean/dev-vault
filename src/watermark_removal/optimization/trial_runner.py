"""Trial runner for executing individual hyperparameter optimization trials."""

import logging
from dataclasses import dataclass
from typing import Any, Optional

import numpy as np
from optuna.trial import Trial

from src.watermark_removal.core.types import ProcessConfig
from src.watermark_removal.metrics.quality_monitor import QualityMonitor

logger = logging.getLogger(__name__)


@dataclass
class TrialResult:
    """Result from executing a single trial."""

    trial_id: int
    """Trial identifier."""

    metric_value: float
    """Composite metric value (to maximize)."""

    quality: float
    """Quality score [0, 1]."""

    boundary_smoothness: float
    """Boundary smoothness [0, 1], lower is better."""

    temporal_consistency: float
    """Temporal consistency [0, 1], higher is better."""

    status: str
    """Trial status: 'complete', 'failed', 'pruned'."""

    error_message: Optional[str] = None
    """Error message if status is 'failed'."""

    duration_sec: float = 0.0
    """Trial execution duration in seconds."""


class TrialRunner:
    """Execute hyperparameter trials for watermark removal optimization.

    Handles trial workflow: load test frames, apply config, run pipeline,
    compute metrics, and report results. Supports early stopping via
    intermediate value reporting.
    """

    def __init__(self, test_frames: list[np.ndarray], region_bbox: tuple[int, int, int, int]) -> None:
        """Initialize trial runner.

        Args:
            test_frames: List of test video frames (HxWx3, uint8, BGR).
            region_bbox: Bounding box of watermark region (x, y, w, h).

        Raises:
            ValueError: If test_frames empty or region_bbox invalid.
        """
        if not test_frames:
            raise ValueError("test_frames cannot be empty")
        if len(test_frames) == 0:
            raise ValueError("test_frames list is empty")

        # Validate region_bbox
        if not isinstance(region_bbox, (tuple, list)) or len(region_bbox) != 4:
            raise ValueError("region_bbox must be (x, y, w, h)")

        x, y, w, h = region_bbox
        if x < 0 or y < 0 or w <= 0 or h <= 0:
            raise ValueError("region_bbox coordinates must be non-negative, dimensions positive")

        self.test_frames = test_frames
        self.region_bbox = region_bbox
        self.quality_monitor = QualityMonitor(enable_logging=False)

        logger.info(
            f"TrialRunner initialized: n_frames={len(test_frames)}, "
            f"region=({x}, {y}, {w}, {h})"
        )

    def run_trial(
        self,
        trial: Trial,
        base_config: ProcessConfig,
        optuna_optimizer: Any,
    ) -> TrialResult:
        """Execute a single optimization trial.

        Trial workflow:
        1. Define search space via trial.suggest_* calls
        2. Create ProcessConfig from trial parameters
        3. Compute synthetic metrics on test frames
        4. Compute composite metric
        5. Report intermediate values for pruning

        Args:
            trial: Optuna trial object.
            base_config: Base ProcessConfig for this trial.
            optuna_optimizer: OptunaOptimizer instance with define_search_space.

        Returns:
            TrialResult with metrics and status.

        Raises:
            TypeError: If trial not Trial, base_config not ProcessConfig.
            RuntimeError: If metric computation fails.
        """
        import time

        start_time = time.time()

        if not isinstance(trial, Trial):
            raise TypeError("trial must be optuna.trial.Trial")
        if not isinstance(base_config, ProcessConfig):
            raise TypeError("base_config must be ProcessConfig")

        try:
            # Step 1: Define search space
            trial_params = optuna_optimizer.define_search_space(trial)
            logger.debug(f"Trial {trial.number}: params={trial_params}")

            # Step 2: Create config from trial parameters
            trial_config = optuna_optimizer.config_from_trial_params(
                base_config, trial_params
            )

            # Step 3: Compute metrics on test frames
            metrics_list = []

            for frame_id, frame in enumerate(self.test_frames):
                # Simulate inpaint processing (synthetic metric)
                # In a real scenario, this would run the actual pipeline

                # Compute boundary smoothness
                boundary_smoothness = self.quality_monitor.compute_boundary_smoothness(
                    frame, self.region_bbox
                )

                # Simulate color consistency based on config
                # Frames with higher context_padding should have better consistency
                padding_factor = min(1.0, trial_config.context_padding / 50.0)
                color_consistency = max(
                    0.1, 1.0 - padding_factor * 0.3 + np.random.normal(0, 0.05)
                )
                color_consistency = np.clip(color_consistency, 0.0, 1.0)

                # Simulate temporal consistency
                temporal_consistency = None
                if frame_id > 0:
                    # Temporal smoothing improves consistency
                    alpha_factor = trial_config.temporal_smooth_alpha
                    base_temporal = 0.7 + alpha_factor * 0.2
                    temporal_consistency = np.clip(
                        base_temporal + np.random.normal(0, 0.05), 0.0, 1.0
                    )

                # Simulate inpaint quality
                # Optical flow weight improves quality
                flow_factor = trial_config.optical_flow_weight
                inpaint_quality = 0.6 + flow_factor * 0.3 + np.random.normal(0, 0.05)
                inpaint_quality = np.clip(inpaint_quality, 0.0, 1.0)

                # Compute frame metrics
                frame_metrics = self.quality_monitor.compute_frame_metrics(
                    frame_id=frame_id,
                    current_frame=frame,
                    inpainted_crop=frame[
                        self.region_bbox[1] : self.region_bbox[1] + self.region_bbox[3],
                        self.region_bbox[0] : self.region_bbox[0] + self.region_bbox[2],
                    ],
                    region_bbox=self.region_bbox,
                    original_frame=frame,
                )

                # Use synthetic values for optimization
                metrics_list.append(
                    {
                        "boundary_smoothness": boundary_smoothness,
                        "temporal_consistency": temporal_consistency or 0.7,
                        "inpaint_quality": inpaint_quality,
                    }
                )

            # Step 4: Aggregate metrics across frames
            if not metrics_list:
                raise RuntimeError("No metrics computed")

            # Use mean of metrics across frames
            avg_boundary_smoothness = float(
                np.mean([m["boundary_smoothness"] for m in metrics_list])
            )
            avg_temporal_consistency = float(
                np.mean([m["temporal_consistency"] for m in metrics_list])
            )
            avg_quality = float(
                np.mean([m["inpaint_quality"] for m in metrics_list])
            )

            # Compute composite metric
            composite_metric = optuna_optimizer.compute_composite_metric(
                quality=avg_quality,
                boundary_smoothness=avg_boundary_smoothness,
                temporal_consistency=avg_temporal_consistency,
            )

            # Step 5: Report intermediate values (for Hyperband pruning)
            trial.report(composite_metric, step=0)

            # Check if trial should be pruned
            if trial.should_prune():
                logger.info(f"Trial {trial.number} pruned by Hyperband")
                duration = time.time() - start_time
                return TrialResult(
                    trial_id=trial.number,
                    metric_value=composite_metric,
                    quality=avg_quality,
                    boundary_smoothness=avg_boundary_smoothness,
                    temporal_consistency=avg_temporal_consistency,
                    status="pruned",
                    duration_sec=duration,
                )

            duration = time.time() - start_time
            logger.info(
                f"Trial {trial.number} completed: "
                f"metric={composite_metric:.4f}, duration={duration:.2f}s"
            )

            return TrialResult(
                trial_id=trial.number,
                metric_value=composite_metric,
                quality=avg_quality,
                boundary_smoothness=avg_boundary_smoothness,
                temporal_consistency=avg_temporal_consistency,
                status="complete",
                duration_sec=duration,
            )

        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Trial {trial.number} failed: {e}")

            # Mark trial as failed in Optuna
            try:
                trial.report(float("-inf"), step=0)
            except Exception:
                pass

            return TrialResult(
                trial_id=trial.number,
                metric_value=float("-inf"),
                quality=0.0,
                boundary_smoothness=1.0,
                temporal_consistency=0.0,
                status="failed",
                error_message=str(e),
                duration_sec=duration,
            )

    def create_objective_function(
        self,
        base_config: ProcessConfig,
        optuna_optimizer: Any,
    ) -> Any:
        """Create objective function for Optuna optimization.

        The returned function can be passed to study.optimize().

        Args:
            base_config: Base ProcessConfig for trials.
            optuna_optimizer: OptunaOptimizer instance.

        Returns:
            Callable that takes a Trial and returns float metric.

        Raises:
            TypeError: If arguments invalid type.
        """
        if not isinstance(base_config, ProcessConfig):
            raise TypeError("base_config must be ProcessConfig")

        def objective(trial: Trial) -> float:
            """Objective function for Optuna."""
            result = self.run_trial(trial, base_config, optuna_optimizer)

            if result.status in ("failed", "pruned"):
                return float("-inf") if result.status == "failed" else result.metric_value

            return result.metric_value

        return objective
