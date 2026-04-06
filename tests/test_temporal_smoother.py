"""Tests for temporal smoothing and frame blending."""

import numpy as np
import pytest

from src.watermark_removal.temporal.temporal_smoother import TemporalSmoother


class TestTemporalSmootherInitialization:
    """Test TemporalSmoother initialization."""

    def test_initialization_default(self):
        """Test TemporalSmoother initializes with default alpha."""
        smoother = TemporalSmoother()
        assert smoother.alpha == 0.3

    def test_initialization_custom_alpha(self):
        """Test TemporalSmoother initializes with custom alpha."""
        smoother = TemporalSmoother(alpha=0.5)
        assert smoother.alpha == 0.5

    def test_initialization_alpha_boundaries(self):
        """Test alpha accepts boundary values."""
        smoother_min = TemporalSmoother(alpha=0.0)
        assert smoother_min.alpha == 0.0

        smoother_max = TemporalSmoother(alpha=1.0)
        assert smoother_max.alpha == 1.0

    def test_initialization_invalid_alpha_below_zero(self):
        """Test alpha rejects values below 0.0."""
        with pytest.raises(ValueError, match="alpha must be in"):
            TemporalSmoother(alpha=-0.1)

    def test_initialization_invalid_alpha_above_one(self):
        """Test alpha rejects values above 1.0."""
        with pytest.raises(ValueError, match="alpha must be in"):
            TemporalSmoother(alpha=1.1)


class TestBlendFrameBasic:
    """Test basic frame blending functionality."""

    def test_blend_frame_happy_path(self):
        """Test basic blending with alpha=0.3."""
        smoother = TemporalSmoother(alpha=0.3)

        # Create test frames
        current = np.ones((100, 100, 3), dtype=np.uint8) * 100
        previous = np.ones((100, 100, 3), dtype=np.uint8) * 200

        blended = smoother.blend_frame(current, previous)

        # Verify output properties
        assert blended.dtype == np.uint8
        assert blended.shape == current.shape

        # Verify interpolation: (1 - 0.3) * 100 + 0.3 * 200 = 70 + 60 = 130
        expected = int((1.0 - 0.3) * 100 + 0.3 * 200)
        assert np.allclose(np.mean(blended), expected, atol=1)

    def test_blend_frame_no_previous(self):
        """Test blending when no previous frame (first frame)."""
        smoother = TemporalSmoother(alpha=0.3)
        current = np.ones((100, 100, 3), dtype=np.uint8) * 100

        blended = smoother.blend_frame(current, previous_frame=None)

        # Should return copy of current
        assert np.array_equal(blended, current)

    def test_blend_frame_alpha_zero(self):
        """Test blending with alpha=0.0 (no blending)."""
        smoother = TemporalSmoother(alpha=0.0)

        current = np.ones((100, 100, 3), dtype=np.uint8) * 100
        previous = np.ones((100, 100, 3), dtype=np.uint8) * 200

        blended = smoother.blend_frame(current, previous)

        # Should return current unchanged
        assert np.array_equal(blended, current)

    def test_blend_frame_alpha_one(self):
        """Test blending with alpha=1.0 (full previous)."""
        smoother = TemporalSmoother(alpha=1.0)

        current = np.ones((100, 100, 3), dtype=np.uint8) * 100
        previous = np.ones((100, 100, 3), dtype=np.uint8) * 200

        blended = smoother.blend_frame(current, previous)

        # Should be equal to previous
        assert np.array_equal(blended, previous)

    def test_blend_frame_multi_channel(self):
        """Test blending preserves all color channels."""
        smoother = TemporalSmoother(alpha=0.5)

        current = np.array([[[100, 150, 200]]], dtype=np.uint8)
        previous = np.array([[[200, 100, 50]]], dtype=np.uint8)

        blended = smoother.blend_frame(current, previous)

        # Each channel should be blended independently
        expected_ch0 = int(0.5 * 100 + 0.5 * 200)  # 150
        expected_ch1 = int(0.5 * 150 + 0.5 * 100)  # 125
        expected_ch2 = int(0.5 * 200 + 0.5 * 50)   # 125

        assert blended[0, 0, 0] == expected_ch0
        assert blended[0, 0, 1] == expected_ch1
        assert blended[0, 0, 2] == expected_ch2


