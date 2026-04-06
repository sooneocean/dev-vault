---
title: feat: Dynamic Watermark Removal System — Phase 2 Enhancement
type: feat
status: planning
date: 2026-03-30
origin: docs/plans/2026-03-30-001-feat-watermark-removal-system-plan.md
---

# Dynamic Watermark Removal System — Phase 2 Enhancement Plan

## Overview

Build upon Phase 1 MVP to add temporal coherence, automatic watermark tracking, advanced blending, and quality hardening. Focus on reducing inter-frame flicker and supporting more complex watermark scenarios.

**Scope:** Temporal smoothing, YOLO-based tracking, Poisson blending, CropRegion serialization (weeks 3-4).

---

## Problem Statement

Phase 1 processes frames independently, leading to:
- **Inter-frame flicker**: ±1-2px jitter at crop edges between adjacent frames
- **Manual tracking required**: Dynamic watermarks need pre-computed JSON bbox list
- **Visible seams**: Simple feather blending insufficient for complex backgrounds
- **No resumption**: Long videos must restart from beginning if interrupted

Phase 2 addresses these limitations while maintaining Phase 1's simplicity.

---

## Requirements Trace

| Req | Description | Priority | Test Signal |
|-----|-------------|----------|------------|
| R11 | Temporal smoothing to reduce inter-frame flicker | High | Alpha-blended frames show reduced jitter |
| R12 | Simple YOLO-based watermark tracking | Medium | Detected bboxes match manual annotations ±5px |
| R13 | Poisson blending at crop edges | Medium | Seamless transitions on complex backgrounds |
| R14 | Color matching at boundaries | Low | Color histogram match at stitched edges |
| R15 | CropRegion JSON serialization | Medium | Resumption from checkpoint successful |
| R16 | Quality monitoring & metrics | High | Per-frame quality scores logged |

---

## Scope Boundaries

### In Scope (Phase 2)
- Temporal smoothing with alpha blending (simple per-frame blending)
- YOLO5 watermark detection (fine-tuned on common watermarks)
- Poisson blending for smooth transitions
- JSON serialization for resume capability
- Quality metrics and monitoring
- Pre-computed watermark model repository

### Out of Scope (Phase 3+)
- Optical flow-based temporal coherence
- Multi-model ensemble detection
- Learned blending networks
- Real-time video processing
- Web UI for annotation and preview
- Cloud deployment infrastructure

---

## Architecture Changes

### New Modules

```
src/watermark_removal/
├── temporal/
│   ├── temporal_smoother.py        # Alpha-blend adjacent frames
│   └── __init__.py
├── detection/
│   ├── watermark_detector.py       # YOLO5-based detection
│   ├── detector_config.yaml        # Model config + thresholds
│   └── __init__.py
├── blending/
│   ├── poisson_blender.py          # Poisson blending
│   ├── color_matcher.py            # Color histogram matching
│   └── __init__.py
└── persistence/
    ├── crop_serializer.py          # CropRegion JSON I/O
    └── __init__.py
```

### Pipeline Changes

```
Phase 1 Pipeline:
  Extract → Preprocess → Inpaint → Stitch → Encode

Phase 2 Pipeline:
  Extract → Detect OR Load JSON → Preprocess → Inpaint → Temporal Smooth → Stitch (Poisson) → Encode
```

### New Configuration Fields

```yaml
# Temporal smoothing
temporal_smooth_alpha: 0.3          # Blend factor (0.0 = no blending, 1.0 = full previous)
temporal_smooth_enabled: true       # Enable/disable temporal smoothing

# Watermark detection
detection_enabled: false            # Auto-detect or use provided mask
detection_model: yolov5s            # yolov5s, yolov5m, yolov5l
detection_confidence: 0.5           # Confidence threshold
detection_nms_threshold: 0.45       # NMS suppression threshold

# Advanced blending
poisson_enabled: true               # Use Poisson blending instead of feather
color_match_enabled: false          # Color histogram matching
color_match_samples: 10             # Number of boundary samples

# Resumption
resume_from_checkpoint: null        # Path to checkpoint JSON (auto-detect if exists)
save_checkpoints: true              # Save CropRegion after preprocessing
checkpoint_frequency: 100           # Save every N frames
```

---

## Implementation Units

### **Unit 15: Temporal Smoothing**

**Goal:** Reduce inter-frame flicker by alpha-blending adjacent frames.

**Requirements:** R11

**Dependencies:** Unit 11 (Pipeline)

