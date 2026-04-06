---
title: "Harness Engineering 研究"
type: resource
tags: [harness-engineering, claude-code, mcp, hooks, plugins, agent-harness, reference, knowledge-management]
created: "2026-03-29"
updated: "2026-04-04"
status: active
subtype: research
maturity: growing
domain: ai-engineering
summary: "Harness Engineering 深度研究 — hooks 生命週期 22 事件、MCP 生態系、plugin 架構與評估框架、agent tool chain 設計模式、scaffolding vs runtime 區分、反模式與實測數據。"
source: "https://martinfowler.com/articles/exploring-gen-ai/harness-engineering.html, https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents, https://code.claude.com/docs/en/hooks"
related: ["[[tech-research-squad]]", "[[prompt-engineering-research]]", "[[context-engineering-research]]", "[[compound-engineering-research]]", "[[claude-code-configuration]]", "[[compound-engineering-plugin]]"]
relation_map: "tech-research-squad:extends, compound-engineering-plugin:documents"
---

# Harness Engineering 研究

## 核心問題

如何設計 agent 的工具鏈、hook、plugin、MCP 架構，讓 AI 成為高效的工程夥伴？

---

## 1. Harness Engineering 的定義與邊界

### 1.1 什麼是 Harness

Harness 不是 agent 本身，而是**管理 agent 如何運作的軟體系統**——管理工具呼叫、context、retry、人類審核、安全執行、子代理協調。它是包裹核心推理迴圈的運行時協調層（Martin Fowler, 2025）。

**類比：** 如果 LLM 是引擎，harness 就是車架、煞車系統、儀表板和安全帶的總和。

### 1.2 Scaffolding vs Harness（兩階段模型）

| 階段 | 時機 | 關注點 | Claude Code 對應 |
|------|------|--------|-----------------|
| **Scaffolding** | 第一個 prompt 之前 | 組裝 agent：system prompt、tool schemas、subagent 註冊 | CLAUDE.md、settings.json、plugin 載入、skill 註冊 |
| **Harness** | 第一個 prompt 之後 | 協調 runtime：tool dispatch、context 管理、安全執行 | hooks、permission rules、compaction、worktree |

**核心 ReAct 迴圈的六階段：**
1. Pre-check & compaction
2. Thinking
3. Self-critique
4. Action
5. Tool execution
6. Post-processing

周圍有七個支援子系統：tool integration、memory、dynamic context curation、safety enforcement、session persistence、subagent orchestration、observability。

### 1.3 Harness Engineering 與其他學科的關係

```
Context Engineering — 管理 context window 中的資訊
    ↑ 子集
Harness Engineering — 管理 agent 的工具鏈與 runtime 行為
    ↑ 子集
Agent Engineering — 設計整個 agent 系統（含推理策略、角色設定）
```

**Harness Engineering 是 Context Engineering 的超集**——它不僅管理資訊，還管理行為。

### 1.4 為什麼 Harness Engineering 重要

Anthropic 在 "Effective Harnesses for Long-Running Agents" 中指出：

> 「跨多個 context window 讓 agent 做出一致進展仍然是一個開放問題。」

解法：用 harness 在 session 之間維持狀態——progress tracking files、structured environments、git history。這正是本 vault 的 session-stop-wrapper + journal 系統在做的事。

---

## 2. Claude Code Hooks 深度解析

### 2.1 Hooks 全景：22 個生命週期事件

截至 2026 年 3 月，Claude Code 提供 **22 個生命週期事件**（從最初的 14 個擴展而來）：

| 類別 | 事件 | 用途 |
|------|------|------|
| **Tool 相關** | PreToolUse | 攔截並阻止 tool 動作（唯一能 block 的 hook） |
| | PostToolUse | Tool 執行後清理（格式化、驗證） |
| | PostToolUseFailure | Tool 失敗後的回復邏輯 |
| | PermissionRequest | 權限要求時的自動決策 |
| **Session 相關** | SessionStart | Session 啟動時初始化 |
| | SessionEnd | Session 結束時清理 |
| | Stop | Claude 結束回覆時（不只是任務完成） |
| | StopFailure | Stop hook 自身失敗時 |
| **Subagent 相關** | SubagentStart | 子代理啟動 |
| | SubagentStop | 子代理結束 |
| **Context 相關** | PreCompact | Compaction 前的保留邏輯 |
| | PostCompact | Compaction 後的恢復動作 |
| | InstructionsLoaded | CLAUDE.md 或 rules 檔案載入時 |
| **配置與環境** | ConfigChange | 設定檔在 session 中被修改 |
| | WorktreeCreate | Worktree 被建立 |
| | WorktreeRemove | Worktree 被移除 |
| **使用者互動** | UserPromptSubmit | 使用者送出 prompt |
| | Notification | 通知發送 |
| | Elicitation | 向使用者要求輸入 |
| | ElicitationResult | 使用者回應 |
| **團隊** | TeammateIdle | 隊友閒置 |
| | TaskCompleted | 任務完成 |

