# Site Optimizer Skill 設置指南

## 📦 已安裝的文件

```
.claude/
├── lib/
│   └── site-optimizer-command.js      ← Slash Command 整合
└── skills/
    ├── SITE-OPTIMIZER.md              ← 完整文檔
    ├── SKILL-SETUP-GUIDE.md           ← 本文件
    └── site-optimizer-config.json     ← 配置和網站信息

scripts/
├── image-alt-text-optimizer.js        ← 核心優化引擎
└── site-optimizer.js                  ← CLI 包裝器
```

---

## 🚀 快速開始

### 1. 設置環境變數

```bash
# 在 .env 或 shell 中設置
export WPCOM_TOKEN="your_wordpress_com_bearer_token"
export ANTHROPIC_API_KEY="your_claude_api_key"

# 或在 .env 文件中
echo "WPCOM_TOKEN=xxx" >> .env
echo "ANTHROPIC_API_KEY=xxx" >> .env
```

### 2. 驗証環境

```bash
# 測試連接（小樣本）
node scripts/site-optimizer.js --site yololab --type image-alt --phase scan --sample 5
```

### 3. 在 Claude Code 中使用

#### 方法 A：使用 Skill 工具

```claude
Skill("site-optimizer", "--site yololab --type image-alt --phase scan --sample 10")
```

#### 方法 B：直接命令（如已配置快捷方式）

```
/site-optimizer --site yololab --type image-alt --phase scan --sample 10
```

#### 方法 C：手動執行腳本

```bash
node scripts/site-optimizer.js --site yololab --type image-alt --phase scan --sample 10
```

---

## 📋 使用示例

### 場景 1: 新網站優化

#### 步驟 1: 配置新網站

編輯 `.claude/skills/site-optimizer-config.json`：

```json
{
  "siteConfig": {
    "mynewsite": {
      "siteId": 987654321,
      "domain": "mynewsite.com",
      "language": "zh_TW",
      "authMethod": "bearer-token",
      "enabledOptimizations": ["image-alt"]
    }
  }
}
```

#### 步驟 2: 掃描和評估

```bash
# 快速掃描（10 篇文章）
node scripts/site-optimizer.js --site mynewsite --type image-alt --phase scan --sample 10

# 查看結果：seo-optimization-output/image-audit-report.json
```

#### 步驟 3: 執行優化

```bash
# Dry-run（查看但不更新）
node scripts/site-optimizer.js --site mynewsite --type image-alt --phase apply-featured --dry-run

# 實際執行
node scripts/site-optimizer.js --site mynewsite --type image-alt --phase apply-featured

# 內嵌圖片
node scripts/site-optimizer.js --site mynewsite --type image-alt --phase apply-inline
```

#### 步驟 4: 查看報告

```bash
node scripts/site-optimizer.js --site mynewsite --type image-alt --phase report

# 查看結果：seo-optimization-output/alt-text-optimization-report.md
```

### 場景 2: 多站點管理

假設你管理 3 個網站：

```json
{
  "siteConfig": {
    "yololab": { ... },
    "myecommerce": { ... },
    "myblog": { ... }
  }
}
```

批量掃描：

```bash
for site in yololab myecommerce myblog; do
  echo "掃描 $site..."
  node scripts/site-optimizer.js --site $site --type image-alt --phase scan --sample 20
done
```

### 場景 3: 定期優化流程

```bash
#!/bin/bash
# optimize-all-sites.sh

SITES=("yololab" "myecommerce" "myblog")

for site in "${SITES[@]}"; do
  echo "=== 優化 $site ==="

  # 掃描
  node scripts/site-optimizer.js --site $site --type image-alt --phase scan

  # 應用
  node scripts/site-optimizer.js --site $site --type image-alt --phase apply-featured
  node scripts/site-optimizer.js --site $site --type image-alt --phase apply-inline

  # 報告
  node scripts/site-optimizer.js --site $site --type image-alt --phase report

  echo "✅ $site 優化完成\n"

  # 等待 5 分鐘後再優化下一個網站（避免 API 限流）
  sleep 300
done
```

---

## 🔧 配置參考

### site-optimizer-config.json 結構

```json
{
  "name": "site-optimizer",
  "version": "1.0.0",
  "supportedOptimizations": {
    "image-alt": {
      "name": "圖片 ALT 文字優化",
      "phases": ["scan", "generate", "apply-featured", "apply-inline", "report", "rollback"],
      "features": [...]
    }
  },
  "siteConfig": {
    "site-name": {
      "siteId": 123456789,          // WordPress.com Site ID
      "domain": "site.com",          // 網站域名
      "language": "zh_TW",          // 語言（影響 ALT text 生成）
      "authMethod": "bearer-token", // 認證方式
      "enabledOptimizations": [...]  // 啟用的優化類型
    }
  }
}
```

### 環境變數

| 變數 | 用途 | 範例 |
|------|------|------|
| `WPCOM_TOKEN` | WordPress.com Bearer Token | `eyJhbGc...` |
| `ANTHROPIC_API_KEY` | Claude API Key | `sk-ant-...` |
| `SITE_CONFIG_PATH` | 自訂配置文件路徑 | `./custom-config.json` |

