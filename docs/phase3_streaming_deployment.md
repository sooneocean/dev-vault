# Phase 3: Streaming Deployment Guide

## Overview

The Phase 3 streaming service enables long-running video processing with multiple concurrent clients, session isolation, and checkpoint-based resumption. This guide covers Docker deployment, session management, concurrent client handling, health monitoring, and checkpoint workflows.

## Architecture Overview

```
Client 1 ─┐
Client 2 ─┤─── Streaming Service ──┬─→ Frame Queue ──→ Processor
Client 3 ─┤                         │
Client 4 ─┘                         └─→ Session Manager (TTL tracking)
                                        └─→ Checkpoint Storage
```

**Key Components**:

- **Streaming Service** — HTTP/WebSocket server (FastAPI)
- **Session Manager** — Lifecycle management, concurrent session tracking
- **Queue Processor** — Background worker for frame processing
- **Checkpoint Storage** — Persisted crop regions and flow data

## Quick Start: Docker Deployment

### 1. Prerequisites

- Docker & Docker Compose installed
- NVIDIA Docker runtime (if GPU acceleration needed)
- 2GB+ free disk space for checkpoints
- 4GB+ free memory for buffer

### 2. Configuration

Create `.env` file:

```bash
# Streaming service
SERVICE_HOST=0.0.0.0
SERVICE_PORT=8000
SERVICE_WORKERS=4

# Storage
CHECKPOINT_DIR=/data/checkpoints
RESULT_DIR=/data/results

# Session management
SESSION_TTL_SEC=3600
RESULT_TTL_SEC=300
MAX_QUEUE_SIZE=100

# GPU (if available)
CUDA_VISIBLE_DEVICES=0
```

### 3. Docker Compose Configuration

File: `docker-compose.streaming.yml`

```yaml
version: "3.9"

services:
  streaming:
    build:
      context: .
      dockerfile: Dockerfile.streaming
    container_name: watermark-removal-streaming

    environment:
      - SERVICE_HOST=0.0.0.0
      - SERVICE_PORT=8000
      - CHECKPOINT_DIR=/data/checkpoints
      - CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-""}

    ports:
      - "8000:8000"

    volumes:
      - ./config:/app/config
      - streaming_checkpoints:/data/checkpoints
      - streaming_results:/data/results

    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s

    restart: unless-stopped

    # GPU support
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

volumes:
  streaming_checkpoints:
  streaming_results:
```

### 4. Build and Start

```bash
# Build image
docker-compose -f docker-compose.streaming.yml build

# Start service
docker-compose -f docker-compose.streaming.yml up -d

# View logs
docker-compose -f docker-compose.streaming.yml logs -f streaming

# Stop service
docker-compose -f docker-compose.streaming.yml down
```

### 5. Verify Service

```bash
# Health check
curl http://localhost:8000/health

# Expected response
{
  "status": "healthy",
  "sessions_active": 0,
  "version": "3.0"
}
```

## Session Management

### Creating a Session

Create a unique session for each video processing task:

```bash
curl -X POST http://localhost:8000/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "config": {
      "video_path": "/data/input.mp4",
      "mask_path": "/data/mask.json",
      "output_dir": "/data/output",
      "optical_flow_enabled": true,
      "optical_flow_resolution": "480"
    }
  }'

# Response
{
  "session_id": "sess_abc123def456",
  "created_at": "2026-03-31T10:00:00Z",
  "config": { ... }
}
```

### Session Lifecycle

```
Creation → Frame Submission → Processing → Completion → Cleanup
   |            |                |             |           |
   └─────────────────────────────────────────────────┘
              Session TTL: 3600s (1 hour default)
```

- **Idle timeout** — Session expires if no frames submitted for TTL duration
- **Auto-cleanup** — Expired sessions cleaned up automatically
- **Manual end** — Explicitly end session when done

### Ending a Session

```bash
curl -X POST http://localhost:8000/sessions/sess_abc123def456/end

# Response
{
  "session_id": "sess_abc123def456",
  "frames_processed": 120,
  "total_time_sec": 450.5,
  "summary": { ... }
}
```

Session end triggers:
1. Final metrics calculation
2. Checkpoint cleanup
3. Temporary files removal
4. Cache invalidation

### Monitoring Active Sessions

```bash
curl http://localhost:8000/sessions

# Response
{
  "active_sessions": 3,
  "sessions": [
    {
      "session_id": "sess_abc123...",
      "created_at": "2026-03-31T10:00:00Z",
      "frames_queued": 45,
      "frames_processed": 32,
      "last_activity": "2026-03-31T10:15:30Z"
    },
    ...
  ]
}
```

## Concurrent Client Handling

### Multiple Clients with Independent Sessions

Each client maintains separate session:

