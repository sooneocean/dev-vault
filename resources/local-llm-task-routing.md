---
title: "本地 LLM 任務路由規則"
type: resource
subtype: config
tags: [llm, mcp, task-routing, ollama, reference, knowledge-management]
created: "2026-03-30"
updated: "2026-04-03"
status: active
maturity: growing
domain: ai-engineering
summary: "RTX 4090 Laptop 上本地模型任務路由決策矩陣 — 定義哪些任務走本地、哪些走 Claude API"
related: ["[[local-llm-deployment]]", "[[dexg16-ai-stack]]"]
relation_map: "local-llm-deployment:extends, dexg16-ai-stack:extends"
---

# 本地 LLM 任務路由規則

## Overview

定義 Claude Code 70/30 混合策略的任務路由決策矩陣。根據 Phase 1 benchmark 數據，將任務按五個維度（品質需求、隱私需求、延遲敏感度、批量大小、推理複雜度）分配到最適合的模型。

透過 OllamaClaude MCP Server 的 `ollama_route_info` 工具可即時查看此矩陣。

## Decision Matrix

### 本地模型路由表

| 任務類型 | 模型 | 速度 | VRAM | 適用場景 | 品質 vs Claude |
|---------|------|------|------|---------|---------------|
| **分類/標籤** | phi4-mini | 19.7 tok/s | 3.7 GB | Vault 筆記分類、topic tagging | ~85% (sufficient) |
| **簡單問答** | phi4-mini | 19.7 tok/s | 3.7 GB | 格式轉換、結構化輸出 | ~80% |
| **初步 Code Review** | phi4-mini | 19.7 tok/s | 3.7 GB | 基礎檢查、Claude 做最終 review | ~70% |
| **程式碼解釋** | phi4-mini | 19.7 tok/s | 3.7 GB | 簡單函式/模組解釋 | ~75% |
| **Embedding** | bge-m3 | N/A | 1.5 GB | 向量嵌入、相似度搜索 | 專用模型 |
| **摘要生成** | qwen3.5:9b | 3.8 tok/s | 13 GB | 批次筆記摘要 | ~85% (high quality) |
| **中英翻譯** | qwen3.5:9b | 3.8 tok/s | 13 GB | 批次翻譯 | ~80% |

### Claude API 保留任務

| 任務類型 | 原因 |
|---------|------|
| 複雜推理 & 規劃 | 需要 1M context + 高品質推理 |
| 架構設計 | 全局理解、跨檔案分析 |
| 最終 Code Review | 需要深度理解和精確判斷 |
| 長文脈絡分析 | 1M context window 優勢 |
| MCP 工具編排 | Agent 協調能力 |
| 創意寫作 | 品質要求最高 |
| Agent 系統設計 | 需要高品質推理 |

## 五維度路由邏輯

| 維度 | 本地 | Claude API | 說明 |
|------|------|-----------|------|
| 品質需求 | 低~中 | 高 | 分類/標籤可容忍偶爾錯誤；架構設計不行 |
| 隱私需求 | 高 | 低 | 敏感資料只走本地 |
| 延遲敏感 | phi4-mini 場景 | 不敏感 | 互動場景用 phi4-mini (19.7 tok/s) |
| 批量大小 | 大批次 | 單次/少量 | 批量摘要/翻譯走本地省費用 |
| 推理複雜度 | 低 | 高 | 簡單分類本地、複雜推理雲端 |

## VRAM 管理策略

### 推薦的並發組合

| Config | 組合 | VRAM | 適用 |
|--------|------|------|------|
| **A (推薦)** | bge-m3 + phi4-mini | ~5.25 GB | 日常互動：分類 + embedding |
| **B (批次)** | bge-m3 + qwen3.5:9b | ~14.5 GB | 批次作業：摘要 + 翻譯 |

### 切換規則

1. 日常使用 Config A（低 VRAM，快速回應）
2. 需要批次摘要/翻譯時，先 `ollama stop phi4-mini`，再載入 qwen3.5:9b
3. Ollama 預設 5 分鐘自動卸載閒置模型
4. 跑 GPU 密集任務前（ComfyUI 等），先用 `/local-status` 檢查 VRAM

## MCP 工具對照

| MCP Tool | 路由模型 | 用途 |
|----------|---------|------|
| `ollama_classify` | phi4-mini | 文本分類 |
| `ollama_summarize` | qwen3.5:9b | 摘要生成 |
| `ollama_translate` | qwen3.5:9b | 中英翻譯 |
| `ollama_general_task` | phi4-mini (default) | 通用任務 |
| `ollama_review_file` | phi4-mini | 初步 code review |
| `ollama_explain_code` | phi4-mini | 程式碼解釋 |
| `ollama_route_info` | (none) | 查看路由矩陣 |

## 成本估算

| 項目 | 本地 | Claude API (估) |
|------|------|----------------|
| Embedding (1K tokens) | $0.00 | ~$0.0001 |
| 分類 (per call) | $0.00 | ~$0.003 (Haiku) |
| 摘要 (per call) | $0.00 | ~$0.01 (Sonnet) |
| 翻譯 (per call) | $0.00 | ~$0.01 (Sonnet) |
| 電費 (RTX 4090, ~150W) | ~$5-10/月 | N/A |

預估 70% 任務量本地化後，每月可節省 $20-50 API 費用（取決於使用頻率）。

## Related

- [[local-llm-deployment]] - 部署記錄和效能數據
- [[dexg16-ai-stack]] - 硬體和 AI 工具棧
