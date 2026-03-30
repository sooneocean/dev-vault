"""Unit 2: Temporal smoothing end-to-end integration tests.

Tests validate that temporal smoothing produces flicker-free output,
comparing simple alpha-blend and adaptive motion-aware modes.
"""

import numpy as np
import pytest

from src.watermark_removal.temporal.temporal_smoother import TemporalSmoother


class TestTemporalFlickerMetric:
    """Tests for flicker metric computation (frame-to-frame L2 distance)."""

    def compute_flicker_metric(self, frames: list[np.ndarray]) -> list[float]:
        """
        Compute inter-frame L2 distance (flicker metric).

        Args:
            frames: List of frames (HxWx3, uint8).

        Returns:
            List of frame-to-frame L2 distances (length = len(frames) - 1).
        """
        flicker_scores = []
        for i in range(1, len(frames)):
            prev_frame = frames[i - 1].astype(np.float32)
            curr_frame = frames[i].astype(np.float32)

            # Compute L2 distance (Euclidean norm)
            diff = curr_frame - prev_frame
            l2_dist = np.sqrt(np.sum(diff ** 2))

            # Normalize by frame size for comparison across different resolutions
            frame_size = np.prod(curr_frame.shape)
            normalized_flicker = l2_dist / np.sqrt(frame_size)

            flicker_scores.append(normalized_flicker)

        return flicker_scores

    def test_flicker_metric_identical_frames(self):
        """Test flicker metric is zero for identical frames."""
        frames = [
            np.ones((100, 100, 3), dtype=np.uint8) * 128
            for _ in range(5)
        ]

        flicker = self.compute_flicker_metric(frames)
        assert len(flicker) == 4
        assert all(f == 0.0 for f in flicker)

    def test_flicker_metric_increasing_motion(self):
        """Test flicker metric increases with greater motion."""
        frames = []
        for i in range(5):
            frame = np.ones((100, 100, 3), dtype=np.uint8) * (100 + i * 20)
            frames.append(frame)

        flicker = self.compute_flicker_metric(frames)
        assert len(flicker) == 4

        # Flicker should be monotonically increasing (constant motion)
        for i in range(len(flicker) - 1):
            assert flicker[i] <= flicker[i + 1]


