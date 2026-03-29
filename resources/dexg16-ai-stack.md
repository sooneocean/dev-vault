---
title: "DEXG16 AI 技術堆疊"
type: resource
tags: [llm]
created: "2026-03-28"
updated: "2026-03-30"
status: active
subtype: catalog
maturity: mature
domain: dev-environment
summary: "AI/ML 工具鏈 — PyTorch 2.11+cu126, Transformers, Ollama, LM Studio, Claude, OpenAI"
source: ""
related: ["[[dexg16-dev-environment]]", "[[dexg16-machine-specs]]", "[[dexg16-project-layout]]", "[[dexg16-ai-coding-tools]]", "[[dexg16-all-projects-catalog]]", "[[claude-code-configuration]]", "[[dexg16-git-and-github]]"]
---

# DEXG16 AI 技術堆疊

## 重點

### GPU 運算能力
- **CUDA Toolkit：** 12.4 + 12.6（雙版本安裝）
- **GPU：** RTX 4090 Laptop（約 16GB VRAM）
- **NVIDIA 驅動：** 32.0.15.9144

### 深度學習框架
| 套件 | 版本 | 說明 |
|------|------|------|
| PyTorch | 2.11.0+cu126 | 對應 CUDA 12.6 |
| Transformers | 5.2.0 | HuggingFace 模型框架 |
| Accelerate | 1.12.0 | 多 GPU / 混合精度訓練 |

### 大型語言模型（LLM）執行環境
| 工具 | 版本 | 用途 |
|------|------|------|
| Ollama | 0.18.3 | 本機 LLM 推論（2026-03-29 confirmed） |
| LM Studio | 已安裝 | 本機模型的圖形介面 |
| ChatWithRTX | 已安裝 | NVIDIA 本機 RAG 方案 |

### LLM SDK
| SDK | 版本 |
|-----|------|
| anthropic | 0.76.0 |
| openai | 2.16.0 |
| ollama（Python） | 0.6.1 |
| langchain | 1.2.13 |
| langchain-anthropic | 已安裝 |

### AI 應用框架
- **browser-use** — AI 瀏覽器自動化（使用 anthropic + openai + ollama）
- **deepagents** — 多 Agent 框架（使用 langchain）

### 本機 AI 專案（DEX_data/_AI/）
- `BasicSR` — 超解析度（Super-resolution）
- `COMFYUI` — Stable Diffusion 節點式工作流編輯器
- `SUPIR` — 圖片放大
- `IOPaint` / `INpaint-web` — 圖片修補（Inpainting）工具
- `YOLOLAB` — 物件偵測
- `Gausian_native_editor` — 3D 高斯（Gaussian Splatting）編輯器

### 相關筆記
- [[dexg16-machine-specs]]
- [[dexg16-dev-environment]]
- [[dexg16-ai-coding-tools]]

## 筆記
