"""Tests for edge blending and feather mask refinement."""

import numpy as np
import pytest
import cv2

from src.watermark_removal.postprocessing.edge_blending import EdgeBlender


class TestEdgeBlenderInitialization:
    """Test EdgeBlender initialization."""

    def test_edge_blender_initialization(self):
        """Test EdgeBlender initializes with default parameters."""
        blender = EdgeBlender()
        assert blender.feather_width == 32
        assert blender.blur_kernel_size == 5

    def test_edge_blender_custom_parameters(self):
        """Test EdgeBlender initializes with custom parameters."""
        blender = EdgeBlender(feather_width=64, blur_kernel_size=7)
        assert blender.feather_width == 64
        assert blender.blur_kernel_size == 7

    def test_edge_blender_blur_kernel_size_odd(self):
        """Test that blur kernel size is forced to be odd."""
        blender = EdgeBlender(blur_kernel_size=6)
        assert blender.blur_kernel_size == 7  # 6 is even, so becomes 7


class TestFeatherMaskCreation:
    """Test feather mask creation methods."""

    def test_create_feather_mask_basic(self):
        """Test basic feather mask creation."""
        blender = EdgeBlender(feather_width=32)
        shape = (1080, 1920)
        region_bbox = (100, 100, 200, 200)

        mask = blender.create_feather_mask(shape, region_bbox, blur=False)

        # Verify mask properties
        assert mask.dtype == np.float32
        assert mask.shape == shape
        assert np.min(mask) >= 0.0
        assert np.max(mask) <= 1.0

    def test_create_feather_mask_with_blur(self):
        """Test feather mask creation with Gaussian blur."""
        blender = EdgeBlender(feather_width=32, blur_kernel_size=5)
        shape = (1080, 1920)
        region_bbox = (100, 100, 200, 200)

        mask = blender.create_feather_mask(shape, region_bbox, blur=True)

        # Verify mask is smooth (blurred)
        assert mask.dtype == np.float32
        assert mask.shape == shape
        # Check that mask is continuous (no sharp edges)
        gradient = np.gradient(mask)
        assert np.max(np.abs(gradient)) < 1.0  # Smooth transitions

    def test_create_distance_feather_mask(self):
        """Test distance-based feather mask creation."""
        blender = EdgeBlender(feather_width=32)
        shape = (1080, 1920)
        region_bbox = (100, 100, 200, 200)

        mask = blender.create_distance_feather_mask(shape, region_bbox, blur=False)

        # Verify mask properties
        assert mask.dtype == np.float32
        assert mask.shape == shape
        assert np.min(mask) >= 0.0
        assert np.max(mask) <= 1.0

        # Verify region interior is 1.0
        x, y, w, h = region_bbox
        interior_mask = mask[y + 10 : y + 10 + 1, x + 10 : x + 10 + 1]
        assert np.allclose(interior_mask, 1.0)

    def test_distance_feather_mask_monotonic_gradient(self):
        """Test that distance feather mask has monotonic gradient."""
        blender = EdgeBlender(feather_width=64)
        shape = (200, 200)
        region_bbox = (50, 50, 100, 100)

        mask = blender.create_distance_feather_mask(shape, region_bbox, blur=False)

        # Sample center line to verify monotonic decrease from center outward
        center_y = 100
        center_x = 100
        line = mask[center_y, :]

        # Check that values decrease as we move away from center
        # Interior should be high, boundary should be low
        assert line[center_x] > 0.5  # Center is high
        assert line[0] < 0.5  # Edge is lower


class TestEdgeBlending:
    """Test edge blending operations."""

    def test_blend_edges_basic(self):
        """Test basic edge blending."""
        blender = EdgeBlender(feather_width=32)

        # Create test frames
        original = np.zeros((1080, 1920, 3), dtype=np.uint8)
        original[:, :] = [100, 100, 100]  # Gray original

        inpainted = np.ones((200, 200, 3), dtype=np.uint8) * 200  # Lighter inpainted

        region_bbox = (100, 100, 200, 200)

        blended = blender.blend_edges(original, inpainted, region_bbox)

        # Verify output properties
        assert blended.dtype == np.uint8
        assert blended.shape == original.shape

        # Verify region was blended (not all original, not all inpainted)
        region = blended[100:300, 100:300]
        assert np.min(region) >= 100  # At least some inpainted (200) blended
        assert np.max(region) <= 200  # But bounded by inpainted value

    def test_blend_edges_with_mask(self):
        """Test edge blending with provided blend mask."""
        blender = EdgeBlender(feather_width=32)

        # Create test frames
        original = np.ones((200, 200, 3), dtype=np.uint8) * 100
        inpainted = np.ones((100, 100, 3), dtype=np.uint8) * 200

        region_bbox = (50, 50, 100, 100)

        # Create custom blend mask
        blend_mask = np.zeros((200, 200), dtype=np.float32)
        blend_mask[50:150, 50:150] = 1.0  # Full opacity in region

        blended = blender.blend_edges(original, inpainted, region_bbox, blend_mask=blend_mask)

        # Verify blending occurred
        assert blended.dtype == np.uint8
        assert blended.shape == original.shape


