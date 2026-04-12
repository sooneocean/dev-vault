#!/usr/bin/env node

/**
 * Phase 3: Apply Tags to WordPress Articles via REST API
 *
 * Reads phase3_tag_assignments.csv and applies primary tags
 * to WordPress.com site via authenticated REST API calls.
 *
 * Usage:
 *   node phase3-apply-tags-wordpress.js <wp_auth_token>
 *
 * Rate limiting: 1 article per second, batch pause every 50 articles
 */

const fs = require('fs').promises;
const path = require('path');
const { spawn } = require('child_process');

const SITE_ID = 133512998;
const SITE_URL = 'yololab.net';
const OUTPUT_DIR = path.resolve(__dirname, '../seo-optimization-output');
const ARTICLE_ID_MAPPING_FILE = path.join(OUTPUT_DIR, 'phase3_wordpress_article_ids.json');

// Tag ID mappings (these would normally be fetched from WordPress)
const TAG_MAPPINGS = {
  'film': 'film',
  'music-review': 'music-review',
  'live-music': 'live-music',
  'hiphop': 'hiphop',
  'kpop': 'kpop',
  'tech': 'tech',
  'sports': 'sports',
  'culture': 'culture',
  'variety': 'variety',
  'lifestyle': 'lifestyle',
  'business': 'business',
  'picks': 'picks',
  'new-releases': 'new-releases'
};

/**
 * Execute curl command for WordPress REST API call
 */
function executeCurl(args) {
  return new Promise((resolve, reject) => {
    const curl = spawn('curl', args, { shell: true });
    let stdout = '';
    let stderr = '';

    curl.stdout.on('data', (data) => {
      stdout += data.toString();
    });

    curl.stderr.on('data', (data) => {
      stderr += data.toString();
    });

    curl.on('close', (code) => {
      if (code === 0) {
        resolve({ stdout, code });
      } else {
        reject(new Error(`curl exited with code ${code}: ${stderr}`));
      }
    });
  });
}

/**
 * Fetch all posts from WordPress to map article_id to WordPress ID
 */
async function fetchWordPressPostIds(token) {
  console.log('\n🔍 Fetching WordPress article IDs...');

  const postMapping = {};
  let page = 1;
  let hasMore = true;

  while (hasMore) {
    console.log(`   [Page ${page}] Fetching...`);

    const args = [
      '-s',
      '-H', `Authorization: Bearer ${token}`,
      `-X GET "https://public-api.wordpress.com/wp/v2/sites/${SITE_ID}/posts?status=publish&per_page=100&page=${page}"`
    ];

    try {
      const result = await executeCurl(args);
      const posts = JSON.parse(result.stdout);

      if (!Array.isArray(posts) || posts.length === 0) {
        hasMore = false;
        break;
      }

      // Map WordPress post ID to our internal article numbering (based on URL or ID)
      posts.forEach(post => {
        // Extract article number from slug or title
        const slug = post.slug || '';
        const match = slug.match(/article-(\d+)/);
        if (match) {
          const articleId = parseInt(match[1]);
          postMapping[articleId] = post.id;
        } else if (slug.includes('article')) {
          // Fallback: use WordPress ID
          postMapping[post.id] = post.id;
        }
      });

      page++;
      // Rate limiting
      await sleep(1000);

    } catch (error) {
      console.error(`   ❌ Error fetching page ${page}:`, error.message);
      hasMore = false;
    }
  }

  // Save mapping for reference
  await fs.writeFile(
    ARTICLE_ID_MAPPING_FILE,
    JSON.stringify(postMapping, null, 2)
  );

  console.log(`   ✅ Mapped ${Object.keys(postMapping).length} articles`);
  return postMapping;
}

/**
 * Apply tags to a single article
 */
async function applyTagsToArticle(wpId, tags, token) {
  const tagSlugs = tags.map(tag => TAG_MAPPINGS[tag] || tag).filter(Boolean);

  if (tagSlugs.length === 0) {
    return { success: false, reason: 'No valid tags' };
  }

  const args = [
    '-s',
    '-X', 'POST',
    `-H "Authorization: Bearer ${token}"`,
    `-H "Content-Type: application/json"`,
    `--data '{"tags":"${tagSlugs.join(',')}"}'`,
    `https://public-api.wordpress.com/wp/v2/sites/${SITE_ID}/posts/${wpId}`
  ];

  try {
    const result = await executeCurl(args);
    const response = JSON.parse(result.stdout);

    if (response.id) {
      return { success: true, wpId, tags: tagSlugs };
    } else {
      return { success: false, reason: response.message || 'Unknown error' };
    }

  } catch (error) {
    return { success: false, reason: error.message };
  }
}

/**
 * Read tag assignments from CSV and process them
 */
