#!/usr/bin/env node

/**
 * YOLO LAB Homepage Builder
 *
 * Creates a static homepage with FSE block structure:
 * - Hero section (H1 + brand description)
 * - Category hubs (Film/Music/Tech/Sports/Entertainment) with Query Loops
 * - Pillar feature section
 * - Recent posts
 *
 * Usage:
 *   export ANTHROPIC_API_KEY="sk-ant-..."
 *   node scripts/homepage-builder.js --dry-run
 *   node scripts/homepage-builder.js
 */

import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// ─── Config ─────────────────────────────────────────────────────────────────

const CONFIG = {
  siteId: 133512998,
  siteDomain: "yololab.net",
  siteUrl: "https://yololab.net",
  pageTitle: "首頁",
  pageSlug: "home",
  outputDir: "./seo-optimization-output",
};

// ─── Helper Functions ───────────────────────────────────────────────────────

function parseArgs() {
  const args = process.argv.slice(2);
  const parsed = {
    dryRun: false,
  };

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    if (arg === "--dry-run") parsed.dryRun = true;
  }

  return parsed;
}

function ensureOutputDir() {
  if (!fs.existsSync(CONFIG.outputDir)) {
    fs.mkdirSync(CONFIG.outputDir, { recursive: true });
  }
}

// ─── FSE Block Template ──────────────────────────────────────────────────────

/**
 * Generate complete FSE block HTML for homepage
 */
