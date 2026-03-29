---
title: "feat: Context Engineering — Compaction 與 Memory 策略"
type: feat
status: completed
date: 2026-03-29
---

# feat: Context Engineering — Compaction 與 Memory 策略

## Overview

建立系統性的 context window 管理策略，涵蓋 CLAUDE.md 瘦身、compaction 指南強化、memory 系統啟用、subagent 隔離規範，讓每次 session 的 context 利用率最大化。

## Problem Frame

sooneocean 使用 Claude Code (Opus 4.6, 1M context) + 12 個 plugins 管理 Obsidian vault。目前的 context 管理痛點：

1. **CLAUDE.md 冗餘**：Project CLAUDE.md (78 行) 與 CONVENTIONS.md、AGENT.md 大量重複（CLI reference、directory structure、agent rules），每次對話浪費 token
2. **Compaction 指引薄弱**：Global CLAUDE.md 只有 3 行 context hygiene 規則，缺乏具體的手動 `/compact` 時機判斷和保留優先級
3. **Memory 系統初步建立但未完善**：project memory (`~/.claude/projects/*/memory/`) 已有 5 個種子檔案（user_profile、project_dev-vault、feedback_architecture、reference_tools、MEMORY.md），但缺乏本次 context engineering 研究的知識沉澱
4. **Plugin overhead 不透明**：12 個 plugins 的 system-reminder 佔用量未測量，可能是最大的固定 token 開銷（估計 35-46K）
5. **缺乏可操作的 subagent 隔離規則**：只有「大範圍探索用 subagent」的模糊指引，沒有具體判斷門檻

## Requirements Trace

**Content Optimization:**
- R1. Project CLAUDE.md 去重後 < 40 行，不重複 CONVENTIONS.md 和 AGENT.md 的內容
- R2. Global CLAUDE.md 的 Context Hygiene 區段擴充為具體的手動 `/compact` 策略（觸發時機、保留優先級、已知陷阱）
- R3. 審查並強化現有 memory 系統——確保涵蓋本次 context engineering 研究成果

**Operational Guidelines:**
- R4. 建立 subagent 隔離決策指南（量化門檻：預估輸出 > 50K tokens 或需讀取 > 3 個超過 500 行的檔案）

**Measurement & Documentation:**
- R5. 記錄 plugin overhead baseline 數據（12 個 plugins 的分類和估計開銷），為未來優化提供參考
- R6. 更新 `context-engineering-research.md` 的迭代紀錄，記錄具體數字和策略變更

## Scope Boundaries

- 不修改 Claude Code 本身或任何 plugin 原始碼
- 不做 plugin 停用（先測量，優化決策留到有數據之後）
- 不修改 `settings.json` 的 hook 配置（那是另一個 plan 的範圍）
- 不建立自動 compaction 機制（Claude Code 的 auto-compact 不可配置）
- `.claude/rules/` 條件載入屬於進階優化，本次僅在 Unit 1 評估可行性，不實作

## Context & Research

### Relevant Code and Patterns

