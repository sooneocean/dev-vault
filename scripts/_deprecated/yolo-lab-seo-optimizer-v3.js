#!/usr/bin/env node

/**
 * YOLO LAB SEO Optimizer v3 (企業級)
 *
 * 分階段優化 898 篇文章，避免算力浪費
 * 支持優先級分類、Schema 生成、OG Tags、內部連結
 *
 * 運行：
 *   export ANTHROPIC_API_KEY="sk-ant-..."
 *   node scripts/yolo-lab-seo-optimizer-v3.js --phase 2 --tier 1 --dry-run
 *
 * 參數：
 *   --phase <1-5>     執行階段 (default: 2)
 *   --tier <1-4>      優先級層級 (default: 1)
 *   --dry-run         模擬運行，不實際更新
 *   --sample <n>      抽樣 n 篇文章（用於測試）
 *   --resume <date>   從指定日期恢復（用於斷點續傳）
 */

import Anthropic from "@anthropic-ai/sdk";
import fs from "fs";
import path from "path";

const client = new Anthropic();

// ─── Config ─────────────────────────────────────────────────────────────────

const CONFIG = {
  siteId: 133512998,
  domain: "yololab.net",
  batchSize: 10,
  delayMs: 1000,
  maxRetries: 3,
  outputDir: "./seo-optimization-output",
};

// ─── Helper Functions ───────────────────────────────────────────────────────

function parseArgs() {
  const args = process.argv.slice(2);
  const parsed = {
    phase: 2,
    tier: 1,
    dryRun: false,
    sample: null,
    resume: null,
  };

  for (let i = 0; i < args.length; i += 2) {
    const key = args[i].replace(/^--/, "");
    const value = args[i + 1];

    if (key === "phase") parsed.phase = parseInt(value);
    if (key === "tier") parsed.tier = parseInt(value);
    if (key === "dry-run") parsed.dryRun = true;
    if (key === "sample") parsed.sample = parseInt(value);
    if (key === "resume") parsed.resume = value;
  }

  return parsed;
}

function ensureOutputDir() {
  if (!fs.existsSync(CONFIG.outputDir)) {
    fs.mkdirSync(CONFIG.outputDir, { recursive: true });
  }
}

function loadOrCreateState(phase, tier) {
  const stateFile = path.join(
    CONFIG.outputDir,
    `state_phase${phase}_tier${tier}.json`
  );
  if (fs.existsSync(stateFile)) {
    return JSON.parse(fs.readFileSync(stateFile, "utf-8"));
  }
  return {
    phase,
    tier,
    startTime: new Date().toISOString(),
    processed: [],
    failed: [],
    skipped: [],
  };
}

function saveState(phase, tier, state) {
  const stateFile = path.join(
    CONFIG.outputDir,
    `state_phase${phase}_tier${tier}.json`
  );
  fs.writeFileSync(stateFile, JSON.stringify(state, null, 2));
}

async function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

// ─── Claude API Functions ───────────────────────────────────────────────────

/**
 * 生成優化標題和 Meta Description
 */
async function generateMetaOptimization(title, excerpt, category) {
  const prompt = `你是中文 SEO 專家。

文章資訊：
- 原標題：${title}
- 摘要：${excerpt || "（無摘要）"}
- 分類：${category}

任務：生成改進的標題和 meta description

要求：
1. 標題：45-60 字，包含主關鍵字，吸引點擊，保留原意
2. Meta Description：120-160 字，自然包含長尾關鍵字，清楚說明價值

回應格式（JSON）：
{
  "optimizedTitle": "...",
  "metaDescription": "...",
  "keywords": ["關鍵字1", "關鍵字2", "關鍵字3"],
  "rationale": "簡短說明"
}`;

  const message = await client.messages.create({
    model: "claude-opus-4-6",
    max_tokens: 500,
    messages: [
      {
        role: "user",
        content: prompt,
      },
    ],
  });

  const content = message.content[0];
  if (content.type !== "text") {
    throw new Error("Unexpected response type from Claude");
  }

  try {
    const jsonMatch = content.text.match(/\{[\s\S]*\}/);
    if (!jsonMatch) {
      throw new Error("No JSON found in response");
    }
    return JSON.parse(jsonMatch[0]);
  } catch (error) {
    console.error("Failed to parse Claude response:", content.text);
    throw error;
  }
}

/**
 * 生成 Schema Markup（Article + Person/VideoObject）
 */
