#!/bin/bash
# YOLO LAB WordPress.com Atomic 自動化腳本
# 用途：一鍵執行所有優化步驟

set -e

SITE_URL="https://yololab.net"
ADMIN_URL="$SITE_URL/wp-admin"
WP_USER="${WP_USER:-your_username}"
WP_PASS="${WP_PASS:-your_password}"

echo "🚀 YOLO LAB 自動化優化啟動"
echo "================================================"

# 1. 外掛啟用/停用 (透過 REST API)
echo "📦 步驟 1：外掛優化..."
echo "停用 SpeedyCache 1.3.8..."
curl -X POST "$SITE_URL/wp-json/wp/v2/plugins/speedycache/speedycache" \
  -u "$WP_USER:$WP_PASS" \
  -H "Content-Type: application/json" \
  -d '{"status":"inactive"}' 2>/dev/null || echo "⚠️ SpeedyCache 停用失敗（可能已停用）"

echo "停用 Page Optimize 0.6.2..."
curl -X POST "$SITE_URL/wp-json/wp/v2/plugins/page-optimize/page-optimize" \
  -u "$WP_USER:$WP_PASS" \
  -H "Content-Type: application/json" \
  -d '{"status":"inactive"}' 2>/dev/null || echo "⚠️ Page Optimize 停用失敗"

echo "啟用 Converter for Media (WebP)..."
curl -X POST "$SITE_URL/wp-json/wp/v2/plugins/webp-converter-for-media/webp-converter-for-media" \
  -u "$WP_USER:$WP_PASS" \
  -H "Content-Type: application/json" \
  -d '{"status":"active"}' 2>/dev/null || echo "⚠️ WebP Converter 啟用失敗"

# 2. Gzip 啟用 (透過 options API)
echo ""
echo "🗜️ 步驟 2：啟用 Gzip 壓縮..."
curl -X POST "$SITE_URL/wp-json/wp/v2/settings" \
  -u "$WP_USER:$WP_PASS" \
  -H "Content-Type: application/json" \
  -d '{"gzipcompression":true}' 2>/dev/null || echo "⚠️ Gzip 啟用失敗"

# 3. 更新 ABOUT 頁面
echo ""
echo "📝 步驟 3：更新 ABOUT 頁面..."
curl -X POST "$SITE_URL/wp-json/wp/v2/pages/3" \
  -u "$WP_USER:$WP_PASS" \
  -H "Content-Type: application/json" \
  -d @about-page-content.json 2>/dev/null || echo "⚠️ ABOUT 頁面更新失敗"

# 4. 用戶清理 (刪除不活躍訂閱者)
echo ""
echo "👥 步驟 4：清理不活躍用戶..."
echo "獲取所有 subscriber 角色用戶..."

# 需要手動操作或提供 API 金鑰
echo "⚠️ 用戶批量刪除需要在 WordPress 後台手動完成"
echo "   進入：wp-admin → 用戶 → 篩選 subscriber → 批量刪除"

echo ""
echo "✅ 自動化步驟完成！"
echo "================================================"
echo ""
echo "📋 待辦清單："
echo "□ 確認外掛狀態（wp-admin/plugins.php）"
echo "□ 檢查 Gzip 設定（wp-admin/options-general.php）"
echo "□ 驗證 ABOUT 頁面顯示（yololab.net/about）"
echo "□ 手動清理 subscriber 用戶"
echo ""
echo "🎯 完成後執行性能驗證："
echo "   lighthouse: https://pagespeed.web.dev/?url=yololab.net"
echo "   Core Web Vitals 檢查"
