"""Pipeline configuration."""

from __future__ import annotations

import os
from pathlib import Path

# Paths
VAULT_ROOT = Path(r"C:\DEX_data\Claude Code DEV")
PIPELINE_ROOT = VAULT_ROOT / "projects" / "tools" / "research-pipeline"
STATE_DIR = PIPELINE_ROOT / "state"
PROMPTS_DIR = PIPELINE_ROOT / "prompts"

# Scan settings
SCAN_TOPICS = {
    "agent-framework": [
        "agent framework",
        "multi-agent",
        "agent orchestration",
        "MCP server",
        "tool use LLM",
    ],
    "agentic-harness": [
        "agentic harness",
        "context prompt",
        "prompt engineering agent",
        "agent context window",
        "system prompt management",
        "prompt optimization",
    ],
    "rag-knowledge": [
        "RAG",
        "retrieval augmented generation",
        "vector database",
        "knowledge graph",
        "embedding model",
    ],
}

GITHUB_SEARCH_FILTERS = {
    "min_stars": 50,
    "language": "python",
    "created_after_days": 30,  # repos created in last N days
}

ARXIV_CATEGORIES = ["cs.AI", "cs.CL", "cs.IR"]
ARXIV_LOOKBACK_DAYS = {"quick-scan": 7, "deep-scan": 30}

# Evaluation thresholds (normalized to 70%)
EVAL_THRESHOLD_POC = 0.70       # >= 70% → poc_candidate
EVAL_THRESHOLD_WATCHING = 0.50  # >= 50% → watching, else not_applicable

# Dedup expiry (days)
DEDUP_EXPIRY = {
    "poc_candidate": 30,
    "watching": 7,
    "not_applicable": 14,
}

# Pipeline lock
LOCK_STALE_HOURS = 6

# MCP server names (as configured in .mcp.json)
MCP_SERVERS = {
    "github": "github",       # via plugin
    "arxiv": "arxiv",
    "huggingface": "huggingface",
    "fetch": "fetch",
    "agent-memory": "agent-memory",
}

# Agent Memory Configuration
AGENT_MEMORY_ENABLED = os.getenv("AGENT_MEMORY_ENABLED", "true").lower() == "true"
AGENT_MEMORY_USE_QUERY_MEMORY = os.getenv("AGENT_MEMORY_USE_QUERY_MEMORY", "true").lower() == "true"
AGENT_MEMORY_API_URL = os.getenv("AGENT_MEMORY_API_URL", "http://localhost:8765")
AGENT_MEMORY_HTTP_SERVER_PORT = int(os.getenv("AGENT_MEMORY_HTTP_SERVER_PORT", "8765"))

# Query Memory specific
QUERY_MEMORY_API_URL = os.getenv("QUERY_MEMORY_API_URL", "https://api.querymemory.com")
QUERY_MEMORY_API_KEY = os.getenv("QUERY_MEMORY_API_KEY", "")

# LanceDB fallback path
LANCEDB_PATH = os.getenv("LANCEDB_PATH", str(STATE_DIR / "agent_memory.db"))

# Agent model assignments
AGENT_MODELS = {
    "scanner": "haiku",   # fast + cheap for scanning
    "evaluator": "sonnet", # balanced for evaluation
    "writer": "sonnet",    # balanced for writing
    "integrator": "sonnet",  # needs reasoning for risk assessment
    "orchestrator": "sonnet",
}

# Max turns per subagent (safety limit)
MAX_TURNS = {
    "scanner": 10,
    "evaluator": 15,
    "writer": 10,
    "integrator": 15,
}

# Integration proposal settings
PROPOSALS_DIR = STATE_DIR / "proposals"
SETTINGS_JSON_PATHS = [
    Path.home() / ".claude" / "settings.json",  # global
    VAULT_ROOT / ".claude" / "settings.json",    # project (if exists)
]
