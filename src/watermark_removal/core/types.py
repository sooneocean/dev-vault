"""Core data types for the watermark removal system."""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional

import numpy as np


class MaskType(str, Enum):
    """Watermark mask format."""

    IMAGE = "image"  # Static JPEG/PNG mask applied to all frames
    BBOX = "bbox"  # JSON sequence of per-frame bounding boxes
    POINTS = "points"  # JSON sequence of per-frame key points (deferred)


@dataclass
class Frame:
    """Single video frame with metadata."""

    frame_id: int
    """Zero-indexed frame number in video sequence."""

    image: np.ndarray
    """Frame data (HxWx3, BGR, uint8)."""

    timestamp_ms: float
    """Frame timestamp in milliseconds from video start."""


@dataclass
class Mask:
    """Watermark mask for a single frame."""

    type: MaskType
    """Mask format (IMAGE, BBOX, POINTS)."""

    data: np.ndarray | dict
    """Mask data: ndarray for IMAGE, dict {x, y, w, h} for BBOX."""

    valid_frame_range: tuple[int, int]
    """Frame ID range where this mask is valid (inclusive)."""


@dataclass
class CropRegion:
    """Mapping metadata for precise stitch-back of inpainted crops.

    This is the central object that tracks the original watermark location
    and all transformation parameters applied during crop/resize. It enables
    exact reconstruction of the original crop position after inpainting.
    """

    x: int
    """Original crop left edge in frame."""

    y: int
    """Original crop top edge in frame."""

    w: int
    """Original crop width in frame."""

    h: int
    """Original crop height in frame."""

    scale_factor: float
    """Resize scale from original crop to inpaint size (1024x1024).

    Used to rescale inpainted result back to original crop dimensions.
    """

    context_x: int
    """Context region left edge (with padding)."""

    context_y: int
    """Context region top edge (with padding)."""

    context_w: int
    """Context region width (with padding)."""

    context_h: int
    """Context region height (with padding)."""

    pad_left: int = 0
    """Padding added on left during resize to 1024x1024."""

    pad_top: int = 0
    """Padding added on top during resize to 1024x1024."""

    pad_right: int = 0
    """Padding added on right during resize to 1024x1024."""

    pad_bottom: int = 0
    """Padding added on bottom during resize to 1024x1024."""


@dataclass
class InpaintConfig:
    """Configuration for Flux inpaint execution."""

    model_name: str = "flux-dev.safetensors"
    """Checkpoint filename (e.g., 'flux-dev', 'sdxl-1.0')."""

    prompt: str = "remove watermark, clean background"
    """Positive prompt for inpainting."""

    negative_prompt: str = "watermark, text, artifacts, blurry"
    """Negative prompt to avoid."""

    steps: int = 20
    """Number of diffusion steps."""

    cfg_scale: float = 7.5
    """Classifier-free guidance scale."""

    seed: int = 42
    """Random seed for reproducibility."""

    sampler: str = "euler"
    """Diffusion sampler (euler, dpmpp, etc)."""


@dataclass
class FlowData:
    """Optical flow data between frame pairs for temporal alignment.

    Stores forward and backward optical flow vectors computed from consecutive
    frames, along with metadata for flow-based boundary warping.
    """

    forward_flow: np.ndarray
    """Forward flow: H×W×2 array of motion vectors from frame_t to frame_t+1."""

    backward_flow: np.ndarray
    """Backward flow: H×W×2 array of motion vectors from frame_t+1 to frame_t."""

    frame_pair_id: tuple[int, int]
    """Frame pair indices (frame_idx_t, frame_idx_t+1)."""

    confidence_map: Optional[np.ndarray] = None
    """Optional: Confidence scores for each flow vector (0.0-1.0)."""

    metadata: dict = field(default_factory=dict)
    """Optional metadata: model_version, compute_time_ms, resolution, etc."""


