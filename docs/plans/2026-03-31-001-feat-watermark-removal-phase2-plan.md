---
title: feat: Watermark Removal System Phase 2 — Temporal Smoothing & Tracking Activation
type: feat
status: active
date: 2026-03-31
origin: docs/plans/2026-03-30-001-feat-watermark-removal-system-plan.md
---

# Watermark Removal System Phase 2 — Activation & Hardening

## Overview

Phase 2 activates, validates, and optimizes advanced features already integrated into Phase 1 codebase:
- **Temporal smoothing** (simple alpha blend + adaptive motion-aware)
- **Watermark tracking** (BBox interpolation + YOLO scaffold)
- **Poisson blending** (iterative solver + gradient preservation)
- **Checkpoint resumption** (state serialization)

Phase 1 built all infrastructure; Phase 2 **proves it works end-to-end** via configuration, YOLO setup, and comprehensive validation.

**Success Criteria:** Enable Phase 2 features via config flags + YOLO model; validate 5+ test scenarios; publish operational guides.

---

## Problem Frame

Phase 1 MVP accepts single-frame per-frame inpaint, producing acceptable but sub-optimal results:
- Inter-frame flicker (±1-2 px jitter at crop edges)
- Watermark boundaries visible when moving
- Temporal incoherence on static backgrounds
- No moving watermark support

Phase 2 removes these limitations by activating already-built but untested features:
1. Temporal smoothing reduces flicker (configurable alpha, adaptive motion-aware)
2. YOLO + tracking enables moving watermark following
3. Poisson blending smooths boundaries beyond feathering
4. Checkpoint save/resume enables long video processing

*Current state:* All code exists, test coverage is 266+ tests, but **no integration test validates Phase 2 end-to-end**.

---

## Requirements Trace

| Req | Description | Unit |
|-----|-------------|------|
| R11 | Apply temporal smoothing to reduce inter-frame flicker | 1, 2 |
| R12 | Support simple YOLO-based bbox tracking for moving watermarks | 1, 3 |
| Phase2-A | Enable temporal smoothing via config flag | 1 |
| Phase2-B | Enable Poisson blending via config flag | 2 |
| Phase2-C | Enable watermark tracking via config flag | 3 |
| Phase2-D | Validate YOLO model loading and detection | 3 |
| Phase2-E | Test temporal smoothing with adaptive motion | 1 |
| Phase2-F | Validate checkpoint save/resume workflow | 4 |
| Phase2-G | Document Phase 2 configuration and operation | 5 |

---

## Scope Boundaries

### In Scope (Phase 2)
- Activate temporal smoothing (simple + adaptive options)
- Activate Poisson blending (dual-path: Jacobi solver + feathering fallback)
- Integrate YOLO model loading + inference
- Checkpoint save/resume validation
- End-to-end pipeline testing (mocked ComfyUI)
- Configuration tuning guides
- Operational documentation

### Out of Scope
- Multi-watermark tracking (Phase 3)
- Automatic watermark detection (Phase 3)
- Optical flow or advanced motion estimation (Phase 3)
- GPU acceleration or CUDA optimization (Phase 3)
- Real-time preview UI (deferred)
- Cloud deployment (deferred)

---

## Context & Research

### Phase 1 Codebase State

**All Phase 2 modules already exist and are test-covered:**

| Module | Tests | Status |
|--------|-------|--------|
| temporal_smoother.py | 12 | ✅ Complete |
| watermark_tracker.py | 15 | ✅ Complete |
| poisson_blender.py | 34 | ✅ Complete |
| checkpoint.py | 4 | ✅ Complete |
| pipeline.py | 12 | ✅ Integrated |

**266 total tests across all modules** — Phase 1 + Phase 2 infrastructure fully tested.

**Configuration Parameters Available:**
- `temporal_smooth_alpha` (0.0-1.0, default 0.0 = disabled)
- `use_adaptive_temporal_smoothing` (bool)
- `use_poisson_blending` (bool)
- `poisson_max_iterations` (int, default 100)
- `use_watermark_tracker` (bool)
- `yolo_model_path` (str/null)
- `yolo_confidence_threshold` (float, 0.0-1.0)
- `use_checkpoints` (bool)

