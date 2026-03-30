"""Tests for core data types."""

import numpy as np
import pytest

from src.watermark_removal.core.types import (
    CropRegion,
    Frame,
    InpaintConfig,
    Mask,
    MaskType,
    ProcessConfig,
)


class TestMaskType:
    """Tests for MaskType enum."""

    def test_enum_values(self):
        """Verify all enum values exist."""
        assert MaskType.IMAGE.value == "image"
        assert MaskType.BBOX.value == "bbox"
        assert MaskType.POINTS.value == "points"

    def test_enum_string_conversion(self):
        """Verify enum can be created from string."""
        assert MaskType("image") == MaskType.IMAGE
        assert MaskType("bbox") == MaskType.BBOX


class TestFrame:
    """Tests for Frame dataclass."""

    def test_frame_creation(self):
        """Test basic Frame instantiation."""
        image = np.zeros((480, 640, 3), dtype=np.uint8)
        frame = Frame(frame_id=0, image=image, timestamp_ms=0.0)

        assert frame.frame_id == 0
        assert frame.image.shape == (480, 640, 3)
        assert frame.timestamp_ms == 0.0

    def test_frame_with_different_resolutions(self):
        """Test Frame with various image dimensions."""
        for h, w in [(1080, 1920), (720, 1280), (480, 640)]:
            image = np.ones((h, w, 3), dtype=np.uint8)
            frame = Frame(frame_id=0, image=image, timestamp_ms=0.0)
            assert frame.image.shape == (h, w, 3)

    def test_frame_with_timestamps(self):
        """Test Frame with various timestamps."""
        image = np.zeros((480, 640, 3), dtype=np.uint8)
        for ts in [0.0, 33.33, 1000.0]:
            frame = Frame(frame_id=0, image=image, timestamp_ms=ts)
            assert frame.timestamp_ms == ts


class TestMask:
    """Tests for Mask dataclass."""

    def test_mask_image_type(self):
        """Test Mask with IMAGE type."""
        image = np.zeros((480, 640), dtype=np.uint8)
        mask = Mask(type=MaskType.IMAGE, data=image, valid_frame_range=(0, 1000))

        assert mask.type == MaskType.IMAGE
        assert mask.data.shape == (480, 640)
        assert mask.valid_frame_range == (0, 1000)

    def test_mask_bbox_type(self):
        """Test Mask with BBOX type."""
        bbox = {"x": 100, "y": 200, "w": 50, "h": 50}
        mask = Mask(type=MaskType.BBOX, data=bbox, valid_frame_range=(5, 5))

        assert mask.type == MaskType.BBOX
        assert mask.data == bbox
        assert mask.valid_frame_range == (5, 5)

    def test_mask_with_sparse_frame_range(self):
        """Test Mask with sparse frame ID validity."""
        bbox = {"x": 0, "y": 0, "w": 100, "h": 100}
        mask = Mask(type=MaskType.BBOX, data=bbox, valid_frame_range=(0, 0))
        assert mask.valid_frame_range == (0, 0)


class TestCropRegion:
    """Tests for CropRegion dataclass."""

    def test_crop_region_basic(self):
        """Test basic CropRegion instantiation."""
        crop = CropRegion(
            x=100, y=200, w=50, h=50,
            scale_factor=2.0,
            context_x=50, context_y=150, context_w=150, context_h=150,
        )

        assert crop.x == 100
        assert crop.y == 200
        assert crop.w == 50
        assert crop.h == 50
        assert crop.scale_factor == 2.0

    def test_crop_region_at_boundary(self):
        """Test CropRegion at image boundary (0, 0)."""
        crop = CropRegion(
            x=0, y=0, w=100, h=100,
            scale_factor=1.0,
            context_x=0, context_y=0, context_w=100, context_h=100,
        )

        assert crop.x == 0
        assert crop.y == 0
        assert crop.context_x == 0
        assert crop.context_y == 0

    def test_crop_region_full_size(self):
        """Test CropRegion at full frame size."""
        crop = CropRegion(
            x=0, y=0, w=1920, h=1080,
            scale_factor=1.0,
            context_x=0, context_y=0, context_w=1920, context_h=1080,
        )

        assert crop.w == 1920
        assert crop.h == 1080
        assert crop.context_w == 1920
        assert crop.context_h == 1080

    def test_crop_region_with_padding(self):
        """Test CropRegion with padding applied."""
        crop = CropRegion(
            x=100, y=100, w=50, h=50,
            scale_factor=0.5,
            context_x=50, context_y=50, context_w=150, context_h=150,
            pad_left=10, pad_top=10, pad_right=10, pad_bottom=10,
        )

        assert crop.pad_left == 10
        assert crop.pad_top == 10
        assert crop.pad_right == 10
        assert crop.pad_bottom == 10


class TestInpaintConfig:
    """Tests for InpaintConfig dataclass."""

    def test_inpaint_config_defaults(self):
        """Test InpaintConfig with default values."""
        config = InpaintConfig()

        assert config.model_name == "flux-dev.safetensors"
        assert config.steps == 20
        assert config.cfg_scale == 7.5
        assert config.seed == 42

    def test_inpaint_config_custom(self):
        """Test InpaintConfig with custom values."""
        config = InpaintConfig(
            model_name="sdxl-1.0.safetensors",
            prompt="custom prompt",
            negative_prompt="custom negative",
            steps=50,
            cfg_scale=10.0,
            seed=100,
        )

        assert config.model_name == "sdxl-1.0.safetensors"
        assert config.prompt == "custom prompt"
        assert config.negative_prompt == "custom negative"
        assert config.steps == 50
        assert config.cfg_scale == 10.0
        assert config.seed == 100