```python
# Client 1: Process video A
import requests

client1_session = requests.post(
    "http://localhost:8000/sessions",
    json={"config": config_a}
).json()
session_id_1 = client1_session["session_id"]

# Client 2: Process video B (concurrent)
client2_session = requests.post(
    "http://localhost:8000/sessions",
    json={"config": config_b}
).json()
session_id_2 = client2_session["session_id"]

# Both sessions process independently
for frame_id, frame_data in frames_a:
    requests.post(
        f"http://localhost:8000/sessions/{session_id_1}/frames",
        files={"frame": frame_data}
    )

for frame_id, frame_data in frames_b:
    requests.post(
        f"http://localhost:8000/sessions/{session_id_2}/frames",
        files={"frame": frame_data}
    )
```

### Queue Depth Management

Monitor queue depth to prevent backpressure:

```bash
# Get session status
curl http://localhost:8000/sessions/sess_abc123/status

# Response
{
  "session_id": "sess_abc123",
  "queue_depth": 45,
  "queue_max": 100,
  "queue_utilization_pct": 45,
  "frames_per_sec": 12.5,
  "est_time_to_drain_sec": 3.6
}
```

Backpressure strategy:

- If queue depth > 80% → throttle submission
- If queue depth > 95% → wait for drain before new frames
- Monitor queue drop if processing slower than submission

```python
# Smart submission with backpressure
while queue_utilization > 0.95:
    time.sleep(1)  # Wait for queue to drain

response = requests.post(
    f"http://localhost:8000/sessions/{session_id}/frames",
    files={"frame": frame_data}
)

if response.status_code == 503:
    # Queue overflow — back off
    time.sleep(5)
```

### Connection Pooling

For high-throughput clients, use connection pools:

```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

session = requests.Session()
retry = Retry(
    total=3,
    backoff_factor=0.5,
    status_forcelist=[503, 504]
)
adapter = HTTPAdapter(max_retries=retry, pool_connections=10)
session.mount("http://", adapter)

# High-throughput submission
for frame_id, frame_data in enumerate(frames):
    response = session.post(
        f"http://localhost:8000/sessions/{session_id}/frames",
        files={"frame": frame_data},
        timeout=30
    )
```

## Health Check Monitoring

### Built-in Health Endpoint

```bash
curl http://localhost:8000/health

# Response (200 OK)
{
  "status": "healthy",
  "timestamp": "2026-03-31T10:15:30Z",
  "sessions_active": 2,
  "queue_total_depth": 120,
  "uptime_sec": 3600,
  "version": "3.0"
}
```

### Prometheus Metrics (optional)

Enable metrics export:

```python
from prometheus_client import Counter, Histogram

frames_processed = Counter(
    "watermark_removal_frames_processed",
    "Total frames processed"
)

processing_time = Histogram(
    "watermark_removal_frame_processing_sec",
    "Processing time per frame"
)

# Export endpoint
curl http://localhost:8000/metrics
```

### Monitoring Strategy

**Kubernetes-ready health checks**:

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 30

readinessProbe:
  httpGet:
    path: /ready
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 10
```

**Alert conditions**:

- Health check fails → restart container
- Queue depth > 90% for >5min → scale up workers
- Memory usage > 80% → restart service
- Processed frames = 0 for >10min → investigate

## Queue Depth Tuning

### Configuration

File: `config/streaming.yaml`

```yaml
streaming:
  max_queue_size: 100          # Max frames queued
  queue_flush_interval_sec: 5  # Batch processing interval
  timeout_per_frame_sec: 300   # 5-minute timeout
  worker_count: 4              # Parallel processors
```

### Tuning Formula

```
Recommended queue size = (frames_per_sec * time_to_process_sec) * 1.5

Example:
- Input: 30 FPS video
- Processing: 8 seconds per frame
- Queue = (30 * 8) * 1.5 = 360 frames
```

**Scenarios**:

| Scenario | FPS | Proc Time | Queue | Workers |
|----------|-----|-----------|-------|---------|
| Real-time (30fps, fast) | 30 | 0.1s | 5 | 1 |
| Batch (30fps, slow) | 30 | 8s | 360 | 4 |
| High throughput | 60 | 2s | 180 | 8 |
| Low resource | 10 | 3s | 45 | 1 |

## Checkpoint Resumption Workflow

### Automatic Checkpointing

Checkpoints saved every N frames:

```yaml
persistence:
  checkpoint_interval_frames: 50  # Save every 50 frames
  checkpoint_dir: /data/checkpoints
  keep_last_n_checkpoints: 3     # Keep 3 versions
```

### Recovery from Checkpoint

**Scenario**: Service crashes after 250 frames

```bash
# 1. Restart service
docker-compose up -d

# 2. Resume session with checkpoint
curl -X POST http://localhost:8000/sessions/sess_abc123/resume \
  -H "Content-Type: application/json" \
  -d '{"from_checkpoint": true}'

