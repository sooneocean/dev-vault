# 常見問題和排查指南

**目的**：快速解決執行和配置中的常見問題
**最後更新**：2026-03-31

---

## 🔴 關鍵錯誤

### 錯誤 1：403 Forbidden - 身份驗證失敗

**症狀**：
```
curl: (22) The requested URL returned error: 403 Forbidden
{"code": "rest_authentication_failed", "message": "Invalid authentication..."}
```

**可能原因**：
1. 應用密碼過期或被撤銷
2. Base64 編碼錯誤
3. 用戶名或密碼錯誤

**排查步驟**：

1. **驗證應用密碼仍然有效**
   ```
   進入 → https://yololab.net/wp-admin/profile.php
   下滑到「應用密碼」
   確認密碼仍在列表中（未被刪除）
   ```

2. **測試 Base64 編碼**
   ```bash
   # 應該產生 : 分隔的密碼形式
   echo "yololab.life@gmail.com:OVsn 4TYb e5U3 wYy4 b0Kl 2dAT" | base64 -w 0

   # 輸出應類似：
   # eW9sb2xhYi5saWZlQGdtYWlsLmNvbTpPVnNuIDRUWWIgZTVVMyB3WXk0IGIwS2wgMmRBVA==
   ```

3. **手動測試 API 呼叫**
   ```bash
   AUTH="eW9sb2xhYi5saWZlQGdtYWlsLmNvbTpPVnNuIDRUWWIgZTVVMyB3WXk0IGIwS2wgMmRBVA=="
   curl -s "https://yololab.net/wp-json/wp/v2/settings" \
     -H "Authorization: Basic $AUTH" | jq .

   # 應返回 200 OK 和 JSON 物件
   ```

**解決方案**：
1. 重新生成應用密碼：
   - 進入 Profile → App Passwords
   - 刪除舊密碼
   - 生成新密碼
   - 在腳本中更新 `WP_PASS` 變數

2. 或者使用 WordPress nonce 代替（如已登入）

---

### 錯誤 2：404 Not Found - REST API 端點不存在

**症狀**：
```
{"code": "rest_no_route", "message": "No route was found matching the request"}
```

**可能原因**：
1. 端點路徑拼寫錯誤
2. 外掛未啟用（例如 Jetpack）
3. WordPress.com 不支持該端點

**排查步驟**：

1. **驗證端點路徑**
   ```
   常見錯誤：
   ❌ /wp/v2/plugins/speedycache/speedycache.php  (含 .php)
   ✅ /wp/v2/plugins/speedycache%2Fspeedycache.php  (URL 編碼)

   或直接使用短路徑（如支持）
   ```

2. **驗證依賴外掛已啟用**
   ```bash
   # 列出所有端點
   curl -s "https://yololab.net/wp-json" | jq '.namespaces'

   # 應包含 "/wp/v2" 和 "/jetpack/v4"
   ```

3. **檢查 WordPress.com 限制**
   - 某些端點在 WordPress.com Atomic 平台上不可用
   - 例如：外掛啟用/停用必須手動操作

**解決方案**：
1. 查看 `docs/API-REFERENCE.md` 確認端點支持狀態
2. 使用標記為「✅ 支持」的端點
3. 對於不支持的操作，使用手動方式（見 `docs/MANUAL-STEPS.md`）

---

### 錯誤 3：400 Bad Request - JSON 格式錯誤

**症狀**：
```
{"code": "rest_invalid_param", "message": "Invalid JSON..."}
```

**可能原因**：
1. JSON 語法錯誤（缺少引號、逗號等）
2. 不正確的字符轉義
3. 多行 JSON 未正確格式化

**排查步驟**：

1. **驗證 JSON 有效性**
   ```bash
   # 使用 jq 驗證
   echo '{"gzipcompression": true}' | jq .

   # 應返回格式化的 JSON，不返回錯誤
   ```

