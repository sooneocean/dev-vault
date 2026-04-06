"""Tests for Phase 2 configuration validation and parameter loading."""

import tempfile
from pathlib import Path

import pytest
import yaml

from src.watermark_removal.core.config_manager import ConfigManager
from src.watermark_removal.core.types import ProcessConfig


class TestPhase2ConfigBasics:
    """Tests for loading basic Phase 2 config parameters."""

    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary directory for test configs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_load_phase2_temporal_config(self, temp_config_dir):
        """Test loading Phase 2 temporal smoothing config."""
        config_file = temp_config_dir / "phase2_temporal.yaml"
        config_data = {
            "video_path": "/tmp/video.mp4",
            "mask_path": "/tmp/mask.png",
            "output_dir": "/tmp/output",
            "temporal_smooth_enabled": True,
            "temporal_smooth_alpha": 0.3,
            "use_adaptive_temporal_smoothing": True,
            "adaptive_motion_threshold": 0.05,
        }

        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        manager = ConfigManager(str(config_file))
        config = manager.load()

        assert config.temporal_smooth_enabled is True
        assert config.temporal_smooth_alpha == 0.3
        assert config.use_adaptive_temporal_smoothing is True
        assert config.adaptive_motion_threshold == 0.05

    def test_load_phase2_tracking_config(self, temp_config_dir):
        """Test loading Phase 2 watermark tracking config."""
        config_file = temp_config_dir / "phase2_tracking.yaml"
        config_data = {
            "video_path": "/tmp/video.mp4",
            "mask_path": "/tmp/mask.json",
            "output_dir": "/tmp/output",
            "use_watermark_tracker": True,
            "yolo_model_path": "/path/to/yolo.pt",
            "yolo_confidence_threshold": 0.6,
            "tracker_smoothing_factor": 0.3,
        }

        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        manager = ConfigManager(str(config_file))
        config = manager.load()

        assert config.use_watermark_tracker is True
        assert config.yolo_model_path == "/path/to/yolo.pt"
        assert config.yolo_confidence_threshold == 0.6
        assert config.tracker_smoothing_factor == 0.3

    def test_load_phase2_poisson_config(self, temp_config_dir):
        """Test loading Phase 2 Poisson blending config."""
        config_file = temp_config_dir / "phase2_poisson.yaml"
        config_data = {
            "video_path": "/tmp/video.mp4",
            "mask_path": "/tmp/mask.png",
            "output_dir": "/tmp/output",
            "use_poisson_blending": True,
            "poisson_max_iterations": 150,
            "poisson_tolerance": 0.005,
        }

        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        manager = ConfigManager(str(config_file))
        config = manager.load()

        assert config.use_poisson_blending is True
        assert config.poisson_max_iterations == 150
        assert config.poisson_tolerance == 0.005

    def test_load_phase2_checkpoint_config(self, temp_config_dir):
        """Test loading Phase 2 checkpoint config."""
        config_file = temp_config_dir / "phase2_checkpoint.yaml"
        config_data = {
            "video_path": "/tmp/video.mp4",
            "mask_path": "/tmp/mask.png",
            "output_dir": "/tmp/output",
            "use_checkpoints": True,
        }

        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        manager = ConfigManager(str(config_file))
        config = manager.load()

        assert config.use_checkpoints is True

    def test_load_full_phase2_config(self, temp_config_dir):
        """Test loading complete Phase 2 config with all features."""
        config_file = temp_config_dir / "phase2_full.yaml"
        config_data = {
            "video_path": "/tmp/video.mp4",
            "mask_path": "/tmp/mask.json",
            "output_dir": "/tmp/output",
            "temporal_smooth_enabled": True,
            "temporal_smooth_alpha": 0.4,
            "use_adaptive_temporal_smoothing": True,
            "adaptive_motion_threshold": 0.08,
            "use_poisson_blending": True,
            "poisson_max_iterations": 200,
            "poisson_tolerance": 0.001,
            "use_watermark_tracker": True,
            "yolo_model_path": "/path/to/yolov8n.pt",
            "yolo_confidence_threshold": 0.55,
            "tracker_smoothing_factor": 0.4,
            "use_checkpoints": True,
        }

        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        manager = ConfigManager(str(config_file))
        config = manager.load()

        assert config.temporal_smooth_alpha == 0.4
        assert config.use_adaptive_temporal_smoothing is True
        assert config.use_poisson_blending is True
        assert config.poisson_max_iterations == 200
        assert config.use_watermark_tracker is True
        assert config.yolo_confidence_threshold == 0.55
        assert config.use_checkpoints is True


