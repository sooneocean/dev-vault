"""Optical flow-based temporal alignment for watermark removal.

This module provides RAFT-based optical flow computation and flow-guided
region alignment for improving temporal consistency across video frames.
"""

from .alignment import align_inpaint_region, compute_flow_confidence, warp_region_boundary
from .flow_processor import OpticalFlowProcessor

__all__ = [
    "OpticalFlowProcessor",
    "align_inpaint_region",
    "compute_flow_confidence",
    "warp_region_boundary",
]
