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
    DEDUP_EXPIRY,
    LOCK_STALE_HOURS,
    MAX_TURNS,
    MCP_SERVERS,
    PIPELINE_ROOT,
    STATE_DIR,
    VAULT_ROOT,
)
from evaluator import evaluate_scan_results, save_evaluation_results
from models import EvaluationResult, PipelineRunState, PoCResult, ScanResult, SeenUrl, Verdict
from poc_runner import run_poc, save_poc_results


def _posix_path(p: Path) -> str:
    """Convert a Windows Path to POSIX string for Claude Code subagents.

    Claude Code CLI runs in a POSIX-like shell (Git Bash / MSYS2) where
    ``C:\\foo`` becomes ``/c/foo``.  Subagents that receive file paths need
    this form so their Write/Read tools resolve correctly.
    """
    s = p.as_posix()  # C:/DEX_data/...
    # Convert drive letter: C:/foo -> /c/foo
    if len(s) >= 2 and s[1] == ":":
        s = "/" + s[0].lower() + s[2:]
    return s


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
    description="Writes structured Obsidian research notes from scan/evaluation results",
    prompt=(PIPELINE_ROOT / "prompts" / "writer.md").read_text(encoding="utf-8")
    if (PIPELINE_ROOT / "prompts" / "writer.md").exists()
    else "Write an Obsidian research note from the provided scan results. Use proper frontmatter.",
    tools=["Read", "Write", "Edit", "Bash"],
    model=AGENT_MODELS["writer"],
    maxTurns=MAX_TURNS["writer"],
)

# Note: The evaluator agent is built dynamically via evaluator.build_evaluator_agent()
# because it needs per-item rubric injection. PoC runner uses subprocess, not a subagent.

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
    """Main pipeline entry point.

    Pipeline flow:
      1. Scan — dispatch source scanner subagents in parallel
      2. Evaluate — LLM-as-Judge 5-dimension scoring per item
      3. PoC — Docker sandbox verification for poc_candidates (deep-scan only)
      4. Write — produce structured Obsidian vault notes with verdicts
    """
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
            print(f"[DRY RUN] Evaluator: 5-dimension LLM-as-Judge (Relevance/Maturity/Integration Effort/Maintenance Risk/Unique Value)")
            print(f"[DRY RUN] PoC Runner: Docker sandbox ({'enabled' if mode == 'deep-scan' else 'skipped in quick-scan'})")
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
            await run_writer_with_evaluations([], [], run_id)
            state.phase = "complete"
            save_run_state(state)
            return

        # Phase 2: Evaluate — LLM-as-Judge 5-dimension scoring
        state.phase = "evaluating"
        save_run_state(state)
        print(f"Evaluating {len(new_results)} new discoveries...")

        eval_results = await evaluate_scan_results(new_results)
        state.evaluation_results = eval_results
        save_evaluation_results(eval_results)
        save_run_state(state)

        # Summarize evaluation verdicts
        poc_candidates = [e for e in eval_results if e.verdict == Verdict.POC_CANDIDATE]
        watching = [e for e in eval_results if e.verdict == Verdict.WATCHING]
        not_applicable = [e for e in eval_results if e.verdict == Verdict.NOT_APPLICABLE]
        print(
            f"Evaluation complete: {len(poc_candidates)} poc_candidate, "
            f"{len(watching)} watching, {len(not_applicable)} not_applicable"
        )

        # Phase 2b: PoC — Docker sandbox for poc_candidates (deep-scan only)
        poc_results: list[PoCResult] = []
        if mode == "deep-scan" and poc_candidates:
            state.phase = "poc"
            save_run_state(state)
            print(f"Running PoC for {len(poc_candidates)} candidates...")

            for eval_r in poc_candidates:
                try:
                    poc_result = run_poc(eval_r)
                    poc_results.append(poc_result)
                    status = "PASS" if poc_result.quickstart_success else "FAIL"
                    print(f"  PoC {eval_r.scan_result.name}: {status}")
                except Exception as e:
                    print(f"  PoC {eval_r.scan_result.name}: ERROR — {e}")

            state.poc_results = poc_results
            save_poc_results(poc_results)
            save_run_state(state)
        elif poc_candidates:
            print(f"Skipping PoC in {mode} mode. {len(poc_candidates)} candidates queued for deep-scan.")

        # Phase 3: Write — structured vault notes with evaluation scores
        state.phase = "writing"
        save_run_state(state)
        await run_writer_with_evaluations(eval_results, poc_results, run_id)

        # Update seen URLs with verdicts and appropriate expiry
        for eval_r in eval_results:
            verdict = eval_r.verdict
            expiry_days = DEDUP_EXPIRY.get(verdict.value, 14)
            seen[eval_r.scan_result.url] = SeenUrl(
                url=eval_r.scan_result.url,
                verdict=verdict,
                first_seen=date.today(),
                expires=date.today() + timedelta(days=expiry_days),
            )
        save_seen_urls(seen)

        state.phase = "complete"
        save_run_state(state)
        print(
            f"Pipeline complete. {len(eval_results)} evaluated, "
            f"{len(poc_candidates)} poc_candidates, "
            f"{len(poc_results)} PoCs run."
        )

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

    results_filename = f"scan-results-{date.today().isoformat()}.json"
    results_posix = _posix_path(STATE_DIR / results_filename)

    scan_prompt = f"""You are the Research Pipeline Orchestrator running in {mode} mode.

Dispatch ALL scanner subagents in parallel:
- github_scanner: Search for new agent framework and RAG tools on GitHub
- arxiv_scanner: Search for recent papers on agents, RAG, and knowledge management
- huggingface_scanner: Search for trending models and spaces on HuggingFace
- web_scanner: Search Product Hunt and Hacker News for new AI tools

After all scanners complete, collect their results and save them to:
{results_posix}

IMPORTANT: Use exactly that POSIX path (starting with /) for the Write tool.

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

    # Read results from state file — try both Windows and POSIX paths
    results_file = STATE_DIR / results_filename
    if results_file.exists():
        try:
            raw = json.loads(results_file.read_text(encoding="utf-8"))
            for item in raw:
                results.append(ScanResult(**item))
        except (json.JSONDecodeError, Exception) as e:
            print(f"Warning: Could not parse scan results: {e}")

    return results


async def run_writer(results: list[ScanResult], run_id: str) -> None:
    """Dispatch the writer subagent to create vault notes (scan-only, no evaluations)."""
    await run_writer_with_evaluations(
        [EvaluationResult(
            scan_result=r,
            scores=[],
            total_score=0,
            max_score=0,
            percentage=0.0,
            verdict=Verdict.WATCHING,
            recommended_action="Pending evaluation",
        ) for r in results],
        [],
        run_id,
    )


async def run_writer_with_evaluations(
    eval_results: list[EvaluationResult],
    poc_results: list[PoCResult],
    run_id: str,
) -> None:
    """Dispatch the writer subagent to create vault notes with evaluation data.

    Generates a daily scan note containing:
    - Evaluation scores and verdicts for each discovery
    - PoC results for poc_candidates (if available)
    - Verdict-based categorization (poc_candidate / watching / not_applicable)
    """
    today = date.today().isoformat()
    note_path = _posix_path(VAULT_ROOT / "resources" / f"research-scan-{today}.md")

    # Build a PoC lookup for quick access
    poc_lookup: dict[str, PoCResult] = {}
    for poc in poc_results:
        poc_lookup[poc.evaluation_result.scan_result.url] = poc

    # Prepare structured data for the writer
    discoveries = []
    for eval_r in eval_results:
        sr = eval_r.scan_result
        entry = {
            "name": sr.name,
            "url": sr.url,
            "source": sr.source.value,
            "description": sr.description,
            "stars": sr.stars,
            "tags": sr.tags,
            "is_paper": sr.is_paper,
            "verdict": eval_r.verdict.value,
            "total_score": eval_r.total_score,
            "max_score": eval_r.max_score,
            "percentage": eval_r.percentage,
            "scores": [
                {"dimension": s.dimension, "score": s.score, "reasoning": s.reasoning}
                for s in eval_r.scores
            ],
            "recommended_action": eval_r.recommended_action,
        }
        # Attach PoC result if available
        if sr.url in poc_lookup:
            poc = poc_lookup[sr.url]
            entry["poc"] = {
                "install_success": poc.install_success,
                "quickstart_success": poc.quickstart_success,
                "execution_time_seconds": poc.execution_time_seconds,
                "notes": poc.notes,
            }
        discoveries.append(entry)

    discoveries_json = json.dumps(discoveries, indent=2, ensure_ascii=False)

    # Count verdicts for frontmatter summary
    n_poc = sum(1 for e in eval_results if e.verdict == Verdict.POC_CANDIDATE)
    n_watch = sum(1 for e in eval_results if e.verdict == Verdict.WATCHING)
    n_skip = sum(1 for e in eval_results if e.verdict == Verdict.NOT_APPLICABLE)
    n_total = len(eval_results)

    writer_prompt = f"""Write an Obsidian research scan note for today's evaluated discoveries.

