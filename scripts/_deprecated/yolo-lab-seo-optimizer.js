#!/usr/bin/env node

/**
 * YOLO LAB SEO Optimizer
 *
 * 自動化優化流量文章的標題和 meta description
 * 策略：只優化 top 流量文章，節省算力
 *
 * 需要：
 *   - WPCOM_TOKEN (WordPress.com API token)
 *   - ANTHROPIC_API_KEY (Claude API key)
 *
 * 運行：
 *   node scripts/yolo-lab-seo-optimizer.js
 */

import Anthropic from "@anthropic-ai/sdk";
import fetch from "node-fetch";

const client = new Anthropic();

// ─── Config ─────────────────────────────────────────────────────────────────
const SITE_ID = 2; // yololab.net
const BLOG_ID = 133512998;
const DOMAIN = "yololab.net";

// Top 流量文章 ID（從統計數據）
const TOP_POSTS = [
  {
    id: 27155,
    title:
      "2026 電影院推薦 | 全台影城殘酷評測：別再只去威秀！這 5 間才是真正的觀影神壇",
    views: 30,
  },
  {
    id: 28183,
    title:
      "湯米巴斯托 Tommy Bastow 深度分析：《幕府將軍》的神父，現在更是 NHK 欽點的「日本通」",
    views: 28,
  },
  {
    id: 32093,
    title: "千萬美金也買不回的真心：Hongkongdoll 崩潰自白，揭露兩段愛情煉獄",
    views: 20,
  },
  {
    id: 30369,
    title:
      "哈利米爾林演技血祭！《皮隆》《Pillion》：披著 BDSM 皮衣的殘酷階級寓言",
    views: 18,
  },
  {
    id: 27412,
    title:
      "Daniel Caesar 2026 Tiny Desk 樂評：從《Son of Spergy》看見浪漫的死與福音的生",
    views: 18,
  },
  {
    id: 30128,
    title: "RINOA 出道黑幕：G 罩杯饒舌歌手下海，背後竟是 IP 社的生死豪賭",
    views: 14,
  },
  {
    id: 31761,
    title: "成本狂降、效率噴發：oh-my-opencode v3.0.0 三巨頭架構深度實測",
    views: 14,
  },
  {
    id: 26090,
    title:
      "七座葛萊美獎! 連續五張專輯獲獎 Sibling Harmony 「同胞和聲」的極致體現 Jacob Collier 家族",
    views: 14,
  },
  {
    id: 31654,
    title: "OpenCode AI 安裝手冊：打造工程師等級的乾淨開發環境",
    views: 14,
  },
  {
    id: 29027,
    title: "YUJU 台北演唱會搶票攻略：Billboard Live 座位圖分析與隱藏成本",
    views: 12,
  },
];

// ─── Helper Functions ───────────────────────────────────────────────────────

async function getWpComAuthToken() {
  const token = process.env.WPCOM_TOKEN;
  if (!token) {
    throw new Error("WPCOM_TOKEN 環境變數未設定");
  }
  return token;
}

async function getPostData(postId) {
  const token = await getWpComAuthToken();

  const response = await fetch(
    `https://public-api.wordpress.com/wp/v2/sites/${BLOG_ID}/posts/${postId}`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    },
  );

  if (!response.ok) {
    throw new Error(`Failed to fetch post ${postId}: ${response.statusText}`);
  }

  return response.json();
}

async function updatePostSEO(postId, seoData) {
  const token = await getWpComAuthToken();

  const response = await fetch(
    `https://public-api.wordpress.com/wp/v2/sites/${BLOG_ID}/posts/${postId}`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        title: seoData.optimizedTitle,
        meta: {
          description: seoData.metaDescription,
        },
      }),
    },
  );

  if (!response.ok) {
    throw new Error(`Failed to update post ${postId}: ${response.statusText}`);
  }

  return response.json();
}

