"""
Unit tests for watermark_removal.core.config_manager module.

Tests configuration loading, validation, and ProcessConfig construction.
"""

import pytest
import tempfile
from pathlib import Path
import yaml

from src.watermark_removal.core.config_manager import ConfigManager
from src.watermark_removal.core.types import ProcessConfig, InpaintConfig


@pytest.fixture
def temp_config_dir():
    """Create temporary directory for config files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


class TestConfigManager:
    """Test ConfigManager class."""

    def test_config_file_not_found(self):
        """Raise FileNotFoundError if config file missing."""
        with pytest.raises(FileNotFoundError):
            ConfigManager("/nonexistent/path/config.yaml")

    def test_load_valid_config_minimal(self, temp_config_dir):
        """Load valid config with only required fields."""
        config_file = temp_config_dir / "minimal.yaml"
        config_data = {
            "video_path": "input.mp4",
            "mask_path": "mask.png",
        }
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        manager = ConfigManager(config_file)
        config = manager.load()

        assert isinstance(config, ProcessConfig)
        assert config.video_path == Path("input.mp4")
        assert config.mask_path == Path("mask.png")
        assert config.output_dir == Path("output")  # default

    def test_load_config_with_defaults(self, temp_config_dir):
        """Load config and verify defaults are applied."""
        config_file = temp_config_dir / "defaults.yaml"
        config_data = {
            "video_path": "video.mp4",
            "mask_path": "mask.json",
        }
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        manager = ConfigManager(config_file)
        config = manager.load()

        # Verify defaults
        assert config.context_padding == 64
        assert config.target_inpaint_size == 1024
        assert config.blend_feather_width == 32
        assert config.batch_size == 4
        assert config.comfyui_host == "127.0.0.1"
        assert config.comfyui_port == 8188

    def test_load_config_missing_required_field(self, temp_config_dir):
        """Raise ValueError if required field missing."""
        config_file = temp_config_dir / "incomplete.yaml"
        config_data = {
            "video_path": "input.mp4",
            # missing mask_path
        }
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        manager = ConfigManager(config_file)
        with pytest.raises(ValueError) as exc_info:
            manager.load()

        assert "mask_path" in str(exc_info.value)
        assert "required" in str(exc_info.value).lower()

    def test_load_config_with_custom_inpaint(self, temp_config_dir):
        """Load config with custom inpaint parameters."""
        config_file = temp_config_dir / "inpaint.yaml"
        config_data = {
            "video_path": "video.mp4",
            "mask_path": "mask.png",
            "inpaint": {
                "model_name": "sdxl-base",
                "steps": 40,
                "cfg_scale": 10.0,
                "seed": 42,
            },
        }
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        manager = ConfigManager(config_file)
        config = manager.load()

        assert config.inpaint.model_name == "sdxl-base"
        assert config.inpaint.steps == 40
        assert config.inpaint.cfg_scale == 10.0
        assert config.inpaint.seed == 42

    def test_load_config_with_custom_paths(self, temp_config_dir):
        """Load config with custom output and paths."""
        config_file = temp_config_dir / "paths.yaml"
        config_data = {
            "video_path": "/path/to/video.mp4",
            "mask_path": "/path/to/mask.json",
            "output_dir": "/tmp/watermark_output",
        }
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        manager = ConfigManager(config_file)
        config = manager.load()

        assert config.video_path == Path("/path/to/video.mp4")
        assert config.mask_path == Path("/path/to/mask.json")
        assert config.output_dir == Path("/tmp/watermark_output")

    def test_load_config_with_custom_parameters(self, temp_config_dir):
        """Load config with custom processing parameters."""
        config_file = temp_config_dir / "custom.yaml"
        config_data = {
            "video_path": "video.mp4",
            "mask_path": "mask.png",
            "output_dir": "output",
            "context_padding": 128,
            "target_inpaint_size": 2048,
            "blend_feather_width": 64,
            "batch_size": 8,
            "inpaint_timeout_sec": 600.0,
            "comfyui_host": "192.168.1.100",
            "comfyui_port": 9999,
            "keep_intermediate": True,
        }
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        manager = ConfigManager(config_file)
        config = manager.load()

        assert config.context_padding == 128
        assert config.target_inpaint_size == 2048
        assert config.blend_feather_width == 64
        assert config.batch_size == 8
        assert config.inpaint_timeout_sec == 600.0
        assert config.comfyui_host == "192.168.1.100"
        assert config.comfyui_port == 9999
        assert config.keep_intermediate is True

    def test_load_config_empty_file(self, temp_config_dir):
        """Raise ValueError if YAML is empty or None."""
        config_file = temp_config_dir / "empty.yaml"
        with open(config_file, "w") as f:
            f.write("")  # Empty file

        manager = ConfigManager(config_file)
        with pytest.raises(ValueError) as exc_info:
            manager.load()

        assert "video_path" in str(exc_info.value)

    def test_load_config_relative_paths(self, temp_config_dir):
        """Load config with relative paths (resolved from cwd)."""
        config_file = temp_config_dir / "relative.yaml"
        config_data = {
            "video_path": "./input/video.mp4",
            "mask_path": "./input/mask.png",
            "output_dir": "./output/watermark",
        }
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        manager = ConfigManager(config_file)
        config = manager.load()

        # Paths should be relative (Path normalizes path separators per platform)
        assert config.video_path == Path("input/video.mp4")
        assert config.mask_path == Path("input/mask.png")

    def test_load_config_with_comments(self, temp_config_dir):
        """Load config with YAML comments (should be ignored)."""
        config_file = temp_config_dir / "commented.yaml"
        config_text = """
# Video input file
video_path: video.mp4

# Watermark mask file
mask_path: mask.png

# Output directory
output_dir: output
"""
        with open(config_file, "w") as f:
            f.write(config_text)

        manager = ConfigManager(config_file)
        config = manager.load()

        assert config.video_path == Path("video.mp4")
        assert config.mask_path == Path("mask.png")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
