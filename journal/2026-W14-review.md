---
title: "Weekly Review 2026-W14"
type: journal
tags: [weekly-review, daily, log, knowledge-management]
created: "2026-03-30"
updated: "2026-04-03"
status: active
maturity: mature
domain: knowledge-management
summary: "Vault 從零到 Grade A 99% 的三日旅程 — 48 notes, 7 plans, 12-agent parallel sessions, 知識複利迴路首次閉合"
related:
  - "[[dev-vault-status]]"
  - "[[tech-research-squad]]"
  - "[[claude-session-manager]]"
  - "[[claude-code-dev-tools]]"
---

# Weekly Review 2026-W14

> 2026-03-28 (Sat) ~ 2026-03-30 (Mon) — Vault 創建後首週（3 日）

## Highlights

This vault went from empty directory to **Grade A 99% health | 48 notes | 299 links | 0 orphans** in just three days. The compound engineering knowledge loop achieved first closure, and a 12-agent parallel session pattern emerged as a highly effective deep-work mode.

---

## Completed

### Day 1 — 2026-03-28 (Sat): Vault Bootstrap

- Built Obsidian vault from scratch using obsidian-agent CLI with PARA structure
- Fixed 2 Windows compatibility bugs in obsidian-agent (path separator in `vault.write`, CRLF in `vault.read`)
- Created 5 core linked notes: CSM project overview, architecture, design decisions, roadmap, area
- Added 5 machine-specific notes: hardware specs, dev environment, AI stack, AI coding tools, project layout
- Added 3 more notes: all projects catalog (20 projects inventoried), Claude Code configuration (11 plugins, 2 hooks), Git/GitHub identity
- Added 4 open-source developer notes: identity, publishing workflow, GitHub repo list, quality standards
- Initialized vault as Git repo, pushed to github.com/sooneocean/dev-vault (public)
- GitHub account inventory: 35 repos (22 public), primary languages TypeScript/Python

### Day 2 — 2026-03-29 (Sun): Compound Engineering + Knowledge Loop Closure

- Set up Telegram bot @maindexlong_bot with pairing and allowlist
- Installed Compound Engineering Plugin (Every Inc) — agents expanded from 5 to 52, gained `/ce:ideate`, `/ce:brainstorm`, `/ce:plan`, `/ce:work`, `/ce:review`, `/ce:compound` workflows, plus context7 MCP server
- Upgraded obsidian-agent v0.6.1 to v0.7.0 — PR #1 submitted to redredchen01/obsidian-agent
  - +6 commands (stale, cluster, digest, thread, suggest, context)
  - Full cross-platform support, backlinks bug fix, tests 100 to 147, MCP tools 19 to 25
- **Plan 001** (completed): `/improve` slash command — workflow self-iteration mechanism
- **Plan 002** (completed): session-stop wrapper script + sync hook + `/bridge-compound` + `/bridge-plan` slash commands — knowledge loop closure
- First complete knowledge cycle: `/ce:compound` -> `/bridge-compound` -> vault resource note
- `/improve` first cycle: 2 proposed, 2 applied (CLAUDE.md v0.7.0 CLI reference + docs/ directory)
- Added combo flow and journal Friction section for faster iteration
- Researched chenglou/pretext (no-DOM text measurement engine), full tech note in vault
- Plans 003 (auto LLM tech research pipeline, 11 units/4 phases) and 005 (local LLM infrastructure, 3 units/3 phases) created and split from original combined plan

### Day 3 — 2026-03-30 (Mon): Schema Upgrade + Deep Research + Multi-Plan Execution

- **Plan 004** (completed): Vault knowledge framework structural upgrade
  - CONVENTIONS.md: added subtype (7 kinds), maturity, domain, relation_map, tag naming rules
  - 7 templates updated with defaults (avoiding CLI placeholder residue)
  - Tag consolidation: 68 to 23 tags, singletons from 72% down to 22%
  - 31 notes migrated to new schema (direct file editing due to CLI updateNote limitation)
  - Source code verification: `"[[note]]:extends"` format breaks CLI parser (vault.mjs:69), adopted separate `relation_map` field
  - Document review (4 agents: coherence + feasibility + scope-guardian + adversarial), 6 auto-fixes