async function generateSchemaMarkup(title, excerpt, author, publishDate, articleContent, contentType) {
  const prompt = `你是 Schema.org 專家。

文章資訊：
- 標題：${title}
- 作者：${author || "YOLO LAB"}
- 發佈日期：${publishDate}
- 內容類型：${contentType}
- 摘要：${excerpt}

任務：生成適合的 JSON-LD Schema Markup

根據內容類型生成：
1. Article Schema（必須）
2. Person Schema（若涉及人物分析）
3. VideoObject Schema（若涉及影片評論）

要求：完整、有效的 JSON-LD 格式，包含所有必需字段。

回應格式（JSON）：
{
  "schemas": [
    { "@context": "https://schema.org", "@type": "Article", ... }
  ],
  "recommendation": "說明哪個 schema 最重要"
}`;

  const message = await client.messages.create({
    model: "claude-opus-4-6",
    max_tokens: 1500,
    messages: [
      {
        role: "user",
        content: prompt,
      },
    ],
  });

  const responseContent = message.content[0];
  if (responseContent.type !== "text") {
    throw new Error("Unexpected response type from Claude");
  }

  try {
    const jsonMatch = responseContent.text.match(/\{[\s\S]*\}/);
    if (!jsonMatch) {
      throw new Error("No JSON found in response");
    }
    return JSON.parse(jsonMatch[0]);
  } catch (error) {
    console.error("Failed to parse Claude response:", responseContent.text);
    throw error;
  }
}

/**
 * 生成 OG Tags
 */
async function generateOGTags(title, metaDescription, contentType) {
  const prompt = `你是社群媒體內容優化專家。

文章資訊：
- 標題：${title}
- Meta Description：${metaDescription}
- 類型：${contentType}

任務：生成最佳的 Open Graph tags

要求：
1. og:title：最多 60 字，吸引點擊
2. og:description：最多 160 字，清楚傳達價值
3. og:image：圖片 URL 或建議尺寸

回應格式（JSON）：
{
  "og:title": "...",
  "og:description": "...",
  "og:image_recommendation": "URL 或 尺寸建議（1200x630）",
  "twitter:card": "summary_large_image",
  "twitter:title": "...",
  "twitter:description": "..."
}`;

  const message = await client.messages.create({
    model: "claude-opus-4-6",
    max_tokens: 500,
    messages: [
      {
        role: "user",
        content: prompt,
      },
    ],
  });

  const content = message.content[0];
  if (content.type !== "text") {
    throw new Error("Unexpected response type from Claude");
  }

  try {
    const jsonMatch = content.text.match(/\{[\s\S]*\}/);
    if (!jsonMatch) {
      throw new Error("No JSON found in response");
    }
    return JSON.parse(jsonMatch[0]);
  } catch (error) {
    console.error("Failed to parse Claude response:", content.text);
    throw error;
  }
}

/**
 * 生成內部連結建議
 */
async function generateInternalLinkSuggestions(title, category, keywords) {
  const prompt = `你是內部連結策略專家。

文章資訊：
- 標題：${title}
- 分類：${category}
- 關鍵字：${keywords.join(", ")}

任務：建議 3-5 個同網站的相關文章位置（不知道具體文章，只基於語義）

要求：
1. 每個建議包含推薦的錨文本和連結位置描述
2. 只提供語義和位置建議，不指定具體 URL

回應格式（JSON）：
{
  "internalLinkSuggestions": [
    {
      "anchorText": "...",
      "location": "段落 X 的結尾",
      "rationale": "為什麼這個連結有幫助"
    }
  ]
}`;

  const message = await client.messages.create({
    model: "claude-opus-4-6",
    max_tokens: 800,
    messages: [
      {
        role: "user",
        content: prompt,
      },
    ],
  });

  const content = message.content[0];
  if (content.type !== "text") {
    throw new Error("Unexpected response type from Claude");
  }

  try {
    const jsonMatch = content.text.match(/\{[\s\S]*\}/);
    if (!jsonMatch) {
      throw new Error("No JSON found in response");
    }
    return JSON.parse(jsonMatch[0]);
  } catch (error) {
    console.error("Failed to parse Claude response:", content.text);
    throw error;
  }
}

// ─── Main Orchestration ─────────────────────────────────────────────────────

