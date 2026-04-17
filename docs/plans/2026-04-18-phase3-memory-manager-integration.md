---
date: 2026-04-18
topic: phase3-memory-manager-integration
phase: 3
---

# Phase 3: Memory Manager Integration Testing

## Context

The Memory Manager Unit (PR #13) provides strict VRAM lifecycle management for RTX 4090. This plan bridges the gap between the unit tests and real-world usage by integrating MemoryManager with:
- Florence2Detector (detection engine)
- DualEngineRouter (routing layer)
- LamaInpainter + FluxInpainter (execution engines)

Current state: Memory Manager tested in isolation; routers/detectors exist but not integrated with MemoryManager lifecycle.

## Goals

1. **Verify memory_offload_mode propagates** from ProcessConfig → DualEngineRouter → FluxInpainter
2. **Test Florence2Detector integration** with MemoryManager (load/unload lifecycle)
3. **Validate complete workflow** (detect → inpaint → cleanup) with real state transitions
4. **Benchmark VRAM usage** (4K images with LaMa vs Flux vs auto-downgrade)
5. **Verify auto-downgrade logic** (Flux → LaMa on OOM)

## Requirements

**R1: DualEngineRouter accepts ProcessConfig.memory_offload_mode**
- Router must read offload mode and apply to FluxInpainter initialization
- Allow override via InpaintEngineConfig for flexibility

**R2: Florence2Detector integrates with MemoryManager**
- Accept optional MemoryManager parameter
- Call load_model("florence2", self.model) on lazy load
- Call unload_model("florence2") on cleanup

**R3: Complete detect→inpaint workflow with state transitions**
- IDLE → DETECT_LOADING → DETECTING → DETECT_CLEANUP → INPAINT_LOADING → INFERRING → INPAINT_CLEANUP → IDLE
- Verify each transition succeeds with mocked models

**R4: Auto-downgrade validation**
- Flux with insufficient VRAM should downgrade to LaMa
- LaMa should succeed even when Flux would OOM
- Log downgrade reasoning

**R5: 4K image VRAM benchmarking**
- Create synthetic 4K image (3840×2160)
- Estimate peak VRAM for Flux (sequential vs fast offload)
- Verify estimate vs actual with mock VRAM tracking

## Files to Modify/Create

| File | Purpose | Change |
|---|---|---|
| `src/watermark_removal/florence2_detector.py` | Add MemoryManager support | Optional MM parameter, load/unload calls |
| `src/watermark_removal/dual_engine_router.py` | Offload mode propagation | Read ProcessConfig.memory_offload_mode, pass to Flux |
| `tests/test_dual_engine_router.py` | NEW: Router unit tests | DualEngineRouter with MemoryManager, offload mode selection |
| `tests/test_memory_manager_integration.py` | NEW: Integration tests | Florence2 + router + VRAM lifecycle |
| `tests/conftest.py` | Shared fixtures | Mock models, VRAM snapshots, 4K image fixtures |

## Implementation Units

### Unit 1: Florence2Detector MemoryManager Integration

**Goal:** Florence2Detector accepts and respects MemoryManager lifecycle

**Approach:**
1. Add `memory_manager: Optional[MemoryManager]` parameter to `__init__`
2. In `_lazy_load_model()`, call `self.memory_manager.load_model("florence2", self.model)`
3. Add `cleanup()` method that calls `self.memory_manager.unload_model("florence2")`
4. Test with mocked MemoryManager

**Files:**
- `src/watermark_removal/florence2_detector.py`

**Test Scenarios:**
- Load without MemoryManager (backward compatible)
- Load with MemoryManager (calls load_model)
- Cleanup removes from tracked models
- State transitions work (IDLE → DETECT_LOADING → DETECTING → DETECT_CLEANUP → IDLE)

**Verification:**
- florence2_detector accepts `mm` parameter
- `mm.load_model("florence2", model)` called on lazy load
- `mm.unload_model("florence2")` called on cleanup
- 4 unit tests passing

---

### Unit 2: DualEngineRouter Offload Mode Propagation

**Goal:** Router reads memory_offload_mode from ProcessConfig and applies to Flux

**Approach:**
1. Modify `DualEngineRouter.__init__` to accept `ProcessConfig` or add `offload_mode` parameter
2. When initializing FluxInpainter, set `enable_sequential_offload` based on mode
3. Handle both InpaintEngineConfig.flux_enable_sequential_offload and ProcessConfig.memory_offload_mode

**Files:**
- `src/watermark_removal/dual_engine_router.py`
- `src/watermark_removal/gradio_app.py` (update to pass config)

**Test Scenarios:**
- Router with FAST offload mode (enable_model_cpu_offload, ~12GB)
- Router with SEQUENTIAL offload mode (enable_sequential_cpu_offload, ~8GB)
- Flux initialized with correct offload setting
- LaMa ignores offload mode (has own tiling strategy)

**Verification:**
- `router.config.flux_enable_sequential_offload` set correctly from mode
- 3 unit tests (fast, sequential, lama-agnostic)

---

### Unit 3: Complete Detect→Inpaint Workflow

**Goal:** Full state machine workflow with Florence2 + Router + MemoryManager

**Approach:**
1. Create integration test that chains: Florence2Detector → DualEngineRouter.inpaint → cleanup
2. Mock models to avoid real downloads
3. Verify state transitions: IDLE → DETECT_LOADING → ... → IDLE
4. Use synthetic 512×512 image to keep test fast

**Files:**
- `tests/test_memory_manager_integration.py` (NEW)

**Test Scenarios:**
- Happy path: detect → inpaint → cleanup all succeed
- VRAM headroom validated at each step
- State transitions logged correctly
- Models unloaded and VRAM cleared between phases

**Verification:**
- 1 integration test passing
- State transition log shows all 8 transitions
- Final state is IDLE with 0 loaded models

---

### Unit 4: Auto-Downgrade Validation

**Goal:** DualEngineRouter downgrades Flux→LaMa on insufficient VRAM

**Approach:**
1. Test with high Flux VRAM estimate, low available VRAM
2. Flux validation fails (insufficient headroom)
3. Router auto-downgrades if `auto_downgrade_on_oom=True`
4. Mock `memory_manager.validate_vram_headroom()` to raise `InsufficientVRAMError`

**Files:**
- `tests/test_dual_engine_router.py` (NEW)

**Test Scenarios:**
- Flux with sufficient VRAM → use Flux
- Flux with insufficient VRAM + auto_downgrade=True → use LaMa
- Flux with insufficient VRAM + auto_downgrade=False → raise error

**Verification:**
- 3 unit tests passing
- Downgrade logic uses correct VRAM check
- Log message explains downgrade reason

---

### Unit 5: 4K Image VRAM Benchmarking

**Goal:** Verify VRAM estimates for 4K images (3840×2160)

**Approach:**
1. Create synthetic 4K image
2. Estimate Flux VRAM for 4K:
   - FAST offload: ~12GB (should fit with 1GB headroom buffer)
   - SEQUENTIAL offload: ~8GB (should fit comfortably)
3. Verify estimate logic scales correctly

**Files:**
- `tests/test_memory_manager_integration.py` (NEW)

**Test Scenarios:**
- 4K Flux FAST estimate >= 12GB
- 4K Flux SEQUENTIAL estimate >= 8GB (accounting for 20% reduction from sequential)
- Estimate > 1080p proportionally
- LaMa estimate stays ~2GB regardless of resolution (uses tiling)

**Verification:**
- 2 unit tests passing
- VRAM estimates align with docstring assumptions
- Headroom buffer (1GB) sufficient for both modes

---

## Dependencies & Assumptions

- **PyTorch ≥2.0** with mock memory functions
- **Mocked Florence2Detector and InpaintEngineRouter** (no real model downloads)
- **MemoryManager** fully functional from PR #13
- **Synthetic test images** (PIL Image.new or numpy arrays)

## Success Criteria

- ✅ Florence2Detector accepts MemoryManager and calls load/unload
- ✅ DualEngineRouter propagates memory_offload_mode to Flux
- ✅ Complete detect→inpaint→cleanup workflow executes all state transitions
- ✅ Auto-downgrade logic works (Flux→LaMa, logs reason)
- ✅ 4K VRAM estimates realistic (12GB Flux FAST, 8GB Flux SEQUENTIAL, 2GB LaMa)
- ✅ 20+ new integration tests passing
- ✅ Backward compatibility (detectors/routers work without MemoryManager)

## Outstanding Questions

### Resolve Before Implementation

- **Q1**: Should Florence2Detector accept MemoryManager in `__init__` or only on `detect()` call?
  - **Decision**: In `__init__` so detector manages full lifecycle
- **Q2**: Should DualEngineRouter require ProcessConfig or keep flexible with InpaintEngineConfig?
  - **Decision**: Accept both (InpaintEngineConfig primary, ProcessConfig as override for UI)

### Deferred to Implementation

- Exact VRAM estimates for real Flux/LaMa models (currently conservative approximations)
- Micro-optimizations for offload mode selection (profile actual models later)
- Streaming integration (Phase 3B)

## Next Steps

→ Begin implementation from Unit 1 (Florence2Detector integration)
