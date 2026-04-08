# Tag Governance Rules for YOLO LAB

**Effective Date:** 2026-04-08
**Last Updated:** 2026-04-08
**Owner:** Editorial & SEO Team

---

## Executive Summary

This document establishes governance rules to maintain tag health, prevent fragmentation reaccumulation, and ensure consistent tagging practices across YOLO LAB.

---

## 1. Tag Creation Rules

### 1.1 Cluster Assignment (Required)

**Every new tag MUST fall into one of 5 super-tag clusters:**

- 🎵 **Music** — Hip-hop, music industry, artists, lyrics, events
- 🎬 **Entertainment** — Film, TV, anime, games, celebrities
- 🌍 **Culture** — Cultural figures, events, classics, lifestyle, business
- 💻 **Tech** — Technology trends, startups, innovation, digital transformation
- ⚽ **Sports** — Athletes, sports news, professional leagues, athletic events

**Process:**
1. Identify primary topic of article
2. Map to most relevant cluster
3. Document mapping in editorial notes
4. Get editorial approval before tagging

**Non-Compliance:** Tags assigned outside clusters will trigger quarterly audit and consolidation recommendation.

### 1.2 Naming Convention (Required)

**All new tags MUST follow:**

- **Format:** `kebab-case` (lowercase, hyphens for spaces)
- **Language:** English only (no Chinese, emoji, or special characters)
- **Length:** 3-50 characters
- **Uniqueness:** No duplicate or near-duplicate tags (exact match check + semantic review)

**Examples:**
- ✅ `artificial-intelligence` (descriptive, unique)
- ✅ `hip-hop-culture` (cluster-specific)
- ❌ `AI` (too short, ambiguous)
- ❌ `Hip-Hop Culture` (spaces, capitals)
- ❌ `人工智能` (non-English)

**Enforcement:** Tag validation script runs quarterly; flags non-compliant tags for remediation.

### 1.3 Content Requirement (Required)

**Before creating a new tag:**

- [ ] **Minimum 3 related articles** published/planned with this tag
- [ ] **Description written** (50+ words explaining scope and relevance)
- [ ] **Cluster mapping documented** (which super-tag cluster & why)
- [ ] **SEO keyword intent** identified (what search terms does this serve?)

**Rationale:** Prevents creation of thin, single-article tags that create SEO debt.

### 1.4 Editorial Approval (Required)

**Tag creation workflow:**

1. **Editor** proposes new tag with:
   - Cluster assignment
   - 3+ article examples
   - Description (50+ words)
   - SEO keyword intent

2. **SEO Lead** reviews for:
   - Keyword research + SERP potential
   - Cluster fit
   - Competition vs. organic opportunity

3. **Editorial Lead** approves or requests revisions

4. **Tag deployed** once approved; added to monitoring dashboard

**Timeline:** 2-3 business days from proposal to deployment

---

## 2. Tag Maintenance Schedule

### 2.1 Monthly Review

**Task:** Monitor tag usage and flag alerts

```bash
# Run monthly:
python scripts/tag-governance-checker.py --report monthly
```

**Checks:**
- Tags with 0 posts (orphaned) → flag for deprecation
- Tags with <5 posts → flag for consolidation review
- Tags with 100+ posts → evaluate splitting into sub-clusters
- Duplicate/semantic overlap tags → recommend merging

**Output:** Monthly governance report (email to editorial team)

### 2.2 Quarterly Audit

**Task:** Full tag structure review

```bash
# Run quarterly (Jan, Apr, Jul, Oct):
python scripts/tag-audit-generator.py --full
python scripts/tag-governance-checker.py --report quarterly
```

**Process:**
1. Generate full tag audit (usage, redundancy, performance)
2. Identify consolidation candidates
3. Present findings to editorial + SEO teams
4. Vote on consolidations/deprecations
5. Document decisions + execute

**Decision Criteria:**

