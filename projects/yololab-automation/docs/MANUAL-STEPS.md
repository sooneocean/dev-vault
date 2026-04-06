---
title: 手動操作清單
type: project
tags: [project, active]
created: 2026-04-03
updated: 2026-04-03
status: active
maturity: growing
domain: knowledge-management
summary: ""
---

# 手動操作清單

**目的**：提供需要手動干預的步驟說明
**最後更新**：2026-03-31
**完成時間**：5-10 分鐘

---

## 1️⃣ 停用衝突外掛

由於 WordPress.com API 限制，必須手動停用這兩個外掛。

### 步驟 A：停用 SpeedyCache 1.3.8

1. **進入外掛管理頁面**
   ```
   URL: https://yololab.net/wp-admin/plugins.php
   ```

2. **找到 SpeedyCache**
   - 在頁面上查找「SpeedyCache」
   - 或使用瀏覽器查找功能（Ctrl+F 或 Cmd+F）搜索「SpeedyCache」

3. **停用外掛**
   - 找到 SpeedyCache 所在的行
   - 點擊下面的「停用」連結（或「Deactivate」）
   - 等待頁面重新整理（通常 2-5 秒）

4. **驗證停用**
   - SpeedyCache 應移至「非活動的外掛」部分
   - 應顯示「啟用」連結而非「停用」

**截圖參考**：
```
外掛頁面應顯示：
┌─────────────────────────────────┐
│ 活躍外掛 (23)                     │
├─────────────────────────────────┤
│ Jetpack                          │
│ Imagify Image Optimizer          │
│ [其他外掛...]                    │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│ 非活躍外掛                        │
├─────────────────────────────────┤
│ SpeedyCache 1.3.8                │
│ [啟用] | [刪除]                   │
│                                 │
│ Page Optimize 0.6.2              │
│ [啟用] | [刪除]                   │
└─────────────────────────────────┘
```

### 步驟 B：停用 Page Optimize 0.6.2

重複步驟 A，但改為搜索「Page Optimize」

1. 進入 https://yololab.net/wp-admin/plugins.php
2. 搜索「Page Optimize」
3. 點擊「停用」
4. 等待頁面重新整理
5. 驗證外掛移至「非活躍外掛」

---

## 2️⃣ 驗證其他外掛狀態

確保關鍵的優化外掛仍然啟用：

### 檢查清單

| 外掛名稱 | 狀態 | 檢查 |
|--------|------|------|
| Jetpack Boost | ✅ Active | [ ] |
| Imagify Image Optimizer | ✅ Active | [ ] |
| WebP Converter for Media | ✅ Active | [ ] |
| Yoast SEO | ✅ Active | [ ] |
| Jetpack | ✅ Active | [ ] |
| Google Site Kit | ✅ Active | [ ] |

### 驗證步驟

1. 進入 https://yololab.net/wp-admin/plugins.php
2. 在「活躍外掛」部分查找上述每個外掛
3. 如果任何外掛顯示為非活躍，點擊「啟用」
4. 截圖或記錄驗證時間

---

## 3️⃣ 檢查頁面渲染

驗證自動更新的 ABOUT 頁面在瀏覽器中正確顯示。

### 步驟

1. **訪問 ABOUT 頁面**
   ```
   URL: https://yololab.net/about
   ```

2. **檢查視覺元素**
   - [ ] 頁頂 hero section 有背景色和標題「YOLO LAB 的故事」
   - [ ] 副標題「科技與媒體數據實驗室」存在
   - [ ] 「我們的使命」部分清晰可見
   - [ ] 五欄配置顯示（音樂、電影、科技、生活、活動）
   - [ ] 底部 CTA 區塊有三個按鈕（Facebook、Instagram、聯絡我們）

3. **檢查功能**
   - [ ] 頁面加載時間 < 3 秒
   - [ ] 所有連結可點擊（Facebook、Instagram、郵件）
   - [ ] 頁面響應式設計（用手機查看也清晰）
   - [ ] 無 JavaScript 錯誤（打開 DevTools 檢查 Console）

4. **記錄截圖**
   - 桌面版完整頁面
   - 手機版完整頁面
   - 保存到 `.logs/` 目錄

---

## 4️⃣ 記錄基準性能指標

在優化後 48-72 小時之前記錄當前性能，作為對比基準。

### 步驟 1：Google PageSpeed Insights

1. 進入 https://pagespeed.web.dev/
2. 輸入 URL：`https://yololab.net`
3. 點擊「分析」
4. **記錄這些分數**：

```
📊 桌面版結果
Date: ____________
Time: ____________

Performance Score: ____/100
Accessibility Score: ____/100
Best Practices Score: ____/100
SEO Score: ____/100

Core Web Vitals:
- Largest Contentful Paint (LCP): ____ms
- Interaction to Next Paint (INP): ____ms
- Cumulative Layout Shift (CLS): ____.___

Total Blocking Time: ____ms
First Contentful Paint: ____ms
Time to Interactive: ____s
```

5. 對「移動版」重複以上步驟
6. **保存結果**到 `.logs/baseline-performance-[date].txt`

