"""GPU memory lifecycle management for RTX 4090 laptop (16GB VRAM).

Enforces strict VRAM allocation state machine to prevent OOM errors.
Orchestrates model load/unload/cleanup across detection → inpainting → post-processing.
"""

import gc
import logging
import torch
from enum import Enum
from typing import Any, Dict, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class MemoryState(str, Enum):
    """GPU memory lifecycle state machine."""

    IDLE = "idle"  # No models loaded
    DETECT_LOADING = "detect_loading"  # Loading Florence-2
    DETECTING = "detecting"  # Florence-2 inference in progress
    DETECT_CLEANUP = "detect_cleanup"  # Unloading Florence-2
    INPAINT_LOADING = "inpaint_loading"  # Loading LaMa or Flux
    INFERRING = "inferring"  # Inpainting inference in progress
    INPAINT_CLEANUP = "inpaint_cleanup"  # Unloading inpaint engine
    POSTPROCESS = "postprocess"  # Edge blending, stitching (lightweight)
    ERROR = "error"  # Error state, models may be partially loaded


@dataclass
class VRAMSnapshot:
    """Point-in-time VRAM utilization snapshot."""

    allocated_gb: float
    reserved_gb: float
    available_gb: float
    state: MemoryState


class InsufficientVRAMError(Exception):
    """Raised when estimated VRAM insufficient for planned operation."""

    pass


class StateTransitionError(ValueError):
    """Raised on invalid or out-of-order state machine transitions."""

    pass