function generateHomepageBlockHTML(categoryMap) {
  const {
    film = 96990390,
    music = 96990386,
    tech = 96990096,
    sports = 96990517,
  } = categoryMap;

  return `<!-- wp:template-part {"slug":"header","theme":"yolo-lab"} /-->

<!-- wp:cover {"url":"https://yololab.net/wp-content/uploads/hero-bg.jpg","dimRatio":40,"align":"full","style":{"spacing":{"padding":{"top":"60px","bottom":"60px"}}}} -->
<div class="wp-block-cover has-background-dim" style="background-color: #050811;padding-top: 60px;padding-bottom: 60px;"><div class="wp-block-cover__inner-container">
<!-- wp:heading {"level":1,"fontSize":"x-large","style":{"typography":{"fontStyle":"normal","fontWeight":"700"}}} -->
<h1 class="wp-block-heading has-x-large-font-size">YOLO LAB｜解構科技邊際與媒體娛樂的數據實驗室</h1>
<!-- /wp:heading -->

<!-- wp:paragraph {"fontSize":"large"} -->
<p class="has-large-font-size">我們深入分析電影、音樂、科技、體育與娛樂產業，透過數據視角揭示媒體真相。提供專業評論、產業動態、文化觀察與實驗性研究，是您了解當代文化的必讀媒體。</p>
<!-- /wp:paragraph -->

<!-- wp:buttons -->
<div class="wp-block-buttons">
<!-- wp:button {"backgroundColor":"vivid-cyan-blue","textColor":"black"} -->
<div class="wp-block-button"><a class="wp-block-button__link has-black-color has-vivid-cyan-blue-background-color wp-element-button" href="/category/film/">瀏覽分類</a></div>
<!-- /wp:button -->
</div>
<!-- /wp:buttons -->
</div></div>
<!-- /wp:cover -->

<!-- wp:group {"tagName":"section","align":"full","style":{"spacing":{"padding":{"top":"40px","bottom":"40px"}}}} -->
<section class="wp-block-group alignfull" style="padding-top: 40px;padding-bottom: 40px;">
<!-- wp:heading {"level":2,"fontSize":"large"} -->
<h2 class="wp-block-heading has-large-font-size">熱門精選</h2>
<!-- /wp:heading -->

<!-- wp:query {"query":{"perPage":4,"orderBy":"comment_count","order":"desc"},"align":"wide"} -->
<div class="wp-block-query">
<!-- wp:post-template {"layout":{"type":"grid","columnCount":4}} -->
<div>
<!-- wp:post-featured-image {"isLink":true,"width":"100%","height":"200px"} /-->
<!-- wp:post-title {"isLink":true,"level":3} /-->
</div>
<!-- /wp:post-template -->
</div>
<!-- /wp:query -->
</section>
<!-- /wp:group -->

<!-- wp:group {"tagName":"section","align":"full","style":{"spacing":{"padding":{"top":"40px","bottom":"40px"}},"backgroundColor":"#f5f5f5"}} -->
<section class="wp-block-group alignfull" style="padding-top: 40px;padding-bottom: 40px;background-color: #f5f5f5;">
<!-- wp:heading {"level":2,"fontSize":"large"} -->
<h2 class="wp-block-heading has-large-font-size">分類導覽</h2>
<!-- /wp:heading -->

<!-- wp:columns {"columns":5} -->
<div class="wp-block-columns">
<!-- wp:column -->
<div class="wp-block-column">
<!-- wp:heading {"level":2,"fontSize":"medium"} -->
<h2 class="wp-block-heading has-medium-font-size"><a href="/category/film/">電影</a></h2>
<!-- /wp:heading -->
<!-- wp:query {"query":{"perPage":3,"categoryIds":[${film}]},"inherit":false} -->
<div class="wp-block-query">
<!-- wp:post-template {"layout":{"type":"list"}} -->
<div>
<!-- wp:post-featured-image {"width":"100%","height":"120px","isLink":true} /-->
<!-- wp:post-title {"isLink":true,"level":3,"fontSize":"small"} /-->
</div>
<!-- /wp:post-template -->
</div>
<!-- /wp:query -->
<!-- wp:button {"size":"small"} -->
<div class="wp-block-button has-custom-width"><a class="wp-block-button__link wp-element-button" href="/category/film/">所有電影 →</a></div>
<!-- /wp:button -->
</div>
<!-- /wp:column -->

<!-- wp:column -->
<div class="wp-block-column">
<!-- wp:heading {"level":2,"fontSize":"medium"} -->
<h2 class="wp-block-heading has-medium-font-size"><a href="/category/music/">音樂</a></h2>
<!-- /wp:heading -->
<!-- wp:query {"query":{"perPage":3,"categoryIds":[${music}]},"inherit":false} -->
<div class="wp-block-query">
<!-- wp:post-template {"layout":{"type":"list"}} -->
<div>
<!-- wp:post-featured-image {"width":"100%","height":"120px","isLink":true} /-->
<!-- wp:post-title {"isLink":true,"level":3,"fontSize":"small"} /-->
</div>
<!-- /wp:post-template -->
</div>
<!-- /wp:query -->
<!-- wp:button {"size":"small"} -->
<div class="wp-block-button has-custom-width"><a class="wp-block-button__link wp-element-button" href="/category/music/">所有音樂 →</a></div>
<!-- /wp:button -->
</div>
<!-- /wp:column -->

<!-- wp:column -->
<div class="wp-block-column">
<!-- wp:heading {"level":2,"fontSize":"medium"} -->
<h2 class="wp-block-heading has-medium-font-size"><a href="/category/tech/">科技</a></h2>
<!-- /wp:heading -->
<!-- wp:query {"query":{"perPage":3,"categoryIds":[${tech}]},"inherit":false} -->
<div class="wp-block-query">
<!-- wp:post-template {"layout":{"type":"list"}} -->
<div>
<!-- wp:post-featured-image {"width":"100%","height":"120px","isLink":true} /-->
<!-- wp:post-title {"isLink":true,"level":3,"fontSize":"small"} /-->
</div>
<!-- /wp:post-template -->
</div>
<!-- /wp:query -->
<!-- wp:button {"size":"small"} -->
<div class="wp-block-button has-custom-width"><a class="wp-block-button__link wp-element-button" href="/category/tech/">所有科技 →</a></div>
<!-- /wp:button -->
</div>
<!-- /wp:column -->

<!-- wp:column -->
<div class="wp-block-column">
<!-- wp:heading {"level":2,"fontSize":"medium"} -->
<h2 class="wp-block-heading has-medium-font-size"><a href="/category/sports/">運動</a></h2>
<!-- /wp:heading -->
<!-- wp:query {"query":{"perPage":3,"categoryIds":[${sports}]},"inherit":false} -->
<div class="wp-block-query">
<!-- wp:post-template {"layout":{"type":"list"}} -->
<div>
<!-- wp:post-featured-image {"width":"100%","height":"120px","isLink":true} /-->
<!-- wp:post-title {"isLink":true,"level":3,"fontSize":"small"} /-->
</div>
<!-- /wp:post-template -->
</div>
<!-- /wp:query -->
<!-- wp:button {"size":"small"} -->
<div class="wp-block-button has-custom-width"><a class="wp-block-button__link wp-element-button" href="/category/sports/">所有運動 →</a></div>
<!-- /wp:button -->
</div>
<!-- /wp:column -->

<!-- wp:column -->
<div class="wp-block-column">
<!-- wp:heading {"level":2,"fontSize":"medium"} -->
<h2 class="wp-block-heading has-medium-font-size"><a href="/search/">更多</a></h2>
<!-- /wp:heading -->
<!-- wp:paragraph -->
<p>探索其他分類與標籤</p>
<!-- /wp:paragraph -->
<!-- wp:button {"size":"small"} -->
<div class="wp-block-button has-custom-width"><a class="wp-block-button__link wp-element-button" href="/search/">搜尋文章 →</a></div>
<!-- /wp:button -->
</div>
<!-- /wp:column -->
</div>
<!-- /wp:columns -->
</section>
<!-- /wp:group -->

<!-- wp:group {"tagName":"section","align":"full","style":{"spacing":{"padding":{"top":"40px","bottom":"40px"}}}} -->
<section class="wp-block-group alignfull" style="padding-top: 40px;padding-bottom: 40px;">
<!-- wp:heading {"level":2,"fontSize":"large"} -->
<h2 class="wp-block-heading has-large-font-size">最新發布</h2>
<!-- /wp:heading -->

<!-- wp:query {"query":{"perPage":9}} -->
<div class="wp-block-query">
<!-- wp:post-template {"layout":{"type":"grid","columnCount":3}} -->
<div>
<!-- wp:post-featured-image {"width":"100%","height":"200px","isLink":true} /-->
<!-- wp:post-title {"isLink":true,"level":3} /-->
<!-- wp:post-date /-->
</div>
<!-- /wp:post-template -->
<!-- wp:query-pagination /-->
</div>
<!-- /wp:query -->
</section>
<!-- /wp:group -->

<!-- wp:template-part {"slug":"footer","theme":"yolo-lab"} /-->`;
}

