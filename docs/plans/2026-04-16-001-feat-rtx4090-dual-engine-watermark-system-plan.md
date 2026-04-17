---
title: RTX 4090 Laptop Dual-Engine Watermark Removal System
type: feat
status: active
date: 2026-04-16
origin: Feature description provided via ce:plan command
---

# RTX 4090 Laptop Dual-Engine Watermark Removal System

## Overview

Transform the existing watermark removal pipeline into a **16GB VRAM-constrained production system** optimized for RTX 4090 laptop hardware. Replace ComfyUI external dependency with local **dual-engine inpainting** (LaMa for speed, Flux.1-Fill FP8 for quality) and add **Florence-2 intelligent detection**, unified with a **Gradio Blocks interface** featuring engine switching, manual mask editing, and progress monitoring.

**Key Constraint:** All operations must run on 16GB VRAM without CUDA out-of-memory errors, achieved through strict memory lifecycle management (model offloading, quantization, tiling).

## Problem Frame

Current system:
- Depends on external ComfyUI server (single inpainting engine, not optimizable for laptop)
- Uses YOLO for detection (ensemble voting, but not watermark-specific)
- Lacks adaptive speed/quality trade-off for different user scenarios
- No GPU memory control—would crash or hang on 16GB hardware

RTX 4090 laptop opportunities:
- Sufficient VRAM for dual-model loading (through time-multiplexing + offloading)
- Local inference eliminates network latency, enables offline-first workflow
- FP8 quantization + tiling unlocks Flux.1 quality on 16GB
- LaMa's lightweight architecture enables <5s watermark removal for batch processing

**User goal:** Single, self-contained application on laptop with no external dependencies, offering speed or quality trade-off via UI.

## Requirements Trace

- **R1.** Detect watermark regions using Florence-2 CAPTION_TO_PHRASE_GROUNDING task
- **R2.** Provide two inpainting engines: LaMa (speed) and Flux.1-Fill FP8 (quality)
- **R3.** Support tiling with Gaussian blending for high-resolution images (4K+)
- **R4.** Implement strict VRAM lifecycle: detect → cleanup → inpaint → cleanup → refine
- **R5.** Gradio Blocks interface with engine selection, manual mask refinement, progress updates
- **R6.** Ensure zero CUDA out-of-memory errors on RTX 4090 (16GB)
- **R7.** Support batch processing with configurable memory footprint (trade-off speed for lower VRAM)
- **R8.** Preserve existing temporal smoothing, optical flow, and video encoding infrastructure

## Scope Boundaries

- **In scope:** Local GPU inference, dual inpainting engines, Florence-2 detection, Gradio frontend
- **Out of scope:**
  - Keep existing ComfyUI integration as fallback (not primary path)
  - Video streaming server (Phase 3) remains separate—plan focuses on image processing
  - Label Studio integration unchanged
  - Optical flow and temporal smoothing used only for video post-inpainting (not in scope for R&D here, reuse existing)

## Context & Research

### Relevant Code and Patterns

**Existing modules to extend:**
- `src/watermark_removal/core/pipeline.py` (640 lines) — Add memory-aware config defaults for LaMa/Flux
- `src/watermark_removal/detection/ensemble_detector.py` — Add Florence-2 alongside YOLO
- `src/watermark_removal/inpaint/` — Replace ComfyUI executor with local Flux.1-Fill pipeline
- `src/watermark_removal/postprocessing/edge_blending.py` — Reuse edge blending for both engines
- `tests/conftest.py` — Extend with Florence-2 and Flux mock fixtures

**New modules to create:**
- `src/watermark_removal/lama_inpainter.py` — LaMa tiling engine with Gaussian blending
- `src/watermark_removal/flux_inpainter.py` — Flux.1-Fill FP8 quantized inference with sequential offload
- `src/watermark_removal/memory_manager.py` — VRAM lifecycle orchestrator (offload/load/cleanup)
- `src/watermark_removal/gradio_app.py` — Main Blocks interface with dual-engine mode selector

**Test files to create:**
- `tests/test_lama_tiling.py` — Gaussian blending reconstruction, boundary artifacts
- `tests/test_flux_fp8_quantization.py` — FP8 loading, inference quality, VRAM consumption
- `tests/test_florence2_detection.py` — Watermark phrase grounding, bbox extraction
- `tests/test_memory_manager.py` — Model offload/load sequencing, VRAM validation
- `tests/test_gradio_dual_engine.py` — Engine switching, progress callbacks, mask editing

### Institutional Learnings

From repo exploration:
- **Checkpoint system** (`src/watermark_removal/core/checkpoint.py`) enables resumption across phases — reuse for long inference jobs
- **ProcessConfig with 51 parameters** — extend with `inpaint_engine` (enum: "lama", "flux"), `enable_fp8`, `enable_sequential_offload` flags
- **RAFT lazy-loading pattern** (optical_flow_processor.py) — apply same device-detection + conditional load to Florence-2, LaMa, Flux models

### External References

