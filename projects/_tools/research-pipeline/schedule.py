"""Schedule management — register/unregister Windows Task Scheduler tasks + Telegram alerts."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from config import PIPELINE_ROOT, STATE_DIR


# Task Scheduler names
DAILY_TASK = "Research Pipeline - Daily Quick Scan"
WEEKLY_TASK = "Research Pipeline - Weekly Deep Scan"

# Paths
GIT_BASH = r"C:\Program Files\Git\bin\bash.exe"
SCRIPTS_DIR = PIPELINE_ROOT / "scripts"
WORKING_DIR = str(PIPELINE_ROOT).replace("/", "\\")


def register_daily(
    time: str = "14:00",  # UTC+8 (= UTC 06:00)
) -> bool:
    """Register daily quick-scan with Windows Task Scheduler."""
    script = str(SCRIPTS_DIR / "daily-scan.sh").replace("\\", "/")

    cmd = [
        "schtasks", "/Create", "/F",
        "/TN", DAILY_TASK,
        "/TR", f'"{GIT_BASH}" "{script}"',
        "/SC", "DAILY",
        "/ST", time,
        "/RL", "HIGHEST",
    ]

    return _run_schtasks(cmd, DAILY_TASK)


def register_weekly(
    day: str = "SUN",
    time: str = "10:00",  # UTC+8 (= UTC 02:00)
) -> bool:
    """Register weekly deep-scan with Windows Task Scheduler."""
    script = str(SCRIPTS_DIR / "weekly-scan.sh").replace("\\", "/")

    cmd = [
        "schtasks", "/Create", "/F",
        "/TN", WEEKLY_TASK,
        "/TR", f'"{GIT_BASH}" "{script}"',
        "/SC", "WEEKLY",
        "/D", day,
        "/ST", time,
        "/RL", "HIGHEST",
    ]

    return _run_schtasks(cmd, WEEKLY_TASK)


def unregister(task_name: str) -> bool:
    """Remove a scheduled task."""
    cmd = ["schtasks", "/Delete", "/F", "/TN", task_name]
    return _run_schtasks(cmd, task_name, action="unregistered")


def status() -> dict:
    """Query current Task Scheduler status for pipeline tasks."""
    result = {}
    for name in [DAILY_TASK, WEEKLY_TASK]:
        try:
            proc = subprocess.run(
                ["schtasks", "/Query", "/TN", name, "/FO", "LIST"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if proc.returncode == 0:
                info = _parse_task_info(proc.stdout)
                result[name] = {"registered": True, **info}
            else:
                result[name] = {"registered": False}
        except (subprocess.TimeoutExpired, FileNotFoundError):
            result[name] = {"registered": False, "error": "schtasks unavailable"}

    return result


def setup_all() -> dict[str, bool]:
    """Register both daily and weekly tasks. Returns success status for each."""
    return {
        "daily": register_daily(),
        "weekly": register_weekly(),
    }


# ---------------------------------------------------------------------------
# Telegram failure notification
# ---------------------------------------------------------------------------


TELEGRAM_CONFIG_PATH = Path.home() / ".claude" / "telegram" / "config.json"


def load_telegram_config() -> dict | None:
    """Load Telegram bot config if available."""
    if not TELEGRAM_CONFIG_PATH.exists():
        return None
    try:
        return json.loads(TELEGRAM_CONFIG_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, PermissionError):
        return None


def send_failure_alert(
    mode: str,
    error: str,
    log_file: str = "",
) -> bool:
    """Send pipeline failure alert via Telegram bot (if configured).

    Uses curl to call the Telegram Bot API directly — no Python dependency needed.
    This runs from shell scripts where the full Python env may not be available.
    """
    config = load_telegram_config()
    if not config or "bot_token" not in config:
        return False

    chat_id = config.get("owner_chat_id") or config.get("chat_id")
    if not chat_id:
        return False

    token = config["bot_token"]
    error_short = error[:500].replace('"', '\\"')

    message = (
        f"⚠️ Research Pipeline Failed\n\n"
        f"Mode: {mode}\n"
        f"Error: {error_short}\n"
    )
    if log_file:
        message += f"Log: {log_file}\n"

    try:
        proc = subprocess.run(
            [
                "curl", "-s", "-X", "POST",
                f"https://api.telegram.org/bot{token}/sendMessage",
                "-d", f"chat_id={chat_id}",
                "-d", f"text={message}",
                "-d", "parse_mode=",
            ],
            capture_output=True,
            text=True,
            timeout=15,
        )
        return proc.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


# ---------------------------------------------------------------------------
# Shell helper: generate notification snippet for wrapper scripts
# ---------------------------------------------------------------------------


def generate_notify_snippet() -> str:
    """Generate bash snippet to add Telegram notification to wrapper scripts."""
    return '''
# Telegram failure notification
notify_failure() {
    local MODE="$1"
    local ERROR="$2"
    local LOG="$3"

    # Check if Python notification helper is available
    cd "$PIPELINE_DIR"
    python -c "
from schedule import send_failure_alert
send_failure_alert('$MODE', '$ERROR', '$LOG')
" 2>/dev/null || true
}

# Call at the end of the script:
# if [ $EXIT_CODE -ne 0 ]; then
#     notify_failure "$MODE" "Pipeline exited with code $EXIT_CODE" "$LOG_FILE"
# fi
'''


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _run_schtasks(cmd: list[str], name: str, action: str = "registered") -> bool:
    """Execute schtasks command and report result."""
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=15,
        )
        if proc.returncode == 0:
            print(f"Task {action}: {name}")
            return True
        else:
            print(f"Failed to {action.rstrip('ed')} {name}: {proc.stderr.strip()}")
            return False
    except FileNotFoundError:
        print("Error: schtasks not found. Are you on Windows?")
        return False
    except subprocess.TimeoutExpired:
        print("Error: schtasks timed out")
        return False


def _parse_task_info(output: str) -> dict:
    """Parse schtasks /FO LIST output into key-value pairs."""
    info = {}
    for line in output.strip().split("\n"):
        if ":" in line:
            key, _, value = line.partition(":")
            key = key.strip().lower().replace(" ", "_")
            info[key] = value.strip()
    return info


# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------


def main():
    """CLI entrypoint for schedule management."""
    if len(sys.argv) < 2:
        print("Usage: python schedule.py [setup|status|teardown|notify-test]")
        sys.exit(1)

    action = sys.argv[1]

    if action == "setup":
        results = setup_all()
        for name, ok in results.items():
            symbol = "✓" if ok else "✗"
            print(f"  {symbol} {name}")

    elif action == "status":
        info = status()
        for name, data in info.items():
            reg = "✓" if data.get("registered") else "✗"
            print(f"\n{reg} {name}")
            if data.get("registered"):
                for k, v in data.items():
                    if k != "registered":
                        print(f"  {k}: {v}")

    elif action == "teardown":
        unregister(DAILY_TASK)
        unregister(WEEKLY_TASK)

    elif action == "notify-test":
        ok = send_failure_alert("test", "This is a test alert from schedule.py")
        print("Notification sent" if ok else "No Telegram config or send failed")

    else:
        print(f"Unknown action: {action}")
        sys.exit(1)


if __name__ == "__main__":
    main()
