#!/usr/bin/env node

/**
 * Phase 3 Batch 1 - SEO Optimizer (Using MCP)
 *
 * 執行 10 篇文章的 SEO 優化，使用 MCP 工具進行 WordPress.com 操作
 * 1. 使用 Claude API 生成優化的標題和 meta description
 * 2. 使用 MCP 工具 wpcom-mcp-content-authoring 執行 posts.update
 * 3. 逐篇報告結果
 */

import Anthropic from "@anthropic-ai/sdk";
import fs from "fs";

const client = new Anthropic();

const ARTICLES = [
  { id: 34826, title: "影后岸井雪乃對決曾敬驊！《鼠一般的你》台北取景..." },
  { id: 34821, title: "5/15上映！《傳奇女伶 高菊花》必看亮點：見證鄒族家族重生" },
  { id: 34816, title: "從金曲新人到靈魂導師！南穎 Fiona 用 R&B 拆解關係中的「依附病理」" },
  { id: 34809, title: "港都最強爵士盛會！高流爵對有春回歸，16組神級陣容再抽韓國機票" },
  { id: 34804, title: "10天飆破1.25億！《愛在每一天》艾琳維拉莫解剖愛情..." },
  { id: 34798, title: "別再忍受腳底慘叫！2026 SKECHERS 穿搭指南：解密霸榜全美的機能美學" },
  { id: 34794, title: "JOYCE 就以斯《才華換桃花》專場：李權哲驚喜站台..." },
  { id: 34788, title: "別在串流看！《死亡賭局》4/24 全台開局..." },
  { id: 34784, title: "拋棄CG肉身獻祭！《捕風追影》成龍梁家輝搏命，3/27必看神作" },
  { id: 34778, title: "為什麼你必須聽 LITTLE JOHN？首張專輯《LITTLE SIZE》揭秘新世代集體焦慮的出口" }
];

const SITE_URL = "yololab.net";
const OUTPUT_FILE = "phase3-batch1-results.json";

// ─── 生成 SEO 數據 ──────────────────────────────────────────────────────────

async function generateSEO(title, excerpt = "") {
  try {
    const message = await client.messages.create({
      model: "claude-opus-4-6",
      max_tokens: 300,
      messages: [
        {
          role: "user",
          content: `快速優化中文 SEO 標題和描述。

**原標題：** ${title}
${excerpt ? `**摘要：** ${excerpt}` : ""}

優化要求：
- SEO 標題：45-60 字，包含主要關鍵詞，吸引點擊率 (CTR)
- Meta Description：120-160 字，清楚描述文章內容，包含 CTA，引導用戶點擊

返回純 JSON 格式，無其他文字：
{
  "optimizedTitle": "your optimized title here",
  "metaDescription": "your meta description here"
}`
        }
      ]
    });

    const text = message.content[0].text;
    const match = text.match(/\{[\s\S]*?\}/);
    if (!match) {
      throw new Error("Response does not contain valid JSON");
    }

    const parsed = JSON.parse(match[0]);

    // 驗證長度
    if (parsed.optimizedTitle.length < 45 || parsed.optimizedTitle.length > 60) {
      console.warn(`  ⚠️  標題長度 ${parsed.optimizedTitle.length}，建議 45-60 字`);
    }
    if (parsed.metaDescription.length < 120 || parsed.metaDescription.length > 160) {
      console.warn(`  ⚠️  描述長度 ${parsed.metaDescription.length}，建議 120-160 字`);
    }

    return parsed;
  } catch (error) {
    throw new Error(`SEO generation failed: ${error.message}`);
  }
}

// ─── 主處理函數 ────────────────────────────────────────────────────────────

async function processArticles() {
  console.log("🚀 Phase 3 Batch 1 - SEO 優化執行（使用 MCP）");
  console.log("=" .repeat(70));
  console.log(`📊 目標文章數: ${ARTICLES.length}`);
  console.log(`🌐 網站: ${SITE_URL}\n`);

  const results = {
    batch: "Phase 3 Batch 1 (MCP)",
    site: SITE_URL,
    startTime: new Date().toISOString(),
    articles: [],
    summary: { success: 0, failed: 0, total: ARTICLES.length }
  };

  for (let idx = 0; idx < ARTICLES.length; idx++) {
    const article = ARTICLES[idx];
    const progress = `[${idx + 1}/${ARTICLES.length}]`;

    console.log(`\n${progress} 文章 ID: ${article.id}`);
    console.log(`   標題: ${article.title.substring(0, 50)}...`);

    try {
      // 1. 生成 SEO 優化
      console.log(`   🤖 生成 SEO 優化...`);
      const seoData = await generateSEO(article.title);

      // 記錄成功結果
      const result = {
        articleId: article.id,
        originalTitle: article.title,
        optimizedTitle: seoData.optimizedTitle,
        metaDescription: seoData.metaDescription,
        titleLength: seoData.optimizedTitle.length,
        descriptionLength: seoData.metaDescription.length,
        status: "generated",
        timestamp: new Date().toISOString(),
        mcp_update_pending: true
      };
      results.articles.push(result);
      results.summary.success++;

      console.log(`   ✅ 生成成功！`);
      console.log(`      SEO 標題 (${seoData.optimizedTitle.length}字): ${seoData.optimizedTitle}`);
      console.log(`      Meta 描述 (${seoData.metaDescription.length}字): ${seoData.metaDescription.substring(0, 60)}...`);

    } catch (error) {
      // 記錄失敗結果
      const result = {
        articleId: article.id,
        originalTitle: article.title,
        status: "failed",
        error: error.message,
        timestamp: new Date().toISOString()
      };
      results.articles.push(result);
      results.summary.failed++;

      console.log(`   ❌ 失敗: ${error.message}`);
    }

    // 延遲以避免 API 限制
    if (idx < ARTICLES.length - 1) {
      await new Promise((r) => setTimeout(r, 800));
    }
  }

  // 保存結果
  fs.writeFileSync(OUTPUT_FILE, JSON.stringify(results, null, 2));

  // 最終報告
  console.log("\n" + "=" .repeat(70));
  console.log("📈 Phase 3 Batch 1 - SEO 生成完成");
  console.log("=" .repeat(70));
  console.log(`✅ 生成成功: ${results.summary.success}/${results.summary.total}`);
  console.log(`❌ 失敗: ${results.summary.failed}/${results.summary.total}`);
  console.log(`\n💾 詳細結果保存: ${OUTPUT_FILE}`);
  console.log(`📊 成功率: ${((results.summary.success / results.summary.total) * 100).toFixed(1)}%`);

  // 列出生成的 SEO 數據
  console.log("\n📋 生成的 SEO 數據摘要：");
  results.articles
    .filter(a => a.status === "generated")
    .forEach((a, i) => {
      console.log(`\n${i + 1}. 文章 ID: ${a.articleId}`);
      console.log(`   原標題: ${a.originalTitle}`);
      console.log(`   SEO 標題: ${a.optimizedTitle}`);
      console.log(`   Meta 描述: ${a.metaDescription}`);
    });

  console.log("\n" + "=" .repeat(70));
  console.log("⏭️  下一步: 使用 MCP 工具執行 posts.update 來應用這些 SEO 優化");
  console.log("=" .repeat(70));
}

// 執行
processArticles().catch((err) => {
  console.error("\n❌ 致命錯誤:", err.message);
  process.exit(1);
});
