"""Tests for configuration management."""

import tempfile
from pathlib import Path

import pytest
import yaml

from src.watermark_removal.core.config_manager import ConfigManager
from src.watermark_removal.core.types import ProcessConfig


class TestConfigManager:
    """Tests for ConfigManager class."""

    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary directory for test configs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_config_manager_valid_config(self, temp_config_dir):
        """Test loading valid configuration."""
        config_file = temp_config_dir / "config.yaml"
        config_data = {
            "video_path": "/tmp/video.mp4",
            "mask_path": "/tmp/mask.png",
            "output_dir": "/tmp/output",
        }

        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        manager = ConfigManager(str(config_file))
        config = manager.load()

        assert isinstance(config, ProcessConfig)
        assert config.video_path.endswith("video.mp4")
        assert config.mask_path.endswith("mask.png")
        assert config.output_dir.endswith("output")

    def test_config_manager_with_all_fields(self, temp_config_dir):
        """Test loading config with all fields specified."""
        config_file = temp_config_dir / "config.yaml"
        config_data = {
            "video_path": "/tmp/video.mp4",
            "mask_path": "/tmp/mask.json",
            "output_dir": "/tmp/output",
            "context_padding": 100,
            "target_inpaint_size": 512,
            "batch_size": 2,
            "timeout": 500.0,
            "output_codec": "vp9",
            "output_crf": 15,
            "keep_intermediate": True,
            "verbose": False,
            "inpaint": {
                "model_name": "sdxl.safetensors",
                "prompt": "custom prompt",
                "negative_prompt": "custom negative",
                "steps": 50,
                "cfg_scale": 10.0,
                "seed": 100,
                "sampler": "dpmpp",
            },
        }

        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        manager = ConfigManager(str(config_file))
        config = manager.load()

        assert config.context_padding == 100
        assert config.target_inpaint_size == 512
        assert config.batch_size == 2
        assert config.timeout == 500.0
        assert config.output_codec == "vp9"
        assert config.output_crf == 15
        assert config.keep_intermediate is True
        assert config.verbose is False
        assert config.inpaint.model_name == "sdxl.safetensors"
        assert config.inpaint.prompt == "custom prompt"
        assert config.inpaint.steps == 50
        assert config.inpaint.cfg_scale == 10.0

    def test_config_manager_default_values(self, temp_config_dir):
        """Test that default values are applied for optional fields."""
        config_file = temp_config_dir / "config.yaml"
        config_data = {
            "video_path": "/tmp/video.mp4",
            "mask_path": "/tmp/mask.png",
            "output_dir": "/tmp/output",
            # Omit optional fields
        }

        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        manager = ConfigManager(str(config_file))
        config = manager.load()

        # Verify defaults
        assert config.context_padding == 50
        assert config.target_inpaint_size == 1024
        assert config.batch_size == 4
        assert config.timeout == 300.0
        assert config.output_codec == "h264"
        assert config.output_crf == 23
        assert config.keep_intermediate is False
        assert config.verbose is True

    def test_config_manager_missing_video_path(self, temp_config_dir):
        """Test that FileNotFoundError is raised if config file missing."""
        config_file = temp_config_dir / "nonexistent.yaml"

        with pytest.raises(FileNotFoundError):
            ConfigManager(str(config_file))

    def test_config_manager_missing_required_video(self, temp_config_dir):
        """Test that ValueError is raised if video_path is missing."""
        config_file = temp_config_dir / "config.yaml"
        config_data = {
            "mask_path": "/tmp/mask.png",
            "output_dir": "/tmp/output",
            # Missing video_path
        }

        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        manager = ConfigManager(str(config_file))
        with pytest.raises(ValueError, match="video_path"):
            manager.load()

    def test_config_manager_missing_required_mask(self, temp_config_dir):
        """Test that ValueError is raised if mask_path is missing."""
        config_file = temp_config_dir / "config.yaml"
        config_data = {
            "video_path": "/tmp/video.mp4",
            "output_dir": "/tmp/output",
            # Missing mask_path
        }

        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        manager = ConfigManager(str(config_file))
        with pytest.raises(ValueError, match="mask_path"):
            manager.load()

    def test_config_manager_missing_required_output(self, temp_config_dir):
        """Test that ValueError is raised if output_dir is missing."""
        config_file = temp_config_dir / "config.yaml"
        config_data = {
            "video_path": "/tmp/video.mp4",
            "mask_path": "/tmp/mask.png",
            # Missing output_dir
        }

        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        manager = ConfigManager(str(config_file))
        with pytest.raises(ValueError, match="output_dir"):
            manager.load()

    def test_config_manager_relative_paths(self, temp_config_dir):
        """Test that relative paths are resolved correctly."""
        config_file = temp_config_dir / "config.yaml"
        config_data = {
            "video_path": "video.mp4",
            "mask_path": "mask.png",
            "output_dir": "output",
        }

        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        manager = ConfigManager(str(config_file))
        config = manager.load()

        # Paths should be absolute
        assert config.video_path != "video.mp4"
        assert config.mask_path != "mask.png"
        assert config.output_dir != "output"
        assert "video.mp4" in config.video_path
        assert "mask.png" in config.mask_path
        assert "output" in config.output_dir

    def test_config_manager_empty_required_field(self, temp_config_dir):
        """Test that ValueError is raised if required field is empty string."""
        config_file = temp_config_dir / "config.yaml"
        config_data = {
            "video_path": "",  # Empty
            "mask_path": "/tmp/mask.png",
            "output_dir": "/tmp/output",
        }

        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        manager = ConfigManager(str(config_file))
        with pytest.raises(ValueError, match="video_path"):
            manager.load()

    def test_config_manager_inpaint_with_partial_fields(self, temp_config_dir):
        """Test inpaint config with some fields specified."""
        config_file = temp_config_dir / "config.yaml"
        config_data = {
            "video_path": "/tmp/video.mp4",
            "mask_path": "/tmp/mask.png",
            "output_dir": "/tmp/output",
            "inpaint": {
                "steps": 30,
                # Other fields will use defaults
            },
        }

        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        manager = ConfigManager(str(config_file))
        config = manager.load()

        assert config.inpaint.steps == 30
        assert config.inpaint.model_name == "flux-dev.safetensors"  # Default
        assert config.inpaint.cfg_scale == 7.5  # Default

    def test_config_manager_no_inpaint_section(self, temp_config_dir):
        """Test that default InpaintConfig is used if inpaint section is missing."""
        config_file = temp_config_dir / "config.yaml"
        config_data = {
            "video_path": "/tmp/video.mp4",
            "mask_path": "/tmp/mask.png",
            "output_dir": "/tmp/output",
            # No inpaint section
        }

        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        manager = ConfigManager(str(config_file))
        config = manager.load()

        # All inpaint defaults should apply
        assert config.inpaint.model_name == "flux-dev.safetensors"
        assert config.inpaint.prompt == "remove watermark, clean background"
        assert config.inpaint.steps == 20
        assert config.inpaint.cfg_scale == 7.5


