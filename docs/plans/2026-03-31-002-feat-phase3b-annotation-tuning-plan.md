---
name: Phase 3B — Label Studio Annotation + Optuna Tuning
description: Annotation workflow (Unit 24) + ensemble hyperparameter tuning (Unit 25) for watermark removal system
type: feat
status: active
timeline: 6-8 weeks (2 units, parallel execution after Phase 3A)
deepened: 2026-03-31
---

# Phase 3B: Label Studio Annotation Integration + Optuna Hyperparameter Tuning

**Date:** 2026-03-31
**Timeline:** 6-8 weeks
**Units:** 24 (Label Studio), 25 (Optuna)
**Building on:** Phase 3A (optical flow, ensemble detection, streaming service)

---

## Executive Summary

Phase 3B enables real-world dataset annotation and automated ensemble optimization. Unit 24 integrates Label Studio for annotation workflows where streaming detections are uploaded as pre-annotations, reviewed by humans, and exported as training data. Unit 25 uses Optuna to automatically tune ensemble voting parameters (model weights, confidence/IoU/NMS thresholds) on validation data, improving mAP 5-15% over baseline with 16-32 GPU hours.

**Delivered in Phase 3B:**
- Label Studio client (LabelStudioClient, dataset exporters, streaming integration)
- Optuna tuning framework (objective function, sampler/pruner configuration, SQLite persistence)
- Checkpoint v1.3 (annotation metadata, tuning results)
- 24-28 unit tests + 6-12 integration tests per unit
- Self-hosted Docker MVP deployment guide

**Key Design Decisions:**
- Async/await throughout (mirrors Phase 3A patterns)
- Feature flags disabled by default (label_studio_enabled, optuna_enabled)
- Validation-only tuning (no model retraining; voting parameters only)
- In-memory annotation state → Redis migration path for distributed
- Checkpoint versioning v1.3 (backward-compatible with v1.0/1.2)

---

## High-Level Design

### Unit 24: Label Studio Annotation Workflow

**Workflow:**
```
Streaming Pipeline (Phase 3A)
    ↓ (detections with confidence)
Label Studio Upload (new /annotation/upload route)
    ↓ (pre-annotations shown to human)
Human Review in Label Studio UI
    ↓ (corrections/acceptance)
Export Annotations (COCO JSON or YOLO format)
    ↓ (training-ready data)
Training Data Pipeline (Unit 25, Phase 4)
```

**Key Responsibility:**
- Convert ensemble detector BBox (pixel coordinates) → Label Studio prediction format (percentage coordinates)
- Upload to Label Studio as pre-annotations (suggestions for human review)
- Export annotations in COCO JSON or YOLO format
- Track task IDs in checkpoint for session resumption
- Graceful degradation if Label Studio unavailable

### Unit 25: Optuna Hyperparameter Tuning

**Workflow:**
```
Pretrained Ensemble Detector (Phase 3A)
    ↓
Optuna Study (suggest hyperparameters)
    ↓
Trial Evaluation (inference on val set, compute mAP)
    ↓ x150-200 trials
Best Parameters (5-15% mAP improvement)
    ↓
Save to Config File (reproducible)
```

**Search Space:**
- 3 model weights (YOLOv5s, m, l): confidence-weighted voting
- 3 post-processing thresholds (confidence, IoU, NMS)
- 1 data augmentation intensity
- **Total: 6-8 hyperparameters, 150-200 trials, TPESampler + HyperbandPruner**

**Key Responsibility:**
- Define objective function (ensemble inference → mAP evaluation)
- Configure sampler (TPESampler multivariate) and pruner (HyperbandPruner)
- Run optimization loop, checkpoint to SQLite
- Extract best params, validate improvement over baseline
- Graceful error handling (model failures, CUDA OOM, trial timeouts)

---

## System-Wide Integration

### Phase 3A → Phase 3B Data Flow

**Phase 3A (Streaming):**
- FastAPI server processes frames
- Ensemble detector (Unit 22) generates BBox predictions per frame
- Session manager caches results

**Phase 3B Unit 24 (Annotation):**
- New route `/annotation/upload` accepts frame_id + detections
- Async background task converts BBox → Label Studio format
- Uploads as predictions to Label Studio project
- Tracks label_studio_task_id in checkpoint
- Waits for human annotations (optional timeout)

