#!/usr/bin/env node

/**
 * WordPress REST API SEO Optimization - Improved v2
 * Real execution with robust error handling
 */

const https = require('https');
const fs = require('fs');
const path = require('path');

// Configuration
const WP_DOMAIN = 'yololab.net';
const WP_USERNAME = 'yololab.life@gmail.com';
const WP_PASSWORD = 'WVOD RQw4 62NK 5BPl 1lTE lryv';
const WP_AUTH = Buffer.from(`${WP_USERNAME}:${WP_PASSWORD}`).toString('base64');

const TOTAL_ARTICLES = 2725;
const BATCH_SIZE = 100;
const TOTAL_PAGES = Math.ceil(TOTAL_ARTICLES / BATCH_SIZE);

// Progress tracking
let processed = 0;
let updated = 0;
let skipped = 0;
let failed = 0;
const failedIds = [];
const startTime = Date.now();
let reportBuffer = [];

/**
 * Make HTTPS request with proper error handling
 */
function makeRequest(options, payload = null) {
  return new Promise((resolve, reject) => {
    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', (chunk) => { data += chunk; });
      res.on('end', () => {
        resolve({ status: res.statusCode, data, headers: res.headers });
      });
    });

    req.on('error', (e) => {
      reject(new Error(`HTTP request error: ${e.message}`));
    });

    req.setTimeout(15000, () => {
      req.destroy();
      reject(new Error('Request timeout'));
    });

    if (payload) {
      req.write(payload);
    }
    req.end();
  });
}

/**
 * Fetch articles from WordPress REST API
 */
async function fetchPage(pageNum) {
  const options = {
    hostname: WP_DOMAIN,
    port: 443,
    path: `/wp-json/wp/v2/posts?per_page=${BATCH_SIZE}&page=${pageNum}&_fields=id,title,meta,excerpt`,
    method: 'GET',
    headers: {
      'Authorization': `Basic ${WP_AUTH}`,
      'User-Agent': 'Claude Code SEO Batch v2'
    }
  };

  try {
    const result = await makeRequest(options);
    if (result.status !== 200) {
      throw new Error(`HTTP ${result.status}`);
    }
    return JSON.parse(result.data);
  } catch (e) {
    throw new Error(`Fetch page ${pageNum} failed: ${e.message}`);
  }
}

/**
 * Generate SEO title and description
 */
function generateSEO(postTitle, postExcerpt) {
  try {
    const cleanTitle = postTitle.replace(/<[^>]*>/g, '').substring(0, 50);
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
  } catch (e) {
    throw new Error(`SEO generation error: ${e.message}`);
  }
}

/**
 * Update post metadata in WordPress
 */
async function updatePost(postId, seoTitle, seoDescription) {
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
      'User-Agent': 'Claude Code SEO Batch v2'
    }
  };

  try {
    const result = await makeRequest(options, payload);
    if (result.status !== 200) {
      throw new Error(`HTTP ${result.status}`);
    }
    return true;
  } catch (e) {
    throw new Error(`Update post ${postId} failed: ${e.message}`);
  }
}

/**
 * Format elapsed time
 */
function formatTime(ms) {
  const seconds = Math.floor(ms / 1000);
  const minutes = Math.floor(seconds / 60);
  return minutes > 0 ? `${minutes}m ${seconds % 60}s` : `${seconds}s`;
}

/**
 * Main batch processing loop
 */
async function runBatch() {
  console.log(`
╔══════════════════════════════════════════════════════════════╗
║     WordPress REST API SEO Batch Processor v2               ║
║     Target: yololab.net (2,725 articles across 28 pages)    ║
╚══════════════════════════════════════════════════════════════╝

[START] ${new Date().toISOString()}
`);

  // Test connectivity first
  try {
    console.log('[TEST] Verifying WordPress REST API connectivity...');
    const testPage = await fetchPage(1);
    console.log(`[OK] API responds: ${testPage.length} posts fetched from page 1\n`);
  } catch (e) {
    console.error(`[FATAL] API test failed: ${e.message}`);
    process.exit(1);
  }

  for (let page = 1; page <= TOTAL_PAGES; page++) {
    try {
      const posts = await fetchPage(page);

      if (!posts || posts.length === 0) {
        console.log(`[PAGE ${page}] No posts found, stopping.`);
        break;
      }

      console.log(`[PAGE ${page}/${TOTAL_PAGES}] Processing ${posts.length} posts...`);

      for (const post of posts) {
        processed++;

        // Skip if already has SEO title
        if (post.meta && post.meta.jetpack_seo_html_title) {
          skipped++;
          continue;
        }

        try {
          // Generate SEO metadata
          const seo = generateSEO(post.title.rendered, post.excerpt?.rendered || '');

          // Update WordPress
          await updatePost(post.id, seo.title, seo.description);
          updated++;

          // Log every 10 posts
          if (processed % 10 === 0) {
            console.log(`  [${processed}] ID ${post.id}: ✅ (${seo.title.length}ch title)`);
          }

          // Throttle: 200ms between API calls
          await new Promise(r => setTimeout(r, 200));
        } catch (e) {
          failed++;
          failedIds.push(post.id);
          console.log(`  [${processed}] ID ${post.id}: ❌ ${e.message}`);
          await new Promise(r => setTimeout(r, 500)); // Backoff on error
        }
      }

      // Milestone reporting
      if (processed >= 100 && processed % 100 === 0) {
        const elapsed = formatTime(Date.now() - startTime);
        const rate = updated > 0 ? ((updated / (processed - skipped)) * 100).toFixed(1) : '0.0';
        console.log(`
[MILESTONE] ✅ ${processed}/2725
[STATS] Updated: ${updated}, Skipped: ${skipped}, Failed: ${failed}
[RATE] Success: ${rate}%, Elapsed: ${elapsed}
`);
      }
    } catch (e) {
      console.log(`[PAGE ${page}] Error: ${e.message}`);
      await new Promise(r => setTimeout(r, 2000)); // Back off on page error
    }
  }

  // Final report
  const totalElapsed = formatTime(Date.now() - startTime);
  const finalRate = updated > 0 ? ((updated / (processed - skipped)) * 100).toFixed(1) : '0.0';

  const report = `
╔══════════════════════════════════════════════════════════════╗
║                  BATCH PROCESSING COMPLETE                  ║
╚══════════════════════════════════════════════════════════════╝

[FINAL STATS]
  Total Processed: ${processed}/${TOTAL_ARTICLES}
  Updated: ${updated}
  Skipped: ${skipped}
  Failed: ${failed}
  Success Rate: ${finalRate}%
  Total Elapsed: ${totalElapsed}

${failed > 0 ? `[FAILED IDS] ${failedIds.join(', ')}\n` : ''}[COMPLETION] ${new Date().toISOString()}
`;

  console.log(report);

  // Save report
  const reportData = {
    timestamp: new Date().toISOString(),
    total_processed: processed,
    updated: updated,
    skipped: skipped,
    failed: failed,
    success_rate: parseFloat(finalRate),
    elapsed_ms: Date.now() - startTime,
    failed_ids: failedIds
  };

  // Ensure output directory exists
  const outputDir = path.join(__dirname, '../seo-optimization-output');
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  fs.writeFileSync(
    path.join(outputDir, 'batch-report-v2.json'),
    JSON.stringify(reportData, null, 2)
  );

  console.log(`[REPORT] Saved to: seo-optimization-output/batch-report-v2.json`);
}

// Execute
runBatch().catch(e => {
  console.error('[FATAL]', e.message);
  process.exit(1);
});
