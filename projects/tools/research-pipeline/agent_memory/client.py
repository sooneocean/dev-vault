"""Agent memory client with Query Memory primary and LanceDB fallback."""

from __future__ import annotations

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Any, Optional

import httpx

from .fallback import LanceDBBackend
from .models import AgentMemoryDocument, BackendConfig, SearchResult

logger = logging.getLogger(__name__)


class QueryMemoryBackend:
    """Query Memory backend for cloud-based storage."""

    def __init__(self, api_url: str, api_key: str):
        """Initialize Query Memory backend.

        Args:
            api_url: Query Memory API URL
            api_key: API key for authentication
        """
        self.api_url = api_url.rstrip("/")
        self.api_key = api_key
        self.client = httpx.AsyncClient(
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            timeout=10.0,
        )

    async def store(self, document: AgentMemoryDocument) -> str:
        """Store document in Query Memory.

        Args:
            document: Document to store

        Returns:
            Document ID
        """
        try:
            payload = {
                "title": f"{document.agent_id}:{document.source}",
                "content": document.content,
                "metadata": document.metadata,
                "tags": [document.agent_id, document.source] + document.metadata.get("domain_tags", []),
            }

            response = await self.client.post(f"{self.api_url}/documents", json=payload)
            response.raise_for_status()

            result = response.json()
            doc_id = result.get("id") or result.get("document_id")

            logger.debug(f"Stored document {doc_id} in Query Memory")
            return doc_id
        except Exception as e:
            logger.error(f"Failed to store document in Query Memory: {e}")
            raise

    async def search(
        self,
        query: str,
        agent_id: Optional[str] = None,
        metadata_filters: Optional[dict[str, Any]] = None,
        top_k: int = 10,
        context_preamble: Optional[str] = None,
    ) -> list[SearchResult]:
        """Search documents in Query Memory.

        Args:
            query: Search query
            agent_id: Optional agent ID filter
            metadata_filters: Optional metadata filters
            top_k: Number of top results
            context_preamble: Optional context to prepend to query

        Returns:
            List of search results
        """
        try:
            # Prepend context if provided
            search_query = f"{context_preamble}\n{query}" if context_preamble else query

            payload = {
                "query": search_query,
                "limit": top_k,
            }

            # Add filters if provided
            if agent_id or metadata_filters:
                filters = {}
                if agent_id:
                    filters["agent_id"] = agent_id
                if metadata_filters:
                    filters.update(metadata_filters)
                payload["filters"] = filters

            response = await self.client.post(f"{self.api_url}/search", json=payload)
            response.raise_for_status()

            results = response.json().get("results", [])

            search_results = []
            for result in results:
                search_results.append(
                    SearchResult(
                        doc_id=result.get("id") or result.get("document_id"),
                        content=result.get("content", ""),
                        metadata=result.get("metadata", {}),
                        relevance_score=float(result.get("score", 0.0)),
                        timestamp=datetime.fromisoformat(result["created_at"]) if result.get("created_at") else None,
                    )
                )

            logger.debug(f"Query Memory search returned {len(search_results)} results")
            return search_results
        except Exception as e:
            logger.error(f"Failed to search Query Memory: {e}")
            raise

    async def search_temporal(
        self,
        domain: str,
        after_date: Optional[datetime] = None,
        before_date: Optional[datetime] = None,
    ) -> list[SearchResult]:
        """Search documents by temporal range in Query Memory.

        Args:
            domain: Domain tag to filter by
            after_date: Only return docs after this date
            before_date: Only return docs before this date

        Returns:
            List of search results
        """
        try:
            filters = {"domain_tags": [domain]}

            if after_date:
                filters["created_after"] = after_date.isoformat()
            if before_date:
                filters["created_before"] = before_date.isoformat()

            payload = {"query": domain, "filters": filters, "limit": 100}

            response = await self.client.post(f"{self.api_url}/search", json=payload)
            response.raise_for_status()

            results = response.json().get("results", [])

            search_results = []
            for result in results:
                search_results.append(
                    SearchResult(
                        doc_id=result.get("id") or result.get("document_id"),
                        content=result.get("content", ""),
                        metadata=result.get("metadata", {}),
                        relevance_score=1.0,
                        timestamp=datetime.fromisoformat(result["created_at"]) if result.get("created_at") else None,
                    )
                )

            logger.debug(f"Query Memory temporal search returned {len(search_results)} results")
            return search_results
        except Exception as e:
            logger.error(f"Failed to search Query Memory temporally: {e}")
            raise

    async def close(self):
        """Close the client."""
        await self.client.aclose()


