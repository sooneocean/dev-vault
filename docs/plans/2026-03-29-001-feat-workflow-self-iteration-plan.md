---
title: "feat: Claude Code 工作流自我迭代改進機制"
type: feat
status: completed
date: 2026-03-29
deepened: 2026-03-29
---

# feat: Claude Code 工作流自我迭代改進機制

## Overview

建立一個 on-demand 的回饋機制，讓 Claude Code 的配置（CLAUDE.md、settings.json hooks、slash commands）能根據累積的使用經驗系統化地迭代改進。核心入口是 `/improve` slash command，在 Claude 活躍的 session 中分析近期 journals、vault 狀態和當前配置，產生可審核的改善建議。

## Problem Frame

Claude Code 的配置（四層架構：Global → Project → Plugin → Runtime）目前是靜態手動維護。每次 session 產生的使用經驗洞察——哪些指令有效、哪些造成摩擦、哪些 hook 缺失——沒有系統化地回饋到配置中。

現有的基礎設施（session-stop hook、claude-mem 記憶、ce:compound 知識複利）各自解決部分問題，但缺乏一個系統化的方式把使用經驗轉化為配置改善。

## Requirements Trace

- R1. 提供系統化的方式從 journal entries、session context、vault 狀態中萃取配置改善信號
- R2. 提供一個 on-demand 入口（`/improve`）分析近期使用經驗並產生改善建議
- R3. 改善建議按配置層級（Global/Project）和風險等級分類
- R4. 低風險建議可快速套用，高風險建議需人工審核確認
- R5. 追蹤已套用的改善，避免重複建議
- R6. 改善歷史可在 Obsidian vault 中瀏覽管理

## Scope Boundaries

- 不修改 plugin 源碼或管理 plugin 安裝/移除
- 不做完全自主修改——Global 層配置永遠需要人工確認
- 初期聚焦 CLAUDE.md 內容、settings.json hooks、slash commands 三類配置
- 不建立獨立的後端服務或資料庫
- 不在 Stop hook 中執行信號收集（Stop hook 在 Claude session 結束後執行，Claude 不可用）
- 所有分析在 Claude 活躍的 session 中 on-demand 執行

## Context & Research

### Relevant Code and Patterns

- **四層配置架構**: Global (`~/.claude/`) → Project (`.claude/`) → Plugin → Runtime，記錄於 `resources/harness-engineering-research.md`
- **session-stop hook**: `settings.json` 中已有 `obsidian-agent hook session-stop` 觸發 journal 記錄。Stop hook 是 shell command，10 秒 timeout，Claude 不在此上下文中
- **slash command pattern**: `.claude/commands/*.md`，統一格式：描述 → 執行邏輯 → `$ARGUMENTS`。這些是 prompt templates，在 Claude session 內執行
- **journal entries**: 每日 journal 記錄 session 活動、學習和反思，是改善信號的自然數據源
- **反思框架**: `projects/tech-research-squad.md` 的 sprint reflection（做了什麼 / 學到什麼 / 哪裡卡住 / 下次要試 / 知識複利）
- **Global vs Project 配置**: `~/.claude/` 不是 git repo，不能用 git rollback。vault 目錄在 git 中

### Institutional Learnings

- Hooks 自動化空間很大，但 Stop hook 只能執行 shell commands，不能觸發 Claude 推理
- CLAUDE.md 結構最佳化仍是開放問題，自動修改有 context pollution 風險（context-engineering-research）
- 分層設定架構要求自動迭代機制明確區分改動的目標層級（harness-engineering-research）
- 目前 settings.json 已授予 Bash(*)、所有讀寫工具和 mcp__* 權限，permission friction 在此專案中不是問題

## Key Technical Decisions

- **`/improve` 為唯一入口，完全 on-demand**: 所有分析在 Claude 活躍的 session 中執行（Claude 可用且能推理），不使用 Stop hook 做信號收集（Stop hook 中 Claude 不可用）。使用者在需要時主動觸發。
  - *拒絕方案*: Stop hook 自動收集 → 架構上不可行，Claude 在 session 結束後不可用
  - *拒絕方案*: Stop hook 中 spawn 獨立 Claude API 呼叫 → 增加成本和延遲，overengineering

- **統一 `improvement` note type 取代 signal/proposal 分離**: 單一 note type 帶 `status` 欄位（`identified` → `proposed` → `applied` / `rejected`），減少模板和聚合管道的複雜度。
  - *拒絕方案*: 分離的 signal + proposal types → 需要額外聚合步驟，增加複雜度卻無明顯好處

