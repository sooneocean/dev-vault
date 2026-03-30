"""Optical flow computation using TorchVision RAFT model."""

import asyncio
import logging
from typing import Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


class OpticalFlowProcessor:
    """Compute optical flow between frame pairs using pretrained RAFT model.

    Supports 480p (optimized, 212ms/frame) and 1080p modes with lazy loading
    and GPU fallback.
    """

    def __init__(self, resolution: str = "480", device: str = "auto") -> None:
        """Initialize optical flow processor.

        Args:
            resolution: '480' for optimized mode or '1080' for offline mode.
            device: 'cuda', 'cpu', or 'auto' (auto-detect GPU availability).

        Raises:
            ValueError: If resolution not supported.
        """
        if resolution not in ("480", "1080"):
            raise ValueError(f"resolution must be '480' or '1080', got {resolution}")

        self.resolution = resolution
        self.device = device if device != "auto" else self._detect_device()
        self.model = None
        self._model_loaded = False

    @staticmethod
    def _detect_device() -> str:
        """Detect best available device."""
        try:
            import torch

            return "cuda" if torch.cuda.is_available() else "cpu"
        except ImportError:
            return "cpu"

    def _lazy_load_model(self) -> None:
        """Lazily load RAFT model (only when first needed)."""
        if self._model_loaded:
            return

        try:
            import torch
            import torchvision

            # Load pretrained RAFT model
            # Use progress=False to avoid threading issues on Windows
            self.model = torchvision.models.optical_flow.raft_large(
                pretrained=True,
                progress=False,
            )
            self.model = self.model.to(self.device)
            self.model.eval()
            self._model_loaded = True

            logger.info(f"Loaded RAFT model on {self.device}")

        except ImportError as e:
            raise RuntimeError(
                f"Failed to import required modules: {e}. "
                "Install with: pip install torch torchvision"
            )
        except RuntimeError as e:
            # Catch RAFT model loading issues
            logger.warning(f"Failed to load RAFT model: {e}")
            raise RuntimeError(f"Failed to load RAFT model: {e}") from e
        except Exception as e:
            # Catch threading/access violations
            logger.warning(f"Failed to load RAFT model (possible threading issue): {e}")
            raise RuntimeError(
                f"Failed to load RAFT model: {e}. "
                "This may be a threading or CUDA/CPU compatibility issue."
            ) from e

    def get_device(self) -> str:
        """Get device name."""
        return self.device

    def _resize_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, Tuple[int, int]]:
        """Resize frame to target resolution, maintaining aspect ratio.

        Args:
            frame: Input frame (H×W×3, uint8, BGR).

        Returns:
            Tuple of (resized_frame, original_size).
        """
        import cv2

        h, w = frame.shape[:2]
        original_size = (h, w)

        if self.resolution == "480":
            # 480p: scale height to 480
            target_h = 480
            scale = target_h / h
            target_w = int(w * scale)
        else:
            # 1080p: scale height to 1080
            target_h = 1080
            scale = target_h / h
            target_w = int(w * scale)

        # Ensure dimensions are divisible by 8 (RAFT requirement)
        target_h = (target_h // 8) * 8
        target_w = (target_w // 8) * 8

        resized = cv2.resize(frame, (target_w, target_h), interpolation=cv2.INTER_LINEAR)
        return resized, original_size

    def _upscale_flow(
        self,
        flow: np.ndarray,
        original_size: Tuple[int, int],
    ) -> np.ndarray:
        """Upscale flow map to original frame size.

        Args:
            flow: Flow map (H×W×2).
            original_size: Original frame size (H, W).

        Returns:
            Upscaled flow map.
        """
        import cv2

        h, w = original_size
        flow_h, flow_w = flow.shape[:2]

        # Compute upscaling factors
        scale_y = h / flow_h
        scale_x = w / flow_w

        # Upscale flow
        upscaled = cv2.resize(flow, (w, h), interpolation=cv2.INTER_LINEAR)

        # Scale flow vectors by upscaling factors
        upscaled[..., 0] *= scale_x  # x-component
        upscaled[..., 1] *= scale_y  # y-component

        return upscaled

    async def compute_flow(
        self,
        frame1: np.ndarray,
        frame2: np.ndarray,
    ) -> np.ndarray:
        """Compute optical flow between two frames.

        Args:
            frame1: First frame (H×W×3, uint8, BGR).
            frame2: Second frame (H×W×3, uint8, BGR).

        Returns:
            Optical flow map (H×W×2, float32).

        Raises:
            ValueError: If frames have different shapes or invalid format.
            RuntimeError: If model fails to compute flow.
        """
        import torch

        if frame1.shape != frame2.shape:
            raise ValueError(
                f"Frames must have same shape, got {frame1.shape} vs {frame2.shape}"
            )

        try:
            # Load model if not already loaded (synchronous to avoid threading issues)
            self._lazy_load_model()

            # Resize to target resolution
            frame1_resized, original_size = await asyncio.to_thread(
                self._resize_frame, frame1
            )
            frame2_resized, _ = await asyncio.to_thread(self._resize_frame, frame2)

            # Convert to torch tensors (HxWx3 -> 1x3xHxW, normalize to [0, 1])
            img1_t = torch.from_numpy(frame1_resized).float() / 255.0
            img2_t = torch.from_numpy(frame2_resized).float() / 255.0

            # Permute to batch format: (1, 3, H, W)
            img1_t = img1_t.permute(2, 0, 1).unsqueeze(0).to(self.device)
            img2_t = img2_t.permute(2, 0, 1).unsqueeze(0).to(self.device)

            # Compute flow on device
            with torch.no_grad():
                flow = await asyncio.to_thread(
                    self._compute_flow_on_device,
                    img1_t,
                    img2_t,
                )

            # Upscale to original size
            flow_upscaled = await asyncio.to_thread(
                self._upscale_flow,
                flow,
                original_size,
            )

            return flow_upscaled

        except Exception as e:
            logger.error(f"Failed to compute optical flow: {e}", exc_info=True)
            raise

    def _compute_flow_on_device(
        self,
        img1: "torch.Tensor",
        img2: "torch.Tensor",
    ) -> np.ndarray:
        """Compute flow on device (synchronous GPU operation).

        Args:
            img1: Batch of images (B×3×H×W, float32, [0, 1]).
            img2: Batch of images (B×3×H×W, float32, [0, 1]).

        Returns:
            Flow map (H×W×2, float32).
        """
        with self.model.eval():
            flow_list = self.model(img1, img2)
            flow = flow_list[-1]  # Take final flow prediction

        # Convert to numpy: (1, 2, H, W) -> (H, W, 2)
        flow_np = flow[0].permute(1, 2, 0).cpu().numpy().astype(np.float32)

        return flow_np