class TestEnsembleConfiguration:
    """Test ensemble detection configuration handling."""

    def test_ensemble_detection_disabled_by_default(self, base_config_dict):
        """Test that ensemble detection is disabled by default."""
        config_dict = base_config_dict.copy()
        config = ProcessConfig(**config_dict)
        assert config.ensemble_detection_enabled is False

    def test_ensemble_detection_enabled(self, base_config_dict):
        """Test enabling ensemble detection via config."""
        config_dict = base_config_dict.copy()
        config_dict["ensemble_detection_enabled"] = True
        config_dict["ensemble_models"] = ["yolov5s", "yolov5m"]
        config = ProcessConfig(**config_dict)
        assert config.ensemble_detection_enabled is True
        assert config.ensemble_models == ["yolov5s", "yolov5m"]

    def test_ensemble_default_models(self, base_config_dict):
        """Test default ensemble models."""
        config_dict = base_config_dict.copy()
        config = ProcessConfig(**config_dict)
        assert config.ensemble_models == ["yolov5s", "yolov5m"]

    def test_ensemble_custom_models(self, base_config_dict):
        """Test custom ensemble models."""
        config_dict = base_config_dict.copy()
        config_dict["ensemble_models"] = ["yolov5m", "yolov5l"]
        config = ProcessConfig(**config_dict)
        assert config.ensemble_models == ["yolov5m", "yolov5l"]

    def test_ensemble_voting_mode(self, base_config_dict):
        """Test ensemble voting mode."""
        config_dict = base_config_dict.copy()
        config_dict["ensemble_voting_mode"] = "confidence_weighted"
        config = ProcessConfig(**config_dict)
        assert config.ensemble_voting_mode == "confidence_weighted"

    def test_ensemble_iou_threshold(self, base_config_dict):
        """Test ensemble IoU threshold configuration."""
        config_dict = base_config_dict.copy()
        config_dict["ensemble_iou_threshold"] = 0.4
        config = ProcessConfig(**config_dict)
        assert config.ensemble_iou_threshold == 0.4

    def test_ensemble_nms_threshold(self, base_config_dict):
        """Test ensemble NMS threshold configuration."""
        config_dict = base_config_dict.copy()
        config_dict["ensemble_nms_threshold"] = 0.5
        config = ProcessConfig(**config_dict)
        assert config.ensemble_nms_threshold == 0.5

    def test_ensemble_model_accuracies(self, base_config_dict):
        """Test ensemble model accuracies configuration."""
        config_dict = base_config_dict.copy()
        config_dict["ensemble_model_accuracies"] = {"yolov5s": 0.80, "yolov5m": 0.92}
        config = ProcessConfig(**config_dict)
        assert config.ensemble_model_accuracies["yolov5s"] == 0.80
        assert config.ensemble_model_accuracies["yolov5m"] == 0.92

    def test_ensemble_validation_models_empty_when_enabled(self, base_config_dict):
        """Test validation: models list cannot be empty when ensemble is enabled."""
        config_dict = base_config_dict.copy()
        config_dict["ensemble_detection_enabled"] = True
        config_dict["ensemble_models"] = []
        with pytest.raises(ValueError, match="ensemble_models must not be empty"):
            ProcessConfig(**config_dict)

    def test_ensemble_validation_invalid_voting_mode(self, base_config_dict):
        """Test validation: only 'confidence_weighted' voting mode is allowed."""
        config_dict = base_config_dict.copy()
        config_dict["ensemble_detection_enabled"] = True
        config_dict["ensemble_voting_mode"] = "invalid_mode"
        with pytest.raises(ValueError, match="ensemble_voting_mode must be"):
            ProcessConfig(**config_dict)

    def test_ensemble_validation_invalid_iou_threshold(self, base_config_dict):
        """Test validation: IoU threshold must be in (0.0, 1.0]."""
        config_dict = base_config_dict.copy()
        config_dict["ensemble_detection_enabled"] = True
        config_dict["ensemble_iou_threshold"] = 0.0
        with pytest.raises(ValueError, match="ensemble_iou_threshold"):
            ProcessConfig(**config_dict)

    def test_ensemble_validation_nms_threshold_range(self, base_config_dict):
        """Test validation: NMS threshold must be in [0.0, 1.0]."""
        config_dict = base_config_dict.copy()
        config_dict["ensemble_detection_enabled"] = True
        config_dict["ensemble_nms_threshold"] = 1.5
        with pytest.raises(ValueError, match="ensemble_nms_threshold"):
            ProcessConfig(**config_dict)
