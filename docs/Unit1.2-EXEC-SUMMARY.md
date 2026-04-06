---
title: Unit 1.2 執行概覽 | Schema Markup 佈署準備完成
type: project
tags: [project, active]
created: 2026-04-03
updated: 2026-04-03
status: active
maturity: growing
domain: knowledge-management
summary: ""
---

# Unit 1.2 執行概覽 | Schema Markup 佈署準備完成
## 2026-04-04 執行報告

---

## 📌 任務狀態

**Unit 1.2：基礎 Schema Markup 佈署**

| 項目 | 狀態 | 備註 |
|------|------|------|
| 計畫文檔 | ✅ 完成 | `docs/plans/2026-04-04-unit1-2-schema-deployment-plan.md` |
| 執行指南 | ✅ 完成 | `docs/Unit1.2-Execution-Guide.md` |
| 快速參考 | ✅ 完成 | `docs/Unit1.2-Quick-Reference.md` |
| 驗證清單 | ✅ 完成 | `docs/Unit1.2-Schema-Validation-Checklist.csv` |
| **準備階段** | ✅ 完成 | 所有工具與清單已就緒 |
| **執行階段** | ⏳ 待執行 | 需要人工操作 Yoast SEO + Google Rich Results Test |

---

## 🎯 任務簡述

**目標：** 為 yololab.net（Site ID: 133512998）的 Top 50 文章佈署有效的 Schema markup

**預期成果：**
- 所有 Top 50 文章有有效 Schema
- Google Rich Results 驗證通過率 ≥ 80%
- 零 Critical Errors
- 完整的驗證報告和修正記錄

**耗時：** 2-2.5 小時（包括修正與驗證）

---

## 📋 執行清單（分階段）

### 🔧 階段 1：Yoast SEO 配置（30 分鐘）

**必做項：**
```
1. 訪問 WordPress 後台 → Yoast SEO → Tools → Schema
2. 驗證默認設定（應為 NewsArticle）
3. 配置分類特定 Schema：
   ✓ 音樂分類 → NewsArticle + MusicRecording + Review
   ✓ 電影分類 → NewsArticle + Movie + Review
   ✓ 科技分類 → NewsArticle
4. 保存配置
5. 驗證配置已生效（編輯 1 篇文章檢查 Yoast Panel）
```

**關鍵檢查點：**
- Yoast Panel 中應顯示對應的 Schema 類型
- 無紅色 ❌ 警告
- 配置保存成功提示

**詳細步驟：** 參考 `Unit1.2-Execution-Guide.md` 的「第 1 階段」

---

### 🔍 階段 2：Schema 驗證（60-75 分鐘）

**驗證範圍：** Top 50 文章中的代表性 15 篇

**驗證分佈：**
- 音樂樂評 5 篇（ID: 30121, 34942, 34935, 34893, 34816）
- 電影評測 5 篇（ID: 34899, 34831, 34784, 34761, 34752）
- 科技分析 5 篇（ID: 34881, 34853, 34666, 34647, 34635）

**驗證工具：** Google Rich Results Test
```
URL: https://search.google.com/test/rich-results
```

**預期結果：**
```
✅ Valid:     ≥ 12 篇 (80%+) → 成功
⚠️ Warnings:  ≤ 2 篇  (13%)  → 可接受
❌ Errors:    0 篇    (0%)   → 必須達成
```

**詳細步驟：** 參考 `Unit1.2-Execution-Guide.md` 的「第 2 階段」

---

### 🔧 階段 3：問題修正（30-45 分鐘）

**修正優先級：**

**P0（必須修正）：**
- Missing required fields（headline, image 等）
- Invalid URL format
- Schema type 完全缺失

**P1（應該修正）：**
- Missing optional fields（author, dateModified 等）
- Missing ratingValue（Review 類型）
- Image URL 404 等

**P2（可選修正）：**
- Recommendations（最佳實踐）
- Deprecation warnings

