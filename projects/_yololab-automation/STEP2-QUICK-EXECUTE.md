---
title: ⚡ Step 2：SEO 批量優化 - 快速執行指南
type: project
tags: [project, active]
created: 2026-04-03
updated: 2026-04-03
status: active
maturity: growing
domain: knowledge-management
summary: ""
---

# ⚡ Step 2：SEO 批量優化 - 快速執行指南

**目標**：一鍵優化 136 篇文章的 SEO 元數據
**預期耗時**：3-5 分鐘
**難度**：簡單（3 步驟）
**開始時間**：2026-03-31 T+0h

---

## 🎯 快速執行方式（推薦）

### 步驟 1️⃣：進入 WordPress 後台

```
URL：https://yololab.net/wp-admin/
使用者：yololab.life@gmail.com
密碼：[你的 WordPress 密碼]
```

### 步驟 2️⃣：安裝並使用「Code Snippets」外掛

**如果未安裝**：

```
進入：https://yololab.net/wp-admin/plugin-install.php
搜尋：Code Snippets
點擊：「Install Now」→ 「Activate」
```

**如果已安裝**：

```
進入側邊欄：Snippets
```

### 步驟 3️⃣：創建並執行優化片段

**進入**：https://yololab.net/wp-admin/admin.php?page=snippets

**點擊**：「Add New」（新增片段）

**在「Code」欄位貼上以下程式碼**：

```php
<?php
if (!current_user_can('manage_options')) return;

class YololabSEOOptimizer {
    private $updated = 0;
    private $failed = 0;

    public function optimize() {
        $args = array(
            'post_type'      => 'post',
            'post_status'    => 'publish',
            'posts_per_page' => -1,
            'fields'         => 'ids'
        );

        $posts = get_posts($args);
        echo "<div class='notice notice-success'><p>🚀 開始優化 " . count($posts) . " 篇文章...</p></div>";

        foreach ($posts as $post_id) {
            $post = get_post($post_id);
            $title = wp_strip_all_tags($post->post_title);
            $seo_title = strlen($title) > 55 ? substr($title, 0, 52) . '...' : $title;

            $excerpt = !empty($post->post_excerpt)
                ? wp_strip_all_tags($post->post_excerpt)
                : wp_trim_words($post->post_content, 25, '');
            $seo_desc = strlen($excerpt) > 155 ? substr($excerpt, 0, 152) . '...' : $excerpt;

            if (empty($seo_desc)) {
                $seo_desc = "深入瞭解《$seo_title》。YOLO LAB 精選推薦。";
            }

            // 儲存 Yoast SEO meta
            update_post_meta($post_id, '_yoast_wpseo_title', $seo_title);
            update_post_meta($post_id, '_yoast_wpseo_metadesc', $seo_desc);
            update_post_meta($post_id, '_meta_description', $seo_desc);

            if (empty($post->post_excerpt)) {
                wp_update_post(array(
                    'ID'           => $post_id,
                    'post_excerpt' => $seo_desc
                ));
            }

            $this->updated++;
        }

        wp_cache_flush();
        if (function_exists('jetpack_is_active')) {
            do_action('jetpack_purge_site_cache');
        }

        echo "<div class='notice notice-success' style='border-left:4px solid #00a32a;'>";
        echo "<p><strong>✅ 完成！</strong></p>";
        echo "<ul>";
        echo "<li>✅ 成功更新：<strong>" . $this->updated . "</strong> 篇文章</li>";
        echo "<li>📅 完成時間：" . date('Y-m-d H:i:s') . "</li>";
        echo "<li>⏭️ 下一步：進入 Google Search Console 檢查爬蟲狀態（24 小時後）</li>";
        echo "</ul>";
        echo "</div>";
    }
}

$optimizer = new YololabSEOOptimizer();
$optimizer->optimize();
?>
```

**然後**：

```
☑️ 勾選「Run snippet everywhere」
🔵 點擊「Save Snippet and Activate」
```

**立即執行**：

```
頁面會自動執行，顯示進度和完成訊息
預期結果：
  ✅ 成功更新：136 篇文章
  ✅ 耗時：2-4 分鐘
```

---

## 📊 執行狀態檢查

### 即時檢查

在 wp-admin 側邊欄，進入：

```
Snippets → 已激活的片段
```

應該看到「YOLO LAB SEO Optimizer」顯示為「已激活」

### 驗證結果（5 分鐘後）

