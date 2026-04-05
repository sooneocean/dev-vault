---
title: Steps
type: project
tags: [project, active]
created: 2026-04-03
updated: 2026-04-03
status: active
maturity: growing
domain: knowledge-management
summary: ""
---

Show local LLM infrastructure status — Ollama models, VRAM usage, GPU health.

## Steps

1. **Ollama status:**
   ```bash
   ollama --version
   ollama list
   ollama ps
   ```

2. **GPU status:**
   ```bash
   nvidia-smi --query-gpu=name,memory.total,memory.used,memory.free,temperature.gpu,utilization.gpu --format=csv,noheader
   ```

3. **Present a summary table:**

| Item | Status |
|------|--------|
| Ollama version | (from --version) |
| Models installed | (count from list) |
| Models loaded | (from ps) |
| GPU | RTX 4090 Laptop |
| VRAM total | 16,376 MiB |
| VRAM used | (from nvidia-smi) |
| VRAM free | (from nvidia-smi) |
| GPU temp | (from nvidia-smi) |
| GPU utilization | (from nvidia-smi) |

4. **If models are loaded, show VRAM breakdown per model** (from `ollama ps`)

5. **Warn if:**
   - VRAM free < 4GB (other GPU apps may be running)
   - Ollama not running (`ollama ps` fails)
   - No local models installed
