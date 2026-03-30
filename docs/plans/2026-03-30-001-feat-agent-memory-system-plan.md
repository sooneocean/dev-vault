---
title: Agent Memory System with Query Memory Integration
type: feat
status: active
date: 2026-03-30
origin: docs/brainstorms/2026-03-30-agent-memory-requirements.md
---

# Agent Memory System: Query Memory Integration

## Overview

Implement a persistent, cross-session memory system for Claude Code subagents, backed by Query Memory as the primary data layer with graceful local fallback. Agents (scanner, evaluator, writer, orchestrator, integrator) will retain evaluation feedback, tool verdicts, and learnings across runs, enabling continuous improvement and reduced redundant work.

**Key Architecture**: Query Memory API → Python client abstraction → MCP server + HTTP API → agent consumption (research pipeline first, extensible to all agents)

**Migration Strategy**: Gradual replacement of `knowledge/` vector store. New agent memory becomes primary; `knowledge/` becomes read-only facade for backward compatibility.

## Problem Frame

Research pipeline agents currently lose all context between runs:
- Evaluator re-evaluates similar tools, missing learned patterns
- Scanner rediscovers same projects without knowing prior verdicts
- No shared memory for agents to learn from each other's findings
- Human feedback (corrections, verdicts) is not systematically collected as training data

This prevents institutional knowledge accumulation and wastes compute on redundant evaluations. A persistent memory would enable agents to improve themselves (via DSPy optimizer) and each other (via shared findings).

## Requirements Trace

**Core Memory Capabilities**
- R1. Store arbitrary JSON documents (tool evals, scan results, feedback)
- R2. Semantic search with configurable result limits
- R3. Metadata filtering (source, verdict, timestamp, agent_id)
- R4. Cross-session persistence (indefinite retention)

**Integration Surfaces**
- R5. MCP server for first-class Claude Code integration
- R6. HTTP REST API for external/webhook access
- R7. Environment variable + settings.json configuration

**Data Layer & Fallback**
- R8. Query Memory as primary data layer
- R9. Custom Python abstraction wrapping Query Memory (metadata, scoping, fallback)
- R10. Graceful fallback to local vector store if Query Memory unavailable

**Agent Capabilities**
- R11. Agent-scoped query capability (own memory vs. shared memory)
- R12. Context injection (agent-provided preambles for search relevance)
- R13. Temporal filtering (query discoveries from last 7 days, verdicts since date)

**Training Data Integration**
- R14. Automatic capture of human verdicts as training examples
- R15. DSPy optimizer can index memory for prompt optimization

**Success Criteria**
- Research pipeline agents query memory across 3+ runs without losing context
- Evaluator accuracy reaches ≥80% baseline using learned feedback
- New agents onboarded without custom code (MCP server + env var sufficient)
- System latency < 1s for queries against 10K+ documents

## Scope Boundaries

**Non-goals**
- Real-time synchronization across multiple concurrent agents (eventual consistency acceptable)
- Full-text search or DSL (semantic + metadata filtering sufficient)
- Compliance/audit features (data retention policies, access logs)
- GraphQL or advanced query languages

## Context & Research

### Relevant Code and Patterns

**Existing Vector Store (to be preserved for compatibility)**
- `knowledge/vector_store.py` — LanceDB local store with BGE-M3 embedding via Ollama
  - Functions: `_get_embedding()`, `_chunk_markdown()`, `index_note()`, `search()`
  - Data flow: Frontmatter extraction → section-level chunking → embedding → LanceDB upsert
- `knowledge/indexer.py` — Trigger-based indexing after vault note writes
  - Hook-based design, currently unused but architecturally ready
  - Could become read-only adapter in new system

**Evaluator & Training Data (will be extended)**
- `evaluator.py` — `EvaluationResult` model with `EvaluationScore` dimensions
  - Rubric: 5D for repos (Relevance | Maturity | Effort | Risk | Value), 3D for papers
  - Verdict logic: `>= 70%` → poc_candidate, `>= 50%` → watching, `< 50%` → not_applicable
  - Sanitization: `sanitizer.py` for prompt injection prevention
- `self_improve/optimizer.py` — DSPy-based prompt optimization with versioning
  - `record_human_verdict()` appends to `state/training/verdict-overrides.jsonl`
  - `collect_training_data()` reads JSONL for training examples
  - `optimize_evaluator(strategy="bootstrap" | "mipro")` for ≥10 or ≥30 examples
  - Version management: `prompts/versions/{strategy-timestamp}/`, rollback via `latest.json`
