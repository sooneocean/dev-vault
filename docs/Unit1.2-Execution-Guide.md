# Unit 1.2 執行指南：基礎 Schema Markup 佈署
## 可操作步驟細節 | 2026-04-04

---

## 前置檢查清單（5 分鐘）

在開始前，請確認以下項目：

- [ ] **WordPress 後台訪問**
  - 登入 https://yololab.net/wp-admin
  - 確認已進入管理員帳戶

- [ ] **Yoast SEO Premium 已安裝啟用**
  - 檢查：WordPress 後台左側邊欄 → Yoast SEO
  - 確認版本（應為 Premium）
  - 查看 License 狀態（應為 Active）

- [ ] **Google Rich Results Test 訪問**
  - 打開 https://search.google.com/test/rich-results
  - 確認可以正常訪問

- [ ] **驗證清單文件**
  - 已下載：`Unit1.2-Schema-Validation-Checklist.csv`
  - 已下載：本執行指南

---

## 第 1 階段：Yoast SEO Schema 配置（30 分鐘）

### Step 1.1：訪問 Yoast SEO Schema 設定

**路徑：**
```
WordPress 後台
→ Yoast SEO
→ Tools（工具）
→ Schema
```

或者直接訪問：
```
https://yololab.net/wp-admin/admin.php?page=wpseo_tools
（選擇 Schema 標籤）
```

**期望看到的畫面：**
- 左側：Schema 類型列表（Article, BlogPosting, NewsArticle, Review 等）
- 中央：當前配置詳情
- 右側：配置選項

### Step 1.2：檢查當前預設 Schema 設定

**檢查項目：**
1. **Default Article Type**（默認文章類型）
   - 應為：NewsArticle 或 BlogPosting
   - 如果是 BlogPosting，建議改為 NewsArticle

2. **Publisher/Organization Logo**
   - 應已設定 YOLO LAB logo
   - 確認 URL 可訪問

3. **Author Display**
   - 應為 Organization（而非 Person）
   - 名稱：YOLO LAB

### Step 1.3：配置分類特定 Schema（關鍵步驟）

#### 配置 1：音樂分類 Schema

**進入位置：**
- WordPress 後台 → Yoast SEO → Tools → Schema
- 或 Yoast SEO → Integrations

**具體步驟：**

1. **找到或新增 Category Rule**
   - 尋找「Categories」或「Taxonomies」部分
   - 選擇 Music 分類（或相應分類 ID）

2. **設定 Schema Type 為 NewsArticle**
   ```
   Category: 音樂 (ID: 96987488, 96987489, 96987631, 96987492, 96990388, 96990390, 96990384)
   → Schema Type: NewsArticle ✓
   → Add Review Schema: ✓（啟用）
   ```

3. **啟用 MusicRecording Schema**
   - 查找 Schema Section：MusicRecording
   - 設定 byArtist: [自動提取或手動輸入]
   - 設定 albumName: [從文章標題提取]

4. **配置 Review Rating（音樂樂評必須）**
   ```
   Review Settings:
   → Enable Review Schema: ✓
   → Rating Scale: 1-10
   → Default Rating: [留空，讓編輯手動填入]
   ```

**測試驗證：**
- 編輯一篇音樂文章（如 Yohee ID: 30121）
- 進入文章編輯頁面
- 查看右側 Yoast SEO Panel → Schema 部分
- 應該看到 NewsArticle + Review 的組合
- **不應有紅色警告**

#### 配置 2：電影分類 Schema

**步驟與音樂類似，但調整為：**

```
Category: 電影 (ID: 96990383, 96990387)
→ Schema Type: NewsArticle ✓
→ Add Review Schema: ✓
→ Add Movie Schema: ✓
```

**配置 Movie Schema：**
- Movie Name: [從文章標題提取]
- Director: [手動或自動]
- Actor: [可選]
- Rating: [從 Review 引用]

**測試驗證：**
- 編輯 NO GOOD 電影文章 (ID: 34899)
- 確認 Yoast Panel 顯示 NewsArticle + Movie + Review
- 無紅色警告

#### 配置 3：科技分類 Schema

```
Category: 科技 (ID: 96990096, 96987489, 96990120, 96990391)
→ Schema Type: NewsArticle ✓
→ Add FAQ Schema: ⚠️（僅針對有 Q&A 段落的文章）
```

**FAQ Schema 配置（可選）：**
- 僅用於有「常見問題」部分的文章
- Yoast SEO 會自動檢測 H3 標題作為問題
- 確保每個 Q&A 對配置完整

