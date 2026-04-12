---
title: Configuration Reference
type: project
tags: [project, active]
created: 2026-04-03
updated: 2026-04-03
status: active
maturity: growing
domain: knowledge-management
summary: ""
---

# Configuration Reference

Complete parameter listing for all Phase 1 and Phase 2 configuration options.

## File Format

Configuration files are YAML. Copy `config/base.yaml` and customize:

```bash
cp config/base.yaml config/my_project.yaml
python scripts/run_pipeline.py --config config/my_project.yaml
```

## Parameter Categories

- [Input/Output](#input-output)
- [Inpaint Model](#inpaint-model)
- [Preprocessing](#preprocessing)
- [Postprocessing (Phase 1)](#postprocessing-phase-1)
- [Phase 2: Temporal Smoothing](#phase-2-temporal-smoothing)
- [Phase 2: Poisson Blending](#phase-2-poisson-blending)
- [Phase 2: Watermark Tracking](#phase-2-watermark-tracking)
- [Phase 2: Checkpointing](#phase-2-checkpointing)
- [Execution](#execution)

---

## Input / Output

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `video_path` | str | `./input/video.mp4` | — | Path to input video file |
| `mask_path` | str | `./input/watermark_mask.png` | — | Path to watermark mask (PNG or JSON) |
| `output_dir` | str | `./output` | — | Directory for output video |
| `checkpoint_dir` | str | `./checkpoints` | — | Directory for checkpoint files |

**Notes:**
- Video formats: MP4, MOV, MKV, AVI (FFmpeg-compatible)
- Mask formats:
  - Static: PNG image (watermark outline)
  - Dynamic: JSON with per-frame bboxes (see [Dynamic Watermark Format](#dynamic-watermark-format))
- Paths: Relative to working directory or absolute paths supported

---

## Inpaint Model

All parameters under `inpaint:` section

| Parameter | Type | Default | Options | Description |
|-----------|------|---------|---------|-------------|
| `inpaint.model_name` | str | `flux-dev` | `flux-dev`, `flux-schnell` | Inpainting model to use |
| `inpaint.prompt` | str | `"remove watermark seamlessly"` | — | Positive prompt for inpainting |
| `inpaint.negative_prompt` | str | `"watermark, text, logo, artifact"` | — | Negative prompt (what to avoid) |
| `inpaint.steps` | int | 20 | 1-50 | Diffusion steps (more = slower, higher quality) |
| `inpaint.cfg_scale` | float | 7.5 | 1.0-20.0 | Guidance scale (adherence to prompt) |
| `inpaint.sampler` | str | `dpmpp_2m` | `dpmpp_2m`, `dpmpp_sde`, `euler`, `lcm` | Sampling method |
| `inpaint.scheduler` | str | `karras` | `karras`, `exponential`, `linear` | Step size scheduler |
| `inpaint.seed` | int | -1 | -1 or 0+ | Random seed (-1 = random each frame) |

**Recommendations:**
- For speed: `model_name: flux-schnell`, `steps: 10-15`
- For quality: `model_name: flux-dev`, `steps: 25-35`
- For prompt: Include background details (texture, color) to improve continuity

---

## Preprocessing

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `context_padding` | int | 64 | 0-256 | Padding around watermark bbox |
| `target_inpaint_size` | int | 1024 | 512-2048 | Target inpaint crop size |

**Details:**
- `context_padding`: Pixels added around watermark for inpainting context
  - 32: Tight crop, fast, minimal context
  - 64: Balanced (default)
  - 96+: Extra context for complex backgrounds
- `target_inpaint_size`: Crops resized to this size, then stitched back
  - 512: Fast, reasonable quality
  - 1024: Balanced (default)
  - 1536+: High detail, slow

---

## Postprocessing (Phase 1)

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `blend_feather_width` | int | 32 | 0-128 | Feather mask width for edge blending |

**Notes:**
- Used when `use_poisson_blending: false`
- Larger width = softer edges, slower
- Typical range: 16-64 (32 is good default)

---

## Phase 2: Temporal Smoothing

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `temporal_smooth_alpha` | float | 0.0 | 0.0-1.0 | Blending factor for adjacent frames |
| `use_adaptive_temporal_smoothing` | bool | false | — | Enable motion-aware smoothing |
| `adaptive_motion_threshold` | float | 0.05 | 0.0-1.0 | Motion detection sensitivity |

**Details:**

`temporal_smooth_alpha`:
- 0.0: No smoothing (Phase 1 baseline)
- 0.1-0.3: Conservative (recommended for most videos)
- 0.3-0.5: Moderate
- 0.5+: Aggressive (may cause motion blur)
- Formula: `output = alpha * prev_frame + (1 - alpha) * current_frame`

`use_adaptive_temporal_smoothing`:
- false: Use fixed `temporal_smooth_alpha`
- true: Adjust alpha per-frame based on motion
- Works with motion above `adaptive_motion_threshold`

`adaptive_motion_threshold`:
- Fraction of frame that must change to detect motion
- 0.02: Very sensitive (pan/zoom detected)
- 0.05: Balanced (default)
- 0.1+: Insensitive (large motion only)

**Overhead:** +3-5ms per frame (+10% typical)

---

## Phase 2: Poisson Blending

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `use_poisson_blending` | bool | false | — | Enable Poisson boundary integration |
| `poisson_max_iterations` | int | 100 | 1-500 | Max Jacobi solver iterations |
| `poisson_tolerance` | float | 0.01 | 0.001-0.1 | Convergence threshold |

**Details:**

`use_poisson_blending`:
- false: Use feather blending (Phase 1 mode)
- true: Use Poisson blending (replaces feather)
- Recommended for high-quality output

`poisson_max_iterations`:
- Jacobi iteration count for Laplace solver
- 50: Fast (~48ms), acceptable quality
- 100: Balanced (default, ~95ms)
- 150: Better (~142ms), minimal improvement
- 200+: Premium (~190ms+), marginal gains

`poisson_tolerance`:
- Solver stops when residual < tolerance
- 0.001: Strict (slow)
- 0.01: Balanced (default)
- 0.05+: Lenient (faster)

**Overhead:** +50-150ms per frame (+100-300% typical)

---

## Phase 2: Watermark Tracking

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `use_watermark_tracker` | bool | false | — | Enable YOLO-based tracking |
| `yolo_model_path` | str/null | null | — | Path to YOLO model weights |
| `yolo_confidence_threshold` | float | 0.5 | 0.0-1.0 | Detection confidence threshold |
| `tracker_sparse_interval` | int | 1 | 1-30 | Detect every Nth frame |
| `tracker_smoothing_factor` | float | 0.3 | 0.0-1.0 | BBox trajectory smoothing |

**Details:**

`use_watermark_tracker`:
- false: Disable tracking (static bbox or none)
- true: Enable YOLO detection

`yolo_model_path`:
- null: Disable (graceful degradation)
- Path to YOLO model weights file
- Options:
  - `~/.local/share/ultralytics/yolov8n.pt` (nano, 6MB, fast)
  - `~/.local/share/ultralytics/yolov8s.pt` (small, 22MB, balanced)
  - `~/.local/share/ultralytics/yolov8m.pt` (medium, 49MB, accurate)
- Setup: See [phase2_yolo_setup.md](phase2_yolo_setup.md)

`yolo_confidence_threshold`:
- Only detections above threshold are used
- 0.3: Permissive (many detections, some false positives)
- 0.5: Balanced (default)
- 0.7+: Strict (few detections, high confidence)

`tracker_sparse_interval`:
- Detect every Nth frame, interpolate others
- 1: Every frame (accurate, slow)
- 5: Every 5th frame (5x speedup, ~95% accurate)
- 10+: Detect infrequently (fast, requires smooth motion)

`tracker_smoothing_factor`:
- Smooth detected bboxes toward previous frame
- Formula: `bbox = (1 - factor) * detected_bbox + factor * prev_bbox`
- 0.0: No smoothing (raw detections)
- 0.1-0.3: Light smoothing (recommended)
- 0.5+: Heavy smoothing (may miss motion)

**Overhead:** +5-30ms per frame (+10-100% depending on sparse_interval)

---

## Phase 2: Checkpointing

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `use_checkpoints` | bool | false | — | Enable checkpoint saving |
| `resume_from_checkpoint` | bool | false | — | Resume from existing checkpoint |

**Details:**

`use_checkpoints`:
- false: No checkpointing
- true: Save state after preprocessing, inpaint, postprocessing

`resume_from_checkpoint`:
- false: Start fresh (ignore any existing checkpoints)
- true: Resume from latest checkpoint in `checkpoint_dir`

**Checkpoint file format (JSON):**
```json
{
  "version": "2.0",
  "stage": "postprocessing",
  "frame_indices": [0, 1, 2, ...],
  "crop_regions": [{...}, {...}],
  "inpaint_results": [{...}, {...}],
  "timestamp": "2026-03-31T12:00:00Z"
}
```

**Overhead:** <1ms per checkpoint save

**Use cases:**
- Videos > 5 minutes (fault tolerance)
- Iterative tuning (save between runs)
- Long batch jobs (resume on failure)

---

## Execution

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `batch_size` | int | 4 | 1-16 | Parallel crops per batch |
| `inpaint_timeout_sec` | float | 300.0 | 10-3600 | ComfyUI request timeout |
| `comfyui_host` | str | `127.0.0.1` | — | ComfyUI server hostname |
| `comfyui_port` | int | 8188 | — | ComfyUI server port |
| `keep_intermediate` | bool | false | — | Keep temp PNG files |

**Details:**

`batch_size`:
- Number of crops inpainted simultaneously
- 1: Sequential (slow, minimum memory)
- 4: Parallel (good balance, default)
- 8+: Aggressive (requires more VRAM)

`inpaint_timeout_sec`:
- Max wait time for ComfyUI response (seconds)
- Increase if ComfyUI slow or on limited hardware

`comfyui_host`/`comfyui_port`:
- Server location for inpainting backend
- Default: localhost:8188

`keep_intermediate`:
- false: Delete temp PNG files (default, saves disk)
- true: Keep files (useful for debugging)

---

## Dynamic Watermark Format

For moving watermarks, use JSON mask file with `use_watermark_tracker: true`:

```json
{
  "frames": [
    {
      "frame_id": 0,
      "bbox": [x1, y1, x2, y2],
      "confidence": 0.95
    },
    {
      "frame_id": 1,
      "bbox": [x1+dx, y1+dy, x2+dx, y2+dy],
      "confidence": 0.92
    }
  ]
}
```

**Format:**
- `frame_id`: Zero-based frame index
- `bbox`: [x1, y1, x2, y2] in pixels
  - (x1, y1) = top-left corner
  - (x2, y2) = bottom-right corner
- `confidence`: Optional detection confidence (0.0-1.0)

**Example (10x10 watermark at top-left, moving 5 pixels/frame):**
```json
{
  "frames": [
    { "frame_id": 0, "bbox": [0, 0, 10, 10] },
    { "frame_id": 1, "bbox": [5, 5, 15, 15] },
    { "frame_id": 2, "bbox": [10, 10, 20, 20] }
  ]
}
```

---

## CLI Overrides

All config parameters can be overridden via command-line flags:

```bash
# Override single parameter
python scripts/run_pipeline.py --config config/base.yaml --temporal-smooth-alpha 0.5

# Multiple overrides
python scripts/run_pipeline.py \
  --video input.mp4 \
  --mask mask.png \
  --use-poisson-blending \
  --poisson-max-iterations 150

# Disable feature
python scripts/run_pipeline.py \
  --config config/my_project.yaml \
  --temporal-smooth-alpha 0.0
```

**Flag format:** `--parameter-name value` (hyphens for underscores, boolean flags are valueless)

---

## Validation & Error Handling

### Valid Ranges

All parameters are validated on load:

```yaml
# Valid ✓
temporal_smooth_alpha: 0.3
poisson_max_iterations: 100

# Invalid ✗
temporal_smooth_alpha: 1.5  # Out of range
poisson_max_iterations: -5  # Negative
```

### Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `ValueError: temporal_smooth_alpha out of range [0.0, 1.0]` | Invalid value | Use 0.0-1.0 |
| `FileNotFoundError: YOLO model not found` | Invalid path | Run setup or use null |
| `TypeError: batch_size must be int` | Wrong type | Convert to integer |
| `ValueError: poisson_max_iterations must be positive` | <= 0 | Use 1+ |

---

## Backward Compatibility

All Phase 2 parameters have safe defaults that disable features:
- `temporal_smooth_alpha: 0.0` → No temporal smoothing
- `use_poisson_blending: false` → Use feather blending
- `use_watermark_tracker: false` → No tracking
- `use_checkpoints: false` → No checkpointing

**Phase 1 configs work unchanged.** Enable Phase 2 features incrementally as needed.

---

## Next Steps

1. **Quick start:** Copy `config/base.yaml`, customize, run
2. **Tuning:** See [phase2_tuning_scenarios.md](phase2_tuning_scenarios.md)
3. **Configuration examples:** See `examples/phase2_advanced_watermark.yaml`
4. **Performance:** See [phase2_performance_guide.md](phase2_performance_guide.md)

---

## References

- Base config: `config/base.yaml`
- Example configs: `examples/phase2_advanced_watermark.yaml`
- Complete guide: [phase2_configuration_guide.md](phase2_configuration_guide.md)
- Tuning scenarios: [phase2_tuning_scenarios.md](phase2_tuning_scenarios.md)
- Performance: [phase2_performance_guide.md](phase2_performance_guide.md)