**Phase 3B Unit 25 (Tuning):**
- Loads Phase 3A pretrained models
- Loads Unit 24 exported annotations (COCO JSON) as ground truth
- Runs Optuna trials (no model training; voting params only)
- Returns best params for ensemble voting

**Phase 4 (Training, Future):**
- Use annotated data from Unit 24 to fine-tune YOLOv5 models
- Use optimized ensemble params from Unit 25 as baseline

---

## Implementation Units

### Unit 24: Label Studio Annotation Integration

#### Goal
Enable annotation workflow where ensemble detector outputs are uploaded to Label Studio as pre-annotations, reviewed by humans, exported as training data.

#### Files to Create

**Core Implementation:**
- `src/watermark_removal/labeling/label_studio_client.py` (280–320 LOC)
  - `LabelStudioClient` class (async wrapper around Label Studio SDK)
  - Methods: `create_project()`, `upload_tasks()`, `create_predictions()`, `get_annotations()`, `export_coco()`, `export_yolo()`
  - Error handling: graceful degradation on API timeout/auth failure
  - Retry logic with exponential backoff

- `src/watermark_removal/labeling/dataset_exporter.py` (200–250 LOC)
  - `CocoExporter` class (Label Studio JSON → COCO format)
  - `YoloExporter` class (Label Studio JSON → YOLO format)
  - Utility functions: `bbox_pixel_to_percentage()`, `bbox_percentage_to_pixel()`
  - Validation: ensure exported coordinates are valid

- `src/watermark_removal/labeling/label_studio_setup.py` (150–180 LOC)
  - `generate_docker_compose()` — Docker Compose YAML for self-hosted Label Studio
  - `initialize_project()` — Create Label Studio project with label config (watermark, logo, text, subtitle, other)
  - `setup_api_key()` — Store API key securely (env var or config file)

- `src/watermark_removal/labeling/__init__.py` (module exports)

**Streaming Server Integration:**
- `src/watermark_removal/streaming/server.py` (modifications)
  - New route: `POST /annotation/upload`
  - Parameters: session_id, frame_id, detections (list[BBox]), label_studio_config (dict)
  - Returns: task_id in Label Studio
  - Implementation: async background task, error handling

**Type System Updates:**
- `src/watermark_removal/core/types.py` (modifications)
  - Add to ProcessConfig:
    ```python
    label_studio_enabled: bool = False
    label_studio_url: str = "http://localhost:8080"
    label_studio_api_key: str | None = None
    label_studio_project_id: int | None = None
    label_studio_wait_timeout_sec: float = 3600.0
    ```
  - New dataclass: `AnnotationTask`
    ```python
    @dataclass
    class AnnotationTask:
        frame_id: int
        timestamp_ms: float
        image_path: str
        detections: list[BBox]
        label_studio_task_id: int | None = None
        annotation_complete: bool = False
        annotation_export_path: str | None = None
    ```

**Checkpoint Persistence:**
- `src/watermark_removal/persistence/crop_serializer.py` (modifications)
  - Extend checkpoint version to "1.3"
  - Add `annotation_tasks` dict to checkpoint JSON
  - Backward-compatible deserialization (v1.0, v1.2 → v1.3)

#### Files to Create (Tests)
- `tests/test_label_studio_integration.py` (550–700 LOC, 18–24 test cases)
  - **TestLabelStudioClient** (8 tests)
    - `test_auth_valid_api_key()` — Authentication with valid token
    - `test_auth_invalid_api_key()` — Reject invalid token
    - `test_create_project()` — Create project with label config
    - `test_upload_tasks()` — Batch upload frames as tasks
    - `test_create_predictions()` — Upload detections as pre-annotations
    - `test_get_annotations()` — Retrieve human annotations
    - `test_export_coco()` — Export in COCO JSON format
    - `test_export_yolo()` — Export in YOLO format

  - **TestCoordinateConversion** (4 tests)
    - `test_pixel_to_percentage()` — BBox (100, 150, 200, 80) in 1920x1080 → Label Studio format
    - `test_percentage_to_pixel()` — Reverse conversion
    - `test_round_trip()` — pixel → percentage → pixel preserves value
    - `test_edge_cases()` — corners, boundaries, zero coordinates

  - **TestDatasetExporter** (4 tests)
    - `test_coco_export_structure()` — Valid COCO JSON (images, annotations, categories)
    - `test_yolo_export_format()` — Normalized coordinates (0–1), one file per image
    - `test_multiclass_export()` — Multiple label categories
    - `test_empty_annotations()` — Frames with no detections

  - **TestStreamingIntegration** (4 tests)
    - `test_annotation_upload_route()` — POST /annotation/upload accepted
    - `test_annotation_disabled()` — label_studio_enabled=False → no API calls
    - `test_auth_failure_graceful()` — Label Studio API error → warning logged, streaming continues
    - `test_session_resumption()` — Checkpoint contains task_ids → resume with annotation state

  - **TestErrorHandling** (2 tests)
    - `test_label_studio_timeout()` — API timeout → graceful degradation
    - `test_invalid_bbox()` — Malformed BBox → validation error caught

