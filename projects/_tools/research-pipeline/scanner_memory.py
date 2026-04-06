"""Scanner and Writer memory integration — stores discoveries and analysis context.

This module provides utilities for:
1. Logging scanner discoveries to memory (pending evaluation)
2. Recording writer analysis and memory context
3. Tracking run metrics (unique vs re-evaluated, duplicates found)
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any

from agent_memory import AgentMemoryClient, AgentMemoryDocument

logger = logging.getLogger(__name__)


class ScannerMemoryLogger:
    """Log scanner discoveries to memory for duplicate detection."""

    def __init__(self, memory_client: AgentMemoryClient | None = None):
        """Initialize logger with optional memory client.

        Args:
            memory_client: Pre-initialized memory client, or None to create one.
        """
        self.memory_client = memory_client
        self._should_close = memory_client is None

    async def __aenter__(self):
        """Async context manager entry."""
        if self._should_close:
            self.memory_client = AgentMemoryClient()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._should_close and self.memory_client:
            try:
                await self.memory_client.close()
            except Exception as e:
                logger.warning(f"Error closing memory client: {e}")

    async def log_discovery(
        self,
        source: str,  # "github" | "arxiv" | "huggingface" | "web"
        name: str,
        url: str,
        description: str,
        domain_tags: list[str],
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Log a scanner discovery to memory.

        Args:
            source: Discovery source (github, arxiv, etc.)
            name: Tool/paper name
            url: URL to the resource
            description: 1-paragraph description
            domain_tags: Tags from ["rag", "agent-framework", "embedding-model", "tool"]
            metadata: Optional additional metadata (stars, authors, license, etc.)
        """
        if not self.memory_client:
            return

        try:
            doc = AgentMemoryDocument(
                agent_id="scanner",
                source=source,
                content=f"Discovered: {name} at {url}\n\n{description}",
                metadata={
                    "verdict": "pending",
                    "domain_tags": domain_tags,
                    "name": name,
                    "url": url,
                    "source_type": source,
                    **(metadata or {}),
                },
            )

            await self.memory_client.store(doc)
            logger.debug(f"Logged discovery: {name} ({source})")

        except Exception as e:
            logger.warning(f"Failed to log discovery {name}: {e}")


class WriterMemoryAnnotator:
    """Annotate writer output with memory context."""

    def __init__(self, memory_client: AgentMemoryClient | None = None):
        """Initialize annotator with optional memory client.

        Args:
            memory_client: Pre-initialized memory client, or None to create one.
        """
        self.memory_client = memory_client
        self._should_close = memory_client is None

    async def __aenter__(self):
        """Async context manager entry."""
        if self._should_close:
            self.memory_client = AgentMemoryClient()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._should_close and self.memory_client:
            try:
                await self.memory_client.close()
            except Exception as e:
                logger.warning(f"Error closing memory client: {e}")

    async def get_memory_status(
        self,
        tool_name: str,
        domain_tags: list[str] | None = None,
    ) -> dict[str, Any]:
        """Get memory status for a tool/paper.

        Returns:
            {
                "first_evaluation": bool,
                "previous_verdict": str | None,
                "previous_score": float | None,
                "days_since_previous": int | None,
                "trend": str  # "upgraded", "downgraded", "unchanged", "first"
            }
        """
        if not self.memory_client:
            return {"first_evaluation": True, "trend": "first"}

        try:
            # Search for previous evaluations
            query = f"{tool_name} evaluation"
            docs = await self.memory_client.search(
                query=query,
                agent_id="evaluator",
                top_k=5,
            )

            if not docs:
                return {"first_evaluation": True, "trend": "first"}

            # Check if we found a relevant previous verdict
            for doc in docs:
                if tool_name.lower() in doc.metadata.get("tool_name", "").lower():
                    prev_verdict = doc.metadata.get("verdict")
                    prev_score = doc.metadata.get("total_score")
                    prev_timestamp = doc.metadata.get("timestamp")

                    return {
                        "first_evaluation": False,
                        "previous_verdict": prev_verdict,
                        "previous_score": prev_score,
                        "timestamp": prev_timestamp,
                        "trend": "re-evaluation",
                    }

            return {"first_evaluation": True, "trend": "first"}

        except Exception as e:
            logger.warning(f"Failed to get memory status for {tool_name}: {e}")
            return {"first_evaluation": True, "trend": "first"}

    async def log_write_analysis(
        self,
        run_id: str,
        note_path: str,
        metrics: dict[str, Any],
    ) -> None:
        """Log writer analysis and metrics to memory.

        Args:
            run_id: Pipeline run identifier
            note_path: Path to generated note
            metrics: {"new_discoveries": N, "re_evaluations": M, "duplicates_skipped": K, ...}
        """
        if not self.memory_client:
            return

        try:
            doc = AgentMemoryDocument(
                agent_id="writer",
                source="write_analysis",
                content=f"Run {run_id}: wrote {note_path}\n\nMetrics: {metrics}",
                metadata={
                    "run_id": run_id,
                    "note_path": note_path,
                    **metrics,
                },
            )

            await self.memory_client.store(doc)
            logger.debug(f"Logged write analysis for run {run_id}")

        except Exception as e:
            logger.warning(f"Failed to log write analysis: {e}")


async def log_run_metrics(
    run_id: str,
    metrics: dict[str, Any],
    memory_client: AgentMemoryClient | None = None,
) -> None:
    """Convenience function to log run metrics to memory.

    Args:
        run_id: Pipeline run identifier
        metrics: {"scan_count": N, "eval_count": M, "poc_count": K, "duplicates": D, ...}
        memory_client: Optional pre-initialized client
    """
    should_close = memory_client is None
    if should_close:
        memory_client = AgentMemoryClient()

    try:
        doc = AgentMemoryDocument(
            agent_id="orchestrator",
            source="run_metrics",
            content=f"Pipeline run {run_id} completed\n\nMetrics: {metrics}",
            metadata={
                "run_id": run_id,
                "timestamp": datetime.utcnow().isoformat(),
                **metrics,
            },
        )

        await memory_client.store(doc)
        logger.info(f"Logged run metrics for {run_id}")

    except Exception as e:
        logger.warning(f"Failed to log run metrics: {e}")
    finally:
        if should_close:
            try:
                await memory_client.close()
            except Exception as e:
                logger.warning(f"Error closing memory client: {e}")
