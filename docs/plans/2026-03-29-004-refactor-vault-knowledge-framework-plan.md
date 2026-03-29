---
title: "refactor: Vault 知識框架結構性升級 — subtype 擴展 + schema 強化 + 圖譜語義化"
type: refactor
status: completed
date: 2026-03-29
deepened: 2026-03-29
---

# refactor: Vault 知識框架結構性升級

## Overview

重新設計 vault 的分類法、frontmatter schema、cross-linking 策略，解決 resources/ catch-all（77% 筆記）、tag 碎片化（72% singletons）、圖譜語義單一（全部 `related`）三大結構問題。採用 subtype 擴展模式，不改目錄結構、不改 obsidian-agent CLI。

## Problem Frame

Vault 目前有 ~30 篇筆記，PARA 結構已出現三個系統性問題：

1. **分類邊界模糊** — `resources/` 佔 77%（23/30），混合了環境清單、研究累積、專案衛星、工具參考、流程文件、改善提案、compound 學習等至少 7 種角色。PARA 的 R 變成了 catch-all bucket。
2. **Cross-linking 稀疏** — 28% 圖譜密度，2 篇孤兒筆記，16 條被 cluster 分析建議但缺失的連結。body 中的 `[[wikilinks]]` 不進入 `_graph.md`。所有 25 篇連通筆記塌縮成一個巨型 cluster，沒有有意義的知識鄰域。
3. **Frontmatter 維度不足** — 只有 2 維分類（type + tags）。20 行 stub 和 370 行深度研究在 metadata 上無法區分。沒有 domain、maturity 維度。CE 輸出和 vault 使用完全不同的 schema，跨搜尋不可能。

## Requirements Trace

- R1. 定義 resource subtypes，將 resources/ 從 1-bucket 分解為語義明確的子分類
- R2. 擴展 frontmatter schema，增加 `subtype`、`maturity`、`domain` 三個維度
- R3. 定義 typed relations（`extends`、`depends-on`、`implements`、`documents`、`supersedes`），取代全部 `related` 的單一語義
- R4. 整合 tag 體系，消除 singleton 碎片，建立一致的命名規範
- R5. 更新 templates 反映新 schema，引導正確分類
- R6. 遷移所有現有筆記到新 schema，保持向後相容
- R7. 驗證遷移後圖譜密度、分類分布、索引健康度

## Scope Boundaries

- 不修改 obsidian-agent CLI 核心（純 vault metadata + conventions 層面）
- 不建立子目錄（保持 type→directory 1:1 對應）
- 不引入向量搜尋或語義搜尋（那是 Plan 003 範疇）
- 不修改 compound-engineering plugin
- 不修改 docs/ 下 CE 產出的 schema（bridge commands 負責轉換）
- CE schema 統一是未來工作，本計畫只在 vault 端建立接收能力

## Context & Research

### Relevant Code and Patterns

- **subtype 先例**: `CONVENTIONS.md` 的 `subtype: improvement` 模式 — 證明 subtype 可行，不破壞 type-directory invariant
- **_graph.md 結構**: `| Source | Links To | Relation |` 表格已有 Relation 欄位，目前全部填 `related`
- **templates/resource.md**: 最弱的 template，只有 3 個泛用 heading（Key Points / Notes / Related），無分類引導
- **templates/improvement.md**: 最強的 template，有 6 個 subtype-specific frontmatter 欄位 — 可作為 subtype template 的範本
- **obsidian-agent sync**: 從 frontmatter `related` 欄位重建 `_graph.md`。新增 frontmatter 欄位會被 sync 忽略（不影響也不利用），typed relation 需要特定格式讓 sync 能讀取或只作為 convention
- **body wikilinks**: 大量 `[[link]]` 存在於筆記正文中但不進入 `_graph.md`（只讀 frontmatter `related`）

### Institutional Learnings

- subtype 模式已被驗證可行且低風險（Plan 001 Unit 3）
- `docs/solutions/` 只有 1 篇，知識複利循環尚未啟動 — vault 的可搜尋性直接影響 CE 的 ROI
- Windows Git Bash 環境穩定性需注意（但本計畫不涉及 script 執行）
- vault 建立僅 2 天（2026-03-28），現在是重構的最佳時機（遷移成本最低）

