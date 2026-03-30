---
title: "Context Engineering 研究"
type: resource
tags: [context-engineering, claude-code, llm]
created: "2026-03-29"
updated: "2026-03-30"
plugins_baseline_date: "2026-03-29"
status: active
subtype: research
maturity: mature
domain: ai-engineering
summary: "Context Engineering — 在有限 context window 中最大化有效資訊的策略。含 1M window 實測數據、compaction 陷阱、CLAUDE.md 最佳化、memory 架構、subagent 隔離模式。"
source: "https://code.claude.com/docs/en/best-practices, https://code.claude.com/docs/en/memory"
related: ["[[tech-research-squad]]", "[[prompt-engineering-research]]", "[[harness-engineering-research]]", "[[compound-engineering-research]]", "[[context-engineering-hygiene]]"]
relation_map: "tech-research-squad:extends, harness-engineering-research:extends"
---

# Context Engineering 研究

## 核心問題

如何在有限的 context window 中最大化有效資訊，讓 LLM 做出最好的決策？

---

## 1. Context Window 管理策略

### 1.1 Context 是什麼

Context window 是模型一次能處理的全部文字——包含系統提示、CLAUDE.md、MCP tool definitions、對話歷史、檔案讀取內容、命令輸出。它是 LLM 的「工作記憶」。

### 1.2 1M Window 實際利用率

**200K window 的 `/context` 實測分佈（Anthropic 官方範例）：**

| 元素 | Token 數 | 佔比 |
|------|---------|------|
| System prompt | 2.7K | 1.3% |
| System tools (built-in) | 16.8K | 8.4% |
| Custom agents | 1.3K | 0.7% |
| Memory files | 7.4K | 3.7% |
| Skills | 1.0K | 0.5% |
| Messages (對話) | 9.6K | 4.8% |
| Auto-compact buffer | 33.0K | **16.5%** |
| Free space | 118K | 58.9% |

**關鍵數字：**
- Auto-compact buffer：**~33K tokens**（之前是 45K，2026 年初降到 33K）
- 有效可用空間：200K window 約 **167K**；1M window 約 **830K**（83%）
- 1M window 相比 200K 有約 **5 倍**可用空間，compaction 事件減少 **15%**
- Plugins/tools 的 overhead 通常吃掉 **15-30K tokens**（視安裝數量）

### 1.3 效能退化閾值

| 使用率 | 可用推理空間 | 狀態 |
|--------|-------------|------|
| < 75% | > 50K | 品質穩定，推薦工作區間 |
| 75-83% | 20-50K | 可接受但需注意 |
| 83.5% | ~33K | **Auto-compact 觸發** |
| 90%+ | < 20K | 勉強運作，頻繁失敗 |
| 95%+ | < 10K | 損壞風險，可能進入無限 compact loop |

**核心洞察：** 更早停止反而延長有效工作時間——每一 turn 維持更高推理品質，比塞滿 context 但品質下降更好。

### 1.4 實用策略

**Must Do:**
- `/clear` — 不相關任務之間務必重置 context
- 同一問題修正兩次仍失敗 → `/clear` + 改進 prompt 重來
- 用 `/context` 或 HUD status line 持續監控使用量
- 引用檔案路徑而非貼上內容（Claude 會自己讀）

**Should Do:**
- `/btw` — 快速問題不需進入 context 歷史
- Batched edits — 一次描述多個修改，減少 read/write 次數
- 用 CLI 工具（`gh`, `aws`）而非 API — 最省 context 的外部互動方式
- `/compact Focus on X` — 帶指示的手動 compact 比自動更精準

**Avoid:**
- Kitchen sink session — 一個 session 做太多不相關事情
- 無範圍的 "investigate" — 會讀數百個檔案灌爆 context
- 在主 context 讀大檔案 — 改用 subagent

---

## 2. Compaction 策略

### 2.1 Compaction 機制

Compaction 是伺服器端的摘要壓縮，把對話歷史濃縮成摘要以釋放空間。

**自動觸發條件：** 使用率達到 **~83.5%** 時自動觸發。

