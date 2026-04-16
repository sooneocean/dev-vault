"""Dual-engine inpainting router: selects LaMa (fast) or Flux (quality)."""

import logging
from enum import Enum
from dataclasses import dataclass
from typing import Tuple, Optional

import numpy as np
from PIL import Image

from .memory_manager import MemoryManager, MemoryState
from .lama_inpainter import LamaInpainter
from .flux_inpainter import FluxInpainter

logger = logging.getLogger(__name__)


class InpaintEngine(str, Enum):
    """Available inpainting engines."""

    LAMA = "lama"
    FLUX = "flux"


@dataclass
class InpaintEngineConfig:
    """Configuration for dual-engine router."""

    engine: InpaintEngine = InpaintEngine.LAMA
    lama_tile_size: int = 512
    lama_overlap: int = 64
    flux_guidance_scale: float = 3.5
    flux_num_steps: int = 50
    flux_enable_sequential_offload: bool = False
    auto_downgrade_on_oom: bool = True
    device: str = "cuda"


class DualEngineRouter:
    """Route inpainting requests to appropriate engine.

    Selects LaMa for speed (default) or Flux for quality.
    Auto-downgrades to LaMa if Flux VRAM insufficient.
    """

    def __init__(self, config: InpaintEngineConfig, memory_manager: Optional[MemoryManager] = None):
        """Initialize router.

        Args:
            config: InpaintEngineConfig with engine selection and params
            memory_manager: Optional MemoryManager for VRAM monitoring
        """
        self.config = config
        self.memory_manager = memory_manager or MemoryManager(device=config.device)
        self.lama = None
        self.flux = None
        self.current_engine = None

    def inpaint(
        self,
        image: np.ndarray,
        mask: np.ndarray,
        prompt: str = "remove watermark, clean background",
    ) -> np.ndarray:
        """Inpaint using selected engine.

        Args:
            image: Input image (H, W, 3) uint8
            mask: Inpaint mask (H, W) uint8
            prompt: Inpainting prompt (for Flux)

        Returns:
            Inpainted image (H, W, 3) uint8
        """
        target_engine = self.config.engine

        # Validate VRAM if using Flux
        if target_engine == InpaintEngine.FLUX:
            h, w = image.shape[:2]
            estimated_vram = self.memory_manager.estimate_peak_vram(
                "flux", (h, w)
            )

            try:
                self.memory_manager.validate_vram_headroom(estimated_vram + 0.5)
            except Exception as e:
                if self.config.auto_downgrade_on_oom:
                    logger.warning(
                        f"Insufficient VRAM for Flux ({estimated_vram}GB). "
                        f"Auto-downgrading to LaMa."
                    )
                    target_engine = InpaintEngine.LAMA
                else:
                    raise

        # Execute with selected engine
        try:
            if target_engine == InpaintEngine.LAMA:
                return self._inpaint_with_lama(image, mask)
            else:
                return self._inpaint_with_flux(image, mask, prompt)
        except Exception as e:
            # Last-resort fallback to LaMa
            if target_engine == InpaintEngine.FLUX and self.config.auto_downgrade_on_oom:
                logger.error(f"Flux failed: {e}. Falling back to LaMa.")
                return self._inpaint_with_lama(image, mask)
            raise

    def _inpaint_with_lama(self, image: np.ndarray, mask: np.ndarray) -> np.ndarray:
        """Inpaint with LaMa (fast path)."""
        if self.lama is None:
            self.lama = LamaInpainter(
                device=self.config.device,
                tile_size=self.config.lama_tile_size,
                overlap=self.config.lama_overlap,
            )

        # Transition memory state
        self.memory_manager.transition_to(MemoryState.INPAINT_LOADING)
        self.lama.load_model()

        self.memory_manager.transition_to(MemoryState.INFERRING)
        result = self.lama.inpaint(image, mask)

        self.memory_manager.transition_to(MemoryState.INPAINT_CLEANUP)
        self.lama.cleanup()

        self.memory_manager.transition_to(MemoryState.IDLE)

        logger.info(f"LaMa inpainting complete")
        return result

    def _inpaint_with_flux(
        self, image: np.ndarray, mask: np.ndarray, prompt: str
    ) -> np.ndarray:
        """Inpaint with Flux (quality path)."""
        if self.flux is None:
            self.flux = FluxInpainter(
                device=self.config.device,
                enable_sequential_offload=self.config.flux_enable_sequential_offload,
                guidance_scale=self.config.flux_guidance_scale,
                num_steps=self.config.flux_num_steps,
            )

        # Transition memory state
        self.memory_manager.transition_to(MemoryState.INPAINT_LOADING)
        self.flux.load_model()

        self.memory_manager.transition_to(MemoryState.INFERRING)
        result = self.flux.inpaint(image, mask, prompt)

        self.memory_manager.transition_to(MemoryState.INPAINT_CLEANUP)
        self.flux.cleanup()

        self.memory_manager.transition_to(MemoryState.IDLE)

        logger.info(f"Flux inpainting complete")
        return result

    def cleanup(self) -> None:
        """Cleanup all models."""
        if self.lama is not None:
            self.lama.cleanup()
        if self.flux is not None:
            self.flux.cleanup()
        self.memory_manager.cleanup_all()
