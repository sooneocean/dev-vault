/**
 * Integration tests for Proposal Engine (uses real Claude API)
 *
 * This test file can be run manually to verify the proposal engine works with Claude API:
 * ANTHROPIC_API_KEY=... npm run test:proposal-integration
 *
 * These are integration tests, not unit tests, so they require API access and will incur costs.
 */

const { generateProposals } = require("./proposal-engine");

// Skip these tests if running in CI or if ANTHROPIC_API_KEY is not set
const skipIfNoApiKey = process.env.ANTHROPIC_API_KEY ? describe : describe.skip;

skipIfNoApiKey("Proposal Engine Integration Tests", () => {
  // Increase timeout for API calls
  jest.setTimeout(30000);

  test("should generate real proposals from Claude API", async () => {
    const githubContext = {
      lastRelease:
        "v1.0.0 released 2026-03-15: Initial release with basic authentication, user dashboard, and document management",
      openIssues: [
        {
          title: "Support for dark mode",
          labels: ["feature", "accessibility"],
        },
        {
          title: "Export documents to PDF",
          labels: ["feature", "export"],
        },
        {
          title: "Real-time collaboration support",
          labels: ["feature", "enhancement"],
        },
        {
          title: "API for third-party integrations",
          labels: ["feature", "api"],
        },
        {
          title: "Search across all documents",
          labels: ["feature", "search"],
        },
      ],
      closedPRs: [
        {
          title: "feat: Add authentication system",
          labels: ["feature"],
        },
        {
          title: "feat: Build user dashboard",
          labels: ["feature"],
        },
        {
          title: "fix: Resolve document upload bug",
          labels: ["bug"],
        },
      ],
    };

    const vaultContext = {
      projectGoals: "Build a collaborative document editing platform for teams",
      learnings:
        "User research shows 60% request dark mode, 45% need PDF export. Architecture uses Node.js + PostgreSQL. Team has 3 developers. Current sprint velocity is 20 story points.",
    };

    const proposals = await generateProposals(githubContext, vaultContext, {
      debug: true,
    });

    // Verify we got proposals back
    expect(Array.isArray(proposals)).toBe(true);
    expect(proposals.length).toBeGreaterThanOrEqual(3);
    expect(proposals.length).toBeLessThanOrEqual(5);

    // Verify structure of each proposal
    proposals.forEach((proposal) => {
      expect(proposal).toHaveProperty("title");
      expect(proposal).toHaveProperty("problem");
      expect(proposal).toHaveProperty("effort");
      expect(proposal).toHaveProperty("value");
      expect(proposal).toHaveProperty("priority");
      expect(proposal).toHaveProperty("rationale");

      // Verify effort is S/M/L
      expect(["S", "M", "L"]).toContain(proposal.effort);

      // Verify value is L/M/H
      expect(["L", "M", "H"]).toContain(proposal.value);

      // Verify priority is a number
      expect(typeof proposal.priority).toBe("number");

      // Verify text fields are not empty
      expect(proposal.title).toBeTruthy();
      expect(proposal.problem).toBeTruthy();
      expect(proposal.rationale).toBeTruthy();
    });

    // Verify proposals are ranked by priority
    for (let i = 1; i < proposals.length; i++) {
      expect(proposals[i].priority).toBeGreaterThanOrEqual(
        proposals[i - 1].priority,
      );
    }

    console.log("\nGenerated proposals:");
    proposals.forEach((p) => {
      console.log(`\n#${p.priority}: ${p.title}`);
      console.log(`  Effort: ${p.effort}, Value: ${p.value}`);
      console.log(`  Problem: ${p.problem}`);
      console.log(`  Rationale: ${p.rationale}`);
      if (p.relatedIssues.length > 0) {
        console.log(
          `  Related issues: ${p.relatedIssues.map((i) => "#" + i).join(", ")}`,
        );
      }
    });
  });

  test("should handle edge case: first release with project goals only", async () => {
    const githubContext = {
      lastRelease: "No previous release", // First release
      openIssues: [], // No open issues yet
      closedPRs: [
        {
          title: "feat: Project initialization",
          labels: ["chore"],
        },
      ],
    };

    const vaultContext = {
      projectGoals:
        "Create a collaborative whiteboarding tool for remote teams with real-time sync",
      learnings: "Initial market research identifies 3 key competitor gaps",
    };

    const proposals = await generateProposals(githubContext, vaultContext, {
      debug: true,
    });

    expect(proposals.length).toBeGreaterThanOrEqual(1);

    console.log("\nFirst release proposals:");
    proposals.forEach((p) => {
      console.log(`\n#${p.priority}: ${p.title}`);
      console.log(`  Effort: ${p.effort}, Value: ${p.value}`);
    });
  });

  test("should validate effort estimates match specification", async () => {
    // S = < 1 day, M = 1-3 days, L = 1+ week
    const githubContext = {
      lastRelease: "v1.0.0",
      openIssues: [
        { title: "Quick UI fix", labels: ["bug"] },
        { title: "New feature module", labels: ["feature"] },
        { title: "Architecture refactor", labels: ["refactor"] },
      ],
      closedPRs: [],
    };

    const proposals = await generateProposals(
      githubContext,
      {},
      { debug: false },
    );

    // Each proposal should have realistic effort estimates
    proposals.forEach((p) => {
      if (p.effort === "S") {
        // Should be for small, focused tasks
        expect(p.rationale.toLowerCase()).toMatch(
          /quick|small|minor|simple|tiny|one.?pager/,
        );
      } else if (p.effort === "L") {
        // Should be for large, complex tasks
        expect(p.rationale.toLowerCase()).toMatch(
          /major|significant|complex|refactor|architecture|rewrite/i,
        );
      }
    });
  });

  test("should validate value estimates are justified", async () => {
    const githubContext = {
      lastRelease: "v1.0.0",
      openIssues: [
        {
          title: "High-demand feature from 50+ users",
          labels: ["feature"],
        },
        {
          title: "Rarely requested improvement",
          labels: ["enhancement"],
        },
      ],
      closedPRs: [],
    };

    const proposals = await generateProposals(
      githubContext,
      { learnings: "User research shows dark mode is the #1 request" },
      { debug: false },
    );

    // Value estimates should be justified in rationale
    proposals.forEach((p) => {
      if (p.value === "H") {
        // High value should have clear justification
        expect(p.rationale.length).toBeGreaterThan(20);
      }
    });
  });
});
