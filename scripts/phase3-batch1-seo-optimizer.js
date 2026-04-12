#!/usr/bin/env node

/**
 * Phase 3 Batch 1 - SEO Optimizer
 *
 * 執行 10 篇文章的 SEO 優化：34826, 34821, 34816, 34809, 34804, 34798, 34794, 34788, 34784, 34778
 * 1. 使用 Claude API 生成優化的標題（45-60字）和 meta description（120-160字）
 * 2. 使用 WordPress.com MCP 工具執行 posts.update
 * 3. 逐篇報告結果
 */

import Anthropic from "@anthropic-ai/sdk";
import fetch from "node-fetch";
import fs from "fs";

const client = new Anthropic();

const BLOG_ID = 133512998;
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

const DELAY_MS = 1000; // API 調用延遲
const OUTPUT_FILE = "phase3-batch1-results.json";

// ─── Progress Tracking ──────────────────────────────────────────────────────

function loadResults() {
  try {
    if (fs.existsSync(OUTPUT_FILE)) {
      return JSON.parse(fs.readFileSync(OUTPUT_FILE, "utf-8"));
    }
  } catch (e) {
    console.log("⚠️  結果文件不存在，建立新記錄\n");
  }
  return {
    batch: "Phase 3 Batch 1",
    startTime: new Date().toISOString(),
    articles: [],
    summary: { success: 0, failed: 0, total: ARTICLES.length }
  };
}

function saveResults(results) {
  results.endTime = new Date().toISOString();
  fs.writeFileSync(OUTPUT_FILE, JSON.stringify(results, null, 2));
}

// ─── WordPress.com API ──────────────────────────────────────────────────────

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

// ─── SEO Generation via Claude API ──────────────────────────────────────────

async function generateSEO(title, excerpt) {
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
- SEO 標題：45-60 字，包含主要關鍵詞，吸引點擊
- Meta Description：120-160 字，清楚描述文章內容，包含 CTA

返回 JSON 格式：
{
  "optimizedTitle": "your title here",
  "metaDescription": "your description here"
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

// ─── Main Processing ───────────────────────────────────────────────────────

async function processArticles() {
  console.log("🚀 Phase 3 Batch 1 - SEO 優化執行");
  console.log("=" .repeat(60));
  console.log(`📊 目標文章數: ${ARTICLES.length}\n`);

  const results = loadResults();
  const token = await getWpComToken();

  for (let idx = 0; idx < ARTICLES.length; idx++) {
    const article = ARTICLES[idx];
    const progress = `[${idx + 1}/${ARTICLES.length}]`;

    console.log(`\n${progress} 處理文章 ID: ${article.id}`);
    console.log(`   原標題: ${article.title.substring(0, 50)}...`);

    try {
      // 1. 獲取完整文章數據
      console.log(`   ⏳ 獲取文章數據...`);
      const post = await fetchPost(article.id, token);
      const excerpt = post.excerpt?.rendered || "";

      // 2. 生成 SEO 優化
      console.log(`   🤖 生成 SEO 優化...`);
      const seoData = await generateSEO(post.title.rendered, excerpt);

      // 3. 更新文章
      console.log(`   📝 更新文章元數據...`);
      await updatePost(article.id, seoData, token);

      // 記錄成功結果
      const result = {
        articleId: article.id,
        originalTitle: article.title,
        optimizedTitle: seoData.optimizedTitle,
        metaDescription: seoData.metaDescription,
        status: "success",
        timestamp: new Date().toISOString()
      };
      results.articles.push(result);
      results.summary.success++;

      console.log(`   ✅ 成功！`);
      console.log(`      SEO 標題: ${seoData.optimizedTitle}`);
      console.log(`      Meta 描述: ${seoData.metaDescription.substring(0, 60)}...`);

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
      await new Promise((r) => setTimeout(r, DELAY_MS));
    }
  }

  // 保存最終結果
  saveResults(results);

  // 最終報告
  console.log("\n" + "=" .repeat(60));
  console.log("📈 Phase 3 Batch 1 完成報告");
  console.log("=" .repeat(60));
  console.log(`✅ 成功: ${results.summary.success}/${results.summary.total}`);
  console.log(`❌ 失敗: ${results.summary.failed}/${results.summary.total}`);
  console.log(`\n💾 詳細結果保存: ${OUTPUT_FILE}`);
  console.log(`📊 成功率: ${((results.summary.success / results.summary.total) * 100).toFixed(1)}%\n`);

  // 列出成功的文章
  if (results.summary.success > 0) {
    console.log("✅ 成功的文章：");
    results.articles
      .filter(a => a.status === "success")
      .forEach(a => {
        console.log(`  - #${a.articleId}: ${a.optimizedTitle}`);
      });
  }

  // 列出失敗的文章
  if (results.summary.failed > 0) {
    console.log("\n❌ 失敗的文章：");
    results.articles
      .filter(a => a.status === "failed")
      .forEach(a => {
        console.log(`  - #${a.articleId}: ${a.error}`);
      });
  }
}

// 執行
processArticles().catch((err) => {
  console.error("\n❌ 致命錯誤:", err.message);
  process.exit(1);
});