#### Patterns to Follow
- Async patterns from `OpticalFlowProcessor` (lazy loading, dependency injection)
- Error handling from `BackgroundTaskRunner` (graceful degradation, logging)
- State tracking from `SessionManager` (TTL-based cleanup, activity timestamps)

#### Execution Note
- Implement LabelStudioClient first (unit testable with mocked API)
- Implement exporters second (coordinate conversion critical)
- Integrate streaming server last (/annotation/upload route)

#### Test Scenarios

| Scenario | Input | Expected Output | Coverage |
|----------|-------|-----------------|----------|
| **Happy path** | Ensemble detections | Uploaded to Label Studio; task_id returned | ✓ |
| **Coordinate conversion** | BBox (100, 150, 200, 80) in 1920x1080 | Percentage (5.21, 13.89, 10.42, 7.41) | ✓ |
| **Pre-annotation** | Detections as predictions | Label Studio shows boxes for human review | ✓ |
| **Export COCO** | Annotated tasks | Valid COCO JSON (images, annotations, categories) | ✓ |
| **Export YOLO** | Annotated tasks | Text files with normalized coordinates | ✓ |
| **Auth failure** | Invalid API key | Request rejected, logging warning | ✓ |
| **Server timeout** | API delay >5s | Graceful degradation, streaming continues | ✓ |
| **Disabled annotation** | label_studio_enabled=False | No API calls, zero overhead | ✓ |
| **Session resumption** | Checkpoint with task_ids | Load existing task state, resume annotation | ✓ |
| **Concurrent uploads** | Multiple frame_ids | Queued uploads, no race conditions | ✓ |
| **Frame sampling** | Every 10th frame | Reduced Label Studio load, temporal interpolation | ✓ |
| **Large video** | 10,000 frames | Batch exports, memory-efficient | ✓ |

#### Verification Criteria
- ✓ Coordinate conversion pixel ↔ percentage numerically correct (±0.01%)
- ✓ Pre-annotations uploaded and queryable via Label Studio API
- ✓ Exported COCO JSON valid (verified with YOLOv5 training pipeline)
- ✓ Exported YOLO format valid (verified with YOLOv5 training pipeline)
- ✓ Graceful degradation when Label Studio unavailable (streaming unaffected)
- ✓ Session resumption preserves annotation task IDs (checkpoint v1.3)
- ✓ Self-hosted Docker deployment documented and tested
- ✓ Frame sampling (configurable) reduces API load while preserving signal
- ✓ Checkpoint serialization backward-compatible (v1.0/1.2 → v1.3)
- ✓ ≥90% test coverage

---

### Unit 25: Optuna Hyperparameter Tuning

#### Goal
Automatically optimize ensemble voting parameters (model weights, confidence/IoU/NMS thresholds) on validation dataset, achieving 5–15% mAP improvement over baseline.

#### Files to Create

**Core Implementation:**
- `src/watermark_removal/tuning/optuna_optimizer.py` (280–350 LOC)
  - `OptunaTuner` class
    - `__init__(storage="sqlite:///optuna.db", study_name="watermark_ensemble_tuning")`
    - `create_study(direction="maximize", sampler=TPESampler(...), pruner=HyperbandPruner(...))`
    - `objective(trial: optuna.Trial) -> float` — ensemble inference on val set, return mAP
    - `optimize(n_trials=150) -> dict` — run optimization, return best_params
    - `get_best_params() -> dict` — extract and format best hyperparameters
  - Graceful error handling for model failures, CUDA OOM, trial timeouts

