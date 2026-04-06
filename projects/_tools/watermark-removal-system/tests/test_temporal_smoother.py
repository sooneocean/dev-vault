"""
Unit tests for watermark_removal.postprocessing.temporal_smoother module.

Tests temporal smoothing logic and adaptive blending.
"""

import pytest
import numpy as np

from src.watermark_removal.postprocessing.temporal_smoother import (
    TemporalSmoother,
    AdaptiveTemporalSmoother,
)


class TestTemporalSmoother:
    """Test TemporalSmoother class."""

    def test_init_valid_alpha(self):
        """Initialize with valid alpha values."""
        for alpha in [0.0, 0.1, 0.3, 0.5, 0.9, 1.0]:
            smoother = TemporalSmoother(alpha=alpha)
            assert smoother.alpha == alpha

    def test_init_invalid_alpha(self):
        """Reject invalid alpha values."""
        with pytest.raises(ValueError):
            TemporalSmoother(alpha=-0.1)

        with pytest.raises(ValueError):
            TemporalSmoother(alpha=1.5)

    def test_smooth_frame_no_previous(self):
        """Smoothing without previous frame returns current frame unchanged."""
        smoother = TemporalSmoother(alpha=0.5)
        current = np.ones((100, 100, 3), dtype=np.uint8) * 128

        result = smoother.smooth_frame(current, previous_frame=None)

        assert np.array_equal(result, current)

    def test_smooth_frame_zero_alpha(self):
        """Zero alpha means no smoothing."""
        smoother = TemporalSmoother(alpha=0.0)
        current = np.ones((100, 100, 3), dtype=np.uint8) * 100
        previous = np.ones((100, 100, 3), dtype=np.uint8) * 200

        result = smoother.smooth_frame(current, previous_frame=previous)

        assert np.array_equal(result, current)

    def test_smooth_frame_full_alpha(self):
        """Alpha=1.0 gives equal weight to current and previous."""
        smoother = TemporalSmoother(alpha=1.0)
        current = np.ones((100, 100, 3), dtype=np.uint8) * 100
        previous = np.ones((100, 100, 3), dtype=np.uint8) * 200

        result = smoother.smooth_frame(current, previous_frame=previous)

        # With alpha=1.0: result = 0*current + 1*previous = previous
        assert np.allclose(result, 200, atol=1)

    def test_smooth_frame_partial_alpha(self):
        """Partial alpha blends correctly."""
        smoother = TemporalSmoother(alpha=0.5)
        current = np.ones((100, 100, 3), dtype=np.uint8) * 100
        previous = np.ones((100, 100, 3), dtype=np.uint8) * 200

        result = smoother.smooth_frame(current, previous_frame=previous)

        # With alpha=0.5: result = 0.5*100 + 0.5*200 = 150
        assert np.allclose(result, 150, atol=1)

    def test_smooth_frame_shape_mismatch(self):
        """Shape mismatch returns current frame unchanged."""
        smoother = TemporalSmoother(alpha=0.5)
        current = np.ones((100, 100, 3), dtype=np.uint8) * 100
        previous = np.ones((200, 200, 3), dtype=np.uint8) * 200

        result = smoother.smooth_frame(current, previous_frame=previous)

        assert np.array_equal(result, current)

    def test_smooth_sequence(self):
        """Smooth entire sequence of frames."""
        smoother = TemporalSmoother(alpha=0.3)

        # Create 3 frames with different values
        frames = [
            np.ones((100, 100, 3), dtype=np.uint8) * 100,
            np.ones((100, 100, 3), dtype=np.uint8) * 150,
            np.ones((100, 100, 3), dtype=np.uint8) * 200,
        ]

        result = smoother.smooth_sequence(frames)

        # First frame unchanged
        assert np.array_equal(result[0], frames[0])

        # Second frame blended: 0.7*150 + 0.3*100
        expected_second = np.clip(0.7 * 150 + 0.3 * 100, 0, 255)
        assert np.allclose(result[1], expected_second, atol=1)

        # Third frame blended with smoothed second
        expected_third = np.clip(0.7 * 200 + 0.3 * expected_second, 0, 255)
        assert np.allclose(result[2], expected_third, atol=1)

    def test_smooth_sequence_empty(self):
        """Empty sequence returns empty."""
        smoother = TemporalSmoother(alpha=0.5)
        result = smoother.smooth_sequence([])
        assert result == []

    def test_smooth_sequence_single_frame(self):
        """Single frame unchanged."""
        smoother = TemporalSmoother(alpha=0.5)
        frames = [np.ones((100, 100, 3), dtype=np.uint8) * 100]

        result = smoother.smooth_sequence(frames)

        assert len(result) == 1
        assert np.array_equal(result[0], frames[0])

    def test_smooth_bidirectional(self):
        """Bidirectional smoothing produces different result than unidirectional."""
        smoother = TemporalSmoother(alpha=0.3)

        frames = [
            np.ones((100, 100, 3), dtype=np.uint8) * 100,
            np.ones((100, 100, 3), dtype=np.uint8) * 150,
            np.ones((100, 100, 3), dtype=np.uint8) * 200,
        ]

        uni_result = smoother.smooth_sequence(frames)
        bi_result = smoother.smooth_bidirectional(frames)

        # Results should be different
        assert not np.array_equal(uni_result[1], bi_result[1])

        # Bidirectional should be more stable (centered)
        # Middle frame should be closer to 150 in bidirectional
        assert np.mean(bi_result[1]) > np.mean(uni_result[1])


class TestAdaptiveTemporalSmoother:
    """Test AdaptiveTemporalSmoother class."""

    def test_adaptive_low_motion(self):
        """Low motion: use full alpha."""
        smoother = AdaptiveTemporalSmoother(alpha=0.5)

        # Similar frames (low motion)
        current = np.ones((100, 100, 3), dtype=np.uint8) * 100
        previous = np.ones((100, 100, 3), dtype=np.uint8) * 101

        result, used_alpha = smoother.smooth_frame_adaptive(
            current, previous_frame=previous, motion_threshold=0.05
        )

        # Should use full alpha
        assert used_alpha == pytest.approx(0.5, rel=0.1)

    def test_adaptive_high_motion(self):
        """High motion: reduce alpha."""
        smoother = AdaptiveTemporalSmoother(alpha=0.5)

        # Different frames (high motion)
        current = np.ones((100, 100, 3), dtype=np.uint8) * 100
        previous = np.ones((100, 100, 3), dtype=np.uint8) * 200

        result, used_alpha = smoother.smooth_frame_adaptive(
            current, previous_frame=previous, motion_threshold=0.05
        )

        # Should use reduced alpha (0.3 * 0.5 = 0.15)
        assert used_alpha < smoother.alpha
        assert used_alpha == pytest.approx(0.5 * 0.3, rel=0.1)

    def test_adaptive_no_previous(self):
        """No previous frame returns 0 alpha."""
        smoother = AdaptiveTemporalSmoother(alpha=0.5)
        current = np.ones((100, 100, 3), dtype=np.uint8) * 100

        result, used_alpha = smoother.smooth_frame_adaptive(current, previous_frame=None)

        assert used_alpha == 0.0
        assert np.array_equal(result, current)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
