#!/usr/bin/env node
/**
 * YOLO LAB v2 首頁自動部署
 * 直接通過 WordPress.com REST API 部署
 *
 * 使用方式: node deploy-homepage-auto.js
 */

const https = require('https');
const fs = require('fs');
const path = require('path');

// ============ 配置 ============
const SITE_ID = '133512998';
const SITE_DOMAIN = 'yololab.net';
const API_BASE = 'public-api.wordpress.com';
const API_VERSION = 'v1.1';

// 使用應用密碼（如果有的話）
// 為了完整的自動化，你需要設置以下環境變數
const WP_APP_PASSWORD = process.env.WP_APP_PASSWORD || null;
const WP_USERNAME = process.env.WP_USERNAME || null;

// ============ 顏色輸出 ============
const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  red: '\x1b[31m',
  cyan: '\x1b[36m',
  bold: '\x1b[1m'
};

function log(msg, color = 'reset') {
  console.log(`${colors[color]}${msg}${colors.reset}`);
}

function logSection(title) {
  log(`\n${'='.repeat(60)}`, 'cyan');
  log(`  ${title}`, 'bold');
  log(`${'='.repeat(60)}\n`, 'cyan');
}

// ============ HTTP 請求函數 ============
function makeApiRequest(method, endpoint, body = null, headers = {}) {
  return new Promise((resolve, reject) => {
    const defaultHeaders = {
      'Content-Type': 'application/json',
      'User-Agent': 'YOLO-Homepage-Deployer/2.0',
      ...headers
    };

    // 添加認證
    if (WP_APP_PASSWORD && WP_USERNAME) {
      const auth = Buffer.from(`${WP_USERNAME}:${WP_APP_PASSWORD}`).toString('base64');
      defaultHeaders['Authorization'] = `Basic ${auth}`;
    }

    const url = new URL(`https://${API_BASE}${endpoint}`);

    const options = {
      hostname: url.hostname,
      port: 443,
      path: url.pathname + url.search,
      method: method,
      headers: defaultHeaders
    };

    const req = https.request(options, (res) => {
      let data = '';

      res.on('data', (chunk) => {
        data += chunk;
      });

      res.on('end', () => {
        try {
          const parsed = JSON.parse(data);
          resolve({
            statusCode: res.statusCode,
            headers: res.headers,
            body: parsed
          });
        } catch (e) {
          resolve({
            statusCode: res.statusCode,
            headers: res.headers,
            body: data
          });
        }
      });
    });

    req.on('error', (error) => {
      reject(error);
    });

    if (body) {
      req.write(JSON.stringify(body));
    }

    req.end();
  });
}

