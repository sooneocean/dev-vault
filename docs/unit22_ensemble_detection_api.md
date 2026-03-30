# Unit 22: Multi-Model Ensemble Watermark Detection - API Documentation

## Overview

Unit 22 implements multi-model ensemble voting for watermark detection, combining YOLOv5s and YOLOv5m models to improve detection accuracy. The implementation provides:

1. **EnsembleDetector**: Loads multiple YOLO models and performs voting-based fusion
2. **BBoxVoter**: Confidence-weighted averaging of detections across models
3. **DetectionOrchestrator**: Unified interface that switches between single and ensemble modes based on configuration

## Configuration

### Enable Ensemble Detection

In your YAML config file:

```yaml
video_path: /path/to/video.mp4
mask_path: /path/to/mask.png
output_dir: /path/to/output

# Enable ensemble detection
ensemble_detection_enabled: true
ensemble_models: ["yolov5s", "yolov5m"]
ensemble_voting_mode: "confidence_weighted"
ensemble_iou_threshold: 0.3
ensemble_nms_threshold: 0.45
ensemble_model_accuracies:
  yolov5s: 0.85
  yolov5m: 0.90
  yolov5l: 0.92
```

### Default Configuration

If not specified, ensemble defaults to:
- **ensemble_detection_enabled**: `false` (uses Phase 2 single-model behavior)
- **ensemble_models**: `["yolov5s", "yolov5m"]`
- **ensemble_voting_mode**: `"confidence_weighted"` (only mode in MVP)
- **ensemble_iou_threshold**: `0.3` (minimum overlap for matching)
- **ensemble_nms_threshold**: `0.45` (NMS suppression threshold)
- **ensemble_model_accuracies**: `{yolov5s: 0.85, yolov5m: 0.90, yolov5l: 0.92}`

## API Usage

### Using DetectionOrchestrator (Recommended)

The orchestrator provides a unified interface that automatically switches between single and ensemble modes:

```python
from src.watermark_removal.detection import DetectionOrchestrator
from src.watermark_removal.core.config_manager import ConfigManager
from src.watermark_removal.core.types import ProcessConfig
import numpy as np

# Option 1: From configuration file
config_mgr = ConfigManager("config.yaml")
config = config_mgr.load()

# Create orchestrator from config
orchestrator = DetectionOrchestrator(
    ensemble_detection_enabled=config.ensemble_detection_enabled,
    ensemble_models=config.ensemble_models,
    ensemble_voting_mode=config.ensemble_voting_mode,
    ensemble_iou_threshold=config.ensemble_iou_threshold,
    ensemble_nms_threshold=config.ensemble_nms_threshold,
    ensemble_model_accuracies=config.ensemble_model_accuracies,
    single_model="yolov5s",  # Fallback for single mode
    single_model_confidence_threshold=0.5,
)

# Detect in a frame
frame = np.zeros((480, 640, 3), dtype=np.uint8)  # Your video frame
bboxes = orchestrator.detect_frame(frame)

# Or detect in multiple frames
frames = [np.zeros((480, 640, 3), dtype=np.uint8) for _ in range(10)]
results_dict = orchestrator.detect_frames(frames)
# returns {frame_idx: [BBox, ...], ...}

# Check detector status
status = orchestrator.get_detector_status()
print(status)
# Single mode: {"mode": "single", "model": "yolov5s", "loaded": True/False}
# Ensemble mode: {"mode": "ensemble", "models": ["yolov5s", "yolov5m"], "model_status": {...}}
```

### Using EnsembleDetector Directly

For more control, use EnsembleDetector directly:

```python
from src.watermark_removal.detection import EnsembleDetector, BBox
import numpy as np

# Configure models
model_configs = [
    ("yolov5s", {"confidence_threshold": 0.5}),
    ("yolov5m", {"confidence_threshold": 0.5}),
]

# Create detector
detector = EnsembleDetector(
    model_configs=model_configs,
    model_accuracies={"yolov5s": 0.85, "yolov5m": 0.90},
    iou_threshold=0.3,
    nms_threshold=0.45,
)

# Detect watermarks
frame = np.zeros((480, 640, 3), dtype=np.uint8)
bboxes = detector.detect_frame(frame)  # Returns list[BBox]

# Batch detection
frames = [np.zeros((480, 640, 3), dtype=np.uint8) for _ in range(10)]
results = detector.detect_frames(frames)  # Returns dict[frame_idx, list[BBox]]

# Check model loading status
status = detector.get_detector_status()
# Returns {"yolov5s": True/False, "yolov5m": True/False}
```

### Using BBoxVoter Directly

For custom voting logic:

