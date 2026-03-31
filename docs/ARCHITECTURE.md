# Watermark Removal System — Architecture Documentation

## Overview

This document describes the complete architecture of the Dynamic Watermark Removal System across all three phases. The system uses a modular, layered design with clear separation of concerns and async/await patterns for efficient resource utilization.

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     CLIENT LAYER (CLI/API)                      │
├─────────────────────────────────────────────────────────────────┤
│ - Command-line interface (run_pipeline.py)                      │
│ - Streaming service API (FastAPI)                               │
│ - Configuration validation (ProcessConfig)                       │
└────────────────┬────────────────────────────────────┬────────────┘
                 │                                    │
        ┌────────▼─────────┐              ┌─────────▼────────┐
        │  PIPELINE LAYER  │              │  SESSION MANAGER │
        ├──────────────────┤              ├──────────────────┤
        │ - Core pipeline  │              │ - Session lifecycle
        │ - Orchestration  │              │ - Concurrent mgmt
        │ - Error handling │              │ - TTL management
        └────────┬─────────┘              └────────┬─────────┘
                 │                                 │
    ┌────────────┼─────────────────────────────────┘
    │            │
    ▼            ▼
┌──────────────────────────────────────────────────────────────┐
│                    PROCESSING LAYERS                         │
├──────────────────────────────────────────────────────────────┤
│
│  PHASE 1: PREPROCESSING
│  ├─ Frame Extraction      (frame_extractor.py)
│  ├─ Mask Loading          (mask_loader.py)
│  ├─ Crop Handling         (crop_handler.py)
│  └─ Region Detection      (automatic region derivation)
│
│  PHASE 2: DETECTION & STITCHING
│  ├─ Ensemble Detection    (ensemble_detection.py)
│  ├─ Edge Blending         (edge_blending.py)
│  ├─ Poisson Blending      (poisson_blender.py)
│  ├─ Stitch Handler        (stitch_handler.py)
│  ├─ Temporal Smoothing    (temporal_smoother.py)
│  └─ Checkpoint System     (crop_serializer.py)
│
│  PHASE 3: ADVANCED FEATURES
│  ├─ Optical Flow          (optical_flow_processor.py)
│  ├─ Flow-based Warping    (warp_region_boundary)
│  ├─ Streaming Support     (session_manager, queue_processor)
│  ├─ Label Studio Export   (label_studio_exporter.py)
│  └─ Optuna Optimization   (optuna_optimizer.py)
│
└──────────────────────────────────────────────────────────────┘
    │                                                    │
    │  (Batch processing, parallelization)             │
    │                                                    │
    ▼                                                    ▼
┌──────────────────────────────────────────────────────────────┐
│                   INPAINTING SERVICE                         │
├──────────────────────────────────────────────────────────────┤
│ - ComfyUI client (async HTTP/WebSocket)                      │
│ - Flux workflow building (flux_workflow_builder.py)          │
│ - Batch orchestration with configurable batching             │
│ - Timeout and error recovery                                 │
└──────────────────────────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────────────────────────┐
│                 PERSISTENCE & STORAGE LAYERS                 │
├──────────────────────────────────────────────────────────────┤
│ - Image I/O (image_io.py)                                    │
│ - Checkpoint I/O (crop_serializer.py)                        │
│ - Video encoding (video_encoder.py)                          │
│ - File system operations (Pathlib)                           │
└──────────────────────────────────────────────────────────────┘
```

## Data Flow Architecture

### Phase 1: Preprocessing

```
Input Video (MP4)
    │
    ├─→ Frame Extraction (FFmpeg)
    │   └─→ PNG Frames (1920x1080, uint8, 3-channel)
    │
    ├─→ Mask Loading
    │   ├─ Static (PNG/JPEG) → Single region
    │   └─ Dynamic (JSON) → Per-frame bounding boxes
    │
    ├─→ Crop Handling
    │   ├─ Extract watermark region
    │   ├─ Add context padding
    │   ├─ Generate CropRegion metadata
    │   └─ Store in-memory with frame association
    │
    └─→ Output: Cropped regions + CropRegion objects
            (ready for inpainting)
