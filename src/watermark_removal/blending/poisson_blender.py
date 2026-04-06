"""Poisson blending and color matching for seamless inpaint integration."""

import cv2
import numpy as np
from skimage import exposure


class PoissonBlender:
    """Apply Poisson blending for seamless region composition."""

    def __init__(self, method: str = "seamless_clone") -> None:
        """
        Initialize Poisson blender.

        Args:
            method: Blending method ("seamless_clone" for Poisson, "mixed_clone" for mixed).
        """
        if method not in ["seamless_clone", "mixed_clone"]:
            raise ValueError(f"Unknown blend method: {method}")
        self.method = method

    def blend(
        self,
        background: np.ndarray,
        inpainted: np.ndarray,
        region_bbox: tuple,
        mask: np.ndarray | None = None,
    ) -> np.ndarray:
        """
        Blend inpainted region into background using Poisson blending.

        Args:
            background: Background frame (HxWx3, uint8, BGR).
            inpainted: Inpainted crop (HxWx3, uint8, BGR).
            region_bbox: Bounding box (x, y, w, h) of inpainted region in background.
            mask: Optional blend mask (HxWx3, uint8 or float). If None, uses full inpainted.

        Returns:
            Blended frame (HxWx3, uint8).
        """
        x, y, w, h = region_bbox

        # Ensure inpainted matches region size
        x_end = min(x + w, background.shape[1])
        y_end = min(y + h, background.shape[0])
        actual_w = x_end - x
        actual_h = y_end - y

        if actual_w <= 0 or actual_h <= 0:
            return background.copy()

        # Resize inpainted to match region
        if inpainted.shape[0] != actual_h or inpainted.shape[1] != actual_w:
            inpainted_resized = cv2.resize(inpainted, (actual_w, actual_h))
        else:
            inpainted_resized = inpainted

        # Create blend mask if not provided
        if mask is None:
            mask = np.ones((actual_h, actual_w), dtype=np.uint8) * 255

        # Convert mask to single channel if needed
        if len(mask.shape) == 3:
            mask = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)

        # Resize mask to match region if needed
        if mask.shape != (actual_h, actual_w):
            mask = cv2.resize(mask, (actual_w, actual_h))

        # Convert background to the correct dtype and make a copy
        background_working = background.astype(np.uint8).copy()

        try:
            # Apply Poisson blending using OpenCV
            center = (x + actual_w // 2, y + actual_h // 2)

            if self.method == "seamless_clone":
                blended = cv2.seamlessClone(
                    inpainted_resized,
                    background_working,
                    mask,
                    center,
                    cv2.NORMAL_CLONE,
                )
            else:  # mixed_clone
                blended = cv2.seamlessClone(
                    inpainted_resized,
                    background_working,
                    mask,
                    center,
                    cv2.MIXED_CLONE,
                )

            return blended.astype(np.uint8)

        except cv2.error as e:
            # Fallback to simple paste if Poisson fails
            background_copy = background.copy()
            background_copy[y:y_end, x:x_end] = inpainted_resized
            return background_copy


class ColorMatcher:
    """Match color distributions between inpainted region and surroundings."""

    @staticmethod
    def match_histograms(
        source: np.ndarray,
        reference: np.ndarray,
        region_bbox: tuple | None = None,
    ) -> np.ndarray:
        """
        Match histogram of source to reference using color histogram matching.

        Args:
            source: Source image (HxWx3, uint8, BGR).
            reference: Reference image (HxWx3, uint8, BGR) to match histogram from.
            region_bbox: Optional (x, y, w, h) bounding box of source in reference
                        for better statistics.

        Returns:
            Color-matched source image (HxWx3, uint8).
        """
        if region_bbox is not None:
            x, y, w, h = region_bbox
            x_end = min(x + w, reference.shape[1])
            y_end = min(y + h, reference.shape[0])

            # Sample reference region near the source for better matching
            reference_region = reference[y:y_end, x:x_end]
        else:
            reference_region = reference

        # Match histograms per channel
        matched = source.copy().astype(np.float32)

        for c in range(3):  # BGR channels
            source_ch = source[:, :, c].astype(np.float32) / 255.0
            ref_ch = reference_region[:, :, c].astype(np.float32) / 255.0

            # Use scikit-image histogram matching
            try:
                matched_ch = exposure.match_histograms(source_ch, ref_ch, channel_axis=None)
                matched[:, :, c] = matched_ch * 255.0
            except Exception:
                # Fallback: keep original if matching fails
                matched[:, :, c] = source[:, :, c]

        return matched.astype(np.uint8)

    @staticmethod
    def match_boundary_colors(
        source: np.ndarray,
        background: np.ndarray,
        region_bbox: tuple,
        boundary_width: int = 10,
    ) -> np.ndarray:
        """
        Match colors at boundary between source and background.

        Args:
            source: Source image (HxWx3, uint8, BGR).
            background: Background image (HxWx3, uint8, BGR).
            region_bbox: Bounding box (x, y, w, h) of source in background.
            boundary_width: Width of boundary to sample for color matching.

        Returns:
            Color-corrected source image (HxWx3, uint8).
        """
        x, y, w, h = region_bbox

        # Extract boundary samples from background near region edges
        x_end = min(x + w, background.shape[1])
        y_end = min(y + h, background.shape[0])

        # Collect boundary samples and find best one
        boundary_candidates = []

        # Top boundary
        if y > boundary_width:
            boundary_candidates.append(
                background[max(0, y - boundary_width) : y, x:x_end]
            )

        # Bottom boundary
        if y_end + boundary_width <= background.shape[0]:
            boundary_candidates.append(
                background[y_end : min(y_end + boundary_width, background.shape[0]), x:x_end]
            )

        # Left boundary
        if x > boundary_width:
            boundary_candidates.append(
                background[y:y_end, max(0, x - boundary_width) : x]
            )

        # Right boundary
        if x_end + boundary_width <= background.shape[1]:
            boundary_candidates.append(
                background[y:y_end, x_end : min(x_end + boundary_width, background.shape[1])]
            )

        if not boundary_candidates:
            return source.copy()

        # Use largest boundary candidate for best statistics
        boundary = max(boundary_candidates, key=lambda b: b.size)

        # Match source histogram to boundary colors
        return ColorMatcher.match_histograms(source, boundary)
