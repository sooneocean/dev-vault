"""
Adaptive temporal smoothing with motion detection.

Adjusts smoothing strength based on per-frame motion estimation.
High motion → less smoothing (preserve detail), low motion → more smoothing (reduce noise).
"""

import logging
import numpy as np
from typing import Optional, List
from .temporal_smoother import TemporalSmoother

logger = logging.getLogger(__name__)


class AdaptiveTemporalSmoother:
    """
    Adaptive temporal smoothing based on motion detection.

    Automatically adjusts alpha blending strength per frame based on estimated motion.
    Preserves motion in high-activity regions while smoothing static areas.
    """

    def __init__(
        self,
        base_alpha: float = 0.3,
        motion_threshold: float = 0.05,
        min_alpha: float = 0.0,
        max_alpha: float = 0.8,
    ):
        """
        Initialize adaptive temporal smoother.

        Args:
            base_alpha: Base blending factor when motion is low (0.0-1.0)
            motion_threshold: Motion magnitude threshold for adaptation (0.0-1.0)
                             Above this, reduce smoothing; below, increase smoothing
            min_alpha: Minimum alpha during high motion (0.0-1.0)
            max_alpha: Maximum alpha during low motion (0.0-1.0)
        """
        if not 0.0 <= base_alpha <= 1.0:
            raise ValueError(f"base_alpha must be in [0.0, 1.0], got {base_alpha}")
        if not 0.0 <= motion_threshold <= 1.0:
            raise ValueError(f"motion_threshold must be in [0.0, 1.0], got {motion_threshold}")
        if not 0.0 <= min_alpha <= max_alpha <= 1.0:
            raise ValueError(f"min_alpha and max_alpha must be ordered and in [0.0, 1.0]")

        self.base_alpha = base_alpha
        self.motion_threshold = motion_threshold
        self.min_alpha = min_alpha
        self.max_alpha = max_alpha

        # Use standard temporal smoother for frame blending
        self.smoother = TemporalSmoother(alpha=base_alpha)

    def estimate_motion(
        self,
        frame1: np.ndarray,
        frame2: np.ndarray,
    ) -> float:
        """
        Estimate per-frame motion magnitude using optical flow approximation.

        Simple approach: normalized sum of absolute frame differences.
        Range: [0.0, 1.0], where 1.0 indicates maximum motion.

        Args:
            frame1: Previous frame (H, W, 3), uint8
            frame2: Current frame (H, W, 3), uint8

        Returns:
            Motion magnitude [0.0, 1.0]
        """
        if frame1.shape != frame2.shape:
            logger.warning("Frame shapes differ, using max motion estimate")
            return 1.0

        # Compute absolute difference
        diff = np.abs(frame1.astype(np.float32) - frame2.astype(np.float32))

        # Average across spatial and color dimensions
        motion = np.mean(diff) / 255.0  # Normalize to [0.0, 1.0]

        # Clamp to [0.0, 1.0]
        return float(np.clip(motion, 0.0, 1.0))

    def adapt_alpha(self, motion: float) -> float:
        """
        Adapt smoothing alpha based on motion magnitude.

        High motion (above threshold) → less smoothing (lower alpha)
        Low motion (below threshold) → more smoothing (higher alpha)

        Args:
            motion: Motion magnitude [0.0, 1.0]

        Returns:
            Adaptive alpha [min_alpha, max_alpha]
        """
        if motion >= self.motion_threshold:
            # High motion: reduce smoothing
            # Linear interpolation from base_alpha to min_alpha
            t = (motion - self.motion_threshold) / (1.0 - self.motion_threshold)
            alpha = self.base_alpha - t * (self.base_alpha - self.min_alpha)
        else:
            # Low motion: increase smoothing
            # Linear interpolation from base_alpha to max_alpha
            t = self.motion_threshold - motion
            alpha = self.base_alpha + (t / self.motion_threshold) * (self.max_alpha - self.base_alpha)

        return float(np.clip(alpha, self.min_alpha, self.max_alpha))

    def smooth_frame(
        self,
        current_frame: np.ndarray,
        previous_frame: Optional[np.ndarray] = None,
        motion: Optional[float] = None,
    ) -> np.ndarray:
        """
        Smooth current frame with adaptive alpha based on motion.

        Args:
            current_frame: Current frame (H, W, 3), uint8
            previous_frame: Previous frame (H, W, 3), uint8, optional
            motion: Optional pre-computed motion magnitude [0.0, 1.0]
                   If None, computed from frames

        Returns:
            Smoothed frame (H, W, 3), uint8
        """
        if previous_frame is None:
            return current_frame

        # Estimate motion if not provided
        if motion is None:
            motion = self.estimate_motion(previous_frame, current_frame)

        # Adapt alpha based on motion
        alpha = self.adapt_alpha(motion)

        # Apply temporal smoothing with adapted alpha
        self.smoother.alpha = alpha
        smoothed = self.smoother.smooth_frame(current_frame, previous_frame)

        logger.debug(f"Motion: {motion:.3f}, Alpha: {alpha:.3f}")
        return smoothed

    def smooth_sequence(
        self,
        frames: List[np.ndarray],
        motion_per_frame: Optional[List[float]] = None,
    ) -> tuple[List[np.ndarray], List[float]]:
        """
        Smooth entire frame sequence with adaptive alpha.

        Args:
            frames: List of frames (each H, W, 3), uint8
            motion_per_frame: Optional list of pre-computed motion values [0.0, 1.0]
                             If None, computed for each transition

        Returns:
            (List of smoothed frames, List of per-frame motion values)
        """
        if not frames:
            return frames, []

        smoothed = []
        motions = []
        previous_frame = None

        for i, frame in enumerate(frames):
            if i == 0:
                # First frame: no previous
                smoothed.append(frame)
                motions.append(0.0)
                previous_frame = frame
            else:
                # Compute or use provided motion
                if motion_per_frame is not None and i - 1 < len(motion_per_frame):
                    motion = motion_per_frame[i - 1]
                else:
                    motion = self.estimate_motion(previous_frame, frame)

                # Smooth with adaptive alpha
                smoothed_frame = self.smooth_frame(frame, previous_frame, motion)
                smoothed.append(smoothed_frame)
                motions.append(motion)
                previous_frame = smoothed_frame

        logger.info(
            f"Adaptive smoothed {len(frames)} frames: "
            f"avg motion={np.mean(motions[1:]):.3f}, "
            f"motion range=[{np.min(motions[1:]):.3f}, {np.max(motions[1:]):.3f}]"
        )

        return smoothed, motions