- **Four-discipline deep research** (12-agent parallel session):
  - Prompt Engineering: 51 to 584 lines — Claude 4.x literal execution; CLAUDE.md optimization +5-11%; well-prompted Sonnet > poorly-prompted Opus
  - Context Engineering: 370 lines — already mature, no changes needed
  - Harness Engineering: 136 to 813 lines — 22 hook events, 14 plugin context overhead analysis, 19 anti-patterns
  - Compound Engineering: 65 to 689 lines — six-stage knowledge loop, 7 plans quality evolution data, measurement framework
- **Plan 003 Phase 2** (completed, 7/11 units): 5-dimension LLM-as-Judge evaluation framework + Docker PoC verification + Writer upgrade, 39 tests all pass
- **Plan 005 Phase 2** (completed, 2/3 units): OllamaClaude MCP 11 to 15 tools (+classify/summarize/translate/route_info), 5-dimension task routing decision matrix, E2E tests pass
- **Plan 006** (completed): Knowledge system unification — Obsidian as canonical store, auto-memory migrated to pointer-only, claude-mem as read complement
- **CSM project**: auto-compact regression bug fixed (234/234 tests pass), MCP project-switcher spec (S0-S3) committed, evaluation report produced
- `/improve` detected 3 proposals, applied 2 (AGENT.md + CONVENTIONS.md CLI reference)
- CLAUDE.md prompt research applied: identity declaration + priority signals + CLI-first reinforcement
- 5 idea notes captured (cli-update-fields-flag, cluster-subtype-domain, relation-map-consumer, etc.)
- Local LLM deployment: 4 models (bge-m3 1.2GB, phi4-mini 2.5GB 19.7 tok/s, qwen3.5:9b 6.6GB 3.8 tok/s, qwen3.5:35b-a3b ~20GB 1.6 tok/s experimental)

---

## Plans Summary

| Plan | Title | Status | Key Metric |
|------|-------|--------|------------|
| 001 | Workflow self-iteration (`/improve`) | **Completed** | 2 cycles run, 4 proposals applied |
| 002 | Obsidian-agent efficiency + knowledge loop | **Completed** | session-stop + sync + bridge commands |
| 003 | Auto LLM tech research pipeline | Phase 2 done (7/11 units) | 39 tests, Docker PoC verified |
| 004 | Vault knowledge framework upgrade | **Completed** | 31 notes migrated, 68->23 tags |
| 005 | Local LLM infrastructure | Phase 2 done (2/3 units) | 4 models, 15 MCP tools |
| 006 | Knowledge system unification | **Completed** | 3 systems -> 1 canonical store |

---

## Issues / Friction

- obsidian-agent CLI `updateNote()` can only update existing keys, cannot INSERT new frontmatter fields — forced manual file editing for schema migration
- obsidian-agent CLI template engine only replaces 5 known keys; new field `{{PLACEHOLDER}}` values persist — templates needed defaults instead
- `obsidian-agent journal` uses UTC timezone, producing yesterday's journal after local midnight
- `relation_map` has no CLI consumer — semantic information lives only in frontmatter, invisible to graph tools
- session-stop hook writes too many raw fragments to journal, requiring manual cleanup
- Disk space warning on Day 1: only ~49GB free on 1.83TB drive

---

## Ideas

- obsidian-agent `research` command could add `--update` mode to diff against prior scans
- pretext engine could be used for CSM TUI text layout optimization
- session-stop hook journal writes should use append-only concise format to avoid fragmentation
- 12-agent parallel mode is highly effective — should be documented as a standard "deep push" work pattern
- `/improve` combo flow (analyze + immediate apply) significantly reduces friction

---

## Updated Notes