| Condition | Action |
|-----------|--------|
| 0 posts | Deprecate immediately |
| 1-4 posts | Review for consolidation |
| 5-20 posts | Monitor, evaluate in next cycle |
| 20+ posts | Keep; evaluate split if >100 |
| Semantic overlap | Merge to primary; implement 301 |

### 2.3 Annual Review

**Task:** Strategic tag structure refresh

- Evaluate 5 super-tag clusters (still serving needs?)
- Propose new clusters if needed
- Review governance rules; update if necessary
- Plan next year's tag roadmap

---

## 3. Low-Usage Tag Policy

### Tags with <5 Posts

**Status:** Candidate for consolidation or deprecation

**Process:**

1. **Identify:** Monthly audit flags tags with <5 posts
2. **Review:** Editorial team votes on consolidation vs. deprecation
3. **Consolidate:** If merging, assign posts to parent super-tag + implement 301 redirect
4. **Deprecate:** If discontinuing, remove tag; reassign posts to relevant clusters
5. **Monitor:** Track merged/deprecated tags for 90 days to ensure posts found

### Orphaned Tags (0 Posts)

**Action:** Automatic deprecation

- Monthly script identifies orphaned tags
- Archived (not deleted) for 90-day recovery period
- Deleted after 90 days if no new posts assigned

---

## 4. Tag Performance Monitoring

### Dashboard Metrics

**Monitor these KPIs per tag:**

| Metric | Healthy Range | Action Trigger |
|--------|---|---|
| Posts | 5+ | <5 = consolidation review |
| Avg Impressions/mo | 20+ | <20 = low demand |
| Avg CTR (SERP) | 2%+ | <2% = consider deprecation |
| Organic Ranking | Top 50 | >100 = lower priority |
| Traffic/mo | 50+ | <50 = low value |

**Tools:**
- Google Search Console (SERP performance)
- Google Analytics 4 (traffic, engagement)
- WordPress.com Analytics (post counts, trends)

**Dashboard Updated:** Monthly via automated script

---

## 5. Tag Merging & Consolidation

### When to Merge

**Merge tags when:**
- High semantic overlap (e.g., "hip-hop-news" + "hip-hop-updates")
- Similar post coverage (<20% unique post delta)
- Low individual traffic (<50 impressions/month each)
- User confusion about distinction (survey feedback)

### Merge Process

1. **Identify pairs/groups** to consolidate
2. **Get editorial approval** (avoid breaking author tagging habits)
3. **Run dry-run merge** on sample articles
4. **Implement 301 redirect** (old tag → primary tag)
5. **Reassign articles** (via `article-tag-remapper.py`)
6. **Monitor 30 days** for issues
7. **Document decision** in governance log

### Redirect Duration

- **Preserve 301 redirects minimum 90 days** (allows search engines to crawl, users to navigate)
- **After 90 days**, evaluate retention:
  - If 0 traffic via redirect → remove after 1 year
  - If >100 impressions/month → preserve indefinitely

---

## 6. Tag Naming & Slug Management

### Slug Immutability

**Do not change tag slugs without strong reason:**

- Breaks existing links + SERP rankings
- Requires 301 redirects for every reference
- Confuses users & internal linking

**Acceptable changes:**
- Fixing typos in slug (e.g., `hip-hop-cultu` → `hip-hop-culture`)
- Removing accidental special characters
- Consolidating duplicates

### Slug Updates

If slug must change:
1. Create new tag with correct slug
2. Merge all posts to new tag
3. Implement 301 redirect (old → new)
4. Preserve redirect for ≥1 year

---

## 7. Governance Violations & Remediation

### Non-Compliance Examples

| Violation | Severity | Remediation |
|-----------|----------|-------------|
| Tag outside 5 clusters | High | Assign to cluster or deprecate |
| Tag with 0 posts (90+ days) | Medium | Archive or delete |
| Tag with <5 posts (6+ months) | Medium | Consolidate or deprecate |
| Non-kebab-case slug | Low | Rename (with 301) |
| Single-article tag | Medium | Consolidate or monitor |
| Duplicate/semantic overlap | Medium | Merge to primary |