**All Phase 2 features are already integrated into pipeline.py** — No code modifications needed for activation.

### Institutional Learnings

From Phase 1 implementation:
- Feather blending sufficient for static watermarks (R7)
- Per-frame inpaint acceptable as MVP baseline
- YAML config highly effective for parameter tuning
- Async/await patterns scale well to 4-8 parallel crops
- CropRegion metadata enables precise stitch-back without rearchitecting

### External References

**YOLO Integration:**
- Ultralytics YOLOv8 documentation: https://docs.ultralytics.com/
- Model selection: YOLOv8n (nano) for lightweight deployment, YOLOv8m for accuracy
- Pre-trained weights available at Hugging Face: https://huggingface.co/ultralytics/

**Temporal Coherence:**
- Alpha blending standard for video stabilization (e.g., optical flow warping + blend)
- Adaptive alpha based on motion: Industry practice (e.g., Adobe Premiere motion adaptive blending)

---

## Key Technical Decisions

| Decision | Rationale |
|----------|-----------|
| **Activate via config, not new code** | All Phase 2 features are integrated; enables feature flags without risky refactors |
| **YOLO model optional** | Graceful degradation if model unavailable; bbox tracking works without detection |
| **Adaptive temporal smoothing** | Motion-aware alpha reduces flicker on moving objects; simple alpha sufficient for static |
| **Dual-path Poisson** | Jacobi solver works well for 1024x1024 regions; feathering fallback when convergence slow |
| **Checkpoint as Phase 2, not Phase 3** | Enables long video processing (addresses scale concern); low risk, already tested |

---

## Open Questions

### Resolved During Planning

- **How much of Phase 2 is already implemented?** → All core features implemented in Phase 1; Phase 2 is activation + testing
- **Do we need to modify pipeline.py?** → No; all Phase 2 integration already present (lines 82-95, 138-152, 290-336, 354-383)
- **Is YOLO model mandatory?** → No; graceful degradation if unavailable; bbox tracking works with manual bboxes
- **What GPU requirements for Poisson?** → None; Jacobi solver is CPU-only; suitable for 1024x1024 crops with 100 iterations (~200ms)

### Deferred to Implementation

- **Exact YOLO model weight source & download strategy** — Will be determined during Unit 3 implementation
- **Optimal temporal smooth alpha per scenario** — Will be tuned via end-to-end testing (Unit 2)
- **Checkpoint file format versioning** — Addressed if checkpoint compatibility breaks arise
- **Performance baseline per Phase 2 feature** — Will be benchmarked in Unit 5

---

## High-Level Technical Design

> *This illustrates the intended approach and is directional guidance for review, not implementation specification.*

### Phase 2 Activation Flow

```
┌─────────────────────────────────────────────────────┐
│ Phase 2 Activation Workflow                         │
└─────────────────────────────────────────────────────┘

1. Configuration Validation (Unit 1)
   ├─ Load YAML with Phase 2 flags
   ├─ Validate parameter ranges
   └─ Report config summary

2. YOLO Setup & Testing (Unit 3)
   ├─ Detect model weights path (local, HF, or null)
   ├─ Lazy load model (graceful fallback)
   ├─ Test inference on sample frame
   └─ Report detection accuracy

3. Pipeline Integration Testing (Units 2, 4)
   ├─ End-to-end with mocked ComfyUI
   ├─ Test temporal smoothing (simple + adaptive)
   ├─ Test checkpoint save/resume
   └─ Validate output quality vs Phase 1

4. Performance Benchmarking (Unit 5)
   ├─ Measure per-frame overhead (temporal + tracking + blending)
   ├─ Report bottlenecks
   └─ Tuning recommendations

5. Documentation & Guides (Unit 6)
   ├─ Configuration reference
   ├─ Tuning scenarios (static/dynamic watermarks)
   └─ Troubleshooting guide
```

### Feature Integration Points