```

**Key objects**:
- `Frame`: Full-resolution image data (numpy uint8 array)
- `CropRegion`: Metadata for watermark region
  - Original coordinates (x, y, w, h)
  - Context coordinates
  - Scale factor, padding
  - Frame ID

### Phase 2: Core Processing

```
Cropped Regions
    │
    ├─→ Inpainting (ComfyUI)
    │   ├─ Batch submission (2-8 crops)
    │   ├─ Flux model inference (5-15s per batch)
    │   └─ Inpainted results (same size as crops)
    │
    ├─→ Detection (optional, Phase 2)
    │   ├─ Ensemble YOLO voting
    │   ├─ Generates detection confidence
    │   └─ Used for boundary adjustment
    │
    ├─→ Edge Blending
    │   ├─ Distance-based feather mask
    │   ├─ Gaussian blur for smooth transition
    │   └─ Multi-channel blend with inpainted regions
    │
    ├─→ Stitch Handler
    │   ├─ Map crop coordinates back to frame
    │   ├─ Apply blended result
    │   └─ Generate full stitched frame
    │
    ├─→ Temporal Smoothing (optional, Phase 2)
    │   ├─ Track region motion across frames
    │   ├─ Smooth boundary positions
    │   └─ Reduce inter-frame flicker
    │
    └─→ Output: Processed frames (1920x1080, uint8)
```

### Phase 3: Advanced Processing

```
Processed Frames + Checkpoint
    │
    ├─→ Optical Flow (optional, Phase 3)
    │   ├─ Compute flow between adjacent frames
    │   ├─ Downsample to 480p or 1080p
    │   ├─ Warp region boundaries according to flow
    │   ├─ Blend with original for smoothness
    │   └─ Generate FlowData with confidence
    │
    ├─→ Streaming Integration (Phase 3)
    │   ├─ Session-based processing
    │   ├─ Queue-based frame submission
    │   ├─ Independent session isolation
    │   └─ TTL-based cleanup
    │
    ├─→ Annotation Export (Phase 3)
    │   ├─ Export frames to Label Studio
    │   ├─ COCO JSON or YOLO format
    │   └─ Model retraining integration
    │
    ├─→ Checkpoint Persistence (Phase 3)
    │   ├─ Save crop regions (v2.0 format)
    │   ├─ Save optical flow data
    │   ├─ Save session metadata
    │   └─ Enable resumption from checkpoint
    │
    └─→ Output: Enhanced frames ready for encoding
```

### Phase 4: Encoding

```
Processed Frames
    │
    ├─→ Video Encoding (FFmpeg)
    │   ├─ Codec selection (h264, h265, vp9)
    │   ├─ Quality control (CRF: 0-51)
    │   ├─ Frame rate preservation
    │   └─ Resolution output
    │
    └─→ Output: Final MP4 (or WebM/mkv)
```

## Component Architecture

### Core Types (types.py)

```python
# Configuration and metadata
class ProcessConfig:
    video_path: Path
    mask_path: Path
    output_dir: Path
    batch_size: int
    optical_flow_enabled: bool
    optical_flow_weight: float
    ensemble_detection_enabled: bool
    # ... 20+ parameters

class CropRegion:
    x, y, w, h: int  # Original coordinates
    scale_factor: float
    context_x, context_y, context_w, context_h: int
    pad_left, pad_top, pad_right, pad_bottom: int

class ProcessMetrics:
    quality: float  # LPIPS
    temporal_consistency: float
    boundary_smoothness: float
    processing_time_ms: float
    # ... per-phase timings

class FlowData:
    frame_pair_id: tuple[int, int]
    flow_field: np.ndarray  # (H, W, 2)
    confidence: float
    metadata: Dict[str, Any]
```

### Pipeline (pipeline.py)

Main orchestration class:

```python
class Pipeline:
    def __init__(self, config: ProcessConfig):
        self.config = config
        self.metrics = ProcessMetrics()

    async def run(self) -> ProcessMetrics:
        # Phase 1: Preprocessing
        frames = await self.extract_frames()
        crop_regions = await self.extract_crops(frames)

        # Phase 2: Processing
        inpainted = await self.inpaint_crops(crop_regions)
        processed = await self.stitch_and_blend(inpainted)

        # Phase 3: Advanced (if enabled)
        if self.config.optical_flow_enabled:
            processed = await self.apply_optical_flow(processed)

        # Phase 4: Encoding
        await self.encode_video(processed)

        return self.metrics
```

### Session Manager (streaming/session_manager.py)

Manages concurrent video processing sessions:

```python
class SessionManager:
    def __init__(self, result_ttl_sec=300, session_ttl_sec=3600):
        self.sessions = {}  # session_id → Session
        self.result_ttl_sec = result_ttl_sec
        self.session_ttl_sec = session_ttl_sec

    async def create_session(config: ProcessConfig) -> str:
        # Create isolated session with TTL
        session_id = generate_session_id()
        session = Session(config, self.session_ttl_sec)
        self.sessions[session_id] = session
        return session_id

    async def get_session(session_id: str) -> Optional[Session]:
        # Return session if not expired
        session = self.sessions.get(session_id)
        if session and session.is_expired():
            del self.sessions[session_id]
            return None
        return session
