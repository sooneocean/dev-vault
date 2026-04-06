#!/usr/bin/env python3
"""
Generate synthetic test videos for end-to-end testing.

Four test scenarios:
1. Static watermark (logo) - simple case
2. Moving watermark (tracking) - left-to-right movement
3. Multiple watermarks - 3 watermarks on same frame
4. Complex background - challenging inpainting scenario

Each video: 30 frames, 1080p, 30 fps
"""

import logging
from pathlib import Path
from typing import Tuple
import sys

try:
    import cv2
    import numpy as np
except ImportError as e:
    print(f"Error: {e}. Install: pip install numpy opencv-python")
    sys.exit(1)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


def create_gradient_frame(
    width: int,
    height: int,
    color1: Tuple[int, int, int],
    color2: Tuple[int, int, int],
    direction: str = "vertical",
) -> np.ndarray:
    """
    Create a gradient background frame.

    Args:
        width: Frame width
        height: Frame height
        color1: RGB tuple for start color
        color2: RGB tuple for end color
        direction: "vertical" or "horizontal"

    Returns:
        Frame with gradient background
    """
    frame = np.zeros((height, width, 3), dtype=np.uint8)

    if direction == "vertical":
        for row in range(height):
            alpha = row / height
            frame[row, :] = [
                int(color1[c] * (1 - alpha) + color2[c] * alpha)
                for c in range(3)
            ]
    else:
        for col in range(width):
            alpha = col / width
            frame[:, col] = [
                int(color1[c] * (1 - alpha) + color2[c] * alpha)
                for c in range(3)
            ]

    return frame


def add_noise(
    frame: np.ndarray,
    intensity: float = 0.1,
) -> np.ndarray:
    """Add noise to frame."""
    noise = np.random.normal(0, intensity * 255, frame.shape).astype(np.uint8)
    return cv2.addWeighted(frame, 0.9, noise, 0.1, 0)


def draw_watermark(
    frame: np.ndarray,
    x: int,
    y: int,
    w: int,
    h: int,
    label: str = "WATERMARK",
) -> np.ndarray:
    """Draw a watermark on frame."""
    # Semi-transparent white background
    overlay = frame.copy()
    cv2.rectangle(overlay, (x, y), (x + w, y + h), (200, 200, 200), -1)
    frame = cv2.addWeighted(frame, 0.7, overlay, 0.3, 0)

    # Border
    cv2.rectangle(frame, (x, y), (x + w, y + h), (100, 100, 100), 2)

    # Text
    font = cv2.FONT_HERSHEY_SIMPLEX
    text_size = cv2.getTextSize(label, font, 1.0, 2)[0]
    text_x = x + (w - text_size[0]) // 2
    text_y = y + (h + text_size[1]) // 2

    cv2.putText(frame, label, (text_x, text_y), font, 1.0, (0, 0, 0), 2)

    return frame


def generate_static_watermark_video(output_path: Path) -> Path:
    """
    Scenario 1: Static watermark (logo in top-left).

    Simple test case: watermark stays in same position.
    """
    logger.info(f"Generating: Static watermark video")

    width, height = 1920, 1080
    fps = 30
    num_frames = 30

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))

    watermark_bbox = (100, 100, 200, 150)
    x, y, w, h = watermark_bbox

    for frame_id in range(num_frames):
        # Blue to green gradient
        frame = create_gradient_frame(width, height, (255, 0, 0), (0, 255, 0))
        frame = add_noise(frame)

        # Static watermark
        frame = draw_watermark(frame, x, y, w, h, "LOGO")

        # Add frame number
        cv2.putText(
            frame, f"Frame {frame_id}", (50, height - 50),
            cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2
        )

        writer.write(frame)

    writer.release()
    logger.info(f"  Created: {output_path} ({output_path.stat().st_size / 1e6:.1f} MB)")

    return output_path


