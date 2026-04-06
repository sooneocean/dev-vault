"""Tests for scanner memory integration (Unit 5)."""

import tempfile
from pathlib import Path

import pytest
import pytest_asyncio

from agent_memory import AgentMemoryClient, BackendConfig
from scanner_memory import ScannerMemoryLogger


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
async def memory_client(config):
    """Create test memory client."""
    client = AgentMemoryClient(config=config)
    yield client
    await client.close()


@pytest.mark.asyncio
async def test_scanner_memory_logger_logs_discovery(memory_client):
    """Test logging a scanner discovery to memory."""
    async with ScannerMemoryLogger(memory_client=memory_client) as logger:
        await logger.log_discovery(
            source="github",
            name="test-framework",
            url="https://github.com/test/test-framework",
            description="A test framework for agents",
            domain_tags=["agent-framework"],
        )

    # Verify logged
    docs = await memory_client.search(
        query="test-framework",
        agent_id="scanner",
    )

    assert len(docs) > 0
    doc = docs[0]
    assert doc.metadata["name"] == "test-framework"
    assert doc.metadata["verdict"] == "pending"


@pytest.mark.asyncio
async def test_scanner_memory_logger_includes_metadata(memory_client):
    """Test that discovery metadata is correctly stored."""
    async with ScannerMemoryLogger(memory_client=memory_client) as logger:
        await logger.log_discovery(
            source="github",
            name="agent-framework",
            url="https://github.com/test/agent-framework",
            description="Multi-agent framework",
            domain_tags=["agent-framework", "tool"],
            metadata={"stars": 500, "language": "Python"},
        )

    docs = await memory_client.search(
        query="agent-framework",
        agent_id="scanner",
    )

    assert len(docs) > 0
    doc = docs[0]

    # Verify metadata
    assert doc.metadata["url"] == "https://github.com/test/agent-framework"
    assert doc.metadata["source_type"] == "github"
    assert "agent-framework" in doc.metadata["domain_tags"]
    assert doc.metadata["stars"] == 500


@pytest.mark.asyncio
async def test_scanner_memory_logger_context_manager(memory_client):
    """Test scanner logger as async context manager."""
    # Use context manager with pre-initialized client
    async with ScannerMemoryLogger(memory_client=memory_client) as logger:
        assert logger.memory_client is not None
        await logger.log_discovery(
            source="arxiv",
            name="Agent Optimization Paper",
            url="https://arxiv.org/abs/2601.01234",
            description="Paper on agent optimization",
            domain_tags=["agent-framework"],
        )

    # Client should still be open after context exit (since we provided it)
    docs = await memory_client.search(
        query="Agent Optimization",
        agent_id="scanner",
    )

    assert len(docs) > 0


@pytest.mark.asyncio
async def test_scanner_memory_logger_creates_client():
    """Test scanner logger creates its own client."""
    async with ScannerMemoryLogger() as logger:
        assert logger.memory_client is not None

        # Log should work
        await logger.log_discovery(
            source="github",
            name="test-tool",
            url="https://github.com/test/test",
            description="Test",
            domain_tags=["tool"],
        )


@pytest.mark.asyncio
async def test_scanner_discovery_content_format(memory_client):
    """Test that discovery content is properly formatted."""
    async with ScannerMemoryLogger(memory_client=memory_client) as logger:
        await logger.log_discovery(
            source="arxiv",
            name="Important Paper",
            url="https://arxiv.org/abs/2601.12345",
            description="A paper about RAG systems",
            domain_tags=["rag"],
        )

    docs = await memory_client.search(
        query="Important Paper",
        agent_id="scanner",
    )

    assert len(docs) > 0
    doc = docs[0]

    # Verify content format
    assert "Discovered: Important Paper" in doc.content
    assert "https://arxiv.org/abs/2601.12345" in doc.content
    assert "RAG systems" in doc.content


@pytest.mark.asyncio
async def test_scanner_logs_multiple_discoveries(memory_client):
    """Test logging multiple discoveries."""
    async with ScannerMemoryLogger(memory_client=memory_client) as logger:
        for i in range(3):
            await logger.log_discovery(
                source="github",
                name=f"tool-{i}",
                url=f"https://github.com/test/tool-{i}",
                description=f"Tool {i}",
                domain_tags=["tool"],
            )

    docs = await memory_client.search(
        query="tool",
        agent_id="scanner",
        top_k=10,
    )

    assert len(docs) >= 3


@pytest.mark.asyncio
async def test_scanner_memory_logger_handles_errors(memory_client):
    """Test error handling in logger."""
    async with ScannerMemoryLogger(memory_client=memory_client) as logger:
        # This should not raise, just log warning
        await logger.log_discovery(
            source="github",
            name="valid-tool",
            url="https://github.com/test/valid",
            description="Valid discovery",
            domain_tags=["tool"],
        )

        # Verify it was logged
        docs = await memory_client.search(
            query="valid-tool",
            agent_id="scanner",
        )

        assert len(docs) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