class AgentMemoryClient:
    """Unified agent memory client: Query Memory primary with LanceDB fallback."""

    def __init__(self, config: Optional[BackendConfig] = None):
        """Initialize agent memory client.

        Args:
            config: Backend configuration. If None, loads from environment variables.
        """
        if config is None:
            config = self._config_from_env()

        self.config = config
        self.use_query_memory = config.use_query_memory
        self.fallback_timeout = config.fallback_timeout_seconds

        # Initialize backends
        self.query_memory_backend: Optional[QueryMemoryBackend] = None
        self.lancedb_backend = LanceDBBackend(
            db_path=config.lancedb_path,
            embedding_model=config.embedding_model,
        )

        if self.use_query_memory:
            try:
                self.query_memory_backend = QueryMemoryBackend(
                    api_url=config.query_memory_api_url,
                    api_key=config.query_memory_api_key,
                )
                logger.info("Initialized Query Memory backend")
            except Exception as e:
                logger.warning(f"Failed to initialize Query Memory backend: {e}. Using LanceDB only.")
                self.query_memory_backend = None

    @staticmethod
    def _config_from_env() -> BackendConfig:
        """Load configuration from environment variables."""
        return BackendConfig(
            use_query_memory=os.getenv("AGENT_MEMORY_USE_QUERY_MEMORY", "true").lower() == "true",
            query_memory_api_url=os.getenv("QUERY_MEMORY_API_URL", "https://api.querymemory.com"),
            query_memory_api_key=os.getenv("QUERY_MEMORY_API_KEY", ""),
            lancedb_path=os.getenv("AGENT_MEMORY_LANCEDB_PATH", "./agent_memory_local.db"),
            fallback_timeout_seconds=float(os.getenv("AGENT_MEMORY_FALLBACK_TIMEOUT", "5.0")),
            embedding_model=os.getenv("AGENT_MEMORY_EMBEDDING_MODEL", "ollama"),
        )

    async def store(self, document: AgentMemoryDocument) -> str:
        """Store document in agent memory.

        Primary: Query Memory
        Fallback: LanceDB (on timeout or error)

        Args:
            document: Document to store

        Returns:
            Document ID
        """
        # Try Query Memory first
        if self.query_memory_backend:
            try:
                doc_id = await asyncio.wait_for(
                    self.query_memory_backend.store(document),
                    timeout=self.fallback_timeout,
                )
                logger.debug(f"Successfully stored document {doc_id} in Query Memory")
                return doc_id
            except asyncio.TimeoutError:
                logger.warning("Query Memory store timeout, falling back to LanceDB")
            except Exception as e:
                logger.warning(f"Query Memory store failed: {e}, falling back to LanceDB")

        # Fallback to LanceDB
        try:
            doc_id = await self.lancedb_backend.store(document)
            logger.info(f"Stored document in LanceDB fallback: {doc_id}")
            return doc_id
        except Exception as e:
            logger.error(f"Failed to store document in both backends: {e}")
            raise

    async def search(
        self,
        query: str,
        agent_id: Optional[str] = None,
        metadata_filters: Optional[dict[str, Any]] = None,
        top_k: int = 10,
        context_preamble: Optional[str] = None,
    ) -> list[SearchResult]:
        """Search agent memory with semantic similarity.

        Primary: Query Memory
        Fallback: LanceDB (on timeout or error)

        Args:
            query: Search query
            agent_id: Optional agent ID filter
            metadata_filters: Optional metadata filters
            top_k: Number of top results
            context_preamble: Optional context for embedding relevance

        Returns:
            List of search results
        """
        # Try Query Memory first
        if self.query_memory_backend:
            try:
                results = await asyncio.wait_for(
                    self.query_memory_backend.search(
                        query=query,
                        agent_id=agent_id,
                        metadata_filters=metadata_filters,
                        top_k=top_k,
                        context_preamble=context_preamble,
                    ),
                    timeout=self.fallback_timeout,
                )
                logger.debug(f"Query Memory search returned {len(results)} results")
                return results
            except asyncio.TimeoutError:
                logger.warning("Query Memory search timeout, falling back to LanceDB")
            except Exception as e:
                logger.warning(f"Query Memory search failed: {e}, falling back to LanceDB")

        # Fallback to LanceDB
        try:
            results = await self.lancedb_backend.search(
                query=query,
                agent_id=agent_id,
                metadata_filters=metadata_filters,
                top_k=top_k,
            )
            logger.info(f"LanceDB fallback search returned {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"Search failed in both backends: {e}")
            return []

    async def search_temporal(
        self,
        domain: str,
        after_date: Optional[datetime] = None,
        before_date: Optional[datetime] = None,
    ) -> list[SearchResult]:
        """Search documents by temporal range.

        Primary: Query Memory
        Fallback: LanceDB (on timeout or error)

        Args:
            domain: Domain tag to filter by
            after_date: Only return docs after this date
            before_date: Only return docs before this date

        Returns:
            List of search results
        """
        # Try Query Memory first
        if self.query_memory_backend:
            try:
                results = await asyncio.wait_for(
                    self.query_memory_backend.search_temporal(
                        domain=domain,
                        after_date=after_date,
                        before_date=before_date,
                    ),
                    timeout=self.fallback_timeout,
                )
                logger.debug(f"Query Memory temporal search returned {len(results)} results")
                return results
            except asyncio.TimeoutError:
                logger.warning("Query Memory temporal search timeout, falling back to LanceDB")
            except Exception as e:
                logger.warning(f"Query Memory temporal search failed: {e}, falling back to LanceDB")

        # Fallback to LanceDB
        try:
            results = await self.lancedb_backend.search_temporal(
                domain=domain,
                after_date=after_date,
                before_date=before_date,
            )
            logger.info(f"LanceDB fallback temporal search returned {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"Temporal search failed in both backends: {e}")
            return []

    async def close(self):
        """Close all connections."""
        if self.query_memory_backend:
            await self.query_memory_backend.close()
