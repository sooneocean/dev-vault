#!/usr/bin/env node

/**
 * Phase 4 SEO Quality Validator
 *
 * 驗證生成的 SEO 數據質量：
 * 1. JSON 結構完整性
 * 2. 字符計數（標題、描述）
 * 3. 關鍵字相關性
 * 4. 隨機抽查（10 篇文章）
 *
 * 使用方式：
 * node phase4-seo-quality-validator.js [--task meta|schema|og|all]
 */

import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const OUTPUT_DIR = path.join(__dirname, "../seo-optimization-output");

const args = process.argv.slice(2);
const taskArg = args.find(a => a.startsWith("--task="))?.split("=")[1] || "all";

const tasks = taskArg === "all"
  ? ["meta", "schema", "og"]
  : [taskArg];

// ─── Utilities ────────────────────────────────────────────────────────────

function log(msg, level = "info") {
  const prefix = {
    info: "ℹ️",
    success: "✓",
    error: "❌",
    warning: "⚠️",
  }[level];
  console.log(`${prefix} ${msg}`);
}

function validateMetaOptimization(article) {
  const errors = [];
  const warnings = [];

  const title = article.meta?.optimizedTitle || "";
  const desc = article.meta?.metaDescription || "";
  const keywords = article.meta?.primaryKeywords || [];

  // 驗證標題
  if (!title) {
    errors.push("缺少 optimizedTitle");
  } else {
    const titleLength = [...title].length; // 計數中文字符
    if (titleLength < 40) {
      warnings.push(`標題太短 (${titleLength} 字)`);
    } else if (titleLength > 65) {
      warnings.push(`標題太長 (${titleLength} 字)`);
    }
  }

  // 驗證描述
  if (!desc) {
    errors.push("缺少 metaDescription");
  } else {
    const descLength = [...desc].length;
    if (descLength < 110) {
      warnings.push(`描述太短 (${descLength} 字)`);
    } else if (descLength > 165) {
      warnings.push(`描述太長 (${descLength} 字)`);
    }
  }

  // 驗證關鍵字
  if (!Array.isArray(keywords) || keywords.length === 0) {
    warnings.push("缺少關鍵字");
  } else if (keywords.length < 3) {
    warnings.push(`關鍵字不足 (${keywords.length} 個)`);
  } else if (keywords.length > 5) {
    warnings.push(`關鍵字過多 (${keywords.length} 個)`);
  }

  return { errors, warnings };
}

function validateSchemaMarkup(article) {
  const errors = [];
  const warnings = [];

  const schema = article.schema;

  if (!schema) {
    errors.push("缺少 Schema Markup");
    return { errors, warnings };
  }

  // 驗證必需字段
  if (!schema["@context"]) errors.push("缺少 @context");
  if (!schema["@type"]) errors.push("缺少 @type");
  if (!schema.headline) errors.push("缺少 headline");

  // 驗證值
  if (schema["@context"] !== "https://schema.org") {
    warnings.push(`@context 異常: ${schema["@context"]}`);
  }

  if (schema.datePublished && !isValidDate(schema.datePublished)) {
    warnings.push(`datePublished 格式異常`);
  }

  return { errors, warnings };
}

function validateOGTags(article) {
  const errors = [];
  const warnings = [];

  const og = article.og;

  if (!og) {
    errors.push("缺少 OG Tags");
    return { errors, warnings };
  }

  // 驗證必需字段
  const requiredFields = ["og:title", "og:description", "og:url", "og:type"];
  requiredFields.forEach(field => {
    if (!og[field]) errors.push(`缺少 ${field}`);
  });

  // 驗證字符計數
  if (og["og:title"]) {
    const titleLen = [...og["og:title"]].length;
    if (titleLen < 40 || titleLen > 60) {
      warnings.push(`og:title 長度異常 (${titleLen} 字)`);
    }
  }

  if (og["og:description"]) {
    const descLen = [...og["og:description"]].length;
    if (descLen < 90 || descLen > 125) {
      warnings.push(`og:description 長度異常 (${descLen} 字)`);
    }
  }

  return { errors, warnings };
}

function isValidDate(dateString) {
  const date = new Date(dateString);
  return date instanceof Date && !isNaN(date);
}

// ─── Validation Logic ────────────────────────────────────────────────────

