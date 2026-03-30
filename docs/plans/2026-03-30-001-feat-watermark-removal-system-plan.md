---
title: feat: Dynamic Watermark Removal System (Crop-Inpaint-Stitch MVP)
type: feat
status: active
date: 2026-03-30
origin: none
---

# Dynamic Watermark Removal System — Implementation Plan

## Overview

Build a production-grade, frame-by-frame watermark removal pipeline that orchestrates **Python-based preprocessing**, **ComfyUI-based inpainting**, and **Python-based postprocessing** to remove dynamic or static watermarks from high-resolution video using the Crop-Inpaint-Stitch approach.

**Scope:** MVP Phase 1 (static/simple dynamic watermarks) in 2 weeks; Phase 2 (temporal smoothing, quality hardening) in weeks 3-4.

---

## Problem Frame

Video watermarks are common but destructive to content quality and downstream use (re-sharing, editing, archival). Current solutions require either:
- Manual frame-by-frame editing (human-intensive, not scalable)
- Third-party SaaS APIs (expensive, closed-box, latency concerns)
- Fragile open-source tools (inconsistent quality, poor temporal coherence)

This system addresses the problem by:
1. Automating frame-by-frame watermark detection and localization
2. Leveraging state-of-art inpaint models (Flux) for high-quality reconstruction
3. Controlling the entire pipeline locally (no external APIs, full transparency)
4. Supporting both static watermarks (fixed region) and simple dynamic ones (motion-tracked bbox)

**Success is measured by:** watermark completely removed, edge blending seamless, output quality suitable for re-archival or re-sharing. **Phase 1 Note:** Frames may show minor inter-frame flicker (±1-2 px jitter at crop edges); temporal smoothing optimization deferred to Phase 2. This is an acceptable tradeoff for per-frame inpaint simplicity in the MVP.

---

## Requirements Trace

| Req | Description | Phase | Test Signal |
|-----|-------------|-------|------------|
| R1 | Extract all frames from input video at original FPS and resolution | 1 | Frame count matches video duration |
| R2 | Support both JPEG mask (static) and JSON bbox sequences (simple dynamic) | 1 | Both mask formats load and correctly produce per-frame masks |
| R3 | Automatically crop watermark region + context padding for inpaint | 1 | Crop region has correct dimensions, context is included |
| R4 | Resize crops to inpaint-optimal resolution (1024x1024) preserving aspect ratio | 1 | Resized crops are 1024x1024, padding strategy applied correctly |
| R5 | Submit crops to ComfyUI, execute Flux inpaint workflow asynchronously | 1 | All crops inpainted within timeout, results saved locally |
| R6 | Stitch inpainted crops back to original frame with zero offset | 1 | Stitched frame dimensions match original, crop region is seamlessly replaced |
| R7 | Apply feather blending (gradient fade) at crop boundaries | 1 | Edge blend width configurable, produces smooth transition |
| R8 | Re-encode frame sequence to output MP4 at original FPS and bitrate | 1 | Output video plays smoothly, no frame drops, target CRF quality applied |
| R9 | Provide YAML-driven configuration for all parameters | 1 | Config file fully controls pipeline behavior without code changes |
| R10 | Report progress, errors, and final output metrics | 1 | Logs show frame count, inpaint duration, stitch accuracy, output file size |
| R11 | (Phase 2) Apply temporal smoothing to reduce inter-frame flicker | 2 | Adjacent frames blended with alpha parameter |
| R12 | (Phase 2) Support simple YOLO-based bbox tracking for moving watermarks | 2 | Bbox coordinates interpolated/tracked across frame sequence |

---

## Scope Boundaries

### In Scope
- Single watermark region per frame (multiple regions deferred to Phase 3)
- Static mask or simple per-frame bbox list (no automatic detection in Phase 1)
- Flux inpaint model only (SDXL supported as alternate via config, not tested)
- Local ComfyUI instance (no cloud APIs)
- MP4 output only (other codecs deferred)
- Basic feather blending (multi-level blending deferred to Phase 2)

### Out of Scope (Phase 2 or later)
- Automatic watermark detection via ML (use manual mask or YOLO plugin)
- Multi-region watermarks in single frame
- Temporal coherence via optical flow or latent-space blending (Phase 2 uses simple alpha blend)
- Real-time preview UI (CLI + examples only)
- Cloud API support or batch web service
- Subtitle/text-region-specific logic

---

## Context & Research

### Relevant Code and Patterns

**ComfyUI Integration (existing, reusable)**
- Path: `projects/tools/comfyui/client.py` — async HTTP/WebSocket client
- Path: `projects/tools/comfyui/workflow.py` — workflow builder and node connector
- Path: `projects/tools/comfyui/cli.py` — CLI entry point pattern
- **Pattern to follow:** Async context managers, error recovery via timeout + retry logic, JSON-based workflow representation

**Configuration Management (existing, reusable)**
- Path: `projects/tools/claude-session-manager/src/csm/core/config.py` — YAML/JSON load with defaults and validation
- **Pattern to follow:** Dataclass config objects, safe defaults, validation at load time

**Error Handling & Logging (existing)**
- Path: `projects/tools/claude-session-manager/src/csm/core/persistence.py` — atomic file writes, exception hierarchy
- **Pattern to follow:** Custom exception classes, logging.getLogger(__name__), graceful degradation

**Testing & Type Hints (existing)**
- Path: `projects/tools/claude-session-manager/tests/` — pytest + pytest-asyncio, full type annotations
- **Pattern to follow:** Dataclasses with type hints, mocking subprocess/I/O for unit tests, integration tests for end-to-end flow

### Institutional Learnings

- **Non-goal:** Do not over-engineer temporal coherence in Phase 1. Static frame-by-frame inpaint is acceptable baseline; temporal smoothing is Phase 2 refinement, not MVP blocker.
- **Architecture principle:** Keep inpaint logic (ComfyUI) separate from preprocessing/postprocessing (Python). Easier to swap inpaint models, debug, and parallelize.
- **Code organization:** Separate concerns into preprocessing/ inpaint/ postprocessing/ modules. Each module has exactly one responsibility. Tests follow module structure.
- **Configuration:** YAML preferred over JSON for complex nested configs; supports comments; maps cleanly to Python dataclasses.