class TestProcessConfig:
    """Tests for ProcessConfig dataclass."""

    def test_process_config_minimal(self):
        """Test ProcessConfig with only required fields."""
        config = ProcessConfig(
            video_path="/tmp/video.mp4",
            mask_path="/tmp/mask.png",
            output_dir="/tmp/output",
        )

        assert config.video_path.endswith("video.mp4")
        assert config.mask_path.endswith("mask.png")
        assert config.output_dir.endswith("output")
        # Verify defaults are applied
        assert config.context_padding == 50
        assert config.target_inpaint_size == 1024
        assert config.batch_size == 4
        assert config.timeout == 300.0

    def test_process_config_with_inpaint_override(self):
        """Test ProcessConfig with custom InpaintConfig."""
        inpaint = InpaintConfig(model_name="custom-model.safetensors")
        config = ProcessConfig(
            video_path="/tmp/video.mp4",
            mask_path="/tmp/mask.png",
            output_dir="/tmp/output",
            inpaint=inpaint,
        )

        assert config.inpaint.model_name == "custom-model.safetensors"

    def test_process_config_validation_missing_video(self):
        """Test ProcessConfig raises ValueError if video_path missing."""
        with pytest.raises(ValueError, match="video_path is required"):
            ProcessConfig(video_path="", mask_path="/tmp/mask.png", output_dir="/tmp/output")

    def test_process_config_validation_missing_mask(self):
        """Test ProcessConfig raises ValueError if mask_path missing."""
        with pytest.raises(ValueError, match="mask_path is required"):
            ProcessConfig(video_path="/tmp/video.mp4", mask_path="", output_dir="/tmp/output")

    def test_process_config_validation_missing_output(self):
        """Test ProcessConfig raises ValueError if output_dir missing."""
        with pytest.raises(ValueError, match="output_dir is required"):
            ProcessConfig(video_path="/tmp/video.mp4", mask_path="/tmp/mask.png", output_dir="")

    def test_process_config_validation_padding(self):
        """Test ProcessConfig validates context_padding."""
        with pytest.raises(ValueError, match="context_padding must be >= 0"):
            ProcessConfig(
                video_path="/tmp/video.mp4",
                mask_path="/tmp/mask.png",
                output_dir="/tmp/output",
                context_padding=-1,
            )

    def test_process_config_validation_inpaint_size(self):
        """Test ProcessConfig validates target_inpaint_size."""
        with pytest.raises(ValueError, match="target_inpaint_size must be >= 256"):
            ProcessConfig(
                video_path="/tmp/video.mp4",
                mask_path="/tmp/mask.png",
                output_dir="/tmp/output",
                target_inpaint_size=128,
            )

    def test_process_config_validation_batch_size(self):
        """Test ProcessConfig validates batch_size."""
        with pytest.raises(ValueError, match="batch_size must be >= 1"):
            ProcessConfig(
                video_path="/tmp/video.mp4",
                mask_path="/tmp/mask.png",
                output_dir="/tmp/output",
                batch_size=0,
            )

    def test_process_config_validation_timeout(self):
        """Test ProcessConfig validates timeout."""
        with pytest.raises(ValueError, match="timeout must be > 0"):
            ProcessConfig(
                video_path="/tmp/video.mp4",
                mask_path="/tmp/mask.png",
                output_dir="/tmp/output",
                timeout=-1,
            )

    def test_process_config_validation_crf(self):
        """Test ProcessConfig validates output_crf."""
        with pytest.raises(ValueError, match="output_crf must be 0-51"):
            ProcessConfig(
                video_path="/tmp/video.mp4",
                mask_path="/tmp/mask.png",
                output_dir="/tmp/output",
                output_crf=100,
            )

    def test_process_config_path_resolution(self):
        """Test ProcessConfig resolves relative paths."""
        config = ProcessConfig(
            video_path="video.mp4",
            mask_path="mask.png",
            output_dir="output",
        )

        # Paths should be resolved to absolute
        assert "/" in config.video_path or "\\" in config.video_path
        assert "video.mp4" in config.video_path
        assert "mask.png" in config.mask_path
        assert "output" in config.output_dir


class TestTypeImportability:
    """Tests for type importability and basic instantiation."""

    def test_all_types_importable(self):
        """Verify all types can be imported."""
        from src.watermark_removal.core.types import (
            CropRegion,
            Frame,
            InpaintConfig,
            Mask,
            MaskType,
            ProcessConfig,
        )

        # If import succeeds, test passes

    def test_all_types_instantiable(self):
        """Verify all types can be instantiated without complex setup."""
        # MaskType
        assert MaskType.IMAGE is not None

        # Frame
        frame = Frame(
            frame_id=0,
            image=np.zeros((480, 640, 3), dtype=np.uint8),
            timestamp_ms=0.0,
        )
        assert frame is not None

        # Mask
        mask = Mask(
            type=MaskType.IMAGE,
            data=np.zeros((480, 640), dtype=np.uint8),
            valid_frame_range=(0, 100),
        )
        assert mask is not None

        # CropRegion
        crop = CropRegion(
            x=0, y=0, w=100, h=100,
            scale_factor=1.0,
            context_x=0, context_y=0, context_w=100, context_h=100,
        )
        assert crop is not None

        # InpaintConfig
        inpaint = InpaintConfig()
        assert inpaint is not None

        # ProcessConfig
        config = ProcessConfig(
            video_path="/tmp/video.mp4",
            mask_path="/tmp/mask.png",
            output_dir="/tmp/output",
        )
        assert config is not None
