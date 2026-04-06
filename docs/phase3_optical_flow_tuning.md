---
title: Phase 3: Optical Flow Tuning Guide
type: project
tags: [project, active]
created: 2026-04-03
updated: 2026-04-03
status: active
maturity: growing
domain: knowledge-management
summary: ""
---

# Phase 3: Optical Flow Tuning Guide

## Overview

Optical flow-based temporal smoothing is a Phase 3 feature that reduces inter-frame flicker and improves boundary smoothness when removing moving watermarks. This guide covers when to enable it, how to tune parameters, and how to debug flow computation failures.

## When to Enable Optical Flow

Enable optical flow (`optical_flow_enabled: true`) when:

1. **Moving watermarks** — Watermarks shift position between frames (e.g., floating logos)
2. **Temporal consistency matters** — You need smooth transitions across frames
3. **GPU available** — Optical flow computation benefits from CUDA acceleration
4. **High-resolution content** — Processing 1080p+ video with temporal artifacts

**Skip optical flow** when:

- Static watermarks only (fixed position, no movement)
- Real-time constraints (inference must be <50ms/frame)
- CPU-only deployment (flow computation is slow on CPU)
- Memory constrained (<2GB VRAM)

## Configuration Parameters

### `optical_flow_enabled` (boolean)
Default: `false`

Enable or disable optical flow computation entirely.

```yaml
optical_flow_enabled: true
```

### `optical_flow_resolution` (string)
Default: `"480"`
Valid values: `"480"` or `"1080"`

Resolution at which optical flow is computed. Lower resolution = faster, less precise.

- **"480"** — 480p flow (~1.4s/frame on GPU, 5% overhead)
  - Fast computation
  - Suitable for real-time or batch processing
  - Recommended for 1080p+ source (downsample, flow, upsample)

- **"1080"** — 1080p flow (~8-12s/frame on GPU, 15% overhead)
  - High precision alignment
  - Better for challenging watermark boundaries
  - Slower, use for archive/batch processing only

### `optical_flow_weight` (float, 0.0-1.0)
Default: `0.5`

Blend factor between original boundary and flow-warped boundary.

- **0.0** — Ignore optical flow entirely (same as disabled)
- **0.3** — Conservative smoothing (preserve detail)
- **0.5** — Balanced smoothing (recommended default)
- **0.7** — Aggressive smoothing (strong boundary alignment)
- **1.0** — Use only flow-warped boundary (may cause artifacts)

```yaml
optical_flow_weight: 0.5
```

## Tuning for Watermark Motion

### Step 1: Identify Motion Characteristics

Examine your watermark across frames:

```python
import cv2
import json

# Load mask (dynamic watermark with bounding boxes)
with open("mask.json") as f:
    frames = json.load(f)

# Check motion across frames
prev_bbox = None
for frame_id, data in frames.items():
    bbox = data["bbox"]  # [x, y, w, h]
    if prev_bbox:
        dx = abs(bbox[0] - prev_bbox[0])
        dy = abs(bbox[1] - prev_bbox[1])
        print(f"Frame {frame_id}: motion = ({dx}, {dy}) pixels")
    prev_bbox = bbox
```

Motion characteristics:

- **Small motion** (0-5 pixels/frame) → `optical_flow_weight: 0.3-0.4`
- **Moderate motion** (5-20 pixels/frame) → `optical_flow_weight: 0.5-0.6`
- **Large motion** (>20 pixels/frame) → `optical_flow_weight: 0.7-0.8`

### Step 2: Choose Resolution

Base decision on source video resolution and GPU capability:

```yaml
# 480p source, GPU available
optical_flow_resolution: "480"
optical_flow_weight: 0.5

# 1080p source, high-end GPU (RTX 3080+)
optical_flow_resolution: "1080"
optical_flow_weight: 0.6

# CPU-only or memory constrained
optical_flow_enabled: false
```

