"""Integration assessor — evaluates how poc_candidate tools fit into the existing toolchain."""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

from claude_agent_sdk import AgentDefinition, ClaudeAgentOptions, query

from config import (
    AGENT_MODELS,
    MAX_TURNS,
    MCP_SERVERS,
    PIPELINE_ROOT,
    PROPOSALS_DIR,
    SETTINGS_JSON_PATHS,
    STATE_DIR,
)
from models import (
    EvaluationResult,
    IntegrationProposal,
    PoCResult,
    RiskLevel,
    Verdict,
)


def build_integrator_agent() -> AgentDefinition:
    """Build the integrator subagent definition."""
    prompt_path = PIPELINE_ROOT / "prompts" / "integrator.md"
    if prompt_path.exists():
        prompt = prompt_path.read_text(encoding="utf-8")
    else:
        prompt = "Assess tool integration into Claude Code toolchain. Return JSON proposals."

    return AgentDefinition(
        description="Assesses how discovered tools integrate into the existing toolchain",
        prompt=prompt,
        tools=["Read", "Bash", "Grep", "Glob"],
        model=AGENT_MODELS["integrator"],
        maxTurns=MAX_TURNS["integrator"],
    )


def _load_current_toolchain() -> dict:
    """Read current toolchain config from settings.json files."""
    toolchain = {"mcp_servers": {}, "settings_path": None}

    for path in SETTINGS_JSON_PATHS:
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                if "mcpServers" in data:
                    toolchain["mcp_servers"].update(data["mcpServers"])
                if toolchain["settings_path"] is None:
                    toolchain["settings_path"] = str(path)
            except (json.JSONDecodeError, PermissionError):
                continue

    return toolchain


async def assess_candidates(
    eval_results: list[EvaluationResult],
    poc_results: list[PoCResult],
) -> list[IntegrationProposal]:
    """Assess poc_candidates and generate integration proposals."""
    # Filter to poc_candidates only
    candidates = [e for e in eval_results if e.verdict == Verdict.POC_CANDIDATE]
    if not candidates:
        return []

    # Build PoC lookup
    poc_lookup: dict[str, PoCResult] = {}
    for poc in poc_results:
        poc_lookup[poc.evaluation_result.scan_result.url] = poc

    # Skip tools where PoC failed
    viable = []
    for c in candidates:
        poc = poc_lookup.get(c.scan_result.url)
        if poc and not poc.quickstart_success:
            print(f"  Skipping {c.scan_result.name}: PoC quickstart failed")
            continue
        viable.append(c)

    if not viable:
        return []

    # Load current toolchain for context
    toolchain = _load_current_toolchain()

    integrator = build_integrator_agent()
    proposals = await _run_integrator(viable, poc_lookup, toolchain, integrator)

    # Save proposals
    save_proposals(proposals)
    return proposals


async def _run_integrator(
    candidates: list[EvaluationResult],
    poc_lookup: dict[str, PoCResult],
    toolchain: dict,
    integrator: AgentDefinition,
) -> list[IntegrationProposal]:
    """Dispatch integrator subagent to produce proposals."""
    # Build candidate summaries for the prompt
    candidate_data = []
    for c in candidates:
        sr = c.scan_result
        entry = {
            "name": sr.name,
            "url": sr.url,
            "source": sr.source.value,
            "description": sr.description[:500],
            "stars": sr.stars,
            "tags": sr.tags,
            "score_pct": f"{c.percentage:.0%}",
            "recommended_action": c.recommended_action,
        }
        poc = poc_lookup.get(sr.url)
        if poc:
            entry["poc"] = {
                "install_success": poc.install_success,
                "quickstart_success": poc.quickstart_success,
                "notes": poc.notes[:300],
            }
        candidate_data.append(entry)

    prompt = f"""Assess these poc_candidate tools for integration into the Claude Code toolchain.

## Current Toolchain
Existing MCP servers: {json.dumps(list(toolchain["mcp_servers"].keys()), ensure_ascii=False)}
Settings file: {toolchain["settings_path"] or "not found"}

## Candidates to Assess
{json.dumps(candidate_data, indent=2, ensure_ascii=False)}

Read the current settings.json to understand the full configuration before making proposals.
Return a JSON array of IntegrationProposal objects (max 3).
If a tool overlaps with an existing MCP server, check whether the new one is meaningfully better.
If no proposals are warranted, return an empty array: []"""

    opts = ClaudeAgentOptions(
        agents={"integrator": integrator},
        permission_mode="bypassPermissions",
    )

    response_text = ""
    async for message in query(prompt=prompt, options=opts):
        if hasattr(message, "content"):
            response_text += str(message.content)

    return _parse_proposals(response_text)


