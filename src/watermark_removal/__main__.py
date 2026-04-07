"""CLI entry point for the watermark removal pipeline.

Usage:
    python -m watermark_removal <config.yaml>
    python -m watermark_removal <config.yaml> --dry-run
    python -m watermark_removal --version
    python -m watermark_removal --help
"""

import asyncio
import json
import sys
from pathlib import Path

from watermark_removal import __version__

USAGE = """\
Usage: python -m watermark_removal <config.yaml> [--dry-run]

Watermark removal pipeline using Crop-Inpaint-Stitch approach.

Positional arguments:
  config_path       Path to YAML configuration file

Options:
  --dry-run         Validate config, check input files, print effective
                    config as JSON, then exit without running the pipeline
  --version         Print version and exit
  --help            Show this help message and exit

Prerequisites:
  ComfyUI must be running at the host:port specified in your config
  (default: 127.0.0.1:8188) before starting a full pipeline run.
"""


def main() -> int:
    """Parse arguments and run the watermark removal pipeline.

    Returns:
        Exit code: 0 on success, 1 on config/usage error, 2 on runtime error.
    """
    args = sys.argv[1:]

    # Handle --version
    if "--version" in args:
        print(__version__)
        return 0

    # Handle --help
    if "--help" in args or "-h" in args:
        print(USAGE)
        return 0

    # Check for --dry-run flag
    dry_run = "--dry-run" in args
    positional = [a for a in args if not a.startswith("--")]

    # No config path provided
    if not positional:
        print(USAGE, file=sys.stderr)
        return 1

    config_path = positional[0]

    # Load config via ConfigManager
    try:
        from watermark_removal.core.config_manager import ConfigManager

        manager = ConfigManager(config_path)
        config = manager.load()
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"Config validation error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Failed to load config: {exc}", file=sys.stderr)
        return 1

    # Dry-run: validate config, check input files, print effective config
    if dry_run:
        errors = []
        if not Path(config.video_path).exists():
            errors.append(f"Video file not found: {config.video_path}")
        if not Path(config.mask_path).exists():
            errors.append(f"Mask file not found: {config.mask_path}")

        if errors:
            for err in errors:
                print(f"Warning: {err}", file=sys.stderr)

        # Print effective config as JSON
        effective = {
            "video_path": str(config.video_path),
            "mask_path": str(config.mask_path),
            "output_dir": str(config.output_dir),
            "comfyui_host": config.comfyui_host,
            "comfyui_port": config.comfyui_port,
            "batch_size": config.batch_size,
            "output_codec": config.output_codec,
            "output_crf": config.output_crf,
            "output_fps": config.output_fps,
            "temporal_smooth_enabled": config.temporal_smooth_enabled,
            "use_poisson_blending": config.use_poisson_blending,
            "ensemble_detection_enabled": config.ensemble_detection_enabled,
            "optical_flow_enabled": config.optical_flow_enabled,
            "inpaint": {
                "model_name": config.inpaint.model_name,
                "steps": config.inpaint.steps,
                "cfg_scale": config.inpaint.cfg_scale,
                "sampler": config.inpaint.sampler,
            },
        }
        print(json.dumps(effective, indent=2))
        return 0

    # Full pipeline run
    try:
        from watermark_removal.core.pipeline import Pipeline

        summary = asyncio.run(Pipeline(config).run())
        print(json.dumps(summary, indent=2, default=str))
        return 0
    except Exception as exc:
        print(f"Pipeline error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
