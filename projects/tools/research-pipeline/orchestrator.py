"""Research Pipeline Orchestrator — dispatches scanner subagents and coordinates the pipeline."""

from __future__ import annotations

import asyncio
import json
import sys
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path

from claude_agent_sdk import AgentDefinition, ClaudeAgentOptions, query

from config import (
    AGENT_MODELS,
    LOCK_STALE_HOURS,
    MAX_TURNS,
    MCP_SERVERS,
    PIPELINE_ROOT,
    STATE_DIR,
    VAULT_ROOT,
)
from models import PipelineRunState, ScanResult, SeenUrl

# ---------------------------------------------------------------------------
# Scanner subagent definitions
# ---------------------------------------------------------------------------

SCANNER_AGENTS: dict[str, AgentDefinition] = {
    "github_scanner": AgentDefinition(
        description="Scans GitHub for trending repos in agent-framework and RAG domains",
        prompt=(PIPELINE_ROOT / "prompts" / "github_scanner.md").read_text(encoding="utf-8")
        if (PIPELINE_ROOT / "prompts" / "github_scanner.md").exists()
        else "Search GitHub for new agent framework and RAG tools. Return structured JSON.",
        tools=["Read", "Bash", "Grep", "Glob", "WebSearch"],
        model=AGENT_MODELS["scanner"],
        mcpServers=[MCP_SERVERS["github"]],
        maxTurns=MAX_TURNS["scanner"],
    ),
    "arxiv_scanner": AgentDefinition(
        description="Scans arXiv for recent papers on agents and RAG",
        prompt=(PIPELINE_ROOT / "prompts" / "arxiv_scanner.md").read_text(encoding="utf-8")
        if (PIPELINE_ROOT / "prompts" / "arxiv_scanner.md").exists()
        else "Search arXiv for recent agent/RAG papers. Return structured JSON.",
        tools=["Read", "WebSearch"],
        model=AGENT_MODELS["scanner"],
        mcpServers=[MCP_SERVERS["arxiv"]],
        maxTurns=MAX_TURNS["scanner"],
    ),
    "huggingface_scanner": AgentDefinition(
        description="Scans HuggingFace for trending models, datasets, and spaces",
        prompt=(PIPELINE_ROOT / "prompts" / "huggingface_scanner.md").read_text(encoding="utf-8")
        if (PIPELINE_ROOT / "prompts" / "huggingface_scanner.md").exists()
        else "Search HuggingFace for trending embedding/agent models. Return structured JSON.",
        tools=["Read", "WebSearch"],
        model=AGENT_MODELS["scanner"],
        mcpServers=[MCP_SERVERS["huggingface"]],
        maxTurns=MAX_TURNS["scanner"],
    ),
    "web_scanner": AgentDefinition(
        description="Scans Product Hunt, Hacker News, and AI newsletters for new tools",
        prompt=(PIPELINE_ROOT / "prompts" / "web_scanner.md").read_text(encoding="utf-8")
        if (PIPELINE_ROOT / "prompts" / "web_scanner.md").exists()
        else "Search the web for new AI/LLM tools on Product Hunt and HN. Return structured JSON.",
        tools=["Read", "WebSearch", "WebFetch"],
        model=AGENT_MODELS["scanner"],
        mcpServers=[MCP_SERVERS["fetch"]],
        maxTurns=MAX_TURNS["scanner"],
    ),
}

WRITER_AGENT = AgentDefinition(
    description="Writes structured Obsidian research notes from scan results",
    prompt=(PIPELINE_ROOT / "prompts" / "writer.md").read_text(encoding="utf-8")
    if (PIPELINE_ROOT / "prompts" / "writer.md").exists()
    else "Write an Obsidian research note from the provided scan results. Use proper frontmatter.",
    tools=["Read", "Write", "Edit", "Bash"],
    model=AGENT_MODELS["writer"],
    maxTurns=MAX_TURNS["writer"],
)

# ---------------------------------------------------------------------------
# State management
# ---------------------------------------------------------------------------


