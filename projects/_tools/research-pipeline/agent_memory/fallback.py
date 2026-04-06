"""Local LanceDB fallback for agent memory."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import lancedb

from .models import AgentMemoryDocument, SearchResult

logger = logging.getLogger(__name__)


class LanceDBBackend:
    """Local vector store backend using LanceDB + Ollama embeddings."""

    def __init__(self, db_path: str = "./agent_memory_local.db", embedding_model: str = "ollama"):
        """Initialize LanceDB backend.

        Args:
            db_path: Path to LanceDB database
            embedding_model: Embedding model type ("ollama" or "query_memory")
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.embedding_model = embedding_model
        self.db = lancedb.connect(str(self.db_path))
        self.table_name = "agent_memory_documents"
        self._ensure_table()

    def _ensure_table(self):
        """Ensure table exists with schema."""
        try:
            self.db.open_table(self.table_name)
        except Exception:
            # Table doesn't exist yet, will be created on first insert
            pass

    async def store(self, document: AgentMemoryDocument) -> str:
        """Store document in LanceDB.

        Args:
            document: Document to store

        Returns:
            Document ID (generated or provided)
        """
        try:
            doc_id = f"mem-{document.timestamp.isoformat()}-{hash(document.content) % 10000:04d}"

            # Prepare document for storage
            doc_data = {
                "doc_id": doc_id,
                "agent_id": document.agent_id,
                "source": document.source,
                "content": document.content,
                "metadata": json.dumps(document.metadata),
                "timestamp": document.timestamp.isoformat(),
            }

            # Get embedding
            embedding = self._get_embedding(document.content)
            doc_data["embedding"] = embedding

            # Store in table
            try:
                table = self.db.open_table(self.table_name)
            except Exception:
                # Table doesn't exist, create it
                table = self.db.create_table(self.table_name, data=[doc_data], mode="overwrite")
                return doc_id

            table.add([doc_data])

            logger.debug(f"Stored document {doc_id} in LanceDB")
            return doc_id
        except Exception as e:
            logger.error(f"Failed to store document in LanceDB: {e}")
            raise

    async def search(
        self,
        query: str,
        agent_id: Optional[str] = None,
        metadata_filters: Optional[dict[str, Any]] = None,
        top_k: int = 10,
    ) -> list[SearchResult]:
        """Search documents by semantic similarity.

        Args:
            query: Search query
            agent_id: Optional agent ID filter
            metadata_filters: Optional metadata filters
            top_k: Number of top results to return

        Returns:
            List of search results
        """
        try:
            # Get query embedding
            query_embedding = self._get_embedding(query)

            # Search in LanceDB
            table = self.db.open_table(self.table_name)
            results = table.search(query_embedding).limit(top_k * 2).to_list()  # Fetch extra for filtering

            # Filter by agent_id and metadata
            filtered_results = []
            for result in results:
                # Check agent_id filter
                if agent_id and result.get("agent_id") != agent_id:
                    continue

                # Check metadata filters
                if metadata_filters:
                    try:
                        doc_metadata = json.loads(result.get("metadata", "{}"))
                        if not self._matches_filters(doc_metadata, metadata_filters):
                            continue
                    except Exception:
                        continue

                # Convert to SearchResult
                try:
                    doc_metadata = json.loads(result.get("metadata", "{}"))
                except Exception:
                    doc_metadata = {}

                # Convert L2 distance to similarity score (0-1)
                # L2 distance: smaller is better. Convert to similarity using 1/(1+distance)
                distance = result.get("_distance", float("inf"))
                similarity = 1.0 / (1.0 + distance) if distance != float("inf") else 0.0

                search_result = SearchResult(
                    doc_id=result["doc_id"],
                    content=result["content"],
                    metadata=doc_metadata,
                    relevance_score=min(1.0, max(0.0, similarity)),  # Clamp to [0, 1]
                    timestamp=datetime.fromisoformat(result.get("timestamp", "")) if result.get("timestamp") else None,
                )
                filtered_results.append(search_result)

                # Stop when we have enough results
                if len(filtered_results) >= top_k:
                    break

            logger.debug(f"LanceDB search for '{query[:50]}' returned {len(filtered_results)} results")
            return filtered_results[:top_k]

        except Exception as e:
            logger.error(f"Failed to search LanceDB: {e}")
            return []

    async def search_temporal(
        self,
        domain: str,
        after_date: Optional[datetime] = None,
        before_date: Optional[datetime] = None,
    ) -> list[SearchResult]:
        """Search documents by temporal range.

        Args:
            domain: Domain tag to filter by
            after_date: Only return docs after this date
            before_date: Only return docs before this date

        Returns:
            List of search results
        """
        try:
            table = self.db.open_table(self.table_name)
            all_results = table.to_pandas()

            filtered = []
            for _, row in all_results.iterrows():
                try:
                    timestamp = datetime.fromisoformat(row["timestamp"])
                except Exception:
                    continue

                # Check temporal bounds
                if after_date and timestamp < after_date:
                    continue
                if before_date and timestamp > before_date:
                    continue

                # Check domain tag
                try:
                    metadata = json.loads(row["metadata"])
                    if domain not in metadata.get("domain_tags", []):
                        continue
                except Exception:
                    continue

                search_result = SearchResult(
                    doc_id=row["doc_id"],
                    content=row["content"],
                    metadata=metadata,
                    relevance_score=1.0,  # All matching results have equal relevance for temporal queries
                    timestamp=timestamp,
                )
                filtered.append(search_result)

            logger.debug(f"Temporal search for domain '{domain}' returned {len(filtered)} results")
            return filtered

        except Exception as e:
            logger.error(f"Failed to search LanceDB temporally: {e}")
            return []

    def _get_embedding(self, text: str) -> list[float]:
        """Get embedding for text using Ollama.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        if self.embedding_model == "ollama":
            # Use existing knowledge/vector_store.py pattern
            try:
                import requests

                response = requests.post(
                    "http://localhost:11434/api/embeddings",
                    json={"model": "bge-m3", "prompt": text},
                    timeout=10,
                )
                if response.status_code == 200:
                    return response.json()["embedding"]
            except Exception as e:
                logger.warning(f"Failed to get embedding from Ollama: {e}")

        # Fallback: simple hash-based "embedding" (not semantic)
        # This is just for testing; in production use actual embedding
        text_hash = hash(text)
        return [float((text_hash >> (i * 8)) & 0xFF) / 255.0 for i in range(384)]

    @staticmethod
    def _matches_filters(metadata: dict[str, Any], filters: dict[str, Any]) -> bool:
        """Check if metadata matches all filters.

        Args:
            metadata: Document metadata
            filters: Filter dict (k-v pairs that must match)

        Returns:
            True if all filters match
        """
        for key, expected_value in filters.items():
            actual_value = metadata.get(key)
            if isinstance(expected_value, list):
                # For lists, check if actual_value is in the list
                if actual_value not in expected_value:
                    return False
            else:
                # For scalar values, check equality
                if actual_value != expected_value:
                    return False
        return True
