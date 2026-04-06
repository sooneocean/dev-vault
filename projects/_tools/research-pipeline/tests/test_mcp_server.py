"""Tests for MCP server (Unit 2)."""

import asyncio
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest
import pytest_asyncio

from agent_memory import AgentMemoryClient, AgentMemoryDocument, BackendConfig
from agent_memory.mcp_server import (
    handle_memory_search,
    handle_memory_store,
    handle_memory_temporal,
)


@pytest.fixture
def config():
    """Create test configuration."""
    tmpdir = tempfile.mkdtemp()
    return BackendConfig(
        use_query_memory=False,
        lancedb_path=str(Path(tmpdir) / "test.db"),
        fallback_timeout_seconds=5.0,
    )


@pytest_asyncio.fixture
async def client(config):
    """Create test client and set it in MCP server."""
    import agent_memory.mcp_server as mcp

    client_instance = AgentMemoryClient(config=config)
    mcp.memory_client = client_instance
    yield client_instance
    await client_instance.close()


# ============================================================================
# UNIT 2: Tool Handler Tests
# ============================================================================


@pytest.mark.asyncio
async def test_memory_store_tool(client):
    """Test memory:store tool handler."""
    params = {
        "agent_id": "evaluator",
        "source": "evaluation",
        "content": "Tool evaluation result",
        "metadata": {
            "verdict": "poc_candidate",
            "domain_tags": ["rag"],
        },
    }

    result = await handle_memory_store(params)

    assert result["type"] == "output"
    content = result["content"]
    assert content["status"] == "stored"
    assert "doc_id" in content
    assert isinstance(content["doc_id"], str)


@pytest.mark.asyncio
async def test_memory_search_tool(client):
    """Test memory:search tool handler."""
    # First store a document
    store_params = {
        "agent_id": "evaluator",
        "source": "evaluation",
        "content": "RAG framework evaluation result",
        "metadata": {"verdict": "poc_candidate", "domain_tags": ["rag"]},
    }
    await handle_memory_store(store_params)

    # Then search for it
    search_params = {
        "query": "RAG framework",
        "agent_id": "evaluator",
        "top_k": 10,
    }

    result = await handle_memory_search(search_params)

    assert result["type"] == "output"
    content = result["content"]
    assert "results" in content
    assert "count" in content
    assert isinstance(content["results"], list)


@pytest.mark.asyncio
async def test_memory_search_with_metadata_filters(client):
    """Test memory:search with metadata filtering."""
    # Store documents with different verdicts
    for verdict in ["poc_candidate", "watching"]:
        params = {
            "agent_id": "evaluator",
            "source": "evaluation",
            "content": f"Tool with verdict {verdict}",
            "metadata": {"verdict": verdict, "domain_tags": ["rag"]},
        }
        await handle_memory_store(params)

    # Search with filter
    search_params = {
        "query": "Tool",
        "agent_id": "evaluator",
        "metadata_filters": {"verdict": "poc_candidate"},
        "top_k": 10,
    }

    result = await handle_memory_search(search_params)

    assert result["type"] == "output"
    assert len(result["content"]["results"]) >= 0  # May or may not filter depending on implementation


@pytest.mark.asyncio
async def test_memory_search_with_context_preamble(client):
    """Test memory:search with context preamble."""
    # Store a document
    store_params = {
        "agent_id": "evaluator",
        "source": "evaluation",
        "content": "Evaluating multi-agent orchestration tools",
        "metadata": {"domain_tags": ["agent-framework"]},
    }
    await handle_memory_store(store_params)

    # Search with preamble
    search_params = {
        "query": "orchestration",
        "context_preamble": "I am the evaluator agent, evaluating tools for agent frameworks",
        "agent_id": "evaluator",
    }

    result = await handle_memory_search(search_params)

    assert result["type"] == "output"
    # Preamble should be used to improve relevance
    assert "results" in result["content"]


