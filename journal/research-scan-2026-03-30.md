---
title: "Research Scan: Agentic Harness & Context Prompt (2026-03-30)"
type: journal
tags: [research-scan, agent-framework, agentic-harness, automation]
created: "2026-03-30"
updated: "2026-03-30"
status: active
---

## 掃描結果摘要

**運行**: quick-scan 模式 (7 天內新項目)
**時間**: 2026-03-30 22:17 UTC
**發現**: 43 項新技術

### 分佈
- GitHub: 14 projects (8.5K - 134K stars)
- arXiv: 13 papers (2603 月份新發表)
- HuggingFace: 10 models/datasets
- Web: 6 tools/platforms

## 高優先級發現

### ⭐ Agentic Harness 直接相關

#### 1. **Domscribe** (Web Tool)
- **URL**: https://www.domscribe.com/
- **功能**: AI agent 的前端上下文系統（pixel-to-code）
- **特點**: JSX/Vue 映射、DOM 點擊編輯、React/Vue/Next.js/Nuxt 支持
- **評估**: 高度相關，應該 PoC

#### 2. **Query Memory** (Web Tool)
- **URL**: https://www.querymemory.com/
- **功能**: Agent 記憶體 API（文檔管理 + RAG）
- **特點**: 無需複雜工程，自動 parsing/chunking/embedding/retrieval
- **評估**: 高相關性，內存管理關鍵

#### 3. **ComposioHQ/agent-orchestrator** (GitHub, 1.8K stars)
- **功能**: 並行編碼 agent 編排
- **特點**: git worktree 隔離、CI 修復、merge conflict 解決
- **評估**: 關鍵的 agent 並行執行架構

#### 4. **Pimzino/agentic-tools-mcp** (GitHub, 420 stars)
- **功能**: MCP 服務器提供 agent 內存 + 任務管理
- **特點**: 持久化記憶、語義搜尋、項目特定存儲
- **評估**: MCP 集成的內存系統

### 📚 關鍵論文

1. **AIP: Agent Identity Protocol** (2603.24775)
   - 跨 MCP/A2A 驗證協議

2. **Before the Tool Call** (2603.20953)
   - Pre-action Authorization (OpenAgent Passport OAP)

3. **Utility-Guided Agent Orchestration** (2603.19896)
   - 平衡 gain/cost/uncertainty 的編排策略

4. **SimpleTool** (2603.00030)
   - 並行解碼優化 function calling (3-6x 加速)

### 🧠 Agent-Tuned Models

**Code Agent**
- **mistralai/Leanstral-2603**: 119B code agent for Lean 4 formal verification (via MCP)

**General Agent Models**
- **Qwen/Qwen3-8B**: Advanced tool calling capability
- **AI45Research/AgentDoG-Qwen3-4B**: Safety-focused trajectory analysis

**Embedding Models**
- **Qwen/Qwen3-Embedding-8B**: 119 languages (MTEB 70.58)
- **jinaai/jina-embeddings-v5-text-nano**: 239M lightweight
- **google/embeddinggemma-300m**: On-device optimized

### 🏗️ Infrastructure & Frameworks

**Top Frameworks**
- **dify** (134K): Complete agentic workflow platform
- **crewAI** (45.9K): Lightweight orchestration + 45+ tools
- **langflow** (18.5K): Low-code visual IDE

**Agent Infrastructure**
- **Maritime**: $1/month agent deployment (Docker)
- **MCPCore**: MCP server IDE + deployment
- **Pensieve**: Organization knowledge graph for agent context

## 🎯 建議下一步

### 立即探索
1. **Domscribe** — 前端上下文集成 (PoC 優先度：★★★)
2. **agentic-tools-mcp** — Agent 記憶體系統 (集成難度：★★☆)
3. **Leanstral-2603** — 代碼驗證 agent (實驗性：★★★)

### 監控
- AIP protocol 標準化進展
- arXiv 新論文（weekly）
- CrewAI/Dify 新功能發布

### 配置更新
✓ Added `agentic-harness` topic to research pipeline
✓ Lowered GitHub filters (min_stars: 100→50, created_days: 90→30)

## 原始數據
- scan-results JSON: `projects/tools/research-pipeline/state/scan-results-2026-03-30.json` (43 items)

