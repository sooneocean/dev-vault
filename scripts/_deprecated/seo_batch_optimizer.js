#!/usr/bin/env node

/**
 * SEO Batch Optimizer for yololab.net
 *
 * Processes all 2,725+ articles:
 * - Checks if article already has SEO optimization
 * - Generates optimized titles (45-60 chars) & descriptions (120-160 chars)
 * - Updates via WordPress REST API
 * - Reports progress in real-time
 */

const Anthropic = require("@anthropic-ai/sdk");

const client = new Anthropic({
  apiKey: process.env.ANTHROPIC_API_KEY,
});

// WordPress REST API client (manual implementation)
const SITE_ID = 133512998;
const BASE_URL = "https://public-api.wordpress.com/rest/v1.1/sites/" + SITE_ID;

// Progress tracking
let totalProcessed = 0;
let totalSuccessful = 0;
let totalSkipped = 0;
let totalFailed = 0;
let batchSuccess = 0;
const failedIds = [];
const startTime = Date.now();

/**
 * Call WordPress REST API
 */
async function wpApiCall(method, endpoint, data = null) {
  const url = BASE_URL + endpoint;
  const options = {
    method,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${process.env.WPCOM_API_TOKEN}`,
    },
  };

  if (data && (method === "POST" || method === "PUT")) {
    options.body = JSON.stringify(data);
  }

  const response = await fetch(url, options);

  if (!response.ok) {
    throw new Error(
      `WordPress API error: ${response.status} ${response.statusText}`
    );
  }

  return response.json();
}

/**
 * Fetch posts list with pagination
 */
async function fetchPostsList(page = 1) {
  return wpApiCall("GET", `/posts?page=${page}&per_page=100&status=publish`);
}

/**
 * Get single post details
 */
async function getPost(postId) {
  return wpApiCall("GET", `/posts/${postId}`);
}

/**
 * Update post with SEO metadata
 */
async function updatePost(postId, title, description) {
  return wpApiCall("PUT", `/posts/${postId}`, {
    meta: {
      jetpack_seo_html_title: title,
      advanced_seo_description: description,
    },
  });
}

/**
 * Generate SEO title + description using Anthropic API
 */
async function generateSeoContent(postTitle, postExcerpt) {
  const prompt = `You are an expert SEO specialist optimizing Chinese language blog content.

Your task: Generate ONLY the SEO title and description for this article. Output ONLY valid JSON, no markdown or explanation.

Article Title: ${postTitle}
Excerpt/Summary: ${postExcerpt}

Requirements:
- SEO Title: 45-60 characters (including spaces), optimized for CTR
- SEO Description: 120-160 characters (including spaces), compelling & keyword-rich
- Both in Traditional Chinese (繁體中文)
- Include primary keywords naturally
- Make description action-oriented when possible

Output ONLY this JSON format (no other text):
{
  "seo_title": "your optimized title here",
  "seo_description": "your optimized description here"
}`;

  const response = await client.messages.create({
    model: "claude-3-5-sonnet-20241022",
    max_tokens: 200,
    messages: [
      {
        role: "user",
        content: prompt,
      },
    ],
  });

  const content = response.content[0].text.trim();

  try {
    const parsed = JSON.parse(content);
    return {
      title: parsed.seo_title,
      description: parsed.seo_description,
    };
  } catch (e) {
    console.error(`JSON parse error for post "${postTitle}":`, content);
    throw new Error("Failed to parse SEO generation response");
  }
}

/**
 * Process single post
 */
async function processPost(post) {
  totalProcessed++;

  // Check if already optimized
  if (
    post.meta?.jetpack_seo_html_title &&
    post.meta.jetpack_seo_html_title.length > 0
  ) {
    totalSkipped++;
    return { skipped: true };
  }

  try {
    // Generate SEO content
    const seo = await generateSeoContent(post.title, post.excerpt || "");

    // Validate lengths
    if (seo.title.length < 45 || seo.title.length > 60) {
      console.warn(
        `Warning: Title length ${seo.title.length} for post ${post.id}`
      );
    }
    if (
      seo.description.length < 120 ||
      seo.description.length > 160
    ) {
      console.warn(
        `Warning: Description length ${seo.description.length} for post ${post.id}`
      );
    }

    // Update WordPress
    await updatePost(post.id, seo.title, seo.description);

    totalSuccessful++;
    batchSuccess++;

    return {
      success: true,
      title: seo.title,
      description: seo.description,
    };
  } catch (error) {
    totalFailed++;
    failedIds.push(post.id);
    console.error(`Failed post ${post.id}:`, error.message);
    return { failed: true, error: error.message };
  }
}

/**
 * Report progress
 */
function reportProgress(isMilestone = false) {
  if (isMilestone || batchSuccess >= 10) {
    const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
    const elapsedMin = Math.floor(elapsed / 60);
    const elapsedSec = Math.floor(elapsed % 60);
    const successRate = (
      ((totalSuccessful + totalSkipped) / totalProcessed) *
      100
    ).toFixed(1);

    console.log(
      `✅ ${totalSuccessful + totalSkipped}/${totalProcessed} 完成 | 成功 ${successRate}% | 耗時 ${elapsedMin}m ${elapsedSec}s`
    );

    if (isMilestone) {
      console.log(
        `   - 新優化: ${totalSuccessful} | 已有: ${totalSkipped} | 失敗: ${totalFailed}`
      );
    }

    batchSuccess = 0;
  }
}

/**
 * Main execution
 */
async function main() {
  console.log(
    "🚀 YOLO LAB SEO 優化開始 | 目標: 2,725+ 篇文章\n"
  );

  let totalPages = 0;
  let currentPage = 1;
  let hasMorePages = true;

  while (hasMorePages) {
    console.log(`\n📄 正在處理第 ${currentPage} 頁...`);

    try {
      const result = await fetchPostsList(currentPage);
      const posts = result.posts || [];

      if (totalPages === 0 && result.found) {
        totalPages = Math.ceil(result.found / 100);
        console.log(`📊 共發現 ${result.found} 篇文章 (${totalPages} 頁)\n`);
      }

      if (posts.length === 0) {
        hasMorePages = false;
        break;
      }

      // Process each post on this page
      for (const post of posts) {
        await processPost(post);

        // Report every 10 posts
        if (totalProcessed % 10 === 0) {
          reportProgress(false);
        }

        // Small delay to avoid rate limiting
        await new Promise((resolve) => setTimeout(resolve, 100));
      }

      // Report milestones (every 100 posts)
      if (totalProcessed % 100 === 0) {
        reportProgress(true);
      }

      currentPage++;
    } catch (error) {
      console.error(`Error on page ${currentPage}:`, error.message);
      // Continue with next page
      currentPage++;
    }
  }

  // Final report
  const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
  const elapsedMin = Math.floor(elapsed / 60);
  const elapsedSec = Math.floor(elapsed % 60);

  console.log("\n" + "=".repeat(60));
  console.log("✨ SEO 優化完成！");
  console.log("=".repeat(60));
  console.log(`總處理: ${totalProcessed} 篇`);
  console.log(`✅ 新優化: ${totalSuccessful} 篇`);
  console.log(`⏭️  已有優化: ${totalSkipped} 篇`);
  console.log(`❌ 失敗: ${totalFailed} 篇`);
  console.log(`耗時: ${elapsedMin}m ${elapsedSec}s`);

  if (failedIds.length > 0) {
    console.log(`\n失敗文章 IDs: ${failedIds.join(", ")}`);
  }

  console.log("=".repeat(60));
}

main().catch(console.error);