- **分析 journals 和 vault 狀態作為信號來源**: `/improve` 讀取近期 journal entries（已包含反思框架）、當前配置檔、和 vault 健康狀態，在 Claude session 內即時分析。
  - *拒絕方案*: 解析 session JSONL → 格式複雜、token 密集，journal entries 已經是更好的結構化摘要

- **風險分層控制**: Project 層變更（`.claude/commands/`, vault CLAUDE.md）為低風險。Global 層變更（`~/.claude/settings.json`, `~/.claude/CLAUDE.md`）為高風險。
  - *依據*: harness-engineering-research 的分層架構觀察

- **分層 rollback 策略**: Project 層用 git（在 vault repo 中）。Global 層用 file backup（修改前複製 `.bak`），因為 `~/.claude/` 不是 git repo。
  - *拒絕方案*: 統一用 git rollback → `~/.claude/` 不在任何 git repo 中，不可行

- **信號類型聚焦三類**: missing hook（手動重複做的事）、instruction gap（CLAUDE.md 中缺少的指引）、command gap（常用但不存在的 slash command）。不包含 permission friction（目前所有權限已授予）。

## Open Questions

### Resolved During Planning

- **改善頻率？** → On-demand（使用者主動觸發 `/improve`）
- **存放位置？** → `resources/` 下以 `improvement-YYYY-MM-DD-NNN.md` 命名
- **如何避免 CLAUDE.md context pollution？** → 高風險分類 + 人工 diff 審核 + file backup rollback
- **Stop hook 能否用於信號收集？** → 不能。Stop hook 是 shell command，Claude 不可用。所有分析移到 on-demand
- **為什麼不分離 signal 和 proposal？** → 統一 note type 帶 status 欄位更簡單，避免聚合管道
- **Global 配置如何 rollback？** → file backup（.bak），不是 git（`~/.claude/` 不是 git repo）

### Deferred to Implementation

- 改善 note 的具體 frontmatter 欄位（需要幾次實際使用 `/improve` 才能確定最有用的欄位）
- CLAUDE.md 改善品質的量化評估方式（需要 baseline 數據）
- 多久清理一次過期的改善建議（取決於實際使用頻率）

## Implementation Units

- [x] **Unit 1: `/improve` 分析與建議 Slash Command**

  **Goal:** 建立核心 on-demand 入口，分析近期使用經驗並產生配置改善建議

  **Requirements:** R1, R2, R3, R6

  **Dependencies:** None

  **Files:**
  - Create: `.claude/commands/improve.md` — 主要 slash command 定義
  - Modify: `CLAUDE.md` — 在 Slash Commands 表格中註冊 `/improve`

  **Approach:**
  - `/improve` 在 Claude 活躍的 session 中執行（Claude 可推理和讀取檔案）
  - 讀取數據源：近期 `journal/*.md` entries（特別是反思框架中的「哪裡卡住」和「下次要試」）、當前 `~/.claude/settings.json` hooks 配置、當前 `CLAUDE.md` 指令、現有 `.claude/commands/` slash commands、`resources/improvement-*.md` 歷史記錄
  - 識別改善機會：missing hook（journal 中提到手動重複做的事）、instruction gap（session 中反覆需要解釋的事）、command gap（常用操作但沒有 slash command）
  - 為每個可行的改善產生 improvement note（`resources/improvement-YYYY-MM-DD-NNN.md`），初始 status 為 `proposed`
  - 呈現摘要給使用者，按風險等級排序（low → high），附帶具體變更建議
  - 低風險建議（Project 層 hook/command）標記為「建議快速套用」，高風險建議（Global CLAUDE.md/settings.json）標記為「需詳細審核」
  - 如果沒有發現改善機會，提示「目前配置運作良好，沒有待處理的改善建議」
  - `/improve` 在調用時使用 `update-config` skill 的能力來理解 settings.json 結構

  **Patterns to follow:**
  - 現有 `.claude/commands/*.md` 的統一格式：描述 → 執行邏輯 → `$ARGUMENTS`
  - `update-config` skill 理解 settings.json hooks 結構的方式

  **Test scenarios:**
  - Happy path: 近期 journal 中記錄了 3 次手動跑 lint → `/improve` 建議新增 PostToolUse lint hook，產生一個 improvement note
  - Happy path: journal 中多次提到 CLAUDE.md 缺少某個指引 → 產生高風險 proposal 帶 diff preview
  - Edge case: 沒有近期 journal entries → 提示需要先累積使用經驗
  - Edge case: 已存在相同改善建議（status=proposed 或 applied）→ 跳過不重複建議
  - Error path: journal 格式異常或缺少反思框架欄位 → graceful degradation，只分析可用數據
  - Integration: improvement note 的 `related` 欄位正確連結到 source journal entries

  **Verification:**
  - `/improve` 在 Claude Code session 中可正常執行
  - 產生的 improvement notes 有完整 frontmatter 和可操作的變更描述
  - 風險等級分類合理（Project 層 = low/medium，Global 層 = medium/high）
  - CLAUDE.md 中 Slash Commands 表格包含 `/improve` 條目