- **PyTorch 2.x quantization:** TorchAO Float8 for inference (requires CUDA 12.1+, compute capability 8.9+)
- **Diffusers memory optimization:** `enable_sequential_cpu_offload()`, `enable_model_cpu_offload()`, VAE tiling patterns
- **LaMa implementation:** GitHub repo references FFT-based convolutions for resolution-robust inpainting; Gaussian tiling blending is standard practice
- **Gradio queue handling:** `concurrency_limit=1` for single GPU; CUDA hanging issue mitigation (Dec 2025) via explicit synchronization
- **Florence-2 capability:** Proven CAPTION_TO_PHRASE_GROUNDING task for object localization (Microsoft docs, 2026)

## Key Technical Decisions

| Decision | Rationale |
|----------|-----------|
| **Replace ComfyUI with local Flux.1-Fill** | Eliminates network dependency, unlocks 16GB optimization through FP8 quantization + sequential CPU offload. Trade-off: slower (45-60s vs instant), but acceptable for batch watermark removal. |
| **Dual-engine (LaMa + Flux)** | LaMa achieves <5s per crop on 16GB without quantization—optimal for speed-first workflows. Flux FP8 for quality-first—trade processing time for perceptual quality when speed not critical. User chooses mode via Gradio. |
| **FP8 quantization (not native PyTorch)** | Use bitsandbytes (production-ready) + TorchAO for Flux text encoder. Native PyTorch FP8 still experimental (Dec 2025); bitsandbytes proven on inference at scale. |
| **Sequential CPU offload for Flux** | `enable_sequential_cpu_offload()` reduces peak VRAM to ~8GB but increases latency to 5-10min. For UX, recommend `enable_model_cpu_offload()` (12GB peak, 45-60s) as default, with sequential as fallback if OOM. |
| **Gaussian tiling with unfold/fold** | unfold/fold + Gaussian weighting avoids visible seams that simple averaging blending introduces. PyTorch native ops for efficiency. |
| **Memory manager orchestrator** | Explicit state machine (detect → cleanup → inpaint → cleanup → refine) ensures tensor cleanup between model loads. Prevents fragmentation-induced OOM on 16GB. |
| **Gradio Blocks (not UI functions)** | Blocks allows fine-grained concurrency control (`concurrency_limit=1`) and custom event handling. Required for safe CUDA queue management. |
| **Florence-2 detection (optional, default OFF)** | CAPTION_TO_PHRASE_GROUNDING is watermark-specific but adds 8GB VRAM + 2-3s latency. Make optional via Gradio checkbox—users can provide mask manually or enable auto-detection if VRAM allows. |

## High-Level Technical Design

> *This illustrates the intended architecture and is directional guidance for review, not implementation specification.*

### VRAM Budget & Model Scheduling (16GB RTX 4090 Laptop)

```
Timeline:

T0: Load user image → detect watermarks
    ├─ Load Florence-2 (FP16): 8GB
    ├─ Inference: 1-2s
    └─ Cleanup: torch.cuda.empty_cache() → 0.5GB reserved, ~8GB free

T1: Select inpainting engine + generate masks
    ├─ Engine choice: LaMa (6GB) or Flux FP8 (12GB)
    ├─ Load selected engine:
    │  ├─ LaMa: Direct load, ~6GB, ready for full-image inference
    │  └─ Flux: Load with enable_model_cpu_offload(), ~12GB peak
    └─ Tiling + inference (see Unit 2 for tiling logic)

T2: Post-processing & blending
    ├─ Unload inference engine: empty_cache() → 0.5GB reserved
    ├─ Load Poisson blender (lightweight): <1GB
    └─ Stitch + encode → output

Key constraint: Never load Florence-2 + inpainting engine simultaneously.
Policy: Detection → cleanup → inpainting → cleanup → post-processing.
```

### Dual-Engine Inference Routes

```
User Input Image
        ↓
   [Choose Engine]
   /            \
  /              \
LaMa Fast Path    Flux Quality Path
(5s-30s)          (45-60s)
  ├─ No quant      ├─ FP8 quantization
  ├─ Full image    ├─ Sequential CPU offload (optional)
  │  OR tiling     ├─ VAE tiling
  ├─ Gaussian      ├─ Attention slicing
  │  blending      └─ 768×768 or 1024×1024
  └─ Output            (user configurable)
                   └─ Output

Both paths:
  ├─ Input: mask from Florence-2 or user-edited
  ├─ Tiling: Only for 4K+ OR if Flux VRAM OOM
  └─ Blending: Edge feathering + Poisson for seamless composite
```

## Implementation Units

- [ ] **Unit 1: Memory Manager Orchestrator**

**Goal:** Implement explicit VRAM lifecycle state machine—orchestrate model load/unload/cleanup across detection → inpainting → post-processing to guarantee zero OOM on 16GB.

**Requirements:** R4, R6

**Dependencies:** None (foundational)

**Files:**
- Create: `src/watermark_removal/memory_manager.py`
- Modify: `src/watermark_removal/core/pipeline.py` (integrate memory manager)
- Test: `tests/test_memory_manager.py`

**Approach:**
- State machine: `IDLE` → `DETECT_LOADING` → `DETECTING` → `DETECT_CLEANUP` → `INPAINT_LOADING` → `INFERRING` → `INPAINT_CLEANUP` → `POSTPROCESS` → `IDLE`
- Per state, define which models are resident on GPU, which on CPU, which unloaded
- Implement methods:
  - `load_model(model_name, device)` — load to GPU or CPU with device_map auto-fallback
  - `unload_model(model_name)` — delete reference, call `torch.cuda.empty_cache()`, verify freed memory
  - `estimate_peak_vram(engine_name, image_resolution)` — predict VRAM for operation before executing (used for LaMa vs Flux choice if both fit)
  - `validate_vram_headroom(threshold_gb=1.0)` — ensure >threshold GB available before operation
