---
title: Unit 1.2：基礎 Schema Markup 佈署計畫
type: project
tags: [project, active]
created: 2026-04-03
updated: 2026-04-03
status: active
maturity: growing
domain: knowledge-management
summary: ""
---

# Unit 1.2：基礎 Schema Markup 佈署計畫
## 2026-04-04 執行版本

---

## 執行概要

**目標**：為 yololab.net 的 Top 50 文章自動新增 Schema markup（NewsArticle + Review + MusicRecording）

**網站信息**：
- Site ID（wpcom-mcp）：133512998
- 平台：WordPress.com Atomic
- 已安裝：Yoast SEO Premium
- 分類：音樂、電影、科技

**預期時間**：2-2.5 小時

---

## 工作流程設計

### 階段 1：本地計畫制定（完成）

#### 1.1 Top 50 文章清單
根據 Unit 1.1 診斷報告：
- Yohee (30121) - 音樂樂評
- Kanye West (34942) - 音樂樂評
- Central Cee (34935) - 音樂樂評
- Sarah Chen (34893) - 音樂樂評
- Jacob Collier (26085) - 音樂樂評
- NO GOOD (34899) - 電影評測
- 其他 44 篇（需從 WordPress 中提取）

#### 1.2 Schema 佈署策略

##### 分類對應 Schema 類型

| 分類 | 主要 Schema | 附加 Schema | 示例文章 |
|------|-----------|-----------|--------|
| 音樂樂評 | NewsArticle | MusicRecording + Review | Yohee (30121) |
| 電影評測 | NewsArticle | Movie + Review | NO GOOD (34899) |
| 科技分析 | NewsArticle | FAQPageSchema（如有） | AI IDE (34881) |

##### Schema 標準模板

**NewsArticle（所有文章）：**
```json
{
  "@context": "https://schema.org",
  "@type": "NewsArticle",
  "headline": "[文章標題]",
  "image": "[特色圖片 URL]",
  "datePublished": "[發佈日期 ISO]",
  "dateModified": "[最後修改日期 ISO]",
  "author": {
    "@type": "Person",
    "name": "YOLO LAB"
  },
  "publisher": {
    "@type": "Organization",
    "name": "YOLO LAB",
    "logo": "https://yololab.net/logo.png"
  }
}
```

**MusicRecording（音樂文章）：**
```json
{
  "@context": "https://schema.org",
  "@type": ["NewsArticle", "Review"],
  "reviewRating": {
    "@type": "Rating",
    "ratingValue": "[評分]",
    "bestRating": 10,
    "worstRating": 0
  },
  "about": {
    "@type": "MusicRecording",
    "name": "[歌曲/專輯名]",
    "byArtist": {
      "@type": "MusicGroup",
      "name": "[藝人名]"
    }
  }
}
```

**Movie + Review（電影文章）：**
```json
{
  "@context": "https://schema.org",
  "@type": ["NewsArticle", "Review"],
  "reviewRating": {
    "@type": "Rating",
    "ratingValue": "[評分]",
    "bestRating": 10
  },
  "about": {
    "@type": "Movie",
    "name": "[電影名]",
    "actor": [
      {"@type": "Person", "name": "[演員名]"}
    ]
  }
}
```

---

### 階段 2：Yoast SEO 配置（預估 30 分鐘）

#### 2.1 訪問 Yoast SEO Schema 設定
- WordPress 後台 → Yoast SEO → Tools → Schema
- 或：Yoast SEO → Integrations → Schema
- 檢查當前預設設定（應為 Blog Post）

#### 2.2 配置分類特定 Schema

**步驟 2.2a：音樂分類設定**
1. 進入 Yoast SEO Schema 設定
2. 添加 Custom Post Type 或 Category 規則：
   - Category: Music（或相應分類）
   - Schema Type: NewsArticle（預設）+ Review（可選）
3. 啟用 MusicRecording 支援
4. 測試：Yohee 文章 (30121)