```

### Queue Processor (streaming/queue_processor.py)

Background worker for frame processing:

```python
class BackgroundTaskRunner:
    def __init__(self, session: Session, max_queue_size=100):
        self.queue = asyncio.Queue(maxsize=max_queue_size)
        self.session = session

    async def start(self):
        # Start background worker
        asyncio.create_task(self.process_queue())

    async def submit_frame(self, frame_id: int, frame_data: bytes) -> bool:
        # Non-blocking frame submission
        try:
            self.queue.put_nowait((frame_id, frame_data))
            return True
        except asyncio.QueueFull:
            return False

    async def process_queue(self):
        # Worker loop
        while not self.stop_event.is_set():
            frame_id, frame_data = await self.queue.get()
            result = await self.process_frame(frame_id, frame_data)
            self.session.add_frame_result(frame_id, result)
```

### Optical Flow (optical_flow/optical_flow_processor.py)

Temporal alignment using RAFT:

```python
class OpticalFlowProcessor:
    def __init__(self, resolution: str = "480", weight: float = 0.5):
        self.model = raft_large(pretrained=True)
        self.resolution = resolution
        self.weight = weight

    def compute_flow(self, frame1: np.ndarray, frame2: np.ndarray) -> FlowData:
        # Compute optical flow between frames
        flow_field = self.model(frame1, frame2)
        confidence = compute_flow_confidence(flow_field)
        return FlowData(
            frame_pair_id=(frame1_id, frame2_id),
            flow_field=flow_field,
            confidence=confidence
        )

    def warp_region_boundary(self, region: CropRegion, flow: FlowData) -> CropRegion:
        # Warp region boundary according to flow
        # Apply blend: warped * weight + original * (1 - weight)
        warped = self.apply_flow_warp(region, flow.flow_field)
        return self.blend_boundaries(region, warped, self.weight)
```

### Checkpoint System (persistence/crop_serializer.py)

Persistence for resumption:

```python
class CropRegionSerializer:
    @staticmethod
    def save_checkpoint(
        crop_regions: Dict[int, CropRegion],
        checkpoint_dir: Path,
        flow_data: Optional[Dict[str, FlowData]] = None
    ):
        # Save in v2.0 format with flow support
        checkpoint_dir.mkdir(exist_ok=True)

        # Save crops
        crops_json = {
            "version": "2.0",  # v2.0 = with flow support
            "timestamp": datetime.now().isoformat(),
            "crops": {
                str(frame_id): crop.to_dict()
                for frame_id, crop in crop_regions.items()
            }
        }
        (checkpoint_dir / "checkpoint_crops.json").write_text(json.dumps(crops_json))

        # Save flow data
        if flow_data:
            flow_json = {
                "version": "1.0",
                "data": {
                    k: v.to_dict() for k, v in flow_data.items()
                }
            }
            (checkpoint_dir / "checkpoint_flow.json").write_text(json.dumps(flow_json))

    @staticmethod
    def load_checkpoint(checkpoint_dir: Path) -> Tuple[Dict[int, CropRegion], Optional[Dict]]:
        # Load crops and flow (backward compatible with v1.0)
        crops_path = checkpoint_dir / "checkpoint_crops.json"
        crops_data = json.loads(crops_path.read_text())

        crop_regions = {
            int(frame_id): CropRegion.from_dict(data)
            for frame_id, data in crops_data.get("crops", {}).items()
        }

        # Load flow if exists
        flow_data = None
        flow_path = checkpoint_dir / "checkpoint_flow.json"
        if flow_path.exists():
            flow_json = json.loads(flow_path.read_text())
            flow_data = {k: FlowData.from_dict(v) for k, v in flow_json.get("data", {}).items()}

        return crop_regions, flow_data
```

## Error Handling Strategy

### Layered Error Handling

```
┌─────────────────────────┐
│  CLI Layer              │  User-friendly error messages
│  try/except main()      │
└────────┬────────────────┘
         │
┌────────▼────────────────┐
│  Pipeline Layer         │  Graceful degradation
│  skip_errors flags      │  Fallback modes
└────────┬────────────────┘
         │
┌────────▼────────────────┐
│  Component Layer        │  Specific exceptions
│  validate inputs        │  Retry logic
│  timeout handling       │
└────────┬────────────────┘
         │
┌────────▼────────────────┐
│  External Services      │  Circuit breaker
│  (ComfyUI, Label Studio)│  Exponential backoff
└─────────────────────────┘
```

### Exception Hierarchy

```python
# Base exception
class WatermarkRemovalError(Exception):
    pass

# Phase-specific
class PreprocessingError(WatermarkRemovalError):
    pass

class InpaintingError(WatermarkRemovalError):
    pass

class PostprocessingError(WatermarkRemovalError):
    pass

