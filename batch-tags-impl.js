const fs = require('fs');
const path = require('path');

function parseCSV(content) {
  const lines = content.trim().split('\n');
  const headers = lines[0].split(',').map(h => h.trim().replace(/^"|"$/g, ''));
  const result = [];

  for (let i = 1; i < lines.length; i++) {
    if (!lines[i].trim()) continue;
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

const reportPath = path.resolve(__dirname, 'seo-optimization-output', 'tag_application_report.csv');
const records = parseCSV(fs.readFileSync(reportPath, 'utf-8'));

console.log('{"mcp_calls": [');

records.forEach((r, idx) => {
  console.log(`  {`);
  console.log(`    "action": "execute",`);
  console.log(`    "wpcom_site": 133512998,`);
  console.log(`    "operation": "posts.update",`);
  console.log(`    "params": {`);
  console.log(`      "id": ${r.article_id},`);
  console.log(`      "tags": [${r.tag_id}]`);
  console.log(`    }`);
  console.log(`  }${idx < records.length - 1 ? ',' : ''}`);
});

console.log('],"metadata": {"total": ' + records.length + ', "batch_size": 50}}');
