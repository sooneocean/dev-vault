"""Automatic watermark detection using YOLOv5."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np


@dataclass
class BBox:
    """Bounding box for detected watermark region."""

    x: int
    """Left edge in pixels."""

    y: int
    """Top edge in pixels."""

    w: int
    """Width in pixels."""

    h: int
    """Height in pixels."""

    confidence: float
    """Detection confidence score (0.0-1.0)."""

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {"x": self.x, "y": self.y, "w": self.w, "h": self.h, "confidence": self.confidence}

    @staticmethod
    def from_dict(d: dict) -> "BBox":
        """Create from dictionary."""
        return BBox(
            x=int(d["x"]),
            y=int(d["y"]),
            w=int(d["w"]),
            h=int(d["h"]),
            confidence=float(d.get("confidence", 1.0)),
        )


class WatermarkDetector:
    """Detect watermark regions in video frames using YOLOv5."""

    def __init__(
        self,
        model_name: str = "yolov5s",
        confidence_threshold: float = 0.5,
        nms_threshold: float = 0.45,
    ) -> None:
        """
        Initialize watermark detector.

        Args:
            model_name: YOLOv5 model variant ("yolov5s", "yolov5m", "yolov5l").
            confidence_threshold: Confidence threshold for detections (0.0-1.0).
            nms_threshold: NMS suppression threshold (0.0-1.0).
        """
        if not (0.0 <= confidence_threshold <= 1.0):
            raise ValueError("confidence_threshold must be 0.0-1.0")
        if not (0.0 <= nms_threshold <= 1.0):
            raise ValueError("nms_threshold must be 0.0-1.0")

        self.model_name = model_name
        self.confidence_threshold = confidence_threshold
        self.nms_threshold = nms_threshold
        self.model = None
        self._model_loaded = False

    def _lazy_load_model(self) -> None:
        """Lazily load YOLOv5 model (only when first needed)."""
        if self._model_loaded:
            return

        try:
            import yolov5

            # Load model from path or pretrained name
            self.model = yolov5.load(self.model_name, device="cpu")
            # Set inference parameters
            self.model.conf = self.confidence_threshold
            self.model.iou = self.nms_threshold
            self._model_loaded = True
        except ImportError:
            raise RuntimeError("yolov5 is not installed. Install with: pip install yolov5")
        except Exception as e:
            raise RuntimeError(f"Failed to load YOLOv5 model '{self.model_name}': {e}")

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
            self._lazy_load_model()

            # YOLOv5 expects BGR or RGB. Convert to RGB for inference.
            frame_rgb = frame[..., ::-1]  # BGR -> RGB

            # Run inference
            results = self.model(frame_rgb, size=640)

            # Extract detections
            detections = results.pred[0].cpu().numpy()  # [N, 6] array: [x1, y1, x2, y2, conf, class]
            bboxes = []

            for det in detections:
                x1, y1, x2, y2, conf, cls_id = det

                # Convert from (x1, y1, x2, y2) to (x, y, w, h)
                x = int(x1)
                y = int(y1)
                w = int(x2 - x1)
                h = int(y2 - y1)
                confidence = float(conf)

                bbox = BBox(x=x, y=y, w=w, h=h, confidence=confidence)
                bboxes.append(bbox)

            return bboxes

        except Exception as e:
            # Graceful fallback: return empty list on detection failure
            return []

    def detect_frames(self, frames: list[np.ndarray]) -> dict[int, list[BBox]]:
        """
        Detect watermarks in multiple frames.

        Args:
            frames: List of video frames (HxWx3, BGR, uint8).

        Returns:
            Dictionary mapping frame index to list of detected bboxes.
        """
        results = {}
        for frame_idx, frame in enumerate(frames):
            bboxes = self.detect_frame(frame)
            if bboxes:  # Only include frames with detections
                results[frame_idx] = bboxes

        return results

    def get_largest_bbox(self, bboxes: list[BBox]) -> Optional[BBox]:
        """
        Select the largest bounding box by area.

        Args:
            bboxes: List of detected bboxes.

        Returns:
            Largest bbox, or None if list is empty.
        """
        if not bboxes:
            return None

        return max(bboxes, key=lambda b: b.w * b.h)

    def filter_by_area(self, bboxes: list[BBox], min_area: int = 100) -> list[BBox]:
        """
        Filter bboxes by minimum area.

        Args:
            bboxes: List of detected bboxes.
            min_area: Minimum area in pixels.

        Returns:
            Filtered list of bboxes.
        """
        return [b for b in bboxes if b.w * b.h >= min_area]

    def filter_by_confidence(self, bboxes: list[BBox], min_confidence: float) -> list[BBox]:
        """
        Filter bboxes by minimum confidence.

        Args:
            bboxes: List of detected bboxes.
            min_confidence: Minimum confidence threshold.

        Returns:
            Filtered list of bboxes.
        """
        return [b for b in bboxes if b.confidence >= min_confidence]