async function processArticle(article, options) {
  const { dryRun } = options;

  const results = {
    id: article.id,
    title: article.title,
    status: "processing",
    optimizations: {},
    error: null,
  };

  try {
    console.log(`[${article.id}] 正在處理 "${article.title.substring(0, 50)}..."`);

    // 1. Meta Optimization
    console.log(`  └─ 生成 Meta 優化...`);
    const metaOpt = await generateMetaOptimization(
      article.title,
      article.excerpt,
      article.category
    );
    results.optimizations.meta = metaOpt;

    // 2. Schema Markup
    console.log(`  └─ 生成 Schema Markup...`);
    const schema = await generateSchemaMarkup(
      article.title,
      article.excerpt,
      article.author,
      article.date,
      article.content,
      article.category
    );
    results.optimizations.schema = schema;

    // 3. OG Tags
    console.log(`  └─ 生成 OG Tags...`);
    const ogTags = await generateOGTags(
      metaOpt.optimizedTitle,
      metaOpt.metaDescription,
      article.category
    );
    results.optimizations.ogTags = ogTags;

    // 4. Internal Links
    console.log(`  └─ 生成內部連結建議...`);
    const internalLinks = await generateInternalLinkSuggestions(
      article.title,
      article.category,
      metaOpt.keywords
    );
    results.optimizations.internalLinks = internalLinks;

    results.status = "success";
    console.log(`✅ 文章 #${article.id} 優化完成\n`);
  } catch (error) {
    results.status = "failed";
    results.error = error.message;
    console.error(`❌ 文章 #${article.id} 失敗: ${error.message}\n`);
  }

  return results;
}

async function main() {
  const args = parseArgs();
  ensureOutputDir();

  console.log("\n🚀 YOLO LAB SEO Optimizer v3 (企業級分階段優化)\n");
  console.log(`📊 參數：Phase ${args.phase}, Tier ${args.tier}`);
  if (args.dryRun) console.log("   模式：DRY RUN（不實際更新）");
  if (args.sample) console.log(`   樣本：${args.sample} 篇（測試用）\n`);

  // 檢查 API key
  if (!process.env.ANTHROPIC_API_KEY) {
    console.error("❌ ANTHROPIC_API_KEY 未設定");
    console.log("運行：export ANTHROPIC_API_KEY='sk-ant-...'\n");
    process.exit(1);
  }

  // 模擬文章數據（實際應從 WordPress.com MCP 讀取）
  const sampleArticles = [
    {
      id: 27155,
      title:
        "2026 電影院推薦 | 全台影城殘酷評測：別再只去威秀！這 5 間才是真正的觀影神壇",
      excerpt:
        "深度評測全台 5 家頂級影城，從放映技術到舒適度全面比較。選對影城才能看到電影的靈魂。",
      author: "YOLO LAB編輯",
      date: "2025-06-15",
      category: "電影",
      content: "...",
    },
    {
      id: 28183,
      title:
        "湯米巴斯托 Tommy Bastow 深度分析：《幕府將軍》的神父，現在更是 NHK 欽點的「日本通」",
      excerpt:
        "從演員到日本文化專家，Tommy Bastow 的職涯轉變如何發生？深度專訪和背景分析。",
      author: "YOLO LAB編輯",
      date: "2025-06-10",
      category: "人物",
      content: "...",
    },
  ];

  // 抽樣或完整列表
  const articlesToProcess = args.sample
    ? sampleArticles.slice(0, args.sample)
    : sampleArticles;

  const state = loadOrCreateState(args.phase, args.tier);
  const results = {
    phase: args.phase,
    tier: args.tier,
    dryRun: args.dryRun,
    processedCount: 0,
    successCount: 0,
    failedCount: 0,
    articles: [],
  };

  // 處理每篇文章
  for (const article of articlesToProcess) {
    // 速率限制
    await sleep(CONFIG.delayMs);

    const optimizations = await processArticle(article, args);
    results.articles.push(optimizations);

    if (optimizations.status === "success") {
      results.successCount++;
      state.processed.push(article.id);
    } else {
      results.failedCount++;
      state.failed.push({ id: article.id, error: optimizations.error });
    }
    results.processedCount++;
  }

  // 保存狀態和結果
  saveState(args.phase, args.tier, state);
  const reportPath = path.join(
    CONFIG.outputDir,
    `report_phase${args.phase}_tier${args.tier}.json`
  );
  fs.writeFileSync(reportPath, JSON.stringify(results, null, 2));

  // 輸出摘要
  console.log("=".repeat(80));
  console.log("📈 優化完成報告");
  console.log("=".repeat(80) + "\n");
  console.log(`✅ 成功：${results.successCount} 篇`);
  console.log(`❌ 失敗：${results.failedCount} 篇`);
  console.log(`📊 總計：${results.processedCount} 篇\n`);
  console.log(`💾 詳細報告：${reportPath}\n`);
  console.log(
    "📋 下一步：審核優化方案，使用 WordPress.com API 批量應用更新"
  );
}

main().catch(console.error);
