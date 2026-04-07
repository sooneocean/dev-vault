"""Export annotations to COCO JSON and YOLO format.

Contains:
- DatasetExporter: Monolithic converter for Label Studio annotations (COCO + YOLO).
- CoordinateConverter: Pixel/percentage bbox conversion with roundtrip validation.
- CocoExporter: Standalone COCO JSON exporter with multi-category support.
- YoloExporter: Standalone YOLO TXT exporter with multi-category support.
- BBoxPixel / BBoxPercentage: Typed bbox dataclasses.
"""

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class DatasetExporter:
    """Convert Label Studio annotations to training dataset formats.

    Supports:
    - COCO JSON format: {"images": [...], "annotations": [...]}
    - YOLO format: per-image .txt files with normalized center coordinates
    """

    def __init__(self) -> None:
        """Initialize dataset exporter."""
        self.image_id_counter = 0
        self.annotation_id_counter = 0

    def export_to_coco_json(
        self,
        annotations: list[dict],
        output_path: Path,
        dataset_name: str = "watermark_removal",
    ) -> None:
        """Export annotations to COCO JSON format.

        Args:
            annotations: List of task dicts from Label Studio with:
                - id: task ID
                - data: dict with image_url or image path
                - annotations: list of annotation records
            output_path: Path to save COCO JSON file.
            dataset_name: Dataset name for metadata.

        Raises:
            ValueError: If annotations format is invalid.
            IOError: If file write fails.
        """
        logger.info(f"Exporting {len(annotations)} annotations to COCO JSON")

        coco_data = {
            "info": {
                "description": dataset_name,
                "version": "1.0",
                "year": 2026,
            },
            "licenses": [],
            "images": [],
            "annotations": [],
            "categories": [
                {
                    "id": 1,
                    "name": "watermark",
                    "supercategory": "object",
                }
            ],
        }

        # Track processed task IDs to avoid duplicates
        processed_tasks = set()

        for task in annotations:
            task_id = task.get("id")
            if task_id in processed_tasks:
                continue
            processed_tasks.add(task_id)

            # Extract image info
            image_data = task.get("data", {})
            image_url = image_data.get("image_url") or image_data.get("image")

            if not image_url:
                logger.warning(f"Task {task_id} has no image_url or image, skipping")
                continue

            # Create image entry (use task_id as image_id)
            image_id = task_id
            coco_data["images"].append(
                {
                    "id": image_id,
                    "file_name": str(image_url),
                    "height": image_data.get("height", 0),
                    "width": image_data.get("width", 0),
                }
            )

            # Extract annotations (predictions)
            task_annotations = task.get("annotations", [])

            # Handle both single annotation and list of annotations
            if isinstance(task_annotations, dict):
                task_annotations = [task_annotations]

            for annotation in task_annotations:
                if not annotation:
                    continue

                # Extract region/result
                result = annotation.get("result", [])
                if not isinstance(result, list):
                    result = [result]

                for region in result:
                    if region.get("type") != "rectanglelabels":
                        continue

                    value = region.get("value", {})
                    x = value.get("x", 0) / 100.0  # Convert from percentage
                    y = value.get("y", 0) / 100.0
                    width = value.get("width", 0) / 100.0
                    height = value.get("height", 0) / 100.0

                    # Convert to absolute coordinates
                    image_width = coco_data["images"][-1].get("width", 1)
                    image_height = coco_data["images"][-1].get("height", 1)

                    abs_x = int(x * image_width)
                    abs_y = int(y * image_height)
                    abs_w = int(width * image_width)
                    abs_h = int(height * image_height)

                    # Create COCO annotation entry
                    self.annotation_id_counter += 1
                    coco_data["annotations"].append(
                        {
                            "id": self.annotation_id_counter,
                            "image_id": image_id,
                            "category_id": 1,  # watermark class
                            "bbox": [abs_x, abs_y, abs_w, abs_h],
                            "area": abs_w * abs_h,
                            "iscrowd": 0,
                            "confidence": value.get("confidence", 1.0),
                        }
                    )

        # Write to file
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(coco_data, f, indent=2)

        logger.info(
            f"Exported {len(coco_data['images'])} images and "
            f"{len(coco_data['annotations'])} annotations to {output_path}"
        )

    def export_to_yolo_format(
        self,
        annotations: list[dict],
        output_dir: Path,
        image_dir: Optional[Path] = None,
    ) -> None:
        """Export annotations to YOLO format.

        Creates one .txt file per image with normalized bbox coordinates:
        class_id center_x center_y width height (all normalized 0-1)

        Args:
            annotations: List of task dicts from Label Studio.
            output_dir: Directory to save .txt files.
            image_dir: Optional base directory for images (for path resolution).

        Raises:
            ValueError: If annotations format is invalid.
            IOError: If file write fails.
        """
        logger.info(f"Exporting {len(annotations)} annotations to YOLO format")

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        processed_tasks = set()

        for task in annotations:
            task_id = task.get("id")
            if task_id in processed_tasks:
                continue
            processed_tasks.add(task_id)

            # Extract image info
            image_data = task.get("data", {})
            image_path = image_data.get("image_url") or image_data.get("image")

            if not image_path:
                logger.warning(f"Task {task_id} has no image, skipping")
                continue

            # Derive output .txt filename from image filename
            image_filename = Path(image_path).name
            txt_filename = output_dir / f"{Path(image_filename).stem}.txt"

            # Get image dimensions
            image_width = image_data.get("width", 1)
            image_height = image_data.get("height", 1)

            # Extract annotations
            task_annotations = task.get("annotations", [])
            if isinstance(task_annotations, dict):
                task_annotations = [task_annotations]

            yolo_lines = []

            for annotation in task_annotations:
                if not annotation:
                    continue

                result = annotation.get("result", [])
                if not isinstance(result, list):
                    result = [result]

                for region in result:
                    if region.get("type") != "rectanglelabels":
                        continue

                    value = region.get("value", {})

                    # Extract bbox in percentage (0-100)
                    x_pct = value.get("x", 0) / 100.0
                    y_pct = value.get("y", 0) / 100.0
                    w_pct = value.get("width", 0) / 100.0
                    h_pct = value.get("height", 0) / 100.0

                    # Convert to YOLO format (center x, center y, width, height)
                    center_x = x_pct + w_pct / 2.0
                    center_y = y_pct + h_pct / 2.0

                    # Class ID: 0 for watermark
                    class_id = 0

                    # Write normalized coordinates
                    line = f"{class_id} {center_x:.6f} {center_y:.6f} {w_pct:.6f} {h_pct:.6f}\n"
                    yolo_lines.append(line)

            # Write .txt file if there are annotations
            if yolo_lines:
                with open(txt_filename, "w") as f:
                    f.writelines(yolo_lines)
                logger.debug(f"Created {txt_filename} with {len(yolo_lines)} annotations")
            else:
                # Create empty .txt file for tasks without annotations
                with open(txt_filename, "w") as f:
                    pass
                logger.debug(f"Created empty {txt_filename} (no annotations)")

        logger.info(f"Exported {len(processed_tasks)} annotation files to {output_dir}")

    def validate_coco_json(self, filepath: Path) -> bool:
        """Validate COCO JSON file structure.

        Args:
            filepath: Path to COCO JSON file.

        Returns:
            True if file is valid COCO JSON.

        Raises:
            ValueError: If validation fails.
        """
        try:
            with open(filepath) as f:
                data = json.load(f)

            # Check required keys
            required_keys = {"info", "images", "annotations", "categories"}
            if not required_keys.issubset(set(data.keys())):
                raise ValueError(f"Missing required keys. Expected {required_keys}")

            # Validate images
            if not isinstance(data.get("images"), list):
                raise ValueError("images must be a list")

            # Validate annotations
            if not isinstance(data.get("annotations"), list):
                raise ValueError("annotations must be a list")

            # Validate categories
            if not isinstance(data.get("categories"), list):
                raise ValueError("categories must be a list")

            logger.info(f"COCO JSON validation passed: {len(data['images'])} images, "
                       f"{len(data['annotations'])} annotations")
            return True

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")
        except Exception as e:
            raise ValueError(f"Validation error: {e}")

    def validate_yolo_format(self, output_dir: Path) -> bool:
        """Validate YOLO format annotation files.

        Args:
            output_dir: Directory containing .txt files.

        Returns:
            True if all .txt files are valid YOLO format.

        Raises:
            ValueError: If validation fails.
        """
        output_dir = Path(output_dir)
        txt_files = list(output_dir.glob("*.txt"))

        if not txt_files:
            logger.warning(f"No .txt files found in {output_dir}")
            return True

        for txt_file in txt_files:
            try:
                with open(txt_file) as f:
                    for line_num, line in enumerate(f, 1):
                        line = line.strip()
                        if not line:
                            continue

                        parts = line.split()
                        if len(parts) != 5:
                            raise ValueError(
                                f"{txt_file}:{line_num} expected 5 values, got {len(parts)}"
                            )

                        # Validate values
                        class_id = int(parts[0])
                        center_x = float(parts[1])
                        center_y = float(parts[2])
                        width = float(parts[3])
                        height = float(parts[4])

                        # Check ranges
                        if not (0 <= center_x <= 1):
                            raise ValueError(f"center_x out of range: {center_x}")
                        if not (0 <= center_y <= 1):
                            raise ValueError(f"center_y out of range: {center_y}")
                        if not (0 <= width <= 1):
                            raise ValueError(f"width out of range: {width}")
                        if not (0 <= height <= 1):
                            raise ValueError(f"height out of range: {height}")

            except (ValueError, OSError) as e:
                raise ValueError(f"YOLO format validation error in {txt_file}: {e}")

        logger.info(f"YOLO format validation passed: {len(txt_files)} files")
        return True


