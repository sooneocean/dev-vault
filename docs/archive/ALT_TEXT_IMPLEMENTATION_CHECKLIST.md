# YOLO LAB 圖片 ALT 文字優化 — 實施檢查單與邊界情況測試

**文件版本**: 1.0
**建立日期**: 2026-04-12
**配套文檔**: YOLOLAB_ALT_TEXT_ARCHITECTURE_REVIEW.md

---

## Part A: 前置設置檢查

### A.1 環境和依賴

- [ ] Node.js v24+ 已安裝？`node --version`
- [ ] 必要 npm 包已安裝？
  - [ ] `@anthropic-ai/sdk` （Claude Vision 和工具使用）
  - [ ] `node-fetch` 或 Node.js 內置 `fetch`（v18+）
- [ ] `WPCOM_TOKEN` 或 `WP_APP_USER`+`WP_APP_PASS` 已配置在 .env 或環境？
- [ ] `.mcp.json` 已配置 wpcom-mcp Bearer token？

### A.2 認證驗證

- [ ] 執行測試 API 調用驗證認證有效性？
  ```bash
  # 測試 v1.1 API
  curl -H "Authorization: Bearer ${WPCOM_TOKEN}" \
    https://public-api.wordpress.com/rest/v1.1/sites/133512998/media \
    | head -20

  # 預期：200 OK + media 清單
  ```
- [ ] Featured_media 更新權限已驗證？（Unit 3 前置條件）
  ```bash
  # 測試媒體 alt 更新（不實際修改，dry-run）
  curl -X POST -H "Authorization: Bearer ${WPCOM_TOKEN}" \
    -H "Content-Type: application/json" \
    -d '{"alt": "test"}' \
    https://public-api.wordpress.com/rest/v1.1/sites/133512998/media/{TEST_MEDIA_ID}?_test_dry_run=1
  ```
- [ ] 文章編輯權限已驗證？（Unit 4 前置條件）
  ```bash
  # 測試文章更新
  curl -H "Authorization: Bearer ${WPCOM_TOKEN}" \
    https://public-api.wordpress.com/wp/v2/sites/133512998/posts/{TEST_POST_ID}?context=edit

  # 預期：200 + content.raw 可讀
  ```

### A.3 磁盤空間和備份

- [ ] `seo-optimization-output/` 目錄已建立且有寫入權限？
- [ ] 預留磁盤空間 >= 100MB？（用於 backup JSON）
  ```bash
  df -h /path/to/repo | awk 'NR==2 {print $4}'  # Check available space
  ```
- [ ] 備份策略已決策？
  - [ ] 備份檔案存放位置（本地 vs 雲端）
  - [ ] 備份保留期限（多久後可刪除）
  - [ ] 備份加密策略（可選）

### A.4 與其他批次腳本的衝突檢查

- [ ] Phase 4 SEO 優化已完成？若仍在運行，該計畫不應啟動
  ```bash
  ls -l seo-optimization-output/ | grep -i "phase4"
  # 預期：存在 phase4-complete.json 或類似的完成標記
  ```
- [ ] 沒有其他 internal-linker 或 geo-optimizer 在運行？
  ```bash
  ps aux | grep node | grep -E "(linker|geo-optimizer)" | grep -v grep
  # 預期：無輸出
  ```
- [ ] 互斥鎖文件 `.lock` 不存在？
  ```bash
  ls -l seo-optimization-output/.lock 2>&1
  # 預期：No such file or directory
  ```

---

## Part B: Unit 1 - 掃描與盤點 驗收標準

### B.1 Happy Path 測試

**測試場景**: 掃描 10-50 篇文章

```bash
node scripts/image-alt-text-optimizer.js --phase scan --sample 50 --dry-run
```

**預期輸出**：
1. Console 日誌顯示進度：
   ```
   ✓ Scanning posts: 50/50 completed
   ✓ Parsed featured_media: 48
   ✓ Parsed inline images: 156
   ```
