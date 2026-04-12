# Implementation Plan Review Findings
**Document:** `docs/plans/2026-04-10-001-feat-yololab-geo-optimization-plan.md`
**Date:** 2026-04-10
**Reviewer Role:** Technical editor (internal consistency)

---

## CRITICAL FINDINGS

### 1. Missing Requirement from Trace (R2)
**Severity:** HIGH | **Confidence:** 0.95

**Finding:** Requirement R2 is omitted from the Requirements Trace section (lines 19-36) but is present in the origin document.

**Location:**
- Plan line 21-36: Lists R1, R3-R16, SC1-SC7 — **R2 is missing**
- Origin document (requirements.md line 69): "R2. 驗證 WordPress.com 對自訂 Schema.org JSON-LD 注入和自訂 HTML 區塊的技術限制，確認 GEO 優化在平台內可行"

**Impact:**
- R2 (WordPress.com technical feasibility validation) is a Phase 0 requirement but is never assigned to any implementation unit
- Units 3, 4 assume WordPress.com supports custom HTML blocks and Schema injection (they depend on this)
- The plan states (line 69 in origin): "（R2 將驗證）" but no Unit actually performs this validation

**Evidence:**
```
Origin requirements: R1, R2, R3, R4-R16, SC1-SC7
Plan requirements trace: R1, R3, R4-R16, SC1-SC7
Missing: R2
```

**Recommendation:** Either (1) add R2 to Unit 1's scope, or (2) explicitly defer R2 to implementation with clear justification that WordPress.com Schema/HTML support is "already verified in SEO Phase 1-5" (as stated in origin assumptions). Current state is neither a delivery commitment nor a documented assumption.

---

### 2. Phase Sequencing Contradiction: Unit 9 Dependencies vs. High-Level Diagram
**Severity:** MODERATE | **Confidence:** 0.80

**Finding:** The high-level flowchart (lines 105-138) contradicts the Unit 9 dependency claim (line 490).

**Location:**
- **Diagram claim** (lines 120-137): Phase 1 → Phase 1.5 (Topo) → Phase 2
  - Phase 1.5 contains Units 6, 7, 8 (Pillar Pages, internal linker GEO extension, author E-E-A-T)
  - Diagram shows Topo executing **after** Phase 1, **before** Phase 2
- **Unit 9 dependency claim** (line 490): "Unit 1-5（所有腳本建置完成）"
  - Unit 9 is titled "Phase 1 執行: 先導測試" and depends only on Units 1-5
  - Unit 9's approach (line 497): "使用 `geo-optimizer-v1.js --tier 1 --sample 50` 執行先導測試" — makes no mention of Pillar Pages, internal linker adjustments, or author pages

**The contradiction:** If Units 6-8 (Phase 1.5) execute after Phase 1 but before Phase 2, then Unit 9 (先導測試 of 50 articles) occurs in which phase?
- **Interpretation A:** Unit 9 is part of Phase 1, so the pilot test runs WITHOUT the topological improvements (Units 6-8). But the diagram shows Phase 1 → Phase 1.5 → Phase 2, implying Topo happens before measurement.
- **Interpretation B:** Unit 9 should depend on Units 1-8, but it only claims dependency on Units 1-5.

**Impact:**
- Ambiguous whether the pilot test (Unit 9) includes the topological improvements or not
- If pilot test is pre-Topo, then Units 6-8 deliverables (Pillar Pages, GEO-enhanced internal links) are not validated in the pilot phase
- Requirements R8, R9, R10 claim coverage in Unit 9 (line 488: "R4-R7, R11, R13, R14-R16") — but R8, R9, R10 are not mentioned, suggesting pilot test doesn't validate them

**Evidence:**
```
Diagram flow: Phase 0 → Phase 1 → [Phase 1.5: Units 6-8] → Phase 2
Unit structure: Phase 1 execution (Unit 9) depends on Units 1-5 only
Unit 9 coverage claim (line 488): R4-R7, R11, R13, R14-R16 (missing R8, R9, R10)
```

