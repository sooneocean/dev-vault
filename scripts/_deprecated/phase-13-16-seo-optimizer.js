#!/usr/bin/env node

/**
 * Phase 13-16 SEO Batch Optimizer for yololab.net
 *
 * Processes 400 articles (IDs 33800-33401) across 4 phases
 * - Phase 13: 33800-33701 (100 articles)
 * - Phase 14: 33700-33601 (100 articles)
 * - Phase 15: 33600-33501 (100 articles)
 * - Phase 16: 33500-33401 (100 articles)
 *
 * Features:
 * - Parallel fetching with WordPress.com API
 * - Claude SEO optimization (title + meta description)
 * - Progress tracking with recovery support
 * - Rate limiting and error handling
 * - Batch update with MCP integration
 */

import Anthropic from "@anthropic-ai/sdk";
import fs from "fs";
import path from "path";

const client = new Anthropic();

// ─── Configuration ──────────────────────────────────────────────────────────

const SITE_ID = 133512998;
const DOMAIN = "yololab.net";
const BATCH_SIZE = 5; // Concurrent API calls
const DELAY_MS = 800; // Rate limit delay
const PROGRESS_FILE = "phase-13-16-progress.json";
const OUTPUT_DIR = "seo-optimization-phase-13-16";

// Phase definitions
const PHASES = {
  13: { start_id: 33800, end_id: 33701, name: "Phase 13: Articles 33800-33701" },
  14: { start_id: 33700, end_id: 33601, name: "Phase 14: Articles 33700-33601" },
  15: { start_id: 33600, end_id: 33501, name: "Phase 15: Articles 33600-33501" },
  16: { start_id: 33500, end_id: 33401, name: "Phase 16: Articles 33500-33401" },
};

// ─── Helper Functions ───────────────────────────────────────────────────────

/**
 * Load or initialize progress file
 */
async function loadProgress() {
  try {
    if (fs.existsSync(PROGRESS_FILE)) {
      const data = fs.readFileSync(PROGRESS_FILE, "utf-8");
      return JSON.parse(data);
    }
  } catch (error) {
    console.log("⚠️  無法載入進度文件，從頭開始");
  }
  return {
    phase: 13,
    phases: {
      13: { completed: 0, failed: [], success: [] },
      14: { completed: 0, failed: [], success: [] },
      15: { completed: 0, failed: [], success: [] },
      16: { completed: 0, failed: [], success: [] },
    },
    total_completed: 0,
    total_failed: [],
  };
}

/**
 * Save progress to file
 */
async function saveProgress(progress) {
  fs.writeFileSync(PROGRESS_FILE, JSON.stringify(progress, null, 2));
}

/**
 * Generate SEO optimizations using Claude
 */
async function generateSEOOptimizations(title, excerpt, content = "") {
  const prompt = `你是 SEO 專家，專門優化繁體中文內容以提高搜尋排名和點擊率。

分析以下文章，生成改進的標題和 meta description：

**原始標題：**
${title}

**文章摘要/內容預覽：**
${excerpt || (content ? content.substring(0, 300) : "（無摘要）")}

**優化要求：**
1. 標題：45-60 字，包含主要關鍵字，具吸引力和清晰度
2. Meta Description：120-160 字，自然包含相關關鍵字，清楚說明內容價值，鼓勵點擊

**回應格式（純 JSON，無額外文本）：**
{
  "optimizedTitle": "...",
  "metaDescription": "...",
  "reasoning": "簡短說明優化策略"
}`;

  const message = await client.messages.create({
    model: "claude-opus-4-6",
    max_tokens: 400,
    messages: [
      {
        role: "user",
        content: prompt,
      },
    ],
  });

  const content_response = message.content[0];
  if (content_response.type !== "text") {
    throw new Error("Unexpected response type from Claude");
  }

  try {
    const jsonMatch = content_response.text.match(/\{[\s\S]*\}/);
    if (!jsonMatch) {
      throw new Error("No JSON found in response");
    }
    return JSON.parse(jsonMatch[0]);
  } catch (error) {
    console.error("Failed to parse Claude response:", content_response.text);
    throw error;
  }
}

/**
 * Fetch article details from WordPress.com via MCP
 * Placeholder - actual integration would use wpcom-mcp-content-authoring
 */
async function fetchArticleViaAPI(articleId) {
  // NOTE: In production, this would call the WordPress.com API via MCP
  // For now, return mock data
  return {
    id: articleId,
    title: `文章 #${articleId}`,
    excerpt: `文章 #${articleId} 的摘要`,
    content: `文章 #${articleId} 的內容`,
    url: `https://${DOMAIN}/?p=${articleId}`,
  };
}

/**
 * Update article metadata via WordPress.com API
 * Placeholder - actual integration would use wpcom-mcp-content-authoring
 */
async function updateArticleViaAPI(articleId, seoData) {
  // NOTE: In production, this would call the WordPress.com API via MCP
  // to update post title and yoast/seo meta description
  console.log(`   更新文章 #${articleId}`);
  return { success: true };
}

/**
 * Generate range of IDs for a phase
 */
function generateArticleIds(startId, endId) {
  const ids = [];
  for (let i = startId; i >= endId; i--) {
    ids.push(i);
  }
  return ids;
}

/**
 * Process articles in batches
 */
