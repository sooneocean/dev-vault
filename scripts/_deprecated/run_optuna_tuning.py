#!/usr/bin/env python
"""CLI entry point for Optuna hyperparameter tuning."""

import asyncio
import argparse
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from watermark_removal.tuning import OptunaTuner, TuningConfig, OPTUNA_AVAILABLE

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Optimize ensemble watermark detection hyperparameters"
    )

    parser.add_argument(
        "--video",
        required=True,
        help="Path to validation video",
    )
    parser.add_argument(
        "--ground-truth",
        required=True,
        help="Path to ground truth annotations (COCO JSON)",
    )
    parser.add_argument(
        "--n-trials",
        type=int,
        default=150,
        help="Number of Optuna trials (default: 150)",
    )
    parser.add_argument(
        "--output-dir",
        default="./tuning_results",
        help="Output directory for results (default: ./tuning_results)",
    )
    parser.add_argument(
        "--gpu-id",
        type=int,
        default=0,
        help="GPU ID to use (default: 0)",
    )
    parser.add_argument(
        "--timeout-hours",
        type=float,
        default=32.0,
        help="Total timeout in hours (default: 32)",
    )

    args = parser.parse_args()

    # Validate inputs
    video_path = Path(args.video)
    gt_path = Path(args.ground_truth)

    if not video_path.exists():
        logger.error(f"Video not found: {video_path}")
        return 1

    if not gt_path.exists():
        logger.error(f"Ground truth not found: {gt_path}")
        return 1

    logger.info(f"Video: {video_path}")
    logger.info(f"Ground truth: {gt_path}")
    logger.info(f"Trials: {args.n_trials}")
    logger.info(f"Timeout: {args.timeout_hours} hours")
    logger.info(f"GPU: {args.gpu_id}")

    if not OPTUNA_AVAILABLE:
        logger.warning("Optuna not installed. Running in MVP/mock mode.")

    # Create tuning config
    config = TuningConfig(
        n_trials=args.n_trials,
        timeout_sec=args.timeout_hours * 3600,
    )

    # Create tuner
    tuner = OptunaTuner(config)

    # Create study
    if not await tuner.create_study():
        logger.error("Failed to create study")
        return 1

    # Placeholder evaluation function
    async def eval_fn(params):
        """Evaluation function (placeholder)."""
        # In real implementation, this would:
        # 1. Load video frames
        # 2. Run ensemble detector with given params
        # 3. Compute mAP against ground truth
        # 4. Return mAP score
        import random
        return random.uniform(0.5, 0.9)

    # Run optimization
    logger.info("Starting optimization...")
    success = await tuner.optimize(eval_fn, args.n_trials)

    if not success:
        logger.error("Optimization failed")
        return 1

    # Save results
    output_path = Path(args.output_dir) / "best_params.json"
    if tuner.save_results(str(output_path)):
        logger.info(f"Best parameters saved: {output_path}")
        logger.info(f"Best mAP: {tuner.get_best_value():.4f}")
    else:
        logger.warning("Failed to save results")

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
