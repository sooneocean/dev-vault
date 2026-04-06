"""
YOLO-based automatic watermark detection.

Detects watermark bounding boxes in video frames using YOLOv8.
Supports lazy model loading and batch inference.
"""

import logging
import numpy as np
from typing import List, Tuple, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class YOLODetector:
    """
    Automatic watermark detection using YOLOv8.

    Supports multiple model sizes (nano, small, medium, large) with lazy loading.
    Provides single-frame and batch inference interfaces.
    """

    # Model size to official checkpoint mapping
    MODEL_SIZES = {
        "nano": "yolov8n.pt",
        "small": "yolov8s.pt",
        "medium": "yolov8m.pt",
        "large": "yolov8l.pt",
    }

    def __init__(
        self,
        model_size: str = "small",
        confidence_threshold: float = 0.5,
        nms_threshold: float = 0.45,
        device: str = "cuda",
    ):
        """
        Initialize YOLO detector with lazy loading.

        Args:
            model_size: Model size (nano/small/medium/large)
            confidence_threshold: Confidence threshold for detections [0.0, 1.0]
            nms_threshold: NMS threshold for post-processing [0.0, 1.0]
            device: Device for inference (cuda, cpu, etc.)

        Raises:
            ValueError: If model_size not supported
        """
        if model_size not in self.MODEL_SIZES:
            raise ValueError(
                f"model_size must be one of {list(self.MODEL_SIZES.keys())}, got {model_size}"
            )

        if not 0.0 <= confidence_threshold <= 1.0:
            raise ValueError(
                f"confidence_threshold must be in [0.0, 1.0], got {confidence_threshold}"
            )

        if not 0.0 <= nms_threshold <= 1.0:
            raise ValueError(f"nms_threshold must be in [0.0, 1.0], got {nms_threshold}")

        self.model_size = model_size
        self.confidence_threshold = confidence_threshold
        self.nms_threshold = nms_threshold
        self.device = device
        self.model = None  # Lazy loaded

    def _load_model(self) -> None:
        """Load YOLO model lazily (only when needed)."""
        if self.model is not None:
            return  # Already loaded

        try:
            from ultralytics import YOLO

            checkpoint = self.MODEL_SIZES[self.model_size]
            logger.info(
                f"Loading YOLO model: {checkpoint} (size={self.model_size}) on {self.device}"
            )

            self.model = YOLO(checkpoint)
            self.model.to(self.device)

            logger.info(f"YOLO model loaded successfully")
        except ImportError:
            logger.error("ultralytics not installed. Install: pip install ultralytics")
            raise RuntimeError(
                "YOLOv8 detection requires ultralytics. Install: pip install ultralytics"
            )
        except Exception as e:
            logger.error(f"Failed to load YOLO model: {e}")
            raise RuntimeError(f"Failed to load YOLO model: {e}")

    def detect(self, image: np.ndarray) -> List[Tuple[float, float, float, float]]:
        """
        Detect watermark bounding boxes in a single frame.

        Args:
            image: BGR ndarray (H, W, 3), uint8

        Returns:
            List of (x, y, w, h) bounding boxes detected
        """
        if self.model is None:
            self._load_model()

        try:
            # Run inference with confidence threshold
            results = self.model(
                image, conf=self.confidence_threshold, verbose=False
            )

            bboxes = []
            for result in results:
                for box in result.boxes:
                    # Extract bbox in (x, y, w, h) format from xyxy
                    xyxy = box.xyxy[0]
                    x1, y1, x2, y2 = (
                        float(xyxy[0]),
                        float(xyxy[1]),
                        float(xyxy[2]),
                        float(xyxy[3]),
                    )
                    x, y = x1, y1
                    w, h = x2 - x1, y2 - y1
                    confidence = float(box.conf[0]) if box.conf is not None else 0.9

                    bboxes.append((x, y, w, h, confidence))

            # Sort by confidence descending
            bboxes.sort(key=lambda b: b[4], reverse=True)

            # Remove confidence value from returned bboxes (kept separate for NMS)
            return [(x, y, w, h) for x, y, w, h, _ in bboxes]

        except Exception as e:
            logger.error(f"YOLO inference failed: {e}")
            return []

    def detect_batch(
        self, images: List[np.ndarray]
    ) -> List[List[Tuple[float, float, float, float]]]:
        """
        Detect watermarks in multiple frames.

        Args:
            images: List of BGR ndarrays (H, W, 3), uint8

        Returns:
            List of bboxes lists, one per image
        """
        if self.model is None:
            self._load_model()

        try:
            results = self.model(images, conf=self.confidence_threshold, verbose=False)

            all_bboxes = []
            for result in results:
                bboxes = []
                for box in result.boxes:
                    xyxy = box.xyxy[0]
                    x1, y1, x2, y2 = (
                        float(xyxy[0]),
                        float(xyxy[1]),
                        float(xyxy[2]),
                        float(xyxy[3]),
                    )
                    x, y = x1, y1
                    w, h = x2 - x1, y2 - y1
                    bboxes.append((x, y, w, h))

                all_bboxes.append(bboxes)

            return all_bboxes

        except Exception as e:
            logger.error(f"YOLO batch inference failed: {e}")
            return [[] for _ in images]

    def detect_with_confidence(
        self, image: np.ndarray
    ) -> List[Tuple[float, float, float, float, float]]:
        """
        Detect watermarks with confidence scores.

        Args:
            image: BGR ndarray (H, W, 3), uint8

        Returns:
            List of (x, y, w, h, confidence) tuples
        """
        if self.model is None:
            self._load_model()

        try:
            results = self.model(
                image, conf=self.confidence_threshold, verbose=False
            )

            bboxes_with_conf = []
            for result in results:
                for box in result.boxes:
                    xyxy = box.xyxy[0]
                    x1, y1, x2, y2 = (
                        float(xyxy[0]),
                        float(xyxy[1]),
                        float(xyxy[2]),
                        float(xyxy[3]),
                    )
                    x, y = x1, y1
                    w, h = x2 - x1, y2 - y1
                    confidence = float(box.conf[0]) if box.conf is not None else 0.9

                    bboxes_with_conf.append((x, y, w, h, confidence))

            # Sort by confidence descending
            bboxes_with_conf.sort(key=lambda b: b[4], reverse=True)
            return bboxes_with_conf

        except Exception as e:
            logger.error(f"YOLO inference failed: {e}")
            return []

    def apply_nms(
        self, bboxes: List[Tuple[float, float, float, float, float]]
    ) -> List[Tuple[float, float, float, float, float]]:
        """
        Apply Non-Maximum Suppression to remove overlapping detections.

        Args:
            bboxes: List of (x, y, w, h, confidence) tuples

        Returns:
            Filtered list after NMS
        """
        if not bboxes:
            return []

        if len(bboxes) == 1:
            return bboxes

        try:
            import cv2

            # Convert (x, y, w, h) to (x1, y1, x2, y2) for NMS
            boxes_xyxy = []
            confidences = []
            for x, y, w, h, conf in bboxes:
                boxes_xyxy.append([x, y, x + w, y + h])
                confidences.append(conf)

            # Use OpenCV NMS
            indices = cv2.dnn.NMSBoxes(
                boxes_xyxy, confidences, self.confidence_threshold, self.nms_threshold
            )

            # Return filtered bboxes
            if len(indices) > 0:
                indices = indices.flatten()
                return [bboxes[i] for i in indices]
            else:
                return []

        except Exception as e:
            logger.warning(f"NMS failed, returning all bboxes: {e}")
            return bboxes

    def cleanup(self) -> None:
        """Release model resources."""
        if self.model is not None:
            try:
                # Clear CUDA cache if using GPU
                import torch

                torch.cuda.empty_cache()
                logger.info("Cleaned up YOLO model resources")
            except Exception as e:
                logger.warning(f"Failed to cleanup YOLO resources: {e}")
            finally:
                self.model = None
