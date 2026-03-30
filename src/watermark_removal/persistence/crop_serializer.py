"""Serialization of CropRegion metadata and optical flow data for checkpoint resumption."""

import json
import logging
from pathlib import Path
from typing import Any, Dict

import numpy as np

from ..core.types import CropRegion, FlowData

logger = logging.getLogger(__name__)

# Checkpoint format version for compatibility tracking
CHECKPOINT_VERSION = "1.2"  # 1.2 adds flow_data support


class CropRegionSerializer:
    """Save and load CropRegion metadata to JSON for resumption."""

    @staticmethod
    def serialize(
        crop_regions: Dict[int, CropRegion],
        flow_data_dict: Dict[str, Any] | None = None,
    ) -> str:
        """Serialize crop regions and flow data to JSON string.

        Args:
            crop_regions: Dictionary mapping frame index to CropRegion.
            flow_data_dict: Optional dictionary of serialized flow data.

        Returns:
            JSON string representation of crop regions and flow data.
        """
        if not crop_regions and not flow_data_dict:
            return json.dumps({"version": CHECKPOINT_VERSION})

        # Convert each CropRegion to dict
        serialized = {
            "version": CHECKPOINT_VERSION,
            "crop_regions": {},
        }

        for frame_idx, crop in crop_regions.items():
            serialized["crop_regions"][str(frame_idx)] = {
                "x": crop.x,
                "y": crop.y,
                "w": crop.w,
                "h": crop.h,
                "scale_factor": crop.scale_factor,
                "context_x": crop.context_x,
                "context_y": crop.context_y,
                "context_w": crop.context_w,
                "context_h": crop.context_h,
                "pad_left": crop.pad_left,
                "pad_top": crop.pad_top,
                "pad_right": crop.pad_right,
                "pad_bottom": crop.pad_bottom,
            }

        # Add flow data if provided
        if flow_data_dict:
            serialized["flow_data"] = flow_data_dict

        return json.dumps(serialized, indent=2)

    @staticmethod
    def deserialize(json_str: str) -> tuple[Dict[int, CropRegion], Dict[str, Any] | None]:
        """Deserialize crop regions and flow data from JSON string.

        Args:
            json_str: JSON string representation of crop regions and flow data.

        Returns:
            Tuple of (crop_regions dict, flow_data dict or None).

        Raises:
            json.JSONDecodeError: If JSON is invalid.
            ValueError: If crop data is malformed.
        """
        if not json_str.strip():
            return {}, None

        data = json.loads(json_str)
        if not data:
            return {}, None

        # Handle both old and new formats
        # Old format: {"0": {...}, "1": {...}, ...}
        # New format: {"version": "1.2", "crop_regions": {...}, "flow_data": {...}}
        if "version" in data:
            # New format
            crop_data_dict = data.get("crop_regions", {})
            flow_data_dict = data.get("flow_data", None)
        else:
            # Old format - treat data as crop_regions directly
            crop_data_dict = data
            flow_data_dict = None

        crop_regions = {}
        for frame_idx_str, crop_data in crop_data_dict.items():
            try:
                frame_idx = int(frame_idx_str)

                crop = CropRegion(
                    x=int(crop_data["x"]),
                    y=int(crop_data["y"]),
                    w=int(crop_data["w"]),
                    h=int(crop_data["h"]),
                    scale_factor=float(crop_data["scale_factor"]),
                    context_x=int(crop_data["context_x"]),
                    context_y=int(crop_data["context_y"]),
                    context_w=int(crop_data["context_w"]),
                    context_h=int(crop_data["context_h"]),
                    pad_left=int(crop_data.get("pad_left", 0)),
                    pad_top=int(crop_data.get("pad_top", 0)),
                    pad_right=int(crop_data.get("pad_right", 0)),
                    pad_bottom=int(crop_data.get("pad_bottom", 0)),
                )

                crop_regions[frame_idx] = crop

            except (KeyError, ValueError, TypeError) as e:
                raise ValueError(
                    f"Malformed crop data for frame {frame_idx_str}: {e}"
                ) from e

        return crop_regions, flow_data_dict

    @staticmethod
    def save_checkpoint(
        crop_regions: Dict[int, CropRegion],
        output_dir: str,
        filename: str = "checkpoint_crops.json",
        flow_data_dict: Dict[str, Any] | None = None,
    ) -> Path:
        """Save crop regions and flow data to checkpoint file.

        Args:
            crop_regions: Dictionary mapping frame index to CropRegion.
            output_dir: Output directory for checkpoint file.
            filename: Checkpoint filename (default: checkpoint_crops.json).
            flow_data_dict: Optional dictionary of serialized flow data.

        Returns:
            Path to saved checkpoint file.

        Raises:
            IOError: If file write fails.
        """
        output_path = Path(output_dir) / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)

        json_str = CropRegionSerializer.serialize(crop_regions, flow_data_dict)

        with open(output_path, "w") as f:
            f.write(json_str)

        logger.info(
            f"Saved crop checkpoint: {output_path} ({len(crop_regions)} regions, "
            f"flow_data={'yes' if flow_data_dict else 'no'})"
        )
        return output_path

    @staticmethod
    def load_checkpoint(
        output_dir: str,
        filename: str = "checkpoint_crops.json",
    ) -> tuple[Dict[int, CropRegion], Dict[str, Any] | None] | None:
        """Load crop regions and flow data from checkpoint file if it exists.

        Args:
            output_dir: Output directory to check for checkpoint file.
            filename: Checkpoint filename (default: checkpoint_crops.json).

        Returns:
            Tuple of (crop_regions, flow_data_dict), or None if checkpoint doesn't exist.

        Raises:
            ValueError: If checkpoint JSON is malformed.
        """
        checkpoint_path = Path(output_dir) / filename

        if not checkpoint_path.exists():
            logger.info(f"No checkpoint found at {checkpoint_path}")
            return None

        try:
            with open(checkpoint_path, "r") as f:
                json_str = f.read()

            crop_regions, flow_data = CropRegionSerializer.deserialize(json_str)
            logger.info(
                f"Loaded crop checkpoint: {checkpoint_path} ({len(crop_regions)} regions, "
                f"flow_data={'yes' if flow_data else 'no'})"
            )
            return crop_regions, flow_data

        except Exception as e:
            logger.error(f"Failed to load checkpoint {checkpoint_path}: {e}")
            raise
