"""Evaluation rubric — 5-dimension scoring for tool/paper assessment."""

from __future__ import annotations

from config import EVAL_THRESHOLD_POC, EVAL_THRESHOLD_WATCHING
from models import EvaluationResult, EvaluationScore, ScanResult, Verdict

# Dimensions for GitHub repos (5D)
REPO_DIMENSIONS = [
    {
        "name": "Relevance",
        "weight": 1,
        "description": (
            "Does this tool solve a concrete problem in Agent frameworks or RAG/knowledge "
            "management? How well does it fit with the current Claude Code toolchain "
            "(14 plugins, 47 agents, MCP servers, Obsidian vault)?"
        ),
        "scoring": "0=unrelated, 3=tangentially related, 5=related domain, 7=directly useful, 10=fills a known gap",
    },
    {
        "name": "Maturity",
        "weight": 1,
        "description": (
            "How production-ready is this project? Consider GitHub stars, commit frequency, "
            "issue response time, release history, and community size."
        ),
        "scoring": "0=abandoned, 3=early prototype, 5=beta with active development, 7=stable with community, 10=battle-tested",
    },
    {
        "name": "Integration Effort",
        "weight": 1,
        "description": (
            "How easy is it to integrate? Consider: pip install simplicity, documentation "
            "quality, Python 3.14 compatibility, Docker/Ollama support, MCP compatibility."
        ),
        "scoring": "0=massive effort, 3=significant work, 5=moderate effort, 7=straightforward, 10=drop-in replacement",
    },
    {
        "name": "Maintenance Risk",
        "weight": 1,
        "description": (
            "How sustainable is this project? Consider: maintainer activity, funding source, "
            "license restrictions, bus factor, corporate backing."
        ),
        "scoring": "0=single abandoned dev, 3=small team no funding, 5=active small team, 7=company-backed, 10=major org with LTS",
    },
    {
        "name": "Unique Value",
        "weight": 1,
        "description": (
            "What does this offer that our current toolchain cannot easily replicate? "
            "Could we achieve the same with existing tools (compound-engineering agents, "
            "WebSearch, claude-mem, obsidian-agent)?"
        ),
        "scoring": "0=fully replaceable, 3=minor convenience, 5=noticeable improvement, 7=significant capability, 10=entirely new capability",
    },
]

# Dimensions for arXiv papers (3D — skip Maturity and Maintenance Risk)
PAPER_DIMENSIONS = [d for d in REPO_DIMENSIONS if d["name"] in ("Relevance", "Integration Effort", "Unique Value")]


def get_dimensions(is_paper: bool) -> list[dict]:
    return PAPER_DIMENSIONS if is_paper else REPO_DIMENSIONS


def compute_verdict(scores: list[EvaluationScore], is_paper: bool) -> Verdict:
    """Compute verdict from scores using normalized 70% threshold."""
    total = sum(s.score for s in scores)
    max_possible = len(scores) * 10
    percentage = total / max_possible if max_possible > 0 else 0

    if percentage >= EVAL_THRESHOLD_POC:
        return Verdict.POC_CANDIDATE
    elif percentage >= EVAL_THRESHOLD_WATCHING:
        return Verdict.WATCHING
    else:
        return Verdict.NOT_APPLICABLE


def build_evaluation_result(
    scan_result: ScanResult,
    scores: list[EvaluationScore],
) -> EvaluationResult:
    """Build a complete EvaluationResult from scores."""
    total = sum(s.score for s in scores)
    max_score = len(scores) * 10
    percentage = total / max_score if max_score > 0 else 0
    verdict = compute_verdict(scores, scan_result.is_paper)

    return EvaluationResult(
        scan_result=scan_result,
        scores=scores,
        total_score=total,
        max_score=max_score,
        percentage=round(percentage, 3),
        verdict=verdict,
    )


def format_rubric_prompt(is_paper: bool) -> str:
    """Format the rubric as a prompt section for the evaluator subagent."""
    dims = get_dimensions(is_paper)
    dim_type = "paper" if is_paper else "tool/repository"

    lines = [
        f"## Evaluation Rubric ({len(dims)} dimensions for {dim_type})",
        "",
        "Score each dimension 0-10 with reasoning. Return JSON.",
        "",
    ]

    for d in dims:
        lines.append(f"### {d['name']}")
        lines.append(d["description"])
        lines.append(f"Scoring guide: {d['scoring']}")
        lines.append("")

    lines.extend([
        "## Threshold",
        f"- >= {EVAL_THRESHOLD_POC*100:.0f}% total → poc_candidate (deep evaluation + PoC)",
        f"- >= {EVAL_THRESHOLD_WATCHING*100:.0f}% total → watching (track for future)",
        f"- < {EVAL_THRESHOLD_WATCHING*100:.0f}% total → not_applicable (skip)",
        "",
        "## Output Format",
        "```json",
        "{",
        '  "scores": [',
        '    {"dimension": "Relevance", "score": 7, "reasoning": "..."},',
        '    {"dimension": "Maturity", "score": 5, "reasoning": "..."},',
        "    ...",
        "  ],",
        '  "recommended_action": "Brief recommendation for what to do with this tool"',
        "}",
        "```",
    ])

    return "\n".join(lines)