## Key Technical Decisions

- **Subtype 擴展 over 子目錄**: 保持 type→directory 1:1 invariant，不需要改 CLI 路由。subtype 作為 CONVENTIONS.md 的新必填欄位（僅 resource type）。理由：已有 improvement 先例證明可行，且 vault 只有 25 篇筆記，子目錄的物理隔離收益不大。
- **Typed relations 用獨立 `relation_map` 欄位**: 經源碼驗證，`vault.mjs:parseFrontmatter()` 的 regex `/^\[\[(.*)\]\]$/` 要求字串以 `]]` 結尾，`"[[note]]:extends"` 格式會導致匹配失敗，污染 `related` 陣列並破壞 backlinks/orphans/cluster/health 等 6+ 個 CLI 功能。因此 `related` 欄位**保持原有 `"[[note]]"` 格式不變**，另設 `relation_map` string 欄位存 typed relations（例如 `relation_map: "csm-architecture:documents, csm-feature-roadmap:implements"`）。CLI 不認識的 key 會被安全忽略，agents 可解析此欄位獲取語義。
- **Maturity 取代 status 的分類角色**: 現有 `status: active | archived | draft` 混合了生命週期和品質兩個維度。新增 `maturity: seed | growing | mature` 專門表達內容品質，`status` 回歸純生命週期用途。
- **Domain 用受控詞彙**: `domain` 欄位使用預定義的受控詞彙而非自由文本，避免重蹈 tags 碎片化的覆轍。初始詞彙從現有筆記的實際聚類推導。
- **Tag 整合用合併而非刪除**: singleton tags 中有價值的合併到 parent tag（如 `jq` → `cli-tools`），無價值的在遷移時移除。不設計階層 tag 系統（Obsidian 原生不支援 nested tags 的搜尋優化）。
- **CE 和 vault schema 保持分離，bridge commands 作 adapter**: 分離是正確的架構決策，原因：(1) CE 的 `type: feat|fix|refactor` 與 vault 的 `type: area|project|resource` 是正交語義維度，強行統一會產生 impedance mismatch；(2) 生命週期不同（CE `completed` ≠ vault `mature`）；(3) `obsidian-agent scanNotes()` 只掃描 PARA 目錄，`docs/` 天然不可見；(4) Bridge commands 讓兩邊各自演進不互相阻塞。但 bridge commands 需要更新以產出符合新 schema 的筆記。

## Open Questions

### Resolved During Planning

- **subtype 要幾種？** → 6 種，從現有筆記的實際角色推導：`reference`（靜態參考）、`research`（累積式研究）、`catalog`（清單/盤點）、`config`（配置記錄）、`learning`（經驗學習）、`standard`（流程/規範）。improvement 保留為第 7 種。
- **domain 初始詞彙？** → 從現有筆記聚類推導 5 個：`ai-engineering`、`dev-environment`、`open-source`、`knowledge-management`、`project-specific`。
- **relation types 要幾種？** → 5 種核心 + 2 種 journal 專用：`extends`、`depends-on`、`implements`、`documents`、`supersedes` + `nav-prev`、`nav-next`（已存在）。
- **是否需要 `confidence` 欄位？** → 不需要。`maturity` 已涵蓋內容品質維度，再加 `confidence` 會讓 frontmatter 過重。
- **`related` 格式向後相容？** → **否**。源碼驗證（`vault.mjs:69`）確認 regex `/^\[\[(.*)\]\]$/` 不容忍後綴。`"[[note]]:extends"` 會導致 parse 失敗，污染 related 陣列。**決策：不修改 `related` 格式，改用獨立的 `relation_map` string 欄位。**

- **`relation_map` 格式？** → 鎖定為帶引號的逗號分隔字串：`relation_map: "note-a:documents, note-b:extends"`。源碼確認 `parseFrontmatter()` 對帶引號字串會正確去引號後存為 plain string；YAML inline map 格式 `{key: val}` 的大括號會被 parser 誤判。此格式在 Unit 1 schema 定義中明確規範。

### Deferred to Implementation

- 某些筆記可能需要同時屬於多個 domain — 是否允許 domain 為陣列（建議從 string 開始，未來需要時再改為 array）
- 遷移順序是否需要考慮 `related` 更新的連鎖效應

