/**
 * Proposal Engine
 * Generates feature proposals for the next version using Claude API
 *
 * Input: GitHub context (release notes, open issues, closed PRs) + vault learnings
 * Output: Structured array of proposals with effort/value estimates and priority ranking
 */

const Anthropic = require("@anthropic-ai/sdk").default;

/**
 * Generate feature proposals for the next version
 *
 * @param {Object} githubContext - GitHub data
 * @param {string} githubContext.lastRelease - Last release notes/summary
 * @param {Array} githubContext.openIssues - Open issues with title and labels
 * @param {Array} githubContext.closedPRs - Recently closed/merged PRs
 * @param {Object} vaultContext - Vault learnings and project context
 * @param {string} vaultContext.projectGoals - Project goals from vault
 * @param {string} vaultContext.learnings - Research/architecture learnings
 * @param {boolean} options.debug - Enable debug logging
 * @returns {Promise<Array>} Array of proposals with structure:
 *   [{
 *     title: string,
 *     problem: string,
 *     effort: 'S' | 'M' | 'L',
 *     value: 'L' | 'M' | 'H',
 *     priority: number,
 *     rationale: string,
 *     relatedIssues: string[]
 *   }]
 */
async function generateProposals(githubContext, vaultContext, options = {}) {
  const { debug = false } = options;

  // Validate inputs
  if (!githubContext) {
    throw new Error("githubContext is required");
  }

  const client = new Anthropic({
    apiKey: process.env.ANTHROPIC_API_KEY,
  });

  // Build context prompt
  const contextPrompt = buildContextPrompt(githubContext, vaultContext);

  if (debug) {
    console.log("[Proposal Engine] Context prompt:\n", contextPrompt);
  }

  // Call Claude API
  const message = await client.messages.create({
    model: "claude-opus-4-1",
    max_tokens: 2048,
    messages: [
      {
        role: "user",
        content: contextPrompt,
      },
    ],
  });

  const responseText =
    message.content[0].type === "text" ? message.content[0].text : "";

  if (debug) {
    console.log("[Proposal Engine] Claude response:\n", responseText);
  }

  // Parse response into structured proposals
  const proposals = parseProposalsResponse(responseText);

  if (debug) {
    console.log(
      "[Proposal Engine] Parsed proposals:",
      JSON.stringify(proposals, null, 2),
    );
  }

  return proposals;
}

/**
 * Build the context prompt for Claude to generate proposals
 */
function buildContextPrompt(githubContext, vaultContext) {
  const {
    lastRelease = "No previous release",
    openIssues = [],
    closedPRs = [],
  } = githubContext;
  const { projectGoals = "", learnings = "" } = vaultContext || {};

  const issuesText =
    openIssues.length > 0
      ? openIssues
          .map(
            (issue) =>
              `- ${issue.title} (${issue.labels?.join(", ") || "no labels"})`,
          )
          .join("\n")
      : "No open issues";

  const prsText =
    closedPRs.length > 0
      ? closedPRs
          .map((pr) => `- ${pr.title} (${pr.labels?.join(", ") || ""})`)
          .join("\n")
      : "No recent PRs";

  const learnersText = learnings ? `\n\nProject Learnings:\n${learnings}` : "";
  const goalsText = projectGoals ? `\n\nProject Goals:\n${projectGoals}` : "";

  return `You are a product manager helping to propose features for the next version of a software project.

## Context

### Last Release
${lastRelease}

### Open Issues (Feature Requests & Improvements)
${issuesText}

### Recently Completed Work (Closed PRs since last release)
${prsText}
${learnersText}${goalsText}

## Task

Propose **3-5 features** for the next version, prioritized by value/effort ratio.

For each proposal, provide:
1. **Title**: Concise feature title
2. **Problem**: 1-2 sentences explaining the problem/need
3. **Effort Estimate**: S (< 1 day), M (1-3 days), or L (1+ week)
4. **Value Estimate**: L (Low), M (Medium), or H (High)
5. **Priority**: Numeric ranking (1 = highest priority)
6. **Rationale**: Why this feature matters, linked to issues/context if available

Format each proposal as a numbered list. Use this structure:

**Proposal N: [Title]**
- Problem: [problem statement]
- Effort: [S|M|L]
- Value: [L|M|H]
- Priority: [number]
- Rationale: [explanation]

Return exactly 3-5 proposals, ranked by value/effort ratio (highest ratio first).`;
}

/**
 * Parse Claude's response into structured proposals
 */
function parseProposalsResponse(responseText) {
  const proposals = [];
  const proposalRegex = /\*\*Proposal\s+(\d+):\s*(.+?)\*\*/g;
  const detailRegex = /^-\s*(\w+):\s*(.+)$/gm;

  let proposalMatch;

  while ((proposalMatch = proposalRegex.exec(responseText)) !== null) {
    const proposalNum = parseInt(proposalMatch[1]);
    const title = proposalMatch[2].trim();

    // Extract the section for this proposal
    const startIdx = proposalMatch.index + proposalMatch[0].length;
    const nextProposal = proposalRegex.exec(responseText);
    proposalRegex.lastIndex = startIdx; // Reset for next iteration

    const endIdx =
      nextProposal && nextProposal.index
        ? nextProposal.index
        : responseText.length;
    const proposalSection = responseText.substring(startIdx, endIdx);

    // Parse details from proposal section
    const details = {};
    let detailMatch;

    while ((detailMatch = detailRegex.exec(proposalSection)) !== null) {
      const key = detailMatch[1].toLowerCase();
      const value = detailMatch[2].trim();
      details[key] = value;
    }

    // Extract effort, value, priority
    const effort = extractEffort(details.effort);
    const value = extractValue(details.value);
    const priority = parseInt(details.priority || proposalNum) || proposalNum;

    // Extract related issues (e.g., #123, #456)
    const relatedIssues = extractIssueNumbers(details.rationale || "");

    if (title) {
      proposals.push({
        title,
        problem: details.problem || "",
        effort,
        value,
        priority,
        rationale: details.rationale || "",
        relatedIssues,
      });
    }
  }

  // If no proposals were parsed, return empty array
  // (error handling will be done by caller)
  return proposals;
}

/**
 * Extract effort estimate (S/M/L)
 */
function extractEffort(effortStr) {
  if (!effortStr) return "M"; // Default
  const match = effortStr.match(/[SML]/i);
  return match ? match[0].toUpperCase() : "M";
}

/**
 * Extract value estimate (L/M/H)
 */
function extractValue(valueStr) {
  if (!valueStr) return "M"; // Default
  const match = valueStr.match(/[LMH]/i);
  return match ? match[0].toUpperCase() : "M";
}

/**
 * Extract issue numbers from text (e.g., #123)
 */
function extractIssueNumbers(text) {
  const matches = text.match(/#(\d+)/g) || [];
  return matches.map((m) => m.substring(1));
}

module.exports = {
  generateProposals,
};