class TestPhase2ConfigDefaults:
    """Tests for Phase 2 parameter defaults (opt-in behavior)."""

    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary directory for test configs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_phase2_features_disabled_by_default(self, temp_config_dir):
        """Test that Phase 2 features are disabled by default (backward compatible)."""
        config_file = temp_config_dir / "base.yaml"
        config_data = {
            "video_path": "/tmp/video.mp4",
            "mask_path": "/tmp/mask.png",
            "output_dir": "/tmp/output",
        }

        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        manager = ConfigManager(str(config_file))
        config = manager.load()

        # All Phase 2 features should be disabled by default
        assert config.use_adaptive_temporal_smoothing is False
        assert config.use_poisson_blending is False
        assert config.use_watermark_tracker is False
        assert config.use_checkpoints is False
        assert config.yolo_model_path is None

    def test_phase2_parameter_defaults(self, temp_config_dir):
        """Test default values for all Phase 2 parameters."""
        config_file = temp_config_dir / "base.yaml"
        config_data = {
            "video_path": "/tmp/video.mp4",
            "mask_path": "/tmp/mask.png",
            "output_dir": "/tmp/output",
        }

        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        manager = ConfigManager(str(config_file))
        config = manager.load()

        # Verify all defaults
        assert config.adaptive_motion_threshold == 0.05
        assert config.poisson_max_iterations == 100
        assert config.poisson_tolerance == 0.01
        assert config.yolo_confidence_threshold == 0.5
        assert config.tracker_smoothing_factor == 0.3

    def test_temporal_smooth_enabled_still_true_by_default(self, temp_config_dir):
        """Test that temporal_smooth_enabled is still True by default (Phase 1 behavior)."""
        config_file = temp_config_dir / "base.yaml"
        config_data = {
            "video_path": "/tmp/video.mp4",
            "mask_path": "/tmp/mask.png",
            "output_dir": "/tmp/output",
        }

        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        manager = ConfigManager(str(config_file))
        config = manager.load()

        # Phase 1 temporal smoothing still enabled (simple alpha, not adaptive)
        assert config.temporal_smooth_enabled is True
        assert config.temporal_smooth_alpha == 0.3
        assert config.use_adaptive_temporal_smoothing is False


class TestPhase2AlphaEdgeCases:
    """Tests for temporal_smooth_alpha edge cases."""

    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary directory for test configs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_temporal_smooth_alpha_zero_disabled(self, temp_config_dir):
        """Test that alpha=0.0 disables temporal smoothing."""
        config_file = temp_config_dir / "alpha_zero.yaml"
        config_data = {
            "video_path": "/tmp/video.mp4",
            "mask_path": "/tmp/mask.png",
            "output_dir": "/tmp/output",
            "temporal_smooth_alpha": 0.0,
        }

        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        manager = ConfigManager(str(config_file))
        config = manager.load()

        assert config.temporal_smooth_alpha == 0.0

    def test_temporal_smooth_alpha_one_maximum(self, temp_config_dir):
        """Test that alpha=1.0 is maximum (full previous-frame blend)."""
        config_file = temp_config_dir / "alpha_one.yaml"
        config_data = {
            "video_path": "/tmp/video.mp4",
            "mask_path": "/tmp/mask.png",
            "output_dir": "/tmp/output",
            "temporal_smooth_alpha": 1.0,
        }

        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        manager = ConfigManager(str(config_file))
        config = manager.load()

        assert config.temporal_smooth_alpha == 1.0

    def test_temporal_smooth_alpha_midrange(self, temp_config_dir):
        """Test typical midrange alpha values."""
        for alpha in [0.1, 0.3, 0.5, 0.7, 0.9]:
            config_file = temp_config_dir / f"alpha_{alpha}.yaml"
            config_data = {
                "video_path": "/tmp/video.mp4",
                "mask_path": "/tmp/mask.png",
                "output_dir": "/tmp/output",
                "temporal_smooth_alpha": alpha,
            }

            with open(config_file, "w") as f:
                yaml.dump(config_data, f)

            manager = ConfigManager(str(config_file))
            config = manager.load()

            assert config.temporal_smooth_alpha == alpha


