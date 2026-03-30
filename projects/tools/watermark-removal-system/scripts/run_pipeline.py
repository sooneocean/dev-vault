#!/usr/bin/env python3
"""
Watermark removal pipeline command-line interface.

Entry point for executing the watermark removal pipeline with YAML config
or command-line arguments.

Usage:
    python scripts/run_pipeline.py --config config/phase1_static.yaml
    python scripts/run_pipeline.py --video input.mp4 --mask mask.png --output output.mp4
"""

import asyncio
import argparse
import sys
import logging
from pathlib import Path

from src.watermark_removal.core.pipeline import Pipeline
from src.watermark_removal.core.config_manager import ConfigManager
from src.watermark_removal.core.types import ProcessConfig


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(asctime)s - %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Watermark removal pipeline: extract, inpaint, stitch, and encode",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with config file
  python scripts/run_pipeline.py --config config/phase1_static.yaml

  # Run with command-line arguments (override config)
  python scripts/run_pipeline.py \\
    --video input.mp4 \\
    --mask mask.png \\
    --output output.mp4 \\
    --batch-size 8

  # Run with config and override specific parameters
  python scripts/run_pipeline.py \\
    --config config/phase1_static.yaml \\
    --batch-size 4 \\
    --blend-feather-width 64
        """,
    )

    parser.add_argument(
        "--config",
        type=Path,
        help="YAML configuration file path",
    )

    parser.add_argument(
        "--video",
        type=Path,
        help="Input video file path",
    )

    parser.add_argument(
        "--mask",
        type=Path,
        help="Watermark mask file path (JPEG or JSON)",
    )

    parser.add_argument(
        "--output",
        type=Path,
        help="Output directory for results",
    )

    parser.add_argument(
        "--context-padding",
        type=int,
        help="Padding around watermark for context (pixels)",
    )

    parser.add_argument(
        "--target-inpaint-size",
        type=int,
        help="Target size for inpaint model (e.g., 1024)",
    )

    parser.add_argument(
        "--blend-feather-width",
        type=int,
        help="Feather blend width at crop edges (pixels)",
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        help="Number of parallel inpaint jobs",
    )

    parser.add_argument(
        "--inpaint-timeout",
        type=float,
        help="Timeout for each inpaint job (seconds)",
    )

    parser.add_argument(
        "--comfyui-host",
        type=str,
        help="ComfyUI server host",
    )

    parser.add_argument(
        "--comfyui-port",
        type=int,
        help="ComfyUI server port",
    )

    parser.add_argument(
        "--keep-intermediate",
        action="store_true",
        help="Keep intermediate frame and crop files",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging (DEBUG level)",
    )

    # Phase 2 arguments
    parser.add_argument(
        "--temporal-smooth-alpha",
        type=float,
        help="Temporal smoothing factor for flicker reduction (0.0-1.0, Phase 2)",
    )

    parser.add_argument(
        "--use-adaptive-temporal-smoothing",
        action="store_true",
        help="Enable adaptive temporal smoothing with motion detection (Phase 2)",
    )

    parser.add_argument(
        "--adaptive-motion-threshold",
        type=float,
        help="Motion threshold for adaptive temporal smoothing (0.0-1.0, Phase 2)",
    )

    parser.add_argument(
        "--use-poisson-blending",
        action="store_true",
        help="Enable Poisson blending for seamless edge integration (Phase 2)",
    )

    parser.add_argument(
        "--poisson-max-iterations",
        type=int,
        help="Maximum iterations for Poisson solver (Phase 2)",
    )

    parser.add_argument(
        "--use-yolo-detection",
        action="store_true",
        help="Enable automatic YOLO watermark detection (Phase 2)",
    )

    parser.add_argument(
        "--yolo-model-size",
        type=str,
        choices=["nano", "small", "medium", "large"],
        help="YOLO model size for detection (Phase 2)",
    )

    parser.add_argument(
        "--yolo-confidence-threshold",
        type=float,
        help="Confidence threshold for YOLO detections (Phase 2)",
    )

    parser.add_argument(
        "--use-watermark-tracker",
        action="store_true",
        help="Enable watermark tracking with bbox interpolation (Phase 2)",
    )

    parser.add_argument(
        "--yolo-model-path",
        type=Path,
        help="Path to custom YOLO model weights (Phase 2)",
    )

    parser.add_argument(
        "--use-checkpoints",
        action="store_true",
        help="Enable pipeline checkpointing for resumption (Phase 2)",
    )

    parser.add_argument(
        "--resume-from-checkpoint",
        action="store_true",
        help="Resume from last checkpoint if available (Phase 2)",
    )

    return parser.parse_args()


def load_config(args) -> ProcessConfig:
    """
    Load configuration from file or arguments.

    Priority:
    1. Command-line arguments (override everything)
    2. Config file (if provided)
    3. Defaults (ProcessConfig defaults)

    Args:
        args: Parsed command-line arguments

    Returns:
        ProcessConfig object

    Raises:
        FileNotFoundError: If config file or required inputs not found
        ValueError: If required parameters missing
    """
    config = None

    # Load from config file if provided
    if args.config:
        if not args.config.exists():
            raise FileNotFoundError(f"Config file not found: {args.config}")

        logger.info(f"Loading config from: {args.config}")
        config_manager = ConfigManager(args.config)
        config = config_manager.load()
    else:
        # Create minimal config from command-line args
        if not args.video or not args.mask:
            raise ValueError(
                "Either --config or both --video and --mask are required"
            )

        config = ProcessConfig(
            video_path=args.video,
            mask_path=args.mask,
            output_dir=args.output or "output",
        )
        logger.info("Using command-line configuration")

    # Override with command-line arguments
    if args.video:
        config.video_path = args.video
    if args.mask:
        config.mask_path = args.mask
    if args.output:
        config.output_dir = args.output
    if args.context_padding is not None:
        config.context_padding = args.context_padding
    if args.target_inpaint_size is not None:
        config.target_inpaint_size = args.target_inpaint_size
    if args.blend_feather_width is not None:
        config.blend_feather_width = args.blend_feather_width
    if args.batch_size is not None:
        config.batch_size = args.batch_size
    if args.inpaint_timeout is not None:
        config.inpaint_timeout_sec = args.inpaint_timeout
    if args.comfyui_host:
        config.comfyui_host = args.comfyui_host
    if args.comfyui_port is not None:
        config.comfyui_port = args.comfyui_port
    if args.keep_intermediate:
        config.keep_intermediate = True

    # Phase 2 overrides - YOLO Detection
    if hasattr(args, 'use_yolo_detection') and args.use_yolo_detection:
        config.use_yolo_detection = True
    if hasattr(args, 'yolo_model_size') and args.yolo_model_size:
        config.yolo_model_size = args.yolo_model_size
    if hasattr(args, 'yolo_confidence_threshold') and args.yolo_confidence_threshold is not None:
        config.yolo_confidence_threshold = args.yolo_confidence_threshold

    # Phase 2 overrides - Temporal Smoothing
    if hasattr(args, 'temporal_smooth_alpha') and args.temporal_smooth_alpha is not None:
        config.temporal_smooth_alpha = args.temporal_smooth_alpha
    if hasattr(args, 'use_adaptive_temporal_smoothing') and args.use_adaptive_temporal_smoothing:
        config.use_adaptive_temporal_smoothing = True
    if hasattr(args, 'adaptive_motion_threshold') and args.adaptive_motion_threshold is not None:
        config.adaptive_motion_threshold = args.adaptive_motion_threshold

    # Phase 2 overrides - Poisson Blending
    if hasattr(args, 'use_poisson_blending') and args.use_poisson_blending:
        config.use_poisson_blending = True
    if hasattr(args, 'poisson_max_iterations') and args.poisson_max_iterations is not None:
        config.poisson_max_iterations = args.poisson_max_iterations

    # Phase 2 overrides - Watermark Tracking
    if hasattr(args, 'use_watermark_tracker') and args.use_watermark_tracker:
        config.use_watermark_tracker = True
    if hasattr(args, 'yolo_model_path') and args.yolo_model_path:
        config.yolo_model_path = args.yolo_model_path

    # Phase 2 overrides - Checkpointing
    if hasattr(args, 'use_checkpoints') and args.use_checkpoints:
        config.use_checkpoints = True
    if hasattr(args, 'resume_from_checkpoint') and args.resume_from_checkpoint:
        config.resume_from_checkpoint = True

    # Validate required files
    if not config.video_path.exists():
        raise FileNotFoundError(f"Video file not found: {config.video_path}")
    if not config.mask_path.exists():
        raise FileNotFoundError(f"Mask file not found: {config.mask_path}")

    logger.info("Configuration loaded and validated")
    logger.info(f"  Video: {config.video_path}")
    logger.info(f"  Mask: {config.mask_path}")
    logger.info(f"  Output: {config.output_dir}")
    logger.info(f"  ComfyUI: {config.comfyui_host}:{config.comfyui_port}")
    logger.info(f"  Batch size: {config.batch_size}")

    return config


async def main():
    """
    Main async entry point.

    Loads config, runs pipeline, and reports results.

    Returns:
        Exit code (0 = success, 1 = error)
    """
    args = parse_arguments()

    # Setup logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")

    try:
        # Load configuration
        config = load_config(args)

        # Create and run pipeline
        logger.info("=" * 70)
        logger.info("Starting Watermark Removal Pipeline")
        logger.info("=" * 70)

        result = await Pipeline.create_and_run(config)

        # Print summary
        logger.info("=" * 70)
        logger.info("Pipeline Complete")
        logger.info("=" * 70)
        logger.info(f"Status: {result['status']}")
        logger.info(f"Frames processed: {result['frames_processed']}")
        logger.info(f"Crops created: {result['crops_created']}")
        logger.info(f"Inpaint duration: {result['inpaint_duration_sec']:.1f}s")
        logger.info(f"Total duration: {result['duration_sec']:.1f}s")
        logger.info(f"Output video: {result['output_video']}")

        print("\n" + "=" * 70)
        print("PIPELINE SUCCESSFUL")
        print("=" * 70)
        print(f"Output: {result['output_video']}")
        print(f"Duration: {result['duration_sec']:.1f}s")

        return 0

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    except RuntimeError as e:
        logger.error(f"Pipeline error: {e}")
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        print(f"UNEXPECTED ERROR: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
