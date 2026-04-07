"""ComfyUI API Client"""

import asyncio
import aiohttp
import json
import uuid
from typing import Dict, Any, Optional, Callable
from pathlib import Path


class ComfyUIClient:
    """ComfyUI API client for workflow submission and monitoring"""

    def __init__(self, host: str = "127.0.0.1", port: int = 8188):
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        self.client_id = str(uuid.uuid4())
        self.session: Optional[aiohttp.ClientSession] = None
        self.ws_connection = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
        if self.ws_connection:
            await self.ws_connection.close()

    async def _ensure_session(self):
        if self.session is None:
            self.session = aiohttp.ClientSession()

    async def get_system_stats(self) -> Dict[str, Any]:
        """Get ComfyUI system stats"""
        await self._ensure_session()
        async with self.session.get(f"{self.base_url}/system") as resp:
            return await resp.json()

    async def submit_prompt(self, prompt: Dict[str, Any]) -> str:
        """
        Submit a workflow prompt to ComfyUI
        Returns: prompt_id
        """
        await self._ensure_session()

        payload = {
            "prompt": prompt,
            "client_id": self.client_id,
        }

        async with self.session.post(
            f"{self.base_url}/prompt",
            json=payload
        ) as resp:
            data = await resp.json()
            if resp.status != 200:
                raise RuntimeError(f"Failed to submit prompt: {data}")
            return data.get("prompt_id")

    async def get_history(self, prompt_id: str) -> Dict[str, Any]:
        """Get execution history for a prompt"""
        await self._ensure_session()
        async with self.session.get(
            f"{self.base_url}/history/{prompt_id}"
        ) as resp:
            return await resp.json()

    async def listen_execution(
        self,
        prompt_id: str,
        callback: Optional[Callable] = None,
        timeout: float = 300
    ) -> Dict[str, Any]:
        """
        Listen for execution completion via WebSocket
        Returns: execution results from history
        """
        await self._ensure_session()

        start_time = asyncio.get_event_loop().time()

        async with self.session.ws_connect(
            f"ws://{self.host}:{self.port}/ws?clientId={self.client_id}"
        ) as ws:
            while True:
                # Check timeout
                if asyncio.get_event_loop().time() - start_time > timeout:
                    raise TimeoutError(f"Execution timeout for {prompt_id}")

                # Wait for message with timeout
                try:
                    msg = await asyncio.wait_for(ws.receive(), timeout=5)
                except asyncio.TimeoutError:
                    continue

                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = json.loads(msg.data)

                    if callback:
                        await callback(data)

                    # Check if our prompt is done
                    if data.get("type") == "execution_complete":
                        if data.get("output", {}).get("prompt_id") == prompt_id:
                            return await self.get_history(prompt_id)

                elif msg.type == aiohttp.WSMsgType.ERROR:
                    raise RuntimeError(f"WebSocket error: {ws.exception()}")
                elif msg.type == aiohttp.WSMsgType.CLOSED:
                    raise RuntimeError("WebSocket connection closed")

    async def execute_workflow(
        self,
        workflow: Dict[str, Any],
        callback: Optional[Callable] = None,
        timeout: float = 300
    ) -> Dict[str, Any]:
        """
        Execute a workflow from start to finish
        Returns: execution history with results
        """
        prompt_id = await self.submit_prompt(workflow)
        print(f"Submitted prompt: {prompt_id}")

        result = await self.listen_execution(prompt_id, callback, timeout)
        return result


async def main():
    """Test ComfyUI connection"""
    async with ComfyUIClient() as client:
        try:
            stats = await client.get_system_stats()
            print("Connected to ComfyUI!")
            print(f"System: {stats}")
        except Exception as e:
            print(f"Cannot connect to ComfyUI: {e}")


if __name__ == "__main__":
    asyncio.run(main())