### External References

- **ComfyUI API:** https://docs.comfy.org/ — REST API for prompt submission, WebSocket for status updates
- **Flux Inpaint Node:** ComfyUI community node; expects `(model, conditioning, neg_conditioning, latent, mask, steps, cfg, sampler, scheduler, seed)`
- **OpenCV (Python-cv2):** Frame I/O (`VideoCapture`, `VideoWriter`), image processing (`resize`, `imwrite`, `imread`), morphology (`findContours`, `boundingRect`)
- **NumPy:** Array operations for mask blending, feathering, and edge detection

---

## Key Technical Decisions

| Decision | Rationale |
|----------|-----------|
| **Separate Python + ComfyUI (not custom nodes)** | Cleaner separation of concerns; easier to test, debug, swap inpaint models; no ComfyUI plugin learning curve |
| **YAML over JSON for config** | Supports comments, cleaner nested structure, standard Python YAML library mature |
| **Per-frame inpaint (no inter-frame coherence in Phase 1)** | Simplifies Phase 1 scope; Phase 2 adds temporal smoothing without rearchitecting |
| **Feather mask blending (not multi-pass)** | Sufficient for Phase 1; visually smooth edges without optical flow complexity |
| **Async/await for inpaint batch execution** | Non-blocking I/O; naturally parallelizes multiple frames; aligns with existing aiohttp patterns |
| **Frame-based offset tracking (CropRegion metadata)** | Enables precise stitch-back without manual coordinate recalculation; test-friendly |
| **Flux as default inpaint model** | State-of-art quality; config-driven so switching to SDXL/others is one line; inpaint specifically designed for mask-guided synthesis |

---

## High-Level Technical Design

> *This illustrates the intended approach and is directional guidance for review, not implementation specification. The implementing agent should treat it as context, not code to reproduce.*

### 4-Layer Pipeline Architecture

```
┌───────────────────────────────────────────────────────────────┐
│ Layer 0: Agent Orchestration (External Entry)                │
│ Input: video.mp4 + mask.json/mask.png                        │
│ Output: output_video.mp4                                     │
└─────────────────────┬─────────────────────────────────────────┘
                      │
┌─────────────────────▼─────────────────────────────────────────┐
│ Layer 1: Preprocessing (Python, Sequential)                   │
│ ┌─────────────────────────────────────────────────────────┐  │
│ │ FrameExtractor: video → framesDir/*.png + metadata.json│  │
│ └────────────┬────────────────────────────────────────────┘  │
│              │                                                │
│ ┌────────────▼────────────────────────────────────────────┐  │
│ │ For each frame:                                         │  │
│ │  ├─ MaskLoader: load mask for this frame               │  │
│ │  ├─ CropHandler: crop + context_padding + resize       │  │
│ │  └─ → cropsDir/frame_XXXXXX.png + CropRegion metadata │  │
│ └──────────────────────────────────────────────────────────┘  │
└─────────────────────┬─────────────────────────────────────────┘
                      │
┌─────────────────────▼─────────────────────────────────────────┐
│ Layer 2: Inpaint Execution (ComfyUI, Async Parallel)          │
│ ┌─────────────────────────────────────────────────────────┐  │
│ │ WorkflowBuilder: build Flux workflow JSON              │  │
│ │ InpaintExecutor: submit batch, monitor async, collect   │  │
│ │ → inpaintedCropsDir/frame_XXXXXX.png (same structure)  │  │
│ └──────────────────────────────────────────────────────────┘  │
└─────────────────────┬─────────────────────────────────────────┘
                      │
┌─────────────────────▼─────────────────────────────────────────┐
│ Layer 3: Postprocessing (Python, Sequential)                  │
│ ┌─────────────────────────────────────────────────────────┐  │
│ │ For each frame:                                         │  │
│ │  ├─ StitchHandler: inpainted_crop → rescale + stitch   │  │
│ │  ├─ EdgeBlending: feather mask at boundaries           │  │
│ │  ├─ [TemporalSmoother: phase 2 only]                   │  │
│ │  └─ → stitchedDir/frame_XXXXXX.png                     │  │
│ └────────────┬────────────────────────────────────────────┘  │
│              │                                                │
│ ┌────────────▼────────────────────────────────────────────┐  │
│ │ VideoEncoder: stitchedDir/*.png → output.mp4 (FFmpeg)  │  │
│ └──────────────────────────────────────────────────────────┘  │
└─────────────────────┬─────────────────────────────────────────┘
                      │
                      ▼
            output_video.mp4 (complete)
```

### Data Flow: Single Frame

```
Original Frame (HxWx3)
         │
         ├─ Mask (either JPEG or JSON bbox)
         │
    ┌────▼────────┐
    │ CropHandler │
    │  extract bbox
    │  + padding
    │  + resize
    └────┬────────┘
         │
    Crop Region Metadata    Resized Crop (1024x1024)
         │                         │
         │                    ┌────▼────────┐
         │                    │ ComfyUI     │
         │                    │ Flux Inpaint│
         │                    └────┬────────┘
         │                         │
         │                  Inpainted Crop
         │                  (1024x1024)
         │                         │
         ├─────────────────────────┤
         │                         │
    ┌────▼─────────────────────────▼──┐
    │ StitchHandler                    │
    │  • Unpad inpainted crop          │
    │  • Rescale to original crop size │
    │  • Feather mask at boundaries    │
    │  • Composite onto original frame │
    └────┬───────────────────────────┘
         │
    Stitched Frame (HxWx3, same size as input)
         │
    ┌────▼──────────────┐
    │ TemporalSmoother  │ (Phase 2 optional)
    │ blend w/ prev     │
    └────┬──────────────┘
         │
    Final Frame (HxWx3)
         │
    Write → framesDir/frame_XXXXXX_out.png
         │
    (Repeat for all frames)
         │
    ┌────▼────────────┐
    │ VideoEncoder    │
    │ FFmpeg → MP4    │
    └────┬────────────┘
         │
    output.mp4
```