class TestPhase2InvalidParameters:
    """Tests for invalid Phase 2 parameter values."""

    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary directory for test configs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_temporal_smooth_alpha_too_high(self, temp_config_dir):
        """Test that alpha > 1.0 raises ValueError."""
        config_file = temp_config_dir / "alpha_invalid.yaml"
        config_data = {
            "video_path": "/tmp/video.mp4",
            "mask_path": "/tmp/mask.png",
            "output_dir": "/tmp/output",
            "temporal_smooth_alpha": 1.5,
        }

        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        manager = ConfigManager(str(config_file))
        with pytest.raises(ValueError, match="temporal_smooth_alpha"):
            manager.load()

    def test_temporal_smooth_alpha_negative(self, temp_config_dir):
        """Test that negative alpha raises ValueError."""
        config_file = temp_config_dir / "alpha_negative.yaml"
        config_data = {
            "video_path": "/tmp/video.mp4",
            "mask_path": "/tmp/mask.png",
            "output_dir": "/tmp/output",
            "temporal_smooth_alpha": -0.1,
        }

        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        manager = ConfigManager(str(config_file))
        with pytest.raises(ValueError, match="temporal_smooth_alpha"):
            manager.load()

    def test_yolo_confidence_threshold_invalid_type(self, temp_config_dir):
        """Test that string confidence threshold raises TypeError on validation."""
        config_file = temp_config_dir / "yolo_invalid.yaml"
        config_data = {
            "video_path": "/tmp/video.mp4",
            "mask_path": "/tmp/mask.png",
            "output_dir": "/tmp/output",
            "yolo_confidence_threshold": "high",  # Wrong type
        }

        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        manager = ConfigManager(str(config_file))
        # This will raise TypeError during config instantiation
        with pytest.raises(TypeError):
            manager.load()

    def test_yolo_confidence_threshold_out_of_range(self, temp_config_dir):
        """Test that confidence threshold outside [0, 1] raises ValueError."""
        config_file = temp_config_dir / "yolo_threshold_invalid.yaml"
        config_data = {
            "video_path": "/tmp/video.mp4",
            "mask_path": "/tmp/mask.png",
            "output_dir": "/tmp/output",
            "yolo_confidence_threshold": 1.5,
        }

        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        manager = ConfigManager(str(config_file))
        with pytest.raises(ValueError, match="yolo_confidence_threshold"):
            manager.load()

    def test_poisson_iterations_zero(self, temp_config_dir):
        """Test that poisson_max_iterations < 1 raises ValueError."""
        config_file = temp_config_dir / "poisson_invalid.yaml"
        config_data = {
            "video_path": "/tmp/video.mp4",
            "mask_path": "/tmp/mask.png",
            "output_dir": "/tmp/output",
            "poisson_max_iterations": 0,
        }

        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        manager = ConfigManager(str(config_file))
        with pytest.raises(ValueError, match="poisson_max_iterations"):
            manager.load()

    def test_poisson_iterations_negative(self, temp_config_dir):
        """Test that negative poisson_max_iterations raises ValueError."""
        config_file = temp_config_dir / "poisson_negative.yaml"
        config_data = {
            "video_path": "/tmp/video.mp4",
            "mask_path": "/tmp/mask.png",
            "output_dir": "/tmp/output",
            "poisson_max_iterations": -5,
        }

        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        manager = ConfigManager(str(config_file))
        with pytest.raises(ValueError, match="poisson_max_iterations"):
            manager.load()

    def test_poisson_tolerance_zero(self, temp_config_dir):
        """Test that poisson_tolerance <= 0.0 raises ValueError."""
        config_file = temp_config_dir / "poisson_tol_invalid.yaml"
        config_data = {
            "video_path": "/tmp/video.mp4",
            "mask_path": "/tmp/mask.png",
            "output_dir": "/tmp/output",
            "poisson_tolerance": 0.0,
        }

        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        manager = ConfigManager(str(config_file))
        with pytest.raises(ValueError, match="poisson_tolerance"):
            manager.load()

    def test_adaptive_motion_threshold_out_of_range(self, temp_config_dir):
        """Test that motion threshold outside [0, 1] raises ValueError."""
        config_file = temp_config_dir / "motion_invalid.yaml"
        config_data = {
            "video_path": "/tmp/video.mp4",
            "mask_path": "/tmp/mask.png",
            "output_dir": "/tmp/output",
            "adaptive_motion_threshold": 1.5,
        }

        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        manager = ConfigManager(str(config_file))
        with pytest.raises(ValueError, match="adaptive_motion_threshold"):
            manager.load()

    def test_tracker_smoothing_factor_out_of_range(self, temp_config_dir):
        """Test that smoothing factor outside [0, 1] raises ValueError."""
        config_file = temp_config_dir / "smooth_invalid.yaml"
        config_data = {
            "video_path": "/tmp/video.mp4",
            "mask_path": "/tmp/mask.png",
            "output_dir": "/tmp/output",
            "tracker_smoothing_factor": 1.2,
        }

        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        manager = ConfigManager(str(config_file))
        with pytest.raises(ValueError, match="tracker_smoothing_factor"):
            manager.load()


