#!/usr/bin/env node

/**
 * Phase 4 Apply SEO to WordPress.com
 *
 * 將生成的 SEO 優化數據應用到 WordPress.com 文章
 * 包括：Meta 標題、Meta Description、Schema Markup、OG Tags
 *
 * 使用方式：
 * export WPCOM_TOKEN=your_token
 * node phase4-apply-seo-to-wordpress.js [--demo] [--dry-run]
 */

import fetch from "node-fetch";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const OUTPUT_DIR = path.join(__dirname, "../seo-optimization-output");

const args = process.argv.slice(2);
const demoMode = args.includes("--demo");
const dryRun = args.includes("--dry-run");

// ─── Configuration ────────────────────────────────────────────────────────

const BLOG_ID = 133512998;
const BATCH_SIZE = 5; // 每批 5 篇（API 限制）
const DELAY_MS = 3000;

// ─── Utilities ────────────────────────────────────────────────────────────

function log(msg, level = "info") {
  const timestamp = new Date().toISOString().split("T")[1].slice(0, 8);
  const prefix = {
    info: "ℹ️",
    success: "✓",
    error: "❌",
    warning: "⚠️",
  }[level];
  console.log(`[${timestamp}] ${prefix} ${msg}`);
}

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function getWpComToken() {
  const token = process.env.WPCOM_TOKEN;
  if (!token) {
    throw new Error(
      "❌ 缺少 WPCOM_TOKEN 環境變數\n" +
      "   請運行: export WPCOM_TOKEN=your_token"
    );
  }
  return token;
}

// ─── Load SEO Data ────────────────────────────────────────────────────────

function loadSeoData() {
  const data = {
    meta: {},
    schema: {},
    og: {},
  };

  // 載入 Meta 數據
  const metaFile = path.join(OUTPUT_DIR, "meta_optimization_results.json");
  if (fs.existsSync(metaFile)) {
    const metaData = JSON.parse(fs.readFileSync(metaFile, "utf-8"));
    metaData.articles.forEach(a => {
      data.meta[a.id] = a.meta;
    });
    log(`已載入 ${Object.keys(data.meta).length} 篇文章的 Meta 數據`);
  } else {
    log(`⚠️ 未找到 Meta 數據文件`);
  }

  // 載入 Schema 數據
  const schemaFile = path.join(OUTPUT_DIR, "schema_optimization_results.json");
  if (fs.existsSync(schemaFile)) {
    const schemaData = JSON.parse(fs.readFileSync(schemaFile, "utf-8"));
    schemaData.articles.forEach(a => {
      data.schema[a.id] = a.schema;
    });
    log(`已載入 ${Object.keys(data.schema).length} 篇文章的 Schema 數據`);
  } else {
    log(`⚠️ 未找到 Schema 數據文件`);
  }

  // 載入 OG 數據
  const ogFile = path.join(OUTPUT_DIR, "og_optimization_results.json");
  if (fs.existsSync(ogFile)) {
    const ogData = JSON.parse(fs.readFileSync(ogFile, "utf-8"));
    ogData.articles.forEach(a => {
      data.og[a.id] = a.og;
    });
    log(`已載入 ${Object.keys(data.og).length} 篇文章的 OG Tags 數據`);
  } else {
    log(`⚠️ 未找到 OG Tags 數據文件`);
  }

  return data;
}

// ─── WordPress.com API ────────────────────────────────────────────────────

async function updatePostMetadata(postId, token, metadata) {
  if (dryRun) {
    log(`[DRY-RUN] 將更新文章 ${postId} 的元數據`, "info");
    return { success: true };
  }

  try {
    const url = `https://public-api.wordpress.com/rest/v1.1/sites/${BLOG_ID}/posts/${postId}`;

    const response = await fetch(url, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(metadata),
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`API 錯誤 ${response.status}: ${error}`);
    }

    return { success: true };
  } catch (error) {
    log(`❌ 更新文章 ${postId} 失敗: ${error.message}`, "error");
    return { success: false, error: error.message };
  }
}