**Recommendation:** Clarify the narrative:
- **Option 1:** Rename "Phase 1.5" to "Phase 1.5-Post-Pilot" and move Units 6-8 to occur after Unit 9's measurement phase
- **Option 2:** Update Unit 9's dependency to include Units 6-8, and update the approach to validate Pillar Pages and GEO-enhanced links
- **Option 3:** Explicitly state that Units 6-8 are **parallel** to Unit 9, not sequential, and update diagram accordingly

---

### 3. Ambiguous Phase 1.5 Sequencing: Unit 6 vs. Unit 7 vs. Unit 8
**Severity:** MODERATE | **Confidence:** 0.75

**Finding:** The execution order of Units 6-8 is linearly sequenced by dependencies but their functional relationships suggest potential parallelization constraints that are not documented.

**Location:** Lines 377-480 (Unit 6, 7, 8 definitions)

**Dependency chain:**
```
Unit 6 (Pillar Pages) → depends on Unit 2
Unit 7 (Internal linker GEO) → depends on Unit 6 (Pillar Pages must exist)
Unit 8 (Author E-E-A-T) → depends on Unit 4 (WordPress injection mechanism)
```

**The ambiguity:**
- Unit 7 says it needs Unit 6 ("Pillar Page 已建立"), and Unit 7's approach (line 425) mentions "連結到相關文章的 FAQ 區塊（`#geo-faq` anchor）"
- But FAQ blocks are created by Unit 2-4, which execute before Unit 6
- Unit 7 could theoretically run in parallel with Unit 6, as it only requires the FAQ infrastructure (Units 2-4), not the Pillar Pages themselves
- The dependency claim ("Unit 6（Pillar Page 已建立）") is stricter than functionally necessary

**Impact:** Potential sequential bottleneck: Unit 7 is blocked on Unit 6 completion, but Unit 6 depends only on Unit 2, while Unit 7 depends on Units 2-4. This creates unnecessary waiting time.

**Recommendation:** Clarify whether Unit 7's "depends on Unit 6" is a true functional dependency (Unit 7 needs specific Pillar Page URLs to create cross-links) or a narrative sequencing (Pillar Pages should conceptually be established before GEO-enhanced links). If it's only the latter, Unit 7 could depend on Unit 4 instead and execute in parallel with Unit 6.

---

### 4. Success Criteria SC1, SC2 Not Assigned to Any Unit
**Severity:** MODERATE | **Confidence:** 0.85

**Finding:** Success criteria SC1 and SC2 (Phase 2 measurement outcomes) are listed in the requirements trace but not assigned to any implementation unit.

**Location:**
- Plan line 36: "SC1-SC7. 結果指標 + 產出指標"
- Unit 9 requirements claim (line 488): "SC3-SC7" (missing SC1, SC2)

**From origin document (lines 99-102):**
- SC1: "先導測試 50 篇文章在 AI 搜尋結果中的引用率相較基線有顯著提升"
- SC2: "來自 AI 搜尋引擎的推薦流量（referral traffic）相較基線有可觀測的增長"

**The gap:**
- SC1 and SC2 are Phase 2 measurements (30-60 day observation), which is NOT detailed in the plan
- Phase 2 is mentioned in the high-level design (line 125) but has no corresponding implementation units
- Unit 9 covers SC3-SC7 (production output metrics) but SC1, SC2 (outcome metrics) require Phase 2 execution

**Impact:**
- The plan is incomplete for Phase 2 deliverables
- Measurability of the entire initiative depends on SC1/SC2, but there's no assigned owner or implementation plan
- Unit 9 cannot claim full success criterion compliance

**Recommendation:** Either (1) add a Unit 10 for Phase 2 measurement execution, or (2) explicitly scope Phase 2 measurement as "out of scope for this plan, will be detailed in Phase 2 planning document" and update the requirements trace to exclude SC1, SC2 from this plan's coverage.

---

## MODERATE-SEVERITY FINDINGS

