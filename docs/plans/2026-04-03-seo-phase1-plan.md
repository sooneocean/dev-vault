# SEO Phase 1 優化計畫：yololab.net
## 2026-04-03 ~ 2026-04-17（2-3 週快速版）

---

## 診斷概要

**網站現況分析：**
- 總流量：1 月 4-6K 日瀏覽 → 現在 800-1K 日瀏覽（掉流量 82%+）
- 文章總量：1,695 篇（2023-2025）
- TOP 50 文章平均瀏覽：4-35 次（長尾嚴重）
- 主要流量來源：Search Engines（極低）

**根本問題：**
- ⚠️ 大量文章零瀏覽（SEO 蛻變沒有起效）
- ⚠️ Title 標籤缺乏關鍵詞優化
- ⚠️ Meta Description 現況不明
- ⚠️ **內部連結網絡完全缺失**（1,695 篇文章孤立）
- ⚠️ Schema markup 缺失（NewsArticle、MusicReview、Review 類型）
- ⚠️ 分類頁面無聚集策略（支柱頁 + 從屬內容未建立）

---

## 執行計畫架構

### Week 1：快速診斷 + TOP 50 標題/Meta/基礎 Schema 優化

#### Unit 1.1：TOP 50 文章診斷與優化清單
- **Goal**：分析 TOP 50 文章的 SEO 缺陷，生成具體優化清單
- **Effort**：4-6 小時
- **Output**：Excel 清單（50 篇文章，含 Title 字數、Meta、焦點關鍵詞、密度、內連數）
- **Dependencies**：無

#### Unit 1.2：基礎 Schema Markup 佈署（NewsArticle + Review）
- **Goal**：為所有文章自動新增 Schema markup
- **Effort**：3-4 小時
- **Output**：所有 TOP 50 文章有有效 Schema
- **Dependencies**：Unit 1.1 完成
- **Test**：Google Rich Results Test × 10 篇文章

#### Unit 1.3：分類頁面基礎優化
- **Goal**：優化 3 個主要分類頁面（音樂、電影、科技）
- **Effort**：2-3 小時
- **Output**：3 個分類頁面優化完成
- **Dependencies**：Unit 1.1 完成

---

### Week 2：分類聚集戰略 + 內部連結網絡建構

#### Unit 2.1：支柱頁 + 從屬頁聚集架構設計
- **Goal**：為每個分類建立支柱頁，定義聚集連結策略
- **Effort**：8-10 小時
- **Output**：3 個支柱頁（已發佈），每個 ≥ 50 個內部連結
- **Dependencies**：Unit 1.3 完成

#### Unit 2.2：批量內部連結佈署
- **Goal**：為 TOP 50 + 同分類文章新增內部連結
- **Effort**：12-16 小時
- **Output**：TOP 50 每篇平均 ≥ 5 個內部連結，同分類互連率 ≥ 60%
- **Dependencies**：Unit 2.1 完成
- **Test**：抽查 10 篇文章驗證連結有效性

#### Unit 2.3：分類內容缺口分析
- **Goal**：識別每個分類的內容缺口，規劃新文章
- **Effort**：4-6 小時
- **Output**：內容缺口清單（≥ 15 個新主題），優先級排序
- **Dependencies**：Unit 2.1 完成

---

### Week 3：發佈 + 監控 + 速度最佳化

#### Unit 3.1：內容發佈 + 索引提交
- **Goal**：發佈新支柱頁和聚集文章，提交到 Google 索引
- **Effort**：6-8 小時
- **Output**：20-30 篇新/更新文章已發佈並索引
- **Dependencies**：Unit 2.1 + Unit 2.3 完成
- **Test**：GSC URL inspection 驗證索引狀態

#### Unit 3.2：頁面速度最佳化 + Core Web Vitals
- **Goal**：優化頁面加載速度，改進 Core Web Vitals
- **Effort**：4-6 小時
- **Output**：Lighthouse ≥ 80，Core Web Vitals > 80% "Good"
- **Dependencies**：無（獨立進行）
- **Test**：PageSpeed Insights + Lighthouse 檢測

#### Unit 3.3：監控儀表板建構 + KPI 追蹤
- **Goal**：建立 Post-Deploy 監控系統，定義 KPI
- **Effort**：3-4 小時
- **Output**：監控儀表板已建立，首份週報告已生成
- **Dependencies**：Unit 3.1 完成

---

## Post-Deploy 監控章節

### 第 1 個月（4 月）：密集監控期

**預期情況：**
- 索引增長：新文章快速被索引
- 排名波動：可能短期下降，之後逐步上升
- 流量變化：無顯著提升（搜尋排名還未大幅改善）

**監控重點：**
1. **技術健康度**（每日檢查）
   - GSC → Coverage：確保無新的索引錯誤
   - PageSpeed Insights：Core Web Vitals 保持穩定
   - Crawl errors：< 5 個

2. **內容品質檢查**（每週 1 次）
   - 抽查 10-20 篇新發佈文章
   - 驗證內部連結有效性
   - 檢查 Schema markup 正確性

3. **流量異常警報**（即時）
   - 設置 GA4 警報：有機流量 ↓ 20% 以上
   - 設置 GSC 警報：impressions ↓ 30% 以上

### 第 2-3 個月（5-6 月）：成長驗證期

**預期情況：**
- 排名提升：TOP 50 文章應晉升 1-3 個位次
- 流量提升：有機流量應達 +30% 至 +50%
- 新排名機會：新文章開始獲得印象

**監控重點：**
1. **搜尋排名改善**（雙週檢查）
   - 追蹤前 100 關鍵詞
   - 目標：排名 < 30 的關鍵詞 ≥ 20 個

2. **流量來源分析**（週檢查）
   - 分析「新用戶」vs「回訪用戶」比例
   - 目標：新用戶占 60% 以上

3. **內容表現排名**（雙週）
   - 識別「表現超預期」的文章
   - 識別「表現低於預期」的文章

4. **競爭對手監控**（月檢查）
   - 追蹤競爭對手的關鍵詞排名
   - 規劃「反制」內容

---

## 8 週預期成果

| KPI | 基準值（Week 1） | 目標（Week 8） | 達成率 |
|-----|-----------------|-----------------|-------|
| **有機流量** | ~2,300/日 | ~3,450/日 (+50%) | > 40% |
| **索引頁面** | ~1,700 | ~3,400 (+100%) | > 100% |
| **平均排名** | 50+ | 35 以下（-30%） | > 50% |
| **點擊率** | ~0.5% | ~0.65% (+30%) | > 20% |
| **Lighthouse** | ~55 | ≥ 80 (+45%) | > 100% |

**達成 ≥ 4 項以上 = Phase 1 成功**

---

## 資源清單與工具堆棧

### 已裝插件（可直接使用）
- ✓ Yoast SEO
- ✓ Google Site Kit
- ✓ Jetpack Boost
- ✓ Page Optimize
- ✓ SpeedyCache
- ✓ Imagify
- ✓ Table of Contents Plus
- ✓ Advanced Custom Fields

### 外部工具（免費層足夠）
- Google Search Console
- Google Analytics 4
- Google PageSpeed Insights
- Google Data Studio
- Google Keyword Planner

---

## Status：Ready to Execute
