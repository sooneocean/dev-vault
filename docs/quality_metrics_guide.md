# Quality Metrics Guide

Phase 2 automatically computes per-frame quality metrics to help assess watermark removal quality. This guide explains each metric and how to interpret results.

## Quick Start

Enable metrics logging:

```yaml
save_checkpoints: true  # Enables quality metrics
```

Metrics are saved to:
- `output/metrics.csv` — Frame-by-frame metrics
- `output/metrics.json` — Detailed metrics + summary statistics

## Metrics Overview

| Metric | Range | Direction | Measures |
|--------|-------|-----------|----------|
| **Boundary Smoothness** | 0.0-1.0 | Lower is better | Gradient variance at inpaint edges |
| **Color Consistency** | 0.0-1.0 | Lower is better | Color histogram distance |
| **Temporal Consistency** | 0.0-1.0 | Higher is better | Frame-to-frame SSIM |
| **Inpaint Quality** | 0.0-1.0 | Higher is better | Region variance (moderate is good) |

## 1. Boundary Smoothness (Lower is Better)

**What it measures:** Smoothness of edges at inpaint region boundaries.

**Computation:**
1. Extract boundary region (±5px around inpaint area)
2. Compute Sobel gradients
3. Calculate normalized gradient variance
4. Normalize to 0-1 scale

**Interpretation:**

| Value | Quality | What it means |
|-------|---------|---|
| < 0.1 | Excellent | Very smooth transition, barely visible seam |
| 0.1-0.3 | Good | Smooth transition, seam minimal |
| 0.3-0.5 | Fair | Some visible seam, but acceptable |
| 0.5-0.7 | Poor | Noticeable seam, needs improvement |
| > 0.7 | Bad | Severe artifacts at boundary |

**How to improve:**
- Increase feather width (more gradual blend)
- Use Poisson blending (enabled by default)
- Increase inpaint quality (more steps, better model)
- Ensure sufficient context padding around region

**Example CSV row:**
```
frame_id,boundary_smoothness,color_consistency,temporal_consistency,inpaint_quality
0,0.25,0.15,None,0.8
1,0.22,0.18,0.92,0.85
2,0.28,0.16,0.91,0.82
```

## 2. Color Consistency (Lower is Better)

**What it measures:** How well inpainted color matches the surrounding original video.

**Computation:**
1. Extract inpaint region from original and stitched frame
2. Compute color histograms (32 bins per channel)
3. Calculate L2 distance between normalized histograms
4. Average across 3 channels, normalize to 0-1

**Interpretation:**

| Value | Quality | What it means |
|-------|---------|---|
| < 0.1 | Excellent | Inpainted color matches surrounding area perfectly |
| 0.1-0.2 | Good | Minor color difference, imperceptible |
| 0.2-0.4 | Fair | Slight color mismatch, slightly visible |
| 0.4-0.6 | Poor | Noticeable color shift |
| > 0.6 | Bad | Severe color mismatch (wrong model/prompt) |

**How to improve:**
- Better inpaint model (e.g., Flux Pro instead of Flux Dev)
- Improve inpaint prompt: "match surrounding color seamlessly"
- Enable color matching:
  ```yaml
  color_match_enabled: true
  ```
- More inpaint context (increase `context_padding`)
- Better mask: ensure watermark region is included

**Example interpretation:**
```
Frame 0: color_consistency=0.15
  → Good: inpainted region blends well color-wise

Frame 5: color_consistency=0.52
  → Poor: noticeable color shift, may need better prompt/model
```

## 3. Temporal Consistency (Higher is Better)

**What it measures:** Frame-to-frame smoothness (consistency between consecutive frames).

**Computation:**
1. Convert frames to grayscale
2. Compute SSIM (Structural Similarity Index) between consecutive frames
3. Normalize SSIM to 0-1 range (SSIM is naturally -1 to 1)
4. First frame has `None` (no previous frame to compare)

**Interpretation:**

