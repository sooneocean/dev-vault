---
title: Steps
type: project
tags: [project, active]
created: 2026-04-03
updated: 2026-04-03
status: active
maturity: growing
domain: knowledge-management
summary: ""
---

Estimate cost savings from local LLM usage vs Claude API.

## Steps

1. **Read benchmark data:**
   - `projects/tools/local-llm/model-inventory.md` — model performance data

2. **Estimate per-task costs:**

| Task | Local Model | Local Cost | Claude API Cost (est.) |
|------|------------|------------|----------------------|
| Embedding (per 1K tokens) | BGE-M3 | $0.00 | ~$0.0001 (API) |
| Classification (per call) | Phi-4 Mini | $0.00 | ~$0.003 (Haiku) |
| Summarization (per call) | Qwen 3.5 9B | $0.00 | ~$0.01 (Sonnet) |
| Translation (per call) | Qwen 3.5 9B | $0.00 | ~$0.01 (Sonnet) |
| Code Review | Claude Opus | N/A | ~$0.15 (Opus) |
| Architecture Design | Claude Opus | N/A | ~$0.30 (Opus) |

3. **Present 70/30 split estimate:**
   - 70% tasks local → $0/month
   - 30% tasks Claude API → estimated based on usage
   - Electricity cost: RTX 4090 Laptop ~150W under load, ~$5-10/month

4. **Note:** These are estimates. Actual savings depend on usage volume.
   Track real usage over 2-4 weeks before drawing conclusions.