# ---------------------------------------------------------------------------
# Typed bbox dataclasses (merged from labeling module)
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Coordinate converter (merged from labeling module)
# ---------------------------------------------------------------------------


class CoordinateConverter:
    """Convert bbox coordinates between pixel and percentage."""

    # Precision tolerance: +/-1 pixel at 480p, +/-2 pixels at 1080p
    PIXEL_TOLERANCE_480P = 1
    PIXEL_TOLERANCE_1080P = 2

    @staticmethod
    def pixel_to_percentage(
        bbox: BBoxPixel,
        frame_width: int,
        frame_height: int,
    ) -> BBoxPercentage:
        """Convert pixel coordinates to percentage (0-100).

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
        """Convert percentage coordinates back to pixels.

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
        """Validate coordinate conversion roundtrip precision.

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


# ---------------------------------------------------------------------------
# Standalone exporters with multi-category support (merged from labeling module)
# ---------------------------------------------------------------------------


class CocoExporter:
    """Export Label Studio annotations to COCO JSON format."""

    @staticmethod
    def export(
        tasks: List[Dict[str, Any]],
        output_path: str,
        frame_width: int = 640,
        frame_height: int = 480,
    ) -> bool:
        """Export tasks to COCO format.

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
        """Export tasks to YOLO format.

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
