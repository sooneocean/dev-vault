# Agent Memory System Setup Guide

## Overview

The Agent Memory System provides persistent, cross-session memory for Claude Code agents in the research pipeline. It uses **Query Memory** as the primary data layer with graceful fallback to **LanceDB** for local vector storage.

**Key features:**
- Persistent storage of tool evaluations, scanner discoveries, and training data
- Semantic search with metadata filtering
- Agent-scoped partitioning for isolation and sharing
- Automatic fallback when Query Memory is unavailable
- MCP server integration for native Claude Code agent support
- HTTP REST API for external services and webhooks

---

## Quick Start

### 1. Environment Setup

Add these environment variables to your shell or `.env` file:

```bash
# Enable/disable agent memory (default: true)
export AGENT_MEMORY_ENABLED=true

# Use Query Memory as primary backend (default: true)
export AGENT_MEMORY_USE_QUERY_MEMORY=true

# Query Memory API configuration
export QUERY_MEMORY_API_URL=https://api.querymemory.com
export QUERY_MEMORY_API_KEY=your_api_key_here  # Obtain from Query Memory dashboard

# Local fallback database path (default: ./agent_memory_local.db)
export LANCEDB_PATH=./agent_memory_local.db

# HTTP API server port (default: 8765)
export AGENT_MEMORY_HTTP_SERVER_PORT=8765
```

### 2. Install Dependencies

```bash
cd projects/tools/research-pipeline
pip install -e .
```

Required packages (should be in `pyproject.toml`):
- `httpx` — Query Memory API client
- `lancedb` — Local vector store fallback
- `pydantic` — Data validation
- `fastapi` — HTTP API server

### 3. Verify Configuration

Check that the memory system is configured correctly:

```bash
# List environment variables being used
env | grep AGENT_MEMORY

# Test local LanceDB is accessible
python -c "from agent_memory import AgentMemoryClient; print('AgentMemoryClient imported successfully')"
```

---

## Architecture

### Data Flow

```
Agent (Scanner/Evaluator/Writer)
    ↓
AgentMemoryClient
    ├─→ Query Memory API (primary, if enabled)
    └─→ LanceDB (local fallback)
         ├─→ Ollama BGE-M3 embeddings
         └─→ Lance vector store
```

### Decision Tree: When Fallback Activates

1. **Query Memory enabled** (`AGENT_MEMORY_USE_QUERY_MEMORY=true`):
   - Try Query Memory API with 5-second timeout
   - On timeout → Log warning, fall back to LanceDB
   - On 503/network error → Log warning, fall back to LanceDB
   - On success → Use Query Memory results

2. **Query Memory disabled** or **not configured**:
   - Use LanceDB directly (no external API calls)
   - Best for air-gapped or local-only environments

3. **Agent Memory disabled** (`AGENT_MEMORY_ENABLED=false`):
   - All memory operations are no-ops
   - Pipeline continues without memory context

---

## Running the System

### Mode 1: MCP Server (for Claude Code agents)

The memory system is automatically available to agents through the MCP server registered in `.mcp.json`.

When `orchestrator.py` starts:
```python
if AGENT_MEMORY_ENABLED:
    AGENT_MEMORY_CLIENT = AgentMemoryClient(
        use_query_memory=AGENT_MEMORY_USE_QUERY_MEMORY,
        query_memory_api_key=QUERY_MEMORY_API_KEY,
    )
```

Agents can then call:
- `memory:store` — Store discovery or evaluation to memory
- `memory:search` — Find related prior evaluations
- `memory:search_temporal` — Query with date filtering

### Mode 2: HTTP API Server (for external services)

Start the HTTP server standalone:

```bash
python -m agent_memory.http_server --port 8765
```

Or let `orchestrator.py` spawn it:
```python
if AGENT_MEMORY_ENABLED and AGENT_MEMORY_HTTP_ENABLED:
    # Orchestrator spawns HTTP server as background task
    pass
```

**Endpoints:**

```http
# Store a single document
POST /memory/store
Content-Type: application/json
{
  "agent_id": "evaluator",
  "source": "evaluation",
  "content": "Evaluated tool-name: poc_candidate",
  "metadata": {
    "verdict": "poc_candidate",
    "tool_name": "tool-name",
    "total_score": 35
  }
}
→ 200 OK { "doc_id": "...", "status": "stored" }

# Search documents
GET /memory/search?query=agent+framework&agent_id=scanner&top_k=5
→ 200 OK [ {doc_id, content, metadata, score}, ... ]

# Temporal query
GET /memory/temporal?domain=agent-framework&after_date=2026-03-25
→ 200 OK [ {...}, ... ]

# Batch store (multiple documents)
POST /memory/batch_store
Content-Type: application/json
{
  "documents": [
    { "agent_id": "...", "source": "...", "content": "...", "metadata": {...} },
    ...
  ]
}
→ 200 OK { "stored": 10, "failed": 0 }

# Health check
GET /health
→ 200 OK { "status": "healthy", "backends": {"query_memory": "available", "lancedb": "ready"} }
```

---