### Configuration-Driven Behavior

```yaml
# Example: config/phase1_static.yaml
video_path: ./input/sample.mp4
mask_path: ./input/watermark_mask.png     # Static JPEG or JSON bbox list

# Inpaint parameters (configurable, not hardcoded)
inpaint:
  model_name: flux-dev                   # Easy to swap: flux-pro, sdxl
  prompt: "remove watermark seamlessly"
  steps: 20
  cfg_scale: 7.5

# Preprocessing
context_padding: 64                       # Extra surrounding context
target_inpaint_size: 1024                 # Upscale/downscale to this

# Postprocessing
blend_feather_width: 32                   # Edge feather width
temporal_smooth_alpha: 0.0                # Disabled in Phase 1

# Execution
batch_size: 4                             # Parallel inpaint jobs
inpaint_timeout_sec: 300.0
```

---

## Implementation Units

### **Unit 1: Data Structures & Type Definitions**

**Goal:** Define all system-wide data structures with complete type safety; serve as the foundation for all downstream modules.

**Requirements:** R1, R2, R3, R4, R6, R7, R9, R10

**Dependencies:** None

**Files:**
- Create: `src/watermark_removal/core/types.py`
- Create: `src/watermark_removal/__init__.py` (package init)
- Test: `tests/test_types.py`

**Approach:**
- Define enums: `MaskType` (IMAGE, BBOX, POINTS)
- Define dataclasses: `Frame`, `Mask`, `CropRegion`, `InpaintConfig`, `ProcessConfig`
- Each dataclass includes doc strings and type hints
- `CropRegion` is the central mapping object: tracks original bbox, context region, scale factor for precise stitch-back
- `ProcessConfig` is the system-wide config object; includes all downstream parameters

**Patterns to follow:**
- Use `@dataclass` with defaults (existing practice: `SessionState`, `WorkflowNode`)
- Use Python 3.10+ union syntax: `str | None` instead of `Union[str, None]`
- Use `Enum` for constrained string values (see: existing `MaskType` logic)

**Test scenarios:**
- **Happy path:** Construct all dataclasses with valid inputs; verify all fields are set correctly
- **Edge case:** `ProcessConfig` with minimal required fields; verify defaults are applied
- **Edge case:** `CropRegion` with crop at image boundary (0, 0) and full-size (w, h); verify no overflow
- **Edge case:** `Mask` type detection from enum; verify all enum values are handled

**Verification:**
- All types are importable and instantiable
- Type hints pass mypy strict mode (if mypy is available)
- Dataclass repr shows all fields

---

### **Unit 2: Configuration Management**

**Goal:** Load YAML config file, validate parameters, construct `ProcessConfig` object.

**Requirements:** R9

**Dependencies:** Unit 1 (types.py)

**Files:**
- Create: `src/watermark_removal/core/config_manager.py`
- Test: `tests/test_config_manager.py`

**Approach:**
- `ConfigManager` class: `__init__(config_path)` → `load() -> ProcessConfig`
- Load YAML (use `PyYAML` library, which is standard)
- Validate required fields: `video_path`, `mask_path`, `output_dir`
- Apply defaults for optional fields (use `ProcessConfig` dataclass defaults)
- Raise `FileNotFoundError` if config file missing
- Raise `ValueError` if required fields missing
- Support relative paths (resolve from current working directory)

**Patterns to follow:**
- Atomic config loading: read file → parse → validate → construct object (existing pattern in `claude-session-manager`)
- Safe defaults: if a parameter is missing, use dataclass default rather than raising error
- Logging: log config file path and parameter summary

**Technical design:**
```
ConfigManager.load():
  1. Read YAML file
  2. Extract required fields (video_path, mask_path)
  3. Build InpaintConfig from inpaint subtree
  4. Build ProcessConfig from top-level fields + InpaintConfig
  5. Return ProcessConfig
```

**Test scenarios:**
- **Happy path:** Load valid config YAML; all fields parsed correctly
- **Edge case:** Config file with missing optional field; default is applied
- **Error path:** Config file does not exist; FileNotFoundError raised
- **Error path:** Required field missing; ValueError raised with clear message
- **Edge case:** Relative paths in config; resolved correctly from cwd
- **Integration:** Config from file matches expected ProcessConfig object (all fields match)

**Verification:**
- Valid config loads without error, produces ProcessConfig
- Invalid config raises specific exception (type, message)

---

### **Unit 3: Frame Extraction**

**Goal:** Extract all frames from video file, save as PNG sequence, return metadata (fps, dimensions, frame count).

**Requirements:** R1

**Dependencies:** Unit 1 (types.py), `opencv-python`

**Files:**
- Create: `src/watermark_removal/preprocessing/frame_extractor.py`
- Create: `src/watermark_removal/utils/image_io.py` (read/write wrapper)
- Test: `tests/test_frame_extractor.py`

**Approach:**
- Use `cv2.VideoCapture` to read video file
- Extract metadata: fps, frame dimensions, total frame count
- For each frame: read image, create `Frame` object, write PNG to disk
- Return list of `Frame` objects (or generator for memory efficiency)
- Handle edge cases: empty video, corrupted frames, unusual fps

**Patterns to follow:**
- Wrapper functions in `image_io.py` for I/O (read_image, write_image, get_image_shape)
- Use `Path` for file operations (existing pattern)
- Logging for frame count and video duration

**Technical design:**
```
FrameExtractor.extract_all():
  1. Open video file with cv2.VideoCapture
  2. Extract fps, total_frames, width, height
  3. Create output directory
  4. For frame_id in range(total_frames):
     a. Read frame (BGR)
     b. Create Frame(frame_id, image, timestamp_ms)
     c. Write PNG to disk: output_dir/frame_XXXXXX.png
     d. Append to frames list
  5. Close video
  6. Log: extracted N frames from video
  7. Return frames list
```

