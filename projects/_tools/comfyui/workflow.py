"""ComfyUI Workflow Management"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict


@dataclass
class WorkflowNode:
    """Represents a ComfyUI workflow node"""
    id: str
    class_type: str
    inputs: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "class_type": self.class_type,
            "inputs": self.inputs,
        }


class WorkflowManager:
    """Load, build, and manage ComfyUI workflows"""

    def __init__(self):
        self.workflows: Dict[str, Dict[str, Any]] = {}

    def load_workflow(self, path: str) -> Dict[str, Any]:
        """Load workflow from JSON file"""
        with open(path, 'r', encoding='utf-8') as f:
            workflow = json.load(f)
        return workflow

    def save_workflow(self, workflow: Dict[str, Any], path: str) -> None:
        """Save workflow to JSON file"""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(workflow, f, indent=2)

    def create_workflow(self, name: str) -> Dict[str, Any]:
        """Create a new empty workflow"""
        workflow = {}
        self.workflows[name] = workflow
        return workflow

    def get_workflow(self, name: str) -> Dict[str, Any]:
        """Get workflow by name"""
        return self.workflows.get(name, {})

    def add_node(
        self,
        workflow: Dict[str, Any],
        node_id: str,
        class_type: str,
        inputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Add a node to workflow"""
        workflow[node_id] = {
            "class_type": class_type,
            "inputs": inputs,
        }
        return workflow

    def connect_nodes(
        self,
        workflow: Dict[str, Any],
        source_id: str,
        source_slot: int,
        target_id: str,
        target_input: str
    ) -> Dict[str, Any]:
        """Connect output of one node to input of another"""
        if target_id not in workflow:
            raise ValueError(f"Target node {target_id} not found")

        workflow[target_id]["inputs"][target_input] = [source_id, source_slot]
        return workflow

    def build_simple_text_workflow(
        self,
        text: str,
        node_id: str = "1"
    ) -> Dict[str, Any]:
        """Build a simple text processing workflow"""
        workflow = {
            node_id: {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "text": text,
                    "clip": ["clip_model", 0]
                }
            }
        }
        return workflow

    def get_node_ids(self, workflow: Dict[str, Any]) -> List[str]:
        """Get all node IDs in workflow"""
        return list(workflow.keys())

    def validate_workflow(self, workflow: Dict[str, Any]) -> bool:
        """Basic workflow validation"""
        if not isinstance(workflow, dict):
            return False

        for node_id, node_data in workflow.items():
            if not isinstance(node_data, dict):
                return False
            if "class_type" not in node_data:
                return False
            if "inputs" not in node_data:
                return False

        return True


def main():
    """Test workflow manager"""
    manager = WorkflowManager()

    # Create a simple workflow
    workflow = manager.create_workflow("test")
    print(f"Created workflow: {workflow}")

    # Add a node
    manager.add_node(
        workflow,
        "1",
        "LoadCheckpoint",
        {"ckpt_name": "model.safetensors"}
    )

    print(f"Workflow with node: {json.dumps(workflow, indent=2)}")


if __name__ == "__main__":
    main()
