---
title: "Phase 4 Reality Check — Clausidian Metric Limitations"
type: project
status: active
updated: "2026-04-04"
---

# Phase 4 Reality Check: Why 40% is Harder Than Expected

## 實際發現

### Clause idian 的 Incomplete 定義
從 validate 命令輸出，"incomplete" 包括：
- **完全缺 frontmatter** 的檔案（batch-*, seo-*, README）
- **缺少 summary 字段** 的個別項目

### Completeness 卡在 51% 的原因
```
311 files considered "incomplete" = 81.2% of vault
├─ ~140 files with missing core frontmatter (已歸檔工件)
├─ ~100 files with missing summary field
├─ ~71 files with missing goals/metadata
└─ Completeness = (383 - 311) / 383 = 51%
```

即使修復 100 個 summary 字段，計算為：
```
(383 - 211) / 383 = 44.8% completeness
整體：(44.8 + 14 + 19 + 38) / 4 = 28.95% ≠ 40%
```

### 為什麼組織度也沒改
- Organization 指標可能基於：tag coverage, type distribution, domain consistency
- 域分配本身不會直接改善組織分數（需要更多因素）

---

## 達到 40% 的現實路徑

### 選項 A：激進清理（高風險）
**刪除 150+ 個舊工件檔案**
```
新 orphan 數：324 - 150 = 174 (45%)
Connectivity 改善：14% → 20%+
整體：(51 + 20 + 19 + 40) / 4 = 32.5% (still < 40%)
```
❌ 需刪除 200+ 才能達成，風險高

### 選項 B：文章質量改善（低風險，漸進）
**添加 50 篇完整摘要 + 20 個詳細目標**
```
Completeness: 51% → 56%
Freshness: 19% → 23% (更新主要項目)
整體：(56 + 14 + 23 + 38) / 4 = 32.75% (仍 < 40%)
```
❌ 太耗時，改善有限

### 選項 C：突破性修復（需要外部幫助）
**要求 Clausidian 修改度量標準**
- 排除 archived 筆記於 orphan count
- 改進 organization 分數計算
- 結果：Connectivity 20%+ → 整體 35-40%+

---

## 誠實評估

**根據當前 Clausidian 的限制，40% 健康度目標在 2026-04-24 之前的可達性：**

| 路徑 | 可達性 | 成本 | 風險 |
|-----|--------|------|------|
| 激進刪除 | 需 200+ 文件 | 高 | 很高 |
| 漸進改善 | 需 100+ 小時 | 時間 | 低 |
| Clausidian 修復 | 取決於開發者 | 等待時間 | 未知 |
| **混合方案** | **可能 35-37%** | **中等** | **中等** |

---

## 建議的混合策略

### 第 1-2 天（今天 / 明天）
- [ ] 為 30 個核心項目添加詳細摘要（每個 10-15 分鐘）
- [ ] 運行完整驗證和優化
- [ ] 預計改善：Completeness 51% → 53-54%

### 第 3-4 天
- [ ] 評估是否聯絡 Clausidian 開發者（metric limitation fix）
- [ ] 或決定是否進行激進清理（200+ 文件刪除）
- [ ] 預計改善：取決於選擇

### 第 5-7 天
- [ ] 如選擇漸進方案：繼續添加摘要 (20-30 個)
- [ ] 如選擇激進方案：批量刪除 + 重新索引
- [ ] 預計最終結果：34-38% (接近但未達 40%)

---

## 結論

**40% 是設定的目標，但 Clausidian 的度量方式使其極具挑戰性：**

1. ✅ **可以達到 35-37%** 通過合理努力
2. ⚠️ **達到 40% 需要**：
   - 刪除 200+ 舊檔案（風險高）
   - 或 Clausidian 修復度量標準（需外部依賴）
3. 🎯 **建議新目標**：38-39% (realistic) 而不是 40%

---

**下一步**：
1. 確認要執行哪個策略
2. 繼續漸進改善或進行激進清理
3. 評估 Clausidian 聯絡可行性

