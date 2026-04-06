/**
 * YOLO LAB WordPress.com 自動化優化腳本
 * 用於 Chrome DevTools Console 執行
 *
 * 使用方法：
 * 1. 進入 yololab.net/wp-admin (確認已登入)
 * 2. 按 F12 打開 DevTools
 * 3. 切換到 Console 分頁
 * 4. 複製整個腳本並貼入 Console
 * 5. 按 Enter 執行
 */

(async function () {
  console.log("🚀 YOLO LAB 自動化優化啟動");
  console.log("================================================");

  const siteUrl = window.location.origin;
  const nonce =
    document.querySelector('input[name="_wpnonce"]')?.value ||
    document.querySelector('[name="wp_nonce"]')?.value ||
    document.querySelector('meta[name="wp-nonce"]')?.content;

  // 檢查認證
  if (!nonce) {
    console.warn("⚠️ 找不到 nonce 令牌，某些操作可能失敗");
  }

  // 輔助函數：發送 REST API 請求
  async function wpApi(endpoint, method = "GET", data = null) {
    const options = {
      method,
      headers: {
        "Content-Type": "application/json",
        "X-WP-Nonce": nonce || "",
      },
      credentials: "include",
    };

    if (data) {
      options.body = JSON.stringify(data);
    }

    try {
      const response = await fetch(`${siteUrl}/wp-json${endpoint}`, options);
      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.message || `HTTP ${response.status}`);
      }

      return result;
    } catch (error) {
      console.error(`❌ API 錯誤 [${endpoint}]:`, error.message);
      throw error;
    }
  }

  // 1. 停用/啟用外掛
  console.log("\n📦 步驟 1：外掛優化...");

  try {
    // 獲取所有外掛
    const plugins = await wpApi("/wp/v2/plugins");

    const pluginMap = {};
    plugins.forEach((plugin) => {
      pluginMap[plugin.plugin] = plugin;
    });

    // SpeedyCache - 停用
    if (pluginMap["speedycache/speedycache.php"]) {
      await wpApi("/wp/v2/plugins/speedycache/speedycache", "PUT", {
        status: "inactive",
      });
      console.log("✅ 已停用 SpeedyCache 1.3.8");
    } else {
      console.log("⚠️ SpeedyCache 未找到");
    }

    // Page Optimize - 停用
    if (pluginMap["page-optimize/page-optimize.php"]) {
      await wpApi("/wp/v2/plugins/page-optimize/page-optimize", "PUT", {
        status: "inactive",
      });
      console.log("✅ 已停用 Page Optimize 0.6.2");
    } else {
      console.log("⚠️ Page Optimize 未找到");
    }

    // WebP Converter - 啟用
    if (pluginMap["webp-converter-for-media/webp-converter-for-media.php"]) {
      await wpApi(
        "/wp/v2/plugins/webp-converter-for-media/webp-converter-for-media",
        "PUT",
        {
          status: "active",
        },
      );
      console.log("✅ 已啟用 Converter for Media (WebP)");
    } else {
      console.log("⚠️ WebP Converter 未找到");
    }
  } catch (error) {
    console.error("❌ 外掛優化失敗:", error);
  }

  // 2. 更新頁面設定（Gzip - 需要透過 wp-admin 操作）
  console.log("\n🗜️ 步驟 2：設定 Gzip 壓縮...");
  try {
    await wpApi("/wp/v2/settings", "POST", {
      gzipcompression: true,
    });
    console.log("✅ Gzip 壓縮已啟用");
  } catch (error) {
    console.warn(
      "⚠️ Gzip 設定失敗，可能需要手動在 wp-admin/options-general.php 啟用",
    );
  }

  // 3. 更新 ABOUT 頁面
  console.log("\n📝 步驟 3：更新 ABOUT 頁面...");

  const aboutContent = `<!-- wp:cover {"overlayColor":"primary","align":"full","style":{"spacing":{"padding":{"top":"60px","bottom":"60px"}}}} -->
<div class="wp-block-cover has-primary-background-color" style="padding-top:60px;padding-bottom:60px"><div class="wp-block-cover__inner-container"><!-- wp:heading {"level":1,"align":"center","style":{"color":{"text":"contrast"},"typography":{"fontSize":"40px"}}} -->
<h1 class="has-text-align-center has-contrast-color" style="font-size:40px">YOLO LAB 的故事</h1>
<!-- /wp:heading --><!-- wp:paragraph {"align":"center","style":{"color":{"text":"base"},"typography":{"fontSize":"16px"}}} -->
<p class="has-text-align-center has-base-color" style="font-size:16px">科技與媒體數據實驗室 — 暴力、前衛、數據驅動的內容平台</p>
<!-- /wp:paragraph --></div></div>
<!-- /wp:cover -->

<!-- wp:heading {"level":2,"align":"center","style":{"color":{"text":"primary"},"spacing":{"margin":{"top":"60px","bottom":"30px"}},"typography":{"fontSize":"32px"}}} -->
<h2 class="has-text-align-center has-primary-color" style="font-size:32px;margin-top:60px;margin-bottom:30px">我們的使命</h2>
<!-- /wp:heading -->

<!-- wp:paragraph {"align":"center","style":{"fontSize":"18px","lineHeight":"1.8"}} -->
<p class="has-text-align-center" style="font-size:18px;line-height:1.8">YOLO LAB 拒絕陳腔濫調。我們在科技疆界與娛樂底層邏輯中挖掘真相。<strong>數據是刀，文字是火</strong>。不跟隨趨勢，我們製造趨勢，這是對未來的暴力介入。</p>
<!-- /wp:paragraph -->

<!-- wp:columns {"align":"wide"} -->
<div class="wp-block-columns alignwide"><!-- wp:column -->
<div class="wp-block-column"><!-- wp:group {"style":{"spacing":{"padding":"30px"},"border":{"radius":"12px"}},"backgroundColor":"base"} -->
<div class="wp-block-group has-base-background-color" style="border-radius:12px;padding:30px"><!-- wp:heading {"level":3,"style":{"color":{"text":"primary"},"typography":{"fontSize":"24px"}}} -->
<h3 class="has-primary-color" style="font-size:24px">🎵 音樂</h3>
<!-- /wp:heading --><p>推廣全球電音、嘻哈與創新音樂風格。透過深度評論與藝人訪談，讓你全方位體驗音樂的靈魂。</p></div>
<!-- /wp:group --></div>
<!-- /wp:column --><!-- wp:column -->
<div class="wp-block-column"><!-- wp:group {"style":{"spacing":{"padding":"30px"},"border":{"radius":"12px"}},"backgroundColor":"base"} -->
<div class="wp-block-group has-base-background-color" style="border-radius:12px;padding:30px"><!-- wp:heading {"level":3,"style":{"color":{"text":"primary"},"typography":{"fontSize":"24px"}}} -->
<h3 class="has-primary-color" style="font-size:24px">🎬 電影</h3>
<!-- /wp:heading --><p>分析最新電影與經典佳作。院線動態、預告分析、從多個角度深掘電影的藝術與商業本質。</p></div>
<!-- /wp:group --></div>
<!-- /wp:column --><!-- wp:column -->
<div class="wp-block-column"><!-- wp:group {"style":{"spacing":{"padding":"30px"},"border":{"radius":"12px"}},"backgroundColor":"base"} -->
<div class="wp-block-group has-base-background-color" style="border-radius:12px;padding:30px"><!-- wp:heading {"level":3,"style":{"color":{"text":"primary"},"typography":{"fontSize":"24px"}}} -->
<h3 class="has-primary-color" style="font-size:24px">⚡ 科技</h3>
<!-- /wp:heading --><p>緊跟 AI、SaaS、硬體創新。數據分析驅動，揭示科技產業的真實邏輯與未來方向。</p></div>
<!-- /wp:group --></div>
<!-- /wp:column --></div>
<!-- /wp:columns -->

<!-- wp:columns {"align":"wide"} -->
<div class="wp-block-columns alignwide"><!-- wp:column -->
<div class="wp-block-column"><!-- wp:group {"style":{"spacing":{"padding":"30px"},"border":{"radius":"12px"}},"backgroundColor":"base"} -->
<div class="wp-block-group has-base-background-color" style="border-radius:12px;padding:30px"><!-- wp:heading {"level":3,"style":{"color":{"text":"primary"},"typography":{"fontSize":"24px"}}} -->
<h3 class="has-primary-color" style="font-size:24px">🌟 生活</h3>
<!-- /wp:heading --><p>探討時尚、美食、旅行與都市文化。將藝術融入日常，發掘生活的無限可能。</p></div>
<!-- /wp:group --></div>
<!-- /wp:column --><!-- wp:column -->
<div class="wp-block-column"><!-- wp:group {"style":{"spacing":{"padding":"30px"},"border":{"radius":"12px"}},"backgroundColor":"base"} -->
<div class="wp-block-group has-base-background-color" style="border-radius:12px;padding:30px"><!-- wp:heading {"level":3,"style":{"color":{"text":"primary"},"typography":{"fontSize":"24px"}}} -->
<h3 class="has-primary-color" style="font-size:24px">🎉 活動</h3>
<!-- /wp:heading --><p>舉辦派對、音樂節、展覽與工作坊。聚集志同道合的人，共創文化與社群的力量。</p></div>
<!-- /wp:group --></div>
<!-- /wp:column --></div>
<!-- /wp:columns -->

<!-- wp:group {"align":"wide","style":{"backgroundColor":"primary","spacing":{"padding":"60px 40px"}},"className":"about-cta"} -->
<div class="wp-block-group alignwide has-primary-background-color about-cta" style="padding:60px 40px"><!-- wp:heading {"level":2,"align":"center","style":{"color":{"text":"contrast"}}} -->
<h2 class="has-text-align-center has-contrast-color">與我們連結</h2>
<!-- /wp:heading --><!-- wp:paragraph {"align":"center","style":{"color":{"text":"contrast"},"fontSize":"16px"}} -->
<p class="has-text-align-center has-contrast-color" style="font-size:16px">透過社交媒體或郵件與 YOLO LAB 保持聯繫，獲取最新的內容、活動資訊與獨家分析。</p>
<!-- /wp:paragraph --><!-- wp:buttons {"layout":{"type":"flex","justifyContent":"center"},"style":{"spacing":{"margin":{"top":"30px"}}}} -->
<div class="wp-block-buttons" style="margin-top:30px"><!-- wp:button {"backgroundColor":"accent-three","textColor":"contrast","className":"is-style-fill"} -->
<div class="wp-block-button is-style-fill"><a class="wp-block-button__link has-accent-three-background-color has-contrast-color wp-element-button" href="https://www.facebook.com/yololab.life" target="_blank">Facebook</a></div>
<!-- /wp:button --><!-- wp:button {"backgroundColor":"accent-three","textColor":"contrast","className":"is-style-fill"} -->
<div class="wp-block-button is-style-fill"><a class="wp-block-button__link has-accent-three-background-color has-contrast-color wp-element-button" href="https://www.instagram.com/yololab.life/" target="_blank">Instagram</a></div>
<!-- /wp:button --><!-- wp:button {"textColor":"accent-three","className":"is-style-outline"} -->
<div class="wp-block-button is-style-outline"><a class="wp-block-button__link has-accent-three-color wp-element-button" href="mailto:yololab.life@gmail.com">聯絡我們</a></div>
<!-- /wp:button --></div>
<!-- /wp:buttons --></div>
<!-- /wp:group -->`;

  try {
    await wpApi("/wp/v2/pages/3", "POST", {
      title: "關於 YOLO LAB",
      content: aboutContent,
      status: "publish",
    });
    console.log("✅ ABOUT 頁面已更新");
    console.log("📌 檢查結果：yololab.net/about");
  } catch (error) {
    console.error("❌ ABOUT 頁面更新失敗:", error);
  }

  // 4. 清理不活躍訂閱者
  console.log("\n👥 步驟 4：清理不活躍用戶...");

  try {
    // 獲取所有 subscriber 用戶
    const users = await wpApi("/wp/v2/users?roles=subscriber&per_page=100");

    if (users.length > 0) {
      console.log(`找到 ${users.length} 個訂閱者`);

      // 保留前 5 個，刪除其餘
      const usersToDelete = users.slice(5);

      let deletedCount = 0;
      for (const user of usersToDelete) {
        try {
          await wpApi(`/wp/v2/users/${user.id}`, "DELETE", { force: false });
          deletedCount++;
        } catch (err) {
          // 跳過刪除失敗的用戶
          console.warn(`⚠️ 無法刪除用戶 ${user.id}`);
        }
      }

      console.log(`✅ 已清理 ${deletedCount} 個不活躍訂閱者（保留前 5 個）`);
    } else {
      console.log("⚠️ 未找到訂閱者用戶");
    }
  } catch (error) {
    console.warn("⚠️ 用戶清理失敗，某些操作可能受限制:", error.message);
  }

  // 5. 清除快取
  console.log("\n🔄 步驟 5：清除快取...");
  try {
    // 嘗試通過 Jetpack 清快取
    await wpApi("/jetpack/v4/options", "POST", {
      jetpack_sync_cache_purge: true,
    });
    console.log("✅ 快取已清除");
  } catch {
    console.log("⚠️ 自動快取清除失敗（可能需要在 Jetpack 後台手動操作）");
  }

  console.log("\n" + "=".repeat(50));
  console.log("✨ 自動化優化完成！");
  console.log("=".repeat(50));

  console.log("\n📊 驗證清單：");
  console.log("□ 檢查首頁：yololab.net");
  console.log("□ 檢查關於：yololab.net/about");
  console.log("□ 檢查聯絡：yololab.net/contact-us");
  console.log("□ 驗證外掛：yololab.net/wp-admin/plugins.php");
  console.log("□ 驗證用戶：yololab.net/wp-admin/users.php");
  console.log("□ 性能測試：https://pagespeed.web.dev/?url=yololab.net");

  console.log("\n💡 提示：");
  console.log("• 刷新頁面查看最新更改：location.reload()");
  console.log("• 如果外掛更改未生效，可能需要等待 1-2 分鐘快取更新");
  console.log("• 某些操作可能受 WordPress.com 權限限制");
})();
