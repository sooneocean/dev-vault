"""Comprehensive test suite for Unit 24: Label Studio annotation integration."""

import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from src.watermark_removal.labeling.label_studio_client import (
    LabelStudioClient,
    PredictionBBox,
)
from src.watermark_removal.labeling.dataset_exporter import (
    CoordinateConverter,
    BBoxPixel,
    BBoxPercentage,
    CocoExporter,
    YoloExporter,
)
from src.watermark_removal.labeling.label_studio_setup import (
    DockerComposeGenerator,
    ProjectInitializer,
    APIKeyManager,
)


class TestLabelStudioClientConfiguration:
    """Tests for LabelStudioClient initialization and configuration."""

    def test_client_initialization_defaults(self):
        """Client initializes with correct defaults."""
        client = LabelStudioClient(url="http://localhost:8080", api_key="test-key")
        assert client.url == "http://localhost:8080"
        assert client.api_key == "test-key"
        assert client.timeout_sec == 30.0
        assert client.max_retries == 3

    def test_client_initialization_custom_timeout(self):
        """Client accepts custom timeout."""
        client = LabelStudioClient(
            url="http://localhost:8080",
            api_key="test-key",
            timeout_sec=60.0
        )
        assert client.timeout_sec == 60.0

    def test_client_state_tracking_empty(self):
        """Client tracks empty state on init."""
        client = LabelStudioClient(url="http://localhost:8080", api_key="test-key")
        assert client._projects == {}
        assert client._tasks == {}


class TestLabelStudioProjectOps:
    """Tests for project creation, task upload, and error handling."""

    @pytest.mark.asyncio
    async def test_create_project_success(self):
        """Project creation succeeds and returns project ID."""
        client = LabelStudioClient(url="http://localhost:8080", api_key="test-key")

        label_config = "<View><Image name='image'/></View>"
        project_id = await client.create_project("watermark_detection", label_config)

        assert isinstance(project_id, int)
        assert project_id > 0
        assert project_id in client._projects

    @pytest.mark.asyncio
    async def test_upload_tasks_batch(self):
        """Task upload processes batch correctly."""
        client = LabelStudioClient(url="http://localhost:8080", api_key="test-key")

        label_config = "<View><Image name='image'/></View>"
        project_id = await client.create_project("watermark_detection", label_config)

        frame_data = [
            {"frame_id": 0, "frame_bytes": b"fake_image_0"},
            {"frame_id": 1, "frame_bytes": b"fake_image_1"},
        ]

        task_ids = await client.upload_tasks(project_id, "session_1", frame_data)

        assert isinstance(task_ids, list)
        assert len(task_ids) == 2
        for task_id in task_ids:
            assert task_id in client._tasks

    @pytest.mark.asyncio
    async def test_upload_tasks_empty_list(self):
        """Upload empty task list returns empty list."""
        client = LabelStudioClient(url="http://localhost:8080", api_key="test-key")

        label_config = "<View><Image name='image'/></View>"
        project_id = await client.create_project("test_project", label_config)

        task_ids = await client.upload_tasks(project_id, "session_1", [])

        assert task_ids == []

    @pytest.mark.asyncio
    async def test_upload_tasks_invalid_project(self):
        """Upload to non-existent project raises ValueError."""
        client = LabelStudioClient(url="http://localhost:8080", api_key="test-key")

        frame_data = [{"frame_id": 0, "frame_bytes": b"fake"}]

        with pytest.raises(ValueError):
            await client.upload_tasks(999, "session_1", frame_data)


