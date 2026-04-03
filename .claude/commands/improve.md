---
title: Analyze Mode (default)
type: project
tags: [project, active]
created: 2026-04-03
updated: 2026-04-03
status: active
maturity: growing
domain: knowledge-management
summary: ""
---

Analyze recent usage experience and suggest configuration improvements for Claude Code.

Usage: `[apply|status]`

- No argument: Analyze journals and current config, identify improvement opportunities
- `apply`: Review and apply pending improvement proposals
- `status`: Show improvement tracking summary

## Analyze Mode (default)

When invoked without arguments:

1. **Read data sources:**
   - Recent journal entries (`journal/*.md`) — focus on `## Friction` section, pain points, "哪裡卡住", "下次要試", repeated manual operations
   - Current `~/.claude/settings.json` hooks configuration
   - Current project `CLAUDE.md` instructions
   - Current `.claude/commands/` slash commands
   - Existing improvement notes (`resources/improvement-*.md`) to avoid duplicate proposals

2. **Identify improvement opportunities** in three categories:
   - **missing-hook**: Operations mentioned as manual/repetitive in journals that could be automated via hooks (PostToolUse, Stop, etc.)
   - **instruction-gap**: Patterns where CLAUDE.md lacks guidance that would have prevented friction or confusion
   - **command-gap**: Frequently needed operations that lack a dedicated slash command

3. **For each improvement found:**
   - Check existing `resources/improvement-*.md` notes — skip if a matching proposal already exists (status = proposed or applied)
   - Create an improvement note at `resources/improvement-YYYY-MM-DD-NNN.md` using the improvement template (`templates/improvement.md`)
   - Set `status: proposed`, assign `risk_level` and `target_layer`
   - Include a concrete suggested change (diff, new hook JSON, or new instruction text)
   - Set `related` field to link to the journal entries that informed the proposal
   - Update `resources/_index.md`, `_tags.md`, `_graph.md`

4. **Present summary** to user, sorted by risk (low → high):
   - For each proposal: title, friction type, target file, risk level, one-line description
   - Low-risk (Project layer): mark as "建議快速套用"
   - High-risk (Global layer): mark as "需詳細審核"

5. **Risk classification:**
   - **low**: New `.claude/commands/` slash command
   - **medium**: Modify vault `CLAUDE.md`, add project-level configuration
   - **high**: Modify `~/.claude/settings.json` or `~/.claude/CLAUDE.md` (affects all projects)

If no improvements are found, report: "目前配置運作良好，沒有待處理的改善建議"

6. **Combo: Offer immediate apply** — After presenting the summary, ask: "要立即套用嗎？" If user agrees, enter Apply Mode inline (skip re-reading proposals, go straight to selection and diff preview). This eliminates the need for a separate `/improve apply` invocation.

## Apply Mode (`apply`)

When invoked with `apply`:

1. Read all `resources/improvement-*.md` notes with `status: proposed`
2. If none found, report: "���有建議已處理"
3. List pending proposals for user to choose from
4. For the selected proposal, show diff preview (before vs after)
5. If `target_layer: global`, warn: "此變更影響所有專案（Global layer）"
6. Ask user to confirm

**On confirmation:**
- **Project layer** files (`.claude/commands/*.md`, vault `CLAUDE.md`):
  - Apply the change
  - Git commit: `chore(config): apply improvement - <title>`
- **Global layer** files (`~/.claude/settings.json`, `~/.claude/CLAUDE.md`):
  - Copy original to `.bak` backup (e.g., `settings.json.bak.YYYY-MM-DD`)
  - For `settings.json`: parse JSON to validate syntax BEFORE applying; abort if invalid
  - Apply the change
- Update the improvement note: set `status: applied`, set `updated` to today, add applied date and target file path to the Application Record section

**On rejection:**
- Update note `status: rejected`, record reason if user provides one

## Status Mode (`status`)

When invoked with `status`:

1. Read all `resources/improvement-*.md` notes
2. Group by status and display:
   - **Proposed**: count + list of titles with risk levels
   - **Applied**: count + recent applications with dates
   - **Rejected**: count
3. If any proposed improvements are older than 30 days, show: "有 N 個建議超過 30 天未處理，建議審核或清理"
4. If no improvement notes exist: "尚無改善記錄，使用 `/improve` 開始分析"

$ARGUMENTS