**Files:**
- Create: `src/watermark_removal/temporal/temporal_smoother.py`
- Create: `src/watermark_removal/temporal/__init__.py`
- Test: `tests/test_temporal_smoother.py`

**Approach:**
- `TemporalSmoother` class: takes alpha blending factor (0.0-1.0)
- Method: `blend_frame(current_frame: np.ndarray, previous_frame: np.ndarray, alpha: float) -> np.ndarray`
- Blending: `output = (1 - alpha) * current + alpha * previous`
- Applied only to inpainted region (preserve original boundaries)
- Store previous frame in pipeline state
- Optional: selective blending (only on crop region edges)

**Patterns to follow:**
- Reuse EdgeBlender's blend mask approach
- Keep blending region-specific (don't blend entire frame)
- Thread-safe frame buffer for parallelization

**Test scenarios:**
- **Happy path:** Blend with alpha=0.3, verify smooth interpolation
- **Edge case:** First frame (no previous), skip blending
- **Edge case:** Alpha=0.0 (no blending), Alpha=1.0 (full previous)
- **Integration:** Blend after inpaint but before stitch

**Verification:**
- Output frames are smooth (gradient analysis)
- Jitter reduced by measured amount
- No performance regression

---

### **Unit 16: Watermark Detection (YOLO)**

**Goal:** Automatically detect watermark regions using YOLO5, eliminating need for manual mask/bbox.

**Requirements:** R12

**Dependencies:** `yolov5` (pip install), Unit 1 (types)

**Files:**
- Create: `src/watermark_removal/detection/watermark_detector.py`
- Create: `src/watermark_removal/detection/detector_config.yaml`
- Create: `src/watermark_removal/detection/__init__.py`
- Test: `tests/test_watermark_detector.py`

**Approach:**
- Use YOLOv5s (smallest, fastest) as baseline
- Support pre-trained watermark detection model (or fine-tune on common watermarks)
- Method: `detect_frames(video_path: str, confidence: float) -> List[Dict[int, BBox]]`
- Return JSON-compatible list of per-frame bounding boxes
- Confidence threshold, NMS threshold configurable
- Fall back to Phase 1 JSON if detection unavailable

**Patterns to follow:**
- Lazy load model (only when detection_enabled=true)
- Cache model in memory between frames
- Async detection if possible (or run in executor)

**Test scenarios:**
- **Happy path:** Detect common watermarks (logo, banner, text)
- **Edge case:** No watermark in frame (return empty bbox)
- **Edge case:** Multiple watermarks (return largest or all?)
- **Accuracy:** Compare detected bboxes to ground truth ±5px tolerance
- **Performance:** <100ms per frame on CPU

**Verification:**
- Detection accuracy >85% on test set
- Bbox coordinates within ±5px of manual annotations
- Processing time <100ms per frame

---

### **Unit 17: Advanced Blending (Poisson)**

**Goal:** Replace simple feather blending with Poisson blending for seamless transitions on complex backgrounds.

**Requirements:** R13, R14

**Dependencies:** Unit 8 (StitchHandler), OpenCV

**Files:**
- Create: `src/watermark_removal/blending/poisson_blender.py`
- Create: `src/watermark_removal/blending/color_matcher.py`
- Create: `src/watermark_removal/blending/__init__.py`
- Test: `tests/test_poisson_blender.py`

**Approach (Poisson Blending):**
- Use OpenCV's `seamlessClone()` for Poisson blending
- Replace inpainted crop using Poisson blend (not simple alpha blend)
- Preserve gradient information at boundaries
- Apply on full frame (not just feather region)

**Approach (Color Matching - Optional):**
- Sample boundary pixels from original frame
- Histogram matching on inpainted crop before blending
- Use scikit-image `match_histograms()` if available

**Patterns to follow:**
- Wrapper around OpenCV Poisson clone (simple delegation)
- Configuration flags to enable/disable each component
- Backward compatible with Phase 1 feather blending

**Test scenarios:**
- **Happy path:** Poisson blend produces seamless transition
- **Edge case:** Boundary artifacts (should be minimal)
- **Edge case:** Color matching (if enabled) matches histogram
- **Integration:** Works with all mask types (static, dynamic)

**Verification:**
- No visible seams on complex backgrounds
- Boundary color histogram match (if color matching enabled)
- Performance: <200ms per frame for Poisson blend

---

### **Unit 18: CropRegion Serialization**

**Goal:** Save and load CropRegion metadata to enable resumption from checkpoint.

**Requirements:** R15

**Dependencies:** Unit 1 (types), Unit 11 (Pipeline)

**Files:**
- Create: `src/watermark_removal/persistence/crop_serializer.py`
- Create: `src/watermark_removal/persistence/__init__.py`
- Test: `tests/test_crop_serializer.py`

**Approach:**
- `CropRegionSerializer` class: JSON I/O for CropRegion objects
- Method: `serialize(crop_regions: Dict[int, CropRegion]) -> str` (JSON string)
- Method: `deserialize(json_str: str) -> Dict[int, CropRegion]`
- Store in `output_dir/checkpoint_crops.json` after preprocessing
- Load on pipeline restart if checkpoint exists
- Skip preprocessing if crops already computed

**Patterns to follow:**
- Use dataclass `asdict()` for serialization
- Preserve all fields (x, y, w, h, scale_factor, context_*, pad_*)
- Include metadata: frame_count, video_hash, mask_hash for validation

**Test scenarios:**
- **Happy path:** Serialize 100 crops, deserialize, verify identity
- **Edge case:** Empty crop dict
- **Edge case:** Round-trip preserves all fields exactly
- **Resumption:** Skip preprocessing, load crops, continue to inpaint

**Verification:**
- Serialized JSON is valid
- Round-trip deserialization is lossless
- Resume from checkpoint works end-to-end

---

### **Unit 19: Quality Monitoring**

**Goal:** Add per-frame quality metrics and logging for monitoring and optimization.

**Requirements:** R16

**Dependencies:** Unit 11 (Pipeline), Unit 9 (EdgeBlender)

**Files:**
- Create: `src/watermark_removal/metrics/quality_monitor.py`
- Create: `src/watermark_removal/metrics/__init__.py`
- Test: `tests/test_quality_monitor.py`

**Approach:**
- `QualityMonitor` class: compute per-frame quality scores
- Metrics:
  - Boundary smoothness (gradient variance at feather edges)
  - Color consistency (histogram distance between original and stitched)
  - Temporal consistency (frame-to-frame SSIM)
  - Inpaint quality (heuristic based on region variance)
- Log metrics to CSV and console
- Final summary with statistics

**Patterns to follow:**
- Non-blocking (compute after stitching)
- Configurable metric set
- Export metrics to JSON for analysis

**Test scenarios:**
- **Happy path:** Compute metrics for 10 frames, log results
- **Edge case:** First frame (no temporal SSIM)
- **Accuracy:** Metrics correlate with visual quality

**Verification:**
- All metrics computed without errors
- Metrics logged to output file
- Metrics make sense (smoothness 0-1, consistency 0-1)

---

### **Unit 20: Integration & Testing**

**Goal:** Integration tests for Phase 2 features, update documentation.

**Requirements:** All Phase 2 units

**Dependencies:** All Units 15-19

**Files:**
- Modify: `tests/integration_test.py` (add Phase 2 scenarios)
- Create: `tests/test_phase2_pipeline.py` (end-to-end with temporal smoothing)
- Modify: `docs/README.md` (document Phase 2 features)
- Create: `docs/phase2_migration_guide.md` (upgrade from Phase 1)

**Approach:**
- Integration test: full pipeline with temporal smoothing enabled
- Integration test: auto-detect + temporal smooth + Poisson blend
- Integration test: resume from checkpoint
- Update README with Phase 2 configuration examples
- Migration guide for Phase 1 users

**Verification:**
- All Phase 2 features work together
- Backward compatibility with Phase 1 configs
- Tests pass, coverage >80%

---

## System-Wide Impact

### Integration Points
- Pipeline orchestration: Add temporal smoother between inpaint and stitch
- Configuration validation: New Phase 2 config fields
- Error handling: Graceful fallback if detection fails
- Logging: Quality metrics and checkpoint status

### Data Flow
```
Phase 1:
  frames → preprocess → inpaint → stitch → encode

Phase 2:
  frames → detect/load → preprocess → inpaint → temporal_smooth → poisson_stitch → quality_monitor → encode
                                                                                  ↓
                                                                         save checkpoint
```

### State Management
- Previous frame buffer (temporal smoother)
- CropRegion checkpoint (serializer)
- Quality metrics accumulation (monitor)

### Error Handling
- Detection failure → fall back to provided mask
- Checkpoint corruption → restart preprocessing
- Poisson blend failure → fall back to feather blending

---

## Dependencies & Infrastructure

### New Python Packages
```
yolov5>=6.2.0          # Watermark detection
scikit-image>=0.19.0   # Color matching (optional)
scipy>=1.7.0           # Advanced image processing
```

### Pre-trained Models
- YOLOv5s pretrained on COCO (default)
- Fine-tuned watermark detection model (future: custom dataset)

### External Resources
- YOLOv5 model downloads (~150MB)
- Watermark detection dataset (if fine-tuning)

---

## Risks & Mitigations

| Risk | Mitigation | Phase |
|------|-----------|-------|
| **Detection accuracy** (false negatives) | Start with conservative threshold (0.5), manual fallback | 2 |
| **Temporal flicker not fully solved** | Alpha blending acceptable for MVP; optical flow in Phase 3 | 2 |
| **Poisson blend artifacts** (halos, color shifts) | Test thoroughly on complex backgrounds, fallback to feather | 2 |
| **Performance regression** (temporal smooth + Poisson) | Profile before/after, optimize critical paths | 2 |
| **Checkpoint compatibility** (format changes) | Version checkpoint format, handle migrations | 2 |
| **Memory usage** (previous frame buffer) | Stream processing in Phase 3 if needed | 2 |

---

## Deferred to Phase 3

1. **Optical flow temporal coherence** — Robust inter-frame tracking
2. **Multi-model ensemble** — Combine multiple detection models
3. **Learned blending networks** — Train blending network on watermark dataset
4. **Real-time processing** — Stream-based pipeline for live feeds
5. **Web UI** — Annotation tool and preview interface
6. **Auto-tuning** — Optimize parameters per-video

---

## Success Criteria

✅ All Phase 2 units implemented and tested
✅ Inter-frame flicker reduced by >50% (visual inspection + metrics)
✅ Auto-detection works on common watermarks (>85% accuracy)
✅ Poisson blending produces seamless transitions (visual inspection)
✅ Resume from checkpoint works end-to-end
✅ Quality metrics logged and analyzed
✅ Backward compatible with Phase 1 (existing configs still work)
✅ Documentation updated with Phase 2 features
✅ All tests passing (>300 total)
✅ Performance acceptable (no significant slowdown)

---

## Execution Strategy

### Parallel Work Paths
- Unit 15 (Temporal): Independent, low dependency
- Unit 16 (Detection): Requires testing data/model
- Unit 17 (Blending): Builds on Unit 9 (EdgeBlender)
- Unit 18 (Serialization): Independent, can test early
- Unit 19 (Monitoring): Depends on all others
- Unit 20 (Integration): Final validation pass

### Suggested Order
1. **Unit 15** → Temporal smoothing (quick win, immediate benefit)
2. **Unit 18** → Serialization (foundation for resume)
3. **Unit 17** → Poisson blending (quality improvement)
4. **Unit 16** → Detection (most complex, last)
5. **Unit 19** → Monitoring (validation and metrics)
6. **Unit 20** → Integration & docs (final polish)

---

## Timeline Estimate

| Unit | Complexity | Est. Days |
|------|-----------|----------|
| 15 | Low | 1-2 |
| 16 | High | 2-3 |
| 17 | Medium | 1-2 |
| 18 | Low | 0.5-1 |
| 19 | Medium | 1-2 |
| 20 | Medium | 1-2 |
| **Total** | — | **7-12 days** |

(Phase 2 timeline: weeks 3-4 = ~10 working days)

---

## Documentation Needs

- README.md: Add Phase 2 configuration examples, feature descriptions
- phase2_migration_guide.md: How to upgrade from Phase 1, new config fields
- detection_model_guide.md: How to fine-tune detection model
- quality_metrics_guide.md: Understanding and interpreting quality scores
- resume_checkpoint_guide.md: How resumption works, checkpoint format

---

## Testing Strategy

### Unit Tests (30-40 new tests)
- Each module gets 5-8 tests covering happy path, edge cases, integration

### Integration Tests (10-15 new tests)
- Phase 2-specific end-to-end tests
- Combinations of features (temporal + detection + Poisson)
- Resume from checkpoint scenario

### Quality Assurance
- Visual inspection of temporal smoothing results
- Detection accuracy on test dataset
- Comparison with Phase 1 baseline (flicker reduction, quality improvement)

---

## Conclusion

Phase 2 enhances Phase 1 MVP with temporal coherence, automatic detection, advanced blending, and resumption capability. Focus is on quality improvement and usability while maintaining simplicity and backward compatibility. All features are optional (can disable via config) to preserve Phase 1 behavior for users satisfied with MVP.
