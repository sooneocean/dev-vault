"""Serialization of CropRegion metadata and optical flow data for checkpoint resumption."""

import json
import logging
from pathlib import Path
from typing import Any, Dict

import numpy as np

from ..core.types import CropRegion, FlowData

logger = logging.getLogger(__name__)

# Checkpoint format version for compatibility tracking
CHECKPOINT_VERSION = "1.3"  # 1.3 adds annotation_tasks and tuning_metadata; backward compatible with 1.0


class CropRegionSerializer:
    """Save and load CropRegion metadata to JSON for resumption."""

    @staticmethod
    def serialize(
        crop_regions: Dict[int, CropRegion],
        flow_data_dict: Dict[str, Any] | None = None,
        annotation_tasks: Dict[int, Dict[str, Any]] | None = None,
        tuning_metadata: Dict[str, Any] | None = None,
    ) -> str:
        """Serialize crop regions, flow data, annotation tasks, and tuning metadata.

        Args:
            crop_regions: Dictionary mapping frame index to CropRegion.
            flow_data_dict: Optional dictionary of serialized flow data (Phase 3A).
            annotation_tasks: Optional dictionary of annotation task metadata (Phase 3B).
            tuning_metadata: Optional dictionary of tuning results (Phase 3B).

        Returns:
            JSON string representation (v1.3 format, backward compatible with v1.0).
        """
        if not crop_regions and not flow_data_dict and not annotation_tasks and not tuning_metadata:
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

        # Add Phase 3A data if provided
        if flow_data_dict:
            serialized["flow_data"] = flow_data_dict

        # Add Phase 3B data if provided
        if annotation_tasks:
            serialized["annotation_tasks"] = annotation_tasks
        if tuning_metadata:
            serialized["tuning_metadata"] = tuning_metadata

        return json.dumps(serialized, indent=2)

    @staticmethod
    def deserialize(json_str: str) -> tuple[Dict[int, CropRegion], Dict[str, Any] | None, Dict[int, Dict] | None, Dict[str, Any] | None]:
        """Deserialize checkpoint data from JSON string (v1.0/1.2/1.3).

        Args:
            json_str: JSON string representation of checkpoint data.

        Returns:
            Tuple of (crop_regions, flow_data, annotation_tasks, tuning_metadata).
            Any may be None if not present in checkpoint.

        Raises:
            json.JSONDecodeError: If JSON is invalid.
            ValueError: If crop data is malformed.
        """
        if not json_str.strip():
            return {}, None, None, None

        data = json.loads(json_str)
        if not data:
            return {}, None, None, None

        # Handle both old and new formats
        # v1.0 format: {"0": {...}, "1": {...}, ...}
        # v1.2 format: {"version": "1.2", "crop_regions": {...}, "flow_data": {...}}
        # v1.3 format: above + "annotation_tasks" and "tuning_metadata"
        if "version" in data:
            # Versioned format
            crop_data_dict = data.get("crop_regions", {})
            flow_data_dict = data.get("flow_data", None)
            annotation_tasks = data.get("annotation_tasks", None)
            tuning_metadata = data.get("tuning_metadata", None)
        else:
            # Old v1.0 format - treat data as crop_regions directly
            crop_data_dict = data
            flow_data_dict = None
            annotation_tasks = None
            tuning_metadata = None

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

        return crop_regions, flow_data_dict, annotation_tasks, tuning_metadata

    @staticmethod
    def save_checkpoint(
        crop_regions: Dict[int, CropRegion],
        output_dir: str,
        filename: str = "checkpoint_crops.json",
        flow_data_dict: Dict[str, Any] | None = None,
        annotation_tasks: Dict[int, Dict[str, Any]] | None = None,
        tuning_metadata: Dict[str, Any] | None = None,
    ) -> Path:
        """Save checkpoint with crop regions, flow data, annotations, and tuning (v1.3).

        Args:
            crop_regions: Dictionary mapping frame index to CropRegion.
            output_dir: Output directory for checkpoint file.
            filename: Checkpoint filename (default: checkpoint_crops.json).
            flow_data_dict: Optional dictionary of serialized flow data (Phase 3A).
            annotation_tasks: Optional dictionary of annotation task metadata (Phase 3B).
            tuning_metadata: Optional dictionary of tuning results (Phase 3B).

        Returns:
            Path to saved checkpoint file.

        Raises:
            IOError: If file write fails.
        """
        output_path = Path(output_dir) / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)

        json_str = CropRegionSerializer.serialize(
            crop_regions, flow_data_dict, annotation_tasks, tuning_metadata
        )

        with open(output_path, "w") as f:
            f.write(json_str)

        logger.info(
            f"Saved checkpoint v1.3: {output_path} ({len(crop_regions)} crop regions, "
            f"flow_data={'yes' if flow_data_dict else 'no'}, "
            f"annotations={'yes' if annotation_tasks else 'no'}, "
            f"tuning={'yes' if tuning_metadata else 'no'})"
        )
        return output_path

    @staticmethod
    def load_checkpoint(
        output_dir: str,
        filename: str = "checkpoint_crops.json",
    ) -> tuple[Dict[int, CropRegion], Dict[str, Any] | None, Dict[int, Dict] | None, Dict[str, Any] | None] | None:
        """Load checkpoint from file (v1.0/1.2/1.3 format, backward compatible).

        Args:
            output_dir: Output directory to check for checkpoint file.
            filename: Checkpoint filename (default: checkpoint_crops.json).

        Returns:
            Tuple of (crop_regions, flow_data, annotation_tasks, tuning_metadata), or None if checkpoint doesn't exist.

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

            crop_regions, flow_data, annotation_tasks, tuning_metadata = CropRegionSerializer.deserialize(json_str)
            logger.info(
                f"Loaded checkpoint v1.3: {checkpoint_path} ({len(crop_regions)} crop regions, "
                f"flow_data={'yes' if flow_data else 'no'}, "
                f"annotations={'yes' if annotation_tasks else 'no'}, "
                f"tuning={'yes' if tuning_metadata else 'no'})"
            )
            return crop_regions, flow_data, annotation_tasks, tuning_metadata

        except Exception as e:
            logger.error(f"Failed to load checkpoint {checkpoint_path}: {e}")
            raise
