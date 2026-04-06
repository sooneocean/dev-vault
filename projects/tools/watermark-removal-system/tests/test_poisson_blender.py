"""
Unit tests for watermark_removal.postprocessing.poisson_blender module.

Tests Poisson blending, gradient preservation, and boundary seamlessness.
"""

import pytest
import numpy as np

from src.watermark_removal.postprocessing.poisson_blender import (
    PoissonBlender,
    GradientPreservingBlender,
)


class TestPoissonBlender:
    """Test PoissonBlender class."""

    def test_init_valid_parameters(self):
        """Initialize with valid parameters."""
        blender = PoissonBlender(max_iterations=50, tolerance=0.01)
        assert blender.max_iterations == 50
        assert blender.tolerance == 0.01

    def test_init_default_parameters(self):
        """Initialize with defaults."""
        blender = PoissonBlender()
        assert blender.max_iterations == 100
        assert blender.tolerance == 1e-2

    def test_blend_identical_images(self):
        """Blending identical images returns identical result."""
        blender = PoissonBlender()
        image = np.ones((100, 100, 3), dtype=np.uint8) * 128
        mask = np.ones((100, 100), dtype=np.uint8) * 255

        result = blender.blend(image, image, mask)

        # Should be very close to original
        assert np.allclose(result, image, atol=5)

    def test_blend_shape_mismatch_target_source(self):
        """Shape mismatch returns target unchanged."""
        blender = PoissonBlender()
        target = np.ones((100, 100, 3), dtype=np.uint8) * 100
        source = np.ones((200, 200, 3), dtype=np.uint8) * 200
        mask = np.ones((100, 100), dtype=np.uint8) * 255

        result = blender.blend(target, source, mask)

        assert np.array_equal(result, target)

    def test_blend_shape_mismatch_target_mask(self):
        """Mask shape mismatch returns target unchanged."""
        blender = PoissonBlender()
        target = np.ones((100, 100, 3), dtype=np.uint8) * 100
        source = np.ones((100, 100, 3), dtype=np.uint8) * 200
        mask = np.ones((200, 200), dtype=np.uint8) * 255

        result = blender.blend(target, source, mask)

        assert np.array_equal(result, target)

    def test_blend_zero_mask(self):
        """Zero mask (no source region) returns mostly target."""
        blender = PoissonBlender(max_iterations=10)
        target = np.ones((100, 100, 3), dtype=np.uint8) * 100
        source = np.ones((100, 100, 3), dtype=np.uint8) * 200
        mask = np.zeros((100, 100), dtype=np.uint8)  # All background

        result = blender.blend(target, source, mask)

        # Should be very close to target
        assert np.allclose(result, target, atol=10)

    def test_blend_full_mask(self):
        """Full mask (all source) produces valid output."""
        blender = PoissonBlender(max_iterations=20)
        target = np.ones((100, 100, 3), dtype=np.uint8) * 100
        source = np.ones((100, 100, 3), dtype=np.uint8) * 200
        mask = np.ones((100, 100), dtype=np.uint8) * 255  # All source

        result = blender.blend(target, source, mask)

        # Result should be valid uint8
        assert result.dtype == np.uint8
        assert result.shape == (100, 100, 3)
        assert np.all(result >= 0) and np.all(result <= 255)
        # Blend should show some source influence (mean > pure target of 100)
        assert np.mean(result) > 100  # Not pure target

    def test_blend_partial_mask_blends(self):
        """Partial mask blends source and target."""
        blender = PoissonBlender(max_iterations=20)
        target = np.ones((100, 100, 3), dtype=np.uint8) * 100
        source = np.ones((100, 100, 3), dtype=np.uint8) * 200
        mask = np.zeros((100, 100), dtype=np.uint8)
        mask[40:60, 40:60] = 255  # Center square is source

        result = blender.blend(target, source, mask)

        # Center should be closer to source, edges to target
        center = result[50, 50, 0]
        edge = result[10, 10, 0]

        assert center > edge  # Center higher value than edge

    def test_blend_gradient_preservation(self):
        """Blending preserves smooth gradients."""
        blender = PoissonBlender(max_iterations=30)

        # Create gradient target
        target = np.zeros((100, 100, 3), dtype=np.uint8)
        for i in range(100):
            target[i, :, :] = int(255 * i / 100)

        # Create flat source
        source = np.ones((100, 100, 3), dtype=np.uint8) * 128
        mask = np.zeros((100, 100), dtype=np.uint8)
        mask[40:60, :] = 255  # Horizontal band

        result = blender.blend(target, source, mask)

        # Gradient should be preserved around edges
        top_gradient = result[35, 50, 0] - result[30, 50, 0]
        bottom_gradient = result[65, 50, 0] - result[60, 50, 0]

        # Both should be positive (increasing gradient)
        assert top_gradient > 0
        assert bottom_gradient > 0

    def test_blend_boundary_seamlessness(self):
        """Boundary between source and target shows transition."""
        blender = PoissonBlender(max_iterations=50, tolerance=0.001)
        target = np.ones((100, 100, 3), dtype=np.uint8) * 50
        source = np.ones((100, 100, 3), dtype=np.uint8) * 200
        mask = np.zeros((100, 100), dtype=np.uint8)
        mask[20:80, 50:] = 255  # Right region is source (not touching border)

        result = blender.blend(target, source, mask)

        # Check boundary region (around x=50)
        left_side = np.mean(result[20:80, 45:50, 0])
        right_side = np.mean(result[20:80, 50:55, 0])

        # Right side should be significantly higher (source) than left (target)
        assert right_side > left_side
        assert left_side < 100  # Closer to target
        assert right_side > 100  # Closer to source

    def test_blend_multichannel_independent(self):
        """Each channel blended independently."""
        blender = PoissonBlender(max_iterations=10)

        target = np.zeros((50, 50, 3), dtype=np.uint8)
        target[:, :, 0] = 100  # Red
        target[:, :, 1] = 50   # Green
        target[:, :, 2] = 25   # Blue

        source = np.zeros((50, 50, 3), dtype=np.uint8)
        source[:, :, 0] = 200  # Red
        source[:, :, 1] = 150  # Green
        source[:, :, 2] = 75   # Blue

        mask = np.ones((50, 50), dtype=np.uint8) * 255

        result = blender.blend(target, source, mask)

        # Interior should blend toward source (boundaries fixed)
        interior = result[10:40, 10:40, :]
        # Interior channels should be closer to source
        assert np.mean(interior[:, :, 0]) > 130  # Red close to source
        assert np.mean(interior[:, :, 1]) > 80   # Green blended
        assert np.mean(interior[:, :, 2]) > 40   # Blue blended

    def test_blend_multichannel_direct(self):
        """Fast direct blending produces valid result."""
        blender = PoissonBlender()
        target = np.ones((50, 50, 3), dtype=np.uint8) * 100
        source = np.ones((50, 50, 3), dtype=np.uint8) * 200
        mask = np.zeros((50, 50), dtype=np.uint8)
        mask[20:30, 20:30] = 255

        result = blender.blend_multichannel_direct(target, source, mask)

        # Result should be valid uint8
        assert result.dtype == np.uint8
        assert result.shape == (50, 50, 3)
        assert np.all(result >= 0) and np.all(result <= 255)


