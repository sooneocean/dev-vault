#!/usr/bin/env node

/**
 * Phase 4 Parallel SEO Optimizer - yololab.net
 *
 * 處理文章 100 篇（IDs: ~34700-34601）
 * 10 個批次並行，每批 10 篇
 *
 * 頁碼分配：
 * - Batch 1: page=9   (IDs ~34700-34691)
 * - Batch 2: page=10  (IDs ~34690-34681)
 * - Batch 3: page=11  (IDs ~34680-34671)
 * - Batch 4: page=12  (IDs ~34670-34661)
 * - Batch 5: page=13  (IDs ~34660-34651)
 * - Batch 6: page=14  (IDs ~34650-34641)
 * - Batch 7: page=15  (IDs ~34640-34631)
 * - Batch 8: page=16  (IDs ~34630-34621)
 * - Batch 9: page=17  (IDs ~34620-34611)
 * - Batch 10: page=18 (IDs ~34610-34601)
 */

import Anthropic from "@anthropic-ai/sdk";
import fetch from "node-fetch";
import fs from "fs";
import path from "path";

const client = new Anthropic();

const BLOG_ID = 133512998;
const BATCH_PAGES = [9, 10, 11, 12, 13, 14, 15, 16, 17, 18];
const PER_PAGE = 10;
const DELAY_MS = 1500; // API 調用延遲
const PROGRESS_DIR = "phase4-progress";
const OUTPUT_DIR = "phase4-output";

// ─── Initialization ────────────────────────────────────────────────────────

function ensureDirectories() {
  [PROGRESS_DIR, OUTPUT_DIR].forEach((dir) => {
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
  });
}

function getProgressFile(batchNum) {
  return path.join(PROGRESS_DIR, `batch-${batchNum}-progress.json`);
}

function getOutputFile(batchNum) {
  return path.join(OUTPUT_DIR, `batch-${batchNum}-results.json`);
}

// ─── Progress Tracking ─────────────────────────────────────────────────────

function loadBatchProgress(batchNum) {
  try {
    const file = getProgressFile(batchNum);
    if (fs.existsSync(file)) {
      return JSON.parse(fs.readFileSync(file, "utf-8"));
    }
  } catch (e) {
    console.log(`⚠️  Batch ${batchNum} 進度文件損壞，從頭開始\n`);
  }
  return {
    batch: batchNum,
    page: BATCH_PAGES[batchNum - 1],
    articles: [],
    processed: 0,
    success: 0,
    failed: 0,
    startTime: new Date().toISOString(),
  };
}

function saveBatchProgress(batchNum, progress) {
  progress.lastUpdate = new Date().toISOString();
  fs.writeFileSync(
    getProgressFile(batchNum),
    JSON.stringify(progress, null, 2)
  );
}

// ─── WordPress.com API ────────────────────────────────────────────────────

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
      `https://public-api.wordpress.com/wp/v2/sites/${BLOG_ID}/posts?page=${page}&per_page=${PER_PAGE}&context=edit`,
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

async function fetchPost(postId, token) {
  try {
    const response = await fetch(
      `https://public-api.wordpress.com/wp/v2/sites/${BLOG_ID}/posts/${postId}?context=edit`,
      { headers: { Authorization: `Bearer ${token}` } }
    );
    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }
    return response.json();
  } catch (error) {
    throw new Error(`Failed to fetch post ${postId}: ${error.message}`);
  }
}

async function updatePost(postId, seoData, token) {
  try {
    const response = await fetch(
      `https://public-api.wordpress.com/wp/v2/sites/${BLOG_ID}/posts/${postId}`,
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          meta: {
            jetpack_seo_html_title: seoData.optimizedTitle,
            advanced_seo_description: seoData.metaDescription,
          },
        }),
      }
    );
    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Update failed: ${response.statusText}`);
    }
    return response.json();
  } catch (error) {
    throw new Error(`Failed to update post ${postId}: ${error.message}`);
  }
}

// ─── SEO Generation ───────────────────────────────────────────────────────

async function generateSEO(title, excerpt) {
  try {
    const message = await client.messages.create({
      model: "claude-opus-4-6",
      max_tokens: 250,
      messages: [
        {
          role: "user",
          content: `你是 SEO 專家。為以下文章生成優化的 SEO 標題和描述。

**原始標題**：${title}

**摘要**：${excerpt || "(無摘要)"}

**要求**：
1. 優化標題：45-60 字，包含主要關鍵詞
2. Meta 描述：120-160 字，吸引人，呼籲行動

**格式**（JSON）：
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

// ─── Batch Processing ─────────────────────────────────────────────────────

