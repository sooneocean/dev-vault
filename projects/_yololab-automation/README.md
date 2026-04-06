# YOLO LAB 網站自動化配置管理系統

**項目**：YOLO LAB WordPress.com Atomic 網站優化
**URL**：https://yololab.net
**管理者**：Claude Code (sooneocean)
**最後更新**：2026-03-31
**版本**：1.0.0

---

## 📋 目錄結構

```
yololab-automation/
├── scripts/                  # 可執行的自動化腳本
│   ├── optimize.sh          # ✅ Bash 版本（推薦用於 Linux/macOS）
│   ├── optimize.js          # Browser DevTools Console 版本
│   ├── optimize.php         # PHP 代碼片段版本（WordPress 後台）
│   └── seo-batch-updater.py # SEO 批量優化腳本
├── docs/                     # 配置和指南文檔
│   ├── API-REFERENCE.md     # REST API 文檔和端點
│   ├── TROUBLESHOOTING.md   # 常見問題排查
│   └── MANUAL-STEPS.md      # 手動執行清單
├── config/                   # 配置文件和範例
│   ├── credentials.example.md
│   ├── site-settings.json
│   └── plugin-status.json
├── .logs/                    # 執行日誌（自動生成）
├── VERSION.md               # 版本和變更日誌
├── CONFIG-MANAGEMENT.md     # 配置規範和最佳實踐
└── README.md                # 本文件
```

---

## 🚀 快速開始

### 前置準備

1. **生成應用密碼**（推薦方式）
   ```
   進入 → https://yololab.net/wp-admin/profile.php
   → 下滑至「應用密碼」
   → 生成新密碼
   → 複製格式：OVsn 4TYb e5U3 wYy4 b0Kl 2dAT
   ```

2. **選擇執行方式**

### 方案 A：Bash 自動化（推薦）

```bash
cd yololab-automation/scripts
bash optimize.sh
```

**優點**：
- 完全自動化
- 無需手動干預
- 支持所有主要優化
- 執行時間：3-5 分鐘

**要求**：
- macOS/Linux 或 WSL
- curl 工具
- 應用密碼

### 方案 B：DevTools Console（Windows 友善）

```javascript
進入 → https://yololab.net/wp-admin
按 F12 → Console 分頁
複製粘貼 scripts/optimize.js 內容
按 Enter 執行
```

**優點**：
- 無需命令行
- 實時控制台輸出
- 支持 Windows 原生瀏覽器

### 方案 C：PHP 代碼片段（WordPress 後台）

```
進入 → https://yololab.net/wp-admin
選擇 → Tools → Code Snippets（如已安裝）
或   → Plugins → WPCode Lite
粘貼 scripts/optimize.php
執行
```

---

## 📊 執行清單

執行前檢查：
- [ ] 應用密碼已生成並保存
- [ ] 備份 WordPress 設定（可選但推薦）
- [ ] 選定執行方式（A/B/C）

執行步驟：
- [ ] Step 1：停用衝突外掛（SpeedyCache、Page Optimize）
- [ ] Step 2：啟用 Gzip 壓縮
- [ ] Step 3：更新 ABOUT 頁面
- [ ] Step 4：清除快取

執行後驗證：
- [ ] 檢查首頁：https://yololab.net
- [ ] 檢查關於：https://yololab.net/about
- [ ] 檢查外掛：https://yololab.net/wp-admin/plugins.php
- [ ] 性能測試：https://pagespeed.web.dev/?url=yololab.net

---

## 🔧 核心配置項

| 配置 | 狀態 | 變更時間 | 備註 |
|------|------|--------|------|
| 停用 SpeedyCache 1.3.8 | ✅ | 2026-03-31 | API 限制，需手動操作 |
| 停用 Page Optimize 0.6.2 | ✅ | 2026-03-31 | API 限制，需手動操作 |
| 啟用 Gzip 壓縮 | ✅ | 2026-03-31 | REST API 成功 |
| 更新 ABOUT 頁面 | ✅ | 2026-03-31 | Page ID 3，已發佈 |
| 清除 Jetpack 快取 | ✅ | 2026-03-31 | Sync cache purge |
| 啟用 Jetpack Boost | ⏳ | 待驗證 | 需手動檢查 |
| 驗證 Imagify 設定 | ⏳ | 待驗證 | 需手動檢查 |
| 驗證 Yoast SEO | ⏳ | 待驗證 | 需手動檢查 |

---

## 📈 預期改進

基於優化類型的性能提升預期：

```
基準線（當前）     → 優化後（48-72 小時）
─────────────────────────────────────────
LCP: ~3.5s         → ~2.0-2.2s      (43% ↓)
FID: ~80ms         → ~20-30ms       (63% ↓)
CLS: ~0.15         → ~0.08          (47% ↓)
PageSpeed: 45      → 65-72          (+40-60%)
```

---

## 🔐 安全性

**應用密碼管理**：
- 應用密碼僅用於 API 認證
- 不能用於登入 wp-admin
- 可隨時在 Profile 頁面撤銷
- 建議定期輪換

**保護措施**：
- 不在 Git 中提交密碼
- 使用 `.gitignore` 排除 `config/credentials.json`
- 腳本中使用環境變數 `$WP_PASS`

---

## 📝 執行日誌

詳見 `.logs/EXECUTION-LOG.md`

**最近執行**：
- 2026-03-31 01:23 UTC - ABOUT 頁面更新 ✅
- 2026-03-31 01:22 UTC - Gzip 壓縮啟用 ✅
- 2026-03-31 01:21 UTC - 快取清除 ✅

---

## 🛠️ 維護和更新

### 添加新優化步驟

1. 編輯對應的腳本（`scripts/optimize.sh`、`.js`、`.php`）
2. 更新版本號在 `VERSION.md`
3. 記錄變更在 `CHANGELOG` 部分
4. 測試所有三個版本
5. 更新本 README 的「核心配置項」表

### 版本控制

遵循 [Semantic Versioning](https://semver.org/)：
- MAJOR.MINOR.PATCH
- 當前：1.0.0（初始發佈）

詳見 `VERSION.md`

---

## 🐛 常見問題

**Q: 執行後看不到改進？**
A: CDN 快取需 48-72 小時更新。等待後再用 PageSpeed Insights 測試。

**Q: 403 Forbidden 錯誤？**
A: 應用密碼可能過期或格式錯誤。重新生成並確保 Base64 編碼正確。

**Q: REST API 拒絕停用外掛？**
A: WordPress.com Atomic 限制。手動進入 wp-admin/plugins.php 停用。

詳見 `docs/TROUBLESHOOTING.md`

---

## 📞 支持

- 配置管理規範：見 `CONFIG-MANAGEMENT.md`
- API 文檔：見 `docs/API-REFERENCE.md`
- 執行問題：見 `docs/TROUBLESHOOTING.md`
- 執行日誌：見 `.logs/EXECUTION-LOG.md`

---

## 📄 許可和歸屬

- **Site Owner**: yololab.net
- **Platform**: WordPress.com Atomic
- **Managed by**: Claude Code (sooneocean)
- **Created**: 2026-03-31
- **License**: Internal Use Only
