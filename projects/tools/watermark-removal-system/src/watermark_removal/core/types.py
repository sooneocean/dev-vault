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

    Attributes:
        frame_id: Which frame this crop came from
        original_bbox: (x, y, w, h) of watermark in original frame
        context_bbox: (x, y, w, h) of crop region including context padding in original frame
        scale_factor: Scaling applied during resize (context_size → 1024x1024)
        pad_left, pad_top, pad_right, pad_bottom: Zero-padding applied during resize
    """
    frame_id: int
    original_bbox: tuple[int, int, int, int]  # (x, y, w, h)
    context_bbox: tuple[int, int, int, int]   # (x, y, w, h)
    scale_factor: float
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
        inpaint: InpaintConfig object with model parameters
        context_padding: Extra surrounding context to include during crop (pixels)
        target_inpaint_size: Resize crops to this size for inpaint (e.g., 1024)
        blend_feather_width: Width of feather mask at crop edges (pixels)
        temporal_smooth_alpha: Alpha for temporal smoothing (0.0 = disabled, Phase 1)
        batch_size: Number of parallel inpaint jobs
        inpaint_timeout_sec: Timeout for each inpaint job (seconds)
        comfyui_host: ComfyUI server host
        comfyui_port: ComfyUI server port
        keep_intermediate: Whether to keep intermediate frame/crop files
    """
    video_path: str | Path
    mask_path: str | Path
    output_dir: str | Path = "output"

    inpaint: InpaintConfig = field(default_factory=InpaintConfig)

    context_padding: int = 64
    target_inpaint_size: int = 1024
    blend_feather_width: int = 32
    temporal_smooth_alpha: float = 0.0

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