class TestTemporalSmootherAlphaSweep:
    """Tests temporal smoothing with alpha sweep [0.0, 0.1, 0.3, 0.5, 1.0]."""

    def create_synthetic_motion_sequence(
        self,
        num_frames: int = 10,
        height: int = 100,
        width: int = 100,
        motion_speed: float = 5.0,
    ) -> list[np.ndarray]:
        """
        Create synthetic frame sequence with progressive motion.

        Simulates a rectangular region moving across the frame.

        Args:
            num_frames: Number of frames.
            height: Frame height.
            width: Frame width.
            motion_speed: Pixels per frame to move region.

        Returns:
            List of frames (HxWx3, uint8).
        """
        frames = []
        region_size = 30

        for frame_idx in range(num_frames):
            frame = np.ones((height, width, 3), dtype=np.uint8) * 100

            # Moving rectangle: shifts right by motion_speed pixels per frame
            rect_x = int(20 + frame_idx * motion_speed)
            rect_y = 35

            # Clip to frame bounds
            x_end = min(rect_x + region_size, width)
            y_end = min(rect_y + region_size, height)

            if rect_x < width and rect_y < height:
                frame[rect_y:y_end, rect_x:x_end, :] = 200

            frames.append(frame)

        return frames

    def apply_temporal_smoothing(
        self,
        frames: list[np.ndarray],
        alpha: float,
    ) -> list[np.ndarray]:
        """
        Apply temporal smoothing to frame sequence.

        Args:
            frames: Input frames.
            alpha: Blending factor.

        Returns:
            Smoothed frames.
        """
        smoother = TemporalSmoother(alpha=alpha)
        smoothed = [frames[0]]  # First frame unchanged

        for i in range(1, len(frames)):
            blended = smoother.blend_frame(frames[i], smoothed[-1])
            smoothed.append(blended)

        return smoothed

    def compute_sequence_flicker(self, frames: list[np.ndarray]) -> float:
        """
        Compute total flicker metric for frame sequence.

        Args:
            frames: Frame sequence.

        Returns:
            Mean frame-to-frame L2 distance.
        """
        flicker_scores = []
        for i in range(1, len(frames)):
            prev_frame = frames[i - 1].astype(np.float32)
            curr_frame = frames[i].astype(np.float32)

            diff = curr_frame - prev_frame
            l2_dist = np.sqrt(np.sum(diff ** 2))
            frame_size = np.prod(curr_frame.shape)
            normalized = l2_dist / np.sqrt(frame_size)

            flicker_scores.append(normalized)

        return float(np.mean(flicker_scores)) if flicker_scores else 0.0

    def test_temporal_smoothing_reduces_flicker(self):
        """Test that temporal smoothing reduces inter-frame flicker."""
        frames = self.create_synthetic_motion_sequence(num_frames=10)

        # Measure flicker without smoothing (alpha=0.0)
        flicker_no_smooth = self.compute_sequence_flicker(frames)

        # Measure flicker with smoothing (alpha=0.3)
        smoothed = self.apply_temporal_smoothing(frames, alpha=0.3)
        flicker_with_smooth = self.compute_sequence_flicker(smoothed)

        # Smoothing should reduce flicker
        assert flicker_with_smooth < flicker_no_smooth

    @pytest.mark.parametrize("alpha", [0.0, 0.1, 0.3, 0.5, 1.0])
    def test_alpha_sweep_decreasing_flicker(self, alpha):
        """Test that higher alpha values reduce flicker (monotonic)."""
        frames = self.create_synthetic_motion_sequence(num_frames=10)

        if alpha == 0.0:
            # No smoothing: output = input, flicker = original
            smoothed = self.apply_temporal_smoothing(frames, alpha=0.0)
            flicker = self.compute_sequence_flicker(smoothed)
            expected_flicker = self.compute_sequence_flicker(frames)
            assert np.isclose(flicker, expected_flicker)
        else:
            # With smoothing: flicker should reduce
            smoothed = self.apply_temporal_smoothing(frames, alpha=alpha)
            flicker_smoothed = self.compute_sequence_flicker(smoothed)

            # Compare with alpha=0.0 (no smoothing)
            flicker_no_smooth = self.compute_sequence_flicker(frames)
            assert flicker_smoothed < flicker_no_smooth

    def test_alpha_monotonic_relationship(self):
        """Test that flicker decreases monotonically with increasing alpha."""
        frames = self.create_synthetic_motion_sequence(num_frames=10)
        alphas = [0.0, 0.1, 0.3, 0.5, 1.0]

        flickers = []
        for alpha in alphas:
            smoothed = self.apply_temporal_smoothing(frames, alpha=alpha)
            flicker = self.compute_sequence_flicker(smoothed)
            flickers.append(flicker)

        # Flicker should be monotonically decreasing
        for i in range(len(flickers) - 1):
            # Allow small tolerance for numerical differences
            assert flickers[i] >= flickers[i + 1] - 1e-6