### 2.2 四種 Handler 類型

| Handler | 用途 | 複雜度 | 適用場景 |
|---------|------|--------|---------|
| **Command** | 執行 shell 命令 | 低 | 格式化、lint、file copy |
| **HTTP** | 呼叫 HTTP endpoint | 中 | Webhook 通知、外部 API |
| **Prompt** | 注入 prompt 給 Claude | 中 | 安全審查、context 補充 |
| **Agent** | 啟動完整 subagent | 高 | 深度驗證、複雜自動化 |

**進階建議：** 從 Command 開始（格式化），升級到 Prompt（安全門），再到 Agent（深度驗證）。

### 2.3 Exit Code 語義（關鍵知識）

| Exit Code | 意義 | 適用 Hook |
|-----------|------|----------|
| 0 | 允許繼續 | 所有 |
| 1 | 警告但不阻止 | 所有（**不是 block**） |
| 2 | **阻止動作** | 僅 PreToolUse |
| 2 | **繼續工作**（不停止） | 僅 Stop |

**最致命的 bug：** 在 PreToolUse security gate 中用 `exit 1` 而非 `exit 2`——看起來有在工作，實際上**零執行力**。

### 2.4 本 Vault 的 Hooks 實作（實測數據）

**現有 hooks 配置（`~/.claude/settings.json`）：**

```
Stop hooks (2):
├── session-stop-wrapper.sh — 從 stdin JSON 擷取 session 摘要 → 寫入 journal Records
└── obsidian-agent sync     — 重建 vault 索引

PostToolUse hooks (2):
├── ruff format + check     — Python 檔案自動格式化 (匹配 .py)
└── npx prettier --write    — JS/TS/CSS 自動格式化 (匹配 .ts/.tsx/.js/.jsx/.css)
```

**session-stop-wrapper.sh 的設計決策：**
- 從 stdin 讀取 Claude Code 管道傳入的 JSON（含 `last_assistant_message`、`stop_reason`、`cwd`）
- Fallback 策略：`last_assistant_message` → `git diff --stat` → `"Session ended (reason)"`
- 靜默失敗（`|| true`）——永遠不阻擋 session 退出
- 摘要截斷到 300 字元，避免 journal 膨脹
- 用 `obsidian-agent patch --heading --append` 追加到指定區段

**效能觀察：**
- 兩個 Stop hooks 各有 10s timeout，但實際執行 < 2s
- PostToolUse hooks 各有 15s timeout，實際 < 1s（ruff 和 prettier 都很快）
- 總 hook 開銷：可忽略不計（每個 < 200ms）

### 2.5 Hook 設計模式

#### 模式 1：確定性格式化（PostToolUse）
```json
{
  "matcher": "Write|Edit",
  "hooks": [{
    "type": "command",
    "command": "format-on-save-logic",
    "timeout": 15
  }]
}
```
**原理：** 格式化是冪等的——跑一百次結果相同。PostToolUse 保證每次寫入後格式一致，**消除了 CLAUDE.md 中的格式化指示**（省 context + 100% 執行率）。

#### 模式 2：安全門（PreToolUse）
```json
{
  "matcher": "Bash",
  "hooks": [{
    "type": "command",
    "command": "check-dangerous-commands.sh"
  }]
}
```
**用途：** 攔截 `rm -rf /`、`git push --force`、hardcoded secrets。
**關鍵：** 必須用 `exit 2` 阻止，`exit 1` 只是警告。

#### 模式 3：Session 日誌（Stop）
```json
{
  "matcher": "",
  "hooks": [{
    "type": "command",
    "command": "session-logger.sh",
    "timeout": 10
  }]
}
```
**本 vault 的實作：** `session-stop-wrapper.sh` 是此模式的真實案例——每次 session 結束自動記錄到 journal。

#### 模式 4：Context 注入（InstructionsLoaded）
```json
{
  "matcher": "",
  "hooks": [{
    "type": "prompt",
    "command": "inject-project-context.sh"
  }]
}
```
**用途：** 在 CLAUDE.md 載入時動態注入最新資訊（環境變數、API 版本、最近的 test 結果）。

#### 模式 5：Worktree 自動設定（WorktreeCreate）
```json
{
  "matcher": "",
  "hooks": [{
    "type": "command",
    "command": "setup-worktree-env.sh"
  }]
}
```
**用途：** 自動複製 `.env`、安裝相依套件、設定確定性 port。

### 2.6 Hook 反模式

| 反模式 | 症狀 | 修正 |
|--------|------|------|
| **exit 1 當 gate** | 看似攔截實際放行 | 用 `exit 2` |
| **Stop + exit 2 無限迴圈** | Claude 持續嘗試「修復」 | 檢查 `stop_hook_active` field |
| **慢 hook（> 2s）** | 每次 tool call 都卡住 | 保持 < 500ms，最差 < 2s |
| **Subagent 繼承 hooks** | 子代理觸發父代理 hooks → 無限遞迴 | 用 `--settings` 給子代理獨立配置 |
| **settings pollution** | Hook script 修改了全域設定 | Hook 只讀取設定，不修改 |
| **UserPromptSubmit 生子代理** | Hook 生出的 subagent 又觸發同一 hook | 加 subagent 偵測旗標 |
| **不靜默失敗** | Hook 錯誤阻擋主流程 | 關鍵路徑加 `|| true` |

