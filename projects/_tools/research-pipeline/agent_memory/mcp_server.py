"""MCP server for agent memory system."""

import asyncio
import json
import logging
import sys
from datetime import datetime
from typing import Any

from .client import AgentMemoryClient
from .mcp_tools import (
    MEMORY_SEARCH_TOOL,
    MEMORY_STORE_TOOL,
    MEMORY_TEMPORAL_TOOL,
    MemorySearchInput,
    MemorySearchOutput,
    MemorySearchResult,
    MemoryStoreInput,
    MemoryStoreOutput,
    MemoryTemporalInput,
    MemoryTemporalOutput,
)
from .models import AgentMemoryDocument

logger = logging.getLogger(__name__)

# Global memory client
memory_client: AgentMemoryClient | None = None


def get_memory_client() -> AgentMemoryClient:
    """Get or initialize global memory client."""
    global memory_client
    if memory_client is None:
        memory_client = AgentMemoryClient()
    return memory_client


async def handle_memory_store(params: dict[str, Any]) -> dict[str, Any]:
    """Handle memory:store tool call.

    Args:
        params: Input parameters (agent_id, source, content, metadata)

    Returns:
        Result dict with doc_id and status
    """
    try:
        input_data = MemoryStoreInput(**params)

        client = get_memory_client()

        document = AgentMemoryDocument(
            agent_id=input_data.agent_id,
            source=input_data.source,
            content=input_data.content,
            metadata=input_data.metadata,
        )

        doc_id = await client.store(document)

        output = MemoryStoreOutput(doc_id=doc_id, status="stored")
        return {"type": "output", "content": json.loads(output.model_dump_json())}

    except Exception as e:
        logger.error(f"Error in memory:store: {e}")
        return {"type": "error", "error": str(e)}


async def handle_memory_search(params: dict[str, Any]) -> dict[str, Any]:
    """Handle memory:search tool call.

    Args:
        params: Input parameters (query, agent_id, metadata_filters, top_k, context_preamble)

    Returns:
        Result dict with search results
    """
    try:
        input_data = MemorySearchInput(**params)

        client = get_memory_client()

        results = await client.search(
            query=input_data.query,
            agent_id=input_data.agent_id,
            metadata_filters=input_data.metadata_filters,
            top_k=input_data.top_k or 10,
            context_preamble=input_data.context_preamble,
        )

        search_results = [
            MemorySearchResult(
                doc_id=r.doc_id,
                content=r.content,
                metadata=r.metadata,
                relevance_score=r.relevance_score,
                timestamp=r.timestamp.isoformat() if r.timestamp else None,
            )
            for r in results
        ]

        output = MemorySearchOutput(results=search_results, count=len(search_results))
        return {"type": "output", "content": json.loads(output.model_dump_json())}

    except Exception as e:
        logger.error(f"Error in memory:search: {e}")
        return {"type": "error", "error": str(e)}


async def handle_memory_temporal(params: dict[str, Any]) -> dict[str, Any]:
    """Handle memory:search_temporal tool call.

    Args:
        params: Input parameters (domain, after_date, before_date)

    Returns:
        Result dict with temporal search results
    """
    try:
        input_data = MemoryTemporalInput(**params)

        client = get_memory_client()

        # Parse dates
        after_date = None
        if input_data.after_date:
            after_date = datetime.fromisoformat(input_data.after_date)

        before_date = None
        if input_data.before_date:
            before_date = datetime.fromisoformat(input_data.before_date)

        results = await client.search_temporal(
            domain=input_data.domain,
            after_date=after_date,
            before_date=before_date,
        )

        search_results = [
            MemorySearchResult(
                doc_id=r.doc_id,
                content=r.content,
                metadata=r.metadata,
                relevance_score=r.relevance_score,
                timestamp=r.timestamp.isoformat() if r.timestamp else None,
            )
            for r in results
        ]

        output = MemoryTemporalOutput(results=search_results, count=len(search_results))
        return {"type": "output", "content": json.loads(output.model_dump_json())}

    except Exception as e:
        logger.error(f"Error in memory:search_temporal: {e}")
        return {"type": "error", "error": str(e)}


async def handle_tool_call(tool_name: str, tool_input: dict[str, Any]) -> dict[str, Any]:
    """Route tool calls to appropriate handlers.

    Args:
        tool_name: Name of the tool (memory:store, memory:search, memory:search_temporal)
        tool_input: Tool input parameters

    Returns:
        Tool result dict
    """
    if tool_name == "memory:store":
        return await handle_memory_store(tool_input)
    elif tool_name == "memory:search":
        return await handle_memory_search(tool_input)
    elif tool_name == "memory:search_temporal":
        return await handle_memory_temporal(tool_input)
    else:
        return {"type": "error", "error": f"Unknown tool: {tool_name}"}


async def main():
    """MCP server main loop (stdio-based).

    This server listens for MCP protocol messages on stdin and responds on stdout.
    Used by Claude Code agents to call agent memory tools.
    """
    logger.basicConfig(level=logging.INFO)

    # Initialize memory client
    client = get_memory_client()
    logger.info("Agent memory MCP server started")

    # Respond with tools list on initialization
    tools_response = {
        "type": "tools",
        "tools": [MEMORY_STORE_TOOL, MEMORY_SEARCH_TOOL, MEMORY_TEMPORAL_TOOL],
    }
    print(json.dumps(tools_response), flush=True)

    # Main message loop
    try:
        while True:
            # Read message from stdin
            line = sys.stdin.readline()
            if not line:
                break

            try:
                message = json.loads(line)
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON: {line}")
                continue

            # Handle different message types
            if message.get("type") == "tool_call":
                result = await handle_tool_call(
                    tool_name=message.get("tool"),
                    tool_input=message.get("input", {}),
                )
                print(json.dumps(result), flush=True)

            elif message.get("type") == "ping":
                print(json.dumps({"type": "pong"}), flush=True)

    except KeyboardInterrupt:
        logger.info("Agent memory MCP server stopped")
    except Exception as e:
        logger.error(f"MCP server error: {e}")
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
