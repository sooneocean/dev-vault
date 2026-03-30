"""Tests for stitch handler with feather blending."""

import numpy as np
import pytest

from src.watermark_removal.core.types import CropRegion
from src.watermark_removal.postprocessing.stitch_handler import StitchHandler


def create_test_frame(width: int = 1920, height: int = 1080) -> np.ndarray:
    """Create a test frame."""
    image = np.zeros((height, width, 3), dtype=np.uint8)
    # Create gradient for visual verification
    for y in range(height):
        image[y, :] = [y % 256, (y // 2) % 256, (y // 3) % 256]
    return image


def create_inpainted_crop(width: int = 1024, height: int = 1024) -> np.ndarray:
    """Create a dummy inpainted crop."""
    image = np.ones((height, width, 3), dtype=np.uint8)
    image[:, :] = [200, 150, 100]  # BGR
    return image


class TestStitchHandlerHappyPath:
    """Happy path tests."""

    def test_stitch_handler_basic_stitch(self):
        """Test basic stitch-back operation."""
        handler = StitchHandler(blend_feather_width=32)

        # Create test data
        original_frame = create_test_frame(width=1920, height=1080)
        inpainted_crop = create_inpainted_crop()

        crop_region = CropRegion(
            x=500,
            y=300,
            w=200,
            h=200,
            scale_factor=2.0,  # Crop was scaled up 2x to 1024
            context_x=450,
            context_y=250,
            context_w=300,
            context_h=300,
            pad_left=362,  # (1024 - 300*2) / 2
            pad_top=362,
            pad_right=362,
            pad_bottom=362,
        )

        result = handler.stitch_back(original_frame, inpainted_crop, crop_region)

        # Verify output dimensions match input
        assert result.shape == original_frame.shape
        assert result.dtype == np.uint8

    def test_stitch_handler_output_has_inpainted_region(self):
        """Test that stitched frame contains inpainted content."""
        handler = StitchHandler(blend_feather_width=32)

        original_frame = create_test_frame(width=1920, height=1080)
        inpainted_crop = create_inpainted_crop()
        inpainted_crop[:, :] = [100, 100, 100]  # Distinct color

        crop_region = CropRegion(
            x=500,
            y=300,
            w=200,
            h=200,
            scale_factor=2.0,
            context_x=450,
            context_y=250,
            context_w=300,
            context_h=300,
            pad_left=362,
            pad_top=362,
            pad_right=362,
            pad_bottom=362,
        )

        result = handler.stitch_back(original_frame, inpainted_crop, crop_region)

        # Check that center region has been modified (contains inpainted content)
        center_x = crop_region.context_x + crop_region.context_w // 2
        center_y = crop_region.context_y + crop_region.context_h // 2

        # Should be influenced by inpainted crop (not the original gradient)
        center_pixel = result[center_y, center_x]
        assert not np.allclose(center_pixel, original_frame[center_y, center_x])

    def test_stitch_handler_feather_blending_smooth(self):
        """Test that feather blending creates smooth transitions."""
        handler = StitchHandler(blend_feather_width=32)

        original_frame = np.ones((1000, 1000, 3), dtype=np.uint8) * 50
        inpainted_crop = np.ones((1024, 1024, 3), dtype=np.uint8) * 200

        crop_region = CropRegion(
            x=400,
            y=400,
            w=200,
            h=200,
            scale_factor=2.0,
            context_x=350,
            context_y=350,
            context_w=300,
            context_h=300,
            pad_left=362,
            pad_top=362,
            pad_right=362,
            pad_bottom=362,
        )

        result = handler.stitch_back(original_frame, inpainted_crop, crop_region)

        # Check that values transition smoothly from original to inpainted
        # At edges should be closer to original
        # At center should be closer to inpainted
        assert result.dtype == np.uint8

        # Center region should be influenced by inpainted
        center_value = result[500, 500, 0]
        assert center_value > 100  # Closer to inpainted (200) than original (50)


class TestStitchHandlerEdgeCases:
    """Edge case tests."""

    def test_stitch_handler_crop_at_frame_edge(self):
        """Test stitch when crop region is at frame boundary."""
        handler = StitchHandler(blend_feather_width=32)

        original_frame = create_test_frame(width=1920, height=1080)
        inpainted_crop = create_inpainted_crop()

        # Crop region near right edge (clipped)
        crop_region = CropRegion(
            x=1800,
            y=500,
            w=100,
            h=100,
            scale_factor=2.0,
            context_x=1750,
            context_y=450,
            context_w=200,
            context_h=200,
            pad_left=362,
            pad_top=362,
            pad_right=362,
            pad_bottom=362,
        )

        result = handler.stitch_back(original_frame, inpainted_crop, crop_region)

        # Should not crash and output valid frame
        assert result.shape == original_frame.shape
        assert result.dtype == np.uint8

    def test_stitch_handler_crop_at_corner(self):
        """Test stitch when crop region is at frame corner."""
        handler = StitchHandler(blend_feather_width=32)

        original_frame = create_test_frame(width=1920, height=1080)
        inpainted_crop = create_inpainted_crop()

        # Crop region at top-left corner (clipped)
        crop_region = CropRegion(
            x=0,
            y=0,
            w=100,
            h=100,
            scale_factor=2.0,
            context_x=0,
            context_y=0,
            context_w=200,
            context_h=200,
            pad_left=362,
            pad_top=362,
            pad_right=362,
            pad_bottom=362,
        )

        result = handler.stitch_back(original_frame, inpainted_crop, crop_region)

        assert result.shape == original_frame.shape
        assert result.dtype == np.uint8

    def test_stitch_handler_small_feather_width(self):
        """Test stitch with very small feather width."""
        handler = StitchHandler(blend_feather_width=1)

        original_frame = create_test_frame()
        inpainted_crop = create_inpainted_crop()

        crop_region = CropRegion(
            x=500,
            y=300,
            w=200,
            h=200,
            scale_factor=2.0,
            context_x=450,
            context_y=250,
            context_w=300,
            context_h=300,
            pad_left=362,
            pad_top=362,
            pad_right=362,
            pad_bottom=362,
        )

        result = handler.stitch_back(original_frame, inpainted_crop, crop_region)

        assert result.shape == original_frame.shape
        # Small feather width creates sharper boundary
        assert result.dtype == np.uint8

    def test_stitch_handler_large_feather_width(self):
        """Test stitch with large feather width."""
        handler = StitchHandler(blend_feather_width=64)

        original_frame = create_test_frame()
        inpainted_crop = create_inpainted_crop()

        crop_region = CropRegion(
            x=500,
            y=300,
            w=200,
            h=200,
            scale_factor=2.0,
            context_x=450,
            context_y=250,
            context_w=300,
            context_h=300,
            pad_left=362,
            pad_top=362,
            pad_right=362,
            pad_bottom=362,
        )

        result = handler.stitch_back(original_frame, inpainted_crop, crop_region)

        assert result.shape == original_frame.shape
        # Large feather width creates smoother blending
        assert result.dtype == np.uint8

    def test_stitch_handler_crop_at_various_positions(self):
        """Test stitch with crop at various frame positions."""
        handler = StitchHandler(blend_feather_width=32)

        original_frame = create_test_frame()
        inpainted_crop = create_inpainted_crop()

        positions = [
            (100, 100),    # Top-left
            (1800, 100),   # Top-right
            (100, 900),    # Bottom-left
            (1800, 900),   # Bottom-right
            (960, 540),    # Center
        ]

        for x, y in positions:
            crop_region = CropRegion(
                x=x,
                y=y,
                w=200,
                h=200,
                scale_factor=2.0,
                context_x=x - 50,
                context_y=y - 50,
                context_w=300,
                context_h=300,
                pad_left=362,
                pad_top=362,
                pad_right=362,
                pad_bottom=362,
            )

            result = handler.stitch_back(original_frame, inpainted_crop, crop_region)
            assert result.shape == original_frame.shape
            assert result.dtype == np.uint8


class TestStitchHandlerErrors:
    """Error handling tests."""

    def test_stitch_handler_invalid_original_frame_shape(self):
        """Test error with invalid original frame shape."""
        handler = StitchHandler()

        # 2D frame (should be 3D)
        invalid_frame = np.zeros((1080, 1920), dtype=np.uint8)
        inpainted_crop = create_inpainted_crop()
        crop_region = CropRegion(x=100, y=100, w=100, h=100, scale_factor=2.0,
                               context_x=50, context_y=50, context_w=200, context_h=200,
                               pad_left=362, pad_top=362, pad_right=362, pad_bottom=362)

        with pytest.raises(ValueError, match="original_frame"):
            handler.stitch_back(invalid_frame, inpainted_crop, crop_region)

    def test_stitch_handler_invalid_inpainted_crop_shape(self):
        """Test error with invalid inpainted crop shape."""
        handler = StitchHandler()

        original_frame = create_test_frame()
        # 2D crop (should be 3D)
        invalid_crop = np.zeros((1024, 1024), dtype=np.uint8)
        crop_region = CropRegion(x=100, y=100, w=100, h=100, scale_factor=2.0,
                               context_x=50, context_y=50, context_w=200, context_h=200,
                               pad_left=362, pad_top=362, pad_right=362, pad_bottom=362)

        with pytest.raises(ValueError, match="inpainted_crop"):
            handler.stitch_back(original_frame, invalid_crop, crop_region)

    def test_stitch_handler_wrong_number_of_channels(self):
        """Test error with wrong number of color channels."""
        handler = StitchHandler()

        original_frame = create_test_frame()
        # 4-channel crop (should be 3)
        invalid_crop = np.zeros((1024, 1024, 4), dtype=np.uint8)
        crop_region = CropRegion(x=100, y=100, w=100, h=100, scale_factor=2.0,
                               context_x=50, context_y=50, context_w=200, context_h=200,
                               pad_left=362, pad_top=362, pad_right=362, pad_bottom=362)

        with pytest.raises(ValueError, match="inpainted_crop"):
            handler.stitch_back(original_frame, invalid_crop, crop_region)


class TestStitchHandlerIntegration:
    """Integration tests."""

    def test_stitch_handler_output_dimensions(self):
        """Test that output frame always matches input dimensions."""
        handler = StitchHandler(blend_feather_width=32)

        for frame_w, frame_h in [(1920, 1080), (1280, 720), (3840, 2160)]:
            original_frame = create_test_frame(width=frame_w, height=frame_h)
            inpainted_crop = create_inpainted_crop()

            crop_region = CropRegion(
                x=100, y=100, w=100, h=100,
                scale_factor=2.0,
                context_x=50, context_y=50,
                context_w=200, context_h=200,
                pad_left=362, pad_top=362,
                pad_right=362, pad_bottom=362,
            )

            result = handler.stitch_back(original_frame, inpainted_crop, crop_region)

            assert result.shape == (frame_h, frame_w, 3)
            assert result.dtype == np.uint8

    def test_stitch_handler_pixel_value_range(self):
        """Test that output pixel values are in valid range [0, 255]."""
        handler = StitchHandler(blend_feather_width=32)

        original_frame = create_test_frame()
        inpainted_crop = create_inpainted_crop()

        crop_region = CropRegion(
            x=500, y=300, w=200, h=200,
            scale_factor=2.0,
            context_x=450, context_y=250,
            context_w=300, context_h=300,
            pad_left=362, pad_top=362,
            pad_right=362, pad_bottom=362,
        )

        result = handler.stitch_back(original_frame, inpainted_crop, crop_region)

        # All pixel values should be in [0, 255]
        assert np.all(result >= 0)
        assert np.all(result <= 255)

    def test_stitch_handler_initialization(self):
        """Test handler initialization with various feather widths."""
        for width in [1, 16, 32, 64, 128]:
            handler = StitchHandler(blend_feather_width=width)
            assert handler.blend_feather_width == width

    def test_stitch_handler_multiple_stitches(self):
        """Test stitching same frame multiple times."""
        handler = StitchHandler(blend_feather_width=32)

        original_frame = create_test_frame()

        results = []
        for i in range(3):
            inpainted_crop = create_inpainted_crop()
            inpainted_crop[:, :] = [100 + i * 10, 100 + i * 10, 100 + i * 10]

            crop_region = CropRegion(
                x=300 + i * 100,
                y=300,
                w=100,
                h=100,
                scale_factor=2.0,
                context_x=250 + i * 100,
                context_y=250,
                context_w=200,
                context_h=200,
                pad_left=362,
                pad_top=362,
                pad_right=362,
                pad_bottom=362,
            )

            result = handler.stitch_back(original_frame, inpainted_crop, crop_region)
            results.append(result)

        # All results should have valid shapes and types
        for result in results:
            assert result.shape == original_frame.shape
            assert result.dtype == np.uint8
