# LLM Tech Research Pipeline

Automated research pipeline for discovering, evaluating, and integrating new LLM technologies into the Claude Code toolchain.

## Architecture

Built on Claude Agent SDK with MCP servers as data source interfaces.

```
Schedule → Orchestrator → Scanner Subagents (parallel)
  → Dedup + Normalize → LLM-as-Judge Evaluation
  → PoC Runner (Docker) → Vault Writer → Knowledge Layer
  → Integration Assessor → Human Gate → Auto-Apply
```

## Prerequisites

- Python 3.14+, Node v24+
- Docker 28.5+
- Ollama (for local models)
- GitHub CLI (`gh`) authenticated
- Claude Code with MCP support

## MCP Servers (configured in vault `.mcp.json`)

| Server | Package | Purpose |
|--------|---------|---------|
| arxiv | `arxiv-mcp-server` | arXiv paper search and analysis |
| huggingface | `huggingface-mcp-server` | HuggingFace model/dataset search |
| fetch | `mcp-server-fetch` | Web page fetching + HTML→Markdown |
| github | (via plugin) | GitHub repo/issue/PR search |

## Local Models (Unit 12)

| Model | Size | Use Case |
|-------|------|----------|
| bge-m3 | ~2.3GB | Embedding (dense + sparse) |
| phi4-mini | ~2.5GB | Classification / tagging |
| qwen3.5:9b | ~6GB | Summarize / translate |
| qwen3.5:35b-a3b | ~20GB | Reasoning (MoE) |

## Directory Structure

```
research-pipeline/
├── orchestrator.py      # Main orchestrator (Claude Agent SDK)
├── config.py            # Pipeline configuration
├── models.py            # Pydantic schemas (ScanResult, EvaluationResult, PoCResult)
├── writer.py            # Vault note writer
├── evaluator.py         # LLM-as-Judge evaluation engine
├── sanitizer.py         # Content sanitizer (prompt injection defense)
├── rubric.py            # Evaluation rubric definition
├── scanners/            # Source scanner subagents
│   ├── base.py          # Shared ScanResult schema
│   ├── github_scanner.py
│   ├── arxiv_scanner.py
│   ├── huggingface_scanner.py
│   └── web_scanner.py
├── knowledge/           # Vector search + knowledge graph
│   ├── vector_store.py  # LanceDB management
│   ├── graph.py         # LightRAG management
│   └── indexer.py       # Indexing trigger
├── local-llm/           # Local model deployment
│   ├── model-inventory.md
│   ├── benchmark.py
│   ├── litellm-config.yaml
│   ├── delegation-config.json
│   └── start-gateway.sh
├── self_improve/        # Self-improvement loop
│   ├── experience.py    # Experience recorder
│   └── optimizer.py     # DSPy prompt optimizer
├── state/               # Runtime state (gitignored)
│   ├── seen_urls.json   # Cross-run dedup
│   ├── pipeline.lock    # Concurrency lock
│   └── scan-results-*.json
├── prompts/             # Subagent system prompts (versioned)
├── dockerfiles/         # PoC sandbox Dockerfiles
├── scripts/             # Scheduling wrapper scripts
├── tests/               # Test suite
└── pyproject.toml       # Dependencies
```

## Plan

See `docs/plans/2026-03-29-003-feat-auto-llm-tech-research-pipeline-plan.md`