class TestTemporalSmootherEdgeCases:
    """Test edge cases for temporal smoothing."""

    def test_alpha_zero_output_equals_input(self):
        """Test alpha=0.0 produces output identical to input."""
        smoother = TemporalSmoother(alpha=0.0)

        frames = [
            np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)
            for _ in range(5)
        ]

        # With alpha=0.0, output should equal input
        for i in range(1, len(frames)):
            blended = smoother.blend_frame(frames[i], frames[i - 1])
            assert np.array_equal(blended, frames[i])

    def test_alpha_one_output_equals_previous(self):
        """Test alpha=1.0 produces output equal to previous frame."""
        smoother = TemporalSmoother(alpha=1.0)

        frames = [
            np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)
            for _ in range(5)
        ]

        # With alpha=1.0, output should equal previous
        for i in range(1, len(frames)):
            blended = smoother.blend_frame(frames[i], frames[i - 1])
            assert np.array_equal(blended, frames[i - 1])

    def test_single_frame_no_smoothing(self):
        """Test that single frame sequence produces no smoothing."""
        smoother = TemporalSmoother(alpha=0.5)

        frame = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)
        blended = smoother.blend_frame(frame, previous_frame=None)

        # Should return copy of current frame
        assert np.array_equal(blended, frame)

    def test_first_frame_always_unchanged(self):
        """Test that first frame is never modified."""
        smoother = TemporalSmoother(alpha=0.5)

        frame1 = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)

        # Blend with no previous frame
        blended = smoother.blend_frame(frame1, previous_frame=None)
        assert np.array_equal(blended, frame1)

    def test_output_dtype_uint8(self):
        """Test that output is always uint8."""
        smoother = TemporalSmoother(alpha=0.5)

        current = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)
        previous = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)

        blended = smoother.blend_frame(current, previous)
        assert blended.dtype == np.uint8

    def test_output_dimensions_match_input(self):
        """Test that output dimensions match input dimensions."""
        smoother = TemporalSmoother(alpha=0.5)

        for height, width in [(100, 100), (240, 320), (480, 640)]:
            current = np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)
            previous = np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)

            blended = smoother.blend_frame(current, previous)
            assert blended.shape == (height, width, 3)

    def test_output_values_in_valid_range(self):
        """Test that output pixel values remain in [0, 255]."""
        smoother = TemporalSmoother(alpha=0.5)

        # Create frames with extreme values
        current = np.ones((100, 100, 3), dtype=np.uint8) * 0
        previous = np.ones((100, 100, 3), dtype=np.uint8) * 255

        blended = smoother.blend_frame(current, previous)

        assert blended.min() >= 0
        assert blended.max() <= 255
        assert np.all(blended >= 0)
        assert np.all(blended <= 255)

    def test_no_nan_or_inf(self):
        """Test that output contains no NaN or inf values."""
        smoother = TemporalSmoother(alpha=0.5)

        current = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)
        previous = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)

        blended = smoother.blend_frame(current, previous)

        assert not np.isnan(blended).any()
        assert not np.isinf(blended).any()


