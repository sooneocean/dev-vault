"""Florence-2 vision language model for intelligent watermark localization.

Uses CAPTION_TO_PHRASE_GROUNDING task to detect watermark regions
and generates smooth masks for inpainting.
"""

import logging
import numpy as np
import cv2
from typing import Tuple, Optional, List
from PIL import Image

logger = logging.getLogger(__name__)


class Florence2Detector:
    """Detect watermarks using Florence-2 vision language model.

    Uses CAPTION_TO_PHRASE_GROUNDING task to locate watermarks,
    text, logos, and other artifacts in images.

    Attributes:
        confidence_threshold: Minimum confidence to accept detection (0-1)
        model: Lazy-loaded Florence-2 model instance
        processor: Lazy-loaded Florence-2 processor instance
        device: Target device ("cuda" or "cpu")
    """

    WATERMARK_PROMPT = (
        "<CAPTION_TO_PHRASE_GROUNDING> watermark text logo "
        "copyright branding overlay symbol badge stamp"
    )

    def __init__(
        self,
        confidence_threshold: float = 0.5,
        device: Optional[str] = None,
    ):
        """Initialize Florence-2 detector.

        Args:
            confidence_threshold: Minimum confidence for detections (0.3-0.9)
            device: Target device ("cuda", "cpu", or None for auto-detect)
        """
        self.confidence_threshold = confidence_threshold
        self.device = device or self._detect_device()
        self.model = None
        self.processor = None
        self._model_loaded = False

        logger.info(
            f"Florence2Detector initialized on {self.device}, "
            f"confidence_threshold={confidence_threshold}"
        )

    @staticmethod
    def _detect_device() -> str:
        """Auto-detect available device."""
        try:
            import torch

            return "cuda" if torch.cuda.is_available() else "cpu"
        except ImportError:
            return "cpu"

    def _lazy_load_model(self) -> None:
        """Lazily load Florence-2 model (only when first needed)."""
        if self._model_loaded:
            return

        try:
            from transformers import AutoProcessor, AutoModelForCausalLM
            import torch

            logger.info(f"Loading Florence-2-large on {self.device}...")

            self.processor = AutoProcessor.from_pretrained(
                "microsoft/Florence-2-large", trust_remote_code=True
            )

            self.model = AutoModelForCausalLM.from_pretrained(
                "microsoft/Florence-2-large",
                device_map="auto",
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                trust_remote_code=True,
            )

            self.model.eval()
            self._model_loaded = True
            logger.info("Florence-2-large loaded successfully")

        except ImportError as e:
            raise RuntimeError(
                f"Florence-2 requires transformers. Install with: "
                f"pip install transformers torch pillow"
            ) from e
        except Exception as e:
            raise RuntimeError(f"Failed to load Florence-2 model: {e}") from e

    def detect(
        self, image_pil: Image.Image
    ) -> Tuple[np.ndarray, List[Tuple[int, int, int, int]]]:
        """Detect watermarks in image and generate mask.

        Args:
            image_pil: Input image as PIL Image

        Returns:
            Tuple of (smooth_mask, bboxes) where:
            - smooth_mask: np.ndarray (H, W) grayscale 0-255 for inpainting
            - bboxes: List of (x, y, w, h) in pixel coordinates

        Raises:
            RuntimeError: If model loading or inference fails
        """
        if image_pil is None or image_pil.size[0] == 0 or image_pil.size[1] == 0:
            logger.warning("Empty image provided to Florence-2 detector")
            return self._empty_mask(image_pil.size if image_pil else (512, 512)), []

        try:
            self._lazy_load_model()

            # Run inference
            with __import__("torch").no_grad():
                inputs = self.processor(
                    text=self.WATERMARK_PROMPT,
                    images=image_pil,
                    return_tensors="pt",
                ).to(self.device)

                generated_ids = self.model.generate(
                    input_ids=inputs["input_ids"],
                    pixel_values=inputs["pixel_values"],
                    max_new_tokens=512,
                    do_sample=False,
                )

            output_text = self.processor.batch_decode(generated_ids, skip_special_tokens=False)[0]

            # Parse bboxes from output
            bboxes = self._parse_grounding_output(output_text, image_pil.size)

            if not bboxes:
                logger.info("No watermarks detected")
                return self._empty_mask(image_pil.size), []

            # Generate mask from bboxes
            mask_binary = self._generate_mask_from_bboxes(bboxes, image_pil.size)

            # Smooth mask with morphological operations + Gaussian blur
            mask_smooth = self._smooth_mask(mask_binary)

            logger.info(f"Detected {len(bboxes)} watermark regions")
            return mask_smooth, bboxes

        except Exception as e:
            logger.error(f"Florence-2 inference failed: {e}")
            raise RuntimeError(f"Florence-2 detection failed: {e}") from e

    def _parse_grounding_output(
        self, output_text: str, image_size: Tuple[int, int]
    ) -> List[Tuple[int, int, int, int]]:
        """Parse Florence-2 GROUNDING output to extract bboxes.

        Args:
            output_text: Model output text containing bbox annotations
            image_size: (width, height) of original image

        Returns:
            List of (x, y, w, h) bboxes in pixel coordinates
        """
        bboxes = []

        try:
            # Florence-2 outputs bboxes as <GROUNDING><loc_?> tokens
            # Extract numeric values from model output (format varies by version)

            # Simple heuristic: look for patterns like "<loc_123><loc_456>"
            # More robust parsing would depend on exact Florence-2 output format

            import re

            # Pattern: <loc_X><loc_Y><loc_X+W><loc_Y+H>
            # where X, Y, W, H are numbers in [0, 1000] range (normalized to 1000)
            pattern = r"<loc_(\d+)>"
            matches = re.findall(pattern, output_text)

            if not matches or len(matches) < 4:
                logger.debug(f"No bbox patterns found in: {output_text[:100]}")
                return []

            # Group into sets of 4 (x_min, y_min, x_max, y_max)
            for i in range(0, len(matches) - 3, 4):
                try:
                    x_norm = int(matches[i]) / 1000.0
                    y_norm = int(matches[i + 1]) / 1000.0
                    x_max_norm = int(matches[i + 2]) / 1000.0
                    y_max_norm = int(matches[i + 3]) / 1000.0

                    # Clamp to [0, 1]
                    x_norm = max(0, min(1, x_norm))
                    y_norm = max(0, min(1, y_norm))
                    x_max_norm = max(0, min(1, x_max_norm))
                    y_max_norm = max(0, min(1, y_max_norm))

                    # Convert to pixel coordinates
                    w_img, h_img = image_size
                    x = int(x_norm * w_img)
                    y = int(y_norm * h_img)
                    w = int((x_max_norm - x_norm) * w_img)
                    h = int((y_max_norm - y_norm) * h_img)

                    # Validate bbox (non-zero size)
                    if w > 0 and h > 0:
                        bboxes.append((x, y, w, h))

                except (ValueError, IndexError):
                    continue

        except Exception as e:
            logger.debug(f"Failed to parse grounding output: {e}")

        return bboxes

    def _generate_mask_from_bboxes(
        self, bboxes: List[Tuple[int, int, int, int]], image_size: Tuple[int, int]
    ) -> np.ndarray:
        """Generate binary mask from bboxes.

        Args:
            bboxes: List of (x, y, w, h) bboxes
            image_size: (width, height)

        Returns:
            Binary mask (H, W, 3) uint8: 0=keep, 255=inpaint
        """
        w_img, h_img = image_size
        mask = np.zeros((h_img, w_img, 3), dtype=np.uint8)

        for x, y, w, h in bboxes:
            # Clamp to image bounds
            x1 = max(0, x)
            y1 = max(0, y)
            x2 = min(w_img, x + w)
            y2 = min(h_img, y + h)

            # Draw region (255 = inpaint area)
            mask[y1:y2, x1:x2] = 255

        return mask

    def _smooth_mask(self, mask_binary: np.ndarray) -> np.ndarray:
        """Smooth mask using morphological operations + Gaussian blur.

        Args:
            mask_binary: Binary mask (H, W, 3) with 0 or 255 values

        Returns:
            Smoothed mask (H, W) grayscale 0-255
        """
        # Convert to grayscale if needed
        if len(mask_binary.shape) == 3:
            mask_gray = cv2.cvtColor(mask_binary, cv2.COLOR_BGR2GRAY)
        else:
            mask_gray = mask_binary.copy()

        # Morphological closing: fill small holes
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask_closed = cv2.morphologyEx(mask_gray, cv2.MORPH_CLOSE, kernel, iterations=1)

        # Morphological opening: remove noise specks
        mask_opened = cv2.morphologyEx(mask_closed, cv2.MORPH_OPEN, kernel, iterations=1)

        # Selective dilation: expand slightly to cover watermark edges
        mask_dilated = cv2.dilate(mask_opened, kernel, iterations=1)

        # Gaussian blur: smooth edges for seamless inpainting
        mask_smooth = cv2.GaussianBlur(mask_dilated, (5, 5), sigmaX=0, sigmaY=0)

        return mask_smooth

    def _empty_mask(self, image_size: Tuple[int, int]) -> np.ndarray:
        """Generate all-white mask (no inpainting)."""
        w, h = image_size
        return np.full((h, w), 255, dtype=np.uint8)

    def cleanup(self) -> None:
        """Cleanup model from GPU memory."""
        if self.model is not None:
            try:
                import torch

                del self.model
                del self.processor
                torch.cuda.empty_cache()
                self._model_loaded = False
                logger.info("Florence-2 model cleaned up")
            except Exception as e:
                logger.warning(f"Error during cleanup: {e}")
