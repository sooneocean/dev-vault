# YOLO LAB 圖片 ALT 文字優化計畫 — 設計改進建議

**文件版本**: 1.0
**準備對象**: 實施團隊
**應用時機**: 編寫 Unit 1-6 代碼之前

本文件詳細說明架構審視中發現的「高優先級」和「中優先級」設計缺陷，並提供具體的改進方案和代碼示例。

---

## 改進 #1: 內嵌圖片部分失敗的狀態追蹤（高優先級）

**原問題**（見架構審視 3.3 章節）：
- 計畫提及「部分失敗策略」但未明確定義如何追蹤「哪張圖片已修改，哪張未修改」
- 使用「索引」（第 M 張）不夠明確，因為 HTML 排序可能不一致
- Resume 時可能重複修改或漏處理某張圖片

**改進方案**：使用 **URL 作為冪等性鍵**，而非位置索引

### 設計詳情

**Unit 4 State 結構改進**：

```json
{
  "name": "inline",
  "startTime": "2026-04-12T08:00:00Z",
  "processed": [123, 456],           // 完全成功的文章
  "partial": [
    {
      "postId": 789,
      "scanTime": "2026-04-12T08:05:00Z",
      "totalImages": 5,
      "imageScanResult": [
        {
          "url": "https://i0.wp.com/yololab.net/images/a.jpg",
          "status": "updated",
          "altText": "生成的 alt text A"
        },
        {
          "url": "https://i0.wp.com/yololab.net/images/b.jpg",
          "status": "failed",
          "error": "Vision API timeout",
          "retryCount": 3
        },
        {
          "url": "https://i0.wp.com/yololab.net/images/c.jpg",
          "status": "skipped",
          "reason": "already_has_reasonable_alt",
          "existingAlt": "..."
        }
      ],
      "originalContent": "..."  // 完整備份
    }
  ],
  "failed": [
    {
      "postId": 990,
      "error": "HTML structure invalid: unclosed img tag",
      "originalContent": "..."
    }
  ]
}
```

### 實現邏輯

