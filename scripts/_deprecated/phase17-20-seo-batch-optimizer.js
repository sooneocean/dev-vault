#!/usr/bin/env node

/**
 * Phase 17-20 SEO 批量優化 - yololab.net
 *
 * 處理文章 400 篇（分 4 個 Phase，每 Phase 100 篇）
 *
 * Phase 17：posts.list page=37-40 (100 篇)
 * Phase 18：posts.list page=41-44 (100 篇)
 * Phase 19：posts.list page=45-48 (100 篇)
 * Phase 20：posts.list page=49-52 (100 篇)
 *
 * 使用 wpcom-mcp API 和 Claude API
 * 實時執行，進度實時保存
 */

import Anthropic from "@anthropic-ai/sdk";
import fetch from "node-fetch";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const client = new Anthropic();

const BLOG_ID = 133512998;
const PHASES = [
  { phase: 17, pages: [37, 38, 39, 40] },
  { phase: 18, pages: [41, 42, 43, 44] },
  { phase: 19, pages: [45, 46, 47, 48] },
  { phase: 20, pages: [49, 50, 51, 52] },
];

const PER_PAGE = 10;
const DELAY_MS = 500;
const PROGRESS_DIR = "phase17-20-progress";
const OUTPUT_DIR = "phase17-20-output";
const BATCH_SIZE = 10;

// ─── 初始化 ────────────────────────────────────────────────────────────

function ensureDirectories() {
  [PROGRESS_DIR, OUTPUT_DIR].forEach((dir) => {
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
  });
}

function getProgressFile(phase) {
  return path.join(PROGRESS_DIR, `phase-${phase}-progress.json`);
}

function getOutputFile(phase) {
  return path.join(OUTPUT_DIR, `phase-${phase}-results.json`);
}

// ─── 進度追蹤 ─────────────────────────────────────────────────────────

function loadPhaseProgress(phase) {
  try {
    const file = getProgressFile(phase);
    if (fs.existsSync(file)) {
      return JSON.parse(fs.readFileSync(file, "utf-8"));
    }
  } catch (e) {
    console.log(`⚠️  Phase ${phase} 進度文件損壞，從頭開始\n`);
  }
  return {
    phase,
    pages: PHASES.find((p) => p.phase === phase).pages,
    articles: [],
    processed: 0,
    success: 0,
    failed: 0,
    skipped: 0,
    startTime: new Date().toISOString(),
  };
}

function savePhaseProgress(phase, progress) {
  progress.lastUpdate = new Date().toISOString();
  fs.writeFileSync(
    getProgressFile(phase),
    JSON.stringify(progress, null, 2)
  );
}

// ─── WordPress.com API ────────────────────────────────────────────────

async function getWpComToken() {
  const token = process.env.WPCOM_TOKEN;
  if (!token) {
    throw new Error(
      "❌ 缺少 WPCOM_TOKEN 環境變數\n" +
      "   請運行: export WPCOM_TOKEN=your_token\n" +
      "   取得令牌: https://developer.wordpress.com/apps/"
    );
  }
  return token;
}

async function fetchPostsList(page, token) {
  try {
    const response = await fetch(
      `https://public-api.wordpress.com/wp/v2/sites/${BLOG_ID}/posts?page=${page}&per_page=${PER_PAGE}&context=edit&_fields=id,title,excerpt,content,categories,tags,date,meta,yoast_seo`,
      { headers: { Authorization: `Bearer ${token}` } }
    );
    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }
    return response.json();
  } catch (error) {
    throw new Error(`Failed to fetch posts list page ${page}: ${error.message}`);
  }
}

