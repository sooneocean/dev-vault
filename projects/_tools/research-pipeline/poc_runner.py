"""PoC Runner — executes tool installation and verification in Docker sandbox."""

from __future__ import annotations

import json
import subprocess
import time
from datetime import date
from pathlib import Path

from config import PIPELINE_ROOT, STATE_DIR
from models import EvaluationResult, PoCResult

DOCKERFILES_DIR = PIPELINE_ROOT / "dockerfiles"
TIMEOUT_SECONDS = 300  # 5 minutes max per PoC


def detect_runtime(eval_result: EvaluationResult) -> str:
    """Detect whether a tool needs Python or Node runtime."""
    metadata = eval_result.scan_result.raw_metadata
    language = metadata.get("language", "").lower()
    tags = [t.lower() for t in eval_result.scan_result.tags]

    if language in ("javascript", "typescript") or "npm" in tags:
        return "node"
    return "python"  # default


def extract_package_name(eval_result: EvaluationResult) -> str:
    """Extract the pip/npm installable package name from scan result."""
    name = eval_result.scan_result.name
    url = eval_result.scan_result.url

    # For GitHub repos, use the repo name (often matches PyPI/npm package)
    if "github.com" in url:
        parts = url.rstrip("/").split("/")
        if len(parts) >= 2:
            return parts[-1].lower().replace("_", "-")

    return name.lower().replace(" ", "-")


def run_poc(eval_result: EvaluationResult) -> PoCResult:
    """Execute a PoC for a single evaluated tool in Docker sandbox.

    Security model:
    - Build stage: network allowed (download dependencies)
    - Run stage: --network=none (no exfiltration)
    - No host filesystem mounts (tmpfs workspace only)
    - No host env vars passed to container
    - Resource limits: 4GB RAM, 2 CPUs, 5 min timeout
    - --security-opt=no-new-privileges
    """
    runtime = detect_runtime(eval_result)
    package_name = extract_package_name(eval_result)
    dockerfile = DOCKERFILES_DIR / f"poc-{runtime}.Dockerfile"

    if not dockerfile.exists():
        return PoCResult(
            evaluation_result=eval_result,
            install_success=False,
            quickstart_success=False,
            execution_time_seconds=0,
            notes=f"Dockerfile not found: {dockerfile}",
        )

    # Check Docker is available
    try:
        subprocess.run(
            ["docker", "info"],
            capture_output=True,
            timeout=10,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return PoCResult(
            evaluation_result=eval_result,
            install_success=False,
            quickstart_success=False,
            execution_time_seconds=0,
            notes="Docker not available or not running",
        )

    image_tag = f"poc-{package_name}:{date.today().isoformat()}"
    start_time = time.time()

    # Phase 1: Build (network allowed)
    build_result = _docker_build(dockerfile, package_name, image_tag)
    if not build_result["success"]:
        return PoCResult(
            evaluation_result=eval_result,
            install_success=False,
            quickstart_success=False,
            execution_time_seconds=time.time() - start_time,
            notes=f"Build failed: {build_result['error'][:500]}",
        )

    # Phase 2: Run (network=none, resource-limited)
    run_result = _docker_run(image_tag, package_name, runtime)

    elapsed = time.time() - start_time

    # Cleanup image
    subprocess.run(["docker", "rmi", image_tag], capture_output=True)

    return PoCResult(
        evaluation_result=eval_result,
        install_success=build_result["success"],
        quickstart_success=run_result["success"],
        execution_time_seconds=round(elapsed, 1),
        notes=run_result.get("output", "")[:1000],
    )


def _docker_build(
    dockerfile: Path, package_name: str, image_tag: str
) -> dict:
    """Build Docker image with the target package installed."""
    try:
        result = subprocess.run(
            [
                "docker", "build",
                "-f", str(dockerfile),
                "--build-arg", f"PACKAGE_NAME={package_name}",
                "-t", image_tag,
                str(DOCKERFILES_DIR),
            ],
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
        )
        return {
            "success": result.returncode == 0,
            "output": result.stdout[-500:] if result.stdout else "",
            "error": result.stderr[-500:] if result.stderr else "",
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "output": "", "error": "Build timed out"}
    except Exception as e:
        return {"success": False, "output": "", "error": str(e)}


def _docker_run(image_tag: str, package_name: str, runtime: str) -> dict:
    """Run the PoC verification in a sandboxed container."""
    # Build the import test command
    if runtime == "python":
        # Normalize package name for import (hyphens → underscores)
        import_name = package_name.replace("-", "_")
        cmd = ["python", "-c", f"import {import_name}; print('{import_name} imported OK')"]
    else:
        cmd = ["node", "-e", f"require('{package_name}'); console.log('{package_name} required OK')"]

    try:
        result = subprocess.run(
            [
                "docker", "run",
                "--rm",
                "--network=none",                         # No network in run phase
                "--memory=4g",
                "--cpus=2",
                "--security-opt=no-new-privileges",
                "--tmpfs", "/workspace:rw,size=1g",       # tmpfs, no host mount
                "--env", "HOME=/workspace",
                "--env", "PATH=/usr/local/bin:/usr/bin:/bin",
                "--env", "LANG=C.UTF-8",
                image_tag,
            ] + cmd,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
        )
        return {
            "success": result.returncode == 0,
            "output": (result.stdout + result.stderr)[:1000],
        }
    except subprocess.TimeoutExpired:
        # Kill the container
        subprocess.run(
            ["docker", "kill", f"$(docker ps -q --filter ancestor={image_tag})"],
            capture_output=True,
            shell=True,
        )
        return {"success": False, "output": "Execution timed out (>5min)"}
    except Exception as e:
        return {"success": False, "output": str(e)}


def save_poc_results(results: list[PoCResult]) -> Path:
    """Save PoC results to state directory."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    path = STATE_DIR / f"poc-results-{date.today().isoformat()}.json"
    data = [r.model_dump(mode="json") for r in results]
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return path
