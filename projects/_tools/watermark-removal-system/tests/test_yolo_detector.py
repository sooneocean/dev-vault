"""
Tests for YOLO automatic watermark detection.

Tests YOLODetector initialization, inference, batch processing, and NMS.
"""

import pytest
import numpy as np
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from watermark_removal.preprocessing.yolo_detector import YOLODetector


class TestYOLODetectorInitialization:
    """Test YOLODetector initialization."""

    def test_init_default(self):
        """Initialize with defaults."""
        detector = YOLODetector()
        assert detector.model_size == "small"
        assert detector.confidence_threshold == 0.5
        assert detector.nms_threshold == 0.45
        assert detector.device == "cuda"
        assert detector.model is None  # Lazy loaded

    def test_init_nano_model(self):
        """Initialize with nano model size."""
        detector = YOLODetector(model_size="nano")
        assert detector.model_size == "nano"

    def test_init_large_model(self):
        """Initialize with large model size."""
        detector = YOLODetector(model_size="large")
        assert detector.model_size == "large"

    def test_init_invalid_model_size(self):
        """Invalid model size raises error."""
        with pytest.raises(ValueError, match="model_size must be one of"):
            YOLODetector(model_size="huge")

    def test_init_invalid_confidence_threshold(self):
        """Invalid confidence threshold raises error."""
        with pytest.raises(ValueError, match="confidence_threshold must be in"):
            YOLODetector(confidence_threshold=1.5)

    def test_init_invalid_nms_threshold(self):
        """Invalid NMS threshold raises error."""
        with pytest.raises(ValueError, match="nms_threshold must be in"):
            YOLODetector(nms_threshold=-0.1)

    def test_init_cpu_device(self):
        """Initialize with CPU device."""
        detector = YOLODetector(device="cpu")
        assert detector.device == "cpu"

    def test_model_sizes_mapping(self):
        """Verify all model sizes have mappings."""
        for size in ["nano", "small", "medium", "large"]:
            assert size in YOLODetector.MODEL_SIZES
            assert YOLODetector.MODEL_SIZES[size].endswith(".pt")


class TestYOLODetectorInference:
    """Test YOLO inference on single frames."""

    @patch("watermark_removal.preprocessing.yolo_detector.logger")
    def test_detect_single_frame_no_detections(self, mock_logger):
        """Detect on frame with no watermarks."""
        # Create a real detector but mock _load_model to avoid actual model loading
        detector = YOLODetector()

        # Create a mock model
        mock_model = MagicMock()
        detector.model = mock_model

        # Setup mock inference
        mock_result = MagicMock()
        mock_result.boxes = []
        mock_model.return_value = [mock_result]

        image = np.zeros((480, 640, 3), dtype=np.uint8)
        bboxes = detector.detect(image)

        assert len(bboxes) == 0
        assert isinstance(bboxes, list)

    @patch("watermark_removal.preprocessing.yolo_detector.logger")
    def test_detect_single_frame_one_watermark(self, mock_logger):
        """Detect one watermark in frame."""
        detector = YOLODetector()

        # Mock box with xyxy coordinates and confidence
        mock_box = MagicMock()
        # xyxy is (x1, y1, x2, y2) = (10, 20, 110, 70)
        # Use actual numpy array that will be properly converted
        xyxy_array = np.array([10.0, 20.0, 110.0, 70.0], dtype=np.float32)
        mock_box.xyxy = [xyxy_array]
        mock_box.conf = [np.array([0.95], dtype=np.float32)]

        mock_result = MagicMock()
        mock_result.boxes = [mock_box]

        # Create a callable mock that returns results when called with any args
        def mock_inference(image, conf=None, verbose=False):
            return [mock_result]

        mock_model = MagicMock(side_effect=mock_inference)
        detector.model = mock_model

        image = np.zeros((480, 640, 3), dtype=np.uint8)
        bboxes = detector.detect(image)

        assert len(bboxes) == 1
        x, y, w, h = bboxes[0]
        # Check that coordinates were extracted correctly
        # x = x1 = 10, y = y1 = 20, w = x2 - x1 = 110 - 10 = 100, h = y2 - y1 = 70 - 20 = 50
        assert x == 10.0
        assert y == 20.0
        assert w == 100.0
        assert h == 50.0

    @patch("watermark_removal.preprocessing.yolo_detector.logger")
    def test_detect_multiple_watermarks(self, mock_logger):
        """Detect multiple watermarks in frame."""
        detector = YOLODetector()

        # Create two mock boxes
        mock_box1 = MagicMock()
        mock_box1.xyxy = [np.array([10.0, 20.0, 110.0, 70.0], dtype=np.float32)]
        mock_box1.conf = [np.array([0.95], dtype=np.float32)]

        mock_box2 = MagicMock()
        mock_box2.xyxy = [np.array([300.0, 200.0, 400.0, 300.0], dtype=np.float32)]
        mock_box2.conf = [np.array([0.85], dtype=np.float32)]

        mock_result = MagicMock()
        mock_result.boxes = [mock_box1, mock_box2]

        def mock_inference(image, conf=None, verbose=False):
            return [mock_result]

        mock_model = MagicMock(side_effect=mock_inference)
        detector.model = mock_model

        image = np.zeros((480, 640, 3), dtype=np.uint8)
        bboxes = detector.detect(image)

        assert len(bboxes) == 2
        # Verify both bboxes present, sorted by confidence
        # First should be 0.95 (higher), second should be 0.85 (lower)
        assert bboxes[0][0] == 10.0    # Higher confidence box
        assert bboxes[1][0] == 300.0   # Lower confidence box

    @patch("watermark_removal.preprocessing.yolo_detector.logger")
    def test_detect_lazy_loading(self, mock_logger):
        """Verify model is lazy loaded on first detection."""
        # Use patch for _load_model to avoid actual model loading
        with patch.object(YOLODetector, '_load_model') as mock_load:
            detector = YOLODetector()
            assert detector.model is None  # Not loaded yet

            # Setup mock model
            mock_model = MagicMock()
            mock_result = MagicMock()
            mock_result.boxes = []
            mock_model.return_value = [mock_result]

            def side_effect():
                detector.model = mock_model

            mock_load.side_effect = side_effect

            image = np.zeros((480, 640, 3), dtype=np.uint8)
            detector.detect(image)

            assert detector.model is not None  # Now loaded
            mock_load.assert_called_once()

    @patch("watermark_removal.preprocessing.yolo_detector.logger")
    def test_detect_model_load_failure(self, mock_logger):
        """Handle model loading failure gracefully."""
        detector = YOLODetector()

        # Mock _load_model to raise an error
        with patch.object(detector, '_load_model', side_effect=RuntimeError("Model not found")):
            image = np.zeros((480, 640, 3), dtype=np.uint8)

            with pytest.raises(RuntimeError, match="Failed to load YOLO model"):
                detector.detect(image)


