"""Pipeline configuration."""

from __future__ import annotations

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
    "rag-knowledge": [
        "RAG",
        "retrieval augmented generation",
        "vector database",
        "knowledge graph",
        "embedding model",
    ],
}

GITHUB_SEARCH_FILTERS = {
    "min_stars": 100,
    "language": "python",
    "created_after_days": 90,  # repos created in last N days
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
}

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
