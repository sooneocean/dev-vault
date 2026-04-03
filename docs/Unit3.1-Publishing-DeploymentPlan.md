---
title: Unit 3.1 內容發佈 + Google 索引提交 — 執行計畫
type: project
tags: [project, active]
created: 2026-04-03
updated: 2026-04-03
status: active
maturity: growing
domain: knowledge-management
summary: ""
---

# Unit 3.1 內容發佈 + Google 索引提交 — 執行計畫

**生成時間**：2026-04-03 12:05
**目標**：發佈 11 篇新文章 + Google Search Console 批量索引提交
**預計耗時**：2-3 小時（含驗證）

---

## 📋 發佈計畫時間表

### Week 2（2026-04-07 ~ 2026-04-13）

#### Batch 1：Tech Priority（3 篇）— 2026-04-07 上午

| 序號 | 文章標題 | 分類 | 發佈時間 | 狀態 |
|------|---------|------|---------|------|
| 1 | LLM 模型完整對比 2026 | Tech | 2026-04-07 09:00 | ⏳ |
| 2 | 提示詞工程完全指南 | Tech | 2026-04-08 09:00 | ⏳ |
| 3 | AI 智能體框架對比 | Tech | 2026-04-09 09:00 | ⏳ |

#### Batch 2：Tech Continuation + Music（3 篇）— 2026-04-10 ~ 2026-04-12

| 序號 | 文章標題 | 分類 | 發佈時間 | 狀態 |
|------|---------|------|---------|------|
| 4 | 向量數據庫選型指南 | Tech | 2026-04-10 09:00 | ⏳ |
| 5 | AI 編程助手工作流優化 | Tech | 2026-04-11 09:00 | ⏳ |
| 6 | 台灣民謠新浪潮 | Music | 2026-04-12 09:00 | ⏳ |

### Week 3（2026-04-14 ~ 2026-04-20）

#### Batch 3：Music + Film（5 篇）

| 序號 | 文章標題 | 分類 | 發佈時間 | 狀態 |
|------|---------|------|---------|------|
| 7 | 電子音樂製作完全入門 | Music | 2026-04-14 09:00 | ⏳ |
| 8 | 古典 × 搖滾藝術碰撞 | Music | 2026-04-15 09:00 | ⏳ |
| 9 | 紀錄電影完整指南 | Film | 2026-04-16 09:00 | ⏳ |
| 10 | 日本新浪潮電影復興論 | Film | 2026-04-17 09:00 | ⏳ |
| 11 | 性別研究視角電影批評 | Film | 2026-04-18 09:00 | ⏳ |

---

## 🎯 發佈工作流程

### Phase 1：文章準備（發佈前 1 天）

對每篇文章執行：

```
✅ Checklist

□ 確認文章字數：3,000+ 字（Tech）/ 2,500+ 字（Music/Film）
□ 驗證內部連結全部有效
□ 檢查 Schema Markup 完整性
  - BlogPosting 基本信息
  - 作者/出版社資訊
  - 發佈日期
  - 如適用：Movie / Review / FAQPage

□ SEO 檢查
  - Title：45-60 字
  - Meta Description：120-160 字
  - 目標 KW 自然出現 3-5 次
  - 內部連結數：3-4 條

□ 人性化檢查
  - AI 語言移除率 ≥ 70%
  - 台灣地方俚語自然融入
  - 評測語氣一致（激烈、專業、實用）

□ 多媒體檢查
  - Featured Image：已設定
  - 內嵌視頻/圖表：需驗證加載速度
  - Alt Text：已補充

□ 分類標籤
  - Primary Category：Music / Film / Tech
  - Tags：3-5 個（參考現有文章）
  - Featured：設定為 Featured（支柱頁會聚集）
```

---

### Phase 2：WordPress 發佈

**使用 wpcom-mcp-content-authoring API**

#### 文章元數據範本

```json
{
  "title": "[文章標題]",
  "content": "[完整 HTML 正文內容]",
  "excerpt": "[簡短 SEO 描述]",
  "status": "draft",  // 發佈前先存為 draft
  "categories": [96990383],  // Tech/Music/Film 分類 ID
  "tags": ["tag1", "tag2", "tag3"],
  "featured_media": [FEATURED_IMAGE_ID],
  "meta": {
    "internal_links": "[slug1],[slug2],[slug3]",  // 自動關聯
    "seo_title": "[SEO Title]",
    "seo_description": "[Meta Description]"
  }
}
```

#### 發佈步驟

1. **草稿存儲** → `status: "draft"`
2. **驗證預覽** → WordPress 前台確認排版
3. **最終檢查** → Schema、SEO、連結
4. **正式發佈** → `status: "publish"` + 設定發佈時間（2026-04-07 09:00 等）

---

### Phase 3：Google Search Console 索引提交

#### 批量索引提交流程

**工具**：Google Search Console API + URL Inspection 工具

#### Step 1：準備 11 篇文章的完整 URL 列表