class StreamingError(WatermarkRemovalError):
    pass

# skip_errors handling
if config.skip_errors_in_preprocessing:
    try:
        frame = extract_frame(frame_id)
    except PreprocessingError as e:
        logger.warning(f"Skipping frame {frame_id}: {e}")
        continue  # Skip to next frame
```

## Concurrency Model

### Async/Await Architecture

```
Event Loop (single-threaded)
├─ Frame extraction (I/O-bound)
├─ Crop extraction (CPU-bound, small)
├─ Inpainting submission (I/O-bound, ComfyUI)
├─ Stitch & blend (CPU-bound, parallelizable)
├─ Session management (I/O-bound)
└─ Checkpoint I/O (I/O-bound)

GPU-accelerated (separate execution):
├─ Optical flow computation
├─ Ensemble detection
└─ ComfyUI Flux inpainting (external)
```

### Parallelization Strategy

1. **Batch Inpainting**: 2-8 crops submitted concurrently to ComfyUI
2. **Frame Extraction**: asyncio.gather() for parallel video reading
3. **Stitching**: Per-frame operations (single-threaded sufficient)
4. **Session Processing**: Independent sessions via asyncio tasks

### Lock-Free Design

- Session isolation eliminates need for locks
- Immutable frame data (numpy arrays) safe for concurrent reads
- Queue-based communication (asyncio.Queue)

## Deployment Architecture

### Single Machine

```
┌────────────────────────────────────┐
│  Docker Container                  │
├────────────────────────────────────┤
│ Streaming Service (port 8000)      │
│ Queue Processor (worker threads)   │
│ Checkpoint Storage (/data/checkpt) │
│ Result Cache (/data/results)       │
└────────────────────────────────────┘
         │
         ├─→ ComfyUI (localhost:8188)
         ├─→ Label Studio (localhost:8080)
         └─→ Volume mounts
```

### Distributed Setup (Kubernetes)

```
┌─────────────────────────────────────┐
│  Kubernetes Cluster                 │
├─────────────────────────────────────┤
│ Streaming Service (Deployment)      │
│  └─ 3 replicas, load-balanced       │
│                                     │
│ Session Manager (Stateful)          │
│  └─ PostgreSQL backend              │
│                                     │
│ ComfyUI (StatefulSet)               │
│  └─ GPU nodes                       │
│                                     │
│ Label Studio (Deployment)           │
│  └─ PostgreSQL + NFS               │
└─────────────────────────────────────┘
```

## Performance Characteristics

### Latency Breakdown (per frame, 1080p)

| Component | Time | % of Total | Parallelizable |
|-----------|------|-----------|-----------------|
| Extraction | 150ms | 2% | Yes (batch) |
| Preprocessing | 50ms | 0.6% | Yes |
| Inpainting | 8000ms | 95% | Yes (batch) |
| Optical Flow | 150ms | 1.8% | Yes |
| Postprocessing | 100ms | 1.2% | Yes |
| **Total** | **8450ms** | **100%** | - |

**Estimated FPS**: 0.12 FPS (8.5s/frame)
- Batch size 4: ~2 FPS (16 frames / 8.5s)
- Batch size 8: ~3.8 FPS (32 frames / 8.5s)

### Memory Usage

| Component | Memory | Notes |
|-----------|--------|-------|
| Frame buffer | 6MB | 1920x1080 RGB uint8 |
| Crop buffer (4) | 8MB | 512x512 per crop |
| Inpainted buffer | 8MB | Results cache |
| Flow computation | 200MB | RAFT model (GPU) |
| Process state | <100MB | Metadata, checkpoints |
| **Total** | **~230MB** | GPU: 6GB for Flux |

## Testing Architecture

### Test Layers

1. **Unit Tests** (170+)
   - Component-level (crop handler, blending, etc.)
   - Config validation
   - Metrics calculation

2. **Integration Tests** (30+)
   - Phase 2-3 feature interaction
   - Backward compatibility
   - Checkpoint resumption
   - Streaming lifecycle

3. **End-to-End Tests**
   - Full pipeline with test video
   - Quality metrics verification
   - Performance benchmarks

### Test Data

- Synthetic frames (480p, 1080p)
- Test masks (static PNG, dynamic JSON)
- Minimal video files (placeholders for I/O tests)
- Checkpoint files (v1.0, v2.0 formats)

## Summary

The architecture provides:

1. **Modularity** — Independent, testable components
2. **Concurrency** — Async/await for efficient resource use
3. **Extensibility** — Phase-based feature addition
4. **Reliability** — Error handling, graceful degradation
5. **Observability** — Metrics, logging, checkpointing
6. **Scalability** — Session isolation, distributed ready
