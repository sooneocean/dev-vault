# WordPress 批量發佈指令 — 11 篇新文章

**用途**：使用 wpcom-mcp-content-authoring API 批量發佈文章
**執行時機**：Agent 生成文章完成後

---

## 📋 Batch 1：Tech Priority（5 篇）

### 文章 1：LLM 模型完整對比 2026

**基本信息**
- 發佈時間：2026-04-07 09:00
- 分類：Tech（96990383）
- Tags：LLM, AI, 模型對比, 2026
- Featured：Yes

**執行指令**
```
action: execute
operation: posts.create
wpcom_site: yololab.net
params: {
  "title": "LLM模型完整對比2026｜GPT-4o vs Claude vs Gemini vs Llama最強評測",
  "content": "[完整 HTML 內容]",
  "excerpt": "2026年LLM模型全面對比：性能、成本、速度完整評測。GPT-4o vs Claude 3.5 Opus vs Gemini 2.0最新對比。",
  "status": "publish",
  "date": "2026-04-07T09:00:00",
  "categories": [96990383],
  "tags": ["LLM", "AI", "GPT-4", "Claude", "模型對比"],
  "meta": {
    "internal_links": "ai-ide-agent-collaboration-survival-guide,ai-computing-power-rationing-survival,tech-pillar"
  },
  "user_confirmed": true
}
```

**預期響應**
```json
{
  "id": [NEW_POST_ID],
  "date": "2026-04-07T09:00:00",
  "link": "https://yololab.net/archives/llm-model-comparison-2026",
  "status": "publish"
}
```

**發佈後檢查**
1. 前台訪問確認：https://yololab.net/archives/llm-model-comparison-2026
2. Featured Image 是否正確顯示
3. 內部連結是否有效點擊

---

### 文章 2-5：重複上述流程

每篇執行 1 次 `posts.create`，調整以下參數：
- `title`、`excerpt`
- `date`（遞增 24 小時）
- `meta.internal_links`（根據文章對應調整）

---

## 📊 Batch 2：Music + Film（6 篇）

重複 Batch 1 流程，使用音樂/電影分類 ID。

---

## 🔍 Google Search Console 索引提交

### Step 1：準備 URL 列表

```json
{
  "urls": [
    "https://yololab.net/archives/llm-model-comparison-2026",
    "https://yololab.net/archives/prompt-engineering-complete-guide",
    "https://yololab.net/archives/ai-agent-framework-comparison",
    "https://yololab.net/archives/vector-database-selection-guide",
    "https://yololab.net/archives/ai-coding-assistant-workflow-optimization",
    "https://yololab.net/archives/taiwan-folk-music-90s-indie",
    "https://yololab.net/archives/electronic-music-production-complete-guide",
    "https://yololab.net/archives/classical-rock-art-collision",
    "https://yololab.net/archives/documentary-film-complete-guide",
    "https://yololab.net/archives/japanese-new-wave-cinema-revival",
    "https://yololab.net/archives/gender-studies-film-criticism"
  ]
}
```

### Step 2：使用 Google Search Console 手動提交

1. 進入 Google Search Console
2. 選擇 yololab.net 資源
3. 左側選單 → URL Inspection
4. 輸入第 1 個 URL → 點「Inspect」
5. 結果頁面點「Request Indexing」
6. 重複步驟 4-5 共 11 次

---

## ✅ 驗證清單

### 發佈後 1 小時

- [ ] 前台 11 篇文章全部可訪問
- [ ] Featured Image 全部正確顯示
- [ ] 內部連結全部有效
- [ ] Schema Markup 通過驗證（https://schema.org/validator）

### 發佈後 24 小時

- [ ] Google Search Console 顯示已提交 URL（Submitted for indexing）
- [ ] 至少 1-2 篇文章已在 GSC 中顯示為 Indexed

### 發佈後 7 天

- [ ] 全部 11 篇文章已被 Google 索引（GSC Coverage 顯示 11/11）
- [ ] 開始在 GSC Performance 報告中出現曝光數

---

## 🎯 成功標準

**發佈成功** ✅
- 11 篇文章全部 `status: publish`
- 前台全部可訪問，排版正確
- Google Search Console 顯示已提交索引

**SEO 成功** ✅（30 天內）
- 有機搜尋流量增長 ≥ 30%
- 至少 5 個目標 KW 進入 Top 20
- 支柱頁引薦流量增長

---

**何時執行？**
- 當 Agent 完成文章生成 ✅
- 將文章內容複製到此指令中
- 逐篇執行 posts.create
- 完成後立即提交 Google Search Console
