"""Experience recorder — tracks pipeline run metrics for learning."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from config import STATE_DIR, VAULT_ROOT


EXPERIENCE_FILE = VAULT_ROOT / "resources" / "research-pipeline-experience.md"


def record_run(
    run_id: str,
    mode: str,
    scan_count: int,
    new_count: int,
    eval_count: int = 0,
    poc_count: int = 0,
    poc_success: int = 0,
    proposals_generated: int = 0,
    proposals_accepted: int = 0,
    proposals_rejected: int = 0,
    errors: list[str] | None = None,
    notes: str = "",
) -> None:
    """Append run metrics to the experience file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    entry = f"""
### Run {run_id} — {timestamp}

| Metric | Value |
|--------|-------|
| Mode | {mode} |
| Sources scanned | 4 |
| Items found | {scan_count} |
| New (not seen before) | {new_count} |
| Evaluated | {eval_count} |
| PoC executed | {poc_count} |
| PoC succeeded | {poc_success} |
| Proposals generated | {proposals_generated} |
| Proposals accepted | {proposals_accepted} |
| Proposals rejected | {proposals_rejected} |
| Errors | {len(errors) if errors else 0} |

"""
    if errors:
        entry += "**Errors:**\n"
        for e in errors[:5]:
            entry += f"- {e[:200]}\n"
        entry += "\n"

    if notes:
        entry += f"**Notes:** {notes}\n\n"

    entry += "---\n"

    # Create file with frontmatter if it doesn't exist
    if not EXPERIENCE_FILE.exists():
        header = """---
title: "研究管線運行經驗"
type: resource
tags: [research-pipeline, experience, metrics, auto-generated]
created: "{date}"
updated: "{date}"
status: active
summary: "研究管線每次運行的 metrics 和學習記錄"
related: ["[[tech-research-squad]]", "[[local-llm-deployment]]"]
---

# 研究管線運行經驗

此文件由管線自動維護，記錄每次運行的 metrics 以供 DSPy 最佳化和人工回顧。

""".format(date=datetime.now().strftime("%Y-%m-%d"))
        EXPERIENCE_FILE.parent.mkdir(parents=True, exist_ok=True)
        EXPERIENCE_FILE.write_text(header, encoding="utf-8")

    # Append the new entry
    with open(EXPERIENCE_FILE, "a", encoding="utf-8") as f:
        f.write(entry)

    # Also save structured JSON for DSPy consumption
    _save_structured(run_id, mode, scan_count, new_count, eval_count,
                     poc_count, poc_success, proposals_generated,
                     proposals_accepted, proposals_rejected, errors)


def _save_structured(run_id, mode, scan_count, new_count, eval_count,
                     poc_count, poc_success, proposals_generated,
                     proposals_accepted, proposals_rejected, errors):
    """Save structured metrics to JSON for future DSPy training."""
    metrics_file = STATE_DIR / "experience-metrics.json"

    existing = []
    if metrics_file.exists():
        try:
            existing = json.loads(metrics_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            existing = []

    existing.append({
        "run_id": run_id,
        "timestamp": datetime.now().isoformat(),
        "mode": mode,
        "scan_count": scan_count,
        "new_count": new_count,
        "eval_count": eval_count,
        "poc_count": poc_count,
        "poc_success": poc_success,
        "proposals_generated": proposals_generated,
        "proposals_accepted": proposals_accepted,
        "proposals_rejected": proposals_rejected,
        "error_count": len(errors) if errors else 0,
    })

    metrics_file.write_text(
        json.dumps(existing, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