**步驟 2.2b：電影分類設定**
1. Category: Film/Movie（或相應分類）
2. Schema Type: NewsArticle + Review
3. 配置 Movie 物件支援
4. 測試：NO GOOD 文章 (34899)

**步驟 2.2c：科技分類設定**
1. Category: Tech（或相應分類）
2. Schema Type: NewsArticle（基礎）
3. 啟用 FAQPageSchema（如果文章有 Q&A 段落）

#### 2.3 驗證配置生效
- 檢查 Yoast SEO Panel 中的 Schema 提示
- 確保無紅色警告
- 預期：綠色「✓ Schema 正確」

---

### 階段 3：Schema 驗證（預估 1-1.5 小時）

#### 3.1 Google Rich Results Test 驗證流程

**步驟 3.1a：準備驗證清單**
```
選擇代表性文章（每個分類）：
- 音樂（Yohee - 30121）
- 電影（NO GOOD - 34899）
- 科技（AI IDE - 34881）
- 其他 7 篇（隨機選）
```

**步驟 3.1b：逐篇驗證**
1. 打開 https://search.google.com/test/rich-results
2. 輸入文章 URL：https://yololab.net/archives/[post-slug]
3. 等待驗證結果（5-10 秒）
4. 記錄結果：
   - ✅ Valid
   - ⚠️ Warnings
   - ❌ Errors

**步驟 3.1c：記錄詳細結果**

| 文章 ID | 標題 | Schema 類型 | 驗證結果 | 問題描述 | 優先級 |
|--------|------|-----------|--------|--------|-------|
| 30121 | Yohee | NewsArticle | ✅ Valid | - | - |
| 34899 | NO GOOD | Review + Movie | ⚠️ Warning | Missing ratingValue | P1 |
| ... | ... | ... | ... | ... | ... |

#### 3.2 Google Search Console 集成檢查
- 登入 Google Search Console（假設已連接）
- 檢查 Enhancements → Rich Results
- 查看 Schema 錯誤數量
- 預期：新部署後錯誤數量不增加

#### 3.3 Lighthouse / PageSpeed Insights 驗證
- 抽查 5 篇文章
- 檢查 Lighthouse 報告中的 Schema 標記
- 預期：所有 Schema 有效

---

### 階段 4：修正與報告（預估 30-45 分鐘）

#### 4.1 問題分類
根據驗證結果，分類問題：

**P0（關鍵）：**
- Missing required fields（如 headline）
- Invalid URL format
- Image not accessible

**P1（重要）：**
- Missing optional fields（如 author）
- Missing ratingValue（Review 類型）
- Warning about structure

**P2（低優先級）：**
- Recommendations（最佳實踐建議）
- Deprecation warnings

#### 4.2 修正策略

**自動修正：**
- 依賴 Yoast SEO 自動填充基礎欄位
- 重新掃描問題文章

**手動修正：**
- 編輯文章中的「Schema」面板
- 填補缺失的欄位（如 ratingValue）
- 驗證 URL 和圖片 URL 正確性

**批量修正：**
- 使用 WordPress REST API 批量更新
- 或 Yoast SEO Bulk Editor（如有）

#### 4.3 報告生成

**最終驗證報告內容：**
1. 驗證時間戳
2. 驗證文章數（推薦 Top 10-15）
3. 結果統計：
   - ✅ Valid 文章數
   - ⚠️ Warning 文章數
   - ❌ Error 文章數
4. 問題清單（P0/P1/P2）
5. 修正執行率
6. 預期成效

---

## 關鍵技術參考

### Google Rich Results Test 詳細說明

**訪問 URL：** https://search.google.com/test/rich-results

**期望結果：**
- Rich Results 類型：Article / Review / FAQ
- 有效的 Properties（綠色勾選）
- 無 Errors（紅色標記）

**常見問題 & 解決方案：**

