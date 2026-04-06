---
title: "Compound Engineering 研究"
type: resource
tags: [compound-engineering, knowledge-loop, workflow, learning-capture, reference, knowledge-management]
created: "2026-03-29"
updated: "2026-04-03"
status: active
subtype: research
maturity: growing
domain: ai-engineering
summary: "Compound Engineering 深度研究 — 知識複利迴路解剖、CE Plugin 六大指令深入分析、反模式與度量、本 vault 實測數據（Plans 001-005 → compound → bridge → vault）、與傳統軟體工程的範式對比。"
source: "https://every.to/chain-of-thought/compound-engineering-how-every-codes-with-agents, https://every.to/guides/compound-engineering, https://lethain.com/everyinc-compound-engineering/"
related: ["[[tech-research-squad]]", "[[prompt-engineering-research]]", "[[context-engineering-research]]", "[[harness-engineering-research]]", "[[compound-engineering-plugin]]", "[[dev-vault-status]]"]
relation_map: "tech-research-squad:extends, compound-engineering-plugin:documents, context-engineering-research:extends, harness-engineering-research:extends"
---

# Compound Engineering 研究

## 核心問題

如何讓每次工程工作累積為下次的加速器，而非增加技術債？

---

## 1. Compound Engineering 的範式轉變

### 1.1 從遞減報酬到知識複利

傳統軟體工程遵循**遞減報酬法則**：每新增一個功能都會注入更多複雜度，讓後續功能更難建構。十年後，團隊花更多時間對抗自己的系統而不是在上面建構，因為每個新功能都是在與舊功能談判。

**Compound Engineering 翻轉這個方程式：** 讓每個功能都為下一個功能複利——透過系統化地把所有學習編碼成可復用的 prompts、slash commands、subagents 和 hooks，讓程式庫變成一個不斷「自我教學」的系統。

| 面向 | 傳統工程 | Compound Engineering |
|------|---------|---------------------|
| 複雜度曲線 | 每個功能讓下一個更難 | 每個功能讓下一個更容易 |
| 知識存放 | 在人的腦中（離職即消失） | 編碼在 CLAUDE.md、hooks、docs 中 |
| Agent 錯誤 | 重複犯同樣的錯 | 學習記錄防止重複 |
| Bug 修復 | 修完就忘 | 變成系統永遠不會再犯的規則 |
| Code review 回饋 | 一次性 | 成為未來每次 review 的預設標準 |
| 新人 onboarding | 需要數週導師指導 | 內建記憶系統讓非專家立即生產 |

### 1.2 核心哲學：80/20 法則

Every Inc. 的核心洞察：**80% 規劃與審查、20% 執行。** 大部分思考發生在程式碼被寫出來之前和之後。

```
Plan + Review = 80% of time
Work + Compound = 20% of time
```

這看似違反直覺——為什麼花更多時間在「不寫程式」上？因為：
- **Plan 品質** 直接決定 agent 執行品質（垃圾進垃圾出）
- **Review 品質** 直接決定知識捕獲品質（學到什麼回饋什麼）
- **執行本身** 大部分由 agent 完成，人工干預越少越好
- **Compound 步驟** 把學到的東西編碼成系統永久記憶

### 1.3 生產力數據

根據 Every Inc. 及社群回報：

| 指標 | 數據 |
|------|------|
| 單人 vs 傳統團隊 | 1 人 = 5 人傳統團隊產出 |
| 功能交付速度 | 掌握 CE 的團隊 **3-7x** 快於傳統方法 |
| Every 的產品開發 | 5 個軟體產品各由 1 人主導開發運維 |
| Kevin Rose demo | 20 分鐘用 Claude Code 建出 Twitter/X clone |

**關鍵前提：** 這些數字建立在「每次迭代都確實 compound」的假設上。如果跳過 compound 步驟，效果會退化回傳統模式。

### 1.4 業界觀點

**Will Larson（Irrational Exuberance）的分析：**

Compound Engineering 由四個模式組成：
1. **Plan** — 把實作與研究解耦（類似 Claude plan mode）
2. **Work** — 按照計畫實作（agentic coding 的核心）
3. **Review** — 讓 agent 對照最佳實踐審查變更
4. **Compound** — 把學習編碼回系統

