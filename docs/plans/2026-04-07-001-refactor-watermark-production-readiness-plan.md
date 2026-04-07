---
title: "refactor: Watermark Removal System — Production Readiness Consolidation"
type: refactor
status: active
date: 2026-04-07
---

# refactor: Watermark Removal System — Production Readiness Consolidation

## Overview

Phase 1-3 of the watermark removal system are feature-complete (8,600 LOC source, 13,000 LOC tests, 785 passing). However, the codebase has accumulated technical debt that blocks real-world usage: duplicate modules (`annotation/` kept, `labeling/` retired; `optimization/` kept, `tuning/` retired), missing dependencies, no CLI entry point, no packaging metadata, and disconnected subsystems (QualityMonitor, config/base.yaml). This plan consolidates the system into a production-ready state before further feature work.

## Problem Frame

The watermark removal system was built in a 9-day sprint across three phases. Each phase added modules incrementally, resulting in:

1. **Duplicate module pairs** that create confusion and import ambiguity: `annotation/` vs `labeling/`, `optimization/` vs `tuning/`
2. **Missing `requirements.txt` entries** — the streaming server imports `fastapi`, `pydantic`, `uvicorn` but they aren't declared
3. **No way to run the system** — no `__main__.py`, no `pyproject.toml`, no CLI; users must write Python code manually
4. **QualityMonitor exists but is disconnected** from the pipeline — processed videos have zero automatic quality scoring
5. **`config/base.yaml` only covers Phase 1** — Phase 2/3 settings (temporal smoothing, ensemble detection, optical flow) are undocumented
6. **Version stuck at 0.1.0** despite three completed phases and 785 passing tests
7. **18 test collection errors** across 18 files — caused by (a) `test_phase3_integration.py` importing nonexistent types (`FrameExtractedData`, `FrameResult`), (b) import path split (`from watermark_removal.*` vs `from src.watermark_removal.*`), (c) missing packages (cv2, optuna, skimage) when venv not activated

## Requirements Trace

- R1. Eliminate duplicate modules — single canonical location for Label Studio and Optuna functionality
- R2. All runtime dependencies declared in `requirements.txt` with proper extras grouping
- R3. System installable via `pip install -e .` with `pyproject.toml`
- R4. CLI entry point: `python -m watermark_removal <config.yaml>` runs the pipeline
- R5. QualityMonitor wired into pipeline with per-frame metrics and summary report
- R6. `config/base.yaml` documents all Phase 1-3 configuration parameters with defaults
- R7. All tests pass with zero collection errors
- R8. Version bumped to 0.9.0 signaling feature-complete but pre-stable (reserve 1.0.0 for after real-world validation)

## Scope Boundaries

- **Not in scope:** ProcessConfig refactoring into sub-configs (high blast radius, 54 fields touch many tests — defer to future plan)
- **Not in scope:** Activating optical flow alignment in stitching (Phase 4 feature work, not consolidation)
- **Not in scope:** MaskType.POINTS implementation (deferred feature)
- **Not in scope:** Reconciling `projects/_tools/watermark-removal-system/` with `src/watermark_removal/` (separate project with different architecture — Phase 3 standalone deployment)
- **Not in scope:** Developer toolchain fixes (10 config breakages, v1.1.0 blockers — separate plan)

## Context & Research

### Relevant Code and Patterns

- `src/watermark_removal/core/pipeline.py` (633L) — main orchestrator, imports from preprocessing/, inpaint/, postprocessing/, temporal/, persistence/, optical_flow/
- `src/watermark_removal/core/types.py` (404L) — ProcessConfig with 54 fields, InpaintConfig already separated as nested dataclass
- `src/watermark_removal/streaming/server.py` — imports `annotation.label_studio_client` (not `labeling/`)
- `src/watermark_removal/metrics/quality_monitor.py` — FrameMetrics dataclass with boundary_smoothness, color_consistency, temporal_consistency, inpaint_quality
- `config/base.yaml` (33L) — only Phase 1 I/O, inpaint, and encoding settings
- `requirements.txt` — has opencv, numpy, pyyaml, aiohttp, pytest, pytest-asyncio, optuna, scikit-image; missing fastapi, pydantic, uvicorn