---

## 3. MCP 生態系深度分析

### 3.1 MCP 協定概觀

Model Context Protocol（MCP）是 2024 年 11 月由 Anthropic 推出的開源標準，讓 AI 系統與外部應用和資料來源連接。截至 2026 年：

| 指標 | 數值 |
|------|------|
| MCP Registry 條目 | ~2,000+（2025.9 launch 起 407% 成長） |
| 主要採用者 | Anthropic, OpenAI, Hugging Face, LangChain, Google |
| 市場規模 | $1.8B（2025 估計） |
| 協定版本 | v1.27+（2026 年） |

### 3.2 2026 MCP 路線圖重點

| 優先項 | 說明 |
|--------|------|
| **MCP Server Cards** | `.well-known` URL 暴露結構化 server 元資料，用於自動發現 |
| **Tasks primitive** | 實驗性功能——任務生命週期管理（retry 語義、過期策略） |
| **安全強化** | SEP-1024（本地安裝安全）、SEP-835（預設 scope 定義） |
| **Resource Indicators** | 防止惡意 server 取得不當 access token |

### 3.3 本 Vault 的 MCP 配置

**Project-level（`.mcp.json`）：**

| Server | 命令 | 用途 |
|--------|------|------|
| arxiv | `uvx arxiv-mcp-server` | 學術論文搜尋 |
| huggingface | `uvx huggingface-mcp-server` | HuggingFace 模型/資料集查詢 |
| fetch | `uvx mcp-server-fetch` | 通用 HTTP fetch |

**Plugin-provided MCP servers（透過 plugins 自動啟動）：**

| Plugin | MCP Server | 工具數 |
|--------|-----------|--------|
| context7 | context7 | 2（resolve-library-id, query-docs） |
| playwright | playwright | 18+（browser automation suite） |
| chrome-devtools-mcp | chrome-devtools | 25+（DevTools automation） |
| claude-mem | mcp-search | 6（smart-search, timeline, outline...） |
| compound-engineering | context7（內建副本） | 2 |

**Cloud-integrated MCP servers（Claude.ai 層級）：**

| Server | 用途 |
|--------|------|
| Figma | 設計稿讀取、Code Connect、FigJam 圖表 |
| Gmail | 郵件搜尋、讀取、草稿 |
| Google Calendar | 行事曆管理 |
| Vercel | 部署、日誌、PR preview |

**總計：** 7+ project/plugin MCP servers + 4 cloud MCP servers = **11+ MCP servers**

### 3.4 MCP Server 設計原則

| 原則 | 說明 |
|------|------|
| **單一職責** | 一個 server 做一件事（fetch ≠ database ≠ file system） |
| **最小工具集** | 只暴露必要的 tools——每個 tool definition 佔 context |
| **結構化回傳** | JSON > 純文字，方便 agent 解析 |
| **`is_error: true`** | 失敗時明確標記，agent 知道要重試或通知使用者 |
| **Instructions** | 在 server 元資料中寫清楚「何時用/何時不用」，幫助 Claude 正確選擇 |
| **Timeout** | MCP 呼叫應 < 10s；長時間操作用 Tasks primitive |
| **Discovery** | 有意義的 tool name 和 description，讓 ToolSearch 能找到 |

### 3.5 MCP vs Plugin vs Skill vs Hook 選擇矩陣

| 需求 | 最佳選擇 | 原因 |
|------|---------|------|
| 連接外部 API/服務 | **MCP Server** | 標準化 protocol、跨 agent 可用 |
| 教 Claude 執行特定流程 | **Skill** | 按需載入（30-50 tokens/skill），指令式 |
| 確定性自動化（每次都跑） | **Hook** | 不依賴 LLM 判斷，100% 執行率 |
| 封裝可分享的工具組合 | **Plugin** | 打包 skills + agents + hooks + MCP |
| 專門角色的獨立推理 | **Agent（.claude/agents/）** | 獨立 context window 和 tool 權限 |
| 快速文字指令 | **Slash Command** | 最輕量——一個 .md 檔案 |

---

## 4. Plugin 架構與評估框架

### 4.1 Plugin 結構

```
my-plugin/
├── .claude-plugin/
│   └── plugin.json        # Manifest（name, version, description）
├── commands/               # Slash commands (.md)
├── agents/                 # Agent definitions (.md)
├── skills/                 # Skills (folder per skill, each has SKILL.md)
├── hooks/                  # Hook definitions
└── mcp/                    # MCP server configs
```

**命名規則：** kebab-case for all directories and files。Skill folder name = skill name（prefixed with plugin namespace）。