### Step 3: Tune Weight Parameter

Start with default (0.5) and adjust based on results:

1. **Extract a short test clip** (10-20 frames with watermark)
2. **Run pipeline** with test config:

```bash
python scripts/run_pipeline.py \
  --config config/test.yaml \
  --output output/test_weight_0.5
```

3. **Inspect output** for boundary artifacts:
   - If seams are visible → increase weight
   - If original boundaries distorted → decrease weight
   - If motion is tracked well → keep current weight

4. **Iterate** with different weights

```yaml
# Test suite
optical_flow_enabled: true
optical_flow_resolution: "480"

# Try sequence: 0.3, 0.5, 0.7
optical_flow_weight: 0.5
```

## Temporal Smoothing Alpha Parameter

The `temporal_smooth_alpha` parameter (in optical flow module) controls smoothing of flow fields across frames:

- **Default: 0.8** — High temporal coherence
- **Range: 0.0-1.0** — Higher = more temporal smoothing
- **Low (0.3-0.5)** — Responsive to frame-to-frame motion changes
- **High (0.7-0.9)** — Smooth trajectories but less responsive

Adjust if flow seems too jumpy or oversmoothed:

```python
# In optical_flow.py OpticalFlowProcessor
temporal_smooth_alpha = 0.8  # Increase to 0.95 for smoother
```

## Performance Impact

Expected overhead when optical flow is enabled:

| Feature | Resolution | GPU | Overhead | Total Time/Frame |
|---------|-----------|-----|----------|------------------|
| Optical flow only | 480p | RTX 3060 | 5% | +70ms |
| Optical flow only | 1080p | RTX 3060 | 15% | +200ms |
| Full Phase 3 | 480p | RTX 3060 | ~12% | +150ms |
| Full Phase 3 | 1080p | RTX 3060 | ~25% | +350ms |

**Recommendation**: Use 480p optical flow for most cases; reserve 1080p for critical quality requirements.

## Debugging Flow Computation Failures

### Issue: "Model loading failed" or PyTorch error

**Symptoms**: Log shows optical flow disabled, model unavailable

**Solutions**:

1. Verify PyTorch with CUDA support:
```bash
python -c "import torch; print(torch.cuda.is_available())"
```

2. Install torch with CUDA:
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

3. If CUDA unavailable, optical flow will fall back to CPU (slow)

### Issue: Out-of-memory (OOM) errors

**Symptoms**: "CUDA out of memory" during flow computation

**Solutions**:

1. Reduce resolution:
```yaml
optical_flow_resolution: "480"  # Not "1080"
```

2. Enable GPU memory optimization:
```python
# In optical_flow.py
torch.cuda.empty_cache()  # Clear cache before processing
```

3. Process frames sequentially (not batch):
```yaml
batch_size: 1  # Process one frame at a time
```

4. Disable optical flow if memory-critical:
```yaml
optical_flow_enabled: false
```

### Issue: Boundary distortion or artifacts

**Symptoms**: Inpainted regions look warped or misaligned

**Solutions**:

1. **Reduce weight** — May be over-relying on flow:
```yaml
optical_flow_weight: 0.3  # Conservative
```

2. **Check flow validity** — Add debug logging:
```python
from watermark_removal.optical_flow import OpticalFlowProcessor

processor = OpticalFlowProcessor(resolution="480", weight=0.5)
flow_data = processor.compute_flow(frame1, frame2)

# Check confidence
print(f"Flow confidence: {flow_data.get('confidence', 0):.2f}")
```

3. **Disable flow for challenging frames**:
```python
if flow_confidence < 0.5:
    # Fall back to non-flow processing
    use_optical_flow = False
```

### Issue: Very slow inference (>20s/frame)

**Symptoms**: Processing takes much longer than expected

**Solutions**:

1. Check GPU utilization:
```bash
nvidia-smi -l 1  # Monitor GPU usage
```