Larson 預測許多 CE 實踐會逐漸被 Claude Code 和 Cursor 等 harness 吸收。這意味著 CE 不是一個獨立工具，而是一個**即將成為標準的工作流範式**。

---

## 2. 知識複利迴路解剖

### 2.1 完整迴路（六階段）

```
Brainstorm → Plan → Work → Review → Compound → [Bridge → Vault] → Repeat
```

每個階段都有獨立的複利機制：

| 階段 | 目的 | 複利機制 | 產出物 |
|------|------|---------|--------|
| Brainstorm | 釐清需求、探索方案 | 需求文件可重用、decision log 累積 | `docs/brainstorms/*.md` |
| Plan | 拆解實作、研究依賴 | 計畫模板累積、document review 標準提升 | `docs/plans/*.md` |
| Work | 執行計畫、寫測試 | worktree 隔離風險、agent 技能庫成長 | 程式碼 + 測試 |
| Review | 多 agent 審查 | 審查標準持續提升、12 角度 parallel review | PR 審查報告 |
| Compound | 記錄學習 | 知識直接餵回下一輪、防止重複錯誤 | `docs/solutions/*.md` |
| Bridge | 知識入庫 | 結構化知識進入永久儲存 | vault `resources/*.md` |

### 2.2 迴路的三個齒輪

```
┌─────────────┐     ┌──────────────┐     ┌────────────────┐
│  規劃齒輪   │ ──→ │  執行齒輪    │ ──→ │  知識齒輪      │
│ Brainstorm  │     │ Work         │     │ Compound       │
│ Plan        │     │ Review       │     │ Bridge         │
│ (80% time)  │     │ (15% time)   │     │ (5% time)      │
└──────┬──────┘     └──────────────┘     └───────┬────────┘
       │                                         │
       └──── 知識回饋到下一個 Plan ←──────────────┘
```

**齒輪 1：規劃齒輪（80%）**
- Brainstorm 產出需求文件
- Plan 把需求轉化為可執行的實作單元
- Document review（6 個 reviewer agents 平行審查）在 plan 階段就捕獲問題
- **複利效果：** 每次 plan 的 document review 標準都基於前次的學習

**齒輪 2：執行齒輪（15%）**
- Work 在隔離的 worktree 中執行
- Review 用 12 個 subagent 從不同角度審查
- **複利效果：** Review 的檢查清單持續從 compound 階段獲得新規則

**齒輪 3：知識齒輪（5%）**
- Compound 萃取 problem → solution → insights
- Bridge 把結構化知識轉入永久 vault
- **複利效果：** 每個 solution 都讓 agent 的知識庫更豐富

### 2.3 迴路的閉合條件

一個完整的知識迴路需要閉合——learning 必須能被未來的 session 存取到。閉合有三種路徑：

| 閉合路徑 | 機制 | 持久性 | 可被搜尋 |
|---------|------|--------|---------|
| CLAUDE.md 規則 | 直接寫入 CLAUDE.md | 每次啟動載入 | 自動（always in context）|
| docs/solutions/ | CE compound 產出 | 磁碟上的 markdown | Agent 主動搜尋 |
| vault notes | Bridge 後的結構化筆記 | Git 管理 + obsidian-agent | search/thread/context |
| claude-mem | MCP 跨 session 記憶 | 獨立資料庫 | smart_search/timeline |
| Auto memory | Claude 自動記錄 | project memory 目錄 | 啟動時載入前 200 行 |

**最強閉合：** CLAUDE.md 規則（每次都載入，零查找成本）。
**最靈活閉合：** vault notes（結構化、可搜尋、可圖譜化）。
**最弱閉合：** docs/solutions/（只在 agent 主動搜尋時才有用）。

### 2.4 知識半衰期

不同類型的知識衰減速度不同：

| 知識類型 | 半衰期 | 最佳存放位置 |
|---------|--------|-------------|
| 行為規則（"不要做 X"） | 永久 | CLAUDE.md |
| 架構決策（"選 A 不選 B 因為..."） | 6-12 個月 | vault resource |
| Bug 修復模式（"問題 X 的根因是 Y"） | 3-6 個月 | docs/solutions/ |
| API 用法（"library X 的正確用法"） | 1-3 個月（版本更新） | context7 即時查詢 |
| 環境配置（"port 3000 被 X 佔用"） | 數週 | Auto memory / 不需記 |