- `src/watermark_removal/tuning/tuning_config.py` (100–150 LOC)
  - `TuningConfig` dataclass
    ```python
    @dataclass
    class TuningConfig:
        n_trials: int = 150
        sampler: str = "tpe"  # "tpe", "random", "cmaes"
        pruner: str = "hyperband"  # "hyperband", "median", "nop"
        search_bounds: dict = field(default_factory=...)
        storage: str = "sqlite:///optuna.db"
        study_name: str = "watermark_ensemble_tuning"
    ```
  - Validation in `__post_init__()` (ensure bounds sensible, trial budget reasonable)

- `scripts/run_optuna_tuning.py` (150–200 LOC)
  - CLI entry point with argparse
    - `--video` (required, path to validation video)
    - `--ground_truth` (required, COCO JSON annotations)
    - `--n_trials` (default 150)
    - `--output_dir` (checkpoint save location)
    - `--gpu_id` (optional, GPU device selection)
  - Load Phase 3A checkpoint, initialize OptunaTuner
  - Run optimization loop, save best_params to JSON

**Type System Updates:**
- `src/watermark_removal/core/types.py` (modifications)
  - Add to ProcessConfig:
    ```python
    optuna_enabled: bool = False
    optuna_study_name: str = "watermark_ensemble_tuning"
    optuna_storage: str = "sqlite:///optuna.db"
    optuna_n_trials: int = 150
    optuna_search_bounds: dict = field(default_factory=lambda: {
        "weight_yolov5s": (0.1, 1.0),
        "weight_yolov5m": (0.1, 1.0),
        "weight_yolov5l": (0.1, 1.0),
        "confidence_threshold": (0.05, 0.95),
        "iou_threshold": (0.3, 0.7),
        "nms_threshold": (0.3, 0.7),
        "augmentation": (0.0, 1.0),
    })
    ```

**Checkpoint Integration:**
- `src/watermark_removal/persistence/crop_serializer.py` (modifications)
  - Extend checkpoint v1.3 with `tuning_metadata` dict:
    ```python
    "tuning_metadata": {
        "study_name": "watermark_ensemble_tuning",
        "best_params": {"weight_yolov5s": 0.52, "weight_yolov5m": 0.33, ...},
        "best_mAP": 0.856,
        "baseline_mAP": 0.801,
        "improvement_percent": 6.8,
        "completed_at": "2026-04-30T14:22:00Z"
    }
    ```

#### Files to Create (Tests)
- `tests/test_optuna_tuning.py` (600–800 LOC, 20–28 test cases)
  - **TestObjectiveFunction** (6 tests)
    - `test_objective_returns_float()` — mAP metric is float
    - `test_objective_valid_range()` — mAP in [0, 1]
    - `test_model_failure_handled()` — If YOLOv5m unavailable, gracefully continue
    - `test_cuda_oom_caught()` — CUDA out of memory → skip trial, continue
    - `test_trial_timeout()` — Long inference → timeout caught, trial skipped
    - `test_inference_correctness()` — mAP computed correctly vs manual verification

  - **TestSearchSpace** (4 tests)
    - `test_weight_bounds()` — Suggested weights in [0.1, 1.0]
    - `test_threshold_bounds()` — Confidence/IoU/NMS in valid ranges
    - `test_augmentation_bounds()` — Augmentation in [0.0, 1.0]
    - `test_search_space_dimensionality()` — 6–8 hyperparameters

  - **TestSamplerConfiguration** (3 tests)
    - `test_tpe_sampler_multivariate()` — TPESampler with multivariate=True
    - `test_sampler_initialization()` — n_startup_trials=10 set correctly
    - `test_sampler_consistency()` — Same seed → reproducible suggestions

  - **TestPrunerConfiguration** (3 tests)
    - `test_hyperband_pruner()` — HyperbandPruner with min_resource=5, max_resource=50
    - `test_pruner_early_stops()` — Unpromising trials halted before completion
    - `test_pruner_efficiency()` — Effective trials reduced 40–60% vs no pruning

  - **TestOptimizationLoop** (4 tests)
    - `test_optimize_convergence()` — 150 trials → converge to stable best_mAP
    - `test_best_params_improvement()` — Best params improve baseline mAP 5–15%
    - `test_sqlite_persistence()` — Study checkpoints to SQLite; load_if_exists resumes
    - `test_result_extraction()` — study.best_params formatted correctly

  - **TestErrorHandling** (2 tests)
    - `test_model_load_failure()` — Pretrained model unavailable → skip trials
    - `test_disk_space_error()` — SQLite write fails → graceful error