- Use `torch.cuda.memory_allocated()`, `torch.cuda.memory_reserved()` for monitoring
- Logging: Track every state transition with VRAM snapshot (allocated, reserved, available)

**Patterns to follow:**
- Similar to `OpticalFlowProcessor` lazy-load pattern in repo
- Config-driven via `ProcessConfig` (add `enable_vram_monitoring`, `vram_safety_threshold_gb`)

**Test scenarios:**
- **Happy path:** Load Florence-2 → cleanup → load LaMa → infer → cleanup → finish (no OOM)
- **Edge case:** Load Florence-2 + manually trigger garbage collection → verify memory reclamation >=500MB
- **Edge case:** Attempt to load Flux without cleanup from previous model → validation error raised
- **Edge case:** VRAM headroom check fails (<1GB free) → raise `InsufficientVRAMError`
- **Integration:** Real inference pipeline with actual model loads (smoke test, not full inference)

**Verification:**
- All state transitions logged with VRAM snapshots
- No unhandled CUDA OOM exceptions
- Cleanup leaves <100MB fragmented CUDA cache

---

- [ ] **Unit 2: Florence-2 Detection Module**

**Goal:** Integrate Florence-2 CAPTION_TO_PHRASE_GROUNDING for intelligent watermark localization; generate masks with Gaussian smoothing.

**Requirements:** R1, R6

**Dependencies:** Unit 1 (memory manager)

**Files:**
- Create: `src/watermark_removal/florence2_detector.py`
- Modify: `src/watermark_removal/detection/ensemble_detector.py` (add Florence-2 as optional alongside YOLO)
- Test: `tests/test_florence2_detection.py`

**Approach:**
- Load Florence-2-large (FP16, trust_remote_code=True) via memory manager
- Task prompt: `"<CAPTION_TO_PHRASE_GROUNDING> watermark text logo copyright branding overlay symbol"`
- Extract bboxes from model output (normalized coordinates 0-1, convert to image space)
- Generate binary mask: black regions for inpainting, white elsewhere
- Smooth mask: OpenCV `cv2.morphologyEx(cv2.MORPH_CLOSE)` → `cv2.dilate(iterations=1)` → `cv2.GaussianBlur(kernel=5)`
- Confidence filtering: Discard detections below user-configurable threshold (default 0.5)
- Fallback: If user provides mask manually, skip auto-detection (Gradio checkbox)

**Execution note:** Unit tests only—inference quality validation deferred to integration testing with real watermarked images.

**Technical design:**
```python
# Pseudo-code
class Florence2Detector:
    def __init__(self, memory_manager, device="cuda"):
        self.memory_manager = memory_manager
        self.processor = None
        self.model = None

    def detect(self, image_pil, confidence_threshold=0.5):
        # Load model via memory manager
        if not self.model:
            self.memory_manager.load_model("florence2", device="cuda")
            self.model = load_florence2()
            self.processor = load_processor()

        # Inference with no_grad
        with torch.no_grad():
            inputs = self.processor(image_pil, prompt=WATERMARK_PROMPT)
            output = self.model(inputs)

        # Extract bboxes (normalized 0-1)
        bboxes_norm = parse_grounding_output(output)
        bboxes_abs = [(x*W, y*H, x2*W, y2*H) for x,y,x2,y2 in bboxes_norm]

        # Confidence filtering (if available in output)
        filtered = [b for b, conf in zip(bboxes_abs, confidences) if conf > threshold]

        # Generate mask
        mask_binary = generate_mask_from_bboxes(filtered, image_pil.size)
        mask_smooth = smooth_mask_opencv(mask_binary)

        return mask_smooth, filtered

    def cleanup(self):
        self.memory_manager.unload_model("florence2")
```

**Patterns to follow:**
- Lazy load pattern from RAFT processor
- Bbox → mask pipeline from existing ensemble detector

**Test scenarios:**
- **Happy path:** Load Florence-2, detect watermark in test image, return smoothed mask
- **Edge case:** Image with no watermarks → empty bbox list → all-white mask (no inpainting)
- **Edge case:** Multiple overlapping watermarks → merged mask (union of bboxes)
- **Error path:** Florence-2 inference fails → fallback to all-white mask + log warning
- **Error path:** GPU memory insufficient → raise exception (caught by memory manager)

**Verification:**
- Model loads successfully (VRAM <8GB)
- Detected bboxes are reasonable (not entire image, not zero-area)
- Mask is binary (0 or 255, no intermediate values) before smoothing, grayscale (0-255) after
- No GPU memory leaked after cleanup

---

- [ ] **Unit 3: LaMa Inpainter with Gaussian Tiling**

**Goal:** Implement fast inpainting engine using LaMa with tile-based inference for high-resolution support and guaranteed <6GB VRAM footprint.

**Requirements:** R2, R3, R6

**Dependencies:** Unit 1 (memory manager)

**Files:**
- Create: `src/watermark_removal/lama_inpainter.py`
- Modify: `src/watermark_removal/inpaint/inpaint_executor.py` (add LaMa path)
- Test: `tests/test_lama_tiling.py`

