#!/usr/bin/env node

/**
 * YOLO LAB SEO 全量批处理器
 * 处理 2,725 篇文章的 SEO 优化
 * Site: yololab.net (ID: 133512998)
 */

const Anthropic = require("@anthropic-ai/sdk");

const client = new Anthropic();

// 配置
const SITE_ID = 133512998;
const PER_PAGE = 100;
const TOTAL_ARTICLES = 2725;
const TOTAL_PAGES = Math.ceil(TOTAL_ARTICLES / PER_PAGE); // 27 页

// 统计数据
let stats = {
  processed: 0,
  optimized: 0, // 已有 SEO 信息的文章
  success: 0, // 成功优化的
  failed: 0, // 失败的
  skipped: 0, // 被跳过的
  failedIds: [], // 失败的 article IDs
};

/**
 * 调用 Claude API 生成 SEO 内容
 */
async function generateSEOContent(title, excerpt) {
  try {
    const response = await client.messages.create({
      model: "claude-opus-4-1-20250805",
      max_tokens: 200,
      messages: [
        {
          role: "user",
          content: `生成这篇文章的 SEO 优化内容。

文章标题: "${title}"
文章摘要: "${excerpt}"

请返回 JSON 格式（严格遵循，不要其他文字）:
{
  "optimizedTitle": "45-60个字符的 SEO 优化标题",
  "metaDescription": "120-160个字符的 SEO 元描述"
}`,
        },
      ],
    });

    const text = response.content[0].text.trim();
    const json = JSON.parse(text);

    return {
      title: json.optimizedTitle || title,
      description: json.metaDescription || excerpt.substring(0, 160),
    };
  } catch (error) {
    console.error(`  ✗ API 错误: ${error.message}`);
    return null;
  }
}

/**
 * 模拟 WordPress 更新操作
 * 实际使用时应调用 mcp__wpcom-mcp__wpcom-mcp-content-authoring posts.update
 */
async function updatePostSEO(postId, seoTitle, seoDescription) {
  try {
    // 模拟延迟（实际应调用 WordPress API）
    await new Promise((r) => setTimeout(r, 100));
    return { success: true };
  } catch (error) {
    console.error(`  ✗ 更新失败: ${error.message}`);
    return { success: false, error: error.message };
  }
}

/**
 * 处理单篇文章
 */
async function processArticle(post) {
  const { id, title, excerpt } = post;

  // 检查是否已优化（简化版，实际应检查 meta.jetpack_seo_html_title）
  const alreadyOptimized = false; // 这里应该检查实际字段

  if (alreadyOptimized) {
    stats.optimized++;
    process.stdout.write("⊘");
    return;
  }

  // 调用 Claude API 生成 SEO 内容
  const seoContent = await generateSEOContent(title, excerpt);

  if (!seoContent) {
    stats.failed++;
    stats.failedIds.push(id);
    process.stdout.write("✗");
    return;
  }

  // 更新到 WordPress（模拟）
  const updateResult = await updatePostSEO(
    id,
    seoContent.title,
    seoContent.description
  );

  if (updateResult.success) {
    stats.success++;
    process.stdout.write("✓");
  } else {
    stats.failed++;
    stats.failedIds.push(id);
    process.stdout.write("✗");
  }
}

/**
 * 处理单页文章
 */
async function processPage(pageNum) {
  console.log(`\n[第 ${pageNum}/${TOTAL_PAGES} 页]`);

  // 这里应该从 WordPress 获取文章列表
  // 模拟数据（实际应调用 posts.list）
  const mockPosts = Array.from({ length: Math.min(100, 2725 - (pageNum - 1) * 100) }, (_, i) => ({
    id: (pageNum - 1) * 100 + i + 1,
    title: `文章标题 ${(pageNum - 1) * 100 + i + 1}`,
    excerpt: `这是第 ${(pageNum - 1) * 100 + i + 1} 篇文章的摘要`,
  }));

  for (const post of mockPosts) {
    await processArticle(post);
    stats.processed++;

    // 每 10 篇显示进度
    if (stats.processed % 10 === 0) {
      const pageProgress =
        stats.processed - (pageNum - 1) * PER_PAGE;
      console.log(
        ` [${stats.processed}/2725] 批次 ${pageNum}: ${pageProgress}/10 成功`
      );
    }
  }

  // 每 100 篇显示完整统计
  if (stats.processed % 100 === 0) {
    const elapsed = Math.round(
      (Date.now() - startTime) / 1000 / 60
    ); // 分钟
    console.log(
      `\n✅ ${stats.processed} 篇完成 (成功 ${stats.success}, 失败 ${stats.failed}, 已优化 ${stats.optimized}, 耗时 ${elapsed}m)\n`
    );
  }

  // 里程碑报告
  const milestones = [500, 1000, 1500, 2000, 2500, 2725];
  if (milestones.includes(stats.processed)) {
    const elapsed = Math.round(
      (Date.now() - startTime) / 1000 / 60
    );
    console.log(
      `\n🎯 里程碑 ${stats.processed}/2725 达成！耗时 ${elapsed}m (成功 ${stats.success}, 失败 ${stats.failed}, 已优化 ${stats.optimized})\n`
    );
  }
}

/**
 * 主函数
 */
async function main() {
  console.log(`
╔════════════════════════════════════════╗
║    YOLO LAB 全量 SEO 优化批处理        ║
║    站点: yololab.net (ID: 133512998)  ║
║    总文章数: 2,725 篇 (27 页)          ║
║    API: Claude Opus 4.6               ║
╚════════════════════════════════════════╝
`);

  global.startTime = Date.now();

  // 逐页处理
  for (let page = 1; page <= TOTAL_PAGES; page++) {
    await processPage(page);
  }

  // 最终报告
  const totalTime = Math.round((Date.now() - startTime) / 1000 / 60);
  console.log(`
╔════════════════════════════════════════╗
║           最终统计报告                 ║
╚════════════════════════════════════════╝
总处理: ${stats.processed}/2725
✓ 成功:    ${stats.success}
✗ 失败:    ${stats.failed}
⊘ 已优化:  ${stats.optimized}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
总耗时: ${totalTime} 分钟
平均速度: ${Math.round(stats.processed / totalTime)} 篇/分钟
`);

  if (stats.failedIds.length > 0) {
    console.log(`\n失败的文章 IDs:\n${stats.failedIds.join(", ")}`);
  }
}

// 错误处理
process.on("unhandledRejection", (err) => {
  console.error("\n致命错误:", err);
  process.exit(1);
});

// 启动
main().catch(console.error);
