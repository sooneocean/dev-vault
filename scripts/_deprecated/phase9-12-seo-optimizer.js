#!/usr/bin/env node

/**
 * YOLO LAB Phase 9-12 SEO Optimization Executor
 *
 * 執行 400 篇文章的 SEO 優化（基於分頁）
 * Phase 9: pages 59-68 (100篇)
 * Phase 10: pages 69-78 (100篇)
 * Phase 11: pages 79-88 (100篇)
 * Phase 12: pages 89-98 (100篇)
 *
 * 使用：
 *   node scripts/phase9-12-seo-optimizer.js --phase 9 --demo
 *   node scripts/phase9-12-seo-optimizer.js --phase 9 --apply
 *   node scripts/phase9-12-seo-optimizer.js --all --apply
 */

const fs = require('fs');
const path = require('path');
const https = require('https');

// ─── Config ────────────────────────────────────────────────────────────────

const CONFIG = {
  siteId: 133512998,
  domain: 'yololab.net',
  batchSize: 5,
  delayMs: 2000,
  outputDir: './seo-optimization-output',
  apiEndpoint: 'https://public-api.wordpress.com/rest/v1.1',
  postsPerPage: 10,  // WordPress API default
};

// Phase 定義（基於分頁）
const PHASES = {
  9: {
    pages: Array.from({length: 10}, (_, i) => 59 + i),  // pages 59-68
    name: 'Phase 9',
  },
  10: {
    pages: Array.from({length: 10}, (_, i) => 69 + i),  // pages 69-78
    name: 'Phase 10',
  },
  11: {
    pages: Array.from({length: 10}, (_, i) => 79 + i),  // pages 79-88
    name: 'Phase 11',
  },
  12: {
    pages: Array.from({length: 10}, (_, i) => 89 + i),  // pages 89-98
    name: 'Phase 12',
  },
};

// ─── Helper Functions ─────────────────────────────────────────────────────

function log(msg, level = 'info') {
  const timestamp = new Date().toISOString().split('T')[1].split('.')[0];
  const prefix = {
    info: '[INFO]',
    warn: '[WARN]',
    error: '[ERROR]',
    success: '[✓]',
  }[level] || '[LOG]';
  console.log(`${timestamp} ${prefix} ${msg}`);
}

function ensureOutputDir() {
  if (!fs.existsSync(CONFIG.outputDir)) {
    fs.mkdirSync(CONFIG.outputDir, { recursive: true });
  }
}

function makeRequest(method, path, body = null) {
  return new Promise((resolve, reject) => {
    const url = new URL(`${CONFIG.apiEndpoint}${path}`);

    const options = {
      hostname: url.hostname,
      port: url.port,
      path: url.pathname + url.search,
      method: method,
      headers: {
        'User-Agent': 'YOLO-LAB-SEO-Optimizer/1.0',
        'Content-Type': 'application/json',
      },
    };

    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          const parsed = JSON.parse(data);
          resolve({ status: res.statusCode, data: parsed, headers: res.headers });
        } catch (e) {
          resolve({ status: res.statusCode, data: data, headers: res.headers });
        }
      });
    });

    req.on('error', reject);
    if (body) req.write(JSON.stringify(body));
    req.end();
  });
}

async function getPostsByPages(pageNumbers) {
  log(`獲取第 ${pageNumbers[0]}-${pageNumbers[pageNumbers.length - 1]} 頁的文章...`);

  const posts = [];
  const pageSize = CONFIG.postsPerPage;

  for (const page of pageNumbers) {
    const offset = (page - 1) * pageSize;

    try {
      const response = await makeRequest(
        'GET',
        `/sites/${CONFIG.siteId}/posts?number=${pageSize}&offset=${offset}&status=publish`
      );

      if (response.status !== 200) {
        log(`第 ${page} 頁獲取失敗: HTTP ${response.status}`, 'warn');
        continue;
      }

      const postList = Array.isArray(response.data.posts) ? response.data.posts : [];
      posts.push(...postList);

      if (postList.length > 0) {
        log(`第 ${page} 頁: 找到 ${postList.length} 篇文章`);
      }
    } catch (error) {
      log(`第 ${page} 頁請求異常: ${error.message}`, 'error');
    }

    // 速率限制
    await new Promise(resolve => setTimeout(resolve, 500));
  }

  log(`共獲取 ${posts.length} 篇文章`);
  return posts;
}

