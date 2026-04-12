#!/usr/bin/env node

/**
 * YOLO LAB 自动登入 + 应用 SEO 优化
 * 通过完整的 WordPress 登入流程 + nonce 机制
 */

import fetch from "node-fetch";
import { CookieJar } from "tough-cookie";
import { HttpCookieAgent, HttpsCookieAgent } from "http-cookie-agent/undici";
import fs from "fs";

// 配置
const CONFIG = {
  siteUrl: "https://yololab.net",
  wpAdminUrl: "https://yololab.net/wp-admin",
  loginUrl: "https://yololab.net/wp-login.php",
  email: "yololab.life@gmail.com",
  password: "yololab4ever",
  reportFile: "./seo-optimization-output/seo-report-2025-1775373361211.json",
};

// Cookie 管理
const cookieJar = new CookieJar();
const httpAgent = new HttpCookieAgent({ cookies: { jar: cookieJar } });
const httpsAgent = new HttpsCookieAgent({ cookies: { jar: cookieJar } });

function getAgent(url) {
  return url.startsWith("https") ? httpsAgent : httpAgent;
}

// 步骤 1：获取登入表单（获取 nonce）
async function getLoginNonce() {
  console.log("🔐 获取登入 nonce...");

  try {
    const response = await fetch(CONFIG.loginUrl, {
      agent: getAgent(CONFIG.loginUrl),
    });

    const html = await response.text();

    // 查找 nonce
    const nonceMatch = html.match(/name="wp-submit"[\s\S]*?<input[^>]*name="([^"]*)"[^>]*value="([^"]*)"/);
    const nonce = html.match(/name="_wpnonce"[^>]*value="([^"]*)"/)?.[1];
    const redirect = html.match(/name="redirect_to"[^>]*value="([^"]*)"/)?.[1];

    console.log(`✅ 获得 nonce: ${nonce?.substring(0, 10)}...`);

    return { nonce, redirect };
  } catch (error) {
    console.error("❌ 获取 nonce 失败:", error.message);
    return null;
  }
}

// 步骤 2：登入
async function login(nonce) {
  console.log("🔓 登入中...");

  const formData = new URLSearchParams();
  formData.append("log", CONFIG.email);
  formData.append("pwd", CONFIG.password);
  formData.append("wp-submit", "登入");
  formData.append("_wpnonce", nonce);
  formData.append("redirect_to", CONFIG.wpAdminUrl);
  formData.append("testcookie", "1");

  try {
    const response = await fetch(CONFIG.loginUrl, {
      method: "POST",
      agent: getAgent(CONFIG.loginUrl),
      body: formData,
      redirect: "manual",
    });

    console.log(`📍 登入响应: ${response.status}`);

    if (response.status === 302 || response.status === 200) {
      console.log("✅ 登入成功");
      return true;
    } else {
      console.log("❌ 登入失败");
      return false;
    }
  } catch (error) {
    console.error("❌ 登入异常:", error.message);
    return false;
  }
}

// 步骤 3：获取管理页面 nonce
async function getAdminNonce() {
  console.log("🔐 获取管理页面 nonce...");

  try {
    const response = await fetch(CONFIG.wpAdminUrl, {
      agent: getAgent(CONFIG.wpAdminUrl),
    });

    const html = await response.text();
    const nonce = html.match(/name="_wpnonce"[^>]*value="([^"]*)"/)?.[1];

    if (nonce) {
      console.log(`✅ 获得管理 nonce: ${nonce.substring(0, 10)}...`);
      return nonce;
    }
    return null;
  } catch (error) {
    console.error("❌ 获取管理 nonce 失败:", error.message);
    return null;
  }
}

// 步骤 4：批量更新文章元数据
async function updateArticles(adminNonce) {
  console.log("\n⚙️ 加载优化报告...");

  if (!fs.existsSync(CONFIG.reportFile)) {
    console.error("❌ 找不到报告文件:", CONFIG.reportFile);
    return 0;
  }

  const report = JSON.parse(fs.readFileSync(CONFIG.reportFile, "utf-8"));
  console.log(`✅ 加载完成: ${report.articles.length} 篇文章\n`);

  let successCount = 0;

  for (const article of report.articles) {
    if (article.status !== "success") {
      console.log(`⏭️  文章 #${article.id} - 跳过`);
      continue;
    }

    const postId = article.id;
    const meta = article.recommendations?.meta || {};
    const og = article.recommendations?.og || {};
    const schema = article.recommendations?.schema || {};

    // 构建更新数据
    const updates = {
      _yoast_wpseo_title: meta.optimizedTitle || "",
      _yoast_wpseo_metadesc: meta.metaDescription || "",
      _yoast_wpseo_focuskw: (meta.primaryKeywords?.[0] || "").substring(0, 100),
      _yoast_wpseo_og_title: og["og:title"] || "",
      _yoast_wpseo_og_description: og["og:description"] || "",
      _yoast_wpseo_schema_article: JSON.stringify(schema.schema || {}),
    };

    // 通过 REST API POST 更新
    const url = `${CONFIG.siteUrl}/wp-json/wp/v2/posts/${postId}`;

    try {
      const response = await fetch(url, {
        method: "POST",
        agent: getAgent(url),
        headers: {
          "Content-Type": "application/json",
          "X-WP-Nonce": adminNonce,
        },
        body: JSON.stringify({ meta: updates }),
      });

      if (response.ok || response.status === 200) {
        console.log(`✅ 文章 #${postId} - 已更新`);
        successCount++;
      } else {
        const error = await response.text();
        console.log(`❌ 文章 #${postId} - 错误 ${response.status}`);
      }
    } catch (error) {
      console.log(`❌ 文章 #${postId} - 异常: ${error.message}`);
    }

    // 延迟
    await new Promise((r) => setTimeout(r, 300));
  }

  return successCount;
}

// 主程序
async function main() {
  console.log("\n");
  console.log("╔════════════════════════════════════════════════════════════╗");
  console.log("║  YOLO LAB 自动登入 + SEO 优化应用                          ║");
  console.log("╚════════════════════════════════════════════════════════════╝");
  console.log("\n");

  // 步骤 1：获取 nonce
  const { nonce } = await getLoginNonce();
  if (!nonce) {
    console.error("\n❌ 无法获取登入 nonce，退出");
    process.exit(1);
  }

  // 步骤 2：登入
  const loggedIn = await login(nonce);
  if (!loggedIn) {
    console.error("\n❌ 登入失败，退出");
    process.exit(1);
  }

  // 步骤 3：获取管理 nonce
  const adminNonce = await getAdminNonce();
  if (!adminNonce) {
    console.error("\n⚠️ 无法获取管理 nonce，尝试不用 nonce 继续...");
  }

  // 步骤 4：更新文章
  const successCount = await updateArticles(adminNonce || "");

  // 总结
  console.log("\n");
  console.log("╔════════════════════════════════════════════════════════════╗");
  console.log("║  完成                                                      ║");
  console.log("╚════════════════════════════════════════════════════════════╝");
  console.log(`\n✅ 成功: ${successCount} 篇\n`);

  if (successCount > 0) {
    console.log("📋 下一步:");
    console.log("  1. 访问 WordPress 后台验证更新");
    console.log("  2. Google Search Console → 请求索引");
    console.log("  3. 2-4 周后查看效果\n");
  }
}

main().catch(console.error);
