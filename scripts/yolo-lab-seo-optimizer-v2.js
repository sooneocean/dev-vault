#!/usr/bin/env node

/**
 * YOLO LAB SEO Optimizer v2
 *
 * 用 Claude API 生成優化方案，用 MCP 工具更新
 * 無需手動 token 設置
 *
 * 運行：
 *   export ANTHROPIC_API_KEY="sk-ant-..."
 *   node scripts/yolo-lab-seo-optimizer-v2.js
 */

import Anthropic from "@anthropic-ai/sdk";
import { execSync } from "child_process";

const client = new Anthropic();

// Top 流量文章（來自統計數據）
const TOP_POSTS = [
  {
    id: 27155,
    title:
      "2026 電影院推薦 | 全台影城殘酷評測：別再只去威秀！這 5 間才是真正的觀影神壇",
    views: 30,
    url: "https://yololab.net/archives/movie-theater-recommendations-2026",
  },
  {
    id: 28183,
    title:
      "湯米巴斯托 Tommy Bastow 深度分析：《幕府將軍》的神父，現在更是 NHK 欽點的「日本通」",
    views: 28,
    url: "https://yololab.net/archives/tommy-bastow-shogun-father-martin-alvito-bakebake-actor-profile",
  },
  {
    id: 32093,
    title: "千萬美金也買不回的真心：Hongkongdoll 崩潰自白，揭露兩段愛情煉獄",
    views: 20,
    url: "https://yololab.net/archives/hongkongdoll-creator-economy-relationship-betrayal",
  },
  {
    id: 30369,
    title:
      "哈利米爾林演技血祭！《皮隆》《Pillion》：披著 BDSM 皮衣的殘酷階級寓言",
    views: 18,
    url: "https://yololab.net/archives/pillion-movie-review-harry-melling-alexander-skarsgard",
  },
  {
    id: 27412,
    title:
      "Daniel Caesar 2026 Tiny Desk 樂評：從《Son of Spergy》看見浪漫的死與福音的生",
    views: 18,
    url: "https://yololab.net/archives/reviews-daniel-caesar-tiny-desk-2026-son-of-spergy-meaning",
  },
  {
    id: 30128,
    title: "RINOA 出道黑幕：G 罩杯饒舌歌手下海，背後竟是 IP 社的生死豪賭",
    views: 14,
    url: "https://yololab.net/archives/rinoa-rapper-ideapocket-debut-analysis",
  },
  {
    id: 31761,
    title: "成本狂降、效率噴發：oh-my-opencode v3.0.0 三巨頭架構深度實測",
    views: 14,
    url: "https://yololab.net/archives/oh-my-opencode-v3-orchestration-revolution-review",
  },
  {
    id: 26090,
    title:
      "七座葛萊美獎! 連續五張專輯獲獎 Sibling Harmony 「同胞和聲」的極致體現 Jacob Collier 家族",
    views: 14,
    url: "https://yololab.net/archives/jacob-collier-susan-collier-musical-origins-harmony",
  },
  {
    id: 31654,
    title: "OpenCode AI 安裝手冊：打造工程師等級的乾淨開發環境",
    views: 14,
    url: "https://yololab.net/archives/opencode-ai-installation-guide-node-bun",
  },
  {
    id: 29027,
    title: "YUJU 台北演唱會搶票攻略：Billboard Live 座位圖分析與隱藏成本",
    views: 12,
    url: "https://yololab.net/archives/yuju-2026-billboard-live-taipei-tickets-seating-guide",
  },
];