**2026 生態系規模：** 340+ plugins、1367+ agent skills（公開 marketplace），加上大量私有 plugins。

### 4.2 Skill 的 Meta-Tool 架構

Skills 透過一個名為 `Skill` 的 meta-tool 運作：
1. 系統把所有可用 skills 格式化成文字描述，嵌入 `Skill` tool 的 prompt
2. Claude 用純 LLM 推理判斷哪個 skill 最相關（無 regex、無 keyword matching）
3. 被選中的 skill 被載入——此時才佔用 context

**Token 效率：** 未使用的 skill 只花 **30-50 tokens**（名稱 + 一行描述），比整份指令載入少 **97%+**。

### 4.3 本環境的 Plugin 清單（14 個）

| Plugin | 來源 | 主要貢獻 | 使用頻率 | Context 開銷 |
|--------|------|---------|---------|-------------|
| compound-engineering | EveryInc | 47 agents, 41+ skills | 核心 | 高（但按需載入） |
| context7 | claude-plugins-official | 即時 library docs | 核心 | 低 |
| github | claude-plugins-official | PR/issue 管理 | 核心 | 低 |
| claude-mem | thedotmack | 跨 session 記憶 | 頻繁 | 中 |
| claude-hud | claude-hud | 狀態列 | 頻繁 | 低 |
| telegram | claude-plugins-official | Telegram 通知 | 頻繁 | 低 |
| review-loop | hamel-review | 獨立審查迴圈 | 偶爾 | 低 |
| cartographer | cartographer-marketplace | Codebase 地圖 | 偶爾 | 低 |
| playwright | claude-plugins-official | 瀏覽器自動化 | 偶爾 | 中（18+ tools） |
| chrome-devtools-mcp | claude-plugins-official | Chrome 除錯 | 偶爾 | 中（25+ tools） |
| typescript-lsp | claude-plugins-official | TS 語言伺服器 | 偶爾 | 中 |
| pyright-lsp | claude-plugins-official | Python 類型檢查 | 偶爾 | 中 |
| posthog | local | 分析 | 極少 | 低 |
| learning-output-style | local | 輸出風格 | 極少 | 低 |

### 4.4 Plugin 評估框架

選擇和評估 plugin 的五維度模型：

| 維度 | 問題 | 評分標準 |
|------|------|---------|
| **Value** | 它解決什麼問題？多頻繁用到？ | 每週用 3+ 次 = 高 |
| **Context Cost** | 載入多少 tool definitions？ | < 2 tools = 低；10+ tools = 高 |
| **Reliability** | 是否穩定？維護狀態？ | 最近 30 天有更新 = 好 |
| **Composability** | 能與其他 plugin 配合嗎？有衝突嗎？ | 獨立運作 = 好；覆寫行為 = 差 |
| **Replaceability** | 能否用更輕量的方式達成？ | Skill/Hook 能取代 = 考慮替換 |

**評估流程：**
1. 安裝後第一週——觀察使用頻率
2. 第二週——用 `/context` 或 `/cost` 測量 context 開銷
3. 第四週——決定保留、停用、或替換
4. 每季——全面重新評估（plugin 數量膨脹是 harness 退化的第一徵兆）

**Context Cost 估算公式：**
```
Plugin overhead ≈ (tool_count × ~150 tokens) + (skill_count × ~40 tokens) + metadata
```

### 4.5 Plugin Profile 策略

不同工作類型可載入不同的 plugin 組合，避免不相關 plugins 佔用 context：

| Profile | Plugins | 估計 overhead |
|---------|---------|--------------|
| **vault-only** | compound-engineering, context7, github, claude-mem | ~25K |
| **web-dev** | + playwright, chrome-devtools, typescript-lsp | ~40K |
| **python-dev** | + pyright-lsp | ~30K |
| **full** | all 14 | ~45-55K |

**目前現況：** 所有 14 個 plugin 永遠啟用。未來可考慮用 project-level `.claude/settings.json` 為不同工作類型設定 profile。

---

## 5. Slash Commands 設計

### 5.1 本 Vault 的 Slash Commands 盤點（17 個）

| 類別 | 命令 | 用途 |
|------|------|------|
| **Vault 核心** | /journal | 建立/開啟今日日誌 |
| | /note | 建立新筆記 |
| | /capture | 快速捕捉想法 |
| | /search | 全文搜尋 |
| | /list | 列出筆記 |
| | /review | 產生週回顧 |
| **自動化橋接** | /bridge-compound | CE 學習文件 → vault resource |
| | /bridge-plan | CE 計畫 → vault project |
| **配置改善** | /improve | 分析使用體驗、建議配置改善 |
| **研究管線** | /research | 觸發 LLM 工具研究掃描 |
| | /research-status | 顯示研究管線狀態 |
| | /research-search | 搜尋研究筆記 |
| | /research-apply | 審核並套用研究建議 |
| **本地 LLM** | /local-status | Ollama 模型、VRAM、GPU 狀態 |
| | /local-cost | 本地 LLM vs Claude API 成本估算 |

