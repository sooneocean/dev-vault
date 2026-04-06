---
title: Unit 1.2 快速參考 | Schema Markup 佈署速查表
type: project
tags: [project, active]
created: 2026-04-03
updated: 2026-04-03
status: active
maturity: growing
domain: knowledge-management
summary: ""
---

# Unit 1.2 快速參考 | Schema Markup 佈署速查表
## 可複製粘貼的命令與清單

---

## 🎯 任務概覽（1 分鐘）

**目標**：為 yololab.net Top 50 文章部署 Schema markup
**時間**：2-2.5 小時
**狀態**：Ready to Execute

| 階段 | 任務 | 時間 | 狀態 |
|------|------|------|------|
| 1 | Yoast SEO 配置 | 30 分鐘 | 待執行 |
| 2 | Schema 驗證 | 60-75 分鐘 | 待執行 |
| 3 | 問題修正 | 30-45 分鐘 | 待執行 |
| 4 | 報告生成 | 15 分鐘 | 待執行 |

---

## 🔗 快速連結

```
WordPress 後台：https://yololab.net/wp-admin
Yoast SEO Tools：https://yololab.net/wp-admin/admin.php?page=wpseo_tools
Google Rich Results Test：https://search.google.com/test/rich-results
Google Search Console：https://search.google.com/search-console
```

---

## 📋 Step 1：Yoast SEO 配置（複製檢查清單）

### 1.1 驗證 Yoast 已安裝

```
WordPress 後台 → Yoast SEO
確認顯示「Yoast SEO」菜單（左側邊欄）
確認 License 狀態：Active（綠色）
```

### 1.2 訪問 Schema 設定

```
Yoast SEO → Tools → Schema
或直接：https://yololab.net/wp-admin/admin.php?page=wpseo_tools
```

### 1.3 配置分類 Schema

**A. 音樂分類**
```
Category: 音樂
├─ Schema Type: NewsArticle ✓
├─ Enable Review: ✓
└─ Enable MusicRecording: ✓
```

**B. 電影分類**
```
Category: 電影
├─ Schema Type: NewsArticle ✓
├─ Enable Review: ✓
└─ Enable Movie: ✓
```

**C. 科技分類**
```
Category: 科技
└─ Schema Type: NewsArticle ✓
```

### 1.4 保存配置

```
點擊頁面下方「Save」或「Update」
等待「Successfully saved」提示
```

### 1.5 驗證配置已生效

```
編輯任一音樂文章：https://yololab.net/wp-admin/post.php?post=30121&action=edit
向下滾動 → 查看右側 Yoast SEO Panel → Schema 標籤
確認顯示：✓ NewsArticle, ✓ Review, ✓ MusicRecording
確認無紅色警告
```

---

## 🔍 Step 2：Schema 驗證（快速流程）

### 2.1 選擇要驗證的 15 篇文章

**音樂樂評（5 篇）：**
```
ID: 30121 - https://yololab.net/archives/yohee-if-i-were-a-player-diss-track-review
ID: 34942 - https://yololab.net/archives/kanye-west-bully-album-analysis
ID: 34935 - https://yololab.net/archives/central-cee-all-roads-lead-home-review
ID: 34893 - https://yololab.net/archives/sarah-chen-slow-blooming-soul-music
ID: 34816 - https://yololab.net/archives/fiona-nan-ying-spring-parasitic-flower-rb-ep
```

**電影評測（5 篇）：**
```
ID: 34899 - https://yololab.net/archives/no-good-ogs-movie-review-christopher-lee-mark-lee
ID: 34831 - https://yololab.net/archives/cold-war-1994-imax-review
ID: 34784 - https://yololab.net/archives/catching-shadow-movie-imax-review
ID: 34761 - https://yololab.net/archives/jodie-foster-private-consultation-mystery-review
ID: 34752 - https://yololab.net/archives/death-bet-movie-review-spring-wind-crime-thriller
```

**科技分析（5 篇）：**
```
ID: 34881 - https://yololab.net/archives/ai-ide-agent-collaboration-survival-guide
ID: 34853 - https://yololab.net/archives/ai-computing-power-rationing-survival
ID: 34666 - https://yololab.net/archives/openclaw-ai-agent-one-person-company
ID: 34647 - https://yololab.net/archives/cli-redesign-for-ai-agents
ID: 34635 - https://yololab.net/archives/shen-yulin-fighting-street-reality-aesthetic
```

### 2.2 Google Rich Results Test - 逐篇驗證流程

**重複此流程 15 次：**

```
1. 打開 https://search.google.com/test/rich-results

2. 在文本框輸入 URL（如）：
   https://yololab.net/archives/yohee-if-i-were-a-player-diss-track-review

3. 點擊「Test URL」按鈕

4. 等待 5-10 秒

5. 查看結果：
   ✅ Valid Rich Results   → 記錄為「✅ Valid」
   ⚠️ Warnings             → 記錄為「⚠️ Warnings」
   ❌ Errors               → 記錄為「❌ Errors」

6. 點擊「View tested URL」展開詳細信息

7. 記錄所有 Error/Warning 到 CSV：
   - Schema 類型
   - 問題欄位
   - 錯誤信息

8. 進入下一個 URL
```

### 2.3 結果記錄格式

```csv
文章ID,標題,驗證結果,主要問題,修正優先級,修正日期
30121,Yohee樂評,✅ Valid,-,P0,-
34942,Kanye West,⚠️ Warnings,Missing ratingValue,P1,2026-04-04
34899,NO GOOD,❌ Errors,Missing headline,P0,2026-04-04
```

---

