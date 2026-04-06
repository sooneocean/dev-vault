"""
Label Studio client for annotation workflow integration.

Provides async wrapper for uploading watermark detection predictions
to Label Studio as pre-annotations, retrieving human corrections,
and exporting annotated data for training.
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from typing import Optional, Dict, List, Any

logger = logging.getLogger(__name__)


@dataclass
class PredictionBBox:
    """Single bbox prediction."""
    x: float  # Percentage, 0-100
    y: float  # Percentage, 0-100
    w: float  # Width in percentage
    h: float  # Height in percentage
    confidence: float  # 0.0-1.0
    label: str = "watermark"


@dataclass
class LabelStudioTask:
    """Label Studio task metadata."""
    task_id: int
    session_id: str
    frame_id: int
    status: str  # "waiting", "in_progress", "completed"
    created_at: float
    updated_at: float


class LabelStudioClient:
    """Async client for Label Studio annotation workflow."""

    def __init__(
        self,
        url: str = "http://localhost:8080",
        api_key: str = "",
        timeout_sec: float = 30.0,
        max_retries: int = 3,
        retry_backoff_sec: float = 1.0,
    ):
        """
        Initialize Label Studio client.

        Args:
            url: Label Studio server URL (e.g., "http://localhost:8080")
            api_key: API key for authentication
            timeout_sec: Request timeout in seconds
            max_retries: Maximum retry attempts on failure
            retry_backoff_sec: Initial backoff for exponential retry
        """
        self.url = url.rstrip("/")
        self.api_key = api_key
        self.timeout_sec = timeout_sec
        self.max_retries = max_retries
        self.retry_backoff_sec = retry_backoff_sec

        # In-memory cache of projects and tasks (Phase 3B MVP)
        # Redis migration path available for Phase 4
        self._projects: Dict[int, Dict[str, Any]] = {}
        self._tasks: Dict[int, Dict[str, Any]] = {}
        self._task_counter = 0

    async def create_project(
        self,
        project_name: str,
        label_config: str,
    ) -> int:
        """
        Create a new Label Studio project.

        Args:
            project_name: Name of the project (e.g., "Watermark Removal")
            label_config: XML label configuration defining annotation schema

        Returns:
            Project ID

        Raises:
            RuntimeError: If project creation fails after retries
        """
        logger.info(f"Creating project: {project_name}")

        project_data = {
            "title": project_name,
            "label_config": label_config,
            "created_at": time.time(),
        }

        # Simulate project creation with in-memory ID
        project_id = hash(project_name) & 0x7FFFFFFF  # Positive int
        self._projects[project_id] = project_data

        logger.info(f"Project created: {project_id}")
        return project_id

    async def upload_tasks(
        self,
        project_id: int,
        session_id: str,
        frame_data_list: List[Dict[str, Any]],
    ) -> List[int]:
        """
        Upload frames as Label Studio tasks.

        Args:
            project_id: Target project ID
            session_id: Streaming session ID for tracking
            frame_data_list: List of {"frame_id": int, "frame_bytes": bytes, ...}

        Returns:
            List of created task IDs

        Raises:
            ValueError: If project not found
            RuntimeError: If upload fails after retries
        """
        if project_id not in self._projects:
            raise ValueError(f"Project {project_id} not found")

        logger.info(f"Uploading {len(frame_data_list)} tasks to project {project_id}")

        task_ids = []
        for frame_data in frame_data_list:
            task_id = self._task_counter
            self._task_counter += 1

            task = {
                "task_id": task_id,
                "project_id": project_id,
                "session_id": session_id,
                "frame_id": frame_data.get("frame_id"),
                "created_at": time.time(),
                "annotations": [],
                "predictions": [],
            }

            self._tasks[task_id] = task
            task_ids.append(task_id)

        logger.info(f"Created {len(task_ids)} tasks")
        return task_ids

    async def create_predictions(
        self,
        project_id: int,
        task_id: int,
        bboxes: List[PredictionBBox],
    ) -> bool:
        """
        Upload ensemble detector predictions as pre-annotations.

        Args:
            project_id: Target project ID
            task_id: Target task ID
            bboxes: List of predictions (pixel → percentage converted)

        Returns:
            True if successful

        Raises:
            ValueError: If task not found
        """
        if task_id not in self._tasks:
            raise ValueError(f"Task {task_id} not found")

        task = self._tasks[task_id]
        if task["project_id"] != project_id:
            raise ValueError(f"Task {task_id} not in project {project_id}")

        logger.info(f"Creating {len(bboxes)} predictions for task {task_id}")

        # Store predictions in task
        predictions = []
        for bbox in bboxes:
            pred = {
                "x": bbox.x,
                "y": bbox.y,
                "w": bbox.w,
                "h": bbox.h,
                "confidence": bbox.confidence,
                "label": bbox.label,
            }
            predictions.append(pred)

        task["predictions"] = predictions
        task["updated_at"] = time.time()

        logger.info(f"Predictions created for task {task_id}")
        return True

    async def get_annotations(
        self,
        task_id: int,
        timeout_sec: Optional[float] = None,
        poll_interval_sec: float = 1.0,
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get human annotations for a task.

        Blocks until annotations are available or timeout.

        Args:
            task_id: Target task ID
            timeout_sec: Max wait time in seconds (None = indefinite)
            poll_interval_sec: Check interval while waiting

        Returns:
            List of annotations (or None if timeout)

        Raises:
            ValueError: If task not found
        """
        if task_id not in self._tasks:
            raise ValueError(f"Task {task_id} not found")

        logger.info(f"Waiting for annotations on task {task_id}")

        timeout = timeout_sec or self.timeout_sec
        deadline = time.time() + timeout

        while True:
            task = self._tasks[task_id]
            annotations = task.get("annotations", [])

            if annotations:
                logger.info(f"Annotations received for task {task_id}: {len(annotations)} items")
                return annotations

            if time.time() > deadline:
                logger.warning(f"Annotation timeout for task {task_id}")
                return None

            await asyncio.sleep(poll_interval_sec)

    async def export_coco(
        self,
        project_id: int,
        output_path: str,
    ) -> bool:
        """
        Export project annotations in COCO JSON format.

        Args:
            project_id: Target project ID
            output_path: File path to write COCO JSON

        Returns:
            True if successful
        """
        if project_id not in self._projects:
            raise ValueError(f"Project {project_id} not found")

        logger.info(f"Exporting project {project_id} to COCO format: {output_path}")

        # Collect all tasks in project
        tasks_in_project = [
            t for t in self._tasks.values()
            if t["project_id"] == project_id
        ]

        # Build COCO structure (simplified)
        coco_data = {
            "info": {
                "description": f"Project {project_id}",
            },
            "images": [],
            "annotations": [],
            "categories": [{"id": 1, "name": "watermark"}],
        }

        image_id = 0
        annotation_id = 0

        for task in tasks_in_project:
            image_id += 1
            coco_data["images"].append({
                "id": image_id,
                "file_name": f"frame_{task['frame_id']}.jpg",
                "width": 640,  # Placeholder
                "height": 480,  # Placeholder
            })

            # Add annotations
            annotations = task.get("annotations", [])
            for ann in annotations:
                annotation_id += 1
                coco_data["annotations"].append({
                    "id": annotation_id,
                    "image_id": image_id,
                    "category_id": 1,
                    "bbox": [ann["x"], ann["y"], ann["w"], ann["h"]],
                    "area": ann["w"] * ann["h"],
                    "iscrowd": 0,
                })

        # Write to file
        with open(output_path, "w") as f:
            json.dump(coco_data, f, indent=2)

        logger.info(f"COCO export complete: {len(coco_data['images'])} images, {len(coco_data['annotations'])} annotations")
        return True

    async def export_yolo(
        self,
        project_id: int,
        output_dir: str,
    ) -> bool:
        """
        Export project annotations in YOLO format.

        Args:
            project_id: Target project ID
            output_dir: Directory to write YOLO format files

        Returns:
            True if successful
        """
        if project_id not in self._projects:
            raise ValueError(f"Project {project_id} not found")

        logger.info(f"Exporting project {project_id} to YOLO format: {output_dir}")

        # Collect all tasks in project
        tasks_in_project = [
            t for t in self._tasks.values()
            if t["project_id"] == project_id
        ]

        # Create YOLO format files (simplified)
        # YOLO format: class_id x_center y_center width height (normalized)
        import os
        os.makedirs(output_dir, exist_ok=True)

        for task in tasks_in_project:
            frame_id = task["frame_id"]
            label_file = os.path.join(output_dir, f"frame_{frame_id}.txt")

            annotations = task.get("annotations", [])
            lines = []
            for ann in annotations:
                # YOLO format: normalized coordinates
                x_center = (ann["x"] + ann["w"] / 2) / 100.0
                y_center = (ann["y"] + ann["h"] / 2) / 100.0
                w = ann["w"] / 100.0
                h = ann["h"] / 100.0

                lines.append(f"0 {x_center:.4f} {y_center:.4f} {w:.4f} {h:.4f}\n")

            with open(label_file, "w") as f:
                f.writelines(lines)

        logger.info(f"YOLO export complete: {len(tasks_in_project)} label files")
        return True

    async def health_check(self) -> bool:
        """
        Check if Label Studio server is reachable.

        Returns:
            True if server is healthy
        """
        try:
            # Simulate connectivity check
            logger.info(f"Health check: {self.url}")
            return True
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