## Configuration Reference

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AGENT_MEMORY_ENABLED` | `true` | Enable/disable all memory operations |
| `AGENT_MEMORY_USE_QUERY_MEMORY` | `true` | Use Query Memory as primary backend |
| `QUERY_MEMORY_API_URL` | `https://api.querymemory.com` | Query Memory API endpoint |
| `QUERY_MEMORY_API_KEY` | `` | API key for Query Memory authentication |
| `LANCEDB_PATH` | `./agent_memory_local.db` | Local LanceDB database path |
| `AGENT_MEMORY_HTTP_SERVER_PORT` | `8765` | HTTP API server port |

### Configuration via settings.json

You can also configure through `.claude/settings.json` (project or global):

```json
{
  "agentMemory": {
    "enabled": true,
    "useQueryMemory": true,
    "queryMemoryApiKey": "your_api_key",
    "lancedbPath": "./agent_memory_local.db"
  }
}
```

Priority order (highest to lowest):
1. Environment variables (`AGENT_MEMORY_*`)
2. Project `.claude/settings.json`
3. Global `~/.claude/settings.json`
4. Hardcoded defaults in code

---

## Metadata Schema

### Document Structure

All documents stored in agent memory have this structure:

```python
{
  "agent_id": str,              # "scanner" | "evaluator" | "writer" | ...
  "source": str,                # "github" | "arxiv" | "evaluation" | "run_metrics"
  "content": str,               # Free-text content (searchable)
  "metadata": {
    # Standard fields
    "verdict": str,             # "pending" | "poc_candidate" | "watching" | "not_applicable"
    "domain_tags": [str],       # ["agent-framework", "rag", "tool", ...]

    # Source-specific
    "name": str,                # Tool/paper name
    "url": str,                 # URL to resource
    "source_type": str,         # "github" | "arxiv" | ...

    # Evaluation-specific
    "tool_name": str,
    "total_score": float,       # 0-50 range
    "percentage": float,        # 0-100

    # Temporal
    "timestamp": str,           # ISO8601 datetime

    # Custom metadata (per-agent)
    // any additional fields
  }
}
```

### Query Filter Examples

```python
# Find previously evaluated tools
memory.search("agent framework", agent_id="evaluator", top_k=5)

# Find new discoveries from scanner
memory.search("arxiv papers", agent_id="scanner", top_k=10)

# Find high-value tools
memory.search("", metadata_filter={"verdict": "poc_candidate"}, top_k=20)

# Find tools evaluated in last 7 days
memory.search_temporal(
    domain="agent-framework",
    after_date=datetime.now() - timedelta(days=7)
)
```

---

## Troubleshooting

### Query Memory Unavailable

**Symptom:** Warnings in logs like `"Failed to query Query Memory, falling back to LanceDB"`

**Diagnosis:**
```bash
# Check API connectivity
curl -i https://api.querymemory.com/health

# Check API key
echo $QUERY_MEMORY_API_KEY  # Should not be empty

# Check network
ping api.querymemory.com
```

**Solutions:**
1. Verify `QUERY_MEMORY_API_KEY` is set correctly
2. Check network connectivity to `api.querymemory.com`
3. Verify API key has not expired (check Query Memory dashboard)
4. Set `AGENT_MEMORY_USE_QUERY_MEMORY=false` to use local-only mode

### LanceDB Corrupted

**Symptom:** Errors like `"LanceDB table not found"` or `"Lance file corrupted"`

**Diagnosis:**
```bash
ls -la $LANCEDB_PATH/
# If directory is empty or corrupted, LanceDB needs rebuild
```

**Solutions:**
1. Backup existing database: `mv agent_memory_local.db agent_memory_local.db.bak`
2. Restart pipeline (fresh LanceDB created on first write)
3. To restore from backup: `mv agent_memory_local.db.bak agent_memory_local.db`

### Embedding Service (Ollama) Not Running

**Symptom:** Errors like `"Failed to get embedding: connection refused"`

**Diagnosis:**
```bash
curl http://localhost:11434/api/embeddings -X POST -d '{"model": "bge-m3"}' -H "Content-Type: application/json"
# Should return embedding vector, not error
```

**Solutions:**
1. Install Ollama: https://ollama.ai
2. Pull BGE-M3 model: `ollama pull bge-m3`
3. Start Ollama service: `ollama serve` (runs on localhost:11434)
4. If running in container, expose port 11434 to host

**Alternative:** Disable embeddings for testing (use hash-based similarity):
```bash
export LANCEDB_USE_OLLAMA=false  # Falls back to hash-based similarity
```

### Memory Operations Slow

**Symptom:** Search latency > 1 second for > 10K documents

**Diagnosis:**
```bash
# Profile Query Memory latency
time python -c "from agent_memory import AgentMemoryClient; c = AgentMemoryClient(); c.search('test')"

# Profile LanceDB latency
time python -c "from agent_memory.fallback import LanceDBBackend; lb = LanceDBBackend(); lb.search('test')"
```

**Solutions:**
1. For Query Memory slowness:
   - Check Query Memory API status dashboard
   - Consider switching to local-only mode: `AGENT_MEMORY_USE_QUERY_MEMORY=false`
