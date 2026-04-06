---
title: Mask Format Specification
type: project
tags: [project, active]
created: 2026-04-03
updated: 2026-04-03
status: active
maturity: growing
domain: knowledge-management
summary: ""
---

# Mask Format Specification

This document defines the formats for specifying watermark regions in the Dynamic Watermark Removal System.

## Overview

The system supports two mask formats:

1. **Static Mask (Image)** — PNG/JPEG image defining a fixed watermark region
2. **Dynamic Mask (JSON)** — Bounding box list with per-frame coordinates for moving watermarks

## Static Mask Format (Image)

A static mask is a single image file that specifies the watermark region for all frames.

### Format Requirements

- **File Format:** PNG or JPEG
- **Dimensions:** Must match the input video frame dimensions (width × height)
  - Example: 1920×1080 for 1080p video
  - If dimensions don't match, mask will be interpreted at the top-left corner or may fail
- **Color Depth:** 8-bit grayscale or RGB (single-channel used)
- **Encoding:** Standard PNG (recommended) or JPEG

### Pixel Interpretation

- **Non-zero pixels** — Mark the watermark region (typically white: 255)
  - These pixels are replaced during inpainting
  - The bounding box of all non-zero pixels defines the watermark area
- **Zero pixels** — Mark preserve regions (typically black: 0)
  - These pixels are preserved in the original frame
  - Surrounding area provides context for inpainting

### Example: Creating a Static Mask

Using Python with OpenCV:

```python
import cv2
import numpy as np

# Create a 1920×1080 mask (all black by default)
mask = np.zeros((1080, 1920), dtype=np.uint8)

# Mark watermark region (e.g., logo at bottom-right)
# Rectangle from (x=1600, y=950) with size 200×100
mask[950:1050, 1600:1800] = 255

# Save as PNG
cv2.imwrite('watermark_mask.png', mask)
```

Using ImageMagick:

```bash
# Create 1920×1080 black image
convert -size 1920x1080 xc:black watermark_mask.png

# Add white rectangle (watermark region)
convert watermark_mask.png -fill white \
  -draw "rectangle 1600,950 1800,1050" \
  watermark_mask.png
```

### Example: Real-World Usage

```yaml
# config.yaml
video_path: input.mp4
mask_path: watermark_mask.png    # Static PNG mask
output_dir: ./output
```

## Dynamic Mask Format (JSON)

A dynamic mask is a JSON file specifying bounding box coordinates for each frame with a watermark.

### Format Specification

JSON array of bounding box objects:

```json
[
  {
    "frame": <frame_number>,
    "x": <left_pixel>,
    "y": <top_pixel>,
    "w": <width_pixels>,
    "h": <height_pixels>
  },
  ...
]
```

### Field Definitions

- **`frame`** (integer, required)
  - Zero-based frame index in the video
  - Frame 0 is the first frame
  - Must be in ascending order (optional but recommended for clarity)

- **`x`** (integer, required)
  - Left edge of bounding box in pixels
  - 0 = leftmost pixel of frame
  - Must be >= 0 and < frame_width

- **`y`** (integer, required)
  - Top edge of bounding box in pixels
  - 0 = topmost pixel of frame
  - Must be >= 0 and < frame_height

- **`w`** (integer, required)
  - Width of bounding box in pixels
  - Must be > 0
  - x + w must be <= frame_width

- **`h`** (integer, required)
  - Height of bounding box in pixels
  - Must be > 0
  - y + h must be <= frame_height

### Sparse Frame Coverage

Frames not listed in the JSON are treated as having **no watermark** and are skipped during preprocessing (the original frame is used directly).

Example: Only frames 0, 1, 2 have a watermark; frames 3-10 are clean:

```json
[
  {"frame": 0, "x": 100, "y": 50, "w": 200, "h": 100},
  {"frame": 1, "x": 110, "y": 50, "w": 200, "h": 100},
  {"frame": 2, "x": 120, "y": 50, "w": 200, "h": 100}
]
```