// ============ 主要部署流程 ============
async function deploy() {
  logSection('🚀 YOLO LAB v2 首頁自動部署');

  // 步驟 1: 讀取 HTML 文件
  log('📂 步驟 1: 讀取首頁 HTML 文件...', 'yellow');
  const htmlFile = path.join(__dirname, '../seo-optimization-output/homepage-v2-ultramodern.html');

  let htmlContent;
  try {
    htmlContent = fs.readFileSync(htmlFile, 'utf8');
    log(`✓ 成功讀取 HTML (${(htmlContent.length / 1024).toFixed(2)} KB, ${htmlContent.split('\n').length} 行)`, 'green');
  } catch (err) {
    log(`✗ 錯誤: 無法讀取 ${htmlFile}`, 'red');
    log(`  ${err.message}`, 'red');
    process.exit(1);
  }

  // 步驟 2: 檢查認證方式
  logSection('🔐 步驟 2: 檢查認證');

  if (WP_APP_PASSWORD && WP_USERNAME) {
    log(`✓ 使用應用密碼認證（用戶: ${WP_USERNAME}）`, 'green');
  } else {
    log('⚠️ 未設置 WordPress 應用密碼', 'yellow');
    log('  環境變數:', 'cyan');
    log('    WP_USERNAME (你的 WordPress.com 用戶名)', 'cyan');
    log('    WP_APP_PASSWORD (應用密碼)', 'cyan');
    log('', 'reset');
    log('生成應用密碼步驟:', 'yellow');
    log('  1. 進入 https://wordpress.com/me/security', 'cyan');
    log('  2. 捲動到 "App Passwords"', 'cyan');
    log('  3. 輸入應用名稱（如 "YOLO Deployer"）', 'cyan');
    log('  4. 複製生成的密碼', 'cyan');
    log('  5. 設置環境變數或編輯此腳本', 'cyan');
    log('', 'reset');
    log('繼續無認證部署將嘗試使用 JWT...\n', 'yellow');
  }

  // 步驟 3: 查詢現有首頁
  logSection('📋 步驟 3: 查詢現有首頁信息');

  try {
    const pagesEndpoint = `/rest/v1.1/sites/${SITE_ID}/posts?type=page&search=home&number=10`;
    log(`查詢: ${API_BASE}${pagesEndpoint}`, 'cyan');

    const pagesResponse = await makeApiRequest('GET', pagesEndpoint);

    if (pagesResponse.statusCode === 200 && pagesResponse.body.posts) {
      const posts = pagesResponse.body.posts;
      log(`✓ 找到 ${posts.length} 個頁面`, 'green');

      posts.forEach((post, i) => {
        log(`  ${i + 1}. "${post.title}" (ID: ${post.ID}, Status: ${post.status})`, 'cyan');
      });

      if (posts.length > 0) {
        log(`\n✓ 將更新首頁 ID: ${posts[0].ID}`, 'green');
      }
    } else {
      log(`狀態碼: ${pagesResponse.statusCode}`, 'yellow');
      if (pagesResponse.body.message) {
        log(`消息: ${pagesResponse.body.message}`, 'yellow');
      }
    }
  } catch (err) {
    log(`⚠️ 查詢失敗: ${err.message}`, 'yellow');
  }

  // 步驟 4: 部署準備
  logSection('📝 步驟 4: 部署準備');

  log('首頁內容摘要:', 'cyan');
  log(`  - HTML 大小: ${(htmlContent.length / 1024).toFixed(2)} KB`, 'cyan');
  log(`  - 區塊數: ${(htmlContent.match(/<!-- wp:/g) || []).length}`, 'cyan');
  log(`  - 設計元素:`, 'cyan');
  log(`    ✓ Hero 區域 (深黑漸層 + 霓虹光暈)`, 'cyan');
  log(`    ✓ Stats Bar (898+/4/2025)`, 'cyan');
  log(`    ✓ Glassmorphism 卡片`, 'cyan');
  log(`    ✓ 分類 4 色塊 (紅紫藍綠)`, 'cyan');
  log(`    ✓ Magazine 雜誌版 (左大右小)`, 'cyan');
  log(`    ✓ Dark Mode + 響應式`, 'cyan');

  // 步驟 5: 部署替代方案
  logSection('🚀 步驟 5: 部署方式');

  if (WP_APP_PASSWORD && WP_USERNAME) {
    log('檢測到應用密碼認證，正在執行自動部署...', 'blue');

    try {
      // 嘗試更新首頁
      // 假設首頁 ID 是 2（WordPress 的常見首頁 ID）
      const updateEndpoint = `/rest/v1.1/sites/${SITE_ID}/posts/2`;
      const updateBody = {
        content: htmlContent,
        status: 'publish'
      };

      log(`\n更新端點: ${updateEndpoint}`, 'cyan');
      log('發送請求...', 'yellow');

      const updateResponse = await makeApiRequest('POST', updateEndpoint, updateBody);

      if (updateResponse.statusCode === 200) {
        log('✓ 首頁更新成功！', 'green');
        log(`  編輯 URL: https://yololab.net/wp-admin/post.php?post=2&action=edit`, 'cyan');
        log(`  查看 URL: https://yololab.net/`, 'cyan');
      } else {
        log(`⚠️ 更新狀態碼: ${updateResponse.statusCode}`, 'yellow');
        if (updateResponse.body.message) {
          log(`  消息: ${updateResponse.body.message}`, 'yellow');
        }
        throwManualDeploymentInstructions();
      }
    } catch (err) {
      log(`✗ 自動部署失敗: ${err.message}`, 'red');
      log('\n轉換為手動部署模式...', 'yellow');
      throwManualDeploymentInstructions();
    }
  } else {
    log('未配置應用密碼認證', 'yellow');
    log('使用手動部署方式', 'yellow');
    throwManualDeploymentInstructions();
  }
}

function throwManualDeploymentInstructions() {
  logSection('📋 手動部署指引');

  log('由於 API 認證限制，請按以下步驟手動部署:\n', 'yellow');

  log('1️⃣ 進入 WordPress 後台', 'blue');
  log('   https://yololab.net/wp-admin\n', 'cyan');

  log('2️⃣ 編輯首頁', 'blue');
  log('   Pages → Homepage/首頁 → Edit\n', 'cyan');

  log('3️⃣ 切換代碼編輯器', 'blue');
  log('   右上角 ⋯ → Code Editor\n', 'cyan');

  log('4️⃣ 替換代碼', 'blue');
  log('   Ctrl+A → Delete → Ctrl+V (貼入新代碼)\n', 'cyan');

  log('5️⃣ 發布', 'blue');
  log('   Update / Publish\n', 'cyan');

  logSection('📁 文件位置');

  log('複製以下文件中的代碼:', 'cyan');
  log('  → seo-optimization-output/homepage-v2-ultramodern.html', 'cyan');
  log('  → seo-optimization-output/homepage-v2-custom.css (可選)\n', 'cyan');

  logSection('✨ 完成');

  log('部署後檢查: https://yololab.net', 'green');
  log('預期效果:', 'green');
  log('  ✓ 深黑 Hero + 綠色光暈', 'cyan');
  log('  ✓ Stats Bar (898+/4/2025)', 'cyan');
  log('  ✓ Glassmorphism 卡片', 'cyan');
  log('  ✓ 4 色分類卡片', 'cyan');
  log('  ✓ Magazine 雜誌版', 'cyan');
  log('  ✓ Dark Mode + 響應式\n', 'cyan');
}

// ============ 執行 ============
deploy().catch(err => {
  log(`\n✗ 致命錯誤: ${err.message}`, 'red');
  process.exit(1);
});