**Test scenarios:**
- **Happy path:** Extract all frames from valid video; frame count matches; frames are BGR ndarray
- **Edge case:** Video with non-standard fps (e.g., 23.976); timestamp_ms calculated correctly
- **Edge case:** Video with 1 frame; returns list with 1 Frame
- **Error path:** Video file does not exist; raises FileNotFoundError
- **Error path:** Video is corrupted; cv2.VideoCapture opens but frame read fails; logs error and stops

**Verification:**
- All frames extracted
- Frame count matches expected value from metadata
- PNG files exist on disk
- Frame objects have correct dimensions

---

### **Unit 4: Mask Loading & Synchronization**

**Goal:** Load watermark mask from either JPEG image file or JSON bbox sequence; return per-frame `Mask` objects synchronized with frame IDs.

**Requirements:** R2

**Dependencies:** Unit 1 (types.py), `opencv-python`

**Files:**
- Create: `src/watermark_removal/preprocessing/mask_loader.py`
- Create: `config/examples/sample_masks/` (example mask and bbox JSON)
- Test: `tests/test_mask_loader.py`

**Approach:**
- `MaskLoader` class: detects mask type (JPEG vs JSON) automatically
- **Type: IMAGE** — Load single PNG/JPEG, apply to all frames
- **Type: BBOX** — Load JSON file with frame-indexed bbox list, return per-frame bbox
- For each call to `load_for_frame(frame)`, return the appropriate `Mask` object

**Patterns to follow:**
- Cache loaded images/JSON in memory (avoid repeated I/O)
- Safe type detection: if suffix is `.json`, treat as BBOX; else treat as IMAGE
- Graceful missing masks: return `None` if a frame has no bbox in the JSON

**JSON BBOX Format:**
```json
{
  "0": {"x": 100, "y": 200, "w": 50, "h": 50},
  "1": {"x": 105, "y": 202, "w": 50, "h": 50},
  "5": {"x": 110, "y": 205, "w": 50, "h": 50}
}
```
(Frame IDs can be sparse; omitted frames have no mask)

**Technical design:**
```
MaskLoader.load_for_frame(frame):
  if self.mask_type == IMAGE:
    Load PNG from disk (cached)
    Return Mask(type=IMAGE, data=ndarray, valid_frame_range=(0, inf))
  elif self.mask_type == BBOX:
    Load JSON from disk (cached)
    If frame.frame_id in JSON:
      Return Mask(type=BBOX, data=dict, valid_frame_range=(frame_id, frame_id))
    Else:
      Return None
```

**Test scenarios:**
- **Happy path (IMAGE):** Load PNG mask; mask is ndarray HxW, single channel
- **Happy path (BBOX):** Load JSON bbox list; frame exists in list; return bbox dict
- **Edge case (BBOX):** Frame does not exist in JSON; return None
- **Edge case (BBOX):** Sparse frame IDs (0, 5, 10 present, 1-4 missing); correct mask returned per frame
- **Error path:** Mask file does not exist; raises FileNotFoundError
- **Integration:** Mask loaded for each frame matches expected type and data

**Verification:**
- Mask type correctly detected
- Per-frame mask objects correctly constructed
- Missing frames handled gracefully

---

### **Unit 5: Crop Handler (Complex)**

**Goal:** Extract watermark region + context padding from frame, resize to inpaint size (1024x1024), generate inpaint mask; return both resized image and metadata for later stitch-back.

**Requirements:** R3, R4, R7

**Dependencies:** Unit 1 (types.py), Unit 4 (mask_loader.py), `opencv-python`, `numpy`

**Files:**
- Create: `src/watermark_removal/preprocessing/crop_handler.py`
- Test: `tests/test_crop_handler.py`

**Approach:**
- Input: `Frame`, `Mask`, config params (context_padding, target_inpaint_size)
- Output: (resized_crop_image, CropRegion metadata)
- **Step 1:** From mask, extract bbox (either from mask image contours or JSON bbox)
- **Step 2:** Add context_padding on all sides, clamp to frame boundaries
- **Step 3:** Crop that region from original frame
- **Step 4:** Resize to target_inpaint_size (usually 1024), maintaining aspect ratio; pad to square
- **Step 5:** Generate inpaint mask (0=keep, 255=inpaint) in the resized space
- **Step 6:** Record all transformation metadata in `CropRegion` object

**Patterns to follow:**
- Boundary clamping: `max(0, x - padding)` to `min(frame_w, x + w + padding)`
- Resize strategy: scale down/up to fit largest dimension into 1024, then pad with zeros to 1024x1024
- Feather inpaint mask (optional): apply Gaussian blur to mask edges to avoid hard inpaint boundaries

**Technical design:**
```
CropHandler.crop_with_context(frame, mask):
  1. Extract bbox from mask:
     if mask.type == IMAGE:
       Find contours in binary mask
       Get bounding rect
     elif mask.type == BBOX:
       Use x, y, w, h directly

  2. Compute context region:
     context_x = max(0, x - padding)
     context_y = max(0, y - padding)
     context_w = min(frame_w - context_x, w + 2*padding)
     context_h = min(frame_h - context_y, h + 2*padding)

  3. Crop from frame:
     cropped = frame.image[context_y:context_y+context_h, context_x:context_x+context_w]

  4. Resize to target size (1024):
     scale = 1024 / max(context_w, context_h)
     new_w = int(context_w * scale)
     new_h = int(context_h * scale)
     resized = cv2.resize(cropped, (new_w, new_h))
     padded = cv2.copyMakeBorder(...) to 1024x1024

  5. Generate inpaint mask:
     (map original bbox to resized space, create 0/255 mask)

  6. Return (padded_resized, CropRegion(...))
```

