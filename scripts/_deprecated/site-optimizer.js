#!/usr/bin/env node

/**
 * Site Optimizer CLI — WordPress 網站批量優化框架
 *
 * 支持多種優化類型：
 *   - image-alt        : 圖片 ALT 文字優化（✅ 完全實現）
 *   - meta-tags        : Meta Tags 優化（🔜 計劃中）
 *   - schema-markup    : Schema Markup 注入（🔜 計劃中）
 *   - internal-links   : 內部連結優化（✅ 已實現）
 *
 * 使用方式：
 *   /site-optimizer --site yololab --type image-alt --phase scan --sample 10
 *   /site-optimizer --site yololab --type image-alt --phase apply-featured
 *   /site-optimizer --site mysite --type image-alt --phase report
 *
 * 詳見文檔：.claude/skills/SITE-OPTIMIZER.md
 */

import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import { execSync } from "child_process";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const CONFIG_PATH = path.join(__dirname, "../.claude/skills/site-optimizer-config.json");

// ─── Config Loading ────────────────────────────────────────────────────────

function loadConfig() {
  if (!fs.existsSync(CONFIG_PATH)) {
    console.error("❌ 配置文件不存在：", CONFIG_PATH);
    process.exit(1);
  }
  return JSON.parse(fs.readFileSync(CONFIG_PATH, "utf-8"));
}

// ─── CLI Arguments Parsing ────────────────────────────────────────────────

function parseArgs() {
  const args = process.argv.slice(2);
  const parsed = {
    site: args.find(a => a.startsWith("--site="))?.split("=")[1] || args[args.indexOf("--site") + 1],
    type: args.find(a => a.startsWith("--type="))?.split("=")[1] || args[args.indexOf("--type") + 1],
    phase: args.find(a => a.startsWith("--phase="))?.split("=")[1] || args[args.indexOf("--phase") + 1],
    sample: parseInt(args.find(a => a.startsWith("--sample="))?.split("=")[1] || args[args.indexOf("--sample") + 1] || "0"),
    dryRun: args.includes("--dry-run"),
    resume: args.includes("--resume"),
    skipVerification: args.includes("--skip-verification"),
    target: args.find(a => a.startsWith("--target="))?.split("=")[1],
    help: args.includes("--help"),
  };
  return parsed;
}

// ─── Help Display ────────────────────────────────────────────────────────

function showHelp() {
  console.log(`
╭─────────────────────────────────────────────────────────────────╮
│           Site Optimizer — WordPress 批量優化框架              │
╰─────────────────────────────────────────────────────────────────╯

📋 使用方式：

  /site-optimizer --site <site> --type <type> --phase <phase> [options]

🎯 必需參數：

  --site <name>          網站名稱（在配置中定義）
  --type <type>          優化類型：image-alt | meta-tags | schema-markup | internal-links
  --phase <phase>        執行階段（依優化類型而異）

⚙️ 可選參數：

  --sample N             只處理前 N 篇文章（用於測試）
  --dry-run              乾運行，不實際更新
  --resume               從上次中斷處繼續
  --skip-verification   跳過執行後驗証（加速）
  --target <target>      回滾目標（featured|inline|all，用於回滾）
  --help                 顯示此幫助信息

📚 圖片 ALT 文字優化 (image-alt) 階段：

  scan              掃描全站文章，盤點圖片 alt 狀態
  generate          Claude Vision 分析圖片，生成 alt text
  apply-featured    批次更新 featured_media alt text
  apply-inline      批次更新內嵌圖片 alt 屬性
  report            產出品質驗証報告
  rollback          從備份還原（需指定 --target）

💡 常見用法：

  # 掃描（測試）
  /site-optimizer --site yololab --type image-alt --phase scan --sample 10

  # 掃描（完整）
  /site-optimizer --site yololab --type image-alt --phase scan

  # 乾運行（查看但不更新）
  /site-optimizer --site yololab --type image-alt --phase apply-featured --dry-run

  # 應用到 featured_media
  /site-optimizer --site yololab --type image-alt --phase apply-featured

  # 應用到內嵌圖片（斷點續傳）
  /site-optimizer --site yololab --type image-alt --phase apply-inline --resume

  # 查看報告
  /site-optimizer --site yololab --type image-alt --phase report

  # 完全回滾
  /site-optimizer --site yololab --type image-alt --phase rollback --target all

📖 更多信息：

  詳見文檔：.claude/skills/SITE-OPTIMIZER.md
  配置文件：.claude/skills/site-optimizer-config.json
  核心代碼：scripts/image-alt-text-optimizer.js

`);
}

// ─── Main Execution ────────────────────────────────────────────────────────