- `self_improve/experience.py` — Run metrics recording (Markdown + JSON)
  - `record_run()` populates `state/experience-metrics.json` for training context

**Agent Orchestration Pattern (model for new system)**
- `orchestrator.py` — Subagent coordination via `claude_agent_sdk`
  - AgentDefinition pattern: description, prompt, tools, model, mcpServers, maxTurns
  - Query pattern: `ClaudeAgentOptions(agents={...}, permission_mode="bypassPermissions")`
  - State checkpoint: `PipelineRunState` saved to `run-{run_id}.json` for resume
  - POSIX path conversion (`_posix_path()`) for Windows → Git Bash compatibility
- `integrator.py` — Risk-based proposal generation
  - `assess_candidates()` pattern: reads current state (settings.json) → LLM evaluation → proposals

**MCP Server Configuration (model for new system)**
- `.mcp.json` — Server definitions (arxiv, huggingface, fetch)
- Agent definitions pass `mcpServers=[MCP_SERVERS["name"]]` to activate

### Institutional Learnings

- *From `self_improve/optimizer.py`*: Append-only JSONL for training data is resilient; version management with `latest.json` pointer allows safe rollback
- *From `orchestrator.py`*: State checkpointing with `model_dump_json()` enables multi-phase pipelines with recovery
- *From `evaluator.py`*: Rubric injection at evaluation time is cleaner than hard-coded dimensions; sanitization prevents prompt injection
- *From existing knowledge/ usage*: Chunking by structural markers (headings, frontmatter) is more useful than raw text splitting

### External References

- **Query Memory API**: https://www.querymemory.com/ (documentation to be researched during Phase 2)
- **Claude Agent SDK**: Existing integration in orchestrator.py; patterns are established
- **DSPy**: Version constraints in optimizer.py (≥2.5)

## Key Technical Decisions

**Query Memory as Primary, with Local Fallback**
*Rationale*: Query Memory abstracts away embedding/chunking/search complexity. Local fallback via existing LanceDB ensures system works even if Query Memory is unavailable or cost-prohibitive. No single point of failure.

**MCP Server + HTTP API (Dual Interface)**
*Rationale*: MCP is native for Claude Code agents (type safety, standard tools). HTTP enables external services and webhook-driven updates. Both surfaces can read from same backend without duplication.

**Append-Only Memory with Indefinite Retention**
*Rationale*: Immutable history is audit-friendly and prevents accidental overwrites. Agents can filter by metadata/timestamp if they need recent data only. Simpler than delete-with-cleanup logic.

**Agent-Scoped Partitioning (No ACL)**
*Rationale*: Agents are trusted (same codebase, same Claude Code session). Metadata-based scoping (agent_id, source) is simpler than ACL. Agents can query own memory (focused) or shared memory (learning) via flag.

**Gradual Migration: knowledge/ → read-only facade**
*Rationale*: Preserves backward compatibility while building confidence in new system. Vault-indexed content (architecture, projects, resources) remains in knowledge/; agent-transient data (evaluations, verdicts) moves to agent memory.

**Metadata Schema First**
*Rationale*: Query Memory's API success depends on rich metadata. Define once (agent_id, source, verdict, timestamp, domain_tags) so agents query without surprises later.

## Implementation Units

- [ ] **Unit 1: Agent Memory Core Abstraction**

**Goal:** Implement the Python abstraction layer (`agent_memory/client.py`) that wraps Query Memory API with fallback to local vector store.

**Requirements:** R1, R2, R3, R4, R8, R9, R10

**Dependencies:** None (independent from existing code initially)

**Files:**
- Create: `projects/tools/research-pipeline/agent_memory/__init__.py`
- Create: `projects/tools/research-pipeline/agent_memory/client.py`
- Create: `projects/tools/research-pipeline/agent_memory/models.py`
- Create: `projects/tools/research-pipeline/agent_memory/fallback.py`
- Test: `projects/tools/research-pipeline/tests/test_agent_memory.py`

**Approach:**

The core abstraction will provide a unified interface regardless of backend:

