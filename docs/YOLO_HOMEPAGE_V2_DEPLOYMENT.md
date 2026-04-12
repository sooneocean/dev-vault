# YOLO LAB 首頁 v2（超現代化）部署指南

**Version:** 2.0 Ultra-Modern
**Date:** 2026-04-08
**Site:** yololab.net (Blog ID: 133512998)

---

## 快速部署（2 分鐘）

### 方式 A：手動部署（推薦）

#### Step 1：備份現有首頁
1. 進入 **WordPress 後台** → Pages
2. 找到首頁（Homepage）
3. 複製現有內容存檔（以防回滾）

#### Step 2：貼入新 HTML 內容
1. 編輯首頁 → 切換到 **代碼編輯器**
2. **完全刪除**現有代碼
3. 複製 `seo-optimization-output/homepage-v2-ultramodern.html` 全部內容
4. **貼入**代碼編輯器
5. 點擊 **Publish / Update**

#### Step 3：驗證視覺效果
1. 訪問 **https://yololab.net**（或首頁 URL）
2. 檢查以下元素：
   - ✅ 深黑 Hero 區域有綠色霓虹光暈
   - ✅ 統計條顯示 898+、4、2025
   - ✅ 毛玻璃卡片在深色背景
   - ✅ 4 個分類卡片有色標（紅、紫、藍、綠）
   - ✅ 最新文章是雜誌風格（左大右小）
3. 用 **Chrome DevTools** (F12) 測試響應式：
   - 桌面 (1200px+)
   - 平板 (768px-1024px)
   - 手機 (320px-767px)

---

## 新設計亮點

### 🌌 Hero 區域
- **深黑漸層背景** + 動畫色移 (`@keyframes gradientShift`)
- **霓虹光暈 H1** — 綠色 `text-shadow` 效果
- **分類 Tag Pills** — 黃色半透明背景
- **2 個 CTA 按鈕** — Primary (綠) + Secondary (玻璃)

### 📊 統計條
- **深灰橫條** — 上下邊框亮點
- 898+、4、2025 三個數據展示

### 🔮 Glassmorphism 卡片
- **毛玻璃效果** — `backdrop-filter: blur(16px)`
- **半透明邊框** — `border: 1px solid rgba(255,255,255,0.15)`
- **Hover 動畫** — 向上浮動 + 綠色光暈

### 🎨 分類網格（4 色塊）
- **電影 (紅)** — `#e74c3c`
- **音樂 (紫)** — `#6a6ab1`
- **科技 (藍)** — `#3498db`
- **運動 (綠)** — `#418a2c`
- 每欄頂部有 **4px 色塊線** + 懸停擴大效果

### 📰 最新文章雜誌版
- **左側英雄文章** — 大圖 + 標題
- **右側 5 篇列表** — 日期 + 分類標籤 + 標題
- **Hover 效果** — 文字變色 + 左縮進

---

## 進階部署（可選）

### 添加全局 CSS（更持久）

如果你要確保樣式在所有更新後都保留，貼入 Additional CSS：

1. 進入 **Appearance > Customize** (或 **Appearance > Additional CSS**)
2. 複製 `seo-optimization-output/homepage-v2-custom.css` 全部內容
3. **貼入** Additional CSS 框
4. 點擊 **Publish**

**好處：**
- CSS 獨立於頁面內容
- 主題更新不會丟失樣式
- 可跨多個頁面使用

---

## 圖片資源（需要替換）

HTML 中引用的圖片 URL：
```
https://yololab.net/wp-content/uploads/hero-bg.jpg         → Hero 背景圖
https://yololab.net/wp-content/uploads/featured-hero.jpg   → 主特色文章
https://yololab.net/wp-content/uploads/post-2.jpg          → 特色卡片 2
https://yololab.net/wp-content/uploads/post-3.jpg          → 特色卡片 3
https://yololab.net/wp-content/uploads/post-4.jpg          → 特色卡片 4
https://yololab.net/wp-content/uploads/latest-hero.jpg     → 最新文章英雄圖
```

**替換方式：**
1. 上傳你的圖片到 WordPress 媒體庫
2. 編輯首頁 → 尋找 `<img src="..."`
3. 用新圖片 URL 替換