2. For LanceDB slowness:
   - Ensure Ollama is running locally (network latency adds up)
   - Consider moving LANCEDB_PATH to SSD if on slow storage

### Agent Cannot Access Memory

**Symptom:** Agent errors like `"Cannot import AgentMemoryClient"` or `"memory:store tool not found"`

**Diagnosis:**
```bash
# Check agent-memory MCP server is registered
cat .mcp.json | grep agent-memory

# Check agent_memory package is installed
python -c "import agent_memory; print(agent_memory.__file__)"

# Check AGENT_MEMORY_ENABLED
echo $AGENT_MEMORY_ENABLED
```

**Solutions:**
1. Verify `.mcp.json` has agent-memory server definition (see Configuration section)
2. Reinstall package: `pip install -e projects/tools/research-pipeline/`
3. Ensure `AGENT_MEMORY_ENABLED=true`
4. Restart Claude Code session to reload MCP servers

---

## Monitoring & Health Checks

### Key Metrics to Track

1. **Fallback Rate** — How often Query Memory is unavailable
   - Success target: < 5% fallback events per hour
   - Warning threshold: > 10%
   - Action: Check Query Memory API status

2. **Query Latency** — Time to search memory
   - Target: < 1s per query (p99)
   - Warning: > 2s consistently
   - Action: Profile Query Memory API or switch to local-only

3. **Storage Growth** — Agent memory database size
   - Monitor: `du -sh $LANCEDB_PATH/`
   - Expected: 100MB per 10K documents
   - Action: Implement cleanup job if size exceeds available disk

4. **Error Rate** — Failed memory operations
   - Success target: > 99.5%
   - Monitor logs for `ERROR` or `WARNING` keywords

### Log Monitoring

```bash
# Watch for fallback events
grep "Falling back to LanceDB" orchestrator.log

# Watch for errors
grep -E "ERROR|Exception" orchestrator.log

# Count Query Memory successes/failures
grep "query_memory" orchestrator.log | grep -c "success"
grep "query_memory" orchestrator.log | grep -c "fallback"
```

---

## Performance Tuning

### Optimizing Query Memory

If using Query Memory as primary backend:

1. **Batch operations**: Use `batch_store()` instead of individual `store()` calls
   - Before: 1000 documents × 0.1s = 100s
   - After: 1000 documents in 1 batch ≈ 1s

2. **Reduce query results**: Lower `top_k` parameter
   - `top_k=5` is usually sufficient for evaluator context
   - Higher values increase API latency

3. **Use metadata filters**: Narrow scope before semantic search
   - Query with `agent_id="scanner"` to ignore evaluator documents

### Optimizing LanceDB

If using local-only mode (`AGENT_MEMORY_USE_QUERY_MEMORY=false`):

1. **SSD storage**: Place LANCEDB_PATH on fast storage
   - HDD: 100-500ms per search
   - SSD: 10-50ms per search

2. **Local Ollama**: Ensure Ollama service is on same machine
   - Network Ollama: +100-200ms per embedding request
   - Local Ollama: <10ms per embedding

3. **Index maintenance**: Periodically optimize LanceDB
   ```bash
   python -c "
   from agent_memory.fallback import LanceDBBackend
   backend = LanceDBBackend()
   backend.optimize()  # Compacts Lance files
   "
   ```

---

## Migration & Cleanup

### Exporting Memory Data

To export all stored memory as JSON:

```bash
python << 'EOF'
import json
from agent_memory import AgentMemoryClient

client = AgentMemoryClient()
docs = client.search("", top_k=10000)  # Get all documents

with open("memory_backup.json", "w") as f:
    json.dump([doc.model_dump() for doc in docs], f, indent=2)

print(f"Exported {len(docs)} documents to memory_backup.json")
EOF
```

### Archiving Old Evaluations

To mark evaluations older than 30 days as archived:

```bash
python << 'EOF'
from datetime import datetime, timedelta
from agent_memory import AgentMemoryClient

client = AgentMemoryClient()
threshold = datetime.now() - timedelta(days=30)

# Query old evaluations
docs = client.search("", agent_id="evaluator", top_k=1000)

for doc in docs:
    if doc.metadata.get("timestamp") < threshold.isoformat():
        # Mark as archived (in Query Memory metadata update)
        doc.metadata["status"] = "archived"
        client.store(doc)

print(f"Archived {len(docs)} old evaluations")
EOF
```

---

## Related Documentation

- **Query Memory API**: https://api.querymemory.com/docs
- **LanceDB Documentation**: https://lancedb.com
- **Agent Memory Code**: `projects/tools/research-pipeline/agent_memory/`
- **Research Pipeline**: `projects/tools/research-pipeline/README.md`

---

## Support

For issues or questions:

1. Check logs: `grep -i "memory" orchestrator.log`
2. Review troubleshooting section above
3. Check agent memory module: `projects/tools/research-pipeline/agent_memory/`
4. Check tests for usage examples: `projects/tools/research-pipeline/tests/test_*_memory.py`