### Step 1.4：保存與驗證配置

**保存步驟：**
1. 完成所有配置後，點擊頁面最下方的「Save」或「Update」按鈕
2. 等待「Successfully saved」提示

**驗證配置已生效：**
1. 打開任一已發佈的音樂文章（如 ID: 30121）
2. 進入「編輯」模式
3. 向下滾動，查看右側 Yoast SEO 面板
4. 確認「Schema」部分顯示：
   ```
   ✓ NewsArticle schema
   ✓ Review schema
   ✓ MusicRecording schema
   （或 Movie schema for films）
   ```
5. **無紅色警告** = 配置成功

---

## 第 2 階段：Schema 驗證（1-1.5 小時）

### Step 2.1：準備驗證清單

**使用文件：** `Unit1.2-Schema-Validation-Checklist.csv`

**從清單中選擇要驗證的文章：**

建議按分類驗證：
- **音樂樂評**（5 篇）：30121, 34942, 34935, 34893, 34816
- **電影評測**（5 篇）：34899, 34831, 34784, 34761, 34752
- **科技分析**（5 篇）：34881, 34853, 34666, 34647, 34635

### Step 2.2：Google Rich Results Test 驗證流程

**詳細步驟：**

1. **打開 Google Rich Results Test**
   - URL：https://search.google.com/test/rich-results
   - （需要 Google 帳戶登入，但一般 Google 帳戶無需驗證）

2. **輸入第一篇文章 URL**
   - 在文本框中輸入：`https://yololab.net/archives/yohee-if-i-were-a-player-diss-track-review`
   - 或複製文章完整 URL

3. **點擊「測試 URL」（Test URL）按鈕**
   - 等待 5-10 秒，工具將抓取並分析頁面

4. **檢查結果**

   **期望結果 1：✅ Valid**
   ```
   Valid Rich Results
   ├─ Article
   │  ├─ headline ✓
   │  ├─ image ✓
   │  ├─ datePublished ✓
   │  └─ author ✓
   └─ Review (if applicable)
      ├─ reviewRating ✓
      └─ ratingValue ✓
   ```
   → **記錄為「✅ Valid」**

   **期望結果 2：⚠️ Warnings**
   ```
   Article schema found, but with warnings:
   ├─ ⚠️ Missing recommended property: author
   └─ ⚠️ Missing optional field: creator
   ```
   → **記錄問題，優先級：P2**

   **期望結果 3：❌ Errors**
   ```
   Article schema has errors:
   ├─ ❌ Missing required property: headline
   └─ ❌ Invalid image URL (404)
   ```
   → **記錄問題，優先級：P0（需立即修正）**

5. **記錄結果到 CSV**
   - 在 `Unit1.2-Schema-Validation-Checklist.csv` 中更新該文章行
   - 填入：
     - **驗證狀態**：已驗證
     - **Rich Results Test結果**：✅/⚠️/❌
     - **錯誤說明**：具體錯誤信息
     - **修正優先級**：P0/P1/P2

6. **逐篇驗證所有 15 篇代表性文章**
   - 預計每篇 3-5 分鐘
   - 總時間：45-75 分鐘

### Step 2.3：Google Search Console 驗證（10 分鐘）

**進入 GSC：**
1. 訪問 https://search.google.com/search-console
2. 選擇 yololab.net 屬性
3. 進入「Enhancements」（增強項目）部分

**查看 Rich Results 報告：**
```
Enhancements
├─ Rich Results
│  ├─ Valid items: [數字]
│  ├─ Warning items: [數字]
│  └─ Error items: [數字]
└─ Breadcrumbs
```

**記錄初始狀態：**
- 記錄當前 Error 和 Warning 數量
- 本次部署完成後，應無新增 Error

### Step 2.4：Lighthouse 驗證（5-10 分鐘）

**測試 5 篇文章的 Lighthouse 報告：**

1. 在 Chrome 中打開文章頁面
2. 按 F12 開啟 DevTools
3. 進入「Lighthouse」標籤
4. 點擊「Analyze page load」

**檢查 Schema 相關項目：**
```
SEO
├─ ✓ Structured data is valid
│  └─ [應為綠色勾選]
└─ ⚠️ [任何警告信息]
```

**記錄結果：**
- 應有「✓ Structured data is valid」
- 無 Schema 相關警告

---

## 第 3 階段：問題修正（30-45 分鐘）

### Step 3.1：問題分類與優先級

根據驗證結果，將問題分為三類：

#### P0（關鍵 - 必須修正）
- Missing required fields（如 headline, image）
- Invalid URL format
- Schema type completely missing