---

- [x] **Unit 2: 改善套用管道**

  **Goal:** 建立審核和套用已批准改善建議的機制，分層處理 Project 和 Global 配置

  **Requirements:** R4, R5

  **Dependencies:** Unit 1

  **Files:**
  - Modify: `.claude/commands/improve.md` — 擴展支援 `apply` 子命令
  - Modify: target config files at runtime

  **Approach:**
  - `/improve apply` 列出 status=proposed 的 improvement notes，使用者選擇要套用的
  - 套用前顯示 diff preview（變更前 vs 變更後）
  - **Project 層配置**（`.claude/commands/*.md`, vault `CLAUDE.md`）：直接修改 + git commit，commit message 格式 `chore(config): apply improvement - <brief description>`。Rollback 用 `git revert`
  - **Global 層配置**（`~/.claude/settings.json`, `~/.claude/CLAUDE.md`）：修改前複製 `.bak` 備份（如 `settings.json.bak.2026-03-29`）+ 額外提醒「此變更影響所有專案」。Rollback 用 `.bak` 檔案還原
  - settings.json 修改前進行 JSON parse 驗證，驗證失敗不套用
  - 更新 improvement note 的 `status` 為 `applied`，記錄套用日期和目標檔案路徑
  - 使用者拒絕時更新 status 為 `rejected`

  **Patterns to follow:**
  - `update-config` skill 的 settings.json 修改方式（用於理解 hooks 結構）
  - git conventional commit 格式

  **Test scenarios:**
  - Happy path: 選擇一個低風險 hook proposal → 顯示 diff → 確認 → settings.json 更新（含 .bak 備份） → improvement note status 變 applied
  - Happy path: 選擇一個 Project 層 slash command proposal → 顯示 diff → 確認 → 檔案更新 → git commit → status 變 applied
  - Edge case: 使用者拒絕套用 → status 更新為 `rejected`
  - Edge case: 沒有 proposed improvements → 提示「所有建議已處理」
  - Error path: settings.json 修改後 JSON parse 驗證失敗 → 不套用，報告錯誤
  - Error path: Global 配置套用後發現問題 → 指引使用者從 `.bak` 檔案還原
  - Integration: 套用的配置變更在下次 session 啟動時確實生效

  **Verification:**
  - Project 層變更有對應的 git commit
  - Global 層變更有對應的 `.bak` 備份檔案
  - settings.json 修改後仍是 valid JSON
  - improvement note 狀態正確更新

---

- [x] **Unit 3: 統一 Improvement Note Type 與模板**

  **Goal:** 建立正式的 improvement note type 和模板，融入 vault 規範

  **Requirements:** R6

  **Dependencies:** None（可與 Unit 1 平行開發，Unit 1 初期可用 inline 格式）

  **Files:**
  - Create: `templates/improvement.md` — 統一的 improvement 模板
  - Modify: `CONVENTIONS.md` — 新增 improvement type 的 frontmatter 規範（作為 resource 的子類型，使用 `type: resource` + `subtype: improvement`，保持 type-directory 一致性）

  **Approach:**
  - 單一模板，frontmatter 包含：title, type (resource), subtype (improvement), tags, created, updated, status (identified/proposed/applied/rejected), risk_level (low/medium/high), target_layer (project/global), target_file, friction_type (missing-hook/instruction-gap/command-gap), related
  - `status` 欄位驅動生命週期：`identified`（發現）→ `proposed`（有具體建議）→ `applied`/`rejected`
  - 使用 `type: resource` + `subtype: improvement` 而非新 type，保持 CONVENTIONS.md 的 type-directory 映射（resource → resources/）
  - 模板 body 包含：問題描述、建議變更（具體 diff 或指令）、預期效果、套用記錄

  **Patterns to follow:**
  - 現有 `templates/*.md` 的 `{{PLACEHOLDER}}` 語法
  - `CONVENTIONS.md` 中的 frontmatter schema
  - vault 的 type-directory 對應慣例

  **Test scenarios:**
  - Happy path: 模板中所有 `{{PLACEHOLDER}}` 都有對應說明，frontmatter 欄位齊全
  - Happy path: `obsidian-agent health` 通過，新 note type 不破壞現有索引
  - Edge case: status 從 proposed 直接跳到 rejected（跳過 applied）是合法的

  **Verification:**
  - 模板檔案存在且格式正確
  - CONVENTIONS.md 中有 improvement subtype 的完整定義
  - `obsidian-agent health` 無新增警告
  - `resources/` 目錄下的 improvement notes 與其他 resource notes 共存正常

