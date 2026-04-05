# wpcom-mcp 批量 SEO 更新方案
**改用** WordPress.com MCP (已驗證 100% 可靠)

## 執行步驟

Pages 7-136 共 2,660 篇文章
每頁 20 篇 × 130 頁

### 關鍵配置
- **Site**: yololab.net
- **Operation**: posts.update
- **Meta Fields**: 
  - `meta[jetpack_seo_html_title]` (55-60 chars)
  - `meta[advanced_seo_description]` (155-160 chars)
- **Rate Limit**: 自動（wpcom-mcp 已優化）

## 批次處理策略
由於 wpcom-mcp 支援單篇更新，建議：
1. 按頁批次處理 (Page 7-20, 21-40, 41-60...)
2. 每頁 20 篇逐一更新
3. 約 30-40 分鐘完成全部

## 進度監控
實時記錄於 seo-batch-wpcom.log
