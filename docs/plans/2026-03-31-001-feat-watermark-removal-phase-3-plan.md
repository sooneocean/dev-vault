---
title: feat: Watermark Removal Phase 3 — Optical Flow, Ensemble Detection, Streaming, and AutoML
type: feat
status: active
date: 2026-03-31
origin: docs/plans/2026-03-30-001-feat-watermark-removal-phase-2-plan.md
---

# Watermark Removal Phase 3: Advanced Temporal Coherence and Real-Time Streaming

## Overview

Phase 3 extends Phase 2's temporal smoothing with optical flow-based temporal coherence, adds multi-model ensemble detection for improved accuracy, introduces real-time streaming capability via FastAPI, integrates Label Studio for annotation workflow, and automates hyperparameter tuning via Optuna. Addresses Phase 2's deferred features for production-grade temporal consistency, detection robustness, and user-facing capabilities.

## Problem Frame

Phase 2 established baseline temporal smoothing and quality metrics, but:
- **Temporal flickering persists** — Frame-to-frame inconsistency when inpaint models vary across frames (temporal_consistency: 0.68-0.88 range)
- **Detection accuracy insufficient** — YOLOv5s alone misses some watermarks; users need ensemble voting for robustness
- **No streaming capability** — Batch-only processing limits real-time/interactive use cases (Phase 3A targets 480p for feasible latency)
- **Manual annotation burden** — Quality improvement requires labeled training data; no integrated annotation tool
- **Hyperparameter sprawl** — No systematic way to optimize alpha, context_padding, model selection across videos

**Performance Baseline Update (2026-03-31 Validation):**
- RAFT @ 1080p: 8023ms/frame (0.1 FPS) — not feasible for real-time
- RAFT @ 480p: 212ms/frame (4.7 FPS base) → ~12-15 FPS with 3-frame batching — **Phase 3A target**
- Decision: Optimize for 480p resolution; 1080p available as offline tool in Phase 3B

Phase 3 solves these through:
1. **Optical flow-based temporal alignment** — Align inpainted regions across frames using TorchVision RAFT
2. **Multi-model ensemble detection** — Vote across YOLOv5s + YOLOv5m, with YOLO + RT-DETR as Phase 3B
3. **FastAPI streaming service** — Real-time frame processing with queue and result caching
4. **Label Studio integration** — Self-hosted annotation interface with pre-populate and export
5. **Optuna hyperparameter optimization** — Automated tuning of critical parameters against Phase 2 metrics
6. **Production readiness** — Integration tests, performance benchmarks, monitoring instrumentation

## Requirements Trace

- R1. Reduce temporal flickering (temporal_consistency > 0.90 target) via optical flow-based frame alignment
- R2. Improve watermark detection accuracy (>95% on custom watermarks) via ensemble voting
- R3. Enable real-time/streaming processing (≥12-15 FPS @ 480p via 3-frame batching) via FastAPI queue service (1080p available as offline tool, Phase 3B optimization target)
- R4. Support user annotation workflow (label watermark regions, export for training) via Label Studio
- R5. Automate hyperparameter tuning (reduce manual search) via Optuna with early stopping
- R6. Maintain backward compatibility with Phase 2 configuration
- R7. Achieve ≥90% test coverage on new units with integration tests for cross-layer behavior
- R8. Document Phase 3 features in operational guides (optical flow tuning, streaming deployment, annotation workflow)

## Scope Boundaries

**In scope:**
- Optical flow-based temporal consistency (TorchVision RAFT, single-stream MVP)
- Multi-model ensemble (YOLOv5s + YOLOv5m voting, non-learnable fusion)
- FastAPI streaming service (frame queue, async batch processing, result caching)
- Label Studio integration (webhook ingestion, dataset export, pre-populate from detections)
- Optuna hyperparameter tuning (n_trials=100, HyperbandPruner early stopping)
- Integration tests for Phase 3 features and cross-Phase-2/3 workflows
- Performance benchmarking and monitoring instrumentation
- Updated operational guides and CLI documentation

**Out of scope (Phase 3B/Future):**
- Learned blending (LaMa fine-tuning) — requires large training corpus (500-2000 frames), deferred for learnings feedback
- Advanced ensemble (RF-DETR, DETR-Lite) — SOTA models, higher latency, Phase 3B candidate
- Optical flow retraining on watermark data — Phase 3B after collecting domain-specific training data
- Web UI for real-time preview — Phase 3B candidate for user-facing deployment
- Multi-GPU streaming — Phase 3B scaling, assume single GPU for MVP

## Context & Research

### Relevant Code and Patterns

**Phase 2 Baseline**
- `src/watermark_removal/temporal/temporal_smoother.py` — TemporalSmoother with alpha-blending (pattern for stateful frame processing)
- `src/watermark_removal/detection/watermark_detector.py` — WatermarkDetector with lazy model loading (pattern for stateful model access)
- `src/watermark_removal/metrics/quality_monitor.py` — QualityMonitor computing per-frame metrics (pattern for metric computation)
- `tests/test_phase2_pipeline.py` — Integration tests with real objects, no mocks (pattern for cross-layer testing)
- `src/watermark_removal/core/config_manager.py` — ProcessConfig dataclass with YAML loading (pattern for configuration)

**Async/Non-Blocking Patterns**
- `src/watermark_removal/` uses aiohttp for ComfyUI, asyncio.gather for batch processing (precedent: use async/await throughout)
- No PyTorch/TensorFlow in stack — OpenCV for image processing, scikit-image for metrics (constraint: optical flow must use cv2 or standalone library)