## High-Level Technical Design

> *This illustrates the intended approach and is directional guidance for review, not implementation specification.*

```
Phase 1: Schema Design (Unit 1)
  CONVENTIONS.md ──→ 新增 subtype / maturity / domain 定義
                ──→ 新增 relation_map convention（related 不動）
                ──→ 新增 tag 整合規範

Phase 2: Templates (Unit 2)
  templates/resource.md ──→ 加入 subtype + 差異化 heading 引導
  templates/*.md        ──→ 加入 maturity / domain / relation_map 欄位

Phase 3a: Tag 整合 (Unit 3)
  _tags.md analysis ──→ 合併 map ──→ 批次更新 tags ──→ git commit checkpoint

Phase 3b: Migration (Unit 4)
  resources/*.md ──→ 逐篇: assign subtype + maturity + domain + relation_map
  areas/*.md     ──→ add maturity + domain
  projects/*.md  ──→ add maturity + domain
  （related 欄位格式完全不變）

Phase 4: Bridge Update (Unit 5)
  bridge-compound.md ──→ 更新 metadata mapping（subtype: learning, maturity, domain）
  bridge-plan.md     ──→ 更新 metadata mapping（maturity, domain）

Phase 5: Index Rebuild + Validation (Unit 6)
  obsidian-agent sync   ──→ rebuild _index / _tags / _graph
  obsidian-agent health ──→ verify Grade A
  obsidian-agent cluster ──→ verify cluster separation
```

## Implementation Units

- [x] **Unit 1: Schema 定義 — 更新 CONVENTIONS.md**

**Goal:** 定義完整的新 frontmatter schema，包括 subtype 列舉、maturity 維度、domain 受控詞彙、typed relations 格式

**Requirements:** R1, R2, R3

**Dependencies:** None

**Files:**
- Modify: `CONVENTIONS.md`

**Approach:**
- 在 Required Frontmatter 區段新增 `maturity` 和 `domain` 欄位
- 新增 Subtypes 區段，定義 resource 的 7 種 subtype（reference / research / catalog / config / learning / standard / improvement）及各自的使用時機說明
- 定義 typed relations convention：`related` 保持原格式，新增 `relation_map` string 欄位存語義（格式：`"note-a:documents, note-b:extends"`），列出 5+2 種 relation type 及使用時機
- 定義 domain 受控詞彙（ai-engineering / dev-environment / open-source / knowledge-management / project-specific）及擴展規則
- 定義 maturity 語義（seed: 初始想法或 stub / growing: 有實質內容但仍在發展 / mature: 完整且穩定）
- 保留現有規則不變：file naming、content rules、agent rules、template usage

**Patterns to follow:**
- 現有 `subtype: improvement` 定義格式（CONVENTIONS.md lines 36-48）
- 欄位定義附帶使用時機說明的模式

**Test scenarios:**
- Happy path: 新 schema 定義完整，所有 7 種 subtype 有明確的使用場景描述
- Edge case: improvement subtype 的現有定義被保留且不衝突
- Edge case: `related` 保持原格式，`relation_map` 新欄位的文檔清楚說明用途和 CLI 行為（被安全忽略）
- Integration: 新 schema 與 templates/ 的預期更新一致

**Verification:**
- CONVENTIONS.md 包含 subtype / maturity / domain / typed relations 的完整定義
- 現有 improvement subtype 定義不受影響
- 一個不熟悉 vault 的 agent 能僅靠 CONVENTIONS.md 正確分類新筆記

---

- [x] **Unit 2: Template 升級**

**Goal:** 更新 resource template 加入 subtype 引導，所有 templates 加入新 schema 欄位

**Requirements:** R5

**Dependencies:** Unit 1

**Files:**
- Modify: `templates/resource.md`
- Modify: `templates/area.md`
- Modify: `templates/project.md`
- Modify: `templates/idea.md`
- Modify: `templates/improvement.md`
- Modify: `templates/journal.md`

