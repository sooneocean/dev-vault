"""Edge blending and feather mask refinement for smooth transitions."""

import cv2
import numpy as np


class EdgeBlender:
    """Apply advanced edge blending to smooth feather transitions."""

    def __init__(self, feather_width: int = 32, blur_kernel_size: int = 5) -> None:
        """
        Initialize edge blender.

        Args:
            feather_width: Width of feather region (pixels)
            blur_kernel_size: Kernel size for Gaussian blur (must be odd)
        """
        self.feather_width = feather_width
        # Ensure kernel size is odd
        self.blur_kernel_size = blur_kernel_size if blur_kernel_size % 2 == 1 else blur_kernel_size + 1

    def create_feather_mask(self, shape: tuple, region_bbox: tuple, blur: bool = True) -> np.ndarray:
        """
        Create a feathered mask using distance transform and optional Gaussian blur.

        Args:
            shape: Shape of output mask (height, width)
            region_bbox: Bounding box (x, y, w, h) of the region to feather
            blur: Whether to apply Gaussian blur for smoother transitions

        Returns:
            Feather mask (float32) with values in [0, 1]
        """
        height, width = shape
        x, y, w, h = region_bbox

        # Create binary mask of the region
        binary_mask = np.zeros((height, width), dtype=np.uint8)
        x_end = min(x + w, width)
        y_end = min(y + h, height)
        binary_mask[y:y_end, x:x_end] = 255

        # Apply Gaussian blur to binary mask for smoother feathering
        if blur:
            blurred = cv2.GaussianBlur(binary_mask, (self.blur_kernel_size, self.blur_kernel_size), 0)
        else:
            blurred = binary_mask

        # Convert to float and normalize to [0, 1]
        feather_mask = blurred.astype(np.float32) / 255.0

        return feather_mask

    def create_distance_feather_mask(
        self, shape: tuple, region_bbox: tuple, blur: bool = True
    ) -> np.ndarray:
        """
        Create feather mask using distance transform for gradient fade.

        Distance-based feathering creates a smooth gradient from the region boundary
        outward, with the gradient width controlled by feather_width.

        Args:
            shape: Shape of output mask (height, width)
            region_bbox: Bounding box (x, y, w, h) of the region to feather
            blur: Whether to apply additional Gaussian blur

        Returns:
            Feather mask (float32) with values in [0, 1]
        """
        height, width = shape
        x, y, w, h = region_bbox

        # Create binary mask of the region
        binary_mask = np.zeros((height, width), dtype=np.uint8)
        x_end = min(x + w, width)
        y_end = min(y + h, height)
        binary_mask[y:y_end, x:x_end] = 255

        # Create inverse mask (outside region)
        inverse_mask = 255 - binary_mask

        # Compute distance transform from boundaries
        # distanceTransform gives distance from each pixel to nearest non-zero pixel
        distance = cv2.distanceTransform(inverse_mask, cv2.DIST_L2, cv2.DIST_MASK_PRECISE)

        # Normalize distance to feather width
        # Pixels within feather_width distance get gradient, others get 0
        feather_mask = np.clip(distance / self.feather_width, 0, 1)

        # Invert so inner region is 1.0 and boundary fades to 0.0
        feather_mask = 1.0 - feather_mask

        # Add binary mask (inner region is always 1.0)
        feather_mask = np.maximum(feather_mask, binary_mask.astype(np.float32) / 255.0)

        # Apply additional Gaussian blur for smoother transition
        if blur:
            feather_mask_uint8 = (feather_mask * 255).astype(np.uint8)
            blurred = cv2.GaussianBlur(feather_mask_uint8, (self.blur_kernel_size, self.blur_kernel_size), 0)
            feather_mask = blurred.astype(np.float32) / 255.0

        return feather_mask

    def blend_edges(
        self,
        original: np.ndarray,
        inpainted: np.ndarray,
        region_bbox: tuple,
        blend_mask: np.ndarray | None = None,
    ) -> np.ndarray:
        """
        Blend inpainted region into original frame using feather mask.

        Args:
            original: Original frame (HxWx3, uint8)
            inpainted: Inpainted crop (HxWx3, uint8)
            region_bbox: Bounding box (x, y, w, h) of the region
            blend_mask: Optional pre-computed blend mask; if None, creates one

        Returns:
            Blended frame (HxWx3, uint8)
        """
        if blend_mask is None:
            blend_mask = self.create_distance_feather_mask(original.shape[:2], region_bbox, blur=True)

        # Ensure inpainted region dimensions match
        x, y, w, h = region_bbox
        x_end = min(x + w, original.shape[1])
        y_end = min(y + h, original.shape[0])
        actual_w = x_end - x
        actual_h = y_end - y

        # Resize inpainted crop to match actual region size if needed
        if inpainted.shape[0] != actual_h or inpainted.shape[1] != actual_w:
            inpainted_resized = cv2.resize(inpainted, (actual_w, actual_h))
        else:
            inpainted_resized = inpainted

        # Create output frame copy
        blended = original.astype(np.float32).copy()

        # Extract blend mask for this region
        region_mask = blend_mask[y:y_end, x:x_end]

        # Ensure region mask matches inpainted dimensions
        if region_mask.shape != (actual_h, actual_w):
            region_mask = cv2.resize(region_mask, (actual_w, actual_h))

        # Blend: output = original * (1 - mask) + inpainted * mask
        # This creates smooth transition from original to inpainted
        inpainted_float = inpainted_resized.astype(np.float32)
        for c in range(3):  # For each color channel
            blended[y:y_end, x:x_end, c] = (
                original[y:y_end, x:x_end, c].astype(np.float32) * (1 - region_mask)
                + inpainted_float[:, :, c] * region_mask
            )

        return blended.astype(np.uint8)