---

- [x] **Unit 4: `/improve status` 追蹤子命令**

  **Goal:** 提供改善歷史的快速總覽

  **Requirements:** R5, R6

  **Dependencies:** Unit 1

  **Files:**
  - Modify: `.claude/commands/improve.md` — 加入 `status` 子命令支援

  **Approach:**
  - `/improve status` 讀取所有 `resources/improvement-*.md` notes，按 status 分組統計
  - 顯示：proposed 數量、applied 數量、rejected 數量、最近套用的改善清單
  - 如果有超過 30 天未處理的 proposed improvements，提醒使用者審核或清理
  - 不需要獨立的 dashboard note（初期用命令輸出即可，避免維護額外的靜態統計檔案）

  **Patterns to follow:**
  - `/list` slash command 的 vault 內容統計模式

  **Test scenarios:**
  - Happy path: 有 3 個 proposed、2 個 applied、1 個 rejected → 正確顯示統計和清單
  - Edge case: 沒有任何 improvement notes → 提示「尚無改善記錄，使用 `/improve` 開始」
  - Edge case: 有過期的 proposed improvements → 顯示提醒

  **Verification:**
  - `/improve status` 輸出簡潔且包含可行動的資訊
  - 統計數據與實際 vault 中的 improvement notes 一致

## System-Wide Impact

- **Interaction graph:** 使用者觸發 `/improve` → Claude 分析 journals + configs → 產生 improvement notes → `/improve apply` 套用 → config files 更新 → 下次 session 行為改善
- **Error propagation:** `/improve` 在 Claude session 中執行，錯誤由 Claude 直接報告給使用者。Config 套用失敗：Project 層用 git revert，Global 層用 .bak 檔案還原
- **State lifecycle risks:** 未處理的 improvement notes 可能累積；`/improve status` 的 30 天過期提醒作為清理機制
- **API surface parity:** `/improve`、`/improve apply`、`/improve status` 在 Claude Code session 中統一可用
- **Integration coverage:** 端對端驗證：journal 反思 → `/improve` 分析 → improvement note → `/improve apply` → config 更新 → 下次 session 驗證效果
- **Unchanged invariants:** 現有 session-stop journal hook 行為不變；現有 formatting hooks（ruff, prettier）不受影響；vault PARA 結構和 obsidian-agent CLI 行為不變；claude-mem 生命週期 hooks 不受影響

## Risks & Dependencies

| Risk | Mitigation |
|------|------------|
| CLAUDE.md context pollution（自動新增的指令降低整體品質） | 高風險分類 + 人工 diff 審核 + file backup rollback |
| Global 設定跨專案副作用 | Global 層變更永遠需要確認 + 「影響所有專案」警告 + .bak 備份 |
| settings.json 語法錯誤導致 Claude Code 啟動異常 | 套用前 JSON parse 驗證 + .bak 備份 |
| 改善建議品質依賴 journal 內容 | journal 反思框架提供結構化輸入；`/improve` 同時讀取配置現狀作為交叉驗證 |
| 改善建議循環衝突 | improvement note 記錄完整歷史 + 人工審核每次變更 |
| improvement notes 累積造成 vault 膨脹 | `/improve status` 30 天過期提醒 + 定期清理 |

## Sources & References

- Harness engineering research: `resources/harness-engineering-research.md`
- Context engineering research: `resources/context-engineering-research.md`
- Compound engineering research: `resources/compound-engineering-research.md`
- Tech research squad reflection: `projects/tech-research-squad.md`
- Claude Code configuration reference: `resources/claude-code-configuration.md`
- Document review findings: P0 — Stop hook 不能觸發 Claude 推理；P0 — `~/.claude/` 不是 git repo