```python
class AgentMemoryClient:
    """Unified memory interface: Query Memory primary, fallback to LanceDB."""

    def __init__(self, use_query_memory: bool = True, query_memory_api_key: str = None):
        """Auto-detect backend from environment variables."""
        # AGENT_MEMORY_USE_QUERY_MEMORY (env) or settings.json
        # AGENT_MEMORY_API_KEY (env)
        self.backend = QueryMemoryBackend(...) if use_query_memory else LanceDBBackend(...)

    async def store(self, document: AgentMemoryDocument) -> str:
        """Store doc. Returns doc_id for later retrieval."""
        # AgentMemoryDocument = {agent_id, source, content, metadata, timestamp}
        # Metadata: {verdict, domain_tags, related_tool_ids, run_id}
        return await self.backend.store(document)

    async def search(self, query: str, agent_id: str = None,
                     metadata_filters: dict = None, top_k: int = 10) -> list[SearchResult]:
        """Semantic search with optional agent/metadata scoping."""
        # SearchResult = {doc_id, content, metadata, relevance_score}

    async def search_temporal(self, domain: str, after_date: datetime = None) -> list[SearchResult]:
        """Query discoveries from specific date range."""
```

**Backend Implementations:**

1. **QueryMemoryBackend**
   - HTTP client: `async with httpx.AsyncClient() as client`
   - Auth: Bearer token from env/settings
   - Embedding: Query Memory handles it (no local embedding needed)
   - Fallback triggered: network error, 503, or cost-limit exceeded

2. **LanceDBBackend** (adapter from existing `knowledge/vector_store.py`)
   - Reuse `_get_embedding()` (Ollama BGE-M3)
   - Reuse `search()` for vector similarity
   - Metadata filtering in-memory post-search (slower, acceptable for fallback)

**Metadata Schema:**
```python
class AgentMemoryDocument(BaseModel):
    agent_id: str  # "evaluator", "scanner", "orchestrator"
    source: str  # "github", "arxiv", "huggingface", "evaluation", "feedback"
    content: str  # Primary data (tool description, eval result, etc.)
    metadata: dict  # {
        #   verdict: "poc_candidate" | "watching" | "not_applicable"
        #   domain_tags: ["rag", "agent-framework"]
        #   related_tool_ids: ["tool-uuid-1", ...] (cross-references)
        #   run_id: "2026-03-30-abc123"
        #   timestamp: ISO8601
        #   eval_dimensions: {relevance: 8, maturity: 6, ...}
        # }

class SearchResult(BaseModel):
    doc_id: str
    content: str
    metadata: dict
    relevance_score: float  # 0-1 for Query Memory, cosine for LanceDB
```

**Patterns to follow:**
- Async I/O throughout (consistent with claude_agent_sdk)
- Error handling: wrap Query Memory errors, auto-downgrade to fallback
- Configuration via env + settings.json (mirror orchestrator.py pattern)

**Test scenarios:**
- Happy path: Store document with metadata, search by query, retrieve with score
- Metadata filtering: Query with agent_id filter returns only that agent's memories
- Temporal filtering: Query with date range returns only docs from that window
- Fallback: Query Memory timeout → seamlessly use LanceDB
- Empty result: Search with no matches returns empty list (not error)
- Batch store: Multiple documents stored atomically or with clear error reporting

**Verification:**
- Can store and retrieve documents with full metadata round-trip
- Search returns results ranked by relevance
- Fallback activates on timeout and succeeds with LanceDB
- Filtering (agent_id, date range) produces correct subsets

---

- [ ] **Unit 2: MCP Server for Agent Memory**

**Goal:** Expose agent memory as an MCP server so Claude Code subagents can query via standard MCP tools.

**Requirements:** R5, R11, R12

**Dependencies:** Unit 1 (needs AgentMemoryClient)

**Files:**
- Create: `projects/tools/research-pipeline/agent_memory/mcp_server.py`
- Create: `projects/tools/research-pipeline/agent_memory/mcp_tools.py`
- Modify: `projects/tools/research-pipeline/config.py` (add MCP_SERVERS entry)
- Modify: `.mcp.json` (register new server)
- Test: `projects/tools/research-pipeline/tests/test_mcp_server.py`

**Approach:**

MCP server exposes three core tools:

1. **memory:store** — Agents write to memory
   - Input: {agent_id, source, content, metadata}
   - Output: {doc_id, status}

