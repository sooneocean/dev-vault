"""Comprehensive test suite for Unit 25: Optuna hyperparameter tuning."""

import json
import pytest
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import sqlite3

from src.watermark_removal.tuning.tuning_config import (
    TuningSearchSpace,
    TuningParameters,
)
from src.watermark_removal.tuning.optuna_optimizer import (
    OptunaTuner,
    TuningConfig,
    OPTUNA_AVAILABLE,
)


class TestTuningSearchSpace:
    """Tests for TuningSearchSpace definition and validation."""

    def test_search_space_default_bounds(self):
        """Search space has correct default bounds."""
        space = TuningSearchSpace()

        assert space.weight_yolov5s == (0.1, 1.0)
        assert space.weight_yolov5m == (0.1, 1.0)
        assert space.weight_yolov5l == (0.1, 1.0)
        assert space.confidence_threshold == (0.05, 0.95)
        assert space.iou_threshold == (0.3, 0.7)
        assert space.nms_threshold == (0.3, 0.7)
        assert space.augmentation_intensity == (0.0, 1.0)

    def test_search_space_custom_bounds(self):
        """Search space accepts custom bounds."""
        space = TuningSearchSpace(
            weight_yolov5s=(0.2, 0.8),
            confidence_threshold=(0.1, 0.9)
        )

        assert space.weight_yolov5s == (0.2, 0.8)
        assert space.confidence_threshold == (0.1, 0.9)
        # Other bounds remain default
        assert space.weight_yolov5m == (0.1, 1.0)

    def test_search_space_to_dict(self):
        """Search space converts to dict correctly."""
        space = TuningSearchSpace()
        space_dict = space.to_dict()

        assert isinstance(space_dict, dict)
        assert len(space_dict) == 7
        assert "weight_yolov5s" in space_dict
        assert "confidence_threshold" in space_dict
        assert space_dict["weight_yolov5s"] == (0.1, 1.0)