**Test scenarios:**
- **Happy path:** Crop with padding, resize, return correct dimensions (1024x1024)
- **Edge case:** Watermark at frame edge; context padding clamps to frame boundary; no overflow
- **Edge case:** Watermark at corner (0, 0); crop still includes context without going negative
- **Edge case:** Large watermark (e.g., 500x500 in 1080p frame); scaled down correctly to 1024x1024
- **Edge case:** Small watermark (10x10); scaled up correctly, padding added
- **Error path:** No watermark in mask (empty contour); raises ValueError with clear message
- **Integration:** CropRegion metadata matches actual crop dimensions and scale factor

**Verification:**
- Resized crop is exactly 1024x1024
- Scale factor computed correctly
- CropRegion metadata is consistent (can be used to stitch back)
- Inpaint mask is 0/255 binary, same size as crop

---

### **Unit 6: Workflow Builder**

**Goal:** Generate Flux inpaint ComfyUI workflow JSON from crop and mask file paths.

**Requirements:** R4

**Dependencies:** Unit 1 (types.py)

**Files:**
- Create: `src/watermark_removal/inpaint/workflow_builder.py`
- Create: `workflows/flux_inpaint_base.json` (workflow template)
- Test: `tests/test_workflow_builder.py`

**Approach:**
- Template-based JSON generation: start with `flux_inpaint_base.json` template, substitute node inputs
- Template includes node IDs and placeholder filenames/parameters
- `WorkflowBuilder.build(image_path, mask_path, config)` → workflow dict

**Workflow Structure:**
```
Nodes:
  1. CheckpointLoader: load Flux model from ckpt_name
  2. LoadImage: load input crop image
  3. LoadImage: load inpaint mask
  4. CLIPTextEncode: encode prompt
  5. CLIPTextEncode: encode negative prompt
  6. VAEEncode: latent encode image
  7. FluxInpaint: inpaint latent with mask
  8. VAEDecode: latent decode to image
  9. SaveImage: save result to disk
```

**Patterns to follow:**
- Use JSON files as templates (no hardcoding node structure)
- Parameter substitution: only replace filenames and inpaint parameters from `InpaintConfig`
- Return dict suitable for ComfyUI `/prompt` API

**Test scenarios:**
- **Happy path:** Build workflow from config; returns valid dict with all node IDs and inputs
- **Edge case:** Override model name via config; workflow uses correct ckpt_name
- **Edge case:** Custom prompt from config; CLIPTextEncode node has correct text
- **Integration:** Built workflow JSON is valid (can be submitted to ComfyUI)

**Verification:**
- Workflow dict has all required nodes
- Node connections (references to [node_id, slot]) are valid
- SaveImage node has correct filename prefix

---

### **Unit 7: Inpaint Executor (Async)**

**Goal:** Submit crops to ComfyUI for inpaint, manage async execution queue, collect results.

**Requirements:** R5

**Dependencies:** Unit 6 (workflow_builder.py), existing `projects/tools/comfyui/client.py`

**Files:**
- Create: `src/watermark_removal/inpaint/inpaint_executor.py`
- Test: `tests/test_inpaint_executor.py`

**Approach:**
- Reuse existing `ComfyUIClient` from `projects/tools/comfyui/`
- `InpaintExecutor` wraps client, manages batch processing
- Submit workflows asynchronously; collect results in parallel
- Support configurable batch size and timeout
- Error handling: timeout, invalid response, missing output file

**Implementation:**
- `inpaint_single(image_path, mask_path, config, output_path)` — submit one crop, await result
- `inpaint_batch(image_mask_pairs, config)` — submit multiple crops in parallel, return results
- Use `asyncio.gather()` to parallelize batch execution

**Patterns to follow:**
- Async context manager (use existing `ComfyUIClient` pattern)
- Exception handling: raise RuntimeError if inpaint fails
- Logging: log batch progress and individual crop timings

**Test scenarios:**
- **Happy path (mock):** Submit one crop; mock ComfyUIClient returns result; result saved to disk
- **Happy path (batch):** Submit 4 crops; all complete within timeout; results collected
- **Error path:** Inpaint timeout; RuntimeError raised with clear message
- **Error path:** ComfyUI unavailable; connection error raised
- **Integration:** Results match expected output dimensions (same as input crop)

**Verification:**
- All submitted crops are inpainted
- Result images exist on disk
- Batch execution completes in reasonable time (< timeout)

---

### **Unit 8: Stitch Handler (Complex, Critical)**

**Goal:** Rescale inpainted crop back to original crop size, composite onto original frame with feather blending at edges.

**Requirements:** R6, R7

**Dependencies:** Unit 1 (types.py), Unit 5 (crop_handler metadata), `opencv-python`, `numpy`

**Files:**
- Create: `src/watermark_removal/postprocessing/stitch_handler.py`
- Test: `tests/test_stitch_handler.py`

**Approach:**
- Input: original frame, inpainted crop (1024x1024), CropRegion metadata
- Output: stitched frame (same size as original)
- **Step 1:** Remove padding from inpainted crop (reverse padding applied during crop)
- **Step 2:** Rescale inpainted crop back to original crop size using scale factor
- **Step 3:** Create feather mask: 1.0 in center, 0.0 at edges (Gaussian-like decay)
- **Step 4:** Composite inpainted crop onto original frame using feather mask (alpha blend per pixel)

**Patterns to follow:**
- Feather mask creation: distance transform from edge, linear ramp from 0 to 1 over feather_width pixels
- Per-channel blending: `result[c] = original[c] * (1 - feather_mask) + inpainted[c] * feather_mask`

**Technical design:**
```
StitchHandler.stitch_back(original_frame, inpainted_crop, crop_region):
  1. Unpad inpainted crop:
     Remove zero-padding added during resize
     → original_crop_size (context_w, context_h)

  2. Rescale:
     Use crop_region.scale_factor to reverse resize
     → context_w x context_h

  3. Create feather mask:
     Distance from edges → gradient 0 (edge) to 1 (center)
     Over blend_feather_width pixels

  4. Composite:
     For each color channel:
       result[y, x, c] = original[y, x, c] * (1 - feather[y, x]) +
                         inpainted[y, x, c] * feather[y, x]

  5. Return result (dtype=uint8)
```

