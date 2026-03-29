---
title: "cluster-subtype-domain-dimensions"
type: idea
tags: [obsidian-agent, clustering]
created: "2026-03-29"
updated: "2026-03-29"
status: draft
maturity: seed
domain: knowledge-management
summary: "Enhance obsidian-agent cluster algorithm to use subtype and domain as clustering dimensions alongside tags and related links"
related: ["[[2026-03-30]]", "[[relation-map-graph-consumer]]"]
relation_map: "relation-map-graph-consumer:extends"
---

# cluster-subtype-domain-dimensions

## The Idea

Enhance the `obsidian-agent cluster` algorithm to consider `subtype` and `domain` frontmatter fields as clustering dimensions, in addition to the current `tags` and `related` links. Notes sharing the same domain (e.g., `ai-engineering`) or subtype (e.g., `research`) would receive higher affinity scores, leading to more meaningful topic clusters.

## Why

Currently, `cluster` produces a single mega-cluster because `related` links form a fully connected graph. Adding orthogonal dimensions (domain, subtype) would break the connectivity and reveal real topic boundaries. After the Plan 004 schema upgrade, every note now has `domain` and most resources have `subtype` — this data is available but unused by the clustering logic.

## Next Steps

- [ ] Read `obsidian-agent` cluster implementation to understand current affinity scoring
- [ ] Design weighted scoring: how much weight for domain match vs. tag overlap vs. related link
- [ ] Prototype with current vault data and compare cluster output before/after
- [ ] Open issue or PR on `redredchen01/obsidian-agent`
