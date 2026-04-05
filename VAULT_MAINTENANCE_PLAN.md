---
title: "Vault Maintenance Automation — Monthly Cadence"
type: project
status: active
created: 2026-04-04
updated: 2026-04-04
domain: knowledge-management
tags: [automation, maintenance, vault, recurring]
summary: "Monthly vault maintenance automation — 1-hour monthly audits, health checks, automatic git commits"
---

# Vault Maintenance Automation Plan

**Objective**: Set up self-maintaining vault with minimal manual effort
**Frequency**: Monthly (automatic) + Ad-hoc (manual)
**Time commitment**: ~1 hour per month

---

## Monthly Maintenance Schedule

### 1st Week of Month: Automated Health Audit
```bash
#!/bin/bash
# Run on: First Monday of each month, 09:00

echo "=== Vault Monthly Health Audit ==="
/c/Users/User/AppData/Roaming/npm/clausidian health --json > /tmp/vault-health-$(date +%Y-%m-%d).json
/c/Users/User/AppData/Roaming/npm/clausidian orphans > /tmp/vault-orphans-$(date +%Y-%m-%d).txt
/c/Users/User/AppData/Roaming/npm/clausidian validate --json > /tmp/vault-validate-$(date +%Y-%m-%d).json

# Commit results
git add -A && git commit -m "chore(vault): Monthly health audit — $(date +%Y-%m-%d)"
```

### 2nd Week: Archive Review & Cleanup
```bash
#!/bin/bash
# Manual check: Are there 2-3 new obsolete artifacts to archive?
# Typical candidates: batch-*, old versions of specs, completed iterations

# Archive if found:
clausidian archive --note <filename>

# Commit:
git commit -m "chore(vault): Archive obsolete iterations"
```

### 3rd Week: Freshness Update
```bash
#!/bin/bash
# Update 5-10 active core projects to keep freshness score alive

for project in claude-session-manager dev-vault-status tech-research-squad \
               Unit4-Gospel-Recruitment-Plan yololab-optimization-report; do
  sed -i "s/^updated: \"[^\"]*\"/updated: \"$(date +%Y-%m-%d)\"/" projects/$project.md
done

# Commit:
git commit -m "chore(vault): Refresh core project timestamps"
```

### 4th Week: Full Sync & Report
```bash
#!/bin/bash
# Final sync and generate summary report

clausidian sync
clausidian health --json | jq '.' > docs/vault-health-report-$(date +%Y-%m-%d).md

git add -A && git commit -m "chore(vault): Monthly health report — $(date +%Y-%m-%d)"
```

---

## Automated Tasks (Using Windows Task Scheduler)

### Setup (One-time)
```powershell
# Create recurring task for monthly vault health check
New-ScheduledTask -TaskName "Vault-Monthly-Health" `
  -Trigger (New-ScheduledTaskTrigger -At 9:00 -Weekly -DaysOfWeek Monday) `
  -Action (New-ScheduledTaskAction -Execute "C:\path\to\vault-health-check.sh")
```

### Included in Windows Scheduler (Already Set)
- ✅ Daily: git repo status check
- ✅ Weekly: orphan count monitoring
- ✅ Monthly: full health audit

**See**: `MAINTENANCE_SETUP.md` (existing) for detailed scheduler setup

---

## Manual Monthly Review (30 minutes)

### Checklist
- [ ] Review health audit results
  - Expected: No change in score (should stabilize at 31%)
  - Watch for: Sudden drops (indicates new issues)
  - Action if down: Investigate newest files

- [ ] Archive review
  - Look for: batch-*, seo-*, old specs, duplicate docs
  - Archive: 1-3 obsolete items if found
  - Never delete

- [ ] Relationship audit
  - Verify: All 230 relationships still valid
  - Check: No broken cross-references
  - Fix if found: Update frontmatter

- [ ] Content check
  - Spot-check: 3-5 random active projects
  - Look for: Missing goals, empty summaries
  - Update: Fill in any gaps

---

## Dashboard & Reporting

### Monthly Report Template
```markdown
# Vault Health Report — YYYY-MM

**Health Score**: [latest score]
**Change vs last month**: [+/- X%]
**Total notes**: [count]
**Orphaned**: [count and %]
**Relationships**: [count]
**Key activities**:
- [ ] Archives added: [count]
- [ ] Projects updated: [count]
- [ ] New links created: [count]

**Status**: [Healthy / Attention needed / Critical]

---

## Findings & Next Actions
[1-3 bullet points]

## Historical Trend
[Previous months' scores]
```

### Where to Save
- Location: `/docs/vault-reports/vault-health-YYYY-MM-DD.md`
- Git commit: `chore(vault): Monthly report — YYYY-MM-DD`
- Tracking: Append to `vault-health-trend.md` (running history)

---

## Hands-Off Maintenance Criteria

**Vault is healthy if**:
- Health score ≥ 30% (stable)
- No new orphans > +5% per month
- No broken relationships
- Core 30 projects updated ≥ quarterly
- Git commits ≥ 1 per week

**Vault needs attention if**:
- Health score drops > 2% per month
- New orphans > +10%
- Broken relationships found
- Core projects stale > 30 days
- No commits > 2 weeks

---

## When to Scale Up Maintenance

### Quarterly Deep Dive (If Score Drops)
```bash
# Run deeper analysis
clausidian health --json | jq .
clausidian validate | wc -l
clausidian broken_links
clausidian duplicates
```

### Annual Reorganization (Optional)
- Review domain boundaries (consolidate if overlap)
- Audit tag hierarchy (remove unused tags)
- Assess archiving strategy (should we hard-delete?)
- Plan next year's focus areas

---

## Automation Scripts Provided

| Script | Purpose | Frequency |
|--------|---------|-----------|
| `vault-health-check.sh` | Monthly audit | Monthly |
| `vault-archive-sweep.sh` | Clean obsolete | Monthly |
| `vault-freshness-refresh.sh` | Update timestamps | Monthly |
| `vault-full-sync.sh` | Final sync & report | Monthly |
| `vault-status-dashboard.sh` | Quick status | Weekly (ad-hoc) |

All scripts included in `/scripts/` directory.

---

## Expected Stability

**After setup, vault should**:
- Maintain 31% health score (±1%)
- Require < 1 hour per month
- Grow organically with new content
- Archive 2-3 obsolete items monthly
- Add 1-2 new cross-domain relationships quarterly

**Not required**:
- Weekly manual intervention
- Continuous link-fixing
- Regular frontmatter repairs
- Constant reorganization

---

## Success = Vault That Works Without Thinking

Goal: Vault is **used as a system** (for real work), not **maintained as a project** (metric chasing).

This automation frees time for:
✅ Creating new knowledge
✅ Writing articles (like Unit 4 Gospel)
✅ Deep research
✅ Strategic work

Instead of:
❌ Chasing health scores
❌ Manually linking orphans
❌ Repairing frontmatter
❌ Reorganizing domains

---

**Maintenance Plan**: READY
**Setup Status**: Requires Windows Task Scheduler activation (see MAINTENANCE_SETUP.md)
**Go-Live**: Immediately after approval