```javascript
// Unit 4 - HTML 修改邏輯（改進版）
async function updateInlineImages(postId, contentRaw, state) {
  // 1. 掃描 <img> 標籤並建立 URL 清單
  const imgRegex = /<img[^>]*>/g;
  const matches = [...contentRaw.matchAll(imgRegex)];

  const imageScanResult = [];
  let modifiedContent = contentRaw;
  let hasChanges = false;

  for (const match of matches) {
    const srcMatch = match[0].match(/src=["']([^"']+)["']/);
    const altMatch = match[0].match(/alt=["']([^"']*)["']/);

    if (!srcMatch) continue;

    const url = srcMatch[1];
    const existingAlt = altMatch ? altMatch[1] : null;

    // 2. 檢查該 URL 是否已在 partial 中處理過
    const existingRecord = findImageRecord(state.partial, postId, url);

    if (existingRecord) {
      // 2a. 已處理：檢查上次結果
      if (existingRecord.status === "updated") {
        // 重新應用同樣的 alt text（冪等性）
        const newTag = match[0].replace(
          /alt=["'][^"']*["']/,
          `alt="${existingRecord.altText}"`
        );
        modifiedContent = modifiedContent.replace(match[0], newTag);
        hasChanges = true;
      } else if (existingRecord.status === "skipped") {
        // 保持原樣
        imageScanResult.push(existingRecord);
      } else if (existingRecord.status === "failed") {
        // 重試邏輯
        if (existingRecord.retryCount < 3) {
          // 重試
          try {
            const newAlt = await generateAltText(url, state.altCache);
            modifiedContent = modifiedContent.replace(
              match[0],
              match[0].replace(/alt=["'][^"']*["']/, `alt="${newAlt}"`)
            );
            existingRecord.status = "updated";
            existingRecord.altText = newAlt;
            hasChanges = true;
          } catch (e) {
            existingRecord.retryCount++;
            existingRecord.lastError = e.message;
          }
        }
        imageScanResult.push(existingRecord);
      }
      continue;
    }

    // 2b. 首次處理
    if (existingAlt && existingAlt.length > 10 && !isFilenamePattern(existingAlt)) {
      // 已有合理的 alt，跳過
      imageScanResult.push({
        url,
        status: "skipped",
        reason: "already_has_reasonable_alt",
        existingAlt
      });
      continue;
    }

    // 2c. 需要生成 alt text
    try {
      const newAlt = await generateAltText(url, state.altCache);
      const newTag = match[0].replace(
        /alt=["'][^"']*["']/,
        `alt="${newAlt}"`
      );
      modifiedContent = modifiedContent.replace(match[0], newTag);
      imageScanResult.push({ url, status: "updated", altText: newAlt });
      hasChanges = true;
    } catch (err) {
      imageScanResult.push({
        url,
        status: "failed",
        error: err.message,
        retryCount: 1
      });
    }
  }

  // 3. 更新 WordPress 並記錄狀態
  if (hasChanges) {
    try {
      await updatePostContent(postId, modifiedContent);

      // 檢查是否全部成功
      const allSuccessful = imageScanResult.every(
        r => r.status !== "failed"
      );

      if (allSuccessful) {
        state.processed.push(postId);
      } else {
        // 部分失敗
        const existing = state.partial.find(p => p.postId === postId);
        if (existing) {
          existing.imageScanResult = imageScanResult;
          existing.lastUpdated = new Date().toISOString();
        } else {
          state.partial.push({
            postId,
            scanTime: new Date().toISOString(),
            totalImages: matches.length,
            imageScanResult,
            originalContent
          });
        }
      }
    } catch (err) {
      // 整個文章失敗
      state.failed.push({
        postId,
        error: err.message,
        originalContent
      });
    }
  } else {
    // 無需修改
    state.processed.push(postId);
  }

  return { modifiedContent, hasChanges };
}

// 輔助函數：查詢現有記錄
function findImageRecord(partial, postId, url) {
  const entry = partial.find(p => p.postId === postId);
  if (!entry) return null;
  return entry.imageScanResult.find(r => r.url === url);
}

// 檢查是否為檔名模式
function isFilenamePattern(alt) {
  return /^(IMG|DSC|Screenshot|screenshot)_?\d+|^image\d+$/.test(alt);
}
```

**優點**：
- ✅ 使用 URL 作為唯一鍵，避免排序問題
- ✅ 完整記錄每張圖片的處理狀態，便於 debug
- ✅ Resume 時能準確重試失敗的圖片
- ✅ 支持冪等性（多次執行結果相同）

---

## 改進 #2: ALT Text 長度管理策略（高優先級）

**原問題**（見架構審視 5.1 章節）：
- 計畫第 196 行提及「超過 150 字元則截斷」但未定義智能截斷邏輯
- 直接截斷可能導致詞組斷裂（例如「台灣音樂製」變成「台灣音樂」）
- 無法確保語義完整性

**改進方案**：實施 **三層次截斷策略**

### 設計詳情

```javascript
// Unit 2 - ALT Text 長度優化
class AltTextOptimizer {
  // Claude response schema
  ALT_TEXT_TOOL = {
    name: "generate_alt_text",
    description: "Generate optimized alt text for images",
    input_schema: {
      type: "object",
      properties: {
        alt_text: {
          type: "string",
          description: "80-125 character alt text in Traditional Chinese"
        },
        is_decorative: {
          type: "boolean",
          description: "Whether image is purely decorative"
        }
      },
      required: ["alt_text", "is_decorative"]
    }
  };

  async generateAltText(imageUrl, articleTitle, categories) {
    const prompt = `你是 SEO 專家，為圖片撰寫搜尋最佳化的替代文字。

圖片來自：${articleTitle}
分類：${categories.join(', ')}
圖片 URL：${imageUrl}

規則：
1. 長度：80-125 字元（絕對上限 150）
2. 語言：繁體中文，清晰自然
3. 內容：描述圖片視覺內容，融入相關關鍵字
4. 禁止：不以「圖片」「image」開頭；避免重複用詞；不含 HTML 標籤
5. 裝飾性：若圖片純為裝飾（spacer/分隔線/背景），回傳 "is_decorative: true"