## Evaluated Discoveries
{discoveries_json}

## Output Requirements
- File path: {note_path}

IMPORTANT: Use exactly that POSIX path (starting with /) for the Write tool.

- Use this frontmatter:
  ```yaml
  ---
  title: "研究掃描 {today}"
  type: resource
  tags: [research-scan, auto-generated, agent-framework, rag]
  created: "{today}"
  updated: "{today}"
  status: active
  summary: "自動掃描評估 {n_total} 項：{n_poc} poc_candidate, {n_watch} watching, {n_skip} not_applicable"
  related: ["[[tech-research-squad]]"]
  ---
  ```

## Note Structure
1. **Ecosystem Overview** — 1-2 paragraph summary of what was found today
2. **PoC Candidates** (verdict = poc_candidate) — table with: Name, Score, Verdict, Source, Stars, Description
   - For each, include a subsection with the 5-dimension score breakdown
   - If PoC results exist, include install/quickstart status
3. **Watching** (verdict = watching) — table with same columns
4. **Not Applicable** (verdict = not_applicable) — brief list with one-line reasoning
5. **Score Distribution** — summary statistics (avg score, score range, verdict counts)
6. **Recommended Actions** — aggregated next steps from all poc_candidates

## Formatting Rules
- Internal links use `[[filename]]` format without .md extension
- Each discovery's score shows: total/max (percentage%)
- Dimension scores formatted as: Relevance: 7 | Maturity: 5 | Integration: 6 | Risk: 4 | Value: 8
- PoC results show: Install: PASS/FAIL | Quickstart: PASS/FAIL | Time: Xs
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
