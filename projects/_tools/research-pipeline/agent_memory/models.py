"""Data models for agent memory system."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class AgentMemoryDocument(BaseModel):
    """A document stored in agent memory."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "agent_id": "evaluator",
                "source": "evaluation",
                "content": "Tool evaluation result for RAG framework X",
                "metadata": {
                    "verdict": "poc_candidate",
                    "domain_tags": ["rag", "agent-framework"],
                    "tool_name": "Example Tool",
                    "tool_url": "https://github.com/example/tool",
                    "scores": {"relevance": 8, "maturity": 6},
                    "run_id": "2026-03-30-abc123",
                },
                "timestamp": "2026-03-30T10:30:00Z",
            }
        }
    )

    agent_id: str = Field(..., description="ID of the agent that created this document (e.g., 'evaluator', 'scanner')")
    source: str = Field(..., description="Source of the document (e.g., 'evaluation', 'github', 'arxiv', 'human_feedback')")
    content: str = Field(..., description="Primary content (tool description, eval result, etc.)")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Rich metadata for filtering and context")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When this document was created")


class SearchResult(BaseModel):
    """Result from a memory search."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "doc_id": "mem-abc123",
                "content": "Tool evaluation result...",
                "metadata": {"verdict": "poc_candidate", "domain_tags": ["rag"]},
                "relevance_score": 0.92,
                "timestamp": "2026-03-30T10:30:00Z",
            }
        }
    )

    doc_id: str = Field(..., description="Unique document ID")
    content: str = Field(..., description="Document content")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Document metadata")
    relevance_score: float = Field(..., description="Relevance score (0-1 for Query Memory, cosine similarity for LanceDB)")
    timestamp: Optional[datetime] = Field(None, description="When the document was created")


class BackendConfig(BaseModel):
    """Configuration for memory backend."""

    model_config = ConfigDict(extra="allow")

    use_query_memory: bool = Field(default=True, description="Whether to use Query Memory (vs LanceDB fallback)")
    query_memory_api_url: str = Field(default="https://api.querymemory.com", description="Query Memory API endpoint")
    query_memory_api_key: str = Field(default="", description="Query Memory API key")
    lancedb_path: str = Field(default="./agent_memory_local.db", description="Path to local LanceDB database")
    fallback_timeout_seconds: float = Field(default=5.0, description="Timeout before falling back to LanceDB")
    embedding_model: str = Field(default="ollama", description="Embedding model (ollama or query_memory)")
