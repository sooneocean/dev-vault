# Tag Remapping Strategy & Merge Playbook

**Date:** 2026-04-08
**Status:** Ready for Implementation (Unit 2 output)

---

## Overview

This document defines how to consolidate YOLO LAB's 80+ managed tags into 5 super-tag clusters while maintaining backward compatibility and preserving user experience.

---

## Current State vs. Proposed State

### Current Structure
- **5 Independently Managed Super-Tag Groups** (implied from TAG_MAPPING)
- **30 Category IDs** in bulk_tags_final.py
- **80+ Tag IDs** distributed across categories
- **Problem:** Tags scattered; no coherent clustering; tag pages weak

### Proposed Structure
- **5 Explicit Super-Tag Clusters:** Music, Entertainment, Culture, Tech, Sports
- **Consolidated Tag Pages:** Richer descriptions, better SEO, related tags
- **Unified Governance:** Clear rules for new tags
- **Backward Compatibility:** 301 redirects for merged tags

---

## Super-Tag Clusters (Detailed Definition)

### 1. Music Cluster
**Slug:** `music`
**Purpose:** Hip-hop, music industry news, artist coverage

**Preserved Tags (Core):**
- `music-topics` (96990595) — General music discussion
- `new-releases` (96990596) — New song releases
- `artist-updates` (96990597) — Artist news and updates
- `live-picks` (96990598) — Live performance coverage

**Merged Tags (301 Redirects):**
- Hip-Hop News (3 tags) → redirects to `/tag/music/`
- Hip-Hop Intro (3 tags) → redirects to `/tag/music/`
- Hip-Hop New Songs (3 tags) → redirects to `/tag/music/`
- Hip-Hop Events (3 tags) → redirects to `/tag/music/#events`
- Music Events (2 tags) → redirects to `/tag/music/`
- Music Personas (3 tags) → redirects to `/tag/music/#personalities`
- YOLO Lyrics (3 tags) → redirects to `/tag/music/` (or sub-cluster if niche)

**Total Child Tags:** 29
**Estimated Posts:** 168 (42 per core tag × 4)

---

### 2. Entertainment Cluster
**Slug:** `entertainment`
**Purpose:** Film, TV, anime, games, entertainment industry

**Preserved Tags (Core):**
- Entertainment core tags (3 tags from original ENTERTAINMENT category)

**Merged Tags (301 Redirects):**
- Film Intro (3 tags) → redirects to `/tag/entertainment/`
- TV Series (3 tags) → redirects to `/tag/entertainment/#tv`
- Anime (3 tags) → redirects to `/tag/entertainment/#anime`
- Classic Films (3 tags) → redirects to `/tag/entertainment/#classics`
- Film Personas (3 tags) → redirects to `/tag/entertainment/#personalities`
- Film Events (3 tags) → redirects to `/tag/entertainment/#events`
- Games (3 tags) → redirects to `/tag/entertainment/#games`
- Games News (2 tags) → redirects to `/tag/entertainment/`

**Total Child Tags:** 24
**Estimated Posts:** 150

---

### 3. Culture Cluster
**Slug:** `culture`
**Purpose:** Cultural events, personalities, classics, lifestyle

**Preserved Tags (Core):**
- Personas (3 tags) — Generic personalities anchor point

**Merged Tags (301 Redirects):**
- Events (3 tags) → redirects to `/tag/culture/#events`
- Author Personas (2 tags) → redirects to `/tag/culture/#personalities`
- Business Personas (3 tags) → redirects to `/tag/culture/#personalities`
- Ragnarok Personas (3 tags) → redirects to `/tag/culture/#personalities` (or review)
- Sexy Personas (3 tags) → redirects to `/tag/culture/#personalities` (or review)
- Classics (2 tags) → redirects to `/tag/culture/#classics`
- Classic Books (3 tags) → redirects to `/tag/culture/#classics`
- Classic Events (3 tags) → redirects to `/tag/culture/#events`
- Classic Works (3 tags) → redirects to `/tag/culture/#classics`

**Total Child Tags:** 29
**Estimated Posts:** 120

---

### 4. Technology Cluster
**Slug:** `tech`
**Purpose:** Tech news, innovation, industry trends

**Preserved Tags (Core):**
- Tech News (3 tags)

**Merged Tags (301 Redirects):**
- Tech Personas (3 tags) → redirects to `/tag/tech/#personalities`

**Total Child Tags:** 6
**Estimated Posts:** 45

---

### 5. Sports Cluster
**Slug:** `sports`
**Purpose:** Sports news and personalities

**Preserved Tags (Core):**
- Sports News (3 tags)

**Merged Tags (301 Redirects):**
- Sports Personas (3 tags) → redirects to `/tag/sports/#personalities`

**Total Child Tags:** 6
**Estimated Posts:** 40

---

## Merge Strategy: Detailed Decision Matrix

| Original Tag | Cluster | Action | Reason | 301 Target |
|---|---|---|---|---|
| Music core (4 tags) | Music | Preserve | High traffic (42 posts each); brand-defining | N/A |
| Hip-Hop News (3) | Music | Merge | Redundant with Music cluster | /tag/music/ |
| Hip-Hop Intro (3) | Music | Merge | Niche; consolidate into parent | /tag/music/ |
| Hip-Hop New Songs (3) | Music | Merge | Covered by `new-releases` core tag | /tag/music/#new-releases |
| YOLO Lyrics (3) | Music | Merge/Keep? | **DECISION PENDING:** Niche YOLO content; evaluate user impact | TBD |
| Entertainment core (3) | Entertainment | Preserve | High traffic; editorial importance | N/A |
| Film/TV/Anime/Games (24) | Entertainment | Merge | Reduce cognitive load; improve discovery | /tag/entertainment/ (with anchors) |
| Personas × 8 (24) | Culture | Merge into 1 | High fragmentation; consolidate into Personas | /tag/culture/#personalities |
| Events × 3 (9) | Culture/Music/Entertainment | Merge | Distribute by domain | /tag/[domain]/#events |
| Tech News (3) | Tech | Preserve | Focused; good coverage | N/A |
| Tech Personas (3) | Tech | Merge | Supplement main cluster | /tag/tech/#personalities |
| Sports News (3) | Sports | Preserve | Focused; good coverage | N/A |
| Sports Personas (3) | Sports | Merge | Supplement main cluster | /tag/sports/#personalities |

