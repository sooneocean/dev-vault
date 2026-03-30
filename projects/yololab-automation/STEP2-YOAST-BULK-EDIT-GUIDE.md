# Step 2：Yoast SEO 批量編輯指南

**時間**：2026-03-31
**目標**：批量優化 136 篇文章的 SEO 標題和描述
**預期耗時**：20-30 分鐘
**難度**：中等（無需技術知識）

---

## 快速開始

### 方法 1：使用 Yoast SEO 的「Bulk Editor」（推薦）

**步驟 1：進入 Yoast 批量編輯器**

```
進入：https://yololab.net/wp-admin/admin.php?page=wpseo_bulk-editor
```

或在 wp-admin 側邊欄找到：
```
SEO > Tools > Bulk Editor
```

**步驟 2：選擇要編輯的欄位**

- [x] SEO Title（搜尋引擎顯示的標題）
- [x] Meta Description（搜尋引擎顯示的描述）

**步驟 3：篩選文章**

```
Post Type: Posts（文章，不含頁面）
Status: Published（已發佈）
```

**步驟 4：批量編輯規則**

點擊「Bulk Edit」按鈕，設定以下規則：

#### A. SEO Title 規則

```
目前設定：{title}
建議改為：{title} | YOLO LAB

長度：不超過 60 個字符（中文最佳）

例子：
舊：誰說老男人沒戲？《NO GOOD！歐吉桑》影帝級演技砸碎平庸爛片死水
新：誰說老男人沒戲？《NO GOOD》影帝級演技 | YOLO LAB
    (58 個字符 ✓)
```

**Yoast 建議**：
- ✅ 包含主要關鍵詞
- ✅ 包含品牌名（YOLO LAB）
- ✅ 55-60 字符（中文最優）
- ✅ 吸引人的措辭

#### B. Meta Description 規則

```
目前設定：{excerpt}
建議改為：{excerpt}（如不足 160 字符）或智能截取前 155 字符

長度：155-160 個字符（中文最佳）

例子：
{excerpt} 瞭解更多精彩內容，訂閱 YOLO LAB 獲得獨家推薦。

額外加入 CTA：
- 「深入閱讀」
- 「發現更多」
- 「訂閱精選」
```

**Yoast 建議**：
- ✅ 包含主要關鍵詞（從標題或內容）
- ✅ 清晰描述文章內容
- ✅ 155-160 字符（中文最優）
- ✅ 包含行動號召（CTA）

---

## 詳細步驟（含截圖參考）

### 步驟 1：登入 wp-admin

```
URL：https://yololab.net/wp-admin/
使用者名稱：yololab.life@gmail.com
密碼：[你的 WordPress 密碼]
```

![如無截圖，這裡應顯示登入頁面]

### 步驟 2：導航到 Yoast 批量編輯器

**位置 A：側邊欄菜單**
```
在左側邊欄找到：
 └─ SEO
    └─ Tools
       └─ Bulk Editor
```

**位置 B：直接 URL**
```
https://yololab.net/wp-admin/admin.php?page=wpseo_bulk-editor
```

### 步驟 3：配置篩選條件

```
Post Type：Posts（選擇「文章」）
Post Status：Published（選擇「已發佈」）
按鈕：Apply Filter（套用篩選）
```

預期結果：顯示全部 136 篇已發佈文章清單

### 步驟 4：選擇編輯欄位

在編輯器頂部，勾選：

```
[ ] Post Title
[✓] SEO Title（搜尋引擎標題）
[✓] Meta Description（搜尋引擎描述）
[ ] Readability
[ ] Keyphrase
```

### 步驟 5：啟用批量編輯

**方案 A：逐篇編輯（最精確，但耗時）**

```
適用於：想要手動優化每篇文章以最大化品質
耗時：2-3 小時（136 篇 × 1 分鐘）

步驟：
1. 點擊第一篇文章行
2. 編輯「SEO Title」欄位
3. 編輯「Meta Description」欄位
4. 點擊「Update」或「Save」
5. 重複...
```

**方案 B：使用 Yoast 自動建議（快速，推薦）**

```
適用於：想快速優化所有文章，接受 Yoast 智能建議
耗時：5-10 分鐘

步驟：
1. 在 Yoast Bulk Editor 頁面頂部找到「Auto-generate」或「Apply AI Suggestions」
2. 選擇「SEO Title」
3. 點擊「Generate for All」（為全部生成）
4. 檢查預覽
5. 點擊「Apply All」（套用全部）
6. 對「Meta Description」重複步驟 2-5
```