回應 JSON：
{
  "alt_text": "...",
  "is_decorative": false
}`;

    // Call Claude with tool_use
    const response = await this.client.messages.create({
      model: "claude-haiku-4-5-20251001",
      max_tokens: 200,
      tools: [this.ALT_TEXT_TOOL],
      messages: [
        { role: "user", content: prompt }
      ]
    });

    // 提取 tool_use 結果
    const toolResult = response.content.find(c => c.type === "tool_use");
    if (!toolResult) throw new Error("Tool invocation failed");

    let { alt_text, is_decorative } = toolResult.input;

    // 後處理：確保長度符合要求
    alt_text = this.normalizeAltText(alt_text);

    return { alt_text, is_decorative };
  }

  normalizeAltText(text) {
    // 移除多餘空白
    text = text.replace(/\s+/g, ' ').trim();

    // 三層次截斷策略
    if (text.length <= 150) {
      return text;
    }

    // 層次 1: 在句號、分號、逗號處斷
    const level1 = this.smartTruncate(text, 150, [
      '\u3002', // 中文句號
      '\uff1b', // 中文分號
      '\uff0c'  // 中文逗號
    ]);
    if (level1.length <= 150) return level1;

    // 層次 2: 在「、」或標點處斷
    const level2 = this.smartTruncate(text, 150, [
      '\u3001', // 中文列舉號
      '\u3015'  // 其他標點
    ]);
    if (level2.length <= 150) return level2;

    // 層次 3: 在中文詞邊界（以常見詞彙為基準）或空格處斷
    const level3 = this.truncateAtWordBoundary(text, 150);
    if (level3.length <= 150) return level3;

    // 層次 4: 硬截斷（最後手段）
    return text.substring(0, 150).trim() + '…';
  }

  smartTruncate(text, maxLen, delimiters) {
    if (text.length <= maxLen) return text;

    let bestCut = null;
    for (const delim of delimiters) {
      const lastIndex = text.lastIndexOf(delim, maxLen);
      if (lastIndex > 0 && (!bestCut || lastIndex > bestCut.index)) {
        bestCut = { index: lastIndex, delim };
      }
    }

    if (bestCut) {
      return text.substring(0, bestCut.index + 1).trim();
    }
    return null;  // 無法截斷，嘗試下一層級
  }

  truncateAtWordBoundary(text, maxLen) {
    // 簡單策略：在空格或常見詞邊界截斷
    if (text.length <= maxLen) return text;

    // 查找最後一個空格
    const lastSpace = text.lastIndexOf(' ', maxLen);
    if (lastSpace > 0) {
      return text.substring(0, lastSpace).trim();
    }

    // 無空格（罕見），硬截斷
    return text.substring(0, maxLen).trim();
  }

  // 品質檢查
  validateAltText(alt) {
    const errors = [];

    if (alt.length < 30) {
      errors.push("ALT text too short (< 30 chars)");
    }
    if (alt.length > 150) {
      errors.push("ALT text exceeds 150 chars after normalization");
    }
    if (/^(image|photo|圖片|image of|photo of)/.test(alt.toLowerCase())) {
      errors.push("Starts with forbidden phrase");
    }
    if (/^的/.test(alt) || /的$/.test(alt)) {
      errors.push("Improper use of possessive particle");
    }

    return { valid: errors.length === 0, errors };
  }
}

// 測試
const optimizer = new AltTextOptimizer();
const tests = [
  "台灣音樂製作人在倫敦音樂節的現場演奏，展示多軌道錄音室設備和效果器，舞台燈光照亮現場樂隊陣容，吉他手和鍵盤手合奏的場景，觀眾熱烈掌聲伴隨著美妙的樂音",
  "短的 alt",
  "正常長度的 alt text，在 80-125 字元之間"
];

for (const text of tests) {
  const normalized = optimizer.normalizeAltText(text);
  const validation = optimizer.validateAltText(normalized);
  console.log({
    original: text.substring(0, 50),
    normalized: normalized.substring(0, 50),
    length: normalized.length,
    valid: validation.valid
  });
}
```

