#!/usr/bin/env node

/**
 * Phase 5-8 Progress Reporter
 * 生成詳細的進度和統計報告
 */

import fs from "fs";
import path from "path";

const PHASES = [5, 6, 7, 8];

function formatTime(ms) {
  const mins = Math.floor(ms / 60000);
  const secs = ((ms % 60000) / 1000).toFixed(0);
  return `${mins}m ${secs}s`;
}

function getProgressFile(phase) {
  return `phase${phase}-progress.json`;
}

function loadPhaseData(phase) {
  const file = getProgressFile(phase);
  if (!fs.existsSync(file)) {
    return null;
  }
  try {
    return JSON.parse(fs.readFileSync(file, "utf-8"));
  } catch (e) {
    console.error(`❌ 無法讀取 ${file}`);
    return null;
  }
}

function generateReport() {
  console.log("\n" + "=".repeat(70));
  console.log("📊 Phase 5-8 進度報告");
  console.log("=".repeat(70) + "\n");

  const allPhases = {};
  let totalSuccess = 0;
  let totalTimeout = 0;
  let totalFailed = 0;
  let totalProcessed = 0;

  // 收集所有 Phase 的數據
  for (const phase of PHASES) {
    const data = loadPhaseData(phase);
    if (!data) {
      console.log(`⚠️  Phase ${phase}: 未找到進度文件\n`);
      continue;
    }

    allPhases[phase] = data;
    totalSuccess += data.success.length;
    totalTimeout += data.timeout.length;
    totalFailed += data.failed.length;
    totalProcessed += data.processed;
  }

  // Phase 細節
  console.log("📈 各 Phase 統計:\n");
  for (const phase of PHASES) {
    const data = allPhases[phase];
    if (!data) continue;

    const success = data.success.length;
    const timeout = data.timeout.length;
    const failed = data.failed.length;
    const total = success + timeout + failed;
    const successRate = total > 0 ? ((success / total) * 100).toFixed(1) : "N/A";

    console.log(`  Phase ${phase}:`);
    console.log(
      `    ✅ 成功:  ${success.toString().padStart(3)} / ${total} (${successRate}%)`
    );
    if (timeout > 0) {
      console.log(`    ⏱️  超時:  ${timeout.toString().padStart(3)}`);
    }
    if (failed > 0) {
      console.log(`    ❌ 失敗:  ${failed.toString().padStart(3)}`);
      // 列出失敗的文章
      const failedIds = data.failed.slice(0, 3);
      failedIds.forEach((f) => {
        console.log(
          `       - #${f.id}: ${f.error.substring(0, 50)}${f.error.length > 50 ? "..." : ""}`
        );
      });
      if (data.failed.length > 3) {
        console.log(
          `       ... 以及 ${data.failed.length - 3} 篇 (見詳細報告)`
        );
      }
    }
    console.log();
  }

  // 總體統計
  console.log("-".repeat(70));
  console.log("\n🎯 總體統計:\n");
  const grandTotal = totalSuccess + totalTimeout + totalFailed;
  const successRate =
    grandTotal > 0 ? ((totalSuccess / grandTotal) * 100).toFixed(1) : "N/A";
  const failureRate =
    grandTotal > 0 ? ((totalFailed / grandTotal) * 100).toFixed(1) : "N/A";

  console.log(`  ✅ 成功:  ${totalSuccess.toString().padStart(3)} / 400 (${successRate}%)`);
  console.log(`  ⏱️  超時:  ${totalTimeout.toString().padStart(3)} / 400`);
  console.log(`  ❌ 失敗:  ${totalFailed.toString().padStart(3)} / 400 (${failureRate}%)\n`);

  // 進度狀態
  console.log("-".repeat(70));
  console.log("\n⏳ 執行狀態:\n");

  let allComplete = true;
  for (const phase of PHASES) {
    const data = allPhases[phase];
    if (!data) {
      console.log(`  Phase ${phase}: ⏳ 未開始`);
      allComplete = false;
    } else {
      const total = data.success.length + data.timeout.length + data.failed.length;
      if (total === 100) {
        console.log(`  Phase ${phase}: ✅ 完成 (${total}/100)`);
      } else {
        console.log(`  Phase ${phase}: 🔄 進行中 (${total}/100)`);
        allComplete = false;
      }
    }
  }

  console.log();

  // 完成時間估計
  if (!allComplete) {
    console.log("-".repeat(70));
    console.log("\n⏱️  耗時估計:\n");

    // 計算已耗時
    let startTime = null;
    for (const phase of PHASES) {
      const data = allPhases[phase];
      if (data && data.startTime) {
        if (!startTime) startTime = new Date(data.startTime);
      }
    }

    if (startTime) {
      const elapsed = Date.now() - startTime;
      console.log(`  已耗時: ${formatTime(elapsed)}`);

      // 估計剩餘時間（基於已完成的篇數）
      if (totalProcessed > 0) {
        const avgTimePerArticle = elapsed / totalProcessed;
        const remaining = 400 - totalProcessed;
        const estimatedRemaining = avgTimePerArticle * remaining;
        console.log(
          `  每篇平均: ${(avgTimePerArticle / 1000).toFixed(2)} 秒`
        );
        console.log(
          `  剩餘篇數: ${remaining}`
        );
        console.log(
          `  估計完成: ${formatTime(elapsed + estimatedRemaining)}`
        );
      }
    }
    console.log();
  }

  // 建議
  console.log("-".repeat(70));
  console.log("\n💡 建議:\n");

  if (allComplete) {
    console.log(`  ✅ 所有 Phase 已完成！`);
    if (totalFailed === 0) {
      console.log(`  🎉 完美！所有 400 篇文章已成功優化`);
    } else if (totalFailed < 5) {
      console.log(
        `  ⚠️  有 ${totalFailed} 篇失敗，建議手動檢查`
      );
    }
  } else {
    const remaining = 400 - totalProcessed;
    if (remaining > 300) {
      console.log(`  ℹ️  正在進行中，已完成 ${totalProcessed}/400 (${((totalProcessed/400)*100).toFixed(1)}%)`);
      console.log(`  ℹ️  剩餘約 ${remaining} 篇，預計再需 ${((remaining/100)*150).toFixed(0)} 分鐘`);
    } else if (remaining > 100) {
      console.log(
        `  ℹ️  已完成 3/4，衝刺階段！剩餘 ${remaining} 篇`
      );
    } else if (remaining > 0) {
      console.log(
        `  🏁 即將完成！剩餘 ${remaining} 篇`
      );
    }
  }

  console.log();
  console.log("=".repeat(70));
  console.log();
}

