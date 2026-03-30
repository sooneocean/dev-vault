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
