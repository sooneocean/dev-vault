---
date: 2026-04-06
topic: agent-rewrite-protocol
---

# Agent Rewrite Protocol — Vault 局部重寫系統

## Problem Frame

AI agent（Claude Code、排程任務等）有大量可以幫助改善筆記品質的機會：
精煉摘要、生成 SEO 版本、整理下一步行動。但現有工具只有「覆蓋全文」或「人工貼上」
兩個選項，沒有「只改指定 section、留下人類內容不動」的安全路徑。

此系統要讓 AI agent 能夠：

1. 搜尋並精準定位目標筆記
2. 只改寫被筆記作者標記為「機器可寫」的 heading
3. 對高風險改寫產生候選稿而非直接覆蓋
4. 每次操作留下可追溯的 audit log

## Requirements

**Safety Protocol**

- R1. 任何寫入前必須先搜尋並確認唯一目標筆記；搜尋結果 >3 篇且無法確定目標時退回
- R2. 讀取 frontmatter 的 `machine_writable_headings` 與 `human_locked_headings`；後者命中時立即停止
- R3. `<!-- HUMAN-LOCK -->` / `<!-- /HUMAN-LOCK -->` 標記的區塊禁止任何 AI 寫入，不論 frontmatter 聲明為何
- R4. 預設行為永遠是 `draft`（寫入候選區），`replace` 需明確傳入且 heading 需在 `machine_writable_headings` 清單中
- R5. High 風險操作（整篇覆寫、改寫人類判斷區、無法確認目標唯一性）一律強制退回 `draft` 模式

**Write Modes**

- R6. `draft` 模式：產生候選稿，寫入目標 heading（例如 `Agent更新區`、`SEO改寫版`），不覆蓋人類正文
- R7. `replace` 模式：替換指定 heading 全部內容；僅允許 heading 在 `machine_writable_headings` 且風險等級不為 High 時使用
- R8. `append` 模式：在指定 heading 後追加內容；適用於 `參考資料`、`待辦`、`Agent Log`

**Frontmatter Schema（筆記端）**

- R9. 每篇允許 agent 改寫的筆記須有 `rewrite_mode`、`machine_writable_headings`、`human_locked_headings` 三個欄位
- R10. 每次成功寫入後自動更新 `updated`、`agent`、`confidence`、`source` 四個 frontmatter 欄位
- R11. 每次操作須追加結構化 log 至 `## Agent Log` heading；格式固定（timestamp、action、heading、confidence、mode、summary）

**Execution Engine（`windows-nodejs-rewriter.js`）**

- R12. 搜尋層使用 `clausidian search "<query>" --json`（非 `obsidian` 桌面 App 可執行檔）；JSON 回傳格式為 `{ results: [{ file, dir, title, ... }] }`，path 需由 `dir + "/" + file` 重組
- R13. REST API 層使用 Obsidian Local REST API（預設 `https://127.0.0.1:27124`）；Bearer token 由環境變數 `OLR_API_KEY` 提供
- R14. HTTPS 請求不得使用 Node.js native `fetch` 的 `agent` 選項（Node 24 靜默忽略）；改用 `https.request()` 或 `undici` dispatcher 實現 `rejectUnauthorized: false`
- R15. LLM 呼叫透過外部命令（`LLM_COMMAND` env var）實現，stdin 送入 prompt，stdout 讀取純文字輸出；不得包含 Markdown code fence
- R16. 失敗情境（搜尋無結果、heading 不存在、PATCH 失敗、LLM 輸出空白）一律寫入 Inbox 或 `Agent更新區`，不中途靜默退出

**LLM Adapter（`llm-adapter.js`，第四份文件）**

- R17. `llm-adapter.js` 實作 stdin → Claude API → stdout 的管道；使用既有 `@anthropic-ai/sdk`
- R18. 從 stdin 讀取完整 prompt 字串（UTF-8），呼叫 `messages.create`，將 assistant 回應純文字寫入 stdout
- R19. 支援以環境變數指定模型（`LLM_MODEL`，預設 `claude-sonnet-4-6`）與 max_tokens（`LLM_MAX_TOKENS`，預設 `2048`）
- R20. 輸出不包含任何 Markdown code fence 或額外格式；如 LLM 回傳 fence 則自動剝除後輸出

