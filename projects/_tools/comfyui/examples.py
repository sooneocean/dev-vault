"""ComfyUI Integration Examples"""

import asyncio
import json
from pathlib import Path

from .client import ComfyUIClient
from .workflow import WorkflowManager


async def example_check_connection():
    """Example: Check if ComfyUI is running"""
    print("=== Checking Connection ===")

    async with ComfyUIClient() as client:
        try:
            stats = await client.get_system_stats()
            print("✓ Connected to ComfyUI")
            print(f"  Stats: {stats}")
        except Exception as e:
            print(f"✗ Cannot connect: {e}")


async def example_simple_workflow():
    """Example: Build and execute a simple workflow"""
    print("\n=== Simple Workflow Example ===")

    manager = WorkflowManager()

    # Create workflow
    workflow = {
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {
                "ckpt_name": "model.safetensors"
            }
        }
    }

    print("Workflow structure:")
    print(json.dumps(workflow, indent=2))

    # Would execute if ComfyUI is running
    # async with ComfyUIClient() as client:
    #     result = await client.execute_workflow(workflow)


async def example_workflow_builder():
    """Example: Build workflow programmatically"""
    print("\n=== Workflow Builder Example ===")

    manager = WorkflowManager()
    workflow = {}

    # Load checkpoint
    manager.add_node(
        workflow, "1",
        "CheckpointLoaderSimple",
        {"ckpt_name": "model.safetensors"}
    )

    # Positive prompt
    manager.add_node(
        workflow, "2",
        "CLIPTextEncode",
        {
            "text": "a beautiful landscape",
            "clip": ["1", 1]
        }
    )

    # Negative prompt
    manager.add_node(
        workflow, "3",
        "CLIPTextEncode",
        {
            "text": "blurry, bad quality",
            "clip": ["1", 1]
        }
    )

    print("Built workflow with 3 nodes:")
    print(json.dumps(workflow, indent=2))


async def example_load_workflow():
    """Example: Load and inspect workflow from file"""
    print("\n=== Load Workflow Example ===")

    # Check if workflow files exist in default ComfyUI locations
    workflow_paths = [
        Path("C:/Users/User/Projects/comfyui/user/default"),
        Path("C:/Program Files/ComfyUI/ComfyUI_windows_portable/ComfyUI/web/scripts"),
    ]

    for path in workflow_paths:
        if path.exists():
            json_files = list(path.glob("*.json"))
            if json_files:
                print(f"Found workflow files in {path}:")
                for f in json_files[:3]:
                    print(f"  - {f.name}")
                break


async def example_execution_with_callback():
    """Example: Execute with real-time callbacks"""
    print("\n=== Execution with Callbacks Example ===")

    async def on_message(msg):
        msg_type = msg.get("type")
        if msg_type == "executing":
            node = msg.get("data", {}).get("node")
            print(f"  Executing: {node}")
        elif msg_type == "execution_progress":
            data = msg.get("data", {})
            print(f"  Progress: {data.get('value')}/{data.get('max')}")

    print("This would monitor real-time execution:")
    print("  - Track node execution")
    print("  - Monitor progress")
    print("  - Capture status messages")


async def main():
    print("ComfyUI Integration Examples\n")

    await example_check_connection()
    await example_simple_workflow()
    await example_workflow_builder()
    await example_load_workflow()
    await example_execution_with_callback()

    print("\n✓ Examples complete")


if __name__ == "__main__":
    asyncio.run(main())
