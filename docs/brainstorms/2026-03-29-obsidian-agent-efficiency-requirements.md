---
date: 2026-03-29
topic: obsidian-agent-efficiency
---

# Obsidian-Agent 底層效率改進

## Problem Frame

sooneocean 使用 obsidian-agent (v0.7.0) + Claude Code 管理 PARA 結構的 dev-vault（25 篇筆記、55 tags、116 relationships）。目前的痛點：

1. **Journal 品質不穩定** — Stop hook 已存在但尚未驗證 journal 內容品質（是否有 activity summary、時間戳）
2. **索引容易過期** — 手動編輯筆記後 `_index.md`、`_tags.md`、`_graph.md` 不會自動更新，需要手動跑 `obsidian-agent sync`
3. **知識是斷裂的** — `/ce:plan`、`/ce:review`、`/ce:compound` 的產出不會自動流入 vault，compound engineering 的知識複利迴路沒有閉合

## Current State（審查後更新）

**已存在的基礎設施：**
- `settings.json` 已有 Stop hook → `obsidian-agent hook session-stop`
- Stop hook 透過 stdin JSON 接收：`session_id`, `transcript_path`, `last_assistant_message`, `cwd`
- 同一 matcher group 的 hooks 按陣列順序依序執行（可保證 journal → sync）
- `obsidian-agent` v0.7.0 已有 `hook session-stop`, `hook daily-backfill`, `sync`, `watch` 命令

**尚未存在的：**
- Stop hook 陣列中沒有 `obsidian-agent sync`（索引不會自動更新）
- 沒有任何 compound-engineering ↔ vault 的整合

## Requirements

**Phase 1: 驗證與調優 Journal + 自動 Sync**

*Journal 品質驗證：*
- R1. 驗證現有 Stop hook 是否正確接收 `last_assistant_message` 並寫入 journal
- R2. Journal 自動記錄的內容至少包含：時間戳、活動摘要；摘要來源優先用 `last_assistant_message`，fallback 用 `git diff --stat`
- R3. 自動記錄應追加到現有 journal 的 Records 區段，不覆蓋手動寫入的內容

*自動索引（同 Phase 配置）：*
- R4. 在 Stop hook 陣列中追加 `obsidian-agent sync`，排在 session-stop 之後
- R5. sync 在 journal 之後執行，確保 journal 也被納入索引

**Phase 2: 知識迴路閉合**

*Compound → Vault：*
- R6. `/ce:compound` 的學習文件（`docs/solutions/[category]/*.md`）透過 PostToolUse hook 或 wrapper 自動在 vault `resources/` 中建立對應筆記，帶正確 frontmatter 和 related links
- R7. `/ce:plan` 的計畫文件（`docs/plans/*.md`）在 vault 中有對應筆記，連結到相關 project

*Review → Journal：*
- R8. `/ce:review` 的審查結果摘要可追加到當天 journal 的 Records 區段（手動觸發即可，不需全自動）

*實作約束：*
- R9. 上述整合以 Claude Code hooks 或 slash command wrapper 實現，不修改 compound-engineering 外掛本身

## Success Criteria

- Session 結束後 journal 自動有完整工作紀錄（含時間戳和摘要）
- 筆記索引在每次 session 結束時自動更新
- Compound engineering 的學習與計畫文件在 vault 中有對應筆記

## Scope Boundaries

- 不修改 compound-engineering 外掛本身
- 不修改 obsidian-agent CLI 核心（本階段以 vault 端配置為主）
- 不做 Obsidian app 的 plugin（純 CLI/MCP 層面）
- 不做即時 watch（file watcher），session 級別的觸發就夠了
- `/ce:review` 整合為手動觸發（review 結果不存檔，無法自動攔截）

## Key Decisions

- **Validate before build**: Phase 1 是驗證現有 hook，不是從零建立
- **Hook over Plugin**: 用 Claude Code hooks 實現自動化，不開發新的 plugin
- **Session-level, not real-time**: 在 session 結束時批次處理
- **Vault-first**: 先在這個 vault 跑通，驗證後再回饋改進到 obsidian-agent repo
- **Phase 2 各項獨立**: R6, R7, R8 是三個獨立整合，各自研究各自實作

## Dependencies / Assumptions

- Claude Code Stop hook 可靠觸發且 stdin JSON 包含 `last_assistant_message`（已由 research 確認）
- `obsidian-agent hook session-stop` 支援從 stdin 讀取 JSON（需驗證）
- Compound-engineering 輸出路徑 hardcoded（`docs/solutions/`, `docs/plans/`）

## Outstanding Questions

### Resolve Before Planning

（已全部解決 — 見 Research 結果）

### Deferred to Planning

- [Affects R2][Technical] `obsidian-agent hook session-stop` 是否已從 stdin 讀取 `last_assistant_message`？若否，需要修改 CLI 或用 wrapper script
- [Affects R6][Technical] compound 學習文件的 YAML frontmatter schema 有 13 種 problem_type — vault 端的筆記要保留多少 metadata？
- [Affects R7][Technical] plan 文件的 `origin` 欄位能否用來自動連結到 vault 中的 brainstorm/project 筆記？

## Next Steps

→ `/ce:plan` for structured implementation planning
