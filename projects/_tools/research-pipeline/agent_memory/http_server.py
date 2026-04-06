"""FastAPI HTTP server for agent memory system."""

from __future__ import annotations

import argparse
import asyncio
import logging
from datetime import datetime
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .client import AgentMemoryClient
from .models import AgentMemoryDocument, BackendConfig

logger = logging.getLogger(__name__)

# Global memory client
memory_client: AgentMemoryClient | None = None


def get_memory_client() -> AgentMemoryClient:
    """Get or initialize global memory client."""
    global memory_client
    if memory_client is None:
        memory_client = AgentMemoryClient()
    return memory_client


def create_app() -> FastAPI:
    """Create and configure FastAPI app."""
    app = FastAPI(
        title="Agent Memory API",
        description="Persistent memory system for Claude Code subagents",
        version="1.0.0",
    )

    # Add CORS middleware for webhook callbacks
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ========================================================================
    # Health Check
    # ========================================================================

    @app.get("/health", tags=["health"])
    async def health_check() -> dict[str, str]:
        """Check server health."""
        try:
            client = get_memory_client()
            return {"status": "healthy", "backend": "ready"}
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            raise HTTPException(status_code=503, detail=f"Backend unavailable: {e}")

    # ========================================================================
    # Store Operations
    # ========================================================================

    @app.post("/memory/store", tags=["memory"])
    async def store_document(
        agent_id: str,
        source: str,
        content: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Store a document in agent memory.

        Args:
            agent_id: ID of storing agent
            source: Source type (evaluation, github, arxiv, feedback)
            content: Document content
            metadata: Optional metadata (verdict, domain_tags, etc.)

        Returns:
            doc_id and status
        """
        try:
            if not content.strip():
                raise ValueError("Content cannot be empty")

            client = get_memory_client()

            document = AgentMemoryDocument(
                agent_id=agent_id,
                source=source,
                content=content,
                metadata=metadata or {},
            )

            doc_id = await client.store(document)

            return {"doc_id": doc_id, "status": "stored"}

        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Store failed: {e}")
            raise HTTPException(status_code=500, detail=f"Store failed: {e}")

    @app.post("/memory/batch_store", tags=["memory"])
    async def batch_store_documents(
        request_body: dict[str, list[dict[str, Any]]],
    ) -> dict[str, Any]:
        """Store multiple documents in batch.

        Args:
            request_body: Dict containing 'documents' key with list of document dicts

        Returns:
            Count of stored and failed documents
        """
        try:
            documents = request_body.get("documents", [])
            client = get_memory_client()

            stored_count = 0
            failed_count = 0

            for doc_dict in documents:
                try:
                    doc = AgentMemoryDocument(
                        agent_id=doc_dict.get("agent_id", "unknown"),
                        source=doc_dict.get("source", "unknown"),
                        content=doc_dict.get("content", ""),
                        metadata=doc_dict.get("metadata", {}),
                    )
                    await client.store(doc)
                    stored_count += 1
                except Exception as e:
                    logger.warning(f"Failed to store document: {e}")
                    failed_count += 1

            return {"stored": stored_count, "failed": failed_count}

        except Exception as e:
            logger.error(f"Batch store failed: {e}")
            raise HTTPException(status_code=500, detail=f"Batch store failed: {e}")

    # ========================================================================
    # Search Operations
    # ========================================================================

    @app.get("/memory/search", tags=["memory"])
    async def search_memory(
        query: str = Query(..., description="Search query"),
        agent_id: Optional[str] = Query(None, description="Filter by agent ID"),
        top_k: int = Query(10, description="Number of results"),
        context_preamble: Optional[str] = Query(None, description="Context for embedding"),
    ) -> dict[str, Any]:
        """Search agent memory by semantic similarity.

        Args:
            query: Search query
            agent_id: Optional agent filter
            top_k: Number of top results
            context_preamble: Optional context for relevance

        Returns:
            List of search results with metadata and scores
        """
        try:
            if not query.strip():
                raise ValueError("Query cannot be empty")

            if top_k < 1 or top_k > 100:
                raise ValueError("top_k must be between 1 and 100")

            client = get_memory_client()

            results = await client.search(
                query=query,
                agent_id=agent_id,
                top_k=top_k,
                context_preamble=context_preamble,
            )

            return {
                "results": [
                    {
                        "doc_id": r.doc_id,
                        "content": r.content,
                        "metadata": r.metadata,
                        "relevance_score": r.relevance_score,
                        "timestamp": r.timestamp.isoformat() if r.timestamp else None,
                    }
                    for r in results
                ],
                "count": len(results),
            }

        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise HTTPException(status_code=500, detail=f"Search failed: {e}")

    # ========================================================================
    # Temporal Search
    # ========================================================================

    @app.get("/memory/temporal", tags=["memory"])
    async def search_temporal(
        domain: str = Query(..., description="Domain tag to filter by"),
        after_date: Optional[str] = Query(None, description="ISO8601 start date"),
        before_date: Optional[str] = Query(None, description="ISO8601 end date"),
    ) -> dict[str, Any]:
        """Search agent memory by temporal range and domain.

        Args:
            domain: Domain tag to filter by
            after_date: ISO8601 date (only return docs after this)
            before_date: ISO8601 date (only return docs before this)

        Returns:
            List of temporal search results
        """
        try:
            if not domain.strip():
                raise ValueError("Domain cannot be empty")

            client = get_memory_client()

            # Parse dates
            after = None
            if after_date:
                try:
                    after = datetime.fromisoformat(after_date)
                except ValueError:
                    raise ValueError(f"Invalid after_date format: {after_date}")

            before = None
            if before_date:
                try:
                    before = datetime.fromisoformat(before_date)
                except ValueError:
                    raise ValueError(f"Invalid before_date format: {before_date}")

            if after and before and after > before:
                raise ValueError("after_date must be before before_date")

            results = await client.search_temporal(
                domain=domain,
                after_date=after,
                before_date=before,
            )

            return {
                "results": [
                    {
                        "doc_id": r.doc_id,
                        "content": r.content,
                        "metadata": r.metadata,
                        "relevance_score": r.relevance_score,
                        "timestamp": r.timestamp.isoformat() if r.timestamp else None,
                    }
                    for r in results
                ],
                "count": len(results),
            }

        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Temporal search failed: {e}")
            raise HTTPException(status_code=500, detail=f"Temporal search failed: {e}")

    return app


async def run_server(host: str = "0.0.0.0", port: int = 8765):
    """Run the HTTP server.

    Args:
        host: Host to bind to
        port: Port to bind to
    """
    import uvicorn

    app = create_app()

    config = uvicorn.Config(app, host=host, port=port, log_level="info")
    server = uvicorn.Server(config)

    logger.info(f"Starting Agent Memory HTTP server on {host}:{port}")
    await server.serve()


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Agent Memory HTTP Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8765, help="Port to bind to")
    parser.add_argument("--log-level", default="info", help="Log level")

    args = parser.parse_args()

    logging.basicConfig(level=args.log_level.upper())

    asyncio.run(run_server(host=args.host, port=args.port))


if __name__ == "__main__":
    main()
