---
title: Checkpoint Resumption Guide
type: project
tags: [project, active]
created: 2026-04-03
updated: 2026-04-03
status: active
maturity: growing
domain: knowledge-management
summary: ""
---

# Checkpoint Resumption Guide

This guide explains how to use checkpoint resumption to handle interruptions in long video processing.

## Quick Start

Enable checkpoints for long videos:

```yaml
save_checkpoints: true
checkpoint_frequency: 100  # Save every 100 frames
resume_from_checkpoint: null  # Auto-detect
```

If processing is interrupted, resume:

```bash
python scripts/run_pipeline.py --config config/your_config.yaml
# Automatically resumes from last checkpoint
```

## Why Use Checkpoints?

**Problem:** Processing a 2-hour video (172,800 frames) with inpainting takes many hours. If interrupted (power failure, crash, timeout), all work is lost.

**Solution:** Periodically save preprocessing results (CropRegions) to disk. If interrupted, resume from the last checkpoint instead of reprocessing everything.

**Benefit:** For 2-hour video interrupted at 50%:
- **Without checkpoint:** Restart from frame 0, lose 1 hour of work
- **With checkpoint:** Resume from frame 50,000 (last saved checkpoint)

## Configuration

### Enable Checkpointing

```yaml
save_checkpoints: true          # Enable checkpoint saving
checkpoint_frequency: 100       # Save every 100 frames
resume_from_checkpoint: null    # Auto-detect checkpoint
```

### Checkpoint Frequency

Choose frequency based on video length and risk tolerance:

| Video Duration | Frames | Recommended Frequency | Checkpoint Interval |
|---|---|---|---|
| 1 minute | 1,800 | 200 | 36-90 seconds |
| 10 minutes | 18,000 | 500 | 3-8 minutes |
| 1 hour | 108,000 | 1000 | 30-60 seconds |
| 2 hours | 216,000 | 2000 | 60-120 seconds |

**Guidance:**
- Frequent (50-100 frames): Safe but slower (more I/O)
- Moderate (100-500 frames): Balanced, recommended
- Sparse (1000+ frames): Fast but risky (lose more work if interrupted)

**Suggested:** Start with `checkpoint_frequency: 500` for 10-minute videos.

## How It Works

### Preprocessing Checkpoints

Checkpoints save preprocessed results from the crop extraction phase:

```
preprocessing: frames → detect/load mask → extract crops → CropRegion data
                                                             ↓
                                                    save checkpoint
```

What's saved (per frame):
- Crop bounding box (x, y, w, h)
- Scale factor
- Context region bounds
- Padding values

**Not saved:**
- Video frames (kept separate)
- Inpaint results (computed during inpaint phase)
- Final stitched frames (computed during stitch phase)

### Checkpoint File Format

Checkpoint stored in `output/checkpoint_crops.json`:

```json
{
  "0": {
    "x": 100,
    "y": 150,
    "w": 200,
    "h": 250,
    "scale_factor": 2.0,
    "context_x": 50,
    "context_y": 100,
    "context_w": 300,
    "context_h": 400,
    "pad_left": 10,
    "pad_top": 20,
    "pad_right": 30,
    "pad_bottom": 40
  },
  "1": { ... },
  ...
}
```

### Resumption Flow

When resuming:

```
1. Check for checkpoint: output/checkpoint_crops.json
2. If checkpoint exists:
   → Load saved CropRegion data
   → Skip preprocessing for saved frames
   → Start inpainting from next unsaved frame
3. If no checkpoint:
   → Start fresh preprocessing
```

## Auto-Detection

With `resume_from_checkpoint: null`, the pipeline automatically detects and resumes:

```bash
# First run (no checkpoint)
python scripts/run_pipeline.py --config config/video.yaml
# ... processing frames 0-500 ...
# (interrupted)

# Resume (auto-detects checkpoint)
python scripts/run_pipeline.py --config config/video.yaml
# ... continues from frame 501 ...
```