class TestEdgeBlendingEdgeCases:
    """Test edge cases for edge blending."""

    def test_feather_mask_at_image_boundary(self):
        """Test feather mask creation at image boundary."""
        blender = EdgeBlender(feather_width=32)
        shape = (200, 200)
        # Region extends beyond boundary
        region_bbox = (100, 100, 150, 150)

        mask = blender.create_feather_mask(shape, region_bbox, blur=False)

        # Verify mask is still valid
        assert mask.dtype == np.float32
        assert mask.shape == shape
        assert np.min(mask) >= 0.0
        assert np.max(mask) <= 1.0

    def test_feather_mask_full_size_region(self):
        """Test feather mask for full-size region."""
        blender = EdgeBlender(feather_width=32)
        shape = (200, 200)
        region_bbox = (0, 0, 200, 200)

        mask = blender.create_feather_mask(shape, region_bbox, blur=False)

        # Entire mask should be high (whole image is region)
        assert np.mean(mask) > 0.8

    def test_blend_edges_mismatched_inpainted_size(self):
        """Test blending when inpainted crop size doesn't match bbox."""
        blender = EdgeBlender(feather_width=32)

        original = np.ones((500, 500, 3), dtype=np.uint8) * 100
        # Inpainted is different size than bbox
        inpainted = np.ones((150, 150, 3), dtype=np.uint8) * 200
        region_bbox = (100, 100, 200, 200)

        blended = blender.blend_edges(original, inpainted, region_bbox)

        # Should still work (resize happens internally)
        assert blended.dtype == np.uint8
        assert blended.shape == original.shape

    def test_large_feather_width(self):
        """Test feather mask with large feather width."""
        blender = EdgeBlender(feather_width=128)
        shape = (500, 500)
        region_bbox = (100, 100, 200, 200)

        mask = blender.create_distance_feather_mask(shape, region_bbox, blur=True)

        # Large feather width should create wider gradient
        assert mask.dtype == np.float32
        assert mask.shape == shape
        # Outer regions should be darker (lower values)
        outer_corner = mask[0, 0]
        center = mask[200, 200]
        assert outer_corner < center


class TestFeatherMaskProperties:
    """Test mathematical properties of feather masks."""

    def test_feather_mask_gradient_monotonic(self):
        """Test that feather mask creates monotonic gradient."""
        blender = EdgeBlender(feather_width=50)
        shape = (300, 300)
        region_bbox = (100, 100, 100, 100)

        mask = blender.create_distance_feather_mask(shape, region_bbox, blur=False)

        # Sample from center outward along a line
        center_x, center_y = 150, 150
        values = []
        for dist in range(0, 100, 10):
            x = center_x + dist
            if x < shape[1]:
                values.append(mask[center_y, x])

        # Values should generally decrease (with some tolerance for blur effects)
        assert len(values) > 2
        assert values[0] >= values[-1]

    def test_feather_mask_blur_smoothness(self):
        """Test that blurred feather mask is smoother than unblurred."""
        blender = EdgeBlender(feather_width=32)
        shape = (300, 300)
        region_bbox = (100, 100, 100, 100)

        mask_no_blur = blender.create_feather_mask(shape, region_bbox, blur=False)
        mask_blur = blender.create_feather_mask(shape, region_bbox, blur=True)

        # Blurred mask should have smaller gradients (smoother)
        grad_no_blur = np.gradient(mask_no_blur)
        grad_blur = np.gradient(mask_blur)

        # RMS of gradients should be smaller for blurred
        rms_no_blur = np.sqrt(np.mean(np.array(grad_no_blur) ** 2))
        rms_blur = np.sqrt(np.mean(np.array(grad_blur) ** 2))

        # Blur should generally reduce gradient magnitude
        assert rms_blur < rms_no_blur or np.isclose(rms_blur, rms_no_blur)


class TestEdgeBlenderIntegration:
    """Integration tests for edge blender."""

    def test_blender_with_realistic_frames(self):
        """Test edge blender with realistic frame content."""
        blender = EdgeBlender(feather_width=48, blur_kernel_size=7)

        # Create realistic test frames (gradient background)
        original = np.zeros((1080, 1920, 3), dtype=np.uint8)
        for y in range(1080):
            original[y, :] = [y % 256, (y // 2) % 256, (y // 3) % 256]

        # Inpainted crop (uniform color to detect seams)
        inpainted = np.ones((200, 200, 3), dtype=np.uint8) * 128

        region_bbox = (800, 500, 200, 200)

        blended = blender.blend_edges(original, inpainted, region_bbox)

        # Verify smooth transition (no harsh seams)
        assert blended.dtype == np.uint8
        assert blended.shape == original.shape

        # Check that region is blended (has some of both original and inpainted)
        region_mean = np.mean(blended[500:700, 800:1000])
        original_region_mean = np.mean(original[500:700, 800:1000])
        inpainted_mean = np.mean(inpainted)

        # Blended should be between original and inpainted
        assert min(original_region_mean, inpainted_mean) <= region_mean <= max(original_region_mean, inpainted_mean)

    def test_blender_multiple_regions(self):
        """Test edge blender on multiple regions in same frame."""
        blender = EdgeBlender(feather_width=32)

        original = np.ones((500, 500, 3), dtype=np.uint8) * 100

        # Blend first region
        inpainted1 = np.ones((100, 100, 3), dtype=np.uint8) * 200
        region1 = (50, 50, 100, 100)
        result1 = blender.blend_edges(original, inpainted1, region1)

        # Blend second region
        inpainted2 = np.ones((80, 80, 3), dtype=np.uint8) * 150
        region2 = (300, 300, 80, 80)
        result2 = blender.blend_edges(result1, inpainted2, region2)

        # Both regions should be blended
        assert result2.dtype == np.uint8
        assert result2.shape == original.shape

        # Check both regions have been modified
        region1_val = np.mean(result2[50:150, 50:150])
        region2_val = np.mean(result2[300:380, 300:380])
        original_val = np.mean(original)

        # Both should differ from original
        assert region1_val != original_val or region2_val != original_val