## 🔧 Step 3：問題修正

### 3.1 P0（關鍵）問題修正

**常見 P0 問題 & 解決方案：**

| 問題 | 原因 | 修正方法 |
|------|------|--------|
| Missing headline | 標題未被識別 | 檢查文章標題是否為空，重新保存 |
| Invalid image URL | 圖片 404 | 更換特色圖片或檢查 CDN |
| Missing "@type" | Schema 類型未設定 | 重新配置 Yoast Schema |

**修正步驟（通用）：**
```
1. 進入文章編輯：https://yololab.net/wp-admin/post.php?post=[ID]&action=edit

2. 向下滾動到 Yoast SEO Panel（右側）

3. 點擊「Schema」標籤

4. 查看紅色 ❌ 警告

5. 根據警告信息修正欄位（如填入評分、更新圖片等）

6. 點擊「Save Draft」或「Update」

7. 等待 5-10 分鐘

8. 重新驗證該 URL
```

### 3.2 P1（重要）問題修正

```
修正策略相同，但不急於立即修正
可在驗證完所有文章後，集中修正
```

### 3.3 P2（低優先級）問題

```
可忽略或留待 Unit 1.3 時修正
不影響 Schema 有效性
```

---

## 📊 Step 4：統計與報告

### 4.1 快速統計

**在 CSV 中計數：**
```
=COUNTIF(D:D,"✅ Valid")           → 有效數量
=COUNTIF(D:D,"⚠️ Warnings")        → 警告數量
=COUNTIF(D:D,"❌ Errors")          → 錯誤數量
```

### 4.2 報告模板

```markdown
# Unit 1.2 完成報告

## 執行日期
2026-04-04

## 結果統計
- ✅ Valid: [12] 篇 (80%)
- ⚠️ Warnings: [2] 篇 (13%)
- ❌ Errors: [1] 篇 (7%)

## 主要發現
1. [問題 1]
2. [問題 2]

## Go/No-Go 決策
- [x] GO：達成 80% 有效率，可進行 Unit 1.3
- [ ] NO-GO：需要追加修正

## 下一步
進行 Unit 1.3 分類頁面優化
```

---

## ⚡ 常見問題速查

### Q1：Yoast 配置後無 Schema

**快速修復：**
```
1. Yoast SEO → Tools → File Cleanup
2. 清除所有快取
3. 重新編輯並保存任意文章
4. 等待 10 分鐘
```

### Q2：Rich Results Test 報錯

**快速修復（按順序嘗試）：**
```
1. 刷新頁面（Ctrl+F5）
2. 等待 10-15 分鐘（爬蟲延遲）
3. 更新相關欄位並重新保存文章
4. 使用不同 URL 格式嘗試（www/non-www）
```

### Q3：圖片 URL 404

**快速修復：**
```
1. 進入文章編輯
2. 點擊「Set featured image」
3. 選擇或上傳新圖片
4. 保存
5. 重新驗證
```

### Q4：如何批量修正

**推薦方案：**
```
方案 1：使用 Yoast Bulk Editor
Yoast SEO → Tools → Bulk Editor

方案 2：手動逐篇修正（≤20 篇）
預計時間：20 篇 × 3-5 分鐘 = 60-100 分鐘
```

---

## 📁 檔案清單

**本次執行生成的檔案：**

```
docs/plans/2026-04-04-unit1-2-schema-deployment-plan.md
  └─ 詳細計畫文檔

docs/Unit1.2-Execution-Guide.md
  └─ 完整執行指南

docs/Unit1.2-Quick-Reference.md
  └─ 本文件（快速參考）

docs/Unit1.2-Schema-Validation-Checklist.csv
  └─ 驗證清單 & 結果記錄表

docs/Unit1.2-Completion-Report.md
  └─ 完成報告（待生成）
```

---

## ✅ 執行清單（列印版）

```
□ 檢查 WordPress & Yoast 環境
□ 訪問 Yoast SEO Schema 設定
□ 配置音樂分類 Schema
□ 配置電影分類 Schema
□ 配置科技分類 Schema
□ 保存配置
□ 驗證配置已生效（測試文章）

□ Google Rich Results Test - 驗證 15 篇文章
  □ 5 篇音樂樂評
  □ 5 篇電影評測
  □ 5 篇科技分析

□ 記錄所有驗證結果到 CSV

□ 修正 P0 問題
□ 修正 P1 問題（如時間允許）
□ 重新驗證修正的文章

□ 生成完成報告
□ 統計最終成績
□ 確認 Go/No-Go 決策

□ 交付文件：
  □ 計畫文檔
  □ 執行指南
  □ 驗證清單（已填寫）
  □ 完成報告
  □ 快速參考（本文件）
```

---

## ⏱️ 時間節奏表

**開始時間：[填入]**

| 階段 | 預計時間 | 開始時間 | 完成時間 | 備註 |
|------|---------|---------|---------|------|
| Step 1: 配置 | 30 分 | | | |
| Step 2: 驗證 | 60-75 分 | | | 15 篇 × 4 分/篇 |
| Step 3: 修正 | 30-45 分 | | | 依問題數 |
| Step 4: 報告 | 15 分 | | | |
| **總計** | **2-2.5 小時** | | | |

**預計完成時間：[填入]**

---

## 🚀 Ready to Execute

所有準備工作已完成。請按照本快速參考指南執行 Unit 1.2。

**需要幫助？** 參考 `Unit1.2-Execution-Guide.md` 中的「常見問題」部分。

---

**版本**：1.0
**最後更新**：2026-04-04
**狀態**：Ready for Immediate Execution
