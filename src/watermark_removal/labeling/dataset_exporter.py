"""
Dataset exporters for Label Studio annotations.

Converts Label Studio annotations to training-ready formats:
- COCO JSON (for object detection frameworks)
- YOLO TXT (for YOLOv5/v8 training)

Handles coordinate system conversions with precision validation.
"""

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any, Tuple

logger = logging.getLogger(__name__)


@dataclass
class BBoxPixel:
    """BBox in pixel coordinates (from ensemble detector)."""
    x: int  # Pixel x (left)
    y: int  # Pixel y (top)
    w: int  # Width in pixels
    h: int  # Height in pixels


@dataclass
class BBoxPercentage:
    """BBox in percentage coordinates (0-100) for Label Studio."""
    x: float  # Percentage (0-100)
    y: float  # Percentage (0-100)
    w: float  # Width in percentage
    h: float  # Height in percentage


class CoordinateConverter:
    """Convert bbox coordinates between pixel and percentage."""

    # Precision tolerance: ±1 pixel at 480p, ±2 pixels at 1080p
    PIXEL_TOLERANCE_480P = 1
    PIXEL_TOLERANCE_1080P = 2

    @staticmethod
    def pixel_to_percentage(
        bbox: BBoxPixel,
        frame_width: int,
        frame_height: int,
    ) -> BBoxPercentage:
        """
        Convert pixel coordinates to percentage (0-100).

        Args:
            bbox: BBox in pixel coordinates
            frame_width: Frame width in pixels
            frame_height: Frame height in pixels

        Returns:
            BBox in percentage coordinates

        Raises:
            ValueError: If frame dimensions invalid
        """
        if frame_width <= 0 or frame_height <= 0:
            raise ValueError(f"Invalid frame dimensions: {frame_width}x{frame_height}")

        x_pct = (bbox.x / frame_width) * 100.0
        y_pct = (bbox.y / frame_height) * 100.0
        w_pct = (bbox.w / frame_width) * 100.0
        h_pct = (bbox.h / frame_height) * 100.0

        # Clamp to valid range
        x_pct = max(0.0, min(100.0, x_pct))
        y_pct = max(0.0, min(100.0, y_pct))
        w_pct = max(0.0, min(100.0 - x_pct, w_pct))
        h_pct = max(0.0, min(100.0 - y_pct, h_pct))

        return BBoxPercentage(x=x_pct, y=y_pct, w=w_pct, h=h_pct)

    @staticmethod
    def percentage_to_pixel(
        bbox: BBoxPercentage,
        frame_width: int,
        frame_height: int,
    ) -> BBoxPixel:
        """
        Convert percentage coordinates back to pixels.

        Args:
            bbox: BBox in percentage coordinates
            frame_width: Frame width in pixels
            frame_height: Frame height in pixels

        Returns:
            BBox in pixel coordinates

        Raises:
            ValueError: If frame dimensions invalid
        """
        if frame_width <= 0 or frame_height <= 0:
            raise ValueError(f"Invalid frame dimensions: {frame_width}x{frame_height}")

        x_px = int((bbox.x / 100.0) * frame_width)
        y_px = int((bbox.y / 100.0) * frame_height)
        w_px = int((bbox.w / 100.0) * frame_width)
        h_px = int((bbox.h / 100.0) * frame_height)

        # Ensure positive dimensions
        w_px = max(1, w_px)
        h_px = max(1, h_px)

        return BBoxPixel(x=x_px, y=y_px, w=w_px, h=h_px)

    @staticmethod
    def validate_roundtrip_precision(
        original_pixel: BBoxPixel,
        frame_width: int,
        frame_height: int,
    ) -> Tuple[bool, str]:
        """
        Validate coordinate conversion roundtrip precision.

        Args:
            original_pixel: Original pixel BBox
            frame_width: Frame width in pixels
            frame_height: Frame height in pixels

        Returns:
            (is_valid, error_message)
        """
        # Convert to percentage
        pct = CoordinateConverter.pixel_to_percentage(
            original_pixel, frame_width, frame_height
        )

        # Convert back to pixel
        reconstructed = CoordinateConverter.percentage_to_pixel(
            pct, frame_width, frame_height
        )

        # Determine tolerance based on resolution
        if frame_height <= 480:
            tolerance = CoordinateConverter.PIXEL_TOLERANCE_480P
        else:
            tolerance = CoordinateConverter.PIXEL_TOLERANCE_1080P

        # Check tolerance
        errors = []
        if abs(reconstructed.x - original_pixel.x) > tolerance:
            errors.append(f"x error: {abs(reconstructed.x - original_pixel.x)}")
        if abs(reconstructed.y - original_pixel.y) > tolerance:
            errors.append(f"y error: {abs(reconstructed.y - original_pixel.y)}")
        if abs(reconstructed.w - original_pixel.w) > tolerance:
            errors.append(f"w error: {abs(reconstructed.w - original_pixel.w)}")
        if abs(reconstructed.h - original_pixel.h) > tolerance:
            errors.append(f"h error: {abs(reconstructed.h - original_pixel.h)}")

        if errors:
            return False, "; ".join(errors)

        return True, ""