---

## 3. Compound Engineering Plugin 深入分析

### 3.1 Plugin 概覽

| 屬性 | 值 |
|------|-----|
| 開發者 | Every Inc. |
| 開源地址 | `github.com/EveryInc/compound-engineering-plugin` |
| 相容性 | Claude Code, Codex, Factory Droid, Gemini CLI, Copilot, Windsurf, Kiro CLI 等 |
| 安裝後 agents | 5 → 52（+47） |
| Slash commands | +22（含核心 ce:* 工作流） |
| Expert skills | +20（架構、開發工具、內容工作流） |
| 附帶 MCP | context7（即時 library 文件查詢） |

### 3.2 六大核心指令深入

#### `/ce:brainstorm` — 需求探索

**目的：** 把模糊的想法精煉成結構化需求文件。

**運作方式：**
- 透過互動式 Q&A 釐清需求
- 自動判斷是否需要完整 ceremony（簡單任務自動 short-circuit）
- 產出 `docs/brainstorms/YYYY-MM-DD-*-requirements.md`

**複利點：**
- 需求文件格式持續標準化
- 歷史 brainstorm 可作為新需求的參考模式
- 問題探索的深度隨累積經驗提升

#### `/ce:plan` — 技術規劃

**目的：** 把需求文件轉化為 agent 可執行的實作計畫。

**運作方式：**
- 讀取需求文件或詳細描述
- 研究程式碼庫中的相關模式
- 產出結構化 plan：Overview → Problem Frame → Requirements Trace → Key Technical Decisions → Implementation Units
- 可觸發 Document Review（6 個平行 reviewer agents）

**複利點：**
- Plan 模板隨每次使用持續改善
- Key Technical Decisions 累積組織的 decision log
- "拒絕方案" 紀錄避免未來重複探索死路
- Document Review 的標準基於歷史 compound learnings

**本 vault 實測：** 7 個 plans（001-005 + context-engineering + knowledge-unification）的品質隨迭代明顯提升。Plan 004 開始加入 subtype 先例引用、scope boundary 更精準。

#### `/ce:work` — 系統化執行

**目的：** 按照計畫系統化實作，維持品質。

**運作方式：**
- 逐 unit 執行 plan 中的 Implementation Units
- 持續跑測試和品質檢查
- 在隔離的 worktree 中工作（可選）

**複利點：**
- 測試模式從 compound learnings 中學習
- 常見錯誤有自動防護（hooks）
- 執行效率隨程式庫的 self-teaching 程度提升

#### `/ce:review` — 多角度審查

**目的：** 用 12 個專業化 subagent 平行審查程式碼。

**運作方式：**
- 12 個 subagent 各從不同角度審查：安全、效能、架構、過度工程、邊界案例等
- Confidence-gated：低信心的發現不會進入報告
- Merge/dedup pipeline 合併重複發現
- 產出結構化 review 報告

**12 個審查角度（推測基於 plugin 結構）：**
1. Security reviewer（安全漏洞）
2. Performance reviewer（效能瓶頸）
3. Architecture reviewer（架構一致性）
4. Over-engineering reviewer（過度設計）
5. Edge case reviewer（邊界情況）
6. Test coverage reviewer（測試覆蓋）
7. Accessibility reviewer（無障礙性）
8. Error handling reviewer（錯誤處理）
9. API design reviewer（API 設計）
10. Documentation reviewer（文件品質）
11. Dependency reviewer（依賴健康度）
12. Coherence reviewer（整體一致性）

**複利點：**
- 每次 review 發現的 pattern 回饋到下次 review 的檢查清單
- 你的回饋成為系統的預設——說一次，系統永遠記得

#### `/ce:compound` — 知識萃取

**目的：** 把剛解決的問題記錄成可搜尋的結構化學習。

**運作方式：**
- 產生 6 個平行 subagents：context analyzer、solution extractor、related docs finder、prevention strategist、category classifier、documentation writer
- 產出 `docs/solutions/<category>/<timestamp>.md`（YAML frontmatter + markdown）
- 格式：Problem → Solution → Key Insights → What Would I Do Differently → Related

**複利點：**
- 未來 session 的 agent 可以搜尋到這些 learnings
- 防止同類問題重複發生
- 建立組織級的「問題 → 解法」知識庫