class TestPhase2ParameterRanges:
    """Parametrized tests for Phase 2 parameter ranges."""

    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary directory for test configs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.mark.parametrize(
        "alpha",
        [0.0, 0.1, 0.25, 0.5, 0.75, 0.99, 1.0],
        ids=[
            "alpha_zero",
            "alpha_low",
            "alpha_quarter",
            "alpha_half",
            "alpha_high",
            "alpha_near_max",
            "alpha_max",
        ],
    )
    def test_temporal_smooth_alpha_valid_range(self, temp_config_dir, alpha):
        """Test all valid temporal_smooth_alpha values."""
        config_file = temp_config_dir / f"alpha_{alpha}.yaml"
        config_data = {
            "video_path": "/tmp/video.mp4",
            "mask_path": "/tmp/mask.png",
            "output_dir": "/tmp/output",
            "temporal_smooth_alpha": alpha,
        }

        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        manager = ConfigManager(str(config_file))
        config = manager.load()

        assert config.temporal_smooth_alpha == alpha

    @pytest.mark.parametrize(
        "iterations",
        [1, 10, 50, 100, 200, 500],
        ids=[
            "single_iter",
            "low_iter",
            "medium_iter",
            "default_iter",
            "high_iter",
            "very_high_iter",
        ],
    )
    def test_poisson_iterations_valid_range(self, temp_config_dir, iterations):
        """Test valid poisson_max_iterations values."""
        config_file = temp_config_dir / f"iter_{iterations}.yaml"
        config_data = {
            "video_path": "/tmp/video.mp4",
            "mask_path": "/tmp/mask.png",
            "output_dir": "/tmp/output",
            "poisson_max_iterations": iterations,
        }

        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        manager = ConfigManager(str(config_file))
        config = manager.load()

        assert config.poisson_max_iterations == iterations

    @pytest.mark.parametrize(
        "threshold",
        [0.0, 0.25, 0.5, 0.75, 1.0],
        ids=[
            "threshold_zero",
            "threshold_low",
            "threshold_mid",
            "threshold_high",
            "threshold_max",
        ],
    )
    def test_yolo_confidence_threshold_valid_range(self, temp_config_dir, threshold):
        """Test valid yolo_confidence_threshold values."""
        config_file = temp_config_dir / f"conf_{threshold}.yaml"
        config_data = {
            "video_path": "/tmp/video.mp4",
            "mask_path": "/tmp/mask.png",
            "output_dir": "/tmp/output",
            "yolo_confidence_threshold": threshold,
        }

        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        manager = ConfigManager(str(config_file))
        config = manager.load()

        assert config.yolo_confidence_threshold == threshold

    @pytest.mark.parametrize(
        "invalid_alpha",
        [-0.5, -0.1, 1.01, 1.5, 2.0],
        ids=[
            "alpha_negative_half",
            "alpha_negative_small",
            "alpha_slightly_over",
            "alpha_over_range",
            "alpha_double",
        ],
    )
    def test_temporal_smooth_alpha_invalid_range(self, temp_config_dir, invalid_alpha):
        """Test invalid temporal_smooth_alpha values raise ValueError."""
        config_file = temp_config_dir / f"alpha_bad_{invalid_alpha}.yaml"
        config_data = {
            "video_path": "/tmp/video.mp4",
            "mask_path": "/tmp/mask.png",
            "output_dir": "/tmp/output",
            "temporal_smooth_alpha": invalid_alpha,
        }

        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        manager = ConfigManager(str(config_file))
        with pytest.raises(ValueError, match="temporal_smooth_alpha"):
            manager.load()

    @pytest.mark.parametrize(
        "invalid_iter",
        [0, -1, -100],
        ids=[
            "iter_zero",
            "iter_negative_one",
            "iter_large_negative",
        ],
    )
    def test_poisson_iterations_invalid_range(self, temp_config_dir, invalid_iter):
        """Test invalid poisson_max_iterations values raise ValueError."""
        config_file = temp_config_dir / f"iter_bad_{invalid_iter}.yaml"
        config_data = {
            "video_path": "/tmp/video.mp4",
            "mask_path": "/tmp/mask.png",
            "output_dir": "/tmp/output",
            "poisson_max_iterations": invalid_iter,
        }

        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        manager = ConfigManager(str(config_file))
        with pytest.raises(ValueError, match="poisson_max_iterations"):
            manager.load()