2. 輸出檔案 `image-audit-report.json`：
   ```json
   {
     "scanTime": "2026-04-12T08:00:00Z",
     "totalPosts": 50,
     "stats": {
       "postsWithFeatured": 48,
       "imagesWithEmptyAlt": 142,
       "imagesWithFilenameAlt": 8,
       "imagesWithReasonableAlt": 6,
       "imagesDecorative": 0,
       "uniqueImageUrls": 145
     },
     "details": [
       {
         "postId": 26964,
         "title": "...",
         "featured": { "mediaId": 12345, "alt": "" },
         "inlineImages": [
           { "src": "i0.wp.com/yololab.net/...", "alt": "" },
           { "src": "i0.wp.com/yololab.net/...", "alt": "IMG_2034" }
         ]
       }
     ]
   }
   ```

**驗收標準**：
- [ ] report.json 包含所有必要欄位
- [ ] `uniqueImageUrls` 計數準確（無重複）
- [ ] `imagesWithFilenameAlt` 正確識別 `IMG_\d+`, `DSC_\d+`, `Screenshot` 等模式
- [ ] Inline images 解析正確（含 Gutenberg block comments 中的 img）

### B.2 邊界情況測試

#### B.2.1 無 Featured Media 的文章
**測試**: 掃描包含無 featured_media（featured_media=0）的文章
**預期**: 該文章在 report 中標記為 `featured: null` 或 omitted，不拋錯誤
- [ ] 邊界測試通過

#### B.2.2 複雜 HTML 結構
**測試**: 掃描包含 Gutenberg 區塊評論的文章
```html
<!-- wp:image {"id":12345} -->
<figure><img src="..." alt=""/></figure>
<!-- /wp:image -->
```
**預期**: 正確識別並解析嵌套的 `<img>`
- [ ] 邊界測試通過

#### B.2.3 外部 CDN 圖片
**測試**: 掃描包含非 i0.wp.com 的圖片（如第三方服務）
**預期**: report 中標記 `externalUrl: true`，記錄可否被 Vision 存取
- [ ] 邊界測試通過

### B.3 Vision URL 存取檢驗

**測試**: Unit 1 結尾的 Vision 可存取性檢驗
```javascript
// pseudocode
const testImage = reportData.details[0].inlineImages[0];
const canVisionAccess = await testClaudeVision(testImage.src);
report.visionAccessibility = canVisionAccess ? "supported" : "fallback_text_only";
```

**預期**:
- [ ] 至少 2 張圖片 Vision URL 測試成功
- [ ] 若測試失敗，自動記錄「降級至純文字推測」
- [ ] Report 中明確標記 Vision 支援狀態

### B.4 Unit 3 前置 API 驗證

**測試**: Unit 1 結尾測試 v1.1 媒體更新 API
```javascript
// pseudocode
const testMediaId = reportData.details[0].featured.mediaId;
const testResult = await testMediaUpdate(testMediaId, { alt: "TEST_ALT_20260412" });
report.apiVerification = {
  mediaUpdateAPI: testResult.success ? "confirmed" : "failed",
  error: testResult.error
};
```

**驗收標準**：
- [ ] 至少一張測試圖片的媒體更新成功
- [ ] 若失敗，report 應清晰記錄失敗原因（認證、權限、API 版本等）
- [ ] 若失敗，應提供「手動修復步驟」

---

## Part C: Unit 2 - Claude Vision ALT 生成 驗收標準

### C.1 Happy Path 測試

**測試場景**: 生成 5-10 張圖片的 alt text

```bash
node scripts/image-alt-text-optimizer.js --phase generate --sample 10 --dry-run
```

**預期輸出**：
1. 每張圖片生成的 alt text：
   ```
   ✓ Image 1: "台灣音樂製作人在倫敦音樂節的現場演奏，展示多軌道錄音室設備"
   ✓ Image 2: "電影海報：古力娜札主演的科幻懸疑劇《謎團》"
   ```
2. 生成統計：
   ```
   Total images: 10
   Generated: 9
   Skipped (decorative): 1
   Failed: 0
   Avg. length: 87 characters
   Keyword coverage: 100% (all generated alt include relevant keywords)
   ```

