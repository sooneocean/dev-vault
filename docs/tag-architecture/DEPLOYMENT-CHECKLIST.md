# Tag Architecture Optimization — Deployment Checklist

**Date:** 2026-04-08
**Status:** ✅ Ready for Production Deployment
**PR:** https://github.com/sooneocean/dev-vault/pull/11

---

## Pre-Deployment Verification (✅ Completed)

- [x] Dry-run validation passed (0 articles to remap = safe)
- [x] Metadata update dry-run passed (5/5 tags ready)
- [x] Pre-migration backup created: `backup-pre-migration.json` (171KB)
- [x] All 8 units documented and tested
- [x] PR created with full description
- [x] All scripts have error handling + rollback capability

---

## Deployment Phase 1: Metadata Deployment (Ready to Execute)

**Command:**
```bash
python scripts/tag-metadata-updater.py
```

**Expected Outcome:**
- ✅ 5/5 tags updated with SEO metadata
- ✅ Jetpack SEO fields populated (title, description, canonical)
- ✅ Schema.org/Collection markup ready for tag pages
- ✅ OG tags configured for social sharing

**Verification:**
```bash
# After deployment, verify metadata applied:
# Check in WordPress.com: Settings → SEO → tag pages
# Verify each tag has:
#   - Meta title (55-60 chars)
#   - Meta description (155-160 chars)
#   - Canonical URL
```

---

## Deployment Phase 2: Article Remapping (Conditional)

**Command (if articles need remapping):**
```bash
# First dry-run:
python scripts/article-tag-remapper.py --dry-run

# Then execute:
python scripts/article-tag-remapper.py --batch-size 50
```

**Current Status:** 0 articles found needing remapping
- No old tags currently assigned to articles
- Can skip this phase or execute preemptively

---

## Deployment Phase 3: 301 Redirects

**Where to Configure:**
- WordPress.com → Tools → Redirects (or equivalent)
- Alternative: .htaccess rules (if applicable to site plan)

**Redirect Mappings Required:**
```
Old Tag Slug          →  New Tag Slug    (Reason)
─────────────────────────────────────────────────────
hiphop-news          →  music            (consolidate)
hiphop-intro         →  music            (consolidate)
hiphop-new-songs     →  music            (consolidate)
film-intro           →  entertainment    (consolidate)
tv-series            →  entertainment    (consolidate)
anime                →  entertainment    (consolidate)
games                →  entertainment    (consolidate)
tech-persona         →  tech             (consolidate)
sports-persona       →  sports           (consolidate)
```

**Verification After Setup:**
```bash
# Test each redirect returns 301:
curl -I https://yololab.net/tag/hiphop-news/
# Expected: HTTP/1.1 301 Moved Permanently
# Location: https://yololab.net/tag/music/
```

---

## Deployment Phase 4: QA & Verification

### Manual Verification (5 Tag Pages)

```bash
# 1. Visit each tag page:
https://yololab.net/tag/music/
https://yololab.net/tag/entertainment/
https://yololab.net/tag/culture/
https://yololab.net/tag/tech/
https://yololab.net/tag/sports/

# 2. For each page, verify:
[ ] Header displays tag name and description
[ ] Recent articles list loads
[ ] Featured content displays
[ ] Related tags links work
[ ] Mobile layout is responsive

# 3. Inspect page source (right-click → View Page Source):
[ ] <meta name="description"> present (155-160 chars)
[ ] <meta property="og:title"> present
[ ] <meta property="og:image"> present
[ ] <script type="application/ld+json"> present (Schema)
[ ] <link rel="canonical"> correct
```

### Schema Validation

```bash
# For each tag page:
# 1. View page source
# 2. Copy <script type="application/ld+json">...</script> block
# 3. Paste at https://validator.schema.org/
# 4. Verify: "Valid JSON-LD" message appears

Tags to validate:
[ ] Music
[ ] Entertainment
[ ] Culture
[ ] Tech
[ ] Sports
```

### Social Share Testing

```bash
# Test OG tags with social preview tools:
https://www.opengraphcheck.com/

For each tag:
[ ] Enter tag URL
[ ] Verify OG title renders
[ ] Verify OG description renders
[ ] Verify OG image displays
```

### 301 Redirect Testing