**Temporal Smoothing:**
```
Preprocessing → Inpaint → Postprocessing [Stitch] → [Temporal Smoothing] → Encoding
                                              ↑                    ↑
                                         (Phase 1)            (Phase 2)
```
- Apply after stitch, before encoding
- Modifies frame sequence in-place
- Configurable alpha or adaptive

**Watermark Tracking:**
```
Frame → [Load Bbox] → [Interpolate] → [Crop] → Inpaint → Stitch
              ↑           ↑
           (Phase 2)  (Phase 2)
           YOLO or    Smooth trajectory
           manual     over keyframes
```
- Detect or load per-frame bbox
- Interpolate missing frames
- Use dynamic bbox for crop region

**Poisson Blending:**
```
Stitch: Inpainted crop + Original frame
          ├─ [Feather mask] ← Phase 1
          └─ [Poisson blend] ← Phase 2 (optional, replaces feather)
```
- Optional; can run with or without
- Dual-path: Jacobi solver or fast feathering fallback

**Checkpointing:**
```
Preprocessing → [Save state] → Inpaint → [Save state] → Postprocessing → [Save state]
                  (Phase 2)                (Phase 2)                     (Phase 2)
```
- Resumable from checkpoint file
- State = crop_regions list + frame index

---

## Implementation Units

- [ ] **Unit 1: Configuration Validation & Phase 2 Parameter Tests**

**Goal:** Validate all Phase 2 parameters can be loaded, parsed, and applied without errors.

**Requirements:** Phase2-A, Phase2-B, Phase2-C, Phase2-G

**Dependencies:** None (uses existing config_manager.py + types.py)

**Files:**
- Create: `tests/test_phase2_config.py`
- Modify: `tests/conftest.py` (add Phase 2 fixtures)
- Read: `src/watermark_removal/core/types.py` (ProcessConfig)
- Read: `src/watermark_removal/core/config_manager.py`

**Approach:**
- Load base.yaml + phase2_temporal.yaml + phase2_tracking.yaml configs
- Validate parameter ranges (alpha ∈ [0, 1], iterations > 0, threshold ∈ [0, 1])
- Test parameter override via CLI args
- Verify backward compatibility: Phase 2 params default to disabled
- Test config error messages (invalid alpha → clear error)

**Patterns to follow:**
- Use `pytest.mark.parametrize` for range testing
- Mirror test structure from `tests/test_config_manager.py`
- Fixtures from `conftest.py`

**Test scenarios:**
- **Happy path**: Load phase2_temporal.yaml; all params parsed correctly
- **Happy path**: Load phase2_tracking.yaml; YOLO config optional
- **Edge case**: temporal_smooth_alpha = 0.0 (disabled); phase 2 feature deactivated
- **Edge case**: temporal_smooth_alpha = 1.0 (max); full previous-frame blend
- **Edge case**: poisson_max_iterations = 1; single iteration (fast, lower quality)
- **Error path**: temporal_smooth_alpha = 1.5 (invalid); raises ValueError
- **Error path**: yolo_confidence_threshold = "high" (wrong type); raises TypeError
- **Integration**: Override config param via CLI flag: `--temporal-smooth-alpha 0.4`

**Verification:**
- All Phase 2 params documented in config reference
- Config loading does not break Phase 1 pipelines (backward compatible)
- Parameter defaults disable Phase 2 (opt-in behavior)

---

- [ ] **Unit 2: Temporal Smoothing End-to-End Test**

**Goal:** Validate temporal smoothing produces flicker-free output; test both simple and adaptive modes.

**Requirements:** Phase2-A, Phase2-E

**Dependencies:** Unit 1, existing temporal_smoother.py

**Files:**
- Create: `tests/test_phase2_temporal_integration.py`
- Read: `src/watermark_removal/postprocessing/temporal_smoother.py`
- Read: `src/watermark_removal/postprocessing/adaptive_temporal_smoother.py`
- Modify: `tests/conftest.py` (add frame sequence fixture)

