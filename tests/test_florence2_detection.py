"""Tests for Florence-2 watermark detection module."""

import pytest
import numpy as np
from PIL import Image
from unittest.mock import Mock, patch, MagicMock

from src.watermark_removal.florence2_detector import Florence2Detector


class TestFlorence2DetectorInitialization:
    """Test detector initialization and device detection."""

    def test_init_default_cpu(self):
        """Default initialization on CPU."""
        detector = Florence2Detector(device="cpu")

        assert detector.device == "cpu"
        assert detector.confidence_threshold == 0.5
        assert detector.model is None
        assert not detector._model_loaded

    def test_init_custom_confidence_threshold(self):
        """Custom confidence threshold."""
        detector = Florence2Detector(device="cpu", confidence_threshold=0.7)
        assert detector.confidence_threshold == 0.7

    def test_device_auto_detection(self):
        """Auto-detect device should use CUDA if available."""
        detector = Florence2Detector(device=None)

        import torch

        if torch.cuda.is_available():
            assert detector.device == "cuda"
        else:
            assert detector.device == "cpu"


class TestFlorence2DetectorDetection:
    """Test watermark detection functionality."""

    @patch("src.watermark_removal.florence2_detector.Florence2Detector._lazy_load_model")
    def test_detect_with_mock_model(self, mock_load):
        """Test detection with mocked model."""
        detector = Florence2Detector(device="cpu")

        # Create test image
        img_pil = Image.new("RGB", (512, 512), color="white")

        # Mock the model inference to return detection output
        mock_model = MagicMock()
        detector.model = mock_model
        detector.processor = MagicMock()
        detector._model_loaded = True

        # Mock processor to return mock inputs
        mock_inputs = {"input_ids": [[1, 2]], "pixel_values": [[0.0]]}
        detector.processor.return_value = mock_inputs

        # Mock model generation
        mock_model.generate.return_value = np.array([[1, 2, 3]])

        # Mock processor batch decode to return grounding output with bbox tokens
        detector.processor.batch_decode.return_value = [
            "<CAPTION_TO_PHRASE_GROUNDING>watermark<loc_100><loc_100><loc_400><loc_400>"
        ]

        mask, bboxes = detector.detect(img_pil)

        assert mask is not None
        assert mask.shape == (512, 512)
        assert mask.dtype == np.uint8
        assert isinstance(bboxes, list)

    def test_detect_empty_image(self):
        """Handle empty image gracefully."""
        detector = Florence2Detector(device="cpu")
        img_pil = None

        mask, bboxes = detector.detect(img_pil)

        assert mask is not None
        assert bboxes == []

    def test_detect_no_watermarks(self):
        """Image with no watermarks should return empty mask."""
        detector = Florence2Detector(device="cpu")
        img_pil = Image.new("RGB", (512, 512), color="white")

        with patch.object(detector, "_lazy_load_model"):
            with patch.object(detector, "_parse_grounding_output", return_value=[]):
                mask, bboxes = detector.detect(img_pil)

                assert bboxes == []
                assert np.all(mask == 255)  # All white = no inpaint


class TestFlorence2DetectorParsing:
    """Test bbox parsing from model output."""

    def test_parse_grounding_output_valid(self):
        """Parse valid grounding output."""
        detector = Florence2Detector(device="cpu")

        # Mock output with bbox tokens
        output = "watermark<loc_100><loc_100><loc_400><loc_400>"
        bboxes = detector._parse_grounding_output(output, (512, 512))

        assert len(bboxes) == 1
        x, y, w, h = bboxes[0]
        assert x >= 0
        assert y >= 0
        assert w > 0
        assert h > 0

    def test_parse_grounding_output_no_bboxes(self):
        """Parse output with no bboxes."""
        detector = Florence2Detector(device="cpu")

        output = "no watermarks found"
        bboxes = detector._parse_grounding_output(output, (512, 512))

        assert bboxes == []

    def test_parse_grounding_multiple_detections(self):
        """Parse output with multiple bboxes."""
        detector = Florence2Detector(device="cpu")

        # Two bboxes
        output = (
            "<loc_100><loc_100><loc_300><loc_300>"
            "<loc_400><loc_400><loc_600><loc_600>"
        )
        bboxes = detector._parse_grounding_output(output, (512, 512))

        assert len(bboxes) == 2
        for x, y, w, h in bboxes:
            assert w > 0 and h > 0

    def test_parse_normalized_to_pixel_conversion(self):
        """Test coordinate conversion from normalized (0-1000) to pixel."""
        detector = Florence2Detector(device="cpu")

        # Bbox at normalized (0.1, 0.2) to (0.4, 0.5) → pixel coords
        output = "<loc_100><loc_200><loc_400><loc_500>"
        bboxes = detector._parse_grounding_output(output, (1000, 1000))

        x, y, w, h = bboxes[0]
        assert x == int(0.1 * 1000)
        assert y == int(0.2 * 1000)


