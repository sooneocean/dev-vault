---
title: feat: Tag Architecture Optimization & Content Enrichment
type: feat
status: completed
date: 2026-04-08
origin: User request via /ce:plan
completed_date: 2026-04-08
---

# Tag Architecture Optimization & Content Enrichment for YOLO LAB

## Overview

YOLO LAB currently has 30 categories mapped to 80+ tags with minimal page metadata and no tag page content strategy. This plan systematizes tag organization through **super-tag grouping** (reducing fragmentation), enriches tag page content with descriptions and structured metadata, and optimizes for both SEO and user navigation. The result: visitors can discover content clusters more easily, search engines understand tag semantics better, and internal linking improves.

## Problem Frame

**Current State:**
- 30 categories with inconsistent naming (English/Chinese mix)
- 80+ tags with no standardized descriptions or page content
- Tag pages are bare—just post lists with no context
- No schema markup on tag archives
- Tag redundancy: similar concepts scattered across multiple tags (e.g., multiple "persona" tags, multiple "news" tags)
- Users can't distinguish between tags or understand their scope
- Low internal linking from tag pages to related content

**Business Impact:**
- Reduced organic traffic from tag page SEO
- Poor user experience for content discovery
- Wasted crawl budget on thin/duplicate tag pages
- Missed opportunity for topical clustering and E-E-A-T signals

## Requirements Trace

- **R1:** Audit all 80+ existing tags and map their usage, redundancy, and semantic overlap
- **R2:** Design a **super-tag grouping strategy**—consolidate 80+ tags into 5-7 topic clusters (Music, Entertainment, Film, Gaming, Tech, Sports, Culture) with 10-15 curated tags each
- **R3:** Write **tag descriptions** (150–200 words)—explain each super-tag cluster scope, related topics, and content strategy
- **R4:** Create **tag page templates** with:
  - Structured description + usage guide
  - Schema.org/TagCollection or Collection markup
  - Open Graph tags optimized for social sharing
  - Related tags widget / internal linking recommendations
- **R5:** Implement **tag metadata optimization**:
  - Meta title & description (60–160 characters, SEO-optimized)
  - Canonical tags to prevent faceting issues
  - Robots meta (indexable, follow) for priority clusters
- **R6:** Execute **tag remapping strategy**:
  - Preserve backward compatibility (301 redirects for merged tags)
  - Update article tag assignments to new super-tag structure
  - Update in `bulk_tags_final.py` and `batch-tag-allocator.py`
- **R7:** Establish **tag governance rules** (documented in codebase) for future additions

## Scope Boundaries

- **In Scope:**
  - Tag structure redesign and content enrichment
  - Tag page SEO optimization (metadata, schema, OG tags)
  - Remapping of existing tags to super-tag clusters
  - Documentation of tag taxonomy and governance

- **Out of Scope:**
  - Redesign of category structure (separate work)
  - Redesign of site-wide navigation (separate work)
  - Full rewrite of post content or archive pages
  - Custom theme modifications (work within WordPress.com template constraints)

## Context & Research

### Relevant Code and Patterns

**Batch Operations:**
- `scripts/batch-tag-allocator.py` (176 lines) — Existing tag assignment pattern using WordPress.com REST API v1.1
- `scripts/bulk_tags_final.py` (154 lines) — Full tag mapping table (30 categories → tag IDs); demonstrates rate limiting and error handling patterns
- `scripts/batch-tag-allocator.py` — Shows category-to-tag routing logic and progress monitoring

**SEO Optimization:**
- `scripts/yolo-lab-seo-optimizer-v3.js` (enterprise-grade SEO tool using Claude API) — Demonstrates:
  - Phased optimization strategy (5 phases, 4 tier levels)
  - Schema generation patterns (`NewsArticle`, `Review`, etc.)
  - OG tag generation for social sharing
  - State management for long-running batch jobs
  - Rate limiting and retry logic