def acquire_lock() -> bool:
    """Acquire pipeline lock. Returns False if another run is active."""
    lock_file = STATE_DIR / "pipeline.lock"
    if lock_file.exists():
        try:
            lock_data = json.loads(lock_file.read_text(encoding="utf-8"))
            locked_at = datetime.fromisoformat(lock_data["locked_at"])
            if datetime.now() - locked_at < timedelta(hours=LOCK_STALE_HOURS):
                return False  # Active lock
        except (json.JSONDecodeError, KeyError):
            pass  # Corrupted lock, proceed

    STATE_DIR.mkdir(parents=True, exist_ok=True)
    lock_file.write_text(json.dumps({
        "locked_at": datetime.now().isoformat(),
        "pid": str(os.getpid()) if "os" in dir() else "unknown",
    }))
    return True


def release_lock() -> None:
    lock_file = STATE_DIR / "pipeline.lock"
    lock_file.unlink(missing_ok=True)


def load_seen_urls() -> dict[str, SeenUrl]:
    """Load cross-run dedup registry."""
    seen_file = STATE_DIR / "seen_urls.json"
    if not seen_file.exists():
        return {}
    try:
        data = json.loads(seen_file.read_text(encoding="utf-8"))
        result = {}
        for url, entry in data.items():
            seen = SeenUrl(**entry)
            if seen.expires >= date.today():
                result[url] = seen  # Only keep non-expired
        return result
    except (json.JSONDecodeError, Exception):
        return {}


def save_seen_urls(seen: dict[str, SeenUrl]) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    data = {url: s.model_dump(mode="json") for url, s in seen.items()}
    (STATE_DIR / "seen_urls.json").write_text(json.dumps(data, indent=2))


def save_run_state(state: PipelineRunState) -> None:
    """Checkpoint run state to disk for resume capability."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    path = STATE_DIR / f"run-{state.run_id}.json"
    path.write_text(state.model_dump_json(indent=2))


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


async def run_pipeline(mode: str = "quick-scan", dry_run: bool = False) -> None:
    """Main pipeline entry point."""
    run_id = f"{date.today().isoformat()}-{uuid.uuid4().hex[:8]}"
    state = PipelineRunState(run_id=run_id, mode=mode)

    if not acquire_lock():
        print("ERROR: Pipeline lock is held by another run. Exiting.")
        sys.exit(1)

    try:
        if dry_run:
            print(f"[DRY RUN] Pipeline mode: {mode}")
            print(f"[DRY RUN] Run ID: {run_id}")
            print(f"[DRY RUN] Scanners to dispatch:")
            for name, agent in SCANNER_AGENTS.items():
                print(f"  - {name}: {agent.description}")
            print(f"[DRY RUN] Writer: {WRITER_AGENT.description}")
            return

        # Phase 1: Scan
        print(f"Starting {mode} pipeline run: {run_id}")
        state.phase = "scanning"
        save_run_state(state)

        scan_results = await run_scanners(mode)
        state.scan_results = scan_results
        save_run_state(state)

        # Dedup against seen URLs
        seen = load_seen_urls()
        new_results = [r for r in scan_results if r.url not in seen]
        print(f"Scan complete: {len(scan_results)} found, {len(new_results)} new")

        if not new_results:
            print("No new discoveries. Writing empty scan note.")
            state.phase = "writing"
            save_run_state(state)
            await run_writer(new_results, run_id)
            state.phase = "complete"
            save_run_state(state)
            return

        # Phase 2: Write results to vault (Phase 1 MVP — no evaluation)
        state.phase = "writing"
        save_run_state(state)
        await run_writer(new_results, run_id)

        # Update seen URLs
        for r in new_results:
            seen[r.url] = SeenUrl(
                url=r.url,
                verdict=None,  # No evaluation in Phase 1
                first_seen=date.today(),
                expires=date.today() + timedelta(days=14),
            )
        save_seen_urls(seen)

        state.phase = "complete"
        save_run_state(state)
        print(f"Pipeline complete. {len(new_results)} new discoveries written to vault.")

    except Exception as e:
        state.errors.append(str(e))
        save_run_state(state)
        print(f"Pipeline error: {e}")
        raise
    finally:
        release_lock()


async def run_scanners(mode: str) -> list[ScanResult]:
    """Dispatch all scanner subagents and collect results."""
    all_agents = {**SCANNER_AGENTS, "writer": WRITER_AGENT}

    opts = ClaudeAgentOptions(
        agents=all_agents,
        permission_mode="bypassPermissions",
    )

    scan_prompt = f"""You are the Research Pipeline Orchestrator running in {mode} mode.

