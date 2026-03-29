"""Shared Pydantic models for the research pipeline."""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, HttpUrl


class SourceType(str, Enum):
    GITHUB = "github"
    ARXIV = "arxiv"
    HUGGINGFACE = "huggingface"
    WEB = "web"


class Verdict(str, Enum):
    POC_CANDIDATE = "poc_candidate"
    WATCHING = "watching"
    NOT_APPLICABLE = "not_applicable"


class ScanResult(BaseModel):
    """A single discovery from a source scanner."""

    source: SourceType
    name: str
    url: str
    description: str = ""
    stars: int | None = None
    last_updated: date | None = None
    tags: list[str] = Field(default_factory=list)
    raw_metadata: dict[str, Any] = Field(default_factory=dict)
    is_paper: bool = False
    discovered_at: datetime = Field(default_factory=datetime.now)


class EvaluationScore(BaseModel):
    """Score for a single evaluation dimension."""

    dimension: str
    score: int = Field(ge=0, le=10)
    reasoning: str


class EvaluationResult(BaseModel):
    """Structured evaluation of a scan result."""

    scan_result: ScanResult
    scores: list[EvaluationScore]
    total_score: int
    max_score: int
    percentage: float
    verdict: Verdict
    recommended_action: str = ""


class PoCResult(BaseModel):
    """Result of a PoC sandbox execution."""

    evaluation_result: EvaluationResult
    install_success: bool
    quickstart_success: bool
    execution_time_seconds: float
    notes: str = ""
    artifacts: list[str] = Field(default_factory=list)


class PipelineRunState(BaseModel):
    """Tracks state of a single pipeline run for checkpointing."""

    run_id: str
    mode: str  # "quick-scan" or "deep-scan"
    started_at: datetime = Field(default_factory=datetime.now)
    phase: str = "scanning"  # scanning, evaluating, poc, writing, complete
    scan_results: list[ScanResult] = Field(default_factory=list)
    evaluation_results: list[EvaluationResult] = Field(default_factory=list)
    poc_results: list[PoCResult] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class SeenUrl(BaseModel):
    """Tracks a previously scanned URL for cross-run dedup."""

    url: str
    verdict: Verdict | None = None
    first_seen: date
    expires: date
