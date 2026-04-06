"""
Unit tests for watermark_removal.core.types module.

Tests all dataclasses and enums:
- Happy path: construct all types with valid inputs
- Edge cases: boundary values, minimal configs, full configs
- Enum values: all MaskType variants are handled
"""

import pytest
import numpy as np
from pathlib import Path

from src.watermark_removal.core.types import (
    MaskType,
    Frame,
    Mask,
    CropRegion,
    InpaintConfig,
    ProcessConfig,
)


class TestMaskType:
    """Test MaskType enum."""

    def test_mask_type_values(self):
        """All enum values are accessible."""
        assert MaskType.IMAGE.value == "image"
        assert MaskType.BBOX.value == "bbox"
        assert MaskType.POINTS.value == "points"

    def test_mask_type_from_string(self):
        """Enum can be constructed from string value."""
        assert MaskType("image") == MaskType.IMAGE
        assert MaskType("bbox") == MaskType.BBOX


class TestFrame:
    """Test Frame dataclass."""

    def test_frame_construction(self):
        """Construct Frame with required fields."""
        image = np.zeros((1080, 1920, 3), dtype=np.uint8)
        frame = Frame(frame_id=0, image=image, timestamp_ms=0.0)

        assert frame.frame_id == 0
        assert frame.image.shape == (1080, 1920, 3)
        assert frame.timestamp_ms == 0.0

    def test_frame_timestamp_calculation(self):
        """Frame timestamps reflect video progression."""
        image = np.zeros((720, 1280, 3), dtype=np.uint8)
        frame_0 = Frame(frame_id=0, image=image, timestamp_ms=0.0)
        frame_1 = Frame(frame_id=1, image=image, timestamp_ms=33.33)  # 30fps
        frame_30 = Frame(frame_id=30, image=image, timestamp_ms=1000.0)  # 1 second

        assert frame_30.timestamp_ms > frame_1.timestamp_ms > frame_0.timestamp_ms

    def test_frame_repr(self):
        """Frame repr includes all fields."""
        image = np.zeros((100, 100, 3), dtype=np.uint8)
        frame = Frame(frame_id=5, image=image, timestamp_ms=166.67)
        repr_str = repr(frame)

        assert "frame_id=5" in repr_str
        assert "timestamp_ms=166.67" in repr_str


class TestMask:
    """Test Mask dataclass."""

    def test_mask_image_type(self):
        """Construct IMAGE-type mask."""
        mask_image = np.ones((100, 100), dtype=np.uint8) * 255
        mask = Mask(mask_type=MaskType.IMAGE, data=mask_image, valid_frame_range=(0, float('inf')))

        assert mask.mask_type == MaskType.IMAGE
        assert mask.data.shape == (100, 100)
        assert mask.valid_frame_range[1] == float('inf')

    def test_mask_bbox_type(self):
        """Construct BBOX-type mask."""
        bbox_data = {"0": {"x": 100, "y": 200, "w": 50, "h": 50}}
        mask = Mask(mask_type=MaskType.BBOX, data=bbox_data, valid_frame_range=(0, 1))

        assert mask.mask_type == MaskType.BBOX
        assert mask.data["0"]["x"] == 100

    def test_mask_defaults(self):
        """Mask with only type specified uses defaults."""
        mask = Mask(mask_type=MaskType.IMAGE)

        assert mask.data is None
        assert mask.valid_frame_range == (0, float('inf'))


class TestCropRegion:
    """Test CropRegion dataclass (central mapping object)."""

    def test_crop_region_construction(self):
        """Construct CropRegion with full metadata."""
        region = CropRegion(
            frame_id=5,
            original_bbox=(100, 200, 50, 50),
            context_bbox=(50, 150, 150, 150),
            scale_factor=2.0,
            pad_left=10,
            pad_top=10,
            pad_right=20,
            pad_bottom=20,
        )

        assert region.frame_id == 5
        assert region.original_bbox == (100, 200, 50, 50)
        assert region.scale_factor == 2.0

    def test_crop_region_at_origin(self):
        """CropRegion at frame origin (0, 0)."""
        region = CropRegion(
            frame_id=0,
            original_bbox=(0, 0, 50, 50),
            context_bbox=(0, 0, 100, 100),
            scale_factor=10.24,
        )

        assert region.original_bbox[0] == 0
        assert region.original_bbox[1] == 0

    def test_crop_region_full_frame(self):
        """CropRegion covering full frame."""
        region = CropRegion(
            frame_id=0,
            original_bbox=(0, 0, 1920, 1080),
            context_bbox=(0, 0, 1920, 1080),
            scale_factor=1.0,
        )

        assert region.original_bbox[2] == 1920
        assert region.original_bbox[3] == 1080