function validateTask(taskType, dataFile) {
  if (!fs.existsSync(dataFile)) {
    log(`❌ 文件不存在: ${dataFile}`, "error");
    return null;
  }

  const data = JSON.parse(fs.readFileSync(dataFile, "utf-8"));
  const validation = {
    task: taskType,
    file: dataFile,
    timestamp: new Date().toISOString(),
    totalArticles: data.articles.length,
    validation: {
      passed: 0,
      warnings: 0,
      errors: 0,
      details: [],
    },
    sampleCheck: [],
  };

  // 驗證所有文章
  data.articles.forEach(article => {
    let articleValidation = {};

    switch (taskType) {
      case "meta":
        articleValidation = validateMetaOptimization(article);
        break;
      case "schema":
        articleValidation = validateSchemaMarkup(article);
        break;
      case "og":
        articleValidation = validateOGTags(article);
        break;
    }

    const { errors, warnings } = articleValidation;
    const status = errors.length === 0 ? "pass" : "fail";

    validation.validation.details.push({
      id: article.id,
      title: article.title,
      status,
      errors,
      warnings,
    });

    if (status === "pass") {
      validation.validation.passed++;
    }
    validation.validation.warnings += warnings.length;
    validation.validation.errors += errors.length;
  });

  // 隨機抽查 10 篇
  const sampleSize = Math.min(10, data.articles.length);
  const sampleIndices = Array.from(
    { length: data.articles.length },
    (_, i) => i
  )
    .sort(() => Math.random() - 0.5)
    .slice(0, sampleSize);

  validation.sampleCheck = sampleIndices.map(i => {
    const article = data.articles[i];
    return {
      id: article.id,
      title: article.title,
      content: article[taskType],
    };
  });

  return validation;
}

// ─── Report Generation ────────────────────────────────────────────────────

function generateReport(validations) {
  const report = {
    timestamp: new Date().toISOString(),
    summary: {
      tasksValidated: validations.length,
      totalArticles: 0,
      passRate: 0,
      totalErrors: 0,
      totalWarnings: 0,
    },
    tasks: validations,
  };

  // 計算統計
  let totalArticles = 0;
  let totalPassed = 0;
  let totalErrors = 0;
  let totalWarnings = 0;

  validations.forEach(v => {
    totalArticles += v.totalArticles;
    totalPassed += v.validation.passed;
    totalErrors += v.validation.errors;
    totalWarnings += v.validation.warnings;
  });

  report.summary.totalArticles = totalArticles;
  report.summary.passRate = totalArticles > 0
    ? ((totalPassed / totalArticles) * 100).toFixed(2) + "%"
    : "N/A";
  report.summary.totalErrors = totalErrors;
  report.summary.totalWarnings = totalWarnings;

  return report;
}

// ─── Main ───────────────────────────────────────────────────────────────

function main() {
  log(`\n════════════════════════════════════════`);
  log(`Phase 4 SEO Quality Validator`);
  log(`════════════════════════════════════════`);

  const validations = [];

  for (const task of tasks) {
    log(`\n驗證 ${task.toUpperCase()} ...`);

    const dataFile = path.join(OUTPUT_DIR, `${task}_optimization_results.json`);
    const validation = validateTask(task, dataFile);

    if (validation) {
      validations.push(validation);

      // 列印摘要
      log(`\n[${task.toUpperCase()}] 驗證結果`);
      log(`  總文章數: ${validation.totalArticles}`);
      log(`  通過: ${validation.validation.passed}`);
      log(`  錯誤: ${validation.validation.errors}`);
      log(`  警告: ${validation.validation.warnings}`);

      // 列出錯誤
      const errorArticles = validation.validation.details.filter(d => d.errors.length > 0);
      if (errorArticles.length > 0) {
        log(`\n  ❌ 有錯誤的文章 (${errorArticles.length}):`, "warning");
        errorArticles.slice(0, 5).forEach(a => {
          log(`     ID ${a.id}: ${a.errors.join(", ")}`);
        });
        if (errorArticles.length > 5) {
          log(`     ... 還有 ${errorArticles.length - 5} 篇`);
        }
      }
    }
  }

  // 生成報告
  if (validations.length > 0) {
    const report = generateReport(validations);

    const reportFile = path.join(OUTPUT_DIR, "PHASE4_QUALITY_VALIDATION_REPORT.json");
    fs.writeFileSync(reportFile, JSON.stringify(report, null, 2));

    log(`\n════════════════════════════════════════`);
    log(`✓ 驗證完成`);
    log(`════════════════════════════════════════`);
    log(`通過率: ${report.summary.passRate}`);
    log(`錯誤: ${report.summary.totalErrors}`);
    log(`警告: ${report.summary.totalWarnings}`);
    log(`\n報告已保存: ${reportFile}`);
  } else {
    log(`❌ 沒有找到驗證的文件`, "error");
  }
}

main();