#### Patterns to Follow
- Async patterns from Phase 3A (objective can be wrapped for parallel workers)
- Configuration validation from ProcessConfig
- Checkpoint save/load from CropRegionSerializer

#### Execution Note
- Implement objective function first (core logic, testable with mocks)
- Implement sampler/pruner configuration next
- Integrate with CLI (scripts/run_optuna_tuning.py) for standalone operation
- Use Phase 3A checkpoint to load pretrained models (no retraining)

#### Test Scenarios

| Scenario | Input | Expected Output | Coverage |
|----------|-------|-----------------|----------|
| **Happy path** | 150 trials, validation set | Converge to best_params with 5–15% mAP improvement | ✓ |
| **Search space** | 6–8 hyperparameters | All suggest_float calls within bounds | ✓ |
| **Sampler** | TPESampler multivariate | Parameter dependencies captured | ✓ |
| **Pruner** | HyperbandPruner | Early stops unpromising trials, 40–60% compute savings | ✓ |
| **Model failure** | YOLOv5m unavailable | Skip trials gracefully, continue with s+l | ✓ |
| **CUDA OOM** | Batch size too large | Trial marked error, next trial runs | ✓ |
| **Checkpoint** | SQLite study db | Study resumable; load_if_exists works | ✓ |
| **Best params** | Extracted from study | Formatted as JSON config | ✓ |
| **Baseline comparison** | Best params vs uniform weights | Best improves baseline 5–15% | ✓ |
| **Disabled tuning** | optuna_enabled=False | No optimization, zero overhead | ✓ |
| **Concurrent workers** | Multiple GPU processes | Distributed Optuna study supported | ✓ |
| **Wall-clock time** | Optimization complete | ≤32 GPU hours on RTX4090 | ✓ |

#### Verification Criteria
- ✓ Search space dimensionality 6–8 hyperparameters
- ✓ Trial budget 150–200 trials; convergence to stable best_params
- ✓ Best params improve baseline ensemble mAP 5–15%
- ✓ Wall-clock time estimate ≤32 GPU hours (verified on RTX4090)
- ✓ Study persists to SQLite; resumable across sessions
- ✓ Sampler/pruner configuration sensible (TPE multivariate, HyperbandPruner)
- ✓ Graceful error handling (model failures, CUDA OOM, timeouts)
- ✓ Disabled tuning (optuna_enabled=False) has zero impact on performance
- ✓ ≥85% test coverage (allowance for compute-heavy trials)

---

## Configuration & Backward Compatibility

### ProcessConfig Extension

New fields added to ProcessConfig with defaults (features disabled):

```python
@dataclass
class ProcessConfig:
    # ... Phase 2 + 3A fields (unchanged) ...

    # Unit 24: Label Studio annotation
    label_studio_enabled: bool = False
    label_studio_url: str = "http://localhost:8080"
    label_studio_api_key: str | None = None
    label_studio_project_id: int | None = None
    label_studio_wait_timeout_sec: float = 3600.0

    # Unit 25: Optuna hyperparameter tuning
    optuna_enabled: bool = False
    optuna_study_name: str = "watermark_ensemble_tuning"
    optuna_storage: str = "sqlite:///optuna.db"
    optuna_n_trials: int = 150
    optuna_search_bounds: dict = field(default_factory=lambda: {
        "weight_yolov5s": (0.1, 1.0),
        "weight_yolov5m": (0.1, 1.0),
        "weight_yolov5l": (0.1, 1.0),
        "confidence_threshold": (0.05, 0.95),
        "iou_threshold": (0.3, 0.7),
        "nms_threshold": (0.3, 0.7),
        "augmentation": (0.0, 1.0),
    })

    def __post_init__(self):
        super().__post_init__()

        # Validate Unit 24 fields
        if self.label_studio_enabled:
            if not self.label_studio_api_key:
                raise ValueError("label_studio_api_key required when annotation enabled")
            if not self.label_studio_project_id:
                raise ValueError("label_studio_project_id required when annotation enabled")
            if not (1 <= self.label_studio_wait_timeout_sec <= 86400):
                raise ValueError("label_studio_wait_timeout_sec must be 1–86400 seconds")

        # Validate Unit 25 fields
        if self.optuna_enabled:
            if not (50 <= self.optuna_n_trials <= 10000):
                raise ValueError("optuna_n_trials must be 50–10000")
            # Validate search bounds (optional; user can customize)
```