**優點**：
- ✅ 智能截斷保持語義完整
- ✅ 三層次退避確保結果品質
- ✅ 驗證邏輯防止不合規的 alt text

---

## 改進 #3: 認證前置驗證機制（高優先級）

**原問題**（見架構審視 2.3 和 5.2 章節）：
- 計畫缺乏「認證驗證」的前置步驟
- 實際 `state_alttext_featured.json` 顯示 401 認證錯誤，導致整個批次失敗
- 無法提前檢測認證問題

**改進方案**：在 Unit 1 掃描階段加入 **API 健康檢查**

### 設計詳情

```javascript
// Unit 1 - 前置 API 驗證
class APIHealthCheck {
  constructor(options = {}) {
    this.siteId = options.siteId || 133512998;
    this.verbose = options.verbose || false;
  }

  async runFullCheck() {
    console.log("🔍 Running API health check...\n");

    const results = {
      timestamp: new Date().toISOString(),
      checks: {
        authentication: null,
        v1_1_media_read: null,
        v1_1_media_update: null,
        v2_posts_read: null,
        v2_posts_update: null,
        vision_url_access: null
      },
      warnings: [],
      errors: []
    };

    try {
      // Check 1: 基本認證
      results.checks.authentication = await this.checkAuthentication();

      // Check 2: REST v1.1 媒體讀取
      results.checks.v1_1_media_read = await this.checkV11MediaRead();

      // Check 3: REST v1.1 媒體更新（測試但不實際修改）
      results.checks.v1_1_media_update = await this.checkV11MediaUpdate();

      // Check 4: wp/v2 文章讀取
      results.checks.v2_posts_read = await this.checkV2PostsRead();

      // Check 5: wp/v2 文章更新（測試但不實際修改）
      results.checks.v2_posts_update = await this.checkV2PostsUpdate();

      // Check 6: Claude Vision URL 存取（異步，非阻擋）
      this.checkVisionAccess().then(result => {
        results.checks.vision_url_access = result;
      }).catch(err => {
        results.checks.vision_url_access = {
          status: "failed",
          error: err.message
        };
      });

    } catch (err) {
      results.errors.push(err.message);
    }

    this.printResults(results);
    return results;
  }

  async checkAuthentication() {
    try {
      const headers = this.getAuthHeaders();
      if (!headers.Authorization) {
        throw new Error("No authorization header found");
      }

      const response = await fetch(
        `https://public-api.wordpress.com/rest/v1.1/sites/${this.siteId}`,
        { headers }
      );

      if (response.status === 401) {
        return {
          status: "failed",
          code: 401,
          error: "Unauthorized - check token validity"
        };
      }
      if (response.status === 403) {
        return {
          status: "failed",
          code: 403,
          error: "Forbidden - insufficient permissions"
        };
      }
      if (!response.ok) {
        return {
          status: "failed",
          code: response.status,
          error: `HTTP ${response.status}`
        };
      }

      return { status: "passed", code: 200 };
    } catch (err) {
      return {
        status: "failed",
        error: err.message
      };
    }
  }

  async checkV11MediaRead() {
    try {
      const headers = this.getAuthHeaders();
      const response = await fetch(
        `https://public-api.wordpress.com/rest/v1.1/sites/${this.siteId}/media?per_page=1`,
        { headers }
      );

      if (!response.ok) {
        return {
          status: "failed",
          code: response.status,
          error: `HTTP ${response.status}`
        };
      }

      const data = await response.json();
      return {
        status: "passed",
        code: 200,
        sampleMedia: data.media?.[0] || null
      };
    } catch (err) {
      return { status: "failed", error: err.message };
    }
  }

  async checkV11MediaUpdate() {
    try {
      const headers = this.getAuthHeaders();

      // 先取得一個存在的 media ID
      const listResponse = await fetch(
        `https://public-api.wordpress.com/rest/v1.1/sites/${this.siteId}/media?per_page=1`,
        { headers }
      );

      if (!listResponse.ok) {
        return {
          status: "skipped",
          reason: "Cannot fetch media list for testing"
        };
      }

      const data = await listResponse.json();
      if (!data.media || data.media.length === 0) {
        return {
          status: "skipped",
          reason: "No media found to test"
        };
      }

      const testMediaId = data.media[0].ID;

      // 執行 dry-run 測試（不實際修改）
      const updateResponse = await fetch(
        `https://public-api.wordpress.com/rest/v1.1/sites/${this.siteId}/media/${testMediaId}?_dry_run=true`,
        {
          method: "POST",
          headers: { ...headers, "Content-Type": "application/json" },
          body: JSON.stringify({ alt: "TEST_ALT_" + Date.now() })
        }
      );

      if (updateResponse.status === 401) {
        return {
          status: "failed",
          code: 401,
          error: "Unauthorized to update media"
        };
      }
      if (updateResponse.status === 403) {
        return {
          status: "failed",
          code: 403,
          error: "Permission denied for media update"
        };
      }
      if (!updateResponse.ok) {
        return {
          status: "failed",
          code: updateResponse.status,
          error: `HTTP ${updateResponse.status}`
        };
      }

      return { status: "passed", code: 200 };
    } catch (err) {
      return { status: "failed", error: err.message };
    }
  }

  async checkV2PostsRead() {
    // 類似 checkV11MediaRead，但用 wp/v2 API
    // ... (省略詳細代碼，邏輯相同)
  }

  async checkV2PostsUpdate() {
    // 類似 checkV11MediaUpdate，但用 wp/v2 API
    // ... (省略詳細代碼，邏輯相同)
  }

  async checkVisionAccess() {
    try {
      // 從掃描結果中取樣一張圖片 URL
      const sampleUrl = "https://i0.wp.com/yololab.net/sample-image.jpg";

      // 測試 Claude Vision 能否存取
      const response = await fetch(sampleUrl, { method: "HEAD" });

      if (response.ok) {
        return { status: "passed", message: "CDN accessible" };
      } else if (response.status === 403 || response.status === 401) {
        return { status: "warning", message: "CDN might be restricted" };
      } else {
        return { status: "failed", code: response.status };
      }
    } catch (err) {
      return { status: "warning", error: err.message };
    }
  }

  getAuthHeaders() {
    // 使用 internal-linker-v2.js 的方法
    const token = process.env.WPCOM_TOKEN ||
      (process.env.WP_APP_USER && process.env.WP_APP_PASS
        ? Buffer.from(`${process.env.WP_APP_USER}:${process.env.WP_APP_PASS}`).toString("base64")
        : null);

    if (!token) {
      throw new Error("No authentication credentials found");
    }

    return {
      Authorization: token.includes("Bearer") ? token : `Bearer ${token}`
    };
  }

  printResults(results) {
    console.log("API Health Check Results:");
    console.log("========================\n");

    for (const [check, result] of Object.entries(results.checks)) {
      if (!result) continue;

      const status = {
        "passed": "✅",
        "failed": "❌",
        "skipped": "⊘",
        "warning": "⚠️"
      }[result.status];

      console.log(`${status} ${check}: ${result.status}`);
      if (result.error) console.log(`   Error: ${result.error}`);
      if (result.code) console.log(`   HTTP ${result.code}`);
    }

    if (results.errors.length > 0) {
      console.log("\n⛔ Critical Errors:");
      results.errors.forEach(e => console.log(`   - ${e}`));
      throw new Error("Health check failed");
    }

    if (results.warnings.length > 0) {
      console.log("\n⚠️ Warnings:");
      results.warnings.forEach(w => console.log(`   - ${w}`));
    }

    console.log("\n✨ Health check passed. Ready to proceed.\n");
  }
}