**本 vault 實證：** `docs/solutions/harness-automation/session-stop-wrapper-2026-03-29.md` 是第一個 compound learning，記錄了 session-stop wrapper 的完整 problem → solution → key insights 迴路。

#### `/ce:ideate` — 主動改進

**目的：** 基於程式碼庫主動建議改進方向。

**運作方式：**
- 分析當前程式碼庫
- 批判性評估可行的改進點
- 產出有根據的建議（不是空想）

**複利點：**
- 建議品質隨程式庫知識累積提升
- 與 `/improve` 互補——ideate 看程式碼，improve 看工作流

### 3.3 Agent 生態系統

Plugin 安裝後帶來的 52 個 agents 分為五大類：

| 類別 | 角色 | 複利機制 |
|------|------|---------|
| Review specialists | 12+ 審查角度 | 審查標準持續累積 |
| Codebase researchers | 程式碼探索與分析 | 對程式庫理解越來越深 |
| Document researchers | 文件探索與驗證 | Plan 品質持續提升 |
| UI/Figma agents | 設計同步與實作 | 設計語言一致性提升 |
| Automation agents | 工作流自動化 | 自動化覆蓋率成長 |

### 3.4 CE Plugin vs 原生 Claude Code

| 面向 | 原生 Claude Code | + CE Plugin |
|------|-----------------|-------------|
| 規劃 | 手動描述任務 | 結構化 brainstorm → plan |
| 執行 | 單 agent | 多 agent 協作 |
| 審查 | 人工或單 agent review | 12 subagent parallel review |
| 知識保留 | Auto memory（被動） | compound + bridge（主動） |
| 學習迴路 | 無系統化機制 | 完整 6 階段迴路 |
| 技能庫 | 內建 skills | +20 expert skills |

---

## 4. 本 Vault 的 Compound Loop 實測數據

### 4.1 迴路時間軸

本 vault 從 2026-03-29 建立以來，已完成多個完整迴路：

```
Day 1 (2026-03-29):
  CE Plugin 安裝 → 認識六大指令
  Plan 001: /improve 自我迭代機制 (4 units, 全部完成)
  Plan 002: obsidian-agent 效率改進 (4 units, 全部完成)
  /ce:compound → session-stop-wrapper learning
  /bridge-compound → vault 入庫
  → 知識複利迴路首次閉合 ✓

Day 1-2 (2026-03-29~30):
  Plan 003: LLM 技術自動調研管線 (11 units, 4 phases)
  Plan 004: Vault 知識框架重構 (7 units, 全部完成)
  Plan 005: 本地 LLM 基礎設施 (3 units, 3 phases, 拆分自 003)
  Context Engineering Strategy Plan
  Knowledge System Unification Plan (7 plans total)
```

### 4.2 迴路品質演進

| 指標 | Plan 001 | Plan 004 | Plan 007 |
|------|---------|---------|---------|
| Problem Frame 精準度 | 中等 | 高（引用先例） | 高（引用跨系統數據）|
| Scope Boundaries | 3 項 | 6 項（含明確排除）| 5 項（精準校準）|
| Key Technical Decisions | 2 項 | 6 項（含拒絕方案）| 5 項（含 trade-off）|
| Document Review | 無 | 有（6 agents） | 有（coherence + feasibility）|
| 跨 plan 引用 | 無 | 引用 Plan 001 模式 | 引用 Plan 001-005 |
| 學習回饋 | 首次 | 明確引用 compound learning | 系統性引用 solutions/ |

**關鍵發現：** Plan 的品質在 7 次迭代中**可觀測地提升**——不是因為人變聰明了，而是因為系統記住了更多模式。

### 4.3 知識閉合率

| 迴路 | 產出 | 閉合到 vault？ | 閉合到 CLAUDE.md？ |
|------|------|---------------|-------------------|
| session-stop wrapper | docs/solutions/ learning | ✓ bridge-compound | ✗ |
| /improve 機制 | improvement notes template | ✓ CONVENTIONS.md | ✓ CLAUDE.md |
| vault 框架重構 | subtype + maturity schema | ✓ CONVENTIONS.md | ✗ |
| context 策略 | CLAUDE.md 瘦身 | ✓ vault research | ✓ CLAUDE.md |

**觀察：** 能閉合到 CLAUDE.md 的學習效果最強（每次 session 自動受益），但只有行為規則適合放那裡。

