#!/usr/bin/env node
/**
 * llm-adapter.js
 *
 * Claude API stdin/stdout bridge.
 * Reads a prompt from stdin, calls claude messages.create, writes plain text to stdout.
 *
 * Usage (as LLM_COMMAND):
 *   LLM_COMMAND="node scripts/llm-adapter.js"
 *   echo "Your prompt here" | node scripts/llm-adapter.js
 *
 * Required env vars:
 *   ANTHROPIC_API_KEY  - Claude API key
 *
 * Optional env vars:
 *   LLM_MODEL          - Claude model ID (default: claude-sonnet-4-6)
 *   LLM_MAX_TOKENS     - Max output tokens (default: 2048)
 */

import Anthropic from "@anthropic-ai/sdk";

// ── Validate env ──────────────────────────────────────────────────────────────

if (!process.env.ANTHROPIC_API_KEY) {
  process.stderr.write("ERROR: ANTHROPIC_API_KEY is not set\n");
  process.exit(1);
}

const MODEL      = process.env.LLM_MODEL      || "claude-sonnet-4-6";
const MAX_TOKENS = parseInt(process.env.LLM_MAX_TOKENS || "2048", 10);

// ── Read stdin ────────────────────────────────────────────────────────────────

let prompt = "";
process.stdin.setEncoding("utf8");

process.stdin.on("data", (chunk) => {
  prompt += chunk;
});

process.stdin.on("close", async () => {
  prompt = prompt.trim();
  if (!prompt) {
    process.stderr.write("ERROR: stdin prompt is empty\n");
    process.exit(1);
  }

  try {
    const client = new Anthropic();

    const message = await client.messages.create({
      model:      MODEL,
      max_tokens: MAX_TOKENS,
      messages:   [{ role: "user", content: prompt }],
    });

    if (!message.content || message.content.length === 0) {
      process.stderr.write("ERROR: Claude returned empty content array\n");
      process.exit(1);
    }

    const block = message.content[0];
    if (block.type !== "text") {
      process.stderr.write(`ERROR: Expected text block, got: ${block.type}\n`);
      process.exit(1);
    }

    // Strip markdown code fences if the model wrapped output in them
    const cleaned = stripCodeFences(block.text);

    process.stdout.write(cleaned + "\n");
    process.exit(0);
  } catch (err) {
    process.stderr.write(`ERROR: Claude API call failed: ${err.message}\n`);
    process.exit(1);
  }
});

// ── Helpers ───────────────────────────────────────────────────────────────────

/**
 * Strip opening and closing markdown code fences.
 * e.g. "```markdown\n content \n```" → " content "
 */
function stripCodeFences(text) {
  return text
    .replace(/^```[\w-]*\r?\n?/m, "")
    .replace(/\r?\n?```\s*$/m, "")
    .trim();
}
