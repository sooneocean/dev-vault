"""Detection orchestrator that switches between single and ensemble modes."""

import logging
from typing import Optional

import numpy as np

from .ensemble_detector import EnsembleDetector
from .watermark_detector import BBox, WatermarkDetector

logger = logging.getLogger(__name__)


class DetectionOrchestrator:
    """Orchestrates watermark detection with support for single and ensemble modes."""

    def __init__(
        self,
        ensemble_detection_enabled: bool = False,
        ensemble_models: Optional[list[str]] = None,
        ensemble_voting_mode: str = "confidence_weighted",
        ensemble_iou_threshold: float = 0.3,
        ensemble_nms_threshold: float = 0.45,
        ensemble_model_accuracies: Optional[dict[str, float]] = None,
        single_model: str = "yolov5s",
        single_model_confidence_threshold: float = 0.5,
        single_model_nms_threshold: float = 0.45,
    ) -> None:
        """
        Initialize detection orchestrator.

        Args:
            ensemble_detection_enabled: Enable ensemble mode.
            ensemble_models: List of model names for ensemble (e.g., ["yolov5s", "yolov5m"]).
            ensemble_voting_mode: Voting strategy ("confidence_weighted" only in MVP).
            ensemble_iou_threshold: Minimum IoU for matching detections across models.
            ensemble_nms_threshold: NMS threshold for ensemble post-processing.
            ensemble_model_accuracies: Baseline accuracies for each model (for weighting).
            single_model: Model name for single-mode (default "yolov5s").
            single_model_confidence_threshold: Confidence threshold for single mode.
            single_model_nms_threshold: NMS threshold for single mode.
        """
        self.ensemble_detection_enabled = ensemble_detection_enabled
        self.ensemble_models = ensemble_models or ["yolov5s", "yolov5m"]
        self.ensemble_voting_mode = ensemble_voting_mode
        self.ensemble_iou_threshold = ensemble_iou_threshold
        self.ensemble_nms_threshold = ensemble_nms_threshold
        self.ensemble_model_accuracies = ensemble_model_accuracies or {
            "yolov5s": 0.85,
            "yolov5m": 0.90,
            "yolov5l": 0.92,
        }
        self.single_model = single_model
        self.single_model_confidence_threshold = single_model_confidence_threshold
        self.single_model_nms_threshold = single_model_nms_threshold

        self._detector: Optional[WatermarkDetector | EnsembleDetector] = None
        self._detector_loaded = False

    def _lazy_load_detector(self) -> None:
        """Lazily load detector (single or ensemble) on first use."""
        if self._detector_loaded:
            return

        try:
            if self.ensemble_detection_enabled:
                logger.info(f"Initializing ensemble detector with models: {self.ensemble_models}")
                # Create model configs with confidence thresholds
                model_configs = [
                    (model_name, {"confidence_threshold": self.single_model_confidence_threshold})
                    for model_name in self.ensemble_models
                ]
                self._detector = EnsembleDetector(
                    model_configs=model_configs,
                    model_accuracies=self.ensemble_model_accuracies,
                    iou_threshold=self.ensemble_iou_threshold,
                    nms_threshold=self.ensemble_nms_threshold,
                )
            else:
                logger.info(f"Initializing single detector: {self.single_model}")
                self._detector = WatermarkDetector(
                    model_name=self.single_model,
                    confidence_threshold=self.single_model_confidence_threshold,
                    nms_threshold=self.single_model_nms_threshold,
                )
            self._detector_loaded = True
        except Exception as e:
            logger.error(f"Failed to load detector: {e}")
            raise RuntimeError(
                f"Failed to initialize watermark detector: {e}. "
                f"Check that required models are available and yolov5 is installed."
            ) from e

    def detect_frame(self, frame: np.ndarray) -> list[BBox]:
        """
        Detect watermarks in a single frame.

        Args:
            frame: Video frame (HxWx3, BGR, uint8).

        Returns:
            List of detected bounding boxes (empty if no detections).
        """
        if frame is None or frame.size == 0:
            return []

        try:
            self._lazy_load_detector()
            if self._detector is None:
                return []
            return self._detector.detect_frame(frame)
        except Exception as e:
            logger.warning(f"Detection failed: {e}")
            return []

    def detect_frames(self, frames: list[np.ndarray]) -> dict[int, list[BBox]]:
        """
        Detect watermarks in multiple frames.

        Args:
            frames: List of video frames (HxWx3, BGR, uint8).

        Returns:
            Dictionary mapping frame index to list of detected bboxes.
        """
        try:
            self._lazy_load_detector()
            if self._detector is None:
                return {}
            return self._detector.detect_frames(frames)
        except Exception as e:
            logger.warning(f"Batch detection failed: {e}")
            return {}

    def get_detector_status(self) -> dict:
        """
        Get status of loaded detector(s).

        Returns:
            Dictionary with detector status information.
        """
        try:
            self._lazy_load_detector()
            if self._detector is None:
                return {"status": "not_loaded"}

            if self.ensemble_detection_enabled and isinstance(self._detector, EnsembleDetector):
                return {
                    "mode": "ensemble",
                    "models": self.ensemble_models,
                    "model_status": self._detector.get_detector_status(),
                }
            else:
                return {
                    "mode": "single",
                    "model": self.single_model,
                    "loaded": self._detector_loaded,
                }
        except Exception as e:
            logger.warning(f"Failed to get detector status: {e}")
            return {"status": "error", "error": str(e)}