#### P1（重要）
- Missing optional fields（如 author, dateModified）
- Missing ratingValue（对于 Review 类型）
- Image URL 返回 404

#### P2（低優先級）
- Recommendations（最佳實踐建議）
- Deprecation warnings
- 可選欄位缺失

### Step 3.2：修正策略

#### 修正方法 1：通過 Yoast SEO Panel（推薦）

**對於每篇有 P0 或 P1 錯誤的文章：**

1. 進入文章編輯頁面（WordPress 後台 → 文章 → 編輯）
2. 向下滾動到「Yoast SEO」面板（右側）
3. 點擊「Schema」標籤
4. 查看紅色警告（❌）或黃色警告（⚠️）

**示例 - 修正缺失的 ratingValue：**
```
[Yoast Panel]
Schema Type: Review
├─ reviewRating
│  ├─ ratingValue: [空白或無效] ← 需要填入
│  └─ bestRating: 10 ✓
```

**操作：**
1. 在 ratingValue 欄位輸入評分（如 8.5）
2. 點擊「Save」或「Update Post」
3. 重新驗證該文章

#### 修正方法 2：手動編輯 HTML Schema（進階）

如果 Yoast Panel 無法修正，可以手動編輯：

1. 進入文章編輯頁面
2. 切換到「HTML 編輯器」模式（而非 Visual）
3. 尋找 `<script type="application/ld+json">` 標籤
4. 編輯 JSON，添加缺失的欄位

**示例：**
```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": ["NewsArticle", "Review"],
  "headline": "Yohee 又熙《如果我是個玩咖》樂評",
  "reviewRating": {
    "@type": "Rating",
    "ratingValue": 8.5,  ← 添加此行
    "bestRating": 10
  }
}
</script>
```

5. 保存文章
6. 重新驗證

### Step 3.3：修正驗證迴圈

**對於每篇有問題的文章：**

1. **第一次修正**
   - 應用上述修正方法
   - 保存文章
   - **等待 5-10 分鐘**（讓 Google 重新爬蟲該頁面）

2. **重新驗證**
   - 在 Google Rich Results Test 中重新測試該 URL
   - 檢查問題是否解決

3. **更新 CSV 記錄**
   - 修改「驗證狀態」為「已修正」或「待重驗」
   - 記錄修正日期

4. **目標：80% 以上文章通過驗證**
   - 至少 12/15 文章應為 ✅ Valid
   - 剩餘可接受 ⚠️ Warnings

---

## 第 4 階段：最終驗證與報告（15 分鐘）

### Step 4.1：最終統計

**彙總所有驗證結果：**

| 結果 | 數量 | 百分比 |
|------|------|--------|
| ✅ Valid | [填入] | [填入]% |
| ⚠️ Warnings | [填入] | [填入]% |
| ❌ Errors | [填入] | [填入]% |
| **總計** | 15 | 100% |

**預期數值：**
- ✅ Valid: ≥ 12 (80%+) ✓ 成功
- ⚠️ Warnings: ≤ 3 (20%-)  ✓ 可接受
- ❌ Errors: 0 (0%) ✓ 必須

### Step 4.2：生成 Unit 1.2 完成報告

**報告內容：**

```markdown
# Unit 1.2 完成報告 - Schema Markup 佈署
## 執行日期：2026-04-04

### 執行摘要
- **目標達成率**：[填入]%
- **驗證文章數**：15 篇
- **有效 Schema 文章**：[數字] 篇
- **修正耗時**：[填入] 小時

### Schema 配置完成項目
- [x] Yoast SEO NewsArticle 全局配置
- [x] 音樂分類 MusicRecording Schema 配置
- [x] 電影分類 Movie + Review Schema 配置
- [x] 科技分類 NewsArticle Schema 配置

### 驗證結果統計
- ✅ Valid: [數字] 篇 ([百分比]%)
- ⚠️ Warnings: [數字] 篇 ([百分比]%)
- ❌ Errors: [數字] 篇 ([百分比]%)

### 發現的主要問題
1. [問題 1]
2. [問題 2]
3. ...

### 修正執行情況
- P0 問題修正率：[數字]%
- P1 問題修正率：[數字]%
- P2 問題修正率：[數字]%

### Go/No-Go 決策
- [ ] **GO**：達成 ≥ 80% 有效率，可進行 Unit 1.3
- [ ] **NO-GO**：未達成目標，需要追加修正

### 下一步建議
1. [建議 1]
2. [建議 2]
```

### Step 4.3：檔案交付清單

