/**
 * Example usage of the GitHub API wrapper module
 * Shows how the module will be integrated into the /iterate command
 *
 * This file is for reference and documentation only.
 * The actual /iterate command is in .claude/commands/iterate.md
 */

const github = require("./github-api");

/**
 * Example 1: Propose features for next release
 * This will be called by `/iterate propose`
 */
async function proposeFeatures(owner, repo) {
  try {
    console.log("📋 Analyzing repository for feature proposals...\n");

    // Get last release
    const lastRelease = await github.getLastRelease(owner, repo);
    if (!lastRelease) {
      console.log(
        "ℹ️  No previous release found. This will be the first release.",
      );
      console.log("   Proposing features based on open issues.\n");
    } else {
      console.log(`✓ Last release: ${lastRelease.tag} (${lastRelease.date})`);
    }

    // Get open feature requests
    const features = await github.getOpenIssuesByLabel(
      owner,
      repo,
      "type: feature",
    );
    console.log(`✓ Found ${features.length} open feature requests\n`);

    // Get completed work (for context)
    const sinceDate = lastRelease
      ? new Date(lastRelease.date)
      : new Date("2000-01-01");
    const completedPRs = await github.getClosedPRsSince(owner, repo, sinceDate);
    console.log(
      `✓ Found ${completedPRs.length} completed PRs since last release\n`,
    );

    // Output for AI proposal generation
    return {
      lastRelease,
      openIssues: features,
      completedWork: completedPRs,
      summary: `Repository has ${features.length} open features and ${completedPRs.length} recent completions.`,
    };
  } catch (error) {
    console.error("❌ Error during feature proposal:", error.message);
    throw error;
  }
}

/**
 * Example 2: Create issues for confirmed features
 * This will be called by `/iterate confirm`
 */
async function confirmFeatures(owner, repo, selectedFeatures, milestoneNumber) {
  try {
    console.log(`📝 Creating ${selectedFeatures.length} GitHub issues...\n`);

    const createdIssues = [];

    for (const feature of selectedFeatures) {
      console.log(`Creating issue: "${feature.title}"`);

      const issue = await github.createIssue(
        owner,
        repo,
        feature.title,
        feature.description || feature.body,
        ["type: feature", ...(feature.labels || [])],
        milestoneNumber,
      );

      console.log(`  ✓ Created issue #${issue.number}`);
      console.log(`    ${issue.url}\n`);

      createdIssues.push(issue);
    }

    console.log(
      `✅ Created ${createdIssues.length} issues in milestone ${milestoneNumber}`,
    );
    return createdIssues;
  } catch (error) {
    console.error("❌ Error during feature confirmation:", error.message);
    throw error;
  }
}

/**
 * Example 3: Check release readiness
 * This will be called by `/iterate release` before creating release
 */
async function checkReleaseReadiness(owner, repo, milestoneNumber) {
  try {
    console.log(
      `🔍 Checking release readiness for milestone #${milestoneNumber}...\n`,
    );

    const status = await github.getReleaseReadiness(
      owner,
      repo,
      milestoneNumber,
    );

    console.log(`Status:`);
    console.log(`  ✓ Merged PRs: ${status.merged_count}/${status.total_count}`);
    console.log(`  ⏳ Open PRs: ${status.open_count}`);

    if (!status.ready) {
      console.log(
        `\n⚠️  Not ready for release! ${status.open_count} PR(s) still open:`,
      );
      status.prs
        .filter((pr) => pr.state === "open")
        .forEach((pr) => {
          console.log(`  - #${pr.number}: ${pr.title}`);
        });
      return null;
    }

    console.log(`\n✅ Ready for release! All PRs merged.\n`);
    return status;
  } catch (error) {
    console.error("❌ Error checking release readiness:", error.message);
    throw error;
  }
}

/**
 * Example 4: Create a release with changelog
 * This will be called by `/iterate release` after approval
 */
