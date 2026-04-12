#!/usr/bin/env node

/**
 * Phase-Based SEO Optimizer for yololab.net
 *
 * 動態批量優化文章，支持分階段處理
 * 自動跟蹤進度，支持恢復
 */

import Anthropic from "@anthropic-ai/sdk";
import fs from "fs";
import path from "path";

const client = new Anthropic();

// ─── Config ─────────────────────────────────────────────────────────────────
const SITE_ID = 133512998;
const DOMAIN = "yololab.net";
const BATCH_SIZE = 10; // 並行API調用數
const DELAY_MS = 1000; // 速率限制延遲
const PROGRESS_FILE = "seo-progress.json";

// Phase definitions
const PHASES = {
  1: { start_id: 35000, batch_size: 100, name: "Phase 1: Articles 35000-34901" },
  2: { start_id: 34900, batch_size: 100, name: "Phase 2: Articles 34900-34801" },
  3: { start_id: 34800, batch_size: 100, name: "Phase 3: Articles 34800-34701" },
};

// ─── Helper Functions ───────────────────────────────────────────────────────

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
    phase: 3,
    completed: 0,
    failed: [],
    success: [],
    last_id: 34800,
  };
}

async function saveProgress(progress) {
  fs.writeFileSync(PROGRESS_FILE, JSON.stringify(progress, null, 2));
}

async function generateSEOOptimizations(title, excerpt, content = "") {
  const prompt = `你是 SEO 專家，專門優化繁體中文內容。

分析以下文章，生成改進的標題和 meta description：

**原始標題：**
${title}

**文章摘要：**
${excerpt || content.substring(0, 300) || "（無摘要）"}

**優化要求：**
1. 標題：45-60 字，包含主關鍵字，吸引點擊
2. Meta Description：120-160 字，自然包含關鍵字，清楚說明內容價值

**回應格式（JSON）：**
{
  "optimizedTitle": "...",
  "metaDescription": "..."
}`;

  const message = await client.messages.create({
    model: "claude-opus-4-6",
    max_tokens: 300,
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

async function fetchArticleViaAPI(articleId) {
  // Simulate fetching from WordPress.com API
  // In real implementation, this would call the MCP endpoint
  return {
    id: articleId,
    title: `文章 #${articleId}`,
    excerpt: "文章摘要",
    content: "",
  };
}

async function updateArticleViaAPI(articleId, seoData) {
  // Simulate updating via WordPress.com API
  // In real implementation, this would call the MCP endpoint
  console.log(`   └─ 更新文章 #${articleId}`);
  return { success: true };
}

// ─── Main Workflow ──────────────────────────────────────────────────────────

async function processPhase(phaseNum) {
  const phaseConfig = PHASES[phaseNum];
  if (!phaseConfig) {
    console.log("❌ 無效的 Phase 編號");
    return;
  }

  console.log(`\n🚀 ${phaseConfig.name}\n`);

  const progress = await loadProgress();
  let currentId = progress.last_id;
  let processedInPhase = 0;

  for (let i = 0; i < phaseConfig.batch_size; i += BATCH_SIZE) {
    const batchIds = [];
    for (let j = 0; j < BATCH_SIZE && currentId >= phaseConfig.start_id - phaseConfig.batch_size; j++) {
      batchIds.push(currentId);
      currentId--;
    }

    if (batchIds.length === 0) break;

    console.log(`📦 批次 #${Math.floor(i / BATCH_SIZE) + 1}: 處理文章 ${batchIds.join(", ")}`);

    // Fetch all articles in this batch in parallel
    const articles = await Promise.all(
      batchIds.map(id => fetchArticleViaAPI(id).catch(e => ({ id, error: e.message })))
    );

    // Generate and update SEO data
    for (const article of articles) {
      if (article.error) {
        console.log(`❌ 文章 #${article.id}: ${article.error}`);
        progress.failed.push({ id: article.id, error: article.error });
        continue;
      }

      try {
        console.log(`[${progress.completed + 1}] 正在優化文章 #${article.id}...`);

        // Generate SEO optimizations
        const seoData = await generateSEOOptimizations(
          article.title,
          article.excerpt,
          article.content
        );

        // Update article
        await updateArticleViaAPI(article.id, seoData);

        console.log(`✅ 文章 #${article.id} 完成`);
        console.log(`   標題: ${seoData.optimizedTitle.substring(0, 50)}...`);
        console.log(`   描述: ${seoData.metaDescription.substring(0, 60)}...`);

        progress.success.push({
          id: article.id,
          title: seoData.optimizedTitle,
          description: seoData.metaDescription,
        });
        progress.completed++;
        processedInPhase++;

        await new Promise((resolve) => setTimeout(resolve, DELAY_MS));
      } catch (error) {
        console.error(`❌ 文章 #${article.id}: ${error.message}`);
        progress.failed.push({ id: article.id, error: error.message });
      }
    }

    // Save progress after each batch
    progress.last_id = currentId;
    await saveProgress(progress);
  }

  // Print phase report
  console.log("\n" + "=".repeat(70));
  console.log(`📊 ${phaseConfig.name} 報告`);
  console.log("=".repeat(70) + "\n");
  console.log(`✅ 本階段完成: ${processedInPhase} 篇`);
  console.log(`📈 累計完成: ${progress.completed} 篇`);
  console.log(`❌ 失敗: ${progress.failed.length} 篇\n`);

  if (progress.failed.length > 0) {
    console.log("失敗的文章：");
    progress.failed.slice(-5).forEach((item) => {
      console.log(`  #${item.id}: ${item.error}`);
    });
    if (progress.failed.length > 5) {
      console.log(`  ... 及 ${progress.failed.length - 5} 篇`);
    }
  }

  console.log("\n💾 進度已保存，可隨時恢復");
}

// ─── Entry Point ────────────────────────────────────────────────────────────

const phaseArg = process.argv[2] || "3";
processPhase(parseInt(phaseArg)).catch(console.error);
