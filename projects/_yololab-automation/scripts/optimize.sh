#!/bin/bash
# YOLO LAB WordPress.com Atomic 自動化腳本 (已修正 JSON 轉義)
# 用途：一鍵執行所有優化步驟

set -e

SITE_URL="https://yololab.net"
ADMIN_URL="$SITE_URL/wp-admin"
WP_USER="yololab.life@gmail.com"
WP_PASS="OVsn 4TYb e5U3 wYy4 b0Kl 2dAT"

# 計算 Base64 authentication
AUTH=$(printf "$WP_USER:$WP_PASS" | base64 -w 0)

echo "🚀 YOLO LAB 自動化優化啟動"
echo "================================================"

# 1. 外掛啟用/停用 (透過 REST API)
echo "📦 步驟 1：外掛優化..."

echo "停用 SpeedyCache 1.3.8..."
curl -s -X PUT "$SITE_URL/wp-json/wp/v2/plugins/speedycache%2Fspeedycache.php" \
  -H "Authorization: Basic $AUTH" \
  -H "Content-Type: application/json" \
  -d '{"status":"inactive"}' > /dev/null && echo "✅ 已停用 SpeedyCache 1.3.8" || echo "⚠️ SpeedyCache 停用失敗（可能已停用）"

echo "停用 Page Optimize 0.6.2..."
curl -s -X PUT "$SITE_URL/wp-json/wp/v2/plugins/page-optimize%2Fpage-optimize.php" \
  -H "Authorization: Basic $AUTH" \
  -H "Content-Type: application/json" \
  -d '{"status":"inactive"}' > /dev/null && echo "✅ 已停用 Page Optimize 0.6.2" || echo "⚠️ Page Optimize 停用失敗"

echo "啟用 Converter for Media (WebP)..."
curl -s -X PUT "$SITE_URL/wp-json/wp/v2/plugins/webp-converter-for-media%2Fwebp-converter-for-media.php" \
  -H "Authorization: Basic $AUTH" \
  -H "Content-Type: application/json" \
  -d '{"status":"active"}' > /dev/null && echo "✅ 已啟用 Converter for Media (WebP)" || echo "⚠️ WebP Converter 啟用失敗"

# 2. Gzip 啟用
echo ""
echo "🗜️ 步驟 2：啟用 Gzip 壓縮..."
curl -s -X POST "$SITE_URL/wp-json/wp/v2/settings" \
  -H "Authorization: Basic $AUTH" \
  -H "Content-Type: application/json" \
  -d '{"gzipcompression":true}' > /dev/null && echo "✅ Gzip 壓縮已啟用" || echo "⚠️ Gzip 啟用失敗"

# 3. 更新 ABOUT 頁面 (使用臨時 JSON 檔案)
echo ""
echo "📝 步驟 3：更新 ABOUT 頁面..."