class TestInpaintConfig:
    """Test InpaintConfig dataclass."""

    def test_inpaint_config_defaults(self):
        """InpaintConfig uses sensible defaults."""
        config = InpaintConfig()

        assert config.model_name == "flux-dev"
        assert config.steps == 20
        assert config.cfg_scale == 7.5
        assert config.seed == -1

    def test_inpaint_config_custom(self):
        """InpaintConfig with custom values."""
        config = InpaintConfig(
            model_name="sdxl-base",
            steps=30,
            cfg_scale=10.0,
            seed=42,
        )

        assert config.model_name == "sdxl-base"
        assert config.steps == 30
        assert config.seed == 42


class TestProcessConfig:
    """Test ProcessConfig (system-wide configuration)."""

    def test_process_config_minimal(self):
        """ProcessConfig with only required fields."""
        config = ProcessConfig(
            video_path="input.mp4",
            mask_path="mask.png",
        )

        assert config.video_path == Path("input.mp4")
        assert config.mask_path == Path("mask.png")
        assert config.output_dir == Path("output")

    def test_process_config_path_conversion(self):
        """String paths are converted to Path objects."""
        config = ProcessConfig(
            video_path="/path/to/video.mp4",
            mask_path="/path/to/mask.json",
            output_dir="/tmp/output",
        )

        assert isinstance(config.video_path, Path)
        assert isinstance(config.mask_path, Path)
        assert isinstance(config.output_dir, Path)

    def test_process_config_defaults(self):
        """ProcessConfig applies sensible defaults."""
        config = ProcessConfig(
            video_path="video.mp4",
            mask_path="mask.png",
        )

        assert config.context_padding == 64
        assert config.target_inpaint_size == 1024
        assert config.blend_feather_width == 32
        assert config.batch_size == 4
        assert config.inpaint_timeout_sec == 300.0
        assert config.comfyui_host == "127.0.0.1"
        assert config.comfyui_port == 8188

    def test_process_config_custom_inpaint(self):
        """ProcessConfig with custom InpaintConfig."""
        inpaint_cfg = InpaintConfig(model_name="sdxl-base", steps=40)
        config = ProcessConfig(
            video_path="video.mp4",
            mask_path="mask.png",
            inpaint=inpaint_cfg,
        )

        assert config.inpaint.model_name == "sdxl-base"
        assert config.inpaint.steps == 40

    def test_process_config_full(self):
        """ProcessConfig with all fields specified."""
        inpaint_cfg = InpaintConfig(steps=50, cfg_scale=12.0)
        config = ProcessConfig(
            video_path="video.mp4",
            mask_path="mask.json",
            output_dir="output",
            inpaint=inpaint_cfg,
            context_padding=128,
            target_inpaint_size=2048,
            blend_feather_width=64,
            batch_size=8,
            comfyui_host="192.168.1.100",
            comfyui_port=9999,
            keep_intermediate=True,
        )

        assert config.context_padding == 128
        assert config.target_inpaint_size == 2048
        assert config.blend_feather_width == 64
        assert config.batch_size == 8
        assert config.comfyui_host == "192.168.1.100"
        assert config.comfyui_port == 9999
        assert config.keep_intermediate is True

    def test_process_config_repr(self):
        """ProcessConfig repr shows key fields."""
        config = ProcessConfig(
            video_path="input.mp4",
            mask_path="mask.png",
        )
        repr_str = repr(config)

        assert "video_path" in repr_str
        assert "mask_path" in repr_str


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
