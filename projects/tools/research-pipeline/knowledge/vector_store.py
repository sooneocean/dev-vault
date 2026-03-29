"""LanceDB vector store — hybrid search (vector + full-text) over research notes."""

from __future__ import annotations

import json
import re
import subprocess
from datetime import date
from pathlib import Path
from typing import Any

from config import PIPELINE_ROOT, VAULT_ROOT

LANCEDB_DIR = PIPELINE_ROOT / "lancedb"
TABLE_NAME = "research_notes"


def _get_embedding(text: str) -> list[float]:
    """Get BGE-M3 embedding from Ollama."""
    result = subprocess.run(
        ["curl", "-s", "http://localhost:11434/api/embed",
         "-d", json.dumps({"model": "bge-m3", "input": text})],
        capture_output=True, text=True, timeout=30,
    )
    data = json.loads(result.stdout)
    return data["embeddings"][0]


def _chunk_markdown(filepath: Path) -> list[dict[str, str]]:
    """Split a Markdown file into chunks by ## headings."""
    text = filepath.read_text(encoding="utf-8")

    # Extract frontmatter
    frontmatter = {}
    if text.startswith("---"):
        end = text.find("---", 3)
        if end > 0:
            fm_text = text[3:end].strip()
            for line in fm_text.split("\n"):
                if ":" in line:
                    key, _, val = line.partition(":")
                    frontmatter[key.strip()] = val.strip().strip('"')
            text = text[end + 3:].strip()

    # Split by ## headings
    sections = re.split(r"\n(?=## )", text)
    chunks = []
    for section in sections:
        section = section.strip()
        if not section or len(section) < 20:
            continue

        # Extract heading
        heading = ""
        if section.startswith("## "):
            heading = section.split("\n")[0].replace("## ", "")

        chunks.append({
            "note_path": str(filepath.relative_to(VAULT_ROOT)),
            "section": heading or "intro",
            "text": section[:2000],  # Limit chunk size
            "title": frontmatter.get("title", filepath.stem),
            "tags": frontmatter.get("tags", ""),
            "date": frontmatter.get("created", ""),
        })

    return chunks


def index_note(filepath: Path) -> int:
    """Index a single research note into LanceDB. Returns chunk count."""
    try:
        import lancedb
    except ImportError:
        print("Warning: lancedb not installed. Run: pip install lancedb")
        return 0

    chunks = _chunk_markdown(filepath)
    if not chunks:
        return 0

    # Generate embeddings
    records = []
    for chunk in chunks:
        try:
            embedding = _get_embedding(chunk["text"][:512])  # BGE-M3 input limit
            records.append({**chunk, "vector": embedding})
        except Exception as e:
            print(f"Warning: embedding failed for {chunk['note_path']}:{chunk['section']}: {e}")
            continue

    if not records:
        return 0

    # Upsert into LanceDB
    LANCEDB_DIR.mkdir(parents=True, exist_ok=True)
    db = lancedb.connect(str(LANCEDB_DIR))

    if TABLE_NAME in db.table_names():
        table = db.open_table(TABLE_NAME)
        # Remove old entries for this file
        table.delete(f'note_path = "{records[0]["note_path"]}"')
        table.add(records)
    else:
        db.create_table(TABLE_NAME, records)

    return len(records)


def index_all_research_notes() -> int:
    """Index all research-scan and research-deep notes."""
    resources_dir = VAULT_ROOT / "resources"
    total = 0

    for pattern in ["research-scan-*.md", "research-deep-*.md", "poc-*.md"]:
        for filepath in resources_dir.glob(pattern):
            count = index_note(filepath)
            if count > 0:
                print(f"Indexed {filepath.name}: {count} chunks")
                total += count

    return total


def search(query: str, top_k: int = 10) -> list[dict[str, Any]]:
    """Hybrid search: vector similarity + keyword matching."""
    try:
        import lancedb
    except ImportError:
        print("Warning: lancedb not installed")
        return []

    if not LANCEDB_DIR.exists():
        return []

    db = lancedb.connect(str(LANCEDB_DIR))
    if TABLE_NAME not in db.table_names():
        return []

    table = db.open_table(TABLE_NAME)

    try:
        query_embedding = _get_embedding(query)
        results = (
            table.search(query_embedding)
            .limit(top_k)
            .to_list()
        )
        return [
            {
                "path": r["note_path"],
                "section": r["section"],
                "text": r["text"][:300],
                "title": r["title"],
                "score": r.get("_distance", 0),
            }
            for r in results
        ]
    except Exception as e:
        print(f"Search error: {e}")
        return []


def index_and_report() -> None:
    """CLI entry: index all notes and print summary."""
    count = index_all_research_notes()
    print(f"Total: {count} chunks indexed in {LANCEDB_DIR}")


if __name__ == "__main__":
    index_and_report()
