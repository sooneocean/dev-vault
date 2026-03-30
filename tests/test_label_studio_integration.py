"""Comprehensive tests for Label Studio integration.

12 unit tests + 6 integration tests = 18 total tests
"""

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from watermark_removal.annotation.label_studio_client import LabelStudioClient
from watermark_removal.annotation.dataset_exporter import DatasetExporter
from watermark_removal.detection.watermark_detector import BBox

logger = logging.getLogger(__name__)


# ============================================================================
# UNIT TESTS (12)
# ============================================================================


class TestLabelStudioClientInit:
    """Test LabelStudioClient initialization."""

    def test_init_default_values(self):
        """Test initialization with default values."""
        client = LabelStudioClient()
        assert client.base_url == "http://localhost:8080/api"
        assert client.api_key == ""
        assert client.timeout == 30.0
        assert client.max_retries == 3
        assert client.backoff_factor == 2.0

    def test_init_custom_values(self):
        """Test initialization with custom values."""
        client = LabelStudioClient(
            host="example.com",
            port=9000,
            api_key="test_key_123",
            timeout=60.0,
            max_retries=5,
        )
        assert client.base_url == "http://example.com:9000/api"
        assert client.api_key == "test_key_123"
        assert client.timeout == 60.0
        assert client.max_retries == 5

    @pytest.mark.asyncio
    async def test_close_session(self):
        """Test closing aiohttp session."""
        client = LabelStudioClient()
        session = await client._get_session()
        assert session is not None
        assert not session.closed

        await client.close()
        assert session.closed


class TestDatasetExporterCOCO:
    """Test COCO JSON export functionality."""

    def test_export_to_coco_json_basic(self, tmp_path):
        """Test basic COCO JSON export."""
        exporter = DatasetExporter()

        annotations = [
            {
                "id": 1,
                "data": {
                    "image_url": "frame_1.jpg",
                    "width": 1920,
                    "height": 1080,
                },
                "annotations": [
                    {
                        "result": [
                            {
                                "type": "rectanglelabels",
                                "value": {
                                    "x": 10.0,
                                    "y": 20.0,
                                    "width": 30.0,
                                    "height": 40.0,
                                    "confidence": 0.95,
                                },
                            }
                        ]
                    }
                ],
            }
        ]

        output_path = tmp_path / "annotations.json"
        exporter.export_to_coco_json(annotations, output_path)

        assert output_path.exists()

        with open(output_path) as f:
            data = json.load(f)

        assert "images" in data
        assert "annotations" in data
        assert "categories" in data
        assert len(data["images"]) == 1
        assert len(data["annotations"]) == 1

    def test_export_to_coco_json_multiple_annotations(self, tmp_path):
        """Test COCO JSON export with multiple annotations per task."""
        exporter = DatasetExporter()

        annotations = [
            {
                "id": 1,
                "data": {"image_url": "frame.jpg", "width": 1920, "height": 1080},
                "annotations": [
                    {
                        "result": [
                            {
                                "type": "rectanglelabels",
                                "value": {"x": 10, "y": 20, "width": 30, "height": 40},
                            },
                            {
                                "type": "rectanglelabels",
                                "value": {"x": 50, "y": 60, "width": 20, "height": 30},
                            },
                        ]
                    }
                ],
            }
        ]

        output_path = tmp_path / "annotations.json"
        exporter.export_to_coco_json(annotations, output_path)

        with open(output_path) as f:
            data = json.load(f)

        assert len(data["annotations"]) == 2

    def test_validate_coco_json_valid(self, tmp_path):
        """Test COCO JSON validation with valid file."""
        coco_data = {
            "info": {"description": "test"},
            "licenses": [],
            "images": [{"id": 1, "file_name": "test.jpg", "height": 100, "width": 100}],
            "annotations": [{"id": 1, "image_id": 1, "category_id": 1, "bbox": [0, 0, 10, 10]}],
            "categories": [{"id": 1, "name": "watermark"}],
        }

        output_path = tmp_path / "coco.json"
        with open(output_path, "w") as f:
            json.dump(coco_data, f)

        exporter = DatasetExporter()
        assert exporter.validate_coco_json(output_path)

    def test_validate_coco_json_invalid(self, tmp_path):
        """Test COCO JSON validation with invalid file."""
        invalid_data = {"info": "missing required fields"}

        output_path = tmp_path / "invalid.json"
        with open(output_path, "w") as f:
            json.dump(invalid_data, f)

        exporter = DatasetExporter()
        with pytest.raises(ValueError, match="Missing required keys"):
            exporter.validate_coco_json(output_path)


