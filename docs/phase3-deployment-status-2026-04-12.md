---
title: "Watermark Phase 3 Deployment Validation Report — 2026-04-12"
type: resource
subtype: learning
status: active
created: "2026-04-12"
updated: "2026-04-12"
domain: project-specific
summary: "Phase 3 deployment validation identified critical issues in optical flow, optuna, and streaming components. Estimated 17-26 failing tests across 5+ modules. System-wide test run causes access violations in RAFT model loading."
---

# Watermark Phase 3 Deployment Validation — Status Report

**Date**: 2026-04-12
**Status**: 🔴 **BLOCKED — Critical Issues Found**
**Validation Scope**: Integration tests, performance benchmarks, documentation

---

## Executive Summary

Phase 3 implementation is **not production-ready** for deployment. Validation identified:
- **676 tests passing** ✅
- **17-26 tests failing** ❌
- **9+ errors during collection** ❌
- **System crash on full test run** (RAFT model access violation)

**Root Cause**: Phase 3 components (optical_flow, optuna, streaming_service, inpaint_executor) have implementation bugs. Issues span multiple layers: async/await, context managers, module imports, algorithm correctness.

---

## Critical Issues Discovered

### 1. Optical Flow (RAFT) — SEVERITY: CRITICAL

**Problem**:
- `with self.model.eval():` syntax error — `eval()` is not a context manager (FIXED in this session)
- Missing `torch` import in `_compute_flow_on_device()` (FIXED in this session)
- Algorithm produces incorrect results: identical frames return ~0.3 flow instead of near-zero
- RAFT model loading causes access violation on Windows (`torch.nn.modules.module.py:2496 in _load_from_state_dict`)

**Location**: `src/watermark_removal/optical_flow/flow_processor.py:224-245`

**Tests Failing** (2):
- `test_optical_flow.py::TestOpticalFlowComputation::test_compute_flow_identical_frames`
- `test_optical_flow.py::TestOpticalFlowComputation::test_compute_flow_shifted_frames`

**Fixes Applied This Session**:
```python
# Before (BROKEN):
def _compute_flow_on_device(self, img1, img2):
    with self.model.eval():  # ❌ Not a context manager
        flow_list = self.model(img1, img2)

# After (PARTIALLY FIXED):
def _compute_flow_on_device(self, img1, img2):
    import torch  # ✅ Added missing import
    self.model.eval()
    with torch.no_grad():  # ✅ Correct context
        flow_list = self.model(img1, img2)
```

**Remaining Issue**: Algorithm correctness — identical frames should produce near-zero flow but return ~0.3. Suggests:
- RAFT model not properly initialized or in eval mode
- Normalization/preprocessing bug
- Test expectation incorrect (unlikely)

**Recommendation**: Deep code review of RAFT integration and window preprocessing.

---

### 2. Optuna Integration — SEVERITY: HIGH

**Problem**: 5+ test failures in optuna integration tests. No detailed error captured this session (tests fail early due to upstream optical_flow issues).

**Location**: `tests/test_optuna_integration.py`

**Tests Failing** (5):
- `test_full_optimization_pipeline`
- `test_optimization_respects_n_trials`
- `test_optimization_finds_best_trial`
- `test_metric_reporting_and_pruning`
- `test_graceful_error_handling_in_trial`

**Estimated Root Cause**: Upstream dependency on watermark_removal modules that fail to import (projects.tools missing, optical_flow load errors).

**Recommendation**: Defer investigation until optical_flow is fixed.

---

### 3. Streaming Service (FastAPI) — SEVERITY: HIGH

**Problem**: 9+ test errors + 3 failures. FastAPI on_event deprecation, async context management issues.

**Location**: `src/watermark_removal/streaming/server.py:89-95`

**Tests Failing/Erroring** (12):
- `test_session_creation`
- `test_session_config_isolation`
- `test_queue_full`
- `test_health_check` (ERROR)
- `test_stream_start` (ERROR)
- `test_stream_start_with_config` (ERROR)
- `test_stream_frame_invalid_session` (ERROR)
- `test_stream_frame_valid_session` (ERROR)
- `test_stream_result_not_found` (ERROR)
- `test_stream_stop` (ERROR)
- `test_full_streaming_pipeline` (ERROR)
- `test_concurrent_sessions_isolated` (ERROR)

**Known Issues**:
```python
@app.on_event("startup")  # ❌ Deprecated in FastAPI 0.109+
@app.on_event("shutdown")  # ❌ Deprecated in FastAPI 0.109+
```

**Recommendation**: Migrate to lifespan context managers (FastAPI modern pattern).

---

### 4. Inpaint Executor — SEVERITY: MEDIUM

**Problem**: 5+ test failures. Module import errors (projects.tools missing).

