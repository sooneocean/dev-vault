#!/usr/bin/env python3
"""
Example: Remove a dynamic watermark from video.

This script demonstrates how to process a video with a moving watermark
(watermark that changes position or size across frames).

Dynamic watermarks are specified as a JSON file with per-frame bounding boxes.

Usage:
  python examples/dynamic_watermark_example.py [--video PATH] [--bbox PATH] [--output DIR]

If no arguments provided, uses example paths (which won't exist without sample data).
"""

import argparse
import asyncio
import json
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


def generate_example_bbox_file(output_path: str, frames: int = 30) -> None:
    """
    Generate an example dynamic bounding box JSON file.

    Creates a JSON file with bounding boxes that drift right across frames.
    """
    bboxes = []
    for frame_idx in range(min(frames, 10)):  # Only first 10 frames
        x = 100 + (frame_idx * 20)  # Drifts right by 20px per frame
        y = 900  # Fixed y position
        w = 200  # Fixed width
        h = 100  # Fixed height

        # Ensure bounds are valid
        if x + w <= 1920:  # Assume 1920×1080 video
            bboxes.append({
                "frame": frame_idx,
                "x": x,
                "y": y,
                "w": w,
                "h": h,
            })

    # Save to JSON
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(bboxes, f, indent=2)

    print(f"Generated example bbox file: {output_path}")
    print(f"Contains {len(bboxes)} frames with dynamic watermark")


async def main() -> int:
    """
    Run watermark removal for a dynamic watermark video.

    Returns:
        Exit code: 0 on success, 1 on failure.
    """
    parser = argparse.ArgumentParser(
        description="Remove dynamic (moving) watermark from video",
        epilog="""
Example usage:

  # Using command-line arguments
  python examples/dynamic_watermark_example.py \\
    --video input.mp4 \\
    --bbox watermark_bbox.json \\
    --output ./output

  # Using config file (recommended for repeated use)
  python examples/dynamic_watermark_example.py \\
    --config config/my_project.yaml

  # Generate example bbox file first
  python examples/dynamic_watermark_example.py \\
    --generate-example bbox_example.json

Notes:
  - Bounding box file is JSON array with per-frame coordinates
  - Frames not listed in JSON are skipped (no watermark)
  - Format: [{"frame": 0, "x": 100, "y": 50, "w": 200, "h": 100}, ...]
  - See docs/mask_format_spec.md for JSON schema details
        """,
    )

    parser.add_argument(
        "--config",
        type=str,
        help="Path to YAML config file (optional if using CLI args)",
    )
    parser.add_argument("--video", type=str, help="Input video path")
    parser.add_argument(
        "--bbox", type=str, help="Bounding box JSON file path (for dynamic watermark)"
    )
    parser.add_argument("--output", type=str, help="Output directory")
    parser.add_argument(
        "--generate-example",
        type=str,
        help="Generate example bbox JSON file at path",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")

    args = parser.parse_args()

    # Handle example generation
    if args.generate_example:
        generate_example_bbox_file(args.generate_example)
        return 0

    setup_logging(verbose=args.verbose)
    logger = logging.getLogger(__name__)

    logger.info("=== Dynamic Watermark Removal ===")

    try:
        # Load configuration
        if args.config:
            logger.info(f"Loading config from {args.config}")
            config_manager = ConfigManager(args.config)
            config = config_manager.load()
        elif args.video and args.bbox and args.output:
            logger.info("Using command-line arguments to build config")
            config = ProcessConfig(
                video_path=args.video,
                mask_path=args.bbox,  # JSON bbox file
                output_dir=args.output,
                # Use defaults for other parameters
                inpaint=InpaintConfig(),
            )
        else:
            logger.error(
                "Either --config or (--video, --bbox, --output) must be provided"
            )
            print("\nTip: Generate example bbox file first:")
            print("  python examples/dynamic_watermark_example.py --generate-example bbox_example.json")
            return 1

        # Apply CLI overrides if provided
        if args.video:
            config.video_path = str(Path(args.video).resolve())
            logger.info(f"Override: video_path = {config.video_path}")

        if args.bbox:
            config.mask_path = str(Path(args.bbox).resolve())
            logger.info(f"Override: mask_path (bbox) = {config.mask_path}")

        if args.output:
            config.output_dir = str(Path(args.output).resolve())
            logger.info(f"Override: output_dir = {config.output_dir}")

        # Validate config
        logger.info("Validating configuration...")
        config.__post_init__()

        # Display config summary
        logger.info(f"Video: {config.video_path}")
        logger.info(f"Bbox file: {config.mask_path}")
        logger.info(f"Output: {config.output_dir}")
        logger.info(f"Model: {config.inpaint.model_name}")
        logger.info(f"Inpaint steps: {config.inpaint.steps}")
        logger.info(f"Batch size: {config.batch_size}")
        logger.info(f"Blend feather width: {config.blend_feather_width}")

        # Validate bbox file exists and is readable
        bbox_path = Path(config.mask_path)
        if not bbox_path.exists():
            raise FileNotFoundError(f"Bbox file not found: {bbox_path}")

        # Try to load and validate JSON
        try:
            with open(bbox_path, "r") as f:
                bboxes = json.load(f)
            if not isinstance(bboxes, list):
                raise ValueError("Bbox file must be a JSON array")
            logger.info(f"Loaded {len(bboxes)} frame entries from bbox file")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in bbox file: {e}")

        # Create and run pipeline
        logger.info("Initializing pipeline...")
        pipeline = Pipeline(config)

        logger.info("Starting pipeline execution...")
        result = await pipeline.run()

        # Print results
        print("\n" + "=" * 70)
        print("DYNAMIC WATERMARK REMOVAL COMPLETE")
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
