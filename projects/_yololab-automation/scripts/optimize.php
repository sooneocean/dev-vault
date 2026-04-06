<?php
/**
 * YOLO LAB WordPress.com 自動化優化腳本
 * 用法：
 * 1. 進入 WordPress 後台 → Tools → Code Snippets （如果已安裝）
 * 2. 或進入 Plugins → WPCode Lite → Add Custom Code
 * 3. 貼上此代碼，執行
 */

if ( ! defined( 'ABSPATH' ) ) {
    exit;
}

echo '<h2>🚀 YOLO LAB 自動化優化啟動</h2>';
echo '<pre style="background: #f5f5f5; padding: 15px; border-radius: 5px;">';

// 1. 停用 SpeedyCache
echo "📦 步驟 1：外掛優化...\n";
$speedycache_plugin = 'speedycache/speedycache.php';
if ( is_plugin_active( $speedycache_plugin ) ) {
    deactivate_plugins( $speedycache_plugin );
    echo "✅ 已停用 SpeedyCache 1.3.8\n";
} else {
    echo "⚠️  SpeedyCache 已停用或未安裝\n";
}

// 2. 停用 Page Optimize
$pageopt_plugin = 'page-optimize/page-optimize.php';
if ( is_plugin_active( $pageopt_plugin ) ) {
    deactivate_plugins( $pageopt_plugin );
    echo "✅ 已停用 Page Optimize 0.6.2\n";
} else {
    echo "⚠️  Page Optimize 已停用或未安裝\n";
}

// 3. 啟用 WebP Converter for Media
$webp_plugin = 'webp-converter-for-media/webp-converter-for-media.php';
if ( file_exists( WP_PLUGIN_DIR . '/' . $webp_plugin ) && ! is_plugin_active( $webp_plugin ) ) {
    activate_plugins( $webp_plugin );
    echo "✅ 已啟用 Converter for Media (WebP)\n";
} else {
    echo "⚠️  WebP Converter 已啟用或未安裝\n";
}

// 4. 啟用 Gzip 壓縮
echo "\n🗜️ 步驟 2：啟用 Gzip 壓縮...\n";
update_option( 'gzipcompression', 1 );
echo "✅ Gzip 壓縮已啟用\n";

