"""Rescale inpainted crop and composite back to original frame with feather blending."""

import logging

import cv2
import numpy as np

from ..core.types import CropRegion, Frame

logger = logging.getLogger(__name__)


class StitchHandler:
    """Rescale inpainted crop back to original size and composite with feather blending."""

    def __init__(self, blend_feather_width: int = 32) -> None:
        """Initialize stitch handler with feather blending parameters.

        Args:
            blend_feather_width: Width (pixels) of feather blending at crop edges.
        """
        self.blend_feather_width = blend_feather_width

    def stitch_back(
        self,
        original_frame: np.ndarray,
        inpainted_crop: np.ndarray,
        crop_region: CropRegion,
    ) -> np.ndarray:
        """Rescale inpainted crop and composite onto original frame with feather blending.

        Args:
            original_frame: Original frame image (HxWx3, uint8, BGR).
            inpainted_crop: Inpainted crop (1024x1024x3, uint8, BGR).
            crop_region: CropRegion metadata with transformation info.

        Returns:
            Stitched frame (same shape as original_frame, uint8, BGR).

        Raises:
            ValueError: If input shapes are invalid.
        """
        # Validate input shapes
        if original_frame.ndim != 3 or original_frame.shape[2] != 3:
            raise ValueError(
                f"original_frame must be HxWx3, got {original_frame.shape}"
            )
        if inpainted_crop.ndim != 3 or inpainted_crop.shape[2] != 3:
            raise ValueError(
                f"inpainted_crop must be HxWx3, got {inpainted_crop.shape}"
            )

        # Step 1: Unpad inpainted crop
        unpadded_crop = self._unpad_crop(inpainted_crop, crop_region)
        logger.debug(f"Unpadded crop shape: {unpadded_crop.shape}")

        # Step 2: Rescale to original context size
        rescaled_crop = self._rescale_crop(unpadded_crop, crop_region)
        logger.debug(f"Rescaled crop shape: {rescaled_crop.shape}")

        # Step 3: Create feather mask
        feather_mask = self._create_feather_mask(
            rescaled_crop.shape[:2],
            self.blend_feather_width,
        )
        logger.debug(f"Feather mask shape: {feather_mask.shape}")

        # Step 4: Composite onto original frame
        stitched_frame = self._composite_with_feather(
            original_frame,
            rescaled_crop,
            crop_region,
            feather_mask,
        )
        logger.debug(f"Stitched frame shape: {stitched_frame.shape}")

        return stitched_frame

    def _unpad_crop(
        self,
        inpainted_crop: np.ndarray,
        crop_region: CropRegion,
    ) -> np.ndarray:
        """Remove padding from inpainted crop.

        Args:
            inpainted_crop: Padded crop (1024x1024x3).
            crop_region: CropRegion with padding values.

        Returns:
            Unpadded crop (context_w x context_h x 3).
        """
        # Crop region contains: pad_left, pad_top, pad_right, pad_bottom
        # Reverse the padding: remove pad_left and pad_right from width,
        # remove pad_top and pad_bottom from height
        h, w = inpainted_crop.shape[:2]

        y_start = crop_region.pad_top
        y_end = h - crop_region.pad_bottom
        x_start = crop_region.pad_left
        x_end = w - crop_region.pad_right

        unpadded = inpainted_crop[y_start:y_end, x_start:x_end]

        return unpadded

    def _rescale_crop(
        self,
        unpadded_crop: np.ndarray,
        crop_region: CropRegion,
    ) -> np.ndarray:
        """Rescale crop back to original context size.

        Args:
            unpadded_crop: Unpadded crop.
            crop_region: CropRegion with scale factor.

        Returns:
            Rescaled crop (context_h x context_w x 3).
        """
        # Reverse the scaling: divide by scale_factor
        target_h = crop_region.context_h
        target_w = crop_region.context_w

        rescaled = cv2.resize(
            unpadded_crop,
            (target_w, target_h),
            interpolation=cv2.INTER_LINEAR,
        )

        return rescaled

    def _create_feather_mask(
        self,
        shape: tuple,
        feather_width: int,
    ) -> np.ndarray:
        """Create feather mask with gradient fade at edges.

        Args:
            shape: (height, width) of mask to create.
            feather_width: Width of feather region (pixels).

        Returns:
            Feather mask (height x width, float32, values in [0, 1]).
        """
        h, w = shape
        mask = np.ones((h, w), dtype=np.float32)

        # Clamp feather width to not exceed half image size
        max_feather = min(feather_width, h // 2, w // 2)

        # Distance from edges
        for y in range(h):
            for x in range(w):
                # Distance to nearest edge
                dist_top = y
                dist_bottom = h - 1 - y
                dist_left = x
                dist_right = w - 1 - x

                min_dist = min(dist_top, dist_bottom, dist_left, dist_right)

                # Linear ramp from 0 to 1 over feather_width pixels
                if min_dist < max_feather:
                    mask[y, x] = min_dist / max_feather
                else:
                    mask[y, x] = 1.0

        return mask

    def _composite_with_feather(
        self,
        original_frame: np.ndarray,
        rescaled_crop: np.ndarray,
        crop_region: CropRegion,
        feather_mask: np.ndarray,
    ) -> np.ndarray:
        """Composite rescaled crop onto original frame using feather mask.

        Args:
            original_frame: Original frame (HxWx3, uint8).
            rescaled_crop: Rescaled crop (context_h x context_w x 3, uint8).
            crop_region: CropRegion with position info.
            feather_mask: Feather mask (context_h x context_w, float32, [0,1]).

        Returns:
            Stitched frame (HxWx3, uint8).
        """
        # Create output frame as copy of original
        stitched = original_frame.copy().astype(np.float32)

        # Get context region position
        context_x = crop_region.context_x
        context_y = crop_region.context_y
        context_h = crop_region.context_h
        context_w = crop_region.context_w

        # Clamp to frame boundaries (in case context was clipped)
        frame_h, frame_w = original_frame.shape[:2]

        # Calculate actual region to composite (may be clipped)
        y_start = max(0, context_y)
        y_end = min(frame_h, context_y + context_h)
        x_start = max(0, context_x)
        x_end = min(frame_w, context_x + context_w)

        # Corresponding region in rescaled crop
        crop_y_start = max(0, -context_y) if context_y < 0 else 0
        crop_x_start = max(0, -context_x) if context_x < 0 else 0
        crop_y_end = crop_y_start + (y_end - y_start)
        crop_x_end = crop_x_start + (x_end - x_start)

        # Extract regions
        original_region = stitched[y_start:y_end, x_start:x_end]
        inpainted_region = rescaled_crop[crop_y_start:crop_y_end, crop_x_start:crop_x_end].astype(np.float32)
        mask_region = feather_mask[crop_y_start:crop_y_end, crop_x_start:crop_x_end]

        # Expand mask to 3 channels
        mask_3ch = np.stack([mask_region] * 3, axis=2)

        # Blend: result = original * (1 - mask) + inpainted * mask
        blended = (
            original_region * (1.0 - mask_3ch) +
            inpainted_region * mask_3ch
        )

        # Clamp to [0, 255] and convert back to uint8
        blended = np.clip(blended, 0, 255).astype(np.uint8)

        # Place blended region back into output frame
        stitched[y_start:y_end, x_start:x_end] = blended

        return stitched.astype(np.uint8)
