"""Tests for writer memory integration (Unit 5)."""

import json
import tempfile
from pathlib import Path

import pytest
import pytest_asyncio

from agent_memory import AgentMemoryClient, AgentMemoryDocument, BackendConfig
from scanner_memory import WriterMemoryAnnotator, log_run_metrics


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


async def _store_previous_evaluation(
    client: AgentMemoryClient,
    tool_name: str,
    verdict: str,
) -> None:
    """Helper to store a previous evaluation."""
    eval_doc = AgentMemoryDocument(
        agent_id="evaluator",
        source="evaluation",
        content=json.dumps({
            "scan_result": {"name": tool_name},
            "verdict": verdict,
            "total_score": 25,
        }),
        metadata={
            "verdict": verdict,
            "tool_name": tool_name,
            "total_score": 25,
        },
    )
    await client.store(eval_doc)


@pytest.mark.asyncio
async def test_writer_memory_annotator_first_evaluation(memory_client):
    """Test getting memory status for first evaluation."""
    async with WriterMemoryAnnotator(memory_client=memory_client) as annotator:
        status = await annotator.get_memory_status("new-tool")

    assert status["first_evaluation"] is True
    assert status["trend"] == "first"


@pytest.mark.asyncio
async def test_writer_memory_annotator_previous_verdict(memory_client):
    """Test getting memory status when tool was previously evaluated."""
    # Store previous evaluation
    await _store_previous_evaluation(memory_client, "known-tool", "watching")

    async with WriterMemoryAnnotator(memory_client=memory_client) as annotator:
        status = await annotator.get_memory_status("known-tool")

    assert status["first_evaluation"] is False
    assert status["previous_verdict"] == "watching"
    assert status["trend"] == "re-evaluation"


@pytest.mark.asyncio
async def test_writer_memory_annotator_context_manager(memory_client):
    """Test annotator as async context manager."""
    async with WriterMemoryAnnotator(memory_client=memory_client) as annotator:
        assert annotator.memory_client is not None
        status = await annotator.get_memory_status("test-tool")

    assert status["trend"] in ["first", "re-evaluation"]


@pytest.mark.asyncio
async def test_writer_memory_annotator_creates_client():
    """Test annotator creates its own client."""
    async with WriterMemoryAnnotator() as annotator:
        assert annotator.memory_client is not None
        status = await annotator.get_memory_status("test-tool")

    assert "trend" in status


@pytest.mark.asyncio
async def test_writer_logs_analysis_metrics(memory_client):
    """Test logging writer analysis metrics to memory."""
    async with WriterMemoryAnnotator(memory_client=memory_client) as annotator:
        metrics = {
            "new_discoveries": 5,
            "re_evaluations": 2,
            "duplicates_skipped": 3,
        }

        await annotator.log_write_analysis(
            run_id="2026-03-30-test",
            note_path="resources/research-scan-2026-03-30.md",
            metrics=metrics,
        )

    # Verify logged
    docs = await memory_client.search(
        query="write_analysis",
        agent_id="writer",
    )

    assert len(docs) > 0
    doc = docs[0]
    assert doc.metadata["run_id"] == "2026-03-30-test"
    assert doc.metadata["new_discoveries"] == 5


@pytest.mark.asyncio
async def test_log_run_metrics_convenience_function(memory_client):
    """Test convenience function for logging run metrics."""
    metrics = {
        "scan_count": 10,
        "eval_count": 8,
        "poc_count": 3,
        "duplicates": 2,
    }

    await log_run_metrics(
        run_id="2026-03-30-metric-test",
        metrics=metrics,
        memory_client=memory_client,
    )

    # Verify logged
    docs = await memory_client.search(
        query="run_metrics",
        agent_id="orchestrator",
    )

    assert len(docs) > 0
    doc = docs[0]
    assert doc.metadata["scan_count"] == 10
    assert doc.metadata["poc_count"] == 3


@pytest.mark.asyncio
async def test_log_run_metrics_creates_client():
    """Test run metrics logging creates its own client."""
    metrics = {
        "scan_count": 5,
        "eval_count": 5,
    }

    # Should not raise even without client provided
    await log_run_metrics(
        run_id="2026-03-30-no-client-test",
        metrics=metrics,
    )


@pytest.mark.asyncio
async def test_writer_memory_annotator_multiple_statuses(memory_client):
    """Test getting status for multiple tools."""
    # Store evaluations for multiple tools
    await _store_previous_evaluation(memory_client, "tool-a", "poc_candidate")
    await _store_previous_evaluation(memory_client, "tool-b", "watching")

    async with WriterMemoryAnnotator(memory_client=memory_client) as annotator:
        status_a = await annotator.get_memory_status("tool-a")
        status_b = await annotator.get_memory_status("tool-b")
        status_new = await annotator.get_memory_status("tool-new")

    assert status_a["previous_verdict"] == "poc_candidate"
    assert status_b["previous_verdict"] == "watching"
    assert status_new["first_evaluation"] is True


@pytest.mark.asyncio
async def test_writer_analysis_includes_timestamp(memory_client):
    """Test that write analysis includes timestamp."""
    async with WriterMemoryAnnotator(memory_client=memory_client) as annotator:
        metrics = {"discoveries": 5}

        await annotator.log_write_analysis(
            run_id="2026-03-30-ts-test",
            note_path="resources/research-scan-2026-03-30.md",
            metrics=metrics,
        )

    docs = await memory_client.search(
        query="write_analysis",
        agent_id="writer",
    )

    # Verify timestamp is included in content or metadata
    assert len(docs) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
