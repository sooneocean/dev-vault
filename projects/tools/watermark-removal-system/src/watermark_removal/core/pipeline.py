"""
Main pipeline orchestration for watermark removal.

Coordinates all layers: preprocessing, inpaint, postprocessing, encoding.
Manages CropRegion persistence, async batch processing, and error handling.
"""

import logging
import asyncio
from pathlib import Path
from datetime import datetime
from typing import List, Optional
import numpy as np

from .types import ProcessConfig, CropRegion


logger = logging.getLogger(__name__)


class Pipeline:
    """Orchestrate all layers of watermark removal pipeline."""

    def __init__(self, config: ProcessConfig):
        """
        Initialize pipeline with configuration.

        Args:
            config: ProcessConfig object with all parameters
        """
        self.config = config
        self.start_time = None
        self.crop_regions: List[CropRegion] = []  # In-memory persistence
        self.inpaint_times: List[float] = []  # Track per-frame inpaint duration

    async def run(self) -> dict:
        """
        Run complete watermark removal pipeline.

        Phases:
        1. [Phase 2] Checkpoint resumption if available
        2. Extract frames from video
        3. For each frame: load mask, crop, save crop metadata, store CropRegion
        4. Pre-flight ComfyUI checks
        5. Submit all crops to inpaint executor (async batch)
        6. For each inpainted crop: stitch, blend, save stitched frame
        7. [Phase 2] Temporal smoothing if enabled
        8. Encode stitched frames to MP4
        9. [Phase 2] Save checkpoint on completion
        10. Log summary and return results

        Returns:
            Summary dict with results and timing:
            - status: "success" or "error"
            - output_video: Path to output MP4
            - duration_sec: Total execution time
            - frames_processed: Number of frames processed
            - inpaint_duration_sec: Total inpaint execution time
            - crops_created: Number of crop regions created
        """
        # Lazy imports to avoid requiring OpenCV/scipy at module load time
        from ..preprocessing.frame_extractor import FrameExtractor
        from ..preprocessing.mask_loader import MaskLoader
        from ..preprocessing.crop_handler import CropHandler
        from ..preprocessing.watermark_tracker import BboxTracker
        from ..inpaint.inpaint_executor import InpaintExecutor
        from ..postprocessing.stitch_handler import StitchHandler
        from ..postprocessing.video_encoder import VideoEncoder
        from ..postprocessing.temporal_smoother import TemporalSmoother
        from ..postprocessing.adaptive_temporal_smoother import AdaptiveTemporalSmoother
        from ..postprocessing.poisson_blender import PoissonBlender
        from ..utils.image_io import read_image, write_image
        from .checkpoint import CheckpointManager

        self.start_time = datetime.now()
        logger.info("Starting watermark removal pipeline")
        logger.info(f"Video: {self.config.video_path}")
        logger.info(f"Mask: {self.config.mask_path}")
        logger.info(f"Output: {self.config.output_dir}")

        # Phase 2: Checkpoint resumption
        checkpoint_manager = None
        if self.config.use_checkpoints:
            checkpoint_manager = CheckpointManager(self.config.checkpoint_dir)
            video_name = self.config.video_path.stem

            if self.config.resume_from_checkpoint:
                loaded_crops, processing_state = checkpoint_manager.load_crop_regions(video_name)
                if loaded_crops:
                    logger.info(f"Resuming from checkpoint: {len(loaded_crops)} crops already processed")
                    self.crop_regions = loaded_crops
                    # In Phase 2+, we'd resume from the inpaint phase
                    # For now, we log and continue normally
                else:
                    logger.info("No checkpoint found, starting fresh")

        try:
            # Ensure output directory exists
            self.config.output_dir.mkdir(parents=True, exist_ok=True)

            # Phase 1: Extract frames
            logger.info("=" * 60)
            logger.info("Phase 1: Frame Extraction")
            logger.info("=" * 60)
            frames_dir = self.config.output_dir / "frames_extracted"
            stitched_dir = self.config.output_dir / "frames_stitched"
            crops_dir = self.config.output_dir / "crops"

            frames_dir.mkdir(parents=True, exist_ok=True)
            stitched_dir.mkdir(parents=True, exist_ok=True)
            crops_dir.mkdir(parents=True, exist_ok=True)

            extractor = FrameExtractor(self.config.video_path, frames_dir)
            frames = extractor.extract_all()
            logger.info(f"Extracted {len(frames)} frames from video")

            # Phase 2: Preprocess (crop)
            logger.info("=" * 60)
            logger.info("Phase 2: Preprocessing (Cropping)")
            logger.info("=" * 60)

            crop_handler = CropHandler(
                target_size=self.config.target_inpaint_size,
                context_padding=self.config.context_padding,
            )
            mask_loader = MaskLoader()

            # Load mask file (auto-detect type)
            mask_data = mask_loader.load_mask(self.config.mask_path)
            if mask_data is None:
                raise RuntimeError(f"Failed to load mask: {self.config.mask_path}")

            # Determine mask type (image vs bbox sequence)
            is_image_mask = isinstance(mask_data, np.ndarray)
            bbox_dict = mask_data if not is_image_mask else None

            # Phase 2: Initialize WatermarkTracker if enabled
            tracker = None
            if self.config.use_watermark_tracker and not is_image_mask and bbox_dict:
                logger.info("Initializing WatermarkTracker for dynamic watermark tracking")
                tracker = BboxTracker(
                    motion_smoothing_factor=self.config.tracker_smoothing_factor,
                )

                # Register detections from bbox_dict
                for frame_id, bbox in bbox_dict.items():
                    # bbox is (x, y, w, h), confidence defaults to 1.0
                    tracker.add_detection(frame_id, bbox, confidence=0.95)

                logger.info(
                    f"Tracker initialized with {len(tracker.detections)} keyframe detections"
                )

            inpaint_crops = []  # List of (frame_id, crop_path) tuples

            for frame in frames:
                bbox = None

                if is_image_mask:
                    # Image mask: extract bbox from connected components or assume full mask region
                    mask = mask_data
                    if not mask_loader.validate_image_mask(mask, frame.image.shape):
                        logger.warning(f"Invalid mask for frame {frame.frame_id}")
                        continue
                    # For simplicity, find contours and use bounding rect
                    try:
                        import cv2
                        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                        if not contours:
                            logger.warning(f"No contours found in mask for frame {frame.frame_id}")
                            continue
                        x, y, w, h = cv2.boundingRect(np.vstack(contours))
                        bbox = (x, y, w, h)
                    except Exception as e:
                        logger.warning(f"Error extracting bbox from mask: {e}")
                        continue
                else:
                    # Bbox sequence: get bbox for this frame
                    if tracker is not None:
                        # Use tracker interpolation for dynamic bboxes
                        bbox = tracker.interpolate(frame.frame_id)
                        if bbox is None:
                            logger.debug(f"No bbox from tracker for frame {frame.frame_id}")
                            continue
                    elif frame.frame_id in bbox_dict:
                        # Fallback to direct bbox lookup
                        bbox = bbox_dict[frame.frame_id]
                    else:
                        logger.debug(f"No bbox for frame {frame.frame_id}")
                        continue

                if bbox is None:
                    continue

                # Validate bbox
                if not mask_loader.validate_bbox(bbox, frame.image.shape):
                    logger.warning(f"Invalid bbox for frame {frame.frame_id}: {bbox}")
                    continue

                # Compute crop region metadata
                try:
                    crop_region = crop_handler.compute_crop_region(
                        frame.frame_id,
                        bbox,
                        frame.image.shape,
                    )
                    if crop_region is None:
                        logger.warning(f"Failed to compute crop region for frame {frame.frame_id}")
                        continue

                    # Extract crop from frame
                    crop_data = crop_handler.extract_crop(frame.image, crop_region)
                    if crop_data is None:
                        logger.warning(f"Failed to extract crop for frame {frame.frame_id}")
                        continue

                    # Save crop to disk
                    crop_path = crops_dir / f"crop_{frame.frame_id:06d}.png"
                    write_image(str(crop_path), crop_data)

                    # Store CropRegion for later stitching
                    self.crop_regions.append(crop_region)
                    inpaint_crops.append((frame.frame_id, crop_path))

                    logger.debug(f"Cropped frame {frame.frame_id}: bbox={bbox}, region={crop_region}")

                except Exception as e:
                    logger.error(f"Error cropping frame {frame.frame_id}: {e}")
                    continue

            logger.info(f"Created {len(inpaint_crops)} crop regions for inpainting")

            # Phase 3: Pre-flight ComfyUI checks
            logger.info("=" * 60)
            logger.info("Phase 3: Pre-flight ComfyUI Checks")
            logger.info("=" * 60)

            executor = InpaintExecutor(
                host=self.config.comfyui_host,
                port=self.config.comfyui_port,
                timeout_sec=self.config.inpaint_timeout_sec,
                batch_size=self.config.batch_size,
            )

            # Health check
            try:
                await self._comfyui_health_check()
                logger.info(f"ComfyUI health check passed ({self.config.comfyui_host}:{self.config.comfyui_port})")
            except Exception as e:
                logger.error(f"ComfyUI health check failed: {e}")
                raise RuntimeError(f"ComfyUI not reachable at {self.config.comfyui_host}:{self.config.comfyui_port}")

            # Phase 4: Inpaint (async batch)
            logger.info("=" * 60)
            logger.info("Phase 4: Inpainting (ComfyUI)")
            logger.info("=" * 60)

            inpaint_start = datetime.now()

            # Prepare inpaint pairs for batch execution
            inpaint_pairs = [
                (crop_path, crop_path.parent / f"mask_{frame_id:06d}.png")
                for frame_id, crop_path in inpaint_crops
            ]

            # Execute inpainting
            inpaint_dir = self.config.output_dir / "inpainted"
            inpaint_dir.mkdir(parents=True, exist_ok=True)

            inpaint_results = await executor.inpaint_batch(
                inpaint_pairs,
                self.config.inpaint,
                inpaint_dir,
            )

            inpaint_duration = (datetime.now() - inpaint_start).total_seconds()
            self.inpaint_times.append(inpaint_duration)
            logger.info(f"Inpainting complete: {len(inpaint_results)} crops inpainted in {inpaint_duration:.1f}s")

            # Phase 5: Postprocessing (stitch + blend)
            logger.info("=" * 60)
            logger.info("Phase 5: Postprocessing (Stitching & Blending)")
            logger.info("=" * 60)

            stitch_handler = StitchHandler(
                blend_feather_width=self.config.blend_feather_width,
            )

            # Initialize Poisson blender if enabled
            poisson_blender = None
            if self.config.use_poisson_blending:
                logger.info("Poisson blending enabled for seamless edge integration")
                poisson_blender = PoissonBlender(
                    max_iterations=self.config.poisson_max_iterations,
                    tolerance=self.config.poisson_tolerance,
                )

            # Stitch inpainted crops back to original frames (can parallelize with asyncio.gather())
            stitched_frames = {}
            for i, (frame, (frame_id, _)) in enumerate(zip(frames, inpaint_crops)):
                if frame_id not in [cr.frame_id for cr in self.crop_regions]:
                    logger.debug(f"No crop region for frame {frame_id}, skipping stitch")
                    continue

                # Find inpainted crop
                inpainted_path = inpaint_dir / f"inpainted_{frame_id:06d}.png"
                if not inpainted_path.exists():
                    logger.warning(f"Inpainted crop not found: {inpainted_path}")
                    continue

                inpainted = read_image(str(inpainted_path))
                crop_region = next((cr for cr in self.crop_regions if cr.frame_id == frame_id), None)

                if crop_region is None:
                    logger.warning(f"CropRegion metadata not found for frame {frame_id}")
                    continue

                # Stitch back to original frame
                try:
                    stitched = stitch_handler.stitch_back(frame.image, inpainted, crop_region)

                    # Apply Poisson blending if enabled (replaces feather blending for better quality)
                    if poisson_blender is not None:
                        # Create binary mask for inpainted region
                        mask = np.zeros((inpainted.shape[0], inpainted.shape[1]), dtype=np.uint8)
                        # Mark inpainted region as 255 (source), rest as 0 (target)
                        x, y, w, h = crop_region.context_bbox
                        mask[y:y+h, x:x+w] = 255

                        # Apply Poisson blending
                        stitched = poisson_blender.blend(
                            stitched,  # target
                            inpainted,  # source (already padded to frame size by stitch_back)
                            mask,
                            blend_width=self.config.blend_feather_width,
                        )

                    stitched_frames[frame_id] = stitched

                    # Save stitched frame
                    stitched_path = stitched_dir / f"frame_{frame_id:06d}.png"
                    write_image(str(stitched_path), stitched)

                    if (i + 1) % 10 == 0:
                        logger.info(f"Stitched {i + 1}/{len(inpaint_crops)} frames")

                except Exception as e:
                    logger.error(f"Error stitching frame {frame_id}: {e}")
                    continue

            logger.info(f"Stitched {len(stitched_frames)} frames")

            # Phase 5.5: Temporal smoothing (Phase 2 optional)
            if self.config.temporal_smooth_alpha > 0.0 or self.config.use_adaptive_temporal_smoothing:
                logger.info("=" * 60)
                logger.info("Phase 5.5: Temporal Smoothing")
                logger.info("=" * 60)

                if self.config.use_adaptive_temporal_smoothing:
                    # Use adaptive temporal smoother
                    logger.info("Using adaptive temporal smoothing with motion detection")
                    adaptive_smoother = AdaptiveTemporalSmoother(
                        base_alpha=self.config.temporal_smooth_alpha or 0.3,
                        motion_threshold=self.config.adaptive_motion_threshold,
                    )

                    # Load stitched frames in order and apply adaptive temporal smoothing
                    frame_ids_sorted = sorted(stitched_frames.keys())
                    frame_list = [stitched_frames[fid] for fid in frame_ids_sorted]

                    smoothed_list, motions = adaptive_smoother.smooth_sequence(frame_list)

                    smoothed_frames = {
                        frame_ids_sorted[i]: smoothed_list[i]
                        for i in range(len(frame_ids_sorted))
                    }

                    # Save smoothed frames
                    for frame_id, smoothed in smoothed_frames.items():
                        smoothed_path = stitched_dir / f"frame_{frame_id:06d}.png"
                        write_image(str(smoothed_path), smoothed)

                    logger.info(f"Adaptive temporal smoothing complete with motion-aware blending")
                else:
                    # Use standard temporal smoother
                    temporal_smoother = TemporalSmoother(alpha=self.config.temporal_smooth_alpha)

                    # Load stitched frames in order and apply temporal smoothing
                    frame_ids_sorted = sorted(stitched_frames.keys())
                    smoothed_frames = {}
                    previous_frame = None

                    for frame_id in frame_ids_sorted:
                        try:
                            current_frame = stitched_frames[frame_id]
                            smoothed = temporal_smoother.smooth_frame(current_frame, previous_frame)
                            smoothed_frames[frame_id] = smoothed
                            previous_frame = smoothed

                            # Save smoothed frame, overwriting stitched frame
                            smoothed_path = stitched_dir / f"frame_{frame_id:06d}.png"
                            write_image(str(smoothed_path), smoothed)

                        except Exception as e:
                            logger.error(f"Error smoothing frame {frame_id}: {e}")
                            smoothed_frames[frame_id] = stitched_frames[frame_id]
                            previous_frame = stitched_frames[frame_id]

                    logger.info(f"Temporal smoothing complete: {len(smoothed_frames)} frames smoothed")

                stitched_frames = smoothed_frames

            # Phase 6: Video encoding
            logger.info("=" * 60)
            logger.info("Phase 6: Video Encoding (FFmpeg)")
            logger.info("=" * 60)

            video_encoder = VideoEncoder(
                fps=extractor.fps,
                codec="libx264",
                crf=self.config.inpaint.cfg_scale,  # Use CRF from config (approximate)
            )

            output_video = self.config.output_dir / "output.mp4"
            frames_pattern = str(stitched_dir / "frame_*.png")

            encode_success = video_encoder.encode(frames_pattern, output_video)
            if not encode_success:
                raise RuntimeError(f"Video encoding failed")

            logger.info(f"Video encoding complete: {output_video}")

            # Phase 7: Checkpoint saving (Phase 2)
            if checkpoint_manager is not None:
                try:
                    video_name = self.config.video_path.stem
                    processing_state = {
                        "frames_processed": len(frames),
                        "crops_created": len(self.crop_regions),
                        "inpaint_duration_sec": sum(self.inpaint_times),
                        "status": "completed",
                    }
                    checkpoint_manager.save_crop_regions(
                        video_name,
                        self.crop_regions,
                        processing_state,
                    )
                except Exception as e:
                    logger.warning(f"Failed to save checkpoint: {e}")

            # Phase 8: Cleanup and summary
            logger.info("=" * 60)
            logger.info("Pipeline Complete")
            logger.info("=" * 60)

            elapsed = (datetime.now() - self.start_time).total_seconds()

            # Clean up intermediate files if configured
            if not self.config.keep_intermediate:
                logger.info("Cleaning up intermediate files...")
                # Note: actual cleanup would delete frames_dir, crops_dir, inpaint_dir, stitched_dir
                pass

            result = {
                "status": "success",
                "output_video": str(output_video),
                "duration_sec": elapsed,
                "frames_processed": len(frames),
                "crops_created": len(self.crop_regions),
                "inpaint_duration_sec": sum(self.inpaint_times),
            }

            logger.info(f"Pipeline complete in {elapsed:.2f}s")
            logger.info(f"  Frames processed: {len(frames)}")
            logger.info(f"  Crops created: {len(self.crop_regions)}")
            logger.info(f"  Inpaint duration: {sum(self.inpaint_times):.1f}s")
            logger.info(f"  Output: {output_video}")

            return result

        except Exception as e:
            logger.error(f"Pipeline failed: {e}", exc_info=True)
            raise

    async def _comfyui_health_check(self) -> bool:
        """
        Check ComfyUI server connectivity and health.

        Returns:
            True if healthy

        Raises:
            RuntimeError: If health check fails
        """
        import aiohttp

        url = f"http://{self.config.comfyui_host}:{self.config.comfyui_port}/system"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    if resp.status == 200:
                        return True
                    else:
                        raise RuntimeError(f"ComfyUI returned status {resp.status}")
        except aiohttp.ClientConnectorError as e:
            raise RuntimeError(f"Cannot connect to ComfyUI: {e}")
        except asyncio.TimeoutError:
            raise RuntimeError("ComfyUI health check timed out")

    @staticmethod
    async def create_and_run(config: ProcessConfig) -> dict:
        """Create pipeline and run it."""
        pipeline = Pipeline(config)
        return await pipeline.run()
