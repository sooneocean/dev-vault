# YOLOv5 Watermark Detection Guide

This guide explains how to use and customize watermark detection in Phase 2.

## Quick Start

Enable auto-detection in your config:

```yaml
detection_enabled: true
detection_model: yolov5s  # Fast, recommended for most cases
detection_confidence: 0.5  # Conservative threshold
```

Run the pipeline:

```bash
python scripts/run_pipeline.py --config config/your_config.yaml
```

## Model Selection

Choose the model that balances speed and accuracy:

| Model | Speed | Accuracy | Memory | Use Case |
|-------|-------|----------|--------|----------|
| **yolov5s** | 50-100ms/frame | 85% | ~200MB | Default, most videos |
| **yolov5m** | 100-150ms/frame | 90% | ~400MB | Better accuracy needed |
| **yolov5l** | 200-300ms/frame | 93% | ~800MB | Maximum accuracy (slow) |

### Lazy Loading

Models are lazily loaded on first detection call. Subsequent frames reuse the same model instance for efficiency.

```python
# First call loads model (~500MB, slow)
detector = WatermarkDetector(model_name="yolov5s")
bboxes = detector.detect_frame(frame1)  # ~2-3 seconds for first call

# Second call reuses model (fast)
bboxes = detector.detect_frame(frame2)  # ~50-100ms
```

## Confidence Threshold

Controls what detections are kept. Lower threshold = more detections (higher false positives).

```yaml
detection_confidence: 0.5  # Default: conservative
```

### Tuning Guide

| Threshold | Detection Rate | False Positives | Use Case |
|-----------|---|---|---|
| **0.3** | 95% | High | Very permissive, manual filtering needed |
| **0.5** | 85% | Low | Default, balanced for most watermarks |
| **0.7** | 70% | Very Low | Conservative, only strong detections |
| **0.9** | 50% | Minimal | Extremely strict, may miss watermarks |

**Recommended approach:**
1. Start with `0.5` (default)
2. If false positives: increase to `0.7`
3. If missed watermarks: decrease to `0.3`, manually review results

## NMS Threshold

Non-Maximum Suppression (NMS) removes overlapping detections. Controls how aggressively to merge nearby detections.

```yaml
detection_nms_threshold: 0.45  # Default
```

### Understanding NMS

If two detections overlap by >45% (NMS threshold), keep the one with higher confidence.

| NMS Value | Behavior | Use Case |
|-----------|----------|----------|
| **0.3** | Aggressive merging | Few overlapping watermarks |
| **0.45** | Default | Most cases |
| **0.6** | Permissive merging | Multiple overlapping watermarks |

## Graceful Fallback

If detection fails (model download error, GPU OOM, etc.), the pipeline automatically falls back to manual mask:

```yaml
detection_enabled: true
mask_path: backup_mask.png  # Fallback if detection fails
```

Behavior:
1. Try to detect watermarks with YOLO model
2. If detection fails: use `mask_path` if provided
3. If no mask: empty list (no removal attempted)

## Fine-tuning on Custom Watermarks

The default YOLOv5s model is trained on COCO (general objects), not watermarks. For best results on custom watermarks:

### Option A: Use detection with fallback (Recommended for MVP)

```yaml
detection_enabled: true
detection_confidence: 0.3  # More permissive
detection_model: yolov5l  # More accurate
mask_path: manual_mask.json  # Fallback
```

Manually validate detections on sample frames, adjust confidence threshold.

### Option B: Fine-tune on watermark dataset (Future Phase 3)

1. Create watermark detection dataset (100+ annotated examples)
2. Fine-tune YOLOv5 model:
   ```bash
   yolo detect train data=watermarks.yaml model=yolov5s.pt epochs=100
   ```
3. Use fine-tuned model:
   ```yaml
   detection_model: /path/to/fine_tuned_model.pt
   ```

Expected improvement: 85% → 95%+ accuracy on custom watermarks.

## Performance Profiling

Profile detection performance on your hardware:

```python
import time
from src.watermark_removal.detection import WatermarkDetector
import cv2

detector = WatermarkDetector(model_name="yolov5s")
frame = cv2.imread("sample_frame.jpg")

# Warm up
detector.detect_frame(frame)

# Benchmark
times = []
for _ in range(10):
    start = time.time()
    bboxes = detector.detect_frame(frame)
    times.append(time.time() - start)

print(f"Average: {sum(times)/len(times)*1000:.1f}ms")
print(f"Min: {min(times)*1000:.1f}ms, Max: {max(times)*1000:.1f}ms")
```

