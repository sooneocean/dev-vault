"""Tests for evaluator memory integration (Unit 4)."""

import json
import tempfile
from datetime import date
from pathlib import Path

import pytest
import pytest_asyncio

from agent_memory import AgentMemoryClient, BackendConfig
from evaluator import _store_evaluation_to_memory
from models import EvaluationResult, EvaluationScore, ScanResult, SourceType, Verdict


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


def create_test_evaluation_result() -> EvaluationResult:
    """Create a test evaluation result."""
    sr = ScanResult(
        source=SourceType.GITHUB,
        name="test-tool",
        url="https://github.com/test/test",
        description="A test tool",
        stars=100,
        tags=["rag", "agent-framework"],
        is_paper=False,
    )

    scores = [
        EvaluationScore(dimension="Relevance", score=8, reasoning="Relevant to RAG"),
        EvaluationScore(dimension="Maturity", score=6, reasoning="Active project"),
    ]

    return EvaluationResult(
        scan_result=sr,
        scores=scores,
        total_score=14,
        max_score=20,
        percentage=70.0,
        verdict=Verdict.POC_CANDIDATE,
        recommended_action="Try in PoC",
    )


@pytest.mark.asyncio
async def test_store_evaluation_to_memory(memory_client):
    """Test storing evaluation result to memory."""
    result = create_test_evaluation_result()

    # Store to memory
    await _store_evaluation_to_memory(memory_client, result)

    # Retrieve and verify
    docs = await memory_client.search(
        query="test-tool",
        agent_id="evaluator",
    )

    assert len(docs) > 0
    doc = docs[0]

    # Verify metadata
    assert doc.metadata["tool_name"] == "test-tool"
    assert doc.metadata["verdict"] == "poc_candidate"
    assert doc.metadata["total_score"] == 14
    assert "rag" in doc.metadata.get("domain_tags", [])


@pytest.mark.asyncio
async def test_store_evaluation_metadata(memory_client):
    """Test that evaluation metadata is correctly stored."""
    result = create_test_evaluation_result()
    await _store_evaluation_to_memory(memory_client, result)

    docs = await memory_client.search(
        query="poc_candidate",
        agent_id="evaluator",
    )

    assert len(docs) > 0
    doc = docs[0]

    # Verify all metadata fields
    assert doc.metadata["verdict"] == "poc_candidate"
    assert doc.metadata["source_type"] == "github"
    assert doc.metadata["url"] == "https://github.com/test/test"
    assert doc.metadata["total_score"] == 14
    assert doc.metadata["max_score"] == 20
    assert doc.metadata["percentage"] == 70.0
    assert "rag" in doc.metadata["domain_tags"]


@pytest.mark.asyncio
async def test_store_evaluation_content_is_valid_json(memory_client):
    """Test that stored content is valid JSON."""
    result = create_test_evaluation_result()
    await _store_evaluation_to_memory(memory_client, result)

    docs = await memory_client.search(
        query="test-tool",
        agent_id="evaluator",
    )

    assert len(docs) > 0
    doc = docs[0]

    # Parse stored JSON
    stored_eval = json.loads(doc.content)

    assert stored_eval["verdict"] == "poc_candidate"
    assert stored_eval["scan_result"]["name"] == "test-tool"
    assert len(stored_eval["scores"]) == 2


@pytest.mark.asyncio
async def test_store_multiple_evaluations(memory_client):
    """Test storing multiple evaluation results."""
    results = [
        EvaluationResult(
            scan_result=ScanResult(
                source=SourceType.GITHUB,
                name=f"tool-{i}",
                url=f"https://github.com/test/tool-{i}",
                tags=["rag"],
            ),
            scores=[],
            total_score=i * 10,
            max_score=50,
            percentage=i * 20.0,
            verdict=Verdict.POC_CANDIDATE if i % 2 == 0 else Verdict.WATCHING,
        )
        for i in range(3)
    ]

    # Store all
    for result in results:
        await _store_evaluation_to_memory(memory_client, result)

    # Verify all stored
    docs = await memory_client.search(
        query="tool",
        agent_id="evaluator",
        top_k=10,
    )

    assert len(docs) == 3


@pytest.mark.asyncio
async def test_domain_tags_extraction(memory_client):
    """Test that domain tags are correctly extracted from scan result tags."""
    sr = ScanResult(
        source=SourceType.GITHUB,
        name="tool",
        url="https://github.com/test/tool",
        tags=["rag", "agent-framework", "other-tag", "embedding-model"],
    )

    result = EvaluationResult(
        scan_result=sr,
        scores=[],
        total_score=0,
        max_score=0,
        percentage=0.0,
        verdict=Verdict.NOT_APPLICABLE,
    )

    await _store_evaluation_to_memory(memory_client, result)

    docs = await memory_client.search(query="tool", agent_id="evaluator")

    assert len(docs) > 0
    doc = docs[0]

    # Only domain tags should be included
    domain_tags = doc.metadata.get("domain_tags", [])
    assert "rag" in domain_tags
    assert "agent-framework" in domain_tags
    assert "embedding-model" in domain_tags
    assert "other-tag" not in domain_tags


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
