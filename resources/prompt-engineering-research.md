---
title: "Prompt Engineering 研究"
type: resource
tags: [prompt-engineering, claude-code, llm, agent-workflow, reference, knowledge-management]
created: "2026-03-29"
updated: "2026-04-03"
status: active
subtype: research
maturity: growing
domain: ai-engineering
summary: "Prompt Engineering 深度研究 — Claude 特有技巧、XML 結構化、CoT/Few-shot 模式、CLAUDE.md 指令最佳化、Agent 工作流提示、反模式與 Opus/Sonnet 差異。"
source: "https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/overview, https://code.claude.com/docs/en/best-practices"
related: ["[[tech-research-squad]]", "[[context-engineering-research]]", "[[harness-engineering-research]]", "[[compound-engineering-research]]"]
relation_map: "tech-research-squad:extends, context-engineering-research:extends"
---

# Prompt Engineering 研究

## 核心問題

如何寫出讓 LLM 精準、一致、可靠地執行任務的指令？

---

## 1. Claude 4.x 世代的提示轉變

### 1.1 從 Claude 3 到 Claude 4.x 的關鍵差異

Claude 4.x（4.5/4.6）在 instruction following 上有根本性轉變：

| 面向 | Claude 3.x | Claude 4.x |
|------|-----------|-----------|
| 指令遵從 | 會「好心」推測你的意圖 | **照字面意義執行**（literal） |
| 輸出風格 | 較冗長，愛解釋 | 更簡潔、直接行動 |
| Tool 使用 | 保守，逐一呼叫 | 激進平行 tool calling |
| 不確定時 | 猜測並嘗試 | 傾向問你或表明假設 |
| Prefill | 支援（控制格式的利器） | **4.6 起最後一個 assistant turn 不再支援 prefill** |

**核心洞察：** Claude 4.5 takes you literally。如果你要求「一個 dashboard」，它可能只給你一個空白框架加標題——因為你沒要求內容。需要 "above and beyond" 行為的話，必須**明確寫出來**。

### 1.2 Adaptive Thinking（取代 Extended Thinking）

| 階段 | 機制 | 狀態 |
|------|------|------|
| 舊版 | `budget_tokens` 手動設定 thinking 預算 | 已在 4.6 deprecated |
| 過渡期 | "ultrathink" magic word → 觸發 31,999 token thinking | 2026-01-17 deprecated |
| 現行 | `effort` 參數 + 自適應 | **Claude 4.6 推薦方式** |

**Adaptive thinking 運作方式：** Claude 根據兩個因素決定思考深度——`effort` 參數（高/中/低）和查詢複雜度。兩者共同影響 thinking token 數量。

**實用建議：**
- 日常任務不需要調 effort——預設值通常夠用
- 複雜架構決策、多檔案重構 → 提高 effort
- Claude Code 中用 `/effort` 命令調整
- 效能隨 thinking token 數量**對數成長**——邊際效益遞減

### 1.3 Structured Outputs（取代 Prefill 控制格式）

**Constrained decoding（2025 年底推出）：** 編譯 JSON schema 為 grammar，在推理時限制 token 生成，**物理上不可能**產出不符 schema 的 JSON。

```python
# API 範例 — Structured Outputs
response = client.messages.parse(
    model="claude-sonnet-4-5-20250514",
    max_tokens=1024,
    messages=[{"role": "user", "content": prompt}],
    response_format={"type": "json_schema", "json_schema": schema},
)
```

**何時用什麼：**
| 需求 | 方法 |
|------|------|
| 保證 JSON 格式合規 | Structured Outputs（推薦） |
| 控制開頭文字（舊模型） | Prefill |
| 自由格式但有結構 | XML tags + 指示 |
| Tool 參數型別安全 | Strict tool use |

---

## 2. Claude 專屬提示技巧

### 2.1 XML Tags — Claude 的結構化利器

XML tags 是 Claude 最與眾不同的提示功能。它讓 Claude 把 prompt 解析為語義段落，而非線性文字。

