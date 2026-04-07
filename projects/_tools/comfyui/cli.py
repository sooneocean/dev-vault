#!/usr/bin/env python3
"""ComfyUI CLI for agent integration"""

import asyncio
import json
import sys
import argparse
from pathlib import Path
from typing import Optional

from .client import ComfyUIClient
from .workflow import WorkflowManager


async def execute_workflow_file(
    workflow_path: str,
    host: str = "127.0.0.1",
    port: int = 8188,
    output_dir: Optional[str] = None,
    timeout: float = 300
) -> dict:
    """Execute a workflow from JSON file"""

    # Load workflow
    with open(workflow_path, 'r') as f:
        workflow = json.load(f)

    print(f"Executing workflow from {workflow_path}")

    async with ComfyUIClient(host, port) as client:
        def message_callback(msg):
            msg_type = msg.get("type")
            if msg_type == "execution_progress":
                progress = msg.get("data", {})
                print(f"Progress: {progress.get('value', 0)}/{progress.get('max', 0)}")
            elif msg_type == "executing":
                node = msg.get("data", {}).get("node")
                if node:
                    print(f"Executing node: {node}")

        result = await client.execute_workflow(workflow, message_callback, timeout)

        if output_dir:
            output_path = Path(output_dir) / "comfyui_result.json"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"Result saved to {output_path}")

        return result


async def check_connection(
    host: str = "127.0.0.1",
    port: int = 8188
) -> bool:
    """Check if ComfyUI is running"""
    async with ComfyUIClient(host, port) as client:
        try:
            stats = await client.get_system_stats()
            print("✓ Connected to ComfyUI")
            print(f"  System: {stats.get('system', {}).get('os', 'Unknown')}")
            return True
        except Exception as e:
            print(f"✗ Cannot connect to ComfyUI: {e}")
            return False


async def load_and_inspect(workflow_path: str) -> dict:
    """Load and inspect a workflow file"""
    with open(workflow_path, 'r') as f:
        workflow = json.load(f)

    print(f"Workflow: {workflow_path}")
    print(f"Nodes: {len(workflow)}")
    print("\nNode details:")

    for node_id, node_data in workflow.items():
        class_type = node_data.get("class_type", "Unknown")
        inputs = node_data.get("inputs", {})
        print(f"  {node_id}: {class_type}")
        for input_name, input_val in inputs.items():
            print(f"    - {input_name}: {input_val}")

    return workflow


async def main():
    parser = argparse.ArgumentParser(description="ComfyUI CLI")
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="ComfyUI host (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8188,
        help="ComfyUI port (default: 8188)"
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # check command
    subparsers.add_parser("check", help="Check ComfyUI connection")

    # execute command
    execute_parser = subparsers.add_parser("execute", help="Execute workflow")
    execute_parser.add_argument("workflow", help="Workflow JSON file path")
    execute_parser.add_argument(
        "--output",
        help="Output directory for results"
    )
    execute_parser.add_argument(
        "--timeout",
        type=float,
        default=300,
        help="Execution timeout in seconds (default: 300)"
    )

    # inspect command
    inspect_parser = subparsers.add_parser("inspect", help="Inspect workflow")
    inspect_parser.add_argument("workflow", help="Workflow JSON file path")

    args = parser.parse_args()

    try:
        if args.command == "check":
            result = await check_connection(args.host, args.port)
            sys.exit(0 if result else 1)

        elif args.command == "execute":
            result = await execute_workflow_file(
                args.workflow,
                args.host,
                args.port,
                args.output,
                args.timeout
            )
            print(json.dumps(result, indent=2))

        elif args.command == "inspect":
            await load_and_inspect(args.workflow)

        else:
            parser.print_help()

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