**Approach:**
- Load LaMa model via transformers.AutoModelForImageInpainting (pretrained, FP32 on CPU, move to GPU as FP16)
- For images ≤2K: full-image inference (no tiling), fast path
- For images >2K: implement sliding-window tiling:
  - Tile size: 512×512, overlap: 64px (balance receptive field + memory)
  - Extract tiles via `torch.nn.functional.unfold(kernel_size=512, stride=448)`
  - Process each tile through LaMa
  - Reconstruct via `torch.nn.functional.fold()` with Gaussian weight blending
- Gaussian weighting: 2D Gaussian centered on each tile, tapers to 0 at edges → seamless seam blending
- Batch processing: Process up to 4 tiles concurrently (tunable per VRAM feedback)

**Execution note:** Verify reconstruction quality with synthetic test images (e.g., known mask → inpaint → compare against ground truth if available, or visual inspection for artifacts).

**Technical design:**
```python
# Pseudo-code
class LamaInpainter:
    def __init__(self, memory_manager, tile_size=512, overlap=64):
        self.memory_manager = memory_manager
        self.model = None
        self.tile_size = tile_size
        self.overlap = overlap
        self.stride = tile_size - overlap

    def inpaint(self, image_rgb, mask_grayscale):
        # Load model
        self.memory_manager.load_model("lama", device="cuda")
        self.model = load_lama_fp16()

        h, w = image_rgb.shape[-2:]

        if max(h, w) <= 2048:
            # Full-image path (fast)
            with torch.no_grad():
                output = self.model(image_rgb, mask_grayscale)
            return output
        else:
            # Tiling path
            tiles_image = extract_tiles_unfold(image_rgb, self.tile_size, self.stride)
            tiles_mask = extract_tiles_unfold(mask_grayscale, self.tile_size, self.stride)

            inpainted_tiles = []
            for tile_img, tile_mask in zip(tiles_image, tiles_mask):
                with torch.no_grad():
                    inpainted = self.model(tile_img, tile_mask)
                inpainted_tiles.append(inpainted)

            # Reconstruct with Gaussian blending
            gaussian_weights = create_gaussian_2d(self.tile_size)
            output = fold_with_gaussian_blending(
                inpainted_tiles, (h, w), self.tile_size, self.stride, gaussian_weights
            )
            return output

    def cleanup(self):
        self.memory_manager.unload_model("lama")
```

**Patterns to follow:**
- Model loading from existing inpaint_executor
- Tile blending from edge_blending module (adapt Gaussian pattern)

**Test scenarios:**
- **Happy path (full-image):** 512×512 image + mask → inpaint → output same shape, no NaN
- **Happy path (tiling):** 4096×4096 image + mask → tiling with 512×512 tiles, 64px overlap → output 4096×4096
- **Edge case:** Image exactly 2048×2048 (boundary) → full-image path preferred, fast
- **Edge case:** Tile at image boundary (smaller than 512×512) → pad or skip, verify no crashes
- **Artifact check:** Reconstructed image shows no visible seams between tiles (visual inspection, or compare against non-tiled ground truth if available)
- **Edge case:** Mask covers entire image → inpainted output is hallucination (expected, acceptable)
- **Error path:** LaMa inference NaN → raise exception, log error

**Verification:**
- Full-image ≤2KB completes <5s
- Tiling 4K image completes <30s
- Peak VRAM during inference <6GB
- Output image has no NaN values
- No visible seams in tiled reconstruction

---

- [ ] **Unit 4: Flux.1-Fill FP8 Quantized Inpainter with Sequential Offloading**

**Goal:** Implement high-quality inpainting engine using Flux.1-Fill with FP8 quantization and sequential CPU offloading, targeting 8-12GB peak VRAM.

**Requirements:** R2, R3, R6

**Dependencies:** Unit 1 (memory manager)

**Files:**
- Create: `src/watermark_removal/flux_inpainter.py`
- Modify: `src/watermark_removal/inpaint/inpaint_executor.py` (add Flux path)
- Test: `tests/test_flux_fp8_quantization.py`

**Approach:**
- Load Flux.1-Fill-dev (HF repo: black-forest-labs/FLUX.1-Fill-dev) with:
  - `torch_dtype=torch.bfloat16` (required for Flux stability)
  - Quantization config: bitsandbytes 8-bit (text encoder) OR native TorchAO Float8 (if CUDA 12.1+ and compute sm_89+)
- Enable optimizations in order:
  1. `pipeline.enable_sequential_cpu_offload()` — OR —
  2. `pipeline.enable_model_cpu_offload()` (recommended default: faster, ~12GB)
  3. `pipeline.vae.enable_tiling()` — VAE decode in tiles
  4. `pipeline.enable_attention_slicing()` — process attention in 1-head slices
- Input resolution: default 768×768 (user tunable 512×512 to 1024×1024)
- Tiling: For Flux, only enable if user explicitly requests (or if OOM detected) — native tiling not recommended by HF (diffusion tiling complex)
- Guidance scale: default 3.5 (typical for Flux)
- Steps: default 50 (tunable, 30-50 range)

**Execution note:** Integration test with real inference on RTX 4090 to verify VRAM peaks and latency. Quality validation deferred (user feedback or separate benchmarking).

