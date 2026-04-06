<?php
/**
 * YOLOLAB SEO 批量優化器 - Code Snippets 版本
 * 在 WordPress 後台直接執行，無 API 限制
 *
 * 使用方式：
 * 1. 進入 https://yololab.net/wp-admin/plugin-install.php?tab=search&type=featured&s=code+snippets
 * 2. 安裝「Code Snippets」外掛
 * 3. 進入 Snippets → Add New
 * 4. 貼上此程式碼
 * 5. 勾選「Run snippet everywhere」
 * 6. 點擊「Save Snippet and Activate」
 *
 * OR 直接執行（單次使用）：
 * 進入 wp-admin → Snippets → Add New → 貼上下面的程式碼 → 勾選「Run snippet everywhere」→ Save
 */

// 只在有 manage_options 權限的管理員執行
if (!current_user_can('manage_options')) {
    return;
}

// 檢查 GET 參數以防止自動觸發
if (!isset($_GET['yololab_seo_optimize']) || $_GET['yololab_seo_optimize'] !== '1') {
    echo '<div class="notice notice-info"><p>';
    echo '要執行 SEO 優化，請訪問：';
    echo '<a href="' . admin_url('admin.php?page=snippets&yololab_seo_optimize=1') . '" class="button button-primary">';
    echo '開始 SEO 優化</a></p></div>';
    return;
}

class YololabSEOOptimizer {

    private $updated = 0;
    private $failed = 0;
    private $batch_size = 50; // 每批處理 50 篇，避免超時

    public function optimize() {
        echo '<div class="wrap"><h1>🚀 YOLO LAB SEO 批量優化</h1>';
        echo '<div style="background:#f1f1f1;padding:15px;border-radius:5px;">';

        $start_time = microtime(true);

        // 獲取所有已發佈文章
        $args = array(
            'post_type'      => 'post',
            'post_status'    => 'publish',
            'posts_per_page' => -1,
            'fields'         => 'ids'
        );

        $posts = get_posts($args);
        $total = count($posts);

        echo "<p><strong>📊 找到 $total 篇文章</strong></p>";

        if ($total === 0) {
            echo '<p style="color:#d63638;">❌ 未找到已發佈文章</p></div></div>';
            return;
        }

        echo '<div style="margin:20px 0;"><strong>⏳ 處理中...</strong><div style="width:100%;height:20px;background:#ddd;border-radius:3px;overflow:hidden;">';

        // 逐篇處理
        foreach ($posts as $post_id) {
            $this->optimize_post($post_id);

            // 進度條
            $progress = round(($this->updated + $this->failed) / $total * 100);
            echo "\r<div style='width:{$progress}%;height:100%;background:#0073aa;transition:width 0.3s;'></div>";

            // 每 50 篇後暫停，避免超時
            if (($this->updated + $this->failed) % $this->batch_size === 0) {
                wp_cache_flush(); // 清理快取
                sleep(1);
            }
        }

        echo '</div></div>';

        $elapsed = microtime(true) - $start_time;

        echo "<p style='margin-top:20px;'><strong>✅ 完成！</strong></p>";
        echo "<ul style='list-style:none;padding:0;'>";
        echo "<li>✅ 成功更新：<strong style='color:#00a32a;'>" . $this->updated . "</strong> 篇</li>";
        echo "<li>❌ 失敗：<strong style='color:#d63638;'>" . $this->failed . "</strong> 篇</li>";
        echo "<li>⏱️ 耗時：<strong>" . number_format($elapsed, 1) . "</strong> 秒</li>";
        echo "</ul>";

        // 清除快取
        wp_cache_flush();

        // 如有 Jetpack，清除其快取
        if (function_exists('jetpack_is_active')) {
            do_action('jetpack_purge_site_cache');
        }

        echo '<p style="margin-top:20px;color:#666;"><strong>📋 下一步：</strong></p>';
        echo '<ul>';
        echo '<li>進入 Google Search Console 檢查爬蟲狀態（24 小時後）</li>';
        echo '<li>運行 PageSpeed Insights 驗證性能（T+72h）</li>';
        echo '<li>監控排名變化（3-7 天）</li>';
        echo '</ul>';

        echo '</div></div>';
    }

    private function optimize_post($post_id) {
        $post = get_post($post_id);

        if (!$post) {
            $this->failed++;
            return;
        }

        // 生成優化的 SEO 標題（55-60 字符）
        $title = $this->clean_text($post->post_title);
        $seo_title = strlen($title) > 55
            ? substr($title, 0, 52) . '...'
            : $title;

        // 生成優化的 Meta 描述（155-160 字符）
        $excerpt = !empty($post->post_excerpt)
            ? $this->clean_text($post->post_excerpt)
            : wp_trim_words($post->post_content, 25, '');

        $seo_desc = strlen($excerpt) > 155
            ? substr($excerpt, 0, 152) . '...'
            : $excerpt;

        // 確保至少有基本描述
        if (empty($seo_desc)) {
            $seo_desc = "深入瞭解《" . $seo_title . "》的詳細內容。YOLO LAB 提供最新評論和推薦。";
        }

        // 保存為 Yoast SEO meta（如果已安裝）
        if (class_exists('WPSEO_Meta')) {
            // Yoast SEO 格式
            update_post_meta($post_id, '_yoast_wpseo_title', $seo_title);
            update_post_meta($post_id, '_yoast_wpseo_metadesc', $seo_desc);
        }

        // 也保存為標準 WordPress meta（向後相容）
        update_post_meta($post_id, '_meta_description', $seo_desc);

        // 更新摘錄（作為備份）
        if (empty($post->post_excerpt)) {
            wp_update_post(array(
                'ID'            => $post_id,
                'post_excerpt'  => $seo_desc
            ));
        }

        $this->updated++;
    }

    private function clean_text($text) {
        // 移除 HTML 標籤
        $text = wp_strip_all_tags($text);
        // 移除多余空白
        $text = preg_replace('/\s+/', ' ', $text);
        // 移除特殊字符
        $text = trim($text);

        return $text;
    }
}

// 執行優化
$optimizer = new YololabSEOOptimizer();
$optimizer->optimize();
?>