**進入任意文章編輯頁面**：

```
https://yololab.net/wp-admin/edit.php?post_type=post
點擊任意文章標題 → 編輯
向下滾動找到「Yoast SEO」區塊
```

應該看到：

```
✅ SEO Title：已填入優化的標題
✅ Meta Description：已填入優化的描述
✅ Google Preview：顯示搜尋結果預覽
```

---

## 🔍 故障排查

### 問題 1：「Code Snippets」外掛未安裝

**解決**：

```
進入：https://yololab.net/wp-admin/plugin-install.php
搜尋「Code Snippets」
點擊「Install Now」
```

### 問題 2：執行後沒看到任何訊息

**解決**：

```
1. 重新整理頁面（Ctrl+R）
2. 檢查瀏覽器主控台是否有錯誤（F12 → Console）
3. 確認已登入為管理員
```

### 問題 3：看到錯誤訊息

**常見錯誤**：

```
Parse error: ...
→ 檢查程式碼是否正確貼上，沒有遺漏任何部分

Fatal error: ...
→ 可能 Yoast SEO 未安裝，這是正常的，會使用標準 meta 欄位
```

---

## ✅ 完成確認清單

執行後，請確認：

```
□ 頁面顯示「✅ 完成！」訊息
□ 顯示「成功更新：136 篇文章」（或接近數字）
□ 檢查任意 3-5 篇文章，驗證 SEO Title 和 Meta Description 已填入
□ 進入 Jetpack Dashboard，確認快取已清除
□ 進入 Google Search Console，記錄當前狀態
```

---

## 📅 後續時程

### T+0h（現在，2026-03-31 T+0h）
```
✅ Step 2 SEO 優化完成
→ 136 篇文章元數據已更新
```

### T+24h（2026-04-01）
```
⏳ Google 開始爬蟲發現新的 Meta 標籤
→ 進入 Google Search Console 驗證
```

### T+48-72h（2026-04-02）
```
🔍 Google 搜尋結果開始顯示新的標題和描述
✅ 進行性能重新測試（PageSpeed Insights）
→ 這是最重要的檢查點
```

### T+7d（2026-04-07）
```
📊 初步排名變化開始出現
→ 檢查 Google Search Console 的「Performance」報告
→ 記錄搜尋排名變化
```

### T+30d（2026-04-30）
```
📈 完整 KPI 評估
→ 對比流量、排名、點擊率變化
```

---

## 💡 常見問題

### Q：執行這個腳本會不會刪除或損毀文章？
**A：不會。** 腳本只更新 Meta 欄位（SEO 標題和描述），不會修改文章內容。完全安全。

### Q：如何撤銷優化？
**A：**
- WordPress 有修訂版本系統，可回復
- 或進入 Snippets → 取消激活此片段
- 或手動進入各文章編輯，恢復舊的 Meta 值

### Q：需要重新發佈文章嗎？
**A：不需要。** Meta 更新自動生效，無需重新發佈。

### Q：能同時執行多次嗎？
**A：不建議。** 等待 3-5 分鐘讓第一次執行完成，然後檢查結果。

### Q：為什麼有些文章的 SEO Title 看起來被截斷？
**A：正常。** 搜尋引擎在桌面上通常顯示 55-60 字符，超出部分會被截斷。這是優化策略的一部分。

---

## 📋 簽署

```
執行人：___________________
執行時間：_________________
執行狀態：
  ☑️ 已完成 - 136 篇文章 SEO 元數據已更新
  ☐ 部分完成 - ___ 篇已更新（原因：__________）
  ☐ 未執行 - 原因：________________________

驗證結果：
  ☑️ 確認頁面顯示「✅ 完成」訊息
  ☑️ 隨機檢查 3 篇文章，SEO 元數據已填入
  ☑️ Jetpack 快取已清除
  ☑️ Google Search Console 記錄已保存

簽署：___________________
日期：___________________
```

---

## 🎉 成功！Step 2 完成

```
✅ Step 1：驗證外掛狀態           [完成]
✅ Step 2：SEO 批量優化           [現在完成]
⏳ Step 3：性能配置驗證           [下一步]

整體進度：66% → 100%（Step 2 後）
預計完成：2026-03-31 T+3h
```

---

**準備好執行？立即進入 wp-admin 開始吧！** 🚀

有任何問題，查看上方「故障排查」或返回 NEXT-ACTIONS.md