**Technical design:**
```python
# Pseudo-code
class FluxInpainter:
    def __init__(self, memory_manager, enable_sequential_offload=False, vram_mode="model_offload"):
        self.memory_manager = memory_manager
        self.pipeline = None
        self.enable_sequential_offload = enable_sequential_offload
        self.vram_mode = vram_mode  # "model_offload" or "sequential"

    def inpaint(self, image_pil, mask_pil, prompt, height=768, width=768, guidance_scale=3.5, steps=50):
        # Load model via memory manager
        self.memory_manager.load_model("flux", device="cuda")
        self.pipeline = load_flux_fp8_quantized()

        # Apply optimization stack
        if self.vram_mode == "sequential":
            self.pipeline.enable_sequential_cpu_offload()
        else:
            self.pipeline.enable_model_cpu_offload()

        self.pipeline.vae.enable_tiling()
        self.pipeline.enable_attention_slicing()

        # Inference
        with torch.no_grad():
            output = self.pipeline(
                prompt=prompt,
                image=image_pil,
                mask=mask_pil,
                height=height,
                width=width,
                num_inference_steps=steps,
                guidance_scale=guidance_scale
            )

        # Sync GPU before measuring memory
        torch.cuda.synchronize()

        return output.images[0]

    def cleanup(self):
        del self.pipeline
        torch.cuda.empty_cache()
        self.memory_manager.unload_model("flux")
```

**Patterns to follow:**
- Model loading from existing inpaint_executor
- Sequential offload pattern from research docs

**Test scenarios:**
- **Happy path (model offload):** Load Flux → inpaint 768×768 image → output 768×768, completion <60s
- **Happy path (sequential offload):** Same input → completion ~5-10min (extreme slow but memory-minimal)
- **Edge case:** Guidance scale 0 (no conditioning) → should still produce reasonable output
- **Edge case:** Step count 1 (minimal) → fast but very noisy (expected)
- **Error path:** OOM on 12GB peak attempt → suggest sequential offload fallback
- **Integration:** Real RTX 4090 inference with VRAM monitoring (non-unit test, separate validation)

**Verification:**
- Model loads without error
- FP8 quantization applied (verify via model weight dtype inspection)
- Sequential offload stack enabled (verify via pipeline attribute checks)
- Output image is valid PIL.Image, no NaN/inf values
- Peak VRAM during inference ≤12GB (model offload) or ≤8GB (sequential)
- Cleanup removes model from GPU (VRAM freed)

---

- [ ] **Unit 5: Dual-Engine Router & Configuration**

**Goal:** Integrate LaMa and Flux inpainters into pipeline; add inpainting engine selection logic based on user choice or auto-selection heuristic.

**Requirements:** R2, R4, R7

**Dependencies:** Unit 3 (LaMa), Unit 4 (Flux), Unit 1 (memory manager)

**Files:**
- Modify: `src/watermark_removal/core/types.py` (add `InpaintEngine` enum: LAMA, FLUX)
- Modify: `src/watermark_removal/core/pipeline.py` (add engine router logic)
- Modify: `src/watermark_removal/core/config_manager.py` (extend ProcessConfig with engine selection params)
- Test: `tests/test_dual_engine_routing.py`

**Approach:**
- Add to `ProcessConfig`:
  - `inpaint_engine: InpaintEngine` (LAMA or FLUX)
  - `enable_flux_sequential_offload: bool` (default False → use model offload)
  - `flux_guidance_scale: float` (default 3.5)
  - `flux_num_steps: int` (default 50)
  - `lama_tile_size: int` (default 512)
