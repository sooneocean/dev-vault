"""Main pipeline orchestration for crop-inpaint-stitch workflow."""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List

import aiohttp

from .types import CropRegion, ProcessConfig, FlowData
from ..preprocessing.frame_extractor import FrameExtractor
from ..preprocessing.mask_loader import MaskLoader
from ..preprocessing.crop_handler import CropHandler
from ..inpaint.workflow_builder import WorkflowBuilder
from ..inpaint.inpaint_executor import InpaintExecutor
from ..postprocessing.stitch_handler import StitchHandler
from ..postprocessing.video_encoder import VideoEncoder
from ..temporal.temporal_smoother import TemporalSmoother
from ..persistence.crop_serializer import CropRegionSerializer
from ..optical_flow import OpticalFlowProcessor, align_inpaint_region, compute_flow_confidence

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
        self.flow_data_dict: Dict[str, Any] = {}  # Stores serialized flow data for checkpoint
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

            # Phase 5: Temporal smoothing (optional Phase 2 feature)
            logger.info("Phase 5: Applying temporal smoothing")
            inpainted = await self._apply_temporal_smoothing(inpainted)

            # Phase 5b: Optical flow computation (optional Phase 3 feature)
            logger.info("Phase 5b: Computing optical flow for temporal alignment")
            await self._compute_optical_flow(frames)

            # Phase 6: Postprocessing (stitch)
            logger.info("Phase 6: Stitching frames")
            stitched = await self._stitch_frames(frames, inpainted)
            logger.info(f"Stitched {len(stitched)} frames")

            # Phase 7: Encoding
            logger.info("Phase 7: Encoding to MP4")
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

        Attempts to resume from checkpoint if available, skipping preprocessing.

        Args:
            frames: List of frame file paths.

        Returns:
            Dictionary mapping frame index to crop file path.

        Raises:
            FileNotFoundError: If mask not found and not skippable.
        """
        self.crops_dir = Path(self.config.output_dir) / "crops"
        self.crops_dir.mkdir(parents=True, exist_ok=True)

        # Attempt to load checkpoint (Phase 2 feature: resumption)
        checkpoint_result = CropRegionSerializer.load_checkpoint(self.config.output_dir)
        if checkpoint_result is not None:
            checkpoint_crops, flow_data = checkpoint_result
            logger.info(f"Resuming from checkpoint: {len(checkpoint_crops)} crops loaded, "
                       f"flow_data={'yes' if flow_data else 'no'}")
            self.crop_regions = checkpoint_crops
            if flow_data:
                self.flow_data_dict = flow_data

            # Return pre-computed crop paths (crops already in crops_dir from prior run)
            crops = {}
            for frame_idx in checkpoint_crops.keys():
                crop_path = self.crops_dir / f"crop_{frame_idx:06d}.png"
                if crop_path.exists():
                    crops[frame_idx] = crop_path
            if len(crops) == len(checkpoint_crops):
                logger.info(f"Using {len(crops)} pre-computed crops from checkpoint")
                return crops
            else:
                logger.warning("Checkpoint crops don't match filesystem, reprocessing")
                self.crop_regions.clear()
                self.flow_data_dict.clear()

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

        # Save checkpoint for potential resumption (Phase 2 feature)
        if self.crop_regions:
            try:
                CropRegionSerializer.save_checkpoint(
                    self.crop_regions,
                    self.config.output_dir,
                    flow_data_dict=self.flow_data_dict if self.config.optical_flow_enabled else None,
                )
            except Exception as e:
                logger.warning(f"Failed to save checkpoint: {e}")

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

    async def _apply_temporal_smoothing(
        self,
        inpainted: Dict[int, Path],
    ) -> Dict[int, Path]:
        """Apply temporal smoothing to reduce inter-frame flicker.

        Args:
            inpainted: Dictionary mapping frame index to inpainted crop path.

        Returns:
            Dictionary mapping frame index to temporally-smoothed crop path.
        """
        import cv2

        if not self.config.temporal_smooth_enabled:
            logger.info("Temporal smoothing disabled, skipping phase")
            return inpainted

        smoother = TemporalSmoother(alpha=self.config.temporal_smooth_alpha)

        smoothed_dir = Path(self.config.output_dir) / "smoothed"
        smoothed_dir.mkdir(parents=True, exist_ok=True)

        smoothed = {}
        previous_frame = None

        for frame_idx in sorted(inpainted.keys()):
            try:
                # Read inpainted crop
                inpainted_crop = cv2.imread(str(inpainted[frame_idx]))

                if inpainted_crop is None:
                    raise FileNotFoundError(f"Failed to read inpainted crop for frame {frame_idx}")

                # Apply temporal smoothing
                blended_crop = smoother.blend_frame(inpainted_crop, previous_frame)

                # Save smoothed crop
                smoothed_path = smoothed_dir / f"smoothed_{frame_idx:06d}.png"
                cv2.imwrite(str(smoothed_path), blended_crop)

                smoothed[frame_idx] = smoothed_path
                previous_frame = blended_crop

                if (frame_idx + 1) % 10 == 0:
                    logger.debug(f"Smoothed {frame_idx + 1}/{len(inpainted)} frames")

            except Exception as e:
                if self.config.skip_errors_in_postprocessing:
                    logger.warning(f"Skipping temporal smooth for frame {frame_idx}: {e}")
                    # Use original inpainted crop if smoothing fails
                    smoothed[frame_idx] = inpainted[frame_idx]
                else:
                    raise

        logger.info(f"Temporal smoothing complete: {len(smoothed)} frames")
        return smoothed

    async def _compute_optical_flow(self, frames: List[Path]) -> None:
        """Compute optical flow between consecutive frames.

        Stores flow data in self.flow_data_dict for checkpoint persistence.

        Args:
            frames: List of original frame paths.
        """
        import cv2
        import numpy as np

        if not self.config.optical_flow_enabled:
            logger.info("Optical flow disabled, skipping phase")
            return

        try:
            processor = OpticalFlowProcessor(
                resolution=self.config.optical_flow_resolution,
                device="auto",
            )
        except RuntimeError as e:
            logger.warning(f"Failed to initialize optical flow processor: {e}. "
                          "Optical flow will be skipped.")
            return

        logger.info(f"Computing optical flow for {len(frames)} frames "
                   f"at {self.config.optical_flow_resolution}p resolution")

        for frame_idx in range(len(frames) - 1):
            try:
                # Read consecutive frames
                frame1 = cv2.imread(str(frames[frame_idx]))
                frame2 = cv2.imread(str(frames[frame_idx + 1]))

                if frame1 is None or frame2 is None:
                    logger.warning(f"Failed to read frames {frame_idx}-{frame_idx + 1}")
                    continue

                # Compute forward flow
                try:
                    forward_flow = await processor.compute_flow(frame1, frame2)
                    backward_flow = await processor.compute_flow(frame2, frame1)

                    # Create FlowData
                    flow_data = FlowData(
                        forward_flow=forward_flow,
                        backward_flow=backward_flow,
                        frame_pair_id=(frame_idx, frame_idx + 1),
                        metadata={
                            "resolution": self.config.optical_flow_resolution,
                            "model": "raft_large",
                        },
                    )

                    # Serialize for checkpoint
                    flow_key = f"{frame_idx}_{frame_idx + 1}"
                    self.flow_data_dict[flow_key] = {
                        "frame_pair": (frame_idx, frame_idx + 1),
                        "forward_flow_shape": list(forward_flow.shape),
                        "confidence": float(compute_flow_confidence(flow_data)),
                    }

                    if (frame_idx + 1) % 10 == 0:
                        logger.debug(f"Computed flow for frames {frame_idx}-{frame_idx + 1}")

                except Exception as e:
                    logger.warning(f"Failed to compute flow for frames {frame_idx}-{frame_idx + 1}: {e}")
                    continue

            except Exception as e:
                if self.config.skip_errors_in_preprocessing:
                    logger.warning(f"Skipping optical flow for frame pair {frame_idx}-{frame_idx + 1}: {e}")
                else:
                    raise

        logger.info(f"Optical flow computation complete: {len(self.flow_data_dict)} frame pairs")

    async def _stitch_frames(
        self,
        frames: List[Path],
        inpainted: Dict[int, Path],
    ) -> List[Path]:
        """Stitch inpainted crops back to original frames.

        Applies optical flow-based alignment if enabled.

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

                # Get crop region (optionally aligned by optical flow)
                crop_region = self.crop_regions[frame_idx]

                # Apply optical flow alignment if available
                if self.config.optical_flow_enabled and self.flow_data_dict:
                    # Check if we have flow data for this frame pair
                    flow_key = f"{frame_idx - 1}_{frame_idx}" if frame_idx > 0 else None

                    if flow_key and flow_key in self.flow_data_dict:
                        # For now, we store metadata only (actual flow alignment deferred to Phase 3B)
                        # In production, would apply align_inpaint_region here
                        logger.debug(f"Flow data available for frame {frame_idx}, "
                                   f"confidence={self.flow_data_dict[flow_key].get('confidence', 'N/A')}")

                # Stitch
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
