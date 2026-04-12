#!/usr/bin/env node
/**
 * SEO Optimization Demo - First 100 Articles
 * Shows the strategy and generates initial batches
 */

const Anthropic = require("@anthropic-ai/sdk");

const client = new Anthropic();

async function generateSeoForArticle(title, excerpt) {
  const prompt = `Generate SEO metadata for this Chinese blog article.
  
Article: "${title}"
Summary: "${excerpt || '(no summary)'}"

Respond with ONLY this JSON format:
{
  "title": "45-60 char SEO title in Traditional Chinese",
  "description": "120-160 char SEO description in Traditional Chinese"
}`;

  const msg = await client.messages.create({
    model: "claude-3-5-sonnet-20241022",
    max_tokens: 150,
    messages: [{ role: "user", content: prompt }],
  });

  try {
    return JSON.parse(msg.content[0].text);
  } catch {
    console.error("Parse error for:", title);
    return null;
  }
}

// Example run
(async () => {
  console.log("SEO 優化演示 - 處理前 5 篇文章\n");

  const articles = [
    {
      id: 35141,
      title: "誰殺了那個拉丁女伶？《傳奇女伶 高菊花》扒開白色恐怖世襲傷痕",
      excerpt:
        "長達20年文史淘金，沈可尚監製神作直擊靈魂。看高菊花如何用狂歡歌聲封印被國家機器絞碎的青春",
    },
  ];

  for (const article of articles) {
    console.log(`[${article.id}] ${article.title}`);
    const seo = await generateSeoForArticle(article.title, article.excerpt);

    if (seo) {
      console.log(`✓ 標題 (${seo.title.length}): ${seo.title}`);
      console.log(
        `✓ 描述 (${seo.description.length}): ${seo.description}\n`
      );
    }
  }
})();
