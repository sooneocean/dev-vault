#!/usr/bin/env python3
"""
Example: Remove a static watermark from video.

This script demonstrates how to process a video with a fixed watermark
(logo, text, or graphic) that appears in the same location in every frame.

Usage:
  python examples/static_watermark_example.py [--video PATH] [--mask PATH] [--output DIR]

If no arguments provided, uses example paths (which won't exist without sample data).
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.watermark_removal.core.config_manager import ConfigManager
from src.watermark_removal.core.pipeline import Pipeline
from src.watermark_removal.core.types import InpaintConfig, ProcessConfig


def setup_logging(verbose: bool = False) -> None:
    """Configure logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


async def main() -> int:
    """
    Run watermark removal for a static watermark video.

    Returns:
        Exit code: 0 on success, 1 on failure.
    """
    parser = argparse.ArgumentParser(
        description="Remove static watermark from video",
        epilog="""
Example usage:

  # Using command-line arguments
  python examples/static_watermark_example.py \\
    --video input.mp4 \\
    --mask watermark_mask.png \\
    --output ./output

  # Using config file (recommended for repeated use)
  python examples/static_watermark_example.py \\
    --config config/my_project.yaml

Notes:
  - Mask must be PNG image same dimensions as video frames
  - White pixels (255) mark watermark region; black (0) is preserve region
  - See docs/mask_format_spec.md for mask requirements
        """,
    )

    parser.add_argument(
        "--config",
        type=str,
        help="Path to YAML config file (optional if using CLI args)",
    )
    parser.add_argument("--video", type=str, help="Input video path")
    parser.add_argument("--mask", type=str, help="Watermark mask PNG path")
    parser.add_argument("--output", type=str, help="Output directory")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")

    args = parser.parse_args()

    setup_logging(verbose=args.verbose)
    logger = logging.getLogger(__name__)

    logger.info("=== Static Watermark Removal ===")

    try:
        # Load configuration
        if args.config:
            logger.info(f"Loading config from {args.config}")
            config_manager = ConfigManager(args.config)
            config = config_manager.load()
        elif args.video and args.mask and args.output:
            logger.info("Using command-line arguments to build config")
            config = ProcessConfig(
                video_path=args.video,
                mask_path=args.mask,
                output_dir=args.output,
                # Use defaults for other parameters
                inpaint=InpaintConfig(),
            )
        else:
            logger.error(
                "Either --config or (--video, --mask, --output) must be provided"
            )
            return 1

        # Apply CLI overrides if provided
        if args.video:
            config.video_path = str(Path(args.video).resolve())
            logger.info(f"Override: video_path = {config.video_path}")

        if args.mask:
            config.mask_path = str(Path(args.mask).resolve())
            logger.info(f"Override: mask_path = {config.mask_path}")

        if args.output:
            config.output_dir = str(Path(args.output).resolve())
            logger.info(f"Override: output_dir = {config.output_dir}")

        # Validate config
        logger.info("Validating configuration...")
        config.__post_init__()

        # Display config summary
        logger.info(f"Video: {config.video_path}")
        logger.info(f"Mask: {config.mask_path}")
        logger.info(f"Output: {config.output_dir}")
        logger.info(f"Model: {config.inpaint.model_name}")
        logger.info(f"Inpaint steps: {config.inpaint.steps}")
        logger.info(f"Batch size: {config.batch_size}")
        logger.info(f"Blend feather width: {config.blend_feather_width}")

        # Create and run pipeline
        logger.info("Initializing pipeline...")
        pipeline = Pipeline(config)

        logger.info("Starting pipeline execution...")
        result = await pipeline.run()

        # Print results
        print("\n" + "=" * 70)
        print("WATERMARK REMOVAL COMPLETE")
        print("=" * 70)
        print(f"Frames processed:          {result['frame_count']}")
        print(f"Total duration:            {result['duration_seconds']:.2f}s")
        print(f"Inpaint duration:          {result['inpaint_duration_seconds']:.2f}s")
        print(f"Encode duration:           {result['encode_duration_seconds']:.2f}s")
        print(f"Output file:               {result['output_path']}")
        print("=" * 70 + "\n")

        # Additional information
        fps = (
            result["frame_count"] / result["duration_seconds"]
            if result["duration_seconds"] > 0
            else 0
        )
        logger.info(f"Processing speed: {fps:.1f} frames/sec")

        return 0

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1

    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return 1

    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
