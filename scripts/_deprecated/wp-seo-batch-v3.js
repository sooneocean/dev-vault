#!/usr/bin/env node

/**
 * WordPress REST API SEO Optimization - v3 with Queue Management
 * Implements smart rate limiting and progress checkpointing
 */

const https = require('https');
const fs = require('fs');
const path = require('path');

const WP_DOMAIN = 'yololab.net';
const WP_USERNAME = 'yololab.life@gmail.com';
const WP_PASSWORD = 'WVOD RQw4 62NK 5BPl 1lTE lryv';
const WP_AUTH = Buffer.from(`${WP_USERNAME}:${WP_PASSWORD}`).toString('base64');

// Progress tracking
let processed = 0;
let updated = 0;
let skipped = 0;
let failed = 0;
const failedIds = [];
const startTime = Date.now();

/**
 * Simple queue for controlled concurrency
 */
class Queue {
  constructor(concurrency = 1) {
    this.concurrency = concurrency;
    this.running = 0;
    this.queue = [];
  }

  async run(fn) {
    while (this.running >= this.concurrency) {
      await new Promise(r => setTimeout(r, 50));
    }
    this.running++;
    try {
      return await fn();
    } finally {
      this.running--;
    }
  }
}

const queue = new Queue(2); // 2 concurrent requests max

/**
 * HTTPS request helper
 */
function httpsRequest(options, payload = null, retries = 1) {
  return new Promise((resolve, reject) => {
    const attempt = () => {
      const req = https.request(options, (res) => {
        let data = '';
        res.on('data', chunk => { data += chunk; });
        res.on('end', () => {
          resolve({ status: res.statusCode, data, headers: res.headers });
        });
      });

      req.on('error', (e) => {
        if (retries > 0) {
          console.log(`    [RETRY] ${options.path.split('/').pop() || 'request'}`);
          setTimeout(attempt, 1000);
        } else {
          reject(e);
        }
      });

      req.setTimeout(20000, () => {
        req.destroy();
        if (retries > 0) {
          console.log(`    [TIMEOUT-RETRY] ${options.path.split('/').pop() || 'request'}`);
          setTimeout(attempt, 1000);
        } else {
          reject(new Error('Request timeout'));
        }
      });

      if (payload) req.write(payload);
      req.end();
    };

    attempt();
  });
}

/**
 * Fetch page with queue management
 */
async function fetchPage(pageNum, batchSize = 100) {
  return queue.run(async () => {
    const options = {
      hostname: WP_DOMAIN,
      port: 443,
      path: `/wp-json/wp/v2/posts?per_page=${batchSize}&page=${pageNum}&_fields=id,title,meta,excerpt`,
      method: 'GET',
      headers: {
        'Authorization': `Basic ${WP_AUTH}`,
        'User-Agent': 'Claude SEO Batch'
      }
    };

    try {
      const result = await httpsRequest(options, null, 2);
      if (result.status !== 200) throw new Error(`HTTP ${result.status}`);
      return JSON.parse(result.data);
    } catch (e) {
      throw new Error(`Fetch page ${pageNum}: ${e.message}`);
    }
  });
}

/**
 * Update post with queue management
 */
async function updatePost(postId, seoTitle, seoDescription) {
  return queue.run(async () => {
    const payload = JSON.stringify({
      meta: {
        jetpack_seo_html_title: seoTitle,
        advanced_seo_description: seoDescription
      }
    });

    const options = {
      hostname: WP_DOMAIN,
      port: 443,
      path: `/wp-json/wp/v2/posts/${postId}`,
      method: 'POST',
      headers: {
        'Authorization': `Basic ${WP_AUTH}`,
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(payload),
        'User-Agent': 'Claude SEO Batch'
      }
    };

    try {
      const result = await httpsRequest(options, payload, 1);
      if (result.status !== 200) throw new Error(`HTTP ${result.status}`);
      return true;
    } catch (e) {
      throw new Error(`Update ${postId}: ${e.message}`);
    }
  });
}

/**
 * Generate SEO metadata
 */
function generateSEO(postTitle, postExcerpt) {
  const cleanTitle = (postTitle || '')
    .replace(/<[^>]*>/g, '')
    .substring(0, 50);

  const cleanExcerpt = (postExcerpt || '')
    .replace(/<[^>]*>/g, '')
    .replace(/&[a-z]+;/g, '')
    .substring(0, 100);

  const seoTitle = `${cleanTitle} - YOLOLAB`.substring(0, 60);
  const seoDescription = `${cleanExcerpt}...更多內容就在YOLOLAB`.substring(0, 160);

  return {
    title: seoTitle.trim(),
    description: seoDescription.trim()
  };
}