class TestLabelStudioPredictions:
    """Tests for prediction upload and retrieval."""

    @pytest.mark.asyncio
    async def test_create_predictions_success(self):
        """Predictions are created and tracked."""
        client = LabelStudioClient(url="http://localhost:8080", api_key="test-key")

        label_config = "<View><Image name='image'/></View>"
        project_id = await client.create_project("test_project", label_config)

        frame_data = [{"frame_id": 0, "frame_bytes": b"fake_image_data"}]
        task_ids = await client.upload_tasks(project_id, "session_1", frame_data)
        task_id = task_ids[0]

        bboxes = [
            PredictionBBox(x=10.0, y=20.0, w=10.0, h=5.0, confidence=0.95)
        ]

        result = await client.create_predictions(project_id, task_id, bboxes)

        assert result is True
        assert len(client._tasks[task_id]["predictions"]) == 1

    @pytest.mark.asyncio
    async def test_get_annotations_with_data(self):
        """Annotations are retrieved when available."""
        client = LabelStudioClient(url="http://localhost:8080", api_key="test-key")

        label_config = "<View><Image name='image'/></View>"
        project_id = await client.create_project("test_project", label_config)

        frame_data = [{"frame_id": 0, "frame_bytes": b"fake_image_data"}]
        task_ids = await client.upload_tasks(project_id, "session_1", frame_data)
        task_id = task_ids[0]

        # Add annotations to task
        client._tasks[task_id]["annotations"] = [
            {"x": 10.0, "y": 20.0, "w": 100.0, "h": 50.0},
        ]

        result = await client.get_annotations(task_id, timeout_sec=1.0)

        assert result is not None
        assert len(result) == 1
        assert result[0]["x"] == 10.0

    @pytest.mark.asyncio
    async def test_get_annotations_timeout(self):
        """get_annotations returns None on timeout."""
        client = LabelStudioClient(url="http://localhost:8080", api_key="test-key")

        label_config = "<View><Image name='image'/></View>"
        project_id = await client.create_project("test_project", label_config)

        frame_data = [{"frame_id": 0, "frame_bytes": b"fake_image_data"}]
        task_ids = await client.upload_tasks(project_id, "session_1", frame_data)
        task_id = task_ids[0]

        # Don't add any annotations, so it times out
        result = await client.get_annotations(task_id, timeout_sec=0.1)

        assert result is None


class TestCoordinateConversionPrecision:
    """Tests for pixel/percentage coordinate conversion and roundtrip precision."""

    def test_pixel_to_percentage_conversion(self):
        """Converts pixel coordinates to percentage correctly."""
        bbox_pixel = BBoxPixel(x=100, y=50, w=200, h=100)

        bbox_pct = CoordinateConverter.pixel_to_percentage(
            bbox_pixel, frame_width=1920, frame_height=1080
        )

        assert pytest.approx(bbox_pct.x, abs=0.1) == (100 / 1920) * 100
        assert pytest.approx(bbox_pct.y, abs=0.1) == (50 / 1080) * 100
        assert pytest.approx(bbox_pct.w, abs=0.1) == (200 / 1920) * 100
        assert pytest.approx(bbox_pct.h, abs=0.1) == (100 / 1080) * 100

    def test_percentage_to_pixel_conversion(self):
        """Converts percentage coordinates to pixel correctly."""
        bbox_pct = BBoxPercentage(x=5.0, y=5.0, w=10.0, h=10.0)

        bbox_px = CoordinateConverter.percentage_to_pixel(
            bbox_pct, frame_width=1920, frame_height=1080
        )

        assert bbox_px.x == int((5.0 / 100) * 1920)
        assert bbox_px.y == int((5.0 / 100) * 1080)
        assert bbox_px.w == int((10.0 / 100) * 1920)
        assert bbox_px.h == int((10.0 / 100) * 1080)

    def test_roundtrip_precision_480p(self):
        """Roundtrip conversion maintains ±1px tolerance at 480p."""
        original = BBoxPixel(x=100, y=50, w=200, h=100)

        is_valid, error_msg = CoordinateConverter.validate_roundtrip_precision(
            original, frame_width=854, frame_height=480
        )

        assert is_valid, f"Roundtrip precision failed: {error_msg}"

    def test_roundtrip_precision_1080p(self):
        """Roundtrip conversion maintains ±2px tolerance at 1080p."""
        original = BBoxPixel(x=100, y=50, w=200, h=100)

        is_valid, error_msg = CoordinateConverter.validate_roundtrip_precision(
            original, frame_width=1920, frame_height=1080
        )

        assert is_valid, f"Roundtrip precision failed: {error_msg}"

    def test_edge_case_zero_coordinates(self):
        """Handles zero coordinates without error."""
        bbox = BBoxPixel(x=0, y=0, w=1, h=1)

        result = CoordinateConverter.pixel_to_percentage(
            bbox, frame_width=1920, frame_height=1080
        )

        assert result.x >= 0
        assert result.y >= 0

    def test_edge_case_full_frame(self):
        """Handles full-frame bounding box."""
        bbox = BBoxPixel(x=0, y=0, w=1920, h=1080)

        result = CoordinateConverter.pixel_to_percentage(
            bbox, frame_width=1920, frame_height=1080
        )

        assert pytest.approx(result.x, abs=0.1) == 0.0
        assert pytest.approx(result.y, abs=0.1) == 0.0
        assert pytest.approx(result.w, abs=0.1) == 100.0
        assert pytest.approx(result.h, abs=0.1) == 100.0


