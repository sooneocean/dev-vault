# 01 — Product Vision

## 產品名稱
**php-blog-mcp-server** — PHP 部落格網站自動化運營 MCP Server

## 問題陳述
部落格網站運營者需要同時管理大量重複性工作：
- 內容發佈與排程
- SEO 優化（meta tags、sitemap、關鍵字分析）
- 效能監控與分析
- 社群媒體同步

這些工作耗時且容易出錯，需要一個 AI 代理可以透過 MCP 協議直接操作網站的解決方案。

## 目標使用者
1. **網站運營者** — 需要自動化日常管理任務
2. **SEO 專員** — 需要批次優化內容與追蹤排名
3. **內容創作者** — 需要 AI 輔助創作與發佈流程

## 核心價值主張
- **一站自動化**：透過 MCP 協議，AI 代理可直接操控網站的全生命週期
- **SEO 智能化**：自動分析關鍵字、生成 meta tags、建立 sitemap
- **運營可視化**：集中式儀表板數據，支援決策

## 成功指標 (KPI)
| 指標 | 目標 |
|------|------|
| MCP Tools 可用數量 | ≥ 20 個 |
| API 回應時間 | < 2s (P95) |
| SEO 自動化覆蓋率 | meta tags 100% 自動生成 |
| 支援平台 | WordPress 優先，可擴展其他 PHP CMS |

## 範圍界定

### In Scope
- MCP Server (TypeScript/Node.js)
- WordPress REST API 整合
- SEO 工具集（分析、優化、sitemap）
- 內容管理工具（CRUD、排程、批次操作）
- 網站分析工具（流量、效能）

### Out of Scope
- 前端 UI（純 MCP Server，無 UI）
- 網站託管服務
- 非 PHP 平台支援（Phase 1 限定）