/**
 * Format time
 */
function formatTime(ms) {
  const seconds = Math.floor(ms / 1000);
  const minutes = Math.floor(seconds / 60);
  return minutes > 0 ? `${minutes}m ${seconds % 60}s` : `${seconds}s`;
}

/**
 * Checkpoint save
 */
function saveCheckpoint() {
  const data = {
    timestamp: new Date().toISOString(),
    processed,
    updated,
    skipped,
    failed,
    failed_ids: failedIds,
    elapsed_ms: Date.now() - startTime
  };
  const outDir = path.join(__dirname, '../seo-optimization-output');
  if (!fs.existsSync(outDir)) fs.mkdirSync(outDir, { recursive: true });
  fs.writeFileSync(path.join(outDir, 'checkpoint.json'), JSON.stringify(data, null, 2));
}

/**
 * Main processing
 */
async function runBatch() {
  console.log(`
╔════════════════════════════════════════════════════════════╗
║   WordPress REST API SEO Batch v3 (Queue-based)           ║
║   Target: yololab.net | 2,725 articles | 28 pages         ║
╚════════════════════════════════════════════════════════════╝

[START] ${new Date().toISOString()}
[CONCURRENCY] 2 concurrent HTTP requests
`);

  // Test connectivity
  try {
    console.log('[TEST] Checking API connectivity...');
    const testPage = await fetchPage(1);
    console.log(`[OK] API ready: ${testPage.length} posts/page\n`);
  } catch (e) {
    console.error(`[FATAL] API test failed: ${e.message}`);
    process.exit(1);
  }

  // Process pages
  for (let page = 1; page <= 28; page++) {
    try {
      const posts = await fetchPage(page);
      if (!posts || posts.length === 0) break;

      console.log(`[PAGE ${page}/28] ${posts.length} posts`);

      for (const post of posts) {
        processed++;

        // Skip if has SEO title
        if (post.meta?.jetpack_seo_html_title) {
          skipped++;
          continue;
        }

        try {
          const seo = generateSEO(post.title.rendered, post.excerpt?.rendered);
          await updatePost(post.id, seo.title, seo.description);
          updated++;

          // Log progress
          if (processed % 20 === 0) {
            const rate = ((updated / (processed - skipped)) * 100).toFixed(1);
            console.log(`  [${processed}] ✅ ${updated} updated | ${rate}% success`);
          }

          // Save checkpoint every 100
          if (processed % 100 === 0) {
            saveCheckpoint();
            console.log(`  [CHECKPOINT] Saved at post #${processed}`);
          }

          // Add delay between updates
          await new Promise(r => setTimeout(r, 100));
        } catch (e) {
          failed++;
          failedIds.push(post.id);
          console.log(`  [${processed}] ❌ ${e.message}`);
        }
      }
    } catch (e) {
      console.error(`[PAGE ${page}] Error: ${e.message}`);
    }
  }

  // Final report
  const elapsed = formatTime(Date.now() - startTime);
  const rate = updated > 0 ? ((updated / (processed - skipped)) * 100).toFixed(1) : '0';

  const report = `
╔════════════════════════════════════════════════════════════╗
║              BATCH PROCESSING COMPLETE                    ║
╚════════════════════════════════════════════════════════════╝

[RESULTS]
  Processed: ${processed}/2725
  Updated: ${updated}
  Skipped: ${skipped}
  Failed: ${failed}
  Success Rate: ${rate}%
  Elapsed: ${elapsed}

${failed > 0 ? `[FAILED] ${failedIds.join(', ')}\n` : ''}[END] ${new Date().toISOString()}
`;

  console.log(report);

  // Save final report
  const outDir = path.join(__dirname, '../seo-optimization-output');
  if (!fs.existsSync(outDir)) fs.mkdirSync(outDir, { recursive: true });

  fs.writeFileSync(path.join(outDir, 'final-report-v3.json'), JSON.stringify({
    timestamp: new Date().toISOString(),
    processed,
    updated,
    skipped,
    failed,
    success_rate: parseFloat(rate),
    elapsed_ms: Date.now() - startTime,
    failed_ids: failedIds
  }, null, 2));

  console.log(`[SAVED] Report: seo-optimization-output/final-report-v3.json`);
}

// Execute
runBatch().catch(e => {
  console.error('[FATAL]', e.message);
  process.exit(1);
});
