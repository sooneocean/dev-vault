#!/usr/bin/env node
"use strict";
/**
 * windows-nodejs-rewriter.js
 *
 * Safe Obsidian vault section rewriter.
 * Searches via clausidian CLI, reads/writes via Obsidian Local REST API.
 *
 * Usage (single note):
 *   node scripts/windows-nodejs-rewriter.js --query "SEO自動化" --heading "SEO改寫版" --mode draft
 *   node scripts/windows-nodejs-rewriter.js --query "SEO自動化" --heading "摘要" --mode replace
 *   node scripts/windows-nodejs-rewriter.js --query "SEO自動化" --heading "Agent更新區" --mode draft --dry-run
 *
 * Usage (batch):
 *   node scripts/windows-nodejs-rewriter.js --batch tasks.json
 *   # tasks.json: [{"query":"...", "heading":"...", "mode":"draft"}, ...]
 *
 * Required env vars:
 *   OLR_API_KEY   - Obsidian Local REST API bearer token
 *   LLM_COMMAND   - command to invoke LLM (stdin = prompt, stdout = plain text)
 *
 * Optional env vars:
 *   OLR_BASE_URL  - default: https://127.0.0.1:27124
 *   OLR_INSECURE  - "true" to disable TLS verification (dev only)
 *   AGENT_NAME    - default: dex-rewriter
 */

const { spawnSync } = require("node:child_process");
const { readFileSync } = require("node:fs");
const https = require("node:https");

// ── CLI args ──────────────────────────────────────────────────────────────────

const args = parseArgs(process.argv.slice(2));

if (!args.batch) {
  if (!args.query)   fail("缺少 --query");
  if (!args.heading) fail("缺少 --heading");
}

// ── Config ────────────────────────────────────────────────────────────────────

const DRY_RUN = args.dryRun === true;

const CONFIG = {
  apiKey:    process.env.OLR_API_KEY || "",
  baseUrl:   process.env.OLR_BASE_URL || "https://127.0.0.1:27124",
  insecure:  (process.env.OLR_INSECURE || "").toLowerCase() === "true",
  agentName: process.env.AGENT_NAME || "dex-rewriter",
  llmCmd:    process.env.LLM_COMMAND || "",
};

if (!DRY_RUN && !CONFIG.apiKey)  fail("缺少環境變數 OLR_API_KEY（dry-run 模式可省略）");
if (!CONFIG.llmCmd)  fail("缺少環境變數 LLM_COMMAND");

// Must stay in sync with templates/t-rewrite-target.md human_locked_headings
const RISK_POLICY = {
  lockedHeadings: ["人類判斷區", "決策紀錄", "原始摘錄"],
  machineWritableDefault: ["Agent更新區", "摘要", "SEO改寫版", "下一步"],
};

// ── Resolve clausidian binary ─────────────────────────────────────────────────
// npm bin -g was removed in npm 9+; use npm root -g to derive the bin path.
// On Windows, spawnSync without shell:true can't resolve .cmd wrappers, so we
// use shell:true throughout clausidian invocations instead of a bare binary path.

const CLAUSIDIAN_BIN = "clausidian"; // resolved via PATH with shell:true

// ── Main ──────────────────────────────────────────────────────────────────────

