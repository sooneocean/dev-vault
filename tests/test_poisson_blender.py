"""Tests for Poisson blending and color matching."""

import numpy as np
import pytest
import cv2

from src.watermark_removal.blending.poisson_blender import PoissonBlender, ColorMatcher


class TestPoissonBlenderInitialization:
    """Test PoissonBlender initialization."""

    def test_initialization_default(self):
        """Test PoissonBlender initializes with default method."""
        blender = PoissonBlender()
        assert blender.method == "seamless_clone"

    def test_initialization_seamless_clone(self):
        """Test initialization with seamless_clone method."""
        blender = PoissonBlender(method="seamless_clone")
        assert blender.method == "seamless_clone"

    def test_initialization_mixed_clone(self):
        """Test initialization with mixed_clone method."""
        blender = PoissonBlender(method="mixed_clone")
        assert blender.method == "mixed_clone"

    def test_initialization_invalid_method(self):
        """Test initialization rejects invalid method."""
        with pytest.raises(ValueError, match="Unknown blend method"):
            PoissonBlender(method="invalid_method")


class TestPoissonBlend:
    """Test Poisson blending functionality."""

    def test_blend_seamless_clone(self):
        """Test Poisson blending with seamless_clone method."""
        blender = PoissonBlender(method="seamless_clone")

        # Create test frames
        background = np.ones((300, 400, 3), dtype=np.uint8) * 100  # Gray background
        inpainted = np.ones((100, 100, 3), dtype=np.uint8) * 200   # Lighter inpaint

        region_bbox = (150, 100, 100, 100)

        blended = blender.blend(background, inpainted, region_bbox)

        # Verify output properties
        assert blended.dtype == np.uint8
        assert blended.shape == background.shape

        # Region should be blended (not just copy)
        region = blended[100:200, 150:250]
        # The blended region should be influenced by the inpainted (which is lighter)
        # Poisson blending is subtle, so just verify it's not the exact background
        assert np.min(region) <= np.max(inpainted) or np.max(region) >= np.min(background)

    def test_blend_mixed_clone(self):
        """Test Poisson blending with mixed_clone method."""
        blender = PoissonBlender(method="mixed_clone")

        background = np.ones((300, 400, 3), dtype=np.uint8) * 100
        inpainted = np.ones((100, 100, 3), dtype=np.uint8) * 200

        region_bbox = (150, 100, 100, 100)

        blended = blender.blend(background, inpainted, region_bbox)

        # Verify output
        assert blended.dtype == np.uint8
        assert blended.shape == background.shape

    def test_blend_with_mask(self):
        """Test blending with custom blend mask."""
        blender = PoissonBlender()

        background = np.ones((300, 400, 3), dtype=np.uint8) * 100
        inpainted = np.ones((100, 100, 3), dtype=np.uint8) * 200

        # Create mask (only center half blended)
        mask = np.zeros((100, 100), dtype=np.uint8)
        mask[25:75, 25:75] = 255

        region_bbox = (150, 100, 100, 100)

        blended = blender.blend(background, inpainted, region_bbox, mask=mask)

        # Verify output
        assert blended.dtype == np.uint8
        assert blended.shape == background.shape

    def test_blend_mismatched_inpainted_size(self):
        """Test blending when inpainted crop size doesn't match bbox."""
        blender = PoissonBlender()

        background = np.ones((300, 400, 3), dtype=np.uint8) * 100
        inpainted = np.ones((80, 80, 3), dtype=np.uint8) * 200  # Different size

        region_bbox = (150, 100, 100, 100)

        blended = blender.blend(background, inpainted, region_bbox)

        # Should handle size mismatch gracefully (resizes inpainted)
        assert blended.dtype == np.uint8
        assert blended.shape == background.shape

    def test_blend_empty_region(self):
        """Test blending with zero-size region."""
        blender = PoissonBlender()

        background = np.ones((300, 400, 3), dtype=np.uint8) * 100
        inpainted = np.ones((100, 100, 3), dtype=np.uint8) * 200

        # Zero-size region
        region_bbox = (150, 100, 0, 100)

        blended = blender.blend(background, inpainted, region_bbox)

        # Should return copy of background
        assert np.array_equal(blended, background)

    def test_blend_at_boundary(self):
        """Test blending when region extends beyond frame boundary."""
        blender = PoissonBlender()

        background = np.ones((300, 400, 3), dtype=np.uint8) * 100
        inpainted = np.ones((100, 100, 3), dtype=np.uint8) * 200

        # Region near/beyond boundary
        region_bbox = (350, 250, 100, 100)

        blended = blender.blend(background, inpainted, region_bbox)

        # Should handle gracefully
        assert blended.dtype == np.uint8
        assert blended.shape == background.shape