**分類分佈：**
- Vault 操作：6 個（35%）
- 橋接/整合：2 個（12%）
- 配置管理：1 個（6%）
- 研究自動化：4 個（24%）
- 基礎設施：2 個（12%）

### 5.2 Slash Command 設計原則

| 原則 | 說明 |
|------|------|
| **單一用途** | 一個命令做一件事，複雜流程用參數模式（如 `/improve [apply\|status]`） |
| **自我文件化** | .md 檔案頂部就是使用說明——Claude 讀了就知道怎麼執行 |
| **冪等安全** | 多次執行不應產生重複副作用（例如 /journal 只建立不重複） |
| **Combo 模式** | 避免多步手動操作——`/improve` 分析完直接問「要套用嗎？」 |
| **低 token** | Command .md 檔案應 < 100 行；過長的邏輯應提取到 script |
| **Bridge 模式** | 跨系統整合的最輕量方式——不改 plugin，只寫一個 .md 轉接器 |

---

## 6. Agent Tool Chain 設計模式

### 6.1 分層設計

Claude Code 的 harness 是四層架構：

```
Layer 4: Runtime (hooks, permissions, compaction)
Layer 3: Plugins (skills, agents, MCP servers)
Layer 2: Project (.claude/, CLAUDE.md, .mcp.json)
Layer 1: Global (settings.json, ~/.claude/CLAUDE.md)
```

**衝突解決：** 上層覆蓋下層。Runtime hook 的行為 > Plugin 的建議 > Project 規則 > Global 規則。

### 6.2 Permission 設計

本環境的 permission 配置：

```json
"permissions": {
  "allow": [
    "Bash(*)", "Read", "Edit", "Write", "Glob", "Grep",
    "WebFetch", "WebSearch", "Skill(*)", "Agent(*)", "mcp__*"
  ],
  "additionalDirectories": ["C:\\Users\\User\\Projects"]
}
```

**設計原則：**
- 規則以 `deny` → `ask` → `allow` 順序評估，**第一個匹配規則勝出**
- `Bash(*)` 是最寬鬆的——允許所有 shell 命令。生產環境應改用白名單（如 `Bash(npm test)`, `Bash(git *)`）
- `mcp__*` 允許所有 MCP 工具——搭配 `enableAllProjectMcpServers: true` 讓 project MCP 自動啟用
- `additionalDirectories` 允許跨目錄操作——我們用它讓 vault 操作也能存取 Projects 目錄

**Trail of Bits 的安全建議：** 生產環境應最小化 allow 清單，用 deny 規則封鎖危險命令（`rm -rf`、`curl | bash`、`chmod 777`），並限制 HTTP hook 的目標 URL。

### 6.3 Worktree 策略

```json
"worktree": {
  "symlinkDirectories": ["node_modules", ".cache"]
}
```

**用途：** `--worktree` 模式建立隔離的 git worktree，避免 agent 的修改影響主分支。`symlinkDirectories` 讓大型目錄（node_modules）用 symlink 共享，減少磁碟和安裝時間。

**2026 更新：** Claude Code 支援最多 **10 個同時 subagent**，每個可在獨立 worktree 中平行工作。WorktreeCreate/WorktreeRemove hooks 可用於自動化環境設定。

### 6.4 Tiered Persona Review（Compound Engineering 案例）

compound-engineering 的 `/ce:review` 展示了進階 agent tool chain：

```
使用者觸發 /ce:review
    ↓
平行啟動 N 個 persona agents:
├── correctness-reviewer
├── security-reviewer
├── performance-reviewer
├── maintainability-reviewer
├── adversarial-reviewer（故意找碴）
└── ...最多 26 個 Code Review agents
    ↓
每個 agent 獨立產出 findings（附帶信心分數）
    ↓
Merge & Dedup pipeline:
├── 去除重複發現
├── 按 confidence 門檻過濾
└── 合併成最終報告
```

**設計啟發：**
- **Diversity > Depth** — 多個不同角度的淺層審查 > 一個角度的深層審查
- **Confidence gating** — 低信心的發現自動過濾，減少噪音
- **Parallel execution** — 不需等前一個 agent 完成

### 6.5 Knowledge Loop（本 Vault 的實作）

```
工作 session
    ↓ Stop hook
session-stop-wrapper.sh → journal Records
    ↓ Stop hook
obsidian-agent sync → 重建索引
    ↓ 手動觸發
/improve → 分析 journal friction → 產出改善建議
    ↓ 手動觸發
/improve apply → 套用到 settings.json / CLAUDE.md
    ↓ 下次 session
改善的配置自動生效
```

**這是一個自我改善的迴圈：** 每次 session 的摩擦被記錄，定期分析，自動建議改善，套用後下次 session 受益。

---

## 7. Long-Running Agent 的 Harness 設計

### 7.1 跨 Context Window 的一致性問題