**手動觸發：**
- `/compact` — 基本壓縮
- `/compact <指示>` — 帶自訂保留指示（推薦）
- `Esc + Esc` → "Summarize from here" — 只壓縮部分對話

### 2.2 什麼會在 Compaction 中丟失

**高風險丟失項目：**
- 精確的技術細節（API rate limit、特定設定值）
- 較早的架構決策上下文
- 檔案修改的完整清單
- 測試命令和預期結果
- 微妙的對話語境（為什麼選 A 不選 B）

**安全的（不會丟）：**
- CLAUDE.md 內容 — **compaction 後會從磁碟重新載入**
- Auto memory 內容 — 獨立於對話存在

**多次 compaction 的累積效應：** 每多一次 compaction cycle，資訊粒度更粗。第三次 compact 後的摘要可能已經失去關鍵細節。

### 2.3 Compaction 陷阱

| 陷阱 | 症狀 | 解法 |
|------|------|------|
| 無限 compact loop | 顯示 "102%" 使用率 | `/clear` 重新開始 |
| 過早觸發 | 每幾分鐘就 compact | 檢查 plugin 是否灌了太多 tool definitions |
| Thrashing | Compact 後重複之前的步驟 | 資訊已丟失，帶完整 context 重啟 |
| 中途打斷 | 操作未完成就 compact | 手動在 70% 時 checkpoint |

### 2.4 推薦 Compaction 模式

```
在 CLAUDE.md 中加入：
"When compacting, MUST preserve: modified file list, test results,
active plan, user decisions, and unresolved errors"
```

**黃金法則：** 在 **70%** 容量時主動 `/compact`，不要等自動觸發（83.5%）。你控制保留什麼比系統自動摘要更精準。

**建議 compact 指示模板：**
```
/compact Focus on: [當前任務描述].
Preserve: files modified ([列出檔案]), test status, pending decisions.
Drop: exploration results already committed, verbose tool outputs.
```

---

## 3. CLAUDE.md 最佳化

### 3.1 檔案位置與載入順序

| 範圍 | 位置 | 用途 | 分享對象 |
|------|------|------|---------|
| 組織政策 | `C:\Program Files\ClaudeCode\CLAUDE.md` | IT 管理的全域規則 | 全組織 |
| 專案 | `./CLAUDE.md` 或 `./.claude/CLAUDE.md` | 團隊共享的專案規範 | 透過 git 分享 |
| 個人 | `~/.claude/CLAUDE.md` | 個人偏好 | 只有自己 |

**載入機制：**
- 向上走：從工作目錄往上每層都檢查
- 向下走：子目錄的 CLAUDE.md 在讀取該目錄檔案時才載入（lazy load）
- `.claude/rules/*.md` — 模組化規則，支援 `paths:` frontmatter 做條件載入
- `@path` import — 引入外部檔案，最多 5 層遞迴

### 3.2 最佳長度與結構

**目標：每個 CLAUDE.md 檔案 < 200 行。**

過長的後果：重要規則被埋沒，Claude 選擇性忽略。

**結構原則：**
- 用 markdown headers + bullets 分組
- 具體可驗證（"用 2-space indentation" 而非 "格式化好一點"）
- 互相矛盾的規則 → Claude 會隨機選一個
- HTML 註解 `<!-- -->` 會在載入時被移除（不佔 token）

### 3.3 Global vs Project 分工

| 放 Global (`~/.claude/CLAUDE.md`) | 放 Project (`./CLAUDE.md`) |
|----------------------------------|---------------------------|
| 語言偏好（繁體中文） | Build/test 命令 |
| Commit message 風格 | 專案架構決策 |
| 個人工具快捷鍵 | 程式碼風格規範 |
| Runtime 版本偏好 | 分支/PR 命名規則 |
| 通用 compact 保留指示 | 專案特有的 gotchas |

### 3.4 Token 浪費最佳化