### 4.4 首次閉合的關鍵洞察

2026-03-29 的首次完整閉合記錄：

```
/ce:compound → docs/solutions/harness-automation/session-stop-wrapper-2026-03-29.md
/bridge-compound → resources/session-stop-wrapper-learning.md（vault 入庫）
```

**學到什麼：**
1. Wrapper > CLI patch 的驗證策略——在 bash wrapper 中驗證後再 upstream
2. `obsidian-agent patch --append` 是可靠的 journal 寫入方式
3. Windows Git Bash stdin piping 穩定（之前存疑的問題解決了）
4. Slash commands 作為輕量 bridge 的理想性——`.claude/commands/*.md` 是指令模板不是可執行腳本
5. Hook 陣列執行順序有保證——journal-then-sync 可靠

這些洞察在 Plan 002-005 中被多次引用，證明 compound → bridge → vault 的迴路確實運作。

---

## 5. Bridge 機制：CE 產出到 Vault 的轉換層

### 5.1 為什麼需要 Bridge

CE Plugin 的產出格式（`docs/plans/`, `docs/solutions/`, `docs/brainstorms/`）和 vault 的 PARA 格式不同：

| 面向 | CE 產出 | Vault 筆記 |
|------|--------|-----------|
| Frontmatter | CE-specific（date, category, problem_type） | PARA（type, subtype, maturity, domain, related） |
| 目錄 | `docs/plans/`, `docs/solutions/` | `resources/`, `projects/` |
| 連結 | 無 cross-reference | `[[wikilinks]]` + `related` 欄位 |
| 索引 | 無 | `_index.md`, `_tags.md`, `_graph.md` |
| 搜尋 | 檔案系統搜尋 | obsidian-agent search/thread/context |

**Bridge 解決的問題：** 把 CE 產出轉換為 vault 格式，讓知識進入可搜尋、可圖譜化的永久儲存。

### 5.2 兩個 Bridge 命令

#### `/bridge-compound`

```
讀取 docs/solutions/ 中的 compound learning
 ↓
萃取 problem, solution, key insights, technologies
 ↓
轉換為 vault resource (subtype: learning)
 ↓
用 obsidian-agent note/patch 建立筆記
 ↓
obsidian-agent sync 更新索引
```

#### `/bridge-plan`

```
讀取 docs/plans/ 中的實作計畫
 ↓
萃取 overview, scope, units, dependencies
 ↓
轉換為 vault project 筆記
 ↓
建立與 source plan 的 `documents` relation
 ↓
obsidian-agent sync 更新索引
```

### 5.3 Bridge 的 Schema 轉換

| CE 欄位 | → | Vault 欄位 |
|---------|---|-----------|
| `date` | → | `created` |
| `category` | → | `tags` |
| `problem_type` | → | 保留在 body |
| `severity` | → | 保留在 body |
| `technologies` | → | `tags`（合併） |
| — | → | `type: resource` |
| — | → | `subtype: learning` |
| — | → | `maturity: seed` → `growing` |
| — | → | `domain: ai-engineering` |
| — | → | `related: [[source-plan]]` |

---

## 6. 與其他三學科的深層關係

### 6.1 四學科生態系統

```
                    ┌──────────────────┐
                    │ Compound Eng.    │
                    │ (知識複利迴路)    │
                    └──────┬───────────┘
                           │ 學習回饋
            ┌──────────────┼──────────────┐
            ↓              ↓              ↓
   ┌────────────┐  ┌────────────┐  ┌──────────────┐
   │ Prompt Eng.│  │Context Eng.│  │ Harness Eng. │
   │ (指令品質) │  │(上下文管理) │  │(工具基礎設施) │
   └────────────┘  └────────────┘  └──────────────┘
```

### 6.2 Compound × Prompt Engineering

| 交叉點 | 說明 |
|--------|------|
| Brainstorm 本質 | Brainstorm 和 Plan 是 prompt 設計的過程——你在寫給 agent 的指令 |
| CLAUDE.md 迭代 | Compound learning → CLAUDE.md 規則 = system prompt 持續最佳化 |
| Prompt caching | Compound 產出的穩定文件天然適合 cache（每次啟動載入） |
| Few-shot 累積 | 每個 docs/solutions/ 都是未來 prompt 的 few-shot 範例 |
| Skill 封裝 | Compound 發現的可復用模式可封裝為 `.claude/skills/` |

