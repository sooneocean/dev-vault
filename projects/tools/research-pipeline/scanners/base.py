"""Shared scanner utilities and result schema."""

from __future__ import annotations

from models import ScanResult


def dedup_results(results: list[ScanResult]) -> list[ScanResult]:
    """Deduplicate scan results by URL, keeping the first occurrence."""
    seen: set[str] = set()
    deduped: list[ScanResult] = []
    for r in results:
        normalized = r.url.rstrip("/").lower()
        if normalized not in seen:
            seen.add(normalized)
            deduped.append(r)
    return deduped


def merge_tags(existing: list[str], new: list[str]) -> list[str]:
    """Merge tag lists, preserving order and removing duplicates."""
    seen: set[str] = set()
    merged: list[str] = []
    for tag in existing + new:
        lower = tag.lower()
        if lower not in seen:
            seen.add(lower)
            merged.append(tag)
    return merged