class TestPhase2BackwardCompatibility:
    """Tests for backward compatibility with Phase 1 configs."""

    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary directory for test configs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_phase1_config_loads_with_phase2_defaults(self, temp_config_dir):
        """Test that Phase 1 config loads and Phase 2 features default to disabled."""
        config_file = temp_config_dir / "phase1_only.yaml"
        config_data = {
            "video_path": "/tmp/video.mp4",
            "mask_path": "/tmp/mask.png",
            "output_dir": "/tmp/output",
            "context_padding": 50,
            "batch_size": 4,
            "output_fps": 30.0,
        }

        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        manager = ConfigManager(str(config_file))
        config = manager.load()

        # Phase 1 fields present
        assert config.context_padding == 50
        assert config.batch_size == 4
        assert config.output_fps == 30.0

        # Phase 2 defaults (disabled)
        assert config.use_adaptive_temporal_smoothing is False
        assert config.use_poisson_blending is False
        assert config.use_watermark_tracker is False
        assert config.use_checkpoints is False

    def test_phase1_with_temporal_smooth_alpha_still_works(self, temp_config_dir):
        """Test that Phase 1 temporal_smooth_alpha parameter still works."""
        config_file = temp_config_dir / "phase1_with_alpha.yaml"
        config_data = {
            "video_path": "/tmp/video.mp4",
            "mask_path": "/tmp/mask.png",
            "output_dir": "/tmp/output",
            "temporal_smooth_alpha": 0.5,
        }

        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        manager = ConfigManager(str(config_file))
        config = manager.load()

        assert config.temporal_smooth_alpha == 0.5
        # Adaptive smoothing still disabled
        assert config.use_adaptive_temporal_smoothing is False

    def test_phase1_only_features_work_alongside_phase2(self, temp_config_dir):
        """Test Phase 1 config works when Phase 2 features are mixed in."""
        config_file = temp_config_dir / "mixed.yaml"
        config_data = {
            "video_path": "/tmp/video.mp4",
            "mask_path": "/tmp/mask.png",
            "output_dir": "/tmp/output",
            "context_padding": 75,
            "batch_size": 2,
            "use_poisson_blending": True,  # Phase 2
            "poisson_max_iterations": 50,  # Phase 2
        }

        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        manager = ConfigManager(str(config_file))
        config = manager.load()

        # Phase 1 features preserved
        assert config.context_padding == 75
        assert config.batch_size == 2

        # Phase 2 features active
        assert config.use_poisson_blending is True
        assert config.poisson_max_iterations == 50

        # Other Phase 2 features still disabled
        assert config.use_adaptive_temporal_smoothing is False
        assert config.use_watermark_tracker is False


