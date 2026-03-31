"""Optuna-based hyperparameter optimization for watermark removal system."""

import logging
from typing import Any, Callable, Optional

import optuna
from optuna.pruners import HyperbandPruner
from optuna.samplers import TPESampler
from optuna.study import Study
from optuna.trial import Trial

from src.watermark_removal.core.types import ProcessConfig

logger = logging.getLogger(__name__)


class OptunaOptimizer:
    """Manage Optuna study for hyperparameter tuning.

    Handles study creation, configuration, and trial execution using
    Tree-structured Parzen Estimator (TPE) sampling with Hyperband pruning.
    """

    def __init__(
        self,
        study_name: str = "watermark_ensemble_tuning",
        storage: str = "sqlite:///optuna.db",
        n_trials: int = 150,
        seed: int = 42,
    ) -> None:
        """Initialize Optuna optimizer.

        Args:
            study_name: Name for the Optuna study (used for tracking).
            storage: Storage backend (SQLite path or database URI).
            n_trials: Total number of trials to execute.
            seed: Random seed for reproducibility.

        Raises:
            ValueError: If n_trials < 1.
        """
        if n_trials < 1:
            raise ValueError("n_trials must be >= 1")

        self.study_name = study_name
        self.storage = storage
        self.n_trials = n_trials
        self.seed = seed
        self._study: Optional[Study] = None

        logger.info(
            f"OptunaOptimizer initialized: study={study_name}, "
            f"n_trials={n_trials}, storage={storage}"
        )

    def create_study(
        self,
        load_if_exists: bool = False,
        direction: str = "maximize",
    ) -> Study:
        """Create or load Optuna study.

        Args:
            load_if_exists: If True, load existing study. If False, create new.
            direction: Optimization direction ("maximize" or "minimize").

        Returns:
            Optuna Study object.

        Raises:
            RuntimeError: If study creation fails.
        """
        try:
            # Create sampler with TPE algorithm
            sampler = TPESampler(seed=self.seed)

            # Create pruner with Hyperband algorithm for early stopping
            pruner = HyperbandPruner()

            # Create study with sampler and pruner
            study = optuna.create_study(
                study_name=self.study_name,
                storage=self.storage,
                sampler=sampler,
                pruner=pruner,
                load_if_exists=load_if_exists,
                direction=direction,
            )

            self._study = study
            logger.info(
                f"Study created: name={study.study_name}, "
                f"direction={direction}, sampler=TPE, pruner=Hyperband"
            )

            return study

        except Exception as e:
            logger.error(f"Failed to create study: {e}")
            raise RuntimeError(f"Study creation failed: {e}") from e

    def get_study(self) -> Optional[Study]:
        """Get current Optuna study.

        Returns:
            Study object or None if not created.
        """
        return self._study

    def define_search_space(self, trial: Trial) -> dict[str, Any]:
        """Define hyperparameter search space for a trial.

        Search space (5 hyperparameters):
        - temporal_smooth_alpha: [0.0, 1.0], default 0.3
        - context_padding: [0, 50], default 16
        - detection_confidence: [0.1, 0.9], default 0.5
        - checkpoint_frequency: [1, 100], default 10
        - optical_flow_weight: [0.0, 1.0], default 0.0

        Args:
            trial: Optuna trial object.

        Returns:
            Dictionary mapping parameter names to suggested values.

        Raises:
            TypeError: If trial is None.
        """
        if trial is None:
            raise TypeError("trial cannot be None")

        # Temporal smoothing: alpha blending factor
        temporal_smooth_alpha = trial.suggest_float(
            "temporal_smooth_alpha",
            low=0.0,
            high=1.0,
            step=0.05,
        )

        # Context padding: pixels around watermark bbox
        context_padding = trial.suggest_int(
            "context_padding",
            low=0,
            high=50,
            step=5,
        )

        # Detection confidence threshold
        detection_confidence = trial.suggest_float(
            "detection_confidence",
            low=0.1,
            high=0.9,
            step=0.05,
        )

        # Checkpoint frequency: save every N frames
        checkpoint_frequency = trial.suggest_int(
            "checkpoint_frequency",
            low=1,
            high=100,
            step=5,
        )

        # Optical flow weight in ensemble
        optical_flow_weight = trial.suggest_float(
            "optical_flow_weight",
            low=0.0,
            high=1.0,
            step=0.05,
        )

        return {
            "temporal_smooth_alpha": temporal_smooth_alpha,
            "context_padding": context_padding,
            "detection_confidence": detection_confidence,
            "checkpoint_frequency": checkpoint_frequency,
            "optical_flow_weight": optical_flow_weight,
        }

    def compute_composite_metric(
        self,
        quality: float,
        boundary_smoothness: float,
        temporal_consistency: float,
        penalty_weight: float = 0.1,
    ) -> float:
        """Compute composite optimization metric.

        Formula: quality + boundary_smoothness - penalty_weight * (1 - temporal_consistency)

        Args:
            quality: Quality score [0, 1].
            boundary_smoothness: Boundary smoothness [0, 1], lower is better.
            temporal_consistency: Temporal consistency [0, 1], higher is better.
            penalty_weight: Weight for temporal consistency penalty.

        Returns:
            Composite metric to maximize.

        Raises:
            ValueError: If metrics outside valid ranges.
        """
        # Validate inputs
        if not (0.0 <= quality <= 1.0):
            raise ValueError(f"quality must be in [0, 1], got {quality}")
        if not (0.0 <= boundary_smoothness <= 1.0):
            raise ValueError(
                f"boundary_smoothness must be in [0, 1], got {boundary_smoothness}"
            )
        if not (0.0 <= temporal_consistency <= 1.0):
            raise ValueError(
                f"temporal_consistency must be in [0, 1], got {temporal_consistency}"
            )
        if penalty_weight < 0.0:
            raise ValueError(f"penalty_weight must be >= 0, got {penalty_weight}")

        # Composite metric: higher quality and smoothness, lower temporal inconsistency
        # Note: boundary_smoothness is already a cost (lower is better), so we subtract it
        # temporal_consistency is a benefit (higher is better), so we subtract its negation
        metric = quality - boundary_smoothness + temporal_consistency - penalty_weight

        return float(metric)

    def optimize(
        self,
        objective_func: Callable[[Trial], float],
        n_jobs: int = 1,
        show_progress_bar: bool = True,
        gc_each_trial: bool = False,
    ) -> Optional[Trial]:
        """Run optimization using the study.

        Args:
            objective_func: Function that takes a trial and returns a metric value.
            n_jobs: Number of parallel jobs (1 = sequential).
            show_progress_bar: Show progress bar during optimization.
            gc_each_trial: Garbage collect after each trial.

        Returns:
            Best trial found, or None if optimization failed.

        Raises:
            RuntimeError: If study not initialized or objective function fails.
        """
        if self._study is None:
            raise RuntimeError("Study not initialized. Call create_study() first.")

        if objective_func is None:
            raise ValueError("objective_func cannot be None")

        try:
            logger.info(
                f"Starting optimization: n_trials={self.n_trials}, "
                f"n_jobs={n_jobs}, show_progress={show_progress_bar}"
            )

            self._study.optimize(
                objective_func,
                n_trials=self.n_trials,
                n_jobs=n_jobs,
                show_progress_bar=show_progress_bar,
                gc_each_trial=gc_each_trial,
            )

            best_trial = self._study.best_trial
            logger.info(
                f"Optimization complete: best_value={best_trial.value:.4f}, "
                f"best_params={best_trial.params}"
            )

            return best_trial

        except Exception as e:
            logger.error(f"Optimization failed: {e}")
            raise RuntimeError(f"Optimization execution failed: {e}") from e

    def get_best_trial(self) -> Optional[Trial]:
        """Get the best trial found so far.

        Returns:
            Best trial or None if no trials completed.
        """
        if self._study is None:
            return None

        try:
            return self._study.best_trial
        except Exception:
            return None

    def get_best_params(self) -> Optional[dict[str, Any]]:
        """Get parameters of the best trial.

        Returns:
            Dictionary of best parameters, or None if unavailable.
        """
        best_trial = self.get_best_trial()
        return best_trial.params if best_trial else None

    def get_best_value(self) -> Optional[float]:
        """Get the best metric value found.

        Returns:
            Best metric value, or None if unavailable.
        """
        best_trial = self.get_best_trial()
        return best_trial.value if best_trial else None

    def get_trials_dataframe(self) -> Any:
        """Get all trials as a pandas DataFrame.

        Returns:
            DataFrame with trial data (empty if no study).

        Raises:
            ImportError: If pandas not available.
        """
        if self._study is None:
            import pandas as pd
            return pd.DataFrame()

        try:
            return self._study.trials_dataframe()
        except Exception as e:
            logger.error(f"Failed to get trials DataFrame: {e}")
            raise

    def config_from_trial_params(
        self,
        base_config: ProcessConfig,
        trial_params: dict[str, Any],
    ) -> ProcessConfig:
        """Create ProcessConfig from trial hyperparameters.

        Merges trial parameters with base configuration, overriding
        specific fields with trial values.

        Args:
            base_config: Base ProcessConfig to start from.
            trial_params: Hyperparameters from trial.suggest_* calls.

        Returns:
            New ProcessConfig with trial parameters applied.

        Raises:
            TypeError: If base_config not ProcessConfig or trial_params not dict.
        """
        if not isinstance(base_config, ProcessConfig):
            raise TypeError("base_config must be ProcessConfig")
        if not isinstance(trial_params, dict):
            raise TypeError("trial_params must be dict")

        # Create a copy of config as dict
        config_dict = {
            "video_path": base_config.video_path,
            "mask_path": base_config.mask_path,
            "output_dir": base_config.output_dir,
            "inpaint": base_config.inpaint,
            "context_padding": trial_params.get(
                "context_padding", base_config.context_padding
            ),
            "temporal_smooth_alpha": trial_params.get(
                "temporal_smooth_alpha", base_config.temporal_smooth_alpha
            ),
            "optical_flow_weight": trial_params.get(
                "optical_flow_weight", base_config.optical_flow_weight
            ),
        }

        # Add remaining config fields
        for field_name in [
            "target_inpaint_size",
            "batch_size",
            "timeout",
            "output_codec",
            "output_crf",
            "output_fps",
            "keep_intermediate",
            "verbose",
            "comfyui_host",
            "comfyui_port",
            "blend_feather_width",
            "skip_errors_in_preprocessing",
            "skip_errors_in_postprocessing",
            "temporal_smooth_enabled",
            "use_adaptive_temporal_smoothing",
            "adaptive_motion_threshold",
            "use_poisson_blending",
            "poisson_max_iterations",
            "poisson_tolerance",
            "use_watermark_tracker",
            "yolo_model_path",
            "yolo_confidence_threshold",
            "tracker_smoothing_factor",
            "use_checkpoints",
            "crop_region",
            "optical_flow_enabled",
            "optical_flow_resolution",
            "ensemble_detection_enabled",
            "ensemble_models",
            "ensemble_voting_mode",
            "ensemble_iou_threshold",
            "ensemble_nms_threshold",
            "ensemble_model_accuracies",
            "streaming_queue_size",
            "streaming_result_ttl_sec",
            "label_studio_enabled",
            "label_studio_url",
            "label_studio_api_key",
            "label_studio_project_id",
            "label_studio_wait_timeout_sec",
            "optuna_enabled",
            "optuna_study_name",
            "optuna_storage",
            "optuna_n_trials",
            "optuna_search_bounds",
        ]:
            config_dict[field_name] = getattr(base_config, field_name)

        return ProcessConfig(**config_dict)