### 5. Terminology Drift: "Phase 1 執行" vs. "Phase 1"
**Severity:** MODERATE | **Confidence:** 0.70

**Finding:** Inconsistent use of "Phase 1" across the document creates ambiguity about what Phase 1 encompasses.

**Location:**
- Line 112 (diagram): "Phase 1: 腳本建置 + 先導測試 50 篇" — suggests Phase 1 includes both script building and pilot test
- Line 220: "### Phase 1: GEO 腳本基礎設施" — Units 2-5, suggests Phase 1 is scripts only
- Line 482: "### Phase 1 執行: 先導測試" — Unit 9, separate heading from "Phase 1"

**The terminology drift:**
- "Phase 1" could mean: (a) Units 2-5 (script infrastructure), or (b) Units 2-9 (scripts + pilot execution)
- "Phase 1 執行" (Phase 1 execution) suggests Unit 9 is the "execution" stage of Phase 1, not a separate phase
- The diagram (line 112) conflates them: "Phase 1: 腳本建置 + 先導測試"

**Impact:** Readers may misinterpret whether Phase 1 is a single delivery or two sequential stages (build → execute).

**Recommendation:** Standardize terminology:
- Option A: Rename section header (line 482) from "Phase 1 執行" to "Phase 1c: 先導測試執行" to clarify it's a sub-phase
- Option B: Rename line 220 to "Phase 1a: GEO 腳本基礎設施" and line 375 to "Phase 1b: 內容拓撲重組" to show they're sequential within Phase 1
- Document clearly which units comprise each logical phase

---

### 6. Unresolved Ambiguity: Unit 2 "Single API Call" Design vs. Error Handling
**Severity:** LOW-MODERATE | **Confidence:** 0.65

**Finding:** The plan claims Unit 2 will use "單次 Claude API 呼叫" to generate all GEO content in one call (line 82: "single longer prompt"), but the test scenarios (line 253) describe error handling that suggests multiple conditional calls might be necessary.

**Location:**
- Line 82: "GEO 將用一次較長的 prompt 產出摘要、FAQ、權威陳述和歸因引用。理由：減少 API 成本和延遲"
- Line 238: "單次 Claude API 呼叫：輸入文章標題、摘要、分類、前 2000 字內容。輸出 JSON 含..."
- Line 251: Edge case test — "字數 < 500 的新聞快訊文章，跳過 FAQ 生成但仍產出摘要"

**The ambiguity:**
- Does "single call" mean one call regardless of content type, or one call per article (but structure varies)?
- If FAQ generation is skipped for short articles, does Unit 2 still make one call with a conditional prompt, or does it make a different call with a simplified prompt?
- The phrasing suggests a single fixed prompt, but the "skip FAQ" logic implies conditional branching

**Impact:** Implementation could diverge on whether to use branching logic (multiple conditional calls) or a single parameterized call.

**Recommendation:** Clarify in the prompt specification section (which is deferred, line 97) whether the single-call design includes conditional instructions within the prompt (e.g., "if article length < 500, skip FAQ generation") or if skip logic happens before/after the API call.

---

## LOW-SEVERITY FINDINGS

### 7. Ungrouped Requirements in Requirements Trace
**Severity:** LOW | **Confidence:** 0.80

**Finding:** The Requirements Trace section (lines 19-36) is a flat list without organizational grouping, making it harder to scan by logical domain.

**Location:** Lines 19-36

**Current structure:**
```
- R1. AI 引用基線量測
- R3. AI 爬蟲可及性
- R4. AI 友善「摘要 + 快速回答」區塊
- R5. FAQ 區塊
... (etc, mixed concern domains)
- SC1-SC7. 結果指標 + 產出指標
```

**Suggested structure (for readability):**
```
## Requirements Trace

**Phase 0: 基線量測與可行性**
- R1. AI 引用基線量測
- R2. WordPress.com 技術驗證
- R3. AI 爬蟲可及性

**面向 A: 單篇內容結構改造**
- R4. AI 友善摘要 + 快速回答
- R5. FAQ 區塊
... (etc)

**成功指標**
- SC1-SC7. 結果與產出指標
```

