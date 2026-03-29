---
title: "feat: Obsidian-Agent 底層效率改進 — Journal 自動化 + 知識迴路閉合"
type: feat
status: completed
date: 2026-03-29
origin: docs/brainstorms/2026-03-29-obsidian-agent-efficiency-requirements.md
---

# feat: Obsidian-Agent 底層效率改進

## Overview

驗證並強化現有的 session-stop hook，讓 journal 自動記錄有意義的活動摘要（而非僅時間戳），同時在 session 結束時自動重建索引。第二階段透過 slash command wrappers 將 compound-engineering 的產出橋接進 vault，閉合知識複利迴路。

## Problem Frame

obsidian-agent v0.7.0 + Claude Code 的 Stop hook 已在運行，但：
1. Journal 自動記錄只有 `[HH:MM:SS] Session ended (reason)`，缺少活動摘要
2. 索引不會在 session 結束時自動更新
3. compound-engineering 的 `/ce:compound` 和 `/ce:plan` 產出與 vault 完全斷裂

(see origin: docs/brainstorms/2026-03-29-obsidian-agent-efficiency-requirements.md)

## Requirements Trace

- R1. 驗證現有 Stop hook 是否正確接收 `last_assistant_message` 並寫入 journal
- R2. Journal 自動記錄至少包含時間戳 + 活動摘要（優先 `last_assistant_message`，fallback `git diff --stat`）
- R3. 追加到 Records 區段，不覆蓋手動內容
- R4. Stop hook 陣列追加 `obsidian-agent sync`
- R5. sync 在 journal 之後執行
- R6. `/ce:compound` 產出自動在 vault `resources/` 建立對應筆記
- R7. `/ce:plan` 產出在 vault 中有對應筆記
- R8. `/ce:review` 摘要可手動追加到 journal（手動觸發）
- R9. 不修改 compound-engineering 外掛本身

## Scope Boundaries

- 不修改 obsidian-agent CLI 核心（用 wrapper script 繞過）
- 不修改 compound-engineering 外掛
- 不做即時 file watcher
- `/ce:review` 為手動觸發，不自動攔截
- MCP server 修正不在本計畫 scope 內（已知問題，獨立處理）

## Context & Research

### Relevant Code and Patterns

- **Stop hook config**: `~/.claude/settings.json` → `hooks.Stop[0].hooks[0]`
- **Hook implementation**: `obsidian-agent/src/commands/hook.mjs` → `sessionStop()` 只讀 `stop_reason`，不讀 `last_assistant_message`
- **Slash command pattern**: `.claude/commands/*.md` — 每個都是一行描述 + CLI 呼叫 + manual fallback + `$ARGUMENTS`
- **Vault frontmatter**: `CONVENTIONS.md` — 必須有 title, type, tags, created, updated, status, summary, related
- **CE compound output**: `docs/solutions/[category]/*.md` — YAML frontmatter 有 title, date, category, problem_type, severity 等 13+ 欄位
- **CE plan output**: `docs/plans/YYYY-MM-DD-NNN-<type>-<name>-plan.md` — frontmatter 有 title, type, status, date, origin
- **Resource template**: `templates/resource.md` — 最適合橋接 CE 產出

### Institutional Learnings

- `docs/solutions/` 目錄尚不存在 — `/ce:compound` 從未被使用過，知識複利循環尚未啟動
- Journal 自動記錄品質偏低 — 只有 `[14:39:55] Session ended (user_exit)` 等級
- 已存在的 self-iteration plan (`docs/plans/2026-03-29-001-feat-workflow-self-iteration-plan.md`) 是相關但不同的工作

## Key Technical Decisions