### Remediation Timeline

- **High severity:** Fix within 1 month
- **Medium severity:** Fix within 1 quarter
- **Low severity:** Fix during annual review

---

## 8. Editorial Responsibilities

### What Editorial Must Do

- [ ] **Tag strategically** — Use tags to organize content by intent, not just keywords
- [ ] **Follow naming convention** — Use kebab-case, English, cluster-relevant names
- [ ] **Document intent** — Note which cluster + why when tagging articles
- [ ] **Avoid over-tagging** — Prefer 1-2 primary tags over 5+ tags per article
- [ ] **Review low-traffic tags** — Volunteer for consolidation discussions

### What Editorial Should NOT Do

- ❌ Create tags for single articles (violates 3+ article rule)
- ❌ Use Chinese or special characters in slugs
- ❌ Tag articles with both parent + child tags (e.g., both "Music" + "Music-Personas")
- ❌ Leave articles untagged (at least 1 super-tag required)

---

## 9. Governance Tools & Scripts

### Automated Checks

**Monthly Script:** `tag-governance-checker.py`

```bash
# Generate monthly governance report
python scripts/tag-governance-checker.py --report monthly

# Output: governance-report-2026-04.json
# Shows: Orphaned tags, low-usage tags, duplicates, non-compliance
```

**Quarterly Audit:** `tag-audit-generator.py`

```bash
# Generate full tag audit
python scripts/tag-audit-generator.py --full

# Output: tag-audit-report.json
# Shows: Usage stats, redundancy analysis, consolidation candidates
```

### Manual Reviews

- **Editorial Review:** Quarterly editorial + SEO meeting
- **Dashboard Review:** Weekly glance at key metrics
- **Ad Hoc Reviews:** When major content initiatives launch (new series, campaigns, etc.)

---

## 10. Future Considerations

### Potential Future Enhancements

- **Auto-Consolidation:** After 6+ months with <5 posts, auto-merge to parent cluster (with notifications)
- **Tag Recommendations:** AI-powered tag suggestions for new articles based on content
- **Tag Synonyms:** Map user misspellings to canonical tags (e.g., "AI" → "artificial-intelligence")
- **Dynamic Clusters:** Merge/split clusters based on traffic + editorial needs
- **Cross-Cluster Tags:** Allow occasional tags spanning multiple clusters (e.g., "AI + Entertainment" for AI-art articles)

### Review Timeline

- **Year 1:** Establish baseline + monitor compliance
- **Year 2:** Evaluate for enhancements; implement top 2 features
- **Year 3+:** Mature governance; focus on optimization

---

## Appendix: Quick Reference

### Tag Creation Checklist

```
□ Cluster assigned (Music/Entertainment/Culture/Tech/Sports)
□ Slug in kebab-case (lowercase, hyphens, no special chars)
□ ≥3 existing articles tagged (or planned)
□ Description written (50+ words)
□ SEO keyword intent identified
□ Editorial approval obtained
```

### Monthly Governance Checklist

```
□ Run tag-governance-checker.py
□ Review orphaned/low-usage tags
□ Flag consolidation candidates
□ Check for naming violations
□ Update monitoring dashboard
□ Email report to editorial team
```

### Quarterly Audit Checklist

```
□ Run tag-audit-generator.py --full
□ Review redundancy analysis
□ Vote on consolidations
□ Execute merges + 301 redirects
□ Document decisions
□ Update governance log
```

---

## Version History

| Date | Change | Owner |
|------|--------|-------|
| 2026-04-08 | Initial governance rules | AI + Editorial Team |
| TBD | Q2 2026 Review | Editorial Team |
| TBD | Annual Review | Editorial + SEO Team |

---

**Questions?** Contact: [Editorial Lead] or [SEO Lead]
**Last Updated:** 2026-04-08
**Next Review:** 2026-07-08
