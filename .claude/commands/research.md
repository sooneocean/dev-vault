Trigger a research pipeline scan to discover new LLM tools and papers.

Usage: /research [mode]
- quick-scan (default): Scan GitHub, arXiv, HuggingFace, web for new tools in last 7 days
- deep-scan: Full scan (30 days) + LLM-as-Judge evaluation + Docker PoC for top candidates

Run:
```bash
cd "C:\DEX_data\Claude Code DEV\projects\tools\research-pipeline"
source .venv/Scripts/activate
python orchestrator.py --mode ${MODE:-quick-scan}
```

If the venv or orchestrator is not available, perform a manual scan:
1. Use WebSearch to find "new AI agent framework 2026", "RAG tools trending", "MCP server new"
2. For each discovery, note: name, URL, description, stars, tags
3. Create a research note at `resources/research-scan-YYYY-MM-DD.md` with proper frontmatter
4. Run `obsidian-agent sync` to update indices

$ARGUMENTS
