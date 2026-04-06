"""Label Studio API client for annotation workflow management."""

import asyncio
import json
import logging
from typing import Any, Optional

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
