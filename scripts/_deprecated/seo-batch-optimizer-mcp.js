#!/usr/bin/env node

/**
 * SEO Batch Optimizer for YOLOLAB.net
 * Uses WordPress.com MCP to fetch articles and Anthropic SDK to generate SEO metadata
 */

const Anthropic = require("@anthropic-ai/sdk");

const SITE_ID = 133512998;
const BATCH_SIZE = 10;
const API_DELAY_MS = 1500;
const TOTAL_ARTICLES = 2725;
const ALREADY_OPTIMIZED = 74;

const client = new Anthropic({
  apiKey: process.env.ANTHROPIC_API_KEY,
});

/**
 * Generate SEO metadata for an article
 */
async function generateSeoMetadata(title, excerpt) {
  try {
    // Clean excerpt
    const excerptText = excerpt
      .replace(/<[^>]+>/g, "")
      .replace(/&nbsp;/g, " ")
      .substring(0, 400);

    const message = await client.messages.create({
      model: "claude-opus-4-6",
      max_tokens: 300,
      messages: [
        {
          role: "user",
          content: `請為以下文章生成優化的 SEO 元數據。

標題：${title}
摘要：${excerptText}

要求：
1. SEO 標題：45-60 字，包含關鍵詞，吸引人
2. Meta 描述：120-160 字，包含關鍵詞和呼籲行動

只輸出 JSON 格式，無其他文本：
{"title": "...", "description": "..."}`,
        },
      ],
    });

    // Parse response
    const text = message.content[0].text;
    try {
      const result = JSON.parse(text);
      return {
        title: result.title,
        description: result.description,
      };
    } catch (e) {
      // Fallback parsing
      const titleMatch = text.match(/"title":\s*"([^"]+)"/);
      const descMatch = text.match(/"description":\s*"((?:[^"\\]|\\.)*)"/);

      return {
        title: titleMatch ? titleMatch[1].replace(/\\"/g, '"') : null,
        description: descMatch ? descMatch[1].replace(/\\"/g, '"') : null,
      };
    }
  } catch (error) {
    console.error(`    [ERROR] Generation failed: ${error.message}`);
    return { title: null, description: null };
  }
}

/**
 * Sleep utility
 */
function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Process demo batch
 */
async function processDemoBatch() {
  console.log("=".repeat(80));
  console.log("SEO Batch Optimizer for YOLOLAB.net");
  console.log(`Site ID: ${SITE_ID}`);
  console.log(`Total articles: ${TOTAL_ARTICLES}`);
  console.log(`Already optimized: ${ALREADY_OPTIMIZED}`);
  console.log(`Remaining: ${TOTAL_ARTICLES - ALREADY_OPTIMIZED}`);
  console.log("=".repeat(80));
  console.log();

  const articles = [
    {
      id: 35141,
      title:
        "誰殺了那個拉丁女伶？《傳奇女伶 高菊花》扒開白色恐怖世襲傷痕",
      excerpt:
        "長達20年文史淘金，沈可尚監製神作《傳奇女伶 高菊花》5/15震撼上映。這不是溫情回顧，而是直擊靈魂的重擊！看高菊花如何用狂歡歌聲封印被絞碎的青春，以肉身抵擋威權凌遲。現在就點入，補修這份遲來的民主學分！",
    },
    {
      id: 35137,
      title:
        "孤獨搖滾魂集結！音羽-otoha- 巡迴台北站：門票、亮點、演出資訊懶人包",
      excerpt:
        "還在回味浮現祭的感動？音羽-otoha- 帶著全編制樂團重返台北！從《孤獨搖滾！》到《黑執事》神曲，這場在 The Wall 的近距離重擊是你與青春焦慮和解的唯一門票。4月14日搶票大戰開打，沒搶到保證後悔。",
    },
    {
      id: 35133,
      title: "Y2K 迷必看！luv 台北站攻略：從《魔物獵人》到關西 Neo Soul 亮點",
      excerpt:
        "別再隔著耳機垂涎！2003 年生關西怪物新人 luv 橫掃 SXSW 後重返台北，4/12 在 The Wall 迎來亞洲巡迴最終站。揉合《魔物獵人》熱血節拍與 Y2K 靈魂律動，這場極具「化學反應」的現場演出，是你親眼見證傳奇崛起的唯一機會。僅剩席次，立即卡位！",
    },
  ];

  console.log("Processing first batch (demo):\n");

  let successCount = 0;
  let failedCount = 0;
  const failedIds = [];

  for (let i = 0; i < articles.length; i++) {
    const article = articles[i];
    const postId = article.id;
    const title = article.title;
    const excerpt = article.excerpt;

    process.stdout.write(
      `  [${i + 1}] Post ${postId}: ${title.substring(0, 45)}... `
    );

    if (!title || !excerpt) {
      console.log("[SKIP - no content]");
      continue;
    }

    // Generate SEO metadata
    const seo = await generateSeoMetadata(title, excerpt);

    if (!seo.title || !seo.description) {
      console.log("[FAIL - generation]");
      failedCount++;
      failedIds.push(postId);
      continue;
    }

    console.log("[OK]");
    console.log(`      Title (${seo.title.length}): ${seo.title.substring(0, 50)}...`);
    console.log(
      `      Desc  (${seo.description.length}): ${seo.description.substring(0, 60)}...`
    );
    successCount++;

    // Rate limiting
    if (i < articles.length - 1) {
      await sleep(300);
    }
  }

  console.log();
  console.log(
    `Batch 1 Result: ${successCount} success, ${failedCount} failed`
  );
  console.log(
    `Running total: ${ALREADY_OPTIMIZED + successCount}/${TOTAL_ARTICLES}`
  );
  console.log(
    `Progress: ${(((ALREADY_OPTIMIZED + successCount) / TOTAL_ARTICLES) * 100).toFixed(2)}%`
  );
  console.log();
  console.log("=".repeat(80));

  if (failedIds.length > 0) {
    console.log(`Failed IDs: ${failedIds.join(", ")}`);
  }

  console.log();
  console.log("Next steps:");
  console.log("1. Review generated SEO metadata above");
  console.log(
    "2. When ready, call posts.update via WordPress.com MCP to persist changes"
  );
  console.log("3. Implement pagination loop for remaining batches");
  console.log("4. Report progress milestones every 100 articles");
}

// Run
processDemoBatch().catch(console.error);