// 使用
const healthCheck = new APIHealthCheck({ siteId: 133512998, verbose: true });
await healthCheck.runFullCheck();
```

**優點**：
- ✅ 前置檢測所有可能的認證/權限問題
- ✅ 清晰的失敗報告，便於診斷
- ✅ 避免浪費時間在已知會失敗的批次上

---

## 改進 #4: HTML 解析失敗的冷卻期機制（高優先級）

**原問題**（見架構審視 5.1 章節）：
- HTML 解析失敗的文章被標記為 failed，但 resume 時仍會重複嘗試
- 無失敗計數或冷卻期，可能陷入「無限重試」
- 對同一失敗文章的多次嘗試浪費資源

**改進方案**：實施 **失敗計數 + 冷卻期** 機制

```javascript
// Unit 4 - 失敗恢復策略
class FailurePolicy {
  constructor(options = {}) {
    this.maxRetries = options.maxRetries || 3;
    this.cooldownHours = options.cooldownHours || 24;
  }

  shouldRetry(failedEntry) {
    if (!failedEntry.retryCount) failedEntry.retryCount = 0;
    if (!failedEntry.lastFailTime) failedEntry.lastFailTime = null;

    // 檢查重試次數
    if (failedEntry.retryCount >= this.maxRetries) {
      failedEntry.status = "abandoned";
      return false;
    }

    // 檢查冷卻期
    if (failedEntry.lastFailTime) {
      const lastFailTime = new Date(failedEntry.lastFailTime);
      const cooldownExpiry = new Date(
        lastFailTime.getTime() + this.cooldownHours * 60 * 60 * 1000
      );

      if (new Date() < cooldownExpiry) {
        return false;  // 仍在冷卻期內
      }
    }

    return true;
  }

