#!/usr/bin/env node

/**
 * YOLO LAB SEO 直接应用脚本
 * 使用 WordPress REST API 直接更新文章
 */

import fetch from "node-fetch";
import fs from "fs";

// 配置
const CONFIG = {
  siteUrl: "https://yololab.net",
  wpAdminUrl: "https://yololab.net/wp-admin",
  email: "yololab.life@gmail.com",
  password: "yololab4ever",
  reportFile: "./seo-optimization-output/seo-report-2025-1775373361211.json",
};

// 加载优化报告
function loadReport() {
  if (!fs.existsSync(CONFIG.reportFile)) {
    console.error("❌ 找不到报告文件:", CONFIG.reportFile);
    process.exit(1);
  }
  return JSON.parse(fs.readFileSync(CONFIG.reportFile, "utf-8"));
}

// 方法 1：尝试基本认证 (WordPress REST API)
async function tryBasicAuth() {
  console.log("🔐 尝试基本认证方式...\n");

  const credentials = Buffer.from(
    `${CONFIG.email}:${CONFIG.password}`
  ).toString("base64");
  const headers = {
    Authorization: `Basic ${credentials}`,
    "Content-Type": "application/json",
  };

  try {
    // 测试连接
    const testUrl = `${CONFIG.siteUrl}/wp-json/wp/v2/posts?per_page=1`;
    const response = await fetch(testUrl, { headers });

    if (response.ok) {
      console.log("✅ 认证成功！");
      return headers;
    } else if (response.status === 401) {
      console.log("⚠️  基本认证未被接受 (HTTP 401)");
      return null;
    } else {
      console.log(`⚠️  连接失败 (HTTP ${response.status})`);
      return null;
    }
  } catch (error) {
    console.log("⚠️  连接错误:", error.message);
    return null;
  }
}

// 方法 2：应用密码认证 (如果用户已生成应用密码)
async function tryApplicationPassword() {
  console.log("🔐 尝试应用密码方式...\n");

  const credentials = Buffer.from(
    `${CONFIG.email}:${CONFIG.password}`
  ).toString("base64");
  const headers = {
    Authorization: `Basic ${credentials}`,
    "Content-Type": "application/json",
  };

  try {
    const testUrl = `${CONFIG.siteUrl}/wp-json/wp/v2/users/me`;
    const response = await fetch(testUrl, { headers });

    if (response.ok) {
      const user = await response.json();
      console.log(`✅ 认证成功！用户: ${user.name}`);
      return headers;
    }
    return null;
  } catch (error) {
    return null;
  }
}

// 更新单篇文章的 Yoast SEO 数据
async function updateArticle(articleId, optimization, headers) {
  const meta = optimization.recommendations?.meta || {};
  const schema = optimization.recommendations?.schema || {};
  const og = optimization.recommendations?.og || {};

  const updateData = {
    meta: {
      _yoast_wpseo_title: meta.optimizedTitle || "",
      _yoast_wpseo_metadesc: meta.metaDescription || "",
      _yoast_wpseo_focuskw: (meta.primaryKeywords?.[0] || "").substring(0, 100),
    },
  };

  // 如果有 Schema，添加到自定义 HTML
  if (schema.schema) {
    updateData.meta._yoast_wpseo_schema_article = JSON.stringify(schema.schema);
  }

  // OG Tags
  if (og["og:title"]) {
    updateData.meta._yoast_wpseo_og_title = og["og:title"];
  }
  if (og["og:description"]) {
    updateData.meta._yoast_wpseo_og_description = og["og:description"];
  }

  const url = `${CONFIG.siteUrl}/wp-json/wp/v2/posts/${articleId}`;

  try {
    const response = await fetch(url, {
      method: "POST",
      headers,
      body: JSON.stringify(updateData),
    });

    if (response.ok) {
      return true;
    } else {
      const error = await response.text();
      console.error(`   错误: ${response.status} - ${error.substring(0, 100)}`);
      return false;
    }
  } catch (error) {
    console.error(`   异常: ${error.message}`);
    return false;
  }
}

// 主程序
async function main() {
  console.log("\n");
  console.log("╔════════════════════════════════════════════════════════════╗");
  console.log("║  YOLO LAB SEO 直接应用 - WordPress REST API 方式          ║");
  console.log("╚════════════════════════════════════════════════════════════╝");
  console.log("\n");

  // 加载报告
  console.log("📄 加载优化报告...");
  const report = loadReport();
  console.log(`✅ 加载完成：${report.articles.length} 篇文章\n`);

  // 尝试认证
  console.log("🔐 尝试 REST API 认证...\n");
  let headers = await tryBasicAuth();

  if (!headers) {
    headers = await tryApplicationPassword();
  }

  if (!headers) {
    console.log("\n❌ REST API 认证失败");
    console.log("\n原因可能是：");
    console.log("  1. WordPress.com 不支持基本认证");
    console.log("  2. 需要使用应用密码（WordPress 7.1+）");
    console.log("  3. REST API 被禁用或有访问限制\n");

    console.log("✅ 备选方案：使用 PHP 脚本");
    console.log("\n请运行以下命令：");
    console.log("  php seo-optimization-output/seo-batch-apply-1775373361227.php\n");
    console.log("或在 WordPress 后台手动应用。\n");
    process.exit(1);
  }

  // 应用优化
  console.log("⚙️  开始应用优化...\n");

  let successCount = 0;
  let failedCount = 0;

  for (const article of report.articles) {
    if (article.status !== "success") {
      console.log(`⏭️  文章 #${article.id} - 跳过（优化失败）`);
      continue;
    }

    process.stdout.write(`📝 更新文章 #${article.id}... `);

    const result = await updateArticle(article.id, article, headers);

    if (result) {
      console.log("✅");
      successCount++;
    } else {
      console.log("❌");
      failedCount++;
    }

    // 延迟，避免速率限制
    await new Promise((r) => setTimeout(r, 500));
  }

  // 总结
  console.log("\n");
  console.log("╔════════════════════════════════════════════════════════════╗");
  console.log("║  应用完成                                                  ║");
  console.log("╚════════════════════════════════════════════════════════════╝");
  console.log(`\n✅ 成功: ${successCount} 篇`);
  console.log(`❌ 失败: ${failedCount} 篇\n`);

  if (successCount > 0) {
    console.log("📋 下一步：");
    console.log("  1. 访问 WordPress 后台验证更新");
    console.log("  2. Google Search Console → 请求索引");
    console.log("  3. 2-4 周后查看效果\n");
  } else {
    console.log("⚠️  所有更新都失败了");
    console.log("   请使用备选方案（PHP 脚本）\n");
  }
}

main().catch(console.error);
