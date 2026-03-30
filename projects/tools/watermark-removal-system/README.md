# Watermark Removal System — Phase 1 (MVP)

A production-grade, frame-by-frame watermark removal pipeline using ComfyUI Flux inpainting.

## Features

- ✅ Automated frame extraction from video
- ✅ Support for static (JPEG) and dynamic (JSON bbox) watermark masks
- ✅ Intelligent crop + context padding for inpainting
- ✅ Async batch processing via ComfyUI
- ✅ Seamless edge blending with feather mask
- ✅ MP4 video output with original fps/quality
- ✅ YAML-driven configuration
- ✅ CLI interface

## Architecture

```
Layer 0: Agent (run_pipeline.py)
   ↓
Layer 1: Preprocessing (frame extraction, masking, cropping)
   ↓
Layer 2: Inpaint (ComfyUI Flux async execution)
   ↓
Layer 3: Postprocessing (stitch, blend, encode)
   ↓
Output: output.mp4
```

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Prepare Configuration

```bash
cp config/phase1_static.yaml config/my_project.yaml
# Edit my_project.yaml with your paths and parameters
```

### 3. Run Pipeline

```bash
python scripts/run_pipeline.py --config config/my_project.yaml
```

Or with CLI args:

```bash
python scripts/run_pipeline.py \
  --video input.mp4 \
  --mask mask.png \
  --output ./output
```

## Configuration

See `config/base.yaml` for all available parameters:

- **inpaint**: Model, prompt, steps, guidance scale, etc.
- **preprocessing**: Context padding, target inpaint size
- **postprocessing**: Feather width, temporal smoothing (Phase 2)
- **execution**: Batch size, timeout, ComfyUI host/port

## Requirements

### System
- Python 3.10+
- FFmpeg (for video encoding)
- ComfyUI running at configurable host/port (default: 127.0.0.1:8188)

### Python Dependencies
```
opencv-python>=4.8.0
numpy>=1.24.0
pyyaml>=6.0
aiohttp>=3.8.0
pytest>=7.0
pytest-asyncio>=0.21.0
```

## Testing

Run unit tests:

```bash
pytest tests/ -v
```

Current test status:
- Unit 1 (Types): 19/19 ✓
- Unit 2 (Config): 10/10 ✓
- Unit 3 (FrameExtractor): 1/1 ✓

## Implementation Status

### Phase 1 (MVP) - In Progress

| Unit | Component | Status |
|------|-----------|--------|
| 1 | Data Types | ✓ Complete |
| 2 | Config Manager | ✓ Complete |
| 3 | Frame Extractor | ✓ Core |
| 4 | Mask Loader | ○ Pending |
| 5 | Crop Handler | ○ Pending |
| 6 | Workflow Builder | ○ Framework |
| 7 | Inpaint Executor | ○ Framework |
| 8 | Stitch Handler | ○ Pending |
| 9 | Edge Blending | ○ Pending |
| 10 | Video Encoder | ○ Pending |
| 11 | Pipeline | ○ Framework |
| 12 | CLI | ○ Functional |
| 13 | Tests & Docs | ○ In progress |

### Phase 2 (Optimization) - Deferred

- [ ] Temporal smoothing (reduce inter-frame flicker)
- [ ] YOLO-based watermark tracking (dynamic watermarks)
- [ ] Poisson blending (advanced edge blending)
- [ ] CropRegion JSON serialization (resumable pipeline)

## Known Limitations (Phase 1)

- Single watermark region per frame
- No automatic watermark detection (manual mask required)
- Per-frame inpainting (may show slight flicker between frames)
- Flux inpaint model only (SDXL as fallback not tested)

## Project Structure

```
watermark-removal-system/
├── src/watermark_removal/
│   ├── core/              # Types, config, pipeline
│   ├── preprocessing/     # Frame extraction, masking, cropping
│   ├── inpaint/          # ComfyUI workflow & execution
│   ├── postprocessing/   # Stitch, blend, encode
│   └── utils/            # Image I/O helpers
├── tests/                # Pytest unit tests
├── scripts/              # CLI entry point
├── config/               # YAML config files
├── workflows/            # ComfyUI workflow templates
├── examples/             # Example usage scripts
└── docs/                 # Documentation
```

## Development Notes

### Architecture Principles

1. **Separation of Concerns**: Each module has one responsibility
2. **Type Safety**: Full type hints throughout
3. **Async I/O**: Non-blocking ComfyUI communication
4. **Configuration-Driven**: All parameters in YAML, no hardcoding
5. **Testing-First**: Unit tests for all modules

### Deferred to Implementation

- Exact inpaint prompt tuning (iterate based on results)
- Mask preprocessing (morphological ops) — add if needed
- CropRegion serialization (Phase 2)
- Automatic watermark detection (Phase 2)

## References

- ComfyUI: https://github.com/comfyanonymous/ComfyUI
- OpenCV: https://docs.opencv.org/
- FFmpeg: https://ffmpeg.org/
- Flux Inpaint: https://huggingface.co/black-forest-labs/FLUX.1

## License

Internal — Anthropic/Claude Code project
