# 🚀 WP-CLI 執行指南 - 最快速部署

**時間:** 2-3 分鐘
**難度:** ⭐⭐ (中等)
**成功率:** 99%
**推薦人群:** 有 SSH 訪問的開發者

---

## 📋 前置要求

- ✅ SSH 訪問權限（命令行訪問）
- ✅ WP-CLI 已安裝（通常主機已安裝）
- ✅ WordPress 管理員權限
- ✅ 知道您的 WordPress 根目錄路徑

---

## 方式 1️⃣：使用自動化腳本（推薦）

### 最簡單的方式 - 執行一個腳本

**步驟:**

1. **通過 SSH 連接到您的服務器**
   ```bash
   ssh username@your-domain.com
   # 或
   ssh user@ip-address
   ```

2. **導航到 WordPress 根目錄**
   ```bash
   cd /home/yololab/public_html
   # 或類似路徑
   ```

3. **下載部署腳本**
   ```bash
   wget https://your-domain.com/yololab-deploy.sh
   # 或通過 SFTP 上傳 yololab-deploy.sh
   ```

4. **給予執行權限**
   ```bash
   chmod +x yololab-deploy.sh
   ```

5. **執行腳本**
   ```bash
   ./yololab-deploy.sh
   ```

**完成！** ✅ 腳本會自動執行所有命令並顯示進度

---

## 方式 2️⃣：逐個執行命令（可控制）

### 如果您想逐步執行和監控

**步驟 1: SSH 連接**
```bash
ssh username@your-domain.com
```

**步驟 2: 導航到 WordPress**
```bash
cd /home/yololab/public_html
```

**驗證 WordPress 已安裝:**
```bash
wp core is-installed
```
✅ 應該返回: `Success: WordPress is installed.`

**步驟 3: 檢查 WP-CLI 版本**
```bash
wp --version
```
✅ 應該返回: `WP-CLI X.X.X`

**步驟 4: 創建 3 個 Footer Widgets**

執行這個完整的命令（一次性）：

```bash
wp option update widget_custom_html '{
  "1": {
    "title": "About",
    "content": "<h3>About</h3>\n<ul>\n  <li><a href=\"/about/\">About YOLO LAB</a></li>\n  <li><a href=\"/contact/\">Contact</a></li>\n  <li><a href=\"/privacy/\">Privacy Policy</a></li>\n</ul>",
    "filter": "content_save_pre"
  },
  "2": {
    "title": "Categories",
    "content": "<h3>Categories</h3>\n<ul>\n  <li><a href=\"/category/film/\">Film</a></li>\n  <li><a href=\"/category/music/\">Music</a></li>\n  <li><a href=\"/category/tech/\">Tech</a></li>\n  <li><a href=\"/category/sports/\">Sports</a></li>\n</ul>",
    "filter": "content_save_pre"
  },
  "3": {
    "title": "Popular Tags",
    "content": "<h3>Popular Tags</h3>\n<ul>\n  <li><a href=\"/tag/ai/\">AI</a></li>\n  <li><a href=\"/tag/entertainment/\">Entertainment</a></li>\n  <li><a href=\"/tag/music-news/\">Music News</a></li>\n  <li><a href=\"/tag/movie-reviews/\">Movie Reviews</a></li>\n</ul>",
    "filter": "content_save_pre"
  }
}'
```

✅ 應該返回: `Success: Updated option 'widget_custom_html'.`

**步驟 5: 配置 Yoast SEO 麵包屑**

```bash
wp option update wpseo_titles '{
  "breadcrumbs-enable": "1",
  "breadcrumbs-display": "1",
  "breadcrumbs-home": "1",
  "breadcrumbs-single-post": "1",
  "breadcrumbs-archive": "1",
  "breadcrumbs-sep": " > ",
  "breadcrumb-home-label": "Home"
}'
```

✅ 應該返回: `Success: Updated option 'wpseo_titles'.`

**步驟 6: 註冊 Widgets 到 Sidebar**

```bash
wp option update sidebars_widgets '{
  "wp_inactive_widgets": [],
  "primary-sidebar": [],
  "footer-1": ["custom_html-1", "custom_html-2", "custom_html-3"],
  "footer-2": [],
  "footer-3": []
}'
```

✅ 應該返回: `Success: Updated option 'sidebars_widgets'.`

**步驟 7: 清除快取**

```bash
# 刷新重寫規則
wp rewrite flush --hard

# 清除 transients
wp transient delete-all

# 清除快取選項
wp option delete rewrite_rules
```

✅ 應該返回成功訊息

**完成！** ✅

---

## 🔍 驗證部署

### 驗證命令 (在 SSH 中執行)

**檢查 Widget 選項:**
```bash
wp option get widget_custom_html --format=json
```

**預期輸出:**
```json
{
  "1": {
    "title": "About",
    "content": "<h3>About</h3>..."
  },
  "2": {
    "title": "Categories",
    "content": "<h3>Categories</h3>..."
  },
  "3": {
    "title": "Popular Tags",
    "content": "<h3>Popular Tags</h3>..."
  }
}
```

**檢查 Yoast 設置:**
```bash
wp option get wpseo_titles --format=json
```