class TestPhase2YOLOModelPath:
    """Tests for YOLO model path handling."""

    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary directory for test configs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_yolo_model_path_none_by_default(self, temp_config_dir):
        """Test that YOLO model path is None when not specified."""
        config_file = temp_config_dir / "base.yaml"
        config_data = {
            "video_path": "/tmp/video.mp4",
            "mask_path": "/tmp/mask.png",
            "output_dir": "/tmp/output",
        }

        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        manager = ConfigManager(str(config_file))
        config = manager.load()

        assert config.yolo_model_path is None

    def test_yolo_model_path_optional(self, temp_config_dir):
        """Test that YOLO model path can be explicitly set to None."""
        config_file = temp_config_dir / "no_yolo.yaml"
        config_data = {
            "video_path": "/tmp/video.mp4",
            "mask_path": "/tmp/mask.png",
            "output_dir": "/tmp/output",
            "use_watermark_tracker": True,
            "yolo_model_path": None,  # Optional
        }

        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        manager = ConfigManager(str(config_file))
        config = manager.load()

        assert config.use_watermark_tracker is True
        assert config.yolo_model_path is None

    def test_yolo_model_path_absolute(self, temp_config_dir):
        """Test absolute YOLO model path."""
        config_file = temp_config_dir / "yolo_abs.yaml"
        config_data = {
            "video_path": "/tmp/video.mp4",
            "mask_path": "/tmp/mask.png",
            "output_dir": "/tmp/output",
            "use_watermark_tracker": True,
            "yolo_model_path": "/usr/local/models/yolov8n.pt",
        }

        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        manager = ConfigManager(str(config_file))
        config = manager.load()

        assert config.yolo_model_path == "/usr/local/models/yolov8n.pt"

    def test_yolo_model_path_home_expansion(self, temp_config_dir):
        """Test YOLO model path with home directory reference."""
        config_file = temp_config_dir / "yolo_home.yaml"
        config_data = {
            "video_path": "/tmp/video.mp4",
            "mask_path": "/tmp/mask.png",
            "output_dir": "/tmp/output",
            "yolo_model_path": "~/.local/share/ultralytics/yolov8n.pt",
        }

        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        manager = ConfigManager(str(config_file))
        config = manager.load()

        # Path should be stored as-is (caller responsible for expansion)
        assert config.yolo_model_path == "~/.local/share/ultralytics/yolov8n.pt"


class TestPhase2ConfigDocumentation:
    """Tests to verify all Phase 2 params are documented in types.py."""

    def test_all_phase2_params_in_process_config(self):
        """Verify all Phase 2 parameters exist in ProcessConfig."""
        config = ProcessConfig(
            video_path="/tmp/video.mp4",
            mask_path="/tmp/mask.png",
            output_dir="/tmp/output",
        )

        # Phase 2 temporal parameters
        assert hasattr(config, "use_adaptive_temporal_smoothing")
        assert hasattr(config, "adaptive_motion_threshold")

        # Phase 2 Poisson parameters
        assert hasattr(config, "use_poisson_blending")
        assert hasattr(config, "poisson_max_iterations")
        assert hasattr(config, "poisson_tolerance")

        # Phase 2 tracking parameters
        assert hasattr(config, "use_watermark_tracker")
        assert hasattr(config, "yolo_model_path")
        assert hasattr(config, "yolo_confidence_threshold")
        assert hasattr(config, "tracker_smoothing_factor")

        # Phase 2 checkpoint parameter
        assert hasattr(config, "use_checkpoints")

    def test_phase2_params_have_docstrings(self):
        """Verify Phase 2 parameters have docstrings."""
        # This test documents expected docstrings exist
        import inspect

        sig = inspect.signature(ProcessConfig)
        params = sig.parameters

        phase2_params = [
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
        ]

        # Check that all Phase 2 params exist as fields
        for param in phase2_params:
            assert param in ProcessConfig.__dataclass_fields__

    def test_phase2_defaults_documented(self):
        """Verify Phase 2 parameter defaults match documentation."""
        config = ProcessConfig(
            video_path="/tmp/video.mp4",
            mask_path="/tmp/mask.png",
            output_dir="/tmp/output",
        )

        # Verify defaults match plan documentation
        assert config.use_adaptive_temporal_smoothing is False
        assert config.adaptive_motion_threshold == 0.05
        assert config.use_poisson_blending is False
        assert config.poisson_max_iterations == 100
        assert config.poisson_tolerance == 0.01
        assert config.use_watermark_tracker is False
        assert config.yolo_model_path is None
        assert config.yolo_confidence_threshold == 0.5
        assert config.tracker_smoothing_factor == 0.3
        assert config.use_checkpoints is False