2. If CPU-based, consider disabling:
```yaml
optical_flow_enabled: false
```

3. Profile computation:
```python
import time
from watermark_removal.optical_flow import OpticalFlowProcessor

processor = OpticalFlowProcessor(resolution="480")
start = time.time()
flow_data = processor.compute_flow(frame1, frame2)
print(f"Flow computation: {time.time() - start:.3f}s")
```

4. If still slow, check for memory swapping:
```bash
vmstat 1 5  # Monitor swap activity
```

## Advanced Tuning: Flow Confidence Threshold

For dynamic watermark tracking, use flow confidence to decide whether to apply optical flow:

```python
from watermark_removal.optical_flow import compute_flow_confidence

# After computing flow
flow_data = processor.compute_flow(frame1, frame2)
confidence = compute_flow_confidence(flow_data)

if confidence > 0.7:
    # High confidence — use flow
    weight = 0.6
else:
    # Low confidence — conservative
    weight = 0.3
```

Recommended thresholds:

- **>0.8** — High quality flow, use weight 0.7-0.9
- **0.5-0.8** — Moderate quality, use weight 0.4-0.6
- **<0.5** — Low quality, use weight 0.2-0.3 or disable

## Configuration Template

Complete optical flow configuration for different scenarios:

### Scenario 1: Animated watermark (heavy motion)
```yaml
optical_flow_enabled: true
optical_flow_resolution: "480"
optical_flow_weight: 0.7
batch_size: 2
output_crf: 20  # Higher quality for visible motion
```

### Scenario 2: Floating logo (light motion)
```yaml
optical_flow_enabled: true
optical_flow_resolution: "480"
optical_flow_weight: 0.4
batch_size: 4
output_crf: 23  # Standard quality
```

### Scenario 3: Static watermark (no motion)
```yaml
optical_flow_enabled: false  # Not needed
# Rest of config unchanged
```

### Scenario 4: CPU-only deployment
```yaml
optical_flow_enabled: false  # Too slow on CPU
# Use Phase 2 features (ensemble detection, checkpoints)
```

## Performance Monitoring

Monitor optical flow overhead in production:

```python
from watermark_removal.metrics import ProcessMetrics

metrics = ProcessMetrics()

# Check temporal consistency
print(f"Temporal consistency: {metrics.temporal_consistency:.2f}")

# Breakdown timing
print(f"Optical flow time: {metrics.optical_flow_time_ms:.1f}ms")
print(f"Total processing: {metrics.processing_time_ms:.1f}ms")

# Overhead percentage
overhead = (metrics.optical_flow_time_ms / metrics.processing_time_ms) * 100
print(f"Optical flow overhead: {overhead:.1f}%")
```

## Checkpoint Resumption with Optical Flow

When resuming from checkpoint, optical flow state is preserved:

```yaml
use_checkpoints: true
checkpoint_dir: ./checkpoints

# These settings restored from checkpoint
optical_flow_enabled: true
optical_flow_resolution: "480"
optical_flow_weight: 0.5
```

Flow data is serialized in checkpoint as FlowData objects containing:
- Computed flow tensors (u, v components)
- Frame pairs (prev_frame_id, curr_frame_id)
- Confidence metrics
- Computation metadata

## Best Practices

1. **Always start with disabled** — Enable only if watermark moves
2. **Test on short clip** — Verify quality before full processing
3. **Monitor performance** — Check if overhead acceptable
4. **Adjust weight conservatively** — Err on side of lower weight
5. **Use GPU when available** — CPU optical flow is slow
6. **Log confidence metrics** — Debug artifacts systematically
7. **Document tuning** — Record weight values that work well

## Further Reading

- Optical flow theory: [RAFT paper](https://arxiv.org/abs/2003.12039)
- Temporal smoothing: See `temporal_smoother.py` implementation
- Flow-based boundary warping: See `optical_flow_processor.py`