class TestDatasetExporterYOLO:
    """Test YOLO format export functionality."""

    def test_export_to_yolo_format_basic(self, tmp_path):
        """Test basic YOLO format export."""
        exporter = DatasetExporter()

        annotations = [
            {
                "id": 1,
                "data": {"image_url": "frame_1.jpg", "width": 1920, "height": 1080},
                "annotations": [
                    {
                        "result": [
                            {
                                "type": "rectanglelabels",
                                "value": {
                                    "x": 50.0,
                                    "y": 50.0,
                                    "width": 20.0,
                                    "height": 30.0,
                                },
                            }
                        ]
                    }
                ],
            }
        ]

        output_dir = tmp_path / "yolo"
        exporter.export_to_yolo_format(annotations, output_dir)

        # Check that .txt file was created
        txt_file = output_dir / "frame_1.txt"
        assert txt_file.exists()

        # Check file format
        with open(txt_file) as f:
            lines = f.readlines()

        assert len(lines) == 1
        parts = lines[0].strip().split()
        assert len(parts) == 5
        assert parts[0] == "0"  # class_id

    def test_export_to_yolo_format_multiple_boxes(self, tmp_path):
        """Test YOLO export with multiple bounding boxes."""
        exporter = DatasetExporter()

        annotations = [
            {
                "id": 1,
                "data": {"image_url": "frame.jpg", "width": 1920, "height": 1080},
                "annotations": [
                    {
                        "result": [
                            {
                                "type": "rectanglelabels",
                                "value": {"x": 10, "y": 20, "width": 30, "height": 40},
                            },
                            {
                                "type": "rectanglelabels",
                                "value": {"x": 50, "y": 60, "width": 20, "height": 30},
                            },
                        ]
                    }
                ],
            }
        ]

        output_dir = tmp_path / "yolo"
        exporter.export_to_yolo_format(annotations, output_dir)

        txt_file = output_dir / "frame.txt"
        with open(txt_file) as f:
            lines = f.readlines()

        assert len(lines) == 2

    def test_validate_yolo_format_valid(self, tmp_path):
        """Test YOLO format validation with valid files."""
        output_dir = tmp_path / "yolo"
        output_dir.mkdir()

        # Create valid YOLO format files
        txt_file = output_dir / "frame_1.txt"
        with open(txt_file, "w") as f:
            f.write("0 0.5 0.5 0.3 0.4\n")
            f.write("0 0.7 0.7 0.2 0.3\n")

        exporter = DatasetExporter()
        assert exporter.validate_yolo_format(output_dir)

    def test_validate_yolo_format_invalid_range(self, tmp_path):
        """Test YOLO format validation with out-of-range values."""
        output_dir = tmp_path / "yolo"
        output_dir.mkdir()

        # Create invalid YOLO format file (center_x > 1.0)
        txt_file = output_dir / "frame_1.txt"
        with open(txt_file, "w") as f:
            f.write("0 1.5 0.5 0.3 0.4\n")

        exporter = DatasetExporter()
        with pytest.raises(ValueError, match="center_x out of range"):
            exporter.validate_yolo_format(output_dir)


class TestStreamingServerIntegration:
    """Test streaming server with Label Studio integration."""

    def test_streaming_server_imports(self):
        """Test that streaming server can be imported."""
        try:
            from watermark_removal.streaming.server import create_app
            assert create_app is not None
        except ImportError as e:
            pytest.skip(f"Streaming server not fully available: {e}")


# ============================================================================
# INTEGRATION TESTS (6)
# ============================================================================