**修正方法：**
```
方法 1：Yoast SEO Panel 手動編輯（推薦）
方法 2：HTML Schema 手動編輯（進階）
方法 3：Yoast Bulk Editor（大批量）
```

**詳細步驟：** 參考 `Unit1.2-Execution-Guide.md` 的「第 3 階段」

---

### 📊 階段 4：報告與統計（15 分鐘）

**統計內容：**
```
- 驗證文章總數：15
- ✅ Valid 數量及百分比
- ⚠️ Warnings 數量及百分比
- ❌ Errors 數量及百分比
- 修正執行情況（P0/P1/P2 修正率）
```

**Go/No-Go 決策：**
```
✅ GO：驗證通過率 ≥ 80%，可進行 Unit 1.3
❌ NO-GO：通過率 < 80%，需要追加修正
```

**詳細步驟：** 參考 `Unit1.2-Execution-Guide.md` 的「第 4 階段」

---

## 📁 生成的文檔列表

### 已生成文檔（本地）

| 文件名 | 用途 | 位置 |
|--------|------|------|
| `2026-04-04-unit1-2-schema-deployment-plan.md` | 詳細計畫 | `docs/plans/` |
| `Unit1.2-Execution-Guide.md` | 完整執行指南 | `docs/` |
| `Unit1.2-Quick-Reference.md` | 快速查閱表 | `docs/` |
| `Unit1.2-Schema-Validation-Checklist.csv` | 驗證清單與結果記錄 | `docs/` |
| `Unit1.2-EXEC-SUMMARY.md` | 本文件（執行概覽） | `docs/` |

### 待生成文檔（執行後）

| 文件名 | 用途 | 生成時間 |
|--------|------|---------|
| `Unit1.2-Completion-Report.md` | 完成報告 | 執行完成後 |
| `Unit1.2-Validation-Results.json` | 詳細驗證結果 | 執行完成後 |

---

## 🚀 立即開始的方法

### 方法 1：直接執行（推薦）

```bash
# 1. 打開快速參考
# 位置：C:/DEX_data/Claude Code DEV/docs/Unit1.2-Quick-Reference.md

# 2. 準備 WordPress 環境
# 登入：https://yololab.net/wp-admin

# 3. 開始 Step 1（Yoast 配置）
# 參考快速參考中的「Step 1：Yoast SEO 配置」

# 4. 按順序完成 Step 2、3、4
```

### 方法 2：詳細參考

```bash
# 1. 閱讀執行指南
# 位置：C:/DEX_data/Claude Code DEV/docs/Unit1.2-Execution-Guide.md

# 2. 進行每個階段的詳細操作
# 每個階段都有完整的逐步說明

# 3. 使用驗證清單記錄結果
# 位置：C:/DEX_data/Claude Code DEV/docs/Unit1.2-Schema-Validation-Checklist.csv
```

### 方法 3：邊做邊參考

```bash
# 1. 開啟快速參考（可列印）
# 2. 同步開啟 WordPress 後台
# 3. 一邊對照清單，一邊操作
# 4. 完成後記錄到 CSV
```

---

## ⚙️ 環境檢查清單

執行前，請確認以下環境已就緒：

```
□ WordPress 後台可訪問
  - URL: https://yololab.net/wp-admin
  - 已登入管理員帳戶

□ Yoast SEO Premium 已安裝啟用
  - 左側邊欄顯示「Yoast SEO」菜單
  - License 狀態：Active（綠色）

□ Google Rich Results Test 可訪問
  - URL: https://search.google.com/test/rich-results
  - 無訪問限制或地理限制

□ Google Search Console 已連接
  - 可訪問 https://search.google.com/search-console
  - yololab.net 已驗證

□ Chrome DevTools / Lighthouse 可用
  - Chrome 或 Edge 瀏覽器已安裝
  - F12 可打開 DevTools
```

---

## 📊 預期工作量與時間安排

### 時間估計（總計 2-2.5 小時）