Frames 3-10 will not be processed (watermark region not defined), and the pipeline will output them unchanged.

### Example: Simple Moving Watermark

A watermark logo that drifts left-to-right across the video:

```json
[
  {"frame": 0, "x": 0, "y": 900, "w": 200, "h": 100},
  {"frame": 1, "x": 50, "y": 900, "w": 200, "h": 100},
  {"frame": 2, "x": 100, "y": 900, "w": 200, "h": 100},
  {"frame": 3, "x": 150, "y": 900, "w": 200, "h": 100},
  {"frame": 4, "x": 200, "y": 900, "w": 200, "h": 100}
]
```

### Example: Real-World Usage

```yaml
# config.yaml
video_path: input.mp4
mask_path: watermark_bbox.json    # Dynamic JSON mask
output_dir: ./output
```

### Creating Dynamic Masks Programmatically

#### Using Python

```python
import json

# Track watermark across frames
# Example: watermark moves 50px right per frame
bboxes = []
for frame_idx in range(30):
    x = 100 + (frame_idx * 50)  # Drifts right
    y = 900
    w = 200
    h = 100

    # Validate bounds
    if x + w <= 1920:  # frame_width
        bboxes.append({
            "frame": frame_idx,
            "x": x,
            "y": y,
            "w": w,
            "h": h
        })

# Save to JSON
with open('watermark_bbox.json', 'w') as f:
    json.dump(bboxes, f, indent=2)
```

#### Using YOLO Detection (Future)

Phase 2 will support automatic watermark detection:

```python
# Pseudo-code (not yet implemented)
# detector = WatermarkDetector(model='yolo-watermark')
# bboxes = detector.detect_frames(video_path)
# save_json_bboxes(bboxes, 'watermark_bbox.json')
```

## Format Detection

The system auto-detects mask format based on file extension:

- `.png`, `.jpg`, `.jpeg` → Treated as static image mask
- `.json` → Treated as dynamic bbox JSON

Explicit format specification in config (future enhancement):

```yaml
mask_path: watermark.data
mask_format: json  # or 'image'
```

## Validation Rules

The system validates masks during load:

### Static Image Masks

1. ✅ File exists and is readable
2. ✅ Dimensions match video frame size (W × H)
3. ✅ Format is valid PNG/JPEG
4. ✅ At least one non-zero pixel exists (defines watermark region)

### Dynamic JSON Masks

1. ✅ File exists and is valid JSON
2. ✅ Root element is an array
3. ✅ Each element has required fields: `frame`, `x`, `y`, `w`, `h`
4. ✅ Frame indices are unique (no duplicates)
5. ✅ Coordinates are within frame bounds: 0 <= x, y; x+w <= width; y+h <= height
6. ✅ Dimensions are positive: w > 0, h > 0

### Error Handling

**If validation fails:**

- Error is logged with details (missing fields, out-of-bounds, etc.)
- Pipeline stops (default: `skip_errors_in_preprocessing: false`)
- Or frame is skipped (if `skip_errors_in_preprocessing: true`)

## Best Practices

### Static Masks

1. **Use high-contrast white on black** for clarity
   - Non-zero = 255 (white) for watermark region
   - Zero = 0 (black) for preserve region

2. **Include context padding** around watermark
   - Inpainting works better with surrounding pixels
   - Typically 50-100px margin around logo

3. **Align precisely with actual watermark**
   - Visual inspection is important
   - Try overlaying mask on frame to verify alignment

4. **Consider frame variations**
   - If watermark size/position changes slightly per-frame, consider dynamic mask instead
   - Static masks apply to all frames identically

### Dynamic Masks

1. **Start with 5-10 frames** for testing
   - Verify coordinates are correct before processing entire video
   - Use small test video to validate

2. **Track watermark center and size** consistently
   - Ensure `w` and `h` don't fluctuate wildly
   - Small interpolation errors are acceptable