# 建立臨時 JSON 檔案
TEMP_JSON=$(mktemp)
cat > "$TEMP_JSON" << 'EOFABOUT'
{
  "title": "關於 YOLO LAB",
  "content": "<!-- wp:cover {\"overlayColor\":\"primary\",\"align\":\"full\",\"style\":{\"spacing\":{\"padding\":{\"top\":\"60px\",\"bottom\":\"60px\"}}}} -->\n<div class=\"wp-block-cover has-primary-background-color\" style=\"padding-top:60px;padding-bottom:60px\"><div class=\"wp-block-cover__inner-container\"><!-- wp:heading {\"level\":1,\"align\":\"center\",\"style\":{\"color\":{\"text\":\"contrast\"},\"typography\":{\"fontSize\":\"40px\"}}} -->\n<h1 class=\"has-text-align-center has-contrast-color\" style=\"font-size:40px\">YOLO LAB 的故事</h1>\n<!-- /wp:heading --><!-- wp:paragraph {\"align\":\"center\",\"style\":{\"color\":{\"text\":\"base\"},\"typography\":{\"fontSize\":\"16px\"}}} -->\n<p class=\"has-text-align-center has-base-color\" style=\"font-size:16px\">科技與媒體數據實驗室 — 暴力、前衛、數據驅動的內容平台</p>\n<!-- /wp:paragraph --></div></div>\n<!-- /wp:cover -->\n\n<!-- wp:heading {\"level\":2,\"align\":\"center\",\"style\":{\"color\":{\"text\":\"primary\"},\"spacing\":{\"margin\":{\"top\":\"60px\",\"bottom\":\"30px\"}},\"typography\":{\"fontSize\":\"32px\"}}} -->\n<h2 class=\"has-text-align-center has-primary-color\" style=\"font-size:32px;margin-top:60px;margin-bottom:30px\">我們的使命</h2>\n<!-- /wp:heading -->\n\n<!-- wp:paragraph {\"align\":\"center\",\"style\":{\"fontSize\":\"18px\",\"lineHeight\":\"1.8\"}} -->\n<p class=\"has-text-align-center\" style=\"font-size:18px;line-height:1.8\">YOLO LAB 拒絕陳腔濫調。我們在科技疆界與娛樂底層邏輯中挖掘真相。<strong>數據是刀，文字是火</strong>。不跟隨趨勢，我們製造趨勢，這是對未來的暴力介入。</p>\n<!-- /wp:paragraph -->\n\n<!-- wp:columns {\"align\":\"wide\"} -->\n<div class=\"wp-block-columns alignwide\"><!-- wp:column -->\n<div class=\"wp-block-column\"><!-- wp:group {\"style\":{\"spacing\":{\"padding\":\"30px\"},\"border\":{\"radius\":\"12px\"}},\"backgroundColor\":\"base\"} -->\n<div class=\"wp-block-group has-base-background-color\" style=\"border-radius:12px;padding:30px\"><!-- wp:heading {\"level\":3,\"style\":{\"color\":{\"text\":\"primary\"},\"typography\":{\"fontSize\":\"24px\"}}} -->\n<h3 class=\"has-primary-color\" style=\"font-size:24px\">🎵 音樂</h3>\n<!-- /wp:heading --><p>推廣全球電音、嘻哈與創新音樂風格。透過深度評論與藝人訪談，讓你全方位體驗音樂的靈魂。</p></div>\n<!-- /wp:group --></div>\n<!-- /wp:column --><!-- wp:column -->\n<div class=\"wp-block-column\"><!-- wp:group {\"style\":{\"spacing\":{\"padding\":\"30px\"},\"border\":{\"radius\":\"12px\"}},\"backgroundColor\":\"base\"} -->\n<div class=\"wp-block-group has-base-background-color\" style=\"border-radius:12px;padding:30px\"><!-- wp:heading {\"level\":3,\"style\":{\"color\":{\"text\":\"primary\"},\"typography\":{\"fontSize\":\"24px\"}}} -->\n<h3 class=\"has-primary-color\" style=\"font-size:24px\">🎬 電影</h3>\n<!-- /wp:heading --><p>分析最新電影與經典佳作。院線動態、預告分析、從多個角度深掘電影的藝術與商業本質。</p></div>\n<!-- /wp:group --></div>\n<!-- /wp:column --><!-- wp:column -->\n<div class=\"wp-block-column\"><!-- wp:group {\"style\":{\"spacing\":{\"padding\":\"30px\"},\"border\":{\"radius\":\"12px\"}},\"backgroundColor\":\"base\"} -->\n<div class=\"wp-block-group has-base-background-color\" style=\"border-radius:12px;padding:30px\"><!-- wp:heading {\"level\":3,\"style\":{\"color\":{\"text\":\"primary\"},\"typography\":{\"fontSize\":\"24px\"}}} -->\n<h3 class=\"has-primary-color\" style=\"font-size:24px\">⚡ 科技</h3>\n<!-- /wp:heading --><p>緊跟 AI、SaaS、硬體創新。數據分析驅動，揭示科技產業的真實邏輯與未來方向。</p></div>\n<!-- /wp:group --></div>\n<!-- /wp:column --></div>\n<!-- /wp:columns -->\n\n<!-- wp:columns {\"align\":\"wide\"} -->\n<div class=\"wp-block-columns alignwide\"><!-- wp:column -->\n<div class=\"wp-block-column\"><!-- wp:group {\"style\":{\"spacing\":{\"padding\":\"30px\"},\"border\":{\"radius\":\"12px\"}},\"backgroundColor\":\"base\"} -->\n<div class=\"wp-block-group has-base-background-color\" style=\"border-radius:12px;padding:30px\"><!-- wp:heading {\"level\":3,\"style\":{\"color\":{\"text\":\"primary\"},\"typography\":{\"fontSize\":\"24px\"}}} -->\n<h3 class=\"has-primary-color\" style=\"font-size:24px\">🌟 生活</h3>\n<!-- /wp:heading --><p>探討時尚、美食、旅行與都市文化。將藝術融入日常，發掘生活的無限可能。</p></div>\n<!-- /wp:group --></div>\n<!-- /wp:column --><!-- wp:column -->\n<div class=\"wp-block-column\"><!-- wp:group {\"style\":{\"spacing\":{\"padding\":\"30px\"},\"border\":{\"radius\":\"12px\"}},\"backgroundColor\":\"base\"} -->\n<div class=\"wp-block-group has-base-background-color\" style=\"border-radius:12px;padding:30px\"><!-- wp:heading {\"level\":3,\"style\":{\"color\":{\"text\":\"primary\"},\"typography\":{\"fontSize\":\"24px\"}}} -->\n<h3 class=\"has-primary-color\" style=\"font-size:24px\">🎉 活動</h3>\n<!-- /wp:heading --><p>舉辦派對、音樂節、展覽與工作坊。聚集志同道合的人，共創文化與社群的力量。</p></div>\n<!-- /wp:group --></div>\n<!-- /wp:column --></div>\n<!-- /wp:columns -->\n\n<!-- wp:group {\"align\":\"wide\",\"style\":{\"backgroundColor\":\"primary\",\"spacing\":{\"padding\":\"60px 40px\"}},\"className\":\"about-cta\"} -->\n<div class=\"wp-block-group alignwide has-primary-background-color about-cta\" style=\"padding:60px 40px\"><!-- wp:heading {\"level\":2,\"align\":\"center\",\"style\":{\"color\":{\"text\":\"contrast\"}}} -->\n<h2 class=\"has-text-align-center has-contrast-color\">與我們連結</h2>\n<!-- /wp:heading --><!-- wp:paragraph {\"align\":\"center\",\"style\":{\"color\":{\"text\":\"contrast\"},\"fontSize\":\"16px\"}} -->\n<p class=\"has-text-align-center has-contrast-color\" style=\"font-size:16px\">透過社交媒體或郵件與 YOLO LAB 保持聯繫，獲取最新的內容、活動資訊與獨家分析。</p>\n<!-- /wp:paragraph --><!-- wp:buttons {\"layout\":{\"type\":\"flex\",\"justifyContent\":\"center\"},\"style\":{\"spacing\":{\"margin\":{\"top\":\"30px\"}}}} -->\n<div class=\"wp-block-buttons\" style=\"margin-top:30px\"><!-- wp:button {\"backgroundColor\":\"accent-three\",\"textColor\":\"contrast\",\"className\":\"is-style-fill\"} -->\n<div class=\"wp-block-button is-style-fill\"><a class=\"wp-block-button__link has-accent-three-background-color has-contrast-color wp-element-button\" href=\"https://www.facebook.com/yololab.life\" target=\"_blank\">Facebook</a></div>\n<!-- /wp:button --><!-- wp:button {\"backgroundColor\":\"accent-three\",\"textColor\":\"contrast\",\"className\":\"is-style-fill\"} -->\n<div class=\"wp-block-button is-style-fill\"><a class=\"wp-block-button__link has-accent-three-background-color has-contrast-color wp-element-button\" href=\"https://www.instagram.com/yololab.life/\" target=\"_blank\">Instagram</a></div>\n<!-- /wp:button --><!-- wp:button {\"textColor\":\"accent-three\",\"className\":\"is-style-outline\"} -->\n<div class=\"wp-block-button is-style-outline\"><a class=\"wp-block-button__link has-accent-three-color wp-element-button\" href=\"mailto:yololab.life@gmail.com\">聯絡我們</a></div>\n<!-- /wp:button --></div>\n<!-- /wp:buttons --></div>\n<!-- /wp:group -->",
  "status": "publish"
}
EOFABOUT

