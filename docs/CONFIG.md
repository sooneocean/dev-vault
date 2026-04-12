# Configuration Reference

Complete configuration guide for the watermark removal pipeline. See [README.md](README.md) for quick start.

## Input Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `video_path` | string | (required) | Input MP4 video path |
| `mask_path` | string | (required) | Watermark mask (PNG) or bboxes (JSON) |
| `output_dir` | string | (required) | Output directory for results |

## Inpaint Configuration

```yaml
inpaint:
  model_name: flux-dev.safetensors    # flux-dev, flux-pro, sdxl-1.5-fp16
  prompt: "remove watermark seamlessly"
  negative_prompt: "watermark, text, artifacts, blurry"
  steps: 20                            # Higher = better quality, slower
  cfg_scale: 7.5                       # 7.5-15 typical range
  seed: 42                             # Reproducibility
  sampler: euler                       # euler, heun, dpm++
```

## Preprocessing

| Parameter | Default | Range | Notes |
|-----------|---------|-------|-------|
| `context_padding` | 50 | 10-200 | Extra pixels around watermark region |
| `target_inpaint_size` | 1024 | 512-2048 | Crop resize for inpainting |
| `skip_errors_in_preprocessing` | false | — | Skip frames with mask errors |

## Postprocessing

| Parameter | Default | Range | Notes |
|-----------|---------|-------|-------|
| `blend_feather_width` | 32 | 16-64 | Edge blending width |
| `output_fps` | 30.0 | 24-60 | Output video FPS |
| `output_codec` | h264 | h264, h265, libvpx | Video codec |
| `output_crf` | 23 | 0-51 | Quality (lower = better) |
| `skip_errors_in_postprocessing` | false | — | Skip frames with stitch/encode errors |

## Execution

| Parameter | Default | Notes |
|-----------|---------|-------|
| `batch_size` | 4 | Parallel crops (2-8 typical) |
| `timeout` | 300.0 | Seconds per batch inpaint job |
| `comfyui_host` | 127.0.0.1 | ComfyUI server IP |
| `comfyui_port` | 8188 | ComfyUI server port |
| `keep_intermediate` | false | Keep temp files for debugging |
| `verbose` | true | DEBUG logging |

## Phase 2 Features (Optional)

All Phase 2 features are backward compatible. Existing configs work unchanged.

### Temporal Smoothing

Reduce inter-frame flicker:
```yaml
temporal_smooth_enabled: true
temporal_smooth_alpha: 0.3              # 0.0-1.0; 0.2-0.3 recommended
```

### Automatic Watermark Detection

Auto-detect watermarks instead of manual mask:
```yaml
detection_enabled: true
detection_model: yolov5s                # yolov5s, yolov5m, yolov5l
detection_confidence: 0.5               # 0.3-0.7 range
mask_path: null                         # Not needed
```

### Advanced Blending

```yaml
poisson_enabled: true                   # Poisson blending (default: on)
color_match_enabled: false              # Optional: histogram matching
```

### Checkpoint Resumption

Resume after interruption:
```yaml
save_checkpoints: true
checkpoint_frequency: 100               # Save every N frames
resume_from_checkpoint: null            # Auto-detect
```

## Quick Reference: Quality Settings

### High Quality
```yaml
inpaint:
  steps: 40
  cfg_scale: 10.0
output_crf: 18
blend_feather_width: 48
context_padding: 100
batch_size: 2
```

### Fast Processing
```yaml
inpaint:
  steps: 10
  cfg_scale: 7.5
output_crf: 28
batch_size: 8
```

### GPU Memory Constrained
```yaml
batch_size: 1
target_inpaint_size: 512
inpaint:
  steps: 15
```
