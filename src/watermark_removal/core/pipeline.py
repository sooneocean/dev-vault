"""Main pipeline orchestration for crop-inpaint-stitch workflow."""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List

import aiohttp

from .types import CropRegion, ProcessConfig
from ..preprocessing.frame_extractor import FrameExtractor
from ..preprocessing.mask_loader import MaskLoader
from ..preprocessing.crop_handler import CropHandler
from ..inpaint.workflow_builder import WorkflowBuilder
from ..inpaint.inpaint_executor import InpaintExecutor
from ..postprocessing.stitch_handler import StitchHandler
from ..postprocessing.video_encoder import VideoEncoder

logger = logging.getLogger(__name__)


class Pipeline:
    """Orchestrate all layers of the watermark removal pipeline."""

    def __init__(self, config: ProcessConfig) -> None:
        """Initialize pipeline with configuration.

        Args:
            config: ProcessConfig with all pipeline parameters.
        """
        self.config = config
        self.crop_regions: Dict[int, CropRegion] = {}
        self.frames_dir: Path | None = None
        self.crops_dir: Path | None = None
        self.stitched_frames_dir: Path | None = None

    async def run(self) -> Dict[str, Any]:
        """Execute the full pipeline.

        Returns:
            Dictionary with pipeline summary:
            - frame_count: Number of frames processed
            - duration_seconds: Total execution time
            - output_path: Path to output video
            - inpaint_duration_seconds: Time spent inpainting
            - encode_duration_seconds: Time spent encoding
        """
        import time

        start_time = time.time()
        logger.info("Pipeline starting")

        try:
            # Phase 1: Extract frames
            logger.info("Phase 1: Extracting frames")
            frames = await self._extract_frames()
            logger.info(f"Extracted {len(frames)} frames")

            # Phase 2: Preprocessing (crop + mask)
            logger.info("Phase 2: Preprocessing crops")
            crops = await self._preprocess_crops(frames)
            logger.info(f"Prepared {len(crops)} crops for inpainting")

            # Phase 3: ComfyUI pre-flight checks
            logger.info("Phase 3: Running ComfyUI pre-flight checks")
            await self._comfyui_preflight()

            # Phase 4: Inpainting
            logger.info("Phase 4: Submitting crops to inpainting")
            inpaint_start = time.time()
            inpainted = await self._inpaint_crops(crops, frames)
            inpaint_duration = time.time() - inpaint_start
            logger.info(f"Inpainting complete in {inpaint_duration:.2f}s")

            # Phase 5: Postprocessing (stitch)
            logger.info("Phase 5: Stitching frames")
            stitched = await self._stitch_frames(frames, inpainted)
            logger.info(f"Stitched {len(stitched)} frames")

            # Phase 6: Encoding
            logger.info("Phase 6: Encoding to MP4")
            encode_start = time.time()
            output_path = await self._encode_video(stitched)
            encode_duration = time.time() - encode_start
            logger.info(f"Encoding complete in {encode_duration:.2f}s")

            # Cleanup
            await self._cleanup()

            total_duration = time.time() - start_time
            summary = {
                "frame_count": len(frames),
                "duration_seconds": total_duration,
                "output_path": str(output_path),
                "inpaint_duration_seconds": inpaint_duration,
                "encode_duration_seconds": encode_duration,
            }

            logger.info(f"Pipeline complete in {total_duration:.2f}s: {summary}")
            return summary

        except Exception as e:
            logger.error(f"Pipeline failed: {e}", exc_info=True)
            await self._cleanup()
            raise

    async def _extract_frames(self) -> List[Path]:
        """Extract frames from input video.

        Returns:
            List of frame file paths.

        Raises:
            FileNotFoundError: If input video not found.
        """
        video_path = Path(self.config.video_path)
        if not video_path.exists():
            raise FileNotFoundError(f"Input video not found: {video_path}")

        # Create frames directory
        self.frames_dir = Path(self.config.output_dir) / "frames"
        self.frames_dir.mkdir(parents=True, exist_ok=True)

        extractor = FrameExtractor()
        extractor.extract_frames(
            video_path=str(video_path),
            output_dir=str(self.frames_dir),
        )

        # Collect frame paths
        frames = sorted(self.frames_dir.glob("frame_*.png"))
        if not frames:
            raise FileNotFoundError(f"No frames extracted from {video_path}")

        logger.info(f"Extracted {len(frames)} frames to {self.frames_dir}")
        return frames

    async def _preprocess_crops(self, frames: List[Path]) -> Dict[int, Path]:
        """Preprocess each frame: load mask, crop, store metadata.

        Args:
            frames: List of frame file paths.

        Returns:
            Dictionary mapping frame index to crop file path.

        Raises:
            FileNotFoundError: If mask not found and not skippable.
        """
        self.crops_dir = Path(self.config.output_dir) / "crops"
        self.crops_dir.mkdir(parents=True, exist_ok=True)

        mask_loader = MaskLoader()
        crop_handler = CropHandler()

        crops = {}

        for frame_idx, frame_path in enumerate(frames):
            try:
                # Load mask for this frame
                mask = mask_loader.load_mask(
                    mask_path=self.config.mask_path,
                    frame_idx=frame_idx,
                    width=1920,  # Default, should come from frame metadata
                    height=1080,
                )

                # Crop region from config or from mask bounding box
                if self.config.crop_region:
                    crop_region = self.config.crop_region
                else:
                    # Derive from mask bounding box (Phase 2 feature)
                    crop_region = self._region_from_mask(mask)

                # Crop + resize + pad
                crop_img = crop_handler.extract_and_pad(
                    frame_path=str(frame_path),
                    crop_region=crop_region,
                )

                # Save crop
                crop_path = self.crops_dir / f"crop_{frame_idx:06d}.png"
                import cv2

                cv2.imwrite(str(crop_path), crop_img)

                # Store CropRegion metadata
                self.crop_regions[frame_idx] = crop_region

                crops[frame_idx] = crop_path

                if (frame_idx + 1) % 10 == 0:
                    logger.debug(f"Preprocessed {frame_idx + 1}/{len(frames)} frames")

            except FileNotFoundError as e:
                if self.config.skip_errors_in_preprocessing:
                    logger.warning(f"Skipping frame {frame_idx}: {e}")
                else:
                    raise

        logger.info(f"Preprocessed {len(crops)} frames")
        return crops

    def _region_from_mask(self, mask) -> CropRegion:
        """Derive CropRegion from mask bounding box.

        Args:
            mask: Numpy array (HxW, uint8).

        Returns:
            CropRegion with derived bounding box.
        """
        import numpy as np

        # Find non-zero region in mask
        coords = np.argwhere(mask > 0)
        if len(coords) == 0:
            raise ValueError("Mask has no non-zero pixels")

        y_min, x_min = coords.min(axis=0)
        y_max, x_max = coords.max(axis=0)

        width = x_max - x_min
        height = y_max - y_min

        return CropRegion(
            x=int(x_min),
            y=int(y_min),
            w=width,
            h=height,
            scale_factor=2.0,
            context_x=int(x_min) - 50,
            context_y=int(y_min) - 50,
            context_w=width + 100,
            context_h=height + 100,
            pad_left=362,
            pad_top=362,
            pad_right=362,
            pad_bottom=362,
        )

    async def _comfyui_preflight(self) -> None:
        """Run ComfyUI pre-flight checks.

        Raises:
            RuntimeError: If ComfyUI not reachable or model not found.
        """
        host = self.config.comfyui_host
        port = self.config.comfyui_port

        # Health check
        try:
            async with aiohttp.ClientSession() as session:
                url = f"http://{host}:{port}/system"
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    if resp.status != 200:
                        raise RuntimeError(
                            f"ComfyUI health check failed: {resp.status}"
                        )
                logger.info(f"ComfyUI reachable at {host}:{port}")
        except Exception as e:
            raise RuntimeError(
                f"ComfyUI not reachable at {host}:{port}: {e}"
            ) from e

        # Model check (Phase 2 feature - for now, just log a warning if needed)
        logger.info("ComfyUI pre-flight checks passed")

    async def _inpaint_crops(
        self,
        crops: Dict[int, Path],
        frames: List[Path],
    ) -> Dict[int, Path]:
        """Submit crops to inpainting executor.

        Args:
            crops: Dictionary mapping frame index to crop file path.
            frames: List of original frame paths (for mask generation).

        Returns:
            Dictionary mapping frame index to inpainted crop file path.
        """
        executor = InpaintExecutor(
            host=self.config.comfyui_host,
            port=self.config.comfyui_port,
        )

        inpainted_dir = Path(self.config.output_dir) / "inpainted"
        inpainted_dir.mkdir(parents=True, exist_ok=True)

        # Prepare (image, mask) pairs
        pairs = []
        crop_indices = []
        for frame_idx in sorted(crops.keys()):
            crop_path = crops[frame_idx]
            mask_path = Path(self.config.output_dir) / "masks" / f"mask_{frame_idx:06d}.png"

            # Create mask file if needed (Phase 1 simplification: reuse original mask)
            if not mask_path.exists():
                mask_path.parent.mkdir(parents=True, exist_ok=True)
                import shutil

                shutil.copy(self.config.mask_path, mask_path)

            pairs.append((str(crop_path), str(mask_path)))
            crop_indices.append(frame_idx)

        # Submit batch
        results = await executor.inpaint_batch(
            image_mask_pairs=pairs,
            config=self.config.inpaint,
            output_dir=str(inpainted_dir),
            batch_size=self.config.batch_size,
        )

        # Map results back to frame indices
        inpainted = {}
        for idx, (frame_idx, result_path) in enumerate(zip(crop_indices, results)):
            inpainted[frame_idx] = result_path

        logger.info(f"Inpainted {len(inpainted)} crops")
        return inpainted

    async def _stitch_frames(
        self,
        frames: List[Path],
        inpainted: Dict[int, Path],
    ) -> List[Path]:
        """Stitch inpainted crops back to original frames.

        Args:
            frames: List of original frame paths.
            inpainted: Dictionary mapping frame index to inpainted crop path.

        Returns:
            List of stitched frame paths in order.
        """
        import cv2
        import numpy as np

        self.stitched_frames_dir = Path(self.config.output_dir) / "stitched"
        self.stitched_frames_dir.mkdir(parents=True, exist_ok=True)

        handler = StitchHandler(blend_feather_width=self.config.blend_feather_width)

        stitched = []

        for frame_idx, frame_path in enumerate(frames):
            if frame_idx not in inpainted:
                logger.warning(f"No inpainted crop for frame {frame_idx}, skipping")
                continue

            try:
                # Read frames
                original = cv2.imread(str(frame_path))
                inpainted_crop = cv2.imread(str(inpainted[frame_idx]))

                if original is None or inpainted_crop is None:
                    raise FileNotFoundError(f"Failed to read frames for frame {frame_idx}")

                # Stitch
                crop_region = self.crop_regions[frame_idx]
                stitched_frame = handler.stitch_back(original, inpainted_crop, crop_region)

                # Save
                stitched_path = self.stitched_frames_dir / f"frame_{frame_idx:06d}.png"
                cv2.imwrite(str(stitched_path), stitched_frame)

                stitched.append(stitched_path)

                if (frame_idx + 1) % 10 == 0:
                    logger.debug(f"Stitched {frame_idx + 1}/{len(frames)} frames")

            except Exception as e:
                if self.config.skip_errors_in_postprocessing:
                    logger.warning(f"Skipping stitch for frame {frame_idx}: {e}")
                else:
                    raise

        logger.info(f"Stitched {len(stitched)} frames")
        return stitched

    async def _encode_video(self, frames: List[Path]) -> Path:
        """Encode stitched frames to MP4.

        Args:
            frames: List of stitched frame paths in order.

        Returns:
            Path to output video file.
        """
        output_path = Path(self.config.output_dir) / "output.mp4"

        encoder = VideoEncoder()

        output = await asyncio.get_event_loop().run_in_executor(
            None,
            encoder.encode_frames_to_video,
            str(self.stitched_frames_dir),
            str(output_path),
            self.config.output_fps,
            self.config.output_codec,
            self.config.output_crf,
        )

        logger.info(f"Encoded video to {output}")
        return output

    async def _cleanup(self) -> None:
        """Clean up temporary directories if configured."""
        if not self.config.keep_intermediate:
            import shutil

            dirs_to_clean = [
                self.crops_dir,
                Path(self.config.output_dir) / "masks",
                Path(self.config.output_dir) / "inpainted",
                self.stitched_frames_dir,
                self.frames_dir,
            ]

            for directory in dirs_to_clean:
                if directory and directory.exists():
                    try:
                        shutil.rmtree(directory)
                        logger.debug(f"Cleaned {directory}")
                    except Exception as e:
                        logger.warning(f"Failed to clean {directory}: {e}")

        # Clear in-memory crop regions
        self.crop_regions.clear()
        logger.debug("Cleared crop regions")