| Value | Quality | What it means |
|-------|---------|---|
| > 0.95 | Excellent | Minimal inter-frame flicker, very smooth |
| 0.85-0.95 | Good | Slight frame-to-frame variation, acceptable |
| 0.70-0.85 | Fair | Noticeable flicker, but tolerable |
| 0.50-0.70 | Poor | Visible flicker, distracting |
| < 0.50 | Bad | Severe flicker/discontinuity |

**How to improve:**
- Enable temporal smoothing:
  ```yaml
  temporal_smooth_enabled: true
  temporal_smooth_alpha: 0.3  # Start with 0.3
  ```
- Increase alpha (more aggressive blending):
  ```yaml
  temporal_smooth_alpha: 0.5  # More smoothing
  ```
- Better inpaint quality (consistent results frame-to-frame)
- Use optical flow (Phase 3)

**Example interpretation:**
```
Frame 0: temporal_consistency=None (first frame)
Frame 1: temporal_consistency=0.88 → Good smoothness
Frame 2: temporal_consistency=0.85 → Good smoothness
Frame 3: temporal_consistency=0.72 → Slight flicker
Frame 4: temporal_consistency=0.68 → More flicker (indicates inpaint quality issue)
```

## 4. Inpaint Quality (Higher is Better)

**What it measures:** Visual quality of the inpainted region itself (based on variance).

**Computation:**
1. Convert inpainted crop to grayscale
2. Compute pixel variance
3. Calculate quality heuristic: regions with moderate variance (not too uniform, not too noisy) score higher
4. Target variance: 0.4 (normalized 0-1)

**Interpretation:**

| Value | Quality | What it means |
|-------|---------|---|
| > 0.8 | Excellent | Natural variance, good inpaint quality |
| 0.6-0.8 | Good | Solid inpaint result |
| 0.4-0.6 | Fair | Acceptable inpaint, some uniformity |
| 0.2-0.4 | Poor | Overly uniform or noisy region |
| < 0.2 | Bad | Poor inpaint (completely uniform or too noisy) |

**How to improve:**
- Better inpaint model (Flux Pro, SD3)
- More steps:
  ```yaml
  inpaint:
    steps: 30  # Default is 20
  ```
- Better prompt:
  ```yaml
  inpaint:
    prompt: "seamlessly inpaint region with natural texture"
  ```
- Larger context:
  ```yaml
  context_padding: 150  # More surrounding context
  ```

**Note:** This is a heuristic and may not correlate perfectly with perceived quality. Use alongside visual inspection.

## Interpreting CSV Output

Sample metrics CSV:

```csv
frame_id,boundary_smoothness,color_consistency,temporal_consistency,inpaint_quality
0,0.25,0.15,,0.82
1,0.22,0.18,0.92,0.85
2,0.28,0.16,0.91,0.82
3,0.31,0.22,0.88,0.79
4,0.35,0.28,0.72,0.75
5,0.42,0.35,0.68,0.71
```

**Analysis:**
- **Boundary smoothness:** Increases from 0.25→0.42 (degrading slightly)
  - Early frames very smooth, later frames slightly worse
  - Still acceptable range

- **Color consistency:** Increases from 0.15→0.35 (degrading)
  - Noticeable color drift in later frames
  - May indicate temporal color shift issue

- **Temporal consistency:** Decreases from 0.92→0.68 (degrading)
  - Early frames very smooth, later frames have flicker
  - Suggests inpaint quality degradation or needs more smoothing

- **Inpaint quality:** Decreases from 0.82→0.71 (expected drift)
  - Progressive quality reduction toward end of video
  - Could be addressed with better prompt or more steps

**Action:** Enable temporal smoothing and increase context padding for better results.

## Summary Statistics

`metrics.json` includes summary stats:

```json
{
  "metrics": [...],
  "summary": {
    "frame_count": 100,
    "boundary_smoothness": {
      "mean": 0.28,
      "std": 0.08,
      "min": 0.15,
      "max": 0.52
    },
    "color_consistency": {
      "mean": 0.22,
      "std": 0.12,
      "min": 0.10,
      "max": 0.45
    },
    "temporal_consistency": {
      "mean": 0.85,
      "std": 0.10,
      "min": 0.62,
      "max": 0.95
    },
    "inpaint_quality": {
      "mean": 0.79,
      "std": 0.08,
      "min": 0.65,
      "max": 0.92
    }
  }
}
```

