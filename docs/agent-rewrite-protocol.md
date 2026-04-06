# Agent Rewrite Protocol v1.0

目的：讓 AI agent 可以安全地在 Obsidian Vault 內執行重寫、補寫、摘要、結構整理，而不直接破壞人類核心內容。

## 一、設計原則

1. **先搜尋，後改寫**
   任何改寫前，必須先搜尋是否已有相同主題、相近筆記、現有草稿或對應 Project。

2. **局部優先，整篇最後**
   優先改寫指定 heading、指定區塊、指定 frontmatter 欄位。
   除非目標文件被標記為 machine-writable，否則不得整篇覆蓋。

3. **候選稿先行**
   高風險改寫先寫入「Agent更新區」或「SEO改寫版」等指定 heading，通過人工檢查後才進行正式覆寫。

4. **人類判斷不可覆蓋**
   以下區域禁止 AI 直接替換：
   - 人類判斷區
   - 決策紀錄
   - 原始摘錄
   - 手動標記為 human-locked 的區塊

5. **每次操作都留痕**
   每次改寫都必須更新 `updated`、`agent`、`confidence`、`source`，並寫入 Agent Log。

## 二、允許改寫的區域

### A. 允許直接改寫
- `## Agent更新區`
- `## 摘要`
- `## SEO改寫版`
- `## 下一步`
- frontmatter 中的以下欄位：`updated`、`agent`、`confidence`、`source`、`related`、`review_at`、`status`（僅限規則允許時）

### B. 只允許追加，不允許替換
- `## 參考資料`
- `## 相關連結`
- `## 待辦`

### C. 禁止 AI 直接改動
- `## 人類判斷區`
- `## 決策紀錄`
- `## 原始摘錄`
- 任意包含以下標記的區塊：
  - `<!-- HUMAN-LOCK -->`
  - `<!-- /HUMAN-LOCK -->`

## 三、改寫模式

| 模式 | 說明 | 適用場景 |
|------|------|---------|
| `draft` | 只產生候選稿，寫進目標 heading | 預設模式；高風險改寫 |
| `replace` | 直接替換指定 heading 內容 | 低風險區域；heading 在 `machine_writable_headings` 中 |
| `append` | 在指定 heading 後追加內容 | 摘要補充、待辦、補鏈建議 |

## 四、標準流程

1. 搜尋筆記（`clausidian search --json`）
2. 讀取全文或指定 heading（Obsidian Local REST API）
3. 驗證 document-map：確認 heading 存在
4. 檢查 frontmatter 權限規則
5. 生成改寫 prompt
6. 呼叫 LLM 產生內容（`LLM_COMMAND`）
7. 計算風險等級，決定最終 mode
8. 依模式執行：draft / append / replace
9. 更新 frontmatter（`updated`、`agent`、`confidence`、`source`）
10. 寫入 Agent Log

## 五、風險分級

### Low
- 改寫的是摘要、SEO版、下一步
- 目標 heading 在 `machine_writable_headings` 中
- 內容為格式整理、語句優化、條列結構化

### Medium
- 改寫的是內文說明段
- 涉及跨段落重組
- 會修改多個 heading

### High
- 嘗試整篇覆寫
- 嘗試修改人類判斷區
- 無法確認目標筆記是否唯一
- LLM 輸出品質異常

High 風險一律退回 draft 模式。

## 六、筆記 frontmatter 約定

```yaml
---
uid: p-example
title: 筆記標題
type: project
status: active
created: 2026-04-06T10:00:00+08:00
updated: 2026-04-06T10:00:00+08:00
source: manual
agent: human
confidence: 1.0
rewrite_mode: section-only
machine_writable_headings:
  - Agent更新區
  - 摘要
  - SEO改寫版
  - 下一步
human_locked_headings:
  - 人類判斷區
  - 決策紀錄
review_at: 2026-04-13
---
```

## 七、Agent Log 格式

```md
## 2026-04-06T18:20:00+08:00
- agent: dex-rewriter
- action: replace-heading
- target: projects/p-example.md
- heading: SEO改寫版
- confidence: 0.86
- source: agent-rewrite
- mode: draft
- summary: 依據原始內容生成 SEO 導向的重寫版本，未覆蓋人類正文
```

## 八、失敗處理

遇到以下情況，停止正式寫入：

- 搜尋結果超過 3 篇且無法確定目標
- 找不到指定 heading（document-map 驗證失敗）
- 命中 `human_locked_headings` 或 `RISK_POLICY.lockedHeadings`
- LLM 輸出空白或長度異常（< 20 chars）
- REST API PATCH 失敗
- frontmatter 缺失核心欄位

## 九、最小安全原則

預設行為永遠不是覆蓋，而是產生候選稿。
只有在以下條件**全部**滿足時，才允許 replace：

- 目標 heading 位於 `machine_writable_headings`
- heading 在 document-map 中確認存在
- 風險分級不是 High
- 找到唯一目標文件（搜尋結果 ≤ 3 且明確）
- LLM 輸出非空且長度 ≥ 20 chars

## 十、執行腳本

| 腳本 | 用途 |
|------|------|
| `scripts/windows-nodejs-rewriter.js` | 主執行腳本；CLI args: `--query`, `--heading`, `--mode` |
| `scripts/llm-adapter.js` | Claude API stdin/stdout bridge；由 `LLM_COMMAND` 指定 |

### 環境變數

| 變數 | 必填 | 說明 |
|------|------|------|
| `OLR_API_KEY` | ✅ | Obsidian Local REST API bearer token |
| `LLM_COMMAND` | ✅ | LLM 呼叫命令（e.g. `node scripts/llm-adapter.js`） |
| `ANTHROPIC_API_KEY` | ✅（使用 llm-adapter） | Claude API key |
| `OLR_BASE_URL` | — | 預設 `https://127.0.0.1:27124` |
| `OLR_INSECURE` | — | `true` 跳過 TLS 驗證（開發用） |
| `AGENT_NAME` | — | 預設 `dex-rewriter` |
| `LLM_MODEL` | — | 預設 `claude-sonnet-4-6` |
| `LLM_MAX_TOKENS` | — | 預設 `2048` |

### 快速開始

```bash
# 設定環境變數
export OLR_API_KEY=your-api-key
export OLR_INSECURE=true
export LLM_COMMAND="node scripts/llm-adapter.js"
export ANTHROPIC_API_KEY=your-anthropic-key

# draft 模式（安全，先看候選稿）
node scripts/windows-nodejs-rewriter.js \
  --query "SEO自動化" \
  --heading "SEO改寫版" \
  --mode draft

# 確認品質後才放開 replace
node scripts/windows-nodejs-rewriter.js \
  --query "SEO自動化" \
  --heading "摘要" \
  --mode replace
```

筆記範本：`templates/t-rewrite-target.md`