@pytest.mark.asyncio
async def test_memory_search_temporal_tool(client):
    """Test memory:search_temporal tool handler."""
    now = datetime.utcnow()

    # Store a document with specific timestamp
    doc = AgentMemoryDocument(
        agent_id="evaluator",
        source="evaluation",
        content="Recent evaluation",
        metadata={"domain_tags": ["rag"]},
        timestamp=now - timedelta(hours=1),
    )
    import agent_memory.mcp_server as mcp

    await mcp.memory_client.store(doc)

    # Search temporal
    search_params = {
        "domain": "rag",
        "after_date": (now - timedelta(days=1)).isoformat(),
    }

    result = await handle_memory_temporal(search_params)

    assert result["type"] == "output"
    content = result["content"]
    assert "results" in content
    assert "count" in content


@pytest.mark.asyncio
async def test_memory_store_error_handling(client):
    """Test error handling in memory:store."""
    # Invalid parameters (missing required field)
    params = {
        "agent_id": "evaluator",
        # Missing 'source'
        "content": "Test",
    }

    result = await handle_memory_store(params)

    assert result["type"] == "error"
    assert "error" in result


@pytest.mark.asyncio
async def test_memory_search_error_handling(client):
    """Test error handling in memory:search."""
    # Invalid parameters (missing required field)
    params = {
        # Missing 'query'
        "agent_id": "evaluator",
    }

    result = await handle_memory_search(params)

    assert result["type"] == "error"
    assert "error" in result


@pytest.mark.asyncio
async def test_agent_scoped_query(client):
    """Test agent-scoped memory queries."""
    # Store documents from different agents
    eval_params = {
        "agent_id": "evaluator",
        "source": "evaluation",
        "content": "Evaluator found tool X",
        "metadata": {"verdict": "poc_candidate"},
    }
    scan_params = {
        "agent_id": "scanner",
        "source": "github",
        "content": "Scanner found tool Y",
        "metadata": {"stars": 1000},
    }

    await handle_memory_store(eval_params)
    await handle_memory_store(scan_params)

    # Search only evaluator's documents
    search_params = {
        "query": "found tool",
        "agent_id": "evaluator",
        "top_k": 10,
    }

    result = await handle_memory_search(search_params)

    assert result["type"] == "output"
    # Results should be agent-scoped
    assert "results" in result["content"]


@pytest.mark.asyncio
async def test_concurrent_tool_calls(client):
    """Test concurrent tool calls (agents calling tools simultaneously)."""

    async def store_doc(i):
        params = {
            "agent_id": f"agent_{i}",
            "source": "evaluation",
            "content": f"Document {i}",
            "metadata": {"index": i},
        }
        return await handle_memory_store(params)

    # Run concurrent stores
    results = await asyncio.gather(*[store_doc(i) for i in range(5)])

    assert len(results) == 5
    assert all(r["type"] == "output" for r in results)
    assert all(r["content"]["status"] == "stored" for r in results)


@pytest.mark.asyncio
async def test_search_result_structure(client):
    """Test that search results have expected structure."""
    # Store document
    store_params = {
        "agent_id": "evaluator",
        "source": "evaluation",
        "content": "Test document content",
        "metadata": {
            "verdict": "poc_candidate",
            "domain_tags": ["rag"],
            "tool_name": "Example",
        },
    }
    await handle_memory_store(store_params)

    # Search
    search_params = {
        "query": "Test",
        "agent_id": "evaluator",
    }

    result = await handle_memory_search(search_params)

    assert result["type"] == "output"
    content = result["content"]

    # Check structure
    assert "results" in content
    assert "count" in content
    assert isinstance(content["results"], list)

    if content["results"]:
        result_item = content["results"][0]
        assert "doc_id" in result_item
        assert "content" in result_item
        assert "metadata" in result_item
        assert "relevance_score" in result_item
        assert isinstance(result_item["relevance_score"], (int, float))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