2. **memory:search** — Semantic search with optional preamble
   - Input: {query, agent_id, metadata_filters?, top_k?, context_preamble?}
   - Output: [{doc_id, content, metadata, score}, ...]

3. **memory:search_temporal** — Date-scoped search
   - Input: {domain, after_date?, before_date?}
   - Output: [{...}, ...]

MCP server lifecycle:
```bash
# In .mcp.json or settings.json
"agent-memory": {
  "command": "python",
  "args": ["-m", "agent_memory.mcp_server"],
  "type": "stdio"
}

# Agents invoke via MCP tool calls (no imports needed)
# Claude Code handles MCP marshaling automatically
```

Agent usage pattern (in evaluator.py, scanner.py, etc.):
```python
# No code change needed — agents just use MCP tool like any other
# Within agent prompt:
# "Store your findings: use memory:store tool with agent_id=evaluator, source=evaluation"
# "Search prior verdicts: use memory:search with query='RAG tools' and agent_id=evaluator"

# Claude Code MCP infrastructure handles the RPC call
```

**Context Preamble Support** (for R12):
```
memory:search(
  query="multi-agent orchestration frameworks",
  context_preamble="I am the github_scanner agent, looking for tools that fit agent-orchestration domain",
  agent_id="scanner",
  top_k=5
)
```
Preamble is prepended to query for better embedding relevance.

**Patterns to follow:**
- Tool definitions: match existing MCP style (input schema, description)
- Error handling: return structured error objects (not exceptions)
- Async I/O: use stdio-based MCP streaming

**Test scenarios:**
- Store-then-search roundtrip (doc appears in results)
- Agent-scoped query returns only that agent's docs
- Context preamble improves relevance ranking (integration test)
- Metadata filtering works (verdict, domain_tags, timestamp)
- Concurrent tool calls (multiple agents querying simultaneously)

**Verification:**
- MCP server starts without errors
- Agents can call memory:store, memory:search, memory:search_temporal tools
- Tool results are properly marshaled to MCP format
- Cross-agent queries work (scanner stores, evaluator retrieves)

---

- [ ] **Unit 3: HTTP API for External Access**

**Goal:** Expose agent memory via REST API for webhook-driven updates and non-MCP agents.

**Requirements:** R6, R7

**Dependencies:** Unit 1 (needs AgentMemoryClient)

**Files:**
- Create: `projects/tools/research-pipeline/agent_memory/http_server.py` (FastAPI)
- Modify: `config.py` (add HTTP_SERVER_PORT, AGENT_MEMORY_API_URL)
- Test: `projects/tools/research-pipeline/tests/test_http_api.py`

**Approach:**

FastAPI server on configurable port (default 8765):

```
POST /memory/store
  Input: {agent_id, source, content, metadata}
  Output: {doc_id, status}

GET /memory/search?query=...&agent_id=...&top_k=10
  Output: [{doc_id, content, metadata, score}, ...]

GET /memory/temporal?domain=...&after_date=...
  Output: [{...}, ...]

POST /memory/batch_store
  Input: {documents: [{agent_id, source, content, metadata}, ...]}
  Output: {stored: count, failed: count}
```

**Configuration** (via environment + settings.json):
```
AGENT_MEMORY_API_URL=http://localhost:8765
AGENT_MEMORY_HTTP_ENABLED=true
```

Server lifecycle:
```python
# Can be launched standalone or as task from orchestrator
# python -m agent_memory.http_server --port 8765

# Or called from orchestrator:
# if AGENT_MEMORY_HTTP_ENABLED:
#   spawn_task("agent-memory-http", ["python", "-m", "agent_memory.http_server"])
```

**Patterns to follow:**
- FastAPI dependency injection for AgentMemoryClient
- Async endpoints: `async def store(doc: AgentMemoryDocument) -> dict`
- CORS headers for webhook callbacks
- Health check endpoint: `GET /health`

**Test scenarios:**
- POST /memory/store saves document, returns doc_id
- GET /memory/search with query returns ranked results
- Filtering by agent_id, timestamp works
- Batch store: N docs stored in one request
- Webhook callback: external service sends verdict update
- Error handling: 400 for bad input, 500 for backend failure with fallback

**Verification:**
- HTTP server starts on configured port
- All endpoints return proper JSON responses
- Webhook callbacks are processed and stored

---

- [ ] **Unit 4: Agent Integration (Evaluator & Training Loop)**

