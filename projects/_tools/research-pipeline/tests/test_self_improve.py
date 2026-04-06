"""Tests for self-improvement: experience recorder + optimizer."""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

# Add pipeline root to path so imports work
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


# ---------------------------------------------------------------------------
# Experience recorder tests
# ---------------------------------------------------------------------------


class TestExperienceRecorder:
    def test_record_creates_vault_note(self, tmp_path):
        from self_improve.experience import record_run

        exp_file = tmp_path / "research-pipeline-experience.md"
        metrics_file = tmp_path / "experience-metrics.json"

        with (
            patch("self_improve.experience.EXPERIENCE_FILE", exp_file),
            patch("self_improve.experience.STATE_DIR", tmp_path),
        ):
            record_run(
                run_id="test-001",
                mode="quick-scan",
                scan_count=40,
                new_count=5,
                eval_count=5,
                poc_count=2,
                poc_success=1,
            )

        assert exp_file.exists()
        content = exp_file.read_text(encoding="utf-8")
        assert "test-001" in content
        assert "quick-scan" in content
        assert "40" in content

    def test_record_creates_structured_json(self, tmp_path):
        from self_improve.experience import record_run

        exp_file = tmp_path / "research-pipeline-experience.md"

        with (
            patch("self_improve.experience.EXPERIENCE_FILE", exp_file),
            patch("self_improve.experience.STATE_DIR", tmp_path),
        ):
            record_run(
                run_id="test-001",
                mode="deep-scan",
                scan_count=80,
                new_count=10,
            )

        metrics = tmp_path / "experience-metrics.json"
        assert metrics.exists()
        data = json.loads(metrics.read_text(encoding="utf-8"))
        assert len(data) == 1
        assert data[0]["run_id"] == "test-001"
        assert data[0]["mode"] == "deep-scan"
        assert data[0]["scan_count"] == 80

    def test_record_appends_to_existing(self, tmp_path):
        from self_improve.experience import record_run

        exp_file = tmp_path / "research-pipeline-experience.md"

        with (
            patch("self_improve.experience.EXPERIENCE_FILE", exp_file),
            patch("self_improve.experience.STATE_DIR", tmp_path),
        ):
            record_run(run_id="run-1", mode="quick-scan", scan_count=10, new_count=2)
            record_run(run_id="run-2", mode="deep-scan", scan_count=20, new_count=5)

        content = exp_file.read_text(encoding="utf-8")
        assert "run-1" in content
        assert "run-2" in content

        metrics = json.loads((tmp_path / "experience-metrics.json").read_text(encoding="utf-8"))
        assert len(metrics) == 2

    def test_record_with_errors(self, tmp_path):
        from self_improve.experience import record_run

        exp_file = tmp_path / "research-pipeline-experience.md"

        with (
            patch("self_improve.experience.EXPERIENCE_FILE", exp_file),
            patch("self_improve.experience.STATE_DIR", tmp_path),
        ):
            record_run(
                run_id="err-001",
                mode="quick-scan",
                scan_count=0,
                new_count=0,
                errors=["Scanner timeout", "API rate limited"],
            )

        content = exp_file.read_text(encoding="utf-8")
        assert "Scanner timeout" in content
        assert "2" in content  # error count

    def test_record_with_proposals(self, tmp_path):
        from self_improve.experience import record_run

        exp_file = tmp_path / "research-pipeline-experience.md"

        with (
            patch("self_improve.experience.EXPERIENCE_FILE", exp_file),
            patch("self_improve.experience.STATE_DIR", tmp_path),
        ):
            record_run(
                run_id="prop-001",
                mode="deep-scan",
                scan_count=50,
                new_count=8,
                proposals_generated=3,
                proposals_accepted=1,
                proposals_rejected=1,
            )

        metrics = json.loads((tmp_path / "experience-metrics.json").read_text(encoding="utf-8"))
        assert metrics[0]["proposals_generated"] == 3


# ---------------------------------------------------------------------------
# Optimizer tests (without DSPy)
# ---------------------------------------------------------------------------


class TestOptimizerTrainingData:
    def test_collect_empty_returns_empty(self, tmp_path):
        from self_improve.optimizer import collect_training_data

        with patch("self_improve.optimizer.TRAINING_DATA_DIR", tmp_path):
            assert collect_training_data() == []

    def test_record_and_collect_verdict(self, tmp_path):
        from self_improve.optimizer import collect_training_data, record_human_verdict

        with patch("self_improve.optimizer.TRAINING_DATA_DIR", tmp_path):
            record_human_verdict(
                tool_name="test-mcp",
                tool_url="https://github.com/test/test-mcp",
                model_verdict="watching",
                human_verdict="poc_candidate",
                scan_result={"description": "Great tool"},
            )

            data = collect_training_data()
            assert len(data) == 1
            assert data[0]["tool_name"] == "test-mcp"
            assert data[0]["model_verdict"] == "watching"
            assert data[0]["human_verdict"] == "poc_candidate"

    def test_multiple_verdicts_appended(self, tmp_path):
        from self_improve.optimizer import collect_training_data, record_human_verdict

        with patch("self_improve.optimizer.TRAINING_DATA_DIR", tmp_path):
            for i in range(5):
                record_human_verdict(
                    tool_name=f"tool-{i}",
                    tool_url=f"https://github.com/test/tool-{i}",
                    model_verdict="watching",
                    human_verdict="not_applicable",
                )

            data = collect_training_data()
            assert len(data) == 5

    def test_malformed_lines_skipped(self, tmp_path):
        from self_improve.optimizer import collect_training_data

        data_file = tmp_path / "verdict-overrides.jsonl"
        data_file.write_text(
            '{"tool_name": "valid", "human_verdict": "watching"}\n'
            'this is not json\n'
            '{"tool_name": "also-valid", "human_verdict": "poc_candidate"}\n',
            encoding="utf-8",
        )

        with patch("self_improve.optimizer.TRAINING_DATA_DIR", tmp_path):
            data = collect_training_data()
            assert len(data) == 2