async function processNote(query, heading, mode, dryRun) {
  if (dryRun) console.log("[dry-run] 不會呼叫 Obsidian REST API，不會寫入任何筆記");

  // 1. Search for target note
  const notePath = searchNotePath(query);
  console.log(`[1/7] 目標筆記：${notePath}`);

  // 2. Read full note and validate permissions
  const fullNote = dryRun
    ? `---\ntitle: ${query}\n---\n\n## ${heading}\n(dry-run 佔位內容)\n`
    : await getNote(notePath);
  const frontmatter = parseFrontmatter(fullNote);
  validateWritePermission(frontmatter, heading, mode);
  console.log(`[2/7] 已讀取筆記，權限驗證通過`);

  // 3. Verify target heading exists via document-map
  if (dryRun) {
    console.log(`[3/7] [dry-run] 跳過 document-map 驗證`);
  } else {
    await verifyHeadingExists(notePath, heading);
    console.log(`[3/7] heading「${heading}」確認存在`);
  }

  // 4. Read current section content
  const currentSection = dryRun
    ? "(dry-run 佔位)"
    : await getHeading(notePath, heading).catch(() => "");
  console.log(`[4/7] 已讀取 heading 內容（${currentSection.length} chars）`);

  // 5. Generate rewrite via LLM
  const prompt = buildRewritePrompt({ path: notePath, heading, mode, fullNote, currentSection });
  const rewritten = runLlm(prompt).trim();
  if (!rewritten) throw new Error("LLM 輸出為空，停止寫入");
  console.log(`[5/7] LLM 已產出內容（${rewritten.length} chars）`);

  // 6. Write to target heading
  const confidence = estimateConfidence({ currentSection, rewritten, mode });
  const finalMode   = chooseMode({ requestedMode: mode, confidence });
  console.log(`[6/7] 寫入模式：${finalMode}，confidence=${confidence}`);

  if (dryRun) {
    console.log(`[6/7] [dry-run] 跳過 PATCH heading。預覽內容：`);
    console.log("---");
    console.log(rewritten);
    console.log("---");
  } else {
    await patchHeading(notePath, heading, finalMode === "append" ? "append" : "replace", rewritten);
    console.log(`[6/7] 已寫入 heading：${heading}`);
  }

  // 7. Update frontmatter + append Agent Log
  const now = new Date().toISOString();

  if (dryRun) {
    console.log(`[7/7] [dry-run] 跳過 frontmatter/Agent Log 寫入`);
    console.log(`完成（dry-run）`);
    return;
  }

  await patchFrontmatter(notePath, "updated",    now);
  await patchFrontmatter(notePath, "agent",      CONFIG.agentName);
  await patchFrontmatter(notePath, "confidence", confidence);
  await patchFrontmatter(notePath, "source",     "agent-rewrite");

  const logBlock = [
    `## ${now}`,
    `- agent: ${CONFIG.agentName}`,
    `- action: ${finalMode === "append" ? "append-heading" : "replace-heading"}`,
    `- target: ${notePath}`,
    `- heading: ${heading}`,
    `- confidence: ${confidence}`,
    `- source: agent-rewrite`,
    `- mode: ${finalMode}`,
    `- summary: 透過外部 LLM 改寫指定 heading`,
    ``,
  ].join("\n");

  await patchHeading(notePath, "Agent Log", "append", logBlock, { createIfMissing: true });
  console.log(`[7/7] 已更新 frontmatter 與 Agent Log`);
  console.log(`完成`);
}

// ── Batch ──────────────────────────────────────────────────────────────────────

async function runBatch(batchFile) {
  let tasks;
  try {
    tasks = JSON.parse(readFileSync(batchFile, "utf8"));
  } catch (e) {
    fail(`無法讀取 batch 檔案 ${batchFile}：${e.message}`);
  }
  if (!Array.isArray(tasks) || tasks.length === 0) {
    fail("batch 檔案必須是非空 JSON 陣列，格式：[{query, heading, mode}, ...]");
  }

  console.log(`[batch] 共 ${tasks.length} 個任務`);
  const results = [];

  for (let i = 0; i < tasks.length; i++) {
    const { query, heading, mode } = tasks[i];
    const label = `[batch ${i + 1}/${tasks.length}]`;
    if (!query || !heading) {
      console.error(`${label} 跳過：缺少 query 或 heading`);
      results.push({ query, heading, status: "skipped" });
      continue;
    }
    console.log(`\n${label} ${query} → ${heading}`);
    try {
      await processNote(query, heading, mode || "draft", DRY_RUN);
      results.push({ query, heading, status: "ok" });
    } catch (err) {
      console.error(`${label} 失敗：${err.message}`);
      results.push({ query, heading, status: "error", error: err.message });
    }
  }

  const ok      = results.filter((r) => r.status === "ok").length;
  const failed  = results.filter((r) => r.status === "error").length;
  const skipped = results.filter((r) => r.status === "skipped").length;
  console.log(`\n[batch] 完成：${ok} 成功 / ${failed} 失敗 / ${skipped} 跳過`);
  if (failed > 0) process.exit(1);
}