# Response
{
  "session_id": "sess_abc123",
  "resumed": true,
  "frames_recovered": 250,
  "next_frame_id": 251
}

# 3. Continue submission from frame 251
for frame_id in range(251, total_frames):
    submit_frame(session_id, frame_id, frame_data[frame_id])
```

### Checkpoint File Structure

```
checkpoints/
├── sess_abc123def456/
│   ├── checkpoint_crops.json       # Crop regions
│   ├── checkpoint_flow.json        # Optical flow data
│   ├── checkpoint_metadata.json    # Session metadata
│   └── checkpoint_frame_250.pkl    # Last processed frame state
```

### Manual Checkpoint Inspection

```python
import json
from pathlib import Path

checkpoint_dir = Path("/data/checkpoints/sess_abc123")

# Load checkpoint
crops = json.loads((checkpoint_dir / "checkpoint_crops.json").read_text())
metadata = json.loads((checkpoint_dir / "checkpoint_metadata.json").read_text())

print(f"Frames processed: {metadata['frames_processed']}")
print(f"Last checkpoint: {metadata['last_checkpoint_time']}")
print(f"Total crops recovered: {len(crops)}")
```

## Performance Tuning

### CPU Optimization

```yaml
streaming:
  # Reduce GIL contention
  worker_count: 2              # Don't over-provision

  # Batch processing
  batch_size: 4
  queue_flush_interval_sec: 10  # Larger batches
```

### GPU Optimization

```yaml
streaming:
  worker_count: 4              # Parallel frame processing
  batch_size: 2                # Batch on GPU

inpaint:
  device: cuda
  dtype: float16              # Reduced memory
```

### Memory Optimization

```yaml
streaming:
  max_queue_size: 50           # Smaller queue
  result_cache_ttl_sec: 60     # Purge results quickly

persistence:
  checkpoint_compression: true # gzip checkpoints
```

## Troubleshooting

### Issue: "Queue overflow" errors

**Symptoms**: Clients get 503 Service Unavailable

**Solutions**:

1. **Increase queue size**:
```yaml
streaming:
  max_queue_size: 200
```

2. **Scale workers**:
```yaml
streaming:
  worker_count: 8
```

3. **Throttle client submission**:
```python
# Wait if queue utilization > 80%
while get_queue_depth() / max_queue > 0.8:
    time.sleep(1)
```

### Issue: Session expires mid-processing

**Symptoms**: "Session not found" error after hours of processing

**Solutions**:

1. **Increase TTL**:
```yaml
streaming:
  session_ttl_sec: 86400  # 24 hours
```

2. **Keep session alive**:
```python
# Heartbeat every 5 minutes
while processing:
    requests.post(f"http://localhost:8000/sessions/{session_id}/ping")
    time.sleep(300)
```

### Issue: High memory usage

**Symptoms**: Container exceeds memory limit, OOM kill

**Solutions**:

1. **Reduce queue size**:
```yaml
streaming:
  max_queue_size: 30
```

2. **Compress checkpoints**:
```yaml
persistence:
  checkpoint_compression: true
```

3. **Purge results aggressively**:
```yaml
streaming:
  result_ttl_sec: 60  # Purge after 1 minute
```

### Issue: Slow frame processing

**Symptoms**: Frames per second drops over time

**Solutions**:

1. **Check queue depth**:
```bash
curl http://localhost:8000/sessions/sess_abc123/status
```

2. **Monitor GPU memory**:
```bash
docker exec watermark-removal-streaming nvidia-smi
```

3. **Reduce batch size if OOM**:
```yaml
batch_size: 1
```

4. **Restart service if memory leak suspected**:
```bash
docker-compose restart
```

## Production Deployment Checklist

- [ ] Load testing completed (verify max throughput)
- [ ] Health checks configured and tested
- [ ] Alerting set up for queue depth and latency
- [ ] Backup strategy for checkpoints defined
- [ ] Log rotation configured
- [ ] GPU memory monitoring enabled
- [ ] Rate limiting implemented (if needed)
- [ ] Session cleanup tested
- [ ] Failover / restart behavior verified
- [ ] Documentation shared with ops team

## Example: End-to-End Deployment

```bash
#!/bin/bash
# Complete deployment script

set -e

echo "Building streaming service..."
docker-compose -f docker-compose.streaming.yml build

echo "Starting service..."
docker-compose -f docker-compose.streaming.yml up -d

echo "Waiting for health check..."
for i in {1..30}; do
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        echo "Service is healthy!"
        break
    fi
    echo "Waiting... ($i/30)"
    sleep 1
done

echo "Service URL: http://localhost:8000"
echo "Logs: docker-compose logs -f"
echo "Stop: docker-compose down"
```

## Further Reading

- Session Manager API: See `streaming/session_manager.py`
- Queue Processing: See `streaming/queue_processor.py`
- Checkpoint Serialization: See `persistence/crop_serializer.py`
