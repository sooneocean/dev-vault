#!/usr/bin/env node

/**
 * Phase 21-27 進度檢查工具
 *
 * 用途:
 * - 實時檢查各 Phase 的執行進度
 * - 生成統計報告
 * - 列出失敗項目（用於重試）
 */

import fs from "fs";
import path from "path";

const PHASES = [21, 22, 23, 24, 25, 26, 27];

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

function formatTime(timestamp) {
  const date = new Date(timestamp);
  return date.toLocaleString("zh-TW");
}

function displayProgressBar(percent) {
  const filled = Math.floor(percent / 5);
  const empty = 20 - filled;
  return `[${("█".repeat(filled) + "░".repeat(empty))}] ${percent.toString().padStart(3)}%`;
}

function printStatus() {
  console.log("\n" + "=".repeat(90));
  console.log("📊 Phase 21-27 即時進度狀態");
  console.log("=".repeat(90) + "\n");

  let totalSuccess = 0;
  let totalFailed = 0;
  let totalTimeout = 0;
  let totalProcessed = 0;
  const phaseDetails = {};

  for (const phase of PHASES) {
    const progress = loadPhaseProgress(phase);

    if (!progress) {
      console.log(`Phase ${phase}: ⭕ 尚未開始`);
      phaseDetails[phase] = {
        status: "pending",
        success: 0,
        failed: 0,
        timeout: 0,
        percent: 0,
      };
      continue;
    }

    const success = progress.success.length;
    const failed = progress.failed.length;
    const timeout = progress.timeout.length;
    const total = 100;
    const percent = Math.round((success / total) * 100);

    totalSuccess += success;
    totalFailed += failed;
    totalTimeout += timeout;
    totalProcessed += success + failed + timeout;

    phaseDetails[phase] = {
      status: percent === 100 ? "complete" : percent > 0 ? "in_progress" : "pending",
      success,
      failed,
      timeout,
      percent,
      startTime: progress.startTime,
    };

    const bar = displayProgressBar(percent);
    const statusIcon =
      percent === 100 ? "✅" : percent > 0 ? "⏳" : "⭕";

    console.log(
      `Phase ${phase}: ${statusIcon} ${bar} | ✅ ${success
        .toString()
        .padStart(3)} | ❌ ${failed.toString().padStart(3)} | ⏱️ ${timeout
        .toString()
        .padStart(3)}`
    );
  }

  console.log("\n" + "-".repeat(90));

  // 總體統計
  const totalTarget = 700;
  const totalPercent = Math.round((totalSuccess / totalTarget) * 100);

  console.log(`🎯 總體進度: ${displayProgressBar(totalPercent)}`);
  console.log(
    `   ✅ 成功: ${totalSuccess.toString().padStart(3)}/700 | ❌ 失敗: ${totalFailed
      .toString()
      .padStart(3)}/700 | ⏱️ 超時: ${totalTimeout
      .toString()
      .padStart(3)}`
  );

  if (totalFailed > 0) {
    console.log(
      `\n⚠️  發現 ${totalFailed} 篇失敗的文章，可執行重試`
    );
  }

  if (totalSuccess === totalTarget) {
    console.log("\n🎉 所有 700 篇文章全部完成!");
  }

  console.log("=".repeat(90) + "\n");

  return { phaseDetails, totalSuccess, totalFailed, totalTimeout, totalPercent };
}

function displayFailedArticles() {
  console.log("\n" + "=".repeat(90));
  console.log("❌ 失敗的文章清單");
  console.log("=".repeat(90) + "\n");

  let totalFailed = 0;

  for (const phase of PHASES) {
    const progress = loadPhaseProgress(phase);

    if (!progress || progress.failed.length === 0) {
      continue;
    }

    console.log(`\n📌 Phase ${phase}:`);
    console.log("-".repeat(90));

    for (const item of progress.failed) {
      console.log(`  - ID ${item.id}: ${item.error}`);
      totalFailed++;
    }
  }

  if (totalFailed === 0) {
    console.log("✅ 沒有失敗的文章!");
  }

  console.log("\n" + "=".repeat(90));
  console.log(`📊 失敗總數: ${totalFailed}\n`);

  return totalFailed;
}

function displayDetailedPhaseReport(phaseNum) {
  console.log("\n" + "=".repeat(90));
  console.log(`📋 Phase ${phaseNum} 詳細報告`);
  console.log("=".repeat(90) + "\n");

  const progress = loadPhaseProgress(phaseNum);

  if (!progress) {
    console.log(`Phase ${phaseNum} 尚未開始\n`);
    return;
  }

  console.log(`開始時間: ${formatTime(progress.startTime)}`);
  console.log(`成功: ${progress.success.length}`);
  console.log(`失敗: ${progress.failed.length}`);
  console.log(`超時: ${progress.timeout.length}`);

  if (progress.failed.length > 0) {
    console.log("\n失敗的文章:");
    for (const item of progress.failed.slice(0, 10)) {
      console.log(`  - ID ${item.id}: ${item.error}`);
    }
    if (progress.failed.length > 10) {
      console.log(`  ... 還有 ${progress.failed.length - 10} 篇`);
    }
  }

  console.log("\n" + "=".repeat(90) + "\n");
}

function main() {
  const args = process.argv.slice(2);
  const command = args[0] || "status";

  console.log("\n🔍 Phase 21-27 狀態檢查工具\n");

  switch (command) {
    case "status":
      printStatus();
      break;

    case "failed":
      displayFailedArticles();
      break;

    case "report":
      {
        const phaseNum = parseInt(args[1]) || 21;
        displayDetailedPhaseReport(phaseNum);
      }
      break;

    case "help":
      console.log(`
使用方法:
  node scripts/phase-21-27-status-check.js [command] [args]

命令:
  status     - 顯示全部 Phase 的即時進度（預設）
  failed     - 列出所有失敗的文章
  report     - 顯示特定 Phase 的詳細報告
             用法: report 21  (查看 Phase 21 的報告)
  help       - 顯示此幫助信息

範例:
  node scripts/phase-21-27-status-check.js status
  node scripts/phase-21-27-status-check.js failed
  node scripts/phase-21-27-status-check.js report 21
      `);
      break;

    default:
      console.log(`未知命令: ${command}\n運行 'help' 查看說明`);
  }
}

main();