async function processBatch(batchNum, token) {
  const page = BATCH_PAGES[batchNum - 1];
  console.log(`\n🚀 Batch ${batchNum} 開始（Page ${page}）\n`);

  const progress = loadBatchProgress(batchNum);

  try {
    // 1. 取得列表（如果還沒有取得）
    if (progress.articles.length === 0) {
      const posts = await fetchPostsList(page, token);
      progress.articles = posts.map((post) => ({
        id: post.id,
        title: post.title.rendered,
        excerpt: post.excerpt.rendered?.replace(/<[^>]*>/g, "") || "",
        status: "pending",
      }));
      saveBatchProgress(batchNum, progress);
    }

    // 2. 處理每篇文章
    for (let i = 0; i < progress.articles.length; i++) {
      const article = progress.articles[i];

      if (article.status === "success") {
        console.log(
          `✅ [${batchNum}/${i + 1}] Post ${article.id} 已完成，跳過\n`
        );
        continue;
      }

      try {
        console.log(`⏳ [${batchNum}/${i + 1}] Post ${article.id}：生成 SEO...`);

        // 生成 SEO
        const seoData = await generateSEO(article.title, article.excerpt);

        // 更新文章
        console.log(`   → 更新文章...`);
        await updatePost(article.id, seoData, token);

        // 記錄成功
        article.status = "success";
        article.seoData = seoData;
        progress.success++;

        console.log(`   ✅ 成功\n`);

        // 延遲以避免 API 限流
        await new Promise((resolve) => setTimeout(resolve, DELAY_MS));
      } catch (error) {
        console.log(`   ❌ 失敗：${error.message}\n`);
        article.status = "failed";
        article.error = error.message;
        progress.failed++;
      }

      progress.processed++;
      saveBatchProgress(batchNum, progress);
    }

    // 3. 保存批次結果
    progress.endTime = new Date().toISOString();
    fs.writeFileSync(
      getOutputFile(batchNum),
      JSON.stringify(progress, null, 2)
    );

    console.log(
      `\n📊 Batch ${batchNum} 完成：${progress.success}/${progress.articles.length} 成功\n`
    );

    return progress;
  } catch (error) {
    console.error(`❌ Batch ${batchNum} 錯誤：${error.message}\n`);
    throw error;
  }
}

// ─── Main Execution ───────────────────────────────────────────────────────

async function main() {
  console.log("=" .repeat(70));
  console.log("Phase 4 Parallel SEO Optimizer - yololab.net");
  console.log("100 篇文章，10 個批次，並行處理");
  console.log("=" .repeat(70));

  ensureDirectories();

  try {
    const token = await getWpComToken();

    // 並行運行所有批次
    const batchPromises = BATCH_PAGES.map((_, index) =>
      processBatch(index + 1, token)
    );

    const results = await Promise.allSettled(batchPromises);

    // 彙總結果
    console.log("\n" + "=" .repeat(70));
    console.log("🏁 Phase 4 最終統計");
    console.log("=" .repeat(70) + "\n");

    let totalSuccess = 0;
    let totalFailed = 0;
    let totalProcessed = 0;

    results.forEach((result, index) => {
      const batchNum = index + 1;
      if (result.status === "fulfilled") {
        const batch = result.value;
        totalSuccess += batch.success;
        totalFailed += batch.failed;
        totalProcessed += batch.processed;

        console.log(
          `📦 Batch ${batchNum.toString().padStart(2, "0")} (Page ${BATCH_PAGES[index].toString().padStart(2, "0")}): ${batch.success.toString().padStart(2, "0")}/${batch.articles.length} ✅`
        );
      } else {
        console.log(
          `📦 Batch ${batchNum.toString().padStart(2, "0")} (Page ${BATCH_PAGES[index].toString().padStart(2, "0")}): ❌ ${result.reason.message}`
        );
      }
    });

    console.log("\n" + "─".repeat(70));
    console.log(`✅ 成功：${totalSuccess}`);
    console.log(`❌ 失敗：${totalFailed}`);
    console.log(`📊 總處理：${totalProcessed}`);
    console.log(`📈 成功率：${((totalSuccess / totalProcessed) * 100).toFixed(2)}%`);
    console.log("─".repeat(70) + "\n");

    // 保存總結
    const summary = {
      phase: 4,
      totalBatches: BATCH_PAGES.length,
      totalArticles: BATCH_PAGES.length * PER_PAGE,
      totalSuccess,
      totalFailed,
      totalProcessed,
      successRate: (totalSuccess / totalProcessed) * 100,
      completedAt: new Date().toISOString(),
      outputDir: OUTPUT_DIR,
      progressDir: PROGRESS_DIR,
    };

    fs.writeFileSync(
      path.join(OUTPUT_DIR, "phase4-summary.json"),
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