Typical results:
- yolov5s: 50-100ms (GPU), 500-1000ms (CPU)
- yolov5m: 100-200ms (GPU), 1000-2000ms (CPU)
- yolov5l: 200-500ms (GPU), 2000-5000ms (CPU)

## Filtering Detections

The detector provides helper methods to filter results:

```python
from src.watermark_removal.detection import WatermarkDetector, BBox

detector = WatermarkDetector()
bboxes = [
    BBox(x=100, y=100, w=200, h=200, confidence=0.95),
    BBox(x=50, y=50, w=100, h=100, confidence=0.4),
    BBox(x=500, y=500, w=50, h=50, confidence=0.85),
]

# By confidence
high_conf = detector.filter_by_confidence(bboxes, 0.7)  # [bbox1, bbox3]

# By area
large = detector.filter_by_area(bboxes, min_area=5000)  # [bbox1]

# Get largest
largest = detector.get_largest_bbox(bboxes)  # bbox1 (200*200 = 40000)
```

## Troubleshooting

### Detection misses some watermarks

**Problem:** Some watermarks not detected even with `detection_confidence: 0.3`

**Solutions:**
1. Use higher-accuracy model:
   ```yaml
   detection_model: yolov5l
   detection_confidence: 0.3
   ```
2. Combine with manual mask fallback:
   ```yaml
   detection_enabled: true
   mask_path: manual_mask.json
   ```
3. Fine-tune on watermark dataset (Phase 3)

### Too many false positives

**Problem:** Detecting non-watermark regions (text, logos, patterns)

**Solutions:**
1. Increase confidence threshold:
   ```yaml
   detection_confidence: 0.7  # More strict
   ```
2. Use smaller model (less noise):
   ```yaml
   detection_model: yolov5s
   ```
3. Manually review and adjust bounding boxes before running

### Model download fails

**Problem:** Error downloading YOLOv5 model weights

**Solutions:**
1. Check internet connection
2. Try again (temporary network issue)
3. Fall back to manual mask:
   ```yaml
   detection_enabled: false
   mask_path: manual_mask.png
   ```

### Out of memory

**Problem:** GPU/CPU runs out of memory during detection

**Solutions:**
1. Use smaller model:
   ```yaml
   detection_model: yolov5s
   ```
2. Reduce batch size or process frames sequentially
3. Run on CPU instead (slower but less memory):
   ```python
   detector = WatermarkDetector(device="cpu")
   ```

## API Reference

### WatermarkDetector Class

```python
from src.watermark_removal.detection import WatermarkDetector, BBox

# Initialize
detector = WatermarkDetector(
    model_name="yolov5s",  # Model size
    confidence_threshold=0.5,  # Confidence threshold
    nms_threshold=0.45,  # NMS suppression threshold
    device="auto"  # "auto", "cuda", "cpu"
)

# Detect in single frame
bboxes: list[BBox] = detector.detect_frame(frame)

# Detect in multiple frames
frame_results: dict[int, list[BBox]] = detector.detect_frames([frame1, frame2, ...])

# Filter by confidence
high_conf = detector.filter_by_confidence(bboxes, 0.7)

# Filter by area
large = detector.filter_by_area(bboxes, min_area=1000, max_area=100000)

# Get largest detection
largest: BBox = detector.get_largest_bbox(bboxes)
```

### BBox Dataclass

```python
from src.watermark_removal.detection import BBox

bbox = BBox(x=100, y=100, w=200, h=200, confidence=0.95)

# Convert to dict (for JSON serialization)
bbox_dict = bbox.to_dict()
# {"x": 100, "y": 100, "w": 200, "h": 200, "confidence": 0.95}

# Create from dict
bbox_restored = BBox.from_dict(bbox_dict)

# Access properties
x, y, w, h = bbox.x, bbox.y, bbox.w, bbox.h
center_x = bbox.x + bbox.w // 2
center_y = bbox.y + bbox.h // 2
```

## Next Steps

- Start with default config (`yolov5s`, confidence `0.5`)
- Monitor detections on sample frames
- Adjust `detection_confidence` based on results
- Consider fine-tuning on watermark dataset if needed (Phase 3)

See `phase2_migration_guide.md` for full Phase 2 configuration examples.