**驗收標準**：
- [ ] 生成的 alt text 長度 30-150 字元（計畫要求 80-125）
- [ ] 不含禁用詞（"image of", "photo of", "圖片的", "的圖片"）
- [ ] 自然融入 1-2 個相關關鍵字（需人工檢查 3-5 個樣本）
- [ ] 繁體中文品質可接受（無簡體中文、無英文詞未翻譯）
- [ ] 同一篇文章的多張圖片 alt text 互不重複

### C.2 邊界情況測試

#### C.2.1 純文字截圖
**測試**: 輸入包含程式碼或文字內容的圖片
**預期**: ALT text 包含截圖中的關鍵詞
```
Example: "WordPress.com REST API 文檔截圖，展示 /media 端點的請求參數"
```
- [ ] 邊界測試通過

#### C.2.2 裝飾性圖片（spacer、分隔線）
**測試**: 輸入純背景或裝飾性圖片
**預期**: `is_decorative: true`，alt text 應為空字串 `alt=""`
- [ ] 邊界測試通過

#### C.2.3 超長生成結果
**測試**: 某些複雜圖片導致 Claude 生成 > 150 字元的 alt
**預期**: 自動重試一次，仍超過則截斷至 150 字元
```javascript
if (altText.length > 150) {
  altText = altText.substring(0, 150).trim() + "...";
}
```
- [ ] 邊界測試通過（確認截斷不會斷詞）

#### C.2.4 Vision URL 無法存取
**測試**: 某些 WordPress CDN URL 被防火牆阻擋
**預期**: 降級為純文字推測（使用文章標題 + 分類 + 位置提示）
```
Example (fallback): "【音樂】文章中的圖片 1 - 現場演奏舞台"
```
- [ ] 邊界測試通過

#### C.2.5 相同 URL 快取命中
**測試**: 同一圖片 URL 出現在 3 篇不同文章中
**預期**: 只呼叫 Claude Vision 一次，後續 2 次快取命中
```javascript
const cacheHits = altCache.filter(c => c.url === targetUrl).length;
assert(cacheHits === 1, "Should hit cache 2 times, only 1 API call");
```
- [ ] 邊界測試通過（確認節省 API 成本）

### C.3 品質閘門檢查

執行完整的品質驗證（至少 20 個樣本）：

```bash
node scripts/image-alt-text-optimizer.js --phase generate --sample 50 --report-quality
```

**品質評分項**（建議權重）：
- 長度適宜（30-150 字元）：20%
- 無禁用詞：15%
- 關鍵字自然融入：25%
- 語言品質（繁體中文、文法）：20%
- 與圖片內容匹配度：20%

**通過標準**：平均得分 >= 70/100

- [ ] 品質檢查通過

---

## Part D: Unit 3 - Featured Media 更新 驗收標準

### D.1 小規模生產環境測試

**測試場景**: 更新 5-10 張圖片

```bash
node scripts/image-alt-text-optimizer.js --phase featured --sample 10
```

**驗收前提條件**：
- [ ] Unit 1 掃描已完成，audit report 可用
- [ ] Unit 2 生成已完成，alt text 快取可用
- [ ] 已備份 WordPress 資料庫（可選但推薦）

**執行步驟**：
1. [ ] Dry-run 模式驗證：
   ```bash
   node scripts/image-alt-text-optimizer.js --phase featured --sample 10 --dry-run
   ```
   預期：生成更新清單但不發送 API 請求

2. [ ] 備份檔案驗證：
   ```bash
   cat seo-optimization-output/alt-text-backup-featured.json | jq '.[] | {mediaId, originalAlt}' | head -5
   ```
   預期：備份包含 mediaId + originalAlt 對

3. [ ] 實際執行：
   ```bash
   node scripts/image-alt-text-optimizer.js --phase featured --sample 10
   ```
   預期：5-10 個媒體成功更新

4. [ ] 驗證結果：
   ```bash
   # 檢查 state 檔案
   cat seo-optimization-output/state_alttext_featured.json | jq '.stats'
   # 預期：{ "total": 10, "updated": 10, "failed": 0, "decorative": 0 }

   # 檢查 WordPress 中的實際值
   curl -H "Authorization: Bearer ${WPCOM_TOKEN}" \
     https://public-api.wordpress.com/rest/v1.1/sites/133512998/media/{UPDATED_MEDIA_ID} \
     | jq '.alt'
   # 預期：生成的 alt text（非空）
   ```

