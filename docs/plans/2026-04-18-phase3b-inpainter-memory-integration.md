---
date: 2026-04-18
topic: phase3b-inpainter-memory-integration
phase: 3b
---

# Phase 3B: LaMa + Flux Inpainter MemoryManager Integration

## Context

Phase 3 integration tests are complete (79 tests passing). Now integrate the actual inpainting engines (LamaInpainter, FluxInpainter) with MemoryManager lifecycle management, mirroring Florence2Detector pattern.

Current state:
- DualEngineRouter already calls `memory_manager.load_model()` / `unload_model()`
- LamaInpainter and FluxInpainter exist but don't integrate with MemoryManager
- Gradio app passes router but doesn't propagate memory_offload_mode to Flux

## Goals

1. **LamaInpainter MemoryManager Integration** — Accept optional MM, call load/unload
2. **FluxInpainter MemoryManager Integration** — Accept optional MM, apply offload mode, call load/unload
3. **DualEngineRouter Offload Propagation** — Pass ProcessConfig.memory_offload_mode → FluxInpainter
4. **Gradio Offload Mode Propagation** — Connect UI slider → ProcessConfig → Router → Flux
5. **Complete Integration Tests** — Test all three engines with MemoryManager in workflow

## Files to Modify/Create

| File | Purpose | Change |
|---|---|---|
| `src/watermark_removal/lama_inpainter.py` | Add MemoryManager support | Optional MM parameter, load/unload calls |
| `src/watermark_removal/flux_inpainter.py` | Add MemoryManager + offload mode | Optional MM, apply offload mode, load/unload |
| `src/watermark_removal/dual_engine_router.py` | Offload mode propagation | Pass ProcessConfig.memory_offload_mode to Flux |
| `src/watermark_removal/gradio_app.py` | UI integration | Create InpaintEngineConfig from ProcessConfig + offload_mode |
| `tests/test_lama_inpainter.py` | Existing test file | Add MemoryManager integration tests |
| `tests/test_flux_inpainter.py` | Existing test file | Add MemoryManager integration tests |
| `tests/test_gradio_app.py` | NEW: Gradio integration | Test offload_mode propagation through UI |

## Implementation Units

### Unit 1: LamaInpainter MemoryManager Integration

**Goal:** LamaInpainter accepts MemoryManager and manages load/unload lifecycle

**Files:**
- `src/watermark_removal/lama_inpainter.py`
- `tests/test_lama_inpainter.py`

**Approach:**
1. Add `memory_manager: Optional[MemoryManager]` parameter to `__init__`
2. In `load_model()`, call `self.memory_manager.load_model("lama", self.model)`
3. In `cleanup()`, call `self.memory_manager.unload_model("lama")`
4. Add 5 unit tests (backward compatible, lifecycle, cleanup)

**Verification:**
- LamaInpainter accepts MM parameter
- load_model() registers with MM
- cleanup() unregisters from MM
- Works without MM (backward compatible)

---

### Unit 2: FluxInpainter MemoryManager Integration

**Goal:** FluxInpainter accepts MemoryManager, applies offload mode, manages lifecycle

**Files:**
- `src/watermark_removal/flux_inpainter.py`
- `tests/test_flux_inpainter.py`

**Approach:**
1. Add `memory_manager: Optional[MemoryManager]` parameter to `__init__`
2. Add `enable_sequential_offload: bool` parameter (already in config, ensure used)
3. In `_lazy_load_model()` or `load_model()`:
   - Apply offload mode to pipeline: `enable_sequential_cpu_offload()` or `enable_model_cpu_offload()`
   - Call `self.memory_manager.load_model("flux", self.model)`
4. In `cleanup()`, call `self.memory_manager.unload_model("flux")`
5. Add 5 unit tests (offload modes, lifecycle, cleanup)

