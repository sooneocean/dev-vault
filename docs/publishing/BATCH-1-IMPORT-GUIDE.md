# Batch 1 文章導入指南

## 📋 當前狀態

- **Article 1**：✅ 已發佈 (April 7, 2026 - via MCP)
- **Article 2-5**：⏳ 待導入 (April 8-11, 2026)
- **XML 檔案**：`batch-1-articles-import.xml` (準備就緒)

---

## 🚀 導入步驟

### Step 1: 訪問 WordPress 後台
進入 https://yololab.net/wp-admin/

### Step 2: 導航到匯入工具
```
工具 (Tools)
  → 匯入 (Import)
  → WordPress
```

### Step 3: 上傳 XML 檔案
- **位置**: `C:\DEX_data\Claude Code DEV\batch-1-articles-import.xml`
- 點擊「選擇檔案」
- 選擇 batch-1-articles-import.xml
- 點擊「上傳檔案並匯入」

### Step 4: 確認導入參數
- **用戶映射**: 預設映射至 yololab.life@gmail.com (自動)
- **下載檔案附件**: 取消勾選 (文章無需下載附件)
- 點擊「提交」

---

## ✅ 導入後驗證

導入完成後，檢查以下項目：

### 文章列表
```
後台 → 文章 → 所有文章
```

確認以下 5 篇文章出現：
1. ❓ LLM模型完整對比2026 - 狀態: **已發佈** (2026-04-07)
2. ❓ 提示詞工程完全指南 - 狀態: **已發佈** (2026-04-08)
3. ❓ AI智能體框架完全對比 - 狀態: **已發佈** (2026-04-09)
4. ❓ 向量數據庫選型指南 - 狀態: **已發佈** (2026-04-10)
5. ❓ AI編程助手工作流優化指南 - 狀態: **已發佈** (2026-04-11)

### 分類驗證
確認所有文章分配到: **AI 科技｜LLM 工具評測、人物分析、最新趨勢 | YOLO LAB** (ID: 96987489)

### SEO 標籤
確認每篇文章的標籤已分配 (Batch 1 文章預設標籤見下表)

---

## 📊 Batch 1 文章清單

| 序號 | 標題 | 日期 | Slug | 標籤 |
|------|------|------|------|------|
| 1 | LLM模型完整對比2026 | 2026-04-07 | llm-model-comparison-2026 | LLM, AI, GPT-4, Claude, 模型對比 |
| 2 | 提示詞工程完全指南 | 2026-04-08 | prompt-engineering-complete-guide | 提示詞, Prompt, ChatGPT, Claude |
| 3 | AI智能體框架完全對比 | 2026-04-09 | ai-agent-framework-comparison | AI Agent, LangGraph, Claude SDK |
| 4 | 向量數據庫選型指南 | 2026-04-10 | vector-database-selection-guide | 向量數據庫, Embedding, RAG |
| 5 | AI編程助手工作流優化 | 2026-04-11 | ai-coding-assistant-workflow-optimization | GitHub Copilot, Claude Code |

---

## 🔍 進階檢查 (如有需要)

### 檢查內部連結
每篇文章應包含指向以下支柱頁面的內部連結：
- `ai-ide-agent-collaboration-survival-guide`
- `ai-computing-power-rationing-survival`
- `tech-pillar`

位置: 後台 → 文章 → [文章名稱] → 編輯 → 向下查看 Meta 欄位

### 檢查發佈日期與時間
確認發佈時間為:
- Article 1-5: **09:00** (台灣時間)

位置: 後台 → 文章 → [文章名稱] → 發佈時間

---

## ⚠️ 常見問題

### Q: 導入失敗怎麼辦?
A: 重試上傳，或嘗試以下步驟:
1. 檢查瀏覽器控制台 (F12) 錯誤訊息
2. 確認檔案編碼為 UTF-8
3. 清除瀏覽器快取後重試

### Q: 文章發佈為草稿狀態?
A: 在文章編輯畫面手動變更狀態為「發佈」

### Q: 部分文章內容不完整?
A: XML 中的文章 2-5 為摘要版本。若需完整內容:
- 編輯文章 → 複製完整內容
- 來源: `docs/articles/` 和 `resources/` 目錄

---

## 📍 下一步

✅ **導入完成後，回報確認**

系統將自動執行:
1. Google Search Console 提交 11 個 URL
2. 內部連結驗證
3. 發佈狀態日誌記錄

導入時間預估: **5-10 分鐘**

