---
title: ComfyUI Integration - Quick Start
type: project
tags: [project, active]
created: 2026-04-03
updated: 2026-04-03
status: active
maturity: growing
domain: knowledge-management
summary: ""
---

# ComfyUI Integration - Quick Start

## 1. 啟動 ComfyUI

選一個方式：

### 方式 A：Portable 版本（推薦 Agent 使用）
```bash
python -m projects.tools.comfyui.launcher --version portable
```

這會啟動 `C:\Program Files\ComfyUI\ComfyUI_windows_portable\ComfyUI` 版本，並等待伺服器準備好。

### 方式 B：Electron GUI
```bash
python -m projects.tools.comfyui.launcher --version electron
```

這會啟動 `C:\Users\User\Projects\comfyui\ComfyUI.exe`。

### 方式 C：手動啟動
```bash
cd "C:\Program Files\ComfyUI\ComfyUI_windows_portable\ComfyUI"
python main.py --listen 127.0.0.1 --port 8188
```

## 2. 驗證連接

```bash
python -m projects.tools.comfyui.cli check
```

輸出應該是：
```
✓ Connected to ComfyUI
  System: Windows
```

## 3. 執行工作流

### 方式 1：CLI 調用
```bash
python -m projects.tools.comfyui.cli execute workflow.json --output ./results
```

### 方式 2：Python 程式碼
```python
import asyncio
from projects.tools.comfyui import ComfyUIClient

async def run():
    async with ComfyUIClient() as client:
        workflow = {
            "1": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {"ckpt_name": "model.safetensors"}
            }
        }
        result = await client.execute_workflow(workflow)
        print(result)

asyncio.run(run())
```

### 方式 3：檢查工作流
```bash
python -m projects.tools.comfyui.cli inspect workflow.json
```

## 4. Agent 使用範例

Agent 可以直接呼叫 CLI：

```python
# 檢查連接
subprocess.run([
    "python", "-m", "projects.tools.comfyui.cli", "check"
])

# 執行工作流
subprocess.run([
    "python", "-m", "projects.tools.comfyui.cli", "execute",
    "my_workflow.json", "--output", "./results"
])
```

或導入模組：

```python
import asyncio
from projects.tools.comfyui import ComfyUIClient, WorkflowManager

async def agent_task():
    manager = WorkflowManager()
    workflow = manager.load_workflow("workflow.json")

    async with ComfyUIClient() as client:
        result = await client.execute_workflow(workflow)
        return result

result = asyncio.run(agent_task())
```

## 5. 工作流結構

ComfyUI 工作流是 JSON，映射節點 ID 到節點定義：

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
      "text": "a beautiful cat",
      "clip": ["1", 1]
    }
  }
}
```

- `class_type` — 節點類型
- `inputs` — 輸入參數
- `["1", 1]` — 引用節點 1 的輸出槽 1

## 6. 常見命令

| 任務 | 命令 |
|------|------|
| 檢查連接 | `python -m projects.tools.comfyui.cli check` |
| 執行工作流 | `python -m projects.tools.comfyui.cli execute workflow.json` |
| 檢查工作流 | `python -m projects.tools.comfyui.cli inspect workflow.json` |
| 執行範例 | `python -m projects.tools.comfyui.examples` |
| 啟動伺服器 | `python -m projects.tools.comfyui.launcher` |

## 7. 故障排除

### 連接失敗
確保 ComfyUI 在執行：
```bash
python -m projects.tools.comfyui.cli check
```

### 工作流錯誤
檢查工作流結構：
```bash
python -m projects.tools.comfyui.cli inspect workflow.json
```

### 超時
如果工作流執行超過 5 分鐘，增加超時時間：
```bash
python -m projects.tools.comfyui.cli execute workflow.json --timeout 600
```

## 8. 目錄結構

```
projects/tools/comfyui/
├── __init__.py          # 模組初始化
├── client.py            # API 客戶端
├── workflow.py          # 工作流管理
├── cli.py               # CLI 工具
├── launcher.py          # 啟動器
├── examples.py          # 範例
├── requirements.txt     # 依賴
├── README.md            # 詳細文檔
└── QUICKSTART.md        # 本檔案
```

## 下一步

- 查看 `examples.py` 瞭解更多用法
- 修改 CLI 以支援更多命令
- 建立自己的工作流腳本
- 與 agent 整合自動化任務