### 6.3 Compound × Context Engineering

| 交叉點 | 說明 |
|--------|------|
| 知識文件化 | Compound 產出讓未來 session 的 context 更精準 |
| Context 衛生 | compound + bridge 避免在主 context 中堆積未結構化資訊 |
| Subagent 使用 | CE 的 6 agent compound 本身就是 subagent 隔離模式的實踐 |
| Memory 補充 | vault notes 補充 auto memory 的不足（結構化 + 可搜尋） |
| Compaction 安全 | 重要知識在 vault 中有永久副本，compaction 丟失不致命 |

### 6.4 Compound × Harness Engineering

| 交叉點 | 說明 |
|--------|------|
| Plugin 架構 | CE Plugin 是 harness engineering 的產物——agent + skill + hook 的組合 |
| Hook 自動化 | Compound learning 可轉化為新的 hook（如 lint、format、test）|
| 配置迭代 | `/improve` 基於 compound 理念讓 settings.json 持續演化 |
| Bridge 命令 | Slash commands 是 harness 能力——bridge 利用 harness 連接 CE 與 vault |
| Worktree 隔離 | `/ce:work` 可用 git worktree 隔離（harness 層能力）|

---

## 7. 反模式與陷阱

### 7.1 Compound 層反模式

| 反模式 | 症狀 | 修正 |
|--------|------|------|
| **跳過 compound** | 同類 bug 反覆出現、agent 重複犯錯 | 每個有意義的 feature 都跑 `/ce:compound` |
| **Compound 但不 bridge** | docs/solutions/ 堆積但無人查閱 | bridge 到 vault 確保可搜尋 |
| **過度 compound** | 瑣碎改動也記錄，噪音淹沒信號 | 只記錄「下次會用到」的學習 |
| **儀式化 compound** | 照表填寫但沒有真正反思 | 聚焦 "What Would I Do Differently" |
| **孤島 compound** | learning 存在但不影響後續行為 | 確保閉合：docs → vault → CLAUDE.md |
| **延遲 compound** | 隔天再記，遺忘關鍵細節 | 完成功能後立即 compound |

### 7.2 Plan 層反模式

| 反模式 | 症狀 | 修正 |
|--------|------|------|
| **跳過 plan 直接 work** | 品質不穩定、scope creep | 任何 > 30 分鐘的任務都先 plan |
| **Plan 過細** | agent 失去靈活性 | 給目標和約束，不給逐行步驟 |
| **不跑 document review** | Plan 中的假設直到執行才暴露 | 至少跑 coherence + feasibility review |
| **Plan 快照過時** | 另一個 session 已改變前提 | Plan 開頭加入 "Context & Research" 確認現狀 |

**本 vault 實證：** Plan 001 的前提假設（memory 目錄為空、68 行 CLAUDE.md）在執行時已過時——另一個 session 已建立了 5 個 memory 檔案。Document review 在規劃階段就能抓到這類「快照過時」問題。

### 7.3 Review 層反模式

| 反模式 | 症狀 | 修正 |
|--------|------|------|
| **只看 agent review 不看自己** | 盲目信任 agent 結論 | 至少讀 critical/high 級發現 |
| **Review 結果不回饋** | review 報告看完即丟 | review 發現要轉入 compound |
| **單一審查角度** | 安全或效能盲點 | 使用 12-subagent parallel review |

### 7.4 知識迴路反模式

| 反模式 | 症狀 | 修正 |
|--------|------|------|
| **開迴路（不閉合）** | 知識產出但不影響後續行為 | 每個 learning 必須有閉合路徑 |
| **過深閉合** | 行為規則埋在 vault 深處 | 高頻行為規則提升到 CLAUDE.md |
| **知識孤島** | 三個系統各自為政 | `/bridge-*` + 統一搜尋策略 |
| **compound without review** | 學到錯誤的教訓 | 先 review 確認品質，再 compound |

---

## 8. 量化 Compound 效果的度量框架

### 8.1 核心度量

