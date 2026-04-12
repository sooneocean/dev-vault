#!/usr/bin/env node

/**
 * Phase 4 Complete SEO Batch Generator - yololab.net
 *
 * 為全部 2,725 篇文章生成：
 * 1. Meta 優化（標題 + Meta Description）
 * 2. JSON-LD Schema Markup
 * 3. Open Graph Tags
 *
 * 執行策略：
 * - 批大小：20 篇/次
 * - 延遲：2 秒/批
 * - 總時間估計：9-10 小時（三個任務可並行）
 *
 * 使用方式：
 * export WPCOM_TOKEN=your_token
 * export ANTHROPIC_API_KEY=your_key
 * node phase4-complete-seo-batch-generator.js [--task meta|schema|og|all] [--sample N] [--demo]
 */

import Anthropic from "@anthropic-ai/sdk";
import fetch from "node-fetch";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const client = new Anthropic();

// ─── Configuration ────────────────────────────────────────────────────────

const BLOG_ID = 133512998;
const BATCH_SIZE = 20;
const DELAY_MS = 2000;
const OUTPUT_DIR = path.join(__dirname, "../seo-optimization-output");
const STATE_DIR = path.join(OUTPUT_DIR, "phase4-state");

// Parse arguments
const args = process.argv.slice(2);
const taskArg = args.find(a => a.startsWith("--task="))?.split("=")[1] || "all";
const sampleSize = parseInt(args.find(a => a.startsWith("--sample="))?.split("=")[1] || "0");
const demoMode = args.includes("--demo");

const tasks = taskArg === "all"
  ? ["meta", "schema", "og"]
  : [taskArg];

// ─── Utilities ────────────────────────────────────────────────────────────

function ensureDirectories() {
  [OUTPUT_DIR, STATE_DIR].forEach((dir) => {
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
  });
}

function log(msg, level = "info") {
  const timestamp = new Date().toISOString().split("T")[1].slice(0, 8);
  const prefix = {
    info: "ℹ️",
    success: "✓",
    error: "❌",
    warning: "⚠️",
  }[level];
  console.log(`[${timestamp}] ${prefix} ${msg}`);
}

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function getWpComToken() {
  const token = process.env.WPCOM_TOKEN;
  if (!token) {
    throw new Error(
      "❌ 缺少 WPCOM_TOKEN 環境變數\n" +
      "   請運行: export WPCOM_TOKEN=your_token"
    );
  }
  return token;
}

// ─── WordPress.com API ────────────────────────────────────────────────────

async function fetchAllPosts(token) {
  const allPosts = [];
  let page = 1;
  let hasMore = true;

  while (hasMore) {
    try {
      const url = `https://public-api.wordpress.com/rest/v1.1/sites/${BLOG_ID}/posts?fields=ID,title,excerpt,slug,date,modified,tags,categories,featured_image&per_page=100&page=${page}`;

      const response = await fetch(url, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!response.ok) {
        throw new Error(`API 錯誤: ${response.status}`);
      }

      const data = await response.json();

      if (!data.posts || data.posts.length === 0) {
        hasMore = false;
      } else {
        allPosts.push(...data.posts);
        page++;
        log(`已獲取 ${allPosts.length} 篇文章`);
        await sleep(500); // 避免速率限制
      }
    } catch (error) {
      log(`獲取文章列表失敗: ${error.message}`, "error");
      hasMore = false;
    }
  }

  return allPosts;
}

// ─── Claude API - Meta Optimization ────────────────────────────────────────

async function generateMetaOptimization(article) {
  const prompt = `你是中文 SEO 專家。

文章資訊：
- 原標題：${article.title}
- 現有標籤：${article.tags?.map(t => t.name).join(", ") || "無"}
- 摘要：${article.excerpt?.slice(0, 200) || "無"}
- 發布日期：${article.date}

任務：生成改進的標題和 Meta Description

要求：
1. SEO 標題：45-60 字，包含主關鍵字，吸引點擊，保留原意
2. Meta Description：120-160 字，自然包含長尾關鍵字，清楚說明價值
3. 主要關鍵字：3-5 個

回應格式（純 JSON，無其他內容）：
{
  "optimizedTitle": "...",
  "metaDescription": "...",
  "primaryKeywords": ["kw1", "kw2", "kw3"],
  "rationale": "簡短說明"
}`;

  const response = await client.messages.create({
    model: "claude-3-5-sonnet-20241022",
    max_tokens: 500,
    messages: [{
      role: "user",
      content: prompt,
    }],
  });

  const content = response.content[0].type === "text" ? response.content[0].text : "";

  try {
    // 提取 JSON
    const jsonMatch = content.match(/\{[\s\S]*\}/);
    if (!jsonMatch) throw new Error("無有效 JSON");

    return JSON.parse(jsonMatch[0]);
  } catch (error) {
    log(`Meta 生成失敗 (ID ${article.ID}): ${error.message}`, "warning");
    return {
      optimizedTitle: article.title,
      metaDescription: article.excerpt?.slice(0, 160) || "",
      primaryKeywords: [],
      rationale: "生成失敗，使用原始數據",
    };
  }
}