function generateSeoMetadata(post) {
  // 基於現有文章內容生成 SEO 元數據
  const title = post.title || '未命名';
  const excerpt = post.excerpt || '';
  const content = post.content || '';

  // 提取關鍵詞
  const keywords = extractKeywords(title, excerpt, content);

  // 生成 meta 描述（155 字符以內）
  const metaDescription = generateMetaDescription(title, excerpt, keywords);

  // 生成 SEO 標題（60 字符以內，含品牌）
  const seoTitle = generateSeoTitle(title);

  return {
    _yoast_wpseo_title: seoTitle,
    _yoast_wpseo_metadesc: metaDescription,
    _yoast_wpseo_focuskw: keywords[0] || '',
  };
}

function extractKeywords(title, excerpt, content) {
  // 從標題和內容提取關鍵詞
  const combined = `${title} ${excerpt} ${content}`.toLowerCase().replace(/<[^>]*>/g, '');

  // YOLO LAB 常見關鍵詞
  const commonKeywords = [
    '科技', '娛樂', '影視', '音樂', '深度', '解析', '2026',
    '演員', '導演', '電影', '展示', '分析', '影評', '樂評',
  ];

  // 檢查包含的關鍵詞
  const found = commonKeywords.filter(kw => combined.includes(kw));
  const result = found.length > 0 ? found.slice(0, 1) : ['YOLO LAB'];

  // 從標題中提取可能的品牌/人名（通常是首個關鍵詞）
  if (result[0].length < 3) {
    const titleWords = title.split(/[\s|：、】》\\]/);
    if (titleWords[0].length > 2 && titleWords[0].length < 20) {
      result.unshift(titleWords[0]);
    }
  }

  return result.slice(0, 3);
}

function generateMetaDescription(title, excerpt, keywords) {
  // 清理 HTML
  let desc = excerpt.replace(/<[^>]*>/g, '').trim();

  if (!desc || desc.length < 20) {
    // 使用標題和關鍵詞生成描述
    desc = `${title}。深度解析 YOLO LAB。`;
  }

  // 截斷至 155 字符
  if (desc.length > 155) {
    desc = desc.substring(0, 152) + '...';
  }

  return desc;
}

function generateSeoTitle(title) {
  // 限制 60 字符
  let seoTitle = title;

  if (seoTitle.length > 50) {
    seoTitle = seoTitle.substring(0, 47) + '...';
  }

  // 如果沒有品牌標記，添加 YOLO LAB
  if (!seoTitle.includes('YOLO') && !seoTitle.includes('LAB')) {
    if (seoTitle.length + 10 <= 60) {
      seoTitle += '｜YOLO LAB';
    }
  }

  return seoTitle.substring(0, 60);
}

async function updatePostSeoMetadata(postId, metadata, isDryRun = false) {
  if (isDryRun) {
    return { success: true, postId, isDryRun: true };
  }

  try {
    const response = await makeRequest(
      'POST',
      `/sites/${CONFIG.siteId}/posts/${postId}`,
      {
        meta: metadata,
      }
    );

    if (response.status === 200 || response.status === 201) {
      return { success: true, postId, response: response.data };
    } else {
      return { success: false, postId, error: `HTTP ${response.status}` };
    }
  } catch (error) {
    return { success: false, postId, error: error.message };
  }
}

async function processPhase(phaseNum, isDryRun = false) {
  const phase = PHASES[phaseNum];
  if (!phase) {
    log(`不存在 Phase ${phaseNum}`, 'error');
    return null;
  }

  log(`\n========== ${phase.name} 開始 ==========`);
  log(`頁面範圍: ${phase.pages[0]}-${phase.pages[phase.pages.length - 1]} (${phase.pages.length * 10} 篇預期)`);
  log(`執行模式: ${isDryRun ? 'DRY RUN' : 'APPLY'}`);

  ensureOutputDir();

  // 獲取文章
  let posts = [];
  try {
    posts = await getPostsByPages(phase.pages);
    log(`成功獲取 ${posts.length} 篇文章`);
  } catch (error) {
    log(`獲取文章失敗: ${error.message}`, 'error');
    return { phase: phaseNum, success: false, error: error.message };
  }

  if (posts.length === 0) {
    log(`未找到指定頁面的文章`, 'warn');
    return { phase: phaseNum, success: false, count: 0, error: 'No posts found' };
  }

  // 處理每篇文章
  const results = {
    phase: phaseNum,
    total: posts.length,
    updated: 0,
    failed: 0,
    skipped: 0,
    details: [],
  };

  for (let i = 0; i < posts.length; i++) {
    const post = posts[i];

    try {
      // 生成 SEO 元數據
      const metadata = generateSeoMetadata(post);

      // 更新文章
      const updateResult = await updatePostSeoMetadata(post.ID, metadata, isDryRun);

      if (updateResult.success) {
        results.updated++;
        const titleDisplay = post.title.substring(0, 45);
        log(`[${i + 1}/${posts.length}] ✓ ID ${post.ID}: ${titleDisplay}`);
      } else {
        results.failed++;
        log(`[${i + 1}/${posts.length}] ✗ ID ${post.ID}: ${updateResult.error}`, 'error');
      }

      results.details.push({
        id: post.ID,
        title: post.title,
        success: updateResult.success,
        metadata: metadata,
      });

      // 速率限制
      if ((i + 1) % CONFIG.batchSize === 0) {
        log(`已處理 ${i + 1}/${posts.length}，等待...`);
        await new Promise(resolve => setTimeout(resolve, CONFIG.delayMs));
      }
    } catch (error) {
      results.failed++;
      log(`[${i + 1}/${posts.length}] 異常: ${error.message}`, 'error');
    }
  }

  // 保存報告
  const reportFile = path.join(
    CONFIG.outputDir,
    `phase${phaseNum}-report-${new Date().toISOString().split('T')[0]}.json`
  );
  fs.writeFileSync(reportFile, JSON.stringify(results, null, 2));
  log(`報告已保存: ${reportFile}`);

  // 統計
  log(`\n========== ${phase.name} 完成 ==========`);
  log(`總計: ${results.total} 篇`);
  log(`成功: ${results.updated} 篇`, 'success');
  log(`失敗: ${results.failed} 篇`);
  log(`略過: ${results.skipped} 篇`);

  return results;
}

