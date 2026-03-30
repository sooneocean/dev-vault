#!/usr/bin/env node

/**
 * /iterate Command - Product Iteration Automation
 *
 * Main CLI orchestrator for the iteration workflow:
 *   /iterate propose   - Analyze and propose next features
 *   /iterate confirm   - Review proposals and create issues
 *   /iterate release   - Generate changelog and create GitHub release
 *
 * Usage:
 *   node iterate-cli.js propose [--output-json]
 *   node iterate-cli.js confirm [--selections "1,2,3"]
 *   node iterate-cli.js release [--version X.Y.Z]
 */

const fs = require("fs");
const path = require("path");
const { execSync } = require("child_process");

// Import supporting modules
const GitHubAPI = require("./github-api");
const { generateProposals } = require("./proposal-engine");
const ChangelogGenerator = require("./changelog-generator");
const VersionSuggester = require("./version-suggester");
const VaultIterationSystem = require("./vault-iteration");

// Instantiate classes
const changelogGen = new ChangelogGenerator();
const versionSuggester = new VersionSuggester();

/**
 * Main CLI entry point
 */
async function main() {
  const subcommand = process.argv[2];
  const args = process.argv.slice(3);

  // Validate environment
  const env = validateEnvironment();
  if (!env.success) {
    console.error(`❌ ${env.error}`);
    process.exit(1);
  }

  try {
    switch (subcommand) {
      case "propose":
        await handlePropose(env, args);
        break;
      case "confirm":
        await handleConfirm(env, args);
        break;
      case "release":
        await handleRelease(env, args);
        break;
      case "--help":
      case "-h":
      case "help":
        showHelp();
        break;
      default:
        console.error(`Unknown subcommand: ${subcommand}`);
        console.error(
          "Use `/iterate propose|confirm|release` or `/iterate help`",
        );
        process.exit(1);
    }
  } catch (error) {
    console.error(`❌ Error: ${error.message}`);
    if (process.env.DEBUG) {
      console.error(error.stack);
    }
    process.exit(1);
  }
}

/**
 * Validate environment: GitHub token, API keys, vault setup
 */
function validateEnvironment() {
  const errors = [];

  // Check GitHub token
  if (!process.env.GITHUB_TOKEN) {
    errors.push(
      'GITHUB_TOKEN env var not set. Set it with: export GITHUB_TOKEN="ghp_..."',
    );
  }

  // Check Claude API key (needed for propose)
  if (!process.env.ANTHROPIC_API_KEY && process.argv[2] === "propose") {
    errors.push(
      'ANTHROPIC_API_KEY env var not set. Set it with: export ANTHROPIC_API_KEY="sk-ant-..."',
    );
  }

  // Check if in a git repo
  try {
    execSync("git rev-parse --git-dir", { stdio: "ignore" });
  } catch {
    errors.push("Not in a git repository. Initialize with: git init");
  }

  // Infer repo info from git remote
  let owner = null;
  let repo = null;
  try {
    const remoteUrl = execSync("git config --get remote.origin.url", {
      encoding: "utf-8",
    }).trim();
    const match = remoteUrl.match(
      /github\.com[:/]([^/]+)\/([^/]+?)(?:\.git)?$/,
    );
    if (match) {
      owner = match[1];
      repo = match[2];
    }
  } catch {
    errors.push(
      "Could not detect GitHub repo from git remote. Ensure remote.origin is set to a GitHub URL.",
    );
  }

  // Check vault root (look for vault index)
  let vaultRoot = null;
  try {
    vaultRoot = path.resolve(process.cwd(), ".");
    if (!fs.existsSync(path.join(vaultRoot, ".obsidian"))) {
      // Fallback: assume vault is in current dir
      vaultRoot = process.cwd();
    }
  } catch {
    errors.push(
      "Could not detect Obsidian vault root. Ensure .obsidian directory exists.",
    );
  }

  // Infer project note path (look for projects/*-version.md or similar)
  let projectNotePath = null;
  if (vaultRoot) {
    const projectsDir = path.join(vaultRoot, "projects");
    if (fs.existsSync(projectsDir)) {
      const files = fs
        .readdirSync(projectsDir)
        .filter((f) => f.includes("version") && f.endsWith(".md"));
      if (files.length > 0) {
        projectNotePath = path.join("projects", files[0]);
      }
    }
  }

  if (errors.length > 0) {
    return {
      success: false,
      error: errors[0],
      details: errors.join("\n  "),
    };
  }

  return {
    success: true,
    github: { owner, repo },
    vault: { root: vaultRoot, projectNotePath },
    apiKey: process.env.ANTHROPIC_API_KEY,
  };
}

