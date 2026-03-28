---
title: "DEXG16 開發環境"
type: resource
tags: [dev-environment, toolchain, runtime]
created: "2026-03-28"
updated: "2026-03-28"
status: active
summary: "DEXG16 開發工具鏈 — Node 24, Python 3.14, CUDA 12.6, Rust, Docker"
source: ""
related: ["[[claude-code-dev-tools]]", "[[dexg16-machine-specs]]", "[[dexg16-ai-stack]]", "[[dexg16-project-layout]]", "[[dexg16-ai-coding-tools]]", "[[dexg16-all-projects-catalog]]"]
---

# DEXG16 開發環境

## 重點

### 核心執行環境
| 執行環境 | 版本 | 備註 |
|----------|------|------|
| Node.js | v24.12.0 | npm 10.8.2 |
| Python | 3.14.2 | pip 26.0.1，已安裝 309 個套件 |
| Rust | 1.94.1 | 透過 rustup/cargo 管理 |
| Java | OpenJDK 1.8 (Corretto) | Amazon Corretto 發行版 |
| Docker | 28.5.1 | Docker Desktop |
| Git | 2.47.1 | Git for Windows |
| Bash | 5.2.37 | MSYS2/Git Bash |

### 套件管理工具
- **npm** — 全域套件：pnpm 10.33、yarn 1.22、bun 1.3、typescript 6.0
- **pip** — 309 個套件（系統層級 Python 3.14）
- **cargo** — Rust 套件管理
- **chocolatey** — Windows 套件管理

### 編輯器與 IDE
| 工具 | 版本 |
|------|------|
| VS Code | 1.111.0 |
| Cursor | 2.6.21 |

### 建置工具
- CMake（已加入 PATH）
- CUDA Toolkit 12.4 + 12.6（雙版本安裝）
- NVIDIA Nsight Compute 2024.3.2
- ImageMagick 7.1.2
- PowerShell 7

### 重要 Python 套件
| 套件 | 版本 | 用途 |
|------|------|------|
| textual | 0.89.1 | TUI 框架（CSM 使用） |
| fastapi | 0.128.0 | Web API 框架 |
| streamlit | 1.54.0 | 資料應用框架 |
| gradio | 6.7.0 | 機器學習展示介面 |
| black | 26.1.0 | 程式碼格式化 |
| psutil | 7.2.2 | 系統監控 |

### 相關筆記
- [[dexg16-machine-specs]]
- [[dexg16-ai-stack]]
- [[dexg16-ai-coding-tools]]

## 筆記