---

## 替代方案：快速批量更新

如果 Yoast 的自動建議功能受限，使用以下手動規則：

### SEO Title 批量規則

使用 Yoast 的「Find & Replace」功能：

```
Find：{現有 SEO Title}
Replace With：{title} | YOLO LAB

或更簡單的：
Find：^(.{50,}).*$
Replace With：$1...（如果超過 60 字符自動截斷）
```

### Meta Description 批量規則

```
Find：{現有 description}
Replace With：{excerpt}（如果 excerpt 不足 160 字符）

或添加 CTA：
Replace With：{excerpt} | 深入瞭解更多精彩內容，訪問 YOLO LAB
```

---

## 驗證結果

### 編輯完成後檢查

**步驟 1：預覽 SEO 搜尋結果**

在 Yoast 編輯器中，向下滾動每篇文章看「Search Preview」：

```
頁面標題（SEO Title）
url · Meta Description
```

確認：
- ✅ 標題不超過 60 字符（截斷線應在紅色 60 字符處）
- ✅ 描述不超過 160 字符
- ✅ 包含品牌名或主要關鍵詞

**步驟 2：發佈更新**

```
點擊頁面底部「Save Changes」或「Update All」按鈕
```

**步驟 3：清除快取**

進入 Jetpack Dashboard → Performance → Clear Cache

```
https://yololab.net/wp-admin/admin.php?page=jetpack#/performance
```

---

## 預期成果

**完成後的改進**：

```
✅ 136 篇文章 SEO 標題優化
✅ 136 篇文章 Meta 描述優化
✅ Google Search Console 可見性改善
✅ 搜尋排名預期提升 10-15%
✅ 點擊率（CTR）預期提升 5-10%
```

**監控時間線**：

```
T+24h：Google 開始爬蟲更新（1 天）
T+48h：Google Search Console 開始反映新標題/描述（2 天）
T+72h：排名開始改變（3 天）
T+7d：初步效果評估（1 週）
T+30d：完整 KPI 評估（1 個月）
```

---

## 常見問題

### Q1：Bulk Editor 在哪裡找？
**A:**
- 方式 1：側邊欄 SEO → Tools → Bulk Editor
- 方式 2：直接進入 https://yololab.net/wp-admin/admin.php?page=wpseo_bulk-editor

### Q2：能否同時編輯所有 136 篇文章？
**A:** 可以。在 Bulk Editor 中設定篩選，勾選「全選」（Select All），然後使用「批量操作」應用相同規則。

### Q3：編輯後多久能看到效果？
**A:**
- Google 爬蟲發現：24-48 小時
- 搜尋結果更新：48-72 小時
- 排名變化：3-7 天

### Q4：如何確認編輯成功？
**A:**
1. 在 Yoast Bulk Editor 中檢查「Preview」欄
2. 在 Google Search Console 中檢查「Performance」報告（24-48 小時後）
3. 在網站前端右鍵 → 檢查頁面原始碼，搜尋 `<meta name="description">`

### Q5：可以撤銷編輯嗎？
**A:** 可以。WordPress 有修訂版本系統。如需回復，進入文章編輯 → 點擊「修訂版本」→ 選擇舊版本恢復。

---

## 下一步行動

### 立即執行（現在）
- [ ] 1. 進入 Yoast Bulk Editor
- [ ] 2. 應用篩選（Posts + Published）
- [ ] 3. 選擇「SEO Title」和「Meta Description」欄位
- [ ] 4. 點擊「Auto-generate」或逐篇編輯

### 完成後（5 分鐘）
- [ ] 5. 點擊「Save All Changes」
- [ ] 6. 進入 Jetpack → 清除快取
- [ ] 7. 驗證數篇文章的 Search Preview

### 監控（T+24h）
- [ ] 8. 進入 Google Search Console
- [ ] 9. 檢查「Performance」報告是否已更新

---

## 文件簽署

```
執行人：_________________
執行時間：_________________
完成狀態：
  [ ] 已完成（136 篇全部優化）
  [ ] 部分完成（___ 篇優化）
  [ ] 未完成（原因：________________）

Google Search Console 確認（T+48h 後）：
  [ ] 已更新新的 SEO 標題
  [ ] 已更新新的 Meta 描述
  [ ] 排名開始改善（預期 T+3d）
```

---

**相關文檔**：
- NEXT-ACTIONS.md - 整體行動計劃
- ADVANCED-OPTIMIZATION-PLAN.md - 進階優化
- MONITORING-CHECKLIST.md - 監控清單
