"""Multi-model ensemble detection."""

import logging
from dataclasses import dataclass
from typing import Optional
import numpy as np
from .watermark_detector import BBox, WatermarkDetector

logger = logging.getLogger(__name__)

@dataclass
class VotingResult:
    bbox: BBox
    source_models: list[str]
    num_votes: int
    individual_confidences: list[float]


class BBoxVoter:
    def __init__(self, model_accuracies: dict, iou_threshold: float = 0.3):
        if not model_accuracies:
            raise ValueError("model_accuracies must not be empty")
        if not (0.0 < iou_threshold <= 1.0):
            raise ValueError("iou_threshold must be in (0.0, 1.0]")
        self.model_accuracies = model_accuracies
        self.iou_threshold = iou_threshold

    @staticmethod
    def compute_iou(bbox1: BBox, bbox2: BBox) -> float:
        x1_min, y1_min = bbox1.x, bbox1.y
        x1_max, y1_max = bbox1.x + bbox1.w, bbox1.y + bbox1.h
        x2_min, y2_min = bbox2.x, bbox2.y
        x2_max, y2_max = bbox2.x + bbox2.w, bbox2.y + bbox2.h
        inter_xmin = max(x1_min, x2_min)
        inter_ymin = max(y1_min, y2_min)
        inter_xmax = min(x1_max, x2_max)
        inter_ymax = min(y1_max, y2_max)
        if inter_xmax < inter_xmin or inter_ymax < inter_ymin:
            return 0.0
        inter_area = (inter_xmax - inter_xmin) * (inter_ymax - inter_ymin)
        area1 = bbox1.w * bbox1.h
        area2 = bbox2.w * bbox2.h
        union_area = area1 + area2 - inter_area
        if union_area == 0:
            return 0.0
        return inter_area / union_area

    def vote(self, detections_by_model: dict):
        if not detections_by_model:
            return []
        model_list = list(detections_by_model.keys())
        anchor_model = model_list[0]
        anchor_detections = detections_by_model[anchor_model]
        if not anchor_detections:
            for model in model_list[1:]:
                if detections_by_model[model]:
                    anchor_model = model
                    anchor_detections = detections_by_model[anchor_model]
                    break
        if not anchor_detections:
            return []
        voting_results = []
        for anchor_bbox in anchor_detections:
            matching_bboxes = {anchor_model: anchor_bbox}
            individual_confidences = {anchor_model: anchor_bbox.confidence}
            for other_model in model_list:
                if other_model == anchor_model:
                    continue
                other_detections = detections_by_model[other_model]
                best_match = None
                best_iou = 0.0
                for other_bbox in other_detections:
                    iou = self.compute_iou(anchor_bbox, other_bbox)
                    if iou > best_iou and iou > self.iou_threshold:
                        best_iou = iou
                        best_match = other_bbox
                if best_match is not None:
                    matching_bboxes[other_model] = best_match
                    individual_confidences[other_model] = best_match.confidence
            merged_bbox = self._compute_weighted_average_bbox(matching_bboxes, self.model_accuracies)
            merged_confidence = self._compute_weighted_average_confidence(individual_confidences, self.model_accuracies)
            merged_bbox.confidence = merged_confidence
            result = VotingResult(
                bbox=merged_bbox,
                source_models=list(matching_bboxes.keys()),
                num_votes=len(matching_bboxes),
                individual_confidences=list(individual_confidences.values()),
            )
            voting_results.append(result)
        return voting_results

    @staticmethod
    def _compute_weighted_average_bbox(bboxes_by_model, model_accuracies):
        weights = {}
        total_weight = 0.0
        for model_name in bboxes_by_model.keys():
            accuracy = model_accuracies.get(model_name, 0.5)
            weights[model_name] = accuracy
            total_weight += accuracy
        for model_name in weights:
            weights[model_name] /= total_weight
        avg_x = avg_y = avg_w = avg_h = 0.0
        for model_name, bbox in bboxes_by_model.items():
            weight = weights[model_name]
            avg_x += bbox.x * weight
            avg_y += bbox.y * weight
            avg_w += bbox.w * weight
            avg_h += bbox.h * weight
        return BBox(x=int(round(avg_x)), y=int(round(avg_y)), w=int(round(avg_w)), h=int(round(avg_h)), confidence=0.0)

    @staticmethod
    def _compute_weighted_average_confidence(confidences_by_model, model_accuracies):
        if not confidences_by_model:
            return 0.0
        weights = {}
        total_weight = 0.0
        for model_name in confidences_by_model.keys():
            accuracy = model_accuracies.get(model_name, 0.5)
            weights[model_name] = accuracy
            total_weight += accuracy
        for model_name in weights:
            weights[model_name] /= total_weight
        avg_confidence = 0.0
        for model_name, conf in confidences_by_model.items():
            weight = weights[model_name]
            avg_confidence += conf * weight
        return float(np.clip(avg_confidence, 0.0, 1.0))

    def apply_nms(self, results: list, nms_threshold: float = 0.45):
        if not results or len(results) <= 1:
            return results
        sorted_results = sorted(results, key=lambda r: r.bbox.confidence, reverse=True)
        nms_results = []
        used_indices = set()
        for i, result in enumerate(sorted_results):
            if i in used_indices:
                continue
            nms_results.append(result)
            for j in range(i + 1, len(sorted_results)):
                if j in used_indices:
                    continue
                other_result = sorted_results[j]
                iou = self.compute_iou(result.bbox, other_result.bbox)
                if iou > nms_threshold:
                    used_indices.add(j)
        return nms_results