| File | Type | Summary |
|------|------|---------|
| [[dev-vault-status]] | project | Vault health A 99%, 48 notes, 299 links |
| [[tech-research-squad]] | project | Four-discipline research framework active |
| [[claude-session-manager]] | project | Auto-compact bug fixed, MCP spec committed |
| [[claude-code-dev-tools]] | area | Claude Code ecosystem tooling collection |
| [[prompt-engineering-research]] | resource | 51 to 584 lines, Claude-specific techniques |
| [[harness-engineering-research]] | resource | 136 to 813 lines, 22 hook events mapped |
| [[compound-engineering-research]] | resource | 65 to 689 lines, six-stage loop anatomy |
| [[context-engineering-research]] | resource | 370 lines, mature baseline established |
| [[local-llm-deployment]] | resource | 4 models benchmarked on RTX 4090 Laptop |
| [[local-llm-task-routing]] | resource | 5-dimension routing decision matrix |
| [[claude-code-configuration]] | resource | 14 plugins, hooks, MCP servers documented |
| [[compound-engineering-plugin]] | resource | CE plugin capabilities and workflow |
| [[toolchain-reference]] | resource | External repos, tools, plugins, config paths |
| [[architecture-lessons]] | resource | Stop hooks, global config safety lessons |
| [[benchmark-first-rule]] | resource | Always benchmark first — estimates were 5-10x off |

---

## Active Projects

- [[claude-session-manager]] — Python TUI dashboard for multi-session Claude Code management. Next: MCP Phase 1 (ProjectManager)
- [[dev-vault-status]] — Obsidian PARA vault with self-iteration workflow. Grade A 99% health achieved
- [[tech-research-squad]] — Four-discipline research framework (Prompt / Context / Harness / Compound Engineering)
- [[csm-feature-roadmap]] — CSM version roadmap and future feature planning

---

## Next Week

- [ ] CSM MCP Phase 1 implementation (ProjectManager — evaluation report recommendation #2)
- [ ] Plan 003 Phase 3: Units 8-11 (knowledge layer + closed loop)
- [ ] Plan 005 Phase 3: quality verification + cost tracking
- [ ] obsidian-agent PR #1 follow-up (OPEN/MERGEABLE, awaiting upstream review)
- [ ] Consider `/improve` proposal: OA_TIMEZONE setting (high risk, requires manual review)
- [ ] Restore CSM development momentum (suggest flagged as low)
- [ ] Deep dive: Prompt Engineering — CLAUDE.md best practices
- [ ] Deep dive: Context Engineering — compaction and memory strategies

---

## Reflection

This vault's first 72 hours demonstrated the power of compound engineering at an extreme pace. Starting from an empty directory on Saturday, the system reached 48 notes with 299 bidirectional links and zero orphans by Monday — a testament to the obsidian-agent CLI + PARA structure combination.

Key patterns that emerged:

1. **Knowledge loop closure** was the pivotal moment (Day 2). Once `brainstorm -> plan -> work -> compound -> bridge -> vault` formed a complete cycle, every subsequent session automatically enriched the knowledge base. This is the compound engineering thesis validated in practice.

2. **12-agent parallel sessions** (Day 3) proved to be a transformative work pattern. Four research disciplines and two plan phases were advanced simultaneously, with subagent isolation preventing context pollution. The vault went from 30 to 48 notes in a single session.

3. **Schema evolution under load** (Plan 004) showed that structural upgrades are best done early. Migrating 31 notes on Day 3 was manageable; at 200+ notes it would have been painful. The friction exposed (CLI limitations, tag fragmentation) was caught at the right scale.

4. **Local LLM reality check**: the 35B model at 1.6 tok/s with empty responses proved that benchmarking before planning is non-negotiable. The 9B model at 3.8 tok/s and phi4-mini at 19.7 tok/s are the practical workhorses on 16GB VRAM.

The velocity is unsustainable long-term — this was a sprint to establish foundations. Next week should shift from infrastructure buildout to steady-state usage: CSM development, research pipeline automation, and letting the compound loop run at a natural cadence.

---
< [[2026-03-30]] | [[2026-W14-review]] >