### D.2 邊界情況測試

#### D.2.1 重複的 Media ID
**測試**: 同一 media ID 被多篇文章引用為 featured_media
**預期**: 只更新一次（Unit 3 開始前應去重）
- [ ] 邊界測試通過

#### D.2.2 API 429 Rate Limit
**測試**: 模擬 WordPress API 返回 429 Too Many Requests
**預期**: 自動等待 + 重試（指數退避）
```javascript
// Simulate rate limit
if (++requestCount % 3 === 0) {
  throw { status: 429, message: "Rate limited" };
}
// Expect: exponential backoff 2s, 4s, 8s, then success
```
- [ ] 邊界測試通過

#### D.2.3 API 失敗 3 次後放棄
**測試**: 某個 media 持續失敗 3 次
**預期**: 記錄到 failed 陣列，繼續處理下一張
- [ ] 邊界測試通過

#### D.2.4 Resume 機制驗證
**測試**: 執行中途中斷，重新執行 --resume
```bash
# 第 1 次執行（更新 1-5 張）
timeout 10 node scripts/image-alt-text-optimizer.js --phase featured --sample 10

# 驗證已更新
cat seo-optimization-output/state_alttext_featured.json | jq '.processed | length'
# 預期：5（或更少）

# 第 2 次執行 --resume
node scripts/image-alt-text-optimizer.js --phase featured --resume

# 驗證追續更新
cat seo-optimization-output/state_alttext_featured.json | jq '.processed | length'
# 預期：>5（已成功恢復並繼續）
```
- [ ] Resume 測試通過

### D.3 生產就緒檢查

執行大規模測試（100+ 篇）：

```bash
node scripts/image-alt-text-optimizer.js --phase featured --sample 100
```

**通過標準**：
- [ ] 成功率 >= 95%（最多 5 個失敗）
- [ ] 平均響應時間 <= 2 秒/image（batch 5 + delay 2000ms）
- [ ] 備份檔案大小合理（< 10MB）
- [ ] State 檔案正確追蹤所有項目

---

## Part E: Unit 4 - 內嵌圖片更新 驗收標準

### E.1 HTML 修改冪等性測試（關鍵）

**測試場景**: 修改同一篇文章的內嵌圖片 ALT，執行兩次

```bash
# 第 1 次執行
node scripts/image-alt-text-optimizer.js --phase inline --sample 1 --post-id 26964

# 驗證修改
curl -H "Authorization: Bearer ${WPCOM_TOKEN}" \
  "https://public-api.wordpress.com/wp/v2/sites/133512998/posts/26964?context=edit" \
  | jq '.content.raw' | grep -o 'alt="[^"]*"' | head -3

# 第 2 次執行（應該冪等，不重複修改）
node scripts/image-alt-text-optimizer.js --phase inline --resume

# 驗證內容未被雙重修改
# 預期：alt text 值與第 1 次執行相同
```

**驗收標準**：
- [ ] 第 2 次執行後，alt text 值未改變
- [ ] HTML 結構完整（無損壞的標籤）
- [ ] Gutenberg block comments 未被修改

### E.2 邊界情況測試

#### E.2.1 複雜嵌套 HTML
**測試**: 包含 `<picture>`, `<figure>`, `<img>` 嵌套的文章
```html
<figure>
  <picture>
    <source srcset="..." />
    <img src="..." alt=""/>
  </picture>
  <figcaption>...</figcaption>
</figure>
```
**預期**: 正確識別並修改 `<img>` 的 alt，保留其他結構不動
- [ ] 邊界測試通過

#### E.2.2 已有合理 ALT 的圖片
**測試**: 文章包含 5 張圖片，其中 2 張已有合理 alt，3 張缺 alt
**預期**: 只修改 3 張缺 alt 的，保留 2 張不動
- [ ] 邊界測試通過

#### E.2.3 HTML 解析異常
**測試**: 某篇文章包含格式錯誤的 HTML（未閉合的標籤）
**預期**: 記錄到 failed，不修改該文章，繼續下一篇
- [ ] 邊界測試通過

