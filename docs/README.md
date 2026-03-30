# Dynamic Watermark Removal System

A production-grade frame-by-frame watermark removal pipeline that uses Python preprocessing, ComfyUI-based Flux inpainting, and Python postprocessing to remove dynamic or static watermarks from high-resolution video.

## Features

- **Crop-Inpaint-Stitch Architecture:** Intelligently crops watermark regions, applies state-of-the-art inpainting, and seamlessly stitches results back
- **Async Processing:** Concurrent frame extraction, batch inpainting, and efficient encoding
- **Configurable Pipeline:** YAML-driven parameters for all aspects (model, quality, timeouts, batch size)
- **Feather Blending:** Smooth edge transitions at crop boundaries using distance transform
- **Error Recovery:** Graceful handling of missing frames, ComfyUI timeouts, and encoding failures
- **Progress Tracking:** Detailed logging of all phases with timing information

## Requirements

### System
- Python 3.10+
- FFmpeg (system binary, required for video encoding)
- ComfyUI server running locally (default: `127.0.0.1:8188`)

### Python Dependencies

```bash
pip install -r requirements.txt
```

Includes:
- `opencv-python>=4.8.0` — Image processing
- `numpy>=1.24.0` — Array operations
- `pyyaml>=6.0` — Configuration parsing
- `aiohttp>=3.8.0` — Async HTTP client for ComfyUI API
- `pytest>=7.0`, `pytest-asyncio>=0.21.0` — Testing

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Verify FFmpeg is installed:
```bash
ffmpeg -version
```

### 2. Prepare Your Input

Create a configuration file:

```bash
cp config/phase1_static.yaml config/my_project.yaml
```

Edit `config/my_project.yaml` with your paths and parameters:

```yaml
video_path: /path/to/input.mp4
mask_path: /path/to/watermark_mask.png  # or mask.json for dynamic

output_dir: ./output

inpaint:
  model_name: flux-dev.safetensors
  prompt: remove watermark seamlessly
  steps: 20
  cfg_scale: 7.5

batch_size: 4
output_fps: 30.0
output_crf: 23  # Quality: 0-51 (lower is better)
```

### 3. Run the Pipeline

```bash
python scripts/run_pipeline.py --config config/my_project.yaml
```

Optional flags:
- `--video <path>` — Override video path from config
- `--mask <path>` — Override mask path from config
- `--output <dir>` — Override output directory
- `--verbose` — Enable DEBUG logging

### 4. Output

The pipeline creates:
```
output_dir/
  frames/                    # Extracted frames (deleted by default)
  crops/                     # Cropped regions (deleted by default)
  inpainted/                 # ComfyUI results (deleted by default)
  stitched/                  # Reconstructed frames (deleted by default)
  output.mp4                 # Final video ✓
```

To keep intermediate files for debugging:
```yaml
keep_intermediate: true
```

## Configuration Guide

### Input Configuration

**`video_path`** (required, string)
- Path to input MP4 video
- Relative or absolute path; relative paths resolve from current working directory