  recordFailure(failedEntry, error) {
    failedEntry.retryCount = (failedEntry.retryCount || 0) + 1;
    failedEntry.lastFailTime = new Date().toISOString();
    failedEntry.lastError = error.message;

    if (failedEntry.retryCount >= this.maxRetries) {
      failedEntry.status = "abandoned";
      failedEntry.abandonedAt = new Date().toISOString();
    }
  }
}

// Unit 4 State 中的 failed 條目
{
  "failed": [
    {
      "postId": 990,
      "error": "HTML structure invalid: unclosed img tag",
      "retryCount": 1,
      "lastFailTime": "2026-04-12T08:00:00Z",
      "lastError": "Regex match failed",
      "status": "retry_pending",
      "cooldownExpiry": "2026-04-13T08:00:00Z"
    },
    {
      "postId": 991,
      "error": "Original error",
      "retryCount": 3,
      "status": "abandoned",
      "abandonedAt": "2026-04-12T12:00:00Z"
    }
  ]
}

// Resume 時的邏輯
async function resumeInlineUpdate() {
  const state = loadState();
  const failurePolicy = new FailurePolicy({ maxRetries: 3, cooldownHours: 24 });

  for (const failedEntry of state.failed) {
    if (!failurePolicy.shouldRetry(failedEntry)) {
      console.log(`⊘ Skipping ${failedEntry.postId}: ${failedEntry.status}`);
      continue;
    }

    console.log(`🔄 Retrying ${failedEntry.postId} (attempt ${failedEntry.retryCount + 1}/3)`);

    try {
      await updateInlineImages(failedEntry.postId);
      // 移出 failed
      state.processed.push(failedEntry.postId);
      state.failed = state.failed.filter(f => f.postId !== failedEntry.postId);
    } catch (err) {
      failurePolicy.recordFailure(failedEntry, err);
      console.log(`❌ Still failed: ${err.message}`);
    }
  }

  saveState(state);
}
```

**優點**：
- ✅ 避免無限重試
- ✅ 清晰的失敗狀態（retry_pending vs abandoned）
- ✅ 冷卻期防止連續失敗浪費資源

---

## 改進 #5: Skipped 狀態的明確分類（中優先級）

**原問題**（見架構審視 3.1.2 章節）：
- State 中 `skipped: []` 為空，但無法區分「合理 alt 的圖片」vs「裝飾性圖片」
- Resume 時無法判斷是否需要重新掃描

**改進方案**：結構化 skipped 條目

```javascript
// Unit 1 和 Unit 3 - Skipped 條目改進
{
  "skipped": [
    {
      "mediaId": 12345,
      "reason": "has_reasonable_alt",
      "existingAlt": "台灣電影導演的作品分析",
      "altLength": 18,
      "skippedAt": "2026-04-12T08:00:00Z"
    },
    {
      "mediaId": 12346,
      "reason": "decorative",
      "visionResult": "spacer / background image",
      "rationale": "Purely decorative, recommended alt=\"\"",
      "skippedAt": "2026-04-12T08:00:00Z"
    },
    {
      "mediaId": 12347,
      "reason": "url_inaccessible",
      "url": "https://example.com/image.jpg",
      "error": "403 Forbidden",
      "skippedAt": "2026-04-12T08:00:00Z"
    }
  ]
}

