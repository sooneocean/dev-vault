#!/usr/bin/env node
/**
 * YOLO LAB v2 自動部署腳本
 * 部署新首頁到 WordPress.com
 *
 * 使用方式:
 *   node auto-deploy-v2.js [--dry-run]
 */

const fs = require('fs');
const path = require('path');
const https = require('https');

// 配置
const CONFIG = {
  SITE_ID: '133512998',
  DOMAIN: 'yololab.net',
  API_BASE: 'public-api.wordpress.com',
  API_VERSION: 'v1.1',
  HTML_FILE: path.join(__dirname, '../seo-optimization-output/homepage-v2-ultramodern.html'),
  DRY_RUN: process.argv.includes('--dry-run'),
  DEMO_MODE: true // 演示模式 - 顯示會發生什麼
};

// ANSI 顏色
const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  red: '\x1b[31m',
  cyan: '\x1b[36m'
};

function log(msg, color = 'reset') {
  console.log(`${colors[color]}${msg}${colors.reset}`);
}

function logSection(title) {
  console.log('');
  log(`${'='.repeat(50)}`, 'cyan');
  log(title, 'blue');
  log(`${'='.repeat(50)}`, 'cyan');
}

async function readHtmlFile() {
  logSection('📂 讀取 HTML 文件');
  try {
    const html = fs.readFileSync(CONFIG.HTML_FILE, 'utf8');
    log(`✓ 成功讀取: ${CONFIG.HTML_FILE}`, 'green');
    log(`  文件大小: ${(html.length / 1024).toFixed(2)} KB`, 'cyan');
    log(`  行數: ${html.split('\n').length}`, 'cyan');
    return html;
  } catch (err) {
    log(`✗ 錯誤: 無法讀取文件 - ${err.message}`, 'red');
    process.exit(1);
  }
}

function displayDeploymentPlan(htmlContent) {
  logSection('📋 部署計畫');

  log('站點信息:', 'yellow');
  log(`  Domain: ${CONFIG.DOMAIN}`, 'cyan');
  log(`  Site ID: ${CONFIG.SITE_ID}`, 'cyan');
  log(`  API: ${CONFIG.API_BASE}/sites/${CONFIG.SITE_ID}`, 'cyan');

  log('', 'reset');
  log('首頁內容:', 'yellow');
  log(`  新首頁大小: ${(htmlContent.length / 1024).toFixed(2)} KB`, 'cyan');
  log(`  區塊數量: ${(htmlContent.match(/<!-- wp:/g) || []).length}`, 'cyan');

  log('', 'reset');
  log('設計元素:', 'yellow');
  log(`  ✓ Hero 區域 (深黑漸層 + 霓虹光暈)`, 'cyan');
  log(`  ✓ Stats Bar (898+/4/2025)`, 'cyan');
  log(`  ✓ Glassmorphism 卡片 (毛玻璃效果)`, 'cyan');
  log(`  ✓ 分類 4 色塊 (紅紫藍綠)`, 'cyan');
  log(`  ✓ Magazine 雜誌版 (左大右小)`, 'cyan');
  log(`  ✓ Dark Mode 支持`, 'cyan');
  log(`  ✓ 完整響應式 (手機/平板/桌面)`, 'cyan');
}

function displayDeploymentSteps() {
  logSection('🚀 部署步驟（手動執行）');

  log('由於 WordPress.com API 認證限制，請按以下步驟手動部署：\n', 'yellow');

  log('步驟 1️⃣ : 進入 WordPress 後台', 'blue');
  log(`  → https://yololab.net/wp-admin\n`, 'cyan');

  log('步驟 2️⃣ : 編輯首頁', 'blue');
  log(`  → Pages → 找到 Homepage/首頁 → 點擊編輯\n`, 'cyan');

  log('步驟 3️⃣ : 切換到代碼編輯器', 'blue');
  log(`  → 點擊右上角 ⋯ (三個點) → Code Editor\n`, 'cyan');

  log('步驟 4️⃣ : 替換首頁代碼', 'blue');
  log(`  → Ctrl+A 全選 → Delete 刪除\n`, 'cyan');

  log('步驟 5️⃣ : 貼入新代碼', 'blue');
  log(`  → 複製以下代碼並貼入編輯框\n`, 'cyan');
}

function displayHtmlCode(htmlContent) {
  logSection('📄 新首頁 HTML 代碼');

  log('複製以下全部代碼（Ctrl+C）:', 'yellow');
  log('', 'reset');
  console.log(htmlContent);
  log('', 'reset');
}

function displayPublishInstructions() {
  logSection('✅ 發布');

  log('步驟 6️⃣ : 發布更新', 'blue');
  log(`  → 點擊 Update（更新）或 Publish（發布）\n`, 'cyan');

  log('步驟 7️⃣ : 驗證', 'blue');
  log(`  → 訪問 https://yololab.net`, 'cyan');
  log(`  → 檢查新首頁效果\n`, 'cyan');
}