#### E.2.4 部分圖片失敗的 Partial 狀態
**測試**: 文章有 5 張圖片，第 3 張生成失敗
**預期**:
- [ ] 前 2 張成功修改並 POST
- [ ] 第 3 張失敗（不修改）
- [ ] 後 2 張成功修改並 POST
- [ ] State 記錄為 `partial`，標記失敗圖片索引
- [ ] --resume 時只重試第 3 張

### E.3 Content Verification

執行完整驗證（10+ 篇文章）：

```bash
node scripts/image-alt-text-optimizer.js --phase inline --sample 10 --verify
```

**驗收標準**：
- [ ] 抽檢 10 篇已修改文章，HTML 結構完整
- [ ] 修改的 `<img>` alt 值正確
- [ ] Gutenberg block comments 保持原樣
- [ ] 備份內容可還原

---

## Part F: Unit 5 - Rollback 驗收標準

### F.1 Rollback 功能測試

**前置**：已成功執行 Unit 3 和 Unit 4

```bash
# 備份當前狀態
cp seo-optimization-output/state_alttext_featured.json state_before_rollback.json

# 執行 rollback
node scripts/image-alt-text-optimizer.js --rollback featured --sample 5

# 驗證還原
curl -H "Authorization: Bearer ${WPCOM_TOKEN}" \
  "https://public-api.wordpress.com/rest/v1.1/sites/133512998/media/{ROLLED_BACK_MEDIA_ID}" \
  | jq '.alt'
# 預期：與 alt-text-backup-featured.json 中的 originalAlt 相同
```

**驗收標準**：
- [ ] --rollback featured 成功還原 featured_media alt
- [ ] --rollback inline 成功還原文章 content.raw
- [ ] --rollback all 兩者皆還原
- [ ] 還原後驗證值與備份完全一致

### F.2 部分 Rollback 測試

```bash
node scripts/image-alt-text-optimizer.js --rollback featured --range 1-50
```

**預期**：只還原前 50 個 featured_media，其他保持更新狀態

- [ ] 範圍指定正確

### F.3 Rollback 失敗恢復

**測試**: 模擬 rollback 中途失敗

```bash
# 停止 rollback（Ctrl+C 中途終止）
# timeout 5 node scripts/... --rollback featured

# 驗證 state 檔案記錄了失敗狀態
cat seo-optimization-output/state_alttext_featured.json | jq '.failed | length'

# 重新執行 --rollback --resume
node scripts/image-alt-text-optimizer.js --rollback featured --resume
```

**預期**：能夠恢復並繼續還原

- [ ] Rollback 失敗恢復正確

---

## Part G: Unit 6 - 報告生成 驗收標準

### G.1 報告內容檢查

```bash
node scripts/image-alt-text-optimizer.js --phase report
cat seo-optimization-output/alt-text-optimization-report.md
```

**報告應包含**：
- [ ] 執行摘要（開始時間、結束時間、總耗時）
- [ ] 統計數字：
  - [ ] 掃描圖片總數
  - [ ] 已更新數量（featured + inline）
  - [ ] 跳過數量（含理由：合理 alt / 裝飾性）
  - [ ] 失敗數量（含失敗原因分布）
  - [ ] Partial 文章數量
- [ ] ALT text 品質分析：
  - [ ] 長度分布（直方圖）
  - [ ] 關鍵字涵蓋率
  - [ ] 裝飾性圖片比例
- [ ] 失敗項目清單（若有）
- [ ] 後續建議和檢查清單

**驗收標準**：
- [ ] 報告可讀且可直接貼入 vault journal
- [ ] 所有統計數字與 state 檔案一致
- [ ] 包含可操作的後續步驟

---

## Part H: 整合測試（端到端）

### H.1 完整流程測試

執行完整的 Unit 1-6 管道（小規模，50 篇文章）：

```bash
# Unit 1: 掃描
node scripts/image-alt-text-optimizer.js --phase scan --sample 50

# Unit 2: 生成（需要 Claude API 調用，時間較長）
node scripts/image-alt-text-optimizer.js --phase generate --sample 50 --dry-run

# Unit 3: Featured 更新
node scripts/image-alt-text-optimizer.js --phase featured --sample 50

# Unit 4: Inline 更新
node scripts/image-alt-text-optimizer.js --phase inline --sample 50

# Unit 6: 報告
node scripts/image-alt-text-optimizer.js --phase report
```

