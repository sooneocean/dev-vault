# REST API 參考文檔

**平台**：WordPress.com Atomic
**API 版本**：wp/v2
**認證**：HTTP Basic Auth (應用密碼)
**最後更新**：2026-03-31

---

## 📌 身份驗證

### 應用密碼生成

1. 進入 **https://yololab.net/wp-admin/profile.php**
2. 下滑至「應用密碼」區塊
3. 輸入應用名稱（例：「自動化優化」）
4. 點擊「生成新密碼」
5. 複製格式：`OVsn 4TYb e5U3 wYy4 b0Kl 2dAT`

### 認證頭構建

```bash
# 基本格式
Authorization: Basic [base64(email:password)]

# 範例
AUTH=$(printf "yololab.life@gmail.com:OVsn 4TYb e5U3 wYy4 b0Kl 2dAT" | base64 -w 0)
curl -H "Authorization: Basic $AUTH" [endpoint]

# Bash 自動化
WP_USER="yololab.life@gmail.com"
WP_PASS="OVsn 4TYb e5U3 wYy4 b0Kl 2dAT"
AUTH=$(printf "$WP_USER:$WP_PASS" | base64 -w 0)
```

---

## 🔌 核心端點

### 1. 插件管理

#### 列出所有插件
```
GET /wp-json/wp/v2/plugins
Authorization: Basic [AUTH]

Response (200 OK):
[
  {
    "plugin": "speedycache/speedycache.php",
    "status": "inactive",
    "name": "SpeedyCache",
    "version": "1.3.8"
  },
  ...
]
```

#### 更新插件狀態

**⚠️ 限制**：WordPress.com 不支持通過 API 更改插件狀態

```
PUT /wp-json/wp/v2/plugins/{plugin_path}
Authorization: Basic [AUTH]
Content-Type: application/json

{
  "status": "active" | "inactive"
}

Error (404 Not Found):
{
  "code": "rest_no_route",
  "message": "No route was found matching the request"
}
```

**解決方案**：手動訪問 https://yololab.net/wp-admin/plugins.php

---

### 2. 設定管理

#### 獲取所有設定
```
GET /wp-json/wp/v2/settings
Authorization: Basic [AUTH]

Response (200 OK):
{
  "title": "YOLO LAB",
  "description": "科技與媒體數據實驗室",
  "url": "https://yololab.net",
  "gzipcompression": false,
  ...
}
```

#### 更新設定

```
POST /wp-json/wp/v2/settings
Authorization: Basic [AUTH]
Content-Type: application/json

{
  "gzipcompression": true
}

Response (200 OK):
{
  "gzipcompression": true,
  "jetpack_sync_cache_purge": false,
  ...
}
```

**常用設定參數**：
- `gzipcompression` (bool)：啟用 Gzip 壓縮
- `jetpack_sync_cache_purge` (bool)：清除 Jetpack 快取
- `blog_public` (int)：0 = 私密，1 = 公開

---

### 3. 頁面管理

#### 列出所有頁面
```
GET /wp-json/wp/v2/pages
Authorization: Basic [AUTH]

Response (200 OK):
[
  {
    "id": 1,
    "title": { "rendered": "首頁" },
    "slug": "home",
    "status": "publish"
  },
  {
    "id": 3,
    "title": { "rendered": "關於 YOLO LAB" },
    "slug": "about",
    "status": "publish"
  }
]
```

#### 獲取特定頁面
```
GET /wp-json/wp/v2/pages/{id}
Authorization: Basic [AUTH]

Response (200 OK):
{
  "id": 3,
  "title": { "raw": "關於 YOLO LAB" },
  "content": { "raw": "[HTML 內容]", "rendered": "[渲染後的 HTML]" },
  "status": "publish",
  "modified": "2026-03-31T01:23:09"
}
```

#### 更新頁面

```
POST /wp-json/wp/v2/pages/{id}
Authorization: Basic [AUTH]
Content-Type: application/json

{
  "title": "關於 YOLO LAB",
  "content": "<!-- wp:cover ... -->...",
  "status": "publish"
}

Response (200 OK):
{
  "id": 3,
  "title": { "raw": "關於 YOLO LAB" },
  "content": { "raw": "[HTML]", "rendered": "[渲染後]" },
  "status": "publish",
  "modified": "2026-03-31T01:23:09"
}
```

**注意**：
- `content` 必須為 WordPress Block 編輯器格式（`<!-- wp:block -->`）
- 使用臨時文件方案處理大型 JSON（見 `scripts/optimize.sh`）

---

### 4. 用戶管理

#### 列出用戶
```
GET /wp-json/wp/v2/users?roles=subscriber&per_page=100
Authorization: Basic [AUTH]

Response (200 OK):
[
  {
    "id": 10,
    "username": "subscriber1",
    "email": "user@example.com",
    "roles": ["subscriber"]
  }
]
```

#### 刪除用戶

