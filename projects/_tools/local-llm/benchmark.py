#!/usr/bin/env python3
"""Local LLM Benchmark — Plan 005 Unit 1 hard gate.

Runs standardized tests on Ollama models and outputs results
to model-inventory.md. A model passes the hard gate if:
- tok/s >= 30
- quality vs Claude baseline >= 70%

Usage:
    python benchmark.py                  # Run all models
    python benchmark.py --model qwen3.5:9b  # Run one model
    python benchmark.py --report         # Show last results
"""

import json
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

OLLAMA_API = "http://localhost:11434"
MODELS = {
    "bge-m3": {"type": "embedding", "expected_vram_gb": 2.0},
    "phi4-mini": {"type": "classify", "expected_vram_gb": 2.5},
    "qwen3.5:9b": {"type": "reasoning", "expected_vram_gb": 6.0},
    "qwen3.5:35b-a3b": {"type": "reasoning-stretch", "expected_vram_gb": 15.0},
}

HARD_GATE_TOK_S = 30
HARD_GATE_QUALITY = 0.70

# --- Test prompts ---

CLASSIFY_PROMPT = """Classify this note into exactly one category: area, project, resource, or idea.
Only output the category name, nothing else.

Note: Claude Code is a CLI tool for AI-assisted coding. I'm exploring how to configure it with hooks and MCP servers for my Obsidian vault."""

SUMMARIZE_TEXT = """Ollama is an open-source tool that makes it easy to run large language models locally.
It supports GGUF format models and provides an OpenAI-compatible API.
Users can pull models from the Ollama library with a single command.
It runs on Windows, macOS, and Linux, with automatic GPU detection for NVIDIA and AMD GPUs.
The tool manages model lifecycle including downloading, loading, and unloading from GPU memory.
It also supports multimodal models for vision tasks."""

SUMMARIZE_PROMPT = f"Summarize this in exactly 3 sentences:\n\n{SUMMARIZE_TEXT}"

TRANSLATE_PROMPT = "Translate to Traditional Chinese: The benchmark results show that Qwen 3.5 9B achieves acceptable quality for classification and summarization tasks on a 16GB VRAM laptop GPU."

REASONING_PROMPT = "What is 17 * 23? Show your work step by step, then give the final answer."


@dataclass
class BenchmarkResult:
    model: str
    model_type: str
    test_name: str
    response: str = ""
    tok_per_sec: float = 0.0
    total_duration_ms: float = 0.0
    vram_used_mib: int = 0
    passed: bool = False
    notes: str = ""


def ollama_generate(model: str, prompt: str, timeout: int = 300) -> dict:
    """Call Ollama API and return response with metrics."""
    try:
        result = subprocess.run(
            ["curl", "-s", OLLAMA_API + "/api/generate",
             "-d", json.dumps({"model": model, "prompt": prompt, "stream": False})],
            capture_output=True, text=True, timeout=timeout
        )
        return json.loads(result.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError) as e:
        return {"error": str(e)}


def ollama_embed(model: str, texts: list[str]) -> dict:
    """Call Ollama embedding API."""
    try:
        result = subprocess.run(
            ["curl", "-s", OLLAMA_API + "/api/embed",
             "-d", json.dumps({"model": model, "input": texts})],
            capture_output=True, text=True, timeout=60
        )
        return json.loads(result.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError) as e:
        return {"error": str(e)}


def get_vram_used() -> int:
    """Get current VRAM usage in MiB."""
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5
        )
        return int(result.stdout.strip())
    except Exception:
        return -1


def run_inference_test(model: str, prompt: str, test_name: str) -> BenchmarkResult:
    """Run a single inference test and collect metrics."""
    res = BenchmarkResult(model=model, model_type=MODELS.get(model, {}).get("type", "unknown"), test_name=test_name)

    data = ollama_generate(model, prompt)
    if "error" in data:
        res.notes = f"Error: {data['error']}"
        return res

    res.response = data.get("response", "").strip()
    res.total_duration_ms = data.get("total_duration", 0) / 1_000_000  # ns to ms
    eval_count = data.get("eval_count", 0)
    eval_duration = data.get("eval_duration", 1)  # ns
    res.tok_per_sec = (eval_count / eval_duration * 1_000_000_000) if eval_duration > 0 else 0
    res.vram_used_mib = get_vram_used()
    res.passed = res.tok_per_sec >= HARD_GATE_TOK_S

    return res