function displayVerificationChecklist() {
  logSection('🎨 驗證清單');

  log('部署後，訪問 https://yololab.net 檢查：\n', 'yellow');

  const checks = [
    { name: 'Hero 區域', desc: '深黑背景 + 綠色霓虹光暈 H1' },
    { name: 'Tag Pills', desc: '黃色半透明標籤（數據驅動、前衛、實驗）' },
    { name: '2 個按鈕', desc: '綠色主按鈕 + 玻璃風格次按鈕' },
    { name: 'Stats Bar', desc: '898+ 文章 / 4 分類 / 2025 數據庫' },
    { name: 'Featured Cards', desc: '毛玻璃卡片 + Hover 浮動效果' },
    { name: '分類 Grid', desc: '紅(電影)、紫(音樂)、藍(科技)、綠(運動)' },
    { name: 'Magazine 版', desc: '左側大圖 + 右側 5 篇文章清單' },
    { name: '響應式', desc: '桌面 / 平板 / 手機都正常' }
  ];

  checks.forEach((check, i) => {
    log(`  ☐ ${i + 1}. ${check.name}`, 'cyan');
    log(`     ${check.desc}\n`, 'cyan');
  });
}

function displayTroubleshooting() {
  logSection('⚠️ 故障排除');

  const issues = [
    {
      problem: '代碼編輯器顯示錯誤',
      solution: '檢查是否有未閉合的 HTML 標籤 — 複製時確保完整'
    },
    {
      problem: '光暈效果不明顯',
      solution: '檢查瀏覽器是否支持 text-shadow — 用 Chrome 最新版'
    },
    {
      problem: '毛玻璃卡片沒效果',
      solution: '需要 Chrome 76+ 或 Safari 9+ — 支持 backdrop-filter'
    },
    {
      problem: '圖片顯示不了',
      solution: '圖片 URL 尚未設置 — 需要替換為真實 URL'
    },
    {
      problem: '小屏幕顯示怪怪的',
      solution: '清除瀏覽器緩存：Ctrl+Shift+Del → 強制刷新 Ctrl+F5'
    }
  ];

  issues.forEach((item, i) => {
    log(`  ${i + 1}. ${item.problem}`, 'yellow');
    log(`     → ${item.solution}\n`, 'cyan');
  });
}

function displayNextSteps() {
  logSection('🎯 下一步');

  log('部署完成後，你可以：\n', 'yellow');

  log('1. 替換圖片 URL', 'blue');
  log(`   上傳真實內容圖片到媒體庫\n`, 'cyan');

  log('2. 優化文案', 'blue');
  log(`   編輯標題、描述、分類文字\n`, 'cyan');

  log('3. SEO 優化', 'blue');
  log(`   添加 Meta 標籤、Schema 標記\n`, 'cyan');

  log('4. 性能監控', 'blue');
  log(`   用 Google PageSpeed Insights 檢測\n`, 'cyan');
}

function displaySummary() {
  logSection('📊 部署摘要');

  log('文件位置：', 'yellow');
  log(`  HTML: seo-optimization-output/homepage-v2-ultramodern.html`, 'cyan');
  log(`  CSS: seo-optimization-output/homepage-v2-custom.css`, 'cyan');
  log(`  指南: docs/YOLO_V2_QUICK_DEPLOY.md\n`, 'cyan');

  log('站點信息：', 'yellow');
  log(`  URL: https://yololab.net`, 'cyan');
  log(`  Admin: https://yololab.net/wp-admin`, 'cyan');
  log(`  Site ID: 133512998\n`, 'cyan');

  log('設計系統：', 'yellow');
  log(`  Primary (主色): #418a2c (綠)`, 'cyan');
  log(`  分類色: 電影(紅) 音樂(紫) 科技(藍) 運動(綠)`, 'cyan');
  log(`  Hero 背景: #050811 (深藍黑)`, 'cyan');
  log(`  Glassmorphism: blur(16px) + 半透明\n`, 'cyan');
}

async function main() {
  console.clear();

  log('╔════════════════════════════════════════════════════╗', 'cyan');
  log('║  YOLO LAB v2 首頁自動部署                           ║', 'cyan');
  log('║  超現代化設計 — Glassmorphism + Micro-animations  ║', 'cyan');
  log('╚════════════════════════════════════════════════════╝', 'cyan');

  const htmlContent = await readHtmlFile();

  displayDeploymentPlan(htmlContent);
  displayDeploymentSteps();
  displayHtmlCode(htmlContent);
  displayPublishInstructions();
  displayVerificationChecklist();
  displayTroubleshooting();
  displayNextSteps();
  displaySummary();

  logSection('✨ 準備完成！');

  if (CONFIG.DEMO_MODE) {
    log('這是演示模式，顯示部署流程和所有必需的代碼。', 'yellow');
    log('', 'reset');
    log('現在請：', 'blue');
    log('  1. 複製上面的 HTML 代碼', 'cyan');
    log('  2. 進入 WordPress 後台', 'cyan');
    log('  3. 編輯首頁 → Code Editor', 'cyan');
    log('  4. 貼入代碼 → Update', 'cyan');
    log('  5. 訪問 yololab.net 驗證效果', 'cyan');
    log('', 'reset');
  }

  log('祝部署順利！🚀\n', 'green');
}

main().catch(err => {
  log(`\n✗ 錯誤: ${err.message}`, 'red');
  process.exit(1);
});