// ── Search ────────────────────────────────────────────────────────────────────

function searchNotePath(query) {
  // Build full command string for shell:true to avoid DEP0190 (args-array + shell).
  // JSON.stringify escapes spaces and special chars in the query.
  const result = spawnSync(
    `${CLAUSIDIAN_BIN} search ${JSON.stringify(query)} --json`,
    { encoding: "utf8", shell: true, stdio: ["pipe", "pipe", "pipe"] }
  );

  if (result.status !== 0) {
    throw new Error(`clausidian search 失敗：${result.stderr || result.stdout}`);
  }

  let parsed;
  try {
    parsed = JSON.parse(result.stdout.trim());
  } catch {
    throw new Error(`無法解析 clausidian 搜尋結果：${result.stdout}`);
  }

  const results = parsed.results || [];

  if (results.length === 0) {
    throw new Error(`找不到符合查詢的筆記：${query}`);
  }
  if (results.length > 3) {
    throw new Error(
      `搜尋「${query}」結果過多（${results.length} 篇），無法確定唯一目標。` +
      `請使用更精準的查詢字串。`
    );
  }
  if (results.length > 1) {
    console.warn(
      `警告：搜尋到 ${results.length} 篇結果，取第一篇。` +
      `建議改用更精準的查詢。`
    );
  }

  const hit = results[0];
  // clausidian file field has no .md extension; subdir present for nested dirs
  return `${hit.subdir || hit.dir}/${hit.file}.md`;
}

// ── Permission validation ─────────────────────────────────────────────────────

function validateWritePermission(frontmatter, heading, mode) {
  if (RISK_POLICY.lockedHeadings.includes(heading)) {
    throw new Error(`heading「${heading}」屬於禁止改動區域（RISK_POLICY.lockedHeadings）`);
  }

  const humanLocked = Array.isArray(frontmatter.human_locked_headings)
    ? frontmatter.human_locked_headings
    : [];
  if (humanLocked.includes(heading)) {
    throw new Error(`heading「${heading}」在筆記的 human_locked_headings 中，禁止改寫`);
  }

  if (mode === "replace") {
    const machineWritable = Array.isArray(frontmatter.machine_writable_headings)
      ? frontmatter.machine_writable_headings
      : RISK_POLICY.machineWritableDefault;
    if (!machineWritable.includes(heading)) {
      throw new Error(
        `heading「${heading}」不在 machine_writable_headings 中。` +
        `replace 模式禁止寫入。改用 --mode draft 或 --mode append。`
      );
    }
  }
}

// ── Frontmatter parser ────────────────────────────────────────────────────────

function parseFrontmatter(md) {
  const match = md.match(/^---\r?\n([\s\S]*?)\r?\n---/);
  if (!match) return {};

  const obj = {};
  const lines = match[1].split(/\r?\n/);
  let currentListKey = null;

  for (const raw of lines) {
    const line = raw.trimEnd();
    if (!line) continue;

    // List item under a previous list key
    const listMatch = line.match(/^\s{2,}-\s+(.*)$/);
    if (listMatch && currentListKey) {
      obj[currentListKey].push(listMatch[1].trim());
      continue;
    }

    // Key: value
    const kv = line.match(/^([A-Za-z0-9_-]+):\s*(.*)$/);
    if (kv) {
      const key   = kv[1];
      const value = kv[2].trim();
      if (value === "") {
        currentListKey = key;
        obj[key] = [];
      } else {
        currentListKey = null;
        obj[key] = stripQuotes(value);
      }
      continue;
    }

    currentListKey = null;
  }

  return obj;
}

function stripQuotes(s) {
  if ((s.startsWith('"') && s.endsWith('"')) ||
      (s.startsWith("'") && s.endsWith("'"))) {
    return s.slice(1, -1);
  }
  return s;
}

// ── LLM ───────────────────────────────────────────────────────────────────────

// Heading-type intent detection — drives instruction #3 in the prompt.
const HEADING_INTENTS = {
  summary:    ["摘要", "summary", "overview", "概述", "簡介", "intro"],
  next_steps: ["下一步", "next", "todo", "action", "行動項目", "待辦"],
  seo:        ["seo", "關鍵字", "keyword", "meta"],
  status:     ["agent更新", "agent log", "狀態", "status", "進度", "update"],
  log:        ["log", "紀錄", "changelog", "history"],
};