/**
 * Subcommand: /iterate propose
 * Analyze and generate feature proposals
 */
async function handlePropose(env, args) {
  console.log("\n📊 Analyzing last release and generating proposals...\n");

  const { owner, repo } = env.github;
  const { root: vaultRoot, projectNotePath } = env.vault;

  // Initialize APIs
  const github = new GitHubAPI({ owner, repo });
  const vault = new VaultIterationSystem(
    vaultRoot,
    projectNotePath || "projects/product-version.md",
  );

  // 1. Read vault: current version, last release date
  let projectData = {
    version: "0.1.0",
    lastReleaseDate: new Date().toISOString().split("T")[0],
  };
  try {
    projectData = vault.readProjectNote();
  } catch {
    console.log(
      "⚠️  Warning: Could not read project version from vault. Using defaults.",
    );
  }

  // 2. Get GitHub context
  console.log("⏳ Fetching GitHub context...");
  const lastRelease = await github.getLastRelease();
  const lastReleaseDate = lastRelease
    ? new Date(lastRelease.published_at).toISOString().split("T")[0]
    : projectData.lastReleaseDate;

  const openIssues = await github.getOpenIssuesByLabel("feature-request", 50);
  const closedPRs = await github.getClosedPRsSince(lastReleaseDate, 100);

  // 3. Get vault learnings
  let vaultContext = {
    projectGoals:
      "Analyze GitHub issues and recent PRs to generate feature proposals.",
    learnings: "Based on current project state.",
  };

  // 4. Generate proposals
  console.log("🤖 Calling Claude API to generate proposals...");
  const githubContext = {
    lastRelease: lastRelease
      ? `${lastRelease.tag_name} released ${lastRelease.published_at}\n\n${lastRelease.body || "No release notes"}`
      : "No previous release",
    openIssues: openIssues.map((issue) => ({
      title: issue.title,
      labels: issue.labels.map((l) => l.name),
    })),
    closedPRs: closedPRs.map((pr) => ({
      title: pr.title,
      labels: pr.labels.map((l) => l.name),
    })),
  };

  const proposals = await generateProposals(githubContext, vaultContext);

  // 5. Create iteration note in vault
  const iterationDate = new Date().toISOString().split("T")[0];
  const iterationNotePath = path.join(
    vaultRoot,
    "iterations",
    `${iterationDate}-v${projectData.version}-iteration.md`,
  );

  // Ensure iterations directory exists
  const iterationsDir = path.dirname(iterationNotePath);
  if (!fs.existsSync(iterationsDir)) {
    fs.mkdirSync(iterationsDir, { recursive: true });
  }

  // Create iteration note with proposals
  const iterationContent = createIterationNote(
    projectData.version,
    iterationDate,
    proposals,
    githubContext,
  );

  fs.writeFileSync(iterationNotePath, iterationContent);
  console.log(`\n✅ Iteration note created: ${iterationNotePath}`);

  // 6. Display proposals
  console.log("\n📋 Proposed Features for Next Version:\n");
  console.log(
    "Rank │ Title                        │ Problem               │ Effort │ Value │ Priority",
  );
  console.log(
    "─────┼──────────────────────────────┼───────────────────────┼────────┼───────┼─────────",
  );

  proposals.forEach((p, i) => {
    const title = p.title.substring(0, 28).padEnd(28);
    const problem = p.problem.substring(0, 21).padEnd(21);
    console.log(
      `  ${i + 1}  │ ${title} │ ${problem} │   ${p.effort}    │   ${p.value}   │    ${p.priority}`,
    );
  });

  console.log("\n💡 Details:\n");
  proposals.forEach((p, i) => {
    console.log(`${i + 1}. ${p.title}`);
    console.log(`   Problem: ${p.problem}`);
    console.log(
      `   Effort: ${p.effort} │ Value: ${p.value} │ Priority: ${p.priority}`,
    );
    console.log(`   Rationale: ${p.rationale}`);
    if (p.relatedIssues.length > 0) {
      console.log(
        `   Related Issues: ${p.relatedIssues.map((id) => "#" + id).join(", ")}`,
      );
    }
    console.log();
  });

  // Save proposals for next step
  const proposalsFile = path.join(
    iterationsDir,
    `${iterationDate}-proposals.json`,
  );
  fs.writeFileSync(proposalsFile, JSON.stringify(proposals, null, 2));

  console.log(
    `👉 Run \`/iterate confirm\` to select features and create issues`,
  );
  console.log(`📝 Iteration note: ${iterationNotePath}`);
}

