---
title: "feat: Agent Rewrite Protocol — Vault 局部重寫系統"
type: feat
status: active
date: 2026-04-06
origin: docs/brainstorms/2026-04-06-agent-rewrite-protocol-requirements.md
---

# feat: Agent Rewrite Protocol — Vault 局部重寫系統

## Overview

建立一套讓 AI agent 安全局部改寫 Obsidian vault 筆記的執行系統。
主要交付三個可執行文件與兩份靜態文件：

1. `scripts/windows-nodejs-rewriter.js` — 改寫指揮腳本（已有草稿，需修正兩個破壞性 bug）
2. `scripts/llm-adapter.js` — Claude API stdin/stdout 橋接器（缺失，需新建）
3. `templates/t-rewrite-target.md` — 筆記範本（草稿可直接落地）
4. `docs/agent-rewrite-protocol.md` — 協議設計文件（落地到 repo docs/）

關鍵修正：(a) `obsidian` 桌面 App binary → `clausidian` CLI；(b) native fetch `agent` 選項無效 → `https.request()`。

## Problem Frame

AI agent 改寫 Obsidian 筆記時，只有「覆蓋全文」或「人工貼上」兩個路徑，缺乏只改指定 section、保留人類內容的安全機制。
現有草稿腳本有兩個在第一次執行就會失敗的 bug，以及一個缺失的 LLM 橋接器。
（參見 origin: `docs/brainstorms/2026-04-06-agent-rewrite-protocol-requirements.md`）

## Requirements Trace

- R1–R5 Safety Protocol：搜尋唯一目標、frontmatter 權限清單、HUMAN-LOCK、draft-first 預設、High 風險退回
- R6–R8 Write modes：draft / replace / append
- R9–R11 Frontmatter schema：`machine_writable_headings`、`human_locked_headings`、每次操作更新四欄位 + Agent Log
- R12 Clausidian search fix：正確 binary + JSON 格式 `{ results: [{ file, dir }] }`，path = `dir/file.md`
- R14 HTTPS fix：`https.request()` 取代 native fetch `agent` 選項
- R16 失敗退回：任何錯誤寫入 Agent更新區，不靜默退出
- R17–R20 LLM Adapter：stdin→Claude API→stdout，剝除 code fence，支援 `LLM_MODEL` / `LLM_MAX_TOKENS` env vars
- R21 Note template：`templates/t-rewrite-target.md`

## Scope Boundaries

- 不批次（每次執行針對單一筆記）
- 不開發 Obsidian plugin
- 不做即時 watch，手動或排程觸發
- `llm-adapter.js` 僅接 Claude API；其他模型由 `LLM_COMMAND` env var 指定

## Context & Research

### Relevant Code and Patterns

- `https.request()` 模式：`.claude/lib/github-api.js:31–88`（Promise wrapper、data 累積、statusCode 分支）
- clausidian binary 解析：`scripts/vlt.mjs:487–497`（`npm bin -g` fallback PATH）
- `@anthropic-ai/sdk` ESM 用法：`scripts/yolo-lab-seo-optimizer.js`（`import Anthropic from "@anthropic-ai/sdk"`, `messages.create()`, `content[0].text`）
- `spawnSync` stdin pipe：無直接先例，標準 Node.js `spawnSync({ input: prompt })` 模式
- 環境變數驗證與 `process.exit(1)` 錯誤模式：所有 `scripts/*.js`

### Institutional Learnings

- 無直接相關的 `docs/solutions/` 條目（此系統為首次建立）

### External References

