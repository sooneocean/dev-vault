---
title: "本地 LLM 部署記錄"
type: resource
tags: [llm, hardware, reference, knowledge-management]
created: "2026-03-29"
updated: "2026-04-03"
status: active
subtype: reference
maturity: growing
domain: ai-engineering
summary: "RTX 4090 Laptop 16GB VRAM 上的本地模型部署、MCP 整合、任務路由決策"
related: ["[[tech-research-squad]]", "[[harness-engineering-research]]", "[[local-llm-task-routing]]"]
relation_map: "dexg16-ai-stack:extends"
---

# 本地 LLM 部署記錄

## 環境

| Item | Detail |
|------|--------|
| GPU | RTX 4090 Laptop (16 GB VRAM) |
| OS | Windows 11 Home 10.0.26200 |
| Ollama | v0.18.3 |
| CUDA | 12.4 + 12.6 |
| PyTorch | 2.11+cu126 |
| Date | 2026-03-29 |

## 部署的模型

### bge-m3 (Embedding)
- **磁碟大小:** 1.2 GB
- **VRAM:** ~1,500 MB
- **嵌入維度:** 1024
- **狀態:** 已部署，運作正常
- **用途:** 本地 RAG 管線的向量嵌入。多語言支援，適合中英文混合場景。

### phi4-mini (Classification)
- **磁碟大小:** 2.5 GB
- **VRAM:** ~3,750 MB
- **速度:** 19.7 tok/s (warm)
- **狀態:** 已部署，運作正常
- **用途:** 文本分類、標籤、路由。能正確分辨 agent-framework / rag / mcp / vector-db 等類別。
- **注意:** 輸出較冗長，需要結構化 system prompt 來控制格式。

### qwen3.5:9b (Summarize / Translate)
- **磁碟大小:** 6.6 GB
- **VRAM:** ~13,000 MB (near full)
- **速度:** 3.8-4.1 tok/s (含思考 tokens)
- **狀態:** 已部署，運作正常
- **用途:** 摘要生成、中英翻譯。品質優秀。
- **注意:** Qwen3.5 系列預設啟用深度思考（`<think>` tags），會產生大量隱藏 tokens。實際可見輸出精煉但總生成時間長。`/no_think` 無法完全關閉思考模式。

### qwen3.5:35b-a3b (Reasoning MoE)
- **磁碟大小:** 23 GB
- **VRAM:** ~13,400 MB (saturated, 僅剩 443 MiB)
- **速度:** 0.9-1.8 tok/s
- **狀態:** 已部署，但效能不足以用於互動場景
- **用途:** 深度推理。MoE 架構（35B 參數，3B 活躍）。
- **注意:** 16GB VRAM 下性能嚴重受限。1000 tokens 預算內全部消耗在思考過程，無法產出可見回答。建議僅用於離線批次處理，或改用雲端 API。

## VRAM 管理策略

```
可用 VRAM: ~14,100 MiB (16,376 - 2,200 OS baseline)

推薦共存組合:
  bge-m3 + phi4-mini = ~5,250 MiB  (OK, 充裕)
  bge-m3 + qwen3.5:9b = ~14,500 MiB  (勉強, 可能部分 offload)
  qwen3.5:35b-a3b = 單獨使用  (VRAM 飽和)
```

Ollama 預設 5 分鐘後自動卸載閒置模型。研究管線應按需載入：先跑 embedding + classification，再切換到 summarization。

## 建議的管線架構

```
文件輸入 → [bge-m3] 嵌入 → [phi4-mini] 分類/標籤 → [qwen3.5:9b] 摘要/翻譯 → [雲端 API] 深度推理
```

- **第一層 (bge-m3):** 快速嵌入，用於相似度檢索和去重
- **第二層 (phi4-mini):** 低延遲分類，決定文件類型和處理路徑
- **第三層 (qwen3.5:9b):** 中品質摘要和翻譯，適合批次處理
- **第四層 (雲端):** 複雜推理任務交給 Kimi K2.5 或 MiniMax M2.5