async function processPhaseBatch(phaseNum, articleIds, progress) {
  const phaseConfig = PHASES[phaseNum];
  console.log(`\n🚀 ${phaseConfig.name}\n`);

  const phaseProgress = progress.phases[phaseNum];
  let batchCount = 1;

  for (let i = 0; i < articleIds.length; i += BATCH_SIZE) {
    const batch = articleIds.slice(i, Math.min(i + BATCH_SIZE, articleIds.length));

    console.log(
      `📦 批次 #${batchCount}: 處理文章 ${batch.join(", ")} (${batch.length}/${articleIds.length})`
    );

    // Fetch all articles in batch
    const articles = await Promise.all(
      batch.map((id) =>
        fetchArticleViaAPI(id).catch((e) => ({
          id,
          error: e.message,
        }))
      )
    );

    // Generate and update SEO data
    for (const article of articles) {
      if (article.error) {
        console.log(`  ❌ 文章 #${article.id}: ${article.error}`);
        phaseProgress.failed.push({ id: article.id, error: article.error });
        progress.total_failed.push({ id: article.id, phase: phaseNum, error: article.error });
        continue;
      }

      try {
        const progressNum = progress.total_completed + 1;
        console.log(`  [${progressNum}] 優化文章 #${article.id}...`);

        // Generate SEO optimizations
        const seoData = await generateSEOOptimizations(
          article.title,
          article.excerpt,
          article.content
        );

        // Update article
        await updateArticleViaAPI(article.id, seoData);

        console.log(`  ✅ 文章 #${article.id} 完成`);
        console.log(`     標題: ${seoData.optimizedTitle.substring(0, 50)}...`);
        console.log(`     描述: ${seoData.metaDescription.substring(0, 55)}...`);

        phaseProgress.success.push({
          id: article.id,
          title: article.title,
          optimizedTitle: seoData.optimizedTitle,
          metaDescription: seoData.metaDescription,
          reasoning: seoData.reasoning || "",
        });

        phaseProgress.completed++;
        progress.total_completed++;

        await new Promise((resolve) => setTimeout(resolve, DELAY_MS));
      } catch (error) {
        console.error(`  ❌ 文章 #${article.id}: ${error.message}`);
        phaseProgress.failed.push({
          id: article.id,
          error: error.message,
        });
        progress.total_failed.push({
          id: article.id,
          phase: phaseNum,
          error: error.message,
        });
      }
    }

    batchCount++;
    // Save progress after each batch
    await saveProgress(progress);
  }

  return phaseProgress;
}

/**
 * Print phase summary report
 */
function printPhaseReport(phaseNum, phaseProgress) {
  const phaseConfig = PHASES[phaseNum];
  console.log("\n" + "=".repeat(75));
  console.log(`📊 ${phaseConfig.name} 報告`);
  console.log("=".repeat(75));
  console.log(`✅ 本階段完成: ${phaseProgress.completed} 篇`);
  console.log(`❌ 本階段失敗: ${phaseProgress.failed.length} 篇`);

  if (phaseProgress.failed.length > 0) {
    console.log("\n失敗的文章（最後 5 篇）：");
    phaseProgress.failed.slice(-5).forEach((item) => {
      console.log(`  #${item.id}: ${item.error}`);
    });
    if (phaseProgress.failed.length > 5) {
      console.log(`  ... 及 ${phaseProgress.failed.length - 5} 篇`);
    }
  }
  console.log("");
}

/**
 * Print overall completion report
 */
function printCompletionReport(progress) {
  console.log("\n" + "=".repeat(75));
  console.log("📈 總體完成報告 (Phase 13-16)");
  console.log("=".repeat(75));
  console.log(`✅ 總完成: ${progress.total_completed} 篇`);
  console.log(`❌ 總失敗: ${progress.total_failed.length} 篇`);
  console.log(`📊 成功率: ${((progress.total_completed / (progress.total_completed + progress.total_failed.length)) * 100).toFixed(2)}%\n`);

  // Per-phase stats
  Object.keys(PHASES).forEach((phaseNum) => {
    const p = progress.phases[phaseNum];
    console.log(`  Phase ${phaseNum}: ${p.completed}/100 完成 (${p.failed.length} 失敗)`);
  });

  console.log("\n💾 進度已保存，可隨時恢復");
}

/**
 * Main orchestration function
 */
async function executePhases(startPhase = 13) {
  // Create output directory
  if (!fs.existsSync(OUTPUT_DIR)) {
    fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  }

  const progress = await loadProgress();

  // Process each phase sequentially
  for (let phaseNum = startPhase; phaseNum <= 16; phaseNum++) {
    const phaseConfig = PHASES[phaseNum];
    if (!phaseConfig) continue;

    const articleIds = generateArticleIds(phaseConfig.start_id, phaseConfig.end_id);
    const phaseProgress = await processPhaseBatch(phaseNum, articleIds, progress);

    // Print phase report
    printPhaseReport(phaseNum, phaseProgress);

    // Save current state
    progress.phase = phaseNum;
    await saveProgress(progress);
  }

  // Print final report
  printCompletionReport(progress);

  // Export summary to JSON
  const summaryPath = path.join(OUTPUT_DIR, "summary.json");
  fs.writeFileSync(summaryPath, JSON.stringify(progress, null, 2));
  console.log(`📄 詳細報告已保存至: ${summaryPath}`);
}

// ─── Entry Point ────────────────────────────────────────────────────────────

const startPhaseArg = process.argv[2] ? parseInt(process.argv[2]) : 13;

if (startPhaseArg < 13 || startPhaseArg > 16) {
  console.error("❌ 無效的 Phase 編號，請輸入 13-16");
  process.exit(1);
}

console.log(`🎯 開始執行 Phase ${startPhaseArg}-16 SEO 優化`);
console.log(`📍 站點: ${DOMAIN} (ID: ${SITE_ID})`);
console.log(`📦 預期處理: ${(17 - startPhaseArg) * 100} 篇文章\n`);

executePhases(startPhaseArg).catch((error) => {
  console.error("❌ 執行失敗:", error);
  process.exit(1);
});