### 步驟 2：Jetpack Analytics

1. 進入 https://yololab.net/wp-admin/admin.php?page=jetpack
2. 點擊「統計」或「Analytics」
3. **記錄最近 7 天的數據**：

```
📊 Jetpack Analytics
Date Range: 最近 7 天
Recording Date: ____________

Total Views: ______
Total Visitors: ______
Average Views Per Day: ______
Most Popular Post: ________________

Top Traffic Source: ________________
Bounce Rate: ____%
Average Time on Site: ____m ____s
```

4. 保存截圖

### 步驟 3：核心 Web 指標歷史

1. 進入 Google Search Console：https://search.google.com/search-console
2. 選擇 yololab.net
3. 導航到「Core Web Vitals」
4. **記錄最近 28 天的整體狀態**：

```
📊 Core Web Vitals 報告
Period: 最近 28 天
Recording Date: ____________

LCP (Largest Contentful Paint):
- Good: ___%
- Needs Improvement: ___%
- Poor: ___%

INP (Interaction to Next Paint):
- Good: ___%
- Needs Improvement: ___%
- Poor: ___%

CLS (Cumulative Layout Shift):
- Good: ___%
- Needs Improvement: ___%
- Poor: ___%
```

---

## 5️⃣ 後續驗證（48-72 小時後）

優化需要時間生效，特別是 CDN 快取更新。

### 時間表

| 操作 | 生效時間 | 驗證方法 |
|-----|---------|---------|
| Gzip 啟用 | 立即 | curl 檢查 Content-Encoding 頭 |
| 快取清除 | 2-4 小時 | 檢查新內容（ABOUT 頁面）可見 |
| CDN 更新 | 48-72 小時 | PageSpeed Insights 分數提升 |
| 搜索引擎索引 | 24-72 小時 | Google Search Console 反映新內容 |

### 驗證清單

**24 小時後**：
- [ ] 訪問 ABOUT 頁面，確認新內容顯示
- [ ] 在 Google 搜索中查找「yololab.net about」，確認索引更新
- [ ] Jetpack Analytics 無異常流量波動

**48-72 小時後**：
- [ ] 在 PageSpeed Insights 重新測試（應有提升）
- [ ] 比較當前分數與基準線
- [ ] 計算改進百分比

**一週後**：
- [ ] 完整 Lighthouse 審計
- [ ] Core Web Vitals 趨勢分析
- [ ] 評估是否達到優化目標

---

## 🆘 常見問題

### Q：停用外掛後頁面變白或無法加載？

**A：** 這是常見的暫時現象。解決方法：

1. 硬刷新頁面（Ctrl+Shift+R 或 Cmd+Shift+R）
2. 清除瀏覽器快取
3. 等待 1-2 分鐘
4. 再次訪問首頁
5. 如問題持續，在 wp-admin/plugins.php 重新啟用該外掛

### Q：ABOUT 頁面內容不顯示？

**A：** 可能原因和解決方案：

1. **頁面尚未發佈**：進入 wp-admin/pages/3，檢查狀態是否為「發佈」
2. **頁面設定為私密**：更改可見性為「公開」
3. **佈景主題不支持**：嘗試更換為標準佈景主題（Twenty-Twenty-Four）
4. **暫存問題**：清除 Jetpack 快取（wp-admin → Jetpack → 清除快取）

### Q：多久後應該看到性能提升？

**A：** 分階段改進：

- **立即**（1-2 小時）：Gzip 啟用立即減少傳輸大小 40-60%
- **短期**（24 小時）：CDN 快取開始更新，頁面加載稍快
- **中期**（48-72 小時）：完整 CDN 快取更新，PageSpeed 分數可提升 10-20 分
- **長期**（1-2 週）：搜索引擎重新索引，可能帶來流量提升

### Q：如果我不小心刪除了外掛怎麼辦？

**A：** 別擔心，外掛刪除不會刪除配置。解決步驟：

1. 進入 wp-admin/plugins.php
2. 點擊「添加新外掛」
3. 搜索外掛名稱（例：「Jetpack」）
4. 點擊「安裝現在」
5. 點擊「啟用」
6. 配置應自動恢復

---

## 📝 完成簽署

完成所有手動步驟後，填寫以下確認：

```
✅ 手動操作完成確認

姓名或識別碼：_____________________
完成日期：_____________________
完成時間：_____________________

已完成步驟：
[ ] 1️⃣ 停用 SpeedyCache
[ ] 2️⃣ 停用 Page Optimize
[ ] 3️⃣ 驗證其他外掛狀態
[ ] 4️⃣ 檢查 ABOUT 頁面渲染
[ ] 5️⃣ 記錄基準性能指標

簽名：_____________________
```

---

## 📞 需要幫助？

- 詳細 API 文檔：見 `docs/API-REFERENCE.md`
- 常見問題排查：見 `docs/TROUBLESHOOTING.md`
- 執行日誌：見 `.logs/EXECUTION-LOG.md`
- 聯繫管理者：sooneocean