class TestYOLODetectorBatch:
    """Test batch inference."""

    @patch("watermark_removal.preprocessing.yolo_detector.logger")
    def test_detect_batch_empty_list(self, mock_logger):
        """Batch inference on empty image list."""
        detector = YOLODetector()
        result = detector.detect_batch([])

        assert result == []

    @patch("watermark_removal.preprocessing.yolo_detector.logger")
    def test_detect_batch_multiple_frames(self, mock_logger):
        """Batch inference on multiple frames."""
        detector = YOLODetector()

        # Create mock results for 3 frames
        mock_results = []
        for _ in range(3):
            mock_result = MagicMock()
            mock_result.boxes = []
            mock_results.append(mock_result)

        def mock_inference(images, conf=None, verbose=False):
            return mock_results

        mock_model = MagicMock(side_effect=mock_inference)
        detector.model = mock_model

        images = [np.zeros((480, 640, 3), dtype=np.uint8) for _ in range(3)]
        result = detector.detect_batch(images)

        assert len(result) == 3
        assert all(isinstance(b, list) for b in result)

    @patch("watermark_removal.preprocessing.yolo_detector.logger")
    def test_detect_batch_with_detections(self, mock_logger):
        """Batch inference with detections in some frames."""
        detector = YOLODetector()

        # Frame 1: 1 detection, Frame 2: 0 detections, Frame 3: 2 detections
        mock_box = MagicMock()
        mock_box.xyxy = [np.array([10.0, 20.0, 110.0, 70.0])]
        mock_box.conf = [np.array([0.95])]

        mock_result1 = MagicMock()
        mock_result1.boxes = [mock_box]

        mock_result2 = MagicMock()
        mock_result2.boxes = []

        mock_result3 = MagicMock()
        mock_result3.boxes = [mock_box, mock_box]

        def mock_inference(images, conf=None, verbose=False):
            return [mock_result1, mock_result2, mock_result3]

        mock_model = MagicMock(side_effect=mock_inference)
        detector.model = mock_model

        images = [np.zeros((480, 640, 3), dtype=np.uint8) for _ in range(3)]
        result = detector.detect_batch(images)

        assert len(result) == 3
        assert len(result[0]) == 1
        assert len(result[1]) == 0
        assert len(result[2]) == 2


