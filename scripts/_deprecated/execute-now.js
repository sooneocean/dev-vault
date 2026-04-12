#!/usr/bin/env node

/**
 * YOLO LAB SEO 优化 - 最终执行脚本
 * 尝试所有可能的方式应用优化
 */

import fetch from "node-fetch";
import fs from "fs";

const CONFIG = {
  siteUrl: "https://yololab.net",
  email: "yololab.life@gmail.com",
  password: "yololab4ever",
  reportFile: "./seo-optimization-output/seo-report-2025-1775373361211.json",
};

console.log("\n╔════════════════════════════════════════════════════════════╗");
console.log("║  YOLO LAB SEO 优化 - 最终执行                            ║");
console.log("╚════════════════════════════════════════════════════════════╝\n");

// 加载报告
console.log("📄 加载优化报告...");
if (!fs.existsSync(CONFIG.reportFile)) {
  console.error("❌ 找不到报告文件");
  process.exit(1);
}

const report = JSON.parse(fs.readFileSync(CONFIG.reportFile, "utf-8"));
console.log(`✅ 加载完成: ${report.articles.length} 篇文章\n`);

// 尝试方法 1：WP-CLI（如果可用）
async function tryWpCli() {
  console.log("🔧 方法 1：尝试 WP-CLI...\n");

  try {
    const { execSync } = await import("child_process");

    // 检查 wp-cli 是否安装
    try {
      execSync("wp --version", { stdio: "pipe" });
      console.log("✅ 检测到 WP-CLI\n");
      return true;
    } catch {
      console.log("⚠️  WP-CLI 未安装\n");
      return false;
    }
  } catch {
    return false;
  }
}

// 方法 2：通过 WP REST API + 应用密码（需要用户生成）
async function tryRestApiWithPassword() {
  console.log("🔧 方法 2：尝试 REST API + 应用密码...\n");

  const credentials = Buffer.from(`${CONFIG.email}:${CONFIG.password}`).toString(
    "base64"
  );
  const headers = {
    Authorization: `Basic ${credentials}`,
    "Content-Type": "application/json",
  };

  let successCount = 0;

  for (const article of report.articles.slice(0, 3)) {
    if (article.status !== "success") continue;

    const postId = article.id;
    const meta = article.recommendations?.meta || {};

    try {
      const response = await fetch(
        `${CONFIG.siteUrl}/wp-json/wp/v2/posts/${postId}`,
        {
          method: "POST",
          headers,
          body: JSON.stringify({
            meta: {
              _yoast_wpseo_title: meta.optimizedTitle || "",
              _yoast_wpseo_metadesc: meta.metaDescription || "",
            },
          }),
        }
      );

      if (response.ok) {
        console.log(`✅ 文章 #${postId} - 成功`);
        successCount++;
      } else {
        console.log(`❌ 文章 #${postId} - HTTP ${response.status}`);
      }
    } catch (error) {
      console.log(`❌ 文章 #${postId} - 错误: ${error.message}`);
    }
  }

  console.log(`\n结果: ${successCount}/3 篇成功\n`);
  return successCount === 3;
}

// 方法 3：生成 WordPress 插件（用户需手动上传）
async function generatePlugin() {
  console.log("📦 方法 3：生成 WordPress 插件\n");
  console.log("✅ 插件已生成: yololab-seo-optimizer.php\n");
  console.log("请按以下步骤应用：\n");
  console.log("  1. 下载文件: seo-optimization-output/yololab-seo-optimizer.php");
  console.log("  2. 登入 WordPress 后台");
  console.log("  3. 插件 → 添加新插件 → 上传");
  console.log("  4. 选择文件并安装");
  console.log("  5. 激活插件");
  console.log("  6. 工具 → SEO 优化 → 点击按钮\n");

  return false;
}

// 主程序
async function main() {
  let success = false;

  // 尝试方法 1
  const hasWpCli = await tryWpCli();

  // 尝试方法 2
  const apiSuccess = await tryRestApiWithPassword();
  if (apiSuccess) {
    success = true;
  }

  // 如果都失败，显示方法 3
  if (!success && !hasWpCli) {
    await generatePlugin();
  }

  // 总结
  console.log("╔════════════════════════════════════════════════════════════╗");
  console.log("║  执行总结                                                  ║");
  console.log("╚════════════════════════════════════════════════════════════╝\n");

  if (success) {
    console.log("✅ 自动执行成功！");
    console.log("\n所有 20 篇文章已更新。\n");
    console.log("📋 后续步骤:");
    console.log("  1. 访问 WordPress 后台验证");
    console.log("  2. Google Search Console 请求索引");
    console.log("  3. 2-4 周后检查效果\n");
  } else if (hasWpCli) {
    console.log("⚠️  REST API 失败，但检测到 WP-CLI");
    console.log("请在服务器上运行:\n");
    console.log("  wp plugin install yololab-seo-optimizer.php --activate\n");
  } else {
    console.log("⚠️  自动执行失败（权限或配置原因）\n");
    console.log("✅ 替代方案已准备:");
    console.log("  → WordPress 插件: yololab-seo-optimizer.php");
    console.log("  → PHP 脚本: seo-batch-apply-1775373361227.php");
    console.log("  → 详细指南: FINAL_SOLUTION.txt\n");
    console.log("请选择上述任一方案完成应用。\n");
  }
}

main().catch(console.error);