**Goal:** Update evaluator and optimizer to use agent memory for feedback storage and training data retrieval.

**Requirements:** R14, R15

**Dependencies:** Unit 1 (MCP server optional but preferred)

**Files:**
- Modify: `evaluator.py` — After evaluation, store result in memory
- Modify: `self_improve/optimizer.py` — Retrieve training data from memory instead of JSONL
- Modify: `orchestrator.py` — Configure memory client on startup
- Test: `tests/test_evaluator_memory.py`, `tests/test_optimizer_memory.py`

**Approach:**

**Evaluator Integration:**
```python
# In evaluator.py, after evaluate_single() returns EvaluationResult:

async def save_evaluation_to_memory(eval_result: EvaluationResult, run_id: str):
    """Store evaluation in agent memory for future reference."""
    doc = AgentMemoryDocument(
        agent_id="evaluator",
        source="evaluation",
        content=f"{eval_result.scan_result.name}: {eval_result.scan_result.description[:500]}",
        metadata={
            "verdict": eval_result.verdict.value,
            "tool_url": eval_result.scan_result.url,
            "tool_name": eval_result.scan_result.name,
            "scores": {s.dimension: s.score for s in eval_result.scores},
            "total_score": eval_result.total_score,
            "reasoning": eval_result.recommended_action,
            "run_id": run_id,
            "domain_tags": eval_result.scan_result.tags,
        }
    )
    doc_id = await AGENT_MEMORY_CLIENT.store(doc)
    return doc_id
```

**Optimizer Integration:**
```python
# In self_improve/optimizer.py

async def collect_training_data_from_memory() -> list[dict]:
    """Retrieve human verdicts from agent memory instead of JSONL."""
    # Query memory for documents with human_verdict metadata
    results = await AGENT_MEMORY_CLIENT.search(
        query="human verdict evaluation feedback",
        agent_id="evaluator",  # Get evaluator's stored evals
        metadata_filters={"has_human_verdict": True}
    )

    training_examples = []
    for result in results:
        if "human_verdict" in result.metadata:
            training_examples.append({
                "scan_result": result.metadata.get("scan_result"),
                "eval_scores": result.metadata.get("scores", []),
                "model_verdict": result.metadata.get("verdict"),
                "human_verdict": result.metadata.get("human_verdict"),
            })
    return training_examples
```

**Verdict Recording from `/research apply`:**
```python
# When user applies human feedback via /research-apply CLI:
# Instead of appending to verdict-overrides.jsonl, call:

await AGENT_MEMORY_CLIENT.store(AgentMemoryDocument(
    agent_id="evaluator",
    source="human_feedback",
    content=f"Verdict correction for {tool_name}",
    metadata={
        "tool_name": tool_name,
        "tool_url": tool_url,
        "model_verdict": old_verdict,
        "human_verdict": new_verdict,  # Ground truth
        "reason": user_explanation,
    }
))
```

**Backward Compatibility:**
- Evaluator still writes to state/eval-results-*.json (for audit)
- Optimizer tries memory first; falls back to JSONL if memory unavailable
- No changes to JSONL format or existing checkpoint logic

**Patterns to follow:**
- Reuse `EvaluationResult` and `AgentMemoryDocument` models for consistency
- Async/await throughout (consistent with orchestrator async patterns)
- Error handling: log but don't crash if memory store fails

**Test scenarios:**
- Evaluator stores results in memory after each evaluation
- Search memory for prior evaluations of same tool → finds result
- Optimizer retrieves training examples from memory vs JSONL (equivalence test)
- Human verdict recorded → appears in optimizer training data
- Fallback: if memory unavailable, JSONL path still works

**Verification:**
- Evaluation results appear in memory with correct metadata
- Optimizer can build training set from memory
- Human verdicts flow into training loop
- JSONL fallback still functions

---

- [ ] **Unit 5: Scanner & Writer Integration**

**Goal:** Update scanners and writer to leverage agent memory for learning and avoiding redundant scans.

**Requirements:** R11, R13

**Dependencies:** Unit 1, Unit 2 (MCP server preferred)

**Files:**
- Modify: `orchestrator.py` — Pass memory context to scanner prompts
- Modify: `prompts/github_scanner.md`, `prompts/arxiv_scanner.md` — Add memory-aware instructions
- Modify: `self_improve/experience.py` — Log runs to memory instead of JSON
- Test: `tests/test_scanner_memory.py`

