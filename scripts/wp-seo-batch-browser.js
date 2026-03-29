/**
 * YOLO LAB — Browser Batch SEO Optimizer (localStorage-persistent)
 *
 * Survives page reloads by storing state in localStorage.
 * Each page load processes one post, then navigates to the next.
 *
 * SETUP:
 *   1. Open any post editor: /wp-admin/post.php?post=XXXX&action=edit
 *   2. Open DevTools Console (F12)
 *   3. Paste this script and press Enter
 *   4. It will scan all posts, then auto-process them one by one
 *
 * COMMANDS (run in console on any wp-admin page):
 *   window.__SEO_STATUS()  — show progress
 *   window.__SEO_STOP()    — stop after current post
 *   window.__SEO_RESET()   — clear all state and stop
 *   window.__SEO_RESUME()  — resume from where it stopped
 */

(async function () {
  "use strict";

  const STORAGE_KEY = "yololab_seo_batch";
  const EDITOR_WAIT = 5000; // ms to wait for editor
  const SAVE_WAIT = 3000; // ms to wait after save

  // ── Keyphrase generator ──────────────────────────────────────────
  function generateKeyphrase(title) {
    title = title
      .replace(/&amp;/g, "&")
      .replace(/&#\d+;/g, "")
      .trim();

    // Strategy 1: Extract《bracket content》with context
    const bracketMatch = title.match(/《([^》]+)》/);
    if (bracketMatch) {
      const bracket = bracketMatch[1].trim();
      const before = title.substring(0, title.indexOf("《")).trim();
      const afterRaw = title.substring(title.indexOf("》") + 1);
      const after = afterRaw.replace(/^[：:，,、\s]+/, "");

      if (before.length > 0 && before.length <= 12) {
        const clean = before.replace(/[！!？?。，,：:；;、\s]+$/, "");
        if (clean.length > 0) return clean + " " + bracket;
      }

      const full = title + " " + after;
      if (/影評|影帝|影后|票房|上映|院線|IMAX|電影|導演|演技/.test(full)) {
        return bracket + " 電影";
      }
      if (/實測|開箱|評價|推薦|試吃|味蕾/.test(full)) {
        return bracket + " 評價";
      }
      return bracket;
    }

    // Strategy 2: First meaningful segment
    const segments = title.split(/[：|｜！？!?\-—–\/]/);
    let first = (segments[0] || title).trim();

    if (first.length > 15) {
      const sub = first.split(/[，,、\s]+/).filter((s) => s.length > 1);
      if (sub.length > 1) first = sub.slice(0, 2).join(" ");
    }
    if (first.length > 20) first = first.substring(0, 15);

    return first.replace(/[，,。！!？?：:；;、\s]+$/, "");
  }

  // ── State management ─────────────────────────────────────────────
  function loadState() {
    try {
      return JSON.parse(localStorage.getItem(STORAGE_KEY)) || null;
    } catch {
      return null;
    }
  }

  function saveState(state) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  }

  function clearState() {
    localStorage.removeItem(STORAGE_KEY);
  }

  // ── Global commands ──────────────────────────────────────────────
  window.__SEO_STATUS = function () {
    const s = loadState();
    if (!s) {
      console.log("No batch in progress.");
      return;
    }
    console.log(
      `Progress: ${s.currentIndex}/${s.posts.length} | Updated: ${s.updated} | Skipped: ${s.skipped} | Errors: ${s.errors}`,
    );
    console.log(`Status: ${s.status}`);
  };

  window.__SEO_STOP = function () {
    const s = loadState();
    if (s) {
      s.status = "stopped";
      saveState(s);
    }
    console.log("Will stop after current post.");
  };

  window.__SEO_RESET = function () {
    clearState();
    console.log("State cleared.");
  };

  window.__SEO_RESUME = function () {
    const s = loadState();
    if (!s) {
      console.log("No state to resume. Run the script again.");
      return;
    }
    s.status = "running";
    saveState(s);
    processNext();
  };

  // ── Helpers ──────────────────────────────────────────────────────
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

  function isEditorPage() {
    return (
      window.location.href.includes("post.php") &&
      window.location.href.includes("action=edit")
    );
  }

  async function waitForYoast(maxRetries = 15) {
    for (let i = 0; i < maxRetries; i++) {
      if (window.wp?.data?.select?.("yoast-seo/editor")) return true;
      await sleep(1000);
    }
    return false;
  }

  // ── Process current post ─────────────────────────────────────────
  async function processCurrentPost() {
    const state = loadState();
    if (!state || state.status !== "running") return;
    if (state.currentIndex >= state.posts.length) {
      state.status = "complete";
      saveState(state);
      console.log(
        "%c=== ALL DONE ===",
        "color: #00d4aa; font-size: 16px; font-weight: bold",
      );
      console.log(
        `Updated: ${state.updated} | Skipped: ${state.skipped} | Errors: ${state.errors}`,
      );
      return;
    }

    if (!isEditorPage()) return;

    const post = state.posts[state.currentIndex];
    const progress = `[${state.currentIndex + 1}/${state.posts.length}]`;

    console.log(`%c${progress} Processing #${post.id}...`, "color: #ffa500");

    // Wait for Yoast
    const yoastReady = await waitForYoast();
    if (!yoastReady) {
      console.warn(`${progress} Yoast not loaded, skipping #${post.id}`);
      state.errors++;
      state.currentIndex++;
      saveState(state);
      processNext();
      return;
    }

    // Check if already has focus keyphrase
    const existing = wp.data.select("yoast-seo/editor").getFocusKeyphrase?.();
    if (existing && existing.trim().length > 0) {
      console.log(
        `${progress} Already has keyphrase: "${existing}" — skipping`,
      );
      state.skipped++;
      state.currentIndex++;
      saveState(state);
      processNext();
      return;
    }

    // Set focus keyphrase
    wp.data.dispatch("yoast-seo/editor").setFocusKeyword(post.kw);
    wp.data.dispatch("yoast-seo/editor").runAnalysis();
    await sleep(2000);

    // Save
    wp.data.dispatch("core/editor").editPost({ meta: {} });
    await wp.data.dispatch("core/editor").savePost();
    await sleep(SAVE_WAIT);

    // Verify
    const finalKw = wp.data.select("yoast-seo/editor").getFocusKeyphrase();
    const saved = !wp.data.select("core/editor").isSavingPost();

    if (saved && finalKw === post.kw) {
      console.log(
        `%c${progress} ✅ #${post.id} → "${post.kw}"`,
        "color: #00d4aa",
      );
      state.updated++;
    } else {
      console.warn(`${progress} Save may have failed for #${post.id}`);
      state.errors++;
    }

    state.currentIndex++;
    saveState(state);

    // Navigate to next
    processNext();
  }

  function processNext() {
    const state = loadState();
    if (!state || state.status !== "running") return;
    if (state.currentIndex >= state.posts.length) {
      state.status = "complete";
      saveState(state);
      console.log(
        "%c=== BATCH COMPLETE ===",
        "color: #00d4aa; font-size: 16px",
      );
      console.log(
        `Updated: ${state.updated} | Skipped: ${state.skipped} | Errors: ${state.errors}`,
      );
      return;
    }

    const next = state.posts[state.currentIndex];
    console.log(`Navigating to post #${next.id}...`);
    window.location.href = `/wp-admin/post.php?post=${next.id}&action=edit`;
  }

  // ── Initialize ───────────────────────────────────────────────────
  const existingState = loadState();

  if (existingState && existingState.status === "running") {
    // Resuming after page reload
    console.log("%c[SEO Batch] Resuming...", "color: #00d4aa");
    await sleep(EDITOR_WAIT);
    processCurrentPost();
    return;
  }

  if (existingState && existingState.status === "stopped") {
    console.log(
      "Batch is stopped. Run __SEO_RESUME() to continue, or __SEO_RESET() to start over.",
    );
    return;
  }

  if (existingState && existingState.status === "complete") {
    console.log(
      "Previous batch completed. Run __SEO_RESET() to start a new batch.",
    );
    return;
  }

  // ── Fresh start: scan all posts ──────────────────────────────────
  const nonce = window.wpApiSettings?.nonce;
  if (!nonce) {
    console.error("Not on a wp-admin page with API access.");
    return;
  }

  console.log(
    "%c=== YOLO LAB SEO Batch Optimizer ===",
    "color: #00d4aa; font-size: 16px; font-weight: bold",
  );
  console.log("%c[Phase 1] Scanning all published posts...", "color: #ffa500");

  const allPosts = [];
  let page = 1;
  let totalPages = 1;

  while (page <= totalPages) {
    const res = await fetch(
      `/wp-json/wp/v2/posts?per_page=100&page=${page}&status=publish&orderby=date&order=desc&_fields=id,title`,
      { headers: { "X-WP-Nonce": nonce } },
    );
    totalPages = parseInt(res.headers.get("X-WP-TotalPages"), 10);
    const total = res.headers.get("X-WP-Total");
    const posts = await res.json();

    for (const p of posts) {
      const title = p.title?.rendered || "";
      allPosts.push({
        id: p.id,
        title: title.substring(0, 50),
        kw: generateKeyphrase(title),
      });
    }

    console.log(
      `  Page ${page}/${totalPages} — ${allPosts.length}/${total} scanned`,
    );
    page++;
    await sleep(300);
  }

  console.log(
    `%c[Phase 1 Complete] ${allPosts.length} posts ready`,
    "color: #00d4aa",
  );

  // Save state and start processing
  const newState = {
    status: "running",
    posts: allPosts,
    currentIndex: 0,
    updated: 0,
    skipped: 0,
    errors: 0,
    startedAt: new Date().toISOString(),
  };
  saveState(newState);

  console.log("%c[Phase 2] Starting batch processing...", "color: #ffa500");
  console.log("Commands: __SEO_STATUS() | __SEO_STOP() | __SEO_RESET()");

  // Navigate to first post
  processNext();
})();