// ─── Claude API - Schema Markup ────────────────────────────────────────────

async function generateSchemaMarkup(article) {
  const prompt = `你是 SEO Schema Markup 專家。

文章資訊：
- 標題：${article.title}
- 標籤：${article.tags?.map(t => t.name).join(", ") || "無"}
- 發布日期：${article.date}
- 修改日期：${article.modified}
- URL：https://yololab.net/?p=${article.ID}

任務：生成適合的 Schema.org JSON-LD 標記

規則：
1. 所有文章都需要 Article Schema（基礎）
2. 如果涉及電影/演唱會，加入 Event/VideoObject Schema
3. 使用以下欄位：@context, @type, headline, description, datePublished, dateModified, author, publisher, image, url
4. 返回單個 Schema 對象（如有多個類型，使用 @type 陣列）

回應格式（純 JSON，無其他內容）：
{
  "@context": "https://schema.org",
  "@type": "Article",
  ...
}`;

  const response = await client.messages.create({
    model: "claude-3-5-sonnet-20241022",
    max_tokens: 1000,
    messages: [{
      role: "user",
      content: prompt,
    }],
  });

  const content = response.content[0].type === "text" ? response.content[0].text : "";

  try {
    const jsonMatch = content.match(/\{[\s\S]*\}/);
    if (!jsonMatch) throw new Error("無有效 JSON");

    return JSON.parse(jsonMatch[0]);
  } catch (error) {
    log(`Schema 生成失敗 (ID ${article.ID}): ${error.message}`, "warning");
    return {
      "@context": "https://schema.org",
      "@type": "Article",
      headline: article.title,
      description: article.excerpt?.slice(0, 200) || "",
      datePublished: article.date,
      dateModified: article.modified,
      author: { "@type": "Person", "name": "YOLO LAB" },
      publisher: {
        "@type": "Organization",
        "name": "YOLO LAB",
      },
    };
  }
}

// ─── Claude API - OG Tags ──────────────────────────────────────────────────

async function generateOGTags(article) {
  const prompt = `你是社群媒體優化專家。

文章資訊：
- 標題：${article.title}
- 摘要：${article.excerpt?.slice(0, 200) || "無"}
- URL：https://yololab.net/?p=${article.ID}
- 標籤：${article.tags?.map(t => t.name).join(", ") || "無"}

任務：生成優化的 Open Graph 和 Twitter Card Meta 標籤

要求：
1. og:title：比 SEO 標題更簡潔（50-55 字），吸引點擊
2. og:description：100-120 字，突出價值和故事性
3. twitter:title：最多 70 字
4. twitter:description：最多 200 字

回應格式（純 JSON，無其他內容）：
{
  "og:title": "...",
  "og:description": "...",
  "og:url": "https://yololab.net/?p=${article.ID}",
  "og:type": "article",
  "twitter:card": "summary_large_image",
  "twitter:title": "...",
  "twitter:description": "..."
}`;

  const response = await client.messages.create({
    model: "claude-3-5-sonnet-20241022",
    max_tokens: 600,
    messages: [{
      role: "user",
      content: prompt,
    }],
  });

  const content = response.content[0].type === "text" ? response.content[0].text : "";

  try {
    const jsonMatch = content.match(/\{[\s\S]*\}/);
    if (!jsonMatch) throw new Error("無有效 JSON");

    return JSON.parse(jsonMatch[0]);
  } catch (error) {
    log(`OG Tags 生成失敗 (ID ${article.ID}): ${error.message}`, "warning");
    return {
      "og:title": article.title,
      "og:description": article.excerpt?.slice(0, 120) || "",
      "og:url": `https://yololab.net/?p=${article.ID}`,
      "og:type": "article",
      "twitter:card": "summary_large_image",
      "twitter:title": article.title,
      "twitter:description": article.excerpt?.slice(0, 200) || "",
    };
  }
}

// ─── Batch Processing ─────────────────────────────────────────────────────