**Approach:**
- Create synthetic frame sequence (10 frames, progressive motion)
- Apply temporal smoothing with various alpha values
- Measure inter-frame difference (flicker metric)
- Verify adaptive smoothing adjusts alpha based on motion
- Compare output quality: Phase 1 (no smoothing) vs Phase 2 (with smoothing)

**Technical design:**
```
For each alpha in [0.0, 0.1, 0.3, 0.5, 1.0]:
  1. Apply TemporalSmoother(alpha)
  2. Compute frame-to-frame L2 distance (flicker)
  3. Verify distance decreases as alpha increases
  4. Assert flicker(alpha=0.3) < flicker(alpha=0.0)

For adaptive smoothing:
  1. Detect motion per-frame via frame diff
  2. Verify alpha adapts (lower on high motion, higher on static)
  3. Assert output smoother than simple alpha on mixed motion
```

**Patterns to follow:**
- Use numpy for frame diff calculation
- Fixture for synthetic frame sequences
- Mirror structure from `tests/test_temporal_smoother.py`

**Test scenarios:**
- **Happy path**: Apply smoothing to 10-frame sequence; output has lower flicker
- **Happy path (adaptive)**: Static region + moving region; adaptive alpha applies correctly
- **Edge case**: alpha = 0.0 (no smoothing); output = input
- **Edge case**: alpha = 1.0 (full blend); output heavily smoothed
- **Edge case**: Single frame; no previous frame; skips smoothing
- **Integration**: Temporal smoothing after stitch phase; pixel values valid [0, 255]

**Verification:**
- Flicker metric improves with temporal smoothing
- Adaptive smoothing responds correctly to motion
- Output frame dimensions match input
- No NaN or overflow values

---

- [ ] **Unit 3: YOLO Model Integration & Watermark Tracking Test**

**Goal:** Validate YOLO model loading, detection, and BBox tracking integration.

**Requirements:** Phase2-C, Phase2-D, R12

**Dependencies:** Unit 1, existing watermark_tracker.py

**Files:**
- Create: `tests/test_phase2_tracking_integration.py`
- Create: `scripts/setup_yolo_model.py` (helper to download weights)
- Modify: `src/watermark_removal/preprocessing/watermark_tracker.py` (if needed for model path resolution)
- Read: `src/watermark_removal/preprocessing/watermark_tracker.py`
- Read: `src/watermark_removal/core/types.py` (ProcessConfig)

**Approach:**
- Detect YOLO model availability (local path, Hugging Face, or none)
- Test YOLOTrackerWrapper lazy loading (graceful fallback if unavailable)
- Validate detection on synthetic frames (rect with known bbox)
- Test bbox interpolation (sparse detections → smooth trajectory)
- Verify tracker integrates with pipeline (crop handler receives dynamic bbox)

**Patterns to follow:**
- Use unittest.mock to test YOLO unavailability
- Fixture for synthetic watermark frames
- Mirror structure from `tests/test_watermark_tracker.py`

**Test scenarios:**
- **Happy path**: YOLO model loads; detects watermark with confidence > threshold
- **Happy path**: Sparse detections (frames 0, 5, 10); interpolation fills frames 1-4, 6-9
- **Edge case**: YOLO model not available; tracker degrades gracefully (returns empty)
- **Edge case**: Detection confidence below threshold; frame skipped
- **Edge case**: Tracking on stationary watermark; bbox stable across frames
- **Error path**: Invalid model path; raises FileNotFoundError with clear message
- **Integration**: BBox from tracker → crop region with correct dimensions

**Verification:**
- YOLO model setup script documented
- Detection confidence logged
- Interpolated trajectory smooth (no discontinuities)
- Pipeline accepts dynamic bbox from tracker

---

- [ ] **Unit 4: Checkpoint Save/Resume Validation**

**Goal:** Validate checkpoint serialization and resumption; enable long video processing.

**Requirements:** Phase2-F

**Dependencies:** Unit 1, existing checkpoint.py