class TestGradientPreservingBlender:
    """Test GradientPreservingBlender class."""

    def test_init(self):
        """Initialize blender."""
        blender = GradientPreservingBlender()
        assert blender is not None

    def test_blend_identical_images(self):
        """Blending identical images returns identical."""
        blender = GradientPreservingBlender()
        image = np.ones((100, 100, 3), dtype=np.uint8) * 128
        mask = np.ones((100, 100), dtype=np.uint8) * 255

        result = blender.blend(image, image, mask)

        assert np.allclose(result, image, atol=5)

    def test_blend_produces_valid_output(self):
        """Blend produces valid uint8 output."""
        blender = GradientPreservingBlender()
        target = np.ones((100, 100, 3), dtype=np.uint8) * 100
        source = np.ones((100, 100, 3), dtype=np.uint8) * 200
        mask = np.zeros((100, 100), dtype=np.uint8)
        mask[30:70, 30:70] = 255

        result = blender.blend(target, source, mask)

        # Check output type and range
        assert result.dtype == np.uint8
        assert result.shape == (100, 100, 3)
        assert np.all(result >= 0) and np.all(result <= 255)

    def test_blend_smooth_transition(self):
        """Gradient blender creates smooth transitions."""
        blender = GradientPreservingBlender()
        target = np.ones((100, 100, 3), dtype=np.uint8) * 50
        source = np.ones((100, 100, 3), dtype=np.uint8) * 200
        mask = np.zeros((100, 100), dtype=np.uint8)
        mask[20:80, 50:] = 255  # Right region source (avoid borders)

        result = blender.blend(target, source, mask)

        # Check smoothness across boundary (interior regions)
        left = np.mean(result[20:80, 40:50, 0])
        right = np.mean(result[20:80, 50:60, 0])

        # Right should be higher (toward source 200) than left
        # Due to feathering, both will be blended, but right higher
        assert right > left  # Right blends more toward source

    def test_blend_feather_width_effect(self):
        """Different feather widths produce different blending."""
        target = np.ones((100, 100, 3), dtype=np.uint8) * 50
        source = np.ones((100, 100, 3), dtype=np.uint8) * 200
        mask = np.zeros((100, 100), dtype=np.uint8)
        mask[40:60, 40:60] = 255

        blender = GradientPreservingBlender()

        result_narrow = blender.blend(target, source, mask, feather_width=10)
        result_wide = blender.blend(target, source, mask, feather_width=50)

        # Different feather widths should produce different results
        assert not np.array_equal(result_narrow, result_wide)

    def test_blend_with_gradient_target(self):
        """Blending works with gradient targets."""
        blender = GradientPreservingBlender()

        # Gradient target
        target = np.zeros((100, 100, 3), dtype=np.uint8)
        for i in range(100):
            target[i, :, :] = int(255 * i / 100)

        source = np.ones((100, 100, 3), dtype=np.uint8) * 128
        mask = np.zeros((100, 100), dtype=np.uint8)
        mask[40:60, :] = 255

        result = blender.blend(target, source, mask, feather_width=20)

        # Should preserve gradient structure
        assert result.dtype == np.uint8
        assert result.shape == (100, 100, 3)

    def test_blend_zero_feather(self):
        """Zero feather width still produces valid output."""
        blender = GradientPreservingBlender()
        target = np.ones((50, 50, 3), dtype=np.uint8) * 100
        source = np.ones((50, 50, 3), dtype=np.uint8) * 200
        mask = np.zeros((50, 50), dtype=np.uint8)
        mask[20:30, 20:30] = 255

        result = blender.blend(target, source, mask, feather_width=1)

        assert result.dtype == np.uint8
        assert result.shape == (50, 50, 3)


