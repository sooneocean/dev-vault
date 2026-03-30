/**
 * Tests for Proposal Engine
 *
 * Test scenarios:
 * - Happy path: Given last release, open issues, and vault context → generate proposals
 * - Proposals ranked by priority (value/effort ratio)
 * - Proposals include problem, effort, value estimates
 * - Edge case: No open issues → proposals based on vault learnings
 * - Edge case: First release (no last release) → proposals based on vault goals
 * - Edge case: Claude API rate limit → graceful degradation
 */

const { generateProposals } = require("./proposal-engine");

// Mock Anthropic client for testing
jest.mock("@anthropic-ai/sdk", () => ({
  default: jest.fn(() => ({
    messages: {
      create: jest.fn(),
    },
  })),
}));

const Anthropic = require("@anthropic-ai/sdk").default;

describe("Proposal Engine", () => {
  let mockClient;

  beforeEach(() => {
    jest.clearAllMocks();
    // Set up mock client
    mockClient = {
      messages: {
        create: jest.fn(),
      },
    };
    Anthropic.mockImplementation(() => mockClient);
  });

  describe("Happy path: Generate proposals", () => {
    test("should generate 5 proposals with effort/value estimates", async () => {
      const mockResponse = `**Proposal 1: Add dark mode toggle**
- Problem: Users request a dark mode option for better accessibility and night usage
- Effort: M
- Value: H
- Priority: 1
- Rationale: High user demand (#42, #51), improves accessibility, medium effort

**Proposal 2: Export to PDF**
- Problem: Users need to export documents as PDF for sharing and offline access
- Effort: M
- Value: M
- Priority: 2
- Rationale: Common request from enterprise users (#38), increases product value

**Proposal 3: Real-time collaboration**
- Problem: Multiple users cannot work on the same document simultaneously
- Effort: L
- Value: H
- Priority: 3
- Rationale: Competitive advantage, aligns with product vision, but low effort

**Proposal 4: API for integrations**
- Problem: Third-party tools cannot integrate with the platform
- Effort: L
- Value: M
- Priority: 4
- Rationale: Opens ecosystem, medium effort, strategic importance

**Proposal 5: Search across all documents**
- Problem: Users can only search within current document, not across all files
- Effort: S
- Value: M
- Priority: 5
- Rationale: Improves usability, small scope, commonly requested (#22)`;

      mockClient.messages.create.mockResolvedValue({
        content: [{ type: "text", text: mockResponse }],
      });

      const githubContext = {
        lastRelease: "v1.0.0 - Initial release with basic features",
        openIssues: [
          {
            title: "Dark mode support",
            labels: ["feature", "accessibility"],
          },
          {
            title: "Export to PDF",
            labels: ["feature", "enterprise"],
          },
          {
            title: "Real-time collaboration",
            labels: ["feature", "enhancement"],
          },
        ],
        closedPRs: [
          {
            title: "Initial project setup",
            labels: ["chore"],
          },
          {
            title: "Basic authentication",
            labels: ["feature"],
          },
        ],
      };

      const vaultContext = {
        projectGoals: "Build a collaborative document editing platform",
        learnings:
          "User research shows 60% prefer dark mode, 40% need PDF export",
      };

      const proposals = await generateProposals(githubContext, vaultContext, {
        debug: false,
      });

      expect(proposals).toHaveLength(5);
      expect(proposals[0].title).toBe("Add dark mode toggle");
      expect(proposals[0].effort).toBe("M");
      expect(proposals[0].value).toBe("H");
      expect(proposals[0].priority).toBe(1);
      expect(proposals[0].problem).toContain("dark mode");
      expect(proposals[0].rationale).toBeTruthy();
    });

    test("should extract issue references from rationale", async () => {
      const mockResponse = `**Proposal 1: Dark mode toggle**
- Problem: Users request dark mode
- Effort: M
- Value: H
- Priority: 1
- Rationale: Related to issues #42, #51`;

      mockClient.messages.create.mockResolvedValue({
        content: [{ type: "text", text: mockResponse }],
      });

      const githubContext = {
        lastRelease: "v1.0.0",
        openIssues: [],
        closedPRs: [],
      };

      const proposals = await generateProposals(
        githubContext,
        {},
        { debug: false },
      );

      expect(proposals[0].relatedIssues).toContain("42");
      expect(proposals[0].relatedIssues).toContain("51");
    });

    test("should rank proposals by priority", async () => {
      const mockResponse = `**Proposal 1: Feature A**
- Problem: Problem A
- Effort: M
- Value: H
- Priority: 1
- Rationale: High priority

**Proposal 2: Feature B**
- Problem: Problem B
- Effort: S
- Value: M
- Priority: 2
- Rationale: Medium priority

**Proposal 3: Feature C**
- Problem: Problem C
- Effort: L
- Value: L
- Priority: 3
- Rationale: Low priority`;

      mockClient.messages.create.mockResolvedValue({
        content: [{ type: "text", text: mockResponse }],
      });

      const proposals = await generateProposals(
        { lastRelease: "v1.0.0", openIssues: [], closedPRs: [] },
        {},
        { debug: false },
      );

      expect(proposals[0].priority).toBe(1);
      expect(proposals[1].priority).toBe(2);
      expect(proposals[2].priority).toBe(3);
    });
  });

  describe("Edge cases", () => {
    test("should generate proposals with no open issues", async () => {
      const mockResponse = `**Proposal 1: Refactor codebase**
- Problem: Code is becoming hard to maintain
- Effort: L
- Value: M
- Priority: 1
- Rationale: Technical debt from vault learnings`;

      mockClient.messages.create.mockResolvedValue({
        content: [{ type: "text", text: mockResponse }],
      });

      const githubContext = {
        lastRelease: "v1.0.0",
        openIssues: [], // No open issues
        closedPRs: [],
      };

      const vaultContext = {
        learnings: "Code refactoring needed to support 10x scale",
      };

      const proposals = await generateProposals(githubContext, vaultContext, {
        debug: false,
      });

      expect(proposals.length).toBeGreaterThan(0);
      expect(proposals[0].title).toBe("Refactor codebase");
    });

    test("should generate proposals for first release (no last release)", async () => {
      const mockResponse = `**Proposal 1: Core MVP features**
- Problem: Product needs foundational features
- Effort: L
- Value: H
- Priority: 1
- Rationale: Aligns with project vision`;

      mockClient.messages.create.mockResolvedValue({
        content: [{ type: "text", text: mockResponse }],
      });

      const githubContext = {
        lastRelease: "No previous release", // First release
        openIssues: [],
        closedPRs: [],
      };

      const vaultContext = {
        projectGoals: "Build a collaborative editing platform",
      };

      const proposals = await generateProposals(githubContext, vaultContext, {
        debug: false,
      });

      expect(proposals.length).toBeGreaterThan(0);
    });

    test("should handle missing vault context gracefully", async () => {
      const mockResponse = `**Proposal 1: Feature A**
- Problem: Problem A
- Effort: M
- Value: M
- Priority: 1
- Rationale: Important feature`;

      mockClient.messages.create.mockResolvedValue({
        content: [{ type: "text", text: mockResponse }],
      });

      const githubContext = {
        lastRelease: "v1.0.0",
        openIssues: [{ title: "Feature request", labels: [] }],
        closedPRs: [],
      };

      // No vault context provided
      const proposals = await generateProposals(githubContext, null, {
        debug: false,
      });

      expect(proposals.length).toBeGreaterThan(0);
    });

    test("should throw error if githubContext is missing", async () => {
      await expect(
        generateProposals(null, {}, { debug: false }),
      ).rejects.toThrow("githubContext is required");
    });
  });

  describe("Effort/Value validation", () => {
    test("should normalize effort estimates to S/M/L", async () => {
      const mockResponse = `**Proposal 1: Feature A**
- Problem: Problem A
- Effort: small
- Value: high
- Priority: 1
- Rationale: Important`;

      mockClient.messages.create.mockResolvedValue({
        content: [{ type: "text", text: mockResponse }],
      });

      const proposals = await generateProposals(
        { lastRelease: "v1.0.0", openIssues: [], closedPRs: [] },
        {},
        { debug: false },
      );

      // Should extract S, M, or L (case-insensitive)
      expect(["S", "M", "L"]).toContain(proposals[0].effort);
    });

    test("should normalize value estimates to L/M/H", async () => {
      const mockResponse = `**Proposal 1: Feature A**
- Problem: Problem A
- Effort: M
- Value: medium
- Priority: 1
- Rationale: Important`;

      mockClient.messages.create.mockResolvedValue({
        content: [{ type: "text", text: mockResponse }],
      });

      const proposals = await generateProposals(
        { lastRelease: "v1.0.0", openIssues: [], closedPRs: [] },
        {},
        { debug: false },
      );

      // Should extract L, M, or H (case-insensitive)
      expect(["L", "M", "H"]).toContain(proposals[0].value);
    });

    test("should apply defaults if effort/value missing", async () => {
      const mockResponse = `**Proposal 1: Feature A**
- Problem: Problem A
- Priority: 1
- Rationale: Important`;

      mockClient.messages.create.mockResolvedValue({
        content: [{ type: "text", text: mockResponse }],
      });

      const proposals = await generateProposals(
        { lastRelease: "v1.0.0", openIssues: [], closedPRs: [] },
        {},
        { debug: false },
      );

      // Should use M as default
      expect(proposals[0].effort).toBe("M");
      expect(proposals[0].value).toBe("M");
    });
  });

  describe("Integration scenarios", () => {
    test("should be callable from /iterate propose command", async () => {
      // This test verifies the interface matches what the /iterate command expects
      const mockResponse = `**Proposal 1: Feature A**
- Problem: Problem A
- Effort: M
- Value: H
- Priority: 1
- Rationale: Important`;

      mockClient.messages.create.mockResolvedValue({
        content: [{ type: "text", text: mockResponse }],
      });

      const githubContext = {
        lastRelease: "v1.0.0",
        openIssues: [],
        closedPRs: [],
      };

      const proposals = await generateProposals(githubContext, {});

      // Verify structure matches spec from requirements
      expect(proposals).toBeInstanceOf(Array);
      expect(proposals[0]).toHaveProperty("title");
      expect(proposals[0]).toHaveProperty("problem");
      expect(proposals[0]).toHaveProperty("effort");
      expect(proposals[0]).toHaveProperty("value");
      expect(proposals[0]).toHaveProperty("priority");
      expect(proposals[0]).toHaveProperty("rationale");
    });
  });

  describe("Effort estimate interpretation", () => {
    test("should parse effort estimates correctly", async () => {
      const mockResponse = `**Proposal 1: Quick fix**
- Problem: Needs quick fix
- Effort: S
- Value: L
- Priority: 1
- Rationale: Less than 1 day

**Proposal 2: Medium feature**
- Problem: Needs medium feature
- Effort: M
- Value: M
- Priority: 2
- Rationale: 1-3 days

**Proposal 3: Big project**
- Problem: Needs big project
- Effort: L
- Value: H
- Priority: 3
- Rationale: 1+ week`;

      mockClient.messages.create.mockResolvedValue({
        content: [{ type: "text", text: mockResponse }],
      });

      const proposals = await generateProposals(
        { lastRelease: "v1.0.0", openIssues: [], closedPRs: [] },
        {},
      );

      expect(proposals[0].effort).toBe("S"); // < 1 day
      expect(proposals[1].effort).toBe("M"); // 1-3 days
      expect(proposals[2].effort).toBe("L"); // 1+ week
    });
  });
});