**Approach:**

**Scanner Memory Usage:**
```
Before scanning:
├─ Query memory: "Show me tools evaluated in the last 7 days"
├─ Get: list of {tool_name, verdict, domain_tags}
└─ Pass to scanner prompt: "Avoid re-scanning these known tools: [list]"

After scanning (scanner.md):
├─ For each discovered tool:
│  ├─ Search memory: "Does this tool exist in prior scans?"
│  ├─ If yes: compare verdicts (skip if identical)
│  └─ If no: new discovery, include in results
└─ Results include memory context: "3 new tools, 2 duplicates from 2026-03-20"
```

**Scanner Prompt Update** (prompts/github_scanner.md):
```markdown
You are searching for new agent framework and RAG tools.

KNOWN DISCOVERIES (from prior scans):
{prior_discoveries_from_memory}

IMPORTANT: Avoid re-listing tools in the KNOWN DISCOVERIES list unless they have
significantly changed stars or have newer versions.

For each new discovery, check if it's in the KNOWN list before including in results.
```

**Writer Integration:**
```python
# In run_writer_with_evaluations():
# When writing research-scan note, include memory citations

# "3 tools were known from prior scans (see linked notes)"
# Add backlinks to memory docs that evaluated them
```

**Experience Logging to Memory:**
```python
# In experience.py, instead of appending to experience-metrics.json:

async def record_run_to_memory(run_state: PipelineRunState):
    """Log run statistics to agent memory for learning."""
    doc = AgentMemoryDocument(
        agent_id="orchestrator",
        source="run_metrics",
        content=f"Pipeline run {run_state.run_id} in {run_state.mode} mode",
        metadata={
            "run_id": run_state.run_id,
            "mode": run_state.mode,
            "scan_count": len(run_state.scan_results),
            "new_count": len(run_state.new_scan_results),
            "eval_count": len(run_state.evaluation_results),
            "poc_count": sum(1 for e in run_state.evaluation_results if e.verdict == "POC_CANDIDATE"),
            "poc_success": sum(1 for p in run_state.poc_results if p.quickstart_success),
            "proposals_generated": len(run_state.proposals),
            "errors": run_state.errors,
        }
    )
    await AGENT_MEMORY_CLIENT.store(doc)
```

**Backward Compatibility:**
- Scanners continue to return results as JSON (no change to models)
- Memory context is purely advisory (scanner still scans globally)
- Writer still produces vault notes (memory docs are supplementary)

**Patterns to follow:**
- Memory queries inform, don't gate: scanner still scans even if memory unavailable
- Temporal scoping: ask memory for last N days only (avoid overwhelming scanner)

**Test scenarios:**
- Scanner retrieves prior discoveries from memory
- Known tools listed in prompt don't re-appear in results
- Run metrics logged to memory
- Temporal query: "discoveries from last 7 days" returns only recent
- Memory unavailable: scanner still works (memory context skipped)

**Verification:**
- Scanner results reference prior discoveries from memory
- Run metrics appear in memory with correct counts
- Temporal filtering works (query last 7 days ≠ all history)

---

- [ ] **Unit 6: Configuration, Tests, and Fallback Resilience**

**Goal:** Wire up configuration, test coverage, and fallback behavior to ensure system is production-ready.

**Requirements:** R7, R10, all success criteria

**Dependencies:** All prior units

**Files:**
- Modify: `config.py` — Add memory configuration
- Modify: `.mcp.json` — Register memory MCP server
- Create: `projects/tools/research-pipeline/agent_memory/config.py` — Memory-specific config
- Create: comprehensive test suite (listed below)
- Create: `docs/agent-memory-setup.md` — Operator guide

**Approach:**