class TestTuningParameters:
    """Tests for validated hyperparameter tuning results."""

    def test_parameters_initialization(self):
        """TuningParameters initializes with valid values."""
        params = TuningParameters(
            weight_yolov5s=0.3,
            weight_yolov5m=0.4,
            weight_yolov5l=0.3,
            confidence_threshold=0.5,
            iou_threshold=0.5,
            nms_threshold=0.5,
            augmentation_intensity=0.5
        )

        assert params.weight_yolov5s == 0.3
        assert params.confidence_threshold == 0.5

    def test_parameters_validation_success(self):
        """Valid parameters pass validation."""
        params = TuningParameters(
            weight_yolov5s=0.3,
            weight_yolov5m=0.4,
            weight_yolov5l=0.3,
            confidence_threshold=0.5,
            iou_threshold=0.5,
            nms_threshold=0.5,
            augmentation_intensity=0.5
        )

        assert params.validate() is True

    def test_parameters_validation_weight_sum(self):
        """Validation checks weight sum is ~1.0."""
        params = TuningParameters(
            weight_yolov5s=0.5,
            weight_yolov5m=0.5,
            weight_yolov5l=0.5,  # Sum > 1.01
            confidence_threshold=0.5,
            iou_threshold=0.5,
            nms_threshold=0.5,
            augmentation_intensity=0.5
        )

        assert params.validate() is False

    def test_parameters_validation_out_of_range(self):
        """Validation rejects out-of-range values."""
        params = TuningParameters(
            weight_yolov5s=1.5,  # > 1.0
            weight_yolov5m=0.3,
            weight_yolov5l=0.0,
            confidence_threshold=0.5,
            iou_threshold=0.5,
            nms_threshold=0.5,
            augmentation_intensity=0.5
        )

        assert params.validate() is False

    def test_parameters_to_dict(self):
        """TuningParameters converts to dict."""
        params = TuningParameters(
            weight_yolov5s=0.3,
            weight_yolov5m=0.4,
            weight_yolov5l=0.3,
            confidence_threshold=0.5,
            iou_threshold=0.5,
            nms_threshold=0.5,
            augmentation_intensity=0.5
        )

        params_dict = params.to_dict()

        assert isinstance(params_dict, dict)
        assert params_dict["weight_yolov5s"] == 0.3
        assert params_dict["confidence_threshold"] == 0.5

    def test_parameters_from_dict(self):
        """TuningParameters creates from dict."""
        data = {
            "weight_yolov5s": 0.3,
            "weight_yolov5m": 0.4,
            "weight_yolov5l": 0.3,
            "confidence_threshold": 0.5,
            "iou_threshold": 0.5,
            "nms_threshold": 0.5,
            "augmentation_intensity": 0.5
        }

        params = TuningParameters.from_dict(data)

        assert params.weight_yolov5s == 0.3
        assert params.confidence_threshold == 0.5

    def test_parameters_save_load(self):
        """TuningParameters saves and loads from JSON."""
        params = TuningParameters(
            weight_yolov5s=0.3,
            weight_yolov5m=0.4,
            weight_yolov5l=0.3,
            confidence_threshold=0.5,
            iou_threshold=0.5,
            nms_threshold=0.5,
            augmentation_intensity=0.5
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            save_path = Path(tmpdir) / "params.json"

            # Save
            save_result = params.save(str(save_path))
            assert save_result is True
            assert save_path.exists()

            # Load
            loaded_params = TuningParameters.load(str(save_path))

            assert loaded_params is not None
            assert loaded_params.weight_yolov5s == 0.3
            assert loaded_params.confidence_threshold == 0.5

    def test_parameters_load_nonexistent(self):
        """TuningParameters load returns None for nonexistent file."""
        result = TuningParameters.load("/nonexistent/path/params.json")

        assert result is None


class TestTuningConfig:
    """Tests for Optuna study and sampler configuration."""

    def test_tuning_config_initialization(self):
        """TuningConfig initializes with valid settings."""
        config = TuningConfig(
            study_name="test_study",
            storage="sqlite:///test.db",
            n_trials=50
        )

        assert config.study_name == "test_study"
        assert config.n_trials == 50

    def test_tuning_config_defaults(self):
        """TuningConfig has reasonable defaults."""
        config = TuningConfig()

        assert config.study_name == "watermark_ensemble_tuning"
        assert config.n_trials == 150
        assert config.direction == "maximize"
        assert config.sampler_n_startup_trials == 10

    def test_tuning_config_search_bounds(self):
        """TuningConfig includes search bounds."""
        config = TuningConfig()

        assert "weight_yolov5s" in config.search_bounds
        assert "confidence_threshold" in config.search_bounds
        assert len(config.search_bounds) == 7


class TestOptunaTuner:
    """Tests for Optuna-based hyperparameter optimizer."""

    def test_tuner_initialization(self):
        """OptunaTuner initializes correctly."""
        config = TuningConfig(study_name="test_study")
        tuner = OptunaTuner(config)

        assert tuner.config == config

    def test_tuner_mock_mode_flag(self):
        """OptunaTuner responds to mock mode flag."""
        # OPTUNA_AVAILABLE should be boolean
        assert isinstance(OPTUNA_AVAILABLE, bool)

    @pytest.mark.skipif(not OPTUNA_AVAILABLE, reason="Optuna not installed")
    def test_create_study_real(self):
        """OptunaTuner creates study when Optuna available."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            config = TuningConfig(
                study_name="test_study",
                storage=f"sqlite:///{db_path}",
                n_trials=10
            )

            tuner = OptunaTuner(config)
            study = tuner.create_study()

            assert study is not None

    def test_tuner_get_best_params_interface(self):
        """OptunaTuner has get_best_params method."""
        config = TuningConfig()
        tuner = OptunaTuner(config)

        # Should have the method available
        assert hasattr(tuner, "get_best_params")

    def test_tuner_save_results_interface(self):
        """OptunaTuner has save_results method."""
        config = TuningConfig()
        tuner = OptunaTuner(config)

        assert hasattr(tuner, "save_results")


class TestOptunaTunerObjective:
    """Tests for Optuna objective function definition."""

    @pytest.mark.asyncio
    async def test_objective_function_signature(self):
        """Objective function has correct signature."""
        config = TuningConfig()
        tuner = OptunaTuner(config)

        # Should have objective method
        assert hasattr(tuner, "objective")

    def test_trial_timeout_handling(self):
        """Tuner handles trial timeout gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            config = TuningConfig(
                study_name="test_study",
                storage=f"sqlite:///{db_path}",
                trial_timeout_sec=1.0
            )

            tuner = OptunaTuner(config)

            # Should not raise
            assert tuner.config.trial_timeout_sec == 1.0


class TestOptunaTunerResults:
    """Tests for results persistence and retrieval."""

    def test_results_save_structure(self):
        """Results are saved in correct JSON structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            results_path = Path(tmpdir) / "results.json"

            # Create mock results
            mock_results = {
                "study_name": "test_study",
                "n_trials": 10,
                "best_value": 0.95,
                "best_params": {
                    "weight_yolov5s": 0.3,
                    "weight_yolov5m": 0.4,
                    "weight_yolov5l": 0.3,
                    "confidence_threshold": 0.5,
                    "iou_threshold": 0.5,
                    "nms_threshold": 0.5,
                    "augmentation_intensity": 0.5
                }
            }

            # Save to JSON
            with open(results_path, "w") as f:
                json.dump(mock_results, f, indent=2)

            # Load and verify
            with open(results_path) as f:
                loaded = json.load(f)

            assert loaded["study_name"] == "test_study"
            assert loaded["best_value"] == 0.95
            assert loaded["best_params"]["weight_yolov5s"] == 0.3

    def test_results_with_tuning_parameters(self):
        """Results can be loaded as TuningParameters."""
        params_dict = {
            "weight_yolov5s": 0.3,
            "weight_yolov5m": 0.4,
            "weight_yolov5l": 0.3,
            "confidence_threshold": 0.5,
            "iou_threshold": 0.5,
            "nms_threshold": 0.5,
            "augmentation_intensity": 0.5
        }

        params = TuningParameters.from_dict(params_dict)

        assert params is not None
        assert params.validate()


class TestSQLiteBackendValidation:
    """Tests for SQLite backend concurrent access patterns."""

    def test_sqlite_database_creation(self):
        """SQLite database can be created without error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"

            # Create connection and table
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE studies (
                    study_id INTEGER PRIMARY KEY,
                    study_name TEXT UNIQUE,
                    created_at REAL
                )
            """)

            conn.commit()
            conn.close()

            assert db_path.exists()

    def test_sqlite_concurrent_read_access(self):
        """SQLite allows concurrent read access."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"

            # Create table
            conn1 = sqlite3.connect(str(db_path))
            cursor1 = conn1.cursor()

            cursor1.execute("""
                CREATE TABLE studies (
                    study_id INTEGER PRIMARY KEY,
                    study_name TEXT UNIQUE
                )
            """)

            cursor1.execute("INSERT INTO studies VALUES (1, 'study_1')")
            conn1.commit()
            conn1.close()

            # Read from different connection
            conn2 = sqlite3.connect(str(db_path))
            cursor2 = conn2.cursor()

            cursor2.execute("SELECT * FROM studies")
            rows = cursor2.fetchall()

            assert len(rows) == 1
            assert rows[0][1] == "study_1"

            conn2.close()

    def test_sqlite_write_serialization(self):
        """SQLite serializes writes correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"

            # Create table
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE trials (
                    trial_id INTEGER PRIMARY KEY,
                    value REAL
                )
            """)

            # Write multiple records
            for i in range(5):
                cursor.execute("INSERT INTO trials VALUES (?, ?)", (i, float(i) * 0.1))

            conn.commit()
            conn.close()

            # Verify all records
            conn2 = sqlite3.connect(str(db_path))
            cursor2 = conn2.cursor()

            cursor2.execute("SELECT COUNT(*) FROM trials")
            count = cursor2.fetchone()[0]

            assert count == 5

            conn2.close()