**預期**：
- [ ] Unit 1-6 全部執行成功
- [ ] 無交叉污染或狀態衝突
- [ ] 報告汇總準確

### H.2 中斷和恢復測試

**場景**: 模擬實際執行中的中斷和恢復

```bash
# 執行並在中途停止（10 秒後）
timeout 10 node scripts/image-alt-text-optimizer.js --phase featured --sample 200

# 驗證 state 檔案已保存
cat seo-optimization-output/state_alttext_featured.json | jq '.processed | length'

# 恢復執行
node scripts/image-alt-text-optimizer.js --phase featured --resume

# 驗證已完成
cat seo-optimization-output/state_alttext_featured.json | jq '.stats'
```

**預期**：
- [ ] --resume 自動跳過已處理項目
- [ ] 完成最終統計正確

---

## Part I: 生產部署清單

### I.1 最終檢查

在執行全站（2,728 篇文章）前：

- [ ] 所有 Unit 1-6 在 sample=50-100 下通過測試
- [ ] 無已知的失敗場景（高優先級項目已修復）
- [ ] 備份和 rollback 機制已驗證可靠
- [ ] Claude API 配額充足（預估 $3-5）
- [ ] WordPress API rate limit 理解清晰（無併發腳本運行）
- [ ] 執行時間和成本估算已溝通相關人員
- [ ] Vault journal 已準備好記錄執行結果

### I.2 執行計劃

**建議執行策略**：

1. **分批執行**（避免一次處理 2,728 篇）：
   - 批次 A：500 篇（測試和監控）
   - 批次 B：1,000 篇（繼續監控）
   - 批次 C：1,228 篇（完成）

2. **監控間隔**：
   - 每批執行後等待 24-48 小時
   - 檢查 Google Search Console 是否有異常
   - 驗證生成的 alt text 未觸發 Google spam 偵測

3. **文檔記錄**：
   ```
   Journal Entry 2026-04-XX:
   - [時間] Unit 1-6 執行完成，批次 A（500 篇）
   - 統計：已更新 485 張 featured + 156 張 inline，失敗 15 張
   - 備份位置：seo-optimization-output/alt-text-backup-*.json
   - 後續步驟：48 小時後檢查 GSC 及其他指標
   ```

---

## Part J: 故障排查指南

### J.1 常見問題和解決方案

| 問題 | 症狀 | 解決方案 |
|------|------|---------|
| **認證失敗** | "Could not resolve authentication" | 檢查 `WPCOM_TOKEN` 或 `.env` 中的認證信息 |
| **API 429 持續出現** | 重試 3 次仍失敗，批次中斷 | 檢查是否有其他 SEO 批次同時運行；增加延遲至 3000ms |
| **Vision URL 無法存取** | "Failed to download image from URL" | 測試該 CDN URL 是否可以通過 curl 訪問；若否，檢查防火牆規則 |
| **HTML 解析失敗** | "Skipped post {id}: HTML parsing error" | 手動檢查文章的 content.raw；若含特殊編碼，需 debug |
| **State 檔案損壞** | JSON 解析錯誤 | 從 backup 恢復或刪除該 state 檔案重新開始 |
| **Rollback 還原錯誤** | "Rollback failed: POST /media/{id} returned 403" | 檢查認證權限；若權限不夠，可能需要應用密碼而非 Bearer token |

### J.2 調試模式

```bash
# 啟用詳細日誌
DEBUG=* node scripts/image-alt-text-optimizer.js --phase featured --sample 5

# 詳細輸出（包含 HTTP 請求/響應）
node scripts/image-alt-text-optimizer.js --phase featured --sample 5 --verbose

# Dry-run 模式（生成所有操作但不實際發送）
node scripts/image-alt-text-optimizer.js --phase featured --sample 50 --dry-run
```

---

**檢查單完成**
**建議人簽名**: System Architecture Expert — Claude 4.5 Haiku
**預計完成日期**: 2026-04-15（Unit 1-2）→ 2026-04-20（Unit 3-6）

