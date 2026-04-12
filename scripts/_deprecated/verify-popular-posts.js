#!/usr/bin/env node
/**
 * Verify YOLO LAB Popular Posts Setup
 *
 * Checks that all components are properly installed and configured
 * Usage: node scripts/verify-popular-posts.js
 */

const fs = require('fs');
const path = require('path');

// Configuration
const PROJECT_DIR = path.join(__dirname, '..');
const CHECKS = [
  {
    name: 'Fetch Script',
    path: path.join(PROJECT_DIR, 'scripts', 'fetch-popular-posts.js'),
    type: 'file'
  },
  {
    name: 'Deploy Script',
    path: path.join(PROJECT_DIR, 'scripts', 'deploy-yolo-homepage.js'),
    type: 'file'
  },
  {
    name: 'Config File',
    path: path.join(PROJECT_DIR, 'data', 'popular-posts.json'),
    type: 'file'
  },
  {
    name: 'Update Shell Script',
    path: path.join(PROJECT_DIR, 'scripts', 'update-popular-posts.sh'),
    type: 'file'
  },
  {
    name: 'Update Batch Script',
    path: path.join(PROJECT_DIR, 'scripts', 'update-popular-posts.bat'),
    type: 'file'
  },
  {
    name: 'Logs Directory',
    path: path.join(PROJECT_DIR, 'logs'),
    type: 'directory'
  },
  {
    name: 'Documentation Guide',
    path: path.join(PROJECT_DIR, 'docs', 'FETCH_POPULAR_POSTS_GUIDE.md'),
    type: 'file'
  },
  {
    name: 'Scheduled Updates Guide',
    path: path.join(PROJECT_DIR, 'docs', 'SCHEDULED_UPDATES_GUIDE.md'),
    type: 'file'
  }
];

// Helper functions
function fileExists(filepath) {
  try {
    return fs.existsSync(filepath);
  } catch (e) {
    return false;
  }
}

function dirExists(dirpath) {
  try {
    return fs.statSync(dirpath).isDirectory();
  } catch (e) {
    return false;
  }
}

function getFileSize(filepath) {
  try {
    return fs.statSync(filepath).size;
  } catch (e) {
    return 0;
  }
}

function formatBytes(bytes) {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

// Verification
console.log('\n╔════════════════════════════════════════════════════════════════╗');
console.log('║  YOLO LAB Popular Posts - System Verification                 ║');
console.log('╚════════════════════════════════════════════════════════════════╝\n');

let passed = 0;
let failed = 0;

// Check each component
console.log('📋 Component Checks:\n');

CHECKS.forEach((check, index) => {
  let status, details;

  if (check.type === 'file') {
    if (fileExists(check.path)) {
      const size = getFileSize(check.path);
      status = '✓';
      details = `(${formatBytes(size)})`;
      passed++;
    } else {
      status = '✗';
      details = '(NOT FOUND)';
      failed++;
    }
  } else if (check.type === 'directory') {
    if (dirExists(check.path)) {
      status = '✓';
      details = '(directory exists)';
      passed++;
    } else {
      status = '✗';
      details = '(NOT FOUND)';
      failed++;
    }
  }

  const line = `${index + 1}. ${check.name}`;
  const padding = ' '.repeat(Math.max(0, 35 - line.length));
  console.log(`  ${status} ${line}${padding} ${details}`);
});

console.log('\n─────────────────────────────────────────────────────────────────\n');

// Check config validity
if (fileExists(path.join(PROJECT_DIR, 'data', 'popular-posts.json'))) {
  try {
    const config = JSON.parse(
      fs.readFileSync(path.join(PROJECT_DIR, 'data', 'popular-posts.json'), 'utf8')
    );

    console.log('📊 Configuration Validity:\n');

    const configChecks = [
      {
        field: 'version',
        ok: !!config.version,
        value: config.version
      },
      {
        field: 'generated_at',
        ok: !!config.generated_at,
        value: config.generated_at
      },
      {
        field: 'include_ids array',
        ok: Array.isArray(config.include_ids) && config.include_ids.length > 0,
        value: `${config.include_ids ? config.include_ids.length : 0} IDs`
      },
      {
        field: 'popular_posts array',
        ok: Array.isArray(config.popular_posts) && config.popular_posts.length > 0,
        value: `${config.popular_posts ? config.popular_posts.length : 0} posts`
      },
      {
        field: 'meta.source',
        ok: !!config.meta && !!config.meta.source,
        value: config.meta ? config.meta.source : 'N/A'
      }
    ];

    configChecks.forEach((check, index) => {
      const status = check.ok ? '✓' : '✗';
      const line = `  ${status} ${check.field}`;
      const padding = ' '.repeat(Math.max(0, 35 - line.length));
      console.log(`${line}${padding} ${check.value}`);
    });

    // Calculate config age
    const configTime = new Date(config.generated_at);
    const now = new Date();
    const ageMs = now - configTime;
    const ageDays = Math.floor(ageMs / 86400000);
    const ageHours = Math.floor((ageMs % 86400000) / 3600000);

    console.log(`\n  Generated: ${configTime.toISOString()}`);
    console.log(`  Age: ${ageDays}d ${ageHours}h`);
    console.log(`  Status: ${ageDays < 7 ? '✓ Fresh' : '⚠ Stale (> 7 days)'}`);
  } catch (e) {
    console.log(`✗ Configuration is invalid JSON: ${e.message}`);
    failed++;
  }
}

console.log('\n─────────────────────────────────────────────────────────────────\n');

// Summary
console.log('📈 Summary:\n');
console.log(`  ✓ Passed: ${passed}`);
console.log(`  ✗ Failed: ${failed}`);

const allChecks = CHECKS.length;
const percentPassed = Math.round((passed / allChecks) * 100);
console.log(`  Score: ${percentPassed}% (${passed}/${allChecks})`);

if (failed === 0) {
  console.log('\n✓ All checks passed! System is ready for use.\n');
  process.exit(0);
} else {
  console.log(`\n⚠ ${failed} check(s) failed. Please review the issues above.\n`);
  process.exit(1);
}