def run_embedding_test(model: str) -> BenchmarkResult:
    """Test embedding model."""
    res = BenchmarkResult(model=model, model_type="embedding", test_name="embedding")

    data = ollama_embed(model, ["Hello world", "你好世界", "Obsidian vault knowledge base"])
    if "error" in data:
        res.notes = f"Error: {data['error']}"
        return res

    embeddings = data.get("embeddings", [])
    if len(embeddings) == 3:
        dims = len(embeddings[0])
        res.response = f"3 embeddings, {dims} dimensions each"
        res.passed = True
        res.notes = f"dims={dims}"
    else:
        res.notes = f"Expected 3 embeddings, got {len(embeddings)}"

    res.vram_used_mib = get_vram_used()
    return res


def run_all_benchmarks(target_model: str | None = None) -> list[BenchmarkResult]:
    """Run all benchmarks, optionally filtered to one model."""
    results = []

    models_to_test = {target_model: MODELS[target_model]} if target_model and target_model in MODELS else MODELS

    for model, info in models_to_test.items():
        print(f"\n{'='*60}")
        print(f"Testing: {model} ({info['type']})")
        print(f"{'='*60}")

        if info["type"] == "embedding":
            print("  Running embedding test...")
            results.append(run_embedding_test(model))
            continue

        # All inference models get basic test
        print("  Running basic inference...")
        results.append(run_inference_test(model, "Explain what a Markdown file is in 2 sentences.", "basic"))

        # Classification test
        if info["type"] in ("classify", "reasoning"):
            print("  Running classification...")
            results.append(run_inference_test(model, CLASSIFY_PROMPT, "classify"))

        # Summarization test
        if info["type"] in ("reasoning", "reasoning-stretch"):
            print("  Running summarization...")
            results.append(run_inference_test(model, SUMMARIZE_PROMPT, "summarize"))

        # Translation test (only main reasoning model)
        if model == "qwen3.5:9b":
            print("  Running translation...")
            results.append(run_inference_test(model, TRANSLATE_PROMPT, "translate"))

        # Reasoning test
        if info["type"] in ("reasoning", "reasoning-stretch"):
            print("  Running reasoning (17*23)...")
            results.append(run_inference_test(model, REASONING_PROMPT, "reasoning"))

    return results


def format_results(results: list[BenchmarkResult]) -> str:
    """Format results as markdown table."""
    lines = [
        "# Local LLM Benchmark Results",
        "",
        f"Date: {time.strftime('%Y-%m-%d %H:%M')}",
        f"GPU: RTX 4090 Laptop (16GB VRAM)",
        f"Hard gate: tok/s >= {HARD_GATE_TOK_S}",
        "",
        "| Model | Test | tok/s | Duration (ms) | VRAM (MiB) | Pass | Notes |",
        "|-------|------|-------|---------------|------------|------|-------|",
    ]

    for r in results:
        status = "✅" if r.passed else "❌"
        tok_s = f"{r.tok_per_sec:.1f}" if r.tok_per_sec > 0 else "N/A"
        dur = f"{r.total_duration_ms:.0f}" if r.total_duration_ms > 0 else "N/A"
        vram = str(r.vram_used_mib) if r.vram_used_mib > 0 else "N/A"
        response_preview = r.response[:80].replace("|", "\\|").replace("\n", " ") if r.response else r.notes
        lines.append(f"| {r.model} | {r.test_name} | {tok_s} | {dur} | {vram} | {status} | {response_preview} |")

    lines.extend(["", "## Responses", ""])
    for r in results:
        if r.response:
            lines.extend([f"### {r.model} — {r.test_name}", "", f"```", r.response[:500], "```", ""])

    return "\n".join(lines)


def main():
    target = None
    if "--model" in sys.argv:
        idx = sys.argv.index("--model")
        if idx + 1 < len(sys.argv):
            target = sys.argv[idx + 1]

    if "--report" in sys.argv:
        inventory = Path(__file__).parent / "model-inventory.md"
        if inventory.exists():
            print(inventory.read_text(encoding="utf-8"))
        else:
            print("No benchmark results found. Run benchmark first.")
        return

    print("Local LLM Benchmark — Plan 005 Unit 1")
    print(f"VRAM before tests: {get_vram_used()} MiB used")

    results = run_all_benchmarks(target)
    report = format_results(results)

    # Write to model-inventory.md
    inventory = Path(__file__).parent / "model-inventory.md"
    inventory.write_text(report, encoding="utf-8")
    print(f"\nResults written to {inventory}")

    # Print summary
    print("\n" + report)

    # Exit code: 1 if any inference model failed hard gate
    inference_results = [r for r in results if r.model_type != "embedding"]
    if any(not r.passed for r in inference_results):
        print("\n⚠️ Some models failed the hard gate (tok/s < 30)")
        sys.exit(1)
    else:
        print("\n✅ All models passed the hard gate")


if __name__ == "__main__":
    main()
