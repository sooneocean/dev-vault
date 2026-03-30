# Claude Code Libraries

This directory contains reusable modules for the product iteration automation workflow.

## Modules

### Proposal Engine (`proposal-engine.js`)

Generates feature proposals for the next product version using Claude API.

**Function:**
```javascript
async generateProposals(githubContext, vaultContext, options = {})
```

**Inputs:**
- `githubContext` (required)
  - `lastRelease` (string): Description of the last release
  - `openIssues` (array): Open issues with `title` and `labels` fields
  - `closedPRs` (array): Recently closed PRs with `title` and `labels`

- `vaultContext` (optional)
  - `projectGoals` (string): Project goals from vault
  - `learnings` (string): Research/architecture learnings

- `options` (optional)
  - `debug` (boolean): Enable debug logging

**Output:**
Returns an array of proposals, each with:
```javascript
{
  title: string,           // Feature title
  problem: string,         // 1-2 sentence problem statement
  effort: 'S'|'M'|'L',    // S < 1 day, M 1-3 days, L 1+ week
  value: 'L'|'M'|'H',     // L = Low, M = Medium, H = High
  priority: number,        // 1 = highest, ranked by value/effort ratio
  rationale: string,       // Justification, may contain issue references
  relatedIssues: string[]  // Array of issue numbers (e.g., ["42", "51"])
}
```

**Example Usage:**
```javascript
const { generateProposals } = require('./.claude/lib/proposal-engine');

const proposals = await generateProposals(
  {
    lastRelease: 'v1.0.0 - Initial release',
    openIssues: [
      { title: 'Dark mode support', labels: ['feature'] },
      { title: 'Export to PDF', labels: ['feature'] }
    ],
    closedPRs: [
      { title: 'feat: Authentication', labels: ['feature'] }
    ]
  },
  {
    projectGoals: 'Build collaborative editing platform',
    learnings: 'User research shows dark mode is #1 request'
  },
  { debug: true }
);

// Output: 3-5 ranked proposals
proposals.forEach(p => {
  console.log(`${p.title} (Effort: ${p.effort}, Value: ${p.value})`);
});
```

## Testing

### Unit Tests
Run unit tests (mocked Claude API):
```bash
npm run test:proposal
```

Tests cover:
- Happy path: Generate 5 proposals with effort/value estimates
- Proposal ranking by priority
- Edge cases: No open issues, first release, missing vault context
- Effort/value estimate normalization
- Issue reference extraction

### Integration Tests
Run integration tests with real Claude API:
```bash
ANTHROPIC_API_KEY=sk-... npm run test:proposal-integration
```

Integration tests validate:
- Real Claude API integration
- Realistic proposal generation from actual GitHub/vault context
- Effort estimate specifications (S/M/L)
- Value estimate justification

## Implementation Notes

### Claude Model
Uses `claude-opus-4-1` model for feature proposal generation. Can be customized in `proposal-engine.js`.

### Prompt Engineering
The context prompt is structured in three sections:
1. **Last Release** - What shipped, what was fixed
2. **Open Issues** - Feature requests and improvements
3. **Project Context** - Goals and learnings from vault

Claude is instructed to propose 3-5 features ranked by value/effort ratio.

### Response Parsing
Claude returns structured text with the format:
```
**Proposal N: [Title]**
- Problem: [problem statement]
- Effort: [S|M|L]
- Value: [L|M|H]
- Priority: [number]
- Rationale: [explanation]
```

The parser extracts this structure and handles:
- Case-insensitive effort/value parsing
- Missing fields (applies sensible defaults)
- Issue reference extraction from rationale (e.g., #123)

### Error Handling
- Throws if `githubContext` is missing
- Returns empty array if Claude response cannot be parsed
- Gracefully handles missing `vaultContext` (optional)

## Integration with `/iterate` Command

This module is called by the `/iterate propose` subcommand:
1. Command fetches GitHub context (last release, open issues, closed PRs)
2. Command searches vault for project learnings
3. Command calls `generateProposals()` with both contexts
4. Command renders proposals to user in table/list format
5. User selects features to confirm via `/iterate confirm`

## Rate Limiting & API Costs

- Claude API rate limits are auto-handled by Anthropic SDK
- Typical proposal generation uses ~200-500 tokens of input, ~300-600 tokens of output
- Cost: ~$0.002 per proposal generation call

## Future Enhancements

1. **Caching** - Cache proposals for repeated calls
2. **Custom Models** - Allow overriding model via options
3. **Effort Distribution** - Return histogram of effort/value
4. **Explanation Generation** - Deeper rationale explanations
5. **Impact Ranking** - Estimated impact on engagement/revenue