| 做法 | 效果 |
|------|------|
| 刪除 Claude 已經會做對的指示 | 直接省 token |
| 用 hooks 取代行為指示 | 確定性 + 省 context |
| 用 skills 取代領域知識 | 按需載入，不佔每次 startup |
| 用 `.claude/rules/` + `paths:` 條件載入 | 只在碰到相關檔案時載入 |
| 用 `@import` 引入長文件 | 保持主檔簡潔 |
| Progressive disclosure（skills-first） | 實測省 ~15K tokens/session（82% 改善） |

### 3.5 指示優先級與定位

- **強調標記有效：** `IMPORTANT:` 和 `YOU MUST` 提高遵守率
- **位置效應：** 靠前的指示更容易被注意到（LLM 的 primacy bias）
- **衝突解決：** 更具體的位置（project）勝過更廣泛的（global）
- **User rules** 在 project rules 之前載入，project 優先級更高

---

## 4. Memory System 設計

### 4.1 四層記憶架構

| 層 | 來源 | 載入時機 | 持久性 |
|----|------|---------|--------|
| CLAUDE.md | 人工撰寫 | 每次啟動（完整載入） | 永久（git 管理） |
| Auto Memory (MEMORY.md) | Claude 自動寫入 | 每次啟動（前 200 行 / 25KB） | 每個 project 目錄 |
| Session Memory | 自動摘要 | 新 session 時注入參考 | 每個 session 目錄 |
| Topic Files | Claude 自動分類 | 按需讀取（不自動載入） | 與 MEMORY.md 同目錄 |

### 4.2 儲存位置

```
~/.claude/projects/<project>/memory/
  MEMORY.md          # 索引（限 200 行 / 25KB，啟動時載入）
  debugging.md       # 主題檔（按需讀取）
  api-conventions.md # 主題檔（按需讀取）
  ...
```

- `<project>` 由 git repo 決定，同 repo 的 worktree 共享
- 非 git 目錄則以工作目錄路徑為 key
- 可用 `autoMemoryDirectory` 設定自訂路徑

### 4.3 Auto Memory 行為

- **版本需求：** Claude Code >= v2.1.59
- **寫入觸發：** Claude 判斷有「下次 session 會有用的資訊」時自動寫
- **寫入內容：** build 命令、debugging 洞察、架構筆記、程式碼風格、工作流習慣
- **不是每次都寫：** Claude 自己判斷是否值得記錄
- **開/關：** `/memory` toggle，或 `autoMemoryEnabled: false`

### 4.4 Auto Dream（記憶整合）

**觸發條件：** 24 小時以上 AND 5+ sessions 完成

**四階段流程：**
1. Orientation — 檢視現有 memory 目錄結構
2. Gather Signal — 從 session 紀錄中 grep corrections、explicit saves、recurring themes
3. Consolidation — 合併新資訊、轉換日期格式、移除過時事實
4. Prune & Index — 更新 MEMORY.md，維持 < 200 行

### 4.5 該存什麼 vs 該推導什麼

| 存入 Memory | 從程式碼推導（不需存） |
|-------------|---------------------|
| 非顯而易見的 build 命令 | 標準語言慣例 |
| 上次 debug 的 root cause | 程式碼結構（讀檔案就知道） |
| 你的偏好修正（"不要用 mock"） | API 用法（查文件） |
| 專案特有的 gotcha | 常見 pattern |
| 跨 session 的決策紀錄 | 每次可從 code review 得知的 |

### 4.6 Memory 組織策略

- MEMORY.md 當索引，不放詳細內容
- 詳細筆記分到 topic files（debugging.md, patterns.md）
- `/memory` 查看和編輯
- 「記住 X」→ 存 auto memory；「加到 CLAUDE.md」→ 需明確說
- `/remember` 可以把跨 session 的 pattern 提升到 CLAUDE.local.md

---

## 5. Subagent 隔離模式

### 5.1 為什麼需要 Subagent

**Context pollution 的量化：**
- 直接在主 context 搜索：169K tokens，91% 是噪音
- 用 subagent 搜索：主 context 只用 21K tokens，76% 是有用信號
- **8 倍** 更乾淨的 context