**Files:**
- Create: `tests/test_phase2_checkpoint_integration.py`
- Read: `src/watermark_removal/core/checkpoint.py`
- Read: `src/watermark_removal/core/pipeline.py` (integration points)

**Approach:**
- Save checkpoint after preprocessing (crop_regions list)
- Save checkpoint after inpaint (crop_regions + inpaint results)
- Resume from checkpoint; verify state loaded correctly
- Test edge cases: corrupted checkpoint, partial save, version mismatch
- Verify checkpoint file format is stable (JSON, readable by humans)

**Patterns to follow:**
- Use tempfile for checkpoint files
- Parametrized tests for checkpoint stages
- Mirror structure from `tests/test_checkpoint.py`

**Test scenarios:**
- **Happy path**: Save after preprocessing; resume correctly; crop_regions match
- **Happy path**: Save after inpaint; resume with inpaint results; stitch works
- **Edge case**: Resume from non-existent checkpoint; raises FileNotFoundError
- **Edge case**: Checkpoint file corrupted (truncated JSON); raises ValueError
- **Error path**: Checkpoint version mismatch; log warning, start from scratch
- **Integration**: Pipeline with `--use-checkpoints --resume-from-checkpoint` flags

**Verification:**
- Checkpoint file format stable and human-readable
- Resume produces identical results to continuous run
- Checkpoint reduces reprocessing time for long videos

---

- [ ] **Unit 5: Performance Benchmarking & Optimization Guide**

**Goal:** Benchmark Phase 2 features; identify bottlenecks; publish tuning recommendations.

**Requirements:** Phase2-E, Phase2-G

**Dependencies:** Units 1-4

**Files:**
- Create: `scripts/benchmark_phase2.py` (benchmark runner)
- Create: `docs/phase2_performance_guide.md` (tuning reference)
- Modify: `docs/README.md` (add Phase 2 section)

**Approach:**
- Benchmark per-frame overhead for each Phase 2 feature
- Measure inpaint time (baseline), temporal smoothing time, tracking time, blending time
- Test on 3 sample videos: static watermark, moving watermark, complex background
- Profile Poisson solver convergence (iterations vs accuracy)
- Identify bottlenecks; publish optimization recommendations

**Technical design:**
```
For each feature [temporal, tracking, poisson]:
  1. Run Phase 1 baseline (no feature)
  2. Run with feature enabled
  3. Measure per-frame time: (total_time - baseline) / frame_count
  4. Report overhead percentage
  5. Identify if overhead acceptable (< 5% per feature)

For Poisson solver:
  1. Test iterations: 50, 100, 200
  2. Measure convergence speed
  3. Visual quality comparison
  4. Recommend optimal iteration count per scenario
```

**Patterns to follow:**
- Use timeit for micro-benchmarks
- Create synthetic test videos (1080p, 30 fps, 10 frames)
- Report mean ± std deviation

**Test scenarios:**
- **Benchmark**: Temporal smoothing overhead on 10-frame video; report per-frame ms
- **Benchmark**: YOLO detection on sparse interval (every 5 frames); report FPS
- **Benchmark**: Poisson solver with iterations 50/100/200; compare time vs quality
- **Benchmark**: Full Phase 2 pipeline (temporal + tracking + poisson); total overhead
- **Recommendation**: For real-time (30 fps): which features to disable
- **Recommendation**: For quality (batch): optimal parameter tuning

**Verification:**
- Benchmark script reproducible on test hardware
- Performance guide published with tuning recommendations
- Overhead < 50% per Phase 2 feature (acceptable for video processing)

---

- [ ] **Unit 6: Phase 2 Documentation & Operational Guide**

**Goal:** Document Phase 2 features, configuration, troubleshooting; publish best practices.

**Requirements:** Phase2-G, Phase2-A through Phase2-F

**Dependencies:** Units 1-5

**Files:**
- Create: `docs/phase2_configuration_guide.md` (detailed config reference)
- Create: `docs/phase2_yolo_setup.md` (YOLO model setup and troubleshooting)
- Create: `docs/phase2_tuning_scenarios.md` (tuning examples: static/dynamic/complex)
- Create: `docs/phase2_performance_guide.md` (benchmarking results, optimization tips)
- Create: `examples/phase2_advanced_watermark.yaml` (example config)
- Modify: `README.md` (add Phase 2 section)
- Modify: `docs/config_reference.md` (expand with Phase 2 params)

