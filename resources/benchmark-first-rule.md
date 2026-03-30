---
title: "Benchmark First Rule"
type: resource
subtype: "learning"
tags: [knowledge-management, auto-memory-migration, local-llm]
created: "2026-03-30"
updated: "2026-03-30"
status: active
maturity: mature
domain: "ai-engineering"
summary: "Always benchmark before planning — local LLM estimates were 5-10x off from reality"
source: ""
related: ["[[dev-vault-status]]", "[[architecture-lessons]]", "[[context-engineering-hygiene]]", "[[toolchain-reference]]", "[[claude-agent-sdk-api]]"]
relation_map: ""
---

# Benchmark First Rule

## Overview

Never trust model card estimates for VRAM and speed on specific hardware. Benchmark first, plan second. This rule emerged from Plan 005 where estimates were 5-10x off from reality.

## Key Points

### The Incident

Plan 005 initially assumed Qwen 3.5 9B would use ~6GB VRAM at 60-80 tok/s. Actual measurement: 13GB VRAM, 3.8 tok/s (due to thinking mode). This invalidated the entire model strategy. The 35B model was similarly unusable (0.9-1.8 tok/s).

### Rules for Local Model Deployment

1. Pull models and run benchmark BEFORE writing detailed implementation units
2. Treat model card numbers as upper bounds, not expected values
3. Watch for "thinking models" (Qwen 3.5, DeepSeek-R1) that have hidden token overhead
4. VRAM estimates from HuggingFace/Ollama are for raw weights — actual usage includes KV cache, thinking overhead, system baseline

### General Principle

For any plan involving hardware-dependent performance claims, validate assumptions with real measurements before committing to an implementation strategy. The cost of a 30-minute benchmark is far less than reworking a multi-unit plan.

## Notes

## Related