3. **Include sparse frames** if watermark disappears
   - Only list frames with watermark
   - Unlisted frames pass through unchanged

4. **Round coordinates carefully**
   - Use integer pixel values (no decimals)
   - Small rounding errors (±1px) are acceptable

5. **Generate from tracking algorithm** when possible
   - Use object detection or manual frame-by-frame annotation
   - Verify first few and last few frames manually

## Examples

### Example 1: Bottom-Right Logo (Static)

Watermark is a logo fixed at bottom-right:

```python
# Create 1920×1080 mask
mask = np.zeros((1080, 1920), dtype=np.uint8)

# Bottom-right corner: (1720, 980) to (1920, 1080)
# Size: 200×100
mask[980:1080, 1720:1920] = 255

cv2.imwrite('logo_mask.png', mask)
```

### Example 2: Moving Banner (Dynamic)

Watermark is a banner that scrolls from left to right:

```json
[
  {"frame": 0, "x": 0, "y": 900, "w": 400, "h": 100},
  {"frame": 1, "x": 50, "y": 900, "w": 400, "h": 100},
  {"frame": 2, "x": 100, "y": 900, "w": 400, "h": 100},
  {"frame": 3, "x": 150, "y": 900, "w": 400, "h": 100},
  {"frame": 4, "x": 200, "y": 900, "w": 400, "h": 100}
]
```

### Example 3: Intermittent Watermark (Dynamic)

Watermark appears only in certain frames (e.g., frames 0, 5, 10):

```json
[
  {"frame": 0, "x": 100, "y": 50, "w": 200, "h": 100},
  {"frame": 5, "x": 100, "y": 50, "w": 200, "h": 100},
  {"frame": 10, "x": 100, "y": 50, "w": 200, "h": 100}
]
```

Frames 1-4, 6-9, 11+ pass through unchanged.

### Example 4: Scaling Watermark (Dynamic)

Watermark size changes per frame:

```json
[
  {"frame": 0, "x": 100, "y": 100, "w": 100, "h": 100},
  {"frame": 1, "x": 90, "y": 90, "w": 120, "h": 120},
  {"frame": 2, "x": 80, "y": 80, "w": 140, "h": 140},
  {"frame": 3, "x": 70, "y": 70, "w": 160, "h": 160}
]
```

## Troubleshooting

### "Mask dimensions don't match video"

**Problem:** Static PNG mask size doesn't match frame size

**Solution:**
```python
import cv2

# Resize mask to match frame
mask = cv2.imread('watermark_mask.png', cv2.IMREAD_GRAYSCALE)
mask_resized = cv2.resize(mask, (1920, 1080))  # target_width, target_height
cv2.imwrite('watermark_mask_resized.png', mask_resized)
```

### "No non-zero pixels in mask"

**Problem:** Static PNG is all black (no watermark defined)

**Solution:**
- Verify PNG was created correctly with white watermark region
- Check file size (should be > 0 bytes and not corrupted)
- Recreate using ImageMagick or Python OpenCV

### "Invalid JSON: expected array"

**Problem:** Dynamic JSON file has wrong structure

**Solution:**
```json
// ✅ Correct
[
  {"frame": 0, "x": 100, "y": 50, "w": 200, "h": 100}
]

// ❌ Wrong (object instead of array)
{
  "bboxes": [
    {"frame": 0, "x": 100, "y": 50, "w": 200, "h": 100}
  ]
}
```

### "Bounding box out of bounds"

**Problem:** Coordinates exceed frame dimensions

**Solution:**
- Check frame resolution (1920×1080 is common but not universal)
- Validate: `x >= 0, y >= 0, x+w <= width, y+h <= height`
- Use frame inspection tool to verify watermark position

```python
# Verify bounds
width, height = 1920, 1080
for bbox in bboxes:
    assert bbox['x'] >= 0 and bbox['y'] >= 0
    assert bbox['x'] + bbox['w'] <= width
    assert bbox['y'] + bbox['h'] <= height
```