| 階段 | 任務 | 耗時 | 難度 |
|------|------|------|------|
| 1 | Yoast 配置 | 30 分 | 簡單 |
| 2 | 15 篇驗證 | 60-75 分 | 中等 |
| 3 | 問題修正 | 30-45 分 | 中等 |
| 4 | 報告統計 | 15 分 | 簡單 |

### 資源需求

```
✓ 1 個 WordPress 管理員帳號
✓ 可訪問網絡環境
✓ 文本編輯工具（記錄 CSV）
✓ 瀏覽器（Chrome/Edge/Firefox）
✓ 可選：Excel 或 Google Sheets（編輯 CSV）
```

---

## 🔄 工作流程圖

```
Start
  ↓
環境檢查 (5 分)
  ↓
Step 1: Yoast 配置 (30 分)
  ↓
驗證配置生效 (5 分)
  ↓
Step 2: 驗證 15 篇文章 (60-75 分)
  ├─ 5 篇音樂樂評
  ├─ 5 篇電影評測
  └─ 5 篇科技分析
  ↓
記錄驗證結果到 CSV
  ↓
Step 3: 修正問題 (30-45 分)
  ├─ 修正 P0 問題
  ├─ 修正 P1 問題
  └─ 重新驗證修正的文章
  ↓
Step 4: 生成報告 (15 分)
  ├─ 統計驗證結果
  ├─ 確認 Go/No-Go
  └─ 交付檔案
  ↓
完成 Unit 1.2
  ↓
進入 Unit 1.3
```

---

## ⚠️ 常見陷阱 & 回避方法

### 陷阱 1：Yoast 配置後文章仍無 Schema

**原因：** 快取未清除或配置未保存
**回避方法：**
```
1. 確保點擊「Save」按鈕
2. 看到「Successfully saved」提示
3. 清除 Yoast 快取（Tools → File Cleanup）
4. 編輯並重新保存任意文章
5. 等待 10 分鐘後驗證
```

### 陷阱 2：Google Rich Results Test 超時或無結果

**原因：** 網絡延遲或 Google 爬蟲延遲
**回避方法：**
```
1. 刷新頁面（Ctrl+F5）
2. 等待 10-15 分鐘後再試
3. 使用不同瀏覽器
4. 檢查 URL 是否包含 www
```

### 陷阱 3：修正後仍驗證失敗

**原因：** Google 爬蟲未更新，或修正不完整
**回避方法：**
```
1. 確保修正已保存（查看文章編輯頁）
2. 等待 15-20 分鐘
3. 使用 GSC 的「Request Indexing」強制更新
4. 重新驗證
```

### 陷阱 4：超時完不成任務

**原因：** 沒有按優先級進行，浪費時間在細節
**回避方法：**
```
1. 優先修正 P0 問題（Critical）
2. 跳過 P2 問題（可選）
3. 設定 80% 為目標（而非 100%）
4. 超出時間則停止修正，進入報告階段
```

---

## 📞 故障排除快速指南

### 問題：Yoast Panel 無「Schema」標籤

**解決方案：**
```
1. Yoast SEO → General → Feature Management
2. 找到「Schema」，確認為「Enabled」
3. 保存
4. 重新進入文章編輯頁
```

### 問題：圖片 URL 驗證失敗（404）

**解決方案：**
```
1. 編輯文章 → Set featured image
2. 上傳新圖片或選擇現有圖片
3. 確保圖片 URL 以 https:// 開頭
4. 保存文章
5. 等待 10 分鐘後重新驗證
```

### 問題：Rating 欄位無法填入

**解決方案：**
```
1. 確認該文章的 Schema Type 為 Review
2. 在 Yoast Panel 中查找 Review 部分
3. 找到「reviewRating」→「ratingValue」
4. 輸入 1-10 之間的數字（如 8.5）
5. 保存文章
```

### 問題：修正後無改進