/**
 * Subcommand: /iterate confirm
 * Review proposals and create GitHub issues
 */
async function handleConfirm(env, args) {
  console.log("\n✅ Confirming feature selections and creating issues...\n");

  const { owner, repo } = env.github;
  const { root: vaultRoot, projectNotePath } = env.vault;

  // Initialize APIs
  const github = new GitHubAPI({ owner, repo });
  const vault = new VaultIterationSystem(
    vaultRoot,
    projectNotePath || "projects/product-version.md",
  );

  // Load most recent proposals
  const iterationsDir = path.join(vaultRoot, "iterations");
  if (!fs.existsSync(iterationsDir)) {
    console.error("❌ No iterations found. Run `/iterate propose` first.");
    process.exit(1);
  }

  const proposalFiles = fs
    .readdirSync(iterationsDir)
    .filter((f) => f.endsWith("-proposals.json"))
    .sort()
    .reverse();

  if (proposalFiles.length === 0) {
    console.error("❌ No proposals found. Run `/iterate propose` first.");
    process.exit(1);
  }

  const latestProposalsFile = path.join(iterationsDir, proposalFiles[0]);
  const proposals = JSON.parse(fs.readFileSync(latestProposalsFile, "utf-8"));

  // Get selections from args or prompt user
  let selectedIndices = [];
  const selectionsArg = args.find((a) => a.startsWith("--selections="));
  if (selectionsArg) {
    selectedIndices = selectionsArg
      .split("=")[1]
      .split(",")
      .map((s) => parseInt(s) - 1);
  } else {
    console.log("📋 Proposals from last analysis:\n");
    proposals.forEach((p, i) => {
      console.log(
        `${i + 1}. ${p.title} (Effort: ${p.effort}, Value: ${p.value})`,
      );
    });
    console.log(
      '\n👉 Specify selections with: /iterate confirm --selections="1,2,3"',
    );
    console.log("   Or manually select and re-run.\n");
    selectedIndices = [0, 1]; // Default: select first two for demo
  }

  // Validate selections
  selectedIndices = selectedIndices.filter(
    (i) => i >= 0 && i < proposals.length,
  );
  const selectedProposals = selectedIndices.map((i) => proposals[i]);

  console.log(
    `\n📝 Creating issues for ${selectedProposals.length} selected features...\n`,
  );

  // Get or create next version milestone
  const projectData = vault.readProjectNote();
  const nextVersion = incrementVersion(projectData.version);
  const milestoneName = `v${nextVersion}`;

  let milestone = await github.getMilestoneByName(milestoneName);
  if (!milestone) {
    milestone = await github.createMilestone(
      milestoneName,
      `Version ${nextVersion} release`,
    );
    console.log(`✓ Created milestone: ${milestoneName}`);
  }

  // Create issues
  const createdIssues = [];
  for (const proposal of selectedProposals) {
    const issue = await github.createIssue(
      proposal.title,
      `**Problem:** ${proposal.problem}\n\n**Effort:** ${proposal.effort}\n**Value:** ${proposal.value}\n\n**Rationale:** ${proposal.rationale}`,
      ["feature"],
      milestone.number,
    );
    createdIssues.push(issue);
    console.log(`✓ Issue #${issue.number}: ${proposal.title}`);
  }

  // Update iteration note with selections
  const iterationFile = fs
    .readdirSync(iterationsDir)
    .filter((f) => f.endsWith("-iteration.md"))
    .sort()
    .reverse()[0];

  if (iterationFile) {
    const iterationPath = path.join(iterationsDir, iterationFile);
    let content = fs.readFileSync(iterationPath, "utf-8");

    // Append selected features section
    const selectedSection = `## Features Selected

Confirmed by developer on ${new Date().toISOString().split("T")[0]}:

${createdIssues.map((issue) => `- [#${issue.number}](${issue.html_url}): ${issue.title}`).join("\n")}
`;

    if (content.includes("## Features Selected")) {
      content = content.replace("## Features Selected", selectedSection.trim());
    } else {
      content += "\n\n" + selectedSection;
    }

    fs.writeFileSync(iterationPath, content);
  }

  console.log(
    `\n✅ ${createdIssues.length} issues created and assigned to milestone: ${milestoneName}`,
  );
  console.log(
    `👉 Merge your features, then run \`/iterate release\` to publish\n`,
  );
}

/**
 * Subcommand: /iterate release
 * Generate changelog and create GitHub release
 */
async function handleRelease(env, args) {
  console.log("\n🚀 Preparing release...\n");

  const { owner, repo } = env.github;
  const { root: vaultRoot, projectNotePath } = env.vault;

  // Initialize APIs
  const github = new GitHubAPI({ owner, repo });
  const vault = new VaultIterationSystem(
    vaultRoot,
    projectNotePath || "projects/product-version.md",
  );

  // Read current version
  let projectData = {
    version: "1.0.0",
    lastReleaseDate: new Date().toISOString().split("T")[0],
  };
  try {
    projectData = vault.readProjectNote();
  } catch {
    console.log("⚠️  Warning: Could not read project version. Using defaults.");
  }

  // Get last release tag
  const lastRelease = await github.getLastRelease();
  const lastTag = lastRelease ? lastRelease.tag_name : null;

  // 1. Fetch merged PRs since last release
  console.log("⏳ Fetching merged PRs since last release...");
  const mergedPRs = await github.getClosedPRsSince(
    projectData.lastReleaseDate,
    200,
  );

  if (mergedPRs.length === 0) {
    console.log("⚠️  No merged PRs since last release. Nothing to release.");
    process.exit(0);
  }

  // 2. Generate changelog
  console.log(
    `📝 Generating changelog from ${mergedPRs.length} merged PRs...\n`,
  );
  const changelog = changelogGen.generateChangelog({
    prs: mergedPRs,
    version: projectData.version,
  });

  // 3. Suggest version
  const suggestedVersion = versionSuggester.suggestVersion(
    projectData.version,
    changelog,
  );
  console.log(`💡 Suggested version: ${suggestedVersion.suggested}`);
  console.log(`   Reason: ${suggestedVersion.reason}\n`);

  // Get version from args or use suggested
  let releaseVersion = suggestedVersion.suggested;
  const versionArg = args.find((a) => a.startsWith("--version="));
  if (versionArg) {
    releaseVersion = versionArg.split("=")[1];
  } else {
    console.log(
      '👉 To use a custom version, run: /iterate release --version="X.Y.Z"',
    );
    console.log(`   Using suggested: ${releaseVersion}\n`);
  }

  // 4. Create GitHub release
  console.log(`📦 Creating GitHub release v${releaseVersion}...\n`);
  const releaseBody = `${changelog}\n\n---\n\n*Released on ${new Date().toISOString().split("T")[0]}*`;

  const release = await github.createRelease(
    `v${releaseVersion}`,
    releaseBody,
    `Release v${releaseVersion}`,
  );

  console.log(`✅ Release created: ${release.html_url}`);

  // 5. Update vault
  console.log("📚 Updating vault...");
  const releaseDate = new Date().toISOString().split("T")[0];
  vault.updateProjectNote({
    version: releaseVersion,
    releaseDate: releaseDate,
    releaseUrl: release.html_url,
    features: mergedPRs.slice(0, 5).map((p) => p.title),
  });

  // Append to iteration history
  const iterationsDir = path.join(vaultRoot, "iterations");
  const iterationFile = fs
    .readdirSync(iterationsDir)
    .filter((f) => f.endsWith("-iteration.md"))
    .sort()
    .reverse()[0];

  if (iterationFile) {
    const iterationPath = path.join(iterationsDir, iterationFile);
    let content = fs.readFileSync(iterationPath, "utf-8");

    const releaseSection = `## Release Record

**Version:** ${releaseVersion}
**Released:** ${new Date().toISOString().split("T")[0]}
**GitHub:** [${release.html_url}](${release.html_url})

### Changelog

${changelog}
`;

    if (content.includes("## Release Record")) {
      content = content.replace("## Release Record", releaseSection.trim());
    } else {
      content += "\n\n" + releaseSection;
    }

    fs.writeFileSync(iterationPath, content);
  }

  console.log(`✅ Vault updated with new version: ${releaseVersion}`);
  console.log(`\n🎉 Release complete!\n`);
  console.log(`📖 Release URL: ${release.html_url}`);
  console.log(`📝 Iteration notes: iterations/${iterationFile}\n`);
}

/**
 * Helper: Create iteration note content
 */
function createIterationNote(version, date, proposals, githubContext) {
  const content = `---
title: "Product Iteration ${date}"
type: project
subtype: iteration-log
status: active
maturity: growing
domain: project-specific
version: "${version}"
iteration_date: "${date}"
proposals_count: ${proposals.length}
selected_count: 0
created: "${date}"
updated: "${date}"
---

# Iteration Log — ${date}

## Proposals Generated

Date: ${date}
Version: ${version}
Total Proposals: ${proposals.length}

| # | Title | Problem | Effort | Value | Priority |
|---|-------|---------|--------|-------|----------|
${proposals.map((p, i) => `| ${i + 1} | ${p.title} | ${p.problem} | ${p.effort} | ${p.value} | ${p.priority} |`).join("\n")}

## Features Selected

*To be filled in by /iterate confirm*

## Release Record

*To be filled in by /iterate release*

## Iteration Notes

- Proposals generated: ${new Date().toLocaleString()}
- GitHub context analyzed: ${proposals.length} proposals from open issues and recent PRs
`;

  return content;
}

/**
 * Helper: Increment semantic version
 */
function incrementVersion(version) {
  const parts = version.split(".");
  if (parts.length < 3) return "1.0.0";
  const patch = parseInt(parts[2]) + 1;
  return `${parts[0]}.${parts[1]}.${patch}`;
}

/**
 * Show help message
 */
function showHelp() {
  console.log(`
/iterate — Product Iteration Automation

USAGE:
  /iterate propose                    # Analyze and propose next features
  /iterate confirm --selections="1,2" # Select features and create issues
  /iterate release --version="1.2.0"  # Generate changelog and release

SETUP:
  export GITHUB_TOKEN="ghp_..."
  export ANTHROPIC_API_KEY="sk-ant-..."

WORKFLOW:
  1. /iterate propose        # Review proposals
  2. /iterate confirm        # Select and create issues
  3. (Development phase)
  4. /iterate release        # Generate changelog and create release

For more info: https://github.com/sooneocean/dev-vault/blob/master/docs/plans/2026-03-30-001-feat-product-iteration-automation-plan.md
`);
}

// Run main
if (require.main === module) {
  main().catch((error) => {
    console.error(`❌ Unexpected error: ${error.message}`);
    process.exit(1);
  });
}

module.exports = { handlePropose, handleConfirm, handleRelease };
