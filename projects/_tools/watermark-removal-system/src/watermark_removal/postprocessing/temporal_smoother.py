"""
Temporal smoothing to reduce inter-frame flicker.

Applies alpha blending between adjacent stitched frames to create smoother transitions
and reduce visual artifacts from per-frame inpainting.
"""

import logging
import numpy as np
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class TemporalSmoother:
    """
    Applies temporal smoothing via alpha blending between adjacent frames.

    Reduces flicker artifacts in video by blending each frame with its neighbors.
    """

    def __init__(self, alpha: float = 0.3):
        """
        Initialize temporal smoother.

        Args:
            alpha: Blending factor (0.0 = no smoothing, 1.0 = full blend with previous)
                   Typical range: 0.1-0.5
        """
        if not 0.0 <= alpha <= 1.0:
            raise ValueError(f"alpha must be in [0.0, 1.0], got {alpha}")

        self.alpha = alpha

    def smooth_frame(
        self,
        current_frame: np.ndarray,
        previous_frame: Optional[np.ndarray] = None,
    ) -> np.ndarray:
        """
        Smooth current frame by blending with previous frame.

        Args:
            current_frame: Current frame (H, W, 3), uint8
            previous_frame: Previous frame (H, W, 3), uint8, optional

        Returns:
            Smoothed frame (H, W, 3), uint8
        """
        if previous_frame is None or self.alpha == 0.0:
            return current_frame

        if previous_frame.shape != current_frame.shape:
            logger.warning(
                f"Frame shape mismatch: prev {previous_frame.shape} vs current {current_frame.shape}"
            )
            return current_frame

        # Alpha blend: result = (1 - alpha) * current + alpha * previous
        # This gives more weight to current frame, with slight blend from previous
        blended = (
            (1.0 - self.alpha) * current_frame.astype(np.float32)
            + self.alpha * previous_frame.astype(np.float32)
        )

        # Clamp to uint8 range
        return np.clip(blended, 0, 255).astype(np.uint8)

    def smooth_sequence(
        self,
        frames: list[np.ndarray],
    ) -> list[np.ndarray]:
        """
        Smooth entire frame sequence.

        Args:
            frames: List of frames (each H, W, 3), uint8

        Returns:
            List of smoothed frames
        """
        if not frames:
            return frames

        if self.alpha == 0.0:
            return frames

        smoothed = []
        for i, frame in enumerate(frames):
            if i == 0:
                # First frame: no previous, return as-is
                smoothed.append(frame)
            else:
                # Blend with previous smoothed frame
                prev = smoothed[-1]
                smoothed_frame = self.smooth_frame(frame, prev)
                smoothed.append(smoothed_frame)

        logger.info(f"Smoothed {len(frames)} frames with alpha={self.alpha}")
        return smoothed

    def smooth_bidirectional(
        self,
        frames: list[np.ndarray],
    ) -> list[np.ndarray]:
        """
        Bidirectional temporal smoothing: forward + backward pass.

        More sophisticated: smooth forward, then backward, for better coherence.

        Args:
            frames: List of frames

        Returns:
            List of bidirectionally smoothed frames
        """
        if not frames or self.alpha == 0.0:
            return frames

        # Forward pass
        forward = self.smooth_sequence(frames)

        # Backward pass: reverse, smooth, reverse back
        backward = self.smooth_sequence(forward[::-1])[::-1]

        # Average forward and backward results
        result = []
        for f, b in zip(forward, backward):
            averaged = (
                0.5 * f.astype(np.float32) + 0.5 * b.astype(np.float32)
            )
            result.append(np.clip(averaged, 0, 255).astype(np.uint8))

        logger.info(f"Bidirectionally smoothed {len(frames)} frames")
        return result


class AdaptiveTemporalSmoother(TemporalSmoother):
    """
    Adaptive temporal smoothing: varies alpha based on frame similarity.

    Applies stronger smoothing where frames are similar (low motion),
    weaker smoothing where frames differ significantly (high motion).
    """

    def smooth_frame_adaptive(
        self,
        current_frame: np.ndarray,
        previous_frame: Optional[np.ndarray] = None,
        motion_threshold: float = 0.05,
    ) -> tuple[np.ndarray, float]:
        """
        Smooth frame with adaptive alpha based on motion detection.

        Args:
            current_frame: Current frame
            previous_frame: Previous frame, optional
            motion_threshold: If frame difference > this, reduce alpha (lower smoothing)

        Returns:
            (smoothed_frame, used_alpha) tuple
        """
        if previous_frame is None or self.alpha == 0.0:
            return current_frame, 0.0

        # Compute frame difference (L2 norm of normalized difference)
        diff = np.abs(current_frame.astype(np.float32) - previous_frame.astype(np.float32))
        normalized_diff = np.mean(diff) / 255.0

        # Adaptive alpha: reduce smoothing if motion detected
        if normalized_diff > motion_threshold:
            # High motion: use lower alpha (less smoothing)
            adaptive_alpha = self.alpha * 0.3
        else:
            # Low motion: use full alpha
            adaptive_alpha = self.alpha

        # Apply blend
        blended = (
            (1.0 - adaptive_alpha) * current_frame.astype(np.float32)
            + adaptive_alpha * previous_frame.astype(np.float32)
        )

        result = np.clip(blended, 0, 255).astype(np.uint8)
        return result, adaptive_alpha