- Heuristic for auto-selection (if user doesn't specify):
  - Image area >2M pixels (2K+) AND user priority "speed" → LaMa
  - Otherwise → Flux (quality default)
  - If estimated Flux VRAM > available VRAM → fallback to LaMa
- Router: Pipeline.run() → after detection → call memory_manager.estimate_peak_vram(engine) → select engine → inpaint → cleanup

**Patterns to follow:**
- Config extensibility from existing ConfigManager
- Pipeline orchestration from core/pipeline.py

**Test scenarios:**
- **Happy path:** Config specifies LaMa → pipeline routes to LaMa inpainter → cleanup
- **Happy path:** Config specifies Flux → routes to Flux with model offload → cleanup
- **Edge case:** Config specifies Flux, but estimate_peak_vram predicts OOM → auto-downgrade to LaMa + log warning
- **Edge case:** Large image + auto-selection heuristic → LaMa chosen for speed
- **Edge case:** Small image + auto-selection → Flux chosen for quality

**Verification:**
- Engine selected matches config or heuristic
- Correct inpainter invoked and cleaned up
- No double-loading of models
- Pipeline completes end-to-end without VRAM errors

---

- [ ] **Unit 6: Gradio Blocks Interface with Dual-Engine Selector**

**Goal:** Create Gradio Blocks UI featuring engine selection, manual mask editing, progress updates, and proper CUDA queue concurrency management.

**Requirements:** R5, R6

**Dependencies:** Unit 5 (dual-engine router)

**Files:**
- Create: `src/watermark_removal/gradio_app.py`
- Test: `tests/test_gradio_dual_engine.py`

**Approach:**
- Use `gr.Blocks()` context (not simple gr.Interface)
- Layout:
  - **Input section:** Image upload
  - **Detection section:**
    - Checkbox: "Auto-detect watermarks (Florence-2)" (default OFF)
    - Slider: Detection confidence threshold (0.3-0.9)
  - **Mask refinement section:**
    - Image viewer for original image
    - Image viewer for detected mask (with paintbrush tool for manual edits)
    - Button: "Update mask"
  - **Inpainting section:**
    - Radio button: "Engine" (LaMa vs Flux)
    - If LaMa: Slider "Tile size" (256-1024), Slider "Overlap" (16-128)
    - If Flux: Slider "Guidance scale" (1-10), Slider "Steps" (10-100), Checkbox "Sequential offload" (default OFF)
  - **Output section:**
    - Progress bar for inference progress
    - Result image viewer
  - **Status section:** Log window for VRAM monitoring, error messages
- Concurrency: `demo.queue(default_concurrency_limit=1)` to prevent simultaneous GPU ops
- Queue-safe design:
  - Use `queue=False` for short (CPU) operations (mask editing)
  - Use explicit `torch.cuda.synchronize()` before returning from GPU functions
- Logging: Every user action logged with timestamp + GPU memory state

**Execution note:** Manual testing on RTX 4090 to verify UI responsiveness and no CUDA hangs.

**Technical design:**
```python
# Pseudo-code
import gradio as gr

class GradioApp:
    def __init__(self, pipeline, memory_manager):
        self.pipeline = pipeline
        self.memory_manager = memory_manager
        self.current_mask = None
        self.current_image = None

    def create_interface(self):
        with gr.Blocks(title="Watermark Removal - RTX 4090") as demo:
            gr.Markdown("## Watermark Removal (RTX 4090 Dual-Engine)")

            with gr.Row():
                with gr.Column():
                    image_input = gr.Image(type="pil", label="Upload image")

                    with gr.Group(label="Watermark Detection"):
                        auto_detect_checkbox = gr.Checkbox(
                            label="Auto-detect watermarks (Florence-2)",
                            value=False
                        )
                        confidence_slider = gr.Slider(
                            minimum=0.3, maximum=0.9, step=0.05, value=0.5,
                            label="Detection confidence"
                        )
                        detect_button = gr.Button("Detect")

                    with gr.Group(label="Mask Refinement"):
                        mask_viewer = gr.Image(type="pil", label="Detected mask (editable)")
                        # Note: gr.ImageEditor exists in newer Gradio for drawing
                        mask_update_button = gr.Button("Update mask")

                with gr.Column():
                    with gr.Group(label="Inpainting Engine"):
                        engine_radio = gr.Radio(
                            choices=["LaMa (Fast)", "Flux.1-Fill (Quality)"],
                            value="LaMa (Fast)",
                            label="Choose engine"
                        )

                        # Dynamic params based on engine selection
                        with gr.Group(label="LaMa Params", visible=True) as lama_params:
                            lama_tile_slider = gr.Slider(256, 1024, 512, step=64, label="Tile size")
                            lama_overlap_slider = gr.Slider(16, 128, 64, step=8, label="Overlap")

                        with gr.Group(label="Flux Params", visible=False) as flux_params:
                            flux_guidance_slider = gr.Slider(1, 10, 3.5, step=0.1, label="Guidance scale")
                            flux_steps_slider = gr.Slider(10, 100, 50, step=5, label="Steps")
                            flux_offload_checkbox = gr.Checkbox(label="Sequential offload (slower, less VRAM)", value=False)

                        # Toggle visibility based on engine selection
                        def update_engine_params(engine):
                            is_lama = "LaMa" in engine
                            return gr.Group(visible=is_lama), gr.Group(visible=(not is_lama))

                        engine_radio.change(
                            update_engine_params,
                            inputs=[engine_radio],
                            outputs=[lama_params, flux_params]
                        )

                        inpaint_button = gr.Button("Inpaint", variant="primary")

                    progress_bar = gr.Progress(label="Inpainting progress")
                    output_image = gr.Image(type="pil", label="Inpainted result")
                    status_log = gr.Textbox(label="Status & VRAM", lines=5, interactive=False)

            # Event handlers
            def detect_watermarks(image, auto_detect, confidence):
                if not auto_detect:
                    self.current_mask = Image.new("RGB", image.size, (255, 255, 255))
                    return self.current_mask, "Manual mask mode (provide mask manually)"

                try:
                    mask, bboxes = self.pipeline.detect_watermarks(image, confidence)
                    self.current_mask = mask
                    self.current_image = image
                    return mask, f"Detected {len(bboxes)} watermarks"
                except Exception as e:
                    return Image.new("RGB", image.size, (255, 255, 255)), f"Error: {e}"

            def inpaint_image(image, engine, **engine_params):
                if self.current_mask is None:
                    return None, "No mask provided"

                try:
                    # Call dual-engine router
                    config = {
                        "inpaint_engine": "LAMA" if "LaMa" in engine else "FLUX",
                        "lama_tile_size": engine_params.get("lama_tile_size", 512),
                        "flux_guidance_scale": engine_params.get("flux_guidance_scale", 3.5),
                        "flux_num_steps": engine_params.get("flux_steps", 50),
                        "enable_flux_sequential_offload": engine_params.get("flux_offload", False)
                    }

                    result = self.pipeline.inpaint_with_config(image, self.current_mask, config)
                    torch.cuda.synchronize()  # Critical for CUDA queue safety

                    return result, "Inpainting complete"
                except Exception as e:
                    return None, f"Inpaint error: {e}"

            detect_button.click(
                detect_watermarks,
                inputs=[image_input, auto_detect_checkbox, confidence_slider],
                outputs=[mask_viewer, status_log],
                queue=False  # CPU operation, no CUDA queue needed
            )

            inpaint_button.click(
                inpaint_image,
                inputs=[
                    image_input, engine_radio,
                    lama_tile_slider, lama_overlap_slider,
                    flux_guidance_slider, flux_steps_slider, flux_offload_checkbox
                ],
                outputs=[output_image, status_log],
                concurrency_limit=1  # Serialize GPU ops
            )

        return demo
```

**Patterns to follow:**
- Gradio Blocks patterns from official docs
- Concurrency management from research findings

**Test scenarios:**
- **Happy path:** Upload image → detect → inpaint with LaMa → output
- **Happy path:** Upload image → manual mask edit → inpaint with Flux → output
- **Edge case:** Disable auto-detect → all-white mask (no inpainting)
- **UI behavior:** Select LaMa → LaMa params visible, Flux params hidden
- **UI behavior:** Select Flux → Flux params visible, LaMa params hidden
- **Error path:** Inpaint before mask → error message displayed in status
- **Concurrency:** Simultaneous requests queued, not parallel (concurrency_limit=1)

**Verification:**
- UI renders without errors
- Engine switching updates UI dynamically
- Inpainting produces valid output
- No CUDA hanging (explicit synchronization in place)
- Status log updates with progress + VRAM info
- Manual mask editing works (if gr.ImageEditor integrated)

---

- [ ] **Unit 7: Configuration & Requirements Updates**

**Goal:** Extend requirements.txt with new dependencies; create production config template for RTX 4090 defaults.

**Requirements:** R4, R6, R7

**Dependencies:** All previous units

**Files:**
- Modify: `requirements.txt` (add Florence-2, Flux, bitsandbytes, torchao, gradio, etc.)
- Create: `config/rtx4090_laptop_defaults.yaml` (optimized defaults for 16GB VRAM)
- Modify: `src/watermark_removal/core/config_manager.py` (add config loading for new engine params)

**Approach:**
- Add dependencies:
  ```
  torch>=2.1.0,<3.0  # PyTorch 2.x for CUDA 12.1 support
  torchvision>=0.16.0
  transformers>=4.45.0  # Florence-2, updated API
  diffusers>=0.30.0  # Flux.1-Fill
  bitsandbytes>=0.44.0  # 8-bit quantization
  torchao>=0.3.0  # TorchAO Float8 (optional, for native FP8)
  gradio>=4.50.0  # Gradio Blocks with queue support
  pillow>=10.0.0  # Image manipulation
  opencv-python>=4.10.0  # Morphological ops
  ```
- Config template: Sensible defaults for RTX 4090 16GB laptop
  ```yaml
  inpaint:
    engine: "lama"  # Start with fast mode by default
    lama:
      tile_size: 512
      overlap: 64
    flux:
      guidance_scale: 3.5
      num_steps: 50
      enable_sequential_offload: false  # Use model offload (faster)
      enable_fp8_quantization: true

  detection:
    enabled: false  # Florence-2 off by default (optional)
    model: "florence2"
    confidence_threshold: 0.5

  memory:
    enable_monitoring: true
    vram_safety_threshold_gb: 1.0  # Warn if <1GB free

  gradio:
    concurrency_limit: 1
    max_queue_size: 50
  ```

**Test scenarios:**
- **Happy path:** Load config template → values match expected defaults
- **Validation:** Required dependencies installed with compatible versions
- **Edge case:** Config missing optional field → sensible default applied

---

- [ ] **Unit 8: Integration Testing & VRAM Validation**

**Goal:** End-to-end integration tests covering full pipeline: detect → inpaint → output; validate VRAM usage on RTX 4090.

**Requirements:** R6, R8

**Dependencies:** All previous units

**Files:**
- Create: `tests/test_integration_dual_engine_rtx4090.py`
- Modify: `tests/conftest.py` (add RTX 4090-specific fixtures, mock Flux/Florence-2 for fast testing)

**Approach:**
- Real inference tests (optional skip if no GPU available):
  - Test image: 1024×1024 watermarked (synthetic or real)
  - Run full pipeline: detect (Florence-2) → cleanup → inpaint (LaMa) → cleanup → output
  - Verify VRAM never exceeds 16GB
  - Benchmark latency per engine
- Mock tests (always run):
  - Mock Florence-2 output → verify mask generation
  - Mock LaMa/Flux inference → verify routing logic
  - Mock VRAM monitoring → verify state machine
- Regression tests:
  - Verify temporal smoothing still works (reuse existing tests)
  - Verify video encoding pipeline unchanged
  - Verify checkpoint system compatible

**Test scenarios:**
- **Integration:** Full pipeline detect → inpaint (LaMa) → output, VRAM ≤16GB
- **Integration:** Full pipeline detect → inpaint (Flux model offload) → output, VRAM ≤16GB
- **Latency:** LaMa <5s per 512×512 crop
- **Latency:** Flux 45-60s per 768×768 image (model offload)
- **Regression:** Optical flow + temporal smoothing still work (Phase 2 features)

**Verification:**
- All integration tests pass
- VRAM monitoring log shows no OOM events
- Latency benchmarks meet expectations
- No regression in existing features

---

## System-Wide Impact

### Interaction Graph
- **Gradio frontend** ↔ **Memory manager** ↔ **Florence-2, LaMa, Flux models**
- **Pipeline orchestrator** calls dual-engine router → inpainting → post-processing (edge blending, stitch)
- **Existing modules:** Temporal smoothing, optical flow, video encoding remain unchanged (called after inpainting)

### Error Propagation
- **OOM errors:** Caught by memory manager, logged with VRAM snapshot, optionally auto-fallback (Flux → LaMa)
- **Inference errors:** Model-specific exceptions caught in unit try-except blocks, user notified via Gradio status
- **Mask editing errors:** Input validation (must be binary or grayscale), user re-prompted

### State Lifecycle Risks
- **Model caching:** LaMa/Flux loaded once, cached for session. Risk: stale weights if long session. Mitigation: Gradio session timeout, explicit unload on exit.
- **VRAM fragmentation:** Peak fragmentation after multiple inpaint cycles. Mitigation: explicit `empty_cache()` + garbage collection between engines.
- **Mask state:** Current mask persists across multiple inpaints. Risk: user may forget to update mask. Mitigation: highlight mask in UI, require explicit "Update mask" action.

### API Surface Parity
- **ProcessConfig:** Extended with `inpaint_engine`, `flux_*`, `lama_*` fields — backward-compatible (defaults used if unspecified)
- **Pipeline.run():** No signature change, new logic internal to orchestration
- **No breaking changes to existing streaming API or video encoding**

### Integration Coverage
- **Florence-2 ↔ Mask generation:** Tested (Unit 2)
- **LaMa ↔ Edge blending:** Existing blending reused, no new integration
- **Flux ↔ Sequential offload:** Tested (Unit 4)
- **Gradio ↔ Pipeline ↔ Memory manager:** Tested (Unit 6)
- **Dual-engine routing:** Tested (Unit 5)

### Unchanged Invariants
- **Temporal smoothing:** Still applied to video sequences after inpainting (Phase 2)
- **Optical flow:** Still optional, lazy-loaded, independent of inpainting choice
- **Video encoding:** FFmpeg path unchanged, output codec/quality unchanged
- **CLI/FastAPI:** Existing entry points still functional (backward compatible)

---

## Risks & Dependencies

| Risk | Mitigation |
|------|-----------|
| **CUDA OOM on 16GB during Flux load** | Sequential CPU offload as fallback; memory manager validation before load; auto-downgrade to LaMa if peak VRAM predicted >12GB |
| **Flux quality degradation with FP8 quantization** | Benchmark against FP16 on small image set; adjust quantization strategy if visible artifacts; document quality trade-off |
| **Gradio CUDA hanging (Dec 2025 known issue)** | Explicit `torch.cuda.synchronize()` before GPU function return; `queue=False` for CPU ops; integration testing on RTX 4090 |
| **Florence-2 false positives** | Optional auto-detection (off by default); allow manual mask editing in UI; confidence threshold configurable |
| **LaMa seams in high-resolution tiling** | Gaussian blending weights tested visually; unfold/fold math validated; integration test on 4K synthetic watermark |
| **Slow Flux inference (45-60s)** | Set expectations in UI; recommend LaMa for batch processing; document latency trade-offs in README |
| **Model download latency on first run** | Document HF_HOME setup; pre-download scripts optional; show progress in Gradio UI |
| **Dependency version conflicts** | Pin exact versions in requirements.txt; test in CI with PyTorch 2.1-2.3 range; document CUDA 12.1 requirement |

## Documentation / Operational Notes

- **Setup guide:** Update QUICK_START_SYSTEM.md with RTX 4090 environment activation, model pre-download, config loading
- **Config template:** Provide `config/rtx4090_laptop_defaults.yaml` with sensible 16GB defaults
- **Troubleshooting:** Document CUDA OOM → fallback to sequential offload, Flux → LaMa auto-downgrade, Florence-2 off-by-default
- **Performance benchmarks:** Document LaMa latency per resolution, Flux latency per step count, VRAM peaks per engine
- **VRAM monitoring:** Log format: timestamp | operation | allocated_gb | reserved_gb | available_gb
- **Gradio deployment:** Single-user laptop app (not multi-user server); concurrency_limit=1 mandatory

## Sources & References

- **Origin document:** Feature description provided 2026-04-16 via ce:plan command
- **Repo:** `src/watermark_removal/` (51 modules, 8,675 LOC)
- **Related PRs/issues:** Phase 2 completion (temporal smoothing, optical flow), Phase 3 active (streaming API, Label Studio)
- **External docs:**
  - [PyTorch 2.x Quantization (TorchAO)](https://docs.pytorch.org/ao/stable/)
  - [Diffusers Memory Optimization](https://huggingface.co/docs/diffusers/en/optimization/memory)
  - [Florence-2 HuggingFace](https://huggingface.co/microsoft/Florence-2-large)
  - [LaMa GitHub](https://github.com/advimman/lama)
  - [Gradio Queuing Guide](https://www.gradio.app/guides/queuing)
  - [Flux.1 Model Docs](https://huggingface.co/docs/diffusers/en/api/pipelines/flux)