---

## Implementation Plan

### Phase 1: Taxonomy Finalization (Unit 2 ✓)
- [x] Define 5 super-tag clusters
- [x] Document merge strategy
- [x] Identify decision points (YOLO-LYRICS, niche PERSONA tags)

**Decision Points Requiring User Input:**
1. **YOLO-LYRICS:** Keep as dedicated sub-cluster or merge into Music?
2. **RAGNAROK-PERSONAS & SEXY-PERSONAS:** Are these brand-critical or can they merge?

### Phase 2: Content Creation (Unit 3)
- [ ] Write 150-200 word descriptions for each super-tag
- [ ] Create tag page templates
- [ ] Draft editorial guidelines

### Phase 3: Metadata Optimization (Unit 4)
- [ ] Generate SEO titles (55-60 chars) for each super-tag
- [ ] Generate meta descriptions (155-160 chars)
- [ ] Generate Schema.org/Collection markup
- [ ] Generate OG tags

### Phase 4: API Implementation (Units 5-6)
- [ ] Build Python script to update tag metadata via WordPress.com REST API
- [ ] Build Python script to remap articles (old tags → new super-tags)
- [ ] Implement 301 redirects via .htaccess or WordPress.com equivalent
- [ ] Backup original tag structure

### Phase 5: QA & Verification (Unit 7)
- [ ] Manually verify 3-5 tag pages (render, metadata, schema)
- [ ] Test 301 redirects (spot-check 10+ merged tags)
- [ ] Submit to Google Search Console
- [ ] Monitor indexing (24h, 7d, 14d)

### Phase 6: Governance (Unit 8)
- [ ] Document tag creation rules
- [ ] Update CONVENTIONS.md
- [ ] Create quarterly audit script

---

## Backward Compatibility & Rollback

### 301 Redirect Implementation

**Option A: WordPress.com Redirect Rules (Recommended)**
```
OLD: /tag/hiphop-news/
NEW: /tag/music/
STATUS: 301 Moved Permanently
```

Implement via WordPress.com's redirect manager or .htaccess equivalent.

**Option B: Tag Slug Mapping (Fallback)**
If WordPress.com doesn't support custom redirects, keep old tag slugs as aliases and canonicalize to new cluster:
```html
<link rel="canonical" href="https://yololab.net/tag/music/">
```

### Rollback Procedure

**If issues occur post-launch:**

1. **Restore tag assignments:** Re-run article-tag-remapper.py with `--rollback` flag
2. **Disable redirects:** Remove 301 redirect rules from .htaccess
3. **Restore tag metadata:** Revert Jetpack SEO fields from backup

**Backup Location:** `docs/tag-architecture/tag-audit-report.json` (pre-migration state)

---

## Data Migration Validation

### Pre-Launch Checklist

- [ ] Export pre-migration tag state (done in Unit 1 audit)
- [ ] Dry-run article remapping script on sample articles
- [ ] Verify 301 redirects resolve correctly
- [ ] Confirm schema markup validates
- [ ] Spot-check OG tags in social media preview

### Success Metrics

| Metric | Target | Validation |
|--------|--------|-----------|
| Tag Pages Indexed | 100% within 7 days | Google Search Console |
| 301 Redirect HTTP Status | 301 (not 302, 404) | curl -I /tag/old-slug/ |
| Meta Tags Present | All tags have meta title & description | Page source inspection |
| Schema Markup Valid | Valid JSON-LD | Schema.org validator |
| Article Tags Updated | 100% of articles re-tagged | Tag count by cluster |

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| 301 redirects not implemented | Low | High (broken links) | Test redirects on staging first; use WordPress.com URL tools |
| Articles lose tags during migration | Low | High (SEO loss) | Dry-run; spot-check 20 articles; maintain backup |
| Search engine de-indexes tag pages | Medium | High (traffic drop) | Implement 301 redirects; submit to GSC; monitor 14 days |
| Conflicting merge decisions | Low | Medium (rework) | Get user approval on YOLO-LYRICS, PERSONA niche tags |
| API rate limiting during bulk updates | Medium | Medium (slow rollout) | Use 0.5s batch delays; implement retry logic |

---

## Next Steps

1. **User Review:** Confirm 5-cluster structure and merge strategy
2. **Decision Point Resolution:** Get input on YOLO-LYRICS and niche PERSONA tags
3. **Unit 3 Kickoff:** Create tag descriptions and templates
4. **Weekly Check-in:** Monitor progress through Units 4-6

---

## Appendix: Tag ID Reference

**Preserved Core Tags:**

| Slug | Tag ID | Cluster | Posts |
|------|--------|---------|-------|
| music-topics | 96990595 | Music | 42 |
| new-releases | 96990596 | Music | 42 |
| artist-updates | 96990597 | Music | 42 |
| live-picks | 96990598 | Music | 42 |
| (Entertainment core) | 96990642-644 | Entertainment | ? |
| personas | 96990660-662 | Culture | ? |
| tech-news | 96990645-647 | Tech | ? |
| sports-news | 96990651-653 | Sports | ? |

**See `super-tag-taxonomy.json` for complete mapping.**
