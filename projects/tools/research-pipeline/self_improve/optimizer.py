"""DSPy prompt optimizer — learns from pipeline run history to improve evaluation quality.

Monthly manual trigger. Requires:
  pip install "dspy>=2.5"

Collects (evaluation_input, human_verdict) pairs from experience-metrics.json +
manual verdict overrides, then optimizes the evaluator prompt using:
  1. BootstrapFewShot — selects best few-shot examples
  2. MIPROv2 — optimizes rubric weights and instructions (optional, ≥30 examples)
"""

from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import PIPELINE_ROOT, STATE_DIR


# Versioned prompt storage
PROMPT_VERSIONS_DIR = PIPELINE_ROOT / "prompts" / "versions"
TRAINING_DATA_DIR = STATE_DIR / "training"
MIN_EXAMPLES_BOOTSTRAP = 10
MIN_EXAMPLES_MIPRO = 30


def collect_training_data() -> list[dict]:
    """Collect (input, verdict) pairs from evaluation results + human overrides.

    Training data structure:
    {
        "scan_result": {...},     # raw scan result as context
        "eval_scores": [...],     # model's original scores
        "model_verdict": "...",   # model's verdict
        "human_verdict": "...",   # human override (ground truth)
    }
    """
    data_file = TRAINING_DATA_DIR / "verdict-overrides.jsonl"
    if not data_file.exists():
        return []

    examples = []
    for line in data_file.read_text(encoding="utf-8").strip().split("\n"):
        if not line.strip():
            continue
        try:
            examples.append(json.loads(line))
        except json.JSONDecodeError:
            continue

    return examples