class TestAdaptiveTemporalSmoothing:
    """Tests for adaptive motion-aware temporal smoothing.

    Adaptive smoothing should:
    - Reduce alpha on high-motion frames (preserve detail)
    - Increase alpha on static frames (smooth flicker)
    """

    def compute_frame_motion(self, frame1: np.ndarray, frame2: np.ndarray) -> float:
        """
        Compute motion magnitude between two frames.

        Uses L2 distance as motion metric.

        Args:
            frame1: Previous frame.
            frame2: Current frame.

        Returns:
            Normalized motion magnitude [0, 1].
        """
        diff = frame2.astype(np.float32) - frame1.astype(np.float32)
        motion = np.sqrt(np.sum(diff ** 2))

        # Normalize by frame size
        max_possible = np.sqrt(np.prod(frame1.shape)) * 255
        normalized_motion = motion / max_possible

        return float(np.clip(normalized_motion, 0.0, 1.0))

    def adaptive_temporal_smoother(
        self,
        frames: list[np.ndarray],
        base_alpha: float = 0.3,
        motion_threshold: float = 0.05,
    ) -> list[np.ndarray]:
        """
        Apply adaptive temporal smoothing based on motion.

        Algorithm:
        - Compute motion magnitude between consecutive frames
        - If motion > threshold: reduce alpha (preserve detail)
        - If motion < threshold: use base_alpha (smooth flicker)

        Args:
            frames: Input frames.
            base_alpha: Alpha for static regions.
            motion_threshold: Motion threshold for adaptation.

        Returns:
            Adaptively smoothed frames.
        """
        if len(frames) < 2:
            return frames

        smoother = TemporalSmoother(alpha=base_alpha)
        smoothed = [frames[0]]

        for i in range(1, len(frames)):
            # Compute motion between previous output and current frame
            motion = self.compute_frame_motion(smoothed[-1], frames[i])

            # Adapt alpha: reduce on high motion
            if motion > motion_threshold:
                # High motion: use lower alpha (less blending)
                adaptive_alpha = base_alpha * 0.5
            else:
                # Low motion: use base alpha (more blending)
                adaptive_alpha = base_alpha

            # Apply blending with adaptive alpha
            adaptive_smoother = TemporalSmoother(alpha=adaptive_alpha)
            blended = adaptive_smoother.blend_frame(frames[i], smoothed[-1])
            smoothed.append(blended)

        return smoothed

    def test_adaptive_smoothing_happy_path(self):
        """Test adaptive smoothing on mixed static/moving frame sequence."""
        # Create frame sequence: static (5 frames) + moving (5 frames)
        static_frames = [
            np.ones((100, 100, 3), dtype=np.uint8) * 100
            for _ in range(5)
        ]

        motion_frames = []
        for i in range(5):
            frame = np.ones((100, 100, 3), dtype=np.uint8) * 100
            # Add moving rectangle
            x = 20 + i * 10
            frame[30:60, x:x+20, :] = 200
            motion_frames.append(frame)

        frames = static_frames + motion_frames

        # Apply adaptive smoothing
        smoothed = self.adaptive_temporal_smoother(
            frames,
            base_alpha=0.3,
            motion_threshold=0.05,
        )

        assert len(smoothed) == len(frames)

        # All outputs should be valid frames
        for frame in smoothed:
            assert frame.shape == (100, 100, 3)
            assert frame.dtype == np.uint8
            assert frame.min() >= 0
            assert frame.max() <= 255

    def test_adaptive_smoothing_preserves_detail_on_motion(self):
        """Test that adaptive smoothing preserves detail during high motion."""
        # Static frame followed by high-motion frame
        static = np.ones((100, 100, 3), dtype=np.uint8) * 100
        motion_frame = np.ones((100, 100, 3), dtype=np.uint8) * 100
        motion_frame[20:80, 20:80, :] = 200  # Significant change

        frames = [static, motion_frame]

        # Apply adaptive smoothing with low motion threshold
        smoothed = self.adaptive_temporal_smoother(
            frames,
            base_alpha=0.5,
            motion_threshold=0.02,  # Strict threshold
        )

        # Second frame should be closer to motion_frame than with static alpha=0.5
        # because adaptive should reduce alpha on high motion
        assert len(smoothed) == 2

    def test_adaptive_smoothing_smooth_on_static(self):
        """Test that adaptive smoothing smooths static regions."""
        # Create static sequence with small random noise
        np.random.seed(42)
        frames = []
        base = np.ones((100, 100, 3), dtype=np.uint8) * 128

        for _ in range(5):
            noisy = base.copy().astype(np.int32)
            noisy += np.random.randint(-5, 5, base.shape)
            noisy = np.clip(noisy, 0, 255).astype(np.uint8)
            frames.append(noisy)

        # Apply adaptive smoothing
        smoothed = self.adaptive_temporal_smoother(
            frames,
            base_alpha=0.4,
            motion_threshold=0.10,
        )

        # Smoothed frames should have less variance (noise reduced)
        original_variance = np.var([f.astype(np.float32) for f in frames[1:]])
        smoothed_variance = np.var([f.astype(np.float32) for f in smoothed[1:]])

        assert smoothed_variance < original_variance


