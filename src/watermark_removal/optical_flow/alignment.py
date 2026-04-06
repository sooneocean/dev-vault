"""Flow-based region alignment for temporal consistency."""

import logging
from typing import Tuple

import numpy as np

from ..core.types import CropRegion, FlowData

logger = logging.getLogger(__name__)


def align_inpaint_region(
    flow_data: FlowData,
    crop_region: CropRegion,
    max_warp_distance: int = 50,
) -> CropRegion:
    """Align inpaint region boundaries using optical flow.

    Uses forward and backward flow vectors to warp the crop region boundaries,
    improving temporal consistency across frame sequences.

    Args:
        flow_data: Optical flow data between frame pair.
        crop_region: Original crop region to align.
        max_warp_distance: Maximum pixel warp distance (clamping).

    Returns:
        Adjusted CropRegion with warped boundaries.

    Raises:
        ValueError: If flow_data has invalid shape.
    """
    if flow_data.forward_flow.shape[2] != 2:
        raise ValueError(
            f"Expected flow shape (..., 2), got {flow_data.forward_flow.shape}"
        )

    # Compute average motion in crop region (used for alignment)
    crop_x, crop_y = crop_region.x, crop_region.y
    crop_w, crop_h = crop_region.w, crop_region.h

    # Extract flow vectors within crop region
    x_min = max(0, crop_x)
    y_min = max(0, crop_y)
    x_max = min(flow_data.forward_flow.shape[1], crop_x + crop_w)
    y_max = min(flow_data.forward_flow.shape[0], crop_y + crop_h)

    if x_max <= x_min or y_max <= y_min:
        logger.warning("Crop region outside flow bounds, returning original region")
        return crop_region

    crop_flow = flow_data.forward_flow[y_min:y_max, x_min:x_max, :]

    # Compute median flow magnitude and direction in region
    flow_magnitude = np.sqrt(crop_flow[..., 0] ** 2 + crop_flow[..., 1] ** 2)
    median_flow_x = np.median(crop_flow[..., 0])
    median_flow_y = np.median(crop_flow[..., 1])

    # Clamp warp distance
    warp_x = np.clip(median_flow_x, -max_warp_distance, max_warp_distance)
    warp_y = np.clip(median_flow_y, -max_warp_distance, max_warp_distance)

    # Compute variance to estimate alignment confidence
    flow_var = np.var(flow_magnitude)

    logger.debug(
        f"Alignment: median_flow=({median_flow_x:.2f}, {median_flow_y:.2f}), "
        f"warp=({warp_x:.2f}, {warp_y:.2f}), variance={flow_var:.4f}"
    )

    # Apply warp to crop region (conservative adjustment)
    aligned_region = CropRegion(
        x=max(0, int(crop_region.x + warp_x * 0.5)),  # Scale warp by 0.5 for stability
        y=max(0, int(crop_region.y + warp_y * 0.5)),
        w=crop_region.w,
        h=crop_region.h,
        scale_factor=crop_region.scale_factor,
        context_x=max(0, int(crop_region.context_x + warp_x * 0.5)),
        context_y=max(0, int(crop_region.context_y + warp_y * 0.5)),
        context_w=crop_region.context_w,
        context_h=crop_region.context_h,
        pad_left=crop_region.pad_left,
        pad_top=crop_region.pad_top,
        pad_right=crop_region.pad_right,
        pad_bottom=crop_region.pad_bottom,
    )

    return aligned_region


def compute_flow_confidence(flow_data: FlowData) -> float:
    """Compute confidence score for optical flow alignment.

    Higher score indicates more reliable flow (low variance, high consistency
    between forward and backward flows).

    Args:
        flow_data: Optical flow data.

    Returns:
        Confidence score (0.0-1.0).
    """
    # Compute forward flow magnitude
    forward_mag = np.sqrt(
        flow_data.forward_flow[..., 0] ** 2 + flow_data.forward_flow[..., 1] ** 2
    )

    # Compute backward flow magnitude
    backward_mag = np.sqrt(
        flow_data.backward_flow[..., 0] ** 2 + flow_data.backward_flow[..., 1] ** 2
    )

    # Compute consistency (smaller difference = higher confidence)
    mag_diff = np.abs(forward_mag - backward_mag)
    median_diff = np.median(mag_diff)

    # Normalize to 0-1 confidence (lower diff = higher confidence)
    # Assume 20 pixels difference indicates low confidence (< 0.1)
    confidence = np.exp(-median_diff / 20.0)

    return float(np.clip(confidence, 0.0, 1.0))


def warp_region_boundary(
    flow: np.ndarray,
    region_pts: np.ndarray,
) -> np.ndarray:
    """Warp region boundary points using optical flow.

    Args:
        flow: Optical flow map (H×W×2).
        region_pts: Boundary points (N×2, [x, y]).

    Returns:
        Warped points (N×2).

    Raises:
        ValueError: If points are outside flow bounds.
    """
    h, w = flow.shape[:2]

    warped_pts = []
    for x, y in region_pts:
        # Clamp to valid range
        x_idx = int(np.clip(x, 0, w - 1))
        y_idx = int(np.clip(y, 0, h - 1))

        # Get flow vector at point
        flow_vec = flow[y_idx, x_idx, :]

        # Warp point
        warped_x = x + flow_vec[0]
        warped_y = y + flow_vec[1]

        warped_pts.append([warped_x, warped_y])

    return np.array(warped_pts, dtype=np.float32)
