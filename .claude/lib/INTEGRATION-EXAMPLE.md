# Proposal Engine Integration Example

This document shows how to integrate the proposal engine with GitHub API and vault context to create the `/iterate propose` command.

## Full Integration Flow

```javascript
// In /iterate propose command implementation

const { generateProposals } = require('./.claude/lib/proposal-engine');
const {
  getLastRelease,
  getOpenIssuesByLabel,
  getClosedPRsSince,
} = require('./.claude/lib/github-api');

async function iteratePropose(owner, repo, vaultSearchResults) {
  try {
    // Step 1: Fetch GitHub context
    console.log('Fetching GitHub context...');

    const lastRelease = await getLastRelease(owner, repo);
    const lastReleaseDate = new Date(lastRelease.published_at);

    // Get open feature requests
    const openIssues = await getOpenIssuesByLabel(owner, repo, 'feature');

    // Get recently closed PRs since last release
    const closedPRs = await getClosedPRsSince(owner, repo, lastReleaseDate);

    // Step 2: Build GitHub context
    const githubContext = {
      lastRelease: `${lastRelease.tag_name} - ${lastRelease.body}`,
      openIssues: openIssues.map(issue => ({
        title: issue.title,
        labels: issue.labels
      })),
      closedPRs: closedPRs.map(pr => ({
        title: pr.title,
        labels: pr.labels
      }))
    };

    // Step 3: Build vault context from search results
    // (vaultSearchResults comes from obsidian-agent search)
    const vaultContext = {
      projectGoals: vaultSearchResults.find(r => r.type === 'goals')?.content || '',
      learnings: vaultSearchResults.find(r => r.type === 'learnings')?.content || ''
    };

    // Step 4: Generate proposals
    console.log('Generating proposals with Claude API...');
    const proposals = await generateProposals(githubContext, vaultContext, {
      debug: false
    });

    // Step 5: Render proposals to user
    console.log('\n=== Feature Proposals ===\n');
    proposals.forEach((p, i) => {
      console.log(`${i + 1}. ${p.title}`);
      console.log(`   Effort: ${p.effort} | Value: ${p.value} | Priority: ${p.priority}`);
      console.log(`   Problem: ${p.problem}`);
      console.log(`   Rationale: ${p.rationale}`);
      if (p.relatedIssues.length > 0) {
        console.log(`   Related: ${p.relatedIssues.map(n => '#' + n).join(', ')}`);
      }
      console.log();
    });

    // Step 6: Save proposals to vault iteration note
    // (this happens in the vault-iteration.js module)
    const iterationNote = {
      version: lastRelease.tag_name,
      generated_at: new Date().toISOString(),
      proposals: proposals
    };

    // Store for /iterate confirm to use
    return iterationNote;

  } catch (error) {
    console.error('Error generating proposals:', error.message);
    throw error;
  }
}
```

## Data Flow Diagram

```
GitHub API                 Vault Context              Proposal Engine
┌──────────────────┐      ┌──────────────────┐       ┌──────────────────┐
│ Last Release     │      │ Project Goals    │       │ Claude API Call  │
│ Open Issues      │─────>│ Research Notes   │──────>│ Structured Prompt│
│ Closed PRs       │      │ Learnings        │       │ Parse Response   │
└──────────────────┘      └──────────────────┘       │ Return Proposals │
                                                     └──────────────────┘
                                                              │
                                                              v
                                                     ┌──────────────────┐
                                                     │ Ranked Proposals │
                                                     │ - Title          │
                                                     │ - Problem        │
                                                     │ - Effort (S/M/L) │
                                                     │ - Value (L/M/H)  │
                                                     │ - Priority       │
                                                     │ - Rationale      │
                                                     └──────────────────┘
```

## Example Output

```
=== Feature Proposals ===

1. Add dark mode toggle
   Effort: M | Value: H | Priority: 1
   Problem: Users request a dark mode option for better accessibility and night usage
   Rationale: High user demand (#42, #51), improves accessibility, medium effort
   Related: #42, #51

2. Export to PDF
   Effort: M | Value: M | Priority: 2
   Problem: Users need to export documents as PDF for sharing and offline access
   Rationale: Common request from enterprise users (#38), increases product value
   Related: #38

3. Real-time collaboration
   Effort: L | Value: H | Priority: 3
   Problem: Multiple users cannot work on the same document simultaneously
   Rationale: Competitive advantage, aligns with product vision, but low effort

4. API for integrations
   Effort: L | Value: M | Priority: 4
   Problem: Third-party tools cannot integrate with the platform
   Rationale: Opens ecosystem, medium effort, strategic importance

5. Search across all documents
   Effort: S | Value: M | Priority: 5
   Problem: Users can only search within current document, not across all files
   Rationale: Improves usability, small scope, commonly requested (#22)
```

## Handling Edge Cases

### No Open Issues
```javascript
// If getOpenIssuesByLabel returns empty array:
const openIssues = []; // Empty

// Proposal engine uses vault learnings and project goals instead
// Claude generates proposals based on project direction and team patterns
```

### First Release
```javascript
// If no previous release:
const lastRelease = {
  tag_name: 'v1.0.0',
  body: 'Initial release'
};

githubContext.lastRelease = 'No previous release';
// Proposals focus on MVP features aligned with project goals
```

### Missing Vault Context
```javascript
// If vault search returns no results:
const vaultContext = {
  projectGoals: '',
  learnings: ''
};

// Proposal engine still works with just GitHub context
// Proposals are generated from open issues and closed PRs alone
```

## Error Handling

```javascript
try {
  const proposals = await generateProposals(githubContext, vaultContext);
} catch (error) {
  if (error.message.includes('githubContext is required')) {
    console.error('Missing GitHub context. Please check GitHub API setup.');
  } else if (error.message.includes('ANTHROPIC_API_KEY')) {
    console.error('Claude API key not found. Please set ANTHROPIC_API_KEY.');
  } else if (error.message.includes('rate limit')) {
    console.error('GitHub API rate limit reached. Please try again later.');
  } else {
    console.error('Failed to generate proposals:', error.message);
  }
}
```

## Performance Notes

- **GitHub API calls**: ~500-1000ms (fetching last release, issues, PRs)
- **Claude API call**: ~2-5 seconds (generating proposals)
- **Total time**: ~3-6 seconds for full `/iterate propose` command
- **Token usage**: ~500 input tokens, ~400 output tokens per call
- **Cost**: ~$0.002 per proposal generation

## Testing the Integration

```bash
# Run unit tests (mocked)
npm run test:proposal

# Run integration tests with real Claude API
ANTHROPIC_API_KEY=sk-... npm run test:proposal-integration

# Test with real GitHub repo
GITHUB_TOKEN=ghp_... ANTHROPIC_API_KEY=sk-... node -e "
const { generateProposals } = require('./.claude/lib/proposal-engine');
const { getLastRelease } = require('./.claude/lib/github-api');

// Your test code here
"
```

## Next Steps

After proposals are generated, the `/iterate confirm` command:
1. Displays proposals to user with checkboxes
2. User selects features to implement
3. Creates GitHub issues for each selected feature
4. Assigns issues to next-version milestone
5. Updates vault iteration note with selections

Then `/iterate release` handles:
1. Verifies all selected features are merged
2. Generates changelog from merged PRs
3. Suggests version bump (patch/minor/major)
4. Creates GitHub release with changelog
5. Updates vault with release notes