def _parse_proposals(response: str) -> list[IntegrationProposal]:
    """Extract IntegrationProposal objects from LLM response."""
    json_str = _extract_json_array(response)
    if not json_str:
        return []

    try:
        raw = json.loads(json_str)
        if not isinstance(raw, list):
            return []

        proposals = []
        for item in raw[:3]:  # Max 3 proposals per run
            proposals.append(IntegrationProposal(
                tool_name=item["tool_name"],
                tool_url=item.get("tool_url", ""),
                risk_level=RiskLevel(item["risk_level"]),
                category=item.get("category", "workflow_change"),
                title=item["title"],
                description=item.get("description", ""),
                config_diff=item.get("config_diff", ""),
                target_file=item.get("target_file", ""),
                existing_tool=item.get("existing_tool", ""),
            ))
        return proposals

    except (json.JSONDecodeError, KeyError, ValueError) as e:
        print(f"Warning: Could not parse integration proposals: {e}")
        return []


def _extract_json_array(text: str) -> str | None:
    """Extract the first JSON array from response text."""
    # Try ```json ... ``` block
    match = re.search(r"```(?:json)?\s*(\[[\s\S]*?\])\s*```", text)
    if match:
        return match.group(1)

    # Try bare JSON array
    match = re.search(r"\[[\s\S]*\"tool_name\"[\s\S]*\]", text)
    if match:
        return match.group(0)

    return None


def save_proposals(proposals: list[IntegrationProposal]) -> Path | None:
    """Save proposals to state/proposals/ as individual files."""
    if not proposals:
        return None

    PROPOSALS_DIR.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()

    for i, p in enumerate(proposals):
        filename = f"{today}-{i+1:02d}-{_slug(p.tool_name)}.json"
        path = PROPOSALS_DIR / filename
        path.write_text(
            p.model_dump_json(indent=2),
            encoding="utf-8",
        )

    # Also save a combined pending list
    pending_path = PROPOSALS_DIR / f"pending-{today}.json"
    pending_path.write_text(
        json.dumps(
            [p.model_dump(mode="json") for p in proposals],
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    return pending_path


def load_pending_proposals() -> list[IntegrationProposal]:
    """Load all pending proposals across all dates."""
    if not PROPOSALS_DIR.exists():
        return []

    pending = []
    for f in sorted(PROPOSALS_DIR.glob("pending-*.json")):
        try:
            raw = json.loads(f.read_text(encoding="utf-8"))
            for item in raw:
                p = IntegrationProposal(**item)
                if p.status == "pending":
                    pending.append(p)
        except (json.JSONDecodeError, Exception):
            continue

    return pending


def update_proposal_status(
    tool_name: str,
    new_status: str,
) -> bool:
    """Update a proposal's status (applied/rejected) in all pending files."""
    if not PROPOSALS_DIR.exists():
        return False

    updated = False
    for f in PROPOSALS_DIR.glob("pending-*.json"):
        try:
            raw = json.loads(f.read_text(encoding="utf-8"))
            changed = False
            for item in raw:
                if item["tool_name"] == tool_name and item["status"] == "pending":
                    item["status"] = new_status
                    changed = True
            if changed:
                f.write_text(
                    json.dumps(raw, indent=2, ensure_ascii=False),
                    encoding="utf-8",
                )
                updated = True
        except (json.JSONDecodeError, Exception):
            continue

    return updated


def _slug(name: str) -> str:
    """Convert tool name to filesystem-safe slug."""
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:40]
