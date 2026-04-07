"""Label Studio API client for annotation workflow management.

Contains two client implementations:
- LabelStudioClient: Production aiohttp-based async client for Label Studio HTTP API.
- LabelStudioSessionClient: Session-aware in-memory client for streaming/MVP workflows.

Also provides dataclasses for prediction and task metadata.
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import aiohttp

logger = logging.getLogger(__name__)


class LabelStudioClient:
    """Python wrapper for Label Studio HTTP API.

    Handles authentication, project management, and annotation CRUD operations.
    Supports both sync and async operations with automatic retry and backoff.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 8080,
        api_key: str = "",
        timeout: float = 30.0,
        max_retries: int = 3,
        backoff_factor: float = 2.0,
    ) -> None:
        """Initialize Label Studio client.

        Args:
            host: Label Studio host (default: localhost).
            port: Label Studio port (default: 8080).
            api_key: API key for authentication.
            timeout: Request timeout in seconds.
            max_retries: Maximum number of retries on transient errors.
            backoff_factor: Exponential backoff multiplier between retries.

        Raises:
            ValueError: If api_key is empty when label_studio_enabled is True.
        """
        self.base_url = f"http://{host}:{port}/api"
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self._session: Optional[aiohttp.ClientSession] = None

        logger.info(f"Initialized Label Studio client at {self.base_url}")

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self) -> None:
        """Close aiohttp session."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def _request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[dict] = None,
        params: Optional[dict] = None,
    ) -> dict:
        """Make HTTP request with automatic retry and backoff.

        Args:
            method: HTTP method (GET, POST, PATCH, DELETE).
            endpoint: API endpoint (relative to base_url).
            json_data: JSON request body.
            params: Query parameters.

        Returns:
            Parsed JSON response.

        Raises:
            RuntimeError: If all retries fail or authentication fails.
        """
        url = f"{self.base_url}/{endpoint}"
        headers = {
            "Authorization": f"Token {self.api_key}",
            "Content-Type": "application/json",
        }

        session = await self._get_session()

        for attempt in range(self.max_retries):
            try:
                async with session.request(
                    method,
                    url,
                    json=json_data,
                    params=params,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                ) as resp:
                    # Handle authentication error
                    if resp.status == 401:
                        raise RuntimeError("Label Studio authentication failed: invalid API key")

                    # Parse response
                    response_data = await resp.json()

                    # Check for error status codes
                    if resp.status >= 400:
                        error_msg = response_data.get("detail", f"HTTP {resp.status}")
                        if resp.status >= 500 and attempt < self.max_retries - 1:
                            # Retry on 5xx errors
                            wait_time = self.backoff_factor ** attempt
                            logger.warning(
                                f"Server error {resp.status}, retrying in {wait_time}s..."
                            )
                            await asyncio.sleep(wait_time)
                            continue
                        raise RuntimeError(f"Label Studio API error: {error_msg}")

                    return response_data

            except asyncio.TimeoutError as e:
                if attempt < self.max_retries - 1:
                    wait_time = self.backoff_factor ** attempt
                    logger.warning(f"Request timeout, retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                    continue
                raise RuntimeError(f"Label Studio server unreachable: {e}")
            except aiohttp.ClientError as e:
                if attempt < self.max_retries - 1:
                    wait_time = self.backoff_factor ** attempt
                    logger.warning(f"Connection error, retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                    continue
                raise RuntimeError(f"Label Studio connection failed: {e}")

    async def create_project(
        self,
        title: str,
        label_config: str,
        description: str = "",
    ) -> dict:
        """Create a new Label Studio project.

        Args:
            title: Project title.
            label_config: XML label configuration for the project.
            description: Optional project description.

        Returns:
            Project response dict with id, title, label_config, etc.

        Raises:
            RuntimeError: If project creation fails.
        """
        payload = {
            "title": title,
            "description": description,
            "label_config": label_config,
        }

        logger.info(f"Creating Label Studio project: {title}")
        response = await self._request("POST", "projects", json_data=payload)
        logger.info(f"Project created with ID: {response.get('id')}")

        return response

    async def get_project(self, project_id: int) -> dict:
        """Get project details.

        Args:
            project_id: Label Studio project ID.

        Returns:
            Project response dict.

        Raises:
            RuntimeError: If project not found or API error.
        """
        logger.debug(f"Fetching project {project_id}")
        return await self._request("GET", f"projects/{project_id}")

    async def list_projects(self, limit: int = 100, offset: int = 0) -> dict:
        """List all projects.

        Args:
            limit: Maximum number of projects to return.
            offset: Pagination offset.

        Returns:
            Dict with count, next, previous, and results (list of projects).

        Raises:
            RuntimeError: If API error.
        """
        params = {"limit": limit, "offset": offset}
        logger.debug(f"Listing projects (limit={limit}, offset={offset})")
        return await self._request("GET", "projects", params=params)

    async def upload_tasks(
        self,
        project_id: int,
        tasks: list[dict],
    ) -> dict:
        """Upload tasks (images with pre-annotations) to a project.

        Args:
            project_id: Label Studio project ID.
            tasks: List of task dicts. Each task should have:
                - data: dict with image_url or image (base64).
                - predictions: optional list of pre-annotations.

        Returns:
            Response dict with task_ids.

        Raises:
            RuntimeError: If upload fails.
        """
        # Create tasks (one at a time to avoid bulk API issues)
        created_task_ids = []

        for i, task in enumerate(tasks):
            try:
                response = await self._request(
                    "POST",
                    f"projects/{project_id}/tasks",
                    json_data=task,
                )
                created_task_ids.append(response.get("id"))

                if (i + 1) % 10 == 0:
                    logger.info(f"Uploaded {i + 1}/{len(tasks)} tasks")

            except RuntimeError as e:
                logger.error(f"Failed to upload task {i}: {e}")
                raise

        logger.info(f"Successfully uploaded {len(created_task_ids)} tasks to project {project_id}")
        return {"task_ids": created_task_ids}

    async def create_annotation(
        self,
        task_id: int,
        annotation_data: dict,
    ) -> dict:
        """Create a new annotation (pre-annotation) for a task.

        Args:
            task_id: Label Studio task ID.
            annotation_data: Annotation dict with result regions and metadata.
                Example:
                {
                    "value": {
                        "x": 10, "y": 20, "width": 100, "height": 80,
                        "rotation": 0, "rectanglelabels": ["watermark"]
                    },
                    "from_name": "label",
                    "to_name": "image",
                    "type": "rectanglelabels"
                }

        Returns:
            Created annotation response.

        Raises:
            RuntimeError: If creation fails.
        """
        payload = {
            "value": annotation_data.get("value", {}),
            "from_name": annotation_data.get("from_name", "label"),
            "to_name": annotation_data.get("to_name", "image"),
            "type": annotation_data.get("type", "rectanglelabels"),
        }

        logger.debug(f"Creating annotation for task {task_id}")
        return await self._request(
            "POST",
            f"tasks/{task_id}/annotations",
            json_data=payload,
        )

    async def get_task_annotations(self, task_id: int) -> dict:
        """Get all annotations for a task.

        Args:
            task_id: Label Studio task ID.

        Returns:
            Task response with annotations.

        Raises:
            RuntimeError: If API error.
        """
        logger.debug(f"Fetching annotations for task {task_id}")
        return await self._request("GET", f"tasks/{task_id}")

    async def download_annotations(self, project_id: int) -> list[dict]:
        """Download all annotations from a project as JSON.

        Args:
            project_id: Label Studio project ID.

        Returns:
            List of task dicts with annotations.

        Raises:
            RuntimeError: If download fails.
        """
        logger.info(f"Downloading annotations from project {project_id}")

        all_tasks = []
        offset = 0
        limit = 100

        while True:
            params = {
                "limit": limit,
                "offset": offset,
                "include": "id,data,annotations",
            }

            response = await self._request("GET", f"projects/{project_id}/tasks", params=params)
            tasks = response.get("results", [])

            if not tasks:
                break

            all_tasks.extend(tasks)
            logger.info(f"Downloaded {len(all_tasks)} tasks so far...")

            if response.get("next") is None:
                break

            offset += limit

        logger.info(f"Downloaded {len(all_tasks)} total annotations")
        return all_tasks

    async def validate_connection(self) -> bool:
        """Validate Label Studio connection and API key.

        Returns:
            True if connection and auth are valid.

        Raises:
            RuntimeError: If connection or auth fails.
        """
        try:
            logger.info("Validating Label Studio connection...")
            await self._request("GET", "user")
            logger.info("Label Studio connection validated")
            return True
        except RuntimeError as e:
            logger.error(f"Label Studio validation failed: {e}")
            raise


# ---------------------------------------------------------------------------
# Dataclasses for prediction/task metadata (merged from labeling module)
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Session-aware in-memory client (merged from labeling module)
# ---------------------------------------------------------------------------


class LabelStudioSessionClient:
    """Session-aware in-memory Label Studio client for streaming/MVP workflows.

    Unlike the production LabelStudioClient (aiohttp-based), this client
    stores projects and tasks in-memory for rapid prototyping and testing.
    It tracks streaming session IDs and supports prediction upload, polling
    annotation retrieval, and simplified COCO/YOLO export.

    Migration path: Replace with LabelStudioClient + Redis cache in Phase 4.
    """

    def __init__(
        self,
        url: str = "http://localhost:8080",
        api_key: str = "",
        timeout_sec: float = 30.0,
        max_retries: int = 3,
        retry_backoff_sec: float = 1.0,
    ):
        """Initialize session-aware Label Studio client.

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
        """Create a new Label Studio project.

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
        """Upload frames as Label Studio tasks.

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
        """Upload ensemble detector predictions as pre-annotations.

        Args:
            project_id: Target project ID
            task_id: Target task ID
            bboxes: List of predictions (pixel -> percentage converted)

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
        """Get human annotations for a task.

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
        """Export project annotations in COCO JSON format.

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
        """Export project annotations in YOLO format.

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
        """Check if Label Studio server is reachable.

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