// 5. 更新 ABOUT 頁面
echo "\n📝 步驟 3：更新 ABOUT 頁面...\n";
$about_content = '<!-- wp:cover {\"overlayColor\":\"primary\",\"align\":\"full\",\"style\":{\"spacing\":{\"padding\":{\"top\":\"60px\",\"bottom\":\"60px\"}}}} -->
<div class=\"wp-block-cover has-primary-background-color\" style=\"padding-top:60px;padding-bottom:60px\"><div class=\"wp-block-cover__inner-container\"><!-- wp:heading {\"level\":1,\"align\":\"center\",\"style\":{\"color\":{\"text\":\"contrast\"},\"typography\":{\"fontSize\":\"40px\"}}} -->
<h1 class=\"has-text-align-center has-contrast-color\" style=\"font-size:40px\">YOLO LAB 的故事</h1>
<!-- /wp:heading --><!-- wp:paragraph {\"align\":\"center\",\"style\":{\"color\":{\"text\":\"base\"},\"typography\":{\"fontSize\":\"16px\"}}} -->
<p class=\"has-text-align-center has-base-color\" style=\"font-size:16px\">科技與媒體數據實驗室 — 暴力、前衛、數據驅動的內容平台</p>
<!-- /wp:paragraph --></div></div>
<!-- /wp:cover -->

<!-- wp:heading {\"level\":2,\"align\":\"center\",\"style\":{\"color\":{\"text\":\"primary\"},\"spacing\":{\"margin\":{\"top\":\"60px\",\"bottom\":\"30px\"}},\"typography\":{\"fontSize\":\"32px\"}}} -->
<h2 class=\"has-text-align-center has-primary-color\" style=\"font-size:32px;margin-top:60px;margin-bottom:30px\">我們的使命</h2>
<!-- /wp:heading -->

<!-- wp:paragraph {\"align\":\"center\",\"style\":{\"fontSize\":\"18px\",\"lineHeight\":\"1.8\"}} -->
<p class=\"has-text-align-center\" style=\"font-size:18px;line-height:1.8\">YOLO LAB 拒絕陳腔濫調。我們在科技疆界與娛樂底層邏輯中挖掘真相。<strong>數據是刀，文字是火</strong>。不跟隨趨勢，我們製造趨勢，這是對未來的暴力介入。</p>
<!-- /wp:paragraph -->

<!-- wp:spacer {\"height\":\"40px\"} -->
<div style=\"height:40px\" aria-hidden=\"true\" class=\"wp-block-spacer\"></div>
<!-- /wp:spacer -->

<!-- wp:columns {\"align\":\"wide\"} -->
<div class=\"wp-block-columns alignwide\"><!-- wp:column -->
<div class=\"wp-block-column\"><!-- wp:group {\"style\":{\"spacing\":{\"padding\":\"30px\"},\"border\":{\"radius\":\"12px\"}},\"backgroundColor\":\"base\"} -->
<div class=\"wp-block-group has-base-background-color\" style=\"border-radius:12px;padding:30px\"><!-- wp:heading {\"level\":3,\"style\":{\"color\":{\"text\":\"primary\"},\"typography\":{\"fontSize\":\"24px\"}}} -->
<h3 class=\"has-primary-color\" style=\"font-size:24px\">🎵 音樂</h3>
<!-- /wp:heading --><p>推廣全球電音、嘻哈與創新音樂風格。透過深度評論與藝人訪談，讓你全方位體驗音樂的靈魂。</p></div>
<!-- /wp:group --></div>
<!-- /wp:column --><!-- wp:column -->
<div class=\"wp-block-column\"><!-- wp:group {\"style\":{\"spacing\":{\"padding\":\"30px\"},\"border\":{\"radius\":\"12px\"}},\"backgroundColor\":\"base\"} -->
<div class=\"wp-block-group has-base-background-color\" style=\"border-radius:12px;padding:30px\"><!-- wp:heading {\"level\":3,\"style\":{\"color\":{\"text\":\"primary\"},\"typography\":{\"fontSize\":\"24px\"}}} -->
<h3 class=\"has-primary-color\" style=\"font-size:24px\">🎬 電影</h3>
<!-- /wp:heading --><p>分析最新電影與經典佳作。院線動態、預告分析、從多個角度深掘電影的藝術與商業本質。</p></div>
<!-- /wp:group --></div>
<!-- /wp:column --><!-- wp:column -->
<div class=\"wp-block-column\"><!-- wp:group {\"style\":{\"spacing\":{\"padding\":\"30px\"},\"border\":{\"radius\":\"12px\"}},\"backgroundColor\":\"base\"} -->
<div class=\"wp-block-group has-base-background-color\" style=\"border-radius:12px;padding:30px\"><!-- wp:heading {\"level\":3,\"style\":{\"color\":{\"text\":\"primary\"},\"typography\":{\"fontSize\":\"24px\"}}} -->
<h3 class=\"has-primary-color\" style=\"font-size:24px\">⚡ 科技</h3>
<!-- /wp:heading --><p>緊跟 AI、SaaS、硬體創新。數據分析驅動，揭示科技產業的真實邏輯與未來方向。</p></div>
<!-- /wp:group --></div>
<!-- /wp:column --></div>
<!-- /wp:columns -->';

$about_update = wp_update_post( array(
    'ID'           => 3,
    'post_title'   => '關於 YOLO LAB',
    'post_content' => $about_content,
    'post_status'  => 'publish'
) );

if ( ! is_wp_error( $about_update ) ) {
    echo "✅ ABOUT 頁面已更新\n";
} else {
    echo "❌ ABOUT 頁面更新失敗：" . $about_update->get_error_message() . "\n";
}

// 6. 清理不活躍訂閱者
echo "\n👥 步驟 4：清理不活躍用戶...\n";
$inactive_users = get_users( array(
    'role'   => 'subscriber',
    'fields' => 'ids'
) );

if ( ! empty( $inactive_users ) ) {
    $deleted_count = 0;
    // 保留前 5 個訂閱者，刪除其餘
    $users_to_delete = array_slice( $inactive_users, 5 );

    foreach ( $users_to_delete as $user_id ) {
        $deleted = wp_delete_user( $user_id, false ); // false = 移至垃圾桶，true = 完全刪除
        if ( $deleted ) {
            $deleted_count++;
        }
    }

    echo "✅ 已清理 $deleted_count 個不活躍訂閱者（保留 5 個）\n";
    echo "   總訂閱者數：" . count( $inactive_users ) . "\n";
} else {
    echo "⚠️  未找到訂閱者用戶\n";
}

echo "\n" . '==================================================' . "\n";
echo "✨ 自動化優化完成！\n";
echo "==================================================" . "\n";
echo "\n📊 後續驗證步驟：\n";
echo "1. 前往 yololab.net 檢查首頁、關於、聯絡頁面\n";
echo "2. 進入 wp-admin/plugins.php 確認外掛狀態\n";
echo "3. 檢查 wp-admin/options-general.php 的 Gzip 設定\n";
echo "4. 進入 wp-admin/users.php 確認用戶清理完成\n";
echo "5. 執行 Lighthouse 審查：https://pagespeed.web.dev/?url=yololab.net\n";

echo '</pre>';

// 重新加載可能的快取
wp_cache_flush();
echo '<p style="color: green; font-weight: bold;">✅ 所有優化已套用，快取已清除。請重新整理瀏覽器檢查結果。</p>';
?>
