#!/usr/bin/env python3
"""
CLI entry point for watermark removal pipeline.

Usage:
    python scripts/run_pipeline.py --config config/my_project.yaml
    python scripts/run_pipeline.py --video input.mp4 --mask mask.png --output output
"""

import asyncio
import argparse
import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    """Main async entry point."""
    parser = argparse.ArgumentParser(
        description="Remove watermarks from video using ComfyUI inpainting"
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Config YAML file path",
    )
    parser.add_argument(
        "--video",
        type=Path,
        help="Input video file (overrides config)",
    )
    parser.add_argument(
        "--mask",
        type=Path,
        help="Watermark mask file (overrides config)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output directory (overrides config)",
    )

    args = parser.parse_args()

    try:
        # Import here to avoid dependency issues
        from src.watermark_removal.core.config_manager import ConfigManager
        from src.watermark_removal.core.pipeline import Pipeline

        # Load config
        if args.config:
            manager = ConfigManager(args.config)
            config = manager.load()
        else:
            # Require at least video and mask
            if not args.video or not args.mask:
                parser.error(
                    "Either --config or both --video and --mask are required"
                )

            from src.watermark_removal.core.types import ProcessConfig
            config = ProcessConfig(
                video_path=args.video,
                mask_path=args.mask,
                output_dir=args.output or "output",
            )

        # Override with CLI args if provided
        if args.video:
            config.video_path = args.video
        if args.mask:
            config.mask_path = args.mask
        if args.output:
            config.output_dir = args.output

        # Run pipeline
        logger.info("Starting pipeline...")
        result = await Pipeline.create_and_run(config)

        # Print summary
        print("\n" + "=" * 60)
        print("PIPELINE COMPLETE")
        print("=" * 60)
        print(f"Status: {result['status']}")
        print(f"Output: {result['output_video']}")
        print(f"Duration: {result['duration_sec']:.2f}s")
        print(f"Frames: {result['frames_processed']}")
        print("=" * 60)

        return 0

    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