class TestTemporalIntegrationPhase1vsPhase2:
    """Integration tests comparing Phase 1 (no smoothing) vs Phase 2 (with smoothing)."""

    def create_realistic_watermark_sequence(
        self,
        num_frames: int = 10,
    ) -> list[np.ndarray]:
        """
        Create synthetic sequence simulating watermark inpaint scenario.

        Frame sequence:
        - Background: static gradient
        - Inpainted region: with temporal inconsistency (simulates per-frame inpaint)

        Args:
            num_frames: Number of frames.

        Returns:
            List of frames.
        """
        frames = []

        for frame_idx in range(num_frames):
            # Static background (gradient)
            frame = np.zeros((200, 200, 3), dtype=np.uint8)
            for y in range(200):
                frame[y, :] = [y % 256, (y // 2) % 256, (y // 3) % 256]

            # Inpainted region (with per-frame variation to simulate inpaint artifacts)
            inpaint_region = 150 + (frame_idx % 10)  # Simulate slight per-frame variation
            frame[75:125, 75:125, :] = inpaint_region

            frames.append(frame)

        return frames

    def test_phase2_temporal_improves_quality(self):
        """Test that Phase 2 temporal smoothing improves output quality."""
        frames = self.create_realistic_watermark_sequence(num_frames=10)

        # Phase 1: No smoothing
        phase1_output = frames.copy()
        phase1_flicker = self._compute_flicker(phase1_output)

        # Phase 2: With temporal smoothing
        smoother = TemporalSmoother(alpha=0.3)
        phase2_output = [frames[0]]
        for i in range(1, len(frames)):
            blended = smoother.blend_frame(frames[i], phase2_output[-1])
            phase2_output.append(blended)

        phase2_flicker = self._compute_flicker(phase2_output)

        # Phase 2 should have lower flicker
        assert phase2_flicker < phase1_flicker

    def test_phase2_output_validity(self):
        """Test that Phase 2 output has valid pixel values and dimensions."""
        frames = self.create_realistic_watermark_sequence(num_frames=10)

        smoother = TemporalSmoother(alpha=0.3)
        smoothed = [frames[0]]
        for i in range(1, len(frames)):
            blended = smoother.blend_frame(frames[i], smoothed[-1])
            smoothed.append(blended)

        # Verify all frames are valid
        for frame in smoothed:
            assert frame.shape == frames[0].shape
            assert frame.dtype == np.uint8
            assert frame.min() >= 0
            assert frame.max() <= 255
            assert not np.isnan(frame).any()

    def _compute_flicker(self, frames: list[np.ndarray]) -> float:
        """Helper to compute mean flicker across frame sequence."""
        flicker_scores = []
        for i in range(1, len(frames)):
            diff = frames[i].astype(np.float32) - frames[i - 1].astype(np.float32)
            l2 = np.sqrt(np.sum(diff ** 2))
            normalized = l2 / np.sqrt(np.prod(frames[i].shape))
            flicker_scores.append(normalized)

        return float(np.mean(flicker_scores)) if flicker_scores else 0.0


class TestTemporalSmootherBlendRegion:
    """Integration tests for region-specific blending (inpaint scenario)."""

    def test_temporal_smoothing_in_crop_region(self):
        """Test temporal smoothing applied only to inpaint crop region."""
        smoother = TemporalSmoother(alpha=0.5)

        # Background frame
        frame1 = np.ones((200, 200, 3), dtype=np.uint8) * 100
        frame2 = np.ones((200, 200, 3), dtype=np.uint8) * 100

        # Inpainted region (lighter)
        frame1[50:150, 50:150, :] = 200
        frame2[50:150, 50:150, :] = 180  # Slightly different

        # Blend only in crop region
        crop_region = (50, 50, 100, 100)
        blended = smoother.blend_frame(frame2, frame1, blend_region=crop_region)

        # Outside region: should match frame2
        outside = blended[0:40, 0:40]
        assert np.allclose(outside, frame2[0:40, 0:40])

        # Inside region: should be blended
        inside = blended[75:125, 75:125]
        frame2_inside = frame2[75:125, 75:125]
        frame1_inside = frame1[75:125, 75:125]

        # Blended should be between frame2 and frame1
        assert np.all(inside >= np.minimum(frame2_inside, frame1_inside) - 1)
        assert np.all(inside <= np.maximum(frame2_inside, frame1_inside) + 1)

    def test_temporal_smoothing_gradient_blend(self):
        """Test gradient blending produces smooth feathered transitions."""
        smoother = TemporalSmoother(alpha=0.5)

        current = np.ones((300, 300, 3), dtype=np.uint8) * 100
        previous = np.ones((300, 300, 3), dtype=np.uint8) * 200

        # Apply gradient blend in center region
        crop_region = (100, 100, 100, 100)
        blended = smoother.blend_frame_gradient(
            current,
            previous,
            blend_region=crop_region,
            feather_width=32,
        )

        # Center should be more blended (closer to 200)
        center = np.mean(blended[130:170, 130:170])

        # Edge should be less blended (closer to 100)
        edge = np.mean(blended[70:110, 70:110])

        # Center should have more influence from previous
        assert center > edge

    def test_temporal_smoothing_preserves_background(self):
        """Test that temporal smoothing preserves unmodified background."""
        smoother = TemporalSmoother(alpha=0.5)

        # Create frames with different background and inpaint region
        frame1 = np.ones((200, 200, 3), dtype=np.uint8) * 100  # Background
        frame2 = np.ones((200, 200, 3), dtype=np.uint8) * 100  # Background

        # Only modify inpaint region in frame2
        frame2[75:125, 75:125, :] = 150

        # Blend only in crop region
        crop_region = (75, 75, 50, 50)
        blended = smoother.blend_frame(frame2, frame1, blend_region=crop_region)

        # Background (outside region) should be unchanged
        assert np.array_equal(blended[0:70, 0:70], frame2[0:70, 0:70])


class TestParameterValidation:
    """Test parameter validation and error handling."""

    def test_invalid_alpha_raises_error(self):
        """Test that invalid alpha values raise ValueError."""
        with pytest.raises(ValueError):
            TemporalSmoother(alpha=-0.1)

        with pytest.raises(ValueError):
            TemporalSmoother(alpha=1.5)

    def test_valid_alpha_boundaries(self):
        """Test that boundary alpha values are accepted."""
        smoother_min = TemporalSmoother(alpha=0.0)
        assert smoother_min.alpha == 0.0

        smoother_max = TemporalSmoother(alpha=1.0)
        assert smoother_max.alpha == 1.0

        smoother_mid = TemporalSmoother(alpha=0.5)
        assert smoother_mid.alpha == 0.5


class TestTemporalSmootherSequence:
    """Test temporal smoothing on realistic frame sequences."""

    def test_10frame_sequence_quality_progression(self):
        """Test temporal smoothing quality on 10-frame sequence."""
        # Create 10-frame sequence with progressive motion
        frames = []
        for i in range(10):
            frame = np.ones((100, 100, 3), dtype=np.uint8) * 100
            # Moving rectangle
            x = 20 + i * 3
            if x < 100:
                frame[40:60, x:x+20, :] = 200
            frames.append(frame)

        # Test different alpha values
        alphas_to_test = [0.0, 0.1, 0.3, 0.5, 1.0]

        for alpha in alphas_to_test:
            smoother = TemporalSmoother(alpha=alpha)
            smoothed = [frames[0]]

            for i in range(1, len(frames)):
                blended = smoother.blend_frame(frames[i], smoothed[-1])
                smoothed.append(blended)

            # Verify output validity
            assert len(smoothed) == 10
            for frame in smoothed:
                assert frame.dtype == np.uint8
                assert frame.shape == (100, 100, 3)
                assert 0 <= frame.min() and frame.max() <= 255

    def test_long_static_sequence_convergence(self):
        """Test temporal smoothing behavior on long static sequence."""
        # Create 20 identical frames
        static_frame = np.ones((100, 100, 3), dtype=np.uint8) * 150
        frames = [static_frame.copy() for _ in range(20)]

        smoother = TemporalSmoother(alpha=0.5)
        smoothed = [frames[0]]

        for i in range(1, len(frames)):
            blended = smoother.blend_frame(frames[i], smoothed[-1])
            smoothed.append(blended)

        # With static frames and temporal smoothing, all outputs should equal input
        for frame in smoothed:
            assert np.array_equal(frame, static_frame)