## Manual Checkpoint Control

### Skip Checkpoints (Force Full Reprocessing)

```yaml
save_checkpoints: false
```

Use when:
- Testing on small videos (no need for checkpoints)
- Changing configuration (old checkpoint may be invalid)

### Explicitly Clear Checkpoint

Delete the checkpoint file to force fresh preprocessing:

```bash
rm output/checkpoint_crops.json
```

Then run normally:

```bash
python scripts/run_pipeline.py --config config/video.yaml
# Will reprocess from frame 0
```

### Disable Resumption (Keep Checkpoints for Reference)

```yaml
save_checkpoints: true
resume_from_checkpoint: false  # Don't use checkpoint
```

Use when:
- Checkpoints exist but you want to reprocess anyway
- Debugging preprocessing changes

## Real-World Examples

### Example 1: Processing Long Video with Auto-Resume

**Scenario:** Process 1-hour video, interrupted after 20 minutes

```yaml
# config/long_video.yaml
video_path: video_1hour.mp4
output_dir: output/
save_checkpoints: true
checkpoint_frequency: 200
```

**First run:**
```bash
$ python scripts/run_pipeline.py --config config/long_video.yaml
[00:00] Preprocessing frames...
[00:05] Frame 0-200 processed, saving checkpoint
[00:10] Frame 200-400 processed, saving checkpoint
[00:15] Frame 400-600 processed, saving checkpoint
[00:20] Interrupted!
```

Checkpoint saved with frames 0-599.

**Resume:**
```bash
$ python scripts/run_pipeline.py --config config/long_video.yaml
[00:00] Loading checkpoint...
[00:00] Resuming from frame 600
[00:01] Frame 600-800 processed, saving checkpoint
[00:06] Frame 800-1000 processed, saving checkpoint
... continues normally ...
```

Preprocessing skipped, saves ~20 minutes!

### Example 2: Handling Configuration Changes

**Scenario:** Ran with `mask_path: mask_v1.png`, now want to use mask_v2

**Problem:** Saved checkpoint has crop regions from mask_v1, shouldn't be reused.

**Solution:** Clear checkpoint and reprocess:

```bash
rm output/checkpoint_crops.json
python scripts/run_pipeline.py --config config/updated.yaml
# Reprocesses with mask_v2, saves new checkpoint
```

### Example 3: Testing on Subset

**Scenario:** Want to test inpaint quality before full video run

```yaml
# config/test_subset.yaml
video_path: video.mp4
output_dir: output_test/
frame_limit: 50  # Only first 50 frames
save_checkpoints: false  # Not needed for small test
```

Run test:
```bash
python scripts/run_pipeline.py --config config/test_subset.yaml
# Fast test, no checkpoints
```

Then use full config with checkpoints:
```bash
python scripts/run_pipeline.py --config config/full.yaml
# Full processing with checkpoints
```

## Troubleshooting

### Checkpoint Not Being Resumed

**Problem:** Changed config, pipeline reprocesses from frame 0 instead of resuming

**Diagnosis:**
1. Check if checkpoint exists:
   ```bash
   ls output/checkpoint_crops.json
   ```
2. Check if resumption is enabled:
   ```yaml
   resume_from_checkpoint: null  # or true
   ```

**Solution:**
- If `resume_from_checkpoint: false` explicitly, change to `null` or `true`
- If checkpoint doesn't exist, verify checkpoint was saved previously
- Check logs for checkpoint save messages

### Checkpoint Corruption or Version Mismatch

**Problem:** Error loading checkpoint (format changed, corrupted file)

**Symptom:**
```
Error: Failed to load checkpoint from output/checkpoint_crops.json
```

**Solution:**
```bash
# Backup old checkpoint (for inspection)
cp output/checkpoint_crops.json output/checkpoint_crops.json.bak

# Remove and reprocess
rm output/checkpoint_crops.json
python scripts/run_pipeline.py --config config/video.yaml
# Starts fresh, creates new checkpoint
```

