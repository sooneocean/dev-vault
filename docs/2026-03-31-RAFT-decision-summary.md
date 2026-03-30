# TorchVision RAFT Decision Summary — Phase 3A Optical Flow

**Date:** 2026-03-31
**Decision:** TorchVision RAFT selected for Phase 3A optical flow-based temporal alignment
**Status:** ✅ Approved for Phase 3A implementation

---

## Executive Summary

**Selected:** TorchVision RAFT (`torchvision.models.optical_flow.raft_large`)

**Why:**
- Official PyTorch 2.0+ integration, pre-trained weights included
- ~20-30ms per 1080p frame on RTX4090 (within acceptable latency budget for 6-10 FPS target)
- No external package management risk (unlike PWC-Net retraining packages)
- Aligns with PyTorch 2.0 ecosystem and Phase 3 async/await patterns
- Extensively documented and maintained

**Alternative Rejected:** PWC-Net retraining package (no official PyPI package; external GitHub dependency management required)

---

## Decision Details

### Core Conflict Resolved

**Problem:** Phase 3 plan assumed "PWC-Net retraining version" as off-shelf package, but this package does not exist as an official PyPI release.

**Available PWC-Net Options:**
1. NVlabs official (PyTorch 0.2 era) — incompatible with PyTorch 2.0+
2. VT-VL Lab fork (`vt-vl-lab/pwc-net.pytorch`) — requires manual integration, CUDA/CuPy dependencies
3. Simon Niklaus reimplementation (`sniklaus/pytorch-pwc`) — same integration challenges

**Cost of Proceeding with PWC-Net:** 2-3 day research/integration cycle; non-zero risk of version conflicts.

**Alternative: TorchVision RAFT**
- Available: `pip install torchvision>=0.15`
- Requires: PyTorch 2.0+ (already mandated for YOLOv5 ensemble detection)
- Performance: Comparable or better than PWC-Net for watermark boundaries
- No additional integration burden

---

## Performance Baseline

**Validation Script:** `scripts/verify_raft_compatibility.py`

**Expected Results (RTX4090, 1080p):**
- RAFT inference: 20-30ms per frame
- Total pipeline (frame decode → flow → detection → inpaint → smoothing): ~330-580ms
- **Estimated achievable FPS: 6-10 FPS @ 1080p**
- **30 FPS target: NOT achievable** without model optimization (Phase 3B)

**Recommendation:** Update plan to target **6-10 FPS @ 1080p** or **20-25 FPS @ 480p**

---

## Impact on Phase 3 Plan

### Updated File: `docs/plans/2026-03-31-001-feat-watermark-removal-phase-3-plan.md`

**Changes Made:**
1. ✅ Unit 21 "Approach" section updated: PWC-Net → TorchVision RAFT
2. ✅ Key Technical Decision #1 revised with RAFT rationale
3. ✅ External References updated with RAFT documentation links
4. ✅ Dependencies section: torch>=2.0,<3.0 + torchvision>=0.15
5. ✅ Risks & Dependencies table: PWC-Net download risk → PyTorch version mismatch risk
6. ✅ Validation & Verification section added with pre-implementation gating script

**Files Modified:**
- `projects/tools/watermark-removal-system/requirements.txt` — added torch>=2.0 and torchvision>=0.15
- `scripts/verify_raft_compatibility.py` — created validation script (22KB)

---

## Phase 3A / 3B Reorganization (Recommended)

Current plan combines 6 units (Units 21-26) with 30 FPS streaming target, which is:
- **Unrealistic timeline:** 6-8 weeks estimated, likely 10-14 weeks actual
- **Complex scope:** optical flow + ensemble + streaming + annotation + tuning all in one release
- **Performance mismatch:** 30 FPS target contradicts realistic 6-10 FPS baseline

**Proposed Reorganization:**

### Phase 3A (8-10 weeks) — Core Delivery
- **Unit 21:** Optical flow (RAFT-based alignment)
- **Unit 22:** Ensemble detection (YOLOv5s + YOLOv5m voting)
- **Unit 23:** FastAPI streaming service (async queue, result caching)
- **Unit 27A:** Security hardening (auth, rate limiting, webhook HMAC)
- **Unit 26:** Integration tests + performance benchmarks

**Value at Phase 3A completion:**
- ✅ 50% temporal flicker reduction (temporal_consistency > 0.85)
- ✅ 95%+ watermark detection accuracy (ensemble voting)
- ✅ Real-time streaming API (6-10 FPS @ 1080p or 20-25 FPS @ 480p)
- ✅ Backward compatible with Phase 2
- ✅ Comprehensive integration test coverage

### Phase 3B (6-8 weeks, separate delivery) — Annotation & AutoML
- **Unit 24:** Label Studio integration (annotation workflow)
- **Unit 25:** Optuna hyperparameter tuning (n_trials=30-100)
- **Documentation:** Operational guides, migration guide

