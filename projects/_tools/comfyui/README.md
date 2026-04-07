# ComfyUI Integration

Python client library for ComfyUI API integration.

## Setup

```bash
pip install -r requirements.txt
```

## Components

### ComfyUIClient
Async HTTP/WebSocket client for ComfyUI API.

```python
from projects.tools.comfyui import ComfyUIClient

async with ComfyUIClient(host="127.0.0.1", port=8188) as client:
    workflow = {...}
    result = await client.execute_workflow(workflow)
```

### WorkflowManager
Load, build, and manage ComfyUI workflows.

```python
from projects.tools.comfyui import WorkflowManager

manager = WorkflowManager()
workflow = manager.load_workflow("my_workflow.json")
manager.add_node(workflow, "1", "LoadCheckpoint", {...})
```

## CLI Usage

### Check Connection
```bash
python -m projects.tools.comfyui.cli check --host 127.0.0.1 --port 8188
```

### Execute Workflow
```bash
python -m projects.tools.comfyui.cli execute workflow.json --output ./results
```

### Inspect Workflow
```bash
python -m projects.tools.comfyui.cli inspect workflow.json
```

## Agent Integration

For agent use, the ComfyUI server must be running at `http://127.0.0.1:8188`.

Start ComfyUI Portable:
```bash
cd "C:\Program Files\ComfyUI\ComfyUI_windows_portable\ComfyUI"
python main.py --listen 127.0.0.1 --port 8188
```

Then agents can:
1. Call CLI commands directly via subprocess
2. Import and use ComfyUIClient/WorkflowManager in Python
3. Process workflow results asynchronously

## ComfyUI Paths

- **Portable (Python)**: `C:\Program Files\ComfyUI\ComfyUI_windows_portable\ComfyUI`
- **GUI (Electron)**: `C:\Users\User\Projects\comfyui`

## Workflow Structure

ComfyUI workflows are JSON dictionaries mapping node IDs to node definitions:

```json
{
  "1": {
    "class_type": "CheckpointLoaderSimple",
    "inputs": {
      "ckpt_name": "model.safetensors"
    }
  },
  "2": {
    "class_type": "CLIPTextEncode",
    "inputs": {
      "text": "a cat",
      "clip": ["1", 1]
    }
  }
}
```

Inputs can be:
- Primitives: strings, numbers, lists
- Node references: `[node_id, output_slot]`

## Development

### Testing Connection
```bash
python -c "
import asyncio
from projects.tools.comfyui import ComfyUIClient

async def test():
    async with ComfyUIClient() as client:
        stats = await client.get_system_stats()
        print('Connected!', stats)

asyncio.run(test())
"
```

### Debugging Workflows
Use `inspect` to understand workflow structure:
```bash
python -m projects.tools.comfyui.cli inspect my_workflow.json
```

### Message Callbacks
Monitor execution in real-time:
```python
async def on_message(msg):
    if msg.get("type") == "execution_progress":
        print(f"Progress: {msg}")

await client.execute_workflow(workflow, on_message)
```