**完成後交付以下文件：**
- ✅ `Unit1.2-Schema-Deployment-Plan.md`（已生成）
- ✅ `Unit1.2-Execution-Guide.md`（本文件）
- ✅ `Unit1.2-Schema-Validation-Checklist.csv`（驗證結果）
- ✅ `Unit1.2-Completion-Report.md`（完成報告）

---

## 常見問題 & 故障排除

### Q1：Yoast SEO Schema 配置後，文章仍無 Schema

**原因：**
- Yoast 快取未清除
- 文章未重新保存
- 分類規則未正確應用

**解決方案：**
1. WordPress 後台 → Yoast SEO → Tools → File Cleanup
2. 清除所有快取
3. 重新編輯並保存任意文章
4. 等待 5-10 分鐘，再驗證

### Q2：Google Rich Results Test 顯示「Image URL 無效」

**原因：**
- 特色圖片 URL 返回 404
- 圖片被刪除或路徑變更
- CDN 延遲

**解決方案：**
1. 進入文章編輯，更新特色圖片
2. 檢查圖片 URL 是否可直接訪問
3. 嘗試重新上傳圖片
4. 保存並等待 10-15 分鐘

### Q3：Yoast Panel 顯示紅色警告「Missing ratingValue」

**原因：**
- Review 類型缺少評分欄位
- 評分欄位為空

**解決方案：**
1. 在 Yoast Schema 面板找到 Review 部分
2. 填入 ratingValue（如 8, 8.5, 9 等）
3. 確認 bestRating 為 10
4. 保存文章

### Q4：如何批量修正所有文章的 Schema

**選項 1：批量編輯（Yoast Bulk Editor）**
```
Yoast SEO → Tools → Bulk Editor
選擇要編輯的文章
更新 Schema 相關欄位
保存
```

**選項 2：使用 WordPress REST API（進階）**
```bash
curl -X PUT https://yololab.net/wp-json/wp/v2/posts/30121 \
  -H "Authorization: Bearer [TOKEN]" \
  -d '{schema: {...}}'
```

**選項 3：手動逐篇修正**
- 適用於問題文章不超過 20 篇的情況
- 預計每篇 3-5 分鐘

---

## 檢查清單 - 執行完成確認

### 前置條件
- [ ] WordPress 後台可訪問
- [ ] Yoast SEO Premium 已啟用
- [ ] Google Rich Results Test 可訪問
- [ ] 驗證清單文件已準備

### 配置階段
- [ ] 訪問 Yoast SEO Schema 設定
- [ ] 配置音樂分類 Schema（NewsArticle + MusicRecording + Review）
- [ ] 配置電影分類 Schema（NewsArticle + Movie + Review）
- [ ] 配置科技分類 Schema（NewsArticle）
- [ ] Yoast Panel 中無紅色警告

### 驗證階段
- [ ] 驗證 5 篇音樂文章
- [ ] 驗證 5 篇電影文章
- [ ] 驗證 5 篇科技文章
- [ ] 記錄所有驗證結果到 CSV
- [ ] 檢查 Google Search Console 無新錯誤

### 修正階段
- [ ] 修正所有 P0 問題
- [ ] 修正所有 P1 問題（如時間允許）
- [ ] 重新驗證修正的文章
- [ ] 達成 ≥ 80% 通過率

### 報告階段
- [ ] 生成完成報告
- [ ] 統計驗證結果
- [ ] 確認 Go/No-Go 決策
- [ ] 交付所有文件

---

## 時間估計與節奏

| 階段 | 預計時間 | 實際時間 | 備註 |
|------|---------|---------|------|
| Step 1.1-1.2 檢查配置 | 10 分鐘 | | |
| Step 1.3 配置 Schema | 20 分鐘 | | |
| Step 2.1-2.2 驗證 15 篇 | 60 分鐘 | | 每篇 4 分鐘 |
| Step 2.3-2.4 檢查 GSC/Lighthouse | 15 分鐘 | | |
| Step 3 問題修正 | 30-45 分鐘 | | 依問題數量 |
| Step 4 報告 | 15 分鐘 | | |
| **總計** | **2-2.5 小時** | | |

---

## 聯絡與支援

如遇到問題或有疑問，請參考：
1. 本文件的「常見問題」部分
2. Yoast SEO 官方文檔：https://yoast.com/structured-data-schema/
3. Google Schema.org 參考：https://schema.org/
4. Google Rich Results 幫助：https://developers.google.com/search/docs/advanced/structured-data/article

---

**版本**：1.0
**最後更新**：2026-04-04
**狀態**：Ready for Execution