async function processAllPhases(isDryRun = false) {
  const allResults = {
    timestamp: new Date().toISOString(),
    isDryRun,
    phases: {},
    summary: {
      totalPosts: 0,
      totalUpdated: 0,
      totalFailed: 0,
    },
  };

  for (const phaseNum of [9, 10, 11, 12]) {
    const result = await processPhase(phaseNum, isDryRun);
    if (result) {
      allResults.phases[`phase${phaseNum}`] = result;
      allResults.summary.totalPosts += result.total || 0;
      allResults.summary.totalUpdated += result.updated || 0;
      allResults.summary.totalFailed += result.failed || 0;
    }

    // 相位之間的延遲
    await new Promise(resolve => setTimeout(resolve, 2000));
  }

  // 保存整體報告
  const reportFile = path.join(
    CONFIG.outputDir,
    `all-phases-report-${new Date().toISOString().split('T')[0]}.json`
  );
  fs.writeFileSync(reportFile, JSON.stringify(allResults, null, 2));

  // 印出最終統計
  log(`\n\n========== 全體相位完成 ==========`);
  log(`執行時間: ${new Date().toISOString()}`);
  log(`執行模式: ${isDryRun ? 'DRY RUN' : 'APPLY'}`);
  log(`\n統計:`);
  log(`  總文章數: ${allResults.summary.totalPosts}`, 'info');
  log(`  成功更新: ${allResults.summary.totalUpdated}`, 'success');
  log(`  失敗: ${allResults.summary.totalFailed}`, allResults.summary.totalFailed > 0 ? 'error' : 'info');
  log(`  成功率: ${((allResults.summary.totalUpdated / allResults.summary.totalPosts) * 100).toFixed(1)}%`);
  log(`\n報告位置: ${CONFIG.outputDir}`);

  return allResults;
}

// ─── Main ─────────────────────────────────────────────────────────────────

async function main() {
  const args = process.argv.slice(2);

  let phaseNum = null;
  let isDryRun = true;
  let processAll = false;

  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--phase' && args[i + 1]) {
      phaseNum = parseInt(args[i + 1]);
      i++;
    } else if (args[i] === '--all') {
      processAll = true;
    } else if (args[i] === '--demo') {
      isDryRun = true;
    } else if (args[i] === '--apply') {
      isDryRun = false;
    }
  }

  log('YOLO LAB Phase 9-12 SEO Optimizer');
  log(`網站 ID: ${CONFIG.siteId}`);
  log(`API 端點: ${CONFIG.apiEndpoint}`);

  if (!processAll && !phaseNum) {
    log('用法:', 'warn');
    log('  node scripts/phase9-12-seo-optimizer.js --phase <9|10|11|12> [--demo|--apply]');
    log('  node scripts/phase9-12-seo-optimizer.js --all [--demo|--apply]');
    log('');
    log('示例:');
    log('  node scripts/phase9-12-seo-optimizer.js --phase 9 --demo');
    log('  node scripts/phase9-12-seo-optimizer.js --all --apply');
    process.exit(1);
  }

  try {
    if (processAll) {
      await processAllPhases(isDryRun);
    } else {
      const result = await processPhase(phaseNum, isDryRun);
      if (!result) process.exit(1);
    }
  } catch (error) {
    log(`致命錯誤: ${error.message}`, 'error');
    process.exit(1);
  }
}

main().catch(err => {
  console.error('Unhandled error:', err);
  process.exit(1);
});