class EnsembleDetector:
    def __init__(self, model_configs, model_accuracies=None, iou_threshold=0.3, nms_threshold=0.45):
        if not model_configs:
            raise ValueError("model_configs must not be empty")
        self.model_configs = model_configs
        self.detectors = {}
        self.iou_threshold = iou_threshold
        self.nms_threshold = nms_threshold
        if model_accuracies is None:
            model_accuracies = {"yolov5s": 0.85, "yolov5m": 0.90, "yolov5l": 0.92}
        self.model_accuracies = model_accuracies
        self.voter = BBoxVoter(model_accuracies=model_accuracies, iou_threshold=iou_threshold)

    def _lazy_load_detector(self, model_name, kwargs):
        if model_name in self.detectors:
            return self.detectors[model_name]
        try:
            detector = WatermarkDetector(model_name=model_name, **kwargs)
            self.detectors[model_name] = detector
            logger.info(f"Loaded ensemble model: {model_name}")
            return detector
        except Exception as e:
            logger.warning(f"Failed to load model {model_name}: {e}")
            return None

    def detect_frame(self, frame):
        if frame is None or frame.size == 0:
            return []
        detections_by_model = {}
        loaded_models = 0
        for model_name, kwargs in self.model_configs:
            detector = self._lazy_load_detector(model_name, kwargs)
            if detector is None:
                continue
            try:
                bboxes = detector.detect_frame(frame)
                if bboxes:
                    detections_by_model[model_name] = bboxes
                    loaded_models += 1
            except Exception as e:
                logger.warning(f"Detection failed for {model_name}: {e}")
                continue
        if loaded_models == 0 or not detections_by_model:
            return []
        voting_results = self.voter.vote(detections_by_model)
        if not voting_results:
            return []
        nms_results = self.voter.apply_nms(voting_results, self.nms_threshold)
        return [result.bbox for result in nms_results]

    def detect_frames(self, frames):
        results = {}
        for frame_idx, frame in enumerate(frames):
            bboxes = self.detect_frame(frame)
            if bboxes:
                results[frame_idx] = bboxes
        return results

    def get_detector_status(self):
        status = {}
        for model_name, kwargs in self.model_configs:
            detector = self._lazy_load_detector(model_name, kwargs)
            status[model_name] = detector is not None
        return status