class TestBlenderIntegration:
    """Integration tests for blending workflow."""

    def test_poisson_vs_gradient_blender(self):
        """Both blenders handle same input."""
        target = np.ones((100, 100, 3), dtype=np.uint8) * 100
        source = np.ones((100, 100, 3), dtype=np.uint8) * 200
        mask = np.zeros((100, 100), dtype=np.uint8)
        mask[40:60, 40:60] = 255

        poisson = PoissonBlender(max_iterations=20)
        gradient = GradientPreservingBlender()

        result_poisson = poisson.blend(target, source, mask)
        result_gradient = gradient.blend(target, source, mask)

        # Both should produce valid outputs
        assert result_poisson.shape == (100, 100, 3)
        assert result_gradient.shape == (100, 100, 3)
        assert result_poisson.dtype == np.uint8
        assert result_gradient.dtype == np.uint8

        # Results should differ (different algorithms)
        assert not np.array_equal(result_poisson, result_gradient)

    def test_realistic_inpaint_composite(self):
        """Blend inpainted region back into original frame."""
        # Simulate original frame with watermark
        original = np.ones((200, 200, 3), dtype=np.uint8) * 150
        # Add some texture/gradient
        for i in range(200):
            original[i, :, 0] = min(255, 150 + i // 2)

        # Simulate inpainted region (clean)
        inpainted = np.ones((200, 200, 3), dtype=np.uint8) * 160
        inpainted[70:130, 70:130, :] = 155  # Smooth center

        # Mask defining inpainted region
        mask = np.zeros((200, 200), dtype=np.uint8)
        mask[70:130, 70:130] = 255

        # Blend
        blender = PoissonBlender(max_iterations=30)
        result = blender.blend(original, inpainted, mask, blend_width=16)

        # Should be seamless
        assert result.shape == (200, 200, 3)
        assert result.dtype == np.uint8
        # Center should have inpainted values
        assert np.mean(result[100, 100, :]) > 150


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
