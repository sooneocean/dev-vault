---
title: "DEXG16 AI 程式設計工具"
type: resource
tags: [claude-code]
created: "2026-03-28"
updated: "2026-03-29"
status: active
subtype: catalog
maturity: mature
domain: ai-engineering
summary: "AI 輔助程式設計工具 — Claude Code, Cursor, Codex CLI, Gemini CLI, Cline"
source: ""
related: ["[[claude-code-dev-tools]]", "[[claude-session-manager]]", "[[dexg16-ai-stack]]", "[[dexg16-dev-environment]]", "[[dexg16-machine-specs]]", "[[dexg16-all-projects-catalog]]", "[[claude-code-configuration]]", "[[dexg16-git-and-github]]", "[[cli-update-fields-flag]]"]
---

# DEXG16 AI 程式設計工具

## 重點

### AI 程式設計助手
| 工具 | 版本 | 類型 | 備註 |
|------|------|------|------|
| **Claude Code** | 2.1.86 | CLI | 主力工具，Opus 4.6（1M context） |
| **Cursor** | 2.6.21 | IDE | 基於 VS Code 的 AI IDE |
| **OpenAI Codex CLI** | 0.116.0 | CLI | `@openai/codex` npm 套件 |
| **Gemini CLI** | 0.35.0 | CLI | `@google/gemini-cli` npm 套件 |
| **Cline** | 2.9.0 | CLI | npm 套件 |
| **Qoder CLI** | 0.1.35 | CLI | `@qoder-ai/qodercli` npm 套件 |

### 全域安裝的 MCP 伺服器
| 伺服器 | 套件名稱 |
|--------|----------|
| 檔案系統（Filesystem） | `@modelcontextprotocol/server-filesystem` |
| 循序思考（Sequential Thinking） | `@modelcontextprotocol/server-sequential-thinking` |
| 瀏覽器自動化（Puppeteer） | `puppeteer-mcp-server` |
| Obsidian Agent | `obsidian-agent`（本機連結） |

### 程式碼分析
- **ast-grep** — `@ast-grep/cli` + `@ast-grep/napi` 0.40.5（結構化程式碼搜尋）
- **TypeScript** — 6.0.2（全域安裝）

### 部署工具
- **Vercel CLI** — 48.1.1（全域 npm）
- **Docker** — 28.5.1

### Claude Code 設定概要
- 模型：Opus 4.6（1M context）
- 全域指令：`~/.claude/CLAUDE.md`
- 語言政策：繁體中文對話、英文程式碼
- Commit 風格：Conventional commits
- SOP 管線：S0-S7 自動駕駛模式（Autopilot）

### 相關筆記
- [[dexg16-dev-environment]]
- [[dexg16-ai-stack]]
- [[claude-session-manager]]

## 筆記