| 度量 | 定義 | 如何測量 | 目標 |
|------|------|---------|------|
| **迴路閉合率** | compound learnings 實際被後續 session 引用的比率 | grep docs/solutions/ 引用出現在 plans 中的次數 | > 50% |
| **重複錯誤率** | 已 compound 的問題再次出現的比率 | journal 中搜尋已知問題關鍵字 | < 10% |
| **Plan 品質演進** | Plan 的結構完整性隨迭代的變化 | 比較 Plan N 和 Plan N+3 的欄位完整性 | 持續上升 |
| **知識庫成長** | docs/solutions/ 和 vault resources 的有效筆記數 | `obsidian-agent stats` | 穩定成長 |
| **Bridge 延遲** | compound → bridge 到 vault 的時間差 | compound 日期 vs vault 筆記 created 日期 | < 1 天 |

### 8.2 Leading Indicators（先行指標）

| 指標 | 意義 | 警戒線 |
|------|------|--------|
| compound 頻率 | 多久做一次 compound | < 1 次/週 = 迴路停滯 |
| /improve 建議數 | 工作流摩擦點數量 | 持續增加 = 配置未跟上使用需求 |
| 孤兒筆記數 | 未連結的知識 | 增加 = bridge 或 linking 不足 |
| docs/solutions/ 堆積 | 未 bridge 的 learnings | > 5 筆 = bridge 流程斷裂 |

### 8.3 本 Vault 的基線數據（2026-03-30）

| 度量 | 目前值 |
|------|-------|
| 總 plans | 7 |
| 總 compound learnings | 1（session-stop-wrapper）|
| 總 bridge 完成 | 1 |
| 迴路閉合率 | 100%（1/1 已 bridge）|
| Plan 品質趨勢 | 上升（Plan 004+ 明顯更結構化）|
| 知識庫 active resources | ~25 筆 |
| compound 頻率 | ~1 次/天（Day 1 數據）|

**基線觀察：** 目前樣本量太小無法得出統計結論，但定性觀察到的 Plan 品質提升是真實的。持續追蹤 4-8 週後可以建立更可靠的趨勢。

---

## 9. 進階模式

### 9.1 Ralph Wiggum Loop（2025 Geoffrey Huntley）

AI coding 的反覆迭代模式——在同一任務上重複跑 agent 直到滿足明確完成條件，而不是在 agent 自認為完成時停止。

**與 Compound Engineering 的關係：**
- Ralph Wiggum loop 是 `Work` 階段的微觀迭代
- CE 的 `Compound` 階段是跨 session 的宏觀迭代
- 兩者結合 = 微觀和宏觀都在學習

### 9.2 Lifelong Agent 模式

學術研究中的「終身 agent」概念：agents 不是靜態產物而是動態過程——持續累積知識、精煉技能、跨時間演化能力。

**CE 的實踐版本：**
- Auto memory = agent 的短期記憶
- docs/solutions/ = agent 的長期記憶
- CLAUDE.md = agent 的本能反應
- vault = agent 的外部知識圖譜

### 9.3 Self-Evolving Feedback Loop

OpenAI Cookbook 提出的自演化 agent 模式：設計一個回饋迴路讓 agentic 系統從經驗中迭代學習，逐漸把人工干預從細節修正轉向高層監督。

**CE 的實作對應：**
1. Issue 捕獲 → `/ce:review` 發現問題
2. 學習回饋 → `/ce:compound` 記錄
3. 系統更新 → bridge + CLAUDE.md 更新
4. 效果驗證 → 下次 plan/work 的品質

### 9.4 Knowledge System Unification

本 vault 正在進行的知識系統統一（Plan 007）：

```
Auto Memory  ──→  指標型 MEMORY.md（只存 pointer）
claude-mem   ──→  讀取為主的搜尋補充
Obsidian     ──→  Canonical store（唯一真相來源）
CLAUDE.md    ──→  行為規則（每次啟動載入）
```

**與 compound 的關係：** 統一後 compound 產出有明確的路由——行為規則去 CLAUDE.md，持久知識去 vault，搜尋索引去 claude-mem。不再有「放哪裡？」的疑問。

---

## 10. 未來發展方向

### 10.1 即將被 Harness 吸收的能力

Will Larson 預測 CE 的許多實踐會被 Claude Code/Cursor 等 harness 原生吸收：

| CE 能力 | 被吸收可能性 | 理由 |
|---------|-------------|------|
| Plan mode | 高 | Claude Code 已有 plan mode |
| Multi-agent review | 中 | Agent Teams 已支援 |
| Compound/learning capture | 低 | 高度依賴組織特定 schema |
| Bridge to external vault | 很低 | 太多自訂可能性 |

