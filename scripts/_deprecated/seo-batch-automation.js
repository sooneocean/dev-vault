#!/usr/bin/env node
/**
 * YOLO LAB SEO Batch Automation v3.0
 *
 * 完全自动化脚本：逐篇处理 2,600+ 文章的 SEO 优化
 *
 * 流程:
 * 1. posts.list 分页获取所有文章
 * 2. posts.get 获取每篇标题+摘要
 * 3. Claude Opus 4.6 生成 SEO 标题+描述
 * 4. posts.update 更新元数据
 * 5. 进度追踪 + 里程碑报告
 *
 * 使用:
 *   export ANTHROPIC_API_KEY="your-key"
 *   export WP_USERNAME="username"
 *   export WP_APP_PASSWORD="password"
 *   node seo-batch-automation.js
 */

const https = require('https');
const fs = require('fs');
const path = require('path');

// ============ 配置 ============
const CONFIG = {
  SITE_ID: '133512998',
  DOMAIN: 'yololab.net',
  API_BASE: 'public-api.wordpress.com',
  ANTHROPIC_BASE: 'api.anthropic.com',
  ANTHROPIC_MODEL: 'claude-opus-4-6-20250805',
  BATCH_SIZE: 1,  // 逐篇处理
  BATCH_DELAY: 750, // 毫秒
  TIMEOUT_PER_POST: 30000, // 30秒
  RETRIES: 3,
  LOG_DIR: path.join(__dirname, '../seo-batch-logs'),
  PROGRESS_FILE: path.join(__dirname, '../seo-batch-logs/progress.json'),
  FAILED_FILE: path.join(__dirname, '../seo-batch-logs/failed-posts.json'),
  MILESTONES: [100, 500, 1000, 1500, 2000, 2600, 2725]
};

// ============ 颜色输出 ============
const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  red: '\x1b[31m',
  cyan: '\x1b[36m',
  magenta: '\x1b[35m',
  bold: '\x1b[1m'
};

function log(msg, color = 'reset') {
  const timestamp = new Date().toISOString().split('T')[1].split('.')[0];
  console.log(`${colors[color]}[${timestamp}] ${msg}${colors.reset}`);
}

function logSection(title) {
  console.log('');
  log(`${'='.repeat(80)}`, 'cyan');
  log(title, 'bold');
  log(`${'='.repeat(80)}`, 'cyan');
  console.log('');
}

function logMilestone(current, total) {
  const percentage = Math.round((current / total) * 100);
  log(`✅ 里程碑达成: ${current}/${total} (${percentage}%)`, 'magenta');
  console.log('');
}

// ============ 初始化日志目录 ============
function initLogDir() {
  if (!fs.existsSync(CONFIG.LOG_DIR)) {
    fs.mkdirSync(CONFIG.LOG_DIR, { recursive: true });
    log(`创建日志目录: ${CONFIG.LOG_DIR}`, 'green');
  }
}

// ============ API 请求函数 ============
function makeHttpsRequest(options, body = null) {
  return new Promise((resolve, reject) => {
    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', (chunk) => { data += chunk; });
      res.on('end', () => {
        try {
          const parsed = JSON.parse(data);
          resolve({ statusCode: res.statusCode, body: parsed });
        } catch {
          resolve({ statusCode: res.statusCode, body: data });
        }
      });
    });

    req.on('error', reject);
    req.on('timeout', () => {
      req.destroy();
      reject(new Error('Request timeout'));
    });

    if (body) req.write(JSON.stringify(body));
    req.end();
  });
}