// ─── 導出詳細 JSON 報告 ───────────────────────────────────────────────────

function exportJsonReport(filename = "seo-phase-5-8-report.json") {
  const report = {
    timestamp: new Date().toISOString(),
    phases: {},
    summary: {
      totalSuccess: 0,
      totalTimeout: 0,
      totalFailed: 0,
    },
  };

  for (const phase of PHASES) {
    const data = loadPhaseData(phase);
    if (!data) continue;

    report.phases[phase] = {
      success: data.success.length,
      timeout: data.timeout.length,
      failed: data.failed,
    };

    report.summary.totalSuccess += data.success.length;
    report.summary.totalTimeout += data.timeout.length;
    report.summary.totalFailed += data.failed.length;
  }

  fs.writeFileSync(filename, JSON.stringify(report, null, 2));
  console.log(`\n💾 詳細報告已導出: ${filename}\n`);
}

// ─── Main ───────────────────────────────────────────────────────────────────

const args = process.argv.slice(2);
if (args.includes("--json")) {
  const filename = args[args.indexOf("--json") + 1] || "seo-phase-5-8-report.json";
  exportJsonReport(filename);
} else if (args.includes("--help")) {
  console.log(`
Phase 5-8 Progress Reporter

用法:
  node scripts/phase-5-8-report.js              # 顯示進度報告
  node scripts/phase-5-8-report.js --json       # 導出 JSON 報告
  node scripts/phase-5-8-report.js --json FILE  # 導出到指定文件

選項:
  --help    顯示此幫助
  --json    導出 JSON 格式報告
`);
} else {
  generateReport();
}