- [Obsidian Local REST API OpenAPI spec](https://raw.githubusercontent.com/coddingtonbear/obsidian-local-rest-api/main/docs/openapi.yaml) — 確認 PATCH headers 與 response codes
- [clausidian source: search.mjs](https://github.com/redredchen01/Clausidian) — 確認 `file` 欄位不含 `.md`、`_vaultSource` 欄位

### Critical Verified Facts

| 問題 | 驗證結果 |
|------|---------|
| clausidian `file` 欄位格式 | **無 `.md` extension**；path = `dir + "/" + file + ".md"` |
| clausidian `--vault` flag | **不存在**；vault 由 `OA_VAULT` env var 或 auto-detect 決定 |
| Local REST API PATCH heading | 需要 `Operation`, `Target-Type`, `Target` headers；body 用 `text/markdown` |
| Local REST API PATCH frontmatter | `Target-Type: frontmatter`；body 用 `application/json`（quoted value） |
| `Create-Target-If-Missing: true` | 支援，可取代 `ensureHeading` POST workaround |
| Node.js 24 native fetch `agent` | **靜默忽略**；self-signed cert 設定無效 |
| undici in dependencies | **不在** `package.json`；只有 `http-cookie-agent` 間接使用，不可直接 import |

## Key Technical Decisions

- **`https.request()` 取代 native fetch**：無需新增依賴，直接複用 `.claude/lib/github-api.js` 模式；`rejectUnauthorized: false` 放在 `options` 物件中（適用 HTTPS 自簽憑證開發場景）
- **clausidian binary resolution**：複用 `vlt.mjs:487–497` 的 `clausidianBin()` 函式，`npm bin -g` → PATH fallback
- **`Create-Target-If-Missing: true` header**：取代原本的 `ensureHeading()` POST workaround；當 Agent Log heading 不存在時讓 REST API 自動建立
- **Document-map GET for heading validation**：PATCH 前先用 `GET /vault/{path}` 加 `Accept: application/vnd.olrapi.document-map+json` 取得 heading 清單，確認目標 heading 存在（而非讓 404 在 PATCH 時爆出）
- **`llm-adapter.js` ESM**：與 `scripts/` 其他腳本一致（`import Anthropic from "@anthropic-ai/sdk"`），`process.stdin` data 累積讀入完整 prompt
- **Frontmatter PATCH body encoding**：字串值用 `JSON.stringify(value)` 包成 `"value"` 形式；數字值直接序列化

## Open Questions

### Resolved During Planning

- **Path 重組格式**：confirmed `dir + "/" + file + ".md"` — `file` 欄位無 `.md` extension（已由 clausidian source 驗證）
- **`--vault` flag 存在否**：不存在；vault 從環境決定（`OA_VAULT`）
- **`ensureHeading` 正確做法**：使用 `Create-Target-If-Missing: true` header，不需要 POST 再 GET 確認
- **undici 可否直接使用**：不行，未在 `package.json` 中，改用 `https.request()`
- **`OLR_BASE_URL` 預設協議**：預設 HTTPS（`https://127.0.0.1:27124`）；`OLR_INSECURE=true` 配合 `rejectUnauthorized: false`

### Deferred to Implementation

- **REST API 404 message 格式**：heading 不存在時的 error body 結構，需看實際回應再決定錯誤訊息格式
- **大 prompt buffer**：`@anthropic-ai/sdk` 0.24.0 messages.create 的 max_tokens 上限及 stdin 大 prompt（>64KB）的行為，可在 llm-adapter.js 加 `process.stdin.setEncoding('utf8')` 後觀察

## High-Level Technical Design

> *此圖為方向性設計指引，非實作規格。實作時應以各 unit 的 Approach 欄位為準。*

```
User/Scheduler
     │
     ▼
windows-nodejs-rewriter.js
     │
     ├─ 1. spawnSync("clausidian", ["search", query, "--json"])
     │      └→ { results: [{ file, dir }] }  → path = dir/file.md
     │
     ├─ 2. GET /vault/{path}                  [https.request()]
     │      └→ full markdown text
     │      parseFrontmatter → validateWritePermission
     │
     ├─ 3. GET /vault/{path}                  [https.request()]
     │      Accept: application/vnd.olrapi.document-map+json
     │      └→ verify TARGET_HEADING exists
     │
     ├─ 4. GET /vault/{path}                  [https.request()]
     │      Target-Type: heading / Target: <heading>
     │      └→ current section content
     │
     ├─ 5. spawnSync(LLM_COMMAND, { input: prompt })
     │      └→  llm-adapter.js  →  Claude API  → stdout plain text
     │
     ├─ 6. PATCH /vault/{path}               [https.request()]
     │      Operation: replace|append
     │      Target-Type: heading / Target: <heading>
     │      Content-Type: text/markdown
     │
     ├─ 7. PATCH /vault/{path} × 4           [https.request()]
     │      Target-Type: frontmatter
     │      (updated, agent, confidence, source)
     │
     └─ 8. PATCH /vault/{path}               [https.request()]
           Target-Type: heading / Target: Agent Log
           Operation: append
           Create-Target-If-Missing: true
```

## Implementation Units

---

- [ ] **Unit 1: 修正 `scripts/windows-nodejs-rewriter.js`（R12, R14, R16）**

**Goal:** 修正兩個破壞性 bug（clausidian binary、HTTPS fetch）並改善 heading 驗證流程，讓腳本在 Node.js 24 + Windows 環境中正確運行。

**Requirements:** R1–R12, R14, R16

**Dependencies:** 無（修改既有文件）

**Files:**
- Modify: `scripts/windows-nodejs-rewriter.js`

**Approach:**

*Fix 1 — clausidian binary & search JSON parsing (R12)*

- 複製 `vlt.mjs:487–497` 的 `clausidianBin()` 函式（`npm bin -g` → PATH fallback）
- 將 `execFileSync("obsidian", [...])` 替換為 `spawnSync(clausidianBin(), ["search", query, "--json"], { encoding: "utf8" })`
- 解析回傳 JSON：`JSON.parse(stdout).results`（頂層結構 `{ results, _vaultName, _vaultSource }`）
- Path 重組：`(result.subdir || result.dir) + "/" + result.file + ".md"`（`subdir` 欄位在深層資料夾時由 clausidian 提供，非深層時缺失；用 OR fallback 統一處理）
- 搜尋結果為空時：`fail("找不到符合查詢的筆記")` (R1)
- 搜尋結果 > 3 時：`fail("搜尋結果過多，無法確定目標")` (R1)

*Fix 2 — HTTPS request layer (R14)*

- 新增 `apiFetch(path, options)` → Promise，內部使用 `https.request()`（模式參考 `.claude/lib/github-api.js:31–88`）
- options 物件：`{ hostname, port, path, method, headers, rejectUnauthorized: !CONFIG.insecure }`
- 回應 body 以 `data += chunk` 累積，`res.on("end")` 解析；`statusCode >= 400` 時 reject（帶 status code + body 摘要）
- 所有 `getNote`, `getHeading`, `patchHeading`, `patchFrontmatter`, `ensureHeading` 改呼叫此函式

*Fix 3 — Heading existence validation*

- 在 `main()` 中，取得 full note 後立即呼叫 `getDocumentMap(notePath)` 確認 `TARGET_HEADING` 存在於文件結構中
- `GET /vault/{path}` 加 `Accept: application/vnd.olrapi.document-map+json`；回傳 JSON，檢查 headings 陣列
- 若 heading 不存在：不論 mode 為何，一律 `fail()`（訊息說明 heading 名稱）；per R16，同時嘗試將錯誤摘要追加至 `Agent更新區`（若 `Agent更新區` 本身也不存在則只 fail，不做第二次 REST 呼叫）
- **不做自動 mode 切換**；讓呼叫方明確指定正確的 heading

*Fix 4 — `ensureHeading` 簡化*

- 移除原本的 `ensureHeading()` POST workaround（需要先讀全文再 POST）
- Agent Log 的 `patchHeading()` 呼叫改加 `Create-Target-If-Missing: "true"` header

**Patterns to follow:**
- `https.request()` wrapper：`.claude/lib/github-api.js:31–88`
- clausidian binary resolution：`scripts/vlt.mjs:487–497`
- `process.exit(1)` + `console.error()` 錯誤模式：`scripts/yolo-lab-seo-optimizer.js`

**Test scenarios:**
- Happy path: `searchNotePath("SEO自動化")` → results[0] with `dir="projects"`, `file="seo-automation"` → path = `"projects/seo-automation.md"`
- Edge case: results array empty → `fail()` called, `process.exit(1)`
- Edge case: results.length === 4 → `fail()` called due to ambiguity
- Edge case: `result.subdir` present (nested dir) → path uses subdir prefix instead of dir
- Edge case: `TARGET_HEADING` in `RISK_POLICY.lockedHeadings` → `validateWritePermission` throws before any REST call
- Edge case: mode=`replace`, heading NOT in `machine_writable_headings` → `validateWritePermission` throws
- Error path: REST API PATCH returns 404 → `fail()` with status + body message
- Error path: `OLR_INSECURE=false` + self-signed cert → https.request rejects; test that `rejectUnauthorized` wires correctly
- Error path: document-map GET shows `TARGET_HEADING` not in headings list → `fail()` called with heading name in message; no PATCH attempted; error summary appended to `Agent更新區` if it exists
- Edge case: `TARGET_HEADING` contains non-ASCII characters (e.g. `"Agent更新區"`) → `Target` header must be percent-encoded via `encodeURIComponent`; verify REST API accepts and routes correctly
- Integration: full success path — search → read → parse frontmatter → validate → get heading → LLM → PATCH heading → PATCH ×4 frontmatter → PATCH Agent Log with `Create-Target-If-Missing`

**Verification:**
- `node scripts/windows-nodejs-rewriter.js --query "test" --heading "Agent更新區" --mode draft` 對測試筆記執行完整流程，無 TypeError 或 HTTPS 錯誤
- `Agent Log` heading 在執行後有新的時間戳記錄
- `人類判斷區` 內容未被修改

---

- [ ] **Unit 2: 建立 `scripts/llm-adapter.js`（R17–R20）**

**Goal:** 提供 `stdin → Claude API → stdout` 的橋接器，讓 `windows-nodejs-rewriter.js` 透過 `LLM_COMMAND` 呼叫。

**Requirements:** R17–R20

**Dependencies:** Unit 1 可獨立進行（但 end-to-end 測試需要 Unit 1 完成）

**Files:**
- Create: `scripts/llm-adapter.js`
- Test: `test/llm-adapter.test.js` (optional, manual integration test)

**Approach:**

- ESM 模組（`import Anthropic from "@anthropic-ai/sdk"`）
- Env var 驗證：`ANTHROPIC_API_KEY` 缺失 → `console.error()` + `process.exit(1)`
- 讀取 stdin：`process.stdin.setEncoding("utf8")`，data event 累積，close event 觸發 LLM 呼叫
- 呼叫 `client.messages.create({ model, max_tokens, messages: [{ role: "user", content: prompt }] })`
- 取 `message.content[0]`，確認 `type === "text"` 後取 `.text`
- Code fence 剝除：`text.replace(/^```[\w]*\n?/m, "").replace(/\n?```$/m, "").trim()`
- 結果寫入 `process.stdout.write(cleaned + "\n")`
- 任何錯誤（API error、空輸出）→ `console.error` to stderr + `process.exit(1)`
- 環境變數：`LLM_MODEL`（預設 `claude-sonnet-4-6`）、`LLM_MAX_TOKENS`（預設 `2048`，parseInt）

**Execution note:** 此 adapter 在整合測試前可以手動驗證：`echo "Hello world" | LLM_COMMAND="" node scripts/llm-adapter.js` 或 `echo "Summarize this text" | node scripts/llm-adapter.js`

**Patterns to follow:**
- SDK import + `client.messages.create`：`scripts/yolo-lab-seo-optimizer.js`（ESM pattern）
- `content[0].type === "text"` guard：`scripts/yolo-lab-seo-optimizer-v2.js`

**Test scenarios:**
- Happy path: stdin prompt → Claude returns `"some text"` → stdout = `"some text\n"` (no fences)
- Happy path with fence: Claude returns `\`\`\`markdown\n content \n\`\`\`` → stripped to `"content"`
- Edge case: `ANTHROPIC_API_KEY` not set → stderr error message + exit code 1
- Edge case: Claude returns empty `content` array → stderr error + exit code 1
- Edge case: `content[0].type !== "text"` → stderr error + exit code 1
- Error path: network error during API call → stderr + exit code 1
- Edge case: `LLM_MAX_TOKENS=512` env var → passes `max_tokens: 512` to SDK (not default 2048)

**Verification:**
- `echo "用一句話描述Node.js" | ANTHROPIC_API_KEY=xxx node scripts/llm-adapter.js` 有文字輸出（非 code fence）
- Exit code 0 on success, 1 on error
- `LLM_COMMAND="node scripts/llm-adapter.js"` 可被 windows-nodejs-rewriter.js 的 `spawnSync` 正確驅動

---

- [ ] **Unit 3: 落地靜態 artifacts（R9, R21）**

**Goal:** 把兩份已有草稿的靜態文件寫入 repo，完成系統的協議文件與筆記範本。

**Requirements:** R9, R21

**Dependencies:** 無（可與 Unit 1/2 平行執行）

**Files:**
- Create: `templates/t-rewrite-target.md`
- Create: `docs/agent-rewrite-protocol.md`

**Approach:**

- `templates/t-rewrite-target.md`：使用 brainstorm 中的草稿，無需修改（frontmatter schema 完整，包含 `machine_writable_headings` / `human_locked_headings` 欄位及所有 heading 結構）
- `docs/agent-rewrite-protocol.md`：使用 brainstorm 中的草稿，落地到 `docs/`（repo 內設計文件，非 vault 資源）；確認各 section 與最終實作決策一致（特別是 binary name = clausidian、path 格式）

**Test expectation: none** — 靜態文件，無行為邏輯。

**Verification:**
- `templates/t-rewrite-target.md` 的 `human_locked_headings` 欄位值必須與 `scripts/windows-nodejs-rewriter.js` 中 `RISK_POLICY.lockedHeadings` 陣列完全一致（人工比對；若日後修改其中一方，另一方必須同步更新）
- `templates/t-rewrite-target.md` frontmatter 可被 `parseFrontmatter()` 正確解析
- 開啟 Obsidian，以此 template 建立一篇測試筆記，確認 headings 結構正確

---

## System-Wide Impact

- **Interaction graph:** 系統呼叫鏈為 `rewriter → clausidian CLI → stdout`、`rewriter → REST API → Obsidian App`、`rewriter → LLM_COMMAND → llm-adapter → Claude API`；三條 external dependency 各自有獨立錯誤路徑
- **Error propagation:** 所有錯誤最終 `process.exit(1)` 且對 stderr 輸出描述；REST API 4xx 以 status code + body 傳遞給 `fail()`；LLM 空輸出在 adapter 與 rewriter 兩層各自 guard
- **State lifecycle risks:** PATCH 操作是 idempotent（同 heading replace 可安全重試）；frontmatter 更新為最後一步，失敗不影響主要 heading 寫入（Agent Log 缺失不算 fatal）
- **API surface parity:** `LLM_COMMAND` env var 是 adapter 介面契約；`llm-adapter.js` 的 stdin/stdout 格式（pure text, no fences）必須穩定，任何格式調整都影響 `runLlm()` 的後處理
- **Integration coverage:** Unit 1 的 test scenarios 最後一項（完整流程 integration）是唯一能驗證三層組件一起運作的場景；建議至少對 `templates/t-rewrite-target.md` 的複本跑一次 draft mode 的端對端測試
- **Unchanged invariants:** vault 的 `clausidian sync` 索引機制不受影響；REST API 讀寫的是 markdown 文件本身，不動 clausidian 的 `_tags.md`/`_graph.md`（這些由 sync 重建）

## Risks & Dependencies

| Risk | Mitigation |
|------|------------|
| Obsidian App 未開啟時 REST API 連線失敗 | 腳本啟動時先做一次 `GET /` health check（Local REST API 提供根路由），失敗則給出明確錯誤訊息 |
| clausidian search 結果不含 `subdir` 欄位（深層筆記路徑錯誤） | `searchNotePath` 加保護邏輯：`item.subdir || item.dir`；Unit 1 test scenario 涵蓋 subdir 情況 |
| REST API PATCH 時 heading 名含非 ASCII 字元（中文 heading） | `Target` header 值需 percent-encode：`encodeURIComponent(heading)`；現有草稿已有 `encodeVaultPath` 函式，需同樣處理 heading 名 |
| `LLM_COMMAND` 設定為空字串時 `spawnSync` 行為不定 | 腳本啟動時 early-exit 驗證 `LLM_COMMAND` 非空（已在草稿中，保留此邏輯） |
| `@anthropic-ai/sdk` 0.24.0 stdin pipe 大 prompt（>64KB）阻塞 | llm-adapter.js 使用 data event 累積而非 readFileSync，不阻塞 event loop；若出現問題 deferred to implementation |

## Documentation / Operational Notes

- 使用前設定環境變數：`OLR_API_KEY`、`OLR_BASE_URL`（可省略，預設 `https://127.0.0.1:27124`）、`OLR_INSECURE=true`（開發期）、`LLM_COMMAND=node scripts/llm-adapter.js`、`ANTHROPIC_API_KEY`
- 開發測試建議先複製 `templates/t-rewrite-target.md` 為 vault 內的測試筆記，再用 `--mode draft` 執行，確認品質後才放開 `replace`
- REST API 憑證：生產環境可在 Obsidian Local REST API 外掛設定中匯出自簽憑證並信任，移除 `OLR_INSECURE=true` 需求

## Sources & References

- **Origin document:** [docs/brainstorms/2026-04-06-agent-rewrite-protocol-requirements.md](docs/brainstorms/2026-04-06-agent-rewrite-protocol-requirements.md)
- Related code (HTTPS pattern): `.claude/lib/github-api.js:31–88`
- Related code (clausidian bin): `scripts/vlt.mjs:487–497`
- Related code (SDK ESM): `scripts/yolo-lab-seo-optimizer.js`
- External docs: [obsidian-local-rest-api OpenAPI](https://coddingtonbear.github.io/obsidian-local-rest-api/)
- External docs: [clausidian GitHub](https://github.com/redredchen01/Clausidian)
