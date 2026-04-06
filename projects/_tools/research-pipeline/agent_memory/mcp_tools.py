"""MCP tool definitions for agent memory."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class MemoryStoreInput(BaseModel):
    """Input for memory:store tool."""

    agent_id: str = Field(..., description="ID of agent storing this document")
    source: str = Field(..., description="Source type (evaluation, github, arxiv, feedback)")
    content: str = Field(..., description="Document content")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Metadata (verdict, domain_tags, etc.)")


class MemoryStoreOutput(BaseModel):
    """Output for memory:store tool."""

    doc_id: str = Field(..., description="Unique document ID")
    status: str = Field(..., description="Status (stored, error)")


class MemorySearchInput(BaseModel):
    """Input for memory:search tool."""

    query: str = Field(..., description="Search query")
    agent_id: Optional[str] = Field(None, description="Filter by agent ID (evaluator, scanner, etc.)")
    metadata_filters: Optional[dict[str, Any]] = Field(None, description="Filter by metadata (verdict, domain_tags)")
    top_k: Optional[int] = Field(10, description="Number of top results")
    context_preamble: Optional[str] = Field(None, description="Context to prepend for better embedding relevance")


class MemorySearchResult(BaseModel):
    """Single result in memory search."""

    doc_id: str = Field(..., description="Document ID")
    content: str = Field(..., description="Document content")
    metadata: dict[str, Any] = Field(..., description="Document metadata")
    relevance_score: float = Field(..., description="Relevance score (0-1)")
    timestamp: Optional[str] = Field(None, description="Creation timestamp")


class MemorySearchOutput(BaseModel):
    """Output for memory:search tool."""

    results: list[MemorySearchResult] = Field(..., description="Search results")
    count: int = Field(..., description="Number of results")


class MemoryTemporalInput(BaseModel):
    """Input for memory:search_temporal tool."""

    domain: str = Field(..., description="Domain tag to filter by (rag, agent-framework, etc.)")
    after_date: Optional[str] = Field(None, description="ISO8601 date: only return docs after this date")
    before_date: Optional[str] = Field(None, description="ISO8601 date: only return docs before this date")


class MemoryTemporalOutput(BaseModel):
    """Output for memory:search_temporal tool."""

    results: list[MemorySearchResult] = Field(..., description="Search results")
    count: int = Field(..., description="Number of results")


# MCP tool definitions for SDK integration
MEMORY_STORE_TOOL = {
    "name": "memory:store",
    "description": "Store a document in agent memory for future retrieval. Documents are immutable (append-only) with rich metadata for filtering.",
    "inputSchema": {
        "type": "object",
        "properties": {
            "agent_id": {
                "type": "string",
                "description": "ID of the agent storing this (e.g., 'evaluator', 'scanner', 'orchestrator')",
            },
            "source": {
                "type": "string",
                "description": "Source type (e.g., 'evaluation', 'github', 'arxiv', 'human_feedback')",
            },
            "content": {
                "type": "string",
                "description": "Primary document content (description, eval result, etc.)",
            },
            "metadata": {
                "type": "object",
                "description": "Rich metadata for filtering: verdict, domain_tags, tool_name, run_id, scores, etc.",
                "additionalProperties": True,
            },
        },
        "required": ["agent_id", "source", "content"],
    },
}

MEMORY_SEARCH_TOOL = {
    "name": "memory:search",
    "description": "Search agent memory by semantic similarity with optional filtering. Returns ranked results with relevance scores.",
    "inputSchema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Natural language search query",
            },
            "agent_id": {
                "type": "string",
                "description": "Optional: filter results to only this agent's documents",
            },
            "metadata_filters": {
                "type": "object",
                "description": "Optional: filter by metadata (e.g., {'verdict': 'poc_candidate'})",
                "additionalProperties": True,
            },
            "top_k": {
                "type": "integer",
                "description": "Number of top results to return (default: 10)",
                "default": 10,
            },
            "context_preamble": {
                "type": "string",
                "description": "Optional: context to improve embedding relevance (e.g., 'I am the evaluator agent, evaluating RAG tools')",
            },
        },
        "required": ["query"],
    },
}

MEMORY_TEMPORAL_TOOL = {
    "name": "memory:search_temporal",
    "description": "Search agent memory by temporal range and domain tag. Useful for finding recent discoveries, feedback, or discoveries in a specific domain.",
    "inputSchema": {
        "type": "object",
        "properties": {
            "domain": {
                "type": "string",
                "description": "Domain tag to filter by (e.g., 'rag', 'agent-framework', 'embedding-model')",
            },
            "after_date": {
                "type": "string",
                "description": "ISO8601 date: only return documents created after this date",
            },
            "before_date": {
                "type": "string",
                "description": "ISO8601 date: only return documents created before this date",
            },
        },
        "required": ["domain"],
    },
}