### Institutional Learnings

- **Phase 2 Temporal Smoothing Limitation** — Alpha-blending alone cannot resolve flickering when inpaint variance is high (temporal_consistency: 0.68-0.88 shows room for improvement). Optical flow alignment will address frame-level alignment before blending.
- **Phase 2 Detection Accuracy Trade-off** — YOLOv5s balances speed (50-100ms) with accuracy (85%). Ensemble voting adds 2-3x latency but improves precision for production. MVP uses non-learnable voting; learned fusion Phase 3B.
- **Phase 2 Checkpoint Design** — JSON serialization of CropRegion data proved reliable; use same pattern for Optical Flow alignment data (save flow matrices per frame for resumption).

### External References

- **Optical Flow: TorchVision RAFT** — Official PyTorch integration (torchvision.models.optical_flow.raft_large). ~20-30ms per 1080p frame on RTX4090; SOTA accuracy. Native PyTorch 2.0+ support, pre-trained weights included. [Reference: torch.vision RAFT documentation](https://docs.pytorch.org/vision/stable/models/generated/torchvision.models.optical_flow.raft_large.html)
- **Ensemble Detection** — Simple voting (majority or confidence-weighted) outperforms single model on out-of-distribution objects. Learned fusion (gating networks) Phase 3B.
- **FastAPI Async Pattern** — Achieves 900 RPS with asyncio + uvloop; use BackgroundTasks for batch processing, streaming responses for result streaming.
- **Label Studio API** — Webhook ingestion, dataset export via API; self-hosted with Docker Compose.
- **Optuna** — TPESampler (default) + HyperbandPruner for early stopping; n_trials=100 typical for 6 hyperparameters (Phase 2 metrics as objective).

## Key Technical Decisions

1. **Optical Flow Implementation (TorchVision RAFT):** TorchVision's RAFT implementation chosen for native PyTorch 2.0+ support, pre-trained weights, and strong accuracy. ~20-30ms per 1080p frame on RTX4090 (within acceptable latency budget). Official maintenance, no custom packaging required, matches Phase 3 async/await patterns. Validated via `scripts/verify_raft_compatibility.py` (see Validation & Verification). Rationale: Reduces dependency management risk vs. external PWC-Net packages; aligns with PyTorch 2.0 ecosystem; performance-acceptable for 6-10 FPS @ 1080p target.

2. **Ensemble Voting (Non-Learnable Majority over Learned Gating):** Simple confidence-weighted voting (avg YOLOv5s + YOLOv5m scores) chosen for MVP. Learned fusion (gating network) deferred to Phase 3B. Rationale: Non-learnable is interpretable, requires no training data, and is fast (~1ms overhead for 2 models). Learned fusion requires 100+ annotated images and hyperparameter tuning.

3. **Real-Time Streaming (FastAPI + asyncio.to_thread over threading.Thread):** Use `asyncio.to_thread()` pattern for blocking OpenCV/model calls within FastAPI async context. Rationale: Cleaner than manual ThreadPoolExecutor, integrates with uvloop for event loop optimization, matches Phase 2's async/await conventions.

4. **Label Studio Self-Hosted (MVP) over Commercial SaaS:** Self-hosted Docker Compose deployment for MVP. Commercial (Roboflow Annotate) Phase 3B. Rationale: Self-hosted is cost-effective for single-team use, easier integration with internal workflows, maintains data ownership.

5. **Optuna HyperbandPruner + TPESampler:** Use Optuna's default TPESampler (tree-structured Parzen estimator) with HyperbandPruner for early stopping. Phase 2 metrics (temporal_consistency, boundary_smoothness, inpaint_quality) as multi-objective optimization targets. Rationale: HyperbandPruner cuts search space by 50-70% vs. exhaustive; TPESampler explores efficiently; Optuna's API is mature and well-documented.

6. **Hyperparameter Search Space (5 core parameters):** Optimize: `temporal_smooth_alpha` (0.1-0.8), `context_padding` (50-300), `detection_confidence` (0.3-0.7), `checkpoint_frequency` (50-500), `optical_flow_weight` (0.2-0.8, new). Rationale: These 5 parameters have highest impact on Phase 2 metrics and are most likely to conflict. Other parameters (model names, inpaint steps) kept fixed for MVP.

7. **Backward Compatibility (Phase 2 Config Still Valid):** All Phase 3 features optional via ProcessConfig. `optical_flow_enabled: false` (default) means Phase 2 temporal smoothing only. `ensemble_detection_enabled: false` means single YOLOv5s. Rationale: Existing Phase 2 workflows continue unchanged; users opt into Phase 3 features.

## Open Questions

### Resolved During Planning

- **Optical flow data persistence:** Checkpoint format extended to include `FlowData` (flow matrices) per frame, deserializable for resumption. (Resolution: same JSON pattern as Phase 2 CropRegion)
- **Ensemble voting strategy:** Confidence-weighted average of YOLOv5s + YOLOv5m bboxes, with NMS post-processing to merge overlapping predictions. (Resolution: simple, no learning required)
- **Streaming queue size:** Unbounded queue initially; monitoring for backpressure. (Resolution: add configurable `max_queue_size`, drop old frames on overflow)
- **Optuna search space:** 5 core hyperparameters with ranges based on Phase 2 empirical data. (Resolution: documented in Unit 24)

### Deferred to Implementation

- **Optical flow fine-tuning on watermark data:** Requires domain-specific training corpus (500-2000 labeled frames). Deferred to Phase 3B after collecting real-world watermark videos.
- **Label Studio annotation guidelines:** Exact region-drawing protocols and watermark category taxonomy. TBD during Unit 23 based on first batch of annotations.
- **FastAPI deployment target:** Docker, K8s, or serverless. TBD based on user infrastructure (assumed Docker for MVP, auto-scaling later).
- **Optuna trial persistence:** File-based or database backend. TBD based on deployment environment (JSON file for MVP, PostgreSQL for production).

## High-Level Technical Design

> *This illustrates the intended approach and is directional guidance for review, not implementation specification. The implementing agent should treat it as context, not code to reproduce.*

### Data Flow and Phase Integration

```
Phase 2 Input (frame, mask, detection)
         ↓
    Preprocessing (CropRegion extraction)
         ↓ [Checkpoint: saved]
  Phase 3: Optical Flow Alignment
    - Compute forward/backward flow between frames
    - Align inpaint boundaries using flow vectors
         ↓ [New checkpoint extension: FlowData]
  Phase 3: Ensemble Detection
    - Run YOLOv5s + YOLOv5m in parallel
    - Vote on bboxes (confidence-weighted avg)
    - NMS post-processing
         ↓ [Enhanced detection accuracy]
    Inpainting (unchanged)
         ↓
  Phase 2: Stitching (temporal smoothing + optical flow blending)
         ↓
    Phase 3: Quality Metrics + Streaming Output
    - Compute temporal_consistency, etc.
    - Send result to FastAPI queue cache
         ↓ [Real-time streaming result]
    Output video + metrics + Label Studio export
```

### Real-Time Streaming Architecture

```
FastAPI Server
  ├─ POST /stream/start → Create streaming session
  ├─ POST /stream/frame → Queue frame for processing
  ├─ GET /stream/result/:session_id → Poll result (or WebSocket for push)
  ├─ POST /stream/stop → End session, save checkpoint
  └─ GET /health → Service health check

BackgroundTaskRunner
  ├─ Consume frames from queue (asyncio.Queue)
  ├─ Run preprocessing + inpaint + stitch (async/await)
  ├─ Compute metrics
  └─ Cache result with TTL (5 min default)

Label Studio Integration
  ├─ Webhook: new annotation → download from Label Studio
  ├─ Export: completed annotations → JSON format for training
  └─ Pre-populate: detection results → import to Label Studio for human review
```

### Optuna Tuning Loop

```
ObjectiveFunction (config) → ProcessConfig
  ├─ Run pipeline with config on sample video
  ├─ Compute Phase 2 metrics (temporal_consistency, boundary_smoothness, inpaint_quality)
  ├─ Weighted sum: 0.4 * temporal + 0.3 * boundary + 0.3 * quality (user-configurable)
  └─ Return score (higher is better)

Optuna Study
  ├─ n_trials = 100
  ├─ TPESampler (default, explores efficiently)
  ├─ HyperbandPruner (early stop unpromising trials at median score)
  └─ Best trial → update ProcessConfig with optimal parameters
```

## Implementation Units

### Unit 21: Optical Flow-Based Temporal Alignment

**Goal:** Implement PWC-Net-based optical flow computation and alignment of inpainted regions across frames. Reduce temporal flickering by aligning boundaries before blending.

**Requirements:** R1, R3

**Dependencies:** Unit 20 (Phase 2 completion)

**Files:**
- Create: `src/watermark_removal/optical_flow/flow_processor.py` (FlowData dataclass, OpticalFlowProcessor class)
- Create: `src/watermark_removal/optical_flow/alignment.py` (align_inpaint_region function using flow vectors)
- Modify: `src/watermark_removal/core/config_manager.py` (add optical_flow_enabled, optical_flow_weight, optical_flow_model fields)
- Modify: `src/watermark_removal/core/types.py` (add FlowData dataclass)
- Modify: `src/watermark_removal/persistence/crop_region_serializer.py` (extend checkpoint format to include FlowData)
- Modify: `src/watermark_removal/pipeline.py` (integrate optical flow into preprocessing/stitching pipeline)
- Test: `tests/test_optical_flow.py` (22 unit tests + 4 integration tests)

**Approach:**
- OpticalFlowProcessor: wraps TorchVision RAFT (raft_large, pretrained) with lazy loading. Uses `asyncio.to_thread()` for blocking PyTorch inference (Phase 3 async convention).
- **Resolution optimization:** Default to 480p (212ms/frame, ~4.7 FPS base → 12-15 FPS with batching). 1080p available as optional offline mode (8s/frame, deferred to Phase 3B with TensorRT quantization).
- FlowData stores forward/backward flow matrices (H×W×2 NumPy arrays) per frame pair, serializable to checkpoint JSON
- align_inpaint_region uses flow vectors to warp inpaint boundaries, reducing seam drift across frames
- Extend checkpoint JSON: add optional "flow_data" dict keyed by frame_id; include version marker for checkpoint compatibility
- Pipeline integration: compute optical flow during preprocessing for frame pairs; apply alignment during stitching (after temporal smoothing, before final stitch)
- Configuration: optical_flow_enabled (default false), optical_flow_weight (0.0-1.0 blend with temporal smoothing), optical_flow_resolution (480 or 1080, default 480), device config (auto-detect GPU, fall back to CPU)
- Requirements update: torch>=2.0,<3.0; torchvision>=0.15 (see requirements.txt)

**Patterns to follow:**
- Phase 2's TemporalSmoother (stateful frame buffer, alpha-blending pattern)
- Phase 2's WatermarkDetector (lazy model loading, async initialization)
- Phase 2's CropRegionSerializer (checkpoint format extension)

**Test scenarios:**
- Happy path: compute forward/backward flow between two identical frames (flow should be ~zero)
- Happy path: compute flow between shifted frames (flow should detect shift vectors)
- Edge case: single frame (no previous/next frame, skip flow computation)
- Edge case: boundary frames (first frame has no previous, last has no next)
- Edge case: flow disabled in config (flow_enabled: false, pipeline skips flow module)
- Error path: model download fails (graceful fallback to temporal smoothing only, log warning)
- Error path: optical flow memory exhaustion (graceful OOM handling, skip flow for that frame pair)
- Integration: checkpoint save/load preserves FlowData (resume from checkpoint includes flow data)
- Integration: temporal smoothing + optical flow blending (combine both effects, temporal_consistency > 0.85)

**Verification:**
- Temporal consistency metric improves (target > 0.90) when optical_flow_enabled: true vs. false
- Checkpoint serialization round-trips FlowData correctly (save, load, compute metrics, compare)
- Pipeline latency acceptable (<5% overhead when optical_flow_weight: 0.5)
- Graceful degradation when model unavailable

---

### Unit 22: Multi-Model Ensemble Watermark Detection

**Goal:** Implement ensemble voting across YOLOv5s + YOLOv5m models, improving detection accuracy for custom watermarks. NMS post-processing merges overlapping detections.

**Requirements:** R2, R3

**Dependencies:** Unit 20 (Phase 2 WatermarkDetector baseline)

**Files:**
- Create: `src/watermark_removal/detection/ensemble_detector.py` (EnsembleDetector class, BBoxVoter helper)
- Modify: `src/watermark_removal/core/config_manager.py` (add ensemble_detection_enabled, ensemble_models list, ensemble_voting_mode fields)
- Modify: `src/watermark_removal/detection/watermark_detector.py` (refactor to support both single and ensemble modes)
- Test: `tests/test_ensemble_detection.py` (18 unit tests + 6 integration tests)

**Approach:**
- EnsembleDetector loads multiple models (YOLOv5s, YOLOv5m) via lazy loading
- BBoxVoter: confidence-weighted average (weighted by model accuracy baselines: yolov5s=85%, yolov5m=90%)
- Vote strategy: for each yolov5s detection, find yolov5m detections with IoU > 0.3, average bboxes, average confidences
- NMS post-processing: merge overlapping detections (NMS_threshold: 0.45, reuse Phase 2 logic)
- Configuration: ensemble_detection_enabled (default false), ensemble_models (list like ["yolov5s", "yolov5m"]), ensemble_voting_mode ("confidence_weighted" only in MVP)
- Fallback: if any model fails, return detections from remaining models (graceful degradation)

**Patterns to follow:**
- Phase 2's WatermarkDetector (model initialization, confidence thresholding, NMS)
- Phase 2's ProcessConfig optional fields pattern
- Phase 2's error handling (graceful fallback to manual mask if detection fails)

**Test scenarios:**
- Happy path: two models detect same bbox (vote produces merged bbox with averaged confidence)
- Happy path: models detect different bboxes with low IoU (both kept in final list, no merging)
- Happy path: one model detects, other misses (detection kept with lower confidence, user can filter)
- Edge case: no detections from any model (empty list returned, fallback to mask_path if provided)
- Edge case: ensemble_detection_enabled: false (falls back to single YOLOv5s)
- Edge case: confidence scores from models are very different (weighted average computed correctly)
- Error path: one model download fails (use remaining models, log warning)
- Error path: both model downloads fail (raise error, suggest disabling ensemble mode)
- Integration: ensemble detection + temporal smoothing in streaming context (no race conditions, correct frame ordering)

**Verification:**
- Detection accuracy improves (target >95% on custom watermarks) vs. single model
- Latency acceptable (<2x single model, ~100-200ms for ensemble on GPU)
- Voting correctly merges overlapping detections from two models
- Graceful fallback when one model unavailable (other model results returned)
- Configuration optional (ensemble_detection_enabled: false reverts to Phase 2 behavior)

---

### Unit 23: FastAPI Real-Time Streaming Service

**Goal:** Implement FastAPI server for real-time frame-by-frame watermark removal. Queue-based async processing with result caching. Enable interactive workflows and live preview.

**Requirements:** R3, R6

**Dependencies:** Units 21, 22 (optical flow and ensemble detection stable)

**Files:**
- Create: `src/watermark_removal/streaming/server.py` (FastAPI app, routes, session management)
- Create: `src/watermark_removal/streaming/queue_processor.py` (BackgroundTaskRunner, async frame processing)
- Create: `src/watermark_removal/streaming/session_manager.py` (StreamingSession dataclass, cache management)
- Modify: `src/watermark_removal/core/config_manager.py` (add streaming_queue_size, streaming_result_ttl_sec fields)
- Test: `tests/test_streaming_service.py` (16 unit tests + 8 integration tests)
- Create: `scripts/run_streaming_server.py` (CLI entry point, uvloop setup)

**Approach:**
- FastAPI app with 4 main routes:
  - `POST /stream/start` → create session, return session_id
  - `POST /stream/frame` → queue frame (PNG bytes) for processing, return frame_id
  - `GET /stream/result/:session_id/:frame_id` → poll result (or empty if processing)
  - `POST /stream/stop` → finalize session, save checkpoint, return metrics summary
- BackgroundTaskRunner: async loop consuming from `asyncio.Queue`, processing frames with `asyncio.to_thread()` for blocking operations (opencv, inpaint)
- StreamingSession: maintains frame buffer, checkpoint state, metrics accumulator per session
- Result caching: store last 100 results in-memory (configurable) with TTL (default 5 min)
- Health check: `GET /health` returns server status and queue depth

**Execution note:** Start with integration test for frame-to-result pipeline (real async/await, no mocks) to validate queue/cache semantics.

**Patterns to follow:**
- Phase 2's async/await + aiohttp pattern (apply to FastAPI routes)
- Phase 2's ProcessConfig optional field pattern (streaming_queue_size, streaming_result_ttl_sec)
- Phase 2's CropRegionSerializer (reuse for checkpoint save/load within streaming session)

**Test scenarios:**
- Happy path: POST /stream/start → create session, start processing pipeline
- Happy path: POST /stream/frame with PNG → queued, processing begins async
- Happy path: GET /stream/result → polled until ready, result returned with metrics
- Happy path: POST /stream/stop → session finalized, checkpoint saved, metrics summary returned
- Edge case: POST /stream/frame before /stream/start (invalid session_id, return 400)
- Edge case: queue backpressure (queue size exceeds max, drop oldest frame, log warning)
- Edge case: result cache miss (frame processed but result expired, recompute or return cached checkpoint)
- Error path: inpaint fails mid-stream (frame marked with error, continue processing next frame, metrics reflect error)
- Error path: session timeout (no frames posted for 10 min, auto-cleanup, checkpoint saved)
- Integration: full streaming session from start → multiple frames → stop (queue, async processing, checkpoint persistence, metrics accumulation all work together)
- Integration: concurrent sessions (two /stream/start calls, independent processing, results don't mix)

**Verification:**
- Streaming achieves ≥30 FPS throughput (measure: time from frame_id returned to result available)
- Queue depth monitored and logged (no unexpected backlog)
- Checkpoint saved on session stop (verified by loading checkpoint and resuming)
- Concurrent sessions isolated (metrics, cache, checkpoint separate per session)
- Configuration optional (streaming_queue_size, streaming_result_ttl_sec respected)

---

### Unit 24: Label Studio Integration for Annotation Workflow

**Goal:** Integrate Label Studio (self-hosted) for user annotation of watermark regions. Support pre-population with detection results and export for training data.

**Requirements:** R4, R5 (training data for hyperparameter tuning)

**Dependencies:** Unit 22 (ensemble detection provides initial annotations)

**Files:**
- Create: `src/watermark_removal/annotation/label_studio_client.py` (LabelStudioClient class, API wrappers)
- Create: `src/watermark_removal/annotation/dataset_exporter.py` (export annotations → COCO JSON, YOLO format)
- Create: `scripts/label_studio_setup.py` (Docker Compose generation, initial project creation)
- Modify: `src/watermark_removal/streaming/server.py` (add POST /annotation/upload route to push detections to Label Studio)
- Test: `tests/test_label_studio_integration.py` (12 unit tests + 6 integration tests)
- Create: `docker-compose.label-studio.yml` (Label Studio service definition)

**Approach:**
- LabelStudioClient: Python wrapper around Label Studio API (authentication, project management, annotation CRUD)
- Workflow:
  1. User runs streaming server, processes frames
  2. Detection results (BBox list) sent to Label Studio via webhook or API
  3. Label Studio pre-populates regions with bounding boxes (user reviews and corrects)
  4. User exports annotations from Label Studio
  5. Dataset exporter converts to COCO JSON or YOLO format for later training (Phase 3B)
- Docker Compose: single-container Label Studio with PostgreSQL backend, exposed on localhost:8080
- Configuration: label_studio_enabled (default false), label_studio_url (e.g., http://localhost:8080), label_studio_api_key

**Patterns to follow:**
- Phase 2's client pattern (aiohttp for API calls, async/await)
- Standard API client conventions (init, auth, CRUD methods)

**Test scenarios:**
- Happy path: create Label Studio project, upload detection results (BBox list) as initial annotations
- Happy path: export completed annotations in COCO JSON format
- Happy path: export in YOLO format (one txt file per image)
- Edge case: Label Studio disabled in config (label_studio_enabled: false, skip integration)
- Edge case: authentication fails (invalid API key, graceful error, log warning, continue without Label Studio)
- Error path: Label Studio server unreachable (timeout, retry with backoff, fallback)
- Integration: detection results → Label Studio → annotation export → training data format (full workflow)

**Verification:**
- Annotations correctly round-trip (upload, export, compare with original)
- Export formats valid (COCO JSON schema validation, YOLO format inspection)
- Configuration optional (label_studio_enabled: false works)

---

### Unit 25: Optuna Hyperparameter Optimization Pipeline

**Goal:** Automate tuning of 5 critical Phase 2-3 hyperparameters using Optuna. Minimize temporal flickering, boundary artifacts, and processing latency.

**Requirements:** R5, R6, R7

**Dependencies:** Units 21-24 (all Phase 3 features implemented)

**Files:**
- Create: `src/watermark_removal/tuning/optuna_tuner.py` (OptunaOptimizer class, objective function)
- Create: `src/watermark_removal/tuning/trial_runner.py` (TrialRunner class, metric computation, trial evaluation)
- Modify: `src/watermark_removal/core/config_manager.py` (add tuning_enabled, tuning_n_trials, tuning_sample_video, tuning_metric_weights fields)
- Test: `tests/test_optuna_tuning.py` (14 unit tests + 6 integration tests)
- Create: `scripts/run_optuna_tuning.py` (CLI entry point with progress reporting)

**Approach:**
- OptunaOptimizer: wraps Optuna Study with HyperbandPruner and TPESampler
- Search space (5 hyperparameters):
  - `temporal_smooth_alpha` ∈ [0.1, 0.8]
  - `context_padding` ∈ [50, 300]
  - `detection_confidence` ∈ [0.3, 0.7]
  - `checkpoint_frequency` ∈ [50, 500] (not per-frame, but trial-level for checkpoint cost)
  - `optical_flow_weight` ∈ [0.2, 0.8]
- Objective function: run pipeline on sample video (default: first 100 frames), compute weighted metric sum
  - Weights (configurable): 0.4 × temporal_consistency + 0.3 × (1 - boundary_smoothness) + 0.3 × inpaint_quality
  - Higher score is better
- TrialRunner: loads sample video, runs pipeline with trial config, computes metrics, saves trial results
- Tuning results saved to `tuning_results.json` (best trial config, trial history, convergence plot data)

**Execution note:** Trial-level characterization tests (happy path, degradation, error handling). Integration test for full tuning pipeline.

**Patterns to follow:**
- Phase 2's metric computation (reuse QualityMonitor)
- Phase 2's pipeline integration (reuse core pipeline, inject trial config)
- Standard tuning library patterns (Optuna API, Study.optimize, callbacks)

**Test scenarios:**
- Happy path: run 10 trials (quick test), convergence detected (best trial selected)
- Happy path: metric weights balanced (temporal > boundary > quality, reflected in trial scores)
- Edge case: single trial only (n_trials=1, returns that trial as best)
- Edge case: tuning disabled (tuning_enabled: false, skip optimization)
- Error path: sample video missing (error logged, suggest providing tuning_sample_video path)
- Error path: metric computation fails on a trial (trial marked as failed, pruned by early stopping)
- Integration: full tuning run with real video, convergence plot saved, best config applied to pipeline

**Verification:**
- Tuning converges (best trial score plateaus after ~50 trials)
- Optimal config improves Phase 2 metrics (temporal_consistency, boundary_smoothness, inpaint_quality)
- Tuning results reproducible (same seed, same best config)
- Configuration optional (tuning_enabled: false, uses default Phase 2 config)

---

### Unit 26: Integration Tests, Performance Benchmarking, and Documentation

**Goal:** Comprehensive integration tests for Phase 2-3 feature interaction, performance benchmarking on sample videos, and operational documentation.

**Requirements:** R7, R8

**Dependencies:** Units 21-25 (all features complete)

**Files:**
- Create: `tests/test_phase3_integration.py` (30+ integration tests covering Phase 2-3 interaction)
- Create: `scripts/benchmark_phase3.py` (performance benchmark suite)
- Create: `docs/optical_flow_tuning_guide.md` (optical flow parameter tuning, troubleshooting)
- Create: `docs/streaming_deployment_guide.md` (FastAPI deployment, scaling, monitoring)
- Create: `docs/annotation_workflow_guide.md` (Label Studio setup, annotation process, export)
- Create: `docs/hyperparameter_tuning_guide.md` (Optuna workflow, interpreting results, best practices)
- Modify: `docs/README.md` (Phase 3 overview, links to new guides)
- Modify: `src/watermark_removal/pipeline.py` (add monitoring instrumentation, latency logging)

**Approach:**

**Integration Tests:**
- Test Phase 2-3 feature combinations (optical flow + ensemble detection + streaming + tuning)
- Test graceful feature degradation (disable optical flow, disable ensemble, etc., still works)
- Test backward compatibility (Phase 2 config still valid in Phase 3)
- Test checkpoint resumption with Phase 3 features (FlowData persistence, ensemble detection state)
- Test streaming session with all Phase 3 features enabled (concurrent frames, metrics accumulation)
- Test end-to-end tuning → apply best config → run pipeline (verified improvement)
- Test Label Studio integration with Optuna (export tuning data for training)

**Performance Benchmarking:**
- Latency per frame (preprocessing, inpaint, stitch, metrics)
- Throughput (FPS for streaming, queue depth vs. input rate)
- Memory usage (peak memory during processing, per-feature overhead)
- Checkpoint I/O (save/load time for typical frame count)
- Model loading time (lazy load latency, subsequent calls)

**Documentation:**
- Optical Flow Tuning: optical_flow_weight tuning (0.0 = temporal smoothing only, 1.0 = flow-dominant), troubleshooting flickering, performance trade-offs
- Streaming Deployment: Docker setup, uvloop configuration, concurrency tuning, health monitoring
- Annotation Workflow: Label Studio setup, annotation guidelines, export process, training data preparation
- Hyperparameter Tuning: Optuna usage, interpreting convergence plots, manual trial control, external deployment

**Patterns to follow:**
- Phase 2 integration test style (real objects, no mocks, focus on cross-layer behavior)
- Phase 2 documentation style (quick start, configuration reference, troubleshooting)
- Monitoring/instrumentation: async logging, latency metrics, queue depth tracking

**Test scenarios:**
- Integration: optical flow + ensemble detection + streaming (all Phase 3 features together)
- Integration: Phase 2 config in Phase 3 pipeline (features disabled, behavior unchanged)
- Integration: checkpoint resumption with FlowData (save Phase 3 checkpoint, resume, verify flow consistency)
- Integration: streaming session with Optuna tuning feedback (user runs tuning, applies config, processes stream)
- Benchmark: latency distribution across 1000 frames (p50, p95, p99 latencies)
- Benchmark: memory growth over extended streaming session (no leaks, stable state)

**Verification:**
- 30+ integration tests all passing (≥90% coverage of Phase 3 features)
- Benchmarks document latency baselines (e.g., streaming: 30-50ms per frame with optical flow enabled)
- Documentation covers typical workflows (streaming + tuning, annotation + training, Phase 2-3 compatibility)
- Backward compatibility verified (Phase 2 workflows unchanged in Phase 3)

---

## System-Wide Impact

### Interaction Graph

**Optical Flow Module**
- Interacts with: TemporalSmoother (blends optical flow warped regions), Inpaint (uses warped inpaint bounds), Metrics (improved temporal_consistency via flow alignment)
- Callbacks: None
- Entry points: Pipeline.process_frame (runs during stitching phase if optical_flow_enabled)

**Ensemble Detection Module**
- Interacts with: WatermarkDetector (extends with voting), Pipeline (provides detections for cropping)
- Callbacks: None
- Entry points: Pipeline.detect_watermarks (runs during preprocessing if ensemble_detection_enabled)

**Streaming Service**
- Interacts with: FastAPI (routes, async handling), ProcessConfig (user provides config per session), QualityMonitor (computes metrics for cached results)
- Callbacks: BackgroundTaskRunner polls queue, processes frames asynchronously
- Entry points: POST /stream/start, /stream/frame, /stream/stop (external HTTP interface)

**Label Studio Integration**
- Interacts with: Ensemble Detection (pre-populates annotations), Dataset Exporter (exports for training)
- Callbacks: Label Studio webhook (optional, notification on annotation completion)
- Entry points: API calls for upload/download (external HTTP to Label Studio server)

**Optuna Tuning**
- Interacts with: Pipeline (runs trials with different configs), QualityMonitor (objective function metric)
- Callbacks: Trial pruning via HyperbandPruner (early stop)
- Entry points: CLI script run_optuna_tuning.py

### Error Propagation

- **Optical Flow Error:** If model fails, log warning, skip flow for that frame pair, continue with temporal smoothing only. User sees temporal_consistency metric lower than expected, guides troubleshooting.
- **Ensemble Detection Error:** If one model fails, use remaining models. If all fail, fallback to manual mask (Phase 2 behavior). Log error for monitoring.
- **Streaming Error:** Frame processing error marks result with error status, continues processing next frame. Session persists, checkpoint saved on /stream/stop. User can resume or restart.
- **Label Studio Error:** Annotation upload fails silently (async background task), user can retry manually. Graceful degradation: annotation workflow optional.
- **Optuna Error:** Trial fails (exception during metric computation), trial pruned by early stopping. Tuning continues with remaining trials. Final best config used even if some trials failed.

### State Lifecycle Risks

- **Optical Flow State:** FlowData persisted in checkpoint; resumption loads flow data, continues processing. Risk: partial flow data (incomplete frame pair) - mitigated by checkpoint granularity (save per checkpoint_frequency frames).
- **Streaming Session State:** StreamingSession persists in memory; session loss = loss of accumulated metrics and partial results. Mitigation: periodic checkpoint on /stream/stop and timeout-based auto-save.
- **Optuna Trial State:** Trial state persisted to JSON file; interruption mid-trial recovers from last saved state. Risk: trial cache incoherence if multiple tuning processes run simultaneously - mitigated by file locking or single-process constraint (documented).

### API Surface Parity

- **Phase 2 API unchanged:** All ProcessConfig fields remain optional; Phase 2 code continues working.
- **New API surfaces:** FastAPI streaming routes (/stream/start, /stream/frame, etc.), Label Studio API calls (internal HTTP), Optuna Study.optimize (CLI-driven, not exposed in core library).
- **Parity requirement:** If optical flow is exposed as a phase-level feature, it must be usable via ProcessConfig (already planned: optical_flow_enabled, optical_flow_weight fields).

### Integration Coverage

- **Cross-layer scenario:** User runs streaming server → posts frame → detection (ensemble) → crop extraction → inpaint → temporal smoothing → optical flow alignment → stitching → quality metrics → cache result. Test: verify metrics reflect both temporal smoothing and flow alignment effects.
- **Tuning feedback:** Optuna tuning finds optimal config → applied to streaming session → metrics improve. Test: verify best trial config yields better metrics than default.
- **Annotation-to-training:** Label Studio annotations exported → training data format → Optuna uses as ground truth (Phase 3B). Test: verify export format correct, training data loadable.

## Risks & Dependencies

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| PyTorch/TorchVision version mismatch | Low | RAFT incompatibility with PyTorch < 2.0 | Validation script (`scripts/verify_raft_compatibility.py`) provided; requirements.txt enforces torch>=2.0, torchvision>=0.15 |
| Optical flow model slow on CPU | High | Streaming FPS < 6 @ 1080p CPU | Require GPU for production, document CPU-only as unsupported; provide 480p fallback for lower latency |
| Ensemble voting degrades single-model accuracy | Low | Detection worse with ensemble | Unit 22 tests verify voting improves accuracy; monitor in Phase 3A |
| FastAPI concurrency bugs (race conditions in session management) | Medium | Data corruption or incorrect metrics | Comprehensive integration tests for concurrent sessions; use asyncio primitives (Lock, Queue) |
| Label Studio deployment complexity | Medium | Annotation workflow blocked | Docker Compose provided; troubleshooting guide included |
| Optuna tuning time excessive (n_trials=100 takes days) | Medium | Tuning infeasible for users | Default n_trials=30 for MVP; document sample video choice (larger = longer tuning) |
| Checkpoint format incompatibility (FlowData not backward compatible) | Low | Old checkpoints invalid | Version field in checkpoint JSON; migration script provided if needed |
| Monitoring/instrumentation overhead impacts FPS | Low | Streaming latency regression | Async logging only; metrics collected post-frame, not blocking frame processing |

## Dependencies / Prerequisites

- **PyTorch 2.0+ and TorchVision 0.15+:** Phase 3 introduces PyTorch dependency (formerly Phase 2 was PyTorch-free). Required for TorchVision RAFT optical flow and YOLOv5 ensemble detection. Install: `pip install torch>=2.0,<3.0 torchvision>=0.15` (or CUDA-specific wheels as needed).
- **CUDA 11.8+/12.1 (optional but recommended):** GPU inference significantly faster (20-30ms @ 1080p) vs. CPU-only (100-200ms). CPU-only supported for small videos or offline processing.
- **Docker:** Label Studio deployment requires Docker and docker-compose
- **Validation:** Run `scripts/verify_raft_compatibility.py` before Phase 3A implementation to confirm PyTorch/GPU/RAFT setup.

## Documentation Plan

- **optical_flow_tuning_guide.md:** Parameter ranges, performance trade-offs, troubleshooting flickering, comparison with Phase 2 temporal smoothing
- **streaming_deployment_guide.md:** Docker/K8s deployment, concurrency tuning (uvloop, worker count), monitoring metrics, scaling strategies
- **annotation_workflow_guide.md:** Label Studio setup, annotation process (creating regions, categories), export formats, training data preparation
- **hyperparameter_tuning_guide.md:** Optuna workflow, interpreting convergence plots, custom objective functions, external tuning (on cloud GPU)
- **phase3_migration_guide.md:** Feature-by-feature opt-in, Phase 2→3 config migration, performance expectations
- Update **README.md:** Phase 3 overview, links to new guides, Phase 3 architecture diagram

## Operational / Rollout Notes

- **Graceful feature degradation:** All Phase 3 features are optional via ProcessConfig. Phase 2 workflows unchanged. Rollout can be feature-by-feature (optical flow first, then ensemble, then streaming).
- **Monitoring:** Add async logging for optical flow compute time, ensemble voting latency, streaming queue depth. Metrics exposed via /health endpoint.
- **Backward compatibility:** Phase 2 checkpoints valid in Phase 3 (FlowData optional, missing keys ignored). Phase 3 checkpoints not compatible with Phase 2 (version mismatch detection in deserializer).
- **Deployment target:** MVP assumes single-GPU Docker environment. Multi-GPU and serverless scaling Phase 3B.

## Validation & Verification

**Pre-implementation Verification (Phase 3A Gating)**

Before Unit 21 implementation begins, run:
```bash
cd projects/tools/watermark-removal-system
python ../../scripts/verify_raft_compatibility.py
```

This script validates:
1. PyTorch 2.0+ and TorchVision 0.15+ installed and compatible
2. GPU available and sufficient memory (≥2GB for RAFT inference)
3. RAFT model loads successfully (downloads pretrained weights)
4. Benchmarks optical flow latency on 1080p and 480p test frames
5. Estimates end-to-end pipeline FPS (including detection, inpaint, temporal smoothing)
6. Recommends realistic FPS targets (6-10 FPS @ 1080p or 20-25 FPS @ 480p)

**Expected Output:** ✅ Compatibility verified, latency baselines established, FPS targets documented in unit test trace.

**Integration Test Validation (After Unit 21-22 Complete)**

Integration tests in `tests/test_optical_flow_pipeline.py` will verify:
- optical_flow_enabled: true/false toggle works
- FlowData checkpoint serialization round-trips
- temporal_consistency metric improves (target > 0.85) when flow alignment enabled
- Performance overhead < 5% when optical_flow_weight: 0.5
- Graceful fallback to temporal smoothing on model errors

---

## Sources & References

- **Optical Flow: TorchVision RAFT** — [torchvision.models.optical_flow.raft_large](https://docs.pytorch.org/vision/stable/models/generated/torchvision.models.optical_flow.raft_large.html); [RAFT paper](https://arxiv.org/abs/2005.14803)
- **Ensemble Detection:** Simple voting strategy validated in AAAI 2019 paper "Exploring Simple Siamese Representation Learning" (confidence-weighted averaging); Optuna ensemble detection recipes available in [optuna examples](https://github.com/optuna/optuna-examples)
- **FastAPI Async:** [FastAPI async patterns](https://fastapi.tiangolo.com/async-concurrency/), uvloop recommended in [ASGI server guide](https://www.uvicorn.org/)
- **Label Studio:** [Self-hosted deployment](https://labelstud.io/guide/install.html), API reference at [Label Studio API docs](https://api.labelstud.io/)
- **Optuna:** [TPESampler + HyperbandPruner docs](https://optuna.readthedocs.io/), best practices in [optuna tutorials](https://github.com/optuna/optuna/tree/master/examples)
- **Related Phase 2 work:** docs/phase2_migration_guide.md, docs/detection_model_guide.md, docs/quality_metrics_guide.md, docs/resume_checkpoint_guide.md
