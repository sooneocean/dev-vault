#!/usr/bin/env node
/**
 * YOLO LAB SEO Batch Automation Demo v3.0
 *
 * 演示模式：模拟 2,600+ 文章的 SEO 优化流程
 * 不需要真实凭证，用于验证脚本逻辑
 *
 * 使用:
 *   node seo-batch-automation-demo.js [--fast] [--total 2725]
 *
 * --fast: 加速运行（10ms 延迟代替 750ms）
 * --total: 指定要处理的文章总数（默认 2725）
 */

const fs = require('fs');
const path = require('path');

// ============ 配置 ============
const CONFIG = {
  SITE_ID: '133512998',
  DOMAIN: 'yololab.net',
  BATCH_DELAY: process.argv.includes('--fast') ? 10 : 750,
  TOTAL_POSTS: parseInt(process.argv.find(a => a.startsWith('--total'))?.split(' ')[0]?.split('=')[1] || '2725'),
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

// ============ 进度追踪 ============
class ProgressTracker {
  constructor(total) {
    this.total = total;
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
    this.processed++;
    this.skipped++;
  }

  save() {
    fs.writeFileSync(CONFIG.PROGRESS_FILE, JSON.stringify({
      processed: this.processed,
      successful: this.successful,
      failed: this.failed,
      skipped: this.skipped,
      total: this.total,
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
    const remaining = (this.total - this.processed) / rate; // 分钟
    return { elapsed, rate, remaining };
  }
}

// ============ 模拟 SEO 生成 ============
function simulateSeoGeneration(postId, title) {
  // 90% 成功率
  if (Math.random() > 0.9) {
    throw new Error('API 超时模拟');
  }

  const truncated = title.substring(0, 45);
  const seoTitle = `${truncated} - SEO优化版 | YOLO LAB`;
  const seoDescription = `深入了解 ${truncated}。本文提供详细分析、最佳实践和实用建议。立即阅读。`;

  return { seoTitle, seoDescription };
}

// ============ 主流程 ============
async function main() {
  initLogDir();
  logSection('🎬 YOLO LAB SEO 批量自动化 演示模式 v3.0');

  log(`📊 配置: ${CONFIG.TOTAL_POSTS} 篇文章 | 延迟: ${CONFIG.BATCH_DELAY}ms`, 'cyan');
  log(`⏱️  预计时间: ${((CONFIG.TOTAL_POSTS * CONFIG.BATCH_DELAY) / 1000 / 60).toFixed(1)} 分钟`, 'cyan');
  console.log('');

  const tracker = new ProgressTracker(CONFIG.TOTAL_POSTS);
  const postsPerPage = 50;

  // 模拟分页处理
  for (let page = 1; page <= Math.ceil(CONFIG.TOTAL_POSTS / postsPerPage); page++) {
    const start = (page - 1) * postsPerPage + 1;
    const end = Math.min(page * postsPerPage, CONFIG.TOTAL_POSTS);

    log(`📄 处理第 ${page} 页 (文章 ${start}-${end})...`, 'blue');

    for (let postId = start; postId <= end; postId++) {
      try {
        const title = `Article Title #${postId}`;

        // 模拟 SEO 生成
        const seo = simulateSeoGeneration(postId, title);

        // 模拟处理
        tracker.addSuccess(postId);

        if (postId % 10 === 0) {
          log(`  [${tracker.processed}/${CONFIG.TOTAL_POSTS}] ✓ #${postId}: "${title.substring(0, 30)}..."`, 'green');
        }

      } catch (err) {
        tracker.addFailed(postId, err.message);
        log(`  [${tracker.processed}/${CONFIG.TOTAL_POSTS}] ✗ #${postId}: ${err.message}`, 'red');
      }

      // 批次延迟
      await new Promise(r => setTimeout(r, CONFIG.BATCH_DELAY));

      // 里程碑报告
      if (CONFIG.MILESTONES.includes(tracker.processed)) {
        tracker.save();
        const stats = tracker.getStats();
        logMilestone(tracker.processed, CONFIG.TOTAL_POSTS);
        log(`✓ 成功: ${tracker.successful} | ✗ 失败: ${tracker.failed} | ⊘ 跳过: ${tracker.skipped}`, 'cyan');
        log(`⏱️  耗时: ${Math.round(stats.elapsed)}秒 | 速率: ${stats.rate.toFixed(1)}/分钟`, 'cyan');
        log(`⏳ 剩余: ${Math.round(stats.remaining)}分钟`, 'yellow');
        console.log('');
      }
    }
  }

  // 最终报告
  tracker.save();
  logSection('📊 批量 SEO 优化完成报告');

  const stats = tracker.getStats();
  const percentage = Math.round(tracker.successful / tracker.processed * 100);

  log(`总处理文章数: ${tracker.processed}`, 'cyan');
  log(`✓ 成功: ${tracker.successful} (${percentage}%)`, 'green');
  log(`✗ 失败: ${tracker.failed}`, tracker.failed > 0 ? 'red' : 'cyan');
  log(`⊘ 跳过: ${tracker.skipped}`, 'yellow');
  log(`⏱️  总耗时: ${Math.round(stats.elapsed)}秒 (${(stats.elapsed / 60).toFixed(1)} 分钟)`, 'cyan');
  log(`📈 平均速率: ${stats.rate.toFixed(1)} 篇/分钟`, 'cyan');

  if (tracker.failedPosts.length > 0) {
    console.log('');
    log(`⚠️  失败的文章 ID 样本: ${tracker.failedPosts.slice(0, 5).map(p => p.id).join(', ')}...`, 'yellow');
  }

  log(`\n📁 详细日志已保存到: ${CONFIG.LOG_DIR}`, 'cyan');
  logSection('演示完成 - 已生成进度日志');

  // 显示日志内容摘要
  if (fs.existsSync(CONFIG.PROGRESS_FILE)) {
    const progress = JSON.parse(fs.readFileSync(CONFIG.PROGRESS_FILE, 'utf8'));
    log(`📋 进度文件: ${CONFIG.PROGRESS_FILE}`, 'cyan');
    log(`   处理: ${progress.processed}/${progress.total}`, 'cyan');
    log(`   成功: ${progress.successful}`, 'cyan');
    log(`   失败: ${progress.failed}`, 'cyan');
  }

  process.exit(0);
}

// ============ 执行 ============
main().catch(err => {
  log(`✗ 致命错误: ${err.message}`, 'red');
  process.exit(1);
});