### Checkpoint Versioning (v1.3)

```json
{
  "version": "1.3",
  "timestamp": "2026-03-31T10:30:00Z",
  "crop_regions": { ... },
  "flow_data": { ... },
  "annotation_tasks": {
    "0": {
      "frame_id": 0,
      "label_studio_task_id": 12345,
      "annotation_complete": true,
      "uploaded_at": "2026-03-31T10:30:00Z"
    },
    "1": { ... }
  },
  "tuning_metadata": {
    "study_name": "watermark_ensemble_tuning",
    "best_params": {
      "weight_yolov5s": 0.52,
      "weight_yolov5m": 0.33,
      "weight_yolov5l": 0.15,
      "confidence_threshold": 0.45,
      "iou_threshold": 0.55,
      "nms_threshold": 0.45,
      "augmentation": 0.6
    },
    "best_mAP": 0.856,
    "baseline_mAP": 0.801,
    "improvement_percent": 6.8,
    "n_trials": 157,
    "completed_at": "2026-04-30T14:22:00Z"
  }
}
```

### Backward Compatibility

- ✓ **Phase 2 configs (v1.0)** still work in Phase 3B (all Phase 3B features optional, disabled by default)
- ✓ **Phase 2 checkpoints (v1.0)** load unchanged (new fields ignored; backward-compatible deserializer)
- ✓ **Phase 3A configs** load in Phase 3B (annotation/tuning skipped if disabled)
- ✓ **Features can be disabled individually** (use Phase 3A without annotation or tuning)
- ✓ **Migration path** v1.0 → v1.2 → v1.3 preserves existing sessions

---

## Sequencing & Timeline

### Dependency Graph

```
Phase 3A (Units 21–23, 27A, 26) [COMPLETE]
    ├─ Unit 24 (Label Studio) — depends on: Phase 3A ensemble + streaming
    │   └─ Produce: Annotated dataset (COCO JSON)
    │       └─ Phase 4 (fine-tuning models, future)
    │
    └─ Unit 25 (Optuna) — depends on: Phase 3A ensemble + annotated validation data
        └─ Produce: Optimal voting parameters
            └─ Phase 4 (update production config, future)
```

### Timeline Estimate

| Week | Unit 24 (Annotation) | Unit 25 (Tuning) | Notes |
|------|----------------------|------------------|-------|
| **1–2** | Implementation (client, exporters) | Implementation (objective, sampler/pruner) | Parallel: no dependencies |
| **2–3** | Unit tests + staging Label Studio instance | Unit tests + mock trials | Integration testing begins |
| **3–4** | Integration tests; production Docker setup | Compute-heavy optimization (16–32 GPU hrs) | Can overlap; different resources |
| **4–5** | Finalize annotation workflow; edge cases | Extract best params; validate improvement | Merge-ready for code review |
| **5–6** | Documentation (annotation guide) | Documentation (tuning guide); operational monitoring | Final polish |
| **6–8** | Buffer: iteration, performance tuning, production readiness | Buffer: compute optimization if wall-clock time exceeds 32 hrs | Risk buffer |

**Parallel Execution:** Units 24 and 25 can run in parallel after Phase 3A stabilizes (both read-only of Phase 3A components; no shared mutable state).

---

## Deployment Readiness

### Pre-Release Checklist

- ✓ **All tests pass**, >90% coverage (Unit 24), ≥85% coverage (Unit 25)
- ✓ **Integration tests** verify annotation workflow → tuning → training
- ✓ **Docker Compose** for Label Studio tested and documented
- ✓ **Optuna trial budget** benchmarked (wall-clock time ≤32 GPU hours)
- ✓ **Phase 2/3A backward compatibility** verified (v1.0/1.2 checkpoints load unchanged)
- ✓ **Configuration documentation** complete (all new fields documented, defaults sensible)
- ✓ **Operational monitoring** for Label Studio sync + Optuna optimization (logging, metrics)
- ⏳ **End-to-end production testing** (real video, real annotators, real tuning)
- ⏳ **Performance optimization** (if wall-clock time exceeds 32 GPU hours)