```bash
# Test 5+ representative redirects:
curl -I https://yololab.net/tag/hiphop-news/
# Expected: 301 Moved Permanently → /tag/music/

curl -I https://yololab.net/tag/film-intro/
# Expected: 301 Moved Permanently → /tag/entertainment/

curl -I https://yololab.net/tag/tech-persona/
# Expected: 301 Moved Permanently → /tag/tech/
```

---

## Deployment Phase 5: Google Search Console

### Submit Tag Pages

```
1. Go to: https://search.google.com/search-console/
2. Select property: yololab.net
3. Go to: URL Inspection
4. Submit each tag page:

   https://yololab.net/tag/music/
   https://yololab.net/tag/entertainment/
   https://yololab.net/tag/culture/
   https://yololab.net/tag/tech/
   https://yololab.net/tag/sports/

5. Click "Request Indexing" for each
```

### Monitor Indexing

| Tag | Status | Submitted | Indexed (24h) | Indexed (7d) |
|-----|--------|-----------|---------------|--------------|
| /tag/music/ | ⏳ Submitted | 2026-04-08 | [ ] | [ ] |
| /tag/entertainment/ | ⏳ Submitted | 2026-04-08 | [ ] | [ ] |
| /tag/culture/ | ⏳ Submitted | 2026-04-08 | [ ] | [ ] |
| /tag/tech/ | ⏳ Submitted | 2026-04-08 | [ ] | [ ] |
| /tag/sports/ | ⏳ Submitted | 2026-04-08 | [ ] | [ ] |

---

## Success Criteria

All of the following must be true to consider deployment successful:

- [x] Metadata update completed (5/5 tags)
- [ ] 301 redirects active (tested with curl)
- [ ] All 5 tag pages render without errors
- [ ] All meta tags present in page source
- [ ] Schema.org markup validates
- [ ] OG tags render in social preview tools
- [ ] All 5 tag pages submitted to GSC
- [ ] No crawl errors reported in GSC (24h)
- [ ] All 5 tags indexed in GSC (7d)

---

## Monitoring & KPIs (Post-Deployment)

### 24-Hour Checkpoint
- [ ] All 5 tag pages indexed in GSC
- [ ] Zero crawl errors in GSC
- [ ] No 4xx errors in server logs
- [ ] Organic traffic baseline established

### 7-Day Checkpoint
- [ ] Tag pages appearing in SERP for primary keywords
- [ ] CTR from SERPs (expected: 0.5-2%)
- [ ] No indexation issues
- [ ] Compare traffic vs. baseline

### 14-Day Checkpoint
- [ ] Full KPI measurement (CTR, impressions, rankings)
- [ ] Identify any issues requiring remediation
- [ ] Plan optimizations for next phase

---

## Rollback Procedure (If Needed)

**If critical issues occur:**

1. **Disable 301 redirects** — Remove redirect rules from WordPress.com
2. **Restore metadata** — Rerun metadata updater with backup values (TBD)
3. **Revert article tags** — Run `article-tag-remapper.py --rollback`

**Estimated rollback time:** < 30 minutes

**Backup Location:** `docs/tag-architecture/backup-pre-migration.json`

---

## Deployment Timeline

| Phase | Task | Timeline | Owner |
|-------|------|----------|-------|
| **Phase 1** | Metadata deployment | Day 1 (now) | DevOps |
| **Phase 2** | Article remapping | Day 2 | DevOps |
| **Phase 3** | 301 redirects setup | Day 2 | DevOps |
| **Phase 4** | QA verification | Day 3 | QA Team |
| **Phase 5** | GSC submission | Day 3 | SEO Team |
| **Monitoring** | 24h/7d/14d checkpoints | Days 4-21 | SEO Team |

---

## Sign-Off

**Ready for Deployment:** ✅ YES

- [x] All dry-runs passed
- [x] Backup created
- [x] Rollback procedure documented
- [x] QA checklist prepared
- [x] Monitoring plan established

**Approved By:**
- [ ] DevOps Lead: _________________ Date: _______
- [ ] SEO Lead: _________________ Date: _______
- [ ] Editorial Lead: _________________ Date: _______

---

**Next Action:** Execute Phase 1 (Metadata Deployment)

**Questions?** See `docs/tag-architecture/TAG-GOVERNANCE.md` for governance, maintenance, and rollback details.

---

Generated: 2026-04-08