2. **檢查特殊字符轉義**
   ```bash
   # 在 JSON 中轉義雙引號
   ❌ "content": "This is a "quoted" word"
   ✅ "content": "This is a \"quoted\" word"
   ```

3. **對於多行 JSON，使用臨時文件**
   ```bash
   # 推薦方式（見 scripts/optimize.sh）
   cat > /tmp/payload.json << 'EOF'
   {
     "key": "value",
     "nested": {
       "field": "data"
     }
   }
   EOF

   curl -d @/tmp/payload.json [endpoint]
   ```

**解決方案**：
1. 使用 JSON 驗證工具（https://jsonlint.com/）
2. 對複雜 JSON 使用臨時文件方案
3. 查看 `scripts/optimize.sh` 中的 ABOUT 頁面更新例子

---

## 🟡 常見警告

### 警告 1：SpeedyCache/Page Optimize 停用失敗

**症狀**：
```
⚠️ SpeedyCache 停用失敗（可能已停用）
```

**原因**：
這不是錯誤，是已知限制。WordPress.com API 不支持通過 REST API 停用外掛。

**解決方案**：
1. 手動進入 https://yololab.net/wp-admin/plugins.php
2. 找到 SpeedyCache
3. 點擊「停用」
4. 等待頁面重新整理

詳見 `docs/MANUAL-STEPS.md` 的第 1 步。

---

### 警告 2：快取清除失敗 - 自動重試失敗

**症狀**：
```
⚠️ 自動快取清除失敗（可能需要在 Jetpack 後台手動操作）
```

**原因**：
Jetpack API 可能暫時不可用，或需要特定權限。

**解決方案**：
1. 進入 https://yololab.net/wp-admin/admin.php?page=jetpack
2. 找到「快取」或「Performance」部分
3. 點擊「清除快取」按鈕
4. 或者等待 24-48 小時，快取會自動更新

---

## 🔵 一般故障排查

### 問題：執行後首頁無法加載

**症狀**：
- https://yololab.net 返回 500 或 502 錯誤
- 或頁面白屏

**排查步驟**：

1. **檢查 WordPress 錯誤日誌**
   ```
   進入 wp-admin/tools.php 查找日誌查看器
   或檢查伺服器日誌 /var/log/
   ```

2. **驗證禁用的外掛無相互依賴**
   ```
   如果 Page Optimize 依賴 SpeedyCache，停用會導致衝突
   解決：重新啟用受影響的外掛
   ```

3. **重新啟動 PHP（如使用自託管）**
   ```bash
   # WordPress.com 會自動處理，無需手動
   # 如使用自託管 WordPress，執行：
   sudo systemctl restart php-fpm
   ```

4. **暫時使用 WordPress 安全模式**
   ```
   進入 wp-admin，禁用所有外掛，然後逐一重新啟用
   以識別衝突的外掛
   ```

---

### 問題：ABOUT 頁面內容未更新

**症狀**：
- ABOUT 頁面仍顯示舊內容
- 或頁面完全空白

**排查步驟**：

1. **檢查頁面發佈狀態**
   ```
   進入 wp-admin/post.php?post=3&action=edit
   確認 Status 為 "Published"（已發佈）
   ```

2. **檢查頁面可見性**
   ```
   Status: Publish
   Visibility: Public（公開）
   ```

3. **清除所有快取**
   ```
   wp-admin → Jetpack → 清除快取
   或者清除瀏覽器快取（Ctrl+Shift+Delete）
   ```

4. **驗證內容已保存**
   ```
   編輯頁面，檢查「最後修改時間」
   應為最近的時間戳（2026-03-31 01:23 之後）
   ```

**解決方案**：
1. 手動進入 wp-admin/pages/3 編輯
2. 複製新內容（見 `scripts/optimize.js` 中的 aboutContent 變數）
3. 粘貼到頁面編輯器
4. 點擊發佈

---

### 問題：性能沒有改善