**How to read:**
- **mean:** Average across all frames (primary indicator)
- **std:** Standard deviation (consistency; lower is more uniform)
- **min/max:** Outliers (frames needing attention)

**Example interpretation:**
```
boundary_smoothness: mean=0.28, std=0.08
  → Average quality is good (0.28)
  → Fairly consistent frame-to-frame (std=0.08, only 3% variation)
  → No major outliers (min=0.15 good, max=0.52 acceptable)

temporal_consistency: mean=0.85, std=0.10
  → Good average smoothness (0.85)
  → Some variation (std=0.10, 12% variation)
  → Watch frames with min=0.62 (low smoothness outliers)
```

## Quality Targets

Aim for these ranges for professional quality:

| Metric | Target | Acceptable | Problem |
|--------|--------|-----------|---------|
| Boundary Smoothness | < 0.20 | < 0.35 | > 0.50 |
| Color Consistency | < 0.15 | < 0.30 | > 0.50 |
| Temporal Consistency | > 0.90 | > 0.80 | < 0.70 |
| Inpaint Quality | > 0.80 | > 0.70 | < 0.60 |

## Analyzing Failure Cases

### Case 1: High boundary smoothness but low temporal consistency

```
Frame 0-2: boundary_smoothness=0.20, temporal_consistency=0.90
Frame 3-5: boundary_smoothness=0.28, temporal_consistency=0.68
```

**Problem:** Inpaint quality degrades mid-video
**Solutions:**
- Check inpaint model stability
- Try deterministic seeds for reproducible results
- Reduce batch size (may improve consistency)
- Use temporal smoothing to bridge gaps

### Case 2: All metrics good except color consistency

```
boundary_smoothness=0.22, color_consistency=0.45, temporal=0.88, quality=0.81
```

**Problem:** Color mismatch
**Solutions:**
- Enable color matching:
  ```yaml
  color_match_enabled: true
  ```
- Improve inpaint prompt to emphasize color:
  ```yaml
  prompt: "seamlessly inpaint region, match surrounding color exactly"
  ```
- Increase context padding

### Case 3: All metrics poor

```
All metrics > 0.40 or < 0.60 (temporal)
```

**Problem:** Fundamental quality issue
**Solutions:**
1. Check mask/detection accuracy (is watermark region correct?)
2. Check inpaint quality (increase steps, better model)
3. Check context padding (too small = artifacts)
4. Verify input video quality (very compressed = harder)

## Visualization

Generate simple plots from CSV:

```python
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("output/metrics.csv")

fig, axes = plt.subplots(2, 2, figsize=(12, 8))

axes[0, 0].plot(df["frame_id"], df["boundary_smoothness"])
axes[0, 0].set_title("Boundary Smoothness (lower is better)")
axes[0, 0].axhline(0.35, color="r", linestyle="--", label="Warning")

axes[0, 1].plot(df["frame_id"], df["color_consistency"])
axes[0, 1].set_title("Color Consistency (lower is better)")
axes[0, 1].axhline(0.30, color="r", linestyle="--", label="Warning")

axes[1, 0].plot(df["frame_id"], df["temporal_consistency"])
axes[1, 0].set_title("Temporal Consistency (higher is better)")
axes[1, 0].axhline(0.80, color="g", linestyle="--", label="Good")

axes[1, 1].plot(df["frame_id"], df["inpaint_quality"])
axes[1, 1].set_title("Inpaint Quality (higher is better)")
axes[1, 1].axhline(0.70, color="g", linestyle="--", label="Good")

plt.tight_layout()
plt.savefig("output/metrics_plot.png")
plt.show()
```

## Next Steps

1. Run pipeline with metrics enabled
2. Export metrics to CSV
3. Check summary statistics (mean values)
4. Identify low-quality frames
5. Adjust configuration based on metric trends
6. Re-run and compare results

See `phase2_migration_guide.md` for configuration examples.