async function generateSEOOptimizations(postData) {
  const prompt = `你是 SEO 專家，專門優化中文內容。

分析以下文章，生成改進的標題和 meta description：

**原始標題：**
${postData.title}

**文章內容摘要：**
${postData.excerpt || "（無摘要）"}

**優化要求：**
1. 標題：45-60 字，包含主關鍵字，吸引點擊
2. Meta Description：120-160 字，自然包含關鍵字，清楚說明內容價值

**回應格式（JSON）：**
{
  "optimizedTitle": "...",
  "metaDescription": "...",
  "rationale": "為什麼這樣優化"
}`;

  const message = await client.messages.create({
    model: "claude-opus-4-6",
    max_tokens: 500,
    messages: [
      {
        role: "user",
        content: prompt,
      },
    ],
  });

  const content = message.content[0];
  if (content.type !== "text") {
    throw new Error("Unexpected response type from Claude");
  }

  try {
    const jsonMatch = content.text.match(/\{[\s\S]*\}/);
    if (!jsonMatch) {
      throw new Error("No JSON found in response");
    }
    return JSON.parse(jsonMatch[0]);
  } catch (error) {
    console.error("Failed to parse Claude response:", content.text);
    throw error;
  }
}

// ─── Main Workflow ──────────────────────────────────────────────────────────

async function main() {
  console.log("\n🚀 YOLO LAB SEO 優化流程 (Top 流量文章批量優化)\n");
  console.log(`📊 將優化 ${TOP_POSTS.length} 篇流量文章\n`);

  const results = {
    success: [],
    failed: [],
    skipped: [],
  };

  for (let i = 0; i < TOP_POSTS.length; i++) {
    const post = TOP_POSTS[i];
    const progress = `[${i + 1}/${TOP_POSTS.length}]`;

    try {
      console.log(`${progress} 正在處理文章 #${post.id}...`);

      // 1. 取得原始文章數據
      const postData = await getPostData(post.id);

      // 2. 用 Claude 生成優化建議
      console.log(`   └─ 生成 SEO 優化建議...`);
      const seoOptimization = await generateSEOOptimizations(postData);

      // 3. 更新到 WordPress.com
      console.log(`   └─ 更新文章...`);
      await updatePostSEO(post.id, seoOptimization);

      // 記錄結果
      results.success.push({
        id: post.id,
        originalTitle: post.title,
        optimizedTitle: seoOptimization.optimizedTitle,
        metaDescription: seoOptimization.metaDescription,
      });

      console.log(`✅ 文章 #${post.id} 優化完成`);
      console.log(
        `   標題: ${seoOptimization.optimizedTitle.substring(0, 50)}...`,
      );
      console.log(
        `   描述: ${seoOptimization.metaDescription.substring(0, 60)}...`,
      );

      // 速率限制（避免 API 超限）
      await new Promise((resolve) => setTimeout(resolve, 1000));
    } catch (error) {
      console.error(`❌ 文章 #${post.id} 失敗: ${error.message}`);
      results.failed.push({
        id: post.id,
        error: error.message,
      });
    }
  }

  // ─── 輸出報告 ───────────────────────────────────────────────────────────

  console.log("\n" + "=".repeat(70));
  console.log("📈 SEO 優化完成報告");
  console.log("=".repeat(70) + "\n");

  console.log(`✅ 成功優化: ${results.success.length} 篇`);
  console.log(`❌ 失敗: ${results.failed.length} 篇`);
  console.log(`⏭️  跳過: ${results.skipped.length} 篇\n`);

  if (results.success.length > 0) {
    console.log("成功的文章：");
    results.success.forEach((item) => {
      console.log(`\n  #${item.id}`);
      console.log(`  原標題: ${item.originalTitle.substring(0, 50)}...`);
      console.log(`  新標題: ${item.optimizedTitle}`);
      console.log(`  Meta:  ${item.metaDescription.substring(0, 80)}...`);
    });
  }

  if (results.failed.length > 0) {
    console.log("\n失敗的文章：");
    results.failed.forEach((item) => {
      console.log(`  #${item.id}: ${item.error}`);
    });
  }

  console.log("\n💡 提示：所有更改已同步到 https://yololab.net");
  console.log("📊 建議在 Google Search Console 中重新爬取受影響的頁面\n");
}

main().catch(console.error);