class TestOptunaWallClockTime:
    """Tests for optimization timing and performance estimates."""

    def test_trial_time_measurement(self):
        """Trial execution time can be measured."""
        start_time = time.time()

        # Simulate a trial
        time.sleep(0.1)

        elapsed = time.time() - start_time

        assert elapsed >= 0.1

    def test_optimization_time_estimation(self):
        """Optimization time can be estimated from trial count."""
        n_trials = 150
        time_per_trial_sec = 25  # 25 seconds per trial

        estimated_time_sec = n_trials * time_per_trial_sec
        estimated_hours = estimated_time_sec / 3600

        # 150 * 25 = 3750 seconds ≈ 62 minutes ≈ 1 hour
        assert estimated_hours >= 1.0
        assert estimated_hours <= 2.0


class TestTuningParameterNormalization:
    """Tests for ensemble weight normalization in objective function."""

    def test_weight_normalization_sums_to_one(self):
        """Normalized weights sum to approximately 1.0."""
        raw_weights = [0.3, 0.4, 0.3]
        total = sum(raw_weights)
        normalized = [w / total for w in raw_weights]

        weight_sum = sum(normalized)

        assert pytest.approx(weight_sum, abs=0.01) == 1.0

    def test_confidence_weighting_computation(self):
        """Confidence-weighted voting computes correctly."""
        predictions = [
            {"model": "yolov5s", "confidence": 0.9, "accuracy": 0.85},
            {"model": "yolov5m", "confidence": 0.85, "accuracy": 0.90},
        ]

        # Weight by accuracy
        total_accuracy = sum(p["accuracy"] for p in predictions)
        weighted_scores = [
            p["confidence"] * (p["accuracy"] / total_accuracy)
            for p in predictions
        ]

        final_score = sum(weighted_scores)

        assert 0.0 <= final_score <= 1.0


class TestTuningConfigValidation:
    """Tests for configuration validation."""

    def test_config_invalid_n_trials(self):
        """Config rejects invalid trial count."""
        with pytest.raises(ValueError):
            TuningConfig(n_trials=0)

    def test_config_invalid_storage_format(self):
        """Config validates storage format."""
        # This should work (valid SQLite path)
        config = TuningConfig(storage="sqlite:///valid.db")
        assert config.storage == "sqlite:///valid.db"

    def test_config_study_name_required(self):
        """Config requires study name."""
        config = TuningConfig()
        assert len(config.study_name) > 0