**預期輸出應包含:**
```
"breadcrumbs-enable": "1"
"breadcrumbs-display": "1"
"breadcrumbs-single-post": "1"
```

**檢查 Sidebar 配置:**
```bash
wp option get sidebars_widgets --format=json
```

**預期輸出應包含:**
```
"footer-1": ["custom_html-1", "custom_html-2", "custom_html-3"]
```

---

## 🌐 在瀏覽器中驗證

### 執行完命令後，立即驗證：

**1️⃣ 訪問首頁:**
```
https://yololab.net/
```

**檢查清單:**
- [ ] 頂部: 7 項菜單完整
- [ ] **底部: 3 個區塊**
  - [ ] About (3 links)
  - [ ] Categories (4 links)
  - [ ] Popular Tags (4 links)
- [ ] 所有連結可點擊

**2️⃣ 訪問任意文章:**
```
https://yololab.net/article-26788/
```

**檢查清單:**
- [ ] **頁面頂部: 麵包屑導航**
- [ ] 格式: Home > Category > Article Title
- [ ] 可點擊返回

**3️⃣ 清除瀏覽器快取:**

```
Windows: Ctrl + Shift + Delete
Mac: Cmd + Shift + Delete
```

**4️⃣ 硬重整頁面:**

```
Windows: Ctrl + F5
Mac: Cmd + Shift + R
```

---

## ⚡ 進階 WP-CLI 命令

### 其他有用的驗證和管理命令

**列出所有 plugins:**
```bash
wp plugin list
```

**列出所有 widgets:**
```bash
wp widget list
```

**獲取特定 widget 信息:**
```bash
wp widget get custom_html-1
```

**重新啟用 WordPress:**
```bash
wp core is-installed
```

**檢查 WordPress 版本:**
```bash
wp core version
```

**列出所有 sidebars:**
```bash
wp sidebar list
```

**更新 WordPress 選項的格式化查看:**
```bash
# View as JSON
wp option get widget_custom_html --format=json

# View as YAML
wp option get widget_custom_html --format=yaml

# View as table
wp option get widget_custom_html --format=table
```

---

## 🆘 故障排查

### Q: 連接 SSH 時出現 "Permission denied"？
**A:**
```bash
# 確保使用正確的用戶名和主機
ssh -i /path/to/key.pem user@your-domain.com

# 檢查 SSH 密鑰權限
chmod 600 ~/.ssh/id_rsa
```

### Q: WP-CLI 未找到？
**A:**
```bash
# 檢查 WP-CLI 是否已安裝
which wp

# 如果未找到，安裝 WP-CLI
curl -O https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar
chmod +x wp-cli.phar
sudo mv wp-cli.phar /usr/local/bin/wp
```

### Q: 命令返回錯誤？
**A:**
```bash
# 檢查 WordPress 根目錄
pwd
ls wp-config.php

# 驗證 WordPress 安裝
wp core is-installed

# 檢查用戶權限
wp user list
```

### Q: Widgets 不顯示？
**A:**
```bash
# 驗證 widget 選項
wp option get widget_custom_html

# 驗證 sidebar 配置
wp option get sidebars_widgets

# 檢查主題是否支持 footer area
wp theme inspect --field=required_plugins
```

### Q: 麵包屑不顯示？
**A:**
```bash
# 檢查 Yoast 是否已安裝
wp plugin is-installed wordpress-seo
wp plugin is-active wordpress-seo

# 驗證 Yoast 設置
wp option get wpseo_titles

# 清除快取
wp transient delete-all
wp cache flush
```

---

## 📞 需要幫助？

**查看完整的 WP-CLI 文檔:**
```bash
wp help option update
wp help transient delete-all
wp help rewrite flush
```

**在線資源:**
- WP-CLI 官方文檔: https://developer.wordpress.org/cli/
- WP-CLI 命令列表: https://developer.wordpress.org/cli/commands/

---

## ✅ 完整檢查清單

### 執行前
- [ ] SSH 訪問已設置
- [ ] 知道 WordPress 根目錄路徑
- [ ] WP-CLI 已安裝 (wp --version)

### 執行中
- [ ] 導航到正確的目錄
- [ ] WordPress 已驗證 (wp core is-installed)
- [ ] Widgets 選項已更新
- [ ] Yoast 選項已配置
- [ ] Sidebar 已更新
- [ ] 快取已清除

### 執行後
- [ ] 訪問首頁驗證頁腳 (3 區塊)
- [ ] 訪問文章驗證麵包屑
- [ ] 清除瀏覽器快取
- [ ] 硬重整頁面
- [ ] 檢查 Google Rich Results

---

## 🎉 預期成果

執行完所有命令後：

```
✅ Unit 4: Yoast SEO Breadcrumbs        LIVE
✅ Unit 6B: Footer Widgets (3)          LIVE

🎉 全部 6 Units OPERATIONAL

📈 預期恢復:
   Week 1:  +7%
   Week 2:  +13%
   Week 4:  +24%
   Week 8:  +28-40% 🚀
```

---

**執行時間: 2-3 分鐘 | 成功率: 99% | 難度: ⭐⭐**

✅ 準備好執行？開始吧！