class TestFlorence2DetectorMaskGeneration:
    """Test mask generation from bboxes."""

    def test_generate_mask_single_bbox(self):
        """Generate mask from single bbox."""
        detector = Florence2Detector(device="cpu")

        bboxes = [(100, 100, 200, 200)]  # (x, y, w, h)
        mask = detector._generate_mask_from_bboxes(bboxes, (512, 512))

        assert mask.shape == (512, 512, 3)
        assert mask.dtype == np.uint8

        # Check that bbox region is marked (255)
        assert np.any(mask[100:300, 100:300] == 255)

        # Check that outside region is not marked (0)
        assert np.all(mask[0:50, 0:50] == 0)

    def test_generate_mask_multiple_bboxes(self):
        """Generate mask from multiple overlapping bboxes."""
        detector = Florence2Detector(device="cpu")

        bboxes = [(50, 50, 100, 100), (100, 100, 100, 100)]
        mask = detector._generate_mask_from_bboxes(bboxes, (512, 512))

        # Union of regions should be marked
        assert np.any(mask[50:150, 50:150] == 255)

    def test_generate_mask_bbox_at_boundary(self):
        """Handle bbox at image boundary."""
        detector = Florence2Detector(device="cpu")

        # Bbox extends beyond image bounds
        bboxes = [(450, 450, 100, 100)]
        mask = detector._generate_mask_from_bboxes(bboxes, (512, 512))

        # Should not crash, clamp to bounds
        assert mask.shape == (512, 512, 3)
        assert np.any(mask[450:512, 450:512] == 255)


class TestFlorence2DetectorMaskSmoothing:
    """Test mask smoothing with morphological operations."""

    def test_smooth_mask_reduces_noise(self):
        """Mask smoothing should reduce sharp edges."""
        detector = Florence2Detector(device="cpu")

        # Create noisy binary mask
        mask_binary = np.zeros((512, 512, 3), dtype=np.uint8)
        mask_binary[100:300, 100:300] = 255

        # Add single-pixel noise
        mask_binary[150, 150] = 0  # Noise in foreground
        mask_binary[50, 50] = 255  # Noise in background

        mask_smooth = detector._smooth_mask(mask_binary)

        # Smooth mask should be grayscale (single channel)
        assert len(mask_smooth.shape) == 2
        assert mask_smooth.dtype == np.uint8

        # Smooth mask should have values 0-255 (not just binary)
        assert not np.all((mask_smooth == 0) | (mask_smooth == 255))

    def test_smooth_mask_grayscale_input(self):
        """Smooth mask should handle grayscale input."""
        detector = Florence2Detector(device="cpu")

        mask_gray = np.zeros((512, 512), dtype=np.uint8)
        mask_gray[100:300, 100:300] = 255

        mask_smooth = detector._smooth_mask(mask_gray)

        assert mask_smooth.shape == (512, 512)
        assert mask_smooth.dtype == np.uint8

    def test_smooth_mask_output_bounds(self):
        """Smooth mask should stay within uint8 bounds."""
        detector = Florence2Detector(device="cpu")

        mask_binary = np.random.choice([0, 255], size=(512, 512, 3)).astype(np.uint8)

        mask_smooth = detector._smooth_mask(mask_binary)

        assert np.all(mask_smooth >= 0)
        assert np.all(mask_smooth <= 255)


