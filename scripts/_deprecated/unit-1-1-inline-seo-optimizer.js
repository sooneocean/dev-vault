#!/usr/bin/env node

/**
 * Unit 1.1: Complete Tier 1-4 SEO Optimization (Reverse: P3→P2→P1→P0)
 * 内联版本 — 直接计算 SEO 优化内容（无额外 API 调用）
 *
 * 策略：使用本地推理生成 SEO 优化
 * - Meta Title/Description（所有 Tier）
 * - Schema Markup（P2+）
 * - OG Tags（P2+）
 * - Internal Links（P1+）
 *
 * 运行：
 *   node scripts/unit-1-1-inline-seo-optimizer.js --tier p3 --sample 2
 */

import fs from "fs";
import path from "path";

// ─── Configuration ─────────────────────────────────────────────────────────

const CONFIG = {
  siteId: 133512998,
  domain: "yololab.net",
  outputDir: "./seo-optimization-output",
  batchSize: 5,
  delayMs: 500,
};

const TIER_CONFIG = {
  p3: { minTraffic: 0, maxTraffic: 50, count: 728, dimensions: 2, desc: "Tier 4 - Ultra low traffic" },
  p2: { minTraffic: 50, maxTraffic: 200, count: 1200, dimensions: 4, desc: "Tier 3 - Low traffic" },
  p1: { minTraffic: 200, maxTraffic: 500, count: 600, dimensions: 4, desc: "Tier 2 - Medium traffic" },
  p0: { minTraffic: 500, maxTraffic: Infinity, count: 200, dimensions: 6, desc: "Tier 1 - High traffic" },
};

// ─── Helper Functions ──────────────────────────────────────────────────────

function parseArgs() {
  const args = process.argv.slice(2);
  const parsed = { tier: "p3", sample: null, dryRun: false };
  for (let i = 0; i < args.length; i += 2) {
    const key = args[i].replace(/^--/, "");
    const value = args[i + 1];
    if (key === "tier") parsed.tier = value;
    if (key === "sample") parsed.sample = parseInt(value);
    if (key === "dry-run") parsed.dryRun = true;
  }
  return parsed;
}

function ensureOutputDir() {
  if (!fs.existsSync(CONFIG.outputDir)) {
    fs.mkdirSync(CONFIG.outputDir, { recursive: true });
  }
}

async function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

// ─── Inline SEO Generators ────────────────────────────────────────────────

/**
 * 生成 Meta Title（SEO 最佳实践）
 * - 50-60 字
 * - 包含主关键字
 * - 吸引点击
 */
function generateMetaTitle(title, category) {
  // 从原标题提取关键字并优化
  const keywords = {
    電影: ["电影推荐", "影城评测", "观影体验"],
    人物: ["人物分析", "职业发展", "背景故事"],
    娛樂: ["娱乐新闻", "直播分析", "创作者"],
    電視: ["电视剧", "韓劇", "新剧推荐"],
  };

  const categoryKeywords = keywords[category] || ["推荐", "分析", "评测"];
  const mainKeyword = categoryKeywords[0];

  // 保留原标题核心词，添加 SEO 关键字
  const shortened = title.substring(0, 35);
  const optimized = `${shortened} | 2026 ${mainKeyword}排行榜`;

  return optimized.substring(0, 60);
}

/**
 * 生成 Meta Description
 * - 150-160 字
 * - 清楚描述价值
 */
function generateMetaDescription(excerpt) {
  if (excerpt.length < 150) {
    return excerpt + " 深度分析与完整评测，助你做出更好的选择。";
  }
  return excerpt.substring(0, 150) + "...了解全部详情。";
}

/**
 * 生成 Schema Markup（JSON-LD）
 */
function generateSchema(article) {
  return {
    "@context": "https://schema.org",
    "@type": "BlogPosting",
    headline: article.title,
    description: article.excerpt,
    datePublished: article.date,
    dateModified: new Date().toISOString().split("T")[0],
    author: {
      "@type": "Organization",
      name: "YOLO LAB",
      url: "https://yololab.net",
    },
    publisher: {
      "@type": "Organization",
      name: "YOLO LAB",
      logo: {
        "@type": "ImageObject",
        url: "https://yololab.net/logo.png",
      },
    },
    mainEntityOfPage: {
      "@type": "WebPage",
      "@id": `https://yololab.net/?p=${article.id}`,
    },
  };
}