**`mask_path`** (required, string)
- Path to watermark mask or bbox list
- Formats: PNG image (static mask) or JSON file (dynamic bbox list)
- See [Mask Format Specification](#mask-format-specification) below

**`output_dir`** (required, string)
- Directory for all outputs and temporary files
- Created if it doesn't exist

### Inpaint Configuration

**`inpaint`** (section)
- `model_name` (default: `flux-dev.safetensors`)
  - ComfyUI model to use; examples: `flux-dev`, `flux-pro`, `sdxl-1.5-fp16`
  - Model must be installed in ComfyUI
- `prompt` (default: `remove watermark, clean background`)
  - Positive guidance prompt for inpainting
- `negative_prompt` (default: `watermark, text, artifacts, blurry`)
  - Negative guidance (what to avoid)
- `steps` (default: `20`)
  - Number of diffusion steps (higher = better quality, slower)
- `cfg_scale` (default: `7.5`)
  - Classifier-free guidance strength (7.5-15 typical)
- `seed` (default: `42`)
  - Random seed for reproducibility
- `sampler` (default: `euler`)
  - Sampling method (e.g., `euler`, `heun`, `dpm++`)

### Preprocessing Configuration

**`context_padding`** (default: `50`)
- Extra pixels around watermark region to include in crop
- Larger values provide more context for inpainting

**`target_inpaint_size`** (default: `1024`)
- Size to resize cropped regions for inpainting (1024x1024)
- Larger = better quality but slower; Flux works best at 1024

### Postprocessing Configuration

**`blend_feather_width`** (default: `32`)
- Width of feather blend at crop edges
- Larger = smoother transitions but more blending artifacts
- Typical range: 16-64

**`output_fps`** (default: `30.0`)
- Frames per second for output video
- Should match input video FPS for natural playback

**`output_codec`** (default: `h264`)
- Video codec: `h264`, `h265`, or `libvpx` (VP9)
- `h264` is most compatible

**`output_crf`** (default: `23`)
- Quality (Constant Rate Factor)
- 0-51 scale; lower is better quality (but larger file)
- 23 = decent quality; 18-20 = high quality; 28+ = lower quality

### Execution Configuration

**`batch_size`** (default: `4`)
- Number of crops to inpaint in parallel
- Larger = faster but higher GPU memory usage
- Typical range: 2-8 depending on GPU

**`timeout`** (default: `300.0`)
- Timeout in seconds per batch inpaint job
- Increase for slow GPU or large batches

**`comfyui_host`** (default: `127.0.0.1`)
- ComfyUI server hostname/IP

**`comfyui_port`** (default: `8188`)
- ComfyUI server port

**`keep_intermediate`** (default: `false`)
- Keep temporary files (frames, crops, inpainted crops, stitched frames) after encoding
- Useful for debugging; takes significant disk space

**`skip_errors_in_preprocessing`** (default: `false`)
- If true, skip frames that fail mask loading or cropping
- If false, pipeline stops on first error

**`skip_errors_in_postprocessing`** (default: `false`)
- If true, skip frames that fail stitching or encoding
- If false, pipeline stops on first error

**`verbose`** (default: `true`)
- Enable DEBUG logging (show detailed progress)

## Mask Format Specification

See [docs/mask_format_spec.md](mask_format_spec.md) for detailed format specifications.

### Quick Reference

**Static Watermark (JPEG Mask)**
- PNG or JPEG image same dimensions as input video frames
- Non-zero pixels (typically 255) mark the watermark region
- Zero pixels are preserved regions
- Example: 1920x1080 image with white rectangle on black background

**Dynamic Watermark (JSON Bbox List)**
- JSON array of frame-indexed bounding boxes
- Format: `[{"frame": 0, "x": 100, "y": 50, "w": 200, "h": 100}, ...]`
- One entry per frame with watermark
- Frames not listed are skipped (no watermark)

## Examples

### Example 1: Remove Static Watermark from Video

Prepare a static mask (white watermark region on black background):

```bash
# Using your own video and mask
python scripts/run_pipeline.py \
  --config config/my_project.yaml \
  --video ./videos/sample.mp4 \
  --mask ./masks/watermark_static.png \
  --output ./output \
  --verbose
```

### Example 2: Remove Dynamic Watermark with Bounding Box List

Create a JSON bbox file with per-frame coordinates:

```json
[
  {"frame": 0, "x": 1600, "y": 400, "w": 200, "h": 200},
  {"frame": 1, "x": 1610, "y": 405, "w": 200, "h": 200},
  {"frame": 2, "x": 1620, "y": 410, "w": 200, "h": 200}
]
```

Then:

```bash
python scripts/run_pipeline.py \
  --config config/my_project.yaml \
  --mask ./masks/dynamic_bbox.json
```

### Example 3: High-Quality Output

For best visual quality:

```yaml
inpaint:
  model_name: flux-dev.safetensors
  prompt: seamlessly remove watermark while preserving detail
  steps: 40  # More steps = better quality
  cfg_scale: 10.0

output_crf: 18  # Higher quality (18-20 recommended)
blend_feather_width: 48  # Smoother blending
context_padding: 100  # More context for inpainting
batch_size: 2  # Slower but more stable
```

### Example 4: Fast Processing

For rapid iteration/testing:

```yaml
inpaint:
  steps: 10  # Quick preview
  cfg_scale: 7.5

output_crf: 28  # Lower quality, smaller file
batch_size: 8  # Faster batching
```

## Troubleshooting

### Pipeline Says "ComfyUI not reachable"

**Problem:** Pipeline can't connect to ComfyUI server

**Solution:**
1. Verify ComfyUI is running: `http://localhost:8188` in browser
2. Check port in config matches ComfyUI: default is 8188
3. If ComfyUI is on different machine:
   ```yaml
   comfyui_host: 192.168.1.100  # Your ComfyUI IP
   comfyui_port: 8188
   ```

### Output Has Visible Seams at Crop Edges

**Problem:** Watermark was removed but stitched edges are visible

**Solution:** Increase feather blending:
```yaml
blend_feather_width: 64  # Default is 32
context_padding: 100     # More surrounding context
```

Or increase prompt guidance:
```yaml
inpaint:
  cfg_scale: 10.0  # Default is 7.5
  steps: 30        # More steps for detail
```

### FFmpeg Command Failed or Encoding Hangs

**Problem:** Video encoder subprocess fails

**Solution:**
1. Verify FFmpeg is installed: `ffmpeg -version`
2. Try different codec:
   ```yaml
   output_codec: h265  # Try H.265 instead
   ```
3. Check available disk space for output
4. Try smaller batch size (GPU memory issue):
   ```yaml
   batch_size: 2
   ```

### Out of Memory / GPU Memory Issues

**Problem:** "CUDA out of memory" or process crashes

**Solution:**
1. Reduce batch size:
   ```yaml
   batch_size: 1  # Process one crop at a time
   ```
2. Reduce inpaint resolution:
   ```yaml
   target_inpaint_size: 512  # Smaller = faster, less VRAM
   ```
3. Reduce number of steps:
   ```yaml
   inpaint:
     steps: 10  # Fewer diffusion steps
   ```

### Watermark Still Visible or Poor Quality

**Problem:** Inpaint result shows artifacts or watermark traces

**Solution:**
1. Improve the prompt:
   ```yaml
   inpaint:
     prompt: "seamlessly inpaint watermark region, blend naturally"
     negative_prompt: "watermark, text, artifacts, visible seams"
   ```
2. Increase quality settings:
   ```yaml
   inpaint:
     steps: 30  # More steps
     cfg_scale: 10.0  # Stronger guidance
   context_padding: 100  # More surrounding context
   ```
3. Try different model:
   ```yaml
   inpaint:
     model_name: flux-pro  # Better but slower
   ```

## Performance Notes

- **Frame Extraction:** ~100-200ms per frame (CPU)
- **Inpainting:** 5-15 seconds per crop batch (GPU, Flux, 20 steps)
- **Stitching:** ~50-100ms per frame (CPU)
- **Encoding:** Variable (depends on video length and codec)

For a 1-minute 1920x1080 video at 30fps (1800 frames) with batch_size=4:
- Expected inpaint time: ~4-6 minutes (1800 frames / 4 batch size × 8-10s per batch)
- Total pipeline time: ~7-10 minutes

## Advanced Configuration

### ComfyUI Workflow Customization

The pipeline uses a standard Flux inpaint workflow. To use a custom workflow:

1. Build your workflow in ComfyUI UI
2. Export workflow JSON from ComfyUI
3. Place in `workflows/custom.json`
4. Reference in config (future enhancement)

Currently, workflow is generated programmatically (see `workflow_builder.py`).

### Temporal Smoothing (Phase 2 Feature)

Phase 1 processes each frame independently. Phase 2 will support:

```yaml
temporal_smooth_alpha: 0.3  # Blend with previous frame (not yet implemented)
```

This reduces inter-frame flicker from independent inpainting.

## Testing

Run the test suite:

```bash
# Unit tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=src --cov-report=html
```

Run integration tests (with mocked ComfyUI):

```bash
pytest tests/integration_test.py -v
```

Run a specific test:

```bash
pytest tests/test_pipeline_integration.py::TestPipelineBasics::test_pipeline_initialization -v
```

## Development

### Project Structure

```
src/watermark_removal/
  core/
    types.py                          # Data structures
    config_manager.py                 # YAML config loading
    pipeline.py                       # Main orchestration
  preprocessing/
    frame_extractor.py               # Video → frames
    mask_loader.py                   # Load masks / bboxes
    crop_handler.py                  # Extract regions
  inpaint/
    inpaint_executor.py              # ComfyUI orchestration
    workflow_builder.py               # Build workflows
  postprocessing/
    stitch_handler.py                # Composite back
    video_encoder.py                 # Frames → MP4

scripts/
  run_pipeline.py                    # CLI entry point

config/
  base.yaml                          # Template config
  phase1_static.yaml                 # Example (static mask)

tests/
  test_*.py                          # Unit tests
  integration_test.py                # End-to-end

docs/
  README.md                          # This file
  mask_format_spec.md                # Format specs
```

### Adding New Features

1. Add configuration fields to `ProcessConfig` in `types.py`
2. Update config loader in `config_manager.py` with defaults
3. Implement feature in appropriate module (preprocessing, inpaint, postprocessing)
4. Add unit tests in `tests/test_<module>.py`
5. Update integration test if cross-layer
6. Document in this README

## Contributing

All code changes should:
- Follow PEP 8 (black formatter compatible)
- Include type hints
- Have corresponding unit tests
- Update documentation if changing public interfaces

## License

[License details here]

## Contact & Support

For issues, feature requests, or questions:
- Create an issue in the project repository
- Check existing issues for similar problems
- See troubleshooting section above

## Roadmap

### Phase 1 (MVP) — Current
- ✅ Static watermark removal (JPEG mask)
- ✅ Simple dynamic watermarks (JSON bbox)
- ✅ Feather blending at edges
- ✅ ComfyUI Flux inpainting
- ✅ CLI interface with YAML config
- ✅ Basic error recovery

### Phase 2 (Enhancement)
- ⏳ Temporal smoothing (reduce inter-frame flicker)
- ⏳ Advanced blending (Poisson blending, color matching)
- ⏳ Automatic watermark detection (YOLO)
- ⏳ Multi-region watermarks
- ⏳ CropRegion serialization for resumption

### Phase 3 (Future)
- 🔄 Optical flow-based temporal coherence
- 🔄 Cloud API support
- 🔄 Web UI for preview and batch processing
- 🔄 Stream processing for memory-constrained environments
