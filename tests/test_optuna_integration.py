"""Tests for Optuna hyperparameter optimization integration."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from optuna.trial import Trial

from src.watermark_removal.core.types import ProcessConfig
from src.watermark_removal.optimization.optuna_optimizer import OptunaOptimizer
from src.watermark_removal.optimization.trial_runner import TrialResult, TrialRunner


class TestOptunaOptimizer:
    """Unit tests for OptunaOptimizer class."""

    def test_optuna_optimizer_init(self):
        """Test OptunaOptimizer initialization."""
        optimizer = OptunaOptimizer(
            study_name="test_study",
            storage="sqlite:///test.db",
            n_trials=50,
            seed=42,
        )

        assert optimizer.study_name == "test_study"
        assert optimizer.storage == "sqlite:///test.db"
        assert optimizer.n_trials == 50
        assert optimizer.seed == 42
        assert optimizer._study is None

    def test_optuna_optimizer_init_invalid_trials(self):
        """Test that ValueError raised if n_trials < 1."""
        with pytest.raises(ValueError, match="n_trials must be >= 1"):
            OptunaOptimizer(n_trials=0)

    def test_optuna_optimizer_create_study(self, tmp_path):
        """Test study creation with TPESampler and HyperbandPruner."""
        db_path = str(tmp_path / "optuna.db")
        storage = f"sqlite:///{db_path}"

        optimizer = OptunaOptimizer(
            study_name="test_study",
            storage=storage,
            n_trials=10,
            seed=42,
        )

        study = optimizer.create_study(load_if_exists=False, direction="maximize")

        assert study is not None
        assert study.study_name == "test_study"
        assert study.direction.name == "MAXIMIZE"
        assert optimizer._study is study

    def test_optuna_optimizer_get_study(self):
        """Test getting study after creation."""
        optimizer = OptunaOptimizer(n_trials=10)

        # Before creation
        assert optimizer.get_study() is None

    def test_optuna_optimizer_define_search_space(self):
        """Test search space definition."""
        optimizer = OptunaOptimizer(n_trials=10)

        # Mock trial
        mock_trial = MagicMock(spec=Trial)
        mock_trial.suggest_float.side_effect = [0.5, 0.2, 0.8]
        mock_trial.suggest_int.side_effect = [25, 50]

        # Mock the suggest methods to return values in order
        call_count = {"float": 0, "int": 0}

        def suggest_float_impl(name, low, high, step=None):
            values = [0.5, 0.8, 0.5]
            val = values[call_count["float"]]
            call_count["float"] += 1
            return val

        def suggest_int_impl(name, low, high, step=None):
            values = [25, 50]
            val = values[call_count["int"]]
            call_count["int"] += 1
            return val

        mock_trial.suggest_float.side_effect = suggest_float_impl
        mock_trial.suggest_int.side_effect = suggest_int_impl

        search_space = optimizer.define_search_space(mock_trial)

        assert isinstance(search_space, dict)
        assert "temporal_smooth_alpha" in search_space
        assert "context_padding" in search_space
        assert "detection_confidence" in search_space
        assert "checkpoint_frequency" in search_space
        assert "optical_flow_weight" in search_space

    def test_optuna_optimizer_search_space_with_real_trial(self, tmp_path):
        """Test search space definition with real trial."""
        db_path = str(tmp_path / "optuna.db")
        storage = f"sqlite:///{db_path}"

        optimizer = OptunaOptimizer(
            study_name="test_study",
            storage=storage,
            n_trials=10,
        )

        study = optimizer.create_study(load_if_exists=False)

        # Create a trial manually
        trial = study.ask()

        search_space = optimizer.define_search_space(trial)

        assert isinstance(search_space, dict)
        assert len(search_space) == 5
        assert 0.0 <= search_space["temporal_smooth_alpha"] <= 1.0
        assert 0 <= search_space["context_padding"] <= 50
        assert 0.1 <= search_space["detection_confidence"] <= 0.9
        assert 1 <= search_space["checkpoint_frequency"] <= 100
        assert 0.0 <= search_space["optical_flow_weight"] <= 1.0

    def test_optuna_optimizer_define_search_space_none_trial(self):
        """Test that TypeError raised if trial is None."""
        optimizer = OptunaOptimizer(n_trials=10)

        with pytest.raises(TypeError, match="trial cannot be None"):
            optimizer.define_search_space(None)

    def test_optuna_optimizer_composite_metric_valid(self):
        """Test composite metric calculation with valid inputs."""
        optimizer = OptunaOptimizer(n_trials=10)

        metric = optimizer.compute_composite_metric(
            quality=0.9,
            boundary_smoothness=0.2,
            temporal_consistency=0.85,
            penalty_weight=0.1,
        )

        # Formula: quality - boundary_smoothness + temporal_consistency - penalty_weight
        expected = 0.9 - 0.2 + 0.85 - 0.1
        assert abs(metric - expected) < 1e-6

    def test_optuna_optimizer_composite_metric_boundary_values(self):
        """Test composite metric with boundary values."""
        optimizer = OptunaOptimizer(n_trials=10)

        # All metrics at 0
        metric_min = optimizer.compute_composite_metric(0.0, 1.0, 0.0, 0.1)
        assert metric_min < 0.0

        # All metrics at 1
        metric_max = optimizer.compute_composite_metric(1.0, 0.0, 1.0, 0.1)
        assert metric_max > 1.8

    def test_optuna_optimizer_composite_metric_invalid_quality(self):
        """Test that ValueError raised if quality outside [0, 1]."""
        optimizer = OptunaOptimizer(n_trials=10)

        with pytest.raises(ValueError, match="quality must be in"):
            optimizer.compute_composite_metric(1.5, 0.5, 0.5)

    def test_optuna_optimizer_composite_metric_invalid_smoothness(self):
        """Test that ValueError raised if boundary_smoothness outside [0, 1]."""
        optimizer = OptunaOptimizer(n_trials=10)

        with pytest.raises(ValueError, match="boundary_smoothness must be in"):
            optimizer.compute_composite_metric(0.8, 1.5, 0.5)

    def test_optuna_optimizer_composite_metric_invalid_temporal(self):
        """Test that ValueError raised if temporal_consistency outside [0, 1]."""
        optimizer = OptunaOptimizer(n_trials=10)

        with pytest.raises(ValueError, match="temporal_consistency must be in"):
            optimizer.compute_composite_metric(0.8, 0.5, -0.5)

    def test_optuna_optimizer_config_from_trial_params(self, base_config_dict):
        """Test creating config from trial parameters."""
        optimizer = OptunaOptimizer(n_trials=10)

        base_config = ProcessConfig(**base_config_dict)
        trial_params = {
            "temporal_smooth_alpha": 0.5,
            "context_padding": 30,
            "optical_flow_weight": 0.7,
        }

        new_config = optimizer.config_from_trial_params(base_config, trial_params)

        assert isinstance(new_config, ProcessConfig)
        assert new_config.temporal_smooth_alpha == 0.5
        assert new_config.context_padding == 30
        assert new_config.optical_flow_weight == 0.7

    def test_optuna_optimizer_config_from_trial_params_preserves_base(self, base_config_dict):
        """Test that base config fields are preserved."""
        optimizer = OptunaOptimizer(n_trials=10)

        base_config = ProcessConfig(
            **{**base_config_dict, "batch_size": 8, "timeout": 500.0}
        )
        trial_params = {"context_padding": 25}

        new_config = optimizer.config_from_trial_params(base_config, trial_params)

        assert new_config.batch_size == 8
        assert new_config.timeout == 500.0
        assert new_config.context_padding == 25

    def test_optuna_optimizer_config_from_trial_params_invalid_config(self):
        """Test that TypeError raised if base_config not ProcessConfig."""
        optimizer = OptunaOptimizer(n_trials=10)

        with pytest.raises(TypeError, match="base_config must be ProcessConfig"):
            optimizer.config_from_trial_params({}, {})

    def test_optuna_optimizer_config_from_trial_params_invalid_params(self, base_config_dict):
        """Test that TypeError raised if trial_params not dict."""
        optimizer = OptunaOptimizer(n_trials=10)

        base_config = ProcessConfig(**base_config_dict)

        with pytest.raises(TypeError, match="trial_params must be dict"):
            optimizer.config_from_trial_params(base_config, [])


class TestTrialRunner:
    """Unit tests for TrialRunner class."""

    @pytest.fixture
    def test_frames(self):
        """Create synthetic test frames."""
        frames = [
            np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)
            for _ in range(3)
        ]
        return frames

    def test_trial_runner_init(self, test_frames):
        """Test TrialRunner initialization."""
        runner = TrialRunner(test_frames, region_bbox=(100, 100, 50, 50))

        assert len(runner.test_frames) == 3
        assert runner.region_bbox == (100, 100, 50, 50)

    def test_trial_runner_init_empty_frames(self):
        """Test that ValueError raised if no test frames."""
        with pytest.raises(ValueError, match="test_frames"):
            TrialRunner([], region_bbox=(0, 0, 10, 10))

    def test_trial_runner_init_invalid_bbox(self, test_frames):
        """Test that ValueError raised if bbox invalid."""
        # Invalid bbox format
        with pytest.raises(ValueError, match="region_bbox must be"):
            TrialRunner(test_frames, region_bbox=(0, 0, 10))

    def test_trial_runner_init_invalid_bbox_coordinates(self, test_frames):
        """Test that ValueError raised if bbox coordinates invalid."""
        with pytest.raises(ValueError, match="coordinates must be non-negative"):
            TrialRunner(test_frames, region_bbox=(-1, 0, 10, 10))

    def test_trial_runner_init_invalid_bbox_dimensions(self, test_frames):
        """Test that ValueError raised if bbox dimensions invalid."""
        with pytest.raises(ValueError, match="dimensions positive"):
            TrialRunner(test_frames, region_bbox=(0, 0, 0, 10))

    def test_trial_runner_run_trial_complete(self, test_frames, base_config_dict, tmp_path):
        """Test running a trial to completion."""
        db_path = str(tmp_path / "optuna.db")
        storage = f"sqlite:///{db_path}"

        optimizer = OptunaOptimizer(
            study_name="test_study",
            storage=storage,
            n_trials=2,
        )
        study = optimizer.create_study(load_if_exists=False)

        base_config = ProcessConfig(**base_config_dict)
        runner = TrialRunner(test_frames, region_bbox=(50, 50, 100, 100))

        # Create a trial
        trial = study.ask()

        result = runner.run_trial(trial, base_config, optimizer)

        assert isinstance(result, TrialResult)
        assert result.status == "complete"
        assert result.trial_id == trial.number
        assert 0.0 <= result.quality <= 1.0
        assert 0.0 <= result.boundary_smoothness <= 1.0
        assert 0.0 <= result.temporal_consistency <= 1.0
        assert result.duration_sec >= 0.0

    def test_trial_runner_run_trial_invalid_trial(self, test_frames, base_config_dict):
        """Test that TypeError raised if trial not Trial."""
        optimizer = OptunaOptimizer(n_trials=2)
        base_config = ProcessConfig(**base_config_dict)
        runner = TrialRunner(test_frames, region_bbox=(50, 50, 100, 100))

        with pytest.raises(TypeError, match="trial must be optuna"):
            runner.run_trial(None, base_config, optimizer)

    def test_trial_runner_run_trial_invalid_config(self, test_frames):
        """Test that TypeError raised if base_config not ProcessConfig."""
        optimizer = OptunaOptimizer(n_trials=2)
        runner = TrialRunner(test_frames, region_bbox=(50, 50, 100, 100))

        mock_trial = MagicMock(spec=Trial)
        mock_trial.number = 0

        with pytest.raises(TypeError, match="base_config must be ProcessConfig"):
            runner.run_trial(mock_trial, {}, optimizer)

    def test_trial_runner_create_objective_function(self, test_frames, base_config_dict, tmp_path):
        """Test creating objective function for Optuna."""
        db_path = str(tmp_path / "optuna.db")
        storage = f"sqlite:///{db_path}"

        optimizer = OptunaOptimizer(
            study_name="test_study",
            storage=storage,
            n_trials=2,
        )
        study = optimizer.create_study(load_if_exists=False)

        base_config = ProcessConfig(**base_config_dict)
        runner = TrialRunner(test_frames, region_bbox=(50, 50, 100, 100))

        objective_func = runner.create_objective_function(base_config, optimizer)

        assert callable(objective_func)

        # Call objective function with a real trial
        trial = study.ask()
        value = objective_func(trial)

        assert isinstance(value, float)
        assert not np.isnan(value)

    def test_trial_runner_objective_function_with_multiple_trials(
        self, test_frames, base_config_dict, tmp_path
    ):
        """Test objective function with multiple trials."""
        db_path = str(tmp_path / "optuna.db")
        storage = f"sqlite:///{db_path}"

        optimizer = OptunaOptimizer(
            study_name="test_study",
            storage=storage,
            n_trials=5,
        )
        study = optimizer.create_study(load_if_exists=False)

        base_config = ProcessConfig(**base_config_dict)
        runner = TrialRunner(test_frames, region_bbox=(50, 50, 100, 100))
        objective_func = runner.create_objective_function(base_config, optimizer)

        # Run multiple trials
        results = []
        for _ in range(3):
            trial = study.ask()
            value = objective_func(trial)
            results.append(value)

        assert len(results) == 3
        assert all(isinstance(v, float) for v in results)


class TestOptunaIntegration:
    """Integration tests for Optuna optimization pipeline."""

    @pytest.fixture
    def test_frames(self):
        """Create synthetic test frames."""
        frames = [
            np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)
            for _ in range(5)
        ]
        return frames

    def test_full_optimization_pipeline(self, test_frames, base_config_dict, tmp_path):
        """Test full optimization pipeline with 10 trials."""
        db_path = str(tmp_path / "optuna.db")
        storage = f"sqlite:///{db_path}"

        # Create optimizer
        optimizer = OptunaOptimizer(
            study_name="full_test",
            storage=storage,
            n_trials=10,
            seed=42,
        )

        study = optimizer.create_study(load_if_exists=False, direction="maximize")

        # Create base config and runner
        base_config = ProcessConfig(**base_config_dict)
        runner = TrialRunner(test_frames, region_bbox=(50, 50, 100, 100))

        objective_func = runner.create_objective_function(base_config, optimizer)

        # Run optimization
        best_trial = optimizer.optimize(
            objective_func,
            n_jobs=1,
            show_progress_bar=False,
        )

        assert best_trial is not None
        assert best_trial.number >= 0
        assert isinstance(best_trial.value, float)

    def test_optimization_respects_n_trials(self, test_frames, base_config_dict, tmp_path):
        """Test that optimization respects n_trials parameter."""
        db_path = str(tmp_path / "optuna.db")
        storage = f"sqlite:///{db_path}"

        optimizer = OptunaOptimizer(
            study_name="trial_count_test",
            storage=storage,
            n_trials=7,
            seed=42,
        )

        study = optimizer.create_study(load_if_exists=False)

        base_config = ProcessConfig(**base_config_dict)
        runner = TrialRunner(test_frames, region_bbox=(50, 50, 100, 100))
        objective_func = runner.create_objective_function(base_config, optimizer)

        optimizer.optimize(objective_func, n_jobs=1, show_progress_bar=False)

        # Check that exactly 7 trials were executed
        assert len(study.trials) == 7

    def test_optimization_finds_best_trial(self, test_frames, base_config_dict, tmp_path):
        """Test that optimization finds a best trial."""
        db_path = str(tmp_path / "optuna.db")
        storage = f"sqlite:///{db_path}"

        optimizer = OptunaOptimizer(
            study_name="best_trial_test",
            storage=storage,
            n_trials=10,
        )

        study = optimizer.create_study(load_if_exists=False)

        base_config = ProcessConfig(**base_config_dict)
        runner = TrialRunner(test_frames, region_bbox=(50, 50, 100, 100))
        objective_func = runner.create_objective_function(base_config, optimizer)

        optimizer.optimize(objective_func, n_jobs=1, show_progress_bar=False)

        best_params = optimizer.get_best_params()
        best_value = optimizer.get_best_value()

        assert best_params is not None
        assert isinstance(best_params, dict)
        assert best_value is not None
        assert isinstance(best_value, float)

    def test_metric_reporting_and_pruning(self, test_frames, base_config_dict, tmp_path):
        """Test that metrics are reported correctly for pruning."""
        db_path = str(tmp_path / "optuna.db")
        storage = f"sqlite:///{db_path}"

        optimizer = OptunaOptimizer(
            study_name="pruning_test",
            storage=storage,
            n_trials=15,
            seed=42,
        )

        study = optimizer.create_study(load_if_exists=False)

        base_config = ProcessConfig(**base_config_dict)
        runner = TrialRunner(test_frames, region_bbox=(50, 50, 100, 100))
        objective_func = runner.create_objective_function(base_config, optimizer)

        optimizer.optimize(objective_func, n_jobs=1, show_progress_bar=False)

        # Check that some trials may have been pruned or completed
        completed_trials = [t for t in study.trials if t.state.name == "COMPLETE"]
        assert len(completed_trials) > 0

    def test_backward_compatibility_disabled_by_default(self, base_config_dict):
        """Test that Optuna is disabled by default in config."""
        config = ProcessConfig(**base_config_dict)

        assert config.optuna_enabled is False
        assert config.optuna_n_trials == 150
        assert config.optuna_study_name == "watermark_ensemble_tuning"

    def test_graceful_error_handling_in_trial(self, test_frames, base_config_dict, tmp_path):
        """Test graceful error handling when trial execution fails."""
        db_path = str(tmp_path / "optuna.db")
        storage = f"sqlite:///{db_path}"

        optimizer = OptunaOptimizer(
            study_name="error_test",
            storage=storage,
            n_trials=3,
        )

        study = optimizer.create_study(load_if_exists=False)

        # Create a base config
        base_config = ProcessConfig(**base_config_dict)

        # Create runner with very small frames to trigger edge cases
        small_frames = [np.zeros((10, 10, 3), dtype=np.uint8) for _ in range(2)]
        runner = TrialRunner(small_frames, region_bbox=(0, 0, 5, 5))

        objective_func = runner.create_objective_function(base_config, optimizer)

        # Run optimization - should not raise exception
        try:
            optimizer.optimize(objective_func, n_jobs=1, show_progress_bar=False)
            # If we get here, optimization completed without exception
            assert True
        except Exception as e:
            # Even if there's an exception, it should be caught gracefully
            pytest.fail(f"Optimization should handle errors gracefully: {e}")

    def test_search_space_validation(self, tmp_path):
        """Test that search space bounds are validated."""
        db_path = str(tmp_path / "optuna.db")
        storage = f"sqlite:///{db_path}"

        # Invalid bounds (low >= high) should be caught by ProcessConfig validation
        config_dict = {
            "video_path": "/tmp/video.mp4",
            "mask_path": "/tmp/mask.png",
            "output_dir": "/tmp/output",
            "optuna_enabled": True,
            "optuna_search_bounds": {
                "test_param": (1.0, 0.5),  # Invalid: low > high
            },
        }

        # ProcessConfig validation should catch this
        with pytest.raises(ValueError, match="optuna_search_bounds"):
            ProcessConfig(**config_dict)

    def test_composite_metric_properties(self):
        """Test mathematical properties of composite metric."""
        optimizer = OptunaOptimizer(n_trials=10)

        # Test monotonicity: increasing quality increases metric
        metric_low_quality = optimizer.compute_composite_metric(
            quality=0.3, boundary_smoothness=0.5, temporal_consistency=0.5
        )
        metric_high_quality = optimizer.compute_composite_metric(
            quality=0.8, boundary_smoothness=0.5, temporal_consistency=0.5
        )
        assert metric_high_quality > metric_low_quality

        # Test monotonicity: decreasing smoothness (worse) increases metric
        metric_good_smooth = optimizer.compute_composite_metric(
            quality=0.5, boundary_smoothness=0.2, temporal_consistency=0.5
        )
        metric_bad_smooth = optimizer.compute_composite_metric(
            quality=0.5, boundary_smoothness=0.8, temporal_consistency=0.5
        )
        assert metric_good_smooth > metric_bad_smooth

        # Test monotonicity: increasing temporal consistency increases metric
        metric_low_temporal = optimizer.compute_composite_metric(
            quality=0.5, boundary_smoothness=0.5, temporal_consistency=0.3
        )
        metric_high_temporal = optimizer.compute_composite_metric(
            quality=0.5, boundary_smoothness=0.5, temporal_consistency=0.8
        )
        assert metric_high_temporal > metric_low_temporal
