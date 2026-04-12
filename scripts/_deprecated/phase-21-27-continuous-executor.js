#!/usr/bin/env node

/**
 * Phase 21-27 持續執行控制器
 *
 * 功能：
 * - 自動執行 Phase 21-27 直至完成
 * - 自動恢復進度（如果中斷）
 * - 實時監控執行狀態
 * - 生成完整執行報告
 */

import { spawn } from "child_process";
import fs from "fs";
import path from "path";

const PHASES = [21, 22, 23, 24, 25, 26, 27];
const OUTPUT_DIR = "seo-optimization-output";

// ─── Utilities ──────────────────────────────────────────────────────────────

function getProgressFile(phase) {
  return `phase${phase}-progress.json`;
}

function loadPhaseProgress(phase) {
  const file = getProgressFile(phase);
  try {
    if (fs.existsSync(file)) {
      return JSON.parse(fs.readFileSync(file, "utf-8"));
    }
  } catch (e) {
    return null;
  }
  return null;
}

function getPhaseStatus() {
  const status = {};
  for (const phase of PHASES) {
    const progress = loadPhaseProgress(phase);
    status[phase] = {
      processed: progress?.processed || 0,
      success: progress?.success.length || 0,
      timeout: progress?.timeout.length || 0,
      failed: progress?.failed.length || 0,
      total: 100,
      percent: Math.round((progress?.success.length || 0) / 100 * 100),
    };
  }
  return status;
}

function printStatus() {
  console.log("\n" + "=".repeat(80));
  console.log("📊 Phase 21-27 實時進度");
  console.log("=".repeat(80) + "\n");

  const status = getPhaseStatus();
  let totalSuccess = 0;
  let totalFailed = 0;

  for (const phase of PHASES) {
    const s = status[phase];
    totalSuccess += s.success;
    totalFailed += s.failed;

    const bar = "█".repeat(Math.floor(s.percent / 5)) + "░".repeat(20 - Math.floor(s.percent / 5));
    console.log(
      `Phase ${phase}: [${bar}] ${s.percent.toString().padStart(3)}% | ✅ ${s.success.toString().padStart(3)} | ❌ ${s.failed.toString().padStart(3)} | ⏱️ ${s.timeout.toString().padStart(3)}`
    );
  }

  console.log("\n" + "-".repeat(80));
  console.log(`🎯 總進度: ✅ ${totalSuccess}/700 (${((totalSuccess/700)*100).toFixed(1)}%) | ❌ ${totalFailed}/700`);
  console.log("=".repeat(80) + "\n");

  return { totalSuccess, totalFailed };
}

async function runMainOptimizer() {
  console.log("\n🚀 啟動 Phase 21-27 SEO 優化批量執行器\n");

  return new Promise((resolve, reject) => {
    const child = spawn("node", ["scripts/phase-21-27-batch-seo-optimizer.js"], {
      cwd: process.cwd(),
      stdio: "inherit",
      shell: true,
    });

    child.on("exit", (code) => {
      if (code === 0) {
        resolve();
      } else {
        reject(new Error(`Process exited with code ${code}`));
      }
    });

    child.on("error", (err) => {
      reject(err);
    });
  });
}

async function generateFinalReport() {
  console.log("\n📋 生成最終執行報告...\n");

  const status = getPhaseStatus();
  const timestamp = new Date().toISOString();

  let totalSuccess = 0;
  let totalFailed = 0;
  let totalTimeout = 0;

  const report = {
    title: "Phase 21-27 SEO 優化完成報告",
    date: timestamp,
    siteId: 133512998,
    siteName: "yololab.net",
    phases: {},
    summary: {},
  };

  for (const phase of PHASES) {
    const s = status[phase];
    report.phases[phase] = s;
    totalSuccess += s.success;
    totalFailed += s.failed;
    totalTimeout += s.timeout;
  }

  report.summary = {
    totalPhases: 7,
    targetArticles: 700,
    totalSuccess,
    totalFailed,
    totalTimeout,
    successRate: ((totalSuccess / 700) * 100).toFixed(1) + "%",
  };

  // 寫入報告
  if (!fs.existsSync(OUTPUT_DIR)) {
    fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  }

  const reportPath = path.join(OUTPUT_DIR, `PHASE-21-27-FINAL-REPORT-${Date.now()}.json`);
  fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));

  console.log(`✅ 報告已保存: ${reportPath}\n`);

  // 列印摘要
  printStatus();

  if (totalFailed === 0) {
    console.log("🎉 全部文章優化完成！無任何失敗。\n");
  } else {
    console.log(`⚠️  有 ${totalFailed} 篇文章失敗，可稍後重試。\n`);
  }
}

async function main() {
  try {
    // 檢查環境
    if (!process.env.WPCOM_TOKEN) {
      console.error("❌ 缺少 WPCOM_TOKEN 環境變數");
      console.error("   請運行: export WPCOM_TOKEN=your_token");
      process.exit(1);
    }

    // 顯示初始狀態
    printStatus();

    // 執行優化
    await runMainOptimizer();

    // 生成最終報告
    await generateFinalReport();

  } catch (err) {
    console.error("\n❌ 執行失敗:", err.message);
    process.exit(1);
  }
}

main();
