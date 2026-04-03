---
title: "pretext-csm-tui-layout"
type: idea
tags: [pretext, tui, text-layout, brainstorm, future, ai-engineering]
created: "2026-03-29"
updated: "2026-04-03"
status: draft
maturity: seed
domain: project-specific
summary: "Use pretext engine for CSM TUI text measurement and layout optimization"
related: ["[[pretext-無-dom-文字測量引擎]]", "[[claude-session-manager]]", "[[csm-feature-roadmap]]", "[[csm-architecture]]", "[[csm-key-design-decisions]]"]
relation_map: "pretext-無-dom-文字測量引擎:depends-on, claude-session-manager:extends"
---

# pretext-csm-tui-layout

## The Idea

Integrate chenglou/pretext (a DOM-free text measurement engine) into CSM's TUI layer. Pretext provides precise text width calculation, line breaking, and layout without requiring a browser DOM — ideal for terminal UIs where accurate text positioning is needed for session panels, log views, and status displays.

## Why

TUI frameworks like Ink (React-based) or Blessed handle basic layouts but struggle with accurate CJK text width, mixed-script line breaking, and dynamic resize. Pretext was designed specifically for this problem — zero-DOM, fast, and supports Unicode width tables. CSM's TUI could benefit from better text wrapping in session logs and more predictable panel sizing.

## Next Steps

- [ ] Review pretext API surface and determine integration points (line-breaking, width measurement)
- [ ] Evaluate compatibility with CSM's chosen TUI framework (Ink / Blessed / raw ANSI)
- [ ] Build a minimal proof-of-concept: render a CSM session log panel using pretext for layout
- [ ] Benchmark pretext vs. current TUI text handling for CJK-heavy content