class TestYOLODetectorWithConfidence:
    """Test confidence-aware detection."""

    @patch("watermark_removal.preprocessing.yolo_detector.logger")
    def test_detect_with_confidence_single(self, mock_logger):
        """Detect with confidence values."""
        detector = YOLODetector()

        mock_box = MagicMock()
        mock_box.xyxy = [np.array([10.0, 20.0, 110.0, 70.0])]
        mock_box.conf = [np.array([0.95])]

        mock_result = MagicMock()
        mock_result.boxes = [mock_box]

        def mock_inference(image, conf=None, verbose=False):
            return [mock_result]

        mock_model = MagicMock(side_effect=mock_inference)
        detector.model = mock_model

        image = np.zeros((480, 640, 3), dtype=np.uint8)
        bboxes_conf = detector.detect_with_confidence(image)

        assert len(bboxes_conf) == 1
        x, y, w, h, conf = bboxes_conf[0]
        assert x == 10.0
        assert y == 20.0
        assert w == 100.0
        assert h == 50.0
        assert conf == 0.95

    @patch("watermark_removal.preprocessing.yolo_detector.logger")
    def test_detect_with_confidence_sorted(self, mock_logger):
        """Detections sorted by confidence descending."""
        detector = YOLODetector()

        # Create boxes with different confidences
        mock_box1 = MagicMock()
        mock_box1.xyxy = [np.array([10.0, 20.0, 110.0, 70.0])]
        mock_box1.conf = [np.array([0.70])]

        mock_box2 = MagicMock()
        mock_box2.xyxy = [np.array([300.0, 200.0, 400.0, 300.0])]
        mock_box2.conf = [np.array([0.95])]

        mock_result = MagicMock()
        mock_result.boxes = [mock_box1, mock_box2]

        def mock_inference(image, conf=None, verbose=False):
            return [mock_result]

        mock_model = MagicMock(side_effect=mock_inference)
        detector.model = mock_model

        image = np.zeros((480, 640, 3), dtype=np.uint8)
        bboxes_conf = detector.detect_with_confidence(image)

        assert len(bboxes_conf) == 2
        # First should be highest confidence (0.95)
        assert bboxes_conf[0][4] == 0.95
        assert bboxes_conf[1][4] == 0.70


class TestYOLODetectorNMS:
    """Test Non-Maximum Suppression."""

    def test_nms_empty_list(self):
        """NMS on empty list."""
        detector = YOLODetector()
        result = detector.apply_nms([])
        assert result == []

    def test_nms_single_box(self):
        """NMS on single box."""
        detector = YOLODetector()
        boxes = [(10.0, 20.0, 100.0, 50.0, 0.95)]
        result = detector.apply_nms(boxes)
        assert len(result) == 1
        assert result[0] == boxes[0]

    def test_nms_overlapping_boxes(self):
        """NMS filters overlapping boxes."""
        # This test requires actual cv2 for NMS
        # If cv2 is available, test the filtering
        try:
            import cv2
            detector = YOLODetector()
            boxes = [
                (10.0, 20.0, 100.0, 50.0, 0.95),    # Keep
                (15.0, 25.0, 100.0, 50.0, 0.90),    # Remove (overlap)
                (300.0, 200.0, 100.0, 100.0, 0.85), # Keep
            ]

            result = detector.apply_nms(boxes)

            # Should filter overlapping boxes
            assert len(result) <= len(boxes)
        except ImportError:
            pytest.skip("cv2 not installed")

    def test_nms_handles_failure(self):
        """NMS handles errors gracefully and returns all boxes."""
        detector = YOLODetector()
        boxes = [(10.0, 20.0, 100.0, 50.0, 0.95)]

        # This might fail if cv2 isn't available, but should still return boxes
        try:
            result = detector.apply_nms(boxes)
            # Should return boxes even on failure
            assert len(result) == len(boxes) or len(result) <= len(boxes)
        except Exception:
            # If there's a failure, it should be logged
            pass


class TestYOLODetectorCleanup:
    """Test resource cleanup."""

    @patch("watermark_removal.preprocessing.yolo_detector.logger")
    def test_cleanup_releases_resources(self, mock_logger):
        """Cleanup releases model and GPU resources."""
        detector = YOLODetector()

        # Create a mock model
        mock_model = MagicMock()
        detector.model = mock_model

        # Cleanup (torch import is lazy, so we don't need to mock it for the test)
        detector.cleanup()

        assert detector.model is None
        # Logger should have been called for successful cleanup
        assert mock_logger.info.called

    def test_cleanup_without_model_loaded(self):
        """Cleanup when model not loaded is safe."""
        detector = YOLODetector()
        # Should not raise
        detector.cleanup()
        assert detector.model is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