def generate_moving_watermark_video(output_path: Path) -> Path:
    """
    Scenario 2: Moving watermark (left-to-right motion).

    Tests watermark tracking capability.
    """
    logger.info(f"Generating: Moving watermark video")

    width, height = 1920, 1080
    fps = 30
    num_frames = 30

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))

    w, h = 200, 150

    for frame_id in range(num_frames):
        # Red to yellow gradient
        frame = create_gradient_frame(width, height, (0, 0, 255), (0, 255, 255))
        frame = add_noise(frame)

        # Moving watermark (left to right)
        progress = frame_id / (num_frames - 1)
        x = int(100 + progress * (width - 300 - 100))
        y = 100

        frame = draw_watermark(frame, x, y, w, h, "MOVING")

        # Add moving object (circle)
        obj_x = int(width / 2 + 300 * (progress - 0.5))
        obj_y = int(height / 2)
        cv2.circle(frame, (obj_x, obj_y), 40, (200, 200, 0), -1)

        # Add frame number
        cv2.putText(
            frame, f"Frame {frame_id} (x={x})", (50, height - 50),
            cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2
        )

        writer.write(frame)

    writer.release()
    logger.info(f"  Created: {output_path} ({output_path.stat().st_size / 1e6:.1f} MB)")

    return output_path


def generate_multi_watermark_video(output_path: Path) -> Path:
    """
    Scenario 3: Multiple watermarks (3 watermarks on same frame).

    Tests multi-watermark processing.
    """
    logger.info(f"Generating: Multi-watermark video")

    width, height = 1920, 1080
    fps = 30
    num_frames = 30

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))

    watermarks = [
        (100, 100, 200, 150, "WM1"),      # Top-left
        (width - 300, 100, 200, 150, "WM2"),  # Top-right
        (width // 2 - 100, height - 250, 200, 150, "WM3"),  # Bottom-center
    ]

    for frame_id in range(num_frames):
        # Purple to cyan gradient
        frame = create_gradient_frame(width, height, (255, 0, 255), (255, 255, 0))
        frame = add_noise(frame)

        # Draw all watermarks
        for x, y, w, h, label in watermarks:
            frame = draw_watermark(frame, x, y, w, h, label)

        # Add frame number
        cv2.putText(
            frame, f"Frame {frame_id} (3 watermarks)", (50, height - 50),
            cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2
        )

        writer.write(frame)

    writer.release()
    logger.info(f"  Created: {output_path} ({output_path.stat().st_size / 1e6:.1f} MB)")

    return output_path


def generate_complex_background_video(output_path: Path) -> Path:
    """
    Scenario 4: Complex background (challenging inpainting).

    Watermark over complex texture/pattern.
    """
    logger.info(f"Generating: Complex background video")

    width, height = 1920, 1080
    fps = 30
    num_frames = 30

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))

    watermark_bbox = (100, 100, 200, 150)
    x, y, w, h = watermark_bbox

    for frame_id in range(num_frames):
        # Create base frame
        frame = np.zeros((height, width, 3), dtype=np.uint8)

        # Checkerboard pattern (challenging for inpainting)
        square_size = 50
        for i in range(0, height, square_size):
            for j in range(0, width, square_size):
                if ((i // square_size) + (j // square_size)) % 2 == 0:
                    frame[i:i+square_size, j:j+square_size] = (100, 100, 200)
                else:
                    frame[i:i+square_size, j:j+square_size] = (200, 100, 100)

        # Add diagonal stripes
        for i in range(0, height + width, 100):
            cv2.line(frame, (i, 0), (i - height, height), (150, 150, 50), 3)

        # Add noise
        frame = add_noise(frame, intensity=0.15)

        # Draw watermark
        frame = draw_watermark(frame, x, y, w, h, "COMPLEX")

        # Add frame number
        cv2.putText(
            frame, f"Frame {frame_id} (complex)", (50, height - 50),
            cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2
        )

        writer.write(frame)

    writer.release()
    logger.info(f"  Created: {output_path} ({output_path.stat().st_size / 1e6:.1f} MB)")

    return output_path


def main():
    """Generate all test videos."""
    fixtures_dir = Path(__file__).parent
    fixtures_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Generating test videos to: {fixtures_dir}")

    videos = [
        ("test_video_static_watermark.mp4", generate_static_watermark_video),
        ("test_video_moving_watermark.mp4", generate_moving_watermark_video),
        ("test_video_multi_watermark.mp4", generate_multi_watermark_video),
        ("test_video_complex_background.mp4", generate_complex_background_video),
    ]

    for filename, generator_func in videos:
        video_path = fixtures_dir / filename
        if video_path.exists():
            logger.info(f"  Skipping {filename} (already exists)")
            continue

        generator_func(video_path)

    logger.info(f"\n✓ All test videos generated")
    logger.info(f"  Location: {fixtures_dir}")


if __name__ == "__main__":
    main()