**Test scenarios:**
- **Happy path:** Stitch crop back to frame; output same size as input; no visible seams
- **Edge case:** Crop at frame boundary (context region clipped); stitch correctly without overflow
- **Edge case:** Very small feather width (1 pixel); sharp but not aliased
- **Edge case:** Large feather width (64 pixels); smooth blending across wide region
- **Integration:** After stitch, frame dimensions match original; all pixel values in [0, 255]

**Verification:**
- Output frame dimensions exactly match input frame
- Feathered region is visually smooth (no hard boundary)
- Pixel values are uint8 (no overflow/underflow)

---

### **Unit 9: Edge Blending (Optional Refinement)**

**Goal:** Smooth edge transitions using multi-level blending or advanced feathering strategies (Phase 1: basic implementation; Phase 2: advanced).

**Requirements:** R7

**Dependencies:** Unit 8 (stitch_handler.py), `opencv-python`, `numpy`

**Files:**
- Create: `src/watermark_removal/postprocessing/edge_blending.py`
- Test: `tests/test_edge_blending.py`

**Approach (Phase 1 - Simple Feather):**
- Feather mask using distance transform (already in Unit 8)
- Optional: apply Gaussian blur to feather mask edges for smoother transition

**Approach (Phase 2 - Advanced):**
- Poisson blending (not Phase 1)
- Color matching at crop boundaries (not Phase 1)

**Patterns to follow:**
- Configurable feather width and blur kernel size
- Return blended region (or feather mask) for composition

**Test scenarios:**
- **Happy path:** Create feather mask with specified width; gradient smooth from 0 to 1
- **Edge case:** Feather width larger than crop size; gracefully clips to region boundary
- **Optional blur:** Apply Gaussian blur to mask edges; transition is even smoother

**Verification:**
- Feather mask is float32 in range [0, 1]
- Gradient is monotonic (no oscillation)

---

### **Unit 10: Video Encoder**

**Goal:** Re-encode frame sequence to MP4 output using FFmpeg with target fps and bitrate.

**Requirements:** R8

**Dependencies:** `ffmpeg-python` (optional wrapper) or subprocess call to FFmpeg binary

**Files:**
- Create: `src/watermark_removal/postprocessing/video_encoder.py`
- Test: `tests/test_video_encoder.py`

**Approach:**
- Use FFmpeg via subprocess (no Python dependency beyond subprocess)
- Command: `ffmpeg -framerate <fps> -pattern_type glob -i "frames/*.png" -c:v h264 -crf <crf> output.mp4`
- Support configurable fps, codec, quality (CRF)

**Patterns to follow:**
- Subprocess error handling: check return code, log stderr if failure
- Input frame glob pattern: assumes frames are `frame_XXXXXX.png` with leading zeros

**Test scenarios:**
- **Happy path (mock subprocess):** Encoder invoked with correct FFmpeg command
- **Edge case:** Specify custom fps; command includes correct -framerate value
- **Error path:** FFmpeg not installed; subprocess raises error with helpful message

**Verification:**
- Output MP4 file exists
- File size reasonable (not empty)
- (Manual: plays without errors)

---

### **Unit 11: Main Pipeline Orchestration**

**Goal:** Coordinate all layers (preprocessing, inpaint, postprocessing) into a single workflow.

**Requirements:** R1-R10

**Dependencies:** All Units 1-10

**Files:**
- Create: `src/watermark_removal/core/pipeline.py`
- Test: `tests/test_pipeline_integration.py`

**Approach:**
- `Pipeline` class: takes `ProcessConfig`, orchestrates execution
- Main method: `async run(config) -> dict` (returns summary: frame count, duration, output path)
- **CropRegion Persistence Strategy:** Store list of `CropRegion` objects in memory (Python list indexed by frame_id). Pass between phases:
  - Phase 1 (preprocessing): populate `crop_regions[frame_id]` as frames are cropped
  - Phase 2 (inpaint): read from list during stitch phase
  - Rationale: In-memory storage is fast for MVP; Phase 2 can serialize to JSON if resumption is needed
- **ComfyUI Pre-flight Checks:** Before inpaint phase starts:
  - Health check: GET `http://{host}:{port}/system` (verify connectivity)
  - Model check: Verify Flux model checkpoint exists in ComfyUI cache
  - VRAM estimate: Warn if estimated VRAM > available (rough heuristic: 8GB for 1024x1024 inpaint)
- **Async/Await Coordination:**
  - Layers 1-2 (preprocessing, inpaint): use async internally for I/O (file operations, ComfyUI calls)
  - Layer 3 (postprocessing): parallelize stitch phase with `asyncio.gather()` for multiple frames (if beneficial)
  - Layer 4 (encoding): subprocess call, wrapped in `asyncio.run_in_executor()` to avoid blocking
  - Entry point (Unit 12): `asyncio.run(Pipeline.run(config))` in `run_pipeline.py`
- Phases:
  1. Extract frames (sequential, build `frames` list)
  2. For each frame: load mask, crop, save crop metadata, store `CropRegion` to list
  3. **Pre-flight ComfyUI checks** (connectivity, model availability, VRAM estimate)
  4. Submit all crops to inpaint executor (async batch with `asyncio.gather()`)
  5. For each inpainted crop: stitch (sequential or parallelized via ProcessPool in Phase 2), blend, save stitched frame
  6. Encode stitched frames to MP4 (async subprocess via `asyncio.run_in_executor()`)
  7. Log summary and return results

**Error handling:**
- Frame extraction fails → stop
- Mask load fails for frame N → skip frame or raise (configurable)
- ComfyUI pre-flight check fails → stop with clear message (e.g., "ComfyUI not reachable at 127.0.0.1:8188"; "Flux model not found in cache")
- Inpaint timeout → retry or fail (configurable)
- Stitch fails → log error, continue or stop (configurable)
- Video encode fails → return error

**Patterns to follow:**
- Logging at each phase
- Progress indicators: "Processed X/Y frames"
- Clean temporary directories if `keep_intermediate=False`
- CropRegion list cleanup after encoding completes (or on error)