**核心優勢：**
- **Clarity** — 清晰分隔指令、上下文、範例、輸入
- **Accuracy** — 減少 Claude 誤解 prompt 各段的機率
- **Flexibility** — 容易增刪修改 prompt 的部分
- **Parseability** — Claude 的輸出也用 XML，方便後處理

**最佳實踐：**

```xml
<instructions>
分析以下程式碼的安全性問題。
針對每個問題提供：嚴重程度、位置、修復建議。
</instructions>

<code language="python">
{{USER_CODE}}
</code>

<output_format>
以 JSON 陣列輸出，每個物件包含 severity, location, fix 欄位。
</output_format>
```

**關鍵規則：**
- 沒有「官方最佳 tag name」——取有意義的名字就好
- 保持一致：整個 prompt 用同樣的 tag 名稱
- 巢狀結構用於層次化內容
- 範例包在 `<example>` 裡（多個用 `<examples>`），Claude 不會把範例誤讀為指令
- `<thinking>` / `<answer>` 可以與 CoT 結合

### 2.2 System Prompt 結構

**推薦三段式結構（2026 最佳實踐）：**

```
[Identity] — 一句話說明角色
[Rules] — 行為約束與限制
[Output Format] — 輸出格式要求
```

**範例：**
```
You are a senior code reviewer specializing in TypeScript.

Rules:
- Only flag issues with severity >= medium
- Never suggest style changes unless they affect readability
- If unsure about intent, ask instead of assuming

Output: Return findings as a markdown table with columns:
| File | Line | Severity | Issue | Suggested Fix |
```

**重要原則：**
- System prompt 像一份合約——明確、有界、可驗證
- 「成功長什麼樣」比「不要做什麼」更有效
- 具體數字勝過形容詞（"最多 3 個建議" > "簡潔地"）
- `IMPORTANT:` 和 `YOU MUST` 提高遵守率
- 靠前的指示更容易被注意到（primacy bias）

### 2.3 Role Prompting

**2025-2026 的轉變：** 過度具體的 role prompting 反而可能限制 Claude 的有用性。

| 做法 | 效果 |
|------|------|
| "You are a helpful assistant" | 通用但穩定 |
| "You are a senior TypeScript engineer with 10 years experience" | 聚焦特定領域，效果好 |
| "You are Dr. Smith, a 42-year-old neurologist who graduated from MIT..." | 過度角色扮演，可能限制 helpfulness |

**建議：** 用一句話設定角色聚焦即可。Role 的價值在於**領域聚焦**，不在於人設細節。

---

## 3. 核心提示模式

### 3.1 Chain-of-Thought (CoT)

**何時用：** 複雜推理——算術、邏輯推導、多步驟分析。

**實作方式：**

| 方式 | 適用場景 |
|------|---------|
| `Think step by step` | 最簡單的觸發 |
| `<thinking>...</thinking>` tags | 明確分離推理與答案 |
| Few-shot + CoT | 在範例中示範推理過程 |
| Adaptive thinking（API） | Claude 自己決定 thinking 深度 |

**Claude 4.6 注意事項：** 如果已啟用 extended thinking / adaptive thinking，**不要在 prompt 中再加 CoT 指示**——會干擾模型自己的推理。先觀察 Claude 的自然 thinking 過程，再決定是否調整。

**進階 CoT 變體（2025）：**
- **Layered CoT** — 多層推理，適合高風險領域（醫療、金融）
- **Trace-of-Thought** — 拆分子問題，適合小模型
- **LongRePS** — 監督長 context 中的推理路徑

### 3.2 Few-shot / Multishot Prompting

**黃金法則：3-5 個範例最佳。**

**範例設計原則：**
- **Relevant** — 鏡像真實使用場景
- **Diverse** — 涵蓋邊界案例，避免 Claude 學到意外 pattern
- **Structured** — 包在 `<example>` tags 裡

