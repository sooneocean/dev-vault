# Local Model Inventory

> RTX 4090 Laptop (16GB VRAM) | Ollama 0.18.3 | CUDA 12.4+12.6
> Benchmarked: 2026-03-29

## Model Matrix

| Model | Disk Size | VRAM (loaded) | tok/s (warm) | Use Case | Status |
|-------|-----------|---------------|--------------|----------|--------|
| bge-m3 | 1.2 GB | ~1,500 MB | N/A (embedding) | Embedding (1024-dim) | Deployed |
| phi4-mini | 2.5 GB | ~3,750 MB | 19.7 tok/s | Classification / Tagging | Deployed |
| qwen3.5:9b | 6.6 GB | ~13,000 MB | 3.8-4.1 tok/s | Summarize / Translate | Deployed |
| qwen3.5:35b-a3b | 23 GB | ~13,400 MB | 0.9-1.8 tok/s | Reasoning (MoE, heavy thinking) | Deployed (slow) |

**Total disk: ~33.3 GB**

## VRAM Budget (16 GB = 16,376 MiB)

- **Baseline (idle):** ~2,200 MiB (OS + display driver)
- **Available for models:** ~14,100 MiB
- **bge-m3 loaded:** ~3,700 MiB total (1,500 MB model)
- **phi4-mini loaded:** ~7,400 MiB total (3,750 MB model)
- **qwen3.5:9b loaded:** ~15,200 MiB total (near full VRAM)
- **qwen3.5:35b-a3b loaded:** ~15,600 MiB total (VRAM saturated, likely CPU offload)

### Concurrency

Only one large model can be resident in VRAM at a time. Ollama auto-unloads idle models (default 5min timeout).

- **bge-m3 + phi4-mini**: Can co-exist (~5,250 MB combined)
- **bge-m3 + qwen3.5:9b**: Tight fit, may partially offload
- **qwen3.5:35b-a3b**: Must run alone, uses all available VRAM

## Benchmark Results

### bge-m3 (Embedding)
- **Dimension:** 1024
- **Cold start:** ~48s (first load to VRAM)
- **Warm latency:** <1s per embedding
- **Quality:** Multilingual, SOTA for its size
- **Notes:** Ideal for local RAG pipeline; fast and lightweight

### phi4-mini (Classification)
- **Cold start:** ~49s (includes model load)
- **Warm inference:** 2.3s for classification task
- **tok/s:** 19.7 (warm)
- **Quality:** Correctly classified "LanceDB" as vector-db; some verbosity in output
- **Notes:** Needs structured system prompt to control output format. Best for quick tagging/routing tasks.

### qwen3.5:9b (Summarize / Translate)
- **Cold start:** ~30s (model load only, no prior model in VRAM)
- **Warm inference:** 28-157s (varies with thinking depth)
- **tok/s:** 3.6-4.1 (includes hidden thinking tokens)
- **Quality:** Excellent summaries, accurate Chinese translation
- **Notes:** Heavy use of `<think>` reasoning tokens inflates total generation. Actual visible output is concise and high quality. `/no_think` flag doesn't fully suppress thinking.

### qwen3.5:35b-a3b (Reasoning MoE)
- **Cold start:** ~112s (VRAM load + possible CPU offload)
- **Warm inference:** 215-606s for 200-1000 tokens
- **tok/s:** 0.9-1.8 (very slow)
- **VRAM:** Saturates 16GB, ~443 MiB free when loaded
- **Quality:** Deep reasoning but all output consumed by thinking tokens within 1000 token budget
- **Notes:** Not practical for interactive use on 16GB VRAM. Consider for batch/offline reasoning only, or use cloud models instead.

## Recommended Pipeline Configuration

```
Input Document
    |
    v
[bge-m3] -- Embedding (fast, local)
    |
    v
[phi4-mini] -- Classify/Tag/Route (~20 tok/s)
    |
    v
[qwen3.5:9b] -- Summarize/Translate (~4 tok/s)
    |
    v
[Cloud API] -- Complex reasoning (replace 35b-a3b for interactive use)
```

## Key Findings

1. **bge-m3 + phi4-mini** are the sweet spot for local inference: fast, fits in VRAM together
2. **qwen3.5:9b** is capable but slow due to thinking overhead; best for batch processing
3. **qwen3.5:35b-a3b** is impractical on 16GB laptop VRAM for interactive use (<2 tok/s)
4. **Thinking models** (qwen3.5 family) consume many hidden tokens; budget 3-5x more than visible output
5. **VRAM management** is critical: only one 9B+ model should be loaded at a time