**Note Template**

- R21. 提供 `templates/t-rewrite-target.md` 作為可被 agent 局部改寫的筆記範本，包含所有必要 frontmatter 欄位與對應 heading 結構

## Success Criteria

- 對 `SEO改寫版` 執行 `--mode draft` 不影響 `## 原始內容` 與 `## 人類判斷區`
- 對 `人類判斷區` 的任何寫入嘗試均拋出錯誤並停止
- `Agent Log` heading 在每次成功操作後有新的時間戳記錄
- 在 Node.js 24 Windows 環境下 HTTPS 請求正常完成（不因 `agent` 選項被忽略而導致憑證錯誤）

## Scope Boundaries

- 不支援整篇覆蓋（除非筆記整體標記 `rewrite_mode: full`，此為後期擴充）
- 不支援跨筆記批次（當前每次執行針對單一筆記）
- 不開發 Obsidian plugin
- 不做即時 watch；操作為手動觸發或排程觸發
- `llm-adapter.js` 僅接 Claude API；其他模型留給 `LLM_COMMAND` 替換

## Key Decisions

- **Clausidian over Obsidian binary**: `obsidian` 在 PATH 是桌面 App，vault 搜尋操作用 `clausidian --json`
- **Local REST API for partial writes**: CLI 無法做 heading-level PATCH，REST API 是唯一安全的局部改寫路徑
- **Draft-first safety**: 預設不覆蓋，只在明確條件下允許 replace
- **Stdout-piped LLM**: 以 stdin/stdout pipe 隔離 LLM 呼叫，讓主腳本不依賴特定 SDK

## Dependencies / Assumptions

- Obsidian Local REST API 外掛已安裝並啟用（預設 port 27124，HTTPS，Bearer token）
- `clausidian` CLI 在 PATH 中（已確認：`/c/Users/User/AppData/Roaming/npm/clausidian`）
- `@anthropic-ai/sdk` 已在 `package.json` dependencies（已確認：`^0.24.0`）
- `ANTHROPIC_API_KEY` 環境變數已設定（Claude API 連線需要）
- Node.js 24 環境（已確認：v24.12.0）
- Obsidian 桌面 App 保持開啟（Local REST API 需要 App 運行中）

## Outstanding Questions

### Resolve Before Planning

（無阻塞性產品決策——技術細節已足夠清晰，可進入 planning）

### Deferred to Planning

- [Affects R12][Technical] `clausidian search --json` 回傳 `{ results: [{ file, dir }] }`，path 重組邏輯（`dir + "/" + file` vs. `dir + "/" + file + ".md"`）需以實際輸出驗證
- [Affects R14][Technical] 選用 `https.request()` 或 `undici` dispatcher 替換 native fetch `agent`；兩者 API 差異需在實作時決定
- [Affects R11][Technical] `ensureHeading` 目前用 POST 追加新 heading；需確認 Local REST API POST 的 append 行為是否在檔尾添加而非覆蓋
- [Affects R17][Needs research] `@anthropic-ai/sdk` 0.24.0 的 `messages.create` non-streaming API 在 stdin/stdout pipe 模式下的 buffer 處理（大 prompt 是否需要分批）
- [Affects R19][Technical] `LLM_MODEL` 預設值：`claude-sonnet-4-6` 是目前最新 Sonnet；planning 時確認是否需要讓用戶可覆蓋為 `claude-opus-4-6`

## Artifacts to Produce

| 文件 | 位置 | 狀態 |
|------|------|------|
| `agent-rewrite-protocol.md` | `docs/` 或 vault `resources/` | 草稿提供，需落地 |
| `windows-nodejs-rewriter.js` | `scripts/` | 草稿提供，需修正 R12/R14 |
| `templates/t-rewrite-target.md` | `templates/` | 草稿提供，可直接落地 |
| `llm-adapter.js` | `scripts/` | **缺失，需新建** |

## Next Steps

→ `/ce:plan` for structured implementation planning