```
https://yololab.net/archives/llm-model-comparison-2026
https://yololab.net/archives/prompt-engineering-complete-guide
https://yololab.net/archives/ai-agent-framework-comparison
https://yololab.net/archives/vector-database-selection-guide
https://yololab.net/archives/ai-coding-assistant-workflow-optimization
https://yololab.net/archives/taiwan-folk-music-90s-indie
https://yololab.net/archives/electronic-music-production-complete-guide
https://yololab.net/archives/classical-rock-art-collision
https://yololab.net/archives/documentary-film-complete-guide
https://yololab.net/archives/japanese-new-wave-cinema-revival
https://yololab.net/archives/gender-studies-film-criticism
```

#### Step 2：批量提交 Indexing API 要求

```bash
# 使用 Google Search Console Indexing API
# 每篇文章執行一次以下請求

curl -X POST https://indexing.googleapis.com/batch \
  -H "Content-Type: application/json" \
  -d '{
    "requests": [
      {
        "indexing_operation": "URL_UPDATED",
        "page_fetch_operation": "MOBILE_OPTIMIZED",
        "url": "https://yololab.net/archives/llm-model-comparison-2026"
      }
    ]
  }' \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

#### Step 3：URL Inspection 工具逐篇驗證

**預期結果**：
- ✅ `URL is on Google`（24-48 小時內）
- ✅ Coverage：Mobile-friendly + Desktop
- ✅ Valid structured data（Schema 驗證）
- ✅ User-declared canonical

#### Step 4：Sitemap 自動更新

```xml
<!-- WordPress 自動在 wp-sitemap.xml 中增加新文章 -->
<!-- 24 小時內 Google 會自動爬取 -->
```

---

## 📊 SEO 預期成效

### 發佈後 1 週（2026-04-14）

| 指標 | 目標 | 預期達成 |
|------|------|---------|
| 索引覆蓋率 | 90%+ | ✅ 11/11 篇 |
| Mobile 友善 | 100% | ✅ 已驗證 |
| Core Web Vitals | All Green | ✅ LCP <2.5s |
| 平均排名位置 | Top 20 | ⏳ 2-4 週後 |

### 發佈後 30 天（2026-05-03）

| 指標 | 目標 | 預期 |
|------|------|------|
| 有機搜尋曝光 | 2,000+ | ⏳ |
| 點擊率 | 50+ 次 | ⏳ |
| 平均排名 | Top 10（部分 KW） | ⏳ |
| 內部點擊率 | 30%+ | ⏳ |

---

## 🔧 發佈檢查清單 — 每篇文章

### 技術檢查
- [ ] W3C HTML 驗證通過（無錯誤）
- [ ] 頁面加載速度 < 3 秒
- [ ] 行動版排版正確
- [ ] 所有外部連結有效（無 404）
- [ ] 內部連結錨文本自然

### SEO 檢查
- [ ] Target KW 在 Title + Meta + H2 中出現
- [ ] Internal Links 已自動關聯（via meta.internal_links）
- [ ] Featured Image 已設定 + Alt text 補充
- [ ] Schema Markup 驗證通過（https://schema.org/validator）
- [ ] Open Graph 標籤補充（og:title, og:image, og:description）

### 內容檢查
- [ ] 無明顯 AI 痕跡（AI 語言移除 ≥ 70%）
- [ ] 標點符號、繁簡體一致
- [ ] 段落長度合理（不超過 3 行）
- [ ] 有 TL;DR、引言、結論

### 發佈檢查
- [ ] 分類已設定（Music / Film / Tech）
- [ ] Tags 已添加（3-5 個）
- [ ] Featured Status 設定
- [ ] 發佈時間已排程（避免重複時間）
- [ ] 發佈前預覽檢查完成

---

## 📈 監控計畫

### 發佈後 24 小時

```bash
# 檢查 Google Search Console
1. URL Inspection Tool → 確認 Indexed
2. Performance Report → 曝光數、點擊數
3. Coverage Report → 新增文章已覆蓋
```

### 發佈後 7 天

```bash
# 檢查關鍵詞排名
1. Google Search Console → 目標 KW 平均排名
2. GSC Coverage → 索引覆蓋率 90%+
3. 內部連結效果 → 支柱頁的引薦流量
```

### 發佈後 30 天

```bash
# 生成 SEO 成效報告
1. 有機搜尋流量增長
2. 目標 KW 排名進展
3. 支柱頁聚集效果評估
4. Top 3 表現最佳文章分析
```

---

## 🎯 後續行動

**當所有 11 篇文章發佈完成（預計 2026-04-18）：**

1. ✅ 生成 SEO 成效基線報告
2. ✅ 開始 Unit 3.2（頁面速度優化 + Core Web Vitals）
3. ✅ 準備 Unit 3.3（監控儀表板）

---

## 💡 注意事項

### 發佈間距
- **避免**：同日發佈多篇文章（會稀釋爬蟲預算）
- **推薦**：每日 1-2 篇（間隔 24 小時以上）

### Google 索引加速
- WordPress Sitemap XML 自動更新
- Indexing API 手動加速（可選）
- Search Console 手動提交（保險做法）

### 內部連結自動化
- 所有文章已預先規劃內部連結
- wpcom-mcp-content-authoring `meta.internal_links` 會自動關聯
- 無需手動在編輯器中添加連結

---

**準備好執行發佈計畫嗎？**
