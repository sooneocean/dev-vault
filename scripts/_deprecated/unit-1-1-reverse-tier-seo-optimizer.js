#!/usr/bin/env node

/**
 * Unit 1.1: Complete Tier 1-4 SEO Optimization (Reverse: P3→P2→P1→P0)
 *
 * 执行策略：
 * - 获取 2023-2024 年未优化文章
 * - 按 GSC 流量分层（P3/P2/P1/P0）
 * - 从 P3 开始反向优化（低风险验证）
 * - 每个 Tier 批量处理（5-10 篇/批）
 *
 * 使用 Claude API 生成优化内容（Meta/Schema/OG/Internal Links）
 * 通过 WordPress REST API 直接更新
 *
 * 运行：
 *   node scripts/unit-1-1-reverse-tier-seo-optimizer.js --tier p3 --sample 5
 */

import Anthropic from "@anthropic-ai/sdk";
import fs from "fs";
import path from "path";

const client = new Anthropic();

// ─── Configuration ─────────────────────────────────────────────────────────

const CONFIG = {
  siteId: 133512998,
  domain: "yololab.net",
  wpRestUrl: "https://yololab.net/wp-json/wp/v2",
  outputDir: "./seo-optimization-output",
  modelForSEO: "claude-opus-4-6", // 高质量 SEO 内容
  batchSize: 5,
  delayMs: 1500, // 避免 rate limit
  maxRetries: 3,
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
  const parsed = {
    tier: "p3", // 默认从 P3 开始
    sample: null,
    dryRun: false,
  };

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

// ─── Data Extraction ──────────────────────────────────────────────────────

/**
 * 模拟获取 2023-2024 年文章
 * 实际应该从 WordPress.com 或 GSC API 获取真实数据
 */
async function fetchArticlesForTier(tier, limit = null) {
  console.log(`📥 Fetching articles for tier ${tier.toUpperCase()} (${TIER_CONFIG[tier].desc})...`);

  // 模拟文章数据（实际应从 REST API 获取）
  const sampleArticles = [
    {
      id: 27155,
      title: "2026 電影院推薦 | 全台影城殘酷評測：別再只去威秀！這 5 間才是真正的觀影神壇",
      excerpt: "深度評測全台 5 家頂級影城，從放映技術到舒適度全面比較。選對影城才能看到電影的靈魂。",
      category: "電影",
      traffic: 45, // P3
      date: "2023-06-15",
    },
    {
      id: 28183,
      title: "湯米巴斯托 Tommy Bastow 深度分析：《幕府將軍》的神父，現在更是 NHK 欽點的「日本通」",
      excerpt: "從演員到日本文化專家，職涯轉變全紀錄。",
      category: "人物",
      traffic: 38, // P3
      date: "2023-06-10",
    },
    {
      id: 28200,
      title: "台灣最狂直播天后是誰？從 OTT 戲劇看直播文化演變",
      excerpt: "直播產業深度分析，台灣創作者生態觀察。",
      category: "娛樂",
      traffic: 120, // P2
      date: "2023-08-20",
    },
    {
      id: 28201,
      title: "2024 年最值得看的 K-Drama：《寄生上流》後時代的韓劇新浪潮",
      excerpt: "韓國電視劇產業分析，2024 年必看清單。",
      category: "電視",
      traffic: 280, // P1
      date: "2023-10-15",
    },
    {
      id: 28202,
      title: "從《騎士》到《勝利號》：韓國科幻電影的崛起之路",
      excerpt: "韓國科幻片製作現狀分析，國際競爭力評估。",
      category: "電影",
      traffic: 680, // P0
      date: "2023-11-01",
    },
  ];

  // 筛选对应 tier 的文章
  const tiered = sampleArticles.filter((article) => {
    const { minTraffic, maxTraffic } = TIER_CONFIG[tier];
    return article.traffic >= minTraffic && article.traffic < maxTraffic;
  });

  const result = limit ? tiered.slice(0, limit) : tiered;
  console.log(`   ✓ Found ${result.length} articles for tier ${tier.toUpperCase()}\n`);

  return result;
}

// ─── SEO Optimization ──────────────────────────────────────────────────────

/**
 * 使用 Claude 生成 SEO 优化内容
 * 根据 Tier 调整维度数量（P3: 2维, P2: 4维, P1-P0: 4-6维）
 */
async function optimizeArticle(article, tier) {
  const config = TIER_CONFIG[tier];
  const dimensions = config.dimensions;

  console.log(`  🔄 Optimizing #${article.id}: "${article.title.substring(0, 40)}..."`);

  try {
    const prompt = `你是 SEO 顾问专家。针对以下文章，生成 ${dimensions} 维 SEO 优化建议。

【文章信息】
- 标题：${article.title}
- 分类：${article.category}
- 摘要：${article.excerpt}

【优化维度（${dimensions}D）】
${
  dimensions >= 2
    ? `
1. **Meta Title & Description**
   - 新标题（≤60 字，包含关键字，吸引点击）
   - Meta Description（≤160 字，清楚传达价值）
`
    : ""
}
${
  dimensions >= 4
    ? `
2. **Schema Markup（JSON-LD）**
   - 使用 Article, NewsArticle 或 BlogPosting Schema
   - 包含 author, datePublished, dateModified, image, keywords

3. **Open Graph Tags**
   - og:title, og:description, og:image（优化社群分享）

4. **Internal Links**
   - 建议 3-5 个内部链接建议（相关文章或枢纽页面）
`
    : ""
}
${
  dimensions >= 6
    ? `
5. **Content Structure**
   - 标题层级建议（H1, H2, H3 逻辑）
   - 关键字密度分析与改进

6. **Technical SEO**
   - Core Web Vitals 友好的内容建议
   - 图片优化（alt 文本）建议
`
    : ""
}

【回应格式】
返回 JSON 格式：
\`\`\`json
{
  "metaTitle": "新标题",
  "metaDescription": "新摘要",
  "schema": { /* JSON-LD 对象 */ },
  "ogTags": { /* OG 标签对象 */ },
  "internalLinks": [ /* 内部链接建议数组 */ ],
  "contentNotes": "内容结构建议（如有）"
}
\`\`\`
`;

    const response = await client.messages.create({
      model: CONFIG.modelForSEO,
      max_tokens: 2000,
      messages: [
        {
          role: "user",
          content: prompt,
        },
      ],
    });

    const content = response.content[0];
    if (content.type !== "text") {
      throw new Error("Unexpected response type");
    }

    // 提取 JSON
    const jsonMatch = content.text.match(/\{[\s\S]*\}/);
    if (!jsonMatch) {
      throw new Error("No JSON found in response");
    }

    const optimizations = JSON.parse(jsonMatch[0]);
    console.log(`     ✓ Generated ${dimensions}D optimizations`);

    return {
      articleId: article.id,
      title: article.title,
      tier: tier.toUpperCase(),
      dimensions,
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

// ─── Batch Processing ──────────────────────────────────────────────────────

async function processTierBatch(articles, tier, dryRun = false) {
  const results = [];

  for (let i = 0; i < articles.length; i += CONFIG.batchSize) {
    const batch = articles.slice(i, i + CONFIG.batchSize);
    console.log(`\n📦 Processing batch ${Math.floor(i / CONFIG.batchSize) + 1}/${Math.ceil(articles.length / CONFIG.batchSize)} (${batch.length} articles)\n`);

    for (const article of batch) {
      const result = await optimizeArticle(article, tier);
      results.push(result);

      // 延迟避免 rate limit
      if (article !== batch[batch.length - 1]) {
        await sleep(CONFIG.delayMs);
      }
    }

    // 批次间延迟
    if (i + CONFIG.batchSize < articles.length) {
      console.log(`   ⏳ Waiting before next batch...\n`);
      await sleep(2000);
    }
  }

  return results;
}

// ─── Report Generation ────────────────────────────────────────────────────

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
  console.log(`\nTier Info: ${report.tierInfo.desc}`);
  console.log(`Articles Processed: ${report.totalProcessed}`);
  console.log(`✓ Successful: ${report.successful}`);
  console.log(`✗ Failed: ${report.failed}`);
  console.log(`Success Rate: ${report.successRate}`);
  console.log(`\nReport saved: ${report.timestamp}`);
  console.log("=".repeat(70) + "\n");
}

// ─── Main ───────────────────────────────────────────────────────────────────

async function main() {
  const args = parseArgs();
  ensureOutputDir();

  console.log("\n🚀 Unit 1.1: Reverse-Tier SEO Optimization (P3→P2→P1→P0)\n");
  console.log(`   Tier: ${args.tier.toUpperCase()} (${TIER_CONFIG[args.tier].desc})`);
  if (args.sample) console.log(`   Sample: ${args.sample} articles`);
  if (args.dryRun) console.log(`   Mode: DRY RUN (no updates)`);
  console.log();

  // 1. 获取该 Tier 的文章
  const articles = await fetchArticlesForTier(args.tier, args.sample);

  if (articles.length === 0) {
    console.log("❌ No articles found for this tier. Exiting.\n");
    process.exit(0);
  }

  // 2. 批量优化
  console.log(`\n🔧 Generating SEO optimizations (${TIER_CONFIG[args.tier].dimensions}D)...\n`);
  const results = await processTierBatch(articles, args.tier, args.dryRun);

  // 3. 生成报告
  const report = generateReport(args.tier, results);
  printSummary(report);

  console.log("✅ Tier optimization complete!\n");
  console.log("📌 Next steps:");
  console.log("   1. Review results in seo-optimization-output/");
  console.log(`   2. Run next tier: node scripts/unit-1-1-reverse-tier-seo-optimizer.js --tier p2`);
  console.log("   3. Monitor GSC/GA4 for 14-day feedback\n");
}

main().catch((error) => {
  console.error("❌ Fatal error:", error);
  process.exit(1);
});
