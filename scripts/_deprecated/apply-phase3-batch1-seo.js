#!/usr/bin/env node

/**
 * Apply Phase 3 Batch 1 SEO Optimizations
 * Uses MCP tool to update WordPress.com posts with SEO metadata
 */

import fs from "fs";

const SITE_ID = "133512998";
const DATA_FILE = "scripts/phase3-batch1-seo-data.json";

const data = JSON.parse(fs.readFileSync(DATA_FILE, "utf-8"));

console.log("🚀 Phase 3 Batch 1 - SEO 應用執行");
console.log("=" .repeat(70));
console.log(`📊 將應用 ${data.articles.length} 篇文章的 SEO 優化\n`);

// 生成 MCP 調用指令
console.log("📋 MCP 工具調用指令序列：\n");

data.articles.forEach((article, idx) => {
  const mcp_call = {
    action: "execute",
    operation: "posts.update",
    wpcom_site: SITE_ID,
    params: {
      id: article.id,
      meta: {
        jetpack_seo_html_title: article.optimizedTitle,
        advanced_seo_description: article.metaDescription
      },
      user_confirmed: "yes"
    }
  };

  console.log(`${idx + 1}. 文章 #${article.id}`);
  console.log(`   原標題: ${article.originalTitle}`);
  console.log(`   SEO 標題: ${article.optimizedTitle}`);
  console.log(`   Meta 描述: ${article.metaDescription}`);
  console.log(`\n   MCP 調用:`);
  console.log(`   ────────────────────────────────────────────────────────────`);
  console.log(`   mcp__wpcom-mcp__wpcom-mcp-content-authoring`);
  console.log(`   {`);
  console.log(`     "action": "${mcp_call.action}",`);
  console.log(`     "operation": "${mcp_call.operation}",`);
  console.log(`     "wpcom_site": "${mcp_call.wpcom_site}",`);
  console.log(`     "params": {`);
  console.log(`       "id": ${mcp_call.params.id},`);
  console.log(`       "meta": {`);
  console.log(`         "jetpack_seo_html_title": "${mcp_call.params.meta.jetpack_seo_html_title}",`);
  console.log(`         "advanced_seo_description": "${mcp_call.params.meta.advanced_seo_description}"`);
  console.log(`       },`);
  console.log(`       "user_confirmed": "${mcp_call.params.user_confirmed}"`);
  console.log(`     }`);
  console.log(`   }`);
  console.log("");
});

console.log("=" .repeat(70));
console.log("💾 MCP 調用指令已生成");
console.log("⏭️  請使用上述 MCP 調用逐篇應用 SEO 優化");