### Import Relationships for Duplicate Modules

| Module | LOC | Imported By (source) | Imported By (tests) |
|--------|-----|---------------------|---------------------|
| `annotation/` | 711 | `streaming/server.py` | `test_label_studio_integration.py` |
| `labeling/` | 1,014 | (none) | `test_unit24_comprehensive.py` |
| `optimization/` | 724 | (none) | `test_optuna_integration.py` |
| `tuning/` | 486 | (none) | `test_unit25_comprehensive.py` |

### Module Consolidation Analysis

**annotation/ vs labeling/ — API Comparison:**

| Feature | `annotation/` (711L) | `labeling/` (1,014L) |
|---------|---------------------|---------------------|
| LabelStudioClient constructor | `(host, port, api_key)` | `(url, api_key)` |
| LabelStudioClient methods | create_project, upload_tasks, create_annotation, get_task_annotations, validate_connection | upload_tasks (session-aware), create_predictions, get_annotations (polling), health_check |
| DatasetExporter | Monolithic `DatasetExporter` class | Separate `CocoExporter`, `YoloExporter` with `CoordinateConverter` |
| Unique dataclasses | (none) | `PredictionBBox`, `LabelStudioTask`, `BBoxPixel`, `BBoxPercentage` |
| Setup utilities | (none) | `DockerComposeGenerator`, `ProjectInitializer`, `APIKeyManager` |
| Import pattern | aiohttp-based with retry/backoff | synchronous requests-based |

**Decision:** Keep `annotation/` as base (production-imported), merge labeling/'s unique classes (`PredictionBBox`, `LabelStudioTask`, `CoordinateConverter`, `CocoExporter`, `YoloExporter`) and setup utilities into `annotation/`. This is a non-trivial merge, not a simple import path change.

**optimization/ vs tuning/ — API Comparison:**

| Feature | `optimization/` (724L) | `tuning/` (486L) |
|---------|----------------------|------------------|
| Main class | `OptunaOptimizer` | `OptunaTuner` |
| Optuna import | Hard import (crashes if missing) | try/except with `OPTUNA_AVAILABLE` flag |
| Config | No config dataclass | `TuningConfig` dataclass |
| Persistence | No save/load | `save_results()`, `load_results()` to JSON |
| Search space | 5 pipeline hyperparams | 7 ensemble detection hyperparams |
| Companion | `TrialRunner` with composite metrics | `TuningSearchSpace`, `TuningParameters` |

**Decision:** Merge into `optimization/` but adopt tuning/'s graceful degradation pattern (try/except import) and migrate `TuningConfig`, `TuningSearchSpace`, `TuningParameters`, and JSON persistence. Keep both `OptunaOptimizer` (pipeline tuning) and `OptunaTuner` (ensemble tuning) as separate classes.

### Institutional Learnings

- **Benchmark-first rule:** Estimates were 5-10x off for RAFT performance — relevant if adding any performance claims to config docs
- **Context engineering hygiene:** Use subagents for large file operations; compact at 70%
- **Dry-run default trap:** Automation scripts that default to dry-run never actually fix anything — relevant for any new CLI defaults

## Key Technical Decisions