```
DELETE /wp-json/wp/v2/users/{id}
Authorization: Basic [AUTH]

Request body (可選):
{
  "force": false,
  "reassign": 1
}

Response (200 OK):
{
  "deleted": true,
  "previous": { ... }
}

⚠️ Error (403 Forbidden):
{
  "code": "rest_cannot_delete_user",
  "message": "Sorry, you are not allowed to delete this user."
}
```

**限制**：WordPress.com 可能限制用戶刪除，用戶被移至垃圾桶而非完全刪除

---

### 5. Jetpack 特定端點

#### 清除快取
```
POST /jetpack/v4/options
Authorization: Basic [AUTH]
Content-Type: application/json

{
  "jetpack_sync_cache_purge": true
}

Response (200 OK):
{
  "jetpack_sync_cache_purge": true
}
```

#### 獲取 Jetpack 統計
```
GET /jetpack/v4/stats
Authorization: Basic [AUTH]

Response (200 OK):
{
  "stats": {
    "views": [
      { "period": "2026-03-31", "views": 150 }
    ],
    "visitors": [
      { "period": "2026-03-31", "visitors": 95 }
    ]
  }
}
```

---

## 🔐 HTTP 狀態碼參考

| 代碼 | 含義 | 常見原因 |
|-----|------|---------|
| 200 | OK | 請求成功 |
| 201 | Created | 資源已建立 |
| 204 | No Content | 成功（無內容回傳） |
| 400 | Bad Request | JSON 格式錯誤 |
| 401 | Unauthorized | 身份驗證失敗 |
| 403 | Forbidden | 權限不足 |
| 404 | Not Found | 端點或資源不存在 |
| 500 | Server Error | 伺服器錯誤 |

---

## 🔗 完整端點清單

| 操作 | 方法 | 端點 | 認證 | 支援狀態 |
|-----|------|------|------|---------|
| 列出插件 | GET | `/wp/v2/plugins` | 需要 | ✅ |
| 更新插件 | PUT | `/wp/v2/plugins/{plugin}` | 需要 | ❌ API 限制 |
| 獲取設定 | GET | `/wp/v2/settings` | 需要 | ✅ |
| 更新設定 | POST | `/wp/v2/settings` | 需要 | ✅ |
| 列出頁面 | GET | `/wp/v2/pages` | 可選 | ✅ |
| 獲取頁面 | GET | `/wp/v2/pages/{id}` | 可選 | ✅ |
| 創建頁面 | POST | `/wp/v2/pages` | 需要 | ✅ |
| 更新頁面 | POST | `/wp/v2/pages/{id}` | 需要 | ✅ |
| 刪除頁面 | DELETE | `/wp/v2/pages/{id}` | 需要 | ✅ |
| 列出用戶 | GET | `/wp/v2/users` | 需要 | ✅ |
| 刪除用戶 | DELETE | `/wp/v2/users/{id}` | 需要 | ⚠️ 限制 |
| Jetpack 選項 | POST | `/jetpack/v4/options` | 需要 | ✅ |
| Jetpack 統計 | GET | `/jetpack/v4/stats` | 需要 | ✅ |

---

## 🛠️ curl 範例

### 檢查 Gzip 狀態
```bash
curl -s https://yololab.net/index.php \
  -I | grep "Content-Encoding"

# 輸出：Content-Encoding: gzip
```

### 啟用 Gzip
```bash
AUTH=$(printf "email@example.com:password" | base64 -w 0)
curl -X POST "https://yololab.net/wp-json/wp/v2/settings" \
  -H "Authorization: Basic $AUTH" \
  -H "Content-Type: application/json" \
  -d '{"gzipcompression":true}'
```

### 更新頁面內容
```bash
AUTH=$(printf "email@example.com:password" | base64 -w 0)
curl -X POST "https://yololab.net/wp-json/wp/v2/pages/3" \
  -H "Authorization: Basic $AUTH" \
  -H "Content-Type: application/json" \
  -d @page-content.json
```

### 清除 Jetpack 快取
```bash
AUTH=$(printf "email@example.com:password" | base64 -w 0)
curl -X POST "https://yololab.net/wp-json/jetpack/v4/options" \
  -H "Authorization: Basic $AUTH" \
  -H "Content-Type: application/json" \
  -d '{"jetpack_sync_cache_purge":true}'
```

---

## 📚 相關資源

- [WordPress REST API 官方文檔](https://developer.wordpress.org/rest-api/)
- [Jetpack API 文檔](https://jetpack.com/support/json-api/)
- [WordPress.com Atomic 支援](https://jetpack.com/support/atomic/)

---

## 🔄 更新日誌

### v1.0 (2026-03-31)
- 初始發佈
- 覆蓋 13 個主要端點
- 應用密碼認證指南
- curl 範例和常見問題

---

**管理員備註**：此文檔應與每個新版本一起更新。遇到新的 API 限制或行為請立即記錄。
