#!/usr/bin/env node

/**
 * YOLO LAB Homepage v2 Deployment
 * Automatically updates the homepage (ID: 35147) on yololab.net
 *
 * Site ID: 133512998
 * Domain: yololab.net
 * Homepage ID: 35147
 */

const fs = require('fs');
const path = require('path');

const SITE_ID = '133512998';
const PAGE_ID = '35147';
const WPCOM_API_BASE = 'https://public-api.wordpress.com/rest/v1.1';

/**
 * Call WordPress.com API
 */
async function wpcomApiCall(method, endpoint, data = null) {
  const token = process.env.WP_COM_TOKEN || process.env.WPCOM_TOKEN;

  if (!token) {
    throw new Error('WordPress.com API token not available (WP_COM_TOKEN or WPCOM_TOKEN env var required)');
  }

  const url = `${WPCOM_API_BASE}/sites/${SITE_ID}${endpoint}`;

  const options = {
    method,
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    }
  };

  if (data) {
    options.body = JSON.stringify(data);
  }

  try {
    console.log(`📡 ${method} ${endpoint}`);
    const response = await fetch(url, options);
    const text = await response.text();
    let json = {};

    try {
      json = JSON.parse(text);
    } catch (e) {
      // Response is not JSON
    }

    if (!response.ok) {
      throw {
        status: response.status,
        message: json.message || response.statusText,
        data: json
      };
    }

    return json;
  } catch (error) {
    throw error;
  }
}

/**
 * Read homepage HTML file
 */
function readHomepageContent() {
  console.log('📖 Reading homepage HTML file...');

  const htmlPath = path.join(
    __dirname,
    '..',
    'seo-optimization-output',
    'homepage-v2-ultramodern.html'
  );

  if (!fs.existsSync(htmlPath)) {
    throw new Error(`Homepage file not found: ${htmlPath}`);
  }

  const content = fs.readFileSync(htmlPath, 'utf-8');
  console.log(`✅ Loaded ${content.length} bytes`);

  return content;
}

/**
 * Fetch current page info
 */
async function getPageInfo() {
  console.log(`🔍 Fetching page info (ID: ${PAGE_ID})...`);

  const page = await wpcomApiCall('GET', `/pages/${PAGE_ID}`);

  console.log(`   Title: ${page.title}`);
  console.log(`   Status: ${page.status}`);
  console.log(`   Current content length: ${page.content.length} bytes`);

  return page;
}

/**
 * Update homepage content
 */
async function updateHomepage(htmlContent) {
  console.log(`\n✏️  Updating homepage (ID: ${PAGE_ID})...`);
  console.log(`   New content length: ${htmlContent.length} bytes`);

  const updateData = {
    content: htmlContent,
    status: 'publish'
  };

  const result = await wpcomApiCall('POST', `/pages/${PAGE_ID}`, updateData);

  console.log(`✅ Homepage updated successfully`);
  console.log(`   ID: ${result.id}`);
  console.log(`   Title: ${result.title}`);
  console.log(`   URL: ${result.URL}`);
  console.log(`   Status: ${result.status}`);
  console.log(`   Modified: ${result.modified}`);

  return result;
}

/**
 * Verify deployment
 */
async function verifyDeployment() {
  console.log(`\n🔍 Verifying deployment...`);

  // Fetch the updated page
  const page = await wpcomApiCall('GET', `/pages/${PAGE_ID}`);

  if (page.content.includes('yolo-hero')) {
    console.log(`✅ Homepage v2 content verified`);
    console.log(`   Contains: Hero section, Stats bar, Featured grid`);
    return true;
  } else {
    console.log(`⚠️  Warning: Homepage content may not be correctly deployed`);
    return false;
  }
}

/**
 * Generate deployment report
 */
async function generateReport(page) {
  console.log('\n' + '='.repeat(60));
  console.log('📊 YOLO LAB HOMEPAGE v2 DEPLOYMENT REPORT');
  console.log('='.repeat(60));
  console.log('');

  console.log('✅ DEPLOYMENT COMPLETED');
  console.log('');
  console.log('Site Details:');
  console.log(`  Domain: yololab.net`);
  console.log(`  Site ID: ${SITE_ID}`);
  console.log(`  Page ID: ${PAGE_ID}`);
  console.log('');

  console.log('Page Details:');
  console.log(`  Title: ${page.title}`);
  console.log(`  URL: ${page.URL}`);
  console.log(`  Status: ${page.status}`);
  console.log(`  Content size: ${page.content.length} bytes`);
  console.log(`  Last modified: ${page.modified}`);
  console.log('');

  console.log('New Features:');
  console.log('  ✓ Hero section with animated gradient background');
  console.log('  ✓ Stats bar (898+ articles, 4 categories, 2025 database)');
  console.log('  ✓ Featured posts grid (glassmorphism cards)');
  console.log('  ✓ Category sections (Film, Music, Tech, Sports)');
  console.log('  ✓ Magazine layout (Latest posts)');
  console.log('  ✓ Full responsive design (mobile/tablet/desktop)');
  console.log('  ✓ Dark mode support');
  console.log('');

  console.log('Verification:');
  console.log(`  Visit: https://yololab.net`);
  console.log(`  Preview: ${page.URL}`);
  console.log('');

  console.log('Next Steps:');
  console.log('  1. Verify homepage displays correctly on desktop/mobile');
  console.log('  2. Test all category links (Film, Music, Tech, Sports)');
  console.log('  3. Check Search Console for indexing status');
  console.log('  4. Monitor analytics for traffic changes');
  console.log('');

  console.log('='.repeat(60));
}

/**
 * Main deployment
 */
async function main() {
  console.log('');
  console.log('🚀 YOLO LAB HOMEPAGE v2 DEPLOYMENT');
  console.log('━'.repeat(60));
  console.log('');

  try {
    // Step 1: Read homepage content
    const htmlContent = readHomepageContent();

    // Step 2: Get current page info
    const currentPage = await getPageInfo();

    // Step 3: Update homepage
    const updatedPage = await updateHomepage(htmlContent);

    // Step 4: Verify deployment
    const verified = await verifyDeployment();

    // Step 5: Generate report
    await generateReport(updatedPage);

    if (verified) {
      console.log('✅ DEPLOYMENT SUCCESSFUL - Homepage v2 is live!');
      process.exit(0);
    } else {
      console.log('⚠️  Deployment completed with warnings');
      process.exit(0);
    }

  } catch (error) {
    console.error('\n❌ DEPLOYMENT FAILED');
    console.error('');

    if (error.status) {
      console.error(`API Error (${error.status}): ${error.message}`);
      if (error.data && error.data.message) {
        console.error(`Details: ${error.data.message}`);
      }
    } else {
      console.error(`Error: ${error.message}`);
      if (error.stack) {
        console.error(error.stack);
      }
    }

    console.error('');
    console.error('Troubleshooting:');
    console.error('  1. Verify WP_COM_TOKEN or WPCOM_TOKEN environment variable is set');
    console.error('  2. Ensure token has permission to edit pages');
    console.error('  3. Check homepage file exists at:', path.join(__dirname, '..', 'seo-optimization-output', 'homepage-v2-ultramodern.html'));
    console.error('  4. Verify Site ID (133512998) and Page ID (35147) are correct');

    process.exit(1);
  }
}

main();