### Checkpoint File Too Large

**Problem:** `checkpoint_crops.json` is very large (>100MB for long video)

**Diagnosis:**
- Check file size:
  ```bash
  ls -lh output/checkpoint_crops.json
  ```
- Typical size: ~1KB per frame (100 MB for 100K frames)

**Solution:** Don't reduce frequency (trade-off safety for size)
- Keep checkpoint for safety
- If disk space critical, use less frequent saves:
  ```yaml
  checkpoint_frequency: 1000  # Every 1000 frames
  ```

### Partially Failed Inpainting After Resume

**Problem:** Resumed from checkpoint, but inpainting fails on certain frames

**Cause:** Checkpoint saved, but inpainting crashed mid-batch

**Solution:**
1. Fix the issue (e.g., GPU memory, bad prompt)
2. Remove inpainted results:
   ```bash
   rm -rf output/inpainted/*
   ```
3. Re-run (preprocessing skipped, inpaint re-runs):
   ```bash
   python scripts/run_pipeline.py --config config/video.yaml
   ```

## API Reference

### CropRegionSerializer Class

```python
from src.watermark_removal.persistence import CropRegionSerializer
from pathlib import Path

# Save checkpoint
crops = {0: crop_region_0, 1: crop_region_1, ...}
checkpoint_path = CropRegionSerializer.save_checkpoint(crops, output_dir="output")
# Returns: Path("output/checkpoint_crops.json")

# Load checkpoint
crops = CropRegionSerializer.load_checkpoint(output_dir="output")
# Returns: dict[int, CropRegion] or None if not found

# Serialize to JSON string (for transmission, storage)
json_str = CropRegionSerializer.serialize(crops)

# Deserialize from JSON string
crops = CropRegionSerializer.deserialize(json_str)
```

### CropRegion Dataclass

```python
from src.watermark_removal.core.types import CropRegion

crop = CropRegion(
    x=100, y=150,              # Crop position
    w=200, h=250,              # Crop size
    scale_factor=2.0,          # Upscale factor
    context_x=50, context_y=100,  # Context region position
    context_w=300, context_h=400,  # Context region size
    pad_left=10, pad_top=20,   # Padding values
    pad_right=30, pad_bottom=40
)

# Access properties
x, y = crop.x, crop.y
context_size = crop.context_w * crop.context_h
```

## Performance Impact

### Checkpoint Saving

Saving checkpoint for every 100-500 frames:
- **Time:** <10ms per checkpoint (fast JSON serialization)
- **Disk I/O:** Minimal (sequential JSON write)
- **Total overhead:** <1% (negligible)

### Checkpoint Loading

Loading checkpoint from disk:
- **Time:** ~100ms (parse JSON for typical 100K frames)
- **Disk I/O:** Single file read
- **Memory:** ~100MB for 100K frames

### Net Benefit

For long video interrupted at 50%:
- **Without checkpoint:** Lose all preprocessing work (10-20 minutes)
- **With checkpoint:** Resume immediately, save 10-20 minutes
- **Checkpoint overhead:** <1% (worth the benefit)

## Best Practices

1. **Always enable for videos > 10 minutes**
   ```yaml
   save_checkpoints: true
   checkpoint_frequency: 500  # Moderate frequency
   ```

2. **Use auto-detection**
   ```yaml
   resume_from_checkpoint: null  # Auto-detect existing checkpoint
   ```

3. **Clear checkpoint when changing preprocessing config**
   ```bash
   rm output/checkpoint_crops.json
   ```

4. **Backup checkpoint before major changes**
   ```bash
   cp output/checkpoint_crops.json output/checkpoint_crops.json.bak
   ```

5. **Monitor checkpoint file size**
   ```bash
   ls -lh output/checkpoint_crops.json
   ```

## See Also

- `phase2_migration_guide.md` — Full Phase 2 configuration
- `docs/README.md` — Pipeline overview
- `src/watermark_removal/persistence/` — Implementation details
