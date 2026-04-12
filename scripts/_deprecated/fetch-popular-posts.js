#!/usr/bin/env node
/**
 * Fetch Popular Posts from YOLO LAB
 *
 * Retrieves top articles by pageviews and generates popular-posts.json
 *
 * Usage:
 *   node scripts/fetch-popular-posts.js                 # Fetch from API
 *   node scripts/fetch-popular-posts.js --test-api      # Test API connection
 *   node scripts/fetch-popular-posts.js --mock           # Use mock data (development)
 *   node scripts/fetch-popular-posts.js --sample         # Use sample tier1 articles
 */

const https = require('https');
const fs = require('fs');
const path = require('path');

// Configuration - read from environment or hardcoded defaults
const JWT_TOKEN = process.env.WORDPRESS_DOT_COM_TOKEN ||
                  process.env.WP_COM_TOKEN ||
                  'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJodHRwczovL3lvbG9sYWIubmV0IiwiaWF0IjoxNzc1NjU1MjM5LCJleHAiOjE3NzU2NzY4MzksInVzZXJfaWQiOjEyNTc4MzMwMCwianRpIjoiWTNNWEFDVHVqMUZ2Y1hBTjFKOGgwNDVxdmNSYTBYNHkifQ.2DfQfqYo-JI-7poXnwWsMMlEDQK9qbpTML-M6NJ2uyc';

const SITE_ID = process.env.YOLO_LAB_SITE_ID || '133512998';
const API_BASE = 'public-api.wordpress.com';
const OUTPUT_FILE = path.join(__dirname, '..', 'data', 'popular-posts.json');
const CACHE_MAX_AGE_DAYS = parseInt(process.env.CACHE_MAX_AGE_DAYS || '7');

// Mock data for testing (from tier1-articles.json structure)
const MOCK_POPULAR_POSTS = [
  { id: 27155, title: 'ARTICLE_27155', views: 350 },
  { id: 28183, title: 'ARTICLE_28183', views: 298 },
  { id: 30591, title: 'ARTICLE_30591', views: 280 },
  { id: 27412, title: 'ARTICLE_27412', views: 265 },
  { id: 34221, title: 'ARTICLE_34221', views: 252 },
  { id: 30369, title: 'ARTICLE_30369', views: 245 },
  { id: 26788, title: 'ARTICLE_26788', views: 238 },
  { id: 27744, title: 'ARTICLE_27744', views: 220 }
];

// Helper function for HTTPS requests with detailed logging
function makeRequest(method, hostname, path, body = null, verbose = false) {
  return new Promise((resolve, reject) => {
    const headers = {
      'Content-Type': 'application/json',
      'User-Agent': 'YOLO-Popular-Posts-Fetcher/2.0',
      'Authorization': `Bearer ${JWT_TOKEN}`
    };

    const options = {
      hostname,
      port: 443,
      path,
      method,
      headers,
      timeout: 10000
    };

    if (verbose) {
      console.log(`  [DEBUG] ${method} ${hostname}${path}`);
      console.log(`  [DEBUG] Headers: ${JSON.stringify(headers, null, 2)}`);
    }

    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          const result = JSON.parse(data);
          if (verbose) {
            console.log(`  [DEBUG] Response status: ${res.statusCode}`);
            console.log(`  [DEBUG] Response body (first 200 chars): ${JSON.stringify(result).substring(0, 200)}`);
          }
          resolve({ status: res.statusCode, data: result, headers: res.headers });
        } catch (e) {
          if (verbose) {
            console.log(`  [DEBUG] Response status: ${res.statusCode}`);
            console.log(`  [DEBUG] Response body (raw, first 200 chars): ${data.substring(0, 200)}`);
          }
          resolve({ status: res.statusCode, data, headers: res.headers });
        }
      });
    });

    req.on('timeout', () => {
      req.abort();
      reject(new Error('Request timeout (10s)'));
    });

    req.on('error', reject);
    if (body) req.write(JSON.stringify(body));
    req.end();
  });
}

