# Tag Architecture Optimization — Implementation Checklist

**Project:** YOLO LAB Tag Architecture Optimization
**Date:** 2026-04-08
**Status:** Units 1-5 Complete, Units 6-8 Ready for Execution

---

## Unit 6: Tag Remapping & 301 Redirects ✅ Ready

**Objective:** Remap article tags and implement 301 redirects

### Execution Steps

1. **Prepare Data Migration Script**
   ```bash
   # Create script to remap articles from old tags to super-tags
   # Script: scripts/article-tag-remapper.py (to be created)
   # Logic:
   # - For each article, identify current tags
   # - Match to new super-tag cluster from super-tag-taxonomy.json
   # - Update article tag assignments via WordPress.com API
   # - Log all changes to JSON for rollback
   ```

2. **Dry-Run Validation**
   ```bash
   python scripts/article-tag-remapper.py --dry-run --sample 20
   # Expected: 20 articles simulated for tag remapping
   # Review output to verify mapping accuracy
   ```

3. **Execute Batch Remapping**
   ```bash
   python scripts/article-tag-remapper.py --batch-size 50 --delay 0.5
   # Expected: All articles remapped; log saved to docs/tag-architecture/migration-logs.json
   ```

4. **Implement 301 Redirects**
   - **Option A (Recommended):** WordPress.com Redirect Manager
     - Go to Tools → Redirects
     - Add: `/tag/{old-slug}/` → `/tag/{new-slug}/`
     - Verify: curl -I https://yololab.net/tag/hiphop-news/ (should show 301)

   - **Option B (Fallback):** .htaccess redirects (if applicable to WordPress.com plan)
     ```apache
     RewriteRule ^tag/hiphop-news/(.*)$ /tag/music/ [R=301,L]
     RewriteRule ^tag/film-intro/(.*)$ /tag/entertainment/ [R=301,L]
     ```

5. **Verify & Document**
   - [ ] Spot-check 20 redirects (curl tests)
   - [ ] Verify articles show new tag assignments in WordPress.com
   - [ ] Document redirect mappings in tag-remapping-strategy.md
   - [ ] Save pre-migration backup to docs/tag-architecture/backup-pre-migration.json

---

## Unit 7: QA & Verification ✅ Ready

**Objective:** Validate tag pages render correctly and schema is valid

### Verification Tasks

1. **Manual Spot-Check (3-5 Tag Pages)**
   - [ ] Visit each tag page: /tag/music/, /tag/entertainment/, /tag/culture/, /tag/tech/, /tag/sports/
   - [ ] Verify:
     - [ ] Header displays correctly
     - [ ] Description renders
     - [ ] Recent articles display
     - [ ] Featured content visible
     - [ ] Related tags links work
   - [ ] Screenshot each page for reference

2. **Metadata & Schema Validation**
   - [ ] View page source; search for meta tags:
     - [ ] `<meta name="description"` present (155-160 chars)
     - [ ] `<meta property="og:title"` present
     - [ ] `<meta property="og:image"` present
   - [ ] Validate schema JSON-LD:
     - [ ] Copy `<script type="application/ld+json">` to https://validator.schema.org/
     - [ ] Expected result: "Valid JSON-LD"

3. **Social Share Testing**
   - [ ] Use https://www.opengraphcheck.com/
   - [ ] For each tag page:
     - [ ] OG title renders
     - [ ] OG description renders
     - [ ] OG image displays

4. **SEO Verification**
   - [ ] Submit tag pages to Google Search Console:
     - [ ] Go to GSC → URL inspection
     - [ ] Paste: https://yololab.net/tag/music/
     - [ ] Click "Request Indexing"
   - [ ] Monitor indexing over 24-48h
   - [ ] Check coverage report for errors

5. **301 Redirect Testing**
   - [ ] For each merged tag:
     ```bash
     curl -I https://yololab.net/tag/hiphop-news/
     # Expected: HTTP 301 Moved Permanently
     # Location: https://yololab.net/tag/music/
     ```

### Success Metrics

| Metric | Target | Validation |
|--------|--------|-----------|
| Tag Pages Indexed | 5/5 within 24h | GSC Coverage Report |
| Meta Tags Present | 100% of tags | Page source inspection |
| Schema Valid | 100% pass JSON-LD validator | Schema.org validator |
| OG Tags Render | 100% of tags | opengraphcheck.com |
| 301 Redirects | 100% return 301 status | curl -I tests |

### QA Report Output

- Create: `docs/tag-architecture/qa-report.md`
- Include: Screenshot evidence, curl outputs, GSC status, recommendations

