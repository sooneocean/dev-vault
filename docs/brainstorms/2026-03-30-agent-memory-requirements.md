---
date: 2026-03-30
topic: agent-memory-system
---

# Agent Memory System: Query Memory Integration

## Problem Frame

Claude Code subagents (scanners, evaluators, writers, orchestrators) currently lose context and learnings between sessions and runs. Each agent starts fresh, unable to:

- Retain evaluation feedback or human verdicts across runs
- Learn from prior discoveries to avoid re-evaluating similar tools
- Share findings or context with other agents
- Build institutional knowledge about recurring problems or patterns

This forces redundant work, prevents learning across time, and misses opportunities for agents to improve themselves or each other. A persistent, queryable agent memory would enable knowledge accumulation and more intelligent agent behavior over time.

## Requirements

**Core Memory Storage & Retrieval**
- R1. Agents can store arbitrary JSON documents (tool evals, scan results, feedback, logs) into a persistent memory store
- R2. Agents can query memory by semantic search (LLM-powered text similarity) with configurable result limits
- R3. Agents can filter memory by metadata tags (e.g., `source:github`, `verdict:poc_candidate`, `timestamp:2026-03-30`, `agent_id:evaluator`)
- R4. Memory is not session-scoped; persists across Claude Code sessions and agent runs indefinitely (with optional expiry)

**Integration Points**
- R5. Memory system exposed as an **MCP server** for first-class Claude Code integration (agents use standard MCP Read/Search tools)
- R6. Memory system exposed as an **HTTP REST API** for agents outside Claude Code (webhook callbacks, external LLMs, cross-platform agents)
- R7. Agents can configure memory endpoint via environment variables (`AGENT_MEMORY_MCP_SERVER`, `AGENT_MEMORY_API_URL`) or via `.claude/settings.json` hooks

**Data Source: Query Memory**
- R8. Use Query Memory (`https://www.querymemory.com/`) as the **data layer** for document storage, embeddings, and retrieval
- R9. Implement a **custom agent memory abstraction** on top of Query Memory (Python client wrapping Query Memory API with agent-specific semantics: metadata, expiry, agent-scoped partitioning)
- R10. If Query Memory is unavailable or cost-prohibitive, system should gracefully degrade to local vector store (existing `knowledge/vector_store.py`)

**Agent-Specific Capabilities**
- R11. Each agent can scope its queries to its own agent ID (e.g., `agent:evaluator` sees only evaluator memory, or cross-agent=true for shared memory)
- R12. Memory supports agent-provided context injection: agents can add preambles ("I'm the evaluator, I'm processing tool X") to improve search relevance
- R13. Memory tracks **temporal relationships**: agents can query "discoveries about RAG tools from the last 7 days" or "all human verdicts on agents since 2026-03-01"

**Training Data Integration**
- R14. Human verdicts and feedback (from `/research apply` or manual override) are automatically stored as training data in memory
- R15. The DSPy optimizer (`self_improve/optimizer.py`) can index memory to retrieve past evaluation examples for prompt optimization

**Success Criteria**
- Agents in the research pipeline (scanner, evaluator, writer) successfully query memory across 3+ runs without losing prior context
- Agents produce more accurate evaluations by learning from prior feedback (baseline: optimizer reaches 80%+ accuracy on evaluation verdicts)
- New agents onboarded to the system can access shared knowledge without custom integration code (MCP server + env var is sufficient)
- System remains responsive under 10,000+ document memory size (sub-1s query latency)

## Scope Boundaries

**Non-goals (explicitly out of scope)**
- Real-time synchronization across multiple running agents (eventual consistency is acceptable)
- Full-text search or advanced query DSL (semantic search + metadata filters are sufficient)
- Compliance/auditing features (e.g., data retention policies, access logs, immutable records)
- GraphQL or other query language (REST API + semantic search satisfy requirements)

## Key Decisions

**Why Query Memory?**
Query Memory provides out-of-the-box document management, embeddings, and retrieval without building a full RAG pipeline. The managed service reduces operational burden. Falls back gracefully to local vector store if needed.

**Why both MCP and HTTP?**
MCP is the native integration for Claude Code subagents (maximum expressiveness). HTTP API enables agents spawned outside Claude Code, external services, and webhook-driven updates. Dual interface maximizes reach without forcing agents to implement their own HTTP clients.

**Why agent-scoped partitioning?**
Prevents information leakage and allows agents to query both their own memory (focused) and shared memory (learning). Simpler than ACLs, sufficient for this scope.

**Why defer full ACL/RBAC?**
Agents are trusted in this context (all running from the same codebase/Claude Code). Access control adds complexity; metadata scoping is simpler and sufficient for MVP.

## Dependencies / Assumptions

- Query Memory API is available and stable (or graceful fallback to local vector store works)
- Agents can be configured with environment variables or `.claude/settings.json` (already supported)
- Existing `knowledge/` module and `self_improve/` integration can be extended without major refactoring
- Claude Agent SDK allows agents to call MCP servers (already supported)

## Outstanding Questions

### Resolved
- **Memory Mutability**: Append-only (immutable). New feedback creates new entries; history is preserved.
- **Data Retention**: Keep everything indefinitely. No auto-expiry. Agents can filter by recency in queries.
- **Cost Model**: Hybrid (Query Memory primary + local vector store fallback). Maximizes resilience and cost control.

### Deferred to Planning
- [Technical] How to handle **authentication** between Claude Code and Query Memory (API keys, tokens)?
- [Technical] What **metadata schema** do we define (tags, agent_id, source, timestamp, verdict, etc.)? Full design in planning.
- [Technical] How to **partition memory** when agents share knowledge (e.g., evaluator stores findings, scanner uses them)? Design the scoping logic in planning.
- [Needs research] What is Query Memory's **query latency** and **embedding quality** under our expected load (10K+ docs)? Benchmark before committing.

## Next Steps

→ **Resolve the three "Resolve Before Planning" questions** above, then proceed to `/ce:plan` for implementation architecture and phasing.
