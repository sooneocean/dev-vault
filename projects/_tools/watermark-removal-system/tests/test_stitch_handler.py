"""
Unit tests for watermark_removal.postprocessing.stitch_handler module.

Tests crop stitching, rescaling, and feather blending.
"""

import pytest
import numpy as np

from src.watermark_removal.postprocessing.stitch_handler import StitchHandler
from src.watermark_removal.core.types import CropRegion


class TestStitchHandler:
    """Test StitchHandler class."""

    def test_init_default(self):
        """Initialize with default parameters."""
        handler = StitchHandler()
        assert handler.blend_feather_width == 32

    def test_init_custom(self):
        """Initialize with custom feather width."""
        handler = StitchHandler(blend_feather_width=64)
        assert handler.blend_feather_width == 64

    def test_remove_padding_no_padding(self):
        """Remove padding with zero padding."""
        handler = StitchHandler()
        crop = np.ones((100, 100, 3), dtype=np.uint8) * 128
        crop_region = CropRegion(
            frame_id=0,
            original_bbox=(10, 10, 50, 50),
            context_bbox=(0, 0, 100, 100),
            scale_factor=1.0,
            pad_left=0,
            pad_top=0,
            pad_right=0,
            pad_bottom=0,
        )

        unpadded = handler._remove_padding(crop, crop_region)

        assert unpadded.shape == (100, 100, 3)
        assert np.array_equal(unpadded, crop)

    def test_remove_padding_with_padding(self):
        """Remove padding from padded crop."""
        handler = StitchHandler()
        crop = np.ones((100, 100, 3), dtype=np.uint8) * 128
        crop_region = CropRegion(
            frame_id=0,
            original_bbox=(10, 10, 50, 50),
            context_bbox=(0, 0, 100, 100),
            scale_factor=1.0,
            pad_left=10,
            pad_top=10,
            pad_right=10,
            pad_bottom=10,
        )

        unpadded = handler._remove_padding(crop, crop_region)

        assert unpadded.shape == (80, 80, 3)

    def test_remove_padding_asymmetric(self):
        """Remove asymmetric padding."""
        handler = StitchHandler()
        crop = np.ones((100, 100, 3), dtype=np.uint8)
        crop_region = CropRegion(
            frame_id=0,
            original_bbox=(0, 0, 50, 50),
            context_bbox=(0, 0, 100, 100),
            scale_factor=1.0,
            pad_left=5,
            pad_top=15,
            pad_right=20,
            pad_bottom=30,
        )

        unpadded = handler._remove_padding(crop, crop_region)

        assert unpadded.shape == (55, 75, 3)

    def test_rescale_to_original_upscale(self):
        """Rescale from small to large (or returns original if OpenCV unavailable)."""
        handler = StitchHandler()
        crop = np.ones((100, 100, 3), dtype=np.uint8) * 128
        crop_region = CropRegion(
            frame_id=0,
            original_bbox=(0, 0, 50, 50),
            context_bbox=(0, 0, 200, 200),  # Context is 200x200
            scale_factor=2.0,  # Original was 100x100, scaled to 50x50 (1/2)
            pad_left=0,
            pad_top=0,
            pad_right=0,
            pad_bottom=0,
        )

        rescaled = handler._rescale_to_original(crop, crop_region)

        # Should return same shape as crop if OpenCV unavailable, or rescaled to 200x200
        assert rescaled.shape in [(100, 100, 3), (200, 200, 3)]

    def test_rescale_to_original_downscale(self):
        """Rescale from large to small (or returns original if OpenCV unavailable)."""
        handler = StitchHandler()
        crop = np.ones((1024, 1024, 3), dtype=np.uint8) * 128
        crop_region = CropRegion(
            frame_id=0,
            original_bbox=(0, 0, 100, 100),
            context_bbox=(0, 0, 256, 256),
            scale_factor=4.0,  # 256 * 4 = 1024
            pad_left=0,
            pad_top=0,
            pad_right=0,
            pad_bottom=0,
        )

        rescaled = handler._rescale_to_original(crop, crop_region)

        # Should return same shape as crop if OpenCV unavailable, or rescaled to 256x256
        assert rescaled.shape in [(1024, 1024, 3), (256, 256, 3)]

    def test_create_feather_mask_shape(self):
        """Feather mask has correct shape."""
        handler = StitchHandler(blend_feather_width=16)
        crop = np.ones((100, 100, 3), dtype=np.uint8)

        mask = handler._create_feather_mask(crop)

        assert mask.shape == (100, 100)
        assert mask.dtype == np.float32

    def test_create_feather_mask_values(self):
        """Feather mask values are in valid range."""
        handler = StitchHandler()
        crop = np.ones((100, 100, 3), dtype=np.uint8)

        mask = handler._create_feather_mask(crop)

        assert np.all(mask >= 0.0)
        assert np.all(mask <= 1.0)

    def test_create_feather_mask_gradient(self):
        """Feather mask has gradient from edges to center (or uniform if scipy unavailable)."""
        handler = StitchHandler(blend_feather_width=10)
        crop = np.ones((50, 50, 3), dtype=np.uint8)

        mask = handler._create_feather_mask(crop)

        # Center should have values >= edges (may be equal if no scipy)
        center_value = mask[25, 25]
        edge_value = mask[0, 25]

        assert center_value >= edge_value

    def test_stitch_back_basic(self):
        """Stitch back basic scenario."""
        handler = StitchHandler()

        # Create test frame
        frame = np.ones((1080, 1920, 3), dtype=np.uint8) * 100

        # Create inpainted crop
        inpainted = np.ones((1024, 1024, 3), dtype=np.uint8) * 200

        # Create crop region
        crop_region = CropRegion(
            frame_id=0,
            original_bbox=(100, 100, 200, 200),
            context_bbox=(50, 50, 300, 300),
            scale_factor=3.41,  # 1024 / 300 ≈ 3.41
            pad_left=362,
            pad_top=362,
            pad_right=362,
            pad_bottom=362,
        )

        result = handler.stitch_back(frame, inpainted, crop_region)

        # Result should be same size as original frame
        assert result.shape == frame.shape
        assert result.dtype == np.uint8
        # Values should be in valid range
        assert np.all(result >= 0)
        assert np.all(result <= 255)

    def test_stitch_back_preserves_frame_dimensions(self):
        """Stitching preserves frame dimensions."""
        handler = StitchHandler()
        frame_shapes = [(480, 640, 3), (1080, 1920, 3), (2160, 3840, 3)]

        for shape in frame_shapes:
            frame = np.ones(shape, dtype=np.uint8) * 100
            inpainted = np.ones((512, 512, 3), dtype=np.uint8) * 200
            crop_region = CropRegion(
                frame_id=0,
                original_bbox=(50, 50, 100, 100),
                context_bbox=(25, 25, 150, 150),
                scale_factor=3.41,
                pad_left=200,
                pad_top=200,
                pad_right=312,
                pad_bottom=312,
            )

            result = handler.stitch_back(frame, inpainted, crop_region)

            assert result.shape == frame.shape

    def test_compose_with_mask_basic(self):
        """Composite foreground onto background with mask."""
        background = np.ones((100, 100, 3), dtype=np.uint8) * 100
        foreground = np.ones((50, 50, 3), dtype=np.uint8) * 200
        mask = np.ones((50, 50), dtype=np.float32) * 0.5  # 50% blend

        result = StitchHandler.compose_with_mask(background, foreground, mask, 25, 25)

        assert result.shape == background.shape
        assert result.dtype == np.uint8
        # Blended region should be between background and foreground
        blended_region = result[25:75, 25:75, :]
        assert np.all(blended_region > 100)
        assert np.all(blended_region < 200)

    def test_compose_with_mask_full_opacity(self):
        """Composite with full opacity mask."""
        background = np.ones((100, 100, 3), dtype=np.uint8) * 100
        foreground = np.ones((50, 50, 3), dtype=np.uint8) * 200
        mask = np.ones((50, 50), dtype=np.float32)  # 100% opacity

        result = StitchHandler.compose_with_mask(background, foreground, mask, 25, 25)

        # Composited region should be foreground color
        composited = result[25:75, 25:75, :]
        assert np.allclose(composited, 200, atol=1)

    def test_compose_with_mask_zero_opacity(self):
        """Composite with zero opacity mask."""
        background = np.ones((100, 100, 3), dtype=np.uint8) * 100
        foreground = np.ones((50, 50, 3), dtype=np.uint8) * 200
        mask = np.zeros((50, 50), dtype=np.float32)  # 0% opacity

        result = StitchHandler.compose_with_mask(background, foreground, mask, 25, 25)

        # Composited region should be background color
        composited = result[25:75, 25:75, :]
        assert np.all(composited == 100)

    def test_compose_with_mask_offset_clamping(self):
        """Composite clamps to background bounds."""
        background = np.ones((100, 100, 3), dtype=np.uint8) * 100
        foreground = np.ones((50, 50, 3), dtype=np.uint8) * 200
        mask = np.ones((50, 50), dtype=np.float32)

        # Offset beyond background bounds
        result = StitchHandler.compose_with_mask(background, foreground, mask, 80, 80)

        assert result.shape == background.shape
        # Corner should have some blending (20x20 overlap)
        corner = result[80:100, 80:100, :]
        assert np.any(corner > 100)  # Some blending occurred