async function processBatch(articles, taskType) {
  const results = [];

  for (let i = 0; i < articles.length; i++) {
    const article = articles[i];

    try {
      let result;

      switch (taskType) {
        case "meta":
          result = await generateMetaOptimization(article);
          break;
        case "schema":
          result = await generateSchemaMarkup(article);
          break;
        case "og":
          result = await generateOGTags(article);
          break;
      }

      results.push({
        id: article.ID,
        title: article.title,
        [taskType]: result,
        success: true,
      });

      log(`[${taskType.toUpperCase()}] 完成 ${i + 1}/${articles.length} (ID: ${article.ID})`);

      // 避免速率限制
      if (i < articles.length - 1) {
        await sleep(DELAY_MS);
      }
    } catch (error) {
      log(`[${taskType.toUpperCase()}] 失敗 (ID ${article.ID}): ${error.message}`, "error");
      results.push({
        id: article.ID,
        title: article.title,
        success: false,
        error: error.message,
      });
    }
  }

  return results;
}

// ─── Main Execution ───────────────────────────────────────────────────────

async function main() {
  ensureDirectories();

  log(`========================================`);
  log(`Phase 4 Complete SEO Batch Generator`);
  log(`========================================`);
  log(`任務: ${tasks.join(", ")}`);
  log(`演示模式: ${demoMode ? "是" : "否"}`);

  try {
    const token = await getWpComToken();

    log(`正在獲取文章列表...`);
    let posts = await fetchAllPosts(token);

    if (sampleSize > 0) {
      posts = posts.slice(0, sampleSize);
      log(`樣本模式：${sampleSize} 篇文章`);
    } else {
      log(`總共 ${posts.length} 篇文章`);
    }

    if (demoMode) {
      posts = posts.slice(0, 2);
      log(`演示模式：2 篇文章`);
    }

    // 依任務執行
    for (const task of tasks) {
      log(`\n════ 開始 ${task.toUpperCase()} 優化 ════`);

      const taskResults = {
        task,
        timestamp: new Date().toISOString(),
        totalArticles: posts.length,
        articles: [],
        stats: {
          success: 0,
          failed: 0,
        },
      };

      // 分批處理
      for (let i = 0; i < posts.length; i += BATCH_SIZE) {
        const batchNum = Math.floor(i / BATCH_SIZE) + 1;
        const batch = posts.slice(i, i + BATCH_SIZE);

        log(`\n[${task.toUpperCase()}] 批次 ${batchNum}/${Math.ceil(posts.length / BATCH_SIZE)}`);

        const batchResults = await processBatch(batch, task);

        batchResults.forEach(r => {
          taskResults.articles.push(r);
          if (r.success) {
            taskResults.stats.success++;
          } else {
            taskResults.stats.failed++;
          }
        });

        // 批次間延遲
        if (i + BATCH_SIZE < posts.length) {
          log(`批次間延遲 3 秒...`);
          await sleep(3000);
        }
      }

      // 保存結果
      const outputFile = path.join(
        OUTPUT_DIR,
        `${task}_optimization_results.json`
      );
      fs.writeFileSync(outputFile, JSON.stringify(taskResults, null, 2));

      log(`\n✓ [${task.toUpperCase()}] 完成`);
      log(`  成功: ${taskResults.stats.success}`);
      log(`  失敗: ${taskResults.stats.failed}`);
      log(`  輸出: ${outputFile}`);
    }

    // 生成總結報告
    generateSummaryReport(posts.length, tasks);

    log(`\n========================================`);
    log(`✓ 全部任務完成！`, "success");
    log(`========================================`);

  } catch (error) {
    log(`致命錯誤: ${error.message}`, "error");
    process.exit(1);
  }
}

function generateSummaryReport(totalArticles, completedTasks) {
  const report = {
    phase: 4,
    timestamp: new Date().toISOString(),
    site: {
      id: BLOG_ID,
      name: "yololab.net",
    },
    execution: {
      totalArticles,
      tasksCompleted: completedTasks,
      batchSize: BATCH_SIZE,
      delayMs: DELAY_MS,
    },
    outputs: completedTasks.map(task => ({
      task,
      file: `${task}_optimization_results.json`,
    })),
    nextSteps: [
      "驗證 JSON 結構完整性",
      "抽查 10 篇文章確保質量",
      "生成質量驗證報告",
      "準備 WordPress 應用腳本",
    ],
  };

  const reportFile = path.join(OUTPUT_DIR, "PHASE4_EXECUTION_SUMMARY.json");
  fs.writeFileSync(reportFile, JSON.stringify(report, null, 2));

  log(`\n執行報告已保存: ${reportFile}`);
}

main().catch(error => {
  log(`未捕捉的錯誤: ${error.message}`, "error");
  process.exit(1);
});
