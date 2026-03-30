/**
 * Vault Iteration System
 *
 * Manages iteration history, version tracking, and vault note creation/updates
 * using the obsidian-agent CLI.
 */

const { execSync } = require("child_process");
const fs = require("fs");
const path = require("path");

class VaultIterationSystem {
  constructor(vaultRoot, projectNotePath) {
    this.vaultRoot = vaultRoot;
    this.projectNotePath = projectNotePath;
    this.iterationDir = path.join(vaultRoot, "iterations");
  }

  /**
   * Ensure iteration directory exists
   */
  _ensureIterationDir() {
    if (!fs.existsSync(this.iterationDir)) {
      fs.mkdirSync(this.iterationDir, { recursive: true });
    }
  }

  /**
   * Parse vault project note to extract version and last release date
   * Returns: { version: string, lastReleaseDate: string }
   */
  readProjectNote() {
    try {
      const content = fs.readFileSync(
        path.join(this.vaultRoot, this.projectNotePath),
        "utf-8",
      );

      // Extract version from frontmatter: current_version: "X.Y.Z"
      const versionMatch = content.match(/current_version:\s*"([^"]+)"/);
      const version = versionMatch ? versionMatch[1] : "0.1.0";

      // Extract last release date from frontmatter: last_release_date: "YYYY-MM-DD"
      const dateMatch = content.match(/last_release_date:\s*"([^"]+)"/);
      const lastReleaseDate = dateMatch
        ? dateMatch[1]
        : new Date().toISOString().split("T")[0];