**解決方案：**
```
1. 在 Google Search Console 中使用「Request Indexing」
2. 或在 Google Rich Results Test 中勾選「Show more details」
3. 查看是否有其他隱藏的問題
4. 聯絡 Yoast 支援或檢查官方文檔
```

---

## 🎓 相關資源

### 官方文檔
- Yoast SEO Schema: https://yoast.com/structured-data-schema/
- Schema.org 標準: https://schema.org/
- Google Rich Results 幫助: https://developers.google.com/search/docs/advanced/structured-data/article

### 內部文檔
- Unit 1.1 診斷報告: `docs/Unit1.1-TOP50-Diagnosis.md`
- SEO Phase 1 計畫: `docs/plans/2026-04-03-seo-phase1-plan.md`
- 項目管理文檔: `CLAUDE.md`

---

## ✅ 交付檢查清單

執行完成時，請確認以下檔案已生成或更新：

```
□ Unit1.2-Schema-Validation-Checklist.csv
  (已填寫所有驗證結果)

□ Unit1.2-Completion-Report.md
  (新生成的完成報告)

□ Unit1.2-Validation-Results.json
  (可選：詳細驗證結果 JSON)

□ Yoast SEO 配置已保存
  (WordPress 後台確認)

□ Google Search Console
  (無新增 Schema 錯誤)
```

---

## 🏁 後續步驟

### 立即行動（下一步）

```
1. 檢查環境是否就緒（5 分鐘）
2. 打開 WordPress 後台和快速參考
3. 開始 Step 1: Yoast SEO 配置
4. 預估完成時間：今天 2-2.5 小時內
```

### 完成後（進入 Unit 1.3）

```
Unit 1.3：分類頁面基礎優化
├─ 時間：2-3 小時
├─ 目標：優化 3 個主要分類頁面
└─ 依賴：Unit 1.2 完成（Go 決策）
```

### 整體進度

```
Week 1（當前）：
├─ Unit 1.1: TOP 50 診斷 ✅ 完成
├─ Unit 1.2: Schema 佈署 ⏳ 執行中
└─ Unit 1.3: 分類優化 📅 待執行

Week 2-3：
├─ Unit 2.1: 支柱頁建設
├─ Unit 2.2: 內部連結網絡
└─ Unit 2.3: 內容缺口分析
```

---

## 📌 重要提醒

1. **時間管理**：嚴格按照時間估計進行，不要卡在細節上
2. **優先級順序**：P0 > P1 > P2，不必追求 100%
3. **記錄結果**：及時更新 CSV，避免遺忘
4. **驗證延遲**：Google 爬蟲延遲 10-20 分鐘，請耐心等待
5. **環境檢查**：開始前確保所有工具可訪問，節省後續時間

---

## 📞 聯絡與支援

如遇到問題：
1. 查看本文件的「故障排除」部分
2. 參考 `Unit1.2-Execution-Guide.md` 的「常見問題 & 故障排除」
3. 查閱官方文檔（見「相關資源」部分）
4. 若問題持續，可暫停並記錄問題，進入 Step 4 生成報告

---

## 📝 簽名與確認

**準備人：** Claude Code Agent
**準備日期：** 2026-04-04
**準備時間：** ~1 小時（文檔與清單生成）

**執行人：** [待填]
**執行開始時間：** [待填]
**執行完成時間：** [待填]

---

**版本**：1.0
**狀態**：✅ Ready to Execute
**下一步**：Proceed with Step 1 of Unit 1.2

---

## 🎯 最後檢查清單（開始執行前）

```
□ 已閱讀本文件
□ 已檢查環境（WordPress、Yoast、Google）
□ 已下載所有支援文檔
□ 已準備 CSV 記錄文件
□ 已設置 2-2.5 小時的不間斷工作時間
□ 已備好所有快速參考清單
□ Ready to Start ✅
```

**開始執行！** 前往 `Unit1.2-Quick-Reference.md` 開始 Step 1。