class TestCocoExporter:
    """Tests for COCO format export."""

    def test_coco_export_empty_project(self):
        """COCO export handles empty project."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "coco.json"

            result = CocoExporter.export([], str(output_path))

            assert result is True
            assert output_path.exists()

            with open(output_path) as f:
                data = json.load(f)

            assert "images" in data
            assert "annotations" in data
            assert "categories" in data
            assert len(data["images"]) == 0
            assert len(data["annotations"]) == 0

    def test_coco_export_with_annotations(self):
        """COCO export formats annotated data correctly."""
        tasks = [
            {
                "frame_id": 0,
                "annotations": [
                    {"x": 10.0, "y": 5.0, "w": 20.0, "h": 10.0, "label": "watermark"}
                ]
            }
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "coco.json"

            result = CocoExporter.export(tasks, str(output_path))

            assert result is True

            with open(output_path) as f:
                data = json.load(f)

            assert len(data["images"]) == 1
            assert len(data["annotations"]) == 1
            assert data["annotations"][0]["bbox"] == [10.0, 5.0, 20.0, 10.0]

    def test_coco_export_multiple_categories(self):
        """COCO export handles multiple label categories."""
        tasks = [
            {
                "frame_id": 0,
                "annotations": [
                    {"x": 10.0, "y": 5.0, "w": 20.0, "h": 10.0, "label": "watermark"},
                    {"x": 50.0, "y": 50.0, "w": 15.0, "h": 15.0, "label": "logo"},
                ]
            }
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "coco.json"

            result = CocoExporter.export(tasks, str(output_path))

            assert result is True

            with open(output_path) as f:
                data = json.load(f)

            assert len(data["annotations"]) == 2
            # First annotation: watermark (category_id=1)
            assert data["annotations"][0]["category_id"] == 1
            # Second annotation: logo (category_id=2)
            assert data["annotations"][1]["category_id"] == 2


class TestYoloExporter:
    """Tests for YOLO format export."""

    def test_yolo_export_empty_project(self):
        """YOLO export handles empty project."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = YoloExporter.export([], tmpdir)

            assert result is True

    def test_yolo_export_format(self):
        """YOLO export generates correct format."""
        tasks = [
            {
                "frame_id": 0,
                "annotations": [
                    {"x": 10.0, "y": 5.0, "w": 20.0, "h": 10.0, "label": "watermark"}
                ]
            }
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            result = YoloExporter.export(tasks, tmpdir)

            assert result is True

            label_file = Path(tmpdir) / "frame_0.txt"
            assert label_file.exists()

            with open(label_file) as f:
                lines = f.readlines()

            assert len(lines) == 1

            parts = lines[0].strip().split()
            assert len(parts) == 5  # class_id, center_x, center_y, width, height
            assert parts[0] == "0"  # watermark class_id


class TestProjectInitializer:
    """Tests for label configuration and project setup."""

    def test_get_label_config_returns_xml(self):
        """Label config generation returns valid XML."""
        initializer = ProjectInitializer()

        config = initializer.get_label_config()

        assert "<View>" in config
        assert "</View>" in config
        assert isinstance(config, str)

    def test_label_config_includes_all_categories(self):
        """Label config includes all watermark categories."""
        initializer = ProjectInitializer()

        config = initializer.get_label_config()

        categories = ["watermark", "logo", "text", "subtitle", "other"]
        for category in categories:
            assert category.lower() in config.lower()


class TestAPIKeyManager:
    """Tests for API key storage and retrieval."""

    def test_api_key_storage_env_var(self):
        """API key can be stored via environment variable."""
        with patch.dict("os.environ", {"LABEL_STUDIO_API_KEY": "test-key-123"}):
            key = APIKeyManager.get_api_key()

            assert key == "test-key-123"

    def test_api_key_storage_file(self):
        """API key can be stored in file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)

            result = APIKeyManager.setup_api_key("test-key-123", str(config_dir))

            assert result is True

            # Verify file was created
            config_file = config_dir / "api_key.json"
            assert config_file.exists()

            # Verify content
            with open(config_file) as f:
                data = json.load(f)

            assert data["api_key"] == "test-key-123"


class TestDockerComposeGenerator:
    """Tests for docker-compose.yml generation."""

    def test_generate_docker_compose(self):
        """Docker Compose file is generated with correct structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "docker-compose.yml"

            result = DockerComposeGenerator.generate(str(output_path), port=8080)

            assert result is True
            assert output_path.exists()

            with open(output_path) as f:
                compose_content = f.read()

            assert "version:" in compose_content
            assert "services:" in compose_content
            assert "8080" in compose_content
            assert "label-studio" in compose_content

    def test_docker_compose_custom_port(self):
        """Docker Compose respects custom port configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "docker-compose.yml"

            result = DockerComposeGenerator.generate(str(output_path), port=9090)

            assert result is True

            with open(output_path) as f:
                compose_content = f.read()

            assert "9090" in compose_content