### 5.2 何時該用 Subagent

| 情境 | 用 Subagent | 用主 Context |
|------|------------|-------------|
| 預估產出 > 50K tokens | Yes | |
| 讀取大量檔案做 research | Yes | |
| Test output / log 分析 | Yes | |
| Verbose git history | Yes | |
| 快速問題（已在 context 中） | | Yes（用 `/btw`） |
| 需要寫入/修改程式碼 | | Yes |
| 需要看當前對話 context | | Yes |

### 5.3 高效 Subagent 模式

**Research Agent（最常用）：**
```
Use subagents to investigate how our authentication system handles
token refresh, and whether we have any existing OAuth utilities.
```
→ 探索完整 codebase，回報摘要，主 context 保持乾淨。

**Test Diagnostician：**
- 跑超 verbose 測試 → parse failures → git blame → 回報 root cause
- 主 context 只收到 2-3K 摘要而非 180K 的完整 log

**Code Reviewer：**
```
Use a subagent to review this code for edge cases
```
→ 獨立 context 審查，不帶實作偏見。

**Multi-Domain Parallel：**
- 多個 subagent 同時探索不同資料域
- 主 agent 綜合結果做決策

### 5.4 Subagent 注意事項

- **成本：** 多 agent session 約消耗 **3-4x** tokens
- **寫入衝突：** 多個 subagent 不要同時編輯同一檔案
- **通訊限制：** Subagent 之間不能直接通訊，只能透過 orchestrator
- **Worktree 隔離：** Agent Teams 中每個 agent 有獨立 git worktree
- **自訂 subagent：** `.claude/agents/xxx.md` 定義專門角色與工具權限

### 5.5 `/btw` vs Subagent 決策

| `/btw` | Subagent |
|--------|----------|
| 看得到完整 context | 獨立 context |
| 沒有工具存取 | 有定義的工具集 |
| 回答完即丟棄 | 結果回報主 context |
| 適合快速查詢 | 適合深度探索 |

---

## 6. 環境實測數據（2026-03-29 Baseline）

### 6.1 Context 開銷估算

基於目前的 harness 配置（12 plugins, 41+ skills, 7+ MCP servers）：

| 元素 | 估計 token 消耗 |
|------|----------------|
| System prompt + tools | ~20K |
| Plugins tool definitions | ~10-15K |
| CLAUDE.md (global 33 行 + project 22 行) | ~1-2K |
| Memory files (5 files, ~5KB) | ~2-4K |
| **啟動時 overhead** | **~33-41K** |
| **1M window 可用** | **~800-810K** |

### 6.2 Plugin 分類與使用頻率

**測量方法：** 從 `settings.json` 的 `enabledPlugins` 列出，手動分類使用頻率。精確 token 測量需要在新 session 中用 `/cost` 比對。

| Plugin | 功能 | 使用頻率 | 備註 |
|--------|------|---------|------|
| compound-engineering | Plans, reviews, skills | 核心 | 提供 52 agents, 41+ skills |
| context7 | Library docs lookup | 核心 | 查文件必用 |
| github | GitHub API integration | 核心 | PR, issues |
| claude-mem | Cross-session memory | 頻繁 | 目前資料為空 |
| claude-hud | Status line display | 頻繁 | UI 輔助 |
| telegram | Telegram bot bridge | 頻繁 | 訊息通道 |
| review-loop | Codex review loop | 偶爾 | 特定 review 流程 |
| cartographer | Codebase mapping | 偶爾 | 新 repo onboarding |
| playwright | Browser automation | 偶爾 | Web testing |
| chrome-devtools-mcp | Chrome debugging | 偶爾 | Web debugging |
| typescript-lsp | TS language server | 偶爾 | 只在 TS 專案用 |
| pyright-lsp | Python type checker | 偶爾 | 只在 Python 專案用 |

