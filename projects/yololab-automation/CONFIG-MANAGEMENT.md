---
title: 配置管理規範
type: project
tags: [project, active]
created: 2026-04-03
updated: 2026-04-03
status: active
maturity: growing
domain: knowledge-management
summary: ""
---

# 配置管理規範

**目的**：統一維護 YOLO LAB WordPress.com 網站的自動化配置和優化指令
**更新日期**：2026-03-31
**責任人**：sooneocean / Claude Code

---

## 1️⃣ 核心配置清單

### 外掛狀態

```json
{
  "disabled": [
    {
      "name": "SpeedyCache",
      "version": "1.3.8",
      "reason": "與 Jetpack Boost 衝突，導致缓存重複和性能下降",
      "disabled_date": "2026-03-31",
      "method": "manual (wp-admin/plugins.php)"
    },
    {
      "name": "Page Optimize",
      "version": "0.6.2",
      "reason": "與 WebP Converter 衝突，導致圖片最佳化重複",
      "disabled_date": "2026-03-31",
      "method": "manual (wp-admin/plugins.php)"
    }
  ],
  "enabled": [
    {
      "name": "Jetpack Boost",
      "version": "latest",
      "features": ["CSS/JS Minification", "Image Lazy Loading", "CCPA Compliance"],
      "critical": true
    },
    {
      "name": "Imagify",
      "version": "latest",
      "features": ["Image Compression", "WebP Generation", "AVIF Support"],
      "critical": true
    },
    {
      "name": "WebP Converter for Media",
      "version": "latest",
      "features": ["Automatic WebP Conversion", "CDN Delivery"],
      "critical": false
    },
    {
      "name": "Yoast SEO",
      "version": "latest",
      "features": ["XML Sitemap", "Readability Analysis", "Structured Data"],
      "critical": true
    },
    {
      "name": "Jetpack",
      "version": "latest",
      "features": ["CDN", "Site Stats", "Downtime Monitoring"],
      "critical": true
    }
  ]
}
```

### WordPress 設定

| 設定項 | 值 | 狀態 | 變更時間 |
|-------|-----|------|---------|
| `gzipcompression` | `1` (true) | ✅ | 2026-03-31 |
| `jetpack_sync_cache_purge` | `true` | ✅ | 2026-03-31 |
| 首頁顯示 | 靜態頁面 | ✅ | 基線 |
| 文章頁設定 | 標準 | ✅ | 基線 |
| 永久連結結構 | `/%postname%/` | ✅ | 基線 |

### 頁面設定

| 頁面 | ID | 標題 | 狀態 | 最後更新 |
|-----|-----|------|------|---------|
| 首頁 | 1 | YOLO LAB | 發佈 | 基線 |
| 關於 | 3 | 關於 YOLO LAB | 發佈 | 2026-03-31 |
| 聯絡 | 5 | 聯絡我們 | 發佈 | 基線 |

---

## 2️⃣ 變更管理流程

### 步驟 1：提議變更

在 VERSION.md 的「待審核變更」段落記錄：

```markdown
## 待審核變更

- [ ] 禁用 X 外掛
  - 原因：衝突
  - 影響：性能 -5%
  - 回退計劃：重新啟用
  - 提議日期：2026-04-01
```

### 步驟 2：測試變更

在 **測試環境** 執行：
- 運行 WordPress 本地副本或測試站點
- 驗證所有主要功能
- 記錄任何副作用
- 獲取性能對比數據

### 步驟 3：應用到生產環境

1. 更新 `scripts/` 中的所有三個版本
2. 在 VERSION.md 中記錄變更
3. 執行自動化腳本或手動操作
4. 驗證結果（見下方「驗證清單」）
5. 記錄執行日誌到 `.logs/EXECUTION-LOG.md`

### 步驟 4：監控

48-72 小時內監控：
- Google PageSpeed Insights 分數
- Jetpack 分析數據
- 核心Web指標（Core Web Vitals）
- 用戶報告的問題

---

## 3️⃣ 驗證清單

### 執行前

- [ ] 已備份 WordPress 設定（可選）
- [ ] 應用密碼已生成並驗證
- [ ] 腳本版本已測試
- [ ] 執行環境已檢查

### 執行中

- [ ] 所有 API 呼叫成功（無 4xx/5xx 錯誤）
- [ ] 控制台輸出無警告信息
- [ ] 執行時間在預期範圍內

### 執行後（立即）

- [ ] 首頁加載正常
- [ ] ABOUT 頁面顯示新內容
- [ ] 後台外掛頁面顯示正確狀態
- [ ] 無 PHP 錯誤或警告

