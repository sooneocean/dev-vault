"""
Unit tests for watermark_removal.preprocessing.crop_handler module.

Tests crop region computation, extraction, and stitch mapping.
"""

import pytest
import numpy as np

from src.watermark_removal.preprocessing.crop_handler import CropHandler
from src.watermark_removal.core.types import CropRegion


class TestCropHandler:
    """Test CropHandler class."""

    def test_init_default(self):
        """Initialize with default parameters."""
        handler = CropHandler()
        assert handler.context_padding == 64
        assert handler.target_size == 1024

    def test_init_custom(self):
        """Initialize with custom parameters."""
        handler = CropHandler(context_padding=32, target_size=512)
        assert handler.context_padding == 32
        assert handler.target_size == 512

    def test_compute_crop_region_simple(self):
        """Compute crop region from watermark bbox."""
        handler = CropHandler(context_padding=64, target_size=1024)
        frame_shape = (1080, 1920, 3)
        watermark_bbox = (100, 100, 200, 150)

        crop = handler.compute_crop_region(0, watermark_bbox, frame_shape)

        assert crop is not None
        assert crop.frame_id == 0
        assert crop.original_bbox == (100, 100, 200, 150)
        assert crop.scale_factor > 0
        assert crop.pad_left >= 0
        assert crop.pad_top >= 0

    def test_compute_crop_region_invalid_bbox(self):
        """Invalid bbox returns None."""
        handler = CropHandler()
        frame_shape = (1080, 1920, 3)

        # Bbox exceeds frame
        crop = handler.compute_crop_region(0, (1900, 100, 100, 100), frame_shape)
        assert crop is None

    def test_compute_crop_region_padding_clamped(self):
        """Context padding clamped to frame bounds."""
        handler = CropHandler(context_padding=100, target_size=512)
        frame_shape = (480, 640, 3)
        # Watermark at corner
        watermark_bbox = (10, 10, 50, 50)

        crop = handler.compute_crop_region(0, watermark_bbox, frame_shape)

        assert crop is not None
        # Context bbox should be clamped
        ctx_x, ctx_y, ctx_w, ctx_h = crop.context_bbox
        assert ctx_x >= 0
        assert ctx_y >= 0
        assert ctx_x + ctx_w <= frame_shape[1]
        assert ctx_y + ctx_h <= frame_shape[0]

    def test_compute_crop_region_scale_factor(self):
        """Scale factor computed correctly."""
        handler = CropHandler(context_padding=0, target_size=1024)
        frame_shape = (2048, 2048, 3)
        # Watermark of 512x512 (max dimension)
        watermark_bbox = (700, 700, 512, 512)

        crop = handler.compute_crop_region(0, watermark_bbox, frame_shape)

        # Without padding, context = watermark = 512x512
        # scale_factor = 1024 / 512 = 2.0
        assert crop is not None
        assert abs(crop.scale_factor - 2.0) < 0.01

    def test_compute_crop_region_zero_padding(self):
        """Zero padding case."""
        handler = CropHandler(context_padding=0, target_size=1024)
        frame_shape = (1080, 1920, 3)
        watermark_bbox = (100, 100, 200, 150)

        crop = handler.compute_crop_region(0, watermark_bbox, frame_shape)

        assert crop is not None
        # Context bbox with no padding should equal watermark bbox
        assert crop.context_bbox == crop.original_bbox

    def test_get_inpaint_region(self):
        """Get inpainting region within padded crop."""
        handler = CropHandler(context_padding=64, target_size=1024)
        crop = CropRegion(
            frame_id=0,
            original_bbox=(100, 100, 200, 150),
            context_bbox=(36, 36, 328, 278),  # With padding
            scale_factor=3.0,
            pad_left=10,
            pad_top=10,
            pad_right=10,
            pad_bottom=10,
        )

        inpaint_bbox = handler.get_inpaint_region(crop)

        # Should be clamped within target_size
        x_start, y_start, x_end, y_end = inpaint_bbox
        assert 0 <= x_start < x_end <= handler.target_size
        assert 0 <= y_start < y_end <= handler.target_size

    def test_validate_bbox_valid(self):
        """Valid bbox passes validation."""
        frame_shape = (480, 640, 3)
        assert CropHandler._validate_bbox((10, 20, 100, 150), frame_shape)

    def test_validate_bbox_negative(self):
        """Negative coords fail."""
        frame_shape = (480, 640, 3)
        assert not CropHandler._validate_bbox((-10, 20, 100, 150), frame_shape)

    def test_validate_bbox_zero_size(self):
        """Zero width/height fails."""
        frame_shape = (480, 640, 3)
        assert not CropHandler._validate_bbox((10, 20, 0, 150), frame_shape)

    def test_validate_bbox_exceeds_bounds(self):
        """Exceeding bounds fails."""
        frame_shape = (480, 640, 3)
        assert not CropHandler._validate_bbox((600, 400, 100, 150), frame_shape)


class TestCropHandlerIntegration:
    """Integration tests for crop handling workflow."""

    def test_crop_computation_workflow(self):
        """Complete crop computation workflow."""
        handler = CropHandler(context_padding=32, target_size=512)
        frame_shape = (1080, 1920, 3)
        watermark_bbox = (500, 500, 300, 200)

        # Compute crop region
        crop = handler.compute_crop_region(0, watermark_bbox, frame_shape)

        assert crop is not None
        assert crop.frame_id == 0

        # Get inpainting region
        inpaint_bbox = handler.get_inpaint_region(crop)

        x_start, y_start, x_end, y_end = inpaint_bbox
        # Should be valid coordinates within padded crop
        assert 0 <= x_start < x_end <= handler.target_size
        assert 0 <= y_start < y_end <= handler.target_size

    def test_multiple_frame_crops(self):
        """Compute crops for multiple frames."""
        handler = CropHandler()
        frame_shape = (1080, 1920, 3)

        bboxes = [
            (100, 100, 200, 150),
            (200, 200, 200, 150),
            (300, 300, 200, 150),
        ]

        crops = []
        for frame_id, bbox in enumerate(bboxes):
            crop = handler.compute_crop_region(frame_id, bbox, frame_shape)
            assert crop is not None
            crops.append(crop)

        assert len(crops) == 3
        assert crops[0].frame_id == 0
        assert crops[2].frame_id == 2

    def test_small_frame_large_watermark(self):
        """Watermark large relative to frame."""
        handler = CropHandler(context_padding=10, target_size=512)
        frame_shape = (480, 640, 3)
        # Watermark takes up most of frame
        watermark_bbox = (50, 50, 500, 350)

        crop = handler.compute_crop_region(0, watermark_bbox, frame_shape)

        assert crop is not None
        # Scale factor should be computed to fit target_size
        assert crop.scale_factor > 0

    def test_large_frame_small_watermark(self):
        """Watermark small relative to frame."""
        handler = CropHandler(context_padding=64, target_size=1024)
        frame_shape = (2160, 3840, 3)
        watermark_bbox = (100, 100, 50, 50)

        crop = handler.compute_crop_region(0, watermark_bbox, frame_shape)

        assert crop is not None
        # Scale factor should be high (upsample)
        assert crop.scale_factor > 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