```xml
<examples>
  <example>
    <input>Fix the login bug where users get 403 after password reset</input>
    <output>
      1. Root cause: Session token not refreshed after password change
      2. Fix: Call refreshToken() in resetPassword handler
      3. Test: Reset password → verify 200 on next request
    </output>
  </example>
  <example>
    <input>The dashboard loads slowly for users with 1000+ items</input>
    <output>
      1. Root cause: N+1 query in items.map(fetchDetails)
      2. Fix: Batch query with WHERE id IN (...) + pagination
      3. Test: Seed 2000 items → verify < 500ms load time
    </output>
  </example>
</examples>
```

**陷阱：** 重複相同範例會讓 Claude 過擬合到特定 pattern，而不是學會通用原則。

### 3.3 Prompt Chaining（任務分解）

**核心概念：** 把複雜任務拆成多個小步驟，每步有獨立 prompt，前步輸出餵入下一步。

**何時用 chaining vs 單一 prompt：**

| 單一 prompt | Prompt chain |
|------------|-------------|
| 任務簡單、獨立 | 多步驟、需要中間檢查 |
| 不需檢查中間結果 | 需要人工審查中間產出 |
| 速度優先 | 正確性優先 |

**常見 chain 模式：**
- Research → Outline → Draft → Edit → Format
- Extract → Transform → Analyze → Visualize
- Generate → Review → Refine → Verify

**Trade-off：** Chain 用延遲換取更高正確性——每個子任務更簡單，Claude 更容易做對。

### 3.4 Self-Check Pattern

在重要 prompt 最後加一個自檢步驟：

```
After generating your response, verify:
1. Does it address all requirements in <instructions>?
2. Is the output format correct?
3. Are there any assumptions not stated?
If any check fails, fix before outputting.
```

---

## 4. CLAUDE.md 指令最佳化

### 4.1 為什麼 CLAUDE.md 是 Prompt Engineering

CLAUDE.md 本質上就是一個**持久化的 system prompt**——它在每次 session 啟動時注入 context，影響 Claude 的所有後續行為。所以 CLAUDE.md 的最佳化就是 prompt engineering 的實踐。

### 4.2 指令容量上限

**實測數據：**
- Frontier LLM 可合理遵守約 **150-200 條指令**
- 非 thinking 模型能注意的指令數更少
- **過長 CLAUDE.md 的致命後果：** 重要規則被埋沒，Claude 選擇性忽略

**黃金法則：** 每個 CLAUDE.md 檔案 < 200 行。

### 4.3 指令設計原則

| 原則 | 好的範例 | 壞的範例 |
|------|---------|---------|
| 具體可驗證 | "用 2-space indentation" | "格式化好一點" |
| 說 why not what | "用 conventional commits（方便 changelog 自動生成）" | "commit message 要用 feat: 開頭" |
| 避免矛盾 | 同一主題只有一條規則 | "保持簡潔" + "提供完整細節" |
| 刪除已知行為 | 不寫 Claude 已經會做的事 | "在回覆中使用繁體中文"（如果 Claude 已從對話推斷） |

### 4.4 節省 Token 的進階技巧

| 技巧 | 機制 | 效果 |
|------|------|------|
| Hooks 取代行為指示 | 確定性執行，不佔 prompt | 100% 執行率 + 省 context |
| Skills 取代領域知識 | 按需載入 | 省 ~15K tokens/session（82%） |
| `.claude/rules/` + `paths:` | 條件載入 | 只在碰到相關檔案時載入 |
| `@import` 引入長文件 | 保持主檔簡潔 | 主檔可維持 < 50 行 |
| 刪除 Claude 已會的事 | 直接省 token | 減少噪音 |

### 4.5 指示優先級

```
組織政策（Program Files/CLAUDE.md）
  ↓ 被覆蓋
個人偏好（~/.claude/CLAUDE.md）
  ↓ 被覆蓋
專案規範（./CLAUDE.md）— 最高優先
```

- **位置效應：** 靠前的指示更容易被注意到
- **衝突解決：** 更具體的位置勝過更廣泛的
- **強調標記：** `IMPORTANT:` 和 `YOU MUST` 有效提升遵守率
- **HTML 註解** `<!-- -->` 會在載入時被移除（不佔 token）