// 生成 SEO 優化方案
async function generateSEOOptimizations(title) {
  const prompt = `你是中文 SEO 專家。

原始標題：
${title}

任務：生成改進的標題和 meta description

要求：
1. 標題：45-60 字，包含主關鍵字，吸引點擊，保留原意但更優化
2. Meta Description：120-160 字，自然包含關鍵字，描述內容價值

回應格式（JSON）：
{
  "optimizedTitle": "...",
  "metaDescription": "..."
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

// 更新文章（用 obsidian-agent CLI）
async function updatePostViaCLI(postId, optimizedTitle, metaDescription) {
  // 準備 JSON 資料
  const updateData = {
    title: optimizedTitle,
    meta: {
      description: metaDescription,
    },
  };

  // 保存臨時檔案
  const tempFile = `/tmp/seo_update_${postId}.json`;
  try {
    // 因為直接用 curl 更新 WordPress.com API
    const curlCmd = `curl -s -X POST \\
      'https://public-api.wordpress.com/wp/v2/sites/133512998/posts/${postId}' \\
      -H 'Authorization: Bearer ${process.env.WPCOM_TOKEN}' \\
      -H 'Content-Type: application/json' \\
      -d '${JSON.stringify(updateData).replace(/'/g, "'\\''")}'`;

    const result = execSync(curlCmd, { encoding: "utf-8" });
    const response = JSON.parse(result);

    return {
      success: true,
      postId,
      updatedTitle: response.title?.rendered || optimizedTitle,
    };
  } catch (error) {
    return {
      success: false,
      postId,
      error: error.message,
    };
  }
}

// 主流程
async function main() {
  console.log("\n🚀 YOLO LAB SEO 優化 v2 (Top 10 流量文章)\n");

  // 檢查 API key
  if (!process.env.ANTHROPIC_API_KEY) {
    console.error("❌ ANTHROPIC_API_KEY 未設定");
    console.log("運行：export ANTHROPIC_API_KEY='sk-ant-...'");
    process.exit(1);
  }

  const results = {
    success: [],
    failed: [],
  };

  for (let i = 0; i < TOP_POSTS.length; i++) {
    const post = TOP_POSTS[i];
    const progress = `[${i + 1}/${TOP_POSTS.length}]`;

    try {
      console.log(`${progress} 正在分析文章 #${post.id}...`);

      // 1. 用 Claude 生成優化方案
      const seoData = await generateSEOOptimizations(post.title);

      console.log(`   ✓ 生成優化方案`);
      console.log(`   新標題: ${seoData.optimizedTitle.substring(0, 50)}...`);

      // 2. 記錄結果（暫不實際更新，先展示方案）
      results.success.push({
        id: post.id,
        url: post.url,
        views: post.views,
        originalTitle: post.title,
        optimizedTitle: seoData.optimizedTitle,
        metaDescription: seoData.metaDescription,
      });

      console.log(`✅ 完成\n`);

      // 速率限制
      await new Promise((resolve) => setTimeout(resolve, 1000));
    } catch (error) {
      console.error(`❌ 文章 #${post.id} 失敗: ${error.message}\n`);
      results.failed.push({
        id: post.id,
        error: error.message,
      });
    }
  }

  // ─── 輸出報告 ───────────────────────────────────────────────────────────

  console.log("\n" + "=".repeat(80));
  console.log("📊 SEO 優化方案報告");
  console.log("=".repeat(80) + "\n");

  console.log(`✅ 成功生成: ${results.success.length} 篇\n`);

  if (results.success.length > 0) {
    results.success.forEach((item) => {
      console.log(`📄 #${item.id} | ${item.views} views`);
      console.log(`   原標題: ${item.originalTitle}`);
      console.log(`   新標題: ${item.optimizedTitle}`);
      console.log(`   Meta:  ${item.metaDescription.substring(0, 80)}...`);
      console.log(`   URL:   ${item.url}\n`);
    });
  }

  if (results.failed.length > 0) {
    console.log("\n❌ 失敗：");
    results.failed.forEach((item) => {
      console.log(`  #${item.id}: ${item.error}`);
    });
  }

  // 保存報告到檔案
  const reportPath = "./seo-optimization-report.json";
  const fs = await import("fs");
  fs.writeFileSync(reportPath, JSON.stringify(results, null, 2));

  console.log(`\n💾 詳細報告已保存到: ${reportPath}`);
  console.log(
    `\n📋 下一步：審核上述優化方案後，使用 WordPress.com 編輯器手動應用或配置 WPCOM_TOKEN 自動更新`,
  );
}

main().catch(console.error);
