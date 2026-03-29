---
title: "relation-map-graph-consumer"
type: idea
tags: [obsidian-agent, relation-map, graph-visualization]
created: "2026-03-29"
updated: "2026-03-29"
status: draft
maturity: seed
domain: knowledge-management
summary: "Build MCP tool or slash command to consume relation_map data and render typed graph visualization"
related: ["[[cluster-subtype-domain-dimensions]]"]
relation_map: "cluster-subtype-domain-dimensions:extends"
---

# relation-map-graph-consumer

## The Idea

Build an MCP tool or slash command (e.g., `/graph --typed`) that reads `relation_map` fields from all vault notes and renders a typed relationship graph. Unlike the current `_graph.md` which only shows undirected `related` links, this would display edge labels (`extends`, `depends-on`, `implements`, `documents`, `supersedes`) and support filtering by relation type.

## Why

The `relation_map` field was introduced in Plan 004 but currently has no consumer — the semantic information sits in frontmatter without any tooling to visualize or query it. The current `_graph.md` and `obsidian-agent` graph views treat all relationships as equivalent. Typed edges would reveal dependency chains, implementation paths, and knowledge evolution arcs that are invisible today.

## Next Steps

- [ ] Design output format: Mermaid diagram with labeled edges, or interactive HTML, or enhanced `_graph.md`
- [ ] Implement a `relation_map` parser that reads all notes and builds a typed adjacency list
- [ ] Create `/graph --typed` slash command or MCP tool `typed-graph`
- [ ] Consider integration with Obsidian's graph view (custom CSS for edge types)