**Tests Failing** (5):
- `test_inpaint_executor_inpaint_single_happy_path`
- `test_inpaint_executor_inpaint_batch_happy_path`
- `test_inpaint_executor_batch_with_batch_size`
- `test_inpaint_executor_comfyui_timeout`
- `test_inpaint_executor_comfyui_connection_error` / `test_inpaint_executor_no_output_file`

**Root Cause**: Missing `projects.tools` module (import error during test collection).

**Recommendation**: Audit test fixtures and conftest.py for stale imports.

---

### 5. Mask Loader — SEVERITY: LOW

**Problem**: 1 test failure (test passes when run in isolation, suggesting state pollution or resource contention).

**Location**: `tests/test_mask_loader.py`

**Tests Failing** (1):
- `test_mask_loader_image_loading`

**Recommendation**: Low priority; may resolve after fixing Phase 3 dependencies.

---

## System-Wide Test Stability

**Finding**: Running full test suite (`pytest tests/ -q`) causes **Windows fatal exception: access violation** in RAFT model loading.

**Error Stack**:
```
File "torchvision\models\optical_flow\raft.py", line 834 in _raft
File "torchvision\models\optical_flow\raft.py", line 865 in raft_large
File "watermark_removal\optical_flow\flow_processor.py", line 59 in _lazy_load_model
```

**Implication**:
- RAFT model loading is not thread-safe on Windows
- Concurrent test execution may trigger race conditions
- Model may need explicit cleanup between tests (e.g., `torch.cuda.empty_cache()` or model destruction)

**Recommendation**:
1. Run optical_flow tests serially: `pytest tests/test_optical_flow.py -x --forceExit`
2. Add model cleanup fixture:
```python
@pytest.fixture(autouse=True)
def cleanup_torch():
    yield
    import gc; gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
```

---

## Performance Benchmarks — INCOMPLETE

Could not validate Phase 3 performance targets due to test failures:
- ❌ RAFT @ 480p: 212ms/frame (4.7 FPS base) — not measured
- ❌ Ensemble detection latency — not measured
- ❌ Streaming service: 12-15 FPS @ 480p — not measured

**Action**: Deferred until optical_flow stability confirmed.

---

## Documentation Status — INCOMPLETE

Could not validate operational guides and CLI documentation. Requires:
- [ ] ARCHITECTURE.md updated for Phase 3 features
- [ ] CLI commands documented (optical flow tuning, streaming deployment)
- [ ] Monitoring instrumentation verified
- [ ] Deployment runbooks created

---

## Remediation Roadmap

### Priority 1: Optical Flow (RAFT)
1. **Debug RAFT model loading** — add verbose logging, identify Windows CUDA/CPU init issue
2. **Verify algorithm correctness** — test with known ground-truth optical flow inputs
3. **Add thread-safety** — ensure lazy loading is serialized, add model cleanup between tests
4. **Retest**: `pytest tests/test_optical_flow.py -v`

### Priority 2: Inpaint Executor + Optuna
1. **Fix module imports** — audit conftest.py and test fixtures for stale projects.tools references
2. **Retest**: `pytest tests/test_inpaint_executor.py tests/test_optuna_integration.py -v`

### Priority 3: Streaming Service
1. **Migrate FastAPI to modern lifespan API** — replace `@app.on_event()` with lifespan context managers
2. **Verify async test setup** — ensure pytest-asyncio is correctly configured
3. **Retest**: `pytest tests/test_streaming_service.py -v`

### Priority 4: System Integration
1. **Run full test suite** (after P1-P3 fixes)
2. **Measure performance benchmarks**
3. **Document Phase 3 operational guides**
4. **Create deployment validation checklist**

---

## Fixes Applied This Session

✅ **Fixed**:
- Optical flow context manager syntax error (line 238)
- Optical flow missing torch import (line 225)

⚠️ **Partial**:
- Optical flow algorithm still produces incorrect results (identical frames)

📝 **Discovered but Deferred**:
- RAFT model loading thread safety issue
- FastAPI on_event deprecation
- Module import errors (projects.tools)
- Async/await context management issues

---

## Conclusion

**Phase 3 is not ready for production deployment.** Estimated remediation effort:
- **Code fixes**: 4-6 hours (optical flow, streaming, imports)
- **Testing & validation**: 2-3 hours
- **Documentation**: 1-2 hours
- **Total**: 7-11 hours for production-ready state

Recommend:
1. Assign Phase 3 implementation issues to original development team
2. Create focused remediation tasks for P1-P3 issues
3. Schedule full integration testing after fixes
4. Review deployment checklist before production rollout

---

**Report Generated**: 2026-04-12
**Validation Performed By**: Claude Code
**Status**: 🔴 BLOCKED — Awaiting Phase 3 remediation