**Approach:**
- `resource.md`: 在 frontmatter 加入 `subtype: ""`、`maturity: seed`、`domain: ""`（使用空字串預設值而非 `{{PLACEHOLDER}}`，因為 CLI 的 template engine 只替換 TITLE/DATE/TYPE/GOAL/CONTENT，不認識新 key 的 placeholder 會殘留為 literal string，違反 CONVENTIONS.md 規則）。body 區段根據 subtype 提供差異化 heading 引導（但保持為一個 template，不拆分成 7 個檔案 — 用 AGENT comment 列出各 subtype 的推薦 heading 和有效值）
- 其他 templates: 在 frontmatter 加入 `maturity: seed`、`domain: ""`（同樣使用預設值，不用 placeholder）
- `improvement.md`: 確認現有 subtype-specific 欄位保留，加入 maturity 和 domain
- 所有 templates 加入 `relation_map: ""` 欄位（optional），並在註解中說明格式

**Patterns to follow:**
- `templates/improvement.md` 的 subtype-specific frontmatter 模式
- 現有 `{{PLACEHOLDER}}` 語法

**Test scenarios:**
- Happy path: 用更新後的 resource template 手動建立一篇 `subtype: research` 筆記，frontmatter 完整且 heading 適當
- Edge case: `templates/improvement.md` 現有欄位全部保留
- Edge case: template 中的 `{{DOMAIN}}` 附有受控詞彙列表作為註解

**Verification:**
- 每個 template 都包含 `maturity` 和 `domain` 欄位
- `resource.md` 包含 `subtype` 欄位和使用引導
- `obsidian-agent note "test" resource` 產出的筆記有新欄位（frontmatter 由 CLI 填，新欄位可能需要手動補 — 這是預期行為，因為不改 CLI）

---

- [x] **Unit 3: Tag 整合策略 + 執行**

**Goal:** 整理 68 個 tags（72% singletons），合併碎片，建立一致的命名規範

**Requirements:** R4

**Dependencies:** Unit 1（需要 domain 定義作為 tag 合併的參考維度）

**Files:**
- Modify: `_tags.md`（由 sync 重建，但需要先規劃合併 map）
- Modify: 所有帶有需合併 tags 的筆記

**Approach:**
- 先讀取 `_tags.md` 完整內容，列出所有 tags 及其出現次數
- 建立 tag 合併 map：將 50+ singleton tags 分為三類 — (a) 合併到 parent tag、(b) 保留（確實是獨特概念）、(c) 移除（無價值噪音）
- 定義 tag 命名規範：kebab-case、英文優先、具體 > 抽象（`session-stop-hook` > `hook`）
- 批次更新筆記的 tags 欄位
- 執行 `obsidian-agent sync` 重建 `_tags.md`

**Patterns to follow:**
- 現有 tag 使用模式中的高頻 tags（`claude-code`, `research`, `github`）作為整合錨點

**Test scenarios:**
- Happy path: 整合後 singleton 比例從 72% 降到 40% 以下
- Edge case: 中文 tags（如 `開源`, `文字測量`）統一改為英文 kebab-case
- Edge case: `subtype` 和 `domain` 引入後，部分 tag 可能變得多餘（如 `research` tag vs `subtype: research`）
- Integration: sync 後 `_tags.md` 正確反映合併結果

**Verification:**
- `_tags.md` 中 singleton tags 數量明顯下降
- 沒有重複語義的 tags 並存（如同時有 `ai-coding` 和 `ai-assisted-development`）
- 命名一致（全部 kebab-case 英文）

---

- [x] **Unit 4: 筆記遷移 — frontmatter 批次更新**

**Goal:** 將所有現有筆記遷移到新 schema：補上 subtype、maturity、domain、typed relations

**Requirements:** R6

**Dependencies:** Units 1-3

**Files:**
- Modify: `resources/*.md`（23 篇）
- Modify: `areas/*.md`（2 篇）
- Modify: `projects/*.md`（3 篇）
- Modify: `journal/*.md`（2 篇 — 只加 domain，journal 不需 maturity/subtype）

**Approach:**
- 根據 Unit 1 定義的分類規則，為每篇 resource 指定 subtype：
  - `catalog`: dexg16-machine-specs, dexg16-dev-environment, dexg16-ai-stack, dexg16-ai-coding-tools, dexg16-project-layout, dexg16-all-projects-catalog, dexg16-git-and-github, github-全部-repo-清單
  - `research`: context-engineering-research, prompt-engineering-research, harness-engineering-research, compound-engineering-research, research-mcp-model-context-protocol-2026-03-29
  - `config`: claude-code-configuration
  - `reference`: compound-engineering-plugin, pretext-無-dom-文字測量引擎
  - `standard`: github-發布流程, 開源專案品質標準
  - `learning`: session-stop-wrapper-learning
  - `improvement`: improvement-2026-03-29-001, improvement-2026-03-29-002（已有）