- **Wrapper script over CLI modification**: `sessionStop()` 不讀 `last_assistant_message`，但 scope boundary 不改 CLI。解法：在 settings.json 中用 bash wrapper script 讀 stdin JSON、提取摘要、呼叫 `obsidian-agent patch`。這比改 CLI 更快驗證且風險更低。
- **Slash commands over PostToolUse hooks for CE bridge**: compound-engineering 產出檔案時沒有可靠的 hook 攔截點（Write tool 不區分寫到哪個目錄）。用 slash command wrapper（`/bridge-compound`, `/bridge-plan`）讓使用者在 CE 工作流結束後手動觸發橋接，更可控且不需要複雜的 matcher。
- **Minimal metadata mapping**: vault 筆記不需要保留 CE 的全部 13 種 problem_type enum — 只保留 title, date, category, severity 作為 tags，其他 metadata 在筆記正文中以連結指向原始 CE 檔案。
- **Phase 1 和 R4/R5 一起做**: sync 只是在 hook 陣列多加一行，不值得獨立成 unit。

## Open Questions

### Resolved During Planning

- **`obsidian-agent hook session-stop` 是否讀 stdin?** → 是，用 `readFileSync(0, 'utf8')` 讀 stdin 並 JSON.parse，但只取 `stop_reason` 欄位
- **hook 執行順序能否保證?** → 是，同一 matcher group 內按陣列順序依序執行
- **compound YAML 保留多少 metadata?** → 最少化：title + date + category + severity 轉為 tags，其他以連結指向原檔
- **plan 的 `origin` 能否用於自動連結?** → 是，`origin` 指向 brainstorm 檔案，可用來搜尋 vault 中的 related project

### Deferred to Implementation

- wrapper script 在 Windows (Git Bash) 環境下 jq + stdin 讀取是否穩定
- `obsidian-agent patch` 的 `--append` 行為是否正確追加到 `## Records` 而非檔案末尾
- `/ce:compound` 第一次使用時 `docs/solutions/` 的實際目錄結構

## High-Level Technical Design

> *This illustrates the intended approach and is directional guidance for review, not implementation specification.*

```
Session End
  │
  ├─→ Hook 1: wrapper script (bash)
  │     ├─ read stdin JSON
  │     ├─ extract last_assistant_message (truncate ~300 chars)
  │     ├─ extract timestamp
  │     ├─ obsidian-agent journal (ensure today's entry exists)
  │     └─ obsidian-agent patch journal --heading "Records" --append summary
  │
  └─→ Hook 2: obsidian-agent sync --vault "..."

After /ce:compound or /ce:plan:
  │
  └─→ User runs /bridge-compound or /bridge-plan
        ├─ read CE output file
        ├─ map metadata to vault frontmatter
        └─ obsidian-agent note (create vault resource note with related links)
```

## Implementation Units

- [x] **Unit 1: Session-stop wrapper script + sync hook**

**Goal:** 讓 session 結束時 journal 自動包含活動摘要，並自動重建索引

**Requirements:** R1, R2, R3, R4, R5

**Dependencies:** None

**Files:**
- Create: `scripts/session-stop-wrapper.sh`
- Modify: `~/.claude/settings.json` (Stop hook array)

**Approach:**
- 寫一個 bash script，用 `cat` 讀 stdin、`jq` 提取 `last_assistant_message`，truncate 到前 300 字元
- 先呼叫 `obsidian-agent journal --vault "..."` 確保 entry 存在
- 再呼叫 `obsidian-agent patch --vault "..." <today> --heading "Records" --append "- [HH:MM:SS] $SUMMARY"`
- fallback: 若 `last_assistant_message` 為空，用 `git diff --stat` 生成摘要
- 在 settings.json 的 Stop hook 陣列中：替換原本的直接 CLI 呼叫為 wrapper script，然後追加 sync hook

**Patterns to follow:**
- 現有 PostToolUse hooks 的 jq stdin 讀取模式
- `obsidian-agent hook session-stop` 的 `readFileSync(0)` 模式（參考但不複製）