// ─── Build Metadata Update ────────────────────────────────────────────────

function buildMetadataUpdate(postId, seoData) {
  const metadata = {};

  // Meta 標題和描述（Yoast SEO）
  if (seoData.meta) {
    metadata._yoast_wpseo_title = seoData.meta.optimizedTitle || "";
    metadata._yoast_wpseo_metadesc = seoData.meta.metaDescription || "";
  }

  // Schema Markup
  if (seoData.schema) {
    metadata._yoast_wpseo_schema = JSON.stringify(seoData.schema);
  }

  // OG Tags
  if (seoData.og) {
    // WordPress 使用 jetpack_sharing_og_* 或直接的 og:* meta
    Object.entries(seoData.og).forEach(([key, value]) => {
      // 轉換為 WordPress meta key 格式
      const metaKey = key.replace(/:/g, "_");
      metadata[`_${metaKey}`] = value;
    });
  }

  return metadata;
}

// ─── Main Processing ──────────────────────────────────────────────────────

async function main() {
  log(`\n════════════════════════════════════════`);
  log(`Phase 4 Apply SEO to WordPress.com`);
  log(`════════════════════════════════════════`);
  log(`Dry-Run 模式: ${dryRun ? "是" : "否"}`);
  log(`演示模式: ${demoMode ? "是" : "否"}`);

  try {
    const token = await getWpComToken();
    const seoData = loadSeoData();

    // 收集所有要更新的文章 ID
    const articleIds = new Set([
      ...Object.keys(seoData.meta).map(Number),
      ...Object.keys(seoData.schema).map(Number),
      ...Object.keys(seoData.og).map(Number),
    ]);

    const articles = Array.from(articleIds);

    if (demoMode) {
      articles.length = Math.min(2, articles.length);
      log(`演示模式：${articles.length} 篇文章`);
    } else {
      log(`準備更新 ${articles.length} 篇文章`);
    }

    const results = {
      timestamp: new Date().toISOString(),
      totalArticles: articles.length,
      updated: 0,
      failed: 0,
      skipped: 0,
      details: [],
    };

    // 分批更新
    for (let i = 0; i < articles.length; i += BATCH_SIZE) {
      const batchNum = Math.floor(i / BATCH_SIZE) + 1;
      const batch = articles.slice(i, i + BATCH_SIZE);
      const totalBatches = Math.ceil(articles.length / BATCH_SIZE);

      log(`\n批次 ${batchNum}/${totalBatches} (${batch.length} 篇)`);

      for (const postId of batch) {
        const articleSeoData = {
          meta: seoData.meta[postId],
          schema: seoData.schema[postId],
          og: seoData.og[postId],
        };

        // 構建元數據
        const metadata = buildMetadataUpdate(postId, articleSeoData);

        // 執行更新
        const result = await updatePostMetadata(postId, token, metadata);

        if (result.success) {
          results.updated++;
          log(`✓ 文章 ${postId} 已更新`);
        } else {
          results.failed++;
          log(`❌ 文章 ${postId} 更新失敗: ${result.error}`, "error");
        }

        results.details.push({
          postId,
          success: result.success,
          error: result.error,
        });

        // 避免速率限制
        await sleep(DELAY_MS);
      }

      // 批次間延遲
      if (i + BATCH_SIZE < articles.length) {
        log(`批次間延遲 5 秒...`);
        await sleep(5000);
      }
    }

    // 保存結果報告
    const reportFile = path.join(OUTPUT_DIR, "PHASE4_APPLICATION_REPORT.json");
    fs.writeFileSync(reportFile, JSON.stringify(results, null, 2));

    log(`\n════════════════════════════════════════`);
    log(`✓ 應用完成`, "success");
    log(`════════════════════════════════════════`);
    log(`已更新: ${results.updated}/${articles.length}`);
    log(`失敗: ${results.failed}`);
    log(`\n報告已保存: ${reportFile}`);

  } catch (error) {
    log(`致命錯誤: ${error.message}`, "error");
    process.exit(1);
  }
}

main();