- 為每篇筆記評估 maturity（seed / growing / mature）— 根據內容豐富度
- 為每篇筆記指定 domain
- `related` 欄位保持原格式不變，為有明確語義關係的筆記新增 `relation_map` 欄位
- 更新 `updated` 欄位為 `2026-03-29`
- 特別注意：`csm-architecture` 和 `csm-key-design-decisions` 的 `relation_map` 應標記 `claude-session-manager:documents`
- Unit 3 和 Unit 4 之間做一次 git commit checkpoint，確保 tag 整合和 schema 遷移可獨立回滾

**Patterns to follow:**
- 現有 `improvement-2026-03-29-001.md` 的 subtype frontmatter 格式
- CONVENTIONS.md 的 frontmatter 規範（更新後版本）

**Test scenarios:**
- Happy path: 所有 23 篇 resources 都有 subtype、maturity、domain 欄位
- Happy path: areas 和 projects 有 maturity、domain 欄位
- Edge case: 已有 `subtype: improvement` 的 2 篇筆記保持不變
- Edge case: journal 筆記只加 domain，不加 subtype 和 maturity
- Edge case: `related` 欄位格式完全不變，新增的 `relation_map` 只出現在有明確語義關係的筆記
- Integration: 遷移後 `obsidian-agent sync` 能正常重建索引（`related` 格式未改動，不會破壞 sync）

**Verification:**
- `obsidian-agent list --type resource` 的所有筆記都有 subtype 欄位
- resources/ 的 subtype 分布合理（不再有單一 bucket 問題）
- 無遺漏 frontmatter 欄位

---

- [x] **Unit 5: Bridge Commands 更新**

**Goal:** 更新 `/bridge-compound` 和 `/bridge-plan` 的 metadata mapping，確保橋接產出的筆記符合新 schema

**Requirements:** R6（向後相容）

**Dependencies:** Unit 1

**Files:**
- Modify: `.claude/commands/bridge-compound.md`
- Modify: `.claude/commands/bridge-plan.md`

**Approach:**
- `/bridge-compound`: 產出的 resource note 固定 `subtype: learning`、`maturity: seed`（初次建立）、`domain` 從 CE compound 的 `category` 欄位推導
- `/bridge-plan`: 產出的 project note 加入 `maturity: seed`、`domain` 從 plan 內容推導
- 兩個 bridge 的 `related` 欄位保持原格式，有明確語義的連結同時設定 `relation_map`

**Patterns to follow:**
- 現有 bridge command 的 slash command 結構
- Unit 1 定義的新 schema

**Test scenarios:**
- Happy path: `/bridge-compound` 產出的 vault note 包含 `subtype: learning`、`maturity: seed`、`domain`
- Happy path: `/bridge-plan` 產出的 vault note 包含 `maturity: seed`、`domain`
- Edge case: CE compound 的 category 無法映射到已知 domain → fallback 到 `project-specific`

**Verification:**
- 橋接產出的筆記通過 `obsidian-agent health` 檢查
- 新橋接的筆記在 `_index.md` 中正確顯示

---

- [x] **Unit 6: 索引重建 + 健康驗證**

**Goal:** 重建所有索引，驗證結構升級的效果

**Requirements:** R7

**Dependencies:** Units 4, 5

**Files:**
- Rebuild: `_tags.md`, `_graph.md`, `resources/_index.md`, `areas/_index.md`, `projects/_index.md`, `ideas/_index.md`
- Modify: `journal/2026-03-29.md`（記錄完成）

**Approach:**
- 執行 `obsidian-agent sync` 重建所有索引
- 執行 `obsidian-agent health` 檢查 Grade
- 執行 `obsidian-agent cluster` 檢查是否出現有意義的 cluster 分離（預期：研究類、環境類、專案類至少分為 2-3 個 cluster）
- 檢查 `_graph.md` 的 Relation 欄位是否正確反映 typed relations（如果 sync 不解析 relation type，至少確認 `related` type 填充正確且不報錯）
- 在 journal 中記錄結構升級完成