Dispatch ALL scanner subagents in parallel:
- github_scanner: Search for new agent framework and RAG tools on GitHub
- arxiv_scanner: Search for recent papers on agents, RAG, and knowledge management
- huggingface_scanner: Search for trending models and spaces on HuggingFace
- web_scanner: Search Product Hunt and Hacker News for new AI tools

After all scanners complete, collect their results and save them to:
{STATE_DIR / f'scan-results-{date.today().isoformat()}.json'}

Each result must be a JSON object with these fields:
- source: "github" | "arxiv" | "huggingface" | "web"
- name: tool/paper name
- url: link
- description: one-paragraph summary
- stars: GitHub stars (null if not applicable)
- tags: relevant topic tags
- is_paper: true if this is a paper, false for tools/repos

Focus on discoveries from the last {"7 days" if mode == "quick-scan" else "30 days"}.
Save the JSON array to the state file, then report a summary."""

    results: list[ScanResult] = []

    async for message in query(prompt=scan_prompt, options=opts):
        # Collect messages — the orchestrator agent will coordinate scanners
        if hasattr(message, "content"):
            print(f"[orchestrator] {str(message.content)[:200]}")

    # Read results from state file
    results_file = STATE_DIR / f"scan-results-{date.today().isoformat()}.json"
    if results_file.exists():
        try:
            raw = json.loads(results_file.read_text(encoding="utf-8"))
            for item in raw:
                results.append(ScanResult(**item))
        except (json.JSONDecodeError, Exception) as e:
            print(f"Warning: Could not parse scan results: {e}")

    return results


async def run_writer(results: list[ScanResult], run_id: str) -> None:
    """Dispatch the writer subagent to create vault notes."""
    results_json = json.dumps(
        [r.model_dump(mode="json") for r in results], indent=2, ensure_ascii=False
    )

    writer_prompt = f"""Write an Obsidian research scan note for today's discoveries.

## Scan Results
{results_json}

## Output Requirements
- File path: {VAULT_ROOT / "resources" / f"research-scan-{date.today().isoformat()}.md"}
- Use this frontmatter:
  ```yaml
  ---
  title: "研究掃描 {date.today().isoformat()}"
  type: resource
  tags: [research-scan, auto-generated, agent-framework, rag]
  created: "{date.today().isoformat()}"
  updated: "{date.today().isoformat()}"
  status: active
  summary: "自動掃描發現 {len(results)} 個新工具/論文"
  related: ["[[tech-research-squad]]"]
  ---
  ```
- Format: Ecosystem Overview → Top Discoveries (table) → Emerging → Summary
- Each discovery gets: name, URL, description, source, stars (if any), tags
- If results are empty, write "No new discoveries today."
- After writing, run: obsidian-agent sync (to update indices)"""

    opts = ClaudeAgentOptions(
        agents={"writer": WRITER_AGENT},
        permission_mode="bypassPermissions",
    )

    async for message in query(prompt=writer_prompt, options=opts):
        if hasattr(message, "content"):
            print(f"[writer] {str(message.content)[:200]}")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

import os  # noqa: E402


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="LLM Tech Research Pipeline")
    parser.add_argument(
        "--mode",
        choices=["quick-scan", "deep-scan"],
        default="quick-scan",
        help="Scan mode (default: quick-scan)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be executed without running",
    )
    args = parser.parse_args()

    asyncio.run(run_pipeline(mode=args.mode, dry_run=args.dry_run))


if __name__ == "__main__":
    main()
