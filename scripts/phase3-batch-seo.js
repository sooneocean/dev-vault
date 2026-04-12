#!/usr/bin/env node

/**
 * Phase 3 SEO Batch Optimizer - yololab.net
 *
 * 處理文章 34800-34701（100 篇）
 * 並行 API 調用，自動恢復進度
 */

import Anthropic from "@anthropic-ai/sdk";
import fetch from "node-fetch";
import fs from "fs";

const client = new Anthropic();

const BLOG_ID = 133512998;
const PHASE_START = 34800;
const PHASE_END = 34701;
const BATCH_SIZE = 10; // 並行調用
const DELAY_MS = 1500;
const PROGRESS_FILE = "phase3-progress.json";

// ─── Progress Tracking ──────────────────────────────────────────────────────

function loadProgress() {
  try {
    if (fs.existsSync(PROGRESS_FILE)) {
      return JSON.parse(fs.readFileSync(PROGRESS_FILE, "utf-8"));
    }
  } catch (e) {
    console.log("⚠️  進度文件損壞，從頭開始\n");
  }
  return {
    processed: 0,
    success: [],
    timeout: [],
    failed: [],
    last_batch: Math.ceil((PHASE_START - PHASE_END) / BATCH_SIZE),
  };
}

function saveProgress(progress) {
  fs.writeFileSync(PROGRESS_FILE, JSON.stringify(progress, null, 2));
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
  const response = await fetch(
    `https://public-api.wordpress.com/wp/v2/sites/${BLOG_ID}/posts/${postId}?context=edit`,
    { headers: { Authorization: `Bearer ${token}` } }
  );
  if (!response.ok) throw new Error(`API error: ${response.statusText}`);
  return response.json();
}

async function updatePost(postId, seoData, token) {
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
}

// ─── SEO Generation ─────────────────────────────────────────────────────────

async function generateSEO(title, excerpt) {
  const message = await client.messages.create({
    model: "claude-opus-4-6",
    max_tokens: 250,
    messages: [
      {
        role: "user",
        content: `快速優化中文 SEO 標題和描述。

**原標題：** ${title}
**摘要：** ${excerpt || "無"}

返回 JSON：{"optimizedTitle": "45-60字", "metaDescription": "120-160字"}`,
      },
    ],
  });

  const text = message.content[0].text;
  const match = text.match(/\{[\s\S]*\}/);
  if (!match) throw new Error("No JSON in response");
  return JSON.parse(match[0]);
}

// ─── Main ───────────────────────────────────────────────────────────────────

async function runPhase3() {
  console.log("🚀 Phase 3: SEO 批量優化\n");
  console.log(`📊 目標範圍: ${PHASE_START} → ${PHASE_END} (100 篇)\n`);

  const progress = loadProgress();
  const token = await getWpComToken();

  let currentId = PHASE_START;
  let batchNum = 0;

  while (currentId >= PHASE_END) {
    batchNum++;
    const batchIds = [];

    // 構建批次 ID 列表
    for (let i = 0; i < BATCH_SIZE && currentId >= PHASE_END; i++) {
      batchIds.push(currentId);
      currentId--;
    }

    console.log(`\n📦 批次 #${batchNum}: [${batchIds.join(", ")}]`);

    // 並行執行
    const results = await Promise.allSettled(
      batchIds.map(async (id) => {
        try {
          // 1. Fetch post data
          console.log(`  ⏳ 文章 #${id}...`);
          const post = await fetchPost(id, token);

          // 2. Generate SEO
          const seoData = await generateSEO(post.title.rendered, post.excerpt.rendered);

          // 3. Update post
          await updatePost(id, seoData, token);

          return {
            id,
            status: "success",
            title: seoData.optimizedTitle,
            desc: seoData.metaDescription,
          };
        } catch (error) {
          return {
            id,
            status: error.message.includes("timeout") ? "timeout" : "failed",
            error: error.message,
          };
        }
      })
    );

    // 處理結果
    let batchSuccess = 0;
    for (const result of results) {
      if (result.status === "fulfilled") {
        const data = result.value;
        if (data.status === "success") {
          console.log(`  ✅ #${data.id}: ${data.title.substring(0, 40)}...`);
          progress.success.push(data.id);
          batchSuccess++;
        } else if (data.status === "timeout") {
          console.log(`  ⏱️  #${data.id}: Timeout (可能已更新)`);
          progress.timeout.push(data.id);
        } else {
          console.log(`  ❌ #${data.id}: ${data.error}`);
          progress.failed.push({ id: data.id, error: data.error });
        }
      }
    }

    progress.processed += batchSuccess;
    console.log(`   → 本批成功: ${batchSuccess}/${batchIds.length}`);

    // 保存進度
    saveProgress(progress);

    // 延遲
    if (currentId >= PHASE_END) {
      await new Promise((r) => setTimeout(r, DELAY_MS));
    }
  }

  // 最終報告
  console.log("\n" + "=".repeat(60));
  console.log("📈 Phase 3 完成報告");
  console.log("=".repeat(60));
  console.log(`\n✅ 成功: ${progress.success.length}`);
  console.log(`⏱️  超時: ${progress.timeout.length} (驗證中...)`);
  console.log(`❌ 失敗: ${progress.failed.length}\n`);

  if (progress.timeout.length > 0) {
    console.log("🔍 驗證超時文章...");
    for (const id of progress.timeout.slice(0, 3)) {
      const post = await fetchPost(id, token);
      const hasMeta =
        post.meta?.jetpack_seo_html_title || post.meta?.advanced_seo_description;
      console.log(`  #${id}: ${hasMeta ? "✅ 已更新" : "❌ 未更新"}`);
    }
  }

  console.log(`\n💾 進度保存: ${PROGRESS_FILE}`);
  console.log(`📊 下一步: Phase 4 (34700-34601)`);
}

runPhase3().catch((err) => {
  console.error("\n❌ 錯誤:", err.message);
  process.exit(1);
});
