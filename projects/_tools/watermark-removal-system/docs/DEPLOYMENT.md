---
title: Docker Deployment Guide
type: project
tags: [project, active]
created: 2026-04-03
updated: 2026-04-03
status: active
maturity: growing
domain: knowledge-management
summary: ""
---

# Docker Deployment Guide

Complete guide for deploying the watermark removal system using Docker.

## Quick Start

### 1. Prerequisites

- Docker Engine >= 20.10
- Docker Compose >= 1.29
- GPU support (optional, but recommended)
  - NVIDIA Docker Runtime for GPU acceleration
  - GPU with 6GB+ VRAM (for inpainting models)

### 2. Environment Setup

Create `.env` file from template:

```bash
cp .env.example .env
```

Configure for your environment:

```bash
# ComfyUI settings
COMFYUI_HOST=comfyui
COMFYUI_PORT=8188

# GPU configuration
GPU_INDEX=0  # Use GPU 0 (or -1 for CPU)

# Model cache
MODELS_CACHE=./models

# Service ports
WATERMARK_REMOVAL_PORT=8000
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000

# Grafana credentials
GRAFANA_PASSWORD=secure_password_here
```

### 3. Build and Start Services

```bash
# Build Docker image
docker-compose build

# Start services
docker-compose up -d

# Check status
docker-compose ps
```

Verify services are healthy:

```bash
# Watermark removal service
curl http://localhost:8000/health

# ComfyUI service
curl http://localhost:8188/api/status
```

### 4. Run Pipeline

#### Using Docker CLI

```bash
docker run --rm \
  -v $(pwd)/data/input:/data/input:ro \
  -v $(pwd)/data/output:/data/output:rw \
  --network watermark-removal-network \
  watermark-removal:latest \
  --video /data/input/video.mp4 \
  --mask /data/input/mask.png \
  --output /data/output \
  --batch-size 4
```

#### Using docker-compose exec

```bash
docker-compose exec watermark-removal \
  python scripts/run_pipeline.py \
  --video /data/input/video.mp4 \
  --mask /data/input/mask.png \
  --output /data/output
```

#### Using docker-compose run

```bash
docker-compose run --rm watermark-removal \
  --video /data/input/video.mp4 \
  --mask /data/input/mask.png \
  --output /data/output
```

### 5. Access Services

| Service | URL | Port |
|---------|-----|------|
| Watermark Removal API | http://localhost:8000 | 8000 |
| ComfyUI Web UI | http://localhost:8188 | 8188 |
| Prometheus Metrics | http://localhost:9090 | 9090 |
| Grafana Dashboards | http://localhost:3000 | 3000 |

---

## Configuration

### Dataset Structure

Organize input data:

```
data/
├── input/
│   ├── video1.mp4
│   ├── video2.mp4
│   └── mask.png
├── output/
│   ├── video1_removed.mp4
│   └── video2_removed.mp4
└── checkpoints/
    └── phase2_checkpoint_1.pkl
```

### YAML Configuration File

Create `config/docker.yaml`:

```yaml
video_path: /data/input/video.mp4
mask_path: /data/input/mask.png
output_dir: /data/output

# Phase 1 settings
context_padding: 64
target_inpaint_size: 1024
blend_feather_width: 32

# Phase 2 settings
temporal_smooth_alpha: 0.3
use_adaptive_temporal_smoothing: true
use_poisson_blending: true
poisson_max_iterations: 100
max_watermarks_per_frame: 2
use_watermark_tracker: false

# Execution
batch_size: 4
comfyui_host: comfyui
comfyui_port: 8188
keep_intermediate: false
```

Pass config to container:

```bash
docker-compose exec watermark-removal \
  python scripts/run_pipeline.py \
  --config /data/config/docker.yaml
```

---

## GPU Support

### NVIDIA GPU Setup

1. Install NVIDIA Docker Runtime:

```bash
# Ubuntu/Debian
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update && sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker
```

2. Set GPU in `.env`:

```bash
GPU_INDEX=0  # Use GPU 0
# or
GPU_INDEX=-1  # Use all GPUs
```

3. Verify GPU is available:

```bash
docker run --rm --gpus all nvidia/cuda:11.8.0-runtime-ubuntu22.04 nvidia-smi
```

### Memory Optimization

For limited GPU memory:

```bash
# Reduce batch size
docker-compose run --rm watermark-removal \
  --batch-size 1  # Process 1 frame at a time

# Reduce target inpaint size
docker-compose run --rm watermark-removal \
  --target-inpaint-size 512

# Enable gradient checkpointing (if supported)
export CUDA_LAUNCH_BLOCKING=1
```

---

## Performance Tuning

### Batch Processing

```bash
# Optimal batch size depends on GPU VRAM:
# 6GB GPU: batch_size = 2-4
# 8GB GPU: batch_size = 4-8
# 12GB+ GPU: batch_size = 8-16

docker-compose run --rm watermark-removal \
  --video /data/input/video.mp4 \
  --batch-size 8 \
  --target-inpaint-size 1024
```

### Monitoring

#### Enable Prometheus metrics:

```bash
docker-compose --profile monitoring up -d
```