**Verification:**
- FluxInpainter accepts MM and offload_mode
- Sequential offload applied when enabled
- Fast offload applied when disabled
- load_model() registers with MM
- cleanup() unregisters from MM

---

### Unit 3: DualEngineRouter Offload Mode Propagation

**Goal:** Router propagates ProcessConfig.memory_offload_mode → FluxInpainter

**Files:**
- `src/watermark_removal/dual_engine_router.py`
- `tests/test_dual_engine_router.py` (add tests)

**Approach:**
1. Update `DualEngineRouter.__init__` to accept optional ProcessConfig
2. If ProcessConfig provided, read `memory_offload_mode` and pass to FluxInpainter
3. Maintain backward compatibility with InpaintEngineConfig alone
4. Add 3 unit tests (ProcessConfig read, mode propagation, backward compat)

**Verification:**
- Router reads offload_mode from ProcessConfig
- Passes mode to FluxInpainter initialization
- Works with InpaintEngineConfig alone (backward compatible)
- Mode propagates correctly (sequential vs fast)

---

### Unit 4: Gradio Offload Mode UI Integration

**Goal:** Gradio UI exposes offload_mode selection, propagates through system

**Files:**
- `src/watermark_removal/gradio_app.py`

**Approach:**
1. Add radio button for offload mode selection: "Fast (12GB)" vs "Sequential (8GB)"
2. In `inpaint_image()` callback:
   - Read offload_mode from UI
   - Create ProcessConfig or InpaintEngineConfig with mode
   - Pass to router
3. Update docstring to document offload_mode parameter
4. Add 2 Gradio integration tests (UI callback, mode propagation)

**Verification:**
- UI renders two offload mode options
- Callback reads UI selection
- Mode propagates to router
- Router applies mode to Flux

---

### Unit 5: Complete Integration Tests

**Goal:** End-to-end tests with LaMa + Flux + MemoryManager in Gradio context

**Files:**
- `tests/test_gradio_app.py` (NEW or extend existing)

**Test Scenarios:**
1. Gradio detection → inpainting (LaMa) → complete
2. Gradio detection → inpainting (Flux, fast offload) → downgrade on OOM
3. Gradio detection → inpainting (Flux, sequential offload) → complete
4. VRAM state tracked through Gradio callbacks
5. State machine resets to IDLE after each operation

**Verification:**
- Gradio callbacks integrate with MemoryManager
- All state transitions execute correctly
- Offload modes work through UI
- 5 integration tests passing

---

## Dependencies & Assumptions

- LamaInpainter and FluxInpainter already exist with `load_model()` and `cleanup()` methods
- DualEngineRouter already instantiates both engines
- ProcessConfig.memory_offload_mode from PR #13 is available
- MemoryManager from PR #13 is functional

## Success Criteria

- ✅ LamaInpainter + FluxInpainter both accept optional MemoryManager
- ✅ FluxInpainter applies offload mode correctly (sequential vs fast)
- ✅ DualEngineRouter propagates ProcessConfig.memory_offload_mode to Flux
- ✅ Gradio UI exposes offload mode selection
- ✅ Complete end-to-end workflow: UI → Router → Inpainters → MemoryManager
- ✅ 20+ new tests passing (5 LaMa + 5 Flux + 3 Router + 2 Gradio + 5 integration)
- ✅ Backward compatible (all components work without MemoryManager)

## Outstanding Questions

### Resolve Before Implementation

- **Q1**: Should FluxInpainter apply offload mode in `__init__` or `load_model()`?
  - **Decision**: In `load_model()` so mode is applied fresh each load
- **Q2**: Should Gradio UI slider scale be 0-16 GB or just two buttons?
  - **Decision**: Two radio buttons (Fast vs Sequential) for clarity

### Deferred to Implementation

- Real Flux model testing (requires actual model download)
- Performance benchmarking (profile actual VRAM with real models)

## Next Steps

→ Execute Unit 1-5 in sequence
→ Create comprehensive Phase 3B PR