// ============ WordPress.com API ============
async function wpApiRequest(method, endpoint, body = null, username, password) {
  const auth = Buffer.from(`${username}:${password}`).toString('base64');

  const options = {
    hostname: CONFIG.API_BASE,
    port: 443,
    path: `/rest/v1.1${endpoint}`,
    method: method,
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Basic ${auth}`,
      'User-Agent': 'YOLO-SEO-Automation/3.0'
    },
    timeout: CONFIG.TIMEOUT_PER_POST
  };

  return makeHttpsRequest(options, body);
}

// ============ Anthropic API ============
async function generateSeoContent(title, excerpt) {
  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) throw new Error('ANTHROPIC_API_KEY not set');

  const prompt = `你是一位 SEO 专家。根据文章标题和摘要，生成优化的 SEO 元数据。

文章标题: ${title}
文章摘要: ${excerpt || '(无)'}

请返回以下信息（用 | 分隔）:
1. SEO 标题（50-60 个字符）
2. SEO 描述（150-160 个字符）

格式: SEO_TITLE|SEO_DESCRIPTION

确保：
- 标题包含主要关键词
- 描述包含行动号召（CTA）
- 两者都符合长度要求`;

  const options = {
    hostname: CONFIG.ANTHROPIC_BASE,
    port: 443,
    path: '/v1/messages',
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-api-key': apiKey,
      'anthropic-version': '2023-06-01'
    },
    timeout: CONFIG.TIMEOUT_PER_POST
  };

  const body = {
    model: CONFIG.ANTHROPIC_MODEL,
    max_tokens: 256,
    messages: [{ role: 'user', content: prompt }]
  };

  try {
    const response = await makeHttpsRequest(options, body);

    if (response.statusCode !== 200) {
      throw new Error(`Anthropic API error: ${response.statusCode} - ${JSON.stringify(response.body)}`);
    }

    const content = response.body.content[0].text;
    const [seoTitle, seoDescription] = content.split('|').map(s => s.trim());

    return { seoTitle, seoDescription };
  } catch (err) {
    throw new Error(`SEO generation failed: ${err.message}`);
  }
}

// ============ 进度追踪 ============
class ProgressTracker {
  constructor() {
    this.processed = 0;
    this.successful = 0;
    this.failed = 0;
    this.skipped = 0;
    this.processedIds = [];
    this.failedPosts = [];
    this.startTime = Date.now();
  }

  addSuccess(postId) {
    this.processed++;
    this.successful++;
    this.processedIds.push(postId);
  }

  addFailed(postId, reason) {
    this.processed++;
    this.failed++;
    this.failedPosts.push({ id: postId, reason });
  }

  addSkipped() {
    this.skipped++;
  }

  save() {
    fs.writeFileSync(CONFIG.PROGRESS_FILE, JSON.stringify({
      processed: this.processed,
      successful: this.successful,
      failed: this.failed,
      skipped: this.skipped,
      processedIds: this.processedIds,
      timestamp: new Date().toISOString()
    }, null, 2));

    fs.writeFileSync(CONFIG.FAILED_FILE, JSON.stringify({
      failed: this.failedPosts,
      count: this.failedPosts.length,
      timestamp: new Date().toISOString()
    }, null, 2));
  }

  getStats() {
    const elapsed = (Date.now() - this.startTime) / 1000;
    const rate = this.processed / (elapsed / 60); // 篇/分钟
    return { elapsed, rate };
  }
}

// ============ 主流程 ============
async function main() {
  initLogDir();
  logSection('🚀 YOLO LAB SEO 批量自动化 v3.0');

  // 验证凭证
  let username = process.env.WP_USERNAME;
  let password = process.env.WP_APP_PASSWORD;
  let apiKey = process.env.ANTHROPIC_API_KEY;

  // 如果环境变量缺失，尝试从 .env 文件读取
  if (!username || !password || !apiKey) {
    const envPath = path.join(__dirname, '../.env');
    if (fs.existsSync(envPath)) {
      log('📂 从 .env 文件读取凭证...', 'yellow');
      const envContent = fs.readFileSync(envPath, 'utf8');
      const envLines = envContent.split('\n');
      for (const line of envLines) {
        if (line.startsWith('WP_USERNAME=')) {
          username = line.split('=')[1].trim().replace(/["']/g, '');
        }
        if (line.startsWith('WP_APP_PASSWORD=')) {
          password = line.split('=')[1].trim().replace(/["']/g, '');
        }
        if (line.startsWith('ANTHROPIC_API_KEY=')) {
          apiKey = line.split('=')[1].trim().replace(/["']/g, '');
        }
      }
    }
  }

  if (!username || !password) {
    log('❌ 缺少 WordPress.com 凭证', 'red');
    log('请设置环境变量或创建 .env 文件:', 'yellow');
    log('  export WP_USERNAME="username"', 'cyan');
    log('  export WP_APP_PASSWORD="password"', 'cyan');
    process.exit(1);
  }

  if (!apiKey) {
    log('❌ 缺少 Anthropic API 密钥', 'red');
    log('请设置:', 'yellow');
    log('  export ANTHROPIC_API_KEY="key"', 'cyan');
    process.exit(1);
  }

  log('✓ 凭证已验证', 'green');
  console.log('');

  const tracker = new ProgressTracker();
  let page = 1;
  let totalPosts = null;
  let continueProcessing = true;

  // 分页获取文章
  while (continueProcessing) {
    try {
      log(`📄 获取第 ${page} 页文章...`, 'blue');

      const listResponse = await wpApiRequest(
        'GET',
        `/sites/${CONFIG.SITE_ID}/posts?page=${page}&number=50&status=publish`,
        null,
        username,
        password
      );

      if (listResponse.statusCode !== 200) {
        log(`⚠️  页面 ${page} 获取失败 (${listResponse.statusCode})`, 'yellow');
        break;
      }

      const { posts, found: total } = listResponse.body;
      if (!totalPosts) totalPosts = total;

      if (!posts || posts.length === 0) {
        log(`✓ 已到达最后一页 (共 ${total} 篇文章)`, 'green');
        continueProcessing = false;
        break;
      }

      log(`  本页: ${posts.length} 篇，累计: ${tracker.processed}/${total}`, 'cyan');

      // 处理每篇文章
      for (const post of posts) {
        if (tracker.processedIds.includes(post.ID)) {
          tracker.addSkipped();
          continue;
        }

        try {
          log(`  [${tracker.processed + 1}/${total}] 处理文章 #${post.ID}: "${post.title.substring(0, 40)}..."`, 'yellow');

          // 获取完整信息
          const getResponse = await wpApiRequest(
            'GET',
            `/sites/${CONFIG.SITE_ID}/posts/${post.ID}`,
            null,
            username,
            password
          );

          if (getResponse.statusCode !== 200) {
            throw new Error(`获取失败: ${getResponse.statusCode}`);
          }

          const fullPost = getResponse.body;
          const excerpt = (fullPost.excerpt || '').replace(/<[^>]*>/g, '').substring(0, 200);

          // 生成 SEO 内容
          let seoTitle, seoDescription;
          for (let retry = 0; retry < CONFIG.RETRIES; retry++) {
            try {
              const seo = await generateSeoContent(fullPost.title, excerpt);
              seoTitle = seo.seoTitle;
              seoDescription = seo.seoDescription;
              break;
            } catch (err) {
              if (retry === CONFIG.RETRIES - 1) throw err;
              await new Promise(r => setTimeout(r, 1000 * (retry + 1)));
            }
          }

          // 更新文章
          const updateResponse = await wpApiRequest(
            'POST',
            `/sites/${CONFIG.SITE_ID}/posts/${post.ID}`,
            {
              title: seoTitle,
              excerpt: seoDescription,
              metadata: [{
                key: 'yoast_seo_title',
                value: seoTitle
              }, {
                key: 'yoast_seo_description',
                value: seoDescription
              }]
            },
            username,
            password
          );

          if (updateResponse.statusCode === 200) {
            tracker.addSuccess(post.ID);
            log(`    ✓ 更新成功`, 'green');
          } else {
            throw new Error(`更新失败: ${updateResponse.statusCode}`);
          }

        } catch (err) {
          tracker.addFailed(post.ID, err.message);
          log(`    ✗ 错误: ${err.message}`, 'red');
        }

        // 批次延迟
        await new Promise(r => setTimeout(r, CONFIG.BATCH_DELAY));

        // 里程碑报告
        if (CONFIG.MILESTONES.includes(tracker.processed)) {
          tracker.save();
          const stats = tracker.getStats();
          logMilestone(tracker.processed, totalPosts);
          log(`⏱️  耗时: ${Math.round(stats.elapsed)}秒 | 速率: ${stats.rate.toFixed(1)}/分钟`, 'cyan');
          log(`✓ 成功: ${tracker.successful} | ✗ 失败: ${tracker.failed} | ⊘ 跳过: ${tracker.skipped}`, 'cyan');
          console.log('');
        }
      }

      page++;

      // 防止无限循环
      if (page > 100) {
        log('⚠️  超过最大页数限制', 'yellow');
        break;
      }

    } catch (err) {
      log(`✗ 页面处理错误: ${err.message}`, 'red');
      break;
    }
  }

  // 最终报告
  tracker.save();
  logSection('📊 批量 SEO 优化完成报告');

  const stats = tracker.getStats();
  log(`总处理文章数: ${tracker.processed}`, 'cyan');
  log(`✓ 成功: ${tracker.successful} (${Math.round(tracker.successful / tracker.processed * 100)}%)`, 'green');
  log(`✗ 失败: ${tracker.failed}`, 'red');
  log(`⊘ 跳过: ${tracker.skipped}`, 'yellow');
  log(`⏱️  总耗时: ${Math.round(stats.elapsed)}秒`, 'cyan');
  log(`📈 平均速率: ${stats.rate.toFixed(1)} 篇/分钟`, 'cyan');

  if (tracker.failedPosts.length > 0) {
    console.log('');
    log(`⚠️  失败的文章 ID: ${tracker.failedPosts.map(p => p.id).join(', ')}`, 'yellow');
  }

  log(`\n📁 详细日志已保存到: ${CONFIG.LOG_DIR}`, 'cyan');
  process.exit(tracker.failed === 0 ? 0 : 1);
}

// ============ 执行 ============
main().catch(err => {
  log(`✗ 致命错误: ${err.message}`, 'red');
  process.exit(1);
});
