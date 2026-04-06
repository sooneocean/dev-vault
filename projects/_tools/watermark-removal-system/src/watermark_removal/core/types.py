"""
Data structures and type definitions for the watermark removal system.

Defines all system-wide dataclasses with complete type safety:
- Frame: single video frame with metadata
- Mask: watermark mask (image or bbox)
- CropRegion: transformation metadata for crop-stitch mapping
- InpaintConfig: inpaint model parameters
- ProcessConfig: system-wide configuration
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional
import numpy as np


class MaskType(str, Enum):
    """Supported watermark mask types."""
    IMAGE = "image"      # JPEG/PNG mask image (static, applies to all frames)
    BBOX = "bbox"        # JSON bbox sequence (per-frame, allows dynamic watermarks)
    POINTS = "points"    # Point cloud (reserved for Phase 2)


@dataclass
class Frame:
    """
    Represents a single video frame.

    Attributes:
        frame_id: 0-indexed frame number
        image: BGR ndarray (H, W, 3), uint8
        timestamp_ms: Frame timestamp in milliseconds
    """
    frame_id: int
    image: np.ndarray
    timestamp_ms: float


@dataclass
class Mask:
    """
    Represents a watermark mask for one or more frames.

    Attributes:
        mask_type: Type of mask (IMAGE, BBOX, POINTS)
        data: Mask data (ndarray for IMAGE, dict for BBOX)
        valid_frame_range: Tuple (start_frame_id, end_frame_id) indicating which frames this mask applies to
    """
    mask_type: MaskType
    data: Optional[np.ndarray | dict] = None
    valid_frame_range: tuple[int, int] = (0, float('inf'))


@dataclass
class CropRegion:
    """
    Metadata for a cropped region, enabling precise stitch-back transformation.

    Tracks the original bbox, context padding, and scaling applied during crop,
    so the inpainted crop can be rescaled and composited back exactly.

    For multi-watermark support, watermark_id distinguishes between multiple
    watermarks in the same frame.

    Attributes:
        frame_id: Which frame this crop came from
        original_bbox: (x, y, w, h) of watermark in original frame
        context_bbox: (x, y, w, h) of crop region including context padding in original frame
        scale_factor: Scaling applied during resize (context_size → 1024x1024)
        watermark_id: ID to distinguish multiple watermarks in same frame (0-indexed, Phase 2)
        pad_left, pad_top, pad_right, pad_bottom: Zero-padding applied during resize
    """
    frame_id: int
    original_bbox: tuple[int, int, int, int]  # (x, y, w, h)
    context_bbox: tuple[int, int, int, int]   # (x, y, w, h)
    scale_factor: float
    watermark_id: int = 0  # Phase 2: distinguishes multiple watermarks per frame
    pad_left: int = 0
    pad_top: int = 0
    pad_right: int = 0
    pad_bottom: int = 0


@dataclass
class InpaintConfig:
    """
    Parameters for the inpaint model (Flux, SDXL, etc).

    Attributes:
        model_name: Model checkpoint name (e.g., "flux-dev", "sdxl-base")
        prompt: Positive prompt guiding inpaint
        negative_prompt: Negative prompt (e.g., "watermark, text, logo")
        steps: Number of diffusion steps
        cfg_scale: Classifier-free guidance scale
        sampler: Sampler type (e.g., "dpmpp_2m")
        scheduler: Scheduler type (e.g., "karras")
        seed: Random seed for reproducibility (-1 = random)
    """
    model_name: str = "flux-dev"
    prompt: str = "remove watermark seamlessly"
    negative_prompt: str = "watermark, text, logo, artifact"
    steps: int = 20
    cfg_scale: float = 7.5
    sampler: str = "dpmpp_2m"
    scheduler: str = "karras"
    seed: int = -1


@dataclass
class ProcessConfig:
    """
    System-wide configuration for the entire watermark removal pipeline.

    Attributes:
        video_path: Path to input video file
        mask_path: Path to mask file (JPEG or JSON)
        output_dir: Directory to save output video and intermediate frames
        checkpoint_dir: Directory for resumable pipeline checkpoints
        inpaint: InpaintConfig object with model parameters
        context_padding: Extra surrounding context to include during crop (pixels)
        target_inpaint_size: Resize crops to this size for inpaint (e.g., 1024)
        blend_feather_width: Width of feather mask at crop edges (pixels)
        temporal_smooth_alpha: Alpha for temporal smoothing (0.0 = disabled, Phase 1)
        use_adaptive_temporal_smoothing: Enable motion-aware temporal smoothing (Phase 2)
        adaptive_motion_threshold: Threshold for motion detection in temporal smoothing
        use_poisson_blending: Enable Poisson equation blending (Phase 2)
        poisson_max_iterations: Max iterations for Poisson solver
        use_watermark_tracker: Enable YOLO-based watermark tracking (Phase 2)
        yolo_model_path: Path to YOLO model weights (e.g., yolov8n.pt)
        yolo_confidence_threshold: Minimum confidence for YOLO detections
        tracker_smoothing_factor: Alpha for tracker bbox smoothing
        use_checkpoints: Enable pipeline checkpointing for resumption (Phase 2)
        resume_from_checkpoint: Resume from last checkpoint if available
        batch_size: Number of parallel inpaint jobs
        inpaint_timeout_sec: Timeout for each inpaint job (seconds)
        comfyui_host: ComfyUI server host
        comfyui_port: ComfyUI server port
        keep_intermediate: Whether to keep intermediate frame/crop files
    """
    video_path: str | Path
    mask_path: str | Path
    output_dir: str | Path = "output"
    checkpoint_dir: str | Path = "checkpoints"

    inpaint: InpaintConfig = field(default_factory=InpaintConfig)

    # Phase 1 Postprocessing
    context_padding: int = 64
    target_inpaint_size: int = 1024
    blend_feather_width: int = 32
    temporal_smooth_alpha: float = 0.0

    # Phase 2 Postprocessing - Temporal Smoothing
    use_adaptive_temporal_smoothing: bool = False
    adaptive_motion_threshold: float = 0.05

    # Phase 2 Postprocessing - Poisson Blending
    use_poisson_blending: bool = False
    poisson_max_iterations: int = 100
    poisson_tolerance: float = 0.01

    # Phase 2 Preprocessing - YOLO Automatic Detection
    use_yolo_detection: bool = False
    yolo_model_size: str = "small"  # nano, small, medium, large
    yolo_confidence_threshold: float = 0.5
    yolo_nms_threshold: float = 0.45

    # Phase 2 Preprocessing - Multi-Watermark Support
    max_watermarks_per_frame: int = 1  # Max watermarks to process per frame
    watermark_merge_threshold: float = 0.3  # IoU threshold for merging overlapping watermarks

    # Phase 2 Preprocessing - Watermark Tracking
    use_watermark_tracker: bool = False
    yolo_model_path: Optional[str | Path] = None
    tracker_sparse_interval: int = 1
    tracker_smoothing_factor: float = 0.3

    # Phase 2 Pipeline - Resumption
    use_checkpoints: bool = False
    resume_from_checkpoint: bool = False

    # Execution
    batch_size: int = 4
    inpaint_timeout_sec: float = 300.0

    comfyui_host: str = "127.0.0.1"
    comfyui_port: int = 8188

    keep_intermediate: bool = False

    def __post_init__(self):
        """Convert path strings to Path objects."""
        if isinstance(self.video_path, str):
            self.video_path = Path(self.video_path)
        if isinstance(self.mask_path, str):
            self.mask_path = Path(self.mask_path)
        if isinstance(self.output_dir, str):
            self.output_dir = Path(self.output_dir)
        if isinstance(self.checkpoint_dir, str):
            self.checkpoint_dir = Path(self.checkpoint_dir)
        if isinstance(self.yolo_model_path, str):
            self.yolo_model_path = Path(self.yolo_model_path)