async function releaseVersion(owner, repo, version, changelog) {
  try {
    console.log(`🚀 Creating release ${version}...\n`);

    const release = await github.createRelease(
      owner,
      repo,
      version,
      changelog,
      `Version ${version}`,
    );

    console.log(`✅ Release created!`);
    console.log(`   Tag: ${release.tag}`);
    console.log(`   URL: ${release.url}`);
    console.log(`   Published: ${release.published_at}\n`);

    return release;
  } catch (error) {
    console.error("❌ Error creating release:", error.message);
    throw error;
  }
}

/**
 * Example 5: Get available milestones
 * This will be called to let user select next version milestone
 */
async function listMilestones(owner, repo) {
  try {
    console.log(`📊 Available milestones:\n`);

    const milestones = await github.getMilestones(owner, repo, "open");

    if (milestones.length === 0) {
      console.log("No open milestones found.\n");
      return [];
    }

    milestones.forEach((m) => {
      const total = m.open_issues + m.closed_issues;
      const progress = m.closed_issues;
      console.log(`  [${m.number}] ${m.title}`);
      console.log(`      Progress: ${progress}/${total} issues done`);
      if (m.due_on) {
        console.log(`      Due: ${m.due_on}`);
      }
      console.log();
    });

    return milestones;
  } catch (error) {
    console.error("❌ Error listing milestones:", error.message);
    throw error;
  }
}

/**
 * Example 6: Full workflow (for testing)
 * Demonstrates end-to-end flow
 */
async function exampleFullWorkflow() {
  // Set up
  process.env.GITHUB_TOKEN = "your_token_here";
  const owner = "your-username";
  const repo = "your-repo";

  try {
    // Step 1: Propose
    console.log("=== STEP 1: PROPOSE FEATURES ===\n");
    const proposals = await proposeFeatures(owner, repo);
    console.log(`Summary: ${proposals.summary}\n`);

    // Step 2: User reviews and confirms features
    console.log("=== STEP 2: CONFIRM FEATURES ===");
    console.log("(User would select features here)\n");
    const selectedFeatures = [
      { title: "Feature 1", description: "Description of feature 1" },
    ];
    const milestone = 5;
    const issues = await confirmFeatures(
      owner,
      repo,
      selectedFeatures,
      milestone,
    );

    // Step 3: Check readiness
    console.log("=== STEP 3: CHECK READINESS ===\n");
    const readiness = await checkReleaseReadiness(owner, repo, milestone);
    if (!readiness) {
      console.log("Cannot proceed with release until all PRs are merged.");
      return;
    }

    // Step 4: Create release
    console.log("=== STEP 4: CREATE RELEASE ===\n");
    const changelog = `## Features\n- Feature 1 (#${issues[0].number})\n`;
    const release = await releaseVersion(owner, repo, "v1.1.0", changelog);

    console.log("=== WORKFLOW COMPLETE ===");
  } catch (error) {
    console.error("Workflow failed:", error.message);
  }
}

// Export examples for use in other modules
module.exports = {
  proposeFeatures,
  confirmFeatures,
  checkReleaseReadiness,
  releaseVersion,
  listMilestones,
  exampleFullWorkflow,
};

// If run directly, show usage
if (require.main === module) {
  console.log("GitHub API Integration - Examples");
  console.log("===================================");
  console.log("");
  console.log("This file shows how the GitHub API wrapper will be used.");
  console.log("");
  console.log("Usage:");
  console.log('  const examples = require("./github-api-example.js");');
  console.log('  await examples.proposeFeatures("owner", "repo");');
  console.log("");
  console.log("Functions available:");
  console.log("  - proposeFeatures(owner, repo)");
  console.log(
    "  - confirmFeatures(owner, repo, selectedFeatures, milestoneNumber)",
  );
  console.log("  - checkReleaseReadiness(owner, repo, milestoneNumber)");
  console.log("  - releaseVersion(owner, repo, version, changelog)");
  console.log("  - listMilestones(owner, repo)");
  console.log("  - exampleFullWorkflow()");
  console.log("");
}