**WordPress.com API Integration:**
- REST API v1.1 endpoint: `https://public-api.wordpress.com/rest/v1.1/sites/{SITE_URL}/posts`
- REST API v2 endpoint: `https://public-api.wordpress.com/wp/v2/sites/{SITE_ID}/posts`
- Authentication: Bearer Token (WP_TOKEN env var) or Basic Auth
- Supports tags, categories, meta (via Jetpack SEO yoast meta fields)

**Existing Patterns:**
- Tag ID mappings in `bulk_tags_final.py` (lines 16–49)
- Batch size: 10–20 posts per batch, 0.5–1.0 second delay between batches
- Progress checkpoints every 50 posts
- JSON state files for resumable jobs

### Institutional Learnings

- **Phase 2 SEO Report** (`docs/plans/2026-03-31-seo-phase2-post-deployment-monitoring.md`):
  - 2,800/2,800 posts optimized (100% success rate)
  - Multi-dimensional approach: title, meta, schema, internal links, alt text
  - Monitoring strategy: 24h, 7d, 14d checkpoints
- **Batch Publishing Pattern** (from `scripts/batch-*.py`):
  - 5-post batches with 3–5 second intervals minimize rate limiting
  - Always fetch existing tags before updating (avoid duplicate assignments)
  - Log failures separately from successes for easy debugging

### External References