## 關鍵發現

1. **16GB VRAM 的甜蜜點是 bge-m3 + phi4-mini**：可共存，快速，覆蓋 embedding + classification
2. **qwen3.5:9b 適合批次摘要**：品質好但速度受限於思考模型的 token 開銷
3. **35B MoE 在筆電不實用**：理論上只需 3B 活躍參數，但實際 VRAM 佔用和推理速度都不理想
4. **思考模型的隱藏成本**：Qwen3.5 系列的 `<think>` tokens 佔總生成量 80%+，需要在 token 預算中考慮
5. **混合本地+雲端是最佳策略**：低延遲小任務本地跑，深度推理用雲端

## MCP 整合 (Phase 2)

### OllamaClaude MCP Server

| Item | Detail |
|------|--------|
| Server | OllamaClaude (Jadael fork, patched) |
| Location | `projects/tools/local-llm/ollama-claude/` |
| Config | `.claude/settings.local.json` (project-level) |
| Transport | stdio |
| Default model | phi4-mini (fast, 19.7 tok/s) |
| Fallback model | qwen3.5:9b (quality, 3.8 tok/s) |
| Timeout | 15 minutes (accounts for cold start) |

### Applied Patches

1. **DEFAULT_MODEL**: `mistral-small` -> `phi4-mini` (matched to local hardware)
2. **POSIX path normalization**: `/c/DEX_data` -> `C:/DEX_data` for Windows compatibility
3. **Task routing tools**: Added `ollama_classify`, `ollama_summarize`, `ollama_translate`, `ollama_route_info`
4. **TASK_ROUTING map**: Auto-routes tasks to optimal model based on benchmark data

### Available MCP Tools (15 total)

**String-based (7):** `ollama_generate_code`, `ollama_explain_code`, `ollama_review_code`, `ollama_refactor_code`, `ollama_fix_code`, `ollama_write_tests`, `ollama_general_task`

**File-aware (4):** `ollama_review_file`, `ollama_explain_file`, `ollama_analyze_files`, `ollama_generate_code_with_context`

**Vault task routing (4):** `ollama_classify`, `ollama_summarize`, `ollama_translate`, `ollama_route_info`

### Task Routing Decision Matrix

詳見 [[local-llm-task-routing]] — 完整的五維度路由規則和成本估算。

### MCP 端對端測試結果 (2026-03-30)

| Test | Tool | Result | Time |
|------|------|--------|------|
| Tools list | JSON-RPC `tools/list` | 15 tools listed | <1s |
| Route info | `ollama_route_info` | Decision matrix returned | <1s |
| Classification | `ollama_classify` | Correct category returned via phi4-mini | ~6s (warm) |
| Translation | Ollama API direct | Translated to Chinese (simplified instead of traditional) | ~6s |
| Cold start | phi4-mini first load | 19.6 tok/s but ~595s total | 10 min |

**Key findings:**
- Warm response time: 5-6 seconds per call (acceptable for delegation)
- Cold start: ~10 minutes (model loading from disk to GPU). Mitigated by `ollama ps` keep-alive
- Phi-4 Mini returns simplified Chinese for translation -> confirms qwen3.5:9b is the right choice for zh-TW tasks
- MCP stdio transport works reliably on Windows

### Slash Commands

- `/local-status` — Ollama models, VRAM usage, GPU health
- `/local-cost` — API cost savings estimation

## 完整效能數據

詳見 [[model-inventory|projects/tools/research-pipeline/local-llm/model-inventory.md]]

## 相關資源

- [[tech-research-squad]] - 技術研究小隊專案
- [[harness-engineering-research]] - Harness Engineering 研究
- [[compound-engineering-research]] - Compound Engineering 研究
- [[local-llm-task-routing]] - 任務路由規則