- **Keep `annotation/`, merge `labeling/` features into it:** `annotation/` is the module imported by production code (`streaming/server.py`). `labeling/` has unique classes (`PredictionBBox`, `LabelStudioTask`, `CoordinateConverter`, `CocoExporter`, `YoloExporter`, setup utilities) that must be merged into `annotation/`, not just import-path-swapped. See Module Consolidation Analysis for full API comparison.
- **Keep `optimization/`, merge `tuning/` patterns into it:** Adopt tuning/'s graceful degradation (try/except optuna import with `OPTUNA_AVAILABLE` flag), migrate `TuningConfig`, `TuningSearchSpace`, `TuningParameters`, and JSON persistence (`save_results`/`load_results`). Keep both `OptunaOptimizer` and `OptunaTuner` as separate classes in `optimization/`.
- **Streaming deps in pyproject.toml extras only:** Base `requirements.txt` keeps core deps (opencv, numpy, pyyaml, aiohttp, optuna, scikit-image). `fastapi>=0.100.0`, `pydantic>=2.0`, `uvicorn>=0.23.0` go in `[streaming]` extra in pyproject.toml. `torch`/`torchvision` go in `[gpu]` extra. `requirements.txt` remains the quick-start for core pipeline; `pip install -e .[streaming]` for the streaming server.
- **pyproject.toml over setup.py:** Modern Python packaging standard (PEP 621). setuptools backend with src layout.
- **CLI via `__main__.py`:** Thin entry point that loads YAML config → ProcessConfig → Pipeline.run() via `asyncio.run()`. `--dry-run` validates config, checks input file existence, and optionally pings ComfyUI — then exits. `--version` prints version. Exit codes: 0=success, 1=config/usage error, 2=pipeline runtime error. Default mode is full run (not dry-run), per institutional learning on the dry-run default trap.
- **QualityMonitor gated by dedicated config field:** Add `quality_metrics_enabled: bool = True` to ProcessConfig. Compute FrameMetrics inside `_stitch_frames()` loop where original frame, inpainted crop, and stitched result are all in memory. Write CSV/JSON to `{output_dir}/quality_report/` before `_cleanup()` runs. Keep `verbose` for logging verbosity only — do not conflate with feature gating.
- **Import path normalization:** After pyproject.toml with src layout, canonical import becomes `from watermark_removal.*`. All `from src.watermark_removal.*` imports in source and test files must be normalized. This is a prerequisite for `pip install -e .` to work correctly.

## Open Questions

### Resolved During Planning

- **Q: Should we merge the two codebases (`src/` and `projects/_tools/`)?** No — they serve different purposes. `src/watermark_removal/` is the Phase 1-2 pipeline. `projects/_tools/watermark-removal-system/` is Phase 3's standalone deployment with api/, distributed/, security/ layers. They share the inner `watermark_removal/` package but have different outer architectures.
- **Q: Should ProcessConfig be refactored now?** No — 54 fields touching dozens of test files is high blast radius. The current flat structure works and all fields have validation. Defer to a dedicated refactor plan when feature growth demands it.
- **Q: What version to target?** 0.9.0 — three phases complete but CLI is being defined for the first time, ProcessConfig refactoring deferred, optical flow stubbed out, and no real-world video processing validated. Reserve 1.0.0 for after CLI contract is validated by actual usage. 0.9.0 signals "feature-complete, API not yet stable" per SemVer.

### Deferred to Implementation

- **Which `labeling/` test assertions to port vs. rewrite** — `test_unit24_comprehensive.py` tests labeling/'s unique API (PredictionBBox, CocoExporter, etc.). After merging these classes into annotation/, test logic may need adjustments depending on method signature differences discovered during the merge

## Implementation Units

- [ ] **Unit 1: Fix all test collection errors**

**Goal:** Restore CI green by resolving 18 collection errors across 18 test files

**Requirements:** R7

**Dependencies:** None