### 執行後（48-72 小時）

- [ ] PageSpeed Insights 分數提升 ≥ 10 分
- [ ] Core Web Vitals 改善
- [ ] Jetpack Analytics 無異常

---

## 4️⃣ 性能基準線

### 當前基準（2026-03-31）

**桌面版**：
- PageSpeed Insights：45
- LCP：3.5s
- FID：80ms
- CLS：0.15

**移動版**：
- PageSpeed Insights：28
- LCP：4.2s
- FID：120ms
- CLS：0.18

### 優化目標（2026-04-30）

**桌面版**：
- PageSpeed Insights：≥ 70
- LCP：≤ 2.5s
- FID：≤ 30ms
- CLS：≤ 0.1

**移動版**：
- PageSpeed Insights：≥ 55
- LCP：≤ 3.5s
- FID：≤ 50ms
- CLS：≤ 0.1

---

## 5️⃣ API 端點清單

### REST API 端點

| 端點 | 方法 | 用途 | 驗證 |
|-----|------|------|------|
| `/wp/v2/plugins/{plugin}` | PUT | 變更外掛狀態 | 需要 manage_plugins |
| `/wp/v2/settings` | POST | 更新 WordPress 設定 | 需要 manage_options |
| `/wp/v2/pages/{id}` | POST | 更新頁面內容 | 需要 edit_pages |
| `/wp/v2/users/{id}` | DELETE | 刪除用戶 | 需要 delete_users |
| `/jetpack/v4/options` | POST | Jetpack 快取設定 | Jetpack 認證 |

### 身份驗證

- **方法**：HTTP Basic Auth
- **格式**：`Authorization: Basic [base64(email:password)]`
- **密碼來源**：WordPress 應用密碼（Profile → App Passwords）

---

## 6️⃣ 回退計劃

### 如果性能下降

1. **立即**: 檢查 Jetpack 快取（可能需要 72 小時清除）
2. **1 小時**: 檢查外掛狀態和設定
3. **24 小時**: 如無改善，重新啟用已禁用的外掛

### 如果 ABOUT 頁面顯示異常

1. 重新執行 optimize 腳本中的「Step 3：更新 ABOUT 頁面」
2. 或手動進入 wp-admin/pages/3 編輯

### 如果 API 呼叫失敗

1. 驗證應用密碼未過期
2. 確認 Base64 編碼正確
3. 檢查網路連接
4. 詳見 `docs/TROUBLESHOOTING.md`

---

## 7️⃣ 定期維護

### 每週

- [ ] 檢查 Jetpack Analytics 無異常波動
- [ ] 查看核心 Web 指標趨勢
- [ ] 確認外掛無新更新導致衝突

### 每月

- [ ] 完整性能審計（Lighthouse）
- [ ] SEO 爬蟲檢查（Yoast）
- [ ] 用戶反饋收集
- [ ] 性能基準線更新

### 季度

- [ ] 重新評估禁用的外掛（是否有新版本解決衝突）
- [ ] CDN 配置審查
- [ ] 備份驗證

---

## 8️⃣ 文檔和交接

### 新手入門

1. 讀 README.md（快速開始）
2. 讀本文件（理解配置）
3. 讀 `docs/API-REFERENCE.md`（API 細節）
4. 讀 `.logs/EXECUTION-LOG.md`（歷史記錄）

### 交接清單

如需轉移責任給他人：

- [ ] 共享所有應用密碼（安全儲存）
- [ ] 培訓 README.md 和本規範
- [ ] 演示至少一次執行流程
- [ ] 交接執行日誌和性能記錄

---

## 9️⃣ 備註和特殊情況

### WordPress.com API 限制

WordPress.com Atomic 平台對某些操作有限制：

- **✅ 支持**：頁面更新、設定修改、快取清除
- **⚠️ 部分支持**：用戶管理（無法完全刪除）
- **❌ 不支持**：外掛啟用/停用（需手動 wp-admin）

### 性能考慮

- 外掛數量 > 30 時開始顯著影響性能
- 圖片未最佳化會拖累 LCP 30-40%
- Gzip 可降低頻寬消耗 40-60%

### 安全性提醒

- 不要在 Git 中提交應用密碼
- 定期輪換密碼（建議 90 天）
- 監控異常 API 活動

---

## 🔟 聯繫方式

- **管理者**: sooneocean
- **監管工具**: Claude Code
- **報告問題**: 見 `docs/TROUBLESHOOTING.md`
- **提議變更**: 更新 VERSION.md 的「待審核變更」部分