      return { version, lastReleaseDate };
    } catch (error) {
      throw new Error(`Failed to read project note: ${error.message}`);
    }
  }

  /**
   * Create a new iteration note with the given proposals
   *
   * @param {Object} params
   * @param {string} params.version - Target version
   * @param {Date} params.date - Iteration date
   * @param {Array} params.proposals - Array of proposal objects
   * @returns {string} Path to created iteration note
   */
  createIterationNote(params) {
    const { version, date, proposals } = params;

    this._ensureIterationDir();

    const dateStr = date.toISOString().split("T")[0];
    const filename = `${dateStr}-v${version}-iteration.md`;
    const filepath = path.join(this.iterationDir, filename);

    // Generate proposals table
    const proposalsTable = proposals
      .map((p, idx) => {
        const rank = idx + 1;
        return `| ${rank} | ${p.title} | ${p.problem} | ${p.effort} | ${p.value} | ${rank} | proposal |`;
      })
      .join("\n");

    // Generate iteration note content
    const content = `---
title: "${version} — Iteration ${dateStr}"
type: project
subtype: iteration-log
tags: []
created: "${dateStr}"
updated: "${dateStr}"
status: active
maturity: growing
domain: project-specific
summary: "Iteration record for version ${version}: proposals, selections, and release metadata"
version: "${version}"
iteration_date: "${dateStr}"
proposals_count: ${proposals.length}
selected_count: 0
github_release_url: ""
github_release_date: ""
related: []
relation_map: ""
---

# ${version} — Iteration ${dateStr}

## Proposals Generated

**Date:** ${dateStr}
**Version Target:** ${version}

### Proposal Details

| # | Title | Problem | Effort | Value | Rank | Status |
|---|-------|---------|--------|-------|------|--------|
${proposalsTable}

**Total Proposals:** ${proposals.length}

## Features Selected

**Date:** (pending)
**Selected:** 0 of ${proposals.length}

### Selected Features

(No features selected yet)

## Release Record

**Release Date:** (pending)
**GitHub Release:** (pending)

### Changelog

(pending)

### Version Jump

- **Previous Version:** (pending)
- **Released Version:** (pending)
- **Version Bump Reason:** (pending)

## Iteration Notes

- Started: ${dateStr}
- Proposals finalized: (pending)
- Released: (pending)

## Links

- [[Dev Vault — Version Tracker|projects/dev-vault-product-version]] — Current version tracking
`;

    fs.writeFileSync(filepath, content, "utf-8");
    return filepath;
  }

  /**
   * Update project note with new version and last release date
   *
   * @param {Object} params
   * @param {string} params.version - New version string
   * @param {string} params.releaseDate - Release date (YYYY-MM-DD)
   * @param {string} params.releaseUrl - GitHub release URL
   * @param {Array} params.features - Array of released features
   */
  updateProjectNote(params) {
    const { version, releaseDate, releaseUrl, features } = params;

    const filepath = path.join(this.vaultRoot, this.projectNotePath);
    let content = fs.readFileSync(filepath, "utf-8");

    // Update current_version in frontmatter
    content = content.replace(
      /current_version:\s*"[^"]+"/,
      `current_version: "${version}"`,
    );

    // Update last_release_date in frontmatter
    content = content.replace(
      /last_release_date:\s*"[^"]+"/,
      `last_release_date: "${releaseDate}"`,
    );

    // Update "Completed Features" section
    const featuresText =
      features.length > 0
        ? features.map((f) => `  - ${f}`).join("\n")
        : "  (None yet)";

    content = content.replace(
      /## Completed Features \(Current Cycle\)\n\n(.|\n)*?(?=\n## |\n$)/,
      `## Completed Features (Current Cycle)\n\n${featuresText}`,
    );

    // Update iteration links
    const iterationLink = `- [[${version} — Iteration ${releaseDate}|iterations/${releaseDate}-v${version}-iteration]]`;
    content = content.replace(
      /### Latest Iteration\n\n- \[\[.+?\|.+?\]\]/,
      `### Latest Iteration\n\n${iterationLink}`,
    );

    fs.writeFileSync(filepath, content, "utf-8");
  }

  /**
   * Append release record to iteration note
   *
   * @param {string} iterationNotePath - Path to iteration note
   * @param {Object} releaseData - Release information
   */
  updateIterationNoteWithRelease(iterationNotePath, releaseData) {
    const {
      version,
      previousVersion,
      changelog,
      releaseDate,
      releaseUrl,
      versionBumpReason,
      selectedFeatures,
    } = releaseData;

    let content = fs.readFileSync(iterationNotePath, "utf-8");

    // Update frontmatter with release info
    content = content.replace(
      /github_release_url: ""/,
      `github_release_url: "${releaseUrl}"`,
    );
    content = content.replace(
      /github_release_date: ""/,
      `github_release_date: "${releaseDate}"`,
    );
    content = content.replace(
      /selected_count: 0/,
      `selected_count: ${selectedFeatures.length}`,
    );

    // Update "Features Selected" section
    const selectedTable = selectedFeatures
      .map(
        (f, idx) =>
          `| ${idx + 1} | ${f.title} | [${f.issueNumber}](${f.issueUrl}) | merged |`,
      )
      .join("\n");

    content = content.replace(
      /(### Selected Features\n\n)\(No features selected yet\)/,
      `$1| # | Title | GitHub Issue | Status |
|---|-------|--------------|--------|
${selectedTable}`,
    );

    // Update "Release Record" section
    content = content.replace(
      /### Changelog\n\n\(pending\)/,
      `### Changelog\n\n${changelog}`,
    );

    // Update "Version Jump" section
    content = content.replace(
      /- \*\*Previous Version:\*\* \(pending\)/,
      `- **Previous Version:** ${previousVersion}`,
    );
    content = content.replace(
      /- \*\*Released Version:\*\* \(pending\)/,
      `- **Released Version:** ${version}`,
    );
    content = content.replace(
      /- \*\*Version Bump Reason:\*\* \(pending\)/,
      `- **Version Bump Reason:** ${versionBumpReason}`,
    );

    // Update GitHub Release link
    content = content.replace(
      /\*\*GitHub Release:\*\* \(pending\)/,
      `**GitHub Release:** [${version}](${releaseUrl})`,
    );

    // Update iteration dates
    const today = new Date().toISOString().split("T")[0];
    content = content.replace(
      /- Released: \(pending\)/,
      `- Released: ${releaseDate}`,
    );

    fs.writeFileSync(iterationNotePath, content, "utf-8");
  }
}

module.exports = VaultIterationSystem;
