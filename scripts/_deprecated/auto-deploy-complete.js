#!/usr/bin/env node
/**
 * YOLO LAB v2 首頁完全自動化部署
 *
 * 此腳本將自動部署新首頁到 WordPress.com
 * 如需完整自動化，請先生成應用密碼
 *
 * 使用方式:
 *   node auto-deploy-complete.js
 *
 * 首次使用需要設置認證：
 *   export WP_USERNAME="你的WordPress.com用戶名"
 *   export WP_APP_PASSWORD="應用密碼"
 *   node auto-deploy-complete.js
 */

const https = require('https');
const fs = require('fs');
const path = require('path');
const readline = require('readline');

// ============ 配置 ============
const SITE_ID = '133512998';
const SITE_URL = 'https://yololab.net';
const API_BASE = 'public-api.wordpress.com';
const HTML_FILE = path.join(__dirname, '../seo-optimization-output/homepage-v2-ultramodern.html');

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
  log(`\n${'='.repeat(70)}`, 'cyan');
  log(`  ${title}`, 'bold');
  log(`${'='.repeat(70)}\n`, 'cyan');
}

// ============ 讀取輸入 ============
function askQuestion(question) {
  return new Promise((resolve) => {
    const rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout
    });
    rl.question(question, (answer) => {
      rl.close();
      resolve(answer);
    });
  });
}

// ============ API 請求 ============
function makeApiRequest(method, path, body = null, username = null, password = null) {
  return new Promise((resolve, reject) => {
    const headers = {
      'Content-Type': 'application/json',
      'User-Agent': 'YOLO-AutoDeploy/2.0'
    };

    // 添加基本認證
    if (username && password) {
      const auth = Buffer.from(`${username}:${password}`).toString('base64');
      headers['Authorization'] = `Basic ${auth}`;
    }

    const options = {
      hostname: API_BASE,
      port: 443,
      path: `/rest/v1.1${path}`,
      method: method,
      headers: headers,
      timeout: 30000
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
            body: parsed
          });
        } catch (e) {
          resolve({
            statusCode: res.statusCode,
            body: data
          });
        }
      });
    });

    req.on('error', reject);
    req.on('timeout', () => {
      req.destroy();
      reject(new Error('請求超時'));
    });

    if (body) {
      req.write(JSON.stringify(body));
    }

    req.end();
  });
}

// ============ 主要部署流程 ============
async function deploy() {
  logSection('🚀 YOLO LAB v2 完全自動化部署');

  // 步驟 1: 檢查凭证
  logSection('🔐 步驟 1: 檢查認證凭证');

  let username = process.env.WP_USERNAME;
  let password = process.env.WP_APP_PASSWORD;

  if (!username || !password) {
    log('❌ 未找到 WordPress.com 認證凭证', 'yellow');
    log('', 'reset');
    log('需要以下任一方式進行認證:', 'cyan');
    log('1. 設置環境變數:', 'cyan');
    log('   export WP_USERNAME="你的 WordPress.com 用戶名"', 'cyan');
    log('   export WP_APP_PASSWORD="應用密碼"', 'cyan');
    log('', 'reset');
    log('2. 或者，在此輸入凭证（僅此次會話）:', 'cyan');
    log('', 'reset');

    username = await askQuestion('請輸入 WordPress.com 用戶名: ');
    password = await askQuestion('請輸入應用密碼: ');

    if (!username || !password) {
      log('❌ 認證凭证缺失，無法繼續部署', 'red');
      log('', 'reset');
      log('如何生成應用密碼:', 'yellow');
      log('1. 進入: https://wordpress.com/me/security', 'cyan');
      log('2. 捲動到 "App Passwords"', 'cyan');
      log('3. 輸入應用名稱（如 "YOLO Deployer"）', 'cyan');
      log('4. 複製生成的密碼', 'cyan');
      log('5. 重新運行此腳本並設置環境變數', 'cyan');
      process.exit(1);
    }
  } else {
    log(`✓ 已找到認證凭证`, 'green');
    log(`  用戶: ${username.substring(0, 3)}...`, 'cyan');
  }

  // 步驟 2: 讀取 HTML 文件
  logSection('📂 步驟 2: 讀取首頁內容');

  let htmlContent;
  try {
    htmlContent = fs.readFileSync(HTML_FILE, 'utf8');
    log(`✓ 成功讀取 HTML 文件`, 'green');
    log(`  文件大小: ${(htmlContent.length / 1024).toFixed(2)} KB`, 'cyan');
    log(`  行數: ${htmlContent.split('\n').length}`, 'cyan');
  } catch (err) {
    log(`✗ 錯誤: 無法讀取 ${HTML_FILE}`, 'red');
    process.exit(1);
  }

  // 步驟 3: 查詢首頁信息
  logSection('🔍 步驟 3: 查詢首頁信息');

  try {
    log('查詢首頁...', 'yellow');
    const listResponse = await makeApiRequest(
      'GET',
      `/sites/${SITE_ID}/posts?type=page&number=100`,
      null,
      username,
      password
    );

    if (listResponse.statusCode === 200 && listResponse.body.posts) {
      const posts = listResponse.body.posts;
      log(`✓ 找到 ${posts.length} 個頁面`, 'green');

      // 尋找首頁（通常是首頁或 ID 為 2 的頁面）
      let homepage = posts.find(p => p.slug === 'home') ||
                     posts.find(p => p.ID === 2) ||
                     posts[0];

      if (homepage) {
        log(`✓ 首頁信息:`, 'green');
        log(`  ID: ${homepage.ID}`, 'cyan');
        log(`  標題: ${homepage.title}`, 'cyan');
        log(`  狀態: ${homepage.status}`, 'cyan');
        log(`  URL: ${homepage.URL}`, 'cyan');
        return await updateHomepage(homepage.ID, htmlContent, username, password);
      }
    } else {
      log(`⚠️ 查詢失敗 (狀態碼: ${listResponse.statusCode})`, 'yellow');
      if (listResponse.body.message) {
        log(`  消息: ${listResponse.body.message}`, 'yellow');
      }
      process.exit(1);
    }
  } catch (err) {
    log(`✗ 錯誤: ${err.message}`, 'red');
    process.exit(1);
  }
}