**觀察：**
- 核心（每次都用）：3 個 — compound-engineering, context7, github
- 頻繁（每週多次）：3 個 — claude-mem, claude-hud, telegram
- 偶爾（特定任務）：6 個 — 這些的 tool definitions 仍佔 context
- compound-engineering 是最大的單一 plugin（52 agents, 41+ skills），但它的 tool definitions 是按需載入的
- LSP plugins (typescript-lsp, pyright-lsp) 在非相關專案中佔用 context 無意義

**未來優化方向（不在本次範圍）：**
- 考慮為不同工作類型建立 plugin profile（如：vault-only, web-dev, python-dev）
- 低頻 plugins 可在不需要時暫時停用以節省 context

---

## 迭代紀錄

### Sprint 1 — 2026-03-29

**做了什麼：** 完整研究 context engineering 五大面向
**來源：** Anthropic 官方文件、ClaudeFast 技術分析、社群最佳實踐、Jason Liu 的 subagent 研究
**關鍵數字：**
- 1M window 實際可用 ~830K (83%)
- Auto-compact buffer: 33K tokens (16.5%)
- CLAUDE.md 建議 < 200 行
- MEMORY.md 只載入前 200 行 / 25KB
- Subagent 讓主 context 噪音從 91% 降到 24%
- 70% 容量時手動 compact 比 83.5% 自動 compact 更好
- Auto Dream 需要 24hr + 5 sessions 才觸發
**哪裡卡住：** 1M window 的退化曲線沒有精確數據（只有 200K 的）
**下次要試：** 實測自己的 session context 分佈（用 `/context`），建立基線
**知識複利：** 這份研究可以直接作為未來 CLAUDE.md 調優的參考依據

### Sprint 2 — 2026-03-29（實作落地）

**做了什麼：** 將 Sprint 1 研究成果轉化為可操作的配置變更
**變更清單：**
- Project CLAUDE.md 瘦身：78 行 → 22 行（-72%），消除與 CONVENTIONS.md/AGENT.md 的重複
- Global CLAUDE.md Context Hygiene 擴充：3 行 → 11 行，加入 compaction 觸發時機、保留優先級、subagent 門檻
- Memory 系統強化：新增 `feedback_context_hygiene.md`，記錄 context engineering 實戰知識
- Plugin baseline：12 個 plugins 分類完成（3 核心 / 3 頻繁 / 6 偶爾）
**學到什麼：**
- Plan 的前提假設（memory 目錄為空、68 行 CLAUDE.md）在執行時已過時——另一個 session 已建立了 5 個 memory 檔案
- Document review 在規劃階段就能抓到這類「快照過時」問題，值得每次 plan 都跑
- CLAUDE.md 去重最大的挑戰不是決定刪什麼，而是確保引用指向（CONVENTIONS.md、AGENT.md）在 runtime 被讀取
**哪裡卡住：** `@import` vs 自然語言引用的行為差異——選了自然語言引用（省 token），但需要驗證 Claude 是否在需要時主動讀取 CONVENTIONS.md
**下次要試：** 在新 session 中測試瘦身後的 CLAUDE.md 是否影響 vault 操作品質；用 `/context` 比對瘦身前後的 token 差異
**知識複利：** Global CLAUDE.md 的 Context Hygiene 規則現在是所有專案共享的——每個新 session 都自動受益

## 開放問題（已更新）

- [x] ~~1M context 的實際有效利用率是多少？~~ → 約 83%（830K/1M）
- [x] ~~Compaction 時哪些資訊最容易丟失？~~ → 精確技術細節、架構決策上下文
- [x] ~~怎樣的 CLAUDE.md 結構最有效？~~ → < 200 行、具體可驗證、hooks > instructions
- [ ] 1M window 在不同填充率下的品質退化曲線（只有 200K 數據）
- [ ] 12 plugins 的 tool definitions 各佔多少 tokens？（需在新 session 中用 `/cost` 實測）
- [ ] Auto Dream 整合後的 MEMORY.md 品質如何？需要人工校正嗎？
- [ ] 多 subagent 的成本效益平衡點在哪裡？

## Related

- [[tech-research-squad]]
- [[prompt-engineering-research]]
- [[harness-engineering-research]]
- [[compound-engineering-research]]