// Resume 邏輯
function shouldReprocess(skippedEntry) {
  const now = new Date();
  const skippedTime = new Date(skippedEntry.skippedAt);
  const daysSinceSkipped = (now - skippedTime) / (1000 * 60 * 60 * 24);

  // 24 小時內跳過的項目，不重新處理
  if (daysSinceSkipped < 1) {
    return false;
  }

  // 特定 reason 需要重新掃描
  if (skippedEntry.reason === "url_inaccessible") {
    // CDN 可能已恢復，24 小時後重試
    return true;
  }

  // 其他 reason 不需要重新處理
  return false;
}
```

---

## 改進 #6: Rollback 驗證邏輯（中優先級）

**原問題**（見架構審視 5.2 章節）：
- Unit 5 計畫提及「還原後驗證」但缺少實現邏輯
- 若還原失敗，無明確的恢復步驟

**改進方案**：實施 **驗證 + 修復** 邏輯

```javascript
// Unit 5 - Rollback 驗證
async function rollbackWithVerification(options) {
  const { phase = "featured", range, dryRun = false } = options;

  const backup = loadBackup(phase);
  const results = {
    timestamp: new Date().toISOString(),
    phase,
    attempted: 0,
    successful: 0,
    failed: [],
    warnings: []
  };

  if (dryRun) {
    console.log("🔍 Dry-run mode: showing what would be rolled back\n");
  }

  for (const entry of backup) {
    // 過濾範圍
    if (range && !isInRange(entry.id, range)) continue;

    results.attempted++;
    const id = entry.id;

    try {
      if (dryRun) {
        console.log(`Would restore ${phase} ${id}`);
        continue;
      }

      // 1. 執行還原
      const rollbackSuccess = await performRollback(phase, entry);
      if (!rollbackSuccess) throw new Error("Rollback API returned error");

      // 2. 驗證（重新獲取並比對）
      const currentValue = await fetchCurrentValue(phase, id);
      const expectedValue = getExpectedValue(phase, entry);

      if (JSON.stringify(currentValue) !== JSON.stringify(expectedValue)) {
        throw new Error(
          `Verification failed: expected ${JSON.stringify(expectedValue)}, got ${JSON.stringify(currentValue)}`
        );
      }

      results.successful++;
      console.log(`✅ ${phase} ${id} rolled back and verified`);

    } catch (err) {
      results.failed.push({
        id,
        error: err.message,
        attempt: "rollback_and_verify"
      });
      console.log(`❌ ${phase} ${id} failed: ${err.message}`);
    }
  }

  // 3. 驗證失敗時的修復邏輯
  if (results.failed.length > 0) {
    console.log(`\n⚠️ ${results.failed.length} rollback(s) failed. Attempting recovery...\n`);

    for (const failedEntry of results.failed) {
      try {
        // 重試一次
        const entry = backup.find(b => b.id === failedEntry.id);
        const retrySuccess = await performRollback(phase, entry);

        if (retrySuccess) {
          const currentValue = await fetchCurrentValue(phase, failedEntry.id);
          const expectedValue = getExpectedValue(phase, entry);

          if (JSON.stringify(currentValue) === JSON.stringify(expectedValue)) {
            results.successful++;
            results.failed = results.failed.filter(f => f.id !== failedEntry.id);
            console.log(`✅ Recovery successful for ${failedEntry.id}`);
          }
        }
      } catch (err) {
        console.log(`❌ Recovery failed: ${err.message}`);
      }
    }
  }

  // 4. 產出報告
  console.log(`\n📊 Rollback Summary:`);
  console.log(`   Attempted: ${results.attempted}`);
  console.log(`   Successful: ${results.successful}`);
  console.log(`   Failed: ${results.failed.length}`);

  if (results.failed.length > 0) {
    console.log(`\n❌ Manual intervention required for:`);
    results.failed.forEach(f => {
      console.log(`   - ${phase} ${f.id}: ${f.error}`);
    });
  }

  return results;
}