- `C:\Users\User\.claude\CLAUDE.md` — Global 指令（25 行，精簡）
- `C:\DEX_data\Claude Code DEV\CLAUDE.md` — Project 指令（78 行，有冗餘）
- `C:\DEX_data\Claude Code DEV\CONVENTIONS.md` — 寫作規則（99 行，與 CLAUDE.md 重疊）
- `C:\DEX_data\Claude Code DEV\AGENT.md` — Agent 快速上手（82 行，與 CLAUDE.md 重疊）
- `C:\Users\User\.claude\settings.json` — 12 個 enabled plugins、hooks 配置
- `C:\Users\User\.claude\projects\C--DEX-data-Claude-Code-DEV\memory\` — 已有 5 個檔案（MEMORY.md、user_profile、project_dev-vault、feedback_architecture、reference_tools）

### Overlap Analysis

CLAUDE.md 與其他檔案的重疊內容：

| CLAUDE.md 區段 | 重疊來源 | 行數 |
|---------------|---------|------|
| Directory Structure 表格 | AGENT.md:59-65, CONVENTIONS.md 隱含 | 8 行 |
| Agent Rules 8 條 | CONVENTIONS.md:67-77 幾乎完全相同 | 9 行 |
| CLI Quick Reference | AGENT.md:7-45 更完整的版本 | 18 行 |
| Slash Commands 表格 | `.claude/commands/` 定義即來源 | 10 行 |
| Templates Available | AGENT.md 沒列但不關鍵 | 1 行 |

**可省約 50+ 行（65%）**，剩餘保留：What This Is、指向 CONVENTIONS.md/AGENT.md 的引用、Git 規則、compound-engineering 整合路徑。注意：CLAUDE.md 已新增 Additional directories 區段和 `/improve` 命令（在前次 plan 執行後加入），這些也需在瘦身時決定保留或移除。

### External References

- [Claude Code Best Practices — Anthropic Official](https://code.claude.com/docs/en/best-practices): CLAUDE.md < 200 行、引用路徑而非貼內容
- [Context Buffer Management](https://claudefa.st/blog/guide/mechanics/context-buffer-management): auto-compact 觸發在 83.5%，buffer 佔 ~33K
- [HyperDev 研究](https://hyperdev.matsuoka.com/p/how-claude-code-got-better-by-protecting): < 75% 使用率是推薦工作區間
- [Jason Liu Subagent 研究](https://jxnl.co/writing/2025/08/29/context-engineering-slash-commands-subagents/): subagent 可讓主 context 清潔度提升 8x
- [Claude Code Memory Docs](https://code.claude.com/docs/en/memory): MEMORY.md 前 200 行/25KB 會自動載入

## Key Technical Decisions

- **瘦身而非重寫**：CLAUDE.md 去重透過指向 CONVENTIONS.md / AGENT.md 的引用取代重複內容，而非重新組織整個指令架構。原因：最小改動、最大 token 節省，且 CONVENTIONS.md 和 AGENT.md 的內容已經組織良好
- **強化現有 memory 而非從零開始**：memory 目錄已有 5 個種子檔案，本次新增 context engineering 研究知識作為補充，而非重建。原因：現有 memory 包含已驗證的架構教訓和工具參考，不應丟棄
- **Guidelines over automation**：手動 `/compact` 和 subagent 策略以 CLAUDE.md 指令實現，不建自動化機制。原因：Claude Code 的 auto-compact（83.5% 觸發）不可配置，手動 `/compact` 加上良好指引已足夠。注意三個概念的區別：`/compact`（手動命令）、auto-compact（系統自動觸發）、compaction（壓縮過程的通稱）
- **先測量再優化 plugins**：只記錄 baseline 數據，不做停用。原因：沒有數據的優化是猜測

## Open Questions

### Resolved During Planning

- **CLAUDE.md 去重後放什麼？** → 只留 vault identity、指向 CONVENTIONS.md/AGENT.md 的引用、compound-engineering 整合路徑、Git 規則。其餘全部由 CONVENTIONS.md 和 AGENT.md 承載
- **Memory 需要補充什麼？** → 現有 5 個 memory 檔案已涵蓋 user profile、project status、architecture feedback、tool reference。缺少的是本次 context engineering 研究的知識沉澱（compaction 策略、subagent 門檻、plugin overhead 意識）→ 新增 `feedback_context_hygiene.md`
- **Subagent 門檻？** → 預估輸出 > 50K tokens 或需讀取 > 3 個超過 500 行的檔案時用 subagent（來自 Jason Liu 研究的 context 清潔度數據和 Claude Session Manager 的 50K token 門檻）

### Deferred to Implementation

- `.claude/rules/` 的具體內容和 `paths:` 配置——需要先完成 CLAUDE.md 瘦身，再評估哪些指令適合條件載入
- Plugin overhead 的具體數字——需要在真實 session 中測量
- Auto dream 機制觸發後 memory 是否需要人工修剪——需要累積足夠 session 後觀察

## Implementation Units

- [ ] **Unit 1: CLAUDE.md 瘦身**

**Goal:** 將 Project CLAUDE.md 從 78 行減至 < 40 行，消除與 CONVENTIONS.md/AGENT.md 的重複

**Requirements:** R1

**Dependencies:** None

**Files:**
- Modify: `C:\DEX_data\Claude Code DEV\CLAUDE.md`

**Approach:**
- 移除 Directory Structure 表格 → 改為 `See AGENT.md for directory structure and CLI reference`
- 移除 Agent Rules 8 條 → 改為 `See CONVENTIONS.md for writing rules and agent guidelines`
- 移除 CLI Quick Reference code block → AGENT.md 已有更完整版本
- 移除 Slash Commands 表格 → commands 定義在 `.claude/commands/` 中
- 移除 Templates Available 行 → 不關鍵
- 保留：What This Is（vault identity）、compound-engineering 路徑（`docs/plans/`, `docs/solutions/`）、Git 區段
- 加入一行指引：`For vault operations, ALWAYS read CONVENTIONS.md before manual edits. Use obsidian-agent CLI when available.`

**Patterns to follow:**
- Global CLAUDE.md 的精簡風格（25 行、每行都有明確用途）
- Anthropic 推薦的 CLAUDE.md 結構：指向詳細文件而非複製內容

**Test scenarios:**
- Happy path: 瘦身後的 CLAUDE.md < 40 行，仍包含 vault identity 和必要引用
- Happy path: 新的 session 中，Claude 仍能正確使用 obsidian-agent CLI（因為 AGENT.md 被引用而非被刪除）
- Edge case: CONVENTIONS.md 被引用但未被讀取——CLAUDE.md 的引用措辭應明確指示「在手動編輯前讀取」
- Integration: CLAUDE.md 的 compound-engineering 路徑引用仍與 `/ce:plan`、`/ce:compound` 的實際輸出路徑一致

**Verification:**
- CLAUDE.md < 40 行
- 沒有與 CONVENTIONS.md 或 AGENT.md 重複的內容段落
- vault identity 和 compound-engineering 整合路徑完整

---

- [ ] **Unit 2: Global CLAUDE.md — Compaction 策略擴充**

**Goal:** 將 Context Hygiene 區段從 3 行擴充為具體可操作的 compaction 指南

**Requirements:** R2, R4

**Dependencies:** None（可與 Unit 1 平行）

**Files:**
- Modify: `C:\Users\User\.claude\CLAUDE.md`

**Approach:**
- 擴充 `## Context Hygiene (1M)` 區段，加入：
  - **Compaction 觸發時機**：自然斷點（完成一個 feature/fix、切換任務前）；連續修正同一問題 2 次失敗時建議 `/clear` 而非 compact
  - **保留優先級**（排序）：(1) active plan/task list (2) user decisions (3) unresolved errors (4) modified file list (5) test results
  - **已知陷阱**：多次 compact 後摘要高度抽象化——超過 2 次 compact 建議 `/clear` + 改進 prompt 重啟
  - **Subagent 隔離規則**：預估探索輸出 > 50K tokens 或需讀取 > 3 個超過 500 行的檔案時用 subagent；stack traces 和 verbose logs 一律在 subagent 中處理
