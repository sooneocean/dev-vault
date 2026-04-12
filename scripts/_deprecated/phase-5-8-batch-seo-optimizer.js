#!/usr/bin/env node

/**
 * Phase 5-8 SEO Batch Optimizer - yololab.net
 *
 * 處理文章 34600-34201（400 篇）
 * 分 4 個 Phase，各 100 篇，每 Phase 分 10 批，每批 10 篇
 * 並行 API 調用，自動恢復進度
 */

import Anthropic from "@anthropic-ai/sdk";
import fetch from "node-fetch";
import fs from "fs";

const client = new Anthropic();

const BLOG_ID = 133512998;

// Phase 定義
const PHASES = {
  5: { start: 34600, end: 34501, pages: "19-28" },
  6: { start: 34500, end: 34401, pages: "29-38" },
  7: { start: 34400, end: 34301, pages: "39-48" },
  8: { start: 34300, end: 34201, pages: "49-58" },
};

const BATCH_SIZE = 10; // 每批 10 篇
const DELAY_MS = 1500; // 批次間延遲

// ─── Progress Tracking ──────────────────────────────────────────────────────

function getProgressFile(phase) {
  return `phase${phase}-progress.json`;
}

function loadProgress(phase) {
  const file = getProgressFile(phase);
  try {
    if (fs.existsSync(file)) {
      const data = JSON.parse(fs.readFileSync(file, "utf-8"));
      console.log(`✅ 載入進度: ${file}`);
      return data;
    }
  } catch (e) {
    console.log(`⚠️  進度文件損壞，從頭開始\n`);
  }
  return {
    phase,
    processed: 0,
    success: [],
    timeout: [],
    failed: [],
    startTime: new Date().toISOString(),
  };
}

function saveProgress(progress) {
  const file = getProgressFile(progress.phase);
  fs.writeFileSync(file, JSON.stringify(progress, null, 2));
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

// ─── Phase Processor ───────────────────────────────────────────────────────

async function processPhase(phaseNum, token) {
  const phaseConfig = PHASES[phaseNum];
  if (!phaseConfig) {
    throw new Error(`❌ 不存在 Phase ${phaseNum}`);
  }

  console.log("\n" + "=".repeat(70));
  console.log(`🚀 Phase ${phaseNum}: SEO 批量優化`);
  console.log("=".repeat(70));
  console.log(`📊 目標範圍: ${phaseConfig.start} → ${phaseConfig.end} (100 篇)`);
  console.log(`📄 頁碼: ${phaseConfig.pages}\n`);

  const progress = loadProgress(phaseNum);

  let currentId = phaseConfig.start;
  let batchNum = 0;

  while (currentId >= phaseConfig.end) {
    batchNum++;
    const batchIds = [];

    // 構建批次 ID 列表
    for (let i = 0; i < BATCH_SIZE && currentId >= phaseConfig.end; i++) {
      batchIds.push(currentId);
      currentId--;
    }

    console.log(
      `\n📦 批次 #${batchNum.toString().padStart(2, " ")}: [${batchIds
        .map((id) => id.toString().padStart(5, " "))
        .join(", ")}]`
    );

    // 並行執行
    const results = await Promise.allSettled(
      batchIds.map(async (id) => {
        try {
          // 1. Fetch post data
          const post = await fetchPost(id, token);

          // 2. Generate SEO
          const seoData = await generateSEO(
            post.title.rendered,
            post.excerpt.rendered
          );

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
          console.log(
            `  ✅ #${data.id}: ${data.title.substring(0, 35).padEnd(35)}...`
          );
          progress.success.push(data.id);
          batchSuccess++;
        } else if (data.status === "timeout") {
          console.log(
            `  ⏱️  #${data.id}: Timeout (可能已更新)`.padEnd(45)
          );
          progress.timeout.push(data.id);
        } else {
          console.log(`  ❌ #${data.id}: ${data.error}`.padEnd(45));
          progress.failed.push({ id: data.id, error: data.error });
        }
      } else {
        console.log(`  ❌ #?: Promise rejected`);
      }
    }

    progress.processed += batchSuccess;
    console.log(
      `   → 本批成功: ${batchSuccess}/${batchIds.length} | 累計: ${progress.success.length}`
    );

    // 保存進度
    saveProgress(progress);

    // 延遲
    if (currentId >= phaseConfig.end) {
      await new Promise((r) => setTimeout(r, DELAY_MS));
    }
  }

  // Phase 完成報告
  console.log("\n" + "-".repeat(70));
  console.log(`📈 Phase ${phaseNum} 完成報告`);
  console.log("-".repeat(70));
  console.log(`✅ 成功: ${progress.success.length.toString().padStart(3)}`);
  console.log(
    `⏱️  超時: ${progress.timeout.length
      .toString()
      .padStart(3)} (驗證中...)`
  );
  console.log(`❌ 失敗: ${progress.failed.length.toString().padStart(3)}\n`);

  return progress;
}

// ─── Main ───────────────────────────────────────────────────────────────────

async function runPhases() {
  console.log("\n🌟 Phase 5-8 大規模 SEO 優化（400 篇文章）\n");

  const token = await getWpComToken();
  const allResults = {};
  const startTime = Date.now();

  // 執行每個 Phase
  for (const phaseNum of [5, 6, 7, 8]) {
    allResults[phaseNum] = await processPhase(phaseNum, token);

    // Phase 間延遲
    if (phaseNum < 8) {
      await new Promise((r) => setTimeout(r, DELAY_MS * 2));
    }
  }

  // 總體報告
  const duration = ((Date.now() - startTime) / 1000 / 60).toFixed(2);

  console.log("\n" + "=".repeat(70));
  console.log("📊 Phase 5-8 最終統計");
  console.log("=".repeat(70) + "\n");

  let totalSuccess = 0;
  let totalTimeout = 0;
  let totalFailed = 0;

  for (const phaseNum of [5, 6, 7, 8]) {
    const result = allResults[phaseNum];
    totalSuccess += result.success.length;
    totalTimeout += result.timeout.length;
    totalFailed += result.failed.length;

    console.log(
      `Phase ${phaseNum}: ✅ ${result.success.length
        .toString()
        .padStart(3)} | ⏱️ ${result.timeout.length
        .toString()
        .padStart(3)} | ❌ ${result.failed.length.toString().padStart(3)}`
    );
  }

  console.log("\n" + "-".repeat(70));
  console.log(`🎉 總計: ✅ ${totalSuccess} | ⏱️ ${totalTimeout} | ❌ ${totalFailed}`);
  console.log(`⏱️  耗時: ${duration} 分鐘`);
  console.log(
    `\n成功率: ${((totalSuccess / 400) * 100).toFixed(1)}% (${totalSuccess}/400)`
  );
  console.log(`失敗率: ${((totalFailed / 400) * 100).toFixed(1)}% (${totalFailed}/400)\n`);

  // 導出進度文件列表
  const progressFiles = [5, 6, 7, 8].map((p) => getProgressFile(p));
  console.log(`💾 進度文件：`);
  progressFiles.forEach((f) => console.log(`   - ${f}`));

  console.log(`\n📝 詳細報告可檢查各 Phase 的 JSON 文件\n`);

  // 如有重大失敗，提示重試
  if (totalFailed > 5) {
    console.log(
      `⚠️  有 ${totalFailed} 篇失敗，建議檢查日誌並重試\n`
    );
  }
}

runPhases().catch((err) => {
  console.error("\n❌ 致命錯誤:", err.message);
  process.exit(1);
});