### 4.6 CLAUDE.md Prompt Learning 效果

根據 Anthropic 內部測試：
- 僅優化 system prompt → 編碼效能提升 **5%+**
- 針對特定 repo 優化 → 效能提升 **11%+**
- 這證明 CLAUDE.md 的品質直接影響產出品質

---

## 5. Agent 工作流的提示設計

### 5.1 Skills vs System Prompts

**2025 年的核心轉變：** 從寫 ad-hoc prompt 到封裝可復用 Skill。

| 面向 | System Prompt | Skill |
|------|--------------|-------|
| 生命週期 | 每次 session 手動設定 | 永久存在，版本化 |
| 載入方式 | 每次啟動時全部載入 | 按需載入（Claude 判斷相關性） |
| 結構 | 自由文字 | YAML frontmatter + markdown body |
| Context 成本 | 固定佔用 | 只在使用時佔用 |
| 復用性 | 跨 session 需手動複製 | 跨 project 共享 |

**Skill 設計原則：**
- 不要 step-by-step 指令 — 給目標和約束
- 包含 scripts/libraries 讓 Claude 組合而非重建 boilerplate
- 單一用途、輕量（minimal tools）最大化可組合性

### 5.2 Subagent Prompt 設計

Claude Code 的 subagent 有獨立 context window、system prompt、tool 權限。

**有效的 subagent 指示：**
```markdown
# Role
You are a code security reviewer.

# Goal
Find security vulnerabilities in the provided codebase.

# Constraints
- Only report issues with CVSS >= 7.0
- Must include proof-of-concept exploit path
- Do NOT suggest style changes

# Output
Return a JSON array of findings with: severity, cwe_id, location, description, fix
```

**關鍵：** Subagent 看不到主對話 context，所以必須在 prompt 中提供所有必要資訊。

### 5.3 Tool-Use Prompting

**工具定義的品質直接影響 Claude 的工具使用品質。**

| 做法 | 效果 |
|------|------|
| 清楚的工具描述 | Claude 知道何時該用哪個工具 |
| 範例包含在 tool schema 中 | Claude 學會正確的參數格式 |
| `is_error: true` 回傳 | Claude 知道工具失敗了，會重試或通知用戶 |
| 結構化 JSON 回傳 | 比純文字更可靠 |

**Tool Search Tool（2025 新功能）：** 可以動態存取數千個 tools 而不消耗 context——類似 skill 的按需載入機制。

### 5.4 Claude Code 中的有效提示

**四種提示模式（by Stephane Derosiaux）：**

| 模式 | 說明 | 範例 |
|------|------|------|
| Explore | 開放式探索 | "How does our auth system work?" |
| Plan | 討論方案，不動手 | "Plan how to add rate limiting" |
| Execute | 精確執行 | "Add rate limiting to /api/login with 5 req/min per IP" |
| Review | 審查已有程式碼 | "Review this PR for edge cases" |

**最佳實踐：**
- 拆成 5-10 分鐘的小任務（一系列精確子任務 > 一個模糊大任務）
- 用 `/clear` 分隔不相關任務
- 描述 WHY（商業目標、用戶背景、成功標準）而不只是 WHAT
- 讓正確性可測量（程式碼通過測試、符合驗收標準）
- 讓 Claude 自己探索、規劃、實作——不要微管理

---

## 6. Opus vs Sonnet 提示差異

### 6.1 效能差距縮小

**2026 現況：** Sonnet 4.6 與 Opus 4.6 的差距是 Claude 歷史上最小的——SWE-bench 差距僅 **1.2 百分點**（79.6% vs 80.8%），但 Sonnet 只要 **1/5 的成本**。

### 6.2 行為差異