**Test scenarios:**
- Happy path: session 結束，journal 出現 `- [HH:MM:SS] <last_assistant_message 摘要>`，且 `_tags.md`/`_graph.md` 索引更新
- Edge case: 今天還沒有 journal entry → wrapper 先建立再 patch
- Edge case: `last_assistant_message` 為空 → fallback 到 `git diff --stat`
- Edge case: stdin JSON parse 失敗 → 靜默失敗，不阻塞 session 結束
- Edge case: vault 中沒有任何改動 → 仍記錄 session 結束時間戳

**Verification:**
- 結束一個 session 後，查看 `journal/YYYY-MM-DD.md` 的 Records 區段有活動摘要
- `obsidian-agent health` 仍然 Grade A
- `_tags.md` 和 `_graph.md` 的 updated 時間 >= session 結束時間

---

- [x] **Unit 2: `/bridge-compound` slash command**

**Goal:** 將 `/ce:compound` 產出的學習文件橋接到 vault

**Requirements:** R6, R9

**Dependencies:** Unit 1（非強依賴，但順序上先做 Phase 1）

**Files:**
- Create: `.claude/commands/bridge-compound.md`

**Approach:**
- Slash command 接收一個引數：CE compound 檔案路徑（例如 `docs/solutions/workflow-issues/my-fix-2026-03-29.md`）
- 讀取 CE 檔案，提取 frontmatter（title, date, category, problem_type, severity）
- 呼叫 `obsidian-agent note "<title>" resource` 建立 vault 筆記
- 用 `obsidian-agent patch` 填入摘要（Problem + Solution 區段）、設定 tags（`[compound-learning, <category>, <severity>]`）、設定 source 指向原始 CE 檔案的相對路徑
- 更新 related links：連結到 `[[tech-research-squad]]` 和相關 project（如果能從 CE metadata 推導）

**Patterns to follow:**
- 現有 `.claude/commands/note.md` 的 slash command 結構
- `CONVENTIONS.md` 的 frontmatter 規範

**Test scenarios:**
- Happy path: 執行 `/bridge-compound docs/solutions/workflow-issues/example.md` → vault 中出現 `resources/example.md` 帶完整 frontmatter
- Edge case: CE 檔案不存在 → 顯示錯誤訊息
- Edge case: vault 中已有同名筆記 → 更新而非重複建立
- Integration: 新建的 vault 筆記出現在 `_index.md` 和 `_graph.md` 中

**Verification:**
- `obsidian-agent list --type resource --tag compound-learning` 列出橋接的筆記
- 筆記的 `related` 欄位包含 `[[tech-research-squad]]`
- `obsidian-agent health` 無退化

---

- [x] **Unit 3: `/bridge-plan` slash command**

**Goal:** 將 `/ce:plan` 產出的計畫文件橋接到 vault

**Requirements:** R7, R9

**Dependencies:** Unit 2（共用模式，但實際可平行）

**Files:**
- Create: `.claude/commands/bridge-plan.md`

**Approach:**
- Slash command 接收 plan 檔案路徑（例如 `docs/plans/2026-03-29-002-feat-obsidian-agent-efficiency-plan.md`）
- 讀取 plan frontmatter（title, type, date, origin）
- 呼叫 `obsidian-agent note "<title>" project` 建立 vault project 筆記（因為 plan 通常對應一個 project）
- 用 `obsidian-agent patch` 填入 Overview 和 Requirements Trace 區段
- 設定 tags（`[plan, <type>]`）、source 指向 plan 檔案路徑
- 若 `origin` 欄位存在（指向 brainstorm），嘗試在 vault 中找到對應筆記並建立雙向連結

**Patterns to follow:**
- Unit 2 的 bridge-compound pattern
- `templates/project.md` 的 project 筆記結構

**Test scenarios:**
- Happy path: 橋接本計畫 → vault 中出現 project 筆記帶正確 frontmatter 和 Requirements Trace
- Edge case: origin brainstorm 已有 vault 筆記 → related 欄位雙向連結
- Edge case: origin 欄位為空 → 跳過自動連結，只建立基本筆記

