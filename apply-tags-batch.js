#!/usr/bin/env node

/**
 * Batch Tag Application Script
 * Applies tags to articles based on tag_application_report.csv
 */

const fs = require('fs');
const path = require('path');

// Simple CSV parser
function parseCSV(content) {
  const lines = content.trim().split('\n');
  const headers = lines[0].split(',').map(h => h.trim().replace(/^"|"$/g, ''));
  const result = [];

  for (let i = 1; i < lines.length; i++) {
    if (!lines[i].trim()) continue;
    // Parse CSV with quoted values
    const values = [];
    let current = '';
    let inQuotes = false;
    for (let j = 0; j < lines[i].length; j++) {
      const char = lines[i][j];
      if (char === '"') {
        inQuotes = !inQuotes;
      } else if (char === ',' && !inQuotes) {
        values.push(current.trim());
        current = '';
      } else {
        current += char;
      }
    }
    values.push(current.trim());

    const obj = {};
    headers.forEach((h, idx) => {
      obj[h] = values[idx] ? values[idx].replace(/^"|"$/g, '') : '';
    });
    result.push(obj);
  }

  return result;
}

async function main() {
  const reportPath = path.resolve(__dirname, 'seo-optimization-output', 'tag_application_report.csv');
  const content = fs.readFileSync(reportPath, 'utf-8');
  const records = parseCSV(content);

  console.log(`Loaded ${records.length} articles for tagging`);
  console.log(`\nArticles to be tagged:\n`);

  // Show first 10 and last 5
  console.log('First 10:');
  records.slice(0, 10).forEach(r => {
    console.log(`  [${r.article_id}] ${r.tag_name} (tag_id: ${r.tag_id})`);
  });

  if (records.length > 15) {
    console.log('  ...');
    console.log('Last 5:');
    records.slice(-5).forEach(r => {
      console.log(`  [${r.article_id}] ${r.tag_name} (tag_id: ${r.tag_id})`);
    });
  }

  console.log(`\n=== IMPORTANT ===`);
  console.log(`This script shows the MCP calls needed to apply tags.`);
  console.log(`Each article will be updated with its assigned tag.`);
  console.log(`Total API calls needed: ${records.length}`);
  console.log(`\nWaiting for manual confirmation to proceed with actual application...`);
  console.log(`\n=== BATCH APPLICATION PLAN ===`);
  console.log(`Batch size: 50 articles`);
  console.log(`Delay between batches: 2 seconds`);
  console.log(`Total batches: ${Math.ceil(records.length / 50)}`);

  // Generate a sample command for the first article
  if (records.length > 0) {
    const first = records[0];
    console.log(`\nSample MCP call for first article:`);
    console.log(`mcp__wpcom-mcp__wpcom-mcp-content-authoring`);
    console.log(`  action: execute`);
    console.log(`  wpcom_site: 133512998`);
    console.log(`  operation: posts.update`);
    console.log(`  params: {`);
    console.log(`    id: ${first.article_id},`);
    console.log(`    tags: [${first.tag_id}]`);
    console.log(`  }`);
  }
}

main().catch(console.error);