| 面向 | Sonnet 4.6 | Opus 4.6 |
|------|-----------|----------|
| 推理深度 | 可能壓縮中間步驟 | 展示完整推理過程 |
| 模糊指令 | 傾向直接行動 | 傾向確認假設、要求釐清 |
| Debug 風格 | 聚焦目標、問你是否解決 | 深度分析，可能長篇探討 |
| 寫作風格 | 更自然、更簡潔 | 可能過度解釋、hedging |
| 多檔案操作 | 能力足夠 | 跨檔案關聯更強 |
| 創意寫作 | 通常更好 | 傾向 verbose |

### 6.3 選擇策略

**核心法則：** 一個 well-prompted Sonnet **永遠**勝過一個 poorly-prompted Opus。

| 場景 | 推薦模型 |
|------|---------|
| 80%+ 的日常任務 | Sonnet 4.6 |
| 深度推理 / 研究分析 | Opus 4.6 |
| Agent Teams | Opus 4.6 |
| 多檔案關聯重構 | Opus 4.6 |
| 快速迭代 / 探索 | Sonnet 4.6 |
| 創意寫作 | Sonnet 4.6（通常更自然） |

**實用工作流：** 在 Claude Code 中，先用 Sonnet 探索和迭代，碰到需要深度推理的問題再切 Opus——很多開發者回報這是最佳組合。

---

## 7. Prompt Caching（成本最佳化）

### 7.1 機制

Prompt caching 讓你標記 prompt 中可重用的部分，後續請求使用 cached 版本。

| 動作 | 成本 |
|------|------|
| Cache write | 1.25x base input price |
| Cache read | **0.1x** base input price |
| 無 cache | 1x base input price |

**效果：** 長 prompt 可省高達 **90% 成本** + **85% 延遲**。

### 7.2 最低 cacheable 長度

| 模型 | 最低 tokens |
|------|-----------|
| Sonnet | 1,024 |
| Opus / Haiku 4.5 | 4,096 |

### 7.3 實用場景

- **Agent harness 的 system prompt：** 50 turn x 10K token prompt = 500K tokens → caching 後大幅節省
- **CLAUDE.md 內容：** Claude Code 每次啟動都重新載入 → 天然適合 caching
- **Tool definitions：** 固定不變 → 極適合 cache

**額外紅利：** Cache read tokens **不計入** Input Tokens Per Minute (ITPM) 限制（Sonnet 3.7+ on Anthropic API）。

---

## 8. 反模式（踩過的坑）

### 8.1 Prompt 設計反模式

| 反模式 | 症狀 | 修正 |
|--------|------|------|
| **模糊指令** | 輸出不穩定，每次不同 | 給具體成功標準和範例 |
| **過度工程** | Prompt 越長品質越差 | 精簡到必要最小 |
| **Kitchen sink session** | Context 被不相關內容灌滿 | `/clear` 分隔任務 |
| **無結構 context** | 回答空泛、離題 | 用 XML tags 分段 |
| **範例單一化** | Claude 學到錯誤 pattern | 多樣化範例，涵蓋邊界 |
| **CoT + Extended thinking** | 干擾模型自有推理 | 二擇一，不要同時用 |
| **跨模型用同一 prompt** | 效果不一致 | 每個模型家族調整 prompt |

### 8.2 CLAUDE.md 反模式

| 反模式 | 症狀 | 修正 |
|--------|------|------|
| **過長 CLAUDE.md** | 重要規則被忽略 | < 200 行，ruthlessly prune |
| **矛盾指令** | Claude 隨機選一個執行 | 每主題只保留一條規則 |
| **寫已知行為** | 浪費 token | 刪除 Claude 已經會做的事 |
| **全放主檔** | 每次載入所有規則 | 用 rules/ + paths: 條件載入 |
| **不可驗證指令** | "寫好的程式碼" | "所有函式有 JSDoc + 回傳型別" |

### 8.3 Agent 工作流反模式