| 問題 | 原因 | 解決方案 |
|------|------|--------|
| `Missing "headline"` | 標題未被正確提取 | 檢查 Yoast 設定，確保文章 title 被設為 headline |
| `Missing "datePublished"` | 發佈日期未被識別 | 確保文章發佈日期正確格式（YYYY-MM-DD） |
| `Invalid URL` in image | 圖片 URL 不可達 | 檢查特色圖片 URL，確保圖片存在 |
| `Missing "ratingValue"` | Review 類型缺少評分 | 在 Yoast Schema 中填入評分（1-10） |

### Yoast SEO Schema 設定位置

**訪問路徑：**
1. WordPress 後台 → Yoast SEO → Tools
2. 選擇「Schema」標籤
3. 或：Yoast SEO → General → Feature Management → Schema

**可配置的 Schema 類型：**
- Article（預設）
- BlogPosting
- NewsArticle
- Review
- Movie
- MusicRecording
- Product
- FAQ
- ...

---

## 執行檢查清單

### 前置條件
- [ ] WordPress 後台可訪問
- [ ] Yoast SEO Premium 已啟用
- [ ] Top 50 文章清單已取得
- [ ] Google Search Console 已連接

### Yoast SEO 配置
- [ ] 訪問 Yoast SEO Schema 設定
- [ ] 配置音樂分類 → NewsArticle + MusicRecording
- [ ] 配置電影分類 → NewsArticle + Movie + Review
- [ ] 配置科技分類 → NewsArticle（+ FAQ 如需要）
- [ ] Yoast SEO Panel 中無紅色警告

### Schema 驗證
- [ ] 準備 10-15 篇代表性文章
- [ ] 在 Google Rich Results Test 中逐篇驗證
- [ ] 記錄所有驗證結果
- [ ] 檢查 Google Search Console 中無新 Schema 錯誤

### 修正與最終驗證
- [ ] 修正所有 P0 問題
- [ ] 修正所有 P1 問題（如時間允許）
- [ ] 重新驗證修正的文章
- [ ] 驗證通過率 ≥ 80%（至少 10/10 應通過）

### 報告與交付
- [ ] 生成 Unit 1.2 完成報告
- [ ] 記錄所有 Schema 驗證結果
- [ ] 確認 Go/No-Go 決策
- [ ] 準備進入 Unit 1.3

---

## 風險與 Fallback

### 風險 1：Yoast SEO 設定不生效
**症狀：** 配置後文章仍無 Schema
**原因：** Yoast Schema 快取或設定未激活
**Fallback：**
1. 清除 Yoast 快取（Yoast SEO → Tools → File Cleanup）
2. 重新保存文章
3. 檢查 Yoast Debug Info（Yoast SEO → Tools → Debugging）

### 風險 2：Google Rich Results Test 返回 Errors
**症狀：** 驗證失敗（Missing required fields）
**原因：** 圖片 URL 不可達或日期格式錯誤
**Fallback：**
1. 手動編輯文章 Schema 欄位
2. 使用 Yoast SEO Custom Schema（Advanced 功能）
3. 直接編輯 HTML `<script type="application/ld+json">` 標籤

### 風險 3：修正後仍無法驗證通過
**症狀：** Yoast 設定完全無效
**Fallback：**
1. 聯絡 Yoast 支援或檢查插件相容性
2. 考慮使用替代 Schema 插件（如 Schema Pro）
3. 手動為所有文章添加 Schema（更耗時）

---

## 預期成果（Unit 1.2 完成後）

| 項目 | 目標 | 達成標準 |
|------|------|--------|
| **Top 50 文章 Schema 佈署** | 100% | 所有 Top 50 文章有有效 Schema |
| **Google Rich Results 驗證通過率** | ≥ 80% | 至少 10/10 驗證通過 |
| **Schema 錯誤數** | 0 | 無 Critical Errors |
| **驗證報告** | 完成 | 詳細記錄所有結果 |

---

## 後續依賴
- **被依賴者**：Unit 1.3（分類頁面優化）、Unit 2.1（支柱頁建設）
- **下一步**：確認本計畫，開始執行 Yoast SEO 配置

---

## 更新日誌
- **2026-04-04**：計畫文檔初版建立
