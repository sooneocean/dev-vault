/**
 * Tests for AI Proposal Engine
 */

const ProposalEngine = require("./proposal-engine");

console.log("Running Proposal Engine tests...\n");

const tests = [
  {
    name: "throws error if no API key provided",
    fn: () => {
      delete process.env.ANTHROPIC_API_KEY;
      try {
        new ProposalEngine();
        return false;
      } catch (error) {
        return error.message.includes("API key");
      }
    },
  },
  {
    name: "initializes with API key from options",
    fn: () => {
      try {
        const engine = new ProposalEngine({
          apiKey: "test-key",
        });
        return engine.apiKey === "test-key";
      } catch (error) {
        return false;
      }
    },
  },
  {
    name: "initializes with API key from env var",
    fn: () => {
      process.env.ANTHROPIC_API_KEY = "env-key";
      try {
        const engine = new ProposalEngine();
        return engine.apiKey === "env-key";
      } catch (error) {
        return false;
      } finally {
        delete process.env.ANTHROPIC_API_KEY;
      }
    },
  },
  {
    name: "has generateProposals method",
    fn: () => {
      const engine = new ProposalEngine({
        apiKey: "test-key",
      });
      return typeof engine.generateProposals === "function";
    },
  },
  {
    name: "fallback proposals are well-formed",
    fn: () => {
      const engine = new ProposalEngine({
        apiKey: "test-key",
      });
      const proposals = engine._generateFallbackProposals();

      return (
        proposals.length > 0 &&
        proposals.every(
          (p) =>
            p.title &&
            p.problem &&
            p.effort &&
            p.value &&
            ["S", "M", "L"].includes(p.effort) &&
            ["L", "M", "H"].includes(p.value),
        )
      );
    },
  },
  {
    name: "can parse simple proposal format",
    fn: () => {
      const engine = new ProposalEngine({
        apiKey: "test-key",
      });

      const mockResponse = `
1. **Feature A**
   - Problem: Users want this
   - Effort: M
   - Value: H
   - Rationale: High demand

2. **Feature B**
   - Problem: Performance issue
   - Effort: L
   - Value: M
   - Rationale: Users complaining about speed
`;

      const proposals = engine._parseProposals(mockResponse);
      return proposals.length >= 1 && proposals[0].title === "Feature A";
    },
  },
];

let passed = 0;
let failed = 0;

tests.forEach((test) => {
  try {
    if (test.fn()) {
      console.log(`✓ ${test.name}`);
      passed++;
    } else {
      console.log(`✗ ${test.name}`);
      failed++;
    }
  } catch (error) {
    console.log(`✗ ${test.name}: ${error.message}`);
    failed++;
  }
});

console.log(`\n${passed} passed, ${failed} failed`);
process.exit(failed > 0 ? 1 : 0);

module.exports = ProposalEngine;