Anthropic 的研究指出核心挑戰：**每個新 session 啟動時沒有前一個 session 的記憶**。

**Anthropic 的解法（Initializer + Coding Agent 模式）：**

| 角色 | 任務 |
|------|------|
| **Initializer Agent** | 首次運行時建立結構化環境——feature list、git repo、progress tracking files |
| **Coding Agent** | 逐 session 漸進式工作，每次先讀 `claude-progress.txt` 和 git history 了解狀態 |

### 7.2 狀態持久化策略

| 策略 | 機制 | 本 Vault 的實作 |
|------|------|----------------|
| **Progress File** | JSON/Markdown 記錄目前狀態 | journal Records（每次 session 自動寫入） |
| **Git History** | Commit log = implicit progress tracking | 每次有意義的變更都 commit |
| **Structured Tests** | 測試狀態檔案追蹤 feature 完成度 | — |
| **Memory System** | Auto Memory + topic files | `~/.claude/projects/*/memory/` |
| **Index Files** | 目錄索引維持導航 | `_index.md` 每次 sync 重建 |

**Anthropic 的關鍵洞察：** 用 JSON 而非 Markdown 儲存 progress——模型比較不會不當修改 JSON 檔案。

### 7.3 「Golden Principles」模式

> 「將最佳實踐編碼為機械式規則，直接寫進 repo。」

| 機制 | 對應 |
|------|------|
| CLAUDE.md 規則 | 每次 session 載入的永久指令 |
| `.claude/rules/*.md` | 條件載入的細部規則 |
| Hook enforcement | 確定性執行，不依賴 LLM |
| CONVENTIONS.md | Agent 必須遵守的 vault 規範 |

---

## 8. 反模式總覽

### 8.1 Hook 反模式（詳見 §2.6）

| 反模式 | 影響 | 嚴重度 |
|--------|------|--------|
| exit 1 當安全門 | 零執行力 | 致命 |
| Stop + exit 2 無限迴圈 | Session 無法結束 | 致命 |
| Subagent 繼承 hooks | 無限遞迴 | 嚴重 |
| 慢 hook（> 2s） | UX 退化 | 中等 |
| 不靜默失敗 | 主流程被阻擋 | 中等 |

### 8.2 Plugin 反模式

| 反模式 | 症狀 | 修正 |
|--------|------|------|
| **Plugin 膨脹** | 裝太多 plugin，context overhead > 50K | 定期評估，停用低頻 plugin |
| **重疊功能** | 兩個 plugin 做同一件事（context7 出現兩次） | 選擇一個，停用另一個 |
| **不分 profile** | Web dev 時載入 Python LSP | 用 project-level settings 切 profile |
| **盲目安裝** | 看到推薦就裝，不評估 | 用 §4.4 評估框架 |
| **忽略 marketplace 版本** | 不更新 plugin 導致 API 不相容 | 設 autoUpdatesChannel: latest |

### 8.3 MCP 反模式

| 反模式 | 症狀 | 修正 |
|--------|------|------|
| **無 instructions** | Claude 不知何時用此 server | 在 server metadata 加 "Use when..." 說明 |
| **暴露過多 tools** | Context 爆炸 | 只暴露必要 tools |
| **無 error signaling** | Claude 不知道呼叫失敗 | 回傳 `is_error: true` |
| **長時間阻塞** | Tool call timeout | 用 Tasks primitive 處理長操作 |
| **無 auth** | 安全風險 | 遵循 SEP-1024 和 Resource Indicators |

### 8.4 Harness 架構反模式

| 反模式 | 症狀 | 修正 |
|--------|------|------|
| **All in CLAUDE.md** | 行為指示和工具設定全塞一個檔案 | 分層：hooks 管行為、skills 管知識、CLAUDE.md 管原則 |
| **Manual everything** | 每次 session 手動做重複操作 | 辨識重複 → hooks/commands 自動化 |
| **No observability** | 不知道 agent 做了什麼 | 用 Stop hook 記錄、HUD 監控、cost tracking |
| **Monolithic agent** | 一個 agent 做所有事 | 拆分 subagent，各有專職和 tool 權限 |
| **No feedback loop** | 配置停滯不改善 | `/improve` 迴圈：journal friction → 分析 → 改善 |

---

## 9. 進階主題

### 9.1 Hooks 的 Token 經濟學

Hooks 是最具 token 效率的自動化方式：

| 方式 | Context 成本 | 執行可靠度 |
|------|-------------|-----------|
| CLAUDE.md 指令 | ~20-50 tokens/條 | 80-95%（LLM 判斷） |
| Skill | ~30-50 tokens（待機）→ 載入時數百 | 95%+（Claude 判斷相關性） |
| Hook | **0 tokens** | **100%**（確定性） |

**核心洞察：** 能用 hook 做的事**絕對不要用 CLAUDE.md 指令**。Hook 免費、確定、不佔 context。

