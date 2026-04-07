#!/usr/bin/env python3
"""ComfyUI Process Launcher"""

import subprocess
import sys
import time
import asyncio
from pathlib import Path
from typing import Optional

from .client import ComfyUIClient


PORTABLE_PATH = Path("C:/Program Files/ComfyUI/ComfyUI_windows_portable/ComfyUI")
ELECTRON_PATH = Path("C:/Users/User/Projects/comfyui")


async def wait_for_server(
    host: str = "127.0.0.1",
    port: int = 8188,
    timeout: float = 60,
    check_interval: float = 1
) -> bool:
    """Wait for ComfyUI server to be ready"""
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            async with ComfyUIClient(host, port) as client:
                await client.get_system_stats()
                return True
        except Exception:
            pass

        await asyncio.sleep(check_interval)

    return False


def launch_portable(
    host: str = "127.0.0.1",
    port: int = 8188
) -> subprocess.Popen:
    """Launch ComfyUI from Portable version"""

    if not PORTABLE_PATH.exists():
        raise FileNotFoundError(f"Portable ComfyUI not found at {PORTABLE_PATH}")

    cmd = [
        sys.executable,
        str(PORTABLE_PATH / "main.py"),
        "--listen", host,
        "--port", str(port),
    ]

    print(f"Starting ComfyUI from: {PORTABLE_PATH}")
    print(f"Command: {' '.join(cmd)}")

    process = subprocess.Popen(
        cmd,
        cwd=str(PORTABLE_PATH),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    return process


def launch_electron() -> subprocess.Popen:
    """Launch ComfyUI Electron version"""

    if not ELECTRON_PATH.exists():
        raise FileNotFoundError(f"Electron ComfyUI not found at {ELECTRON_PATH}")

    exe_path = ELECTRON_PATH / "ComfyUI.exe"
    if not exe_path.exists():
        raise FileNotFoundError(f"ComfyUI.exe not found at {exe_path}")

    print(f"Starting ComfyUI from: {exe_path}")

    process = subprocess.Popen([str(exe_path)])
    return process


async def start_and_wait(
    version: str = "portable",
    host: str = "127.0.0.1",
    port: int = 8188,
    wait_timeout: float = 60
) -> subprocess.Popen:
    """
    Start ComfyUI and wait for it to be ready

    Args:
        version: "portable" or "electron"
        host: Server host
        port: Server port
        wait_timeout: Timeout in seconds

    Returns:
        subprocess.Popen object
    """

    if version == "portable":
        process = launch_portable(host, port)
    elif version == "electron":
        process = launch_electron()
    else:
        raise ValueError(f"Unknown version: {version}")

    print(f"Waiting for ComfyUI to start (timeout: {wait_timeout}s)...")

    if await wait_for_server(host, port, wait_timeout):
        print("✓ ComfyUI is ready!")
        return process
    else:
        process.terminate()
        raise TimeoutError(f"ComfyUI did not start within {wait_timeout} seconds")


async def main():
    import argparse

    parser = argparse.ArgumentParser(description="Launch ComfyUI")
    parser.add_argument(
        "--version",
        choices=["portable", "electron"],
        default="portable",
        help="Which version to launch"
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Server host"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8188,
        help="Server port"
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=60,
        help="Startup timeout in seconds"
    )

    args = parser.parse_args()

    try:
        process = await start_and_wait(
            args.version,
            args.host,
            args.port,
            args.timeout
        )
        print(f"Process ID: {process.pid}")
        print("Press Ctrl+C to stop")

        # Keep process alive
        process.wait()

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