**Patterns to follow:**
- Plan 002 Unit 4 的驗證模式

**Test scenarios:**
- Happy path: `obsidian-agent health` 維持 Grade A
- Happy path: `obsidian-agent cluster` 顯示 2+ 個有意義的 cluster
- Edge case: `_graph.md` 的 phantom entry（`research-chenglou-pretext-...`）被清除
- Edge case: sync 對 `relation_map` 等新欄位安全忽略（不報錯、不影響索引）
- Integration: `obsidian-agent search "subtype:research"` 或類似查詢可利用新欄位（若 CLI 支援 frontmatter 搜尋）

**Verification:**
- Health Grade A
- Cluster 數量 > 1（目前是 1 個巨型 cluster）
- 索引中無 phantom entries
- Tag singleton 比例 < 40%
- subtype 分布：至少 5 種 subtype 在使用中

## System-Wide Impact

- **CONVENTIONS.md**: schema 新增 3 個欄位（subtype, maturity, domain）+ typed relations convention + tag 命名規範。這是 vault 的 source of truth，影響所有 agent 行為
- **Templates**: 所有 templates 更新，影響未來筆記建立的預設值
- **現有筆記**: ~30 篇全部 frontmatter 更新，但內容不變
- **_tags.md**: tag 數量可能減少 30-40%（合併 singletons）
- **_graph.md**: `rebuildGraph()` 硬編碼 Relation 欄位為 `related`（`index-manager.mjs:49`）。`relation_map` 的語義資訊**不會反映在 `_graph.md` 中**。Typed relations 的唯一存活位置是各筆記的 frontmatter `relation_map` 欄位。Agent 若需查詢 relation type 必須讀筆記 frontmatter，不能依賴 `_graph.md` 第三欄
- **Slash commands**: `/bridge-compound` 和 `/bridge-plan` 在本計畫 Unit 5 中更新，產出符合新 schema 的筆記
- **obsidian-agent CLI**: 不受影響（新欄位被忽略），但未來可選擇性利用 subtype/domain 做更精準的 list/search
- **不受影響的 invariants**: type→directory 對應、file naming convention、journal 格式、CE 產出 schema

## Risks & Dependencies

| Risk | Mitigation |
|------|------------|
| `relation_map` string 欄位被 CLI parser 意外解析 | 源碼確認 `parseFrontmatter()` 對不認識的 key 安全忽略。低風險，但實作時仍需用一篇筆記驗證 |
| subtype 分類邊界仍模糊（某篇筆記可能同時是 reference 和 research） | CONVENTIONS.md 定義明確的使用時機 + "when in doubt" 規則（選最主要的角色） |
| Tag 合併可能遺失有用的細粒度分類 | 合併前列出完整 map 供人工確認，保留有獨特價值的 singletons |
| 30 篇筆記的 batch 更新可能引入 frontmatter 格式錯誤 | 每篇更新後跑 `obsidian-agent health` 做增量驗證 |
| domain 受控詞彙太窄或太寬 | 初始定義 5 個 domain，CONVENTIONS.md 明確說明新增 domain 的流程 |

## Sources & References

- Related plans: [Plan 001 - workflow self-iteration](docs/plans/2026-03-29-001-feat-workflow-self-iteration-plan.md), [Plan 002 - obsidian-agent efficiency](docs/plans/2026-03-29-002-feat-obsidian-agent-efficiency-plan.md)
- Schema definition: `CONVENTIONS.md`
- Template files: `templates/resource.md`, `templates/improvement.md`
- Index system: `_tags.md`, `_graph.md`, `resources/_index.md`
- subtype precedent: `CONVENTIONS.md` improvement subtype (lines 33-50)
- CLI parser source: `obsidian-agent/src/vault.mjs` (lines 54-75: `parseFrontmatter()`, line 69: related regex)
- Graph rebuild: `obsidian-agent/src/index-manager.mjs` (lines 42-58: `rebuildGraph()`, line 49: hardcoded `related`)
- Bridge commands: `.claude/commands/bridge-compound.md`, `.claude/commands/bridge-plan.md`