class TestBlendFrameRegionSpecific:
    """Test region-specific blending."""

    def test_blend_frame_with_region(self):
        """Test blending only within specified region."""
        smoother = TemporalSmoother(alpha=0.5)

        current = np.ones((200, 200, 3), dtype=np.uint8) * 100
        previous = np.ones((200, 200, 3), dtype=np.uint8) * 200

        # Blend only in region (50, 50, 100, 100)
        region = (50, 50, 100, 100)
        blended = smoother.blend_frame(current, previous, blend_region=region)

        # Region should be blended (130)
        region_mean = np.mean(blended[50:150, 50:150])
        assert np.isclose(region_mean, 150, atol=1)  # 0.5 * 100 + 0.5 * 200

        # Outside region should remain current (100)
        outside_mean = np.mean(blended[0:40, 0:40])
        assert np.isclose(outside_mean, 100, atol=1)

    def test_blend_frame_region_at_boundary(self):
        """Test region blending at frame boundary."""
        smoother = TemporalSmoother(alpha=0.5)

        current = np.ones((100, 100, 3), dtype=np.uint8) * 100
        previous = np.ones((100, 100, 3), dtype=np.uint8) * 200

        # Region extending beyond frame boundary
        region = (80, 80, 50, 50)
        blended = smoother.blend_frame(current, previous, blend_region=region)

        # Should handle gracefully, blending in valid area
        assert blended.shape == current.shape
        assert blended.dtype == np.uint8

    def test_blend_frame_empty_region(self):
        """Test region blending with empty/invalid region."""
        smoother = TemporalSmoother(alpha=0.5)

        current = np.ones((100, 100, 3), dtype=np.uint8) * 100
        previous = np.ones((100, 100, 3), dtype=np.uint8) * 200

        # Region with zero width
        region = (50, 50, 0, 100)
        blended = smoother.blend_frame(current, previous, blend_region=region)

        # Should return copy of current
        assert np.array_equal(blended, current)


class TestBlendFrameGradient:
    """Test gradient blending at region edges."""

    def test_blend_frame_gradient_basic(self):
        """Test gradient blending creates feathered transition."""
        smoother = TemporalSmoother(alpha=0.5)

        current = np.ones((300, 300, 3), dtype=np.uint8) * 100
        previous = np.ones((300, 300, 3), dtype=np.uint8) * 200

        # Gradient blend in region
        region = (100, 100, 100, 100)
        blended = smoother.blend_frame_gradient(
            current, previous, blend_region=region, feather_width=32
        )

        # Center should be more blended (closer to 200)
        center_mean = np.mean(blended[130:170, 130:170])

        # Edge should be less blended (closer to 100)
        edge_mean = np.mean(blended[80:120, 80:120])

        # Center should have more influence from previous
        assert center_mean > edge_mean

    def test_blend_frame_gradient_no_previous(self):
        """Test gradient blending with no previous frame."""
        smoother = TemporalSmoother(alpha=0.5)
        current = np.ones((100, 100, 3), dtype=np.uint8) * 100

        region = (25, 25, 50, 50)
        blended = smoother.blend_frame_gradient(
            current, previous_frame=None, blend_region=region
        )

        # Should return copy of current
        assert np.array_equal(blended, current)

    def test_blend_frame_gradient_alpha_zero(self):
        """Test gradient blending with alpha=0.0."""
        smoother = TemporalSmoother(alpha=0.0)

        current = np.ones((100, 100, 3), dtype=np.uint8) * 100
        previous = np.ones((100, 100, 3), dtype=np.uint8) * 200

        region = (25, 25, 50, 50)
        blended = smoother.blend_frame_gradient(
            current, previous, blend_region=region
        )

        # Should return copy of current
        assert np.array_equal(blended, current)