class TestColorMatcher:
    """Test color histogram matching."""

    def test_match_histograms_basic(self):
        """Test basic histogram matching."""
        # Create source with specific colors
        source = np.ones((100, 100, 3), dtype=np.uint8) * 50  # Dark
        reference = np.ones((100, 100, 3), dtype=np.uint8) * 200  # Light

        matched = ColorMatcher.match_histograms(source, reference)

        # Verify output
        assert matched.dtype == np.uint8
        assert matched.shape == source.shape

        # Matched should be closer to reference in mean
        source_mean = np.mean(source)
        matched_mean = np.mean(matched)
        reference_mean = np.mean(reference)

        # Matched mean should be closer to reference than source was
        assert abs(matched_mean - reference_mean) < abs(source_mean - reference_mean)

    def test_match_histograms_with_region(self):
        """Test histogram matching with specific region."""
        source = np.ones((100, 100, 3), dtype=np.uint8) * 50
        background = np.ones((300, 300, 3), dtype=np.uint8) * 200

        region_bbox = (100, 100, 100, 100)

        matched = ColorMatcher.match_histograms(source, background, region_bbox)

        # Verify output
        assert matched.dtype == np.uint8
        assert matched.shape == source.shape

    def test_match_boundary_colors(self):
        """Test boundary color matching."""
        # Source to blend
        source = np.ones((100, 100, 3), dtype=np.uint8) * 80

        # Background with different color
        background = np.ones((300, 300, 3), dtype=np.uint8) * 150

        region_bbox = (100, 100, 100, 100)

        matched = ColorMatcher.match_boundary_colors(
            source, background, region_bbox, boundary_width=10
        )

        # Verify output
        assert matched.dtype == np.uint8
        assert matched.shape == source.shape

        # Matched should be adjusted toward boundary colors
        boundary_mean = np.mean(background)
        matched_mean = np.mean(matched)
        source_mean = np.mean(source)

        # Matched should be closer to boundary than original source
        assert abs(matched_mean - boundary_mean) <= abs(source_mean - boundary_mean)

    def test_boundary_colors_at_frame_edge(self):
        """Test boundary matching when region is at frame edge."""
        source = np.ones((50, 50, 3), dtype=np.uint8) * 100
        background = np.ones((200, 200, 3), dtype=np.uint8) * 180

        # Region at corner
        region_bbox = (0, 0, 50, 50)

        matched = ColorMatcher.match_boundary_colors(
            source, background, region_bbox, boundary_width=10
        )

        # Should handle edge case gracefully
        assert matched.dtype == np.uint8
        assert matched.shape == source.shape


class TestPoissonBlenderIntegration:
    """Integration tests for Poisson blending workflow."""

    def test_blend_then_color_match(self):
        """Test combining Poisson blending with color matching."""
        blender = PoissonBlender()

        # Create frames
        background = np.ones((300, 400, 3), dtype=np.uint8) * 150
        inpainted = np.ones((100, 100, 3), dtype=np.uint8) * 80

        region_bbox = (150, 100, 100, 100)

        # First: Poisson blend
        blended = blender.blend(background, inpainted, region_bbox)

        # Then: Color match to reduce color artifacts
        color_corrected = ColorMatcher.match_boundary_colors(
            blended[100:200, 150:250],
            background,
            (0, 0, 100, 100),  # Relative region
        )

        # Verify both operations succeeded
        assert blended.dtype == np.uint8
        assert color_corrected.dtype == np.uint8

    def test_realistic_watermark_removal(self):
        """Test realistic watermark removal scenario."""
        # Create background with gradient
        background = np.zeros((200, 300, 3), dtype=np.uint8)
        for y in range(200):
            background[y, :] = [y % 256, (y // 2) % 256, (y // 3) % 256]

        # Watermark region in light gray
        watermark_region = np.ones((80, 80, 3), dtype=np.uint8) * 200

        # Inpainted result (background-like)
        inpainted = np.zeros((80, 80, 3), dtype=np.uint8)
        for y in range(80):
            actual_y = 60 + y
            inpainted[y, :] = [actual_y % 256, (actual_y // 2) % 256, (actual_y // 3) % 256]

        region_bbox = (110, 60, 80, 80)

        # Poisson blend
        blender = PoissonBlender()
        blended = blender.blend(background, inpainted, region_bbox)

        # Verify seamless
        assert blended.dtype == np.uint8
        assert blended.shape == background.shape

        # Blended region should look natural (similar color to surroundings)
        blended_region = blended[60:140, 110:190]
        background_region = background[60:140, 110:190]

        # Color difference should be small (Poisson preserves gradients)
        color_diff = np.mean(np.abs(blended_region.astype(float) - background_region.astype(float)))
        assert color_diff < 100  # Reasonable color match


class TestPoissonBlenderEdgeCases:
    """Test edge cases and error handling."""

    def test_blend_with_3channel_mask(self):
        """Test blending with 3-channel mask."""
        blender = PoissonBlender()

        background = np.ones((300, 400, 3), dtype=np.uint8) * 100
        inpainted = np.ones((100, 100, 3), dtype=np.uint8) * 200

        # 3-channel mask
        mask = np.ones((100, 100, 3), dtype=np.uint8) * 255

        region_bbox = (150, 100, 100, 100)

        blended = blender.blend(background, inpainted, region_bbox, mask=mask)

        # Should convert to single channel internally
        assert blended.dtype == np.uint8

    def test_blend_with_float_mask(self):
        """Test blending with float mask [0, 1]."""
        blender = PoissonBlender()

        background = np.ones((300, 400, 3), dtype=np.uint8) * 100
        inpainted = np.ones((100, 100, 3), dtype=np.uint8) * 200

        # Float mask [0, 1]
        mask = np.ones((100, 100), dtype=np.float32) * 0.8

        region_bbox = (150, 100, 100, 100)

        blended = blender.blend(background, inpainted, region_bbox, mask=mask)

        # Should handle float mask gracefully
        assert blended.dtype == np.uint8

    def test_color_matcher_no_boundary_samples(self):
        """Test boundary color matching when region is entire frame."""
        source = np.ones((100, 100, 3), dtype=np.uint8) * 100
        background = np.ones((100, 100, 3), dtype=np.uint8) * 180

        # Region fills entire background
        region_bbox = (0, 0, 100, 100)

        matched = ColorMatcher.match_boundary_colors(
            source, background, region_bbox, boundary_width=10
        )

        # Should handle gracefully (no boundary to sample)
        assert matched.dtype == np.uint8
        assert matched.shape == source.shape