**Benefits of Split:**
- 3A ships sooner with proven core features
- 3B builds on 3A feedback (real watermark data, user feedback)
- Reduces per-release risk and complexity
- Allows user adoption of 3A features before 3B tuning data collection

---

## PyTorch 2.0+ Dependency

Phase 3 now explicitly requires PyTorch 2.0+. This changes Phase 2's "PyTorch-free" design.

**Rationale:**
- Unit 21 (optical flow): TorchVision RAFT requires PyTorch 2.0+
- Unit 22 (ensemble): YOLOv5 requires torch>=2.0 for modern GPU optimization
- No workaround available that avoids PyTorch

**Documentation Update:** CLAUDE.md decision log should note:
```
Phase 3 (2026-03-31): Adopted PyTorch 2.0+ as hard dependency.
Rationale: optical flow (TorchVision RAFT) + ensemble detection (YOLOv5) require torch>=2.0.
Phase 2 "PyTorch-free" constraint no longer applicable to Phase 3+.
```

---

## Pre-Implementation Checklist

Before Unit 21 implementation begins:

- [ ] Run `scripts/verify_raft_compatibility.py` on target GPU
  - Confirms PyTorch 2.0+ and TorchVision 0.15+ installed
  - Validates RAFT model loading and inference latency
  - Establishes performance baseline
  - **Gate:** ✅ Compatible and latency acceptable → proceed to implementation
  - **Gate:** ❌ Incompatible or latency > 50ms @ 1080p → escalate, defer Phase 3A

- [ ] Update `requirements.txt` with torch>=2.0,<3.0 and torchvision>=0.15
  - Pin to specific CUDA version wheels if using GPU (cu118, cu121, etc.)

- [ ] Verify Phase 3 plan updated with RAFT decision
  - Unit 21 approach revised
  - Key Technical Decision #1 updated
  - Validation & Verification section included

- [ ] Confirm Phase 3A/3B reorganization approved
  - Unit 21-23 + 27A + 26 → Phase 3A (core 8-10 weeks)
  - Unit 24-25 → Phase 3B (annotation + tuning 6-8 weeks, separate release)

---

## Risk Assessment

| Risk | Severity | Mitigation |
|------|----------|------------|
| RAFT slower than expected on specific GPU | Low | Validation script provides real latency; recommend RTX4090 or better for 1080p |
| PyTorch 2.0 incompatibility with legacy CUDA | Low | requires.txt specifies CUDA wheels; document CUDA 11.8+/12.1 support |
| 6-10 FPS target feels slow to users | Medium | Communicate realistic baseline; Phase 3B includes optimization and multi-GPU scaling |
| Phase 3A → 3B split feels incomplete | Low | Phase 3A alone delivers core value (flicker reduction + streaming); tuning Phase 3B is enhancement |

---

## Next Steps

1. **Run Validation Script** (immediately, before implementation sprint)
   ```bash
   python scripts/verify_raft_compatibility.py
   ```
   Expected: ✅ RAFT model loads, 1080p latency 20-30ms, estimated FPS 6-10

2. **Implementation Begins** (upon validation success)
   - Unit 21: OpticalFlowProcessor + FlowData serialization
   - Unit 22: EnsembleDetector + BBoxVoter (parallel with Unit 21)
   - Unit 23: FastAPI streaming service

3. **Security Review** (Unit 23-24 boundary)
   - FastAPI routes require authentication (Bearer token or API key)
   - Streaming queue needs backpressure handling (max_queue_size with frame dropping)
   - Webhook validation (HMAC signatures, rate limiting)

4. **Phase 3A Release** (estimate: 8-10 weeks from start)
   - Core optical flow + ensemble + streaming working
   - 30+ integration tests passing
   - Performance baselines documented

5. **Phase 3B Planning** (after Phase 3A completion)
   - Collect real watermark videos and user feedback
   - Label Studio annotation workflow
   - Optuna tuning with user data

---

## Decision Authority & Sign-Off

**Decision Made By:** Claude + user review (2026-03-31)
**Approved For:** Phase 3A implementation
**Timeline:** 8-10 weeks to Phase 3A completion
**Contingency:** If RAFT latency > 50ms @ 1080p, escalate and reconsider PWC-Net integration

---

## References

- **TorchVision RAFT Docs:** https://docs.pytorch.org/vision/stable/models/generated/torchvision.models.optical_flow.raft_large.html
- **RAFT Paper:** https://arxiv.org/abs/2005.14803
- **Validation Script:** `scripts/verify_raft_compatibility.py`
- **Phase 3 Plan:** `docs/plans/2026-03-31-001-feat-watermark-removal-phase-3-plan.md`