// Test API connection
async function testApiConnection() {
  console.log('\n📡 Testing Jetpack Stats API connection...\n');

  try {
    // Try Jetpack Stats endpoint
    const jResponse = await makeRequest('GET', 'yololab.net', '/wp-json/jetpack/v4/stats/posts');
    console.log(`✓ Jetpack endpoint: ${jResponse.status}`);

    if (jResponse.status === 200) {
      console.log('  Sample response:', JSON.stringify(jResponse.data).substring(0, 100) + '...');
      return true;
    } else if (jResponse.status === 403 || jResponse.status === 401) {
      console.log(`⚠ Jetpack API requires authentication. Status: ${jResponse.status}`);
      return false;
    }
  } catch (error) {
    console.error(`✗ Jetpack API error: ${error.message}`);
  }

  try {
    // Fallback to WordPress.com v1.1 API
    console.log('\n📡 Trying WordPress.com REST API v1.1...\n');
    const wpResponse = await makeRequest('GET', API_BASE, `/rest/v1.1/sites/${SITE_ID}/posts?number=100&status=publish`);
    console.log(`✓ WordPress.com API: ${wpResponse.status}`);

    if (wpResponse.status === 200) {
      console.log(`  Found ${wpResponse.data.posts ? wpResponse.data.posts.length : 0} posts`);
      return true;
    }
  } catch (error) {
    console.error(`✗ WordPress.com API error: ${error.message}`);
  }

  return false;
}

// Fetch from Jetpack Stats API (multiple endpoint strategies)
async function fetchFromJetpackStats() {
  console.log('\n📊 Fetching from Jetpack Stats API...\n');

  const endpoints = [
    // Strategy 1: Direct Jetpack Stats endpoint
    {
      name: 'Jetpack v4 Stats (posts)',
      path: '/wp-json/jetpack/v4/stats/posts?period=month&quantity=20'
    },
    // Strategy 2: WordPress REST v2 with views meta
    {
      name: 'WordPress REST v2 posts',
      path: '/wp-json/wp/v2/posts?per_page=100&status=publish&orderby=modified'
    },
    // Strategy 3: Custom stats endpoint
    {
      name: 'Jetpack v4 Stats (top posts)',
      path: '/wp-json/jetpack/v4/stats/top-posts?period=month'
    }
  ];

  for (const endpoint of endpoints) {
    try {
      console.log(`  Trying: ${endpoint.name}`);
      const response = await makeRequest('GET', 'yololab.net', endpoint.path);

      if (response.status === 200) {
        const posts = parseJetpackResponse(response.data, endpoint.name);
        if (posts && posts.length > 0) {
          console.log(`✓ Retrieved ${posts.length} top posts from Jetpack Stats`);
          return posts;
        }
      } else if (response.status === 403 || response.status === 401) {
        console.log(`  ⚠ Authentication required (${response.status}). Trying next endpoint...`);
      }
    } catch (error) {
      console.log(`  ⚠ ${endpoint.name}: ${error.message}`);
      continue;
    }
  }

  console.log('⚠ All Jetpack endpoints failed.');
  return null;
}

// Parse Jetpack API response (handles multiple formats)
function parseJetpackResponse(data, endpointName) {
  if (!data) return null;

  let posts = [];

  // Format 1: Array of posts with views
  if (Array.isArray(data)) {
    posts = data
      .filter(p => p.views > 0 || p.views_short > 0)
      .sort((a, b) => (b.views || b.views_short || 0) - (a.views || a.views_short || 0))
      .slice(0, 8)
      .map((post, index) => ({
        id: post.post_id || post.ID || post.id,
        title: post.post_title || post.title || 'Untitled',
        views: post.views || post.views_short || 0,
        rank: index + 1
      }));
  }
  // Format 2: Object with 'data' array
  else if (data.data && Array.isArray(data.data)) {
    posts = data.data
      .filter(p => p.views > 0)
      .sort((a, b) => (b.views || 0) - (a.views || 0))
      .slice(0, 8)
      .map((post, index) => ({
        id: post.post_id || post.ID || post.id,
        title: post.post_title || post.title || 'Untitled',
        views: post.views || 0,
        rank: index + 1
      }));
  }
  // Format 3: WordPress REST v2 posts (need to calculate views)
  else if (data.posts && Array.isArray(data.posts)) {
    posts = data.posts
      .slice(0, 8)
      .map((post, index) => ({
        id: post.ID,
        title: post.title,
        views: post.views || 0,
        rank: index + 1
      }));
  }

  return posts.length > 0 ? posts : null;
}

