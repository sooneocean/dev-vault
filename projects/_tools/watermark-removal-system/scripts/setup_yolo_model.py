#!/usr/bin/env python3
"""
YOLO Model Setup Helper

Downloads and verifies YOLO model weights for watermark detection.
Provides multiple strategies: auto-download, Hugging Face, manual path.

Usage:
    python scripts/setup_yolo_model.py --model-size nano
    python scripts/setup_yolo_model.py --model-size nano --device cpu
    python scripts/setup_yolo_model.py --verify-only
"""

import logging
import sys
import argparse
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class YOLOModelSetup:
    """Manage YOLO model download and verification."""

    # Official model weights mapping
    MODEL_URLS = {
        "nano": "https://github.com/ultralytics/assets/releases/download/v8.1.0/yolov8n.pt",
        "small": "https://github.com/ultralytics/assets/releases/download/v8.1.0/yolov8s.pt",
        "medium": "https://github.com/ultralytics/assets/releases/download/v8.1.0/yolov8m.pt",
        "large": "https://github.com/ultralytics/assets/releases/download/v8.1.0/yolov8l.pt",
    }

    # Hugging Face model URLs (alternative source)
    HF_MODEL_URLS = {
        "nano": "https://huggingface.co/ultralytics/yolov8/resolve/main/yolov8n.pt",
        "small": "https://huggingface.co/ultralytics/yolov8/resolve/main/yolov8s.pt",
        "medium": "https://huggingface.co/ultralytics/yolov8/resolve/main/yolov8m.pt",
        "large": "https://huggingface.co/ultralytics/yolov8/resolve/main/yolov8l.pt",
    }

    # Expected model sizes (approximate)
    MODEL_SIZES = {
        "nano": 6_000_000,      # ~6 MB
        "small": 23_000_000,    # ~23 MB
        "medium": 50_000_000,   # ~50 MB
        "large": 100_000_000,   # ~100 MB
    }

    def __init__(self):
        """Initialize setup helper."""
        # Check for ultralytics
        try:
            from ultralytics import YOLO
            self.yolo_available = True
            logger.info("ultralytics is installed")
        except ImportError:
            self.yolo_available = False
            logger.warning("ultralytics not installed. Install: pip install ultralytics")

    def get_default_model_dir(self) -> Path:
        """Get default YOLO model directory.

        Returns:
            Path to ~/.local/share/ultralytics/ or ultralytics cache directory
        """
        home = Path.home()
        default_dir = home / ".local" / "share" / "ultralytics"

        # Fallback: check ultralytics cache
        if not default_dir.exists():
            try:
                from ultralytics.utils import SETTINGS
                if 'runs_dir' in SETTINGS:
                    return Path(SETTINGS['runs_dir']).parent
            except Exception as e:
                logger.debug(f"Could not get ultralytics cache dir: {e}")

        return default_dir

    def verify_model_availability(self, model_size: str = "nano") -> Optional[Path]:
        """Verify model weights are available locally.

        Args:
            model_size: Model size (nano/small/medium/large)

        Returns:
            Path to model if available, None otherwise
        """
        if model_size not in self.MODEL_SIZES:
            logger.error(f"Invalid model size: {model_size}")
            return None

        model_dir = self.get_default_model_dir()
        model_path = model_dir / f"yolov8{model_size[0]}.pt"

        if model_path.exists():
            size_bytes = model_path.stat().st_size
            expected_size = self.MODEL_SIZES[model_size]

            # Allow 10% size variance
            if abs(size_bytes - expected_size) / expected_size < 0.1:
                logger.info(f"✓ Model found: {model_path} ({size_bytes / 1e6:.1f} MB)")
                return model_path
            else:
                logger.warning(f"Model exists but size mismatch: {size_bytes} bytes")
                return model_path
        else:
            logger.info(f"Model not found: {model_path}")
            return None

    def download_model(self, model_size: str = "nano", use_hf: bool = False) -> Optional[Path]:
        """Download model weights using ultralytics auto-download.

        Args:
            model_size: Model size (nano/small/medium/large)
            use_hf: Use Hugging Face mirror (if GitHub unavailable)

        Returns:
            Path to downloaded model, None if failed
        """
        if not self.yolo_available:
            logger.error("ultralytics is required for auto-download")
            logger.error("Install: pip install ultralytics")
            return None

        try:
            from ultralytics import YOLO

            checkpoint = f"yolov8{model_size[0]}.pt"
            logger.info(f"Downloading YOLO model: {checkpoint}")
            logger.info("(This may take a few minutes on first run)")

            # YOLO will auto-download to cache
            model = YOLO(checkpoint)

            model_dir = self.get_default_model_dir()
            model_path = model_dir / checkpoint

            if model_path.exists():
                logger.info(f"✓ Model downloaded: {model_path}")
                return model_path
            else:
                logger.warning(f"Model loaded but path unclear: {model_path}")
                return None

        except ImportError:
            logger.error("ultralytics not installed")
            return None
        except Exception as e:
            logger.error(f"Download failed: {e}")
            logger.info("Try manual download from:")
            logger.info(f"  GitHub: {self.MODEL_URLS.get(model_size, 'N/A')}")
            logger.info(f"  Hugging Face: {self.HF_MODEL_URLS.get(model_size, 'N/A')}")
            return None

    def verify_model_inference(self, model_path: Path) -> bool:
        """Verify model can run inference (smoke test).

        Args:
            model_path: Path to model weights

        Returns:
            True if inference successful, False otherwise
        """
        if not self.yolo_available:
            logger.error("ultralytics required for verification")
            return False

        if not model_path.exists():
            logger.error(f"Model file not found: {model_path}")
            return False

        try:
            import numpy as np
            from ultralytics import YOLO

            logger.info(f"Loading model: {model_path}")
            model = YOLO(str(model_path))

            # Create dummy image for testing
            dummy_image = np.ones((480, 640, 3), dtype=np.uint8) * 100

            logger.info("Running inference test...")
            results = model.predict(dummy_image, conf=0.5, verbose=False)

            logger.info(f"✓ Inference successful")
            logger.info(f"  Model device: {model.device}")
            logger.info(f"  Output shape: {len(results)} result(s)")

            return True

        except Exception as e:
            logger.error(f"Inference test failed: {e}")
            return False

    def print_setup_instructions(self, model_size: str = "nano"):
        """Print setup instructions for manual setup.

        Args:
            model_size: Model size (nano/small/medium/large)
        """
        print("\n" + "="*60)
        print("YOLO Model Setup Instructions")
        print("="*60)

        print(f"\n1. Install ultralytics:")
        print("   pip install ultralytics")

        print(f"\n2. Download model (auto):")
        print(f"   python -c \"from ultralytics import YOLO; YOLO('yolov8{model_size[0]}.pt')\"")

        print(f"\n3. Or download manually:")
        print(f"   GitHub:  {self.MODEL_URLS[model_size]}")
        print(f"   Hugging Face: {self.HF_MODEL_URLS[model_size]}")

        model_dir = self.get_default_model_dir()
        print(f"\n4. Place model in: {model_dir}")

        print(f"\n5. Verify installation:")
        print(f"   python scripts/setup_yolo_model.py --model-size {model_size} --verify-only")

        print(f"\n6. Configure in YAML:")
        model_file = model_dir / f"yolov8{model_size[0]}.pt"
        print(f"   yolo_model_path: {model_file}")

        print("\n" + "="*60 + "\n")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="YOLO Model Setup for Watermark Detection",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/setup_yolo_model.py --model-size nano
  python scripts/setup_yolo_model.py --verify-only
  python scripts/setup_yolo_model.py --check nano --device cpu
        """,
    )

    parser.add_argument(
        "--model-size",
        choices=["nano", "small", "medium", "large"],
        default="nano",
        help="Model size (default: nano for fast inference)",
    )

    parser.add_argument(
        "--device",
        choices=["cuda", "cpu"],
        default="cuda",
        help="Inference device (default: cuda)",
    )

    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only verify existing model, don't download",
    )

    parser.add_argument(
        "--check",
        metavar="MODEL_SIZE",
        help="Check if model is available",
    )

    parser.add_argument(
        "--download",
        metavar="MODEL_SIZE",
        help="Download model (auto-download via ultralytics)",
    )

    parser.add_argument(
        "--test-inference",
        metavar="MODEL_PATH",
        help="Test model inference",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose logging",
    )

    args = parser.parse_args()

    # Setup logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(levelname)s: %(message)s",
    )

    setup = YOLOModelSetup()

    # Handle different commands
    if args.check:
        model_path = setup.verify_model_availability(args.check)
        if model_path:
            print(f"✓ Model available: {model_path}")
            return 0
        else:
            print(f"✗ Model not available")
            return 1

    if args.download:
        model_path = setup.download_model(args.download)
        if model_path:
            print(f"✓ Model ready: {model_path}")
            return 0
        else:
            print(f"✗ Download failed")
            return 1

    if args.test_inference:
        success = setup.verify_model_inference(Path(args.test_inference))
        return 0 if success else 1

    if args.verify_only:
        model_path = setup.verify_model_availability(args.model_size)
        if model_path:
            success = setup.verify_model_inference(model_path)
            return 0 if success else 1
        else:
            print(f"✗ Model not found: {args.model_size}")
            setup.print_setup_instructions(args.model_size)
            return 1

    # Default: setup flow
    logger.info(f"Checking YOLO {args.model_size} model availability...")
    model_path = setup.verify_model_availability(args.model_size)

    if model_path:
        logger.info(f"✓ Model found: {model_path}")
        logger.info("Running inference test...")
        success = setup.verify_model_inference(model_path)
        if success:
            logger.info(f"✓ Setup complete! Model ready for use")
            logger.info(f"Add to config:")
            logger.info(f"  use_watermark_tracker: true")
            logger.info(f"  yolo_model_path: {model_path}")
            return 0
        else:
            logger.error("Inference test failed")
            return 1
    else:
        logger.info(f"Model not found. Attempting download...")
        model_path = setup.download_model(args.model_size)

        if model_path:
            logger.info(f"✓ Download successful: {model_path}")
            success = setup.verify_model_inference(model_path)
            if success:
                logger.info(f"✓ Setup complete! Model ready for use")
                return 0
        else:
            logger.error("Setup failed. See instructions below:")
            setup.print_setup_instructions(args.model_size)
            return 1


if __name__ == "__main__":
    sys.exit(main())
