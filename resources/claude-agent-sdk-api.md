---
title: "Claude Agent SDK API"
type: resource
subtype: "reference"
tags: [knowledge-management, auto-memory-migration, claude-agent-sdk]
created: "2026-03-30"
updated: "2026-03-30"
status: active
maturity: growing
domain: "ai-engineering"
summary: "Verified API shape for claude-agent-sdk v0.1.52 — AgentDefinition, subagent dispatch, MCP inheritance, Windows compatibility"
source: ""
related: ["[[dev-vault-status]]", "[[architecture-lessons]]", "[[benchmark-first-rule]]", "[[context-engineering-hygiene]]", "[[toolchain-reference]]"]
relation_map: ""
---

# Claude Agent SDK API

## Overview

Verified API reference for claude-agent-sdk v0.1.52 (PyPI). NOT claude-code-sdk (older, no subagent support).

## Key Points

### Core API

- `AgentDefinition(description, prompt, tools, model, mcpServers, maxTurns, ...)`
- `ClaudeAgentOptions(agents={'name': AgentDefinition(...)}, permission_mode='bypassPermissions')`
- `query(prompt, options)` — async generator, stateless
- `ClaudeSDKClient(options)` — stateful, bidirectional

### MCP in Subagents

- **By name:** `mcpServers=['context7']` (inherit from parent)
- **Inline:** `mcpServers=[{'my-server': {'command': 'uvx', 'args': ['pkg']}}]`
- **In-process:** `create_sdk_mcp_server()` + `@tool` decorator

### Windows Compatibility

- Agent defs sent via stdin initialize request (NOT command line) — bypasses 32K limit
- SDK bundles claude.exe 227MB at `_bundled/claude.exe`
- Long system prompts: use file-based `SystemPromptFile` instead of inline

### Hooks

- `SubagentStart`: `{session_id, agent_id, agent_type}`
- `SubagentStop`: `{session_id, agent_id, agent_transcript_path}`

## Notes

## Related