**洞察：** CE Plugin 的長期價值在於**組織特定的知識累積機制**——這是 harness 無法通用化的部分。

### 10.2 Compound Knowledge Plugin

Every Inc. 還開發了 `compound-knowledge-plugin`，把 CE 的理念擴展到**知識工作**（非程式碼）：brainstorm, plan, review, execute, save learnings。這暗示 compound engineering 的核心模式（迴路 + 知識萃取 + 回饋）是通用的，不限於軟體工程。

### 10.3 本 Vault 的下一步

1. 追蹤更多 compound learnings 以建立統計基線
2. 自動化 bridge 流程（目前手動觸發 `/bridge-compound`）
3. 建立 compound → CLAUDE.md promotion 的標準流程
4. 量化 compound 前後 Plan 品質差異（需要更多數據點）
5. 探索 claude-mem timeline 作為 compound history 的視覺化

---

## 迭代紀錄

### Sprint 1 — 2026-03-29

**做了什麼：** 安裝 CE Plugin，認識六大指令與 52 agents
**關鍵發現：**
- Plugin 從 5 agents 爆增到 52
- 附帶 context7 MCP server
- 80/20 法則是核心哲學

### Sprint 5 — 2026-03-30

**做了什麼：** 全面深入 Compound Engineering 研究——從 65 行 stub 擴充為完整研究筆記
**來源：** Every Inc 官方文章與指南、Will Larson 評論分析、agentic-patterns.com 模式文件、VelvetShark 工作流分析、Martin Fowler LLM learning loop、OpenAI self-evolving agents cookbook、本 vault 7 個 plans 與 1 個 compound learning 的實測數據
**關鍵發現：**
- CE 翻轉了傳統軟體工程的遞減報酬——每個功能讓下一個更容易而非更難
- 80/20 法則（規劃+審查 vs 執行）是核心，但需要 compound 步驟才能真正複利
- 12-subagent parallel review 是品質保證的關鍵機制
- 知識有半衰期——行為規則（永久）vs API 用法（1-3 個月）需要不同存放策略
- 本 vault 的 Plan 品質在 7 次迭代中可觀測提升（Plan 004+ 引用先例、scope 更精準）
- Bridge 是 CE → Vault 的關鍵轉換層，沒有 bridge 的 compound learning 容易成為孤島
- Will Larson 預測 CE 實踐會被 harness 吸收，Plugin 的長期價值在組織特定知識累積
**哪裡卡住：** 量化「複利效果」仍需更多數據點（目前只有 1 個 compound learning 樣本）
**下次要試：**
- 追蹤 compound learnings 在後續 plans 中被引用的頻率
- 測試 compound → CLAUDE.md promotion 的標準流程
- 自動化 bridge 觸發（目前手動）
- 建立 4-8 週的度量基線
**知識複利：** 這份研究本身就是 compound engineering 的實踐——它記錄了 vault 的知識迴路運作方式，讓未來的 session 能直接參考而非重新探索

## 開放問題（已更新）

- [x] ~~`/ce:compound` 產出的文件放哪裡最有效？~~ → `docs/solutions/<category>/` + bridge 到 vault
- [x] ~~反思框架的最佳迭代頻率？~~ → 每個有意義的 feature 都 compound，不要累積
- [ ] 如何量化「複利效果」？→ 已建立度量框架（Section 8），需要 4-8 週數據
- [ ] compound learning 被後續 session 引用的實際頻率？（需追蹤）
- [ ] bridge 自動化——能否在 `/ce:compound` 後自動觸發 bridge？
- [ ] compound → CLAUDE.md promotion 的判斷標準是什麼？（行為規則 vs 知識參考）
- [ ] 12 subagent review 各自的精準度和召回率？（需要 review quality 數據）
- [ ] CE Plugin 的 agent/skill overhead 佔用多少 context tokens？
- [ ] Compound Knowledge Plugin（非程式碼版）是否適用於本 vault 的知識管理？

## Related

- [[tech-research-squad]]
- [[prompt-engineering-research]]
- [[context-engineering-research]]
- [[harness-engineering-research]]
- [[compound-engineering-plugin]]