def record_human_verdict(
    tool_name: str,
    tool_url: str,
    model_verdict: str,
    human_verdict: str,
    scan_result: dict | None = None,
    eval_scores: list[dict] | None = None,
) -> None:
    """Record a human verdict override as training data for future optimization."""
    TRAINING_DATA_DIR.mkdir(parents=True, exist_ok=True)
    data_file = TRAINING_DATA_DIR / "verdict-overrides.jsonl"

    entry = {
        "timestamp": datetime.now().isoformat(),
        "tool_name": tool_name,
        "tool_url": tool_url,
        "model_verdict": model_verdict,
        "human_verdict": human_verdict,
        "scan_result": scan_result or {},
        "eval_scores": eval_scores or [],
    }

    with open(data_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _check_dspy() -> bool:
    """Check if DSPy is available."""
    try:
        import dspy  # noqa: F401
        return True
    except ImportError:
        return False


def optimize_evaluator(
    strategy: str = "bootstrap",  # "bootstrap" or "mipro"
    model: str = "ollama_chat/phi4-mini",
) -> Path | None:
    """Run DSPy optimization on the evaluator prompt.

    Args:
        strategy: "bootstrap" (BootstrapFewShot, ≥10 examples) or
                  "mipro" (MIPROv2, ≥30 examples)
        model: LiteLLM model string for DSPy

    Returns:
        Path to saved optimized prompt, or None if insufficient data / error.
    """
    if not _check_dspy():
        print("Error: DSPy not installed. Run: pip install 'dspy>=2.5'")
        return None

    import dspy

    examples = collect_training_data()
    min_required = MIN_EXAMPLES_MIPRO if strategy == "mipro" else MIN_EXAMPLES_BOOTSTRAP

    if len(examples) < min_required:
        print(f"Insufficient training data: {len(examples)}/{min_required} examples.")
        print(f"Record more human verdicts via record_human_verdict() or /research apply.")
        return None

    # Configure DSPy with local model
    lm = dspy.LM(model, temperature=0.1)
    dspy.configure(lm=lm)

    # Build training set
    trainset = _build_trainset(examples)

    # Define the evaluation signature
    class EvaluateDiscovery(dspy.Signature):
        """Evaluate a newly discovered AI tool for integration potential."""

        tool_description: str = dspy.InputField(desc="Sanitized description of the tool")
        tool_metadata: str = dspy.InputField(desc="Stars, source, tags, creation date")
        verdict: str = dspy.OutputField(desc="poc_candidate, watching, or not_applicable")
        reasoning: str = dspy.OutputField(desc="Brief justification for the verdict")

    # Build module
    evaluator_module = dspy.ChainOfThought(EvaluateDiscovery)

    # Optimize
    if strategy == "bootstrap":
        optimizer = dspy.BootstrapFewShot(
            metric=_verdict_accuracy,
            max_bootstrapped_demos=4,
            max_labeled_demos=8,
        )
    else:
        optimizer = dspy.MIPROv2(
            metric=_verdict_accuracy,
            num_candidates=5,
            init_temperature=0.7,
        )

    print(f"Running {strategy} optimization with {len(trainset)} examples...")
    optimized = optimizer.compile(evaluator_module, trainset=trainset)

    # Save optimized module
    save_path = _save_optimized(optimized, strategy, len(trainset))
    print(f"Optimized prompt saved to: {save_path}")

    return save_path


def _build_trainset(examples: list[dict]) -> list:
    """Convert raw training data to DSPy Examples."""
    import dspy

    trainset = []
    for ex in examples:
        sr = ex.get("scan_result", {})
        description = sr.get("description", ex.get("tool_name", ""))[:500]
        metadata = json.dumps({
            "stars": sr.get("stars"),
            "source": sr.get("source"),
            "tags": sr.get("tags", []),
        })

        trainset.append(dspy.Example(
            tool_description=description,
            tool_metadata=metadata,
            verdict=ex["human_verdict"],
            reasoning="",
        ).with_inputs("tool_description", "tool_metadata"))

    return trainset


def _verdict_accuracy(example, prediction, trace=None) -> bool:
    """Metric: does the predicted verdict match the human verdict?"""
    return prediction.verdict.strip().lower() == example.verdict.strip().lower()


def _save_optimized(module, strategy: str, num_examples: int) -> Path:
    """Save optimized module with versioning."""
    PROMPT_VERSIONS_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    version_dir = PROMPT_VERSIONS_DIR / f"{strategy}-{timestamp}"
    version_dir.mkdir(parents=True, exist_ok=True)

    # Save DSPy module state
    module.save(str(version_dir / "module.json"))

    # Save metadata
    meta = {
        "strategy": strategy,
        "timestamp": datetime.now().isoformat(),
        "num_examples": num_examples,
        "status": "active",
    }
    (version_dir / "meta.json").write_text(
        json.dumps(meta, indent=2),
        encoding="utf-8",
    )

    # Update "latest" symlink / pointer
    latest_file = PROMPT_VERSIONS_DIR / "latest.json"
    latest_file.write_text(
        json.dumps({"version": version_dir.name, **meta}, indent=2),
        encoding="utf-8",
    )

    return version_dir


def rollback(version_name: str | None = None) -> bool:
    """Rollback to a previous prompt version.

    If version_name is None, rolls back to the version before current "latest".
    """
    if not PROMPT_VERSIONS_DIR.exists():
        print("No prompt versions found.")
        return False

    latest_file = PROMPT_VERSIONS_DIR / "latest.json"
    if not latest_file.exists():
        print("No active optimized prompt to rollback from.")
        return False

    current = json.loads(latest_file.read_text(encoding="utf-8"))
    current_name = current.get("version", "")

    if version_name:
        target = PROMPT_VERSIONS_DIR / version_name
        if not target.exists():
            print(f"Version not found: {version_name}")
            return False
    else:
        # Find the previous version
        versions = sorted(
            [d for d in PROMPT_VERSIONS_DIR.iterdir()
             if d.is_dir() and d.name != current_name],
            key=lambda d: d.name,
            reverse=True,
        )
        if not versions:
            print("No previous version to rollback to.")
            return False
        target = versions[0]

    # Load target metadata
    target_meta = json.loads((target / "meta.json").read_text(encoding="utf-8"))

    # Update latest pointer
    latest_file.write_text(
        json.dumps({"version": target.name, **target_meta}, indent=2),
        encoding="utf-8",
    )

    # Mark rolled-back version
    current_dir = PROMPT_VERSIONS_DIR / current_name
    if current_dir.exists():
        current_meta_path = current_dir / "meta.json"
        if current_meta_path.exists():
            current_meta = json.loads(current_meta_path.read_text(encoding="utf-8"))
            current_meta["status"] = "rolled_back"
            current_meta_path.write_text(
                json.dumps(current_meta, indent=2), encoding="utf-8"
            )

    print(f"Rolled back from {current_name} to {target.name}")
    return True


def list_versions() -> list[dict]:
    """List all saved prompt optimization versions."""
    if not PROMPT_VERSIONS_DIR.exists():
        return []

    versions = []
    for d in sorted(PROMPT_VERSIONS_DIR.iterdir()):
        if not d.is_dir():
            continue
        meta_path = d / "meta.json"
        if meta_path.exists():
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            versions.append({"name": d.name, **meta})

    return versions


def training_data_stats() -> dict:
    """Return stats about available training data."""
    examples = collect_training_data()
    if not examples:
        return {"total": 0, "ready_for_bootstrap": False, "ready_for_mipro": False}

    verdicts = {}
    for ex in examples:
        v = ex.get("human_verdict", "unknown")
        verdicts[v] = verdicts.get(v, 0) + 1

    return {
        "total": len(examples),
        "verdict_distribution": verdicts,
        "ready_for_bootstrap": len(examples) >= MIN_EXAMPLES_BOOTSTRAP,
        "ready_for_mipro": len(examples) >= MIN_EXAMPLES_MIPRO,
    }


# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------


def main():
    import sys

    if len(sys.argv) < 2:
        print("Usage: python optimizer.py [optimize|rollback|versions|stats]")
        print("  optimize [bootstrap|mipro]  — Run prompt optimization")
        print("  rollback [version-name]     — Revert to previous prompt version")
        print("  versions                    — List all prompt versions")
        print("  stats                       — Show training data statistics")
        sys.exit(1)

    action = sys.argv[1]

    if action == "optimize":
        strategy = sys.argv[2] if len(sys.argv) > 2 else "bootstrap"
        optimize_evaluator(strategy=strategy)

    elif action == "rollback":
        version = sys.argv[2] if len(sys.argv) > 2 else None
        rollback(version)

    elif action == "versions":
        for v in list_versions():
            status_mark = "✓" if v.get("status") == "active" else "○"
            print(f"  {status_mark} {v['name']} ({v.get('strategy', '?')}, {v.get('num_examples', '?')} examples)")

    elif action == "stats":
        stats = training_data_stats()
        print(f"Training examples: {stats['total']}")
        if stats.get("verdict_distribution"):
            for v, c in stats["verdict_distribution"].items():
                print(f"  {v}: {c}")
        print(f"Ready for BootstrapFewShot: {'✓' if stats['ready_for_bootstrap'] else '✗'} (need {MIN_EXAMPLES_BOOTSTRAP})")
        print(f"Ready for MIPROv2: {'✓' if stats['ready_for_mipro'] else '✗'} (need {MIN_EXAMPLES_MIPRO})")

    else:
        print(f"Unknown action: {action}")
        sys.exit(1)


if __name__ == "__main__":
    main()
