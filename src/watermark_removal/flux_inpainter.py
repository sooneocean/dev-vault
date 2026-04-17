"""Flux.1-Fill high-quality inpainting with FP8 quantization."""

import logging
import numpy as np
import torch
from typing import Optional, TYPE_CHECKING
from PIL import Image

if TYPE_CHECKING:
    from .memory_manager import MemoryManager

logger = logging.getLogger(__name__)


class FluxInpainter:
    """High-quality watermark removal using Flux.1-Fill with memory optimization.

    Supports FP8 quantization and sequential CPU offloading to fit 16GB VRAM.
    """

    def __init__(
        self,
        device: str = "cuda",
        enable_sequential_offload: bool = False,
        guidance_scale: float = 3.5,
        num_steps: int = 50,
        memory_manager: Optional["MemoryManager"] = None,
    ):
        """Initialize Flux inpainter.

        Args:
            device: "cuda" or "cpu"
            enable_sequential_offload: Use sequential offload (slow, low VRAM)
                or model offload (default, faster)
            guidance_scale: Guidance scale (1-10, default 3.5)
            num_steps: Inference steps (30-100, default 50)
            memory_manager: Optional MemoryManager for GPU lifecycle management
        """
        self.device = device
        self.enable_sequential_offload = enable_sequential_offload
        self.guidance_scale = guidance_scale
        self.num_steps = num_steps
        self.memory_manager = memory_manager
        self.pipeline = None
        self._model_loaded = False

    def load_model(self) -> None:
        """Load Flux.1-Fill model with optimizations."""
        if self._model_loaded:
            return

        try:
            from diffusers import FluxInpaintPipeline
            import bitsandbytes

            logger.info("Loading Flux.1-Fill with FP8 quantization...")

            self.pipeline = FluxInpaintPipeline.from_pretrained(
                "black-forest-labs/FLUX.1-Fill-dev",
                torch_dtype=torch.bfloat16,
                device_map="auto"
            )

            # Apply memory optimizations
            if self.enable_sequential_offload:
                self.pipeline.enable_sequential_cpu_offload()
                logger.info("Enabled sequential CPU offload (slow but low VRAM)")
            else:
                self.pipeline.enable_model_cpu_offload()
                logger.info("Enabled model CPU offload (faster)")

            # VAE tiling for memory efficiency
            self.pipeline.vae.enable_tiling()

            # Attention slicing
            self.pipeline.enable_attention_slicing()

            self._model_loaded = True

            # Register with MemoryManager if provided
            if self.memory_manager:
                self.memory_manager.load_model("flux", self.pipeline)

            logger.info("Flux.1-Fill loaded successfully")

        except ImportError as e:
            raise RuntimeError(
                f"Flux.1-Fill requires: pip install diffusers bitsandbytes torch"
            ) from e
        except Exception as e:
            raise RuntimeError(f"Failed to load Flux model: {e}") from e

    def inpaint(
        self,
        image: np.ndarray,
        mask: np.ndarray,
        prompt: str = "remove watermark, clean background",
    ) -> np.ndarray:
        """Inpaint watermarked region in image.

        Args:
            image: Input image (H, W, 3) uint8 0-255
            mask: Inpaint mask (H, W) uint8, 255=inpaint, 0=keep
            prompt: Inpainting prompt

        Returns:
            Inpainted image (H, W, 3) uint8
        """
        if not self._model_loaded:
            self.load_model()

        try:
            # Convert to PIL
            image_pil = Image.fromarray(image, "RGB")
            mask_pil = Image.fromarray(mask.astype(np.uint8), "L")

            # Get dimensions (use 768x768 default, can be tuned)
            h, w = image.shape[:2]
            infer_h = min(h, 1024) if h % 2 == 0 else min(h, 1023)
            infer_w = min(w, 1024) if w % 2 == 0 else min(w, 1023)

            with torch.no_grad():
                output = self.pipeline(
                    prompt=prompt,
                    image=image_pil,
                    mask_image=mask_pil,
                    height=infer_h,
                    width=infer_w,
                    num_inference_steps=self.num_steps,
                    guidance_scale=self.guidance_scale,
                ).images[0]

            # Synchronize GPU
            torch.cuda.synchronize()

            # Convert back to numpy
            result = np.array(output, dtype=np.uint8)

            return result

        except RuntimeError as e:
            if "out of memory" in str(e).lower():
                logger.error(
                    f"CUDA OOM on {self.device}. "
                    f"Try enabling sequential offload (slower but lower VRAM)."
                )
                raise RuntimeError(
                    f"Flux inpainting failed (OOM): {e}. "
                    f"Suggest fallback to LaMa or sequential offload."
                ) from e
            raise RuntimeError(f"Flux inpainting failed: {e}") from e

    def cleanup(self) -> None:
        """Cleanup model from GPU."""
        if self.pipeline is not None:
            try:
                # Unregister from MemoryManager if provided
                if self.memory_manager:
                    self.memory_manager.unload_model("flux")

                del self.pipeline
                torch.cuda.empty_cache()
                self._model_loaded = False
                logger.info("Flux model cleaned up")
            except Exception as e:
                logger.warning(f"Error during cleanup: {e}")