```python
from src.watermark_removal.detection import BBox, BBoxVoter

# Create voter
voter = BBoxVoter(
    model_accuracies={"yolov5s": 0.85, "yolov5m": 0.90},
    iou_threshold=0.3,
)

# Define detections from each model
bbox_s = BBox(x=100, y=100, w=100, h=100, confidence=0.95)
bbox_m = BBox(x=105, y=105, w=95, h=95, confidence=0.90)

detections_by_model = {
    "yolov5s": [bbox_s],
    "yolov5m": [bbox_m],
}

# Vote
voting_results = voter.vote(detections_by_model)
# Returns list[VotingResult] with merged bboxes and confidences

# Apply NMS
final_results = voter.apply_nms(voting_results, nms_threshold=0.45)
# Returns list[VotingResult] after suppressing overlaps

# Extract final bboxes
final_bboxes = [result.bbox for result in final_results]
```

## Data Types

### BBox
```python
@dataclass
class BBox:
    x: int                    # Left edge in pixels
    y: int                    # Top edge in pixels
    w: int                    # Width in pixels
    h: int                    # Height in pixels
    confidence: float         # Detection confidence (0.0-1.0)
```

### VotingResult
```python
@dataclass
class VotingResult:
    bbox: BBox                           # Merged bbox from voting
    source_models: list[str]             # Models that detected this
    num_votes: int                       # Number of detections merged
    individual_confidences: list[float]  # Original confidences per model
```

## How Ensemble Voting Works

1. **Model Loading**: Models are lazily loaded on first detection (minimize startup overhead)

2. **Per-Frame Detection**: Each model runs inference on the frame independently

3. **Voting**:
   - Select anchor model (first with detections)
   - For each anchor detection, find matching detections in other models
   - Match criteria: IoU > threshold (default 0.3)
   - Merge matched detections:
     - Bbox: weighted average (weights = model accuracies)
     - Confidence: weighted average (weights = model accuracies)

4. **NMS Post-Processing**: Remove overlapping merged detections (NMS threshold 0.45)

5. **Result**: List of final bboxes with merged confidences

## Example: Voting Algorithm

```
Input: Two models detect watermarks
yolov5s: [BBox(100, 100, 100, 100, conf=0.95)]
yolov5m: [BBox(105, 105, 95, 95, conf=0.90)]

IoU Matching (threshold 0.3):
  yolov5s detection matches yolov5m detection (IoU ≈ 0.89)

Weight Calculation:
  yolov5s weight = 0.85 / (0.85 + 0.90) = 0.486
  yolov5m weight = 0.90 / (0.85 + 0.90) = 0.514

Bbox Averaging:
  merged_x = 100 * 0.486 + 105 * 0.514 ≈ 102.5 → 102 (rounded)
  merged_y = 100 * 0.486 + 105 * 0.514 ≈ 102.5 → 102
  merged_w = 100 * 0.486 + 95 * 0.514 ≈ 97.6 → 98
  merged_h = 100 * 0.486 + 95 * 0.514 ≈ 97.6 → 98

Confidence Averaging:
  merged_conf = 0.95 * 0.486 + 0.90 * 0.514 ≈ 0.924

Output: [BBox(102, 102, 98, 98, conf=0.924)]
```

## Graceful Degradation

If one model fails to load:

```python
# With ensemble disabled (fallback to single model):
orchestrator = DetectionOrchestrator(ensemble_detection_enabled=False)
bboxes = orchestrator.detect_frame(frame)  # Uses yolov5s

# With ensemble enabled (partial failure):
orchestrator = DetectionOrchestrator(ensemble_detection_enabled=True)
# If yolov5m fails to load:
# - Uses yolov5s detections instead
# - Logs warning: "Failed to load model yolov5m: ..."
# - Returns valid results from yolov5s
bboxes = orchestrator.detect_frame(frame)
```

## Performance Characteristics

- **Initialization**: Minimal (lazy loading deferred to first inference)
- **Per-Frame Latency**: ~2x single model (sequential execution of both models)
  - yolov5s: ~50ms per frame on GPU
  - yolov5m: ~70ms per frame on GPU
  - Voting & NMS: ~5ms
  - **Total ensemble**: ~125ms per frame
- **Memory**: Both models loaded in VRAM (~2GB combined for YOLOv5s+m on GPU)

## Testing

Run unit tests:
```bash
pytest tests/test_ensemble_detection.py -v
```

Run config tests:
```bash
pytest tests/test_config_manager.py::TestEnsembleConfiguration -v
```

## Migration from Phase 2

Phase 2 used single WatermarkDetector. To migrate to ensemble:

1. **Enable in config**:
   ```yaml
   ensemble_detection_enabled: true
   ```

2. **No code changes needed** if using DetectionOrchestrator:
   ```python
   # Old Phase 2 code still works (uses single model)
   orchestrator = DetectionOrchestrator(ensemble_detection_enabled=False)

   # New ensemble mode (improved accuracy)
   orchestrator = DetectionOrchestrator(ensemble_detection_enabled=True)
   ```

## Future Work (Phase 3A+)

- Parallel GPU execution of models (reduce latency from 2x to 1.5x)
- Learned fusion networks (improve accuracy beyond voting)
- Additional ensemble modes beyond confidence_weighted
- RF-DETR model integration (Phase 3B)
- Production accuracy benchmarking vs single model