async function updatePost(postId, seoData, token) {
  try {
    const payload = {
      meta: {
        yoast_meta: {
          title: seoData.optimizedTitle || "",
          metadesc: seoData.metaDescription || "",
        },
      },
    };

    const response = await fetch(
      `https://public-api.wordpress.com/wp/v2/sites/${BLOG_ID}/posts/${postId}`,
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      }
    );

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Update failed: ${response.statusText} - ${error}`);
    }
    return response.json();
  } catch (error) {
    throw new Error(`Failed to update post ${postId}: ${error.message}`);
  }
}

// ─── SEO 生成 ───────────────────────────────────────────────────────

async function generateSEO(title, excerpt, categories) {
  try {
    const categoryStr = Array.isArray(categories)
      ? categories.map((c) => (typeof c === "object" ? c.name : c)).join(", ")
      : "";

    const message = await client.messages.create({
      model: "claude-haiku-4-5-20251001",
      max_tokens: 200,
      messages: [
        {
          role: "user",
          content: `你是 SEO 專家。為以下文章生成優化的 SEO 標題和描述。

**原始標題**：${title}

**分類**：${categoryStr || "(無分類)"}

**摘要**：${excerpt ? excerpt.replace(/<[^>]*>/g, "").substring(0, 200) : "(無摘要)"}

**要求**：
1. 優化標題：45-60 字，包含主要關鍵詞，符合搜尋趨勢
2. Meta 描述：120-160 字，包含主要關鍵詞，具有行動號召，吸引點擊

**格式（JSON）**：
{
  "optimizedTitle": "...",
  "metaDescription": "..."
}`,
        },
      ],
    });

    const content = message.content[0].text;
    const match = content.match(/\{[\s\S]*\}/);
    if (!match) throw new Error("Unable to parse JSON from Claude response");

    return JSON.parse(match[0]);
  } catch (error) {
    throw new Error(`SEO generation failed: ${error.message}`);
  }
}

// ─── Phase 執行 ─────────────────────────────────────────────────────

async function executePhase(phaseNum, token) {
  const phaseConfig = PHASES.find((p) => p.phase === phaseNum);
  console.log(
    `\n🚀 Phase ${phaseNum} 開始（Pages ${phaseConfig.pages.join(", ")}）\n`
  );

  const progress = loadPhaseProgress(phaseNum);

  try {
    // 1. 收集所有文章（如果還沒有）
    if (progress.articles.length === 0) {
      console.log(`📥 Phase ${phaseNum}: 開始收集文章...\n`);

      for (const page of phaseConfig.pages) {
        try {
          const posts = await fetchPostsList(page, token);

          if (!Array.isArray(posts) || posts.length === 0) {
            console.log(`   ⚠️  Page ${page} 無文章或返回格式異常\n`);
            continue;
          }

          for (const post of posts) {
            progress.articles.push({
              id: post.id,
              title: post.title?.rendered || post.title || "",
              excerpt:
                post.excerpt?.rendered?.replace(/<[^>]*>/g, "") ||
                post.excerpt ||
                "",
              categories: post.categories || [],
              status: "pending",
            });
          }

          console.log(`   ✅ Page ${page}: 收集 ${posts.length} 篇\n`);
          savePhaseProgress(phaseNum, progress);

          // 頁面間延遲
          await new Promise((resolve) => setTimeout(resolve, DELAY_MS));
        } catch (error) {
          console.log(`   ⚠️  Page ${page} 出錯：${error.message}\n`);
        }
      }

      console.log(
        `\n📊 Phase ${phaseNum} 共收集 ${progress.articles.length} 篇文章\n`
      );
    }

    // 2. 處理每篇文章
    let batchCount = 0;
    for (let i = 0; i < progress.articles.length; i++) {
      const article = progress.articles[i];

      // 跳過已完成的
      if (article.status === "success") {
        console.log(
          `✅ [${phaseNum}/${i + 1}/${progress.articles.length}] Post ${article.id} 已完成，跳過\n`
        );
        progress.skipped++;
        continue;
      }

      if (article.status === "failed") {
        console.log(
          `⏭️  [${phaseNum}/${i + 1}/${progress.articles.length}] Post ${article.id} 已失敗，跳過\n`
        );
        continue;
      }

      try {
        console.log(
          `⏳ [${phaseNum}/${i + 1}/${progress.articles.length}] Post ${article.id}：生成 SEO...`
        );

        // 生成 SEO
        const seoData = await generateSEO(
          article.title,
          article.excerpt,
          article.categories
        );

        // 更新文章
        console.log(`   → 更新文章...`);
        await updatePost(article.id, seoData, token);

        // 記錄成功
        article.status = "success";
        article.seoData = seoData;
        progress.success++;

        console.log(`   ✅ 成功\n`);

        // 批次延遲
        batchCount++;
        if (batchCount % BATCH_SIZE === 0) {
          console.log(`⏸️  批次 ${batchCount / BATCH_SIZE} 完成，暫停...\n`);
          await new Promise((resolve) => setTimeout(resolve, DELAY_MS * 2));
        } else {
          await new Promise((resolve) => setTimeout(resolve, DELAY_MS));
        }
      } catch (error) {
        console.log(`   ❌ 失敗：${error.message}\n`);
        article.status = "failed";
        article.error = error.message;
        progress.failed++;
      }

      progress.processed++;
      savePhaseProgress(phaseNum, progress);
    }

    // 3. 保存最終結果
    progress.endTime = new Date().toISOString();
    fs.writeFileSync(
      getOutputFile(phaseNum),
      JSON.stringify(progress, null, 2)
    );

    console.log(
      `\n📊 Phase ${phaseNum} 完成：${progress.success}/${progress.articles.length} 成功 (跳過 ${progress.skipped})\n`
    );

    return progress;
  } catch (error) {
    console.error(`❌ Phase ${phaseNum} 錯誤：${error.message}\n`);
    throw error;
  }
}

// ─── 主程序 ───────────────────────────────────────────────────────

async function main() {
  console.log("=" .repeat(70));
  console.log("Phase 17-20 SEO 批量優化 - yololab.net");
  console.log("400 篇文章，4 個 Phase，逐 Phase 串行執行");
  console.log("=" .repeat(70));

  ensureDirectories();

  try {
    const token = await getWpComToken();

    const results = [];
    for (const phaseConfig of PHASES) {
      const result = await executePhase(phaseConfig.phase, token);
      results.push(result);
    }

    // 彙總結果
    console.log("\n" + "=" .repeat(70));
    console.log("🏁 Phase 17-20 最終統計");
    console.log("=" .repeat(70) + "\n");

    let totalSuccess = 0;
    let totalFailed = 0;
    let totalSkipped = 0;
    let totalProcessed = 0;

    results.forEach((result) => {
      totalSuccess += result.success;
      totalFailed += result.failed;
      totalSkipped += result.skipped;
      totalProcessed += result.processed;

      console.log(
        `📦 Phase ${result.phase.toString().padStart(2, "0")}: ${result.success
          .toString()
          .padStart(3, "0")}/${result.articles.length} ✅ (跳過 ${result.skipped})`
      );
    });

    console.log("\n" + "─".repeat(70));
    console.log(`✅ 成功：${totalSuccess}`);
    console.log(`⏭️  跳過：${totalSkipped}`);
    console.log(`❌ 失敗：${totalFailed}`);
    console.log(`📊 總處理：${totalProcessed}`);
    console.log(
      `📈 成功率：${totalProcessed > 0 ? ((totalSuccess / totalProcessed) * 100).toFixed(2) : 0}%`
    );
    console.log("─".repeat(70) + "\n");

    // 保存總結
    const summary = {
      phases: PHASES.map((p) => p.phase),
      totalBatches: PHASES.length,
      totalArticles: PHASES.length * PER_PAGE * 4,
      totalSuccess,
      totalFailed,
      totalSkipped,
      totalProcessed,
      successRate: totalProcessed > 0 ? (totalSuccess / totalProcessed) * 100 : 0,
      completedAt: new Date().toISOString(),
      outputDir: OUTPUT_DIR,
      progressDir: PROGRESS_DIR,
    };

    fs.writeFileSync(
      path.join(OUTPUT_DIR, "phase17-20-summary.json"),
      JSON.stringify(summary, null, 2)
    );

    console.log(
      `📁 詳細結果已保存至 ${OUTPUT_DIR}/ 和 ${PROGRESS_DIR}/ 目錄\n`
    );
  } catch (error) {
    console.error("❌ 致命錯誤：", error.message);
    process.exit(1);
  }
}

// Run
main().catch(console.error);