@dataclass
class ProcessConfig:
    """System-wide configuration for watermark removal pipeline."""

    video_path: str
    """Input video file path (absolute or relative)."""

    mask_path: str
    """Mask file path: JPEG for static, JSON for dynamic."""

    output_dir: str
    """Output directory for frames and final MP4."""

    inpaint: InpaintConfig = field(default_factory=InpaintConfig)
    """Inpaint model and sampling configuration."""

    context_padding: int = 50
    """Extra pixels to include around watermark bbox."""

    target_inpaint_size: int = 1024
    """Target resize dimension for inpaint (1024x1024)."""

    batch_size: int = 4
    """Number of crops to inpaint concurrently."""

    timeout: float = 300.0
    """Inpaint execution timeout in seconds."""

    output_codec: str = "h264"
    """Video codec (h264, vp9, etc)."""

    output_crf: int = 23
    """Video quality: lower = better (0-51, H.264 convention)."""

    output_fps: float = 30.0
    """Output video frames per second."""

    keep_intermediate: bool = False
    """Keep temporary frame/crop files after encoding."""

    verbose: bool = True
    """Enable verbose logging."""

    comfyui_host: str = "127.0.0.1"
    """ComfyUI server hostname."""

    comfyui_port: int = 8188
    """ComfyUI server port."""

    blend_feather_width: int = 32
    """Feather blend width in pixels at stitch boundaries."""

    skip_errors_in_preprocessing: bool = False
    """Skip frames that fail preprocessing instead of stopping."""

    skip_errors_in_postprocessing: bool = False
    """Skip frames that fail postprocessing instead of stopping."""

    temporal_smooth_enabled: bool = True
    """Enable temporal smoothing to reduce inter-frame flicker."""

    temporal_smooth_alpha: float = 0.3
    """Alpha blending factor for temporal smoothing (0.0-1.0)."""

    use_adaptive_temporal_smoothing: bool = False
    """Enable motion-aware adaptive alpha for temporal smoothing."""

    adaptive_motion_threshold: float = 0.05
    """Motion threshold for adaptive temporal smoothing (0.0-1.0)."""

    use_poisson_blending: bool = False
    """Enable Poisson blending to smooth stitch boundaries."""

    poisson_max_iterations: int = 100
    """Max iterations for Poisson solver convergence."""

    poisson_tolerance: float = 0.01
    """Convergence tolerance for Poisson solver."""

    use_watermark_tracker: bool = False
    """Enable YOLO-based watermark tracking for moving watermarks."""

    yolo_model_path: str | None = None
    """Path to YOLO model weights (null = disabled, auto-download if available)."""

    yolo_confidence_threshold: float = 0.5
    """YOLO detection confidence threshold (0.0-1.0)."""

    tracker_smoothing_factor: float = 0.3
    """BBox trajectory smoothing factor for tracking (0.0-1.0)."""

    use_checkpoints: bool = False
    """Enable checkpoint save/resume for long video processing."""

    crop_region: "CropRegion | None" = None
    """Override crop region (if None, derived from mask)."""

    optical_flow_enabled: bool = False
    """Enable optical flow-based temporal alignment (RAFT model)."""

    optical_flow_weight: float = 0.5
    """Blending weight for optical flow alignment (0.0-1.0)."""

    optical_flow_resolution: str = "480"
    """Optical flow computation resolution: '480' (optimized) or '1080'."""

    ensemble_detection_enabled: bool = False
    """Enable multi-model ensemble detection for improved accuracy."""

    ensemble_models: list[str] = field(default_factory=lambda: ["yolov5s", "yolov5m"])
    """List of YOLO model variants to use in ensemble (e.g., ['yolov5s', 'yolov5m'])."""

    ensemble_voting_mode: str = "confidence_weighted"
    """Ensemble voting strategy: 'confidence_weighted' (average by model accuracy)."""

    ensemble_iou_threshold: float = 0.3
    """Minimum IoU to match detections across ensemble models (0.0-1.0)."""

    ensemble_nms_threshold: float = 0.45
    """NMS threshold for post-processing ensemble results (0.0-1.0)."""

    ensemble_model_accuracies: dict[str, float] = field(
        default_factory=lambda: {"yolov5s": 0.85, "yolov5m": 0.90, "yolov5l": 0.92}
    )
    """Baseline accuracy baseline for each model (used for confidence weighting)."""

    def __post_init__(self):
        """Validate configuration."""
        if not self.video_path:
            raise ValueError("video_path is required")
        if not self.mask_path:
            raise ValueError("mask_path is required")
        if not self.output_dir:
            raise ValueError("output_dir is required")

        # Resolve relative paths
        self.video_path = str(Path(self.video_path).resolve())
        self.mask_path = str(Path(self.mask_path).resolve())
        self.output_dir = str(Path(self.output_dir).resolve())

        # Validate numeric parameters
        if self.context_padding < 0:
            raise ValueError("context_padding must be >= 0")
        if self.target_inpaint_size < 256:
            raise ValueError("target_inpaint_size must be >= 256")
        if self.batch_size < 1:
            raise ValueError("batch_size must be >= 1")
        if self.timeout <= 0:
            raise ValueError("timeout must be > 0")
        if not (0 <= self.output_crf <= 51):
            raise ValueError("output_crf must be 0-51")
        if not (0.0 <= self.temporal_smooth_alpha <= 1.0):
            raise ValueError("temporal_smooth_alpha must be 0.0-1.0")

        # Phase 2 parameter validation
        if not (0.0 <= self.adaptive_motion_threshold <= 1.0):
            raise ValueError("adaptive_motion_threshold must be 0.0-1.0")
        if self.poisson_max_iterations < 1:
            raise ValueError("poisson_max_iterations must be >= 1")
        if self.poisson_tolerance <= 0.0:
            raise ValueError("poisson_tolerance must be > 0.0")
        if not (0.0 <= self.yolo_confidence_threshold <= 1.0):
            raise ValueError("yolo_confidence_threshold must be 0.0-1.0")
        if not (0.0 <= self.tracker_smoothing_factor <= 1.0):
            raise ValueError("tracker_smoothing_factor must be 0.0-1.0")

        # Phase 3 optical flow parameter validation
        if not (0.0 <= self.optical_flow_weight <= 1.0):
            raise ValueError("optical_flow_weight must be 0.0-1.0")
        if self.optical_flow_resolution not in ("480", "1080"):
            raise ValueError("optical_flow_resolution must be '480' or '1080'")

        # Phase 3 ensemble detection parameter validation
        if self.ensemble_detection_enabled:
            if not self.ensemble_models:
                raise ValueError("ensemble_models must not be empty when ensemble_detection_enabled=true")
            if self.ensemble_voting_mode not in ("confidence_weighted",):
                raise ValueError("ensemble_voting_mode must be 'confidence_weighted'")
            if not (0.0 < self.ensemble_iou_threshold <= 1.0):
                raise ValueError("ensemble_iou_threshold must be in (0.0, 1.0]")
            if not (0.0 <= self.ensemble_nms_threshold <= 1.0):
                raise ValueError("ensemble_nms_threshold must be 0.0-1.0")
            if not self.ensemble_model_accuracies:
                raise ValueError("ensemble_model_accuracies must not be empty")