**推薦尺寸：**
| 圖片 | 寬 × 高 | 用途 |
|------|---------|------|
| hero-bg.jpg | 1920×400 | Hero 背景（或實際高度）|
| featured-*.jpg | 800×500 | 特色卡片（16:10） |
| latest-hero.jpg | 800×400 | 雜誌版英雄圖 |

---

## 自訂修改

### 改變主色
在 HTML 代碼或 CSS 中找到 `--color-primary: #418a2c` 改為你的顏色。

### 改變分類色標
CSS 中的 `--color-film`, `--color-music`, `--color-tech`, `--color-sports`。

### 調整 Hero 高度
在 `.yolo-hero { min-height: 600px; }` 改為你想要的像素。

### 改變卡片數量
編輯 `.yolo-featured-grid` 的 `grid-template-columns` 或添加/刪除 `.yolo-glass-card` 元素。

---

## Dark Mode（自動）

設計已支持系統深色模式 (`@media (prefers-color-scheme: dark)`)。

**測試方式：**
1. Chrome DevTools → **Cmd+Shift+P** (Mac) 或 **Ctrl+Shift+P** (Windows)
2. 輸入 `Dark mode`
3. 點擊 **Emulate CSS media feature prefers-color-scheme**
4. 選擇 **prefers-color-scheme: dark**
5. 網站自動切換深色配色

---

## 故障排除

| 問題 | 解決方案 |
|------|--------|
| 代碼編輯器顯示錯誤 | 檢查是否有未閉合的 HTML 標籤 — 複製粘貼時確保完整 |
| 卡片沒有毛玻璃效果 | 檢查瀏覽器是否支持 `backdrop-filter`（需 Chrome 76+ / Safari 9+） |
| 霓虹光暈不明顯 | 檢查首頁背景是否是深色 — 使用 Cover Block 設深黑背景 |
| 圖片顯示不了 | 檢查 URL 是否正確 — 在瀏覽器開發者工具查看 404 錯誤 |
| 響應式顯示怪怪的 | 清除瀏覽器緩存（Ctrl+Shift+Del） — 強制刷新 Ctrl+F5 |

---

## 驗證清單

部署後，確保以下都正常：

- [ ] 首頁可訪問（無 404）
- [ ] Hero 區域顯示綠色霓虹光暈
- [ ] Stats 條顯示 3 個數字
- [ ] Featured 卡片在深色背景 + 有 Hover 效果
- [ ] 4 個分類卡片顯示 + 色塊線可見
- [ ] 最新文章雜誌版布局正確（左大右小）
- [ ] 桌面版本響應式正常
- [ ] 平板版本響應式正常（2 欄）
- [ ] 手機版本響應式正常（1 欄）
- [ ] Dark Mode 自動切換（DevTools 測試）
- [ ] 所有連結正確（瀏覽器無 404）

---

## 性能提示

1. **優化圖片** — 使用 WebP 或壓縮 JPG（<150KB）
2. **字體加載** — Pixeloid Sans 已內嵌，無額外請求
3. **CSS 動畫** — `backdrop-filter` 可能在低端設備卡，可關閉
4. **禁用不需要的元素** — 刪除 HTML 中不需要的卡片
5. **Lighthouse 檢測** — 進入 https://pagespeed.web.dev 檢測性能

---

## 回滾方案

如果新設計不滿意，回到舊版本：

1. 進入 **Pages > 首頁**
2. 點擊右上角 **Revisions**（修訂版本）
3. 選擇之前的版本
4. 點擊 **Restore**

---

## 下一步優化

### Phase 4：添加 Breadcrumb 結構化數據
- 所有頁面添加 BreadcrumbList JSON-LD

### Phase 5：內部連結優化
- 從首頁自動鏈接到相關文章

### Phase 6：分類頁升級
- 套用 Glassmorphism 卡片到分類存檔頁

---

## 支持

**文件位置：**
- HTML: `seo-optimization-output/homepage-v2-ultramodern.html`
- CSS: `seo-optimization-output/homepage-v2-custom.css`
- 本指南: `docs/YOLO_HOMEPAGE_V2_DEPLOYMENT.md`

**問題回報：**
- 檢查 WordPress.com 系統狀態：https://wordpress.com/status
- 查看主題文檔：https://wordpress.com/support/themes

---

**部署日期：** 2026-04-08
**設計師：** Claude Code
**版本：** v2.0 Ultra-Modern
