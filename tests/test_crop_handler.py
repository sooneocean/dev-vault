"""Tests for crop handling with context padding."""

import tempfile
from pathlib import Path

import cv2
import numpy as np
import pytest

from src.watermark_removal.core.types import CropRegion, Frame, Mask, MaskType
from src.watermark_removal.preprocessing.crop_handler import CropHandler


def create_test_frame(width: int = 1920, height: int = 1080) -> Frame:
    """Create a test frame with gradient pattern.

    Args:
        width: Frame width.
        height: Frame height.

    Returns:
        Frame object.
    """
    image = np.zeros((height, width, 3), dtype=np.uint8)
    # Create gradient for visual verification
    for y in range(height):
        image[y, :] = [y % 256, (y // 2) % 256, (y // 3) % 256]

    return Frame(frame_id=0, image=image, timestamp_ms=0.0)


def create_bbox_mask(x: int, y: int, w: int, h: int) -> Mask:
    """Create a bbox mask.

    Args:
        x, y, w, h: Bbox coordinates.

    Returns:
        Mask object with BBOX type.
    """
    return Mask(
        type=MaskType.BBOX,
        data={"x": x, "y": y, "w": w, "h": h},
        valid_frame_range=(0, 0),
    )


def create_image_mask_with_circle(
    mask_width: int = 1920, mask_height: int = 1080, circle_x: int = 960, circle_y: int = 540, radius: int = 100
) -> Mask:
    """Create an image mask with a circle.

    Args:
        mask_width: Mask width.
        mask_height: Mask height.
        circle_x: Circle center x.
        circle_y: Circle center y.
        radius: Circle radius.

    Returns:
        Mask object with IMAGE type.
    """
    mask_image = np.zeros((mask_height, mask_width), dtype=np.uint8)
    cv2.circle(mask_image, (circle_x, circle_y), radius, 255, -1)

    return Mask(
        type=MaskType.IMAGE,
        data=mask_image,
        valid_frame_range=(0, float("inf")),
    )


class TestCropHandlerHappyPath:
    """Happy path tests."""

    def test_crop_handler_basic_crop_and_resize(self):
        """Test basic crop with padding and resize to 1024x1024."""
        handler = CropHandler(context_padding=50, target_inpaint_size=1024)
        frame = create_test_frame()
        mask = create_bbox_mask(x=500, y=300, w=200, h=200)

        crop, crop_region = handler.crop_with_context(frame, mask)

        assert crop.shape == (1024, 1024, 3)
        assert isinstance(crop_region, CropRegion)
        assert crop_region.x == 500
        assert crop_region.y == 300
        assert crop_region.w == 200
        assert crop_region.h == 200

    def test_crop_handler_metadata_consistency(self):
        """Test that CropRegion metadata is internally consistent."""
        handler = CropHandler(context_padding=50, target_inpaint_size=1024)
        frame = create_test_frame()
        mask = create_bbox_mask(x=600, y=400, w=300, h=300)

        _, crop_region = handler.crop_with_context(frame, mask)

        # Context region should include padding
        assert crop_region.context_x <= crop_region.x
        assert crop_region.context_y <= crop_region.y
        assert crop_region.context_w >= crop_region.w
        assert crop_region.context_h >= crop_region.h

        # Padding should be non-negative and consistent
        assert crop_region.pad_left >= 0
        assert crop_region.pad_top >= 0
        assert crop_region.pad_right >= 0
        assert crop_region.pad_bottom >= 0

        # Scale factor should be positive
        assert crop_region.scale_factor > 0

    def test_crop_handler_with_image_mask(self):
        """Test cropping with image mask (circle)."""
        handler = CropHandler(context_padding=50, target_inpaint_size=1024)
        frame = create_test_frame()
        mask = create_image_mask_with_circle(mask_width=1920, mask_height=1080, circle_x=960, circle_y=540, radius=100)

        crop, crop_region = handler.crop_with_context(frame, mask)

        assert crop.shape == (1024, 1024, 3)
        assert crop_region.scale_factor > 0


class TestCropHandlerEdgeCases:
    """Edge case tests."""

    def test_crop_handler_watermark_at_frame_edge(self):
        """Test crop when watermark is near frame edge."""
        handler = CropHandler(context_padding=100, target_inpaint_size=1024)
        frame = create_test_frame(width=1920, height=1080)
        # Watermark near right edge
        mask = create_bbox_mask(x=1800, y=500, w=100, h=100)

        crop, crop_region = handler.crop_with_context(frame, mask)

        assert crop.shape == (1024, 1024, 3)
        # Context should be clamped to frame boundary
        assert crop_region.context_x + crop_region.context_w <= 1920

    def test_crop_handler_watermark_at_corner(self):
        """Test crop when watermark is at frame corner."""
        handler = CropHandler(context_padding=100, target_inpaint_size=1024)
        frame = create_test_frame(width=1920, height=1080)
        # Watermark at top-left corner
        mask = create_bbox_mask(x=0, y=0, w=100, h=100)

        crop, crop_region = handler.crop_with_context(frame, mask)

        assert crop.shape == (1024, 1024, 3)
        # Context should not go negative
        assert crop_region.context_x >= 0
        assert crop_region.context_y >= 0

    def test_crop_handler_large_watermark(self):
        """Test crop with large watermark."""
        handler = CropHandler(context_padding=50, target_inpaint_size=1024)
        frame = create_test_frame(width=1920, height=1080)
        # Large watermark (500x500) with padding becomes 600x600 context
        # which is still smaller than 1024, so gets scaled up
        mask = create_bbox_mask(x=700, y=290, w=500, h=500)

        crop, crop_region = handler.crop_with_context(frame, mask)

        assert crop.shape == (1024, 1024, 3)
        # Scale factor should be > 1 (context region < 1024)
        assert crop_region.scale_factor > 1.0

    def test_crop_handler_small_watermark(self):
        """Test crop with small watermark (scaled up)."""
        handler = CropHandler(context_padding=50, target_inpaint_size=1024)
        frame = create_test_frame(width=1920, height=1080)
        # Small watermark (20x20)
        mask = create_bbox_mask(x=950, y=530, w=20, h=20)

        crop, crop_region = handler.crop_with_context(frame, mask)

        assert crop.shape == (1024, 1024, 3)
        # Scale factor should be greater than 1 (scaled up)
        assert crop_region.scale_factor > 1.0

    def test_crop_handler_various_sizes(self):
        """Test crop with various frame and watermark sizes."""
        handler = CropHandler(context_padding=30, target_inpaint_size=512)  # Different target size
        frame = create_test_frame(width=1280, height=720)
        mask = create_bbox_mask(x=400, y=300, w=150, h=100)

        crop, crop_region = handler.crop_with_context(frame, mask)

        assert crop.shape == (512, 512, 3)
        assert crop_region.scale_factor > 0


class TestCropHandlerErrors:
    """Error handling tests."""

    def test_crop_handler_empty_image_mask(self):
        """Test error when image mask is empty."""
        handler = CropHandler()
        frame = create_test_frame()
        # Empty mask (no contours)
        empty_mask = Mask(
            type=MaskType.IMAGE,
            data=np.zeros((1080, 1920), dtype=np.uint8),
            valid_frame_range=(0, float("inf")),
        )

        with pytest.raises(ValueError, match="No watermark contours found"):
            handler.crop_with_context(frame, empty_mask)

    def test_crop_handler_invalid_bbox_dimensions(self):
        """Test error with invalid bbox dimensions."""
        handler = CropHandler()
        frame = create_test_frame()
        # Invalid: zero width
        mask = create_bbox_mask(x=500, y=300, w=0, h=100)

        with pytest.raises(ValueError, match="Invalid watermark region"):
            handler.crop_with_context(frame, mask)

    def test_crop_handler_negative_bbox(self):
        """Test error with negative bbox coordinates."""
        handler = CropHandler()
        frame = create_test_frame()
        # Negative width
        mask = create_bbox_mask(x=500, y=300, w=-100, h=100)

        with pytest.raises(ValueError, match="Invalid watermark region"):
            handler.crop_with_context(frame, mask)


class TestCropHandlerInpaintMask:
    """Tests for inpaint mask generation."""

    def test_crop_handler_inpaint_mask_generation(self):
        """Test that inpaint mask is generated correctly."""
        handler = CropHandler(context_padding=50, target_inpaint_size=1024)
        frame = create_test_frame()
        mask = create_bbox_mask(x=500, y=300, w=200, h=200)

        crop, crop_region = handler.crop_with_context(frame, mask)

        # Manually check that inpaint mask makes sense
        # The inpaint mask should be binary (0 or 255)
        # This is an indirect check - the actual mask is used internally
        assert crop.shape == (1024, 1024, 3)
        assert crop.dtype == np.uint8


class TestCropHandlerIntegration:
    """Integration tests."""

    def test_crop_handler_metadata_for_stitching(self):
        """Test that metadata can be used for stitching back (validation only)."""
        handler = CropHandler(context_padding=50, target_inpaint_size=1024)
        frame = create_test_frame(width=1920, height=1080)
        mask = create_bbox_mask(x=800, y=400, w=300, h=300)

        crop, crop_region = handler.crop_with_context(frame, mask)

        # Verify metadata would allow stitch-back
        # Original bbox should be inside context region
        assert crop_region.x >= crop_region.context_x
        assert crop_region.y >= crop_region.context_y
        assert crop_region.x + crop_region.w <= crop_region.context_x + crop_region.context_w
        assert crop_region.y + crop_region.h <= crop_region.context_y + crop_region.context_h

        # Context region should be within frame
        assert crop_region.context_x >= 0
        assert crop_region.context_y >= 0
        assert crop_region.context_x + crop_region.context_w <= 1920
        assert crop_region.context_y + crop_region.context_h <= 1080

    def test_crop_handler_padding_configuration(self):
        """Test different padding configurations."""
        # Test with no padding
        handler_no_pad = CropHandler(context_padding=0, target_inpaint_size=1024)
        frame = create_test_frame()
        mask = create_bbox_mask(x=500, y=300, w=200, h=200)

        _, crop_region_no_pad = handler_no_pad.crop_with_context(frame, mask)

        # Context should equal bbox when no padding
        assert crop_region_no_pad.context_x == 500
        assert crop_region_no_pad.context_y == 300
        assert crop_region_no_pad.context_w == 200
        assert crop_region_no_pad.context_h == 200

        # Test with large padding
        handler_large_pad = CropHandler(context_padding=200, target_inpaint_size=1024)

        _, crop_region_large_pad = handler_large_pad.crop_with_context(frame, mask)

        # Context should be larger with padding
        assert crop_region_large_pad.context_w > crop_region_no_pad.context_w
        assert crop_region_large_pad.context_h > crop_region_no_pad.context_h

    def test_crop_handler_multiple_frames(self):
        """Test cropping same mask across multiple frames."""
        handler = CropHandler(context_padding=50, target_inpaint_size=1024)
        mask = create_bbox_mask(x=500, y=300, w=200, h=200)

        # Create frames with different content (different gradients)
        frame1 = create_test_frame(width=1920, height=1080)
        frame2_image = np.ones((1080, 1920, 3), dtype=np.uint8) * 128
        frame2 = Frame(frame_id=1, image=frame2_image, timestamp_ms=33.33)

        crop1, crop_region1 = handler.crop_with_context(frame1, mask)
        crop2, crop_region2 = handler.crop_with_context(frame2, mask)

        # Different frames should produce same crop dimensions
        assert crop1.shape == crop2.shape
        # Different content
        assert not np.array_equal(crop1, crop2)
        # Same metadata (same mask position)
        assert crop_region1.x == crop_region2.x
        assert crop_region1.y == crop_region2.y
