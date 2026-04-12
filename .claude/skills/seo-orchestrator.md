# SEO Orchestrator Skill

> Unified conversational SEO optimization for WordPress.com sites.
> Replaces the `/site-optimizer` CLI with a natural-language `/seo` entry point.

## Triggers

- `/seo`
- "optimize SEO"
- "SEO audit"
- "fix meta tags"
- "add schema markup"
- "optimize alt text"
- "internal links"

## Workflow

When this skill is triggered, follow these steps in order:

### Step 1: Session Resume Detection

Check for existing orchestrator state:

```bash
cat seo-optimization-output/seo-orchestrator-state.json 2>/dev/null
```

If state exists and is **not stale** (< 24h old), present:
- What module was running
- Progress (e.g., "150/250 articles processed")
- Ask: **Resume**, **Abandon** (clear state, start fresh), or **Rollback**

If state is **stale** (> 24h), inform the user and offer fresh start or rollback.

If no state exists, proceed to Step 2.

### Step 2: Quick Audit

Check for cached audit results:

```bash
cat seo-optimization-output/audit-cache.json 2>/dev/null
```

If cache exists and is **fresh** (< 7 days old), use it. Otherwise, run a sample scan.

**Sample scan** — scan ~100 articles across all 4 modules to estimate site-wide coverage:

```bash
# Image ALT audit
node scripts/modules/image-alt.js --action scan --site yololab --sample 100

# Meta Tags audit
node scripts/modules/meta-tags.js --action scan --site yololab --sample 100

# Schema Markup audit
node scripts/modules/schema-markup.js --action scan --site yololab --sample 100

# Internal Links audit
node scripts/modules/internal-links.js --action scan --site yololab --sample 100
```

### Step 3: Present Findings (Consultant Mode)

Present audit results as a consultant would. Format:

```
SEO Audit Summary — yololab.net (2,728 articles)
═══════════════════════════════════════════════════

Module              Coverage    Missing/Weak    Priority
─────────────────────────────────────────────────────────
Image ALT           72%         ~760 images     Medium
Meta Tags           45%         ~1,500 articles High
Schema Markup       27%         ~2,000 articles High
Internal Links      70%         ~820 articles   Medium

Recommended action order:
1. Meta Tags — highest impact on search rankings
2. Schema Markup — enables rich snippets
3. Image ALT — improves image search visibility
4. Internal Links — strengthens site structure

What would you like to optimize? (specific module / "all" / "top priority")
```

### Step 4: User Confirmation

Before any writes, always show:

1. **Article count** — how many articles will be affected
2. **Estimated time** — based on batch:5, delay:2s rate limits
3. **Cost estimate** — for modules using Claude API (meta-tags, schema)
4. **3 sample changes** — show before/after for 3 representative articles
5. **Backup status** — confirm backups will be created

Example:
```
Meta Tags Optimization — Confirmation
═══════════════════════════════════════

Articles to process: 1,500
Estimated time: ~2.5 hours
Claude API cost: ~$2-4
Backup: seo-optimization-output/backups/meta-tags-backup-{timestamp}.json

Sample changes (3 of 1,500):

1. "旅行者的故事" → "旅行者的故事：2025最感人的旅途紀錄 | YOLO LAB"
   Meta desc: (empty) → "從東京到冰島，記錄每一段改變人生的旅程..."

2. "電影推薦清單" → "2025必看電影推薦清單：10部改變視野的佳作"
   Meta desc: (empty) → "精選10部跨越類型的年度佳作..."

3. ...

Proceed? (yes / adjust sample size / cancel)
```

### Step 5: Execute Module

Acquire global lock, then execute the chosen module:

```bash
# Acquire lock (handled by the module scripts)
# Execute module
node scripts/modules/{module-name}.js --action run --site yololab [options]
```

**Module execution commands:**

| Module | Command |
|--------|---------|
| Image ALT | `node scripts/modules/image-alt.js --action run --site yololab` |
| Meta Tags | `node scripts/modules/meta-tags.js --action run --site yololab` |
| Schema Markup | `node scripts/modules/schema-markup.js --action run --site yololab` |
| Internal Links | `node scripts/modules/internal-links.js --action run --site yololab` |

**Options:** `--sample N`, `--dry-run`, `--resume`, `--force`

During execution, the module writes progress to `seo-orchestrator-state.json` for resume support.

### Step 6: Report Results

After module completion, present a structured summary:

```
Meta Tags Optimization — Complete
═══════════════════════════════════

Results:
  Updated:  1,423 articles
  Skipped:    52 (already optimized)
  Failed:     25 (see details below)
  Duration:   2h 15m

Backup saved: seo-optimization-output/backups/meta-tags-backup-20260412.json

Failed articles (top 5):
  - Post #12345: API timeout
  - Post #12678: Content too short for meta generation
  ...

Next steps:
  - Run schema-markup optimization
  - Review failed articles manually
  - Rollback if needed: node scripts/modules/meta-tags.js --action rollback --site yololab
```

### Step 7: Offer Next Actions

After reporting:
- **Continue** with another module
- **Rollback** the completed module
- **Done** — clear state and finish

## Module Reference

### Image ALT (`image-alt`)
- Phases: scan → apply-featured → apply-inline → report
- Rollback: `--action rollback --target featured|inline|all`
- Uses Claude Vision for alt text generation
- Cost: ~$0.001/image

### Meta Tags (`meta-tags`)
- Phases: scan → generate → apply → verify
- Rollback: restores original `_yoast_wpseo_title` and `_yoast_wpseo_metadesc`
- Uses Claude for meta title/description generation
- Verifies Yoast field support before batch starts

### Schema Markup (`schema-markup`)
- Phases: scan → generate → apply → verify
- Rollback: restores original `_yoast_wpseo_schema`
- Generates JSON-LD (Article, BlogPosting)
- Validates `@context` and `@type` fields

### Internal Links (`internal-links`)
- Phases: scan → generate-proposals → inject → fix-broken
- Rollback: restores full `post.content` from NDJSON backup
- Checks for existing "延伸閱讀" sections to avoid duplicates
- Large backups (~50-100MB for full site)

## Configuration

Site configs live in `.claude/skills/site-optimizer-config.json`:

```json
{
  "siteConfig": {
    "yololab": {
      "siteId": 133512998,
      "domain": "yololab.net",
      "language": "zh_TW",
      "totalArticles": 2728
    }
  }
}
```

## Environment Variables

| Variable | Required | Purpose |
|----------|----------|---------|
| `WPCOM_TOKEN` | Yes | WordPress.com Bearer token for API access |
| `ANTHROPIC_API_KEY` | For meta/schema | Claude API for text generation |

## Rollback

Every module creates backups before writes. To rollback:

```bash
node scripts/modules/{module}.js --action rollback --site yololab
```

Rollback restores the exact original values. For internal links, this includes full Gutenberg block content.

## Rate Limits

All modules use proven rate limits: `batch:5, delay:2000ms, retries:3, backoff:3000ms`.
Full site (2,728 articles) takes 6-8 hours per module.

## Lock Management

A global lock (`seo-optimization-output/seo-orchestrator.lock`) prevents concurrent SEO operations.
Lock has 8-hour TTL. If a session crashes, the lock auto-expires.

To manually clear a stale lock:
```bash
rm seo-optimization-output/seo-orchestrator.lock
```

## Supersedes

This skill replaces `/site-optimizer`. The old skill is deprecated.
See: `.claude/skills/SITE-OPTIMIZER.md` (legacy reference)
