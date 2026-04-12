# Dynamic Watermark Removal System

A production-grade frame-by-frame watermark removal pipeline: **Crop → Inpaint (ComfyUI Flux) → Stitch**.

## Features

- **Crop-Inpaint-Stitch Architecture:** Intelligently crops watermark regions, applies Flux inpainting, and seamlessly stitches results
- **Async Processing:** Concurrent frame extraction, batch inpainting, efficient encoding
- **Configurable Pipeline:** YAML-driven parameters for all aspects
- **Feather Blending:** Smooth edge transitions at crop boundaries
- **Error Recovery:** Graceful handling of missing frames, ComfyUI timeouts, encoding failures
- **Phase 2 Features:** Optional temporal smoothing, automatic detection (YOLOv5), Poisson blending, quality metrics

## Requirements

- Python 3.10+
- FFmpeg (system binary)
- ComfyUI server running locally (default: `127.0.0.1:8188`)
- Dependencies: `pip install -r requirements.txt` (OpenCV, NumPy, aiohttp, pytest, pytest-asyncio)

## Quick Start

```bash
# Setup
pip install -r requirements.txt

# Create config
cp config/phase1_static.yaml config/my_project.yaml

# Edit config (set video_path, mask_path, output_dir)
nano config/my_project.yaml

# Run pipeline
python scripts/run_pipeline.py --config config/my_project.yaml

# Output: output_dir/output.mp4 ✓
```

**Optional flags:** `--video <path>`, `--mask <path>`, `--output <dir>`, `--verbose`

## Input Formats

**Static Watermark:** PNG/JPEG mask image (1920×1080), white = watermark region, black = preserve

**Dynamic Watermark:** JSON bbox list
```json
[{"frame": 0, "x": 1600, "y": 400, "w": 200, "h": 200}, ...]
```

See [Mask Format Specification](mask_format_spec.md) for details.

## Configuration

Full configuration reference: [CONFIG.md](CONFIG.md)

Quick example (high quality):
```yaml
inpaint:
  steps: 40
  cfg_scale: 10.0
output_crf: 18                   # Higher quality
blend_feather_width: 48          # Smoother blending
batch_size: 2
```

## Phase 2 Features (Optional)

All backward compatible. Enable in config:

```yaml
# Temporal smoothing (reduce inter-frame flicker)
temporal_smooth_enabled: true
temporal_smooth_alpha: 0.3

# Auto-detect watermarks (instead of manual mask)
detection_enabled: true
detection_model: yolov5s

# Poisson blending (seamless transitions)
poisson_enabled: true

# Save checkpoints & quality metrics
save_checkpoints: true
```

## Troubleshooting

Common issues: [TROUBLESHOOT.md](TROUBLESHOOT.md)

Quick help:
- **ComfyUI not reachable:** Check `http://localhost:8188`, verify port in config
- **Visible seams:** Increase `blend_feather_width: 64`, `context_padding: 100`
- **GPU out of memory:** Reduce `batch_size: 1`, `target_inpaint_size: 512`
- **Poor quality:** Try `steps: 30`, `cfg_scale: 10.0`, or model `flux-pro`

Enable debugging: `verbose: true`, `keep_intermediate: true`

## Testing

```bash
pytest tests/ -v                 # Unit tests
pytest tests/ --cov=src          # With coverage
pytest tests/integration_test.py -v  # Integration tests
```

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for system design, data flow, and module reference.

Project structure (overview):
```
src/watermark_removal/
  core/            # Pipeline orchestration, config, types
  preprocessing/   # Frame extraction, mask loading, cropping
  inpaint/         # ComfyUI orchestration, workflow building
  postprocessing/  # Stitching, video encoding
  detection/       # YOLOv5 watermark detection (Phase 2)
  temporal/        # Inter-frame smoothing (Phase 2)
  blending/        # Poisson blending (Phase 2)
  persistence/     # Checkpointing (Phase 2)
  metrics/         # Quality monitoring (Phase 2)

scripts/run_pipeline.py          # CLI entry point
config/                          # Example configs
tests/                           # Test suite
```

## Performance

Typical timings (1920×1080, 30fps, Flux dev, 20 steps):
- Frame extraction: ~100-200ms per frame
- Inpainting: 5-15s per crop batch (GPU)
- Stitching: ~50-100ms per frame
- Encoding: Variable (depends on codec, length)

**Example:** 1-minute video (1800 frames), batch_size=4 → ~7-10 minutes total

## Development

Adding new features:
1. Add config fields to `ProcessConfig` (types.py)
2. Update config loader with defaults (config_manager.py)
3. Implement in appropriate module
4. Add unit tests (tests/test_*.py)
5. Update integration test if cross-layer
6. Document in this README or CONFIG.md

Code style: PEP 8 (black compatible), type hints required, unit tests required.

## Roadmap

| Phase | Status | Features |
|-------|--------|----------|
| **Phase 1** | ✅ | Static/dynamic watermark removal, feather blending, CLI, error recovery |
| **Phase 2** | ✅ | Temporal smoothing, auto-detection (YOLOv5), Poisson blending, metrics, checkpoints |
| **Phase 3** | 🔄 | Optical flow, cloud API, web UI, stream processing |

## License

[License details here]

## Support

- **Issues:** Create issue in repository
- **Questions:** Check troubleshooting section above
- **Documentation:** README.md (overview) → CONFIG.md (settings) → ARCHITECTURE.md (design) → TROUBLESHOOT.md (help)