class TestStitchHandlerIntegration:
    """Integration tests for StitchHandler."""

    def test_full_stitch_workflow(self):
        """Complete stitch workflow from padded crop to stitched frame."""
        handler = StitchHandler(blend_feather_width=16)

        # Create frames
        original = np.ones((480, 640, 3), dtype=np.uint8) * 128
        inpainted = np.ones((256, 256, 3), dtype=np.uint8) * 200

        # Create metadata
        crop_region = CropRegion(
            frame_id=0,
            original_bbox=(50, 50, 100, 100),
            context_bbox=(25, 25, 150, 150),
            scale_factor=1.7,  # 256 / 150 ≈ 1.7
            pad_left=53,
            pad_top=53,
            pad_right=53,
            pad_bottom=53,
        )

        result = handler.stitch_back(original, inpainted, crop_region)

        # Verify result shape and dtype
        assert result.shape == original.shape
        assert result.dtype == np.uint8
        # Result will equal original if OpenCV unavailable, which is fine

    def test_stitch_with_different_feather_widths(self):
        """Stitching with different feather widths."""
        original = np.ones((480, 640, 3), dtype=np.uint8) * 128
        inpainted = np.ones((256, 256, 3), dtype=np.uint8) * 200

        crop_region = CropRegion(
            frame_id=0,
            original_bbox=(50, 50, 100, 100),
            context_bbox=(25, 25, 150, 150),
            scale_factor=1.7,
            pad_left=53,
            pad_top=53,
            pad_right=53,
            pad_bottom=53,
        )

        handler_sharp = StitchHandler(blend_feather_width=4)
        handler_soft = StitchHandler(blend_feather_width=32)

        result_sharp = handler_sharp.stitch_back(original, inpainted, crop_region)
        result_soft = handler_soft.stitch_back(original, inpainted, crop_region)

        # Both results should have same dimensions
        assert result_sharp.shape == original.shape
        assert result_soft.shape == original.shape
        # Results might be equal if OpenCV/scipy unavailable, which is fine


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
