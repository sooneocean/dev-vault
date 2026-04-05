"""Export annotations to COCO JSON and YOLO format."""

import json
import logging
from pathlib import Path
from typing import Any, Optional

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