**Approach:**
- Document each Phase 2 config parameter with range, default, effect
- Provide YOLO setup walkthrough (install ultralytics, download weights, verify)
- Publish tuning scenarios: static logo (feather sufficient), moving watermark (full Phase 2), complex background (adaptive temporal)
- Include troubleshooting (slow detection, flicker persists, memory issues)
- Example YAML configs for common scenarios

**Patterns to follow:**
- Use same structure as Phase 1 docs
- Include before/after examples (Phase 1 vs Phase 2 output quality)
- Clear instructions for non-technical users

**Test scenarios:**
- **Happy path**: User follows YOLO setup guide; model loads and detects
- **Happy path**: User applies tuning scenario for their watermark type; result improves
- **Error path**: User encounters "YOLO model not found"; troubleshooting section resolves
- **Troubleshooting**: Flicker persists; guide recommends increasing temporal_smooth_alpha
- **Troubleshooting**: Slow detection; guide recommends sparse_interval or YOLOv8n

**Verification:**
- Documentation complete and accurate
- All Phase 2 features documented with examples
- Troubleshooting covers common issues
- Example configs are functional

---

## System-Wide Impact

### Interaction Graph
- **Entry point:** `scripts/run_pipeline.py --use-adaptive-temporal-smoothing --use-poisson-blending --use-watermark-tracker`
- **Callbacks:** None (sequential pipeline with optional features)
- **Middleware:** Config flags gate Phase 2 features on/off
- **Observers:** Logging enhanced for Phase 2 metrics (flicker score, detection confidence, solver iterations)

### Error Propagation
- **Temporal smoothing fails** → Log warning, skip temporal smoothing, continue with Phase 1 output
- **YOLO model unavailable** → Log info, degrade to manual bboxes, continue
- **Poisson solver non-convergent** → Fall back to feather blending, continue
- **Checkpoint corrupted** → Log warning, start from scratch without resume

### State Lifecycle Risks
- **Checkpoint files:** Persist across runs; versioning needed if format changes (Phase 3)
- **YOLO model cache:** Downloaded to disk; may consume 100MB+ per model variant
- **Frame sequences:** Unchanged from Phase 1 (PNG temp files, cleaned if `keep_intermediate=False`)
- **Metadata:** CropRegion list + motion vectors stored in checkpoint; ensure serializable

### API Surface Parity
- CLI flags for Phase 2 features (e.g., `--temporal-smooth-alpha 0.3`)
- Config file parameters for all Phase 2 options
- No public API changes; all Phase 2 is config-driven

### Integration Coverage
- **End-to-end (Unit 2):** Temporal smoothing integrated into full pipeline
- **Cross-layer (Unit 3):** YOLO → Tracker → CropHandler (watermark region)
- **Cross-layer (Unit 4):** Checkpoint save/resume across preprocessing → postprocessing
- **Data consistency (Units 1-4):** All Phase 2 features produce valid pixel data [0, 255], same frame dimensions

### Unchanged Invariants
- Original video/mask files **never modified** (read-only)
- Frame extraction **still deterministic** (same frame_id, same order)
- Phase 1 output **still valid without Phase 2** (backward compatible)
- CropRegion serialization **unchanged** (Phase 2 adds checkpoint wrapping)

---

## Risks & Dependencies

| Risk | Mitigation | Phase |
|------|-----------|-------|
| **YOLO model unavailable** | Graceful degradation; tracker works with manual bboxes | 2 |
| **Temporal smoothing introduces flicker** | Tuning guide for alpha selection; adaptive mode available | 2 |
| **Poisson solver slow** | Iteration count configurable; feather fallback available | 2 |
| **Checkpoint file format breaks** | Version field in checkpoint; Phase 3 handles migration | 2→3 |
| **Performance overhead too high** | Benchmark study; disable features if needed | 2 |
| **YOLO licenses/redistribution** | Ultralytics YOLOv8 is open-source (AGPL); document licensing | 2 |