const INTENT_INSTRUCTIONS = {
  summary:    "3. 提煉核心重點，使用簡潔條列或短段落，去除冗詞",
  next_steps: "3. 列出具體可執行的行動項目，使用 `- [ ]` checkbox 格式",
  seo:        "3. 優化關鍵字密度與可讀性，標題含主關鍵字，描述控制在 150 字以內",
  status:     "3. 以狀態更新格式撰寫：完成項目、當前阻礙、下一步行動",
  log:        "3. 以時間序條列新增項目，格式：`- YYYY-MM-DD: 事項`",
  general:    "3. 寫出更清楚、更有結構、更利於知識庫使用的版本",
};

function resolveHeadingIntent(heading) {
  const h = heading.toLowerCase();
  for (const [intent, keywords] of Object.entries(HEADING_INTENTS)) {
    if (keywords.some((k) => h.includes(k.toLowerCase()))) return intent;
  }
  return "general";
}

function buildRewritePrompt({ path, heading, mode, fullNote, currentSection }) {
  const intent      = resolveHeadingIntent(heading);
  const instruction = INTENT_INSTRUCTIONS[intent];
  return [
    "你是一個 Obsidian 知識庫重寫代理。",
    "你的任務是改寫指定 heading 的內容，不得碰其他區塊。",
    "",
    `目標筆記：${path}`,
    `目標 heading：${heading}`,
    `模式：${mode}`,
    `改寫意圖：${intent}`,
    "",
    "限制：",
    "1. 不得改寫人類判斷、決策立場或未指定區塊",
    "2. 保留原文關鍵資訊，不要虛構",
    instruction,
    "4. 使用繁體中文",
    "5. 不要輸出 Markdown code fence",
    "6. 直接輸出 heading 底下應有的正文內容",
    "",
    `目前 heading 內容如下：`,
    currentSection || "(空白)",
    "",
    "整篇筆記全文如下：",
    fullNote,
  ].join("\n").trim();
}

function runLlm(prompt) {
  // Pass the full command string to shell (avoids DEP0190 deprecation that
  // fires when combining shell:true with an args array).
  const res = spawnSync(CONFIG.llmCmd, {
    input:    prompt,
    encoding: "utf8",
    shell:    true,
  });

  if (res.status !== 0) {
    throw new Error(`LLM_COMMAND 執行失敗（exit ${res.status}）：${res.stderr || res.stdout}`);
  }
  return res.stdout;
}

function estimateConfidence({ currentSection, rewritten, mode }) {
  if (!rewritten || rewritten.length < 20) return 0.45;
  if (mode === "draft")   return 0.9;
  if (!currentSection)    return 0.72;
  return 0.84;
}

function chooseMode({ requestedMode, confidence }) {
  if (requestedMode === "append") return "append";
  if (requestedMode === "replace" && confidence >= 0.8) return "replace";
  return "append"; // downgrade replace→append if confidence low
}

// ── REST API helpers ──────────────────────────────────────────────────────────

/**
 * Low-level HTTPS request to Obsidian Local REST API.
 * Uses https.request() — native fetch in Node 24 silently ignores the agent
 * option, making rejectUnauthorized:false ineffective.
 */
function apiRequest(method, urlPath, extraHeaders = {}, bodyStr = null) {
  return new Promise((resolve, reject) => {
    const url  = new URL(CONFIG.baseUrl);
    const opts = {
      hostname:           url.hostname,
      port:               parseInt(url.port, 10) || (url.protocol === "https:" ? 443 : 80),
      path:               urlPath,
      method,
      rejectUnauthorized: !CONFIG.insecure,
      headers: {
        Authorization: `Bearer ${CONFIG.apiKey}`,
        ...extraHeaders,
      },
    };

    const req = (url.protocol === "https:" ? https : require("node:http")).request(opts, (res) => {
      let data = "";
      res.on("data", (chunk) => { data += chunk; });
      res.on("end", () => {
        if (res.statusCode >= 400) {
          reject(new Error(
            `REST API ${res.statusCode} ${res.statusMessage} — ${urlPath}\n${data.slice(0, 200)}`
          ));
          return;
        }
        resolve(data);
      });
    });

    req.on("error", reject);
    if (bodyStr !== null) req.write(bodyStr);
    req.end();
  });
}

