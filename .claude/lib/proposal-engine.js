/**
 * AI Feature Proposal Engine
 *
 * Generates feature proposals by analyzing:
 * - Last release notes
 * - Open issues (feature requests)
 * - Recently completed PRs
 * - Vault learnings (project context)
 */

const https = require("https");

class ProposalEngine {
  constructor(options = {}) {
    this.apiKey = options.apiKey || process.env.ANTHROPIC_API_KEY;
    this.model = options.model || "claude-opus-4-6";

    if (!this.apiKey) {
      throw new Error(
        "Anthropic API key not provided. Set ANTHROPIC_API_KEY env var or pass apiKey in options.",
      );
    }
  }

  /**
   * Call Claude API to generate proposals
   * @private
   */
  async _callClaudeAPI(prompt) {
    return new Promise((resolve, reject) => {
      const payload = JSON.stringify({
        model: this.model,
        max_tokens: 2000,
        messages: [
          {
            role: "user",
            content: prompt,
          },
        ],
      });

      const options = {
        hostname: "api.anthropic.com",
        port: 443,
        path: "/v1/messages",
        method: "POST",
        headers: {
          "x-api-key": this.apiKey,
          "anthropic-version": "2023-06-01",
          "content-type": "application/json",
        },
      };

      const req = https.request(options, (res) => {
        let data = "";

        res.on("data", (chunk) => {
          data += chunk;
        });

        res.on("end", () => {
          try {
            const parsed = JSON.parse(data);

            if (res.statusCode >= 400) {
              reject(
                new Error(
                  `Claude API error (${res.statusCode}): ${parsed.error?.message || data}`,
                ),
              );
              return;
            }

            resolve(parsed);
          } catch (error) {
            reject(new Error(`Failed to parse Claude API response: ${error}`));
          }
        });
      });

      req.on("error", reject);
      req.write(payload);
      req.end();
    });
  }

  /**
   * Generate feature proposals from context
   * @param {Object} params
   * @param {string} params.lastReleaseNotes - Changelog of last release
   * @param {Array} params.openIssues - Array of open feature request issues
   * @param {Array} params.recentPRs - Recently completed PRs
   * @param {string} params.vaultContext - Project context from vault
   * @returns {Promise<Array>} Array of proposal objects
   */
  async generateProposals(params) {
    const {
      lastReleaseNotes = "",
      openIssues = [],
      recentPRs = [],
      vaultContext = "",
    } = params;

    // Format context for the prompt
    const issuesText =
      openIssues.length > 0
        ? openIssues
            .map((i) => `- ${i.title} (${i.labels.join(", ") || "no label"})`)
            .join("\n")
        : "(No open feature requests)";

    const prsText =
      recentPRs.length > 0
        ? recentPRs.map((p) => `- ${p.title}`).join("\n")
        : "(No recent PRs)";

    const prompt = `You are a product manager analyzing a software project's development history to propose the next features.

## Last Release
${lastReleaseNotes || "(Initial release or no previous release notes)"}

## Open Feature Requests
${issuesText}

## Recently Completed Work
${prsText}

## Project Context
${vaultContext || "(No additional context)"}

---

Based on this information, propose 3-5 high-value features for the next release. For each proposal, provide:

1. **Title** - Feature name
2. **Problem** - What problem does it solve?
3. **Effort** - Estimate (S=<1 day, M=1-3 days, L=1+ week)
4. **Value** - Impact (L=High, M=Medium, H=Low)
5. **Rationale** - Why prioritize this?

Format as a numbered list. Example:

1. **Feature Name**
   - Problem: What users are asking for
   - Effort: M
   - Value: L
   - Rationale: Links to issues, user feedback, or strategic alignment

Generate proposals now:`;

    try {
      const response = await this._callClaudeAPI(prompt);

      // Extract text content from response
      const content = response.content?.[0]?.text || "";

      // Parse proposals from response
      const proposals = this._parseProposals(content);

      return proposals;
    } catch (error) {
      throw new Error(`Failed to generate proposals: ${error.message}`);
    }
  }

  /**
   * Parse Claude's response into structured proposals
   * @private
   */
  _parseProposals(text) {
    const proposals = [];

    // Split by numbered items (1., 2., 3., etc.)
    const items = text.split(/\n(?=\d+\.\s+\*\*)/);

    items.forEach((item) => {
      const titleMatch = item.match(/\*\*(.+?)\*\*/);
      const effortMatch = item.match(/Effort:\s*(\w+)/i);
      const valueMatch = item.match(/Value:\s*(\w+)/i);
      const problemMatch = item.match(/Problem:\s*(.+?)(?:\n|$)/i);
      const rationaleMatch = item.match(/Rationale:\s*(.+?)(?:\n\d+\.|$)/is);

      if (titleMatch) {
        proposals.push({
          title: titleMatch[1].trim(),
          problem: problemMatch ? problemMatch[1].trim() : "To be determined",
          effort: effortMatch ? effortMatch[1].toUpperCase() : "M",
          value: valueMatch ? valueMatch[1].toUpperCase() : "M",
          rationale: rationaleMatch ? rationaleMatch[1].trim() : "",
        });
      }
    });

    return proposals.length > 0
      ? proposals
      : this._generateFallbackProposals();
  }

  /**
   * Generate fallback proposals if parsing fails
   * @private
   */
  _generateFallbackProposals() {
    return [
      {
        title: "Improve Documentation",
        problem: "Users struggle to understand project features",
        effort: "M",
        value: "M",
        rationale: "Better docs reduce support burden and improve adoption",
      },
      {
        title: "Add API Rate Limiting",
        problem: "No protection against abuse",
        effort: "S",
        value: "M",
        rationale: "Prevents API misuse and improves stability",
      },
      {
        title: "Implement Caching Layer",
        problem: "Performance degradation under load",
        effort: "L",
        value: "H",
        rationale: "Significantly improves response times",
      },
    ];
  }
}

module.exports = ProposalEngine;