---

## Unit 8: Tag Governance & Future Rules ✅ Ready

**Objective:** Document governance rules and prevent tag debt reaccumulation

### Governance Documentation

1. **Create TAG-GOVERNANCE.md**
   ```markdown
   # Tag Governance Rules

   ## New Tag Creation Rules

   **Requirement:** All new tags must:
   1. Fall into one of 5 super-tag clusters (Music, Entertainment, Culture, Tech, Sports)
   2. Follow naming convention: kebab-case, English, no duplicates
   3. Have accompanying description (50+ words)
   4. Include ≥3 related articles before launch
   5. Get editorial approval before deployment

   ## Maintenance Schedule

   - **Monthly:** Monitor tag usage; identify low-traffic tags (<5 posts)
   - **Quarterly:** Run tag-audit-generator.py; review for consolidation opportunities
   - **Annual:** Full tag structure review; update taxonomy if needed

   ## Low-Usage Tag Policy

   Tags with <5 posts automatically flagged for consolidation or deprecation.
   Decision required from editorial team before action.
   ```

2. **Update CONVENTIONS.md**
   - Add section: "Tag Naming & Governance"
   - Include rules from TAG-GOVERNANCE.md

3. **Create Optional Audit Script**
   ```bash
   # scripts/tag-governance-checker.py
   # Quarterly audit to identify:
   # - Orphaned tags (0 posts)
   # - Low-usage tags (<5 posts)
   # - Duplicate/semantic overlap tags
   # - Tags violating naming conventions
   ```

4. **Create Monitoring Dashboard Template**
   - Track: Tag traffic (impressions, CTR), tag growth, consolidation opportunities
   - Tools: Google Analytics 4, Google Search Console, custom reports

---

## Summary: All Units Status

| Unit | Task | Status | Output Files |
|------|------|--------|--------------|
| 1 | Tag Audit | ✅ Complete | tag-audit-report.json, tag-redundancy-analysis.md |
| 2 | Taxonomy Design | ✅ Complete | super-tag-taxonomy.json, tag-remapping-strategy.md |
| 3 | Content & Templates | ✅ Complete | tag-descriptions.md, tag-page-template.md |
| 4 | Metadata & Schema | ✅ Complete | tag-metadata.json, tag-schema-implementation.md |
| 5 | Metadata Update Script | ✅ Complete | tag-metadata-updater.py |
| 6 | Tag Remapping & Redirects | 🔄 Ready | article-tag-remapper.py, migration logs |
| 7 | QA & Verification | 🔄 Ready | qa-report.md, screenshots, GSC evidence |
| 8 | Governance | 🔄 Ready | TAG-GOVERNANCE.md, CONVENTIONS.md updates |

---

## Next Steps

1. **User Review** (Optional): Share progress with stakeholder; get feedback on Units 1-5
2. **Unit 6 Execution**: Run tag remapping script + implement 301 redirects
3. **Unit 7 Execution**: Perform QA checks and document findings
4. **Unit 8 Execution**: Document governance rules and commit
5. **Final Deployment**: Push changes to production; monitor Search Console for 14 days

---

## Risk Mitigation

| Risk | Mitigation | Responsibility |
|------|-----------|-----------------|
| Tag URL breakage | 301 redirects + 90-day preservation | Unit 6 |
| Article tag loss | Dry-run validation + backup | Unit 6 |
| Schema rendering issues | Manual validation + testing | Unit 7 |
| Governance non-compliance | Automated checker + review process | Unit 8 |

---

## Timeline

- **Phase 1 (This week):** Units 1-5 ✅ Complete
- **Phase 2 (Next week):** Units 6-7 execution + testing
- **Phase 3 (Week 3):** Unit 8 + governance launch
- **Phase 4 (Weeks 4-6):** Monitoring + optimization (24h, 7d, 14d checkpoints)

---

## Appendix: Key File References

- Plan: `docs/plans/2026-04-08-001-feat-tag-architecture-optimization-plan.md`
- Audit Output: `docs/tag-architecture/tag-audit-report.json`
- Taxonomy: `docs/tag-architecture/super-tag-taxonomy.json`
- Descriptions: `docs/tag-architecture/tag-descriptions.md`
- Metadata: `docs/tag-architecture/tag-metadata.json`
- Scripts: `scripts/tag-audit-generator.py`, `scripts/tag-metadata-updater.py`, `scripts/article-tag-remapper.py` (TBD)

---

**Created by:** AI (Claude)
**Last Updated:** 2026-04-08
**Next Review:** 2026-04-15