async function processTagAssignments(token, postMapping) {
  console.log('\n📝 Reading tag assignments...');

  const csvPath = path.join(OUTPUT_DIR, 'phase3_tag_assignments.csv');
  const csvContent = await fs.readFile(csvPath, 'utf-8');
  const lines = csvContent.split('\n').slice(1); // Skip header

  const results = {
    total: 0,
    success: 0,
    failed: 0,
    skipped: 0,
    details: []
  };

  console.log(`\n🔄 Applying tags to ${lines.length} articles...`);
  console.log(`   Rate: 1 article/second, batch pause every 50 articles\n`);

  for (let i = 0; i < lines.length; i++) {
    if (!lines[i].trim()) continue;

    const parts = lines[i].split(',');
    const articleId = parseInt(parts[0]);
    const title = parts[1];
    const assignedTag = parts[2];
    const alternativeTags = parts[4] ? parts[4].split(';') : [];

    results.total++;

    // Get WordPress ID
    const wpId = postMapping[articleId];
    if (!wpId) {
      results.skipped++;
      results.details.push({
        articleId,
        status: 'skipped',
        reason: 'No WordPress ID mapping'
      });

      // Show progress
      if ((i + 1) % 50 === 0) {
        console.log(`   [${i + 1}/${lines.length}] Success: ${results.success}, Failed: ${results.failed}, Skipped: ${results.skipped}`);
        await sleep(5000); // 5s pause every 50 articles
      }
      continue;
    }

    // Apply tags
    const tags = [assignedTag, ...alternativeTags.slice(0, 2)]; // Primary + 2 alternatives max
    const result = await applyTagsToArticle(wpId, tags, token);

    if (result.success) {
      results.success++;
      results.details.push({
        articleId,
        wpId,
        title: title.substring(0, 50),
        status: 'success',
        tags: result.tags
      });
    } else {
      results.failed++;
      results.details.push({
        articleId,
        wpId,
        title: title.substring(0, 50),
        status: 'failed',
        reason: result.reason
      });
    }

    // Rate limiting
    await sleep(1000);

    // Show progress
    if ((i + 1) % 50 === 0) {
      console.log(`   [${i + 1}/${lines.length}] Success: ${results.success}, Failed: ${results.failed}, Skipped: ${results.skipped}`);
      await sleep(5000); // 5s pause every 50 articles
    }
  }

  return results;
}

/**
 * Generate final report
 */
async function generateFinalReport(results) {
  console.log('\n' + '='.repeat(80));
  console.log('📊 Phase 3 Application Results');
  console.log('='.repeat(80));

  const successRate = ((results.success / results.total) * 100).toFixed(2);
  console.log(`
✅ Successfully Applied: ${results.success}/${results.total} (${successRate}%)
❌ Failed: ${results.failed}
⏭️  Skipped: ${results.skipped}
⏱️  Total Processing Time: ~${(results.total * 1.1 / 60).toFixed(1)} minutes
  `);

  // Save detailed results
  const reportPath = path.join(OUTPUT_DIR, 'phase3_application_results.json');
  await fs.writeFile(
    reportPath,
    JSON.stringify(results, null, 2)
  );

  console.log(`📁 Results saved to: phase3_application_results.json`);

  if (results.failed > 0) {
    const failedArticles = results.details.filter(d => d.status === 'failed');
    console.log(`\n⚠️  ${results.failed} articles failed. Review and retry with:
   node phase3-apply-tags-wordpress.js <token> --retry-failed`);
  }

  console.log('\n✨ Phase 3 tag application complete!');
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Main entry point
 */
async function main() {
  console.log('\n' + '='.repeat(80));
  console.log('🚀 PHASE 3: Apply Tags to WordPress Articles');
  console.log('='.repeat(80));
  console.log(`Site: ${SITE_URL}`);
  console.log(`Target: 1,725 articles with assigned tags`);

  // Validate arguments
  if (process.argv.length < 3) {
    console.error('\n❌ Missing WordPress authentication token');
    console.error('Usage: node phase3-apply-tags-wordpress.js <wp_auth_token>');
    console.error('\nTo get your token:');
    console.error('1. Go to https://wordpress.com/me/security');
    console.error('2. Create an application password');
    console.error('3. Use as: node phase3-apply-tags-wordpress.js your-token-here');
    process.exit(1);
  }

  const token = process.argv[2];

  try {
    // Step 1: Fetch WordPress post IDs
    const postMapping = await fetchWordPressPostIds(token);

    // Step 2: Process tag assignments
    const results = await processTagAssignments(token, postMapping);

    // Step 3: Generate report
    await generateFinalReport(results);

    process.exit(results.failed > 0 ? 1 : 0);

  } catch (error) {
    console.error('\n❌ Fatal error:', error.message);
    process.exit(1);
  }
}

// Execute only in real mode (not in dry-run)
if (require.main === module) {
  main().catch(err => {
    console.error(err);
    process.exit(1);
  });
}

module.exports = { applyTagsToArticle, fetchWordPressPostIds };