**Impact:** Minor — the plan is still understandable, but the flat list makes it harder to verify completeness and relate requirements to phases.

**Recommendation:** Group requirements by phase/concern domain for better scannability. Keep original R# IDs for traceability.

---

### 8. Forward Reference Not Yet Resolved: "現有 `data/pillar-map.json` 的 5 個 Pillar article 覆蓋度"
**Severity:** LOW | **Confidence:** 0.60

**Finding:** Unit 6 approach (line 390) references "評估現有 `data/pillar-map.json` 的 5 個 Pillar article 覆蓋度，補齊缺失的 Classic 和 Games 分類" without showing evidence that this data file currently has 5 articles.

**Location:** Line 390

**Issue:** The plan assumes `data/pillar-map.json` exists and has 5 Pillar articles, but no verification step confirms this before Unit 6 execution. If the file doesn't exist or has a different structure, Unit 6's approach needs adjustment.

**Impact:** Minimal risk (file likely exists from prior SEO phases), but represents an unverified assumption.

**Recommendation:** Unit 1 or Unit 6's verification should confirm the structure and content of `data/pillar-map.json` before execution.

---

## CONSISTENCY WITH ORIGIN DOCUMENT

### Good Alignments
✓ Problem framing matches requirements document
✓ High-level design conceptually sound (Phase 0 → Phase 1 → Phase 2 → Phase 3)
✓ Core script patterns and dependencies trace correctly
✓ Risk mitigation strategies well-reasoned

### Gaps vs. Origin
✗ R2 omitted from trace
✗ SC1, SC2 not assigned to implementation units
✗ "Already verified in Phase 1-5" claim (line 144 in origin) not explicitly restated in plan scope boundaries

---

## SUMMARY TABLE

| ID | Issue | Severity | Confidence | Category | Recommendation |
|---|---|---|---|---|---|
| #1 | R2 missing from requirements trace | HIGH | 0.95 | Traceability | Add to Unit 1 or defer with justification |
| #2 | Unit 9 dependencies vs. phase diagram | MODERATE | 0.80 | Sequencing | Clarify Unit 9's place in phase flow; update dependencies or diagram |
| #3 | Unit 7 dependency chain ambiguity | MODERATE | 0.75 | Sequencing | Clarify Unit 7's true functional dependency vs. narrative sequencing |
| #4 | SC1, SC2 not assigned to any unit | MODERATE | 0.85 | Scope | Add Phase 2 unit or explicitly defer with rationale |
| #5 | "Phase 1" vs. "Phase 1 執行" terminology | MODERATE | 0.70 | Terminology | Standardize naming (Phase 1a, 1b, 1c) or add explicit clarification |
| #6 | Unit 2 "single call" design ambiguity | LOW-MODERATE | 0.65 | Technical | Clarify prompt structure for conditional FAQ skipping |
| #7 | Flat requirements trace list | LOW | 0.80 | Structure | Group by phase/domain (autofix_class: auto) |
| #8 | Unverified `pillar-map.json` assumption | LOW | 0.60 | Assumption | Add pre-flight verification step |

---

## NOTES FOR IMPLEMENTER

1. **Before starting Unit 1:** Confirm whether R2 (WordPress.com technical validation) is considered "already done" based on SEO Phase 1-5 experience. If so, document this assumption explicitly in the plan's Scope Boundaries section.

2. **Before starting Unit 9:** Clarify whether the 50-article pilot includes the topological improvements (Units 6-8) or runs independently. Update the diagram or unit dependencies to match.

3. **Phase 2 Planning:** Ensure a separate implementation plan details how SC1 and SC2 will be measured (AI platforms to query, sampling methodology, attribution tracking). This is critical for demonstrating ROI.

4. **Unit 7 Optimization:** If Unit 7's Pillar Page dependency is narrative only, move its dependency back to Unit 4 to enable parallel execution with Unit 6.

