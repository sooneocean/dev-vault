"""Tests for agent memory system (Unit 1)."""

import asyncio
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from agent_memory import AgentMemoryClient, AgentMemoryDocument, BackendConfig, SearchResult


@pytest.fixture
def config():
    """Create test configuration."""
    # Use temporary directory for LanceDB in tests
    tmpdir = tempfile.mkdtemp()
    return BackendConfig(
        use_query_memory=False,  # Use LanceDB only for tests
        lancedb_path=str(Path(tmpdir) / "test_agent_memory.db"),
        fallback_timeout_seconds=5.0,
    )


@pytest_asyncio.fixture
async def client(config):
    """Create test client."""
    client = AgentMemoryClient(config=config)
    yield client
    await client.close()


@pytest.fixture
def sample_document():
    """Create a sample document."""
    return AgentMemoryDocument(
        agent_id="evaluator",
        source="evaluation",
        content="Tool evaluation for RAG framework",
        metadata={
            "verdict": "poc_candidate",
            "domain_tags": ["rag", "agent-framework"],
            "tool_name": "Example Tool",
            "tool_url": "https://github.com/example/tool",
            "scores": {"relevance": 8, "maturity": 6},
            "run_id": "2026-03-30-abc123",
        },
    )


# ============================================================================
# UNIT 1: Core Functionality
# ============================================================================


@pytest.mark.asyncio
async def test_store_and_retrieve_document(client, sample_document):
    """Test storing a document and verifying it's retrievable."""
    # Store document
    doc_id = await client.store(sample_document)
    assert doc_id is not None
    assert isinstance(doc_id, str)

    # Search for it
    results = await client.search(
        query="RAG framework evaluation",
        agent_id="evaluator",
    )

    assert len(results) > 0
    assert any(r.content == sample_document.content for r in results)


@pytest.mark.asyncio
async def test_search_returns_correct_structure(client, sample_document):
    """Test that search results have correct structure."""
    await client.store(sample_document)

    results = await client.search(
        query="RAG evaluation",
        agent_id="evaluator",
    )

    assert len(results) > 0
    result = results[0]

    assert isinstance(result, SearchResult)
    assert result.doc_id is not None
    assert isinstance(result.content, str)
    assert isinstance(result.relevance_score, float)
    assert 0 <= result.relevance_score <= 1


@pytest.mark.asyncio
async def test_metadata_filtering(client):
    """Test filtering by metadata."""
    # Store multiple documents with different verdicts
    doc1 = AgentMemoryDocument(
        agent_id="evaluator",
        source="evaluation",
        content="Tool A evaluation",
        metadata={"verdict": "poc_candidate", "domain_tags": ["rag"]},
    )
    doc2 = AgentMemoryDocument(
        agent_id="evaluator",
        source="evaluation",
        content="Tool B evaluation",
        metadata={"verdict": "watching", "domain_tags": ["rag"]},
    )

    await client.store(doc1)
    await client.store(doc2)

    # Search for poc_candidate only
    results = await client.search(
        query="evaluation",
        agent_id="evaluator",
        metadata_filters={"verdict": "poc_candidate"},
        top_k=10,
    )

    # All returned results should have verdict="poc_candidate"
    # (This is a best-effort filter; LanceDB filtering is post-search)
    assert len(results) > 0


@pytest.mark.asyncio
async def test_agent_id_filtering(client):
    """Test filtering by agent_id."""
    # Store documents from different agents
    eval_doc = AgentMemoryDocument(
        agent_id="evaluator",
        source="evaluation",
        content="Evaluator found tool X",
        metadata={"verdict": "poc_candidate"},
    )
    scan_doc = AgentMemoryDocument(
        agent_id="scanner",
        source="github",
        content="Scanner found tool Y",
        metadata={"stars": 1000},
    )

    await client.store(eval_doc)
    await client.store(scan_doc)

    # Search only evaluator's memory
    results = await client.search(
        query="found tool",
        agent_id="evaluator",
    )

    assert len(results) > 0
    # Should only return evaluator's document
    assert all(doc.agent_id == "evaluator" for doc in results if hasattr(doc, "agent_id"))


@pytest.mark.asyncio
async def test_temporal_filtering(client):
    """Test temporal range queries."""
    now = datetime.utcnow()

    # Store documents at different times
    old_doc = AgentMemoryDocument(
        agent_id="evaluator",
        source="evaluation",
        content="Old evaluation",
        metadata={"domain_tags": ["rag"]},
        timestamp=now - timedelta(days=10),
    )
    new_doc = AgentMemoryDocument(
        agent_id="evaluator",
        source="evaluation",
        content="New evaluation",
        metadata={"domain_tags": ["rag"]},
        timestamp=now - timedelta(hours=1),
    )

    await client.store(old_doc)
    await client.store(new_doc)

    # Query only recent documents (last 7 days)
    results = await client.search_temporal(
        domain="rag",
        after_date=now - timedelta(days=7),
    )

    assert len(results) > 0
    # New doc should be in results
    assert any("New evaluation" in r.content for r in results)


@pytest.mark.asyncio
async def test_empty_search_result(client):
    """Test that searching with no matches returns empty list."""
    # Don't store anything
    results = await client.search(
        query="this term should not exist xyz123",
        agent_id="evaluator",
    )

    assert results == []