curl -s -X POST "$SITE_URL/wp-json/wp/v2/pages/3" \
  -H "Authorization: Basic $AUTH" \
  -H "Content-Type: application/json" \
  -d @"$TEMP_JSON" > /dev/null && echo "✅ ABOUT 頁面已更新" || echo "⚠️ ABOUT 頁面更新失敗"

# 清理臨時檔案
rm -f "$TEMP_JSON"

# 4. 清除快取
echo ""
echo "🔄 步驟 4：清除快取..."
curl -s -X POST "$SITE_URL/wp-json/wp/v2/settings" \
  -H "Authorization: Basic $AUTH" \
  -H "Content-Type: application/json" \
  -d '{"jetpack_sync_cache_purge":true}' > /dev/null && echo "✅ 快取已清除" || echo "⚠️ 快取清除失敗"

echo ""
echo "=================================================="
echo "✨ 自動化優化完成！"
echo "=================================================="
echo ""
echo "📊 驗證清單："
echo "□ 檢查首頁：https://yololab.net"
echo "□ 檢查關於：https://yololab.net/about"
echo "□ 檢查外掛：https://yololab.net/wp-admin/plugins.php"
echo "□ 驗證 Gzip：https://yololab.net/wp-admin/options-general.php"
echo "□ 性能測試：https://pagespeed.web.dev/?url=yololab.net"
echo ""