- **Schema.org Collections & Tag semantics:**
  - [Schema.org/Collection](https://schema.org/Collection) for tag cluster semantics
  - [Schema.org/Thing → keywords](https://schema.org/Thing#property-keywords) for tag markup
- **WordPress.com Tag Management:**
  - REST API docs: `https://developer.wordpress.com/docs/api/`
  - Jetpack SEO meta fields (title, description, robots)
- **Tag Page SEO Best Practices:**
  - Google: [Manage your content in Google Search](https://support.google.com/webmasters/answer/9454834)
  - [Avoid thin content on faceted pages / tag archives](https://www.searchenginejournal.com/thin-content-seo/436891/)

## Key Technical Decisions

1. **Super-Tag Grouping Model**: 5–7 topic clusters vs. 30-category flat structure
   - **Rationale:** Reduces cognitive load, enables cross-domain discovery, improves internal link density, aligns with topical clustering best practices (E-E-A-T signals for Google SGE).

2. **Backward Compatibility via ID Preservation**: Keep existing tag IDs, update slug/name and metadata only
   - **Rationale:** Avoids breaking existing tag URLs (unless explicit 301 strategy), simplifies rollback, maintains existing article-to-tag relationships.

3. **Tag Page Content Strategy**: Templated descriptions (not AI-generated per-post) + schema markup + OG tags
   - **Rationale:** Consistent, reviewable content; faster publication; reusable templates; search engine compatibility.

4. **Phased Rollout**: Audit → Design → Content → Metadata → Migration → Monitoring
   - **Rationale:** Reduces risk, allows validation before batch updates, enables rollback at each phase.

5. **Use Claude API for Tag Description + SEO Generation**: Leverage yolo-lab-seo-optimizer-v3.js patterns
   - **Rationale:** Proven batch workflow, context-aware content, consistent style, resumable state management.

## Open Questions

### Resolved During Planning

- **Q: Should we preserve all 80+ tags, or consolidate into super-tags?**
  - **A:** User chose **aggressive consolidation** to 5–7 super-tag clusters (R2). This improves discoverability and SEO.

- **Q: What is the scope of tag page content?**
  - **A:** User chose **Deep** (R4): full page editing + schema + OG tags. Not lightweight (name only) or standard (name + brief description).

- **Q: How do we handle tag merging without breaking URLs?**
  - **A:** (Deferred to implementation, see below.)

### Deferred to Implementation

- **Q: Exact tag merge strategy:** Should merged tags 301 redirect to super-tag? Or keep both and change article assignments? Implementation will validate with WordPress.com API behavior.
- **Q: Tag description templates:** Exact format and character counts will be determined during content creation (Unit 4).
- **Q: Schema dialect:** Will confirm whether to use `Collection`, `TagCollection`, or custom schema during Unit 5 (Metadata Optimization).
- **Q: Monitoring metrics:** KPIs (CTR, impressions, ranking improvements) will be defined during Unit 7 (Monitoring & Governance).

## High-Level Technical Design

This illustrates the intended approach and is directional guidance for review, not implementation specification. The implementing agent should treat it as context, not code to reproduce.

```
┌─────────────────────────────────────────────────────────────────┐
│                  YOLO LAB TAG ARCHITECTURE REDESIGN             │
└─────────────────────────────────────────────────────────────────┘

PHASE 1: AUDIT & ANALYZE
┌──────────────────────────────────────────────────────────┐
│ Current State                                            │
│ • 30 categories × 80+ tags (mapping in bulk_tags_*.py)  │
│ • Tag usage counts from WordPress.com API               │
│ • Semantic overlap analysis (via Claude)                │
│ → Output: Tag audit spreadsheet, redundancy report      │
└──────────────────────────────────────────────────────────┘
                         ↓
PHASE 2: DESIGN SUPER-TAG GROUPS
┌──────────────────────────────────────────────────────────┐
│ Consolidation Strategy                                   │
│ • Define 5–7 super-tag clusters (e.g., "Music", "Film") │
│ • Assign 10–15 curated tags to each cluster             │
│ • Create tag → super-tag mapping table                  │
│ • Decide preservation vs. merge strategy                │
│ → Output: New taxonomy spreadsheet, merge playbook      │
└──────────────────────────────────────────────────────────┘
                         ↓
PHASE 3: CONTENT CREATION
┌──────────────────────────────────────────────────────────┐
│ Write Tag Descriptions                                  │
│ • 150–200 word descriptions for each super-tag cluster  │
│ • Related topics list, content strategy explanation     │
│ • Use Claude API for batch generation + review          │
│ → Output: Tag description file, editorial guidelines    │
└──────────────────────────────────────────────────────────┘
                         ↓
PHASE 4: SEO & METADATA OPTIMIZATION
┌──────────────────────────────────────────────────────────┐
│ Tag Page Metadata                                        │
│ • SEO title (55–60 chars) + meta description (155–160)  │
│ • Schema markup (Schema.org/Collection or TagCollection)│
│ • OG tags (title, description, image)                   │
│ • Canonical, robots meta (index/follow)                 │
│ → Output: Metadata CSV, schema templates                │
└──────────────────────────────────────────────────────────┘
                         ↓
PHASE 5: BATCH MIGRATION & REMAPPING
┌──────────────────────────────────────────────────────────┐
│ Update WordPress.com                                    │
│ • Update tag metadata via REST API                      │
│ • Remap article tags (old → new super-tag)              │
│ • Create 301 redirects (if merging tags)                │
│ • Update batch allocation scripts                       │
│ → Output: Migration logs, success report                │
└──────────────────────────────────────────────────────────┘
                         ↓
PHASE 6: VERIFICATION & MONITORING
┌──────────────────────────────────────────────────────────┐
│ QA & Performance Baseline                               │
│ • Verify tag page rendering (description, schema)       │
│ • Check Google Search Console indexing                  │
│ • Monitor ranking changes (day 1, 7, 14)                │
│ • Set up tag page performance dashboard                 │
│ → Output: QA report, monitoring plan, KPI dashboard     │
└──────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ Data Flow                                                       │
│                                                                 │
│ Audit → Design → Content → Metadata → Batch Update             │
│                                        └─→ 301 Redirects       │
│                                        └─→ Article Remapping   │
│                                        └─→ Script Updates      │
│                                                                 │
│ Monitoring feeds back to governance (tag creation rules)       │
└─────────────────────────────────────────────────────────────────┘
```

## Implementation Units

- [ ] **Unit 1: Tag Audit & Redundancy Analysis**

**Goal:** Understand current state — count tag usage, identify redundancy, document semantic overlap.

**Requirements:** R1

**Dependencies:** None (baseline data gathering)

**Files:**
- Create: `docs/tag-architecture/tag-audit-report.json` (tag usage stats)
- Create: `docs/tag-architecture/tag-redundancy-analysis.md` (semantic analysis + merge candidates)
- Modify: `bulk_tags_final.py` (optional: add debugging to export tag usage)

**Approach:**
- Query WordPress.com API to fetch all tags and their post counts
- Map tags to categories using existing mapping in `bulk_tags_final.py`
- Identify semantic clusters:
  - Multiple "PERSONA" tags → merge into "Personalities"
  - Multiple "NEWS" tags → merge into "News & Updates"
  - Multiple "EVENT" tags → merge into "Events & Culture"
- Document which tags are orphaned or low-usage
- Prioritize merge candidates (low-usage dupes first, high-impact clusters last)

**Patterns to follow:**
- Use `bulk_tags_final.py` tag ID mappings as reference
- Follow REST API v2 query pattern from `batch-tag-allocator.py` for fetching posts by tag
- Document findings in JSON + markdown for easy review

**Test scenarios:**
- Happy path: Fetch 30 categories, 80+ tags, post counts for each → audit report successfully generated
- Edge case: Some tags have 0 posts → report them separately as orphaned
- Integration: Verify tag counts match WordPress.com dashboard (manual spot-check)

**Verification:**
- Audit report lists all 80+ tags with post counts
- Redundancy analysis identifies 5–10 merge candidates
- Merge playbook documents which tags to consolidate and new super-tag names

---

- [ ] **Unit 2: Design Super-Tag Taxonomy & Merge Strategy**

**Goal:** Define 5–7 super-tag clusters, assign curated tags to each, decide on merge approach (preserve or redirect).

**Requirements:** R2, R6

**Dependencies:** Unit 1

**Files:**
- Create: `docs/tag-architecture/super-tag-taxonomy.json` (super-tag cluster definitions)
- Create: `docs/tag-architecture/tag-remapping-strategy.md` (merge playbook, 301 strategy, rollback plan)
- Modify: `bulk_tags_final.py` (prepare for new tag mappings, add comments)

**Approach:**
- Based on Unit 1 audit, consolidate 80+ tags into 5–7 clusters:
  - **Music** (10–15 tags: hip-hop news, personalities, lyrics, events, etc.)
  - **Entertainment** (10–15 tags: film, TV, anime, games, persons, etc.)
  - **Tech** (3–5 tags: tech news, personas, events)
  - **Sports** (3–5 tags: news, personas)
  - **Culture** (5–8 tags: events, personas, classics, business, etc.)
  - *Optional:* **Trending**, **Interviews**, **Deep Dives** (cross-cutting tags)
- For each super-tag cluster:
  - Document scope and coverage (2–3 sentence description)
  - List constituent tags to be merged
  - Assign 10–15 representative child tags to keep under the super-tag
- Decide merge strategy:
  - **Preserve & Redirect:** Keep old tag IDs as redirects, update post assignments to new super-tag
  - **Merge & Deprecate:** Delete old tags, update all posts to new super-tag
  - **Hybrid:** High-volume tags preserved, low-volume tags merged
- Document rollback plan (restore from backup if needed)

**Patterns to follow:**
- Use `bulk_tags_final.py` structure (category ID → tag ID array) as template
- Follow phase-based approach from `yolo-lab-seo-optimizer-v3.js` (audit → design → execute → monitor)

**Test scenarios:**
- Happy path: Define 5–7 super-tag clusters covering all 80+ existing tags
- Edge case: Tags with overlapping scope → decide consolidation rules
- Validation: Every existing tag maps to exactly one super-tag cluster

**Verification:**
- Taxonomy JSON document lists all super-tag clusters with child tags
- Merge playbook covers 100% of tags (old → new mapping)
- Rollback plan documented and validated by team

---

- [ ] **Unit 3: Create Tag Descriptions & Content Templates**

**Goal:** Write 150–200 word descriptions for each super-tag cluster; create tag page content templates.

**Requirements:** R3, R4

**Dependencies:** Unit 2

**Files:**
- Create: `docs/tag-architecture/tag-descriptions.md` (descriptions for each super-tag cluster)
- Create: `docs/tag-architecture/tag-page-template.md` (HTML/block structure for tag pages)
- Create: `.claude/lib/tag-description-generator.js` (optional: Claude API wrapper for batch generation)

**Approach:**
- For each super-tag cluster, draft a 150–200 word description covering:
  - **What:** Scope and coverage of this tag cluster
  - **Why:** Why this cluster matters to readers
  - **What's Here:** Types of content published under this tag
  - **Related:** Cross-references to related clusters
  - **Editorial Voice:** Brief note on YOLO LAB's approach to this topic
- Create tag page template(s):
  - Header: Super-tag name, description, keyword list
  - Content section: 3–5 featured articles (curated or automatic)
  - Related tags widget: 5–8 related super-tag clusters
  - Meta: Last updated, post count, traffic metrics (future)
- Use Claude API to batch-generate descriptions (iterate on 1–2 samples, then generate all)

**Patterns to follow:**
- Tone/voice: Match YOLO LAB's editorial style (see existing articles for reference)
- Structure: Use existing SEO optimization patterns from `yolo-lab-seo-optimizer-v3.js` for consistency
- Review process: Create draft descriptions, stage for team review before finalization

**Test scenarios:**
- Happy path: Generate 150–200 word descriptions for 5–7 super-tag clusters
- Edge case: Description too short or too long → iterate and regenerate
- Style validation: Descriptions match YOLO LAB tone and editorial guidelines

**Verification:**
- All super-tag clusters have descriptions (150–200 words each)
- Tag page template renders correctly in WordPress.com block editor
- Template includes related tags widget and featured content

---

- [ ] **Unit 4: Generate Tag Metadata & Schema Markup**

**Goal:** Create SEO metadata (titles, descriptions, canonical, robots) and schema markup for tag pages.

**Requirements:** R4, R5

**Dependencies:** Unit 3

**Files:**
- Create: `docs/tag-architecture/tag-metadata.csv` (tag ID, slug, title, description, canonical, robots)
- Create: `docs/tag-architecture/tag-schema-templates.json` (schema.org Collection or TagCollection markup)
- Create: `.claude/lib/tag-metadata-generator.js` (Claude API wrapper for batch SEO generation)

**Approach:**
- For each super-tag cluster, generate:
  - **SEO Title** (55–60 characters): Include keyword + "| YOLO LAB"
  - **Meta Description** (155–160 characters): Compelling summary for SERP display
  - **Canonical URL**: `https://yololab.net/tag/{slug}/` (prevent faceting issues)
  - **Robots Meta**: `index, follow` for primary clusters; `noindex, follow` for niche/low-traffic clusters (decision deferred to Unit 7)
  - **OG Tags**: Title, description, image (use YOLO LAB logo or representative image)
- Generate schema markup:
  - Dialect: `Schema.org/Collection` or `TagCollection` (validate WordPress.com support)
  - Properties: name, description, keywords, mainEntity (featured articles), url
- Use Claude API to batch-generate, following patterns from `yolo-lab-seo-optimizer-v3.js`:
  - Phase 1: Generate titles + descriptions for all clusters
  - Phase 2: Generate schema markup
  - Phase 3: QA review and refinement

**Patterns to follow:**
- Follow SEO constraints from `scripts/seo/seo-batch-config.json` (title length, description length)
- Use retry logic from `yolo-lab-seo-optimizer-v3.js` for API calls
- Store state in JSON files for resumability

**Test scenarios:**
- Happy path: Generate SEO metadata for 5–7 super-tag clusters
- Edge case: Title too long → truncate intelligently; description too short → expand
- Schema validation: Validate schema JSON against Schema.org validator (external tool)

**Verification:**
- Metadata CSV has 5–7 rows (one per super-tag cluster) with all columns filled
- Schema markup validates against Schema.org
- OG tags render correctly in social sharing tools (manual spot-check)

---

- [ ] **Unit 5: Create Tag Page Metadata Update Script**

**Goal:** Build a reusable script to apply metadata (title, description, canonical, robots) and schema markup to WordPress.com tag pages.

**Requirements:** R5

**Dependencies:** Unit 4

**Files:**
- Create: `scripts/tag-metadata-updater.py` (batch script to apply metadata to tag pages)
- Create: `scripts/config/tag-metadata-config.json` (configuration for tag update batches)
- Modify: `bulk_tags_final.py` (optional: add utilities for tag metadata handling)

**Approach:**
- Create a Python script similar to `batch-tag-allocator.py`:
  - Read tag metadata CSV from Unit 4
  - Query WordPress.com REST API v2 to fetch tag objects
  - Use Jetpack SEO fields (yoast_meta) to store:
    - `yoast_meta['title']` → SEO title
    - `yoast_meta['description']` → Meta description
    - `yoast_meta['canonical']` → Canonical URL
  - Use standard tag fields for:
    - `name` → update to super-tag name (if merging)
    - `slug` → update slug for consistency
    - `description` → store readable description (for tag admin area)
  - Handle schema markup:
    - Store as comment or custom field? (defer to implementation decision)
    - Or inject into tag page via WordPress.com Customize section
- Implement batch logic:
  - Batch size: 10 tags per batch
  - Delay: 0.5 second between batches (rate limiting)
  - Progress checkpoints every 20 tags
  - Retry logic: 3 attempts with exponential backoff
  - State management: Resume from failure point

**Patterns to follow:**
- Follow patterns from `batch-tag-allocator.py` and `bulk_tags_final.py`
- Use same error handling and progress monitoring
- Store logs to JSON for debugging

**Test scenarios:**
- Happy path: Update 5–7 tag pages with metadata and schema
- Edge case: Some tags already have metadata → skip or override (decision in implementation)
- Integration: Verify metadata appears in WordPress.com tag edit screen and on front-end

**Verification:**
- Script runs without errors
- Tag metadata updates successfully (verify via API GET request)
- Schema markup appears in page source

---

- [ ] **Unit 6: Implement Article Tag Remapping & 301 Redirects**

**Goal:** Update existing articles to use new super-tag structure; handle tag merges with 301 redirects if needed.

**Requirements:** R6

**Dependencies:** Unit 2, Unit 5

**Files:**
- Create: `scripts/article-tag-remapper.py` (batch script to remap article tags)
- Create: `scripts/config/tag-merge-redirect-config.json` (301 redirect mappings if applicable)
- Modify: `bulk_tags_final.py` (update with new super-tag mappings)
- Create: `docs/tag-architecture/migration-execution-log.json` (track remapping progress)

**Approach:**
- **Article Remapping:**
  - For each article currently tagged with old tags, identify new super-tag assignments
  - Use super-tag taxonomy from Unit 2 (old tag ID → super-tag ID mapping)
  - Query articles by old tag, update their tag assignments to new super-tags
  - Handle many-to-one merges (multiple old tags → single super-tag)
  - Example: Article with tags [Hip-Hop News, Hip-Hop Intro] → new super-tag [Music]
  - Preserve article metadata (title, content, publish date, etc.)
- **301 Redirect Strategy (if merging tags):**
  - If merging old tags into super-tags, decide:
    - Option A: Keep old tag URLs as 301 redirects to super-tag page
    - Option B: Delete old tags, no redirect (acceptable if low traffic)
    - Option C: Create rewrite rules at WordPress.com level
  - Implement via WordPress.com REST API or .htaccess equivalent
  - Document redirect mapping in config
- **Batch Execution:**
  - Batch size: 50 articles per batch
  - Delay: 0.5 second between batches
  - Progress checkpoints every 200 articles
  - Retry logic: 3 attempts with exponential backoff
  - Dry-run mode: Simulate remapping without making changes

**Patterns to follow:**
- Follow batch execution patterns from `batch-tag-allocator.py` and `bulk_tags_final.py`
- Log all changes to JSON for rollback capability
- Document remapping rules for future reference

**Test scenarios:**
- Happy path: Remap 100+ articles from old tags to new super-tags
- Edge case: Article with multiple old tags → ensure correct super-tag assignment
- Conflict resolution: If article already has super-tag + old tag → consolidate
- Rollback: Verify dry-run produces correct mapping without side effects

**Verification:**
- Migration logs show all articles remapped successfully
- Articles tagged with old tags now show new super-tag assignments
- 301 redirects (if implemented) return correct status codes
- No articles lose their tags during migration

---

- [ ] **Unit 7: Tag Page QA & Verification**

**Goal:** Verify tag pages render correctly, metadata appears in page source, schema validates, and monitoring is in place.

**Requirements:** R4, R5

**Dependencies:** Unit 5, Unit 6

**Files:**
- Create: `docs/tag-architecture/qa-report.md` (verification checklist + findings)
- Create: `docs/tag-architecture/tag-page-audit-checklist.json` (automated audit config)
- Create: `.claude/lib/tag-page-audit.js` (optional: script to audit tag pages)

**Approach:**
- **Manual Verification (sample tags):**
  - Visit 3–5 representative tag pages (high-traffic, medium, low-traffic)
  - Verify:
    - Description renders (text is visible, not hidden)
    - SEO metadata appears in page title and meta tags (inspect source)
    - Schema markup is valid (use Schema.org validator)
    - OG tags are present (check with social sharing preview tool)
    - Related tags widget appears and links work
    - Featured content loads correctly
- **Automated Checks (optional):**
  - Query WordPress.com API to check tag metadata for all clusters
  - Fetch page source and verify schema markup presence
  - Check for broken links in related tags
  - Validate page load performance (GTmetrix or similar)
- **Search Engine Verification (post-deployment):**
  - Submit tag pages to Google Search Console
  - Monitor indexing status and ranking changes (baseline)
  - Track click-through rate (CTR) from SERP
  - Monitor 24h, 7d, 14d after deployment (similar to Phase 2 monitoring)

**Test scenarios:**
- Happy path: All 5–7 super-tag pages verify successfully
- Edge case: Schema markup not found in source → debug rendering
- Integration: Tag pages appear in Google Search Console within 24 hours
- Performance: Tag pages load in < 3 seconds (WordPress.com baseline)

**Verification:**
- QA report documents all 5–7 tag pages passed verification
- Schema markup validates against Schema.org
- Google Search Console shows tag pages indexed
- Monitoring plan established for 24h, 7d, 14d checks

---

- [ ] **Unit 8: Tag Governance & Future Rules**

**Goal:** Document tag creation rules, approval process, and guardrails to prevent reaccumulation of tag debt.

**Requirements:** R7

**Dependencies:** Unit 2, Unit 7

**Files:**
- Create: `docs/tag-architecture/TAG-GOVERNANCE.md` (rules, approval, maintenance)
- Modify: `CONVENTIONS.md` (add tag naming conventions section)
- Create: `scripts/tag-governance-checker.py` (optional: script to audit tag health quarterly)

**Approach:**
- **Tag Creation Rules:**
  - New tags must fall into one of the 5–7 super-tag clusters (no orphan tags)
  - Tag slug must follow convention: `kebab-case`, English, no duplicates
  - Tag description required before publication (prevent thin tags)
  - Must have ≥ 3 related articles before adding (prevent low-traffic tags)
  - Approval: Require editorial review before deployment
- **Maintenance Schedule:**
  - Quarterly: Audit tag usage and consolidate low-traffic tags
  - Annual: Full tag structure review and refresh
  - Document: Track tag creations, merges, deprecations
- **Monitoring Dashboard:**
  - Tag traffic (impressions, CTR)
  - Tag health (usage count, content quality)
  - Merge candidates (low-traffic, semantic overlap)
  - Orphaned tags (< 3 articles)

**Patterns to follow:**
- Follow conventions from existing `CONVENTIONS.md` (case-sensitive, language, metadata structure)
- Use governance patterns from Phase 2 post-deployment monitoring

**Test scenarios:**
- Future-proof: Rules prevent creation of duplicate or low-value tags
- Monitoring: Quarterly audits identify maintenance needs
- Compliance: All future tags created follow new conventions

**Verification:**
- Governance document signed off by team lead
- Conventions updated with tag naming rules
- Monitoring scripts run successfully in test environment

## System-Wide Impact

- **Tag URL Structure**: Super-tag consolidation will change tag page URLs. Old tags will either 301 redirect (if kept) or be deleted. Ensure GSC and analytics track the transition.

- **Internal Linking**: More curated tag pages with better descriptions and related tags widget will improve internal link density and topical clustering. E-E-A-T signals should improve.

- **Article Metadata**: Articles will be retagged to new super-tag structure. Existing links to old tag pages may break if not 301 redirected. Crawl budget may spike temporarily due to tag structure changes.

- **Search Performance**: Tag pages with better metadata and schema should rank better for tag-related queries. Monitor SERP impressions and CTR during monitoring phase.

- **Editorial Workflow**: New tag governance rules will require team adoption. Communicate rules early in Unit 8 to reduce friction.

- **API Compatibility**: Tag metadata updates use WordPress.com REST API v2 (Jetpack SEO fields). Ensure WP_TOKEN env var has sufficient permissions.

- **Unchanged Invariants**: Category structure remains unchanged (30 categories). Article content is not modified. Site navigation is not redesigned.

## Risks & Dependencies

| Risk | Mitigation |
|------|------------|
| **Tag URL changes break existing links** | Implement 301 redirects for merged tags; track in GSC. Document old → new URL mapping. |
| **WordPress.com API rate limiting during batch updates** | Use 0.5s delays between batches (proven from Phase 2). Monitor API response codes; auto-retry on 429. |
| **Incomplete tag metadata from Claude API** | Validate generated content before batch apply. Start with sample (5 tags), review, iterate. |
| **Article tag remapping misses edge cases** | Use dry-run mode to simulate before execute. Spot-check 20 remapped articles. Maintain rollback script. |
| **Search engine de-indexes tag pages during transition** | Implement 301 redirects; submit refreshed URLs to GSC; monitor indexing. Keep old tags as redirects for 90 days minimum. |
| **Team resistance to new tag governance rules** | Involve team early (Unit 2 design phase). Document rationale. Provide automation (governance-checker.py). |

## Documentation / Operational Notes

- **Rollback Capability**: Store pre-migration state of all tags (metadata, article assignments) in JSON backup. Maintain script to restore state if needed.
- **Google Search Console Submission**: After Unit 5, re-submit tag pages to GSC. Track indexing progress over 24h, 7d, 14d.
- **Monitoring Dashboard**: Set up dashboard (Analytics 4, GSC, custom) to track tag page traffic and SEO metrics post-deployment.
- **Editorial Communication**: Notify team of new tag governance rules before Unit 8 completion. Provide quick-start guide for tag creation workflow.
- **WordPress.com Customization**: Verify whether tag page schema markup can be injected via WordPress.com block editor or Customize panel (if not available, schema embedding strategy may change).

## Sources & References

- **Origin document:** User request (2026-04-08) for tag optimization via `/ce:plan` skill
- **Related code:**
  - `scripts/bulk_tags_final.py` — Existing tag ID mappings
  - `scripts/batch-tag-allocator.py` — Tag assignment pattern
  - `scripts/yolo-lab-seo-optimizer-v3.js` — Enterprise SEO generation (Claude API integration)
- **Related plans:**
  - `docs/plans/2026-03-31-seo-phase2-post-deployment-monitoring.md` — Phase 2 SEO monitoring (reference for monitoring structure)
  - `docs/plans/2026-04-03-seo-phase1-plan.md` — Phase 1 SEO audit (reference for diagnostic approach)
- **External references:**
  - [Schema.org/Collection](https://schema.org/Collection)
  - [WordPress.com REST API docs](https://developer.wordpress.com/docs/api/)
  - [Google Search Console: Tag page optimization](https://support.google.com/webmasters)