### Known Constraints

- **Label Studio scaling:** In-memory session manager sufficient for single-node; migrate to Redis for distributed annotators (Phase 3B+)
- **Optuna parallelization:** Single-process optimization; distributed workers via cloud Optuna service deferred (Phase 3B+)
- **Model fine-tuning:** Phase 3B tunes voting parameters only; fine-tuning of YOLOv5 models deferred to Phase 4
- **Annotation volume:** Tested for <10k frames; larger volumes may require batch export optimization
- **Production monitoring:** Logging + metrics in place; custom dashboards deferred to operational setup

---

## Success Criteria

### Unit 24 (Label Studio Annotation)

1. **Detections uploadable** — Ensemble detector BBox outputs convertible to Label Studio format
2. **Human review enabled** — Annotators can accept/correct boxes in Label Studio UI
3. **Exports valid** — COCO JSON and YOLO formats accepted by YOLOv5 training
4. **Graceful degradation** — Label Studio unavailable → streaming continues without disruption
5. **Session resumption** — Checkpoint v1.3 preserves task IDs; can resume annotation state
6. **Self-hosted MVP** — Docker Compose deployment documented and tested
7. **Test coverage** — ≥90% coverage, 18–24 tests, ≤5% flakiness

### Unit 25 (Optuna Tuning)

1. **Optimization converges** — 150–200 trials → stable best_params
2. **Improvement measurable** — Best params improve baseline mAP 5–15%
3. **Compute efficient** — Wall-clock time ≤32 GPU hours (HyperbandPruner early stopping)
4. **Checkpoint persistent** — Study saved to SQLite, resumable
5. **Error resilient** — Graceful handling of model failures, CUDA OOM, timeouts
6. **Production-ready** — Disabled tuning (optuna_enabled=False) has zero overhead
7. **Test coverage** — ≥85% coverage, 20–28 tests, ≤5% flakiness

---

## Post-Phase 3B Work (Deferred)

### Phase 4 (Model Fine-Tuning, Future)

- Fine-tune YOLOv5s/m/l on annotated dataset from Unit 24
- Use optimized ensemble params from Unit 25 as baseline
- Evaluate improvement on held-out test set

### Phase 3B+ (Scaling & Optimization)

- Migrate session manager to Redis (distributed annotators)
- Implement distributed Optuna workers (multi-GPU/multi-node optimization)
- Add webhook callbacks for Label Studio (automated retraining on new annotations)
- Implement batch export optimization (>10k frames)

---

## References & Patterns

### Key Resources

- **Label Studio Documentation:** [label-studio-sdk](https://github.com/HumanSignal/label-studio-sdk)
- **Optuna Documentation:** [optuna.readthedocs.io](https://optuna.readthedocs.io/)
- **Phase 3A Patterns:** Async/await, feature flags, graceful degradation, lazy loading, dependency injection
- **Checkpoint Format:** JSON v1.3 with backward-compatible deserializer

### Implementation Patterns to Follow

| Pattern | Source (Phase 3A) | How to Apply (Phase 3B) |
|---------|-------------------|------------------------|
| **Async HTTP** | `BackgroundTaskRunner` | Use `aiohttp.ClientSession` for Label Studio API |
| **Lazy Loading** | `OpticalFlowProcessor` | Load Label Studio client only if enabled |
| **Error Handling** | `EnsembleDetector` (model fallback) | Graceful degradation if Label Studio unavailable |
| **State Tracking** | `SessionManager` | AnnotationTask in checkpoint for resumption |
| **Feature Flags** | ProcessConfig | label_studio_enabled, optuna_enabled (default False) |
| **Configuration** | ProcessConfig validation | Validate bounds in __post_init__ |
| **Testing** | Phase 3A test suites | Mock external APIs; integration tests with real objects |

---

**Phase 3B Status:** 🟡 Planning Complete — Ready for Implementation
**Next Step:** Begin Unit 24 & 25 implementation (parallel execution after Phase 3A stabilization)