async function main() {
  const args = parseArgs();

  if (args.help || !args.site || !args.type || !args.phase) {
    showHelp();
    if (!args.help) {
      console.error("❌ 缺少必需參數。使用 --help 查看幫助。");
      process.exit(1);
    }
    process.exit(0);
  }

  const config = loadConfig();

  // Validate site
  if (!config.siteConfig[args.site]) {
    console.error(`❌ 未知的網站：${args.site}`);
    console.error(`已配置的網站：${Object.keys(config.siteConfig).join(", ")}`);
    process.exit(1);
  }

  const siteConfig = config.siteConfig[args.site];

  // Validate optimization type
  if (!config.supportedOptimizations[args.type]) {
    console.error(`❌ 未知的優化類型：${args.type}`);
    console.error(`支持的類型：${Object.keys(config.supportedOptimizations).join(", ")}`);
    process.exit(1);
  }

  const optConfig = config.supportedOptimizations[args.type];

  // Validate phase
  if (!optConfig.phases.includes(args.phase)) {
    console.error(`❌ 無效的階段：${args.phase}`);
    console.error(`支持的階段：${optConfig.phases.join(", ")}`);
    process.exit(1);
  }

  // Route to appropriate handler
  console.log(`\n═══════════════════════════════════════════════════`);
  console.log(`  Site Optimizer — ${optConfig.name}`);
  console.log(`═══════════════════════════════════════════════════\n`);
  console.log(`🌐 網站：${siteConfig.domain}`);
  console.log(`📝 優化：${optConfig.name}`);
  console.log(`⏱️  階段：${args.phase}`);
  if (args.sample > 0) console.log(`📊 樣本：${args.sample} 篇文章`);
  if (args.dryRun) console.log(`🏜️  模式：乾運行（不更新）`);
  if (args.resume) console.log(`▶️  模式：斷點續傳`);
  console.log();

  try {
    switch (args.type) {
      case "image-alt":
        await handleImageAltOptimization(args, siteConfig, optConfig);
        break;
      case "meta-tags":
        console.error("🔜 Meta Tags 優化尚未實現。計劃在 Phase 2 推出。");
        process.exit(1);
        break;
      case "schema-markup":
        console.error("🔜 Schema Markup 優化尚未實現。計劃在 Phase 2 推出。");
        process.exit(1);
        break;
      case "internal-links":
        await handleInternalLinksOptimization(args, siteConfig, optConfig);
        break;
      default:
        console.error(`❌ 未知的優化類型：${args.type}`);
        process.exit(1);
    }
  } catch (error) {
    console.error(`\n❌ 執行失敗：${error.message}`);
    process.exit(1);
  }
}

// ─── Image Alt Optimization Handler ────────────────────────────────────────

async function handleImageAltOptimization(args, siteConfig, optConfig) {
  const scriptPath = path.join(__dirname, "image-alt-text-optimizer.js");

  // Build command
  let cmd = `node "${scriptPath}" --phase=${args.phase}`;

  if (args.sample > 0) cmd += ` --sample=${args.sample}`;
  if (args.dryRun) cmd += ` --dry-run`;
  if (args.resume) cmd += ` --resume`;
  if (args.skipVerification) cmd += ` --skip-verification`;

  // Handle rollback phase
  if (args.phase === "rollback" || args.phase === "apply-inline") {
    // For inline phase, use "inline" API phase
    if (args.phase === "apply-inline") {
      cmd = cmd.replace("--phase=apply-inline", "--phase=inline");
    }
    // For rollback, use special syntax
    if (args.phase === "rollback") {
      cmd = cmd.replace("--phase=rollback", `--rollback=${args.target || "all"}`);
    }
  }

  // Map apply phases to script phases
  if (args.phase === "apply-featured") {
    cmd = cmd.replace("--phase=apply-featured", "--phase=featured");
  } else if (args.phase === "apply-inline") {
    cmd = cmd.replace("--phase=apply-inline", "--phase=inline");
  }

  console.log(`🚀 執行命令：${cmd}\n`);

  try {
    execSync(cmd, { stdio: "inherit", cwd: __dirname });
    console.log(`\n✅ 執行完成！\n`);
  } catch (error) {
    throw error;
  }
}

// ─── Internal Links Optimization Handler ──────────────────────────────────

async function handleInternalLinksOptimization(args, siteConfig, optConfig) {
  const scriptPath = path.join(__dirname, "internal-linker-v2.js");

  // Map phases
  const phaseMap = {
    "scan": "fetch-map",
    "generate": "propose",
    "apply-featured": "inject",
    "apply-inline": "fix-broken",
    "report": "propose", // Reuse proposal phase for reporting
  };

  const scriptPhase = phaseMap[args.phase] || args.phase;

  let cmd = `node "${scriptPath}" --phase ${scriptPhase}`;
  if (args.dryRun) cmd += ` --dry-run`;
  if (args.sample > 0) cmd += ` --sample ${args.sample}`;

  console.log(`🚀 執行命令：${cmd}\n`);

  try {
    execSync(cmd, { stdio: "inherit", cwd: __dirname });
    console.log(`\n✅ 執行完成！\n`);
  } catch (error) {
    throw error;
  }
}

// ─── Run ─────────────────────────────────────────────────────────────────

main().catch(error => {
  console.error(`\n❌ 致命錯誤：${error.message}`);
  process.exit(1);
});