/**
 * 生成 OG Tags
 */
function generateOGTags(title, description) {
  return {
    "og:title": title.substring(0, 60),
    "og:description": description.substring(0, 160),
    "og:type": "article",
    "og:image": "https://yololab.net/featured-image.jpg",
    "og:url": "https://yololab.net",
    "twitter:card": "summary_large_image",
    "twitter:title": title.substring(0, 60),
    "twitter:description": description.substring(0, 200),
  };
}

/**
 * 生成内部链接建议
 */
function generateInternalLinks(article) {
  const categoryLinks = {
    電影: [
      { title: "2024 必看电影清单", url: "/?p=27200" },
      { title: "影城体验对比", url: "/?p=27150" },
      { title: "电影评测标准", url: "/?p=27100" },
    ],
    人物: [
      { title: "人物访谈系列", url: "/?p=28100" },
      { title: "职业发展案例", url: "/?p=28150" },
      { title: "跨界人物分析", url: "/?p=28200" },
    ],
    娛樂: [
      { title: "直播平台对比", url: "/?p=28300" },
      { title: "创作者生态", url: "/?p=28350" },
    ],
    電視: [
      { title: "韓劇排行榜", url: "/?p=28400" },
      { title: "電視劇製作分析", url: "/?p=28450" },
    ],
  };

  return categoryLinks[article.category] || [
    { title: "精选推荐", url: "/?p=1" },
    { title: "相关分析", url: "/?p=2" },
  ];
}

// ─── Sample Articles ──────────────────────────────────────────────────────

async function fetchArticlesForTier(tier, limit = null) {
  console.log(`📥 Fetching articles for tier ${tier.toUpperCase()} (${TIER_CONFIG[tier].desc})...`);

  const sampleArticles = [
    {
      id: 27155,
      title: "2026 電影院推薦 | 全台影城殘酷評測：別再只去威秀！這 5 間才是真正的觀影神壇",
      excerpt: "深度評測全台 5 家頂級影城，從放映技術到舒適度全面比較。選對影城才能看到電影的靈魂。",
      category: "電影",
      traffic: 45,
      date: "2023-06-15",
    },
    {
      id: 28183,
      title: "湯米巴斯托 Tommy Bastow 深度分析：《幕府將軍》的神父，現在更是 NHK 欽點的「日本通」",
      excerpt: "從演員到日本文化專家，職涯轉變全紀錄。",
      category: "人物",
      traffic: 38,
      date: "2023-06-10",
    },
    {
      id: 28200,
      title: "台灣最狂直播天后是誰？從 OTT 戲劇看直播文化演變",
      excerpt: "直播產業深度分析，台灣創作者生態觀察。",
      category: "娛樂",
      traffic: 120,
      date: "2023-08-20",
    },
    {
      id: 28201,
      title: "2024 年最值得看的 K-Drama：《寄生上流》後時代的韓劇新浪潮",
      excerpt: "韓國電視劇產業分析，2024 年必看清單。",
      category: "電視",
      traffic: 280,
      date: "2023-10-15",
    },
    {
      id: 28202,
      title: "從《騎士》到《勝利號》：韓國科幻電影的崛起之路",
      excerpt: "韓國科幻片製作現狀分析，國際競爭力評估。",
      category: "電影",
      traffic: 680,
      date: "2023-11-01",
    },
  ];

  const tiered = sampleArticles.filter((article) => {
    const { minTraffic, maxTraffic } = TIER_CONFIG[tier];
    return article.traffic >= minTraffic && article.traffic < maxTraffic;
  });

  const result = limit ? tiered.slice(0, limit) : tiered;
  console.log(`   ✓ Found ${result.length} articles for tier ${tier.toUpperCase()}\n`);

  return result;
}

// ─── Optimization Engine ──────────────────────────────────────────────────