**已驗證的轉換：**
- ~~「Python 檔案存檔後用 ruff 格式化」~~ → PostToolUse hook（✓ 已實作）
- ~~「JS/TS 檔案存檔後用 prettier」~~ → PostToolUse hook（✓ 已實作）
- ~~「Session 結束時記錄到 journal」~~ → Stop hook（✓ 已實作）

### 9.2 建立自己的 MCP Server

**最小 MCP Server 結構（stdio 模式）：**
```
my-server/
├── package.json
├── src/
│   └── index.ts       # 實作 tools/resources/prompts
└── tsconfig.json
```

**關鍵決策：**
- **stdio vs SSE：** 本地用 stdio（簡單、低延遲），遠端用 SSE（支援網路）
- **Tool granularity：** 粗粒度工具（一個 tool 做多件事）vs 細粒度（每件事一個 tool）。推薦**細粒度**——讓 Claude 自己組合
- **Authentication：** 本地 server 免 auth；暴露到網路的需實作 OAuth2/API key

### 9.3 Custom Agent 設計

`.claude/agents/xxx.md` 定義專門角色：

```markdown
---
name: vault-librarian
description: Manages vault notes, indices, and relationships
tools: [Read, Write, Edit, Glob, Grep, Bash(obsidian-agent*)]
---

# Vault Librarian

You manage an Obsidian vault. Your job:
1. Create/update notes following CONVENTIONS.md
2. Maintain bidirectional links
3. Run obsidian-agent sync after changes

## Constraints
- Never modify files outside the vault
- Always update _index.md after changes
```

**設計原則：**
- 最小 tool 權限——只給 agent 需要的工具
- 明確的成功標準——不是 "manage the vault"，而是具體的動作清單
- 約束優先——先說「不能做什麼」再說「要做什麼」

---

## Harness 全貌（Sprint 1 盤點）

### 整體數據

| 要素 | 數量 | 說明 |
|------|------|------|
| Plugins | 14 | 含 compound-engineering, telegram, claude-mem 等 |
| Skills | 41+ | compound-engineering 提供 41 個 + 專案自訂 6 個 |
| Agents | 47 | compound-engineering 提供的專業子代理 |
| MCP Servers | 11+ | 3 project + 4 plugin-provided + 4 cloud-integrated |
| Hooks | 4 個 | 2 Stop + 2 PostToolUse |
| Slash Commands | 17 | vault 6 + bridge 2 + config 1 + research 4 + infra 2 |
| LSP Servers | 2 | typescript-lsp, pyright-lsp |
| Lifecycle Events | 22 | 可掛載的 hook 點位 |

### 已安裝 Plugins 清單

| Plugin | 版本 | 用途 |
|--------|------|------|
| compound-engineering | 2.58.1 | 累積式工程工作流（核心） |
| telegram | 0.0.4 | Telegram bot 整合 |
| claude-mem | 10.6.1 | 持久化記憶、計畫、時間線 |
| claude-hud | 0.0.10 | 狀態列顯示 |
| cartographer | 1.4.0 | 程式碼地圖 |
| review-loop | 1.8.0 | 審查迴圈 |
| context7 | latest | Library 文件即時查詢 |
| github | latest | GitHub 整合 |
| typescript-lsp | 1.0.0 | TypeScript 語言伺服器 |
| pyright-lsp | 1.0.0 | Python 語言伺服器 |
| playwright | latest | 瀏覽器自動化 |
| chrome-devtools-mcp | latest | Chrome DevTools |
| posthog | 1.0.0 | 分析（local only） |
| learning-output-style | latest | 輸出風格（local only） |

### Compound Engineering — Agent 分類

| 類別 | 數量 | 代表 Agents |
|------|------|------------|
| Code Review | 26 | correctness, security, performance, maintainability, adversarial... |
| Document Review | 7 | feasibility, coherence, scope-guardian, product-lens... |
| Research | 6 | best-practices, framework-docs, git-history, issue-intelligence... |
| Workflow | 4 | bug-reproduction, lint, pr-comment-resolver, spec-flow-analyzer |
| Design | 3 | design-iterator, figma-design-sync, design-implementation-reviewer |
| Documentation | 1 | ankane-readme-writer |

### 關鍵設定

- Effort: high
- 權限: Bash(*), Read, Edit, Write, Glob, Grep, WebFetch, WebSearch, mcp__* 全開
- Auto-updates: latest channel
- Enable all project MCP servers: true
- Skip dangerous mode permission prompt: true

---

## 迭代紀錄

### Sprint 1 — 2026-03-29

**做了什麼：** 完整盤點 harness 全貌 — 14 plugins, 47 agents, 41 skills
**學到什麼：**
- Compound Engineering 是目前最大的外掛，單獨貢獻 47 agents + 41 skills
- Hooks 只有格式化，還有很大的自動化空間
- 架構是分層的：Global → Project → Plugin → Runtime
- Agent 分類很清楚：Review (最多) > Doc Review > Research > Workflow > Design > Docs
**哪裡卡住：** 還沒實際用過 `/ce:review` 或 `/ce:plan`，不確定效果
**下次要試：** 用 `/ce:brainstorm` 或 `/ce:plan` 跑一個真實任務，體驗完整工作流
**知識複利：** 這份盤點本身就是未來快速定位工具的索引

