#!/usr/bin/env node

/**
 * SEO Batch Optimizer for yololab.net (Using MCP)
 *
 * Strategy:
 * 1. Fetch all articles page by page
 * 2. For each article without SEO optimization:
 *    - Call Anthropic API to generate SEO title + description
 *    - Use MCP tool to update WordPress
 * 3. Report progress every 10 posts, milestones every 100
 *
 * Note: This is a coordinator script that needs to be executed in Claude Code
 * where MCP tools are available.
 */

const Anthropic = require("@anthropic-ai/sdk");
const fs = require("fs");

const client = new Anthropic({
  apiKey: process.env.ANTHROPIC_API_KEY,
});

const SITE_ID = 133512998;

// Progress state
let state = {
  totalProcessed: 0,
  totalSuccessful: 0,
  totalSkipped: 0,
  totalFailed: 0,
  failedIds: [],
  batchSuccessCount: 0,
  startTime: Date.now(),
  currentPage: 1,
  totalPages: null,
};

const STATE_FILE = "/tmp/seo_optimizer_state.json";

/**
 * Generate SEO content using Anthropic API
 */
async function generateSeoContent(postTitle, postExcerpt) {
  const prompt = `You are an expert SEO specialist optimizing Chinese language blog content for yololab.net - a data-driven culture & entertainment lab.

Task: Generate SEO title and description. Output ONLY valid JSON.

Article Title: ${postTitle}
Excerpt: ${postExcerpt || "(no excerpt)"}

Requirements:
- SEO Title: 45-60 characters (with spaces), CTR-optimized for Google/social
- SEO Description: 120-160 characters (with spaces), engaging & keyword-rich
- Both in Traditional Chinese (繁體中文)
- Reflect the analytical/data-driven tone of YOLO LAB
- Avoid clickbait while being compelling

Output format (JSON ONLY):
{
  "seo_title": "...",
  "seo_description": "..."
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

  const text = response.content[0].text.trim();

  try {
    const parsed = JSON.parse(text);
    return {
      seoTitle: parsed.seo_title,
      seoDescription: parsed.seo_description,
    };
  } catch (e) {
    throw new Error(`Failed to parse: ${text}`);
  }
}

/**
 * Report progress
 */
function reportProgress(isMilestone = false) {
  const { totalProcessed, totalSuccessful, totalSkipped, totalFailed, batchSuccessCount, startTime } = state;

  if (isMilestone || batchSuccessCount >= 10) {
    const elapsed = (Date.now() - startTime) / 1000;
    const min = Math.floor(elapsed / 60);
    const sec = Math.floor(elapsed % 60);
    const successRate = (
      ((totalSuccessful + totalSkipped) / totalProcessed) * 100
    ).toFixed(1);

    console.log(
      `\n📊 進度: ${totalSuccessful + totalSkipped}/${totalProcessed} ✓ | 成功率 ${successRate}% | 耗時 ${min}m ${sec}s`
    );

    if (isMilestone) {
      console.log(`   新優化: ${totalSuccessful} | 已有: ${totalSkipped} | 失敗: ${totalFailed}`);
    }

    state.batchSuccessCount = 0;
  }
}

/**
 * Save state to file
 */
function saveState() {
  fs.writeFileSync(STATE_FILE, JSON.stringify(state, null, 2));
}

/**
 * Main coordinator logic
 */
async function coordinateBatchOptimization() {
  console.log("🚀 YOLO LAB SEO 批量優化啟動\n");
  console.log("⚠️  說明:");
  console.log("- 本腳本為調度器，負責生成 SEO 內容");
  console.log("- 實際的 WordPress 更新需透過 Claude Code MCP 工具執行");
  console.log("- 每篇文章的更新會在下一行顯示調用指令\n");

  console.log("第一步：生成前 10 篇文章的 SEO 內容（測試）\n");

  // Mock data for demonstration
  const mockPosts = [
    {
      id: 35141,
      title: "誰殺了那個拉丁女伶？《傳奇女伶 高菊花》扒開白色恐怖世襲傷痕",
      excerpt:
        "長達20年文史淘金，沈可尚監製神作直擊靈魂。看高菊花如何用狂歡歌聲封印被國家機器絞碎的青春",
    },
    {
      id: 35137,
      title:
        "孤獨搖滾魂集結！音羽-otoha- 巡迴台北站：門票、亮點、演出資訊懶人包",
      excerpt: "日本動畫神作改編演唱會降臨台北，必看亮點全解析",
    },
    {
      id: 35133,
      title:
        "Y2K 迷必看！luv 台北站攻略：從《魔物獵人》到關西 Neo Soul 亮點",
      excerpt: "2026 電音盛事 luv 台北站完整指南，門票搶購攻略",
    },
  ];

  for (const post of mockPosts) {
    try {
      state.totalProcessed++;

      console.log(`[${state.totalProcessed}] 處理: "${post.title}"`);

      // Skip if already has SEO
      // (We'll skip check when integrated with MCP)
      if (post.seo_skip) {
        state.totalSkipped++;
        console.log("   ⏭️  已有優化，略過\n");
        continue;
      }

      // Generate SEO content
      console.log("   🤖 生成 SEO 內容...");
      const seo = await generateSeoContent(post.title, post.excerpt);

      state.totalSuccessful++;
      state.batchSuccessCount++;

      console.log(`   ✅ 標題 (${seo.seoTitle.length} 字): ${seo.seoTitle}`);
      console.log(
        `   ✅ 描述 (${seo.seoDescription.length} 字): ${seo.seoDescription}`
      );

      // Save to state for later processing
      state[`post_${post.id}`] = seo;

      console.log(
        `   ➡️  MCP 調用: updatePost(${post.id}, "${seo.seoTitle}", "${seo.seoDescription}")\n`
      );

      reportProgress(false);

      // Rate limit: 100ms between API calls
      await new Promise((resolve) => setTimeout(resolve, 100));
    } catch (error) {
      state.totalFailed++;
      state.failedIds.push(post.id);
      console.error(`   ❌ 失敗: ${error.message}\n`);
    }
  }

  saveState();

  console.log("\n" + "=".repeat(60));
  console.log("✨ SEO 生成階段完成！");
  console.log("=".repeat(60));
  console.log(`已生成: ${state.totalSuccessful} 篇`);
  console.log(`失敗: ${state.totalFailed} 篇`);
  console.log(`\n💾 狀態已保存到: ${STATE_FILE}`);
  console.log("\n下一步: 使用 MCP 工具批量更新 WordPress");
  console.log("範例: posts.update(35141, {meta: {...}})");
}

coordinateBatchOptimization().catch(console.error);