/** Encode vault-relative path for use in URL segments. */
function encodePath(vaultRelPath) {
  return vaultRelPath.split("/").map(encodeURIComponent).join("/");
}

/**
 * Build the heading Target value required by Obsidian Local REST API 3.x.
 * Format: "NoteName::HeadingText"  (note name without .md extension)
 * This matches the format returned by document-map headings.
 */
function headingTarget(vaultRelPath, heading) {
  const noteName = vaultRelPath.split("/").pop().replace(/\.md$/i, "");
  return `${noteName}::${heading}`;
}

async function getNote(vaultRelPath) {
  return apiRequest("GET", `/vault/${encodePath(vaultRelPath)}`);
}

async function getDocumentMap(vaultRelPath) {
  const raw = await apiRequest(
    "GET",
    `/vault/${encodePath(vaultRelPath)}`,
    { Accept: "application/vnd.olrapi.document-map+json" }
  );
  try {
    return JSON.parse(raw);
  } catch {
    throw new Error(`無法解析 document-map 回應：${raw.slice(0, 200)}`);
  }
}

async function verifyHeadingExists(vaultRelPath, heading) {
  const map = await getDocumentMap(vaultRelPath);
  // document-map returns {headings: ["NoteName::HeadingName", ...]}
  // Strip the "NoteName::" prefix to get bare heading text.
  const headingNames = (map.headings || []).map((h) => {
    const sep = h.indexOf("::");
    return sep >= 0 ? h.slice(sep + 2) : h;
  });
  if (!headingNames.includes(heading)) {
    throw new Error(
      `heading「${heading}」不存在於筆記中。` +
      `可用 heading：${headingNames.join("、") || "(無)"}。` +
      `請確認 --heading 參數拼寫正確。`
    );
  }
}

async function getHeading(vaultRelPath, heading) {
  return apiRequest(
    "GET",
    `/vault/${encodePath(vaultRelPath)}`,
    {
      "Target-Type": "heading",
      "Target":      headingTarget(vaultRelPath, heading),
    }
  );
}

async function patchHeading(vaultRelPath, heading, operation, content, opts = {}) {
  const headers = {
    "Operation":    operation,
    "Target-Type":  "heading",
    "Target":       headingTarget(vaultRelPath, heading),
    "Content-Type": "text/markdown",
  };
  if (opts.createIfMissing) {
    headers["Create-Target-If-Missing"] = "true";
  }
  return apiRequest(
    "PATCH",
    `/vault/${encodePath(vaultRelPath)}`,
    headers,
    content
  );
}

async function patchFrontmatter(vaultRelPath, field, value) {
  return apiRequest(
    "PATCH",
    `/vault/${encodePath(vaultRelPath)}`,
    {
      "Operation":                "replace",
      "Target-Type":              "frontmatter",
      "Target":                   field,
      "Content-Type":             "application/json",
      "Create-Target-If-Missing": "true",
    },
    JSON.stringify(value)
  );
}

// ── Utilities ─────────────────────────────────────────────────────────────────

function parseArgs(argv) {
  const out = {};
  for (let i = 0; i < argv.length; i++) {
    const key = argv[i];
    const val = argv[i + 1];
    if (key === "--query")   { out.query   = val; i++; }
    if (key === "--heading") { out.heading = val; i++; }
    if (key === "--mode")    { out.mode    = val; i++; }
    if (key === "--batch")   { out.batch   = val; i++; }
    if (key === "--dry-run") { out.dryRun  = true; }
  }
  return out;
}

function fail(msg) {
  console.error(`ERROR: ${msg}`);
  process.exit(1);
}

// ── Entry ─────────────────────────────────────────────────────────────────────

const onError = (err) => fail(err.message || String(err));

if (args.batch) {
  runBatch(args.batch).catch(onError);
} else {
  processNote(args.query, args.heading, args.mode || "draft", DRY_RUN)
    .catch(onError);
}