// Fetch from WordPress.com v1.1 API with multiple parameter strategies
async function fetchFromWordPressAPI(maxRetries = 2) {
  console.log('\n📚 Fetching from WordPress.com REST API...\n');

  // Multiple parameter combinations to try
  const paramVariants = [
    // Variant 1: Minimal parameters
    `/rest/v1.1/sites/${SITE_ID}/posts?number=100&status=publish`,
    // Variant 2: With fields
    `/rest/v1.1/sites/${SITE_ID}/posts?number=100&status=publish&fields=ID,title,views`,
    // Variant 3: Without views field (may not be available)
    `/rest/v1.1/sites/${SITE_ID}/posts?number=50&status=publish`
  ];

  for (let paramIndex = 0; paramIndex < paramVariants.length; paramIndex++) {
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        const path = paramVariants[paramIndex];
        console.log(`  Variant ${paramIndex + 1}: Attempt ${attempt}/${maxRetries}...`);

        const response = await makeRequest('GET', API_BASE, path);

        // Log detailed response for debugging
        if (response.status !== 200) {
          console.log(`    Status: ${response.status}`);
          if (response.data && typeof response.data === 'object') {
            if (response.data.message) console.log(`    Message: ${response.data.message}`);
            if (response.data.error) console.log(`    Error: ${response.data.error}`);
          }
        }

        if (response.status === 200 && response.data.posts && Array.isArray(response.data.posts)) {
          // Parse posts with views
          const posts = response.data.posts
            .filter(p => p.ID && (p.views > 0 || !p.views)) // Include all posts if views not available
            .sort((a, b) => (b.views || 0) - (a.views || 0))
            .slice(0, 8)
            .map((post, index) => ({
              id: post.ID,
              title: post.title || 'Untitled',
              views: post.views || 0,
              modified: post.modified,
              rank: index + 1
            }));

          if (posts.length > 0) {
            console.log(`✓ Retrieved ${posts.length} posts from WordPress.com API`);
            if (posts[0].views > 0) {
              console.log(`  Top article views: ${posts[0].views}`);
            } else {
              console.log(`  (Views data not available in response)`);
            }
            return posts;
          }
        } else if (response.status === 401 || response.status === 403) {
          console.log(`✗ Authentication failed (${response.status}). Skipping other variants.`);
          return null;
        }
      } catch (error) {
        console.log(`    Error: ${error.message}`);
        if (attempt < maxRetries) {
          const delayMs = 1000 * attempt;
          await new Promise(resolve => setTimeout(resolve, delayMs));
        }
      }
    }
  }

  console.log('✗ All WordPress.com API variants exhausted');
  return null;
}

// Generate popular posts configuration
function generateConfig(popularPosts) {
  return {
    generated_at: new Date().toISOString(),
    period: '30_days',
    version: '1.0',
    popular_posts: popularPosts,
    include_ids: popularPosts.map(p => p.id),
    exclude_ids: [],
    meta: {
      source: 'jetpack_stats',
      total_count: popularPosts.length,
      last_updated: new Date().toISOString()
    }
  };
}

// Save configuration to file
function saveConfig(config) {
  const dir = path.dirname(OUTPUT_FILE);
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }

  fs.writeFileSync(OUTPUT_FILE, JSON.stringify(config, null, 2));
  console.log(`\n✓ Saved config to: ${OUTPUT_FILE}`);
  console.log(`  Include IDs: ${config.include_ids.join(', ')}`);

  return OUTPUT_FILE;
}

// Load existing configuration as fallback
function loadExistingConfig() {
  try {
    const data = fs.readFileSync(OUTPUT_FILE, 'utf8');
    const config = JSON.parse(data);
    console.log(`✓ Loaded existing config from: ${OUTPUT_FILE}`);
    return config;
  } catch (error) {
    console.log(`⚠ No existing config found: ${error.message}`);
    return null;
  }
}