### Sprint 2 — 2026-03-29

**做了什麼：** 完成 obsidian-agent 底層效率改進（brainstorm → plan → work 全流程）
- 建立 `scripts/session-stop-wrapper.sh` — Stop hook 自動擷取 `last_assistant_message` 寫入 journal Records
- 新增 sync hook — session 結束時自動重建 vault 索引
- 建立 `/bridge-compound` slash command — 橋接 CE compound 學習文件到 vault resources
- 建立 `/bridge-plan` slash command — 橋接 CE plan 到 vault project 筆記

**學到什麼：**
- Stop hook 的 `sessionStop()` 只讀 `stop_reason`，wrapper script 繞過此限制直接讀 stdin JSON
- `obsidian-agent patch --heading --append` 可靠追加到指定區段
- slash command 是最輕量的 CE ↔ vault 橋接方式，不需改 plugin 本身

**哪裡卡住：**
- Windows Git Bash 的 pipe stdin 行為與 file redirect 不同，需要實測確認
- journal 被多個 session 同時 patch 時可能產生意外追加（已清理）

**下次要試：**
- 實際跑一次 `/ce:compound` → `/bridge-compound` 的完整知識複利流程
- 驗證 sync hook 的索引更新時間是否在 10s timeout 內

**知識複利：** wrapper script 模式可複製到其他 hook 自動化；bridge command 模式可擴展到其他 CE 產出

### Sprint 3 — 2026-03-30

**做了什麼：** 全面深化 Harness Engineering 研究——從 136 行擴充為完整的研究筆記
**來源：** Martin Fowler 的 harness engineering 定義、Anthropic "Effective Harnesses for Long-Running Agents"、Claude Code hooks 官方文件（22 events）、MCP 2026 路線圖、Plugin marketplace 生態調查、本 vault 的 settings.json/hooks/commands 實測資料
**關鍵發現：**
- Harness 分為 Scaffolding（組裝時）和 Runtime（運行時）兩階段——CLAUDE.md 是 scaffolding，hooks 是 runtime
- 22 個 lifecycle events 覆蓋從 session 啟動到 context compaction 的完整生命週期
- Hook 的 token 經濟學：0 context cost + 100% 執行率，是最高效的自動化方式
- Exit code 語義是最常見的 bug 源——exit 1 ≠ block，exit 2 才是
- 本環境有 14 plugins 但只用 4 個 hooks——hooks 擴展空間巨大
- MCP 生態系 2026 年從實驗轉向企業級採用，Registry 條目已超 2000
- Plugin 評估需要五維框架：Value, Context Cost, Reliability, Composability, Replaceability
- Anthropic 的 long-running agent 用 JSON progress file + initializer/coder 雙 agent 模式解決跨 session 一致性
**哪裡卡住：**
- Plugin 的精確 context overhead 需要用 `/cost` 實測（目前只有估算）
- 22 個 lifecycle events 中只用了 2 個類別（Stop, PostToolUse），其他 20 個的實用場景待探索
**下次要試：**
- 實作 PreToolUse 安全門 hook（攔截危險 Bash 命令）
- 實作 SessionStart hook（自動載入相關 context）
- 用 `/cost` 測量 plugin profile 在不同配置下的 token 差異
- 設計一個自己的 MCP server（可能用 obsidian-agent 作為基礎）
**知識複利：** Plugin 評估框架和 Hook 設計模式可直接用於未來的 harness 調優；反模式清單是 code review 時的 checklist

## 開放問題（已更新）

- [x] ~~Plugin 之間的互動與衝突如何管理？~~ → Plugin 評估框架 §4.4 + Profile 策略 §4.5
- [x] ~~Hook 還能做什麼自動化？~~ → §2.5 列出 5 種模式；已實作 3 個，另有安全門和 context 注入待探索
- [x] ~~架構是分層的？~~ → 四層：Global → Project → Plugin → Runtime（§6.1）
- [ ] 如何設計自己的 MCP server？→ §9.2 有初步框架，待實作驗證
- [ ] 47 個 agents 中哪些最值得優先掌握？（需要按使用場景排優先級）
- [ ] `/ce:review` 的 tiered persona 機制實際效果如何？（需要真實 PR 測試）
- [ ] 14 plugins 各自佔多少 context tokens？（需要用 `/cost` 對比測量）
- [ ] PreToolUse security gate 在 Windows Git Bash 環境是否可靠？
- [ ] 22 個 lifecycle events 中 PreCompact/PostCompact 的實際用途？
- [ ] Plugin profile 切換的自動化方式？（project-level settings 還是 script？）

## Related

- [[tech-research-squad]]
- [[claude-code-configuration]]
- [[compound-engineering-plugin]]
- [[prompt-engineering-research]]
- [[context-engineering-research]]