**Test scenarios:**
- **Integration test (end-to-end, mock subprocess/ComfyUI):** Full pipeline runs without error; output file exists

**Verification:**
- Output video file created
- Frame count and duration match expectations
- Logs show all phases completed

---

### **Unit 12: CLI Entry Point**

**Goal:** Provide user-facing command-line interface to invoke pipeline.

**Requirements:** R9, R10

**Dependencies:** Unit 2 (config_manager), Unit 11 (pipeline)

**Files:**
- Create: `scripts/run_pipeline.py`
- Create: `config/base.yaml` (default configuration)
- Create: `config/phase1_static.yaml` (example: static watermark)

**Approach:**
- `run_pipeline.py` entry point (synchronous wrapper):
  - Define `async def main()` that loads config, calls `Pipeline.run()`, prints summary
  - In `__main__` block: wrap with `asyncio.run(main())` to execute async pipeline
  - `argparse` to parse command-line args: `--config`, `--video`, `--mask`, `--output`
  - Load config from YAML
  - Override with CLI args if provided
  - Call `await Pipeline.run(config)` inside async main
  - Print summary to stdout
  - Exit code 0 on success, 1 on failure (via exception handling in `asyncio.run()`)

**Async/Await Pattern Example:**
```python
import asyncio
import sys
from src.watermark_removal.core.pipeline import Pipeline
from src.watermark_removal.core.config_manager import ConfigManager

async def main():
    try:
        config = ConfigManager(args.config).load()
        result = await Pipeline.run(config)
        print(f"Pipeline complete: {result}")
        return 0
    except RuntimeError as e:
        print(f"Pipeline failed: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
```

**Patterns to follow:**
- Use `argparse` with descriptive help (existing pattern in `projects/tools/comfyui/cli.py`)
- Positional or named args for flexibility
- Wrap top-level async entry with `asyncio.run()` (not in library code, only CLI scripts)

**Test scenarios:**
- **Happy path:** Run with config file; pipeline completes; output summary printed
- **Error path:** Config file missing; error message printed; exit code 1

**Verification:**
- Help text is clear and complete
- Config file correctly loaded
- Results printed to stdout

---

### **Unit 13: Comprehensive Test Suite & Documentation**

**Goal:** Ensure all units are well-tested; provide clear usage documentation and examples.

**Requirements:** All (indirect)

**Dependencies:** All Units 1-12

**Files:**
- Modify: `tests/test_*.py` (individual unit tests from above)
- Create: `tests/integration_test.py` (end-to-end with mocked ComfyUI)
- Create: `examples/static_watermark_example.py` (example: JPEG mask)
- Create: `examples/dynamic_watermark_example.py` (example: JSON bbox)
- Create: `docs/README.md` (usage guide)
- Create: `docs/mask_format_spec.md` (mask/bbox format specification)

**Approach:**
- Unit tests: each test file covers one module, uses mocks for I/O and ComfyUI calls
- Integration test: mocks only external services (ComfyUI, subprocess), exercises all layers
- Examples: runnable scripts showing common usage patterns
- Documentation: clear walkthrough of pipeline, configuration, and output

**Patterns to follow:**
- pytest + pytest-asyncio (existing project pattern)
- Fixtures for common test data (mock frames, masks)
- Parametrized tests for variations (e.g., different crop positions)

**Test scenarios per unit:** (Covered in earlier units)

**Verification:**
- All tests pass
- Test coverage > 80% for non-trivial code
- Examples run without error (with mock ComfyUI or skip)
- Documentation is clear and complete

---

## System-Wide Impact

### Interaction Graph
- **Entry point:** `scripts/run_pipeline.py` (orchestrated by Agent)
- **Callbacks:** None (sequential pipeline)
- **Middleware:** None (pure transformations)
- **Observers:** Logging (every phase)

### Error Propagation
- **Layer 1 (Preprocessing):** Frame extraction or mask loading fails → pipeline stops, error logged
- **Layer 2 (Inpaint):** ComfyUI unavailable or timeout → raise RuntimeError, offer retry or skip
- **Layer 3 (Postprocessing):** Stitch or encoding fails → log error, decide to stop or continue
- **Failure recovery:** CLI can resume from config (restart processing) but not resume-from-checkpoint in Phase 1

### State Lifecycle Risks
- **Frame sequences:** Large video → many PNG files on disk. Cleanup: delete if `keep_intermediate=False`
- **Crop metadata:** `CropRegion` objects must be preserved throughout pipeline (in memory for now; persistent JSON option in Phase 2)
- **Inpainted crops:** Temporary storage, deleted after stitch
- **Stitched frames:** Temporary storage, deleted after encoding (or kept if debugging)

### Unchanged Invariants
- Original video file is **never modified** (read-only input)
- Original mask file is **never modified** (read-only input)
- Frame extraction order is **deterministic** (frame_id = video frame order)
- Crop-stitch mapping is **1:1** (each crop maps to exactly one frame region; no merging)

### Integration Coverage
- **End-to-end:** Must test full pipeline with mock ComfyUI (Unit 13)
- **Cross-layer:** Frame → Crop → Inpaint → Stitch → Video (all layers must work together)
- **Data consistency:** CropRegion metadata must survive preprocessing → inpaint → postprocessing phases

---

## Risks & Dependencies

| Risk | Mitigation | Phase |
|------|-----------|-------|
| **Inter-frame flicker** (Temporal coherence missing) | Phase 1 uses per-frame inpaint; Phase 2 adds temporal smoothing (alpha blend). Acceptable for MVP. | 1 → 2 |
| **Stitch seams visible** (Edge blending insufficient) | Configurable feather width; Phase 2 adds Poisson blending. Test carefully with various watermark sizes. | 1 → 2 |
| **ComfyUI timeout** (Slow inpaint) | Configurable timeout (default 300s). Fallback: log error, skip frame or retry. | 1 |
| **Out-of-memory** (Large video) | Phase 1: load frames one at a time during stitch phase. Stream processing in Phase 3 (optional). | 1 → 3 |
| **Mask misalignment** (JPEG or JSON incorrect) | Validate mask format in Unit 4. Provide example masks. Document format clearly. | 1 |
| **Path resolution** (Relative paths fail) | Use `Path.cwd()` to resolve relative paths consistently. Unit 2 handles this. | 1 |
| **FFmpeg not installed** | Subprocess error with helpful message. Document FFmpeg dependency in README. | 1 |
| **Quality degradation on complex backgrounds** | Known limitation. Phase 2 exploration: larger context padding, better prompts, ensemble models. | 1 → 2 |