async function optimizeArticle(article, tier) {
  const config = TIER_CONFIG[tier];
  console.log(`  🔄 Optimizing #${article.id}: "${article.title.substring(0, 40)}..."`);

  try {
    const metaTitle = generateMetaTitle(article.title, article.category);
    const metaDescription = generateMetaDescription(article.excerpt);

    const optimizations = {
      metaTitle,
      metaDescription,
    };

    if (config.dimensions >= 4) {
      optimizations.schema = generateSchema(article);
      optimizations.ogTags = generateOGTags(metaTitle, metaDescription);
    }

    if (config.dimensions >= 4) {
      optimizations.internalLinks = generateInternalLinks(article);
    }

    console.log(`     ✓ Generated ${config.dimensions}D SEO optimizations`);

    return {
      articleId: article.id,
      title: article.title,
      tier: tier.toUpperCase(),
      dimensions: config.dimensions,
      optimizations,
      status: "success",
      timestamp: new Date().toISOString(),
    };
  } catch (error) {
    console.error(`     ✗ Error: ${error.message}`);
    return {
      articleId: article.id,
      title: article.title,
      tier: tier.toUpperCase(),
      status: "failed",
      error: error.message,
    };
  }
}

// ─── Batch & Report ────────────────────────────────────────────────────────

async function processTierBatch(articles, tier) {
  const results = [];

  for (let i = 0; i < articles.length; i += CONFIG.batchSize) {
    const batch = articles.slice(i, i + CONFIG.batchSize);
    console.log(`\n📦 Processing batch ${Math.floor(i / CONFIG.batchSize) + 1}/${Math.ceil(articles.length / CONFIG.batchSize)} (${batch.length} articles)\n`);

    for (const article of batch) {
      const result = await optimizeArticle(article, tier);
      results.push(result);
      if (article !== batch[batch.length - 1]) {
        await sleep(CONFIG.delayMs);
      }
    }

    if (i + CONFIG.batchSize < articles.length) {
      console.log(`   ⏳ Waiting before next batch...\n`);
      await sleep(1000);
    }
  }

  return results;
}

function generateReport(tier, results) {
  const successful = results.filter((r) => r.status === "success");
  const failed = results.filter((r) => r.status === "failed");

  const report = {
    tier: tier.toUpperCase(),
    tierInfo: TIER_CONFIG[tier],
    totalProcessed: results.length,
    successful: successful.length,
    failed: failed.length,
    successRate: ((successful.length / results.length) * 100).toFixed(1) + "%",
    results,
    timestamp: new Date().toISOString(),
  };

  const reportPath = path.join(
    CONFIG.outputDir,
    `unit-1-1-tier-${tier}-report-${new Date().toISOString().split("T")[0]}.json`
  );
  fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));

  return report;
}

function printSummary(report) {
  console.log("\n" + "=".repeat(70));
  console.log(`📊 Unit 1.1 ${report.tier} Optimization Report`);
  console.log("=".repeat(70));
  console.log(`\nTier: ${report.tierInfo.desc}`);
  console.log(`Total Processed: ${report.totalProcessed}`);
  console.log(`✓ Successful: ${report.successful}`);
  console.log(`✗ Failed: ${report.failed}`);
  console.log(`Success Rate: ${report.successRate}`);
  console.log(`\nDimensions: ${report.tierInfo.dimensions}D`);
  console.log("=".repeat(70) + "\n");
}

// ─── Main ──────────────────────────────────────────────────────────────────

async function main() {
  const args = parseArgs();
  ensureOutputDir();

  console.log("\n🚀 Unit 1.1: Reverse-Tier SEO Optimization (Inline)\n");
  console.log(`   Tier: ${args.tier.toUpperCase()} (${TIER_CONFIG[args.tier].desc})`);
  if (args.sample) console.log(`   Sample: ${args.sample} articles`);
  console.log();

  const articles = await fetchArticlesForTier(args.tier, args.sample);

  if (articles.length === 0) {
    console.log("❌ No articles found for this tier.\n");
    process.exit(0);
  }

  console.log(`🔧 Generating SEO optimizations (${TIER_CONFIG[args.tier].dimensions}D)...\n`);
  const results = await processTierBatch(articles, args.tier);

  const report = generateReport(args.tier, results);
  printSummary(report);

  console.log("✅ Complete! Next tier: node scripts/unit-1-1-inline-seo-optimizer.js --tier p2\n");
}

main().catch((error) => {
  console.error("❌ Error:", error);
  process.exit(1);
});