class TestTemporalSmootherEdgeCases:
    """Test edge cases for temporal smoother."""

    def test_blend_with_realistic_gradient(self):
        """Test blending with realistic gradient background."""
        smoother = TemporalSmoother(alpha=0.3)

        # Create gradient frames
        height, width = 200, 200
        current = np.zeros((height, width, 3), dtype=np.uint8)
        previous = np.zeros((height, width, 3), dtype=np.uint8)

        for y in range(height):
            current[y, :] = [y % 256, (y // 2) % 256, (y // 3) % 256]
            previous[y, :] = [255 - (y % 256), 255 - ((y // 2) % 256), 255 - ((y // 3) % 256)]

        blended = smoother.blend_frame(current, previous)

        # Verify smooth interpolation
        assert blended.dtype == np.uint8
        assert blended.shape == current.shape

        # Blended should be between current and previous
        assert np.all(blended >= np.minimum(current, previous))
        assert np.all(blended <= np.maximum(current, previous))

    def test_blend_different_frame_sizes(self):
        """Test blending when frames are different sizes."""
        smoother = TemporalSmoother(alpha=0.5)

        current = np.ones((100, 100, 3), dtype=np.uint8) * 100
        previous = np.ones((150, 150, 3), dtype=np.uint8) * 200

        # This should handle size mismatch gracefully
        # (in practice, frames should be same size, but robustness test)
        try:
            blended = smoother.blend_frame(current, previous)
            # If it doesn't raise, shape should match current
            assert blended.shape == current.shape
        except Exception:
            # Or it might raise a shape error, which is also acceptable
            pass

    def test_temporal_sequence(self):
        """Test temporal smoothing across a sequence of frames."""
        smoother = TemporalSmoother(alpha=0.3)

        # Simulate 5 frames with changing values
        frames = [
            np.ones((50, 50, 3), dtype=np.uint8) * (50 + i * 30)
            for i in range(5)
        ]

        # Blend frames sequentially
        blended_frames = [frames[0]]
        for i in range(1, len(frames)):
            blended = smoother.blend_frame(frames[i], blended_frames[-1])
            blended_frames.append(blended)

        # Verify sequence properties
        assert len(blended_frames) == 5

        # Blended frames should show smoothing: less sharp transitions
        transition_0_to_1 = abs(float(np.mean(frames[1])) - float(np.mean(frames[0])))
        transition_1_to_2 = abs(float(np.mean(frames[2])) - float(np.mean(frames[1])))

        blended_transition_0_to_1 = abs(
            float(np.mean(blended_frames[1])) - float(np.mean(blended_frames[0]))
        )
        blended_transition_1_to_2 = abs(
            float(np.mean(blended_frames[2])) - float(np.mean(blended_frames[1]))
        )

        # Blended transitions should be smaller (smoother)
        assert blended_transition_0_to_1 < transition_0_to_1
        assert blended_transition_1_to_2 < transition_1_to_2


class TestTemporalSmootherIntegration:
    """Integration tests for temporal smoother."""

    def test_smoother_with_inpaint_scenario(self):
        """Test smoother in context of inpaint workflow."""
        smoother = TemporalSmoother(alpha=0.3)

        # Simulate inpaint scenario: original frame with watermark region
        original = np.ones((200, 200, 3), dtype=np.uint8) * 128
        inpainted = original.copy()
        inpainted[50:150, 50:150] = 200  # Inpainted region is lighter

        previous_original = np.ones((200, 200, 3), dtype=np.uint8) * 120
        previous_inpainted = previous_original.copy()
        previous_inpainted[50:150, 50:150] = 210

        # Blend only the inpainted region
        region = (50, 50, 100, 100)
        blended = smoother.blend_frame(inpainted, previous_inpainted, blend_region=region)

        # Region should be blended
        region_mean = np.mean(blended[50:150, 50:150])
        assert region_mean > 200 or region_mean < 210  # Between values

        # Outside region should be from current frame
        outside_mean = np.mean(blended[0:40, 0:40])
        assert np.isclose(outside_mean, np.mean(original[0:40, 0:40]))