- 總行數控制在原有 3 行 → 約 12-15 行（仍遠低於 200 行上限）

**Patterns to follow:**
- 現有 Global CLAUDE.md 的簡潔命令式風格
- 用 `MUST`/`IMPORTANT` 標記關鍵規則（提高遵守率）

**Test scenarios:**
- Happy path: 新 session 啟動後，Claude 在適當時機主動建議 `/compact` 並說明保留了哪些資訊
- Happy path: 大範圍 codebase 探索時，Claude 主動使用 subagent 而非在主 context 中 Read 所有檔案
- Edge case: 連續 2 次 compact 後，Claude 建議 `/clear` 而非繼續壓縮
- Error path: 使用者要求在 context 快滿時繼續工作——Claude 應警告而非靜默降級

**Verification:**
- Global CLAUDE.md 的 Context Hygiene 區段包含觸發時機、保留優先級、subagent 門檻
- 總行數 < 45 行（global CLAUDE.md 整體）

---

- [ ] **Unit 3: Memory 系統強化**

**Goal:** 審查現有 5 個 memory 檔案，補充本次 context engineering 研究的知識沉澱

**Requirements:** R3

**Dependencies:** Unit 2（compaction 策略確定後才能寫入相關 memory）

**Files:**
- Modify: `C:\Users\User\.claude\projects\C--DEX-data-Claude-Code-DEV\memory\MEMORY.md`
- Modify: `C:\Users\User\.claude\projects\C--DEX-data-Claude-Code-DEV\memory\feedback_architecture.md`
- Create: `C:\Users\User\.claude\projects\C--DEX-data-Claude-Code-DEV\memory\feedback_context_hygiene.md`

**Existing memory files (DO NOT overwrite):**
- `MEMORY.md` — 4 categories index (User, Project, Feedback, Reference)
- `user_profile.md` — sooneocean profile, already comprehensive
- `project_dev-vault.md` — vault status with completed/pending items
- `feedback_architecture.md` — architecture lessons about hooks, git, slash commands
- `reference_tools.md` — repos, skills, config paths

**Approach:**
- 審查現有 memory 內容是否仍正確，更新 `project_dev-vault.md` 的 pending items
- 新增 `feedback_context_hygiene.md` (type: feedback)：compaction 時機建議、subagent 隔離門檻、plugin overhead 意識——從本次研究萃取的可操作 context engineering 知識
- 更新 `MEMORY.md` 索引，加入新 memory 的引用
- 不重複已存在於 `feedback_architecture.md` 的內容

**Patterns to follow:**
- 現有 memory 檔案的 frontmatter 格式和風格
- MEMORY.md 的 4-category 索引結構

**Test scenarios:**
- Happy path: 新 memory 檔案與現有檔案無內容重疊
- Happy path: MEMORY.md 索引反映所有 memory 檔案
- Edge case: feedback_context_hygiene 的內容與 Global CLAUDE.md 的 Context Hygiene 互補而非重複——memory 記錄「為什麼」，CLAUDE.md 記錄「做什麼」
- Integration: auto dream 機制在未來 session 中可正確處理新增的 memory

**Verification:**
- 新增的 memory 檔案有完整 frontmatter
- MEMORY.md 索引包含所有 memory 檔案的引用
- 現有 memory 檔案的內容未被覆蓋或損壞