**Verification:**
- `obsidian-agent list --type project` 包含橋接的 plan 筆記
- 筆記的 related 欄位連結到對應的 brainstorm（如果存在）

---

- [x] **Unit 4: 驗證與文件化**

**Goal:** 端到端驗證所有改進，更新 vault 研究筆記

**Requirements:** All (R1-R9)

**Dependencies:** Units 1-3

**Files:**
- Modify: `resources/harness-engineering-research.md` (更新迭代紀錄)
- Modify: `projects/tech-research-squad.md` (更新 progress)
- Modify: `journal/2026-03-29.md` (記錄完成)

**Approach:**
- 手動觸發一次 session 結束，驗證 Unit 1 的 journal 摘要品質
- 執行一次 `/ce:compound`（記錄本次改進本身），然後 `/bridge-compound` 驗證 Unit 2
- 使用本計畫 bridge 到 vault 驗證 Unit 3
- 更新研究筆記的迭代紀錄（Sprint 2）

**Test scenarios:**
- Integration: 完整 session 結束 → journal 有摘要 + 索引更新
- Integration: `/ce:compound` → `/bridge-compound` → vault 筆記存在且健康
- Integration: `/bridge-plan` 本計畫 → vault project 筆記連結到 brainstorm

**Verification:**
- `obsidian-agent health` 維持 Grade A
- `obsidian-agent stats` 顯示筆記數增加
- 知識複利循環可示範：compound → bridge → vault → 下次 context 可用

## System-Wide Impact

- **Settings.json**: Stop hook 陣列從 1 個 hook 變為 2 個（wrapper + sync）
- **Session 結束延遲**: 增加 ~2-5 秒（wrapper script + sync），在 10 秒 timeout 內
- **Vault 結構**: 新增 `scripts/` 目錄（放 wrapper script）；`resources/` 可能增加 compound-learning 類型筆記
- **Slash commands**: 從 6 個增加到 8 個（`/bridge-compound`, `/bridge-plan`）
- **不受影響**: compound-engineering 外掛本身、其他 hooks（PostToolUse 格式化）、MCP server 配置

## Risks & Dependencies

| Risk | Mitigation |
|------|------------|
| Windows Git Bash 下 jq + stdin 管道不穩定 | wrapper script 用 `|| true` 確保不阻塞 session；首次驗證時測試 |
| `obsidian-agent patch --append` 行為不符預期 | 驗證階段 (Unit 4) 明確測試；fallback 方案是直接用 sed/awk 追加 |
| session timeout (10s) 不夠 wrapper + sync | 分開為兩個 hook entry，各自有 10s timeout |
| `/ce:compound` 從未使用過，`docs/solutions/` 結構未知 | Unit 2 的 bridge command 在讀取時驗證目錄結構，找不到則提示使用者 |

## Documentation / Operational Notes

- 完成後更新 `CLAUDE.md` 的 CLI Quick Reference 加入 `/bridge-compound` 和 `/bridge-plan`
- 更新 `resources/harness-engineering-research.md` 的 Sprint 2 迭代紀錄

## Sources & References

- **Origin document:** [obsidian-agent-efficiency-requirements](docs/brainstorms/2026-03-29-obsidian-agent-efficiency-requirements.md)
- Related plan: [workflow-self-iteration-plan](docs/plans/2026-03-29-001-feat-workflow-self-iteration-plan.md)
- Hook implementation: `obsidian-agent/src/commands/hook.mjs` → `sessionStop()`
- Sync implementation: `obsidian-agent/src/commands/sync.mjs`
- Claude Code hooks docs: https://code.claude.com/docs/en/hooks
- Compound-engineering skill sources: `~/.claude/plugins/cache/compound-engineering-plugin/compound-engineering/2.58.1/skills/`