class CocoExporter:
    """Export Label Studio annotations to COCO JSON format."""

    @staticmethod
    def export(
        tasks: List[Dict[str, Any]],
        output_path: str,
        frame_width: int = 640,
        frame_height: int = 480,
    ) -> bool:
        """
        Export tasks to COCO format.

        Args:
            tasks: List of Label Studio task dicts
            output_path: Path to write COCO JSON
            frame_width: Expected frame width (for validation)
            frame_height: Expected frame height (for validation)

        Returns:
            True if successful
        """
        logger.info(f"Exporting {len(tasks)} tasks to COCO format")

        coco_data = {
            "info": {
                "description": "Watermark removal annotations",
                "version": "1.0",
            },
            "images": [],
            "annotations": [],
            "categories": [
                {"id": 1, "name": "watermark"},
                {"id": 2, "name": "logo"},
                {"id": 3, "name": "text"},
                {"id": 4, "name": "subtitle"},
                {"id": 5, "name": "other"},
            ],
        }

        annotation_id = 0

        for image_id, task in enumerate(tasks, start=1):
            frame_id = task.get("frame_id")

            # Add image entry
            coco_data["images"].append({
                "id": image_id,
                "file_name": f"frame_{frame_id}.jpg",
                "width": frame_width,
                "height": frame_height,
            })

            # Add annotations
            annotations = task.get("annotations", [])
            for ann in annotations:
                annotation_id += 1

                # Get label (default to watermark)
                label_name = ann.get("label", "watermark")
                category_id = {
                    "watermark": 1,
                    "logo": 2,
                    "text": 3,
                    "subtitle": 4,
                    "other": 5,
                }.get(label_name, 1)

                # BBox in COCO format: [x, y, width, height]
                # (percentage from Label Studio needs to be converted)
                x = ann["x"]  # Already in percentage
                y = ann["y"]
                w = ann["w"]
                h = ann["h"]

                coco_data["annotations"].append({
                    "id": annotation_id,
                    "image_id": image_id,
                    "category_id": category_id,
                    "bbox": [x, y, w, h],
                    "area": w * h,
                    "iscrowd": 0,
                })

        # Write to file
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(coco_data, f, indent=2)

        logger.info(
            f"COCO export complete: {len(coco_data['images'])} images, "
            f"{len(coco_data['annotations'])} annotations"
        )
        return True


class YoloExporter:
    """Export Label Studio annotations to YOLO format."""

    @staticmethod
    def export(
        tasks: List[Dict[str, Any]],
        output_dir: str,
        frame_width: int = 640,
        frame_height: int = 480,
    ) -> bool:
        """
        Export tasks to YOLO format.

        Args:
            tasks: List of Label Studio task dicts
            output_dir: Directory to write YOLO label files
            frame_width: Expected frame width
            frame_height: Expected frame height

        Returns:
            True if successful
        """
        logger.info(f"Exporting {len(tasks)} tasks to YOLO format")

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        label_map = {
            "watermark": 0,
            "logo": 1,
            "text": 2,
            "subtitle": 3,
            "other": 4,
        }

        for task in tasks:
            frame_id = task.get("frame_id")
            label_file = output_dir / f"frame_{frame_id}.txt"

            annotations = task.get("annotations", [])
            lines = []

            for ann in annotations:
                label_name = ann.get("label", "watermark")
                class_id = label_map.get(label_name, 0)

                # Convert percentage to normalized YOLO coordinates
                # YOLO: <class_id> <x_center> <y_center> <width> <height>
                # (all normalized 0-1, relative to image width/height)
                x_center = (ann["x"] + ann["w"] / 2.0) / 100.0
                y_center = (ann["y"] + ann["h"] / 2.0) / 100.0
                width = ann["w"] / 100.0
                height = ann["h"] / 100.0

                # Clamp to valid range
                x_center = max(0.0, min(1.0, x_center))
                y_center = max(0.0, min(1.0, y_center))
                width = max(0.0, min(1.0, width))
                height = max(0.0, min(1.0, height))

                lines.append(f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}\n")

            if lines:
                with open(label_file, "w") as f:
                    f.writelines(lines)

        logger.info(f"YOLO export complete: {len(tasks)} label files")
        return True