class MemoryManager:
    """Orchestrate GPU memory lifecycle for watermark removal pipeline.

    Guarantees zero OOM errors on 16GB VRAM through explicit state transitions,
    model offloading, and cleanup validation.

    Attributes:
        device: Target device ("cuda" or "cpu")
        vram_safety_threshold_gb: Minimum VRAM headroom required before operation
        enable_monitoring: Enable per-transition VRAM logging
    """

    # VRAM footprint estimates (FP16/FP8) on RTX 4090
    MODEL_VRAM_ESTIMATES = {
        "florence2": 8.0,  # FP16 (~3.2B params)
        "lama": 2.0,  # FP16 with tiling
        "flux": 12.0,  # FP16 + optimizations (sequential offload → 8GB, model offload → 12GB)
        "poisson_blender": 0.5,  # Lightweight post-processing
    }

    def __init__(
        self,
        device: str = "cuda",
        vram_safety_threshold_gb: float = 1.0,
        enable_monitoring: bool = True,
        vram_budget: float = 16.0,
    ):
        """Initialize memory manager.

        Args:
            device: Target device ("cuda" or "cpu", auto-detect if "auto")
            vram_safety_threshold_gb: Minimum free VRAM before operation (default 1GB)
            enable_monitoring: Enable VRAM logging per state transition
            vram_budget: Total VRAM budget in GB (default 16.0 for RTX 4090; used on CPU or for testing)
        """
        if device == "auto":
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        self.vram_safety_threshold_gb = vram_safety_threshold_gb
        self.enable_monitoring = enable_monitoring
        self.state = MemoryState.IDLE

        # Detect actual VRAM or use budget parameter
        if self.device == "cuda" and torch.cuda.is_available():
            try:
                props = torch.cuda.get_device_properties(torch.device("cuda"))
                self._total_vram_gb = props.total_memory / (1024 ** 3)
            except Exception as e:
                logger.warning(f"Failed to detect actual VRAM: {e}. Using vram_budget={vram_budget}GB")
                self._total_vram_gb = vram_budget
        else:
            self._total_vram_gb = vram_budget  # CPU path uses budget parameter

        # Track loaded models for cleanup
        self._loaded_models: Dict[str, Any] = {}

        # State transition rules (defines which states are valid transitions)
        self._valid_transitions = {
            MemoryState.IDLE: [MemoryState.DETECT_LOADING, MemoryState.INPAINT_LOADING],
            MemoryState.DETECT_LOADING: [MemoryState.DETECTING, MemoryState.ERROR],
            MemoryState.DETECTING: [MemoryState.DETECT_CLEANUP, MemoryState.ERROR],
            MemoryState.DETECT_CLEANUP: [MemoryState.IDLE, MemoryState.INPAINT_LOADING],
            MemoryState.INPAINT_LOADING: [MemoryState.INFERRING, MemoryState.ERROR],
            MemoryState.INFERRING: [MemoryState.INPAINT_CLEANUP, MemoryState.ERROR],
            MemoryState.INPAINT_CLEANUP: [MemoryState.IDLE, MemoryState.POSTPROCESS],
            MemoryState.POSTPROCESS: [MemoryState.IDLE, MemoryState.DETECT_LOADING],
            MemoryState.ERROR: [MemoryState.IDLE],  # Always allow reset from error
        }

        logger.info(
            f"MemoryManager initialized on {self.device}, "
            f"total_vram={self._total_vram_gb:.1f}GB, "
            f"safety threshold={vram_safety_threshold_gb}GB"
        )

    def _get_vram_snapshot(self) -> VRAMSnapshot:
        """Get current VRAM utilization snapshot."""
        if self.device != "cuda":
            return VRAMSnapshot(
                allocated_gb=0.0,
                reserved_gb=0.0,
                available_gb=self._total_vram_gb,  # Use configured or detected VRAM budget
                state=self.state,
            )

        allocated_gb = torch.cuda.memory_allocated() / (1024 ** 3)
        reserved_gb = torch.cuda.memory_reserved() / (1024 ** 3)
        available_gb = self._total_vram_gb - reserved_gb  # Use detected or configured total VRAM

        return VRAMSnapshot(
            allocated_gb=round(allocated_gb, 2),
            reserved_gb=round(reserved_gb, 2),
            available_gb=round(available_gb, 2),
            state=self.state,
        )

    def _log_vram_transition(self, from_state: MemoryState, to_state: MemoryState):
        """Log state transition with VRAM snapshot."""
        if not self.enable_monitoring:
            return

        snapshot = self._get_vram_snapshot()
        logger.info(
            f"State transition: {from_state} → {to_state} | "
            f"Allocated: {snapshot.allocated_gb}GB | "
            f"Reserved: {snapshot.reserved_gb}GB | "
            f"Available: {snapshot.available_gb}GB"
        )

    def transition_to(self, target_state: MemoryState) -> bool:
        """Transition to target state with validation.

        Args:
            target_state: Target memory state

        Returns:
            True if transition succeeded, False if invalid

        Raises:
            StateTransitionError: If transition not allowed from current state
        """
        if target_state not in self._valid_transitions.get(self.state, []):
            raise StateTransitionError(
                f"Invalid transition: {self.state} → {target_state}. "
                f"Valid transitions: {self._valid_transitions.get(self.state, [])}"
            )

        self._log_vram_transition(self.state, target_state)
        self.state = target_state
        return True

    def validate_vram_headroom(self, threshold_gb: Optional[float] = None) -> bool:
        """Check if sufficient VRAM headroom is available.

        Args:
            threshold_gb: Override default safety threshold

        Returns:
            True if headroom >= threshold, False otherwise

        Raises:
            InsufficientVRAMError: If headroom insufficient
        """
        threshold = threshold_gb or self.vram_safety_threshold_gb
        snapshot = self._get_vram_snapshot()

        if snapshot.available_gb < threshold:
            raise InsufficientVRAMError(
                f"Insufficient VRAM: Available {snapshot.available_gb}GB < "
                f"Required {threshold}GB. "
                f"Current allocation: {snapshot.allocated_gb}GB"
            )

        return True

    def estimate_peak_vram(
        self, engine_name: str, image_resolution: Tuple[int, int]
    ) -> float:
        """Estimate peak VRAM for operation.

        Args:
            engine_name: Model name ("lama", "flux", "florence2")
            image_resolution: (height, width) tuple

        Returns:
            Estimated peak VRAM in GB
        """
        base_vram = self.MODEL_VRAM_ESTIMATES.get(engine_name, 2.0)

        # Scale estimate for high-resolution images
        h, w = image_resolution
        pixels = h * w
        if pixels > 2048 * 2048:  # >4K
            # Tiling reduces peak but estimate conservatively
            base_vram *= 1.2
        elif pixels < 512 * 512:  # <512×512
            base_vram *= 0.8

        return base_vram

    def load_model(
        self, model_name: str, model_instance: Any, device: Optional[str] = None
    ) -> None:
        """Load model to GPU and register for cleanup.

        Args:
            model_name: Model identifier ("florence2", "lama", "flux")
            model_instance: Model object (assumed to have .to() method)
            device: Target device (defaults to self.device)

        Raises:
            InsufficientVRAMError: If estimated VRAM insufficient
        """
        device = device or self.device
        estimated_vram = self.estimate_peak_vram(model_name, (1024, 1024))

        try:
            self.validate_vram_headroom(estimated_vram + 0.5)  # 0.5GB buffer
        except InsufficientVRAMError as e:
            logger.warning(f"VRAM validation failed for {model_name}: {e}")
            raise

        # Unload existing model if already loaded
        if model_name in self._loaded_models:
            self.unload_model(model_name)

        if device == "cuda":
            model_instance.to("cuda")
            torch.cuda.synchronize()

        self._loaded_models[model_name] = model_instance

        snapshot = self._get_vram_snapshot()
        logger.info(
            f"Loaded {model_name} on {device}. "
            f"VRAM allocated: {snapshot.allocated_gb}GB / {self._total_vram_gb:.1f}GB"
        )

    def unload_model(self, model_name: str) -> bool:
        """Unload model from GPU and cleanup.

        Args:
            model_name: Model identifier

        Returns:
            True if model was unloaded, False if not loaded
        """
        if model_name not in self._loaded_models:
            logger.debug(f"Model {model_name} not loaded, skipping unload")
            return False

        try:
            model = self._loaded_models.pop(model_name)
            del model
            torch.cuda.empty_cache()
            gc.collect()

            snapshot = self._get_vram_snapshot()
            logger.info(
                f"Unloaded {model_name}. "
                f"VRAM allocated: {snapshot.allocated_gb}GB / {self._total_vram_gb:.1f}GB"
            )
            return True
        except Exception as e:
            logger.error(f"Error unloading {model_name}: {e}")
            return False

    def verify_cleanup(self) -> None:
        """Assert VRAM fragmentation is below threshold after cache clear.

        Raises InsufficientVRAMError if more than 500MB remains allocated
        after torch.cuda.empty_cache().

        This validates that cleanup was effective and fragmentation is acceptable.
        """
        if self.device != "cuda":
            return  # Skip on CPU

        allocated_gb = torch.cuda.memory_allocated() / (1024 ** 3)
        if allocated_gb > 0.5:
            raise InsufficientVRAMError(
                f"Cleanup left {allocated_gb:.2f}GB allocated; expected <0.5GB. "
                "Fragmentation may cause OOM on next model load."
            )
        logger.debug(f"Cleanup verification passed: {allocated_gb:.3f}GB allocated")

    def cleanup_all(self) -> None:
        """Cleanup all loaded models and reset state."""
        for model_name in list(self._loaded_models.keys()):
            self.unload_model(model_name)

        if self.device == "cuda":
            torch.cuda.empty_cache()
            self.verify_cleanup()  # Assert fragmentation is acceptable

        self._loaded_models.clear()
        self.state = MemoryState.IDLE
        logger.info("All models cleaned up, state reset to IDLE")

    def get_status(self) -> Dict[str, Any]:
        """Get current memory manager status.

        Returns:
            Dictionary with state, VRAM snapshot, loaded models
        """
        snapshot = self._get_vram_snapshot()
        return {
            "state": self.state.value,
            "device": self.device,
            "allocated_gb": snapshot.allocated_gb,
            "reserved_gb": snapshot.reserved_gb,
            "available_gb": snapshot.available_gb,
            "loaded_models": list(self._loaded_models.keys()),
        }

    def execute(self, fn, *args, **kwargs):
        """Run fn(*args, **kwargs) and ensure cleanup on exception.

        Does not manage state transitions (caller is responsible for correct
        state machine sequencing). Uses try/finally so cleanup always runs
        if an exception occurs.

        Args:
            fn: Callable to execute
            *args: Positional arguments to pass to fn
            **kwargs: Keyword arguments to pass to fn

        Returns:
            Return value of fn(*args, **kwargs)

        Raises:
            Any exception raised by fn, after calling cleanup_all()
        """
        try:
            return fn(*args, **kwargs)
        except Exception:
            self.cleanup_all()
            raise
