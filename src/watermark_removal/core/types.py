"""Core data types for the watermark removal system."""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

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

    crop_region: "CropRegion | None" = None
    """Override crop region (if None, derived from mask)."""

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