class TestOptimizerStats:
    def test_stats_empty(self, tmp_path):
        from self_improve.optimizer import training_data_stats

        with patch("self_improve.optimizer.TRAINING_DATA_DIR", tmp_path):
            stats = training_data_stats()
            assert stats["total"] == 0
            assert stats["ready_for_bootstrap"] is False
            assert stats["ready_for_mipro"] is False

    def test_stats_with_data(self, tmp_path):
        from self_improve.optimizer import record_human_verdict, training_data_stats

        with patch("self_improve.optimizer.TRAINING_DATA_DIR", tmp_path):
            for i in range(12):
                verdict = "poc_candidate" if i < 4 else "watching" if i < 8 else "not_applicable"
                record_human_verdict(
                    tool_name=f"tool-{i}",
                    tool_url=f"url-{i}",
                    model_verdict="watching",
                    human_verdict=verdict,
                )

            stats = training_data_stats()
            assert stats["total"] == 12
            assert stats["ready_for_bootstrap"] is True
            assert stats["ready_for_mipro"] is False
            assert stats["verdict_distribution"]["poc_candidate"] == 4
            assert stats["verdict_distribution"]["watching"] == 4
            assert stats["verdict_distribution"]["not_applicable"] == 4


class TestOptimizerDspyCheck:
    def test_check_dspy_returns_false(self):
        from self_improve.optimizer import _check_dspy

        # DSPy is not installed in test env
        assert _check_dspy() is False

    def test_optimize_without_dspy_returns_none(self, tmp_path):
        from self_improve.optimizer import optimize_evaluator

        with patch("self_improve.optimizer.TRAINING_DATA_DIR", tmp_path):
            result = optimize_evaluator()
            assert result is None


class TestVersionManagement:
    def test_list_versions_empty(self, tmp_path):
        from self_improve.optimizer import list_versions

        with patch("self_improve.optimizer.PROMPT_VERSIONS_DIR", tmp_path):
            assert list_versions() == []

    def test_list_versions_with_entries(self, tmp_path):
        from self_improve.optimizer import list_versions

        # Create two version directories
        v1 = tmp_path / "bootstrap-20260301-120000"
        v1.mkdir()
        (v1 / "meta.json").write_text(json.dumps({
            "strategy": "bootstrap",
            "num_examples": 15,
            "status": "active",
        }))

        v2 = tmp_path / "bootstrap-20260315-120000"
        v2.mkdir()
        (v2 / "meta.json").write_text(json.dumps({
            "strategy": "bootstrap",
            "num_examples": 20,
            "status": "active",
        }))

        with patch("self_improve.optimizer.PROMPT_VERSIONS_DIR", tmp_path):
            versions = list_versions()
            assert len(versions) == 2
            assert versions[0]["name"] == "bootstrap-20260301-120000"

    def test_rollback_no_versions(self, tmp_path):
        from self_improve.optimizer import rollback

        with patch("self_improve.optimizer.PROMPT_VERSIONS_DIR", tmp_path):
            assert rollback() is False

    def test_rollback_to_previous(self, tmp_path):
        from self_improve.optimizer import rollback

        # Create two versions + latest pointer
        v1 = tmp_path / "bootstrap-v1"
        v1.mkdir()
        (v1 / "meta.json").write_text(json.dumps({
            "strategy": "bootstrap", "num_examples": 10, "status": "active",
        }))

        v2 = tmp_path / "bootstrap-v2"
        v2.mkdir()
        (v2 / "meta.json").write_text(json.dumps({
            "strategy": "bootstrap", "num_examples": 15, "status": "active",
        }))

        latest = tmp_path / "latest.json"
        latest.write_text(json.dumps({"version": "bootstrap-v2"}))

        with patch("self_improve.optimizer.PROMPT_VERSIONS_DIR", tmp_path):
            result = rollback()
            assert result is True

            # latest now points to v1
            current = json.loads(latest.read_text(encoding="utf-8"))
            assert current["version"] == "bootstrap-v1"

            # v2 is marked as rolled_back
            v2_meta = json.loads((v2 / "meta.json").read_text(encoding="utf-8"))
            assert v2_meta["status"] == "rolled_back"

    def test_rollback_to_specific_version(self, tmp_path):
        from self_improve.optimizer import rollback

        v1 = tmp_path / "v1"
        v1.mkdir()
        (v1 / "meta.json").write_text(json.dumps({
            "strategy": "bootstrap", "num_examples": 10, "status": "active",
        }))

        v2 = tmp_path / "v2"
        v2.mkdir()
        (v2 / "meta.json").write_text(json.dumps({
            "strategy": "mipro", "num_examples": 30, "status": "active",
        }))

        latest = tmp_path / "latest.json"
        latest.write_text(json.dumps({"version": "v2"}))

        with patch("self_improve.optimizer.PROMPT_VERSIONS_DIR", tmp_path):
            result = rollback("v1")
            assert result is True

            current = json.loads(latest.read_text(encoding="utf-8"))
            assert current["version"] == "v1"
            assert current["strategy"] == "bootstrap"