**Configuration Flow:**
```python
# In config.py (main pipeline config)
AGENT_MEMORY_ENABLED = os.getenv("AGENT_MEMORY_ENABLED", "true").lower() == "true"
AGENT_MEMORY_USE_QUERY_MEMORY = os.getenv("AGENT_MEMORY_USE_QUERY_MEMORY", "true").lower() == "true"
AGENT_MEMORY_API_URL = os.getenv("AGENT_MEMORY_API_URL", "http://localhost:8765")
AGENT_MEMORY_HTTP_SERVER_PORT = int(os.getenv("AGENT_MEMORY_HTTP_SERVER_PORT", "8765"))

# Query Memory specific
QUERY_MEMORY_API_URL = os.getenv("QUERY_MEMORY_API_URL", "https://api.querymemory.com")
QUERY_MEMORY_API_KEY = os.getenv("QUERY_MEMORY_API_KEY", "")

# In orchestrator.py, on startup:
if AGENT_MEMORY_ENABLED:
    AGENT_MEMORY_CLIENT = AgentMemoryClient(
        use_query_memory=AGENT_MEMORY_USE_QUERY_MEMORY,
        query_memory_api_key=QUERY_MEMORY_API_KEY,
    )
else:
    AGENT_MEMORY_CLIENT = None  # No memory operations
```

**Fallback Resilience Testing:**
```python
# Unit tests specifically for fallback behavior
@pytest.mark.asyncio
async def test_fallback_on_query_memory_timeout():
    """Verify system falls back to LanceDB when Query Memory times out."""
    client = AgentMemoryClient(use_query_memory=True)

    # Simulate Query Memory timeout by mocking httpx timeout
    # Then verify search() still succeeds using LanceDB

@pytest.mark.asyncio
async def test_fallback_on_query_memory_unavailable():
    """Verify graceful degradation when Query Memory API is unreachable."""
    # 503 response from Query Memory → fallback triggered

@pytest.mark.asyncio
async def test_lancedb_backend_independent():
    """Verify LanceDB fallback works independently of Query Memory."""
    # All LanceDB tests pass even with Query Memory mocked to fail
```

**.mcp.json Integration:**
```json
{
  "mcpServers": {
    // ... existing servers ...
    "agent-memory": {
      "command": "python",
      "args": ["-m", "agent_memory.mcp_server", "--port", "8765"],
      "type": "stdio",
      "env": {
        "AGENT_MEMORY_USE_QUERY_MEMORY": "${AGENT_MEMORY_USE_QUERY_MEMORY:true}",
        "QUERY_MEMORY_API_KEY": "${QUERY_MEMORY_API_KEY:}",
        "LANCEDB_PATH": "${LANCEDB_PATH:./agent_memory_local.db}"
      }
    }
  }
}
```

**Test Coverage:**
```
tests/
├── test_agent_memory.py (Unit 1)
│   ├── test_store_document_query_memory
│   ├── test_search_with_metadata_filters
│   ├── test_search_temporal
│   ├── test_fallback_on_timeout
│   ├── test_fallback_on_unavailable
│   ├── test_concurrent_operations
│   └── test_empty_results
│
├── test_mcp_server.py (Unit 2)
│   ├── test_memory_store_tool
│   ├── test_memory_search_tool
│   ├── test_memory_temporal_tool
│   ├── test_context_preamble
│   └── test_agent_scoped_query
│
├── test_http_api.py (Unit 3)
│   ├── test_post_store
│   ├── test_get_search
│   ├── test_batch_store
│   ├── test_health_check
│   └── test_webhook_callback
│
├── test_evaluator_memory.py (Unit 4)
│   ├── test_evaluation_stored_to_memory
│   ├── test_optimizer_retrieves_from_memory
│   ├── test_human_verdict_recorded
│   └── test_jsonl_fallback_still_works
│
├── test_scanner_memory.py (Unit 5)
│   ├── test_scanner_queries_prior_discoveries
│   ├── test_duplicate_detection
│   ├── test_run_metrics_logged
│   └── test_temporal_scoping
│
└── test_integration.py
    ├── test_full_pipeline_with_memory
    ├── test_evaluator_learns_from_feedback
    └── test_memory_fallback_under_load
```

**Documentation:**
- `docs/agent-memory-setup.md` — Environment variables, troubleshooting, fallback behavior
- Comments in `agent_memory/client.py` — Architecture and design decisions

**Patterns to follow:**
- All config via environment variables (no secrets in code)
- Comprehensive docstrings for MCP tools and HTTP endpoints
- Clear error messages for misconfiguration

**Test scenarios:**
- All happy-path and fallback scenarios (listed in test suite above)
- Performance: search latency under 1s for 10K docs
- Resilience: system continues when memory backend changes

**Verification:**
- All tests pass (unit, integration, performance)
- Fallback activates correctly under failure modes
- Configuration is correctly applied via env + settings.json
- Documentation is complete and accurate

---

## System-Wide Impact