---

## External Dependencies

**System Requirements:**
- Python 3.10+
- FFmpeg (system binary, required for Unit 10)
- ComfyUI server running at `127.0.0.1:8188` (or configurable host/port)

**Python Dependencies (Unit 2 creates `requirements.txt`):**
```
opencv-python>=4.8.0
numpy>=1.24.0
pyyaml>=6.0
aiohttp>=3.8.0  # For async ComfyUI API calls
pytest>=7.0
pytest-asyncio>=0.21.0
```

**Installation Verification (Unit 11 pre-flight checks):**
- FFmpeg: `subprocess.run(['ffmpeg', '-version'])` in Unit 10
- OpenCV: `import cv2` in Unit 3
- ComfyUI: HTTP health check in Unit 11

---

## Deferred to Implementation

- **Exact inpaint prompt tuning:** Start with generic "remove watermark"; iterate based on results
- **Mask preprocessing (morphological ops):** Not needed for clean JPEG masks; add if needed
- **Multi-region watermarks:** Out of Phase 1 scope; add selective-region support in Phase 2-3
- **Automatic watermark detection:** Out of Phase 1 scope; integrate YOLO or heuristic detection in Phase 2
- **Optical flow temporal coherence:** Out of Phase 1 scope; add learned blending in Phase 3
- **CropRegion JSON serialization:** Phase 2 enhancement for resumption capability; Phase 1 uses in-memory list

---

## Documentation & Operational Notes

### Getting Started

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Prepare config:**
   ```bash
   cp config/phase1_static.yaml config/my_project.yaml
   # Edit my_project.yaml with paths and parameters
   ```

3. **Run pipeline:**
   ```bash
   python scripts/run_pipeline.py --config config/my_project.yaml
   ```

4. **Output:**
   - `output_dir/frames_*.png` — stitched frames
   - `output_dir/output.mp4` — final video

### Mask Format Specification

See `docs/mask_format_spec.md` for:
- JPEG mask requirements (dimensions, encoding)
- JSON bbox format and example
- Frame ID mapping and sparse sequences

### Configuration Reference

See `docs/config_reference.md` for:
- All config parameters and defaults
- Tuning guidance for different scenarios (logo, banner, embedded text)

### Known Limitations (Phase 1)

- Single watermark region per frame
- No automatic detection (manual mask required)
- No temporal smoothing (may see flicker)
- Flux inpaint only (SDXL support deferred)

---

## Sources & References

- **ComfyUI API:** https://github.com/comfyanonymous/ComfyUI/wiki
- **Flux Inpaint Paper:** (Link to model card or paper if published)
- **OpenCV:** https://docs.opencv.org/4.5.2/ (frame I/O, image operations)
- **NumPy:** https://numpy.org/doc/stable/ (array operations)
- **FFmpeg:** https://ffmpeg.org/ffmpeg.html
- **Related repo code:** `projects/tools/comfyui/` (client, workflow builder, CLI patterns)

---

## Appendix: Directory Structure Summary

```
watermark-removal-system/
├── README.md
├── pyproject.toml
├── requirements.txt
├── .gitignore
│
├── config/
│   ├── base.yaml
│   ├── phase1_static.yaml
│   └── examples/
│       ├── simple_logo_watermark.yaml
│       └── corner_watermark.yaml
│
├── src/watermark_removal/
│   ├── __init__.py
│   ├── core/
│   │   ├── types.py              # Unit 1
│   │   ├── config_manager.py     # Unit 2
│   │   └── pipeline.py           # Unit 11
│   ├── preprocessing/
│   │   ├── frame_extractor.py    # Unit 3
│   │   ├── mask_loader.py        # Unit 4
│   │   └── crop_handler.py       # Unit 5
│   ├── inpaint/
│   │   ├── workflow_builder.py   # Unit 6
│   │   └── inpaint_executor.py   # Unit 7
│   ├── postprocessing/
│   │   ├── stitch_handler.py     # Unit 8
│   │   ├── edge_blending.py      # Unit 9
│   │   └── video_encoder.py      # Unit 10
│   └── utils/
│       ├── image_io.py
│       ├── logger.py
│       └── path_utils.py
│
├── workflows/
│   ├── flux_inpaint_base.json    # Template
│   └── sdxl_inpaint_base.json    # (Phase 2)
│
├── scripts/
│   ├── run_pipeline.py           # Unit 12
│   ├── test_comfyui_connection.py
│   ├── inspect_frame.py
│   └── generate_sample_mask.py
│
├── examples/
│   ├── static_watermark_example.py
│   ├── dynamic_watermark_example.py
│   └── sample_masks/
│       ├── static_logo_mask.png
│       └── dynamic_bboxes.json
│
├── tests/
│   ├── test_types.py
│   ├── test_config_manager.py
│   ├── test_frame_extractor.py
│   ├── test_mask_loader.py
│   ├── test_crop_handler.py
│   ├── test_workflow_builder.py
│   ├── test_inpaint_executor.py
│   ├── test_stitch_handler.py
│   ├── test_edge_blending.py
│   ├── test_video_encoder.py
│   ├── test_pipeline_integration.py
│   └── conftest.py               # pytest fixtures
│
└── docs/
    ├── README.md
    ├── mask_format_spec.md
    └── config_reference.md
```

---

**Plan Status:** Ready for implementation.

**Recommended Start:** Unit 1 (types.py) → Unit 2 (config_manager.py) → Unit 3-5 (preprocessing pipeline).