**症狀**：
- PageSpeed Insights 分數未提升
- Core Web Vitals 無改善

**可能原因**：
1. CDN 快取未完全更新（需 48-72 小時）
2. 其他性能瓶頸未解決（圖片大小、JavaScript 體積）
3. Gzip 未正確啟用

**排查步驟**：

1. **驗證 Gzip 已啟用**
   ```bash
   curl -s https://yololab.net -I | grep "Content-Encoding"

   應返回：Content-Encoding: gzip
   如果未出現，進入 wp-admin/options-general.php 確認
   ```

2. **檢查圖片最佳化**
   ```bash
   # 檢查圖片大小
   curl -s https://yololab.net | grep -o 'src="[^"]*\.(jpg|png)"' | head -5

   # 圖片應該經過壓縮（< 100KB）
   # 如果 > 500KB，說明 Imagify 未正常運作
   ```

3. **等待 48-72 小時**
   - CDN 快取需要時間更新
   - 重新測試後應有 20-40% 的改進
   - 如超過 72 小時仍無改善，查看其他優化機會

4. **檢查其他瓶頸**
   ```
   進入 PageSpeed Insights 詳細報告
   查看「Opportunities」部分
   可能需要進一步優化：
   - 減少未使用的 CSS/JS
   - 增大壓縮圖像
   - 實施延遲加載
   ```

---

## 📋 診斷清單

執行以下檢查來診斷問題：

```bash
#!/bin/bash
# 診斷腳本

SITE="https://yololab.net"

echo "🔍 YOLO LAB 診斷報告"
echo "========================"
echo "時間：$(date)"
echo ""

# 檢查 1：網站可訪問性
echo "✓ 檢查 1：網站可訪問性"
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" $SITE

# 檢查 2：Gzip 狀態
echo "✓ 檢查 2：Gzip 啟用狀態"
curl -s $SITE -I | grep -i "Content-Encoding" || echo "❌ Gzip 未啟用"

# 檢查 3：API 認證
echo "✓ 檢查 3：REST API 認證"
AUTH=$(printf "email:password" | base64)
curl -s "$SITE/wp-json/wp/v2/settings" \
  -H "Authorization: Basic $AUTH" \
  -o /dev/null -w "HTTP Status: %{http_code}\n"

# 檢查 4：外掛列表
echo "✓ 檢查 4：已啟用的外掛"
curl -s "$SITE/wp-json/wp/v2/plugins?status=active" \
  -H "Authorization: Basic $AUTH" | jq '.[].name'

echo ""
echo "診斷完成"
```

---

## 🆘 聯絡支援

如果問題無法通過以上步驟解決：

1. **收集診斷信息**
   - 執行上述診斷腳本
   - 複製完整錯誤訊息
   - 記錄執行時間和環境（OS、curl 版本）

2. **檢查日誌**
   - `.logs/EXECUTION-LOG.md` - 執行歷史
   - WordPress 錯誤日誌 (wp-admin/tools.php)
   - 伺服器日誌（如自託管）

3. **聯繫**
   - 管理者：sooneocean
   - 提供上述所有信息

4. **參考文檔**
   - 完整 API 文檔：`docs/API-REFERENCE.md`
   - 配置規範：`CONFIG-MANAGEMENT.md`
   - 執行指南：`docs/MANUAL-STEPS.md`

---

## 📝 疑問報告模板

```markdown
## 問題報告

**日期**：YYYY-MM-DD
**時間**：HH:MM UTC
**執行腳本**：optimize.sh / optimize.js / optimize.php

### 症狀描述
[詳細描述問題]

### 錯誤訊息
[完整的錯誤訊息或日誌]

### 已嘗試的解決方案
- [ ] 解決方案 1
- [ ] 解決方案 2

### 環境信息
- 操作系統：
- curl 版本：
- Bash 版本：

### 附加信息
[任何其他相關信息]
```

---

**最後更新**：2026-03-31
**維護者**：Claude Code (sooneocean)