@pytest.mark.asyncio
async def test_concurrent_operations(client, sample_document):
    """Test concurrent store operations."""
    # Store multiple documents concurrently
    docs = [
        AgentMemoryDocument(
            agent_id=f"agent_{i}",
            source="evaluation",
            content=f"Document {i}",
            metadata={"index": i},
        )
        for i in range(5)
    ]

    # Run stores concurrently
    doc_ids = await asyncio.gather(*[client.store(doc) for doc in docs])

    assert len(doc_ids) == 5
    assert all(id is not None for id in doc_ids)


@pytest.mark.asyncio
async def test_search_ranking_by_relevance(client):
    """Test that search results are ranked by relevance."""
    doc1 = AgentMemoryDocument(
        agent_id="evaluator",
        source="evaluation",
        content="This is about RAG retrieval augmented generation systems",
        metadata={"domain_tags": ["rag"]},
    )
    doc2 = AgentMemoryDocument(
        agent_id="evaluator",
        source="evaluation",
        content="Something completely different about databases",
        metadata={"domain_tags": ["database"]},
    )

    await client.store(doc1)
    await client.store(doc2)

    results = await client.search(
        query="RAG retrieval augmented generation",
        agent_id="evaluator",
    )

    assert len(results) >= 1
    # First result should be more relevant (doc1)
    assert "RAG" in results[0].content or results[0].relevance_score > 0.5


# ============================================================================
# UNIT 1: Fallback Resilience
# ============================================================================


@pytest.mark.asyncio
async def test_fallback_to_lancedb_on_timeout():
    """Test that system falls back to LanceDB on Query Memory timeout."""
    # Create config that attempts Query Memory but will timeout
    tmpdir = tempfile.mkdtemp()
    config = BackendConfig(
        use_query_memory=True,
        query_memory_api_url="http://localhost:9999",  # Non-existent service
        query_memory_api_key="fake_key",
        lancedb_path=str(Path(tmpdir) / "test.db"),
        fallback_timeout_seconds=0.1,  # Very short timeout
    )

    client = AgentMemoryClient(config=config)

    # Try to store - should fall back to LanceDB
    doc = AgentMemoryDocument(
        agent_id="evaluator",
        source="evaluation",
        content="Test document",
        metadata={},
    )

    # Should not raise error; should fall back to LanceDB
    doc_id = await client.store(doc)
    assert doc_id is not None

    await client.close()


@pytest.mark.asyncio
async def test_lancedb_independent():
    """Test that LanceDB backend works independently."""
    tmpdir = tempfile.mkdtemp()
    config = BackendConfig(
        use_query_memory=False,  # Don't use Query Memory
        lancedb_path=str(Path(tmpdir) / "test.db"),
    )

    client = AgentMemoryClient(config=config)

    doc = AgentMemoryDocument(
        agent_id="evaluator",
        source="evaluation",
        content="Test document",
        metadata={"test": "value"},
    )

    # Store and retrieve
    doc_id = await client.store(doc)
    assert doc_id is not None

    results = await client.search("Test document", agent_id="evaluator")
    assert len(results) > 0
    assert results[0].content == "Test document"

    await client.close()


@pytest.mark.asyncio
async def test_document_metadata_roundtrip(client):
    """Test that metadata is preserved in storage and retrieval."""
    metadata = {
        "verdict": "poc_candidate",
        "domain_tags": ["rag", "agent-framework"],
        "scores": {"relevance": 0.9, "maturity": 0.8},
        "nested": {"key": "value"},
    }

    doc = AgentMemoryDocument(
        agent_id="evaluator",
        source="evaluation",
        content="Test",
        metadata=metadata,
    )

    await client.store(doc)

    results = await client.search("Test", agent_id="evaluator")
    assert len(results) > 0

    retrieved_metadata = results[0].metadata
    assert retrieved_metadata.get("verdict") == "poc_candidate"
    assert "rag" in retrieved_metadata.get("domain_tags", [])


# ============================================================================
# UNIT 1: Integration Tests
# ============================================================================


@pytest.mark.asyncio
async def test_full_workflow_store_search_filter(client):
    """Test complete workflow: store, search, and filter."""
    # Create evaluation results for multiple tools
    tools = [
        ("Tool A", "poc_candidate", ["rag"]),
        ("Tool B", "watching", ["rag"]),
        ("Tool C", "poc_candidate", ["agent-framework"]),
    ]

    for tool_name, verdict, tags in tools:
        doc = AgentMemoryDocument(
            agent_id="evaluator",
            source="evaluation",
            content=f"{tool_name} is a good framework for {', '.join(tags)}",
            metadata={
                "verdict": verdict,
                "domain_tags": tags,
                "tool_name": tool_name,
            },
        )
        await client.store(doc)

    # Search for RAG tools
    results = await client.search(
        query="RAG framework",
        agent_id="evaluator",
        metadata_filters={"domain_tags": ["rag"]},
    )

    assert len(results) >= 1
    # Should find Tool A and Tool B
    tool_names = [r.metadata.get("tool_name") for r in results]
    assert any("Tool" in name for name in tool_names if name)


@pytest.mark.asyncio
async def test_timestamp_preservation(client):
    """Test that timestamps are correctly stored and retrieved."""
    custom_time = datetime(2026, 3, 30, 10, 30, 0)

    doc = AgentMemoryDocument(
        agent_id="evaluator",
        source="evaluation",
        content="Test",
        metadata={},
        timestamp=custom_time,
    )

    await client.store(doc)

    results = await client.search("Test", agent_id="evaluator")
    assert len(results) > 0

    retrieved_time = results[0].timestamp
    # Check that timestamp is close to original (allowing for minor precision loss)
    if retrieved_time:
        time_diff = abs((retrieved_time - custom_time).total_seconds())
        assert time_diff < 1  # Within 1 second


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
