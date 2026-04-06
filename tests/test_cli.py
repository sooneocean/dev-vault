"""Tests for CLI entry point."""

import asyncio
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import cv2
import numpy as np
import pytest

from src.watermark_removal.core.config_manager import ConfigManager
from src.watermark_removal.core.types import ProcessConfig


def create_test_yaml_config(path: str) -> None:
    """Create a test YAML config file."""
    yaml_content = """
video_path: input.mp4
mask_path: mask.png
output_dir: ./output

inpaint:
  model_name: flux-dev.safetensors
  prompt: remove watermark
  negative_prompt: artifacts
  steps: 20
  cfg_scale: 7.5
  seed: 42
  sampler: euler

context_padding: 50
target_inpaint_size: 1024
batch_size: 4
timeout: 300.0
output_codec: h264
output_crf: 23
output_fps: 30.0
keep_intermediate: false
verbose: true
"""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(yaml_content)


class TestConfigManager:
    """Test ConfigManager functionality."""

    def test_config_manager_initialization(self):
        """Test ConfigManager initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = f"{tmpdir}/config.yaml"
            create_test_yaml_config(config_path)

            manager = ConfigManager(config_path)
            assert manager.config_path == Path(config_path).resolve()

    def test_config_manager_missing_file(self):
        """Test error when config file missing."""
        with pytest.raises(FileNotFoundError, match="Config file not found"):
            ConfigManager("/nonexistent/config.yaml")

    def test_config_manager_load(self):
        """Test loading and parsing YAML config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = f"{tmpdir}/config.yaml"
            create_test_yaml_config(config_path)

            manager = ConfigManager(config_path)
            config = manager.load()

            assert isinstance(config, ProcessConfig)
            assert config.output_codec == "h264"
            assert config.output_crf == 23
            assert config.batch_size == 4
            assert config.inpaint.steps == 20

    def test_config_manager_with_new_fields(self):
        """Test ConfigManager handles new pipeline fields."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = f"{tmpdir}/config.yaml"
            yaml_content = """
video_path: input.mp4
mask_path: mask.png
output_dir: ./output

comfyui_host: 192.168.1.100
comfyui_port: 9000
blend_feather_width: 64
output_fps: 24.0
skip_errors_in_preprocessing: true

inpaint:
  model_name: flux-dev.safetensors
"""
            Path(config_path).parent.mkdir(parents=True, exist_ok=True)
            Path(config_path).write_text(yaml_content)

            manager = ConfigManager(config_path)
            config = manager.load()

            assert config.comfyui_host == "192.168.1.100"
            assert config.comfyui_port == 9000
            assert config.blend_feather_width == 64
            assert config.output_fps == 24.0
            assert config.skip_errors_in_preprocessing is True

    def test_config_manager_missing_required_fields(self):
        """Test error when required fields missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = f"{tmpdir}/config.yaml"
            yaml_content = """
video_path: input.mp4
# mask_path: missing!
output_dir: ./output
"""
            Path(config_path).parent.mkdir(parents=True, exist_ok=True)
            Path(config_path).write_text(yaml_content)

            manager = ConfigManager(config_path)
            with pytest.raises(ValueError, match="Required config field missing"):
                manager.load()

    def test_config_manager_invalid_yaml(self):
        """Test error with invalid YAML syntax."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = f"{tmpdir}/config.yaml"
            yaml_content = """
this is not: valid: yaml: syntax:
"""
            Path(config_path).parent.mkdir(parents=True, exist_ok=True)
            Path(config_path).write_text(yaml_content)

            manager = ConfigManager(config_path)
            with pytest.raises(Exception):  # yaml.YAMLError or similar
                manager.load()


class TestConfigOverrides:
    """Test CLI parameter override behavior."""

    def test_config_path_resolution(self):
        """Test that config paths are resolved to absolute."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = f"{tmpdir}/config.yaml"
            create_test_yaml_config(config_path)

            manager = ConfigManager(config_path)
            config = manager.load()

            # Paths should be absolute after loading
            assert Path(config.video_path).is_absolute()
            assert Path(config.mask_path).is_absolute()
            assert Path(config.output_dir).is_absolute()

    def test_config_defaults(self):
        """Test that config uses correct defaults."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = f"{tmpdir}/config.yaml"
            # Minimal YAML with only required fields
            yaml_content = """
video_path: input.mp4
mask_path: mask.png
output_dir: ./output
"""
            Path(config_path).parent.mkdir(parents=True, exist_ok=True)
            Path(config_path).write_text(yaml_content)

            manager = ConfigManager(config_path)
            config = manager.load()

            # Should have defaults for optional fields
            assert config.batch_size == 4
            assert config.output_codec == "h264"
            assert config.output_crf == 23
            assert config.output_fps == 30.0
            assert config.blend_feather_width == 32
            assert config.comfyui_host == "127.0.0.1"
            assert config.comfyui_port == 8188


class TestConfigValidation:
    """Test ProcessConfig validation."""

    def test_config_validation_invalid_crf(self):
        """Test that invalid CRF raises error on load."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = f"{tmpdir}/config.yaml"
            yaml_content = """
video_path: input.mp4
mask_path: mask.png
output_dir: ./output

output_crf: 100
"""
            Path(config_path).parent.mkdir(parents=True, exist_ok=True)
            Path(config_path).write_text(yaml_content)

            manager = ConfigManager(config_path)
            # Validation should raise ValueError during load for invalid CRF
            with pytest.raises(ValueError, match="output_crf"):
                manager.load()

    def test_config_validation_invalid_batch_size(self):
        """Test that invalid batch_size raises error on load."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = f"{tmpdir}/config.yaml"
            yaml_content = """
video_path: input.mp4
mask_path: mask.png
output_dir: ./output

batch_size: 0
"""
            Path(config_path).parent.mkdir(parents=True, exist_ok=True)
            Path(config_path).write_text(yaml_content)

            manager = ConfigManager(config_path)
            # Validation should raise ValueError during load for batch_size < 1
            with pytest.raises(ValueError, match="batch_size"):
                manager.load()
