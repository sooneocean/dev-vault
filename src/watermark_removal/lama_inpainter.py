"""LaMa fast inpainting engine with Gaussian tiling for 4K+ support."""

import logging
import numpy as np
import torch
import torch.nn.functional as F
from typing import Tuple, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .memory_manager import MemoryManager

logger = logging.getLogger(__name__)


class LamaInpainter:
    """Fast watermark removal using LaMa model with tiling support.

    LaMa uses Fourier convolutions for resolution-robust inpainting.
    Supports both full-image (≤2K) and tiling (>2K) inference.
    """

    def __init__(
        self,
        device: str = "cuda",
        tile_size: int = 512,
        overlap: int = 64,
        memory_manager: Optional["MemoryManager"] = None,
    ):
        """Initialize LaMa inpainter.

        Args:
            device: "cuda" or "cpu"
            tile_size: Tile size for high-res processing (512)
            overlap: Tile overlap for seamless blending (64px = 12.5%)
            memory_manager: Optional MemoryManager for GPU lifecycle management
        """
        self.device = device
        self.tile_size = tile_size
        self.overlap = overlap
        self.stride = tile_size - overlap
        self.memory_manager = memory_manager
        self.model = None
        self._model_loaded = False

    def load_model(self) -> None:
        """Load LaMa model from HuggingFace."""
        if self._model_loaded:
            return

        try:
            from transformers import AutoModelForImageInpainting

            logger.info("Loading LaMa model...")
            self.model = AutoModelForImageInpainting.from_pretrained(
                "timm/lama",
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32
            )
            self.model.to(self.device)
            self.model.eval()
            self._model_loaded = True

            # Register with MemoryManager if provided
            if self.memory_manager:
                self.memory_manager.load_model("lama", self.model)

            logger.info("LaMa model loaded successfully")
        except Exception as e:
            raise RuntimeError(f"Failed to load LaMa model: {e}") from e

    def inpaint(self, image: np.ndarray, mask: np.ndarray) -> np.ndarray:
        """Inpaint watermarked region in image.

        Args:
            image: Input image (H, W, 3) uint8 0-255
            mask: Inpaint mask (H, W) uint8, 255=inpaint, 0=keep

        Returns:
            Inpainted image (H, W, 3) uint8
        """
        if not self._model_loaded:
            self.load_model()

        h, w = image.shape[:2]

        # Decide path based on resolution
        if max(h, w) <= 2048:
            return self._inpaint_full_image(image, mask)
        else:
            return self._inpaint_with_tiling(image, mask)

    def _inpaint_full_image(self, image: np.ndarray, mask: np.ndarray) -> np.ndarray:
        """Inpaint full image (fast path for ≤2K)."""
        image_t = self._preprocess(image)
        mask_t = self._preprocess_mask(mask)

        with torch.no_grad():
            output = self.model(image_t, mask_t)

        return self._postprocess(output)

    def _inpaint_with_tiling(self, image: np.ndarray, mask: np.ndarray) -> np.ndarray:
        """Inpaint with tiling for high-resolution (>2K)."""
        h, w = image.shape[:2]

        # Extract overlapping tiles
        tiles_img = self._extract_tiles(image, self.tile_size, self.stride)
        tiles_mask = self._extract_tiles(mask, self.tile_size, self.stride)
        tile_coords = self._get_tile_coords(h, w, self.tile_size, self.stride)

        # Inpaint each tile
        inpainted_tiles = []
        for tile_img, tile_mask in zip(tiles_img, tiles_mask):
            with torch.no_grad():
                tile_img_t = self._preprocess(tile_img)
                tile_mask_t = self._preprocess_mask(tile_mask)
                inpainted = self.model(tile_img_t, tile_mask_t)
                inpainted_tiles.append(self._postprocess(inpainted))

        # Reconstruct with Gaussian blending
        return self._reconstruct_from_tiles(
            inpainted_tiles, tile_coords, (h, w), self.tile_size
        )

    def _extract_tiles(
        self, image: np.ndarray, tile_size: int, stride: int
    ) -> list:
        """Extract overlapping tiles from image."""
        h, w = image.shape[:2] if len(image.shape) == 2 else image.shape[:2]
        tiles = []

        for y in range(0, h - self.overlap, stride):
            for x in range(0, w - self.overlap, stride):
                y_end = min(y + tile_size, h)
                x_end = min(x + tile_size, w)

                if len(image.shape) == 3:
                    tile = image[y:y_end, x:x_end, :]
                else:
                    tile = image[y:y_end, x:x_end]

                tiles.append(tile)

        return tiles

    def _get_tile_coords(
        self, h: int, w: int, tile_size: int, stride: int
    ) -> list:
        """Get (y, x, y_end, x_end) coordinates for each tile."""
        coords = []

        for y in range(0, h - self.overlap, stride):
            for x in range(0, w - self.overlap, stride):
                y_end = min(y + tile_size, h)
                x_end = min(x + tile_size, w)
                coords.append((y, x, y_end, x_end))

        return coords

    def _create_gaussian_window(self, size: int) -> np.ndarray:
        """Create 2D Gaussian window for tile blending."""
        # 1D Gaussian
        gauss_1d = np.exp(-np.linspace(-2, 2, size) ** 2 / 0.5)
        # 2D Gaussian (outer product)
        gaussian_2d = gauss_1d[:, None] * gauss_1d[None, :]
        return gaussian_2d / gaussian_2d.max()

    def _reconstruct_from_tiles(
        self,
        tiles: list,
        coords: list,
        output_shape: Tuple[int, int],
        tile_size: int,
    ) -> np.ndarray:
        """Reconstruct image from overlapping tiles with Gaussian blending."""
        h, w = output_shape
        output = np.zeros((h, w, 3), dtype=np.float32)
        weight_map = np.zeros((h, w), dtype=np.float32)

        gaussian_weights = self._create_gaussian_window(tile_size)

        for tile, (y, x, y_end, x_end) in zip(tiles, coords):
            tile_h, tile_w = tile.shape[:2]

            # Adjust weights for edge tiles
            w_gauss = gaussian_weights[:tile_h, :tile_w]

            # Accumulate weighted tile
            output[y:y_end, x:x_end] += tile * w_gauss[:, :, None]
            weight_map[y:y_end, x:x_end] += w_gauss

        # Normalize by accumulated weight
        weight_map = np.maximum(weight_map, 1e-8)
        output = output / weight_map[:, :, None]

        return np.clip(output, 0, 255).astype(np.uint8)

    def _preprocess(self, image: np.ndarray) -> torch.Tensor:
        """Preprocess image for model input."""
        # Normalize to [-1, 1]
        img_float = image.astype(np.float32) / 255.0
        img_float = img_float * 2.0 - 1.0

        # HWC -> CHW
        img_chw = img_float.transpose(2, 0, 1)

        # Add batch dim
        img_batch = np.expand_dims(img_chw, 0)

        return torch.from_numpy(img_batch).to(self.device)

    def _preprocess_mask(self, mask: np.ndarray) -> torch.Tensor:
        """Preprocess mask for model input."""
        # Ensure uint8 range 0-255, invert so 0=keep, 1=inpaint
        if mask.max() > 1:
            mask_norm = mask.astype(np.float32) / 255.0
        else:
            mask_norm = mask.astype(np.float32)

        # Invert: 255->0, 0->1 (LaMa expects 1 = inpaint region)
        mask_inv = 1.0 - (mask_norm > 0.5).astype(np.float32)

        # Add channel dim (1, H, W)
        mask_chw = np.expand_dims(mask_inv, 0)

        # Add batch dim
        mask_batch = np.expand_dims(mask_chw, 0)

        return torch.from_numpy(mask_batch).to(self.device)

    def _postprocess(self, tensor: torch.Tensor) -> np.ndarray:
        """Postprocess model output to image."""
        # Remove batch dim
        output = tensor.squeeze(0)

        # CHW -> HWC
        output = output.permute(1, 2, 0)

        # Detach and move to CPU
        output = output.detach().cpu().numpy()

        # Denormalize from [-1, 1] to [0, 255]
        output = (output + 1.0) / 2.0 * 255.0
        output = np.clip(output, 0, 255).astype(np.uint8)

        return output

    def cleanup(self) -> None:
        """Cleanup model from GPU."""
        if self.model is not None:
            # Unregister from MemoryManager if provided
            if self.memory_manager:
                self.memory_manager.unload_model("lama")

            del self.model
            torch.cuda.empty_cache()
            self._model_loaded = False
            logger.info("LaMa model cleaned up")