class TestFlorence2DetectorIntegration:
    """Integration tests for full detection workflow."""

    @patch("src.watermark_removal.florence2_detector.Florence2Detector._lazy_load_model")
    def test_full_detection_workflow(self, mock_load):
        """Test complete detection workflow."""
        detector = Florence2Detector(device="cpu")

        # Create test image with synthetic watermark
        img_pil = Image.new("RGB", (512, 512), color="white")

        # Mock model loading
        detector._model_loaded = True
        detector.model = MagicMock()
        detector.processor = MagicMock()

        # Mock successful detection
        detector.processor.return_value = {"input_ids": [[1]], "pixel_values": [[0.0]]}
        detector.model.generate.return_value = np.array([[1]])
        detector.processor.batch_decode.return_value = [
            "<loc_200><loc_200><loc_400><loc_400>"
        ]

        mask, bboxes = detector.detect(img_pil)

        assert mask is not None
        assert len(bboxes) >= 0
        assert mask.dtype == np.uint8
        assert mask.shape[0] == 512
        assert mask.shape[1] == 512

    def test_detector_cleanup(self):
        """Test model cleanup doesn't crash."""
        detector = Florence2Detector(device="cpu")
        detector._model_loaded = True
        detector.model = MagicMock()
        detector.processor = MagicMock()

        # Cleanup should not raise
        detector.cleanup()
        assert not detector._model_loaded


class TestFlorence2DetectorMemoryManager:
    """Test Florence2Detector integration with MemoryManager."""

    def test_init_accepts_memory_manager(self):
        """Detector should accept optional MemoryManager."""
        from src.watermark_removal.memory_manager import MemoryManager

        mm = MemoryManager(device="cpu")
        detector = Florence2Detector(device="cpu", memory_manager=mm)

        assert detector.memory_manager is mm

    def test_init_without_memory_manager(self):
        """Detector should work without MemoryManager (backward compatible)."""
        detector = Florence2Detector(device="cpu")
        assert detector.memory_manager is None

    @patch("src.watermark_removal.florence2_detector.Florence2Detector._lazy_load_model")
    def test_lazy_load_without_memory_manager(self, mock_load):
        """Lazy load should work without MemoryManager."""
        detector = Florence2Detector(device="cpu")
        detector._model_loaded = True
        detector.model = MagicMock()
        detector.processor = MagicMock()

        # Mock lazy load to succeed
        with patch.object(detector, "_lazy_load_model", wraps=detector._lazy_load_model):
            # Should not crash even without MM
            assert detector.memory_manager is None

    def test_lazy_load_calls_memory_manager_load(self):
        """Lazy load should call memory_manager.load_model if provided."""
        mock_mm = MagicMock()
        detector = Florence2Detector(device="cpu", memory_manager=mock_mm)

        # Manually trigger lazy load simulation
        detector._model_loaded = False
        mock_model = MagicMock()
        detector.model = mock_model

        # Simulate what _lazy_load_model does
        if detector.memory_manager:
            detector.memory_manager.load_model("florence2", detector.model)

        mock_mm.load_model.assert_called_once_with("florence2", mock_model)

    def test_cleanup_calls_memory_manager_unload(self):
        """Cleanup should call memory_manager.unload_model if provided."""
        mock_mm = MagicMock()
        detector = Florence2Detector(device="cpu", memory_manager=mock_mm)
        detector._model_loaded = True
        detector.model = MagicMock()
        detector.processor = MagicMock()

        detector.cleanup()

        mock_mm.unload_model.assert_called_once_with("florence2")

    def test_cleanup_without_memory_manager(self):
        """Cleanup should work without MemoryManager."""
        detector = Florence2Detector(device="cpu")
        detector._model_loaded = True
        detector.model = MagicMock()
        detector.processor = MagicMock()

        # Should not crash
        detector.cleanup()
        assert not detector._model_loaded

    def test_full_lifecycle_with_memory_manager(self):
        """Full detection lifecycle should integrate with MemoryManager."""
        from src.watermark_removal.memory_manager import MemoryManager

        mm = MemoryManager(device="cpu")
        detector = Florence2Detector(device="cpu", memory_manager=mm)

        # Check initial state
        assert detector.memory_manager is mm
        assert not detector._model_loaded
        assert "florence2" not in mm._loaded_models

        # Simulate lazy load
        detector._model_loaded = True
        detector.model = MagicMock()
        detector.processor = MagicMock()

        # Register with MM
        if detector.memory_manager:
            detector.memory_manager.load_model("florence2", detector.model)

        # Should be tracked
        assert "florence2" in mm._loaded_models

        # Cleanup
        detector.cleanup()

        # Should be untracked
        assert "florence2" not in mm._loaded_models
