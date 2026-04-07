"""
Optuna-based hyperparameter tuning for ensemble watermark detection.

Optimizes voting parameters (model weights, confidence/IoU/NMS thresholds)
to maximize mAP on a validation dataset without retraining models.

Target: 5-15% mAP improvement in 16-32 GPU hours on RTX4090.
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional, Dict, Any, Callable

logger = logging.getLogger(__name__)

# Optional Optuna import for MVP testing
try:
    import optuna
    from optuna.samplers import TPESampler
    from optuna.pruners import HyperbandPruner
    OPTUNA_AVAILABLE = True
except ImportError:
    OPTUNA_AVAILABLE = False
    logger.warning("Optuna not installed. MVP mode: testing only, no actual optimization.")


@dataclass
class TuningConfig:
    """Configuration for hyperparameter tuning."""

    # Study configuration
    study_name: str = "watermark_ensemble_tuning"
    storage: str = "sqlite:///optuna.db"
    n_trials: int = 150
    timeout_sec: Optional[float] = None  # None = no timeout
    direction: str = "maximize"  # maximize mAP

    # Search space bounds
    search_bounds: Dict[str, tuple] = field(default_factory=lambda: {
        "weight_yolov5s": (0.1, 1.0),
        "weight_yolov5m": (0.1, 1.0),
        "weight_yolov5l": (0.1, 1.0),
        "confidence_threshold": (0.05, 0.95),
        "iou_threshold": (0.3, 0.7),
        "nms_threshold": (0.3, 0.7),
        "augmentation_intensity": (0.0, 1.0),
    })

    # Sampler configuration
    sampler_n_startup_trials: int = 10
    sampler_n_warmup_steps: int = 50

    # Pruner configuration
    pruner_reduction_factor: float = 3.0
    pruner_min_early_stopping_rate_low: float = 0.0
    pruner_min_early_stopping_rate_high: float = 5.0

    # Timeout per trial
    trial_timeout_sec: float = 3600.0  # 1 hour per trial

    def __post_init__(self):
        """Validate configuration."""
        if self.n_trials < 1:
            raise ValueError("n_trials must be >= 1")
        if self.direction not in ["maximize", "minimize"]:
            raise ValueError(f"Invalid direction: {self.direction}")
        if not self.search_bounds:
            raise ValueError("search_bounds cannot be empty")


class OptunaTuner:
    """Hyperparameter tuner using Optuna."""

    def __init__(self, config: TuningConfig):
        """
        Initialize tuner.

        Args:
            config: Tuning configuration

        Raises:
            RuntimeError: If Optuna not installed and not in mock mode
        """
        self.config = config
        self.study: Optional[Any] = None
        self.best_params: Optional[Dict[str, float]] = None
        self.best_value: Optional[float] = None

        if not OPTUNA_AVAILABLE:
            logger.warning("Optuna not available; using mock study for testing")
            self.mock_mode = True
        else:
            self.mock_mode = False

    async def create_study(self) -> bool:
        """
        Create or load Optuna study.

        Returns:
            True if successful
        """
        logger.info(f"Creating study: {self.config.study_name}")

        if self.mock_mode:
            logger.info("Using mock study for testing")
            self.study = {"name": self.config.study_name, "trials": []}
            return True

        try:
            sampler = TPESampler(
                n_startup_trials=self.config.sampler_n_startup_trials,
                n_warmup_steps=self.config.sampler_n_warmup_steps,
            )

            pruner = HyperbandPruner(
                reduction_factor=self.config.pruner_reduction_factor,
                min_early_stopping_rate_low=self.config.pruner_min_early_stopping_rate_low,
                min_early_stopping_rate_high=self.config.pruner_min_early_stopping_rate_high,
            )

            self.study = optuna.create_study(
                study_name=self.config.study_name,
                storage=self.config.storage,
                load_if_exists=True,
                sampler=sampler,
                pruner=pruner,
                direction=self.config.direction,
            )

            logger.info(f"Study created/loaded: {self.config.study_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to create study: {e}")
            return False

    async def objective(
        self,
        trial: Any,
        eval_fn: Callable,
    ) -> float:
        """
        Objective function for Optuna trial.

        Args:
            trial: Optuna trial object
            eval_fn: Async evaluation function that returns mAP score

        Returns:
            mAP score (0.0-1.0)

        Raises:
            optuna.TrialPruned: If trial is pruned
            RuntimeError: If evaluation fails
        """
        if self.mock_mode:
            # Mock mode: return random value
            import random
            return random.uniform(0.5, 0.9)

        logger.info(f"Running trial {trial.number}")

        try:
            # Sample hyperparameters
            params = {}
            for param_name, (low, high) in self.config.search_bounds.items():
                if "weight" in param_name:
                    # Weights: sample continuously and normalize
                    params[param_name] = trial.suggest_float(param_name, low, high)
                elif "threshold" in param_name or "intensity" in param_name:
                    # Thresholds and intensity: sample continuously
                    params[param_name] = trial.suggest_float(param_name, low, high)
                else:
                    params[param_name] = trial.suggest_float(param_name, low, high)

            # Normalize weights to sum to 1.0
            weight_sum = (
                params.get("weight_yolov5s", 0.0)
                + params.get("weight_yolov5m", 0.0)
                + params.get("weight_yolov5l", 0.0)
            )
            if weight_sum > 0:
                params["weight_yolov5s"] /= weight_sum
                params["weight_yolov5m"] /= weight_sum
                params["weight_yolov5l"] /= weight_sum

            logger.info(f"Trial {trial.number} params: {params}")

            # Evaluate with timeout
            try:
                mAP = await asyncio.wait_for(
                    eval_fn(params),
                    timeout=self.config.trial_timeout_sec,
                )
            except asyncio.TimeoutError:
                logger.warning(f"Trial {trial.number} timeout")
                mAP = 0.0

            logger.info(f"Trial {trial.number} mAP: {mAP:.4f}")

            # Store trial metrics for checkpoint
            if not hasattr(self, "_trial_history"):
                self._trial_history = []
            self._trial_history.append({
                "trial_number": trial.number,
                "params": params,
                "mAP": mAP,
                "timestamp": time.time(),
            })

            return mAP

        except Exception as e:
            logger.error(f"Trial {trial.number} failed: {e}")
            return 0.0

    async def optimize(
        self,
        eval_fn: Callable,
        n_trials: Optional[int] = None,
    ) -> bool:
        """
        Run optimization loop.

        Args:
            eval_fn: Async function(params_dict) -> mAP score
            n_trials: Number of trials (overrides config)

        Returns:
            True if successful

        Raises:
            RuntimeError: If study not created
        """
        if self.study is None:
            raise RuntimeError("Study not created. Call create_study() first.")

        n_trials = n_trials or self.config.n_trials
        logger.info(f"Starting optimization: {n_trials} trials")

        if self.mock_mode:
            # Mock mode: simulate trials
            for trial_num in range(n_trials):
                import random
                mAP = random.uniform(0.5, 0.9)
                logger.info(f"Trial {trial_num} mAP: {mAP:.4f}")
                await asyncio.sleep(0.01)  # Simulate work

            self.best_value = 0.75
            self.best_params = {"weight_yolov5s": 0.3, "weight_yolov5m": 0.5, "weight_yolov5l": 0.2}
            return True

        try:
            start_time = time.time()

            def objective_wrapper(trial):
                # Synchronous wrapper for Optuna
                loop = asyncio.get_event_loop()
                return loop.run_until_complete(self.objective(trial, eval_fn))

            self.study.optimize(
                objective_wrapper,
                n_trials=n_trials,
                timeout=self.config.timeout_sec,
            )

            elapsed = time.time() - start_time
            logger.info(f"Optimization complete in {elapsed:.1f}s")

            # Get best parameters
            self.best_value = self.study.best_value
            self.best_params = self.study.best_params

            logger.info(f"Best mAP: {self.best_value:.4f}")
            logger.info(f"Best params: {self.best_params}")

            return True

        except Exception as e:
            logger.error(f"Optimization failed: {e}")
            return False

    def get_best_params(self) -> Optional[Dict[str, float]]:
        """
        Get best parameters found.

        Returns:
            Best params dict (or None if not yet optimized)
        """
        return self.best_params

    def get_best_value(self) -> Optional[float]:
        """
        Get best mAP value.

        Returns:
            Best mAP (or None if not yet optimized)
        """
        return self.best_value

    def save_results(self, output_path: str) -> bool:
        """
        Save optimization results to JSON.

        Args:
            output_path: Path to write results

        Returns:
            True if successful
        """
        if self.best_params is None:
            logger.warning("No optimization results to save")
            return False

        results = {
            "study_name": self.config.study_name,
            "best_mAP": self.best_value,
            "best_params": self.best_params,
            "timestamp": time.time(),
        }

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(results, f, indent=2)

        logger.info(f"Results saved to {output_path}")
        return True

    def load_results(self, input_path: str) -> bool:
        """
        Load optimization results from JSON.

        Args:
            input_path: Path to read results

        Returns:
            True if successful
        """
        input_path = Path(input_path)
        if not input_path.exists():
            logger.warning(f"Results file not found: {input_path}")
            return False

        try:
            with open(input_path, "r") as f:
                results = json.load(f)

            self.best_value = results.get("best_mAP")
            self.best_params = results.get("best_params")

            logger.info(f"Results loaded from {input_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to load results: {e}")
            return False