| 反模式 | 症狀 | 修正 |
|--------|------|------|
| **微管理步驟** | Claude 失去靈活性 | 給目標+約束，不給步驟 |
| **模糊大任務** | 品質崩潰 | 拆成 5-10 分鐘的子任務 |
| **不清理 context** | Prompt drift | `/clear` + 新 session |
| **忽略中間驗證** | 錯誤累積到最後 | Prompt chain + checkpoint |
| **Subagent 不給完整 context** | 產出離題 | Subagent 看不到主對話，必須在 prompt 寫明所有資訊 |

---

## 9. 立即可用的 Prompt 模板

### 9.1 Code Review Prompt

```xml
<instructions>
Review the following code changes for:
1. Correctness bugs (logic errors, off-by-one, null handling)
2. Security issues (injection, auth bypass, data leak)
3. Performance problems (N+1, unnecessary allocation)

Severity levels: critical / major / minor
Only report issues with severity >= major.
</instructions>

<diff>
{{GIT_DIFF}}
</diff>

<output_format>
| File | Line | Severity | Category | Issue | Fix |
</output_format>
```

### 9.2 Bug Analysis Prompt

```xml
<context>
Project: {{PROJECT_NAME}}
Stack: {{TECH_STACK}}
</context>

<bug_report>
{{BUG_DESCRIPTION}}
</bug_report>

<instructions>
1. Identify the most likely root cause
2. Explain the failure chain (what triggers it)
3. Propose a fix with minimal blast radius
4. Suggest a regression test
</instructions>
```

### 9.3 CLAUDE.md Minimal Template

```markdown
# Project: [Name]

## Stack
[Language], [Framework], [Key libraries]

## Build & Test
- `npm test` — unit tests
- `npm run lint` — linting

## Conventions
- [Most important coding convention]
- [Most important naming convention]

## Gotchas
- [Non-obvious thing that trips up Claude]
```

---

## 迭代紀錄

### Sprint 4 — 2026-03-30

**做了什麼：** 全面深入 Prompt Engineering 研究——從 51 行 stub 擴充為完整的研究筆記
**來源：** Anthropic 官方文件（prompt engineering docs、extended thinking docs）、Claude Code best practices、社群實測分析、Prompt Builder 2026 指南
**關鍵發現：**
- Claude 4.x 的 literal instruction following 是最大行為轉變——prompt 需要比 3.x 更具體
- Prefill 在 4.6 最後一個 assistant turn 已不支援 → 用 Structured Outputs 取代
- Adaptive thinking 取代 budget_tokens/ultrathink → 用 `effort` 參數
- CLAUDE.md 優化可帶來 5-11% 效能提升（Anthropic 實測）
- Well-prompted Sonnet 永遠勝過 poorly-prompted Opus
- Prompt caching 可省 90% 成本 + 85% 延遲
- Skills 按需載入省 ~15K tokens/session（82% 改善）
**哪裡卡住：** 中文 vs 英文 prompt 的效果差異仍無可靠基準測試數據
**下次要試：**
- 實測自己的 CLAUDE.md 優化前後差異（用 `/cost` 對比）
- 建立常用 prompt 模板庫（在 .claude/skills/ 中封裝）
- 測試 Sonnet → Opus 切換工作流的實際效果
**知識複利：** 這份研究直接指導 CLAUDE.md 精簡、skill 設計、日常提示習慣——每個 session 都受益

## 開放問題（已更新）

- [x] ~~CLAUDE.md 中的指令優先級如何運作？~~ → 專案 > 個人 > 組織，靠前優先
- [x] ~~長 system prompt vs 短 system prompt 的 trade-off？~~ → < 200 行最佳；過長被忽略
- [ ] 中文 vs 英文 prompt 的效果差異？（需要自己建 benchmark）
- [ ] 不同 effort 等級對 Claude Code 日常任務的影響有多大？
- [ ] Structured Outputs 在 Claude Code agent 工作流中的最佳整合方式？
- [ ] 自訂 skill prompt 的品質如何系統性評估？
- [ ] Prompt caching 在 Claude Code（非 API 直接使用）中如何生效？

## Related

- [[tech-research-squad]]
- [[context-engineering-research]]
- [[harness-engineering-research]]
- [[compound-engineering-research]]