Access dashboards:
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000

#### View logs:

```bash
# Watermark removal logs
docker-compose logs -f watermark-removal

# ComfyUI logs
docker-compose logs -f comfyui

# All services
docker-compose logs -f
```

#### Resource usage:

```bash
docker stats watermark-removal comfyui
```

---

## Troubleshooting

### Common Issues

#### 1. ComfyUI not found/unavailable

```bash
# Check ComfyUI service status
docker-compose ps comfyui

# Check ComfyUI logs
docker-compose logs comfyui

# Restart ComfyUI
docker-compose restart comfyui

# Verify connectivity
docker-compose exec watermark-removal \
  curl -I http://comfyui:8188/api/status
```

#### 2. GPU out of memory

```bash
# Solution 1: Reduce batch size
docker-compose run --rm watermark-removal \
  --batch-size 1

# Solution 2: Reduce model size
docker-compose run --rm watermark-removal \
  --target-inpaint-size 512

# Solution 3: Clear model cache
docker volume rm watermark-removal_comfyui-data
```

#### 3. Slow processing

```bash
# Check GPU usage
docker exec comfyui nvidia-smi

# Monitor system resources
docker stats --no-stream

# Check for bottlenecks in logs
docker-compose logs watermark-removal | grep -i "time\|duration\|fps"
```

#### 4. File permissions issues

```bash
# Fix mount permissions
sudo chown -R $(id -u):$(id -g) data/
chmod -R 755 data/
```

### Health Checks

```bash
# Manual health check
docker-compose exec watermark-removal curl -f http://localhost:8000/health

# Check container health status
docker inspect watermark-removal --format='{{.State.Health}}'
```

---

## Advanced Configuration

### Multi-GPU Setup

```yaml
# docker-compose.yml
services:
  watermark-removal:
    environment:
      - CUDA_VISIBLE_DEVICES=0,1,2,3  # Use 4 GPUs
```

### Scaling

```bash
# Scale ComfyUI workers
docker-compose up -d --scale comfyui=3
```

### Custom Network

```bash
# Create external network for communication with other services
docker network create production-network

# Update docker-compose.yml
networks:
  watermark-removal-network:
    external:
      name: production-network
```

---

## Security

### Production Recommendations

1. **Use secrets management:**

```bash
# Create Docker secrets
echo "COMFYUI_API_KEY=secret" | docker secret create comfyui_key -

# Reference in docker-compose.yml
environment:
  - COMFYUI_API_KEY_FILE=/run/secrets/comfyui_key
```

2. **Limit resource usage:**

```yaml
services:
  watermark-removal:
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G
        reservations:
          cpus: '2'
          memory: 4G
```

3. **Use read-only mounts where possible:**

```bash
volumes:
  - ./config:/data/config:ro  # Read-only
  - ./data/input:/data/input:ro  # Read-only
  - ./data/output:/data/output:rw  # Read-write
```

4. **Set up firewall rules:**

```bash
# UFW example
sudo ufw allow 8188/tcp  # ComfyUI
sudo ufw allow 8000/tcp  # Watermark removal API
sudo ufw default deny incoming
```

---

## Deployment Examples

### Single Video Processing

```bash
docker-compose run --rm watermark-removal \
  --video /data/input/sample.mp4 \
  --mask /data/input/logo.png \
  --output /data/output \
  --batch-size 4
```

### Batch Processing with Config

```bash
docker-compose run --rm watermark-removal \
  --config /data/config/batch.yaml \
  --keep-intermediate
```

### With All Phase 2 Features

```bash
docker-compose run --rm watermark-removal \
  --video /data/input/video.mp4 \
  --mask /data/input/mask.json \
  --use-adaptive-temporal-smoothing \
  --use-poisson-blending \
  --use-watermark-tracker \
  --max-watermarks-per-frame 3 \
  --batch-size 8
```

### Resume from Checkpoint

```bash
docker-compose run --rm watermark-removal \
  --video /data/input/video.mp4 \
  --mask /data/input/mask.json \
  --use-checkpoints \
  --resume-from-checkpoint \
  --output /data/output
```

---

## Maintenance

### Cleanup

```bash
# Stop all services
docker-compose down

# Remove unused images
docker image prune -a

# Clear volumes
docker volume prune

# Full cleanup (WARNING: deletes all data)
docker-compose down -v
docker system prune -a
```

### Backup

```bash
# Backup models cache
tar -czf models-backup-$(date +%Y%m%d).tar.gz models/

# Backup checkpoints
tar -czf checkpoints-backup-$(date +%Y%m%d).tar.gz data/checkpoints/

# Backup output results
tar -czf output-backup-$(date +%Y%m%d).tar.gz data/output/
```

### Updating

```bash
# Pull latest image
docker-compose pull

# Rebuild with latest
docker-compose build --no-cache

# Restart services
docker-compose restart
```

---

## Support

For issues or questions:
1. Check logs: `docker-compose logs -f`
2. Review configuration in `.env`
3. Verify GPU availability: `nvidia-smi`
4. Check disk space: `df -h`
5. Open an issue with logs and configuration (sanitized)
