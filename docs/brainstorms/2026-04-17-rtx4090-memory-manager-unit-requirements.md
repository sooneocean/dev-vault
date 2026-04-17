---
date: 2026-04-17
topic: rtx4090-memory-manager-unit
---

# RTX 4090 Memory Manager Unit — Requirements

## Problem Frame

The RTX 4090 laptop (16GB VRAM) watermark removal system requires strict GPU memory lifecycle orchestration to avoid CUDA out-of-memory (OOM) errors. Current codebase lacks a memory-aware abstraction for:

1. **Model lifecycle** — Load, execute, unload models in optimal sequence (detect → cleanup → inpaint → cleanup → blend)
2. **VRAM accounting** — Track peak VRAM consumption per operation; fail fast if budget exceeded
3. **Cache cleanup** — Explicit `torch.cuda.empty_cache()` calls with verification to prevent fragmentation
4. **Offloading strategy** — Choose between `enable_model_cpu_offload()` (faster, 12GB peak) vs `enable_sequential_cpu_offload()` (slower, 8GB peak) based on user config
5. **Device placement** — Handle CPU fallback gracefully if GPU unavailable

Without this unit, dual-engine inpainting (LaMa + Flux) cannot safely run on 16GB—peak VRAM conflicts will cause hangs or crashes.

## Requirements

**Memory Lifecycle State Machine**
- R1. Implement state machine with explicit transitions: `idle` → `detecting` → `cleanup` → `inpainting` → `cleanup` → `blending` → `idle`
- R2. Only one model may be loaded per state; any state transition must unload the previous model before loading the next
- R3. `cleanup` state explicitly calls `torch.cuda.empty_cache()` and verifies remaining VRAM is <1GB (allow 500MB margin)

**VRAM Budget Enforcement**
- R4. Maintain a `vram_budget` parameter (default 16GB for RTX 4090); raise `VRAMExceededError` if any operation would exceed budget
- R5. Before loading any model, check `torch.cuda.get_device_properties(device).total_memory` to verify actual GPU capacity
- R6. Log model load/unload with peak VRAM consumption (use `torch.cuda.max_memory_allocated()` after each operation)

**Offload Strategy Selection**
- R7. Support two offload modes: `"fast"` (default, `enable_model_cpu_offload()`, 12GB peak) and `"sequential"` (`enable_sequential_cpu_offload()`, 8GB peak)
- R8. Mode is selectable via `ProcessConfig.memory_offload_mode`; users choose based on speed/VRAM trade-off (UI exposure handled in Gradio unit)
- R9. Automatically apply offload mode to any diffusers-based pipeline passed to the state machine

**Device & Fallback Handling**
- R10. Detect GPU availability at initialization; if CUDA unavailable, fail with clear error (GPU required for this unit)

**Integration Points**
- R12. Expose a public API: `MemoryManager(vram_budget=16, offload_mode="fast")` with methods `load_model(name, model)`, `execute(fn, *args)`, `cleanup()`, `current_state()`
- R13. Integrate with existing `ProcessConfig` type; add fields `memory_offload_mode` (enum: "fast", "sequential"), `vram_budget_gb` (int, default 16)

**Testing & Verification**
- R15. Unit tests verify state transitions, VRAM tracking, cleanup effectiveness, and OOM prevention with mock models
- R16. Integration test with Florence-2 + LaMa on simulated 16GB GPU (mocking peak VRAM); confirm zero OOM (benchmarking of actual model VRAM is deferred to Phase 3 integration testing)

## Scope Boundaries

- **In scope:** Memory state machine, VRAM tracking, cache cleanup, offload mode selection, device availability detection
- **Out of scope:**
  - Actual Florence-2, LaMa, Flux model implementations (separate units)
  - Gradio UI integration (handled in Gradio unit)
  - Advanced profiling tools (memory profiler for R&D only, not production)
  - Mixed device placement (encoder on GPU, decoder on CPU) — defer to Phase 3 if needed
  - Async version for streaming pipelines (Phase 3)

## Success Criteria

- Zero CUDA OOM errors when running detect → inpaint → blend pipeline on RTX 4090 16GB with user-provided images up to 4K resolution
- Peak VRAM consumption stays within configured budget; if exceeded, raise clear error before crash
- State machine enforces strict ordering; attempting out-of-order transitions raises `StateTransitionError`
- `fast` mode completes inpainting in 45-60s; `sequential` mode completes in 5-10min (acceptable trade-off)
- Unit tests pass with 100% state coverage; integration test reproduces real Florence-2 + LaMa workflow

## Key Decisions

| Decision | Rationale |
|----------|-----------|
| **Explicit state machine vs. implicit cleanup** | State machine makes memory contracts explicit in code and tests. Prevents accidental model leaks from hidden references or async tasks. |
| **Separate `cleanup` state** | Ensures reliable cache clearing between model loads. Alternative (inline cleanup after unload) risks fragmentation if exceptions occur. |
| **User-selectable offload mode** | Different users have different speed/VRAM constraints. UI choice (not auto-detection) respects user knowledge of their workload. |
| **VRAM budget as config, not hardcoded** | Enables testing on CPU/smaller GPUs and GPU variability. |

## Dependencies / Assumptions

- **PyTorch ≥2.0** with CUDA 12.1+ (bitsandbytes requires this for FP8)
- **Diffusers ≥0.28.0** with `enable_model_cpu_offload()` and `enable_sequential_cpu_offload()` methods
- **Florence-2 and LaMa models** available locally or via Hugging Face `transformers` (downloading/caching is out of scope for this unit)
- **VRAM accounting is best-effort** — `torch.cuda.max_memory_allocated()` may include internal fragmentation; we enforce budget conservatively (leave 500MB margin)

## Outstanding Questions

### Resolve Before Planning

- [Needs research] Should memory manager support CPU-only fallback transparently (auto-switch models to CPU if OOM detected), or fail fast with clear error? **Decision:** Fail fast with error; transparent fallback risks surprising performance degradation and hides user's hardware mismatch. Fallback only when CUDA fully unavailable.

### Deferred to Planning

- [Technical] How to mock GPU VRAM in unit tests given pytest runs on user's actual hardware? Consider `unittest.mock.patch('torch.cuda.get_device_properties')` or separate integration test suite with configurable VRAM limits.
- [Needs research] Is `torch.cuda.empty_cache()` sufficient to prevent fragmentation, or do we need `torch.cuda.reset_peak_memory_stats()` after each cleanup?

## Next Steps

→ `/ce:plan` for structured implementation planning
