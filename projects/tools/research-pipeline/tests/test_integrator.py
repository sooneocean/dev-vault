"""Tests for the integration assessor — proposals, risk tiers, dedup, and persistence."""

from __future__ import annotations

import json
import sys
import tempfile
from datetime import date, datetime
from pathlib import Path
from unittest.mock import patch

import pytest

# Add pipeline root to path so imports work
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from models import (
    EvaluationResult,
    EvaluationScore,
    IntegrationProposal,
    PoCResult,
    RiskLevel,
    ScanResult,
    SourceType,
    Verdict,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def make_scan_result(
    name: str = "test-mcp",
    url: str = "https://github.com/test/test-mcp",
    source: SourceType = SourceType.GITHUB,
    stars: int = 5000,
    **kwargs,
) -> ScanResult:
    return ScanResult(
        source=source,
        name=name,
        url=url,
        description="A test MCP server.",
        stars=stars,
        tags=["mcp", "test"],
        is_paper=False,
        **kwargs,
    )


def make_eval_result(
    name: str = "test-mcp",
    verdict: Verdict = Verdict.POC_CANDIDATE,
    pct: float = 0.75,
) -> EvaluationResult:
    sr = make_scan_result(name=name, url=f"https://github.com/test/{name}")
    return EvaluationResult(
        scan_result=sr,
        scores=[
            EvaluationScore(dimension="Relevance", score=8, reasoning="Good"),
            EvaluationScore(dimension="Maturity", score=7, reasoning="OK"),
        ],
        total_score=int(pct * 50),
        max_score=50,
        percentage=pct,
        verdict=verdict,
        recommended_action="Integrate",
    )


def make_poc_result(
    name: str = "test-mcp",
    install_ok: bool = True,
    quickstart_ok: bool = True,
) -> PoCResult:
    eval_result = make_eval_result(name=name)
    return PoCResult(
        evaluation_result=eval_result,
        runtime="python",
        install_success=install_ok,
        quickstart_success=quickstart_ok,
        execution_time_s=2.5,
        notes="All tests passed" if quickstart_ok else "quickstart failed",
    )


def make_proposal(
    name: str = "test-mcp",
    risk: RiskLevel = RiskLevel.LOW,
    status: str = "pending",
) -> IntegrationProposal:
    return IntegrationProposal(
        tool_name=name,
        tool_url=f"https://github.com/test/{name}",
        risk_level=risk,
        category="mcp_server_add",
        title=f"Add {name} to settings.json",
        description="Test proposal",
        config_diff='{"mcpServers": {"test": {"command": "npx"}}}',
        target_file="settings.json",
        status=status,
    )


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------


class TestIntegrationProposal:
    def test_default_status_is_pending(self):
        p = make_proposal()
        assert p.status == "pending"

    def test_risk_levels(self):
        assert RiskLevel.LOW.value == "low"
        assert RiskLevel.MEDIUM.value == "medium"
        assert RiskLevel.HIGH.value == "high"

    def test_serialization_roundtrip(self):
        p = make_proposal()
        data = p.model_dump(mode="json")
        restored = IntegrationProposal(**data)
        assert restored.tool_name == p.tool_name
        assert restored.risk_level == p.risk_level

    def test_created_at_auto_set(self):
        p = make_proposal()
        assert isinstance(p.created_at, datetime)


# ---------------------------------------------------------------------------
# Proposal parsing tests
# ---------------------------------------------------------------------------


class TestParseProposals:
    def test_parse_valid_json_array(self):
        from integrator import _parse_proposals

        response = """```json
[
  {
    "tool_name": "paper-search-mcp",
    "tool_url": "https://github.com/example/paper-search",
    "risk_level": "low",
    "category": "mcp_server_add",
    "title": "Add paper-search-mcp",
    "description": "Adds full-text arXiv search",
    "config_diff": "{}",
    "target_file": "settings.json"
  }
]
```"""
        proposals = _parse_proposals(response)
        assert len(proposals) == 1
        assert proposals[0].tool_name == "paper-search-mcp"
        assert proposals[0].risk_level == RiskLevel.LOW

    def test_parse_bare_json(self):
        from integrator import _parse_proposals

        response = '[{"tool_name": "x", "risk_level": "medium", "category": "tool_replace", "title": "Replace X"}]'
        proposals = _parse_proposals(response)
        assert len(proposals) == 1
        assert proposals[0].risk_level == RiskLevel.MEDIUM

    def test_parse_max_3_proposals(self):
        from integrator import _parse_proposals

        items = [
            {"tool_name": f"tool-{i}", "risk_level": "low", "category": "mcp_server_add", "title": f"Add tool-{i}"}
            for i in range(5)
        ]
        response = json.dumps(items)
        proposals = _parse_proposals(response)
        assert len(proposals) == 3  # capped at 3

    def test_parse_empty_array(self):
        from integrator import _parse_proposals

        proposals = _parse_proposals("[]")
        assert proposals == []

    def test_parse_invalid_json_returns_empty(self):
        from integrator import _parse_proposals

        proposals = _parse_proposals("This is not JSON at all")
        assert proposals == []

    def test_parse_invalid_risk_level_returns_empty(self):
        from integrator import _parse_proposals

        response = '[{"tool_name": "x", "risk_level": "critical", "category": "x", "title": "x"}]'
        proposals = _parse_proposals(response)
        assert proposals == []  # ValueError from RiskLevel


# ---------------------------------------------------------------------------
# Proposal persistence tests
# ---------------------------------------------------------------------------


class TestProposalPersistence:
    def test_save_and_load_proposals(self, tmp_path):
        from integrator import load_pending_proposals, save_proposals

        with patch("integrator.PROPOSALS_DIR", tmp_path):
            proposals = [make_proposal("tool-a"), make_proposal("tool-b", RiskLevel.MEDIUM)]
            save_proposals(proposals)

            loaded = load_pending_proposals()
            assert len(loaded) == 2
            assert loaded[0].tool_name == "tool-a"
            assert loaded[1].tool_name == "tool-b"

    def test_save_empty_returns_none(self, tmp_path):
        from integrator import save_proposals

        with patch("integrator.PROPOSALS_DIR", tmp_path):
            result = save_proposals([])
            assert result is None

    def test_update_proposal_status(self, tmp_path):
        from integrator import load_pending_proposals, save_proposals, update_proposal_status

        with patch("integrator.PROPOSALS_DIR", tmp_path):
            proposals = [make_proposal("tool-a"), make_proposal("tool-b")]
            save_proposals(proposals)

            updated = update_proposal_status("tool-a", "applied")
            assert updated is True

            pending = load_pending_proposals()
            assert len(pending) == 1
            assert pending[0].tool_name == "tool-b"

    def test_update_nonexistent_tool_returns_false(self, tmp_path):
        from integrator import save_proposals, update_proposal_status

        with patch("integrator.PROPOSALS_DIR", tmp_path):
            save_proposals([make_proposal("tool-a")])
            assert update_proposal_status("nonexistent", "applied") is False

    def test_load_from_empty_dir(self, tmp_path):
        from integrator import load_pending_proposals

        with patch("integrator.PROPOSALS_DIR", tmp_path):
            assert load_pending_proposals() == []


# ---------------------------------------------------------------------------
# Toolchain loading tests
# ---------------------------------------------------------------------------


class TestLoadToolchain:
    def test_loads_mcp_servers_from_settings(self, tmp_path):
        from integrator import _load_current_toolchain

        settings = tmp_path / "settings.json"
        settings.write_text(json.dumps({
            "mcpServers": {"github": {"command": "npx"}, "fetch": {"command": "npx"}},
        }))

        with patch("integrator.SETTINGS_JSON_PATHS", [settings]):
            toolchain = _load_current_toolchain()
            assert "github" in toolchain["mcp_servers"]
            assert "fetch" in toolchain["mcp_servers"]
            assert toolchain["settings_path"] == str(settings)

    def test_handles_missing_settings(self, tmp_path):
        from integrator import _load_current_toolchain

        nonexistent = tmp_path / "does-not-exist.json"
        with patch("integrator.SETTINGS_JSON_PATHS", [nonexistent]):
            toolchain = _load_current_toolchain()
            assert toolchain["mcp_servers"] == {}
            assert toolchain["settings_path"] is None

    def test_handles_invalid_json(self, tmp_path):
        from integrator import _load_current_toolchain

        settings = tmp_path / "settings.json"
        settings.write_text("not valid json {{{")

        with patch("integrator.SETTINGS_JSON_PATHS", [settings]):
            toolchain = _load_current_toolchain()
            assert toolchain["mcp_servers"] == {}

    def test_merges_multiple_settings_files(self, tmp_path):
        from integrator import _load_current_toolchain

        global_settings = tmp_path / "global.json"
        global_settings.write_text(json.dumps({"mcpServers": {"github": {"command": "npx"}}}))

        project_settings = tmp_path / "project.json"
        project_settings.write_text(json.dumps({"mcpServers": {"custom-mcp": {"command": "node"}}}))

        with patch("integrator.SETTINGS_JSON_PATHS", [global_settings, project_settings]):
            toolchain = _load_current_toolchain()
            assert "github" in toolchain["mcp_servers"]
            assert "custom-mcp" in toolchain["mcp_servers"]


# ---------------------------------------------------------------------------
# Slug generation tests
# ---------------------------------------------------------------------------


class TestSlug:
    def test_simple_name(self):
        from integrator import _slug

        assert _slug("paper-search-mcp") == "paper-search-mcp"

    def test_special_chars_replaced(self):
        from integrator import _slug

        assert _slug("My Tool (v2.0)") == "my-tool-v2-0"

    def test_truncated_at_40(self):
        from integrator import _slug

        result = _slug("a" * 60)
        assert len(result) <= 40


# ---------------------------------------------------------------------------
# JSON extraction tests
# ---------------------------------------------------------------------------


class TestExtractJsonArray:
    def test_extracts_from_markdown_block(self):
        from integrator import _extract_json_array

        text = '```json\n[{"tool_name": "x"}]\n```'
        assert _extract_json_array(text) is not None

    def test_extracts_bare_array(self):
        from integrator import _extract_json_array

        text = 'Here are the proposals: [{"tool_name": "x"}]'
        assert _extract_json_array(text) is not None

    def test_returns_none_for_no_json(self):
        from integrator import _extract_json_array

        assert _extract_json_array("No JSON here") is None