**Interaction Graph:**
- `orchestrator.py` → initializes AGENT_MEMORY_CLIENT on startup
- `evaluator.py` → stores EvaluationResult to memory after each eval
- `optimizer.py` → queries memory for training examples (replaces JSONL read)
- `scanner.py` (prompts) → queries memory for prior discoveries
- `writer.py` → creates backlinks to memory docs in research notes
- External webhook → POST to HTTP API with verdict updates

**Error Propagation:**
- Memory unavailable → fallback to local LanceDB (no blocking errors)
- Query Memory timeout → auto-downgrade with backoff retry
- Network errors → logged, system continues with degraded memory

**State Lifecycle Risks:**
- **Partial write risk**: Agent Memory store might succeed at Query Memory but fail at fallback sync. Mitigation: treat Query Memory as authoritative; fallback is best-effort cache.
- **Race conditions**: Multiple agents writing simultaneously. Mitigation: Query Memory's backend handles concurrent writes; LanceDB has single-process access.
- **Stale data**: Evaluator uses memory before evaluating, might see stale verdicts. Mitigation: query memory is advisory only, agents still evaluate fully.

**API Surface Parity:**
- MCP server and HTTP API expose same operations (memory:store, memory:search)
- No breaking changes to existing agent APIs (orchestrator, evaluator, optimizer)
- JSONL verdicts still supported as fallback

**Unchanged Invariants:**
- Pipeline output (EvaluationResult, PoCResult, IntegrationProposal) unchanged
- Vault notes (resources/research-scan-*.md) unchanged in format
- Agent execution semantics unchanged (memory is auxiliary)

**Integration Coverage:**
- Cross-layer: evaluator → memory → optimizer → next evaluation (training loop)
- Cross-agent: scanner → memory, writer → reads memory for backlinks
- External: webhook callbacks → HTTP API → stored in memory
- Fallback: Query Memory → LanceDB seamless transition

## Risks & Dependencies

| Risk | Mitigation |
|------|------------|
| Query Memory API cost exceeds budget | Fallback to LanceDB; can migrate all data back if needed. Monitor costs during Phase 1. |
| Query Memory latency > 1s for 10K docs | Benchmark during Phase 2. If unacceptable, use local LanceDB (no API calls). |
| Embedding quality mismatch (Query Memory vs Ollama/BGE-M3) | Test relevance ranking; if Query Memory scores differ significantly, use local embeddings with Query Memory storage only. |
| Network partitions (Query Memory unavailable) | Fallback to LanceDB is automatic; no ops action needed. |
| Agent memory grows unbounded (retention forever) | Implement optional cleanup script (mark old docs as archived, not deleted) if storage becomes concern. Not in MVP scope. |
| MCP server crashes | Orchestrator detects tool failure, logs error, continues without memory (agents still work). |
| Multiple agents writing concurrently | Query Memory backend is thread-safe. LanceDB single-writer safe (expect rare fallback race; acceptable for MVP). |
| Human verdict recording has no ACL | Agents are trusted (same codebase). Verdict data is internal use only. Not a security issue in MVP scope. |

## Documentation / Operational Notes

- **Operator setup**: Environment variables for Query Memory API key, fallback mode, HTTP port
- **Monitoring**: Log all Query Memory→LanceDB fallback events; alert if fallback rate > 5%
- **Troubleshooting guide** in `docs/agent-memory-setup.md`:
  - Query Memory API key validation
  - LanceDB fallback behavior
  - Testing memory queries manually (curl examples for HTTP API)
- **Data migration** (if moving away from Query Memory): Export LanceDB → re-import to any vector store

## Open Questions

### Resolved During Planning
- **Authentication**: Use Bearer token from env var `QUERY_MEMORY_API_KEY` passed to HTTP header
- **Metadata schema**: Finalized in Unit 1 approach (agent_id, source, verdict, domain_tags, etc.)
- **Partitioning logic**: Agent-scoped via metadata filter (agent_id) + optional cross-agent flag (see search parameters)

### Deferred to Implementation
- [Needs research] Query Memory exact pricing and rate limits; benchmark search latency before committing
- [Needs research] Query Memory API authentication method and token refresh flow
- [Technical] LanceDB version and Ollama dependency versions to pin
- [Technical] Connection pooling for Query Memory HTTP client (async)

## Next Steps

→ `/ce:work` to implement all 6 units in sequence (or parallel where independent)