---

- [ ] **Unit 4: Plugin Overhead Baseline 測量**

**Goal:** 記錄當前 plugin 配置的 context 開銷數據，為未來優化提供參考

**Requirements:** R5

**Dependencies:** None（可與其他 Unit 平行）

**Files:**
- Modify: `C:\DEX_data\Claude Code DEV\resources\context-engineering-research.md`

**Approach:**
- 列出所有 12 個 enabled plugins 及其功能分類
- 用 `/cost` 或對話開始時的 token 使用量記錄 baseline
- 分類 plugins 為：核心（每次都用）、頻繁（每週多次）、偶爾（特定任務才用）
- 將數據記錄在 `context-engineering-research.md` 的迭代紀錄區段
- 不做停用決策——只提供數據和建議

**Patterns to follow:**
- `context-engineering-research.md` 現有的表格格式
- 研究筆記的迭代紀錄格式（日期 + 發現）

**Test scenarios:**
- Happy path: 12 個 plugins 全部列出，每個有功能描述和使用頻率分類
- Happy path: baseline 數據記錄在 context-engineering-research.md 的迭代紀錄中
- Edge case: 無法精確測量 token 開銷——記錄估計值和測量方法

**Verification:**
- context-engineering-research.md 有新的迭代紀錄條目
- Plugin 列表完整，有分類和建議

---

- [ ] **Unit 5: 研究筆記更新**

**Goal:** 將本次研究成果回饋到 vault 的 context-engineering-research.md

**Requirements:** R6

**Dependencies:** Unit 2, Unit 4（需要 compaction 策略和 plugin 數據作為輸入）

**Files:**
- Modify: `C:\DEX_data\Claude Code DEV\resources\context-engineering-research.md`
- Modify: `C:\DEX_data\Claude Code DEV\resources\_index.md`（如有需要更新 updated date）

**Approach:**
- 更新「已知策略」區段，加入本次研究發現的具體數字和策略
- 填入「迭代紀錄」區段——Sprint 記錄格式
- 更新「開放問題」——標記已回答的問題、新增新問題
- 加入 external references 到 Related 區段
- 更新 frontmatter 的 `updated` 欄位

**Patterns to follow:**
- `tech-research-squad.md` 的 Sprint 反思框架：做了什麼、學到什麼、哪裡卡住、下次要試、知識複利
- vault 的 `[[wikilink]]` 格式

**Test scenarios:**
- Happy path: 迭代紀錄包含具體的數字（1M window 利用率、compaction 觸發點、subagent 8x 改善）
- Happy path: 開放問題中已回答的問題有清楚的答案標記
- Integration: `_index.md` 的 updated date 與筆記的 frontmatter updated 一致

**Verification:**
- 迭代紀錄不為空
- 已知策略包含量化數據
- 開放問題有更新

## System-Wide Impact

- **Interaction graph:** CLAUDE.md 瘦身影響每次 session 的啟動 context。所有使用 CONVENTIONS.md 和 AGENT.md 的流程不受影響（這些檔案不被修改）
- **Error propagation:** 如果 CLAUDE.md 去重過度，Claude 可能遺漏某些指令——透過明確的引用指向（`See CONVENTIONS.md`）而非沉默刪除來降低風險
- **State lifecycle risks:** Memory 檔案一旦寫入就會在每次 session 載入。錯誤的 memory 會持續影響行為直到被刪除。種子 memory 只包含已確認的事實
- **API surface parity:** Global CLAUDE.md 的變更影響所有專案的 session——Context Hygiene 規則應保持通用性
- **Unchanged invariants:** CONVENTIONS.md、AGENT.md、`settings.json` hooks、obsidian-agent CLI 行為——全部不被本 plan 修改

## Risks & Dependencies

| Risk | Mitigation |
|------|------------|
| CLAUDE.md 去重後 Claude 不再讀 CONVENTIONS.md | 用明確措辭引導：「MUST read CONVENTIONS.md before manual edits」 |
| Global CLAUDE.md 過長影響其他專案 | 擴充控制在 < 15 行，遠低於 200 行上限 |
| Memory 種子內容過時後誤導未來 session | 只寫已確認事實；Auto dream 會自動修剪過時 memory |
| Plugin overhead 測量不精確 | 記錄測量方法和已知限制，未來可重複測量 |

## Sources & References

- Related vault notes: `context-engineering-research.md`, `harness-engineering-research.md`, `prompt-engineering-research.md`
- Related project: `tech-research-squad.md` (TODO: 深入研究 Context Engineering)
- Related plan: `2026-03-29-001-feat-workflow-self-iteration-plan.md` (CLAUDE.md 自動優化)
- External: Anthropic official docs, claudefa.st mechanics guides, HyperDev analysis, Jason Liu subagent research