**Files:**
- Modify: `tests/test_phase3_integration.py` (fix nonexistent type imports: `FrameExtractedData` → appropriate type from `core/types.py`, `FrameResult` → `ProcessingResult`)
- Modify: `tests/test_cli.py` (examine and fix — directly relevant to Unit 5's CLI work)
- Modify: All test files using `from watermark_removal.*` to use `from src.watermark_removal.*` (or defer to Unit 5's import normalization)
- Test: Full test suite collection

**Approach:**
- **1a: Fix code-level import errors** in `test_phase3_integration.py`: `FrameExtractedData` does not exist in `core/types.py` — alias from existing type or create it. `FrameResult` only exists in `projects/_tools/` — replace with `ProcessingResult` from `streaming/session_manager.py`
- **1b: Fix import path inconsistency** — `test_phase3_integration.py` and `test_label_studio_integration.py` use `from watermark_removal.*` while all other tests use `from src.watermark_removal.*`. Standardize to the majority pattern (`src.` prefix) for now; Unit 5 will normalize all to `from watermark_removal.*` after pyproject.toml
- **1c: Verify venv activation** — 17 of 18 errors are missing packages (cv2, optuna, skimage). Ensure `.venv` is activated when running pytest. Add `pytest.ini` or `pyproject.toml [tool.pytest.ini_options]` with `testpaths = ["tests"]`
- **1d: Examine `tests/test_cli.py`** — if it specifies expected CLI behavior, Unit 5's `__main__.py` should satisfy it

**Patterns to follow:**
- Existing test files use `pytest-asyncio` for async tests, heavy mocking of external deps (OpenCV, ComfyUI, YOLO)
- Majority import style: `from src.watermark_removal.X import Y`

**Test scenarios:**
- Happy path: `pytest tests/ --co -q` (inside .venv) collects all tests with 0 errors, 785+ tests collected
- Happy path: `pytest tests/test_phase3_integration.py -v` runs without collection failures
- Happy path: `pytest tests/test_cli.py --co -q` collects without errors

**Verification:**
- `pytest tests/ --co -q` inside activated .venv shows 0 errors, 785+ tests collected
- No import of nonexistent types (`FrameExtractedData`, `FrameResult`) remains

---

- [ ] **Unit 2: Consolidate annotation/ and labeling/ modules**

**Goal:** Single canonical `annotation/` package for all Label Studio functionality

**Requirements:** R1

**Dependencies:** None (can parallel with Unit 1; verify via `tests/test_label_studio_integration.py` and `tests/test_unit24_comprehensive.py` independently)

**Files:**
- Modify: `src/watermark_removal/annotation/__init__.py`
- Move: `src/watermark_removal/labeling/label_studio_setup.py` → `src/watermark_removal/annotation/label_studio_setup.py`
- Delete: `src/watermark_removal/labeling/` (entire directory)
- Modify: `tests/test_unit24_comprehensive.py` (update imports from `labeling` → `annotation`)
- Test: `tests/test_label_studio_integration.py`, `tests/test_unit24_comprehensive.py`

**Approach:**
- **Merge `label_studio_client.py`:** labeling/ version has 23L of unique content including `PredictionBBox`, `LabelStudioTask` dataclasses, session-aware `upload_tasks`, `create_predictions`, polling-based `get_annotations`, `health_check`. Diff both files and merge labeling/'s unique methods/classes into annotation/'s aiohttp-based client
- **Merge `dataset_exporter.py`:** labeling/ has `CoordinateConverter`, `CocoExporter`, `YoloExporter` with `BBoxPixel`/`BBoxPercentage` dataclasses — a different API than annotation/'s monolithic `DatasetExporter`. Add these as additional export classes in annotation/
- **Move `label_studio_setup.py`** (270L) into `annotation/` — unique file with `DockerComposeGenerator`, `ProjectInitializer`, `APIKeyManager`
- **Update `annotation/__init__.py`** exports to include all merged classes
- **Update test imports** in `test_unit24_comprehensive.py` — not just path changes but may need test logic updates if method signatures differ between merged clients
- **Delete `labeling/` directory** only after all tests pass

**Patterns to follow:**
- `streaming/server.py` line 16: `from src.watermark_removal.annotation.label_studio_client import LabelStudioClient` — existing production import must remain valid
- annotation/'s aiohttp-based async pattern with retry/backoff is the preferred client architecture

**Test scenarios:**
- Happy path: `streaming/server.py` import of `annotation.label_studio_client` still resolves
- Happy path: All `test_label_studio_integration.py` tests pass unchanged (annotation/ API preserved)
- Happy path: All `test_unit24_comprehensive.py` tests pass with updated imports (may need method signature adjustments)
- Happy path: All public methods from labeling/`label_studio_client.py` are callable from annotation/ with identical signatures
- Happy path: `PredictionBBox`, `LabelStudioTask`, `CocoExporter`, `YoloExporter` importable from `annotation/`
- Edge case: `label_studio_setup.py` functions work correctly from new location
- Error path: Importing from deleted `labeling/` raises `ModuleNotFoundError`

**Verification:**
- `labeling/` directory no longer exists
- `grep -r "from.*labeling" src/ tests/` returns zero matches
- All Label Studio tests pass
- Feature parity: every public class/method from labeling/ exists in annotation/

---

- [ ] **Unit 3: Consolidate optimization/ and tuning/ modules**

**Goal:** Single canonical `optimization/` package for all Optuna/tuning functionality

**Requirements:** R1

**Dependencies:** Unit 1

**Files:**
- Modify: `src/watermark_removal/optimization/__init__.py`
- Move: `src/watermark_removal/tuning/tuning_config.py` → `src/watermark_removal/optimization/tuning_config.py`
- Delete: `src/watermark_removal/tuning/` (entire directory)
- Modify: `tests/test_unit25_comprehensive.py` (update imports from `tuning` → `optimization`)
- Test: `tests/test_optuna_integration.py`, `tests/test_unit25_comprehensive.py`

**Approach:**
- **Adopt tuning/'s graceful degradation:** Replace optimization/'s hard `import optuna` with tuning/'s `try/except` pattern and `OPTUNA_AVAILABLE` flag. This prevents import crashes when optuna is not installed
- **Keep both optimizer classes:** `OptunaOptimizer` (pipeline-level tuning, 420L) and `OptunaTuner` (ensemble detection tuning, 362L) serve different use cases — keep both in `optimization/`
- **Migrate tuning/'s unique features:** `TuningConfig` dataclass, `TuningSearchSpace`, `TuningParameters`, and JSON persistence (`save_results`/`load_results`) into `optimization/`
- Move `tuning/tuning_config.py` (112L) into `optimization/tuning_config.py`
- Move `tuning/optuna_optimizer.py` into `optimization/optuna_tuner.py` (renamed to avoid filename collision)
- Update `optimization/__init__.py` to export all migrated classes
- Update test imports in `test_unit25_comprehensive.py`
- Delete `tuning/` directory

**Patterns to follow:**
- `test_optuna_integration.py`: `from src.watermark_removal.optimization.optuna_optimizer import OptunaOptimizer`
- tuning/'s graceful degradation pattern: `try: import optuna; OPTUNA_AVAILABLE = True; except ImportError: OPTUNA_AVAILABLE = False`

**Test scenarios:**
- Happy path: `test_optuna_integration.py` passes unchanged (OptunaOptimizer API preserved)
- Happy path: `test_unit25_comprehensive.py` passes with updated imports (OptunaTuner, TuningConfig, TuningSearchSpace, TuningParameters)
- Happy path: `from optimization import TuningSearchSpace, TuningParameters, OptunaTuner` works
- Happy path: Importing optimization/ without optuna installed does not crash (graceful degradation)
- Error path: Importing from deleted `tuning/` raises `ModuleNotFoundError`

**Verification:**
- `tuning/` directory no longer exists
- `grep -r "from.*tuning" src/ tests/` returns zero matches (excluding docs)
- All Optuna/tuning tests pass
- `OPTUNA_AVAILABLE` flag used in both optimizer classes

---

- [ ] **Unit 4: Fix requirements.txt — core deps only**

**Goal:** Base requirements.txt declares core pipeline dependencies; optional deps managed exclusively via pyproject.toml extras

**Requirements:** R2

**Dependencies:** None (can parallel with Units 2-3)

**Files:**
- Modify: `requirements.txt`
- Test: (verified by pip install in clean venv)

**Approach:**
- `requirements.txt` contains **core pipeline deps only**: opencv-python, numpy, pyyaml, aiohttp, optuna, scikit-image
- Move test deps (`pytest`, `pytest-asyncio`) out of requirements.txt — they belong in `[dev]` extras in pyproject.toml (Unit 5)
- Do NOT add fastapi/pydantic/uvicorn to requirements.txt — these go in `[streaming]` extras in pyproject.toml
- Do NOT add torch/torchvision — these go in `[gpu]` extras in pyproject.toml
- Document in comments which phase introduced each core dependency
- Verify Python 3.14 compatibility for all pinned versions

**Patterns to follow:**
- Current requirements.txt uses `>=X.Y.Z` version pinning with occasional upper bounds

**Test scenarios:**
- Happy path: `pip install -r requirements.txt` in clean venv succeeds
- Happy path: `python -c "from watermark_removal.core.pipeline import Pipeline"` succeeds after install (core pipeline importable)
- Edge case: `import watermark_removal.streaming.server` fails with ImportError for fastapi — expected behavior without `[streaming]` extras

**Verification:**
- `pip install -r requirements.txt` succeeds in clean venv
- Core pipeline modules importable; streaming server requires `pip install -e .[streaming]`

---

- [ ] **Unit 5: Add pyproject.toml, __main__.py, and normalize imports**

**Goal:** System installable via `pip install -e .` with CLI entry point, all imports normalized, version set to 0.9.0

**Requirements:** R3, R4, R8

**Dependencies:** Unit 4 (core deps correct), Units 2-3 (modules consolidated)

**Files:**
- Create: `pyproject.toml`
- Create: `src/watermark_removal/__main__.py`
- Modify: `src/watermark_removal/__init__.py` (version = "0.9.0")
- Modify: `src/watermark_removal/streaming/server.py` (normalize `from src.watermark_removal.*` → `from watermark_removal.*`)
- Modify: All test files using `from src.watermark_removal.*` (normalize to `from watermark_removal.*`)
- Modify: Any source files with `src.` prefix imports
- Test: `tests/test_cli.py` (examine existing expectations), full suite

**Approach:**
- **5a: pyproject.toml** — PEP 621 metadata, setuptools backend with src layout. Version 0.9.0. Extras: `[streaming]` (fastapi>=0.100.0, pydantic>=2.0, uvicorn>=0.23.0), `[gpu]` (torch>=2.0.0, torchvision>=0.15.0), `[dev]` (pytest, pytest-asyncio)
- **5b: Import normalization** — After pyproject.toml, canonical import is `from watermark_removal.*`. Sweep all `from src.watermark_removal.*` in source and test files using `grep -r "from src\.watermark_removal" src/ tests/` and replace with `from watermark_removal.*`. This is the largest subtask (41+ test files + streaming/server.py)
- **5c: __main__.py** — Load YAML config via ConfigManager, construct ProcessConfig, run `asyncio.run(Pipeline(config).run())`, print JSON summary. `--dry-run`: validate YAML→ProcessConfig, check input files exist, optionally ping ComfyUI at configured host:port, print effective config, exit 0. `--version`: print version, exit 0. Exit codes: 0=success, 1=config/usage error, 2=pipeline runtime error. Default mode is full run (not dry-run). ComfyUI requirement documented in --help text.
- **5d: Version bump** — Set version to 0.9.0 in both `__init__.py` and `pyproject.toml`

**Patterns to follow:**
- `src/watermark_removal/core/config_manager.py` (142L) already handles YAML loading and validation — reuse it
- Pipeline returns a summary dict from `run()` — print it as JSON
- `tests/test_cli.py` may already define expected CLI interface — examine before implementing __main__.py

**Test scenarios:**
- Happy path: `pip install -e .` succeeds, `python -m watermark_removal --version` prints `0.9.0`
- Happy path: `python -m watermark_removal config/base.yaml --dry-run` validates config, checks file existence, exits cleanly
- Happy path: After `pip install -e .`, `from watermark_removal.core.pipeline import Pipeline` works without sys.path manipulation
- Happy path: `grep -r "from src\.watermark_removal" src/ tests/` returns zero matches
- Error path: `python -m watermark_removal` with no args prints usage and exits with code 1
- Error path: `python -m watermark_removal nonexistent.yaml` prints clear error about missing file to stderr
- Edge case: Config with invalid parameters prints validation error from ProcessConfig.__post_init__

**Verification:**
- `pip install -e .` succeeds
- `python -m watermark_removal --version` outputs `0.9.0`
- `python -m watermark_removal --help` outputs usage info with ComfyUI prerequisite note
- Zero `from src.watermark_removal` imports remain in source or test files
- Version consistent across `__init__.py` and `pyproject.toml`

---

- [ ] **Unit 6: Wire QualityMonitor into pipeline**

**Goal:** Per-frame quality metrics computed after stitching, summary written to output directory

**Requirements:** R5

**Dependencies:** Units 2-3 (clean module state)

**Files:**
- Modify: `src/watermark_removal/core/types.py` (add `quality_metrics_enabled` field to ProcessConfig)
- Modify: `src/watermark_removal/core/pipeline.py` (import and call QualityMonitor)
- Modify: `src/watermark_removal/metrics/quality_monitor.py` (if API adjustments needed)
- Create: `tests/test_quality_monitor_integration.py`
- Test: `tests/test_quality_monitor_integration.py`

**Approach:**
- Add `quality_metrics_enabled: bool = True` to ProcessConfig in `core/types.py` (with validation in `__post_init__`)
- Import QualityMonitor in pipeline.py
- Instantiate QualityMonitor **once** before the `_stitch_frames()` loop (it maintains `_previous_frame` state for temporal consistency)
- Inside the stitch loop, call `compute_frame_metrics(frame_id, stitched_frame, inpainted_crop_ndarray, (crop_region.x, crop_region.y, crop_region.w, crop_region.h), original_frame_ndarray)` — all data is available as local variables in the loop
- For skipped frames (missing inpainted crop or caught exception), skip metrics computation with a warning log — record gap in metrics file
- Write metrics summary (CSV + JSON) to `{output_dir}/quality_report/` **before** `_cleanup()` runs
- Add metrics summary to the pipeline return dict
- Gate behind `self.config.quality_metrics_enabled`, NOT `verbose` (keep verbose for logging only)

**Patterns to follow:**
- `metrics/quality_monitor.py` already defines FrameMetrics with boundary_smoothness, color_consistency, temporal_consistency, inpaint_quality
- Pipeline's existing phase pattern: log phase start → execute → log completion
- Pipeline's error handling pattern: try/except with `skip_errors_in_postprocessing` flag

**Test scenarios:**
- Happy path: Pipeline run with quality_metrics_enabled=True produces `quality_report/metrics.csv` and `quality_report/summary.json` in output_dir
- Happy path: FrameMetrics contain valid boundary_smoothness (0-1), color_consistency (0-1), temporal_consistency (0-1 or None for first frame)
- Happy path: Pipeline return dict includes `quality_metrics` key with summary statistics
- Edge case: Single-frame video produces metrics with temporal_consistency=None
- Edge case: Pipeline with quality_metrics_enabled=False skips quality monitoring entirely (no quality_report/ created)
- Edge case: Frames skipped during stitching (missing inpainted crop) are omitted from metrics with frame_id gap noted
- Error path: If QualityMonitor computation fails for a frame, log warning and continue (pipeline never crashes on metrics failure)

**Verification:**
- Pipeline runs produce quality report files in output directory when quality_metrics_enabled=True
- Quality metrics appear in pipeline summary dict
- All existing pipeline tests still pass (QualityMonitor defaults to enabled but doesn't break mocked pipeline tests)
- `verbose` flag has no effect on quality metrics output

---

- [ ] **Unit 7: Complete config/base.yaml with Phase 2-3 settings**

**Goal:** All ProcessConfig parameters documented in base YAML with sensible defaults

**Requirements:** R6

**Dependencies:** None (documentation task)

**Files:**
- Modify: `config/base.yaml`
- Create: `config/phase2_advanced.yaml` (example for Phase 2 features)
- Create: `config/phase3_streaming.yaml` (example for Phase 3 streaming + ensemble)
- Test: (verified by loading through ConfigManager)

**Approach:**
- **First:** Read `config/phase1_static.yaml` and check `config/examples/` for existing content — do not duplicate what already exists
- Keep `config/base.yaml` as a **minimal starter config** (~20 fields for the core pipeline + temporal smoothing) — not all 54 fields
- Create `config/full_reference.yaml` with all 55 ProcessConfig fields (including new `quality_metrics_enabled`) organized by phase, with YAML comments. Complex types documented with examples: `optuna_search_bounds: {weight_yolov5s: [0.1, 1.0], ...}`, `ensemble_model_accuracies: {yolov5s: 0.85, ...}`
- Create phase-specific example configs only if `config/phase1_static.yaml` doesn't already cover those scenarios
- Validate all config files load without error through ConfigManager

**Patterns to follow:**
- Current `config/base.yaml` uses flat YAML keys matching ProcessConfig field names
- `docs/phase2_tuning_scenarios.md` already documents three tuning scenarios — align with those

**Test scenarios:**
- Happy path: `ConfigManager.load("config/base.yaml")` produces valid ProcessConfig with all defaults
- Happy path: `ConfigManager.load("config/phase2_advanced.yaml")` enables temporal smoothing and Poisson blending
- Happy path: `ConfigManager.load("config/phase3_streaming.yaml")` enables ensemble detection and streaming
- Error path: Config with invalid parameter values caught by ProcessConfig.__post_init__ validation

**Verification:**
- All example configs load without error
- Every ProcessConfig field appears in at least one YAML example with a comment

---

- [ ] **Unit 8: Final validation sweep**

**Goal:** Confirm all consolidation work is complete, all tests green, no stale references

**Requirements:** R7, R8

**Dependencies:** All previous units

**Files:**
- Test: Full test suite

**Approach:**
- Run full test suite: `pytest tests/ -v` — all tests must pass, 0 errors, 0 failures
- Verify `pip install -e .` still works after all changes
- Verify `python -m watermark_removal --version` outputs `0.9.0`
- Sweep for stale references: `grep -r "from.*labeling" src/ tests/`, `grep -r "from.*tuning" src/ tests/`, `grep -r "from src\.watermark_removal" src/ tests/`
- Verify no remaining references to deleted modules or old import paths
- Verify `quality_metrics_enabled` field exists in ProcessConfig and is documented in config/full_reference.yaml

**Test expectation: none** — this unit runs existing tests, not new ones. All test creation happened in prior units.

**Verification:**
- `pytest tests/ -v` — full suite green, 785+ tests pass
- `python -m watermark_removal --version` outputs `0.9.0`
- `grep -r "from.*labeling\|from.*tuning\|from src\.watermark_removal" src/ tests/` returns zero matches
- `pip install -e .[streaming]` succeeds and streaming server importable

## System-Wide Impact

- **Interaction graph:** Module consolidation affects test imports and `streaming/server.py` → `annotation/` import chain. No runtime behavior changes — only import paths.
- **Error propagation:** QualityMonitor integration adds a new failure point in the pipeline. Mitigated by try/except with warning-level logging — never crashes the pipeline.
- **State lifecycle risks:** None — consolidation is structural, not behavioral. QualityMonitor is read-only (computes metrics from existing frames).
- **API surface parity:** `__main__.py` CLI provides a new public interface. Config YAML format is the contract — ProcessConfig field names = YAML keys.
- **Integration coverage:** QualityMonitor integration needs an end-to-end test verifying metrics files are produced after a full pipeline run (Unit 6 test scenarios cover this).
- **Unchanged invariants:** Core pipeline behavior (extract → crop → inpaint → stitch → encode) is untouched. All existing ProcessConfig fields retain their defaults and validation rules.

## Risks & Dependencies

| Risk | Mitigation |
|------|------------|
| labeling/ → annotation/ merge is non-trivial (incompatible APIs) | Feature comparison matrix created; merge plan budgets explicit work for each class. Test parity verified per Unit 2 |
| optimization/ + tuning/ have different architectures | Both optimizer classes preserved; graceful degradation adopted from tuning/. See Module Consolidation Analysis |
| Import normalization touches 41+ files | Mechanical find-and-replace (`src.watermark_removal` → `watermark_removal`); run full test suite after each batch |
| QualityMonitor adds latency to pipeline | Dedicated `quality_metrics_enabled` flag; metrics are fast (SSIM, histogram comparison) |
| pyproject.toml path resolution on Windows | Test with `pip install -e .` on Windows; use `python -m` as primary entry point |
| Removing duplicate modules breaks downstream code | `grep -r` sweep for all import references before deletion |
| 0.9.0 version may confuse users expecting 1.0.0 | Document in CHANGELOG that 1.0.0 follows after real-world validation and CLI stabilization |

## Sources & References

- Related code: `src/watermark_removal/core/pipeline.py`, `src/watermark_removal/core/types.py`
- Related code: `src/watermark_removal/metrics/quality_monitor.py`
- Related code: `src/watermark_removal/annotation/`, `src/watermark_removal/labeling/`
- Related code: `src/watermark_removal/optimization/`, `src/watermark_removal/tuning/`
- Related config: `config/base.yaml`, `requirements.txt`
- Architecture doc: `docs/ARCHITECTURE.md`
- Phase completion reports: `docs/reports/`