// Main execution with comprehensive error handling
async function main() {
  console.log('\n╔════════════════════════════════════════════════════════════════╗');
  console.log('║  YOLO LAB Popular Posts Fetcher v2.0                          ║');
  console.log('║  Generates popular-posts.json for homepage deployment         ║');
  console.log('╚════════════════════════════════════════════════════════════════╝');

  const args = process.argv.slice(2);

  // Handle CLI arguments
  if (args.includes('--test-api')) {
    const success = await testApiConnection();
    process.exit(success ? 0 : 1);
  }

  if (args.includes('--mock')) {
    console.log('\n🔧 Using mock data (development mode)\n');
    const config = generateConfig(MOCK_POPULAR_POSTS);
    saveConfig(config);
    console.log('✓ Mock configuration saved\n');
    process.exit(0);
  }

  if (args.includes('--sample')) {
    console.log('\n📋 Using sample tier1 articles\n');
    const samplePosts = MOCK_POPULAR_POSTS;
    const config = generateConfig(samplePosts);
    saveConfig(config);
    console.log('✓ Sample configuration saved\n');
    process.exit(0);
  }

  // Cascade: Try real APIs, then fallback to cache, then mock
  let popularPosts = null;
  let source = null;

  // ─────────────────────────────────────────────────────────────
  // Attempt 1: Jetpack Stats API (preferred)
  // ─────────────────────────────────────────────────────────────
  console.log('\n📡 FETCH STRATEGY 1: Jetpack Stats API (preferred)');
  console.log('─'.repeat(64));
  popularPosts = await fetchFromJetpackStats();
  if (popularPosts && popularPosts.length > 0) {
    source = 'jetpack_stats';
    console.log(`✓ Success! Will use ${popularPosts.length} articles from Jetpack Stats\n`);
  }

  // ─────────────────────────────────────────────────────────────
  // Attempt 2: WordPress.com REST API (backup)
  // ─────────────────────────────────────────────────────────────
  if (!popularPosts || popularPosts.length === 0) {
    console.log('\n📡 FETCH STRATEGY 2: WordPress.com REST API (backup)');
    console.log('─'.repeat(64));
    popularPosts = await fetchFromWordPressAPI();
    if (popularPosts && popularPosts.length > 0) {
      source = 'wordpress_rest_api';
      console.log(`✓ Success! Will use ${popularPosts.length} articles from WordPress API\n`);
    }
  }

  // ─────────────────────────────────────────────────────────────
  // Fallback 3: Use existing cached config
  // ─────────────────────────────────────────────────────────────
  if (!popularPosts || popularPosts.length === 0) {
    console.log('\n📚 FALLBACK 1: Cached Configuration');
    console.log('─'.repeat(64));
    const existingConfig = loadExistingConfig();
    if (existingConfig && existingConfig.popular_posts && existingConfig.popular_posts.length > 0) {
      console.log('✓ Using cached popular posts from last successful fetch');
      console.log(`  Last updated: ${existingConfig.meta.last_updated}`);
      console.log(`  Age: ${Math.floor((Date.now() - new Date(existingConfig.meta.last_updated)) / 86400000)} days\n`);
      process.exit(0);
    }
  }

  // ─────────────────────────────────────────────────────────────
  // Fallback 4: Use mock data as final resort
  // ─────────────────────────────────────────────────────────────
  if (!popularPosts || popularPosts.length === 0) {
    console.log('\n⚠️  FALLBACK 2: Mock Data (DEVELOPMENT MODE)');
    console.log('─'.repeat(64));
    console.log('⚠️  All API attempts failed. Using mock data as fallback.');
    console.log('   This indicates a connectivity issue - please investigate!\n');
    popularPosts = MOCK_POPULAR_POSTS;
    source = 'mock_data';
  }

  // ─────────────────────────────────────────────────────────────
  // Generate and save configuration
  // ─────────────────────────────────────────────────────────────
  console.log('\n📝 GENERATING CONFIGURATION');
  console.log('─'.repeat(64));
  const config = generateConfig(popularPosts);
  config.meta.source = source || 'unknown';
  saveConfig(config);

  console.log('\n✅ EXECUTION SUMMARY');
  console.log('─'.repeat(64));
  console.log(`Source: ${source || 'unknown'}`);
  console.log(`Articles: ${popularPosts.length}/8`);
  console.log(`IDs: [${config.include_ids.join(', ')}]`);
  console.log(`Config: ${OUTPUT_FILE}`);
  console.log('\n✓ Popular posts configuration generated successfully\n');

  process.exit(0);
}

main().catch(error => {
  console.error('\n✗ Fatal error:', error.message);
  process.exit(1);
});