class TestLabelStudioIntegration:
    """Integration tests for Label Studio workflow."""

    @pytest.mark.asyncio
    async def test_client_request_method_headers(self):
        """Test that _request method sets correct headers."""
        client = LabelStudioClient(api_key="test_key_123")

        # Mock the session
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"id": 1})

        mock_session = AsyncMock()
        mock_session.request = AsyncMock()
        mock_session.request.return_value.__aenter__.return_value = mock_response
        mock_session.closed = False

        client._session = mock_session

        # Make a request
        try:
            result = await client._request("GET", "user")
            assert result == {"id": 1}

            # Verify request was made with correct headers
            call_args = mock_session.request.call_args
            headers = call_args.kwargs.get("headers", {})
            assert "Authorization" in headers
            assert "Token test_key_123" in headers["Authorization"]
        finally:
            await client.close()

    @pytest.mark.asyncio
    async def test_export_and_validate_roundtrip(self, tmp_path):
        """Test export -> validate -> reimport roundtrip."""
        exporter = DatasetExporter()

        # Create test annotations
        annotations = [
            {
                "id": 1,
                "data": {"image_url": "frame_1.jpg", "width": 1920, "height": 1080},
                "annotations": [
                    {
                        "result": [
                            {
                                "type": "rectanglelabels",
                                "value": {
                                    "x": 25.0,
                                    "y": 25.0,
                                    "width": 50.0,
                                    "height": 50.0,
                                },
                            }
                        ]
                    }
                ],
            }
        ]

        # Export to COCO
        coco_path = tmp_path / "coco.json"
        exporter.export_to_coco_json(annotations, coco_path)

        # Validate COCO
        assert exporter.validate_coco_json(coco_path)

        # Re-read and verify
        with open(coco_path) as f:
            coco_data = json.load(f)

        assert len(coco_data["images"]) == 1
        assert len(coco_data["annotations"]) == 1

    @pytest.mark.asyncio
    async def test_yolo_export_and_validate_roundtrip(self, tmp_path):
        """Test YOLO export -> validate roundtrip."""
        exporter = DatasetExporter()

        annotations = [
            {
                "id": 1,
                "data": {"image_url": "frame.jpg", "width": 1920, "height": 1080},
                "annotations": [
                    {
                        "result": [
                            {
                                "type": "rectanglelabels",
                                "value": {
                                    "x": 10,
                                    "y": 20,
                                    "width": 30,
                                    "height": 40,
                                },
                            }
                        ]
                    }
                ],
            }
        ]

        output_dir = tmp_path / "yolo"
        exporter.export_to_yolo_format(annotations, output_dir)

        # Validate
        assert exporter.validate_yolo_format(output_dir)

        # Verify file contents
        txt_file = output_dir / "frame.txt"
        with open(txt_file) as f:
            content = f.read().strip()

        parts = content.split()
        assert len(parts) == 5
        # All values should be between 0 and 1
        for i in range(1, 5):
            val = float(parts[i])
            assert 0 <= val <= 1

    @pytest.mark.asyncio
    async def test_streaming_server_detection_to_label_studio_mock(self):
        """Test detection upload flow with mocked Label Studio."""
        server = AnnotationStreamServer(
            label_studio_enabled=True,
            label_studio_api_key="test_key",
            label_studio_host="localhost",
            label_studio_port=8080,
        )

        # Mock the Label Studio client
        server.label_studio_client.upload_tasks = AsyncMock(
            return_value={"task_ids": [42]}
        )

        # Create test detections
        detections = [
            BBox(x=100, y=50, w=200, h=150, confidence=0.95),
            BBox(x=300, y=200, w=150, h=100, confidence=0.87),
        ]

        # Upload to Label Studio
        response = await server.upload_detections_to_label_studio(
            project_id=1,
            frame_id=1,
            image_url="s3://bucket/frame.jpg",
            image_width=1920,
            image_height=1080,
            detections=detections,
        )

        assert response["task_id"] == 42
        assert response["uploaded_count"] == 2
        assert response["frame_id"] == 1

        await server.close()

    @pytest.mark.asyncio
    async def test_full_workflow_config_optional(self):
        """Test that workflow works when Label Studio is optional (disabled)."""
        # This simulates a deployment where Label Studio is disabled
        server = AnnotationStreamServer(label_studio_enabled=False)

        # Even with Label Studio disabled, server should initialize
        assert server.label_studio_client is None

        # Operations should fail gracefully
        with pytest.raises(RuntimeError):
            await server.validate_label_studio()

        await server.close()

    @pytest.mark.asyncio
    async def test_bbox_format_conversion(self):
        """Test BBox serialization and deserialization."""
        # Create BBox
        original = BBox(x=100, y=50, w=200, h=150, confidence=0.95)

        # Serialize to dict
        bbox_dict = original.to_dict()
        assert bbox_dict["x"] == 100
        assert bbox_dict["y"] == 50
        assert bbox_dict["w"] == 200
        assert bbox_dict["h"] == 150
        assert bbox_dict["confidence"] == 0.95

        # Deserialize back
        restored = BBox.from_dict(bbox_dict)
        assert restored.x == original.x
        assert restored.y == original.y
        assert restored.w == original.w
        assert restored.h == original.h
        assert restored.confidence == original.confidence


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