---

## 📊 輸出和報告

### 掃描輸出

執行 `--phase scan` 後，查看：

```bash
# 掃描報告
seo-optimization-output/image-audit-report.json

# 內容：
# {
#   "totalPosts": 2728,
#   "summary": {
#     "featuredMedia": { "total": 1500, "needsAlt": 1200, ... },
#     "inlineImages": { "total": 5000, "needsAlt": 3800, ... }
#   },
#   "posts": [...]
# }
```

### 優化報告

執行 `--phase report` 後，查看：

```bash
# 優化報告（Markdown）
seo-optimization-output/alt-text-optimization-report.md

# 內容：
# - 執行摘要（表格）
# - 品質分析（長度分布）
# - 失敗項目清單
# - 後續建議
```

### 備份文件

執行 `--phase apply-featured` 或 `--phase apply-inline` 後：

```bash
# Featured Media 備份
seo-optimization-output/alt-text-backup-featured.json

# 內嵌圖片備份
seo-optimization-output/alt-text-backup-inline.json

# 內容：{ "created": "...", "items": [{ "mediaId": 123, "originalAlt": "..." }, ...] }
```

### 狀態文件（用於斷點續傳）

```bash
seo-optimization-output/state_alttext_featured.json
seo-optimization-output/state_alttext_inline.json

# 內容：{ "processed": [...], "failed": [...], "skipped": [...], "stats": {...} }
```

---

## 🐛 故障排除

### 認證失敗（401）

```bash
# 檢查 token
echo $WPCOM_TOKEN

# 如果空白，重新設置
export WPCOM_TOKEN="your_token"

# 測試連接
node scripts/site-optimizer.js --site yololab --type image-alt --phase scan --sample 1
```

### API Rate Limit（429）

腳本會自動處理，但如果仍有問題：

```bash
# 減小批次
node scripts/site-optimizer.js --site yololab --type image-alt --phase scan --sample 50

# 跳過驗証加速
node scripts/site-optimizer.js --site yololab --type image-alt --phase apply-featured --skip-verification
```

### 斷點續傳失敗

```bash
# 檢查 state 文件是否存在
ls seo-optimization-output/state_alttext_*.json

# 如果損壞，刪除並重新開始
rm seo-optimization-output/state_alttext_*.json

# 重新執行（會從頭開始）
node scripts/site-optimizer.js --site yololab --type image-alt --phase apply-featured
```

### 回滾失敗

```bash
# 檢查備份是否存在
ls seo-optimization-output/alt-text-backup-*.json

# 如果缺失，無法回滾。下次執行會產生新備份。

# 手動恢復（如有備份）
node scripts/site-optimizer.js --site yololab --type image-alt --phase rollback --target all
```

---

## 📈 監控和效果評估

### 前後對比

```bash
# 優化前
node scripts/site-optimizer.js --site yololab --type image-alt --phase scan > scan-before.txt

# 優化後（2-4 週）
node scripts/site-optimizer.js --site yololab --type image-alt --phase scan > scan-after.txt

# 比較改變
diff scan-before.txt scan-after.txt
```

### Google Search Console 監控

優化後 2-4 週在 Google Search Console 中檢查：

1. **Performance**
   - 圖片搜尋印象增加
   - CTR 變化

2. **Coverage**
   - 無效結構化數據減少

3. **Enhancements**
   - Rich Results 增加

---

## 🔐 安全性注意事項

1. **Token 管理**
   - 不要在代碼中硬編碼 token
   - 使用環境變數或 .env（.gitignored）
   - 定期輪換 token

2. **數據備份**
   - 始終備份在更新前（自動進行）
   - 定期備份備份文件本身
   - 測試回滾流程

3. **API 配額**
   - 監控 Claude API 使用量
   - 監控 WordPress.com API 速率限制
   - 在非尖峰時段運行大批次

---

## 📚 相關文檔

- **完整文檔**：`.claude/skills/SITE-OPTIMIZER.md`
- **配置文件**：`.claude/skills/site-optimizer-config.json`
- **核心代碼**：`scripts/image-alt-text-optimizer.js`
- **CLI 包裝器**：`scripts/site-optimizer.js`
- **命令整合**：`.claude/lib/site-optimizer-command.js`

---

## ✅ 檢查清單

優化前的準備：

- [ ] WPCOM_TOKEN 已設置
- [ ] ANTHROPIC_API_KEY 已設置
- [ ] 網站已在配置中
- [ ] 已執行 --sample 10 測試
- [ ] 已檢查掃描報告

優化中的監控：

- [ ] 定期檢查進度（使用 --resume）
- [ ] 監控失敗率
- [ ] 備份文件完整

優化後的驗證：

- [ ] 已查看最終報告
- [ ] 已驗証隨機 10 篇文章
- [ ] 已記錄前後統計
- [ ] 已規劃後續 Google 監控

---

## 🎯 下一步

1. **立即**：為你的網站配置並執行掃描
2. **本週**：執行首個優化（dry-run + 實際執行）
3. **後續**：設置定期優化流程
4. **2-4週後**：在 GSC 中評估效果

有問題？查看文檔或檢查故障排除部分。祝優化順利！ 🚀