---

## Documentation / Operational Notes

**YOLO Setup:**
```bash
# Install ultralytics
pip install ultralytics

# Download model weights (auto on first use, or manual)
python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"

# Verify in config
yolo_model_path: ~/.local/share/ultralytics/yolov8n.pt
```

**Phase 2 Configuration Example:**
```yaml
# Base Phase 1 config
video_path: input.mp4
mask_path: watermark.json  # Moving watermark bbox

# Phase 2: Temporal Smoothing
temporal_smooth_alpha: 0.3  # Simple: 0.1-0.5
use_adaptive_temporal_smoothing: true  # Motion-aware
adaptive_motion_threshold: 0.05

# Phase 2: Poisson Blending
use_poisson_blending: true
poisson_max_iterations: 100
poisson_tolerance: 0.01

# Phase 2: Watermark Tracking
use_watermark_tracker: true
yolo_model_path: ~/.local/share/ultralytics/yolov8n.pt
yolo_confidence_threshold: 0.5
tracker_smoothing_factor: 0.3

# Phase 2: Checkpointing (for long videos)
use_checkpoints: true
```

**Monitoring & Validation:**
- Log temporal smoothing confidence (flicker metric per frame)
- Log YOLO detection confidence per frame
- Log Poisson solver iterations and convergence
- Checkpoint file size as proxy for long-video capability

**Known Limitations (Phase 2):**
- Single watermark region per frame (multiple regions in Phase 3)
- YOLO model size 50-300MB (not mobile-friendly; Phase 3 explores lightweight models)
- Poisson solver CPU-only (GPU in Phase 3)
- Temporal smoothing limited to adjacent frames (advanced optical flow in Phase 3)

---

## Sources & References

- **Origin document:** [docs/plans/2026-03-30-001-feat-watermark-removal-system-plan.md](docs/plans/2026-03-30-001-feat-watermark-removal-system-plan.md) — Phase 1 requirements and architecture
- **Phase 1 Implementation:** 266+ tests across all modules; all Phase 2 features integrated
- **Ultralytics YOLOv8:** https://docs.ultralytics.com/ — Model selection, API, licensing
- **Temporal Coherence:** Industry practice (e.g., Adobe Premiere motion-aware blending)
- **Poisson Blending:** Classic computer vision technique; Jacobi solver standard for iterative solutions

---

## Appendix: Phase 2 Integration Checklist

**Configuration:**
- [ ] Phase 2 config parameters documented in `config_reference.md`
- [ ] Example `phase2_*.yaml` configs created
- [ ] CLI flags for Phase 2 options implemented

**YOLO Setup:**
- [ ] `setup_yolo_model.py` script created
- [ ] Model download documented in `phase2_yolo_setup.md`
- [ ] Graceful degradation tested (model unavailable)

**Testing:**
- [ ] Unit 1: Configuration validation tests pass
- [ ] Unit 2: Temporal smoothing end-to-end tests pass
- [ ] Unit 3: YOLO tracking integration tests pass
- [ ] Unit 4: Checkpoint save/resume tests pass
- [ ] Unit 5: Performance benchmarks completed

**Documentation:**
- [ ] Phase 2 configuration guide published
- [ ] YOLO setup guide published
- [ ] Tuning scenarios guide published
- [ ] Performance guide published
- [ ] Troubleshooting guide published
- [ ] README updated with Phase 2 section

**Validation:**
- [ ] 5+ end-to-end test scenarios pass
- [ ] Performance overhead < 50% acceptable for video processing
- [ ] All Phase 1 features still work (backward compatible)

---

**Plan Status:** Ready for implementation.

**Recommended Start:** Unit 1 (config validation) → Unit 3 (YOLO setup) → Unit 2 (temporal testing) → Unit 4 (checkpoints) → Unit 5 (benchmarking) → Unit 6 (documentation).