// ============ 更新首頁 ============
async function updateHomepage(pageId, htmlContent, username, password) {
  logSection('📝 步驟 4: 更新首頁內容');

  try {
    log('正在上傳首頁內容...', 'yellow');

    const updateBody = {
      content: htmlContent,
      status: 'publish'
    };

    const updateResponse = await makeApiRequest(
      'POST',
      `/sites/${SITE_ID}/posts/${pageId}`,
      updateBody,
      username,
      password
    );

    if (updateResponse.statusCode === 200) {
      logSection('✨ 部署成功！');

      log('✓ 首頁已成功更新', 'green');
      log('', 'reset');
      log('訪問你的網站:', 'cyan');
      log(`  ${SITE_URL}/`, 'blue');
      log('', 'reset');
      log('編輯首頁:', 'cyan');
      log(`  ${SITE_URL}/wp-admin/post.php?post=${pageId}&action=edit`, 'blue');
      log('', 'reset');

      logSection('🎨 驗證清單');

      log('訪問網站後，檢查以下元素:', 'yellow');
      log('', 'reset');
      log('□ Hero 區域 - 深黑背景 + 綠色霓虹光暈', 'cyan');
      log('□ Tag Pills - 黃色半透明標籤', 'cyan');
      log('□ Stats Bar - 898+ / 4 / 2025', 'cyan');
      log('□ Featured Cards - 毛玻璃效果 + Hover 浮動', 'cyan');
      log('□ 分類卡片 - 紅紫藍綠色標線', 'cyan');
      log('□ Magazine 版 - 左大右小布局', 'cyan');
      log('□ 響應式 - F12 Device Toolbar 測試', 'cyan');
      log('□ Dark Mode - F12 切換深色模式', 'cyan');
      log('', 'reset');

      logSection('✅ 完成！');

      log('首頁已自動部署完成！', 'green');
      log('', 'reset');
      log('現在你可以:', 'cyan');
      log('1. 訪問 https://yololab.net 查看新首頁', 'cyan');
      log('2. 替換圖片 URL（可選）', 'cyan');
      log('3. 優化文案和內容（可選）', 'cyan');
      log('4. 運行 Lighthouse 審查（推薦）', 'cyan');
      log('', 'reset');

      return true;
    } else if (updateResponse.statusCode === 401) {
      log(`✗ 認證失敗 (401)`, 'red');
      log('  請檢查 WordPress.com 用戶名和應用密碼', 'red');
      process.exit(1);
    } else {
      log(`✗ 更新失敗 (狀態碼: ${updateResponse.statusCode})`, 'red');
      if (updateResponse.body.message) {
        log(`  消息: ${updateResponse.body.message}`, 'red');
      }
      process.exit(1);
    }
  } catch (err) {
    log(`✗ 錯誤: ${err.message}`, 'red');
    process.exit(1);
  }
}

// ============ 執行 ============
deploy().catch(err => {
  log(`\n✗ 致命錯誤: ${err.message}`, 'red');
  process.exit(1);
});