// ─── Main ───────────────────────────────────────────────────────────────────

async function main() {
  const args = parseArgs();
  ensureOutputDir();

  // Load category IDs
  const categoryMapPath = path.join(__dirname, "../data/category-map.json");
  if (!fs.existsSync(categoryMapPath)) {
    console.error("❌ category-map.json not found. Run Task #1 first.");
    process.exit(1);
  }

  const categoryData = JSON.parse(fs.readFileSync(categoryMapPath, "utf-8"));
  const primaryCategories = categoryData.primary_categories || {};

  const categoryMap = {
    film: primaryCategories.film?.id,
    music: primaryCategories.music?.id,
    tech: primaryCategories.tech?.id,
    sports: primaryCategories.sports?.id,
  };

  // Generate FSE block HTML
  const blockHTML = generateHomepageBlockHTML(categoryMap);

  // Prepare page payload
  const pagePayload = {
    title: CONFIG.pageTitle,
    slug: CONFIG.pageSlug,
    status: "publish",
    type: "page",
    content: blockHTML,
  };

  console.log("🏗️  YOLO LAB Homepage Builder");
  console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
  console.log(`Site: ${CONFIG.siteDomain}`);
  console.log(`Page Title: ${CONFIG.pageTitle}`);
  console.log(`Page Slug: ${CONFIG.pageSlug}`);
  console.log(`Categories: Film(${categoryMap.film}) | Music(${categoryMap.music}) | Tech(${categoryMap.tech}) | Sports(${categoryMap.sports})`);
  console.log("");

  if (args.dryRun) {
    console.log("📋 DRY RUN — Preview Only");
    console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
    console.log("Page Payload:");
    console.log(JSON.stringify(pagePayload, null, 2).substring(0, 500) + "...");
    console.log("");
    console.log("✅ Dry run complete. Block HTML saved to:");
    console.log(`   ${CONFIG.outputDir}/homepage-block.html`);

    // Save block HTML for review
    fs.writeFileSync(
      path.join(CONFIG.outputDir, "homepage-block.html"),
      blockHTML
    );
  } else {
    console.log("⚠️  ACTUAL EXECUTION (not dry-run)");
    console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
    console.log("This would create/update the homepage page on WordPress.com.");
    console.log("Requires ANTHROPIC_API_KEY and WordPress.com authentication.");
    console.log("");
    console.log("Next steps:");
    console.log("1. Use wpcom-mcp-content-authoring pages.create endpoint");
    console.log("2. Set page as static front page via WordPress Settings > Reading");
    console.log("3. Verify category Query Loops render correctly");
    console.log("");
    console.log("📝 Page payload for API call:");
    console.log(JSON.stringify(pagePayload, null, 2).substring(0, 300) + "...");

    // Save page payload for later
    fs.writeFileSync(
      path.join(CONFIG.outputDir, "homepage-page-payload.json"),
      JSON.stringify(pagePayload, null, 2)
    );

    // Save block HTML
    fs.writeFileSync(
      path.join(CONFIG.outputDir, "homepage-block.html"),
      blockHTML
    );

    console.log("");
    console.log("✅ Files saved:");
    console.log(`   - ${CONFIG.outputDir}/homepage-page-payload.json`);
    console.log(`   - ${CONFIG.outputDir}/homepage-block.html`);
  }
}

main().catch((err) => {
  console.error("❌ Error:", err.message);
  process.exit(1);
});
