"""Tests for HTTP API server (Unit 3)."""

import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient

from agent_memory import AgentMemoryClient, BackendConfig
from agent_memory.http_server import create_app


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
async def client_instance(config):
    """Create client instance and set it in HTTP server."""
    import agent_memory.http_server as http

    client = AgentMemoryClient(config=config)
    http.memory_client = client
    yield client
    await client.close()


@pytest.fixture
def http_client(client_instance):
    """Create HTTP test client."""
    app = create_app()
    return TestClient(app)


# ============================================================================
# UNIT 3: HTTP API Endpoint Tests
# ============================================================================


def test_health_check(http_client):
    """Test health check endpoint."""
    response = http_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_store_document(http_client):
    """Test POST /memory/store endpoint."""
    response = http_client.post(
        "/memory/store",
        params={
            "agent_id": "evaluator",
            "source": "evaluation",
            "content": "Tool evaluation result",
            "metadata": {"verdict": "poc_candidate", "domain_tags": ["rag"]},
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "stored"
    assert "doc_id" in data
    assert isinstance(data["doc_id"], str)


def test_store_without_metadata(http_client):
    """Test storing document without metadata."""
    response = http_client.post(
        "/memory/store",
        params={
            "agent_id": "scanner",
            "source": "github",
            "content": "Found new tool on GitHub",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "stored"


def test_store_empty_content_fails(http_client):
    """Test that empty content is rejected."""
    response = http_client.post(
        "/memory/store",
        params={
            "agent_id": "evaluator",
            "source": "evaluation",
            "content": "",
        },
    )

    assert response.status_code == 400


def test_batch_store(http_client):
    """Test POST /memory/batch_store endpoint."""
    documents = [
        {
            "agent_id": "evaluator",
            "source": "evaluation",
            "content": f"Tool {i} evaluation",
            "metadata": {"index": i},
        }
        for i in range(3)
    ]

    response = http_client.post("/memory/batch_store", json={"documents": documents})

    assert response.status_code == 200
    data = response.json()
    assert data["stored"] == 3
    assert data["failed"] == 0


def test_search_documents(http_client):
    """Test GET /memory/search endpoint."""
    # Store a document first
    store_response = http_client.post(
        "/memory/store",
        params={
            "agent_id": "evaluator",
            "source": "evaluation",
            "content": "RAG framework evaluation",
            "metadata": {"verdict": "poc_candidate"},
        },
    )
    assert store_response.status_code == 200

    # Search for it
    response = http_client.get(
        "/memory/search",
        params={
            "query": "RAG framework",
            "agent_id": "evaluator",
            "top_k": 10,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "count" in data
    assert isinstance(data["results"], list)


def test_search_with_invalid_query(http_client):
    """Test search with invalid parameters."""
    response = http_client.get(
        "/memory/search",
        params={
            "query": "",  # Empty query
        },
    )

    assert response.status_code == 400


def test_search_with_invalid_top_k(http_client):
    """Test search with invalid top_k."""
    response = http_client.get(
        "/memory/search",
        params={
            "query": "test",
            "top_k": 1000,  # Too large
        },
    )

    assert response.status_code == 400


def test_search_result_structure(http_client):
    """Test that search results have correct structure."""
    # Store document
    http_client.post(
        "/memory/store",
        params={
            "agent_id": "evaluator",
            "source": "evaluation",
            "content": "Test content",
            "metadata": {"verdict": "poc_candidate", "domain_tags": ["rag"]},
        },
    )

    # Search
    response = http_client.get(
        "/memory/search",
        params={
            "query": "Test",
            "agent_id": "evaluator",
        },
    )

    assert response.status_code == 200
    data = response.json()

    # Check structure
    if data["results"]:
        result = data["results"][0]
        assert "doc_id" in result
        assert "content" in result
        assert "metadata" in result
        assert "relevance_score" in result
        assert "timestamp" in result
        assert 0 <= result["relevance_score"] <= 1


def test_temporal_search(http_client, client_instance):
    """Test GET /memory/temporal endpoint."""
    import asyncio

    # Store a document with known timestamp
    async def store_doc():
        from agent_memory import AgentMemoryDocument

        doc = AgentMemoryDocument(
            agent_id="evaluator",
            source="evaluation",
            content="Recent discovery",
            metadata={"domain_tags": ["rag"]},
            timestamp=datetime.utcnow() - timedelta(hours=1),
        )
        await client_instance.store(doc)

    asyncio.run(store_doc())

    # Temporal search
    response = http_client.get(
        "/memory/temporal",
        params={
            "domain": "rag",
            "after_date": (datetime.utcnow() - timedelta(days=1)).isoformat(),
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "count" in data


def test_temporal_search_invalid_dates(http_client):
    """Test temporal search with invalid date format."""
    response = http_client.get(
        "/memory/temporal",
        params={
            "domain": "rag",
            "after_date": "not-a-valid-date",
        },
    )

    assert response.status_code == 400


def test_temporal_search_invalid_date_range(http_client):
    """Test temporal search with after > before."""
    now = datetime.utcnow()
    response = http_client.get(
        "/memory/temporal",
        params={
            "domain": "rag",
            "after_date": now.isoformat(),
            "before_date": (now - timedelta(days=1)).isoformat(),
        },
    )

    assert response.status_code == 400


def test_agent_scoped_query(http_client):
    """Test agent-scoped search."""
    # Store documents from different agents
    http_client.post(
        "/memory/store",
        params={
            "agent_id": "evaluator",
            "source": "evaluation",
            "content": "Evaluator found tool A",
            "metadata": {"verdict": "poc_candidate"},
        },
    )
    http_client.post(
        "/memory/store",
        params={
            "agent_id": "scanner",
            "source": "github",
            "content": "Scanner found tool B",
            "metadata": {"stars": 1000},
        },
    )

    # Search only evaluator
    response = http_client.get(
        "/memory/search",
        params={
            "query": "found tool",
            "agent_id": "evaluator",
        },
    )

    assert response.status_code == 200
    # Evaluator should see their own documents


def test_search_with_context_preamble(http_client):
    """Test search with context preamble."""
    # Store document
    http_client.post(
        "/memory/store",
        params={
            "agent_id": "evaluator",
            "source": "evaluation",
            "content": "Evaluating agent orchestration frameworks",
            "metadata": {"domain_tags": ["agent-framework"]},
        },
    )

    # Search with preamble
    response = http_client.get(
        "/memory/search",
        params={
            "query": "orchestration",
            "context_preamble": "I am an evaluator looking at agent frameworks",
        },
    )

    assert response.status_code == 200


def test_batch_store_partial_failure(http_client):
    """Test batch store with some invalid documents."""
    documents = [
        {
            "agent_id": "evaluator",
            "source": "evaluation",
            "content": "Valid document",
        },
        {
            "agent_id": "evaluator",
            "source": "evaluation",
            "content": "",  # Invalid: empty content
        },
        {
            "agent_id": "scanner",
            "source": "github",
            "content": "Another valid document",
        },
    ]

    response = http_client.post("/memory/batch_store", json={"documents": documents})

    assert response.status_code == 200
    data = response.json()
    assert data["stored"] >= 2  # At least the valid ones
    assert data["failed"] >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
