---
title: "Dev Vault Status"
type: project
tags: [knowledge-management, auto-memory-migration, project, active]
created: "2026-03-30"
updated: "2026-04-03"
status: active
maturity: growing
domain: "knowledge-management"
summary: "Obsidian PARA vault with self-iteration workflow, current progress and pending work"
goal: "Build an open-source developer knowledge base (PARA structure) with continuous self-iteration loop: /improve → analyze → propose → apply → learn"
deadline: ""
related: ["[[compound-engineering-research]]", "[[2026-03-30]]", "[[architecture-lessons]]", "[[context-engineering-hygiene]]", "[[benchmark-first-rule]]", "[[toolchain-reference]]", "[[claude-agent-sdk-api]]", "[[claude-session-manager]]"]
relation_map: ""
---

# Dev Vault Status

## Goal

Open-source developer knowledge base (PARA structure) with self-iteration workflow for continuous improvement.

**Repo**: github.com/sooneocean/dev-vault (master branch)
**Structure**: PARA (areas/projects/resources/journal/ideas) + docs/plans/ + docs/solutions/

## Progress

| Date | Update |
|------|--------|
| 2026-03-29 | /improve slash command: analyze → propose → apply self-iteration loop (with combo flow) |
| 2026-03-29 | Improvement template + journal Friction section for structured signal collection |
| 2026-03-29 | session-stop wrapper script + sync hook for auto journal writing |
| 2026-03-29 | /bridge-compound and /bridge-plan slash commands for knowledge loop closure |
| 2026-03-29 | Compound Engineering Plugin installed (52 agents, context7 MCP) |
| 2026-03-29 | obsidian-agent upgraded to v0.7.0 (6 new commands, cross-platform) |
| 2026-03-29 | session-wrap-skill v3.5 installed globally |
| 2026-03-29 | First complete /improve cycle: 2 proposals → 2 applied → committed |
| 2026-03-29 | Knowledge compound loop first closure: /ce:compound → bridge → vault |

## TODO

- [ ] CSM (Claude Session Manager): flagged low momentum, needs development push
- [ ] obsidian-agent PR #1: OPEN/MERGEABLE at redredchen01/obsidian-agent, waiting upstream review
- [ ] Deep research: Prompt Engineering best practices
- [ ] Plan 003: LLM research pipeline (11 units, 4 phases) — cleaned, local LLM content split out
- [ ] Plan 005: Local LLM infrastructure (3 units, 3 phases) — benchmark complete, plan needs update
- [ ] WordPress YOLO LAB: connected via Chrome DevTools MCP, explored admin
- [ ] Fix garbled char in .claude/commands/improve.md encoding

## Notes

### Local LLM Deployment Status

4 models deployed: bge-m3, phi4-mini, qwen3.5:9b, qwen3.5:35b-a3b

**Critical finding**: Qwen 3.5 thinking mode causes 9B to run at only 3.8 tok/s (expected 60-80) with 13GB VRAM (expected 6GB). Phi-4 Mini became the interactive workhorse (19.7 tok/s), Qwen 9B demoted to batch use.

OllamaClaude MCP: installed + patched (path fix + model change), project-level config. LiteLLM Proxy removed (unnecessary).

Hardware corrections: disk 491GB (not 49GB), Ollama 0.18.3 (not 0.17.0).

