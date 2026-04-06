"""Indexing trigger — called after vault notes are written to update LanceDB."""

from __future__ import annotations

from pathlib import Path

from config import VAULT_ROOT


def index_after_write(note_path: str | Path) -> None:
    """Index a newly written note into the knowledge layer."""
    filepath = Path(note_path)
    if not filepath.is_absolute():
        filepath = VAULT_ROOT / filepath

    if not filepath.exists():
        print(f"Warning: Note not found: {filepath}")
        return

    # Only index research-related notes
    name = filepath.name
    if not any(name.startswith(prefix) for prefix in ["research-scan-", "research-deep-", "poc-"]):
        return

    try:
        from knowledge.vector_store import index_note
        count = index_note(filepath)
        if count > 0:
            print(f"Indexed {name}: {count} chunks")
    except ImportError:
        print("Warning: LanceDB not available, skipping vector indexing")
    except Exception as e:
        print(f"Warning: Indexing failed for {name}: {e}")
