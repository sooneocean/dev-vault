"""Temporal smoothing to reduce inter-frame flicker."""

import numpy as np
import cv2


class TemporalSmoother:
    """Apply alpha blending to adjacent frames for temporal coherence."""

    def __init__(self, alpha: float = 0.3) -> None:
        """
        Initialize temporal smoother.

        Args:
            alpha: Blending factor (0.0 = no blending, 1.0 = full previous frame).
                   Recommended: 0.2-0.4 for subtle smoothing.

        Raises:
            ValueError: If alpha not in [0.0, 1.0].
        """
        if not 0.0 <= alpha <= 1.0:
            raise ValueError(f"alpha must be in [0.0, 1.0], got {alpha}")
        self.alpha = alpha

    def blend_frame(
        self,
        current_frame: np.ndarray,
        previous_frame: np.ndarray | None = None,
        blend_region: tuple | None = None,
    ) -> np.ndarray:
        """
        Blend current frame with previous frame using alpha blending.

        Blending: output = (1 - alpha) * current + alpha * previous

        Args:
            current_frame: Current frame (HxWx3, uint8)
            previous_frame: Previous frame (HxWx3, uint8) or None for first frame.
            blend_region: Optional (x, y, w, h) bounding box to blend only in that region.
                         If None, blends entire frame.

        Returns:
            Blended frame (HxWx3, uint8). If no previous frame or alpha=0, returns current unchanged.
        """
        # First frame: no blending
        if previous_frame is None or self.alpha == 0.0:
            return current_frame.copy()

        # Full-frame blending
        if blend_region is None:
            current_float = current_frame.astype(np.float32)
            previous_float = previous_frame.astype(np.float32)
            blended = (1.0 - self.alpha) * current_float + self.alpha * previous_float
            return blended.astype(np.uint8)

        # Region-specific blending
        blended = current_frame.astype(np.float32).copy()

        x, y, w, h = blend_region
        x_end = min(x + w, current_frame.shape[1])
        y_end = min(y + h, current_frame.shape[0])
        actual_w = x_end - x
        actual_h = y_end - y

        if actual_w <= 0 or actual_h <= 0:
            return current_frame.copy()

        # Blend only in region
        current_region = current_frame[y:y_end, x:x_end, :].astype(np.float32)
        previous_region = previous_frame[y:y_end, x:x_end, :].astype(np.float32)

        blended_region = (1.0 - self.alpha) * current_region + self.alpha * previous_region
        blended[y:y_end, x:x_end, :] = blended_region

        return blended.astype(np.uint8)

    def blend_frame_gradient(
        self,
        current_frame: np.ndarray,
        previous_frame: np.ndarray | None = None,
        blend_region: tuple | None = None,
        feather_width: int = 32,
    ) -> np.ndarray:
        """
        Blend with gradient mask at region edges for smoother transitions.

        Useful for blending only at crop region boundaries, avoiding blending
        the entire inpainted region.

        Args:
            current_frame: Current frame (HxWx3, uint8)
            previous_frame: Previous frame (HxWx3, uint8) or None for first frame.
            blend_region: (x, y, w, h) bounding box for the region to feather.
            feather_width: Width of gradient feathering (pixels).

        Returns:
            Blended frame (HxWx3, uint8).
        """
        if previous_frame is None or self.alpha == 0.0 or blend_region is None:
            return self.blend_frame(current_frame, previous_frame, None)

        # Create distance-based feather mask
        x, y, w, h = blend_region
        height, width = current_frame.shape[:2]

        # Binary mask of region
        binary_mask = np.zeros((height, width), dtype=np.uint8)
        x_end = min(x + w, width)
        y_end = min(y + h, height)
        binary_mask[y:y_end, x:x_end] = 255

        # Distance transform from boundary
        inverse_mask = 255 - binary_mask
        distance = cv2.distanceTransform(inverse_mask, cv2.DIST_L2, cv2.DIST_MASK_PRECISE)

        # Normalize distance to feather width [0, 1]
        # 0 at boundaries, 1+ deep inside region
        feather_mask = np.clip(distance / feather_width, 0, 1)

        # Ensure region interior stays 1.0 (max blend strength at center)
        feather_mask = np.maximum(feather_mask, binary_mask.astype(np.float32) / 255.0)

        # Use distance-based mask as blend strength
        blend_strength = feather_mask.astype(np.float32)

        # Apply gradient blending
        current_float = current_frame.astype(np.float32)
        previous_float = previous_frame.astype(np.float32)

        blended = np.zeros_like(current_float)
        for c in range(3):  # Per-channel
            # Blend with spatially-varying alpha
            blended[:, :, c] = (
                current_float[:, :, c] * (1.0 - self.alpha * blend_strength)
                + previous_float[:, :, c] * (self.alpha * blend_strength)
            )

        return blended.astype(np.uint8)