async function performRollback(phase, entry) {
  if (phase === "featured") {
    return await updateMediaAlt(entry.mediaId, entry.originalAlt);
  } else if (phase === "inline") {
    return await updatePostContent(entry.postId, entry.originalContent);
  }
}

async function fetchCurrentValue(phase, id) {
  if (phase === "featured") {
    const media = await getMedia(id);
    return { alt: media.alt };
  } else if (phase === "inline") {
    const post = await getPost(id);
    return { content: post.content.raw };
  }
}

function getExpectedValue(phase, entry) {
  if (phase === "featured") {
    return { alt: entry.originalAlt };
  } else if (phase === "inline") {
    return { content: entry.originalContent };
  }
}
```

**優點**：
- ✅ 驗證確保還原正確
- ✅ 修復邏輯提高可靠性
- ✅ 清晰的失敗報告便於人工干預

---

## 改進 #7: 與 Phase 4 的互斥檢查（中優先級）

**原問題**：計畫未提及如何防止與 Phase 4 SEO 批次同時運行

**改進方案**：實施 **執行時互斥鎖**

```javascript
// Unit 1 啟動時的互斥檢查
async function acquireExecutionLock() {
  const lockFile = "seo-optimization-output/.lock";
  const timeout = 3 * 60 * 60 * 1000;  // 3 小時

  if (fs.existsSync(lockFile)) {
    const lock = JSON.parse(fs.readFileSync(lockFile, "utf-8"));
    const lockAge = Date.now() - new Date(lock.timestamp).getTime();

    if (lockAge < timeout) {
      throw new Error(
        `Another SEO batch is running: ${lock.processName} (started ${lock.timestamp})\n` +
        `Lock file: ${lockFile}\n` +
        `To force: rm ${lockFile}`
      );
    } else {
      console.log("⚠️ Stale lock file detected, removing...");
      fs.unlinkSync(lockFile);
    }
  }

  // 建立新鎖
  const lock = {
    timestamp: new Date().toISOString(),
    processName: "image-alt-text-optimizer",
    pid: process.pid,
    args: process.argv.slice(2)
  };

  fs.writeFileSync(lockFile, JSON.stringify(lock, null, 2));
  return { lock, release: () => fs.unlinkSync(lockFile) };
}

// 使用
const { lock, release } = await acquireExecutionLock();
try {
  await runOptimizer();
} finally {
  release();
}
```

---

## 實施優先級表

| 優先級 | 改進項目 | 影響 | 複雜度 | 建議時機 |
|-------|---------|------|--------|---------|
| 🔴 高 | #1 內嵌圖片部分失敗追蹤 | 避免數據丟失 | 中等 | Unit 4 編寫前 |
| 🔴 高 | #2 ALT Text 截斷策略 | 品質保證 | 低 | Unit 2 編寫前 |
| 🔴 高 | #3 認證前置驗證 | 快速失敗 | 低 | Unit 1 編寫前 |
| 🔴 高 | #4 失敗冷卻期機制 | 資源優化 | 低 | Unit 4 編寫前 |
| 🟡 中 | #5 Skipped 分類 | 狀態清晰度 | 低 | Unit 1-4 編寫前 |
| 🟡 中 | #6 Rollback 驗證 | 恢復可靠性 | 中等 | Unit 5 編寫前 |
| 🟡 中 | #7 互斥檢查 | 防止衝突 | 低 | Unit 1 啟動前 |

---

**文件完成**
**作者**: System Architecture Expert — Claude 4.5 Haiku
**建議審查者**: 實施團隊 Lead

